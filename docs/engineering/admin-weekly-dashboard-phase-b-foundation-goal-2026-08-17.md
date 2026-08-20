# 관리자 주간 대시보드 Phase B 기반 계약 목표 — 2026-08-17

## 현재 상태

- 기준 커밋은 `4fdef31`이고 `origin/main`과 동기화되어 있다.
- v6에는 웹 관리자 앱과 운영 데이터베이스가 아직 없다. 현재 실행 가능한 제품 경계는
  `humansearch` Python 패키지와 `pytest`/`ruff`/`mypy` 검증 배관뿐이다.
- 기존 v4 화면은 월요일 기준 집계와 실패 시 정적 값 유지가 있어 새 요구사항의 정본으로
  사용할 수 없다. 읽기 전용 결함 증거로만 본다.
- `bash scripts/session-status.sh`는 약 73초 후 세 줄을 모두 출력했다.
  결과는 `HEAD: 4fdef31 (synced)`, `ORIGIN: 4fdef31`,
  `RED: 1/19 (acceptance-0-7.sh 제외 — CI 담당)`이다.
- 기존 RED는 `scripts/acceptance-0-2.sh`의 도달 불가능 객체 11건이다. 추적 파일·비밀
  검사는 통과하며, 해결에는 reflog 만료/GC가 필요하므로 이번 기능 범위에서 건드리지 않는다.

## 근본 원인

기존 몰입도 잔디밭 스펙은 `/admin/dashboard`, 운영 테이블, 외부 사이트 세션 수집기가 v6에
이미 있다고 가정했다. 실제 저장소에는 그 실행 표면이 없어서 화면이나 수집기부터 만들면
기술 스택, 운영 인증, 개인정보 보존, 외부 사이트 정책, 집계 의미를 한 변경에 섞게 된다.

따라서 첫 단계는 새 의존성이나 네트워크 없이 다음 불변식을 실행 가능한 순수 계약으로
고정하는 것이다.

1. 회의 주차 이름과 실적 기간을 분리한다.
2. 실적 기간은 일요일 00:00 KST 이상, 다음 일요일 00:00 KST 미만이다.
3. 실행·포지션·원시 후보·출처 내부 고유 후보·메일 숫자를 서로 대체하지 않는다.
4. 모든 표시 숫자는 한 입력 스냅샷과 입력 지문·계약 버전·근거 행 수를 가진다.
5. 조회 실패와 미실행은 0이 아니라 `FAIL`/`NOT_RUN`과 이유다.
6. 출처를 넘는 동일 후보 판정은 신원 연결 계약 전까지 `NOT_RUN`이다.
7. API용 스냅샷은 이름·이메일·제목·본문 같은 개인정보 원문을 포함하지 않는다.
8. 이 단계에는 Gmail, ClickUp, LinkedIn, Saramin, JobKorea 네트워크 호출이나 쓰기 경로가 없다.

## 구현 계약

기존 `humansearch` 검증 배관을 재사용한다. 새 런타임 의존성, 웹 프레임워크, 데이터베이스,
새 `scripts/acceptance-*.sh`는 추가하지 않는다.

예상 구현 경계:

- `humansearch/src/humansearch/admin_weekly_dashboard/`
  - 주간 경계 계산
  - 상태와 입력 사건 계약
  - 결정론적 스냅샷 집계와 JSON 직렬화
- `humansearch/tests/`
  - 주간 경계, 집계 단위, 실패 상태, 개인정보 비노출, 외부 효과 부재의 런타임 시험
- `contracts/admin-weekly-dashboard/metric-contract-v1.json`
  - 표시 가능한 metric id, 사건 종류, 단위, 설명의 유일한 정본

계약 JSON에는 비밀값, 계정 식별자, 개인 URL, 후보자 데이터가 없어야 한다. Python 구현은
계약 JSON의 metric id를 재정의하지 않고 읽어 검증한다.

## 인수 기준

### AC-B1 — 주간 경계

`2026-08-17`과 같은 ISO 주의 `2026-08-18` 회의는 모두 다음 값을 반환한다.

```text
meeting_iso_week=2026-W34
week_anchor_monday_kst=2026-08-17
event_start_kst=2026-08-09T00:00:00+09:00
event_end_exclusive_kst=2026-08-16T00:00:00+09:00
```

종료 경계와 정확히 같은 사건은 제외하고 시작 경계와 같은 사건은 포함한다.

### AC-B2 — 집계 단위 분리

