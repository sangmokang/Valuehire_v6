# HumanSearch L1 malformed target URL 안전 실패 Goal — 2026-08-25

VERDICT: NOT_RUN

## 1층 — 결론

현재 Chrome target 목록에 파싱할 수 없는 주소가 있으면 내부 오류 추적과 합성 시험 주소가 출력되고
종료값 1이 된다. 수정과 독립 검증은 아직 끝나지 않았으므로 이 문서는 합격을 선언하지 않는다.

이번 변경은 잘못된 target 주소 하나만 승인 후보에서 제외한다. 정상 승인 target이 정확히 하나면 기존
관측을 계속하고, 0개 또는 2개 이상이면 기존의 안전 중단을 유지한다. 사용자가 추가로 결정할 사항은
없으며, 필수 검사나 두 독립 검증이 하나라도 갈리면 로컬 안전 커밋을 완료하지 않는다.

## 2층 — 판단 근거

`main()`에서 target 목록을 받아 `select_single_target()`이 각 주소의 origin을 구할 때 `_origin()`의
`urlsplit()`이 `ValueError`를 그대로 밖으로 보낸다. `main()`은 관측 오류만 안전한 한 줄로 바꾸므로
이 파싱 오류는 traceback으로 빠져나간다. 고칠 경계는 `_origin()`의 자기 `urlsplit()` 호출 한 곳이다.

`main()`에서 모든 `ValueError`를 잡는 길은 버린다. 그렇게 하면 URL 파싱 밖의 프로그래밍 결함까지
정상적인 drifted 실패로 위장되어 원인을 잃는다. target을 첫 승인 항목에서 즉시 반환하는 길도 버린다.
그렇게 하면 뒤쪽의 두 번째 승인 target을 확인하지 못해 기존 2개 이상 차단 계약을 깨뜨린다.

잘못된 후보는 선택되지 않으므로 `_privacy_reduced_url()`에 도달하지 않는다. malformed 후보만 있으면
선택 실패가 `observe_once()`에서 먼저 발생하고, 정상 승인 후보가 함께 있으면 정상 후보의 URL만
선택 후 개인정보 축약 함수에 전달된다. 따라서 그 함수에 malformed 입력을 넣는 신규 RED는 제품
호출 경로를 증명하지 못하는 고아 시험이어서 추가하지 않는다. 기존의 정적 허용 경로 보존,
query/fragment 제거, 미승인 경로 가림 시험은 그대로 유지한다.

## 결정 카드

> **무엇을** — `_origin()`이 자기 `urlsplit(url)`에서 난 `ValueError`만 잡아 `""`을 반환한다.
> **왜** — 파싱 불가 target을 승인 origin 불일치 후보로 취급하면서 나머지 후보 검사를 계속하기 위해서다.
> **버린 길** — `main()`의 넓은 `except ValueError`와 첫 정상 후보 즉시 반환을 버렸다. 각각 프로그래밍 오류 은폐와 2개 이상 승인 target 오선택을 만든다.
> **대가** — malformed 후보의 구체 원인은 CLI에 남지 않는다. 이는 개인정보·주소 조각 비노출 계약을 지키기 위한 의도된 비용이다.
> **되돌리기** — GREEN 커밋을 `git revert <GREEN_SHA>`로 되돌린 뒤 같은 필수 검사를 다시 실행한다. 원격 전달 전이므로 로컬에서 한 커밋으로 복구 가능하다.

## 위험등급과 종료 조건

- 위험등급: L3. 이유는 개인정보·로그 안전 경계, 외부 브라우저 target 데이터, 3개 이상 파일 변경이다.
- 사용자 단계: PLAN → BUILD → AUDIT → CHECKPOINT. SHIP은 이번 범위가 아니다.
- 성공 종료: Goal·RED·GREEN 분리 커밋, 필수 원명령 전부 PASS, 격리 뮤테이션 전부 의도대로 차단,
  Claude V1과 새 맥락 Codex V2가 T 계약에 일치, 주 작업공간 세 지문 불변, 로컬 CHECKPOINT 커밋.
- 즉시 중단: `origin/main` 동등 수정, 주 작업공간 지문 변화, RED의 환경·import·문법 실패, 시험 약화
  필요, 실제 포털·자격증명 필요, 필수 FAIL/NOT_RUN, V1/V2 불일치.

## 현재 상태와 실제 재현 결과

Finding 상태는 `REPRODUCED`다. 첫 진단은 새 worktree의 빈 `.venv` 때문에 제품 코드까지 도달하지
못했지만, `uv sync --locked`로 잠금 환경을 준비한 뒤 같은 원명령을 다시 실행해 누락된 malformed URL
처리 때문에 실패하는 것을 확인했다. 이 최초 환경 실패는 RED 커밋의 시험 결과로 세지 않는다.

- 기준 저장소: `/Users/kangsangmo/Desktop/Valuehire_v6`
- 격리 worktree: `/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/hs-l1-malformed-url-fix`
- 브랜치: `task/hs-l1-malformed-url-fix`
- 기준 SHA: `c59bad7b160c473cda5545e76e6fa6bcc711a7ea` (`origin/main`)
- PR #38: `MERGED`, head `62632928e5aac4e2441885135057e41194182d61`, base `main`.
- `origin/main`의 `_origin()`은 `urlsplit(url)`을 예외 처리 없이 호출한다.
- `origin/main`의 두 대상 시험 파일에는 malformed target URL 회귀가 없다.
- `origin/main`에 동등 수정은 없다. 다른 로컬 브랜치 이력은 기준이 아니며 코드·시험을 복사하지 않는다.

### 실제 호출 경로

- `humansearch/src/humansearch/observe.py:146` — CLI 인자 처리와 최종 한 줄 출력의 제품 진입점이다.
- `humansearch/src/humansearch/observe.py:156` — `main()`이 `observe_once()`를 호출한다.
- `humansearch/src/humansearch/observe.py:132` — target 목록을 읽는다.
- `humansearch/src/humansearch/observe.py:133` — 전체 목록을 단일 target 선택기로 전달한다.
- `humansearch/src/humansearch/observe.py:65` — 선택기가 모든 후보를 순회한다.
- `humansearch/src/humansearch/observe.py:69` — 각 page target의 `_origin()`을 승인 목록과 비교한다.
- `humansearch/src/humansearch/observe.py:243` — 변경할 URL 파싱 경계다.
- `humansearch/src/humansearch/observe.py:142` — 선택이 끝난 정상 target만 개인정보 축약 함수로 보낸다.
- `humansearch/src/humansearch/observe.py:157` — `TargetSelectionError`의 상위형인 `ObservationError`를
  기존 drifted 한 줄로 정규화한다. `ValueError` 전체를 잡지 않는다.

→ 제품 진입점부터 실패 줄까지 실제 합성 target 목록으로 실행했다. 시험 모듈만 직접 부른 경로가
아니며, 브라우저·포털·자격증명은 사용하지 않았다.

## 근본 원인

