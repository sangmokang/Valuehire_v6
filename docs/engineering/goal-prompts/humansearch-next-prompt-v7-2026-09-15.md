# HumanSearch 다음 실행 프롬프트 v7 — 2026-09-15 01:40, 적대 리뷰 독립 재현 반영

v5(`docs/engineering/goal-prompts/humansearch-next-prompt-v5-2026-09-14.md`) §1·§4~§9 규칙과 v6(`docs/engineering/goal-prompts/humansearch-next-prompt-v6-2026-09-14.md`) §3-3~§6은 그대로 유효하다. 축약·재해석하지 않는다. v7은 v6 §2의 숫자 정정과 §3-1·§3-2를 **재현된 증거 기준의 실행 지시**로 바꾼 것이다. 착수 전 `git worktree list`, 두 워크트리 `git status --short`, `gh pr view 83 96 --json headRefOid` 로 HEAD를 다시 읽는다. 01:36 기준 HEAD: #83 = 6f8b98b, #96 = 9590645, 둘 다 clean.

## 0. 용어
- Finding ID: `docs/engineering/humansearch-codex-adversarial-verdict-2026-09-14.md` 표의 F83-1·F83-2·F83-3·F96-1·F96-2. 재검토 보고는 이 ID로만 한다.
- RED→GREEN: 빠진 동작 때문에 실패하는 시험을 먼저 커밋하고, 최소 변경으로 통과시켜 두 번째 커밋. 두 커밋 사이에 push 없음.
- 재현 스크립트: `docs/engineering/goal-prompts/humansearch-adversarial-repro-2026-09-15/` 3개. 지금은 "통과/written"이 나오고, 수정 뒤에는 "거부/denied"로 뒤집혀야 한다. RED 시험은 이 스크립트를 pytest로 옮긴 것이다.

## 1. 장부 정합 — 이미 끝났다. 다시 세지 않는다
Codex 원문 라벨 high 3(F83-1·F83-2·F96-1)·medium 2(F83-3·F96-2). "S1 4건"은 Claude의 무근거 격상이었고 정정됐다. 다섯 건 전부 Claude가 01:37~01:39에 워크트리 코드로 독립 재현했다(REPRODUCED). 심각도를 바꾸려면 근거를 장부 결정 카드에 쓰고 바꾼다.

## 2. PR #83 — 워크트리 `worktrees/hs-13-stack-20260910`, 브랜치 `task/hs-13-stack-20260910`

불변조건(EARS):
- I-a: When 본문 줄이 JD 원문에 없는 채용 조건을 담으면, 그 줄이 프레임 접두(`문의:`·`제목:` 등)로 시작하더라도 시스템은 패킷 생성을 거부해야 한다. And When JD 원문의 조건 줄이 프레임 위치에 있더라도 충실도 검사 대상에서 빠지지 않아야 한다.
- I-b: When `claim_send` 가 True를 돌려준 뒤에는, 새 attempt 가 열리기 전까지 시스템은 같은 packet_id 의 저장 패킷 본문·수신자 digest 를 바꾸는 `save` 를 거부해야 한다. 순서가 뒤집혀도(save 확인 → 청구 → save 교체) 같다.
- I-c: When 회사 리서치 절이 CompanyBrief 의 검증된 렌더링 결과(예 `- 매출: 300억 원 [I1]`)와 일치하면 시스템은 채용 조건으로 오인해 거부하지 않아야 한다.

RED (셋 다 현재 HEAD에서 실제 실패해야 한다. 통과하면 시험이 잘못된 것):
- `tests/test_hs_1302c_frame_prefix_hiding.py` (F83-1): 음성 `문의: 대졸 필수`·`문의: 재택근무 가능` → `BriefInputError`. 양성 `문의: 담당 컨설턴트`, 기존 정상 프레임 줄 → 통과. JD 원문 조건 줄을 프레임 접두로 옮긴 경우 → 여전히 검사 대상(누락 0). JSON 왕복 후에도 같은 판정.
- `tests/test_hs_1309f_save_claim_ordering.py` (F83-2): ① 결정적 — `_has_send_intent` 직후에 record_intent(A)+claim_send(A) 를 끼우는 훅(재현 스크립트 그대로) → save(B) 는 거부되거나 claim 이 False 여야 한다. ② 동시 — ThreadPoolExecutor 로 save(B) 와 record_intent+claim_send(A) 를 100회 경합 → 어떤 회차에서도 "claim True 이면서 저장 digest ≠ 청구 digest" 가 0. 지금은 ①에서 둘 다 성공, ②에서 불일치 ≥1 이라 실패.
- `tests/test_hs_1305b_company_amount_roundtrip.py` (F83-3): test_hs_1305 `_draft()` → `compose_brief_mail` → `SearchPacket` → `to_json`/`from_json` 왕복 통과. 지금은 `매출: 300억 원` 으로 거부돼 실패. 음성 대조군: 회사 절에 `경력 5년 이상` 을 끼우면 여전히 거부.