합성 입력 `run 2 / position 2 / raw discovery 3 / source-unique candidate 2 /
recommendation mail 4`는 각각 별도 metric으로 보존된다. 근거 없는 총 몰입도나 ClickUp 카드
수를 후보 수로 바꾼 metric은 존재하지 않는다.

### AC-B3 — 단일 정본과 provenance

모든 metric은 `status`, `value`, `reason`, `metric_contract_version`, `source_collection`,
`source_row_count`, `input_sha256`를 가진다. 같은 입력은 같은 snapshot hash를 만들며 표시값과
provenance는 같은 함수 호출 결과에서 나온다.

### AC-B4 — 조용한 실패 금지

필수 소스가 `FAIL` 또는 `NOT_RUN`이면 연결 metric의 `value`는 `null`이고 이유가 남는다.
빈 입력의 정상적인 0건과 조회 실패를 구분한다.

### AC-B5 — 개인정보와 외부 효과 경계

스냅샷 JSON에 합성 이름·이메일·제목·본문 원문이 나타나지 않는다. 구현 패키지는 Python
네트워크·HTTP·브라우저·DB·서브프로세스 모듈을 import하지 않으며 외부 사이트 실행 액션을
노출하지 않는다.

### AC-B6 — 출처 간 신원 과장 금지

두 출처가 같은 합성 키를 보내도 원시 행은 각각 남고 출처 내부 고유 수만 계산한다.
전사 고유 후보 metric은 `NOT_RUN`이고 신원 연결 계약 부재 이유를 가진다.

### AC-B7 — 저장소 게이트

다음 명령이 실제 시험 수를 0보다 크게 출력하고 통과한다.

```bash
cd humansearch
uv run --no-sync pytest -q tests/test_admin_weekly_window.py \
  tests/test_admin_weekly_snapshot.py tests/test_admin_weekly_boundaries.py
uv run --no-sync ruff check src tests
uv run --no-sync mypy src tests
cd ..
bash scripts/acceptance-hs-gates.sh
bash verify.sh
```

기존 `acceptance-0-2.sh` RED는 별도 기저 결함으로 보고하며 이번 변경으로 악화하지 않는다.

## RED 계획

1. 구현 모듈이 없는 상태에서 위 인수 시험을 먼저 작성한다.
2. `ModuleNotFoundError` 또는 계약 미구현으로 실패하는 실행 로그를 남긴다.
3. 시험만 단독 커밋한다. 그 뒤 시험 기대값을 바꾸지 않는다.
4. 최소 구현 후 표적 시험, ruff, mypy, 기존 HumanSearch 게이트, 비밀 검사를 실행한다.
5. 월요일 시작 변이, 실패를 0으로 바꾸는 변이, 출처 간 고유 수 생성 변이가 각각 시험을
   깨는지 확인하고 원복한다.

## 적대 검증 계획

1. `env -u ANTHROPIC_API_KEY claude -p`로 이 목표와 diff를 1차 검토한다.
2. 출력 전문과 실행 명령을 이 문서에 append한다.
3. Codex가 각 지적을 `file:line`과 실행으로 `CONFIRM/REFUTE/PARTIAL` 판정한다.
4. 확인된 결함을 고치고 모든 게이트를 다시 실행한다.

## 정본

우선순위는 사용자 제공 `AGENTS.md` > `docs/sot/*` >
`admin-weekly-dashboard-v6-replacement-goal-2026-08-16.md` > 이 문서 > 구현 > 시험이다.

## 비범위

- 웹 UI, 관리자 인증, DB migration, Supabase mirror
- Gmail/ClickUp/캘린더 실제 계정 읽기
- LinkedIn/Saramin/JobKorea 자동 수집
- ClickUp/메일/외부 서비스 쓰기
- 배포, 운영 주소 전환, 기존 서비스 삭제
- 기존 git unreachable object의 reflog 만료 또는 GC

## 실행 증거

### RED — 구현 전 계약 고정

```bash
cd humansearch
uv run --no-sync pytest -q tests/test_admin_weekly_window.py \
  tests/test_admin_weekly_snapshot.py tests/test_admin_weekly_boundaries.py
```

```text
ERROR tests/test_admin_weekly_window.py
ERROR tests/test_admin_weekly_snapshot.py
ERROR tests/test_admin_weekly_boundaries.py
ModuleNotFoundError: No module named 'humansearch.admin_weekly_dashboard'
3 errors in 0.10s
```