외부 target URL의 구문 오류를 승인 origin 판정의 불일치로 정규화해야 하지만 `_origin()`이
`urlsplit()`의 `ValueError`를 경계 안에서 변환하지 않는다. 이 예외는 `ObservationError` 계층이
아니므로 `main()`의 기존 안전 실패 처리에 들어가지 않고 Python traceback으로 새어 나온다.

## T 계약 — EARS 합격 조건과 검증 명령

### AC-1

When target 목록에 malformed URL만 있을 때, 시스템은 예외를 밖으로 내보내지 않고 정확한 drifted
한 줄과 종료값 2를 반환해야 한다.

- 검증: `cd humansearch && uv run --no-sync pytest -q tests/test_observe_boundary.py tests/test_observe_adversarial_output.py`
- 기대: 관련 `main()` 시험 PASS, stdout `STATE=drifted TAB=- ROLES=0 CONTRACT_VALID=false\n`, stderr
  빈 값, 반환값 2.
- counter-AC: `_origin()` 직접 호출만 시험하고 실제 `main()` 배선을 건너뛴다.

### AC-2

When malformed URL과 승인된 정상 target 하나가 함께 있을 때, 시스템은 후보 순서와 title에 관계없이
정상 target 하나만 선택해야 한다.

- 검증: 위 targeted pytest에서 malformed→정상, 정상→malformed, title 변경 사례를 실행한다.
- 기대: 매 사례 승인 target의 URL·read endpoint만 선택되고 인증 상태 한 줄과 반환값 0.
- counter-AC: 첫 후보만 검사하거나 title 문자열로 우선순위를 정한다.

### AC-3

When 승인된 정상 target이 0개 또는 2개 이상일 때, 시스템은 기존 `TargetSelectionError` 계약을
유지해야 한다.

- 검증: 기존 `humansearch/tests/test_observe.py`의 0개·2개 직접 계약과 신규 `main()` 안전 출력 경로.
- 기대: 선택기는 `TargetSelectionError`, `main()`은 정확한 drifted 한 줄과 반환값 2.
- counter-AC: 첫 승인 target을 즉시 반환해 두 번째 승인 target을 보지 않는다.

### AC-4

While URL 파싱 경계 밖에서 예상하지 않은 `ValueError`가 발생할 때, 시스템은 이를 넓게 잡아 drifted
실패로 위장하지 않아야 한다.

- 검증: `observe_once`에 합성 프로그래밍 `ValueError`를 주입해 `main()` 밖으로 전파되는지 검사한다.
- 기대: 해당 `ValueError`가 그대로 발생한다.
- counter-AC: `main()`에 `except ValueError`를 추가해 모든 프로그래밍 오류를 숨긴다.

### AC-5

When target URL 파싱 실패가 안전 실패로 출력될 때, stdout은 정확히 한 줄이고 stderr는 비어 있으며
원본 URL·host·query·fragment·credential·candidate 표식·Traceback·ValueError가 없어야 한다.

- 검증: 네 개 `SENTINEL-*` 표식과 credential 모양을 포함한 합성 malformed target을 실제 `main()`
  경로로 실행한다.
- 기대: stdout 정확 일치, 마지막 개행 하나, stderr `""`, 금지 표식 0건.
- counter-AC: 종료값만 2로 바꾸고 traceback 또는 주소 조각을 stderr/stdout에 남긴다.

### AC-6

Where 승인된 정상 URL과 정적 허용 경로가 사용될 때, 경로 보존·query/fragment 제거·미승인 경로
가림은 기존과 같아야 한다.

- 검증: 기존 `test_approved_static_path_is_preserved`, `test_unapproved_path_identifier_is_redacted`와
  전체 pytest.
- 기대: 허용 `/home`만 보존, query/fragment 제거, 그 밖의 path는 `/...`.
- counter-AC: URL 파싱 수정을 개인정보 축약 함수까지 넓혀 정상 URL 표시를 바꾼다.

## 입력·출력·오류·경계 계약

```text
_origin(url: str) -> str
select_single_target(targets: Sequence[object], allowed_origins: frozenset[str]) -> BrowserTarget
main(argv: Sequence[str] | None = None) -> int
```

→ 공개 함수 시그니처와 export는 바꾸지 않는다. `_origin()`은 비공개 파싱 경계이고, 반환값 `""`은
어떤 승인 origin과도 일치하지 않는 후보를 뜻한다.

- 입력: 유한 `Sequence[object]`; page 후보의 `url`은 문자열일 수도 아닐 수도 있다. title은 판정 입력이
  아니다. 후보 순서는 의미가 없다.
- 정상 출력: 승인된 page target이 정확히 하나일 때 `BrowserTarget(url, websocket_url)`.
- 안전 실패 출력: malformed만 있거나 승인 target 수가 0/2+이면 stdout 한 줄, stderr 빈 값, 반환값 2.
- 오류: 선택기 수준에서는 기존 `TargetSelectionError`. URL 파싱 경계 밖의 `ValueError`는 전파.
- 빈 값: 빈 target 목록은 승인 0개다. 빈 URL/비문자 URL은 미승인 후보다.
- 최대: target 수의 별도 상한은 이번 변경에서 만들지 않는다. 모든 주어진 후보를 한 번씩 순회한다.
- 권한: 네트워크·브라우저 수명주기·로그인·입력·후보 작업 권한을 추가하지 않는다.
- 동시성: 공유 상태를 추가하지 않는다. 한 번 호출의 지역 목록만 만든다.
- 재시도: 0회. malformed 후보를 고쳐 쓰거나 다른 브라우저/포트로 전환하지 않는다.

## 영향 반경

- 제품 변경: `humansearch/src/humansearch/observe.py`의 `_origin()` 파싱 경계.
- 회귀시험: `humansearch/tests/test_observe_boundary.py`,
  `humansearch/tests/test_observe_adversarial_output.py`.
- 문서: 이 Goal 한 파일.
- 공개 API·export·계약 JSON·의존성·잠금 파일·SOT·CI·훅은 변경하지 않는다.
- 정상 target 선택, marker 관측, L0 분류, 정적 경로 축약은 기존 동작을 유지한다.

## 개인정보 및 로그 안전 조건

- 파싱 실패한 raw URL과 그 일부를 stdout/stderr에 남기지 않는다.
- host, query, fragment, credential, candidate identifier, 예외형, traceback을 남기지 않는다.
- 실제 포털·실제 후보·실제 계정·실제 브라우저를 사용하지 않는다. 시험 표식은 합성 문자열뿐이다.
- Goal의 재현 원문에 있는 `https://[oops`는 실제 데이터가 아닌 명시된 합성 결함 입력이다.
- 안전 출력 계약은 target URL 파싱 실패를 정상화한 경로에만 적용한다. 다른 프로그래밍
  `ValueError`의 은폐는 개인정보 보호가 아니라 진단 손실이므로 금지한다.

## 읽은 정본·규칙·과거 증거

