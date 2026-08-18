VERDICT: PASS

# Admin Weekly Dashboard v6 Phase 0 계획 검사기 fresh codeaudit — 2026-08-18

## 1층 — 한 줄 결론

지금 확인된 큰 결함은 0건입니다. 다만 이 검사는 계획의 뜻이 옳다는 승인이나 관리자 제품 개발 허가가 아니며, P0-01은 별도 조건 3개가 해결될 때까지 계속 막혀 있습니다.

push와 PR은 이 문서를 작성한 시점에는 각각 0건입니다. 외부 실행 서버의 실제 결과는 push 뒤에만 확인할 수 있으므로 아직 완료 근거로 세지 않았습니다.

## 먼저 밝히는 실패·재시도·미확인

- Claude 감사 호출 6회 중 5회는 safeguard 1회, 빈 출력·timeout 3회, 첫 줄 형식 위반 1회로 무효였습니다. 여섯 번째 본문만 첫 줄 `VERDICT: PASS`와 file:line·명령·결과·심각도·미확인 목록을 갖춰 유효했습니다.
- 유효 Claude는 P0/P1 0건이라고 했지만 Codex가 실제 false PASS 6건을 재현했습니다. 이 6건은 모두 별도 RED/GREEN 커밋으로 수정됐습니다.
- `git diff --check a02a3da8..HEAD`는 과거 문서 한 파일의 기존 trailing whitespace 7건 때문에 exit 2입니다. 신규 구간 `7c038bea..HEAD`는 0건입니다.
- GitHub 서버의 실제 Actions 결과, branch protection, runner-only audit evidence authority는 아직 확인하지 못했습니다.
- 과거 전체 이력의 질문 횟수는 저장소 문서와 현재 대화 밖을 검색할 권한이 없어 전역 횟수로 말하지 않습니다.

## 판정 수치

- P0: 0
- P1: 0
- P2: 1
- Claude 누락: 6
- Claude 과장: 2
- 최종 mutation: 32/32
- 신규 구간 whitespace 위반: 0
- historical full-chain whitespace blocker: 7

P2 1건은 `scripts/verify/admin-phase0-plan-structural-contract.mjs:217-219`의 JavaScript 정규식 `\Z`입니다. 문자열 끝이 아니라 문자 `Z`로 해석되어 장래 표에 대문자 Z가 들어가면 거짓 실패할 수 있지만, 거짓 통과 방향은 아니어서 이번 수정 규칙에 따라 손대지 않았습니다.

## 2층 — 요구사항·주장 대조표

| ID | 사용자 요구/Claude 주장 | 판정 | 근거 | 반증/공백 | 심각도 |
| --- | --- | --- | --- | --- | --- |
| R1 | 시작 HEAD·branch·clean·ancestry·기존 9커밋 유지 | 구현 확인 | 시작 `4c75940`, branch 일치, base 대비 9개 확인 후 append-only 8커밋 추가 | amend/rebase/squash/reset 0 | 없음 |
| R2 | active inventory를 graph와 독립 재산출 | 구현 확인 | 독립 parser 결과 active 135, graph consumer 135 | 의미 적합성은 별도 | 없음 |
| R3 | 누락·추가·중복 active ID 실패 | 구현 확인 | `scripts/verify/check-admin-phase0-plan.mjs:152-175`, final 32/32 | 없음 | 없음 |
| R4 | unknown dependency·blocker·cycle 실패 | 구현 확인 | evaluator의 graph/blocker 검증과 독립 parser unknown/cycle 0 | 없음 | 없음 |
| R5 | Phase 0 26행·15필드 exact, duplicate field 실패 | 구현 확인 | fixture 26행, checker duplicate mutation, acceptance `phase0Rows=26` | semantic correctness는 별도 | 없음 |
| R6 | 빈 group·duplicate dependency field 실패 | 구현 확인 | `check-admin-phase0-plan.mjs:349-386`, final 32/32 | 없음 | 없음 |
| R7 | CI step이 jobs.verify.steps에 정확히 1회 | 구현 확인 | `.github/workflows/verify.yml:184-186`, evaluator `:516-562` | GitHub 서버 실행은 아직 미확인 | 없음 |
| R8 | 다른 job·주석·if·continue-on-error·오류 무시 우회 차단 | 구현 확인 | evaluator `:175-214`, mutation `:284-467`, workflow SHA pin `:520-522` | 동일 작성자가 workflow+contract+evaluator를 함께 바꾸면 통과 가능 | 없음 |
| R9 | 깨진 baseline을 mutation 성공으로 오인 금지 | 구현 확인 | checker `:469-496`, 독립 공격은 `mutationsCaught=0 mutationsRequired=0`으로 exit 1 | 없음 | 없음 |
| R10 | replacement goal 실제 입력 | 구현 확인 | evaluator replacement goal anchor/AC 검사, 기존 mutation 유지 | 사업 의미는 별도 | 없음 |
| R11 | structural PASS를 semantic PASS·실행 허가로 과장 금지 | 구현 확인 | fixture `:4-5`, evaluator `:282-286`, checker `:519-526` | 동일 작성자 공격도 두 flag 유지 | 없음 |
| R12 | 검사기가 CI production call path에 연결 | 구현 확인 | workflow `:186` → acceptance `:14` → checker `--self-test` | 실제 Actions run은 push 전 미확인 | 없음 |
| R13 | 실제 false PASS만 RED→GREEN 별도 commit | 구현 확인 | RED `61bb92a`, `b4cb6b1`, `6d390ea`, `786c153`; GREEN `199d8eb`, `fbe6067`, `82ed4e6`, `8ce7bfb` | 없음 | 없음 |
| R14 | 기존 26 mutations 보존 | 구현 확인 | mutation name 32개, unique 32개, duplicate 0 | 삭제·skip 0 | 없음 |
| R15 | 전체 검증과 fresh codeaudit P0/P1 0 | 구현 확인 | 아래 검증 장부, 본 판정 P0 0/P1 0 | historical 7건과 P0-01 blocker는 남음 | 없음 |
| R16 | 관리자 제품·P0-01 이후 micro 금지 | 구현 확인 | 변경 파일은 checker/evaluator/fixture와 증거 문서뿐 | 제품 코드 변경 0 | 없음 |
| R17 | 조건 충족 전 push·PR 금지 | 구현 확인 | 본 감사 작성 시 push 0, PR 0 | 증거 commit 뒤에만 수행 가능 | 없음 |