GREEN 최소 수정 방향(설계는 바꿔도 되나 아래 counter-AC를 못 넘기면 안 된다):
- F83-1: 프레임 줄 면제를 폐지하고, 허용 프레임 줄은 구조화 필드에서 렌더한 정확 문자열과의 일치로만 통과. counter-AC: 조건 정규식에 단어 하나 추가해 두 반례만 잡는 수정은 실패(제3의 반례 `문의: 야간 근무 가능` 으로 변이 시험).
- F83-2: `PacketStore.save` 의 확인·교체를 `_channel_lock`(send_ledger, flock 재진입 안전) 과 같은 잠금 안에 넣는다. 새 SQLite·새 잠금 파일 체계를 만들지 않는다. counter-AC: 잠금 없이 사후 `_check_current_packet_digest` 만 강화하는 수정은 승인 본문 소실을 못 막으므로 실패.
- F83-3: 회사 리서치 절은 CompanyBrief 렌더링 결과와 줄 단위 대조해 허용. counter-AC: `억 원` 패턴을 통째로 빼는 수정은 음성 대조군에서 실패.

인수:
```
cd worktrees/hs-13-stack-20260910/humansearch
uv run pytest tests/test_hs_1302c_frame_prefix_hiding.py tests/test_hs_1309f_save_claim_ordering.py tests/test_hs_1305b_company_amount_roundtrip.py -q
# 기대: passed ≥ 8, failed 0
uv run pytest tests/test_hs_1304b.py tests/test_hs_1309e.py tests/test_hs_1305.py tests/test_hs_1309b.py -q
# 기대: 기존 90 + 1309b 전부 passed (01:39 실측 90 passed 였다)
uv run ruff check src tests && uv run mypy src tests
cd .. && bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-1300.sh
# 기대: PASS 줄 ≥1, CHECKED: > 92
uv run python docs/engineering/goal-prompts/humansearch-adversarial-repro-2026-09-15/repro_pr83.py        # 기대: F83-1 두 줄 REJECTED, 담당 컨설턴트 PASSED_THROUGH, F83-3 packet ok
uv run python docs/engineering/goal-prompts/humansearch-adversarial-repro-2026-09-15/repro_pr83_race.py   # 기대: save(B) REJECTED 또는 got=False
```
변이(각 GREEN 커밋 뒤): 수정 줄을 되돌린 사본에서 해당 RED가 다시 실패하는지 확인. 생존 0.

## 3. PR #96 — 워크트리 `worktrees/hs-0402a-runner-boundary-20260914`, draft PR

불변조건: When 경계가 검증한 디렉터리 밖이면 시스템은 **실제 write 를 한 바이트도 하지 않아야 한다**. 경로 문자열 검사 강화가 아니라 루트 디렉터리 FD 고정 + `dir_fd`·`O_NOFOLLOW` 상대 열기로 보장한다.

시험 fixture: 이 Mac에 `hsrunner` 계정이 없다. 재현 스크립트처럼 `_runner_uid` 를 현재 uid로 대체하는 fixture 를 두고, 대체 사실을 시험 docstring에 적는다. 실제 OS 임시 디렉터리(`tmp_path`)에서 돌린다.

RED (현재 HEAD 실측: a=denied, b/b2/c=written, d=0바이트 잔존, e=denied):
- (a) 루트 자체 symlink → denied. **이미 통과하므로 RED가 아니다.** 회귀 보호 시험으로 같은 파일에 둔다.
- (b) 루트 상위 컴포넌트 symlink → 지금 written·링크 대상에 파일. 기대 denied, 파일 0.
- (b2) 상위 디렉터리 0777(타인 쓰기 가능) → 지금 written. 기대 denied.
- (c) 검사 직후 루트를 symlink 로 교체(재현 스크립트의 `_ensure_parent` 훅) → 지금 보호 밖에 파일 생성. 기대: 보호 밖 파일 0. 구현이 dir_fd 로 바뀌면 훅 지점이 사라질 수 있으니 시험은 "교체 뒤 보호 밖 디렉터리에 파일 0" 만 단언한다.
- (d) write 중 OSError → 지금 0바이트 파일 잔존. 기대: 최종 경로에 파일 0, 임시 파일 0.
- (e) (d) 뒤 같은 경로 재시도 → 지금 `target_already_exists`. 기대 WRITTEN, 내용 일치.