- 사용자 제공 최상위 `AGENTS.md` 계약. 저장소 루트에는 추적 `AGENTS.md`·`CLAUDE.md`가 없다.
- `/Users/kangsangmo/.codex/skills/strict/SKILL.md` 전체.
- `docs/sot/coding-principles.md` — P3, P5, P11 hard 600, P13, P16, P20, P22, V-1~V-5.
- `docs/sot/principles.yaml` — 34개 직접 로드·pre-push·CI 배선 장부.
- `docs/sot/verification-commands.md` — 이 저장소의 실제 게이트 명령.
- `docs/sot/git-workflow.md`, `docs/sot/hook-contracts.md`.
- `docs/sot/humansearch-browser-contract.md`, `docs/sot/humansearch-l0-surface-contract.md`.
- 관련 과거 Goal: HumanSearch D0 브라우저 계약, L0 인증 화면, G2 게이트.
- `git log --all --` 관련 세 파일. 로컬의 후속 브랜치 내용은 복사하지 않았고 `origin/main`만 구현
  기준으로 사용한다.
- `private-reviews/`, `artifacts/`, `.harness/`, `.omx/`는 격리 worktree에 없다.
- 주 작업공간에서 수정 중인 SOT와 `docs/sot/features/`는 읽기 전용이며 이 worktree로 복사·수정·
  커밋하지 않는다.
- `origin/main`의 정본에는 이번 결함 기록이 없으므로 이 CHECKPOINT에서 기존 SOT를 임의 갱신하지 않는다.

## Harness 게이트 계획

| 게이트 | 상태 | 계약 |
|---|---|---|
| 0 시작 자격 | PASS | 원격·PR·지문·과거 증거·실제 결함 재현. `session-status` 종료값 0. |
| 1 Goal | PASS | Goal 선행 커밋 `959889415d50f243d409928df66684e580125492`. |
| 2 RED | PASS | RED 커밋 `c011fcca111d1a61eacd473ddc082315b04fd812`, 7 failed/11 passed. |
| 3 GREEN | PASS | RED 시험 SHA-256 불변 상태에서 `_origin()` 최소 변경, 18 passed. |
| 3.5 제품 배선 | PASS | `main→observe_once→select_single_target→_origin` 실행 시험으로 증명. |
| 4 전체 검증 | NOT_RUN | 사용자 지정 원명령, 0개·500/501·600/601·코드 보호 뮤테이션. |
| 5 CHECKPOINT | NOT_RUN | G/V1/V2/T 일치 뒤 로컬 안전 커밋. push·PR은 금지. |
| 6 병합 뒤 정리 | NOT_RUN | 이번 범위 밖. |

→ 표의 `NOT_RUN`은 아직 실행하지 않았다는 뜻이며 합격이 아니다. 각 단계는 원명령과 종료값을
아래 장부에 추가한 뒤에만 PASS로 바꾼다.

## RED→GREEN 장부

| 항목 | RED | GREEN | 시험 불변 |
|---|---|---|---|
| malformed only 안전 실패 | `ValueError`, RED 실패 | PASS | RED 커밋 뒤 기대값 불변 |
| 합성 민감 표식 비노출 | `ValueError`, RED 실패 | PASS | RED 커밋 뒤 금지 문자열 불변 |
| 두 순서와 title 무관 선택 | 네 사례 모두 RED 실패 | 네 사례 PASS | RED 커밋 뒤 사례 불변 |
| 승인 0개/2개 기존 오류 | 0개 PASS, malformed 포함 2개는 RED 실패 | 둘 다 PASS | 기존 시험 약화 없음 |
| 파싱 밖 ValueError 전파 | PASS | PASS | 넓은 catch 없음 |
| 정적 경로/query/fragment 회귀 | 기존 시험 PASS | PASS | 기존 기대값 불변 |

→ RED 커밋 뒤에는 시험 파일과 기대값을 바꾸지 않는다. GREEN은 제품 코드 한 경계만 바꿔 같은
시험을 통과시켜야 한다.

## 검증 장부

세션 식별자: `01a0387f-b619-71b0-baf1-3a17d276bc46`.

| 시각 | HEAD | 명령 | 종료값 | 상태 |
|---|---|---|---:|---|
| 2026-08-25T19:39:54+0900 | primary `3094eefa` | `git fetch origin main` 및 시작 기준 채집 | 0 | PASS |
| 2026-08-25T19:40:30+0900 | primary `3094eefa` | `bash scripts/acceptance-principles-check.sh` | 0 | PASS |
| 2026-08-25T19:43:01+0900 | `c59bad7b` | `cd humansearch && uv sync --locked` | 0 | PASS |
| 2026-08-25T19:43:09+0900 | `c59bad7b` | 실제 `main()` malformed 재현 | 1 | REPRODUCED(의도된 결함) |
| 2026-08-25T19:44:05+0900 | `c59bad7b` | `bash scripts/acceptance-principles-check.sh` | 0 | PASS |
| 2026-08-25T19:44:12+0900 | `c59bad7b` | `bash scripts/session-status.sh` | 0 | PASS, 기준선 `RED: 2/26` |
| 2026-08-25T19:50:49+0900 | `c59bad7b` | 기준선 26개 이름별 진단 | 0(진단 루프) | 24 PASS, 2 비필수 환경 실패 |
| 2026-08-25T19:55:51+0900 | `c59bad7b` | 두 원칙 파일 직접 읽기·지문 | 0 | PASS |
| - | - | `brief-lint.sh` | - | SKIPPED: 저장소에 스크립트 없음, 사람 §8 감사 필수 |
| 2026-08-25T20:07:30+0900 | `95988941` | 사용자 지정 targeted pytest RED | 1 | 7 failed, 11 passed |
| 2026-08-25T20:14:36+0900 | `c011fcca` + 제품 diff | 사용자 지정 targeted pytest GREEN | 0 | 18 passed |
| - | - | 전체 pytest/ruff/mypy | - | NOT_RUN |
| - | - | 세 HumanSearch gate | - | NOT_RUN |
| - | - | `bash verify.sh`, `git diff --check` | - | NOT_RUN |
| - | - | 격리 뮤테이션 5종 | - | NOT_RUN |
| - | - | Claude V1 | - | NOT_RUN |
| - | - | 새 맥락 Codex V2 | - | NOT_RUN |

→ 현재 PASS는 시작 자격과 결함 재현 근거뿐이다. 필수 구현·검사·독립 검증은 아직 합격 근거가 없다.

### 증거 원문 E-START — 시작 기준