→ 시험 러너가 없는 첫 시도는 `NOT_RUN`으로 버리고 `uv sync --locked` 후 다시 실행했다.
위 출력은 시험 3개가 의도한 미구현 모듈 때문에 collection RED가 된 실행 결과다.

### GREEN — 순수 계약 구현

```bash
cd humansearch
uv run --no-sync pytest -q tests/test_admin_weekly_window.py \
  tests/test_admin_weekly_snapshot.py tests/test_admin_weekly_boundaries.py
uv run --no-sync ruff check src tests
uv run --no-sync mypy --strict src tests
```

```text
.........                                                                [100%]
9 passed in 0.02s
All checks passed!
Success: no issues found in 9 source files
```

→ 주간 경계, metric 단위, provenance, 실패 상태, 개인정보 비노출, 외부효과 금지의 첫
9개 시험이 통과했고 lint/type 검사 대상도 0건이 아니다.

### 반대 시험

1. `event_start_date`를 월요일이 되도록 8일 전에서 7일 전으로 고쳤을 때
   `test_admin_weekly_window.py`가 `2 failed, 1 passed`로 일요일 누락을 잡았다.
2. 실패 source의 `value=None`을 `value=0`으로 바꿨을 때
   `test_failed_and_not_run_sources_are_not_rendered_as_zero`가 실패했다.
3. 전사 고유 후보 metric을 `NOT_RUN`에서 출처 무시 distinct로 바꿨을 때
   `test_cross_source_unique_candidate_metric_stays_not_run`이 `PASS != NOT_RUN`으로 실패했다.

→ 세 변이는 모두 RED를 확인한 뒤 `apply_patch`로 원복했고 같은 표적 시험을 다시 통과시켰다.

### 로컬 적대검토에서 추가로 재현한 결함

코드 검토는 raw status 문자열이 `SourceState`를 통과한 뒤 직렬화에서 깨질 수 있음을 찾았다.
보안 검토는 자유형 `reason`의 개인정보 누출, 후보키의 HMAC 형식 미검증, private payload 기반
공개 hash oracle을 찾았다. 다음 네 회귀시험을 테스트 전용 커밋 `939912f`로 먼저 RED로 만들었다.

```text
FAILED test_source_state_rejects_runtime_status_strings — DID NOT RAISE TypeError
FAILED test_source_state_rejects_uncontrolled_failure_text — DID NOT RAISE ValueError
FAILED test_candidate_key_requires_lowercase_hmac_sha256_shape — DID NOT RAISE ValueError
FAILED test_private_payload_does_not_create_a_public_hash_oracle — hash mismatch
4 failed, 6 passed in 0.05s
```

구현 커밋 `46e7a80`에서 status enum 강제, reason code allowlist, HMAC-SHA256 형태 검증,
private payload의 공개 hash 제외를 적용했다.

```text
.............                                                            [100%]
13 passed in 0.04s
All checks passed!
Success: no issues found in 10 source files
```

→ 네 지적은 모두 `CONFIRM→FIXED`다. HMAC 비밀키 보관과 실제 생성은 adapter가 생기는 다음
단계의 별도 계약이며, 이 단계는 전달값의 소문자 64자리 형식만 강제한다.

### 기존 mutation 게이트 배선 결함

첫 전체 검증에서 `scripts/acceptance-hs-gates-mutations.sh`는 고장 코드를 판정하기 전에 임시
프로젝트에 루트 metric 계약이 없어 7개 시험이 `FileNotFoundError`로 실패했다. 계약을 패키지
안에 복제하지 않고, mutation sandbox의 동일한 저장소 상대 경계에 계약 한 벌을 복사하도록
`fedb6c6`에서 수정했다.

```bash
bash scripts/acceptance-hs-gates-mutations.sh
```

```text
PASS: gates mutations blocked 6/6
```

→ 깨진 시험·타입·lint·0건 수집·import·source 삭제의 여섯 변이가 이제 각자 의도한 이유로
차단되고 깨끗한 baseline도 통과한다.

## 1차 적대검증 — Claude CLI `NOT_RUN`

첫 시도는 worktree에서 API 키 환경변수를 제거하고 목표·SOT·전체 diff를 직접 읽도록 했다.