GREEN 최소 수정: 상위 체인 각 단계 lstat(소유자=러너·symlink 아님·타인 쓰기 불가) → 루트 `os.open(O_RDONLY|O_DIRECTORY|O_NOFOLLOW)` FD 고정 → 하위 mkdir/open 은 전부 `dir_fd=` 상대 경로 → 임시 이름에 쓰고 fsync → `os.link`(덮어쓰기 금지) 또는 `renameat` 게시 → 실패 시 임시 파일·FD 정리. counter-AC: `Path.resolve()` 비교만 추가하는 수정은 (c)에서 실패.

인수:
```
cd worktrees/hs-0402a-runner-boundary-20260914/humansearch
uv run pytest tests/test_runner_boundary*.py -q          # 기대: 새 시험 ≥ 6 포함 전부 passed
uv run ruff check src tests && uv run mypy src tests
uv run python docs/engineering/goal-prompts/humansearch-adversarial-repro-2026-09-15/repro_pr96.py
# 기대: (a)(b)(b2)(c) denied 또는 OUTSIDE False, (d) leftover False, (e) written, (ctl) written
```
main 작업트리의 미추적 `runner_boundary.py` 는 손대지 않는다(다른 세션 소유). PR #96 본문에 "main 미추적 복사본은 이 수정 전 버전(9590645와 동일)" 이라고 적는다.

## 4. 재검토 — Codex adversarial-review 재실행

2·3의 GREEN 커밋 뒤 각 워크트리에서 같은 명령·같은 초점으로 다시 돌린다.
```
cd worktrees/hs-13-stack-20260910
CLAUDE_PLUGIN_ROOT=$HOME/.claude/plugins/cache/openai-codex/codex/1.0.2 node "$CLAUDE_PLUGIN_ROOT/scripts/codex-companion.mjs" adversarial-review "--wait --scope branch --base origin/main F83-1 F83-2 F83-3 가 닫혔는지, 새 우회가 있는지. 판정 장부 docs/engineering/humansearch-codex-adversarial-verdict-2026-09-14.md 의 ID 별로 해결/부분 해결/미해결을 표로."
cd ../hs-0402a-runner-boundary-20260914
... adversarial-review "--wait --scope branch --base origin/main F96-1 F96-2 가 닫혔는지. 검증된 경계 밖 write 0 불변조건을 공격."
```
결과를 판정 장부에 "재검토 2026-09-xx" 절로 붙이고, ID별 `해결 / 부분 해결 / 미해결` + Codex 원문 링크. 미해결이 high 면 그 PR은 병합 후보에서 뺀다. 재검토 결과를 codex-companion 이 못 받으면 NOT_RUN 으로 적고 PASS 로 바꾸지 않는다.

## 5. 그다음
v6 §3-3(HS-03.02, 워크트리 존재·커밋 0) → §3-4(HS-05.02~05 → HS-06.01 → HS-11.01). v6 §4 병합 순서 제안 유지(#96·#83은 §4 재검토에서 high 미해결 0 이어야 순서에 들어간다).

## 6. 금지·경계
v5 §1, v6 §5 전부. 추가: `--no-verify` 금지, 시험 fixture에 실명·이력서 원문 금지(합성만), 재현 스크립트의 uid 대체를 제품 코드에 넣지 않는다, Codex 재검토 없이 "닫힘" 을 쓰지 않는다.

## 7. 종료 보고
1. F83-1·2·3·F96-1·2 각각: RED 커밋 SHA·GREEN 커밋 SHA·시험 수·변이 생존 수·재현 스크립트 출력 뒤집힘 여부.
2. §4 재검토: ID별 해결/부분/미해결, Codex 원문 위치.
3. 회귀: 인수 명령 실제 출력(숫자 그대로).
4. NOT_RUN·BLOCKED 목록과 이유.
5. 사장님 결정 필요 항목만 5줄 카드.