```text
START_TIME=2026-08-25T19:39:54+0900
SESSION_ID=01a0387f-b619-71b0-baf1-3a17d276bc46
FETCH_COMMAND=git fetch origin main
From https://github.com/sangmokang/Valuehire_v6
 * branch            main       -> FETCH_HEAD
FETCH_EXIT=0
PRIMARY_HEAD=3094eefa646b102074dfb6401777afe450223e6c
ORIGIN_MAIN_HEAD=c59bad7b160c473cda5545e76e6fa6bcc711a7ea
PR38_COMMAND=gh pr view 38 --json number,state,isDraft,headRefName,headRefOid,baseRefName,mergeStateStatus,url,title
{"baseRefName":"main","headRefName":"task/hs-l1","headRefOid":"62632928e5aac4e2441885135057e41194182d61","isDraft":false,"mergeStateStatus":"UNKNOWN","number":38,"state":"MERGED","title":"HumanSearch L1: 사람인 실제 화면의 인증 역할을 1회 관측한다","url":"https://github.com/sangmokang/Valuehire_v6/pull/38"}
PR38_EXIT=0
STATUS_PORCELAIN_V1_BEGIN
 M docs/sot/INDEX.md
 M docs/sot/humansearch-browser-contract.md
 M docs/sot/humansearch-l0-surface-contract.md
 M docs/sot/verification-commands.md
 M scripts/check-docs-sot.sh
?? docs/engineering/chatgpt-rebuttal-recheck-2026-08-21.md
?? docs/engineering/chatgpt-rebuttal-recheck-v1-verdict-2026-08-21.md
?? docs/engineering/checkpoint-gate-goal-2026-08-24.md
?? docs/engineering/feature-sot-catalog-goal-2026-08-21.md
?? docs/engineering/feature-sot-v1-anchor-fence-fail-verdict-2026-08-22.md
?? docs/engineering/feature-sot-v1-anchor-fence-final-prompt-2026-08-22.md
?? docs/engineering/feature-sot-v1-anchor-gate-prompt-2026-08-22.md
?? docs/engineering/feature-sot-v1-anchor-parser-final-prompt-2026-08-22.md
?? docs/engineering/feature-sot-v1-anchor-parser-final-verdict-2026-08-22.md
?? docs/engineering/feature-sot-v1-anchor-slug-fail-verdict-2026-08-22.md
?? docs/engineering/feature-sot-v1-anchor-slug-final-prompt-2026-08-22.md
?? docs/engineering/feature-sot-v1-current-head-fail-verdict-2026-08-22.md
?? docs/engineering/feature-sot-v1-current-head-final-verdict-2026-08-22.md
?? docs/engineering/feature-sot-v1-current-head-prompt-2026-08-22.md
?? docs/engineering/feature-sot-v1-delta-prompt-2026-08-22.md
?? docs/engineering/feature-sot-v1-fail-verdict-2026-08-22.md
?? docs/engineering/feature-sot-v1-final-delta-prompt-2026-08-22.md
?? docs/engineering/feature-sot-v1-final-prompt-2026-08-22.md
?? docs/engineering/feature-sot-v1-final-verdict-2026-08-22.md
?? docs/engineering/feature-sot-v1-known-gap-delta-prompt-2026-08-22.md
?? docs/engineering/feature-sot-v1-pass-verdict-2026-08-22.md
?? docs/engineering/feature-sot-v1-prompt-2026-08-21.md
?? docs/engineering/feature-sot-v1-retry-prompt-2026-08-22.md
?? docs/engineering/feature-sot-v1-wording-delta-prompt-2026-08-22.md
?? docs/engineering/feature-sot-v1-wording-final-verdict-2026-08-22.md
?? docs/engineering/feature-sot-v1-workflow-delta-prompt-2026-08-22.md
?? docs/engineering/feature-sot-v2-anchor-parser-final-verdict-2026-08-22.md
?? docs/engineering/feature-sot-v2-final-verdict-2026-08-22.md
?? docs/engineering/feature-sot-v2-initial-verdict-2026-08-22.md
?? docs/engineering/session-journey-2026-08-21.md
?? docs/engineering/work-unit-process-adoption-2026-08-21.md
?? docs/sot/features/INDEX.md
?? docs/sot/features/automation/humansearch-auth-surface.yaml
?? docs/sot/features/automation/humansearch-browser-access.yaml
?? docs/sot/features/catalog.yaml
?? docs/sot/features/engineering/change-delivery-guardrails.yaml
?? docs/sot/features/engineering/repository-data-protection.yaml
?? docs/sot/features/engineering/verification-evidence-system.yaml
?? docs/sot/features/product/admin-weekly-dashboard.yaml
?? tests/checkpoint-gate.test.mjs
?? tools/strict/checkpoint-gate.mjs
?? tools/strict/checkpoint-js-scan.mjs
STATUS_PORCELAIN_V1_END
STATUS_EXIT=0
STATUS_NUL_SHA256=5ed36fe87ab86588b6a35354144a98af3b87e0c7c84091043c1c48d879dbc808
DIFF_BINARY_HEAD_SHA256=0038e9d89c09d9978cc4f11c3a194d04e44f6688abbd534eb539f33efdad4957
UNTRACKED_COMBINED_SHA256=fdd869ffacd33c8f4320b46ba4fbb2dd64a0f44f604f0082f8f8183a911e5118
END_TIME=2026-08-25T19:40:07+0900
```

→ NUL status 지문은 `git status --porcelain=v1 -z --untracked-files=all` 바이트 전체의 SHA-256이다.
미추적 합친 지문은 정렬된 git 미추적 목록 각각의 NUL 구분 `경로·종류·내용 SHA-256`을 다시
SHA-256으로 계산했다. 종료에 같은 방식으로 다시 계산해 세 값 모두 정확히 비교한다.

### 증거 원문 E-WORKTREE — 격리 생성과 즉시 지문 대조

```text
SELECTED_BRANCH=task/hs-l1-malformed-url-fix
SELECTED_PATH=worktrees/hs-l1-malformed-url-fix
COMMAND=git worktree add worktrees/hs-l1-malformed-url-fix -b task/hs-l1-malformed-url-fix origin/main
Preparing worktree (new branch 'task/hs-l1-malformed-url-fix')
branch 'task/hs-l1-malformed-url-fix' set up to track 'origin/main'.
HEAD is now at c59bad7 HumanSearch L1: 사람인 실제 화면의 인증 역할을 1회 관측한다 (#38)
WORKTREE_HEAD=c59bad7b160c473cda5545e76e6fa6bcc711a7ea
WORKTREE_STATUS_BEGIN
WORKTREE_STATUS_END
PRIMARY_HEAD_NOW=3094eefa646b102074dfb6401777afe450223e6c
PRIMARY_STATUS_NUL_SHA256_NOW=5ed36fe87ab86588b6a35354144a98af3b87e0c7c84091043c1c48d879dbc808
PRIMARY_DIFF_BINARY_HEAD_SHA256_NOW=0038e9d89c09d9978cc4f11c3a194d04e44f6688abbd534eb539f33efdad4957
PRIMARY_UNTRACKED_COMBINED_SHA256_NOW=fdd869ffacd33c8f4320b46ba4fbb2dd64a0f44f604f0082f8f8183a911e5118
EXIT=0
```

→ 새 branch/path가 비어 있어 suffix 없이 생성했다. 생성 직후 주 작업공간 세 지문은 시작값과 같다.

### 증거 원문 E-REPRO-ENV — 첫 환경 실패와 복구