```bash
env -u ANTHROPIC_API_KEY claude -p 'Read docs/engineering/admin-weekly-dashboard-phase-b-foundation-goal-2026-08-17.md, docs/sot/coding-principles.md, and the full git diff origin/main...HEAD in this repository. Perform an adversarial code review of the new admin weekly dashboard Phase B foundation. Run read-only tests or small pure probes if needed. Look specifically for Sunday-to-Saturday boundary errors, metric-unit conflation, nondeterministic hashes, source failure rendered as zero, PII leakage, misleading provenance, fail-open contract parsing, hidden external effects, and tests that can pass while behavior is wrong. Output: VERDICT PASS or FAIL, then ranked findings with exact file:line, a reproduction command or concrete input for every finding, and state whether each acceptance criterion AC-B1 through AC-B7 is proven, disproven, or not run. Do not modify files.'
```

```text
NO_OUTPUT — 180 seconds; interrupted; no verdict body
```

중립 디렉터리에서 CLI 자체를 분리 진단한 요청은 성공했다.

```bash
cd /private/tmp
env -u ANTHROPIC_API_KEY claude -p 'Reply with exactly OK.'
```

```text
OK
```

같은 중립 디렉터리에서 절대경로 저장소 검토를 시킨 두 번째 요청도 180초 동안 본문 0자였다.
마지막으로 Claude의 도구 사용을 없애기 위해 전체 diff를 stdin으로 직접 전달했다.

```bash
git -C /Users/kangsangmo/Desktop/Valuehire_v6/worktrees/admin-dashboard-foundation \
  diff --no-ext-diff --unified=5 origin/main...HEAD | \
  env -u ANTHROPIC_API_KEY claude -p 'The complete Phase B goal, contract, implementation, and tests diff is provided on stdin. Do not use tools or read files. Review only this diff adversarially. Output VERDICT PASS or FAIL, then ranked findings with exact diff file and line context. Check weekly boundary, metric separation, deterministic hash, failure versus zero, PII leakage, input validation, fail-closed contract behavior, hidden external effects, and test gaps. End with AC-B1 through AC-B7 as PROVEN, DISPROVEN, or NOT_RUN.'
```

```text
NO_OUTPUT — 120 seconds; interrupted; exit 130; no verdict body
```

→ Claude 프로그램은 짧은 응답에는 정상이나 세 검토 경로 모두 판정 본문을 만들지 못했다.
외부 판정을 추정하거나 PASS로 바꾸지 않으며 strict V1은 `NOT_RUN`이다.

## 2차 — Codex 재공격

Claude의 주장이 0건이라 재현할 V1 finding은 없다. 대신 독립 코드·보안 검토의 네 finding과
목표의 AC를 직접 실행으로 다시 공격했다.

| 항목 | 판정 | 근거 |
|---|---|---|
| AC-B1 주간 경계 | PROVEN | 월·화 동일 창, 시작 포함·끝 제외 시험과 월요일 변이 RED |
| AC-B2 단위 분리 | PROVEN | run 2 / position 2 / raw 3 / source-unique 2 / mail 4 단언 |
| AC-B3 단일 입력·provenance | PROVEN | 역순 입력도 동일 API payload와 hash, 모든 metric provenance 필드 단언 |
| AC-B4 실패와 0 구분 | PROVEN | FAIL/NOT_RUN은 null, PASS 빈 입력만 0; zero 변이 RED |
| AC-B5 개인정보·외부효과 | PROVEN(Phase B) | 원문 비노출, private hash oracle 제거, 계약상 5개 외부효과 DISABLED |
| AC-B6 출처 간 신원 과장 금지 | PROVEN | source 내부 2와 global NOT_RUN 분리, global distinct 변이 RED |
| AC-B7 저장소 게이트 | PROVEN(기능 범위) | G2 14 tests, ruff/mypy 10 files, mutation 6/6, antiforge 3/3, verify PASS |

기존 `acceptance-0-2.sh`의 unreachable object 11건은 작업 전부터 있던 별도 RED다. 비밀 추적
파일 검사는 PASS이고 이를 고치기 위한 reflog expire/GC는 이번 비범위라 실행하지 않았다.

## 현재 결론

`Phase B 기능 계약: PASS / Claude V1: NOT_RUN / 운영 제품·화면: NOT_RUN`

- Phase B의 순수 weekly snapshot 계약은 구현·회귀·변이·기존 게이트로 검증됐다.
- Claude V1이 없으므로 strict 전체 합격을 주장하지 않는다.
- 웹 UI, 관리자 인증, DB, 실제 읽기 연결은 다음 Phase C의 별도 goal/worktree 대상이다.