→ 뭘 대조했나: 사용자 요구 17개를 현재 코드·이력·실행 결과와 한 줄씩 대조했습니다.

→ 뭐가 나왔나: checker hardening 범위의 미이행은 0개이고, 외부 CI와 P0-01 권한 조건은 별도 미확인·blocker로 남았습니다.

→ 좋은 소식인가 나쁜 소식인가: push/PR gate에는 좋은 소식이지만 P0-01 실행 허가는 여전히 나쁜 소식입니다.

## 핵심 해설

실제 호출은 `.github/workflows/verify.yml:184-186`의 한 step이 `scripts/acceptance-admin-phase0-plan.sh:14`를 실행하고, 이 스크립트가 checker를 `--self-test`로 호출하는 구조입니다. checker는 정상 bundle을 먼저 검사한 뒤 `scripts/verify/check-admin-phase0-plan.mjs:469-496`에서 mutation 32개를 각각 새 임시 bundle에 적용합니다.

Codex가 찾은 false PASS는 step 문구만 맞아도 실제 실행은 건너뛸 수 있다는 공통 원인이었습니다. job-level 인용 `if`, 주석이 붙은 decoy job, `BASH_ENV`, `pull_request` 삭제, skip된 `needs`, custom shell이 그 여섯 경로였습니다.

최종 방어는 두 층입니다. evaluator는 job/step의 알려진 위험을 직접 검사하고, `scripts/verify/fixtures/admin-phase0-plan-structural-contract.json:1593`이 현재 workflow SHA-256을 보관하며 evaluator `:520-522`가 파일 전체가 달라졌는지 검사합니다. 따라서 아직 열거하지 않은 workflow 단독 변경도 실패합니다.

## 놓친 더 나은 답

Claude는 “13개 공격 전부 확인, P0/P1 0”이라고 결론내기 전에 step parser만 공격하지 말고 실행 여부를 바꾸는 상위 YAML을 함께 공격했어야 합니다. 더 나은 답은 최소한 다음을 포함했어야 합니다.

1. `verify` job 자체의 `if`와 `needs`를 step 뒤에 두는 순서 공격
2. workflow trigger에서 `pull_request`를 제거하는 공격
3. Bash 시작 파일과 custom shell로 명령 본문을 실행하지 않는 공격
4. 알려진 키 목록보다 workflow 전체 hash pin을 선택할지에 대한 결정

개선된 결론은 “현재 후보는 6개 false PASS가 있으므로 FAIL이며, 수정 뒤에도 구조 검사는 의미 승인이나 실행 허가가 아니다”입니다.

## 적대 반박

가장 강한 반론은 “workflow hash를 contract에 넣어도 같은 작성자가 workflow, contract, evaluator의 contract hash를 함께 바꾸면 다시 PASS할 수 있다”입니다. 이 반론은 맞습니다.

