# HumanSearch 다음 실행 프롬프트 v6 — 2026-09-14 21시, 적대적 리뷰 반영

이 문서는 v5(`docs/engineering/goal-prompts/humansearch-next-prompt-v5-2026-09-14.md`)를 대체하지 않는다. v5 §1·§4~§8의 규칙은 전부 유효하다. v6는 **v5 위에 21시 실측과 Codex 적대적 리뷰 5건을 얹어 "어디서부터"를 고정**한다. 사장님 최신 결정(9/13 23:24 RPS 생성 승인, Aside 전용, Chrome 비간섭)은 다시 묻지 않는다.

## 0. 용어

- WU: 작은 작업 단위 하나. 워크트리 1개 = 브랜치 1개 = PR 1개.
- S1: 병합을 막는 높은 심각도 결함. 라운드 수와 무관하게 고칠 때까지 merge 차단.
- 스택: 앞 PR이 아직 안 합쳐졌어도 그 브랜치 위에 다음 브랜치를 쌓는 것. 앞 PR 병합을 기다리지 않는다.

## 1. 21시 실측 상태(이 값이 착수 기준)

- 로컬 main f12ea33(origin fc6beed + 1커밋). main 작업트리에 다른 세션 미커밋 17파일 — **건드리지 마라**. 그중 `humansearch/src/humansearch/runner_boundary.py`(미추적)는 PR #96 HEAD와 바이트 동일한 복사본이다.
- main에 병합된 HumanSearch 제품 코드는 `auth_surface.py`·`observe.py`·`_cdp.py`뿐(L0·D0·L1). 검색·저장·SQLite·잡코리아·RPS는 main에 0줄.
- HS PR 16개 전부 OPEN·CI SUCCESS 2/2·MERGEABLE, **병합 0건**: #13 #54 #83 #85 #86 #87(draft) #88 #89 #90(draft) #91 #92 #93 #94(draft) #95(draft) #96(draft) #97(draft).
- 이 PR들의 워크트리(`worktrees/hs-*-20260914`, `hs-13-stack-20260910`)는 11:27~11:59 마지막 커밋 뒤 전부 clean(hs-0101a만 1파일 dirty). 다른 세션의 트랙 A·B 작업은 그 시각 이후 멈춰 있다. 착수 전 `git worktree list` + `git -C <wt> status --short` 로 다시 확인하고, dirty면 그 워크트리는 남의 것으로 간주한다.
- 잡코리아·RPS 라이브 0회. Aside 45103은 /json/version 403(인증 필요). Chrome 조작 0.

## 2. 적대적 리뷰 결과(2026-09-14 21시, `docs/engineering/humansearch-codex-adversarial-verdict-2026-09-14.md`)

**2026-09-15 01:40 정정**: 아래 원래 문구의 "S1 4건"은 Claude가 F96-2(Codex medium)를 근거 없이 올린 것이다. Codex 원문 라벨 정본은 **high 3(F83-1·F83-2·F96-1) / medium 2(F83-3·F96-2)**. 누락된 네 번째 원문 finding은 없다. Finding ID·독립 재현 결과는 판정 장부(위 파일) 표를 따른다. 이 §2 나머지는 역사 기록으로 남긴다.

S1로 취급할 것 4건(원문, 정정 전):
1. PR #83 `brief/linkedin_limit.py:285-289` — `문의: 대졸 필수` 같은 프레임 접두 줄이 조건 정규식에 안 걸리면 통째로 면제됨(실행 재현). [F83-1]
2. PR #83 `brief/packet.py:294-300` — `PacketStore.save` 가 장부 잠금 밖에서 intent 확인·파일 교체. save→record_intent→claim_send→save 순서로 승인 digest와 저장 패킷이 갈라짐. [F83-2]
3. PR #96 `runner_boundary.py:55-66` — 보호 루트의 상위 디렉터리·심볼릭 링크 미검사. 검사 뒤 루트 교체 시 절대경로 open이 밖에 씀. [F96-1]
4. PR #96 `runner_boundary.py:140-146` — write/close 실패 시 생성 파일 미정리 → 같은 경로 재시도가 O_EXCL로 영구 거부(코드 확인됨). [F96-2, Codex medium]

중간 1건: PR #83 `brief/types_packet.py:324-330` — 정상 fixture `- 매출: 300억 원 [I1]` 이 회사 리서치 절에서 거부(실행 재현). [F83-3]