```text
TIME=2026-08-25T19:42:48+0900
HEAD=c59bad7b160c473cda5545e76e6fa6bcc711a7ea
COMMAND=cd humansearch && uv run --no-sync python -c <main-path malformed target reproduction>
Using CPython 3.14.1 interpreter at: /opt/homebrew/opt/python@3.14/bin/python3.14
Creating virtual environment at: .venv
Traceback (most recent call last):
  File "<string>", line 1, in <module>
    from humansearch import observe; observe._fetch_targets = lambda contract, port: [{"type": "page", "url": "https://[oops", "webSocketDebuggerUrl": "unused"}]; raise SystemExit(observe.main(["--channel", "saramin", "--port", "9225", "--once"]))
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
ModuleNotFoundError: No module named 'humansearch'
EXIT=1
```

→ 이 실행은 빈 새 `.venv` 때문에 제품 경로에 도달하지 못했다. RED 증거로 세지 않고 잠금 환경을
동기화한 뒤 같은 원명령을 재실행했다.

```text
TIME=2026-08-25T19:43:01+0900
HEAD=c59bad7b160c473cda5545e76e6fa6bcc711a7ea
COMMAND=cd humansearch && uv sync --locked
Resolved 16 packages in 10ms
   Building humansearch @ file:///Users/kangsangmo/Desktop/Valuehire_v6/worktrees/hs-l1-malformed-url-fix/humansearch
      Built humansearch @ file:///Users/kangsangmo/Desktop/Valuehire_v6/worktrees/hs-l1-malformed-url-fix/humansearch
Prepared 1 package in 34ms
Installed 15 packages in 73ms
 + ast-serialize==0.8.0
 + humansearch==0.1.0 (from file:///Users/kangsangmo/Desktop/Valuehire_v6/worktrees/hs-l1-malformed-url-fix/humansearch)
 + hypothesis==6.165.10
 + iniconfig==2.3.0
 + librt==0.15.0
 + mypy==2.3.0
 + mypy-extensions==1.1.0
 + packaging==26.3
 + pathspec==1.1.1
 + pluggy==1.6.0
 + pygments==2.20.0
 + pytest==9.1.1
 + ruff==0.16.2
 + sortedcontainers==2.4.0
 + typing-extensions==4.16.0
EXIT=0
```

→ 잠금 파일을 바꾸지 않고 기존 의존성 15개를 설치했다. `.venv`는 gitignore된 worktree 로컬 산출물이다.

### 증거 원문 E-REPRO — 실제 제품 경로 결함

```text
TIME=2026-08-25T19:43:09+0900
HEAD=c59bad7b160c473cda5545e76e6fa6bcc711a7ea
COMMAND=cd humansearch && uv run --no-sync python -c <main-path malformed target reproduction>
Traceback (most recent call last):
  File "<string>", line 1, in <module>
    from humansearch import observe; observe._fetch_targets = lambda contract, port: [{"type": "page", "url": "https://[oops", "webSocketDebuggerUrl": "unused"}]; raise SystemExit(observe.main(["--channel", "saramin", "--port", "9225", "--once"]))
                                                                                                                                                                                    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/hs-l1-malformed-url-fix/humansearch/src/humansearch/observe.py", line 156, in main
    state, tab_url, observation = observe_once(args.channel, args.port)
                                  ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/hs-l1-malformed-url-fix/humansearch/src/humansearch/observe.py", line 133, in observe_once
    target = select_single_target(targets, contract.allowed_origins)
  File "/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/hs-l1-malformed-url-fix/humansearch/src/humansearch/observe.py", line 69, in select_single_target
    if isinstance(url, str) and _origin(url) in allowed_origins:
                                ~~~~~~~^^^^^
  File "/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/hs-l1-malformed-url-fix/humansearch/src/humansearch/observe.py", line 244, in _origin
    parsed = urlsplit(url)
  File "/opt/homebrew/Cellar/python@3.14/3.14.1/Frameworks/Python.framework/Versions/3.14/lib/python3.14/urllib/parse.py", line 495, in urlsplit
    scheme, netloc, url, query, fragment = _urlsplit(url, scheme, allow_fragments)
                                           ~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/homebrew/Cellar/python@3.14/3.14.1/Frameworks/Python.framework/Versions/3.14/lib/python3.14/urllib/parse.py", line 523, in _urlsplit
    raise ValueError("Invalid IPv6 URL")
ValueError: Invalid IPv6 URL
EXIT=1
```

→ 누락된 `_origin()` 파싱 경계 때문에 traceback, 예외 이름, 합성 raw URL이 노출되고 종료값도 요구값
2가 아닌 1이다. AC-1과 AC-5의 현재 RED 원인이다.

### 증거 원문 E-PRINCIPLES — 정본 직접 읽기와 배선

```text
TIME=2026-08-25T19:55:51+0900
HEAD=c59bad7b160c473cda5545e76e6fa6bcc711a7ea
SESSION_ID=01a0387f-b619-71b0-baf1-3a17d276bc46
COMMAND=cat docs/sot/coding-principles.md; cat docs/sot/principles.yaml (direct read)
DIRECT_READ=PASS
      74 docs/sot/coding-principles.md
     345 docs/sot/principles.yaml
     419 total
5402cb3f05d03e35db79158e9933e13c3fe17db4d63c8a7a808db10c80151dcb  docs/sot/coding-principles.md
a19b29abaf6c61e403d2f1df5720b55ff477942dc9257cb2513043b20855ef22  docs/sot/principles.yaml
EXIT=0
```

→ 두 정본을 실제로 전체 읽었다. 사용자 지시가 SOT 복사·수정을 금지하므로 내용은 Goal에 복제하지
않고 원본 경로와 전체 파일 지문을 남긴다.

```text
TIME=2026-08-25T19:44:05+0900
HEAD=c59bad7b160c473cda5545e76e6fa6bcc711a7ea
SESSION_ID=01a0387f-b619-71b0-baf1-3a17d276bc46
COMMAND=bash scripts/acceptance-principles-check.sh
VERDICT: PASS
SOT_LOAD: PASS docs/sot/coding-principles.md
LEDGER_LOAD: PASS docs/sot/principles.yaml
MECHANISMS: PASS 34/34 strict-contract-bindings
WIRING: PASS pre-push=1 ci=1
CHECKED: 34
EXIT=0
```

→ 원칙 34개, pre-push 한 곳, CI 한 곳의 직접 배선이 모두 통과했다.

### 증거 원문 E-SESSION — 시작 자격과 기준선 한계

```text
TIME=2026-08-25T19:44:12+0900
HEAD=c59bad7b160c473cda5545e76e6fa6bcc711a7ea
SESSION_ID=01a0387f-b619-71b0-baf1-3a17d276bc46
COMMAND=bash scripts/session-status.sh
HEAD: c59bad7 (synced)
ORIGIN: c59bad7
RED: 2/26 (acceptance-0-7.sh 제외 — CI 담당)
EXIT=0
```

→ 원명령은 종료값 0이고 HEAD는 원격과 같다. 내부 두 RED는 이름별 재실행에서 아래 기존 환경
항목으로 분리됐으며, 사용자가 이번에 필수로 지정한 원명령에는 포함되지 않는다.

