# HumanSearch 다음 실행 프롬프트 v8 — 2026-09-15 09:30(10:05 자기 검증 4건 반영), Codex 현황 보고 검증 반영

> 정본 위치는 이 저장소 `docs/engineering/goal-prompts/`. 바탕화면 사본(`~/Desktop/hs-next-prompt-v*.md`)은 경유지였고 2026-09-15 10:30 이후 갱신하지 않는다. v5~v7·판정 장부·재현 스크립트도 같은 폴더에 있다.

`/strict` 로 실행한다. 위험등급은 L3(저장·인증·라이브 동작·SOT 수정이 섞임)다. v5(`docs/engineering/goal-prompts/humansearch-next-prompt-v5-2026-09-14.md`) §1·§4~§9, v6(`docs/engineering/goal-prompts/humansearch-next-prompt-v6-2026-09-14.md`) §4~§6, v7(`docs/engineering/goal-prompts/humansearch-next-prompt-v7-2026-09-15.md`) §2·§3·§4 는 그대로 유효하다. v8 은 Codex 가 09-15 08:44 에 낸 "다른 작업 현황" 보고를 검증해 틀린 곳을 바로잡고, 그 위에서 순서를 다시 고정한 것이다. 축약·재해석하지 않는다.

## 결론

Codex 가 오늘 아침 낸 현황 보고는 큰 줄기(병합 0, 잡코리아 실제 코드 0, RPS 는 판정만)는 맞지만 PR 3개와 로컬 브랜치 1개를 빠뜨렸고, 그 탓에 "SQLite 미확인·저장 연결 0"이라는 틀린 결론을 냈다. 다음 세션은 v7 의 결함 수정 2건을 먼저 끝내고, 로컬에만 있는 암호화 계약 브랜치를 원격에 올린 뒤, 후보 중복 식별(HS-03.02)부터 새 작업을 시작한다. 사장님이 정할 것은 암호화 의존성 선택 1건뿐이며, 그 카드는 종료 보고에서 올린다.

## 0. 착수 전 실측 — 이 숫자가 다르면 멈추고 다시 읽는다

```
cd ~/Desktop/Valuehire_v6
git worktree list | grep -c hs-            # 10:00 실측 45 (hs- 워크트리 수. 09:30 초판의 43은 재지 않고 적은 숫자였다 — 정정)
gh pr list --state open --json number,headRefOid,isDraft --jq '.[] | select(.number>=83 or .number==54 or .number==13) | [.number,.headRefOid[0:7],.isDraft] | @tsv'
# 09:20 실측 HEAD: #54 c308eb0 · #83 6f8b98b · #85 443631e · #86 10e9eec · #87 bb311dc(draft) · #88 15534a1 · #89 5228555 · #90 e9e91e4(draft) · #91 387b25f · #92 840d12d · #93 0f46e71 · #94 381f178(draft) · #95 af3942a(draft) · #96 9590645(draft) · #97 7473ec8(draft) · #13 fbe0640(CONFLICTING)
for w in hs-13-stack-20260910 hs-0402a-runner-boundary-20260914 hs-0302-candidate-identity-20260914 hs-0303a-encryption-contract-20260914; do echo "$w $(git -C worktrees/$w status --short | wc -l)"; done
# 09:20 실측: 전부 0 (미커밋 없음)
git status --short | wc -l                  # main 작업트리 미커밋 17 — 다른 세션 소유, 손대지 않는다
```
→ 무엇을: 워크트리 수·열린 PR 의 HEAD·네 워크트리의 미커밋 수를 읽는다. 무엇이: 09:20 값이 주석에 있다. 좋은/나쁜: 값이 다르면 다른 세션이 움직인 것이므로 착수하지 않고 다시 읽는다.

## 1. 용어