HS 밖 2건(다른 세션 소유, 이 프롬프트 범위 아님, 보고만): `check-strict-verdict-ledger.sh:103-109` 옛 증거 재사용 통과, `run-acceptance.sh:64-74` 검사기가 독립 승인 경계가 아님.

## 3. 착수 순서 — 여기서부터

한 번에 하나. 앞 PR 병합을 기다리지 않고 스택으로 바로 다음.

### 3-1. PR #83 S1 2건 + 중간 1건 닫기 (트랙 A 계속, 워크트리 `worktrees/hs-13-stack-20260910`)

각 건마다 RED 커밋 → GREEN 커밋.
- RED-1: `humansearch/tests/test_hs_1302b_frame_prefix.py` — LinkedIn 본문에 `문의: 대졸 필수`, `문의: 재택근무 가능` 추가한 패킷 생성이 `_reject` 돼야 함. 지금은 통과하므로 실패. 양성: `문의: 담당 컨설턴트` 는 통과해야 함.
- GREEN-1: 프레임 줄 면제를 폐지하고, 허용 프레임 줄은 구조화 필드(수신처·회사명)에서 렌더한 정확 문자열과 일치할 때만 통과.
- RED-2: `test_hs_1309d_save_claim_race.py` — save(B)의 intent 확인 직후를 멈추는 훅(monkeypatch로 `_has_send_intent` 뒤에 barrier) → record_intent(A)·claim_send(A) → save(B) 재개. 기대: save(B) 거부 또는 claim_send(A) 실패. 지금은 둘 다 성공하므로 실패.
- GREEN-2: `PacketStore.save`·`record_intent`·`claim_send` 가 같은 packet_id 잠금(기존 `_channel_lock` 계열 재사용, 새 SQLite 만들지 말 것) 안에서 확인·교체.
- RED-3: `test_hs_1305_company_amount_roundtrip.py` — test_hs_1305 정상 `_draft` → `compose_brief_mail` → `SearchPacket` → JSON 왕복이 통과해야 함. 지금은 `매출: 300억 원` 으로 거부돼 실패.
- GREEN-3: 회사 리서치 절 금액은 CompanyBrief 렌더링 결과와 대조해 허용.

인수(각 건 GREEN 뒤):
```
cd worktrees/hs-13-stack-20260910/humansearch && uv run pytest tests/test_hs_1302b_frame_prefix.py tests/test_hs_1309d_save_claim_race.py tests/test_hs_1305_company_amount_roundtrip.py -q
# 기대: 전부 passed, 0 failed. 새 시험 최소 6개(음성 2·양성 1·경합 1·왕복 1·역직렬화 1)
cd worktrees/hs-13-stack-20260910 && bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-1300.sh
# 기대: PASS 줄 ≥1, CHECKED: 숫자가 현재(92)보다 커야 함
```
변이: GREEN-1의 면제 폐지 줄을 되돌리면 RED-1이 다시 실패해야 함(생존 0). 결과를 PR #83 본문 "적대 검증 로그"에 13회차로 추가하고 `docs/engineering/humansearch-codex-adversarial-verdict-2026-09-14.md` 를 링크. `--no-verify` 금지.

### 3-2. PR #96 S1 2건 닫기 (워크트리 `worktrees/hs-0402a-runner-boundary-20260914`, draft PR)

- RED-4: `tests/test_runner_boundary_parent_swap.py` — tmp 상위 디렉터리를 러너가 아닌 다른 소유(또는 0777)로 두고 루트를 만든 뒤 write_file 하면 DENIED(`parent_chain_invalid`)여야 함. 현재는 WRITTEN이라 실패.
- GREEN-4: 루트 open(O_DIRECTORY|O_NOFOLLOW)으로 FD 고정 → `os.open(rel, dir_fd=root_fd, O_NOFOLLOW)` 로 하위 열기. 상위 체인은 각 단계 lstat로 소유자·심볼릭 링크 검사.
- RED-5: `tests/test_runner_boundary_partial_write.py` — `handle.write` 가 OSError를 내도록 monkeypatch → 첫 호출 DENIED(`write_failed`) 뒤 **두 번째 정상 호출이 WRITTEN** 이어야 함. 현재는 `target_already_exists` 라 실패.
- GREEN-5: 같은 디렉터리 임시 파일(`.tmp-<uuid>`)에 쓰고 fsync → `os.link`/`rename` 원자 게시(덮어쓰기 금지 유지) → 실패 시 임시 파일·FD 정리.