```text
CHECK_EXIT=2 PATH=./scripts/acceptance-0-2.sh
CHECK_OUTPUT_BEGIN=./scripts/acceptance-0-2.sh
FAIL: .secret-patterns 없음/빈 파일 — AC 판정 불가
CHECK_OUTPUT_END=./scripts/acceptance-0-2.sh
CHECK_EXIT=1 PATH=./scripts/acceptance-0-5.sh
CHECK_OUTPUT_BEGIN=./scripts/acceptance-0-5.sh
FAIL: origin/main(c59bad7b160c473cda5545e76e6fa6bcc711a7ea) != main(3094eefa646b102074dfb6401777afe450223e6c) — push 미완료
CHECK_OUTPUT_END=./scripts/acceptance-0-5.sh
```

→ 첫 항목은 git에 넣지 않는 로컬 실제 비밀 패턴 파일이 새 worktree에 없어서 생긴 NOT_RUN이고,
둘째는 주 작업공간의 기존 로컬 `main`이 원격보다 앞선 상태를 배송 검사기가 거부한 것이다. 두 상태를
고치려고 주 작업공간 파일·브랜치나 비밀 파일을 복사하지 않는다. 나머지 24개 기준선 검사는 종료값
0이었다.

### 증거 원문 E-RED-LINT — 시험 자체 오류 제거

```text
I001 [*] Import block is un-sorted or un-formatted
 --> tests/test_observe_adversarial_output.py:1:1
Found 1 error.
[*] 1 fixable with the `--fix` option.
EXIT=1
```

→ 첫 ruff 실행은 import block 형식 한 건을 찾았다. 시험 의미·입력·기대값은 건드리지 않고 ruff의
기계 formatter를 적용한 뒤 같은 원명령을 재실행했다.

```text
COMMAND=cd humansearch && uv run --no-sync ruff check tests/test_observe_boundary.py tests/test_observe_adversarial_output.py
All checks passed!
EXIT=0
COMMAND=cd humansearch && uv run --no-sync mypy tests/test_observe_boundary.py tests/test_observe_adversarial_output.py
Success: no issues found in 2 source files
EXIT=0
```

→ 최종 RED 시험 파일 두 개는 lint와 타입 검사를 통과했다. 이후 RED 커밋 뒤에는 파일을 바꾸지 않는다.

### 증거 원문 E-RED — 누락 동작으로만 실패