최종 HEAD에서 plan·graph·contract ID와 evaluator hash를 함께 바꾼 동일 작성자 공격은 exit 0이었습니다. workflow까지 함께 바꾸려면 contract의 workflow hash와 evaluator의 contract hash도 같이 바꾸면 됩니다. 그러므로 이 장치는 독립 감사 권한이 아니라 review 대상 변경을 한 묶음으로 드러내는 구조 검사입니다.

반박 후에도 남는 결론은 다음과 같습니다. 단독 plan·graph·workflow drift는 모두 fail-closed하고, 동일 작성자 권한 경계는 `semanticAuditRequired=true`, `executionPermission=false`로 공개되어 있습니다. 그래서 checker hardening은 PASS지만 P0-01 실행은 BLOCKED입니다.

## 설계 결정 카드

**무엇을**: `.github/workflows/verify.yml` 전체 SHA-256을 structural contract에 pin했습니다.

**왜**: trigger·needs·shell처럼 새 YAML 키를 하나씩 나열하면 아직 모르는 같은 종류의 우회가 남기 때문입니다.

**버린 대안**: 알려진 위험 키만 정규식으로 계속 추가하는 방식은 누락이 반복돼 버렸습니다.

**대가**: 정상적인 workflow 변경도 contract와 evaluator pin을 함께 갱신하고 다시 감사해야 합니다.

**되돌리는 법**: workflow hash 필드·검사를 제거하고 검증된 YAML parser 기반의 명시적 schema 검사로 교체할 수 있습니다.

## 3층 — 근거 장부

| 주장 | 판정 | 1차 근거 | 근거 강도 | 미확인 |
| --- | --- | --- | --- | --- |
| 정상 구조 기준 | 확인 | acceptance 출력 26/135/32/32/PASS/true/false | 실행 결과 | GitHub 서버 run |
| active/graph 독립 일치 | 확인 | 독립 Node parser 26/135/135, 모든 오류 수 0 | 독립 계산 | 사업 의미 |
| workflow 불변 | 확인 | workflow SHA `dcddcd1f...`, fixture 같은 값, contract SHA `4bd91efd...` | 파일 hash | 동일 작성자 공동 변경 |
| 기존 mutations 보존 | 확인 | name count 32, unique 32, duplicate 0 | 정적+실행 | 없음 |
| 신규 whitespace 없음 | 확인 | `git diff --check 7c038bea..HEAD` exit 0 | Git 실행 | 없음 |
| historical blocker | 확인 | `git diff --check a02a3da8..HEAD` 기존 7건 | Git 실행 | 해결 안 됨 |
| pre-push | 확인 | 18개 검사 exit 0, 설계상 CI 담당 3개 skip | 실행 결과 | 실제 CI |
| 노출 스캔 | 확인 | tracked 125, history blob 705, PII 위반 0 | 실행 결과 | 없음 |
| 제품 구현 없음 | 확인 | `4c75940..HEAD` 변경 코드 파일 3개뿐 | Git diff | 증거 문서는 후속 추가 |

→ 뭘 대조했나: 각 완료 주장을 독립 계산·hash·Git·실행 출력에 연결했습니다.

→ 뭐가 나왔나: 구조 검증 증거는 모두 일치했고, historical 7건과 외부 CI만 완료 근거에서 제외됐습니다.

→ 좋은 소식인가 나쁜 소식인가: checker hardening에는 좋은 소식이지만 전체 Phase 0 착수 판단에는 충분하지 않습니다.

## 반복 질문 조사

- 검색 범위: 현재 대화의 사용자 메시지와 이 branch의 engineering 문서
- 정확히 같은 사용자 요청: 확인된 범위에서 1회
- 의미상 유사한 저장소 감사 기록: 2026-08-17 hardening goal/codeaudit 1세트
- 현재 질문의 전역 순번: 미확인. 보관된 전체 사용자 세션을 검색하지 않았으므로 “몇 번째”라고 단정하지 않습니다.

## 검증 신뢰도와 우선순위

실행한 명령은 syntax 3개, acceptance, 독립 parser, mechanism 25개/registry 4개, pre-push 18개, verify, data exposure, 두 diff-check, session-status, git status입니다. 전부 final code HEAD `8ce7bfbc327be2790790ee335a5185725b25e9e4`에서 실행했습니다.

우선순위는 다음과 같습니다.

1. P0-01의 runner-only audit evidence authority 해결
2. historical full-chain whitespace 7건 해결
3. fresh semantic plan audit PASS 확보
4. P2 `\Z` false-fail parser를 별도 승인된 cleanup에서 수정

위 1~3이 끝나기 전 P0-01은 계속 BLOCKED이며 P0-02나 관리자 제품 구현을 시작하면 안 됩니다.

## 문서 형식 검사

최종 `brief-lint` 결과는 위반 0건입니다. 이 수치는 문서 형식만 증명하며 회사 차원의 합격 근거가 아닙니다.