인수:
```
cd worktrees/hs-0402a-runner-boundary-20260914/humansearch && uv run pytest tests/test_runner_boundary*.py -q && uv run ruff check src tests && uv run mypy src tests
# 기대: passed, ruff 0, mypy 0
```
main 작업트리의 미추적 `runner_boundary.py` 복사본은 **손대지 마라**(다른 세션 소유). PR #96 본문에 "main 미추적 복사본은 이 수정 전 버전" 이라고 적는다.

### 3-3. 새 WU 착수 — HS-03.02 후보 중복 식별 (워크트리 `worktrees/hs-0302-candidate-identity-20260914`, 이미 존재, HEAD 7473ec8 = HS-03.01과 동일·커밋 0)

선행 HS-03.01(PR #97) 위 스택. 인수 기준(WU 장부 `worktrees/hs-0004-recovery-20260910/docs/engineering/humansearch-next-issues-wu-2026-09-10.md` HS-03.02 행 그대로):
- 같은 `(position, candidate, channel)` 2회 기록 → 행 1개.
- 포지션이 다르거나 채널이 다르면 별도 행(이름으로 합치지 않는다).
- SQLite 2연결이 동시에 같은 키를 넣어도 unique 제약이 1행을 보장(경쟁 시험).
- 키 구성요소가 비면 거부.
```
cd worktrees/hs-0302-candidate-identity-20260914/humansearch && uv run pytest tests/test_hs_0302*.py -q
# 기대: 최소 5 passed(중복 1·포지션 다름 1·채널 다름 1·2연결 경쟁 1·빈 키 거부 1)
```

### 3-4. 그다음(3-3 PR 올린 뒤 바로)

HS-05.02 → 05.03 → 05.04 → 05.05 순서(선행 HS-01.02 PR #54 + HS-03.01 PR #97, 둘 다 스택 베이스로 사용). 각각 WU 장부 행의 인수 기준을 그대로 쓴다. HS-05.05(회수 가능한 전송 핸들)는 경합 100회 `sent_after_stop==0`, 실제 소켓 중단 ≤1000ms 를 시험으로 고정한다. 그 뒤 HS-06.01 → HS-11.01(잡코리아 exact-origin·fixture 계약). 잡코리아·RPS 라이브는 v5 §6 조건 미충족이면 NOT_RUN으로 두고 로컬 구현만 계속.

## 4. 사장님께 올릴 병합 순서(이번 세션은 병합하지 않는다)

의존성 기준. 앞이 합쳐져야 뒤가 충돌 없이 들어간다.
#85 → #93 → #94 → #89 → #97 → #54 → #86 → #88 → #87 → #90 → #92 → #95 → #96(3-2 완료 뒤) → #83(3-1 완료 뒤) → #91.
#13(G3 57커밋, 충돌 7파일)은 병합하지 않고 #95(HS-01.01a)로 대체. 병합 뒤 `docs/sot/INDEX.md` 에 RPS·LinkedIn 정본 2개 등재 여부를 확인(미등재 결함, 검사기 없음).

## 5. 금지·경계(v5 §1 재확인)

- main 작업트리 미커밋 17파일, 남의 dirty 워크트리, Chrome, 실제 발송, RPS 실제 생성, 훅 우회, 강제 push, f12ea33 처분 — 전부 하지 않는다.
- 이력서 원문·후보 실명·세션 값은 git·PR·로그에 넣지 않는다. 시험 fixture는 합성 데이터만.
- Aside 확장 로그인·재시작은 사장님 조치. 필요해지면 그 단계에서만 요청하고 그 전까지 로컬 작업을 계속한다.

## 6. 종료 보고 형식

1. 3-1·3-2: 결함별 RED 커밋 SHA·GREEN 커밋 SHA·시험 수·변이 생존 수·PR 현재 SHA CI 결과.
2. 3-3·3-4: 착수한 WU, PR 번호, 스택 베이스, 인수 명령 실제 출력.
3. NOT_RUN 목록과 이유(라이브·병합 대기).
4. 사장님 결정 필요 항목만 5줄 카드로.