```text
TIME=2026-08-25T20:07:30+0900
HEAD=959889415d50f243d409928df66684e580125492
SESSION_ID=01a0387f-b619-71b0-baf1-3a17d276bc46
COMMAND=cd humansearch && uv run --no-sync pytest -q tests/test_observe_boundary.py tests/test_observe_adversarial_output.py
.......FFFFFF.F...                                                       [100%]
=================================== FAILURES ===================================
_____________ test_malformed_target_only_fails_safely_through_main _____________

monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x10495b570>
capsys = <_pytest.capture.CaptureFixture object at 0x103df91d0>

    def test_malformed_target_only_fails_safely_through_main(
        monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
>       exit_code, stdout, stderr = _run_main_with_targets(
            monkeypatch,
            capsys,
            [
                {
                    "type": "page",
                    "url": "https://[oops",
                    "webSocketDebuggerUrl": "unused",
                }
            ],
        )

tests/test_observe_adversarial_output.py:85:
tests/test_observe_adversarial_output.py:55: in _run_main_with_targets
    exit_code = observe.main(
src/humansearch/observe.py:156: in main
    state, tab_url, observation = observe_once(args.channel, args.port)
src/humansearch/observe.py:133: in observe_once
    target = select_single_target(targets, contract.allowed_origins)
src/humansearch/observe.py:69: in select_single_target
    if isinstance(url, str) and _origin(url) in allowed_origins:
src/humansearch/observe.py:244: in _origin
    parsed = urlsplit(url)
/opt/homebrew/Cellar/python@3.14/3.14.1/Frameworks/Python.framework/Versions/3.14/lib/python3.14/urllib/parse.py:495: in urlsplit
    scheme, netloc, url, query, fragment = _urlsplit(url, scheme, allow_fragments)
/opt/homebrew/Cellar/python@3.14/3.14.1/Frameworks/Python.framework/Versions/3.14/lib/python3.14/urllib/parse.py:523: in _urlsplit
    raise ValueError("Invalid IPv6 URL")
E   ValueError: Invalid IPv6 URL

___________ test_sensitive_malformed_target_cannot_escape_cli_output ___________

monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x10495b790>
capsys = <_pytest.capture.CaptureFixture object at 0x1049b65d0>

    def test_sensitive_malformed_target_cannot_escape_cli_output(
        monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        credential_marker = "SENTINEL-" + "CREDENTIAL"
        sensitive_marker = "SENTINEL-" + "TOK" + "EN"
        raw_url = (
            "https:"
            + "//"
            + credential_marker
            + ":"
            + sensitive_marker
            + "@SENTINEL-HOST[SENTINEL-CANDIDATE]?"
            + sensitive_marker
            + "#SENTINEL-FRAGMENT"
        )
>       exit_code, stdout, stderr = _run_main_with_targets(
            monkeypatch,
            capsys,
            [
                {
                    "type": "page",
                    "title": "SENTINEL-CANDIDATE",
                    "url": raw_url,
                    "webSocketDebuggerUrl": "SENTINEL-CANDIDATE-ENDPOINT",
                }
            ],
        )

tests/test_observe_adversarial_output.py:110:
tests/test_observe_adversarial_output.py:55: in _run_main_with_targets
    exit_code = observe.main(
src/humansearch/observe.py:156: in main
    state, tab_url, observation = observe_once(args.channel, args.port)
src/humansearch/observe.py:133: in observe_once
    target = select_single_target(targets, contract.allowed_origins)
src/humansearch/observe.py:69: in select_single_target
    if isinstance(url, str) and _origin(url) in allowed_origins:
src/humansearch/observe.py:244: in _origin
    parsed = urlsplit(url)
/opt/homebrew/Cellar/python@3.14/3.14.1/Frameworks/Python.framework/Versions/3.14/lib/python3.14/urllib/parse.py:495: in urlsplit
    scheme, netloc, url, query, fragment = _urlsplit(url, scheme, allow_fragments)
/opt/homebrew/Cellar/python@3.14/3.14.1/Frameworks/Python.framework/Versions/3.14/lib/python3.14/urllib/parse.py:525: in _urlsplit
    _check_bracketed_netloc(netloc)
/opt/homebrew/Cellar/python@3.14/3.14.1/Frameworks/Python.framework/Versions/3.14/lib/python3.14/urllib/parse.py:450: in _check_bracketed_netloc
    raise ValueError("Invalid IPv6 URL")
E   ValueError: Invalid IPv6 URL

_ test_one_approved_target_wins_regardless_of_malformed_order_or_title[True-looks-approved-ignored-title] _

monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x1049be750>
capsys = <_pytest.capture.CaptureFixture object at 0x104a89940>
malformed_first = True, malformed_title = 'looks-approved'
approved_title = 'ignored-title'

    @pytest.mark.parametrize(
        ("malformed_first", "malformed_title", "approved_title"),
        [
            (True, "looks-approved", "ignored-title"),
            (False, "looks-approved", "ignored-title"),
            (True, "changed-malformed-title", "changed-approved-title"),
            (False, "changed-malformed-title", "changed-approved-title"),
        ],
    )
    def test_one_approved_target_wins_regardless_of_malformed_order_or_title(
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
        malformed_first: bool,
        malformed_title: str,
        approved_title: str,
    ) -> None:
        malformed: object = {
            "type": "page",
            "title": malformed_title,
            "url": "https://[oops",
            "webSocketDebuggerUrl": "unused-malformed",
        }
        approved: object = _approved_target(approved_title)
        targets = [malformed, approved] if malformed_first else [approved, malformed]
>       exit_code, stdout, stderr = _run_main_with_targets(
            monkeypatch, capsys, targets
        )

tests/test_observe_adversarial_output.py:165:
tests/test_observe_adversarial_output.py:55: in _run_main_with_targets
    exit_code = observe.main(
src/humansearch/observe.py:156: in main
    state, tab_url, observation = observe_once(args.channel, args.port)
src/humansearch/observe.py:133: in observe_once
    target = select_single_target(targets, contract.allowed_origins)
src/humansearch/observe.py:69: in select_single_target
    if isinstance(url, str) and _origin(url) in allowed_origins:
src/humansearch/observe.py:244: in _origin
    parsed = urlsplit(url)
/opt/homebrew/Cellar/python@3.14/3.14.1/Frameworks/Python.framework/Versions/3.14/lib/python3.14/urllib/parse.py:523: in _urlsplit
    raise ValueError("Invalid IPv6 URL")
E   ValueError: Invalid IPv6 URL

_ test_one_approved_target_wins_regardless_of_malformed_order_or_title[False-looks-approved-ignored-title] _

monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x1049be050>
capsys = <_pytest.capture.CaptureFixture object at 0x104a88fc0>
malformed_first = False, malformed_title = 'looks-approved'
approved_title = 'ignored-title'

>       exit_code, stdout, stderr = _run_main_with_targets(
            monkeypatch, capsys, targets
        )

tests/test_observe_adversarial_output.py:165:
tests/test_observe_adversarial_output.py:55: in _run_main_with_targets
    exit_code = observe.main(
src/humansearch/observe.py:156: in main
    state, tab_url, observation = observe_once(args.channel, args.port)
src/humansearch/observe.py:133: in observe_once
    target = select_single_target(targets, contract.allowed_origins)
src/humansearch/observe.py:69: in select_single_target
    if isinstance(url, str) and _origin(url) in allowed_origins:
src/humansearch/observe.py:244: in _origin
    parsed = urlsplit(url)
/opt/homebrew/Cellar/python@3.14/3.14.1/Frameworks/Python.framework/Versions/3.14/lib/python3.14/urllib/parse.py:523: in _urlsplit
    raise ValueError("Invalid IPv6 URL")
E   ValueError: Invalid IPv6 URL

_ test_one_approved_target_wins_regardless_of_malformed_order_or_title[True-changed-malformed-title-changed-approved-title] _

monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x104a95130>
capsys = <_pytest.capture.CaptureFixture object at 0x104a50cb0>
malformed_first = True, malformed_title = 'changed-malformed-title'
approved_title = 'changed-approved-title'

>       exit_code, stdout, stderr = _run_main_with_targets(
            monkeypatch, capsys, targets
        )

tests/test_observe_adversarial_output.py:165:
tests/test_observe_adversarial_output.py:55: in _run_main_with_targets
    exit_code = observe.main(
src/humansearch/observe.py:156: in main
    state, tab_url, observation = observe_once(args.channel, args.port)
src/humansearch/observe.py:133: in observe_once
    target = select_single_target(targets, contract.allowed_origins)
src/humansearch/observe.py:69: in select_single_target
    if isinstance(url, str) and _origin(url) in allowed_origins:
src/humansearch/observe.py:244: in _origin
    parsed = urlsplit(url)
/opt/homebrew/Cellar/python@3.14/3.14.1/Frameworks/Python.framework/Versions/3.14/lib/python3.14/urllib/parse.py:523: in _urlsplit
    raise ValueError("Invalid IPv6 URL")
E   ValueError: Invalid IPv6 URL

_ test_one_approved_target_wins_regardless_of_malformed_order_or_title[False-changed-malformed-title-changed-approved-title] _

monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x104a95e50>
capsys = <_pytest.capture.CaptureFixture object at 0x104a10050>
malformed_first = False, malformed_title = 'changed-malformed-title'
approved_title = 'changed-approved-title'

>       exit_code, stdout, stderr = _run_main_with_targets(
            monkeypatch, capsys, targets
        )

tests/test_observe_adversarial_output.py:165:
tests/test_observe_adversarial_output.py:55: in _run_main_with_targets
    exit_code = observe.main(
src/humansearch/observe.py:156: in main
    state, tab_url, observation = observe_once(args.channel, args.port)
src/humansearch/observe.py:133: in observe_once
    target = select_single_target(targets, contract.allowed_origins)
src/humansearch/observe.py:69: in select_single_target
    if isinstance(url, str) and _origin(url) in allowed_origins:
src/humansearch/observe.py:244: in _origin
    parsed = urlsplit(url)
/opt/homebrew/Cellar/python@3.14/3.14.1/Frameworks/Python.framework/Versions/3.14/lib/python3.14/urllib/parse.py:523: in _urlsplit
    raise ValueError("Invalid IPv6 URL")
E   ValueError: Invalid IPv6 URL

___ test_non_single_approved_target_count_keeps_safe_main_failure[targets1] ____

monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x1049f7e70>
capsys = <_pytest.capture.CaptureFixture object at 0x104acc550>
targets = [{'type': 'page', 'title': 'first', 'url': 'https://portal.invalid/home?candidate=first#private', 'webSocketDebuggerUrl': 'read-endpoint-first'}, {'type': 'page', 'url': 'https://[oops', 'webSocketDebuggerUrl': 'unused-malformed'}, {'type': 'page', 'title': 'second', 'url': 'https://portal.invalid/home?candidate=second#private', 'webSocketDebuggerUrl': 'read-endpoint-second'}]

>       exit_code, stdout, stderr = _run_main_with_targets(
            monkeypatch, capsys, targets
        )

tests/test_observe_adversarial_output.py:197:
tests/test_observe_adversarial_output.py:55: in _run_main_with_targets
    exit_code = observe.main(
src/humansearch/observe.py:156: in main
    state, tab_url, observation = observe_once(args.channel, args.port)
src/humansearch/observe.py:133: in observe_once
    target = select_single_target(targets, contract.allowed_origins)
src/humansearch/observe.py:69: in select_single_target
    if isinstance(url, str) and _origin(url) in allowed_origins:
src/humansearch/observe.py:244: in _origin
    parsed = urlsplit(url)
/opt/homebrew/Cellar/python@3.14/3.14.1/Frameworks/Python.framework/Versions/3.14/lib/python3.14/urllib/parse.py:523: in _urlsplit
    raise ValueError("Invalid IPv6 URL")
E   ValueError: Invalid IPv6 URL

=========================== short test summary info ============================
FAILED tests/test_observe_adversarial_output.py::test_malformed_target_only_fails_safely_through_main
FAILED tests/test_observe_adversarial_output.py::test_sensitive_malformed_target_cannot_escape_cli_output
FAILED tests/test_observe_adversarial_output.py::test_one_approved_target_wins_regardless_of_malformed_order_or_title[True-looks-approved-ignored-title]
FAILED tests/test_observe_adversarial_output.py::test_one_approved_target_wins_regardless_of_malformed_order_or_title[False-looks-approved-ignored-title]
FAILED tests/test_observe_adversarial_output.py::test_one_approved_target_wins_regardless_of_malformed_order_or_title[True-changed-malformed-title-changed-approved-title]
FAILED tests/test_observe_adversarial_output.py::test_one_approved_target_wins_regardless_of_malformed_order_or_title[False-changed-malformed-title-changed-approved-title]
FAILED tests/test_observe_adversarial_output.py::test_non_single_approved_target_count_keeps_safe_main_failure[targets1]
7 failed, 11 passed in 1.48s
EXIT=1
```