- WU: 작업 단위(Work Unit). 인수 기준 1개 = 워크트리 1개 = PR 1개.
- EARS: `When ... 시스템은 ... 해야 한다` 꼴의 한 줄 합격 조건. counter-AC 는 겉보기만 합격인 가짜 완료 시나리오.
- RED→GREEN: 빠진 동작 때문에 실패하는 시험을 먼저 커밋하고, 최소 변경으로 통과시켜 두 번째 커밋. 사이에 push 없음.
- 스택 베이스: PR 의 base 브랜치가 main 이 아니라 앞 PR 브랜치인 것. 앞 PR 이 합쳐져야 뒤가 들어간다.
- Finding ID: `docs/engineering/humansearch-codex-adversarial-verdict-2026-09-14.md` 의 F83-1·2·3, F96-1·2.

## 2. Codex 보고(09-15 08:44) 정정 — 이것이 정본 현황이다

Codex 는 PR 12개(54·83·85~94)를 고정 배열로 조회했다(`~/Desktop/hs-handoff-review-20260915-evidence/fixed-prs-current.json` 의 `pr` 필드). 그래서 아래 세 가지를 놓쳤다.

| 정정 | Codex 가 쓴 것 | 09:20 실측 | 근거 |
|---|---|---|---|
| ① PR 누락 3건 | "SQLite·G3·HS00 회복은 별도 로컬 작업, 최신 완료 여부 미확인" | **#97** HS-03.01 SQLite 스키마 부트스트랩(코드 294줄, `sqlite3.connect` 로 실제 DB 파일 생성·마이그레이션·0600 권한 검사), **#95** G3 리터럴 추출(#13 대체), **#96** HS-04.02a 러너 쓰기 경계(코드 163줄). 셋 다 Draft·CI 2/2 SUCCESS·MERGEABLE | `gh pr list` 09:20; `git show 7473ec8:humansearch/src/humansearch/storage_schema.py` 150~172행(sqlite3 연결·마이그레이션 적용) |
| ② 로컬 전용 브랜치 | 언급 없음 | `worktrees/hs-0303a-encryption-contract-20260914` HEAD 773e795, hs-0401 위 1커밋(SOT 후보 `docs/sot/humansearch-encryption-contract.md` 184줄 + goal 163줄). **원격 0·PR 0 → 소실 위험** | `git branch -r | grep 0303a` 0건 |
| ④ PR 없는 로컬 브랜치 (Claude 초판도 놓침) | "HS00 회복은 별도 로컬 작업, 완료 여부 미확인" — 이 부분은 Codex 가 맞았다 | `task/hs-0004-recovery-20260910` origin/main+48커밋·974파일·41,404줄(HS-00.01~03 시험·인수 스크립트·WU 장부 포함), 원격 0·PR 0. `task/hs-rps-before-rewrite-20260914` 7커밋·1,140줄(#87 이전 RPS 판정 초안, 워크트리 없음). `task/hs-d1-permit` 2커밋. `task/hs-0004-20260910` 은 recovery 에 없는 커밋 4개. 전부 원격 0 | `git branch` × `git branch -r` × `gh pr list --state all` 대조 10:00 |
| ⑤ detached 워크트리 | 언급 없음 | `~/Desktop/hs-premerge-handoff-20260914`(4591d77)·`hs-handoff-fix-20260914`(387b25f)·`hs-pr91-restore.*`(8552796) — 10:10 실측 셋 다 원격 포함(`git branch -r --contains` 각 1). 보존 조치 불필요 | `git branch -r --contains <sha>` 10:10 |
| ③ "저장 실제 연결 0" | 89·90 남은 범위 = "실제 암호화 저장·권한·삭제·독립 재조회 연결" | 부분 부정확. #97 이 DB 를 실제로 만들고 #96 이 실제 파일을 쓴다. 다만 #96 은 F96-1(high)·F96-2(medium) 미수정, 암호화는 0303a 계약 단계 | 09:23 새로 실행: #97 `test_hs_0301.py` 18 passed, #96 runner 시험 14 passed, `repro_pr96.py` (b)(b2)(c) 여전히 written·(d) 0바이트 잔존 |

→ 무엇을: Codex 표와 09:20 `gh pr list`·코드·새 시험 실행을 대조했다. 무엇이: Codex 누락 3건(①)·미언급 1건(②)·부분 부정확 1건(③), 그리고 Claude 초판이 놓친 로컬 브랜치 4개(④). ④의 WU 장부는 **hs-0004-recovery 브랜치에만** 있으므로 이 브랜치가 사라지면 4-5 의 장부 행 번호도 사라진다. 좋은/나쁜: 나쁜 소식이지만 방향은 유리하다 — 저장 기반은 Codex 가 말한 것보다 더 진행돼 있다.

Codex 가 맞게 쓴 것(새로 실측해 유지): RPS 는 판정 코드까지(`rps_project_resolution.py` 591줄, 파일·네트워크·브라우저 import 0개, 30 passed). 잡코리아 검색·상세·저장·복귀 코드는 전 PR 통틀어 0줄. #83 813 passed(15.58초). F83-1·2·3 은 6f8b98b 에서 09:24 그대로 재현(`문의: 대졸 필수` PASSED_THROUGH, save(B) ACCEPTED 뒤 digest 불일치, `매출: 300억 원` REJECTED). 병합 0.

**v7 은 아무 세션도 착수하지 않았다.** #83·#96 HEAD 가 v7 작성 시각(01:36)과 같다.

## 3. 구현 범위 — 어디까지 됐나

| 층 | 있는 것 | 없는 것 |
|---|---|---|
| main 병합됨 | L0 인증표면·D0 브라우저 계약·L1 사람인 탭 1개 읽기 관측(`observe.py`·`_cdp.py`) | 그 외 전부 |
| PR(미병합) 계약·정책 문서 | #85 열람 증거 · #86 Aside 정책 · #88 RPS 프로젝트 · #89 저장 정책 · #90 LinkedIn 상세 저장 · #92 잡코리아 우선 순서 | INDEX 등재(검사기 없음) |
| PR(미병합) 순수 판정 코드 | #93 증거 형식 검증 · #94 커버리지 분류 · #87 RPS 프로젝트 선택 판정 · #83 브리프·패킷·발송 장부(13,499줄) | 브라우저·DB 를 만지는 코드 0 |
| PR(미병합) 실제 부작용 코드 | #97 SQLite 생성 · #96 보호 디렉터리 파일 쓰기 · #54 CDP 핸드셰이크 검증 | #96 결함 2건 · 암호화 · 후보 행 기록(HS-03.02) |
| 로컬만 | 0303a 암호화 의존성 계약 · hs-0004-recovery(WU 장부·HS-00 시험 48커밋) · hs-rps-before-rewrite(RPS 초안 7커밋) · hs-d1-permit(2커밋) | push·PR. 처분은 사장님 결정(§7-5 카드) |
| 라이브 | 0 | 잡코리아 1명 완주 · RPS 생성/필터 · Aside 1초 중단 · checkpoint 재개 |

→ 무엇을: 16개 PR 의 변경 파일을 `git diff --name-only origin/<base>...<head>` 로 나눠 층을 매겼다. 무엇이: 실제 부작용을 내는 코드는 #97·#96·#54 세 개뿐이고 브라우저를 움직이는 코드는 0. 좋은/나쁜: "병합만 남았다"는 오해를 막는 표다.

## 4. 순서 — 한 번에 하나, 앞 PR 병합을 기다리지 않고 스택으로

### 4-1. v7 §2 — PR #83 F83-1·2·3 RED→GREEN (워크트리 `hs-13-stack-20260910`)
v7 §2 의 EARS·RED·GREEN·counter-AC·인수 명령 그대로. 09:24 재현 출력이 뒤집혀야 한다: `repro_pr83.py` 의 `문의: 대졸 필수`·`문의: 재택근무 가능` → REJECTED, `문의: 담당 컨설턴트` → PASSED_THROUGH 유지, F83-3 → packet ok. `repro_pr83_race.py` → save(B) REJECTED 또는 got=False.

### 4-2. v7 §3 — PR #96 F96-1·2 RED→GREEN (워크트리 `hs-0402a-runner-boundary-20260914`)
v7 §3 그대로. `repro_pr96.py` 의 (b)(b2)(c) → denied 또는 OUTSIDE False, (d) leftover False, (e) written.

### 4-3. 로컬 전용 브랜치 배송 (코드 변경 0)
- When 로컬 커밋이 원격에 없으면 시스템은 같은 브랜치명으로 push 하고 Draft PR 을 만들어야 한다. 대상과 base: 0303a → base `hs-0401-storage-policy-contract-20260914`(부모 5228555 확인됨). `hs-0004-recovery-20260910` → base main, 제목에 "회수 보존·병합 대상 아님" 명시(974파일이라 리뷰 대상이 아니라 소실 방지용). `hs-rps-before-rewrite-20260914` 는 #87 로 대체됐으므로 push 만 하고 PR 은 만들지 않는다. `hs-d1-permit` 은 D0 정본이 기각한 방식(메모리 기록)이라 push 만.
- 검증: `gh pr view <새번호> --json headRefOid,baseRefName,isDraft` → 773e795 · hs-0401… · true. CI 2/2 SUCCESS 까지 확인. `git branch -r | grep -cE 'hs-0303a|hs-0004-recovery|hs-rps-before|hs-d1-permit'` → 4. pre-push 훅이 recovery 브랜치에서 FAIL 이면 우회하지 않고 BLOCKED 로 보고한다(훅 27검사는 체크아웃 트리만 본다).
- counter-AC: 내용을 고쳐서 올리는 것. 승인대기 계약은 사장님 결정 전까지 그대로 둔다. 문서 안 결정 카드를 종료 보고 §7-5 에 옮겨 적는다.

### 4-4. HS-03.02 후보 중복 식별 (워크트리 `hs-0302-candidate-identity-20260914`, HEAD 7473ec8 = #97, 커밋 0, 스택 베이스 #97 브랜치)
goal 문서 `docs/engineering/humansearch-hs-0302-candidate-identity-goal-2026-09-15.md` 를 코드보다 먼저 커밋한다. 아래 AC 를 그대로 옮긴다.

#97 실제 스키마(`storage_schema.py` 51~62행, `hs_candidates` 표): 기본키는 `candidate_key_hmac` **하나**이고 `position_ref`·`channel` 은 일반 열, `channel` 허용값은 `'saramin','jobkorea','linkedin_rps'`(`linkedin` 아님). 현재 HEAD 에는 이 표에 행을 넣는 함수가 **없다**(`storage_status` 기본값 `schema_only`). 그래서 RED 는 "기록 함수 부재"에서 시작한다.

- AC-1: When 같은 `(position_ref, channel, candidate_ref)` 로 2회 기록하면 시스템은 `hs_candidates` 행 1개만 남겨야 한다. `candidate_key_hmac` 은 이 세 값의 HMAC 이어야 하며 HMAC 키는 러너 보호 디렉터리(#96)에서 읽는다.
- AC-2: When `position_ref` 또는 `channel` 이 다르면 시스템은 별도 행을 만들어야 한다. 이름·이메일이 같아도 합치지 않는다(HMAC 입력에 세 값이 모두 들어가야 성립).
- AC-3: While SQLite 연결 2개가 같은 키를 동시에 넣으면 시스템은 기본키 제약으로 1행을 보장하고, 진 쪽은 명시적 `duplicate` 결과를 돌려줘야 한다(`sqlite3.IntegrityError` 삼킴 금지, 다른 오류는 그대로 올림).
- AC-4: If 세 값 중 하나라도 비거나 `channel` 이 허용값 밖이면 시스템은 기록을 거부하고 DB 에 행을 만들지 않아야 한다.
- counter-AC: 응용 코드에서 `SELECT` 뒤 `INSERT` 로만 막는 것(AC-3 경쟁 시험에서 2행 생김). HMAC 입력에서 `position_ref` 나 `channel` 을 빼는 것(AC-2 위반). HMAC 키를 코드 상수로 두는 것. 스키마 표를 새로 하나 더 만들어 기존 `hs_candidates` 를 우회하는 것.
- 입출력 계약: 입력 `dict(position_ref:str, channel:Literal["saramin","jobkorea","linkedin_rps"], candidate_ref:str, observed_at:RFC3339)`, 출력 `Literal["inserted","duplicate"]`, 오류 `StorageSchemaError` 하위 타입. 기존 마이그레이션 1 은 수정하지 않는다. 열 추가가 필요하면 `_MIGRATIONS` 에 버전 2 로 추가하고 `_expected_schema_signature` 가 바뀐 표를 포함해야 한다.
- 검증:
```
cd worktrees/hs-0302-candidate-identity-20260914/humansearch
uv run pytest tests/test_hs_0302*.py -q      # 기대: ≥5 passed (중복1·포지션다름1·채널다름1·2연결경쟁1·빈키거부1), RED 커밋에서는 전부 실패
uv run pytest -q                              # 기대: 241 + 새 시험 전부 passed (#97 기준 241 passed 09:23 실측)
uv run ruff check src tests && uv run mypy src tests
cd .. && bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-0302.sh   # 기대: PASS 줄 ≥1, CHECKED: ≥5
```
→ 무엇을: 새 시험·전체 시험·린터·인수 스크립트 순서로 돌린다. 무엇이: 기대 숫자가 주석에 있고 241 은 #97 HEAD 에서 09:23 실측한 값이다. 좋은/나쁜: RED 커밋에서 새 시험이 통과하면 시험이 잘못된 것이다.

> **무엇을** — HS-03.02 를 #97 SQLite 스키마 위 스택으로 두고, 기존 `hs_candidates` 기본키(`candidate_key_hmac`)를 세 값 HMAC 으로 정의해 중복을 막는다.
> **왜** — 장부 168행 인수 기준이 "2연결 경쟁도 unique 제약 보장"을 요구하고, 응용 코드 검사로는 경쟁 시험을 못 넘긴다. 표를 새로 만들면 #93·#94 증거 표가 참조하는 외래키가 갈라진다.
> **버린 길** — main 기준 새 브랜치: #97 마이그레이션 없이는 표가 없어 기각. 이름 기반 병합: 장부 AC-2 위반이라 기각. `unique(position_ref, candidate_key_hmac, channel)` 복합 제약 추가: 기본키가 이미 단독이라 HMAC 입력 정의로 같은 효과를 내는 쪽이 마이그레이션 0개라 채택.
> **대가** — #97 이 병합되기 전까지 이 PR 도 Draft 로 남고, #97 이 바뀌면 rebase 가 필요하다.
> **되돌리기** — 코드는 PR 을 닫으면 회수된다. 단 이미 버전 2 를 적용한 로컬 DB 는 `storage_schema.py` 201~211행(`_current_version`, 모르는 버전이면 `unsupported schema version` 으로 거부)이 초기화를 막으므로 **DB 파일을 지우고 재초기화**해야 한다(Codex F-V8-02 재현). 라이브 0 이라 지워지는 건 합성 시험 데이터뿐이지만, 이 절차와 재시작 시험을 goal 문서 롤백 절에 적는다. 열을 추가하지 않는 설계(HMAC 입력 정의만)면 버전 2 자체가 없어 이 문제가 생기지 않는다 — 그쪽을 우선한다.
- 변이: 기본키 제약 줄을 지운 사본에서 AC-3 시험이, HMAC 입력에서 `channel` 을 뺀 사본에서 AC-2 시험이 각각 실패하는지. 생존 0.

### 4-5. 그다음 — WU 장부 행 그대로(각각 goal 문서 + 워크트리 + PR)
WU 장부 = `worktrees/hs-0004-recovery-20260910/docs/engineering/humansearch-next-issues-wu-2026-09-10.md`. 순서와 스택 베이스:

| WU | 장부 행 | 스택 베이스 | 핵심 EARS(장부 인수 기준을 옮긴 것) |
|---|---|---|---|
| HS-05.02 | 201행 | #86 브랜치(#54 의 3파일은 main 위라 충돌 없음 — #54 병합 전이면 cherry-pick 하고 PR 본문에 적는다) | When 발견된 브라우저가 **예상 engine 과 예상 profile 둘 다 일치하고 그런 후보가 정확히 1개**일 때만 선택. 포트 파일 0개·2개·오래됨·다른 engine·**같은 engine 다른 profile**·비로컬 바인딩이면 거부. 필수 반례: 같은 Aside·같은 origin·다른 로그인 profile 이 유일한 후보인 경우(Codex F-V8-03) → 거부. 포트 하드코딩 변이 검출 |
| HS-05.03 | 202행 | HS-05.02 | When HS-05.02 가 고른 profile 안에서 exact-origin 탭이 정확히 1개일 때만 선택. 0/2개·유사 호스트·다른 profile 의 같은 origin 탭·선택 후 탭 변경 거부 |
| HS-05.04 | 203행 | **두 사슬이 만나는 지점.** base 는 HS-05.03 브랜치 하나로 두고, SQLite 가 필요하므로 그 시점까지 #85→#93→#94→#89→#97→HS-03.02 가 병합돼 있어야 한다. 안 돼 있으면 착수하지 않고 §7-4 BLOCKED 로 보고 | While 실제 SQLite 2연결이 사용권을 다투면 RPS 채널당 1개·타 채널 인스턴스별 1개. 만료·증가 번호로 오래된 소유자 거부 |
| HS-05.05 | 204행 | HS-05.04 | When `/hs stop`·STOP 파일·브라우저 접촉 중 하나가 오면 시스템은 1000ms 안에 실제 소켓을 닫아야 한다. send 전/중/후 경합 각 100회 `sent_after_stop==0`. 플래그만 보는 변이 검출 |
| HS-06.01 | 224행 | HS-05.05 | When DB 재시작 뒤 같은 단계에서 복구. 미확인 외부 효과를 완료로 저장하는 변이 검출 |
| HS-11.01 | 309행 | HS-06.01 | When 잡코리아 허용 origin·목록/상세 fixture 출처가 계약과 다르면 거부. 인증 예외 거부 |

→ 무엇을: WU 장부의 인수 기준을 EARS 한 줄로 옮기고 스택 베이스를 지정했다. 무엇이: 6개 WU 가 사슬로 이어진다. 좋은/나쁜: 각 WU 는 앞 WU 병합을 기다리지 않고 바로 다음 워크트리를 판다.

HS-11.02 이후(실제 잡코리아 검색 적용·1명 완주)와 RPS 생성·필터 쓰기(HS-11.04c·d)는 v5 §6 라이브 조건(Aside 45103 인증·사장님 Chrome 미점유·STOP 장치 실증) 미충족이면 NOT_RUN 으로 두고 로컬 구현만 계속한다. RPS 프로젝트 생성은 09-13 23:24 승인됨 — 다시 묻지 않는다.

## 5. 사장님께 올릴 병합 순서(이번 세션은 병합하지 않는다)

v6 §4 유지 + 0303a 삽입: #85 → #93 → #94 → #89 → #97 → **0303a(새 번호)** → HS-03.02(새 번호) — 이 여섯이 먼저 합쳐져야 4-5 의 HS-05.04 에서 두 사슬이 만난다 → #54 → #86 → #88 → #87 → #90 → #92 → #95 → #96(4-2 뒤) → #83(4-1 뒤) → #91. #13 은 #95 로 대체, 닫기 요청은 사장님 결정.

## 6. 금지·경계
v5 §1, v6 §5, v7 §6 전부. 추가: Codex 의 08:44 표를 현황으로 인용하지 않는다(§2 정정본을 쓴다). `timeout` 명령은 이 Mac 에 없다 — 시험 명령에 넣지 않는다. 임시 검증 워크트리는 스크래치에만 만들고 끝나면 `git worktree remove` 한다.

## 7. 종료 보고
1. 4-1·4-2: Finding ID 별 RED SHA·GREEN SHA·시험 수·변이 생존 수·재현 스크립트 출력 뒤집힘 여부. v7 §4 Codex 재검토 ID 별 해결/부분/미해결.
2. 4-3: 새 PR 번호·HEAD·CI.
3. 4-4·4-5: 착수한 WU, PR 번호, 스택 베이스, 인수 명령 실제 출력(숫자 그대로).
4. NOT_RUN·BLOCKED 목록과 이유.
5. 사장님 결정 필요 항목만 5줄 카드(무엇을/왜/버린 길/대가/되돌리기). 0303a 암호화 의존성 선택, hs-0004-recovery(974파일) 처분(보존 PR 유지 / 장부만 발라내기 / 폐기)은 여기 반드시 포함.