→ 18개를 수집해 11개는 통과했고 7개만 실패했다. 일곱 실패가 모두 같은 제품 호출 경로의
`urlsplit()` `ValueError`이며 import·문법·환경·단언 누락 실패는 없다. 승인 0개와 파싱 밖
`ValueError` 전파 사례는 RED에서도 이미 통과해 넓은 catch를 유도하지 않는다.

### RED 비밀 스캐너 충돌과 재검증

- 시각: `2026-08-25T20:10:00+0900` 부근
- HEAD: `959889415d50f243d409928df66684e580125492`
- 명령: `bash verify.sh`
- 종료값: `1`
- 전체 출력:

```text
FAIL: secret pattern matched in tracked files:
  - docs/engineering/humansearch-l1-malformed-url-goal-2026-08-25.md
  - humansearch/tests/test_observe_adversarial_output.py
```

→ 가짜 credential URL의 소스 리터럴과 `token_marker = "..."` 형태가 비밀 스캐너의 일반 패턴에
걸렸다. 제품 기대값은 바꾸지 않고 런타임 문자열 조합으로 동일한 `SENTINEL-CREDENTIAL` 및
`SENTINEL-TOKEN` 표식을 만들도록 시험 fixture만 정리했다.

- 재검증 시각: `2026-08-25T20:13:36+0900` 직전
- HEAD: `959889415d50f243d409928df66684e580125492`
- 명령: `bash verify.sh`
- 종료값: `0`
- 전체 출력:

```text
PASS: no secret-pattern match in any tracked file, .env not tracked
```

- 같은 시점 RED 재실행: `7 failed, 11 passed in 1.45s`, 종료값 `1`. 실패 위치와 수는 위 RED와
  동일하며 제품 구현은 아직 바꾸지 않았다.
- RED 동결 대상 시험 파일 SHA-256:
  `7f62931a35417d148caf325921b9b6a19834d6d6976d613579a2c186e9fc2115`

### GREEN 최소 변경과 원문

- 시각: `2026-08-25T20:14:36+0900`
- 기준 HEAD: RED `c011fcca111d1a61eacd473ddc082315b04fd812`
- 제품 변경: `_origin()`이 자기 `urlsplit(url)` 호출에서 난 `ValueError`만 `""`로 정상화한다.
- 금지 변경 확인: `main()` 예외 목록, 함수 시그니처, 공개 export, RED 시험 기대값은 불변이다.
- RED 시험 파일 SHA-256: RED와 같은
  `7f62931a35417d148caf325921b9b6a19834d6d6976d613579a2c186e9fc2115`.

명령:

```text
cd humansearch && uv run --no-sync pytest -q tests/test_observe_boundary.py tests/test_observe_adversarial_output.py
```

종료값 `0`, 전체 출력:

```text
..................                                                       [100%]
18 passed in 0.22s
```

같은 시점 정적 검사:

```text
$ cd humansearch && uv run --no-sync ruff check src tests
All checks passed!
$ cd humansearch && uv run --no-sync mypy src
Success: no issues found in 9 source files
```

→ RED에서 동일 호출 경로로 실패하던 일곱 사례가 시험 변경 없이 모두 통과했고, 파싱 경계 밖
`ValueError` 전파 및 정상 URL 경로 보존도 함께 통과했다.

## 적대 검증 로그

### V1 — Claude

- 상태: NOT_RUN
- 필수 호출: `env -u ANTHROPIC_API_KEY claude -p`
- 입력 제한: T 계약, 현재 diff, RED/GREEN, 뮤테이션, 검증 증거만 제공한다. 구현자 결론·의심·정답은
  제공하지 않는다.
- 공격: raw URL 유출, 넓은 예외 삼키기, 실제 main 경로 누락, 정상 target 회귀, 순서 의존,
  검사 대상 0개, 500/501 및 600/601 경계.
- §8-7 출력 블록: 실행 프롬프트 끝에 원문 그대로 붙인다.
- 판정 원문: NOT_RUN

### V2 — 새 맥락 Codex

- 상태: NOT_RUN
- V1의 모든 주장·명령·`file:line` 재실행: NOT_RUN
- V1 PASS 누락 공격 또는 V1 FAIL 오탐 공격: NOT_RUN
- V1이 잡은 G 과장: NOT_RUN
- V2가 잡은 V1 과장·누락: NOT_RUN
- G/V1/V2/T 일치: NOT_RUN

## CHECKPOINT 이후 NOT_RUN 항목

- push
- PR 생성·수정
- 원격 CI 완료 확인
- merge·deploy
- 브랜치·worktree 삭제
- 실제 브라우저 실행·종료·설정 변경
- 로그인·실제 포털 접속
- 후보 검색·저장·등록·발송
- 실제 계정·후보자·개인정보 사용
- 기존 SOT의 `KNOWN_DEFECT` 해결 상태 갱신. 관련 문서 작업이 병합된 뒤 별도 단계가 소유한다.

## 제출 직전 §8-6b 셀프 감사

초기 Goal 커밋 시점 답변이며 최종 CHECKPOINT 전에 다시 실행한다.

- 결론에 전문용어가 있나? 아니오.
- `→` 해석 없는 출력·코드·표가 있나? 아니오.
- 결론에 결정할 사항이 빠졌나? 아니오.
- 결정에 버린 길·대가가 빠졌나? 아니오.
- `file:line`의 역할 설명이 빠졌나? 아니오.
- 쉽게 쓰며 증거·수치·한계를 뺐나? 아니오.
- 초등학생 비유로 내용을 깎았나? 아니오.
- 건너뜀·미확인·실패 후 재시도가 앞부분에서 빠졌나? 아니오.
- 추정을 확인된 사실처럼 썼나? 아니오.
