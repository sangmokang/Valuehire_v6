VERDICT: PASS

# Admin Weekly Dashboard v6 Phase 0 계획 검사기 fresh codeaudit — 2026-08-17

## 1층 — 결론 — 쉬운 결론

이번 계획 검사기 보강 범위에서는 심각한 미해결 결함을 찾지 못했습니다. 처음 만든 후보에는 서버 검사를 다른 작업으로 옮기거나 조건 키를 다른 순서로 쓰면 통과하는 결함 세 개와, 연결 문서의 중복·빈 항목을 통과시키는 결함 세 개가 있었지만 모두 고치고 재시험했습니다.

다만 이 판정은 계획의 틀이 고정 계약과 같은지만 다룹니다. 계획 내용 전체가 사업 요구에 맞다는 별도 감사, 과거 공백 오류, 다른 검증 도구의 유효 판정 본문이 없으므로 첫 제품 작업을 시작하거나 원격 제출을 완료했다고 판단할 수 없습니다.

앞부분에서 확인하지 못한 것은 세 가지입니다. ※ GitHub 서버에서 실제 실행된 결과, ※ 다른 검증 도구의 유효 본문, ※ 상위 계획 전체의 의미 적합성은 확인하지 못했습니다. Claude 첫 호출은 safeguard로 실패했고 재호출은 빈 출력 상태로 약 2분 뒤 종료했습니다.

## 2층 — 판단 근거

### 감사 모드와 범위

감사 모드는 코드/실행입니다. `276af11c30173412ea7f9b68e578224237a6e2aa`를 검사 대상 후보로 삼아 goal, 상위 replacement goal, Phase 0 계획, canonical dependency overlay, 새 JSON 계약, 계약 evaluator, self-test runner, acceptance, CI workflow, verification SOT, mechanism registry를 대조했습니다.

판정 기준은 구조 계약입니다. 상위 사업 요구의 의미 완전성은 이 검사기의 권한 밖이며, 구조 성공 출력도 `semanticAuditRequired=true`와 `executionPermission=false`를 유지해야 합니다.

### 요구사항·주장 대조표

| ID | 사용자 요구 | 판정 | 근거 | 반증·공백 | 심각도 |
|---|---|---|---|---|---|
| R1 | replacement goal을 실제 입력으로 읽고 Node·pnpm·Phase 0 종료 계약과 parent AC 40개를 확인 | 구현 확인 | `admin-phase0-plan-structural-contract.mjs:5-16`은 입력 파일 목록, `:287-306`은 anchor와 AC 집합을 검사 | 의미 전수 감사는 하지 않음 | 낮음 — 범위가 출력에 공개됨 |
| R2 | 독립 active micro 135개와 graph consumer를 exact-set으로 비교 | 구현 확인 | JSON 계약의 provenance와 active IDs, evaluator `:391-424`의 missing/unexpected/unknown 검사, 독립 parser 135=135 | 같은 작성자가 계약과 evaluator를 함께 바꾸는 권한 경계는 남음 | 중간 — review가 없으면 계약 변경을 승인할 수 있음 |
| R3 | 모든 dependency, 중복 consumer, 중복 field, cycle, 0건을 실패 | 구현 확인 | evaluator `:88-147`, `:391-425`, `:459-480`; 26개 self-test | 별도 YAML parser를 쓰지 않고 고정 문법을 직접 파싱 | 낮음 — 고정 문법 밖 입력은 fail-closed 시험으로 보완 |
| R4 | blocker 선언·edge의 missing, unknown, duplicate, unused를 분리 | 구현 확인 | evaluator `:427-457`; unknown blocker와 declaration/edge 삭제 재시험 | 없음 | 낮음 |
| R5 | Phase 0 26행의 15필드와 duplicate field를 exact 비교 | 구현 확인 | evaluator `:58-85`, `:308-389`; JSON 계약 26행 | 구조 일치가 문장 의미의 정당성을 증명하지 않음 | 낮음 |
| R6 | `jobs.verify.steps` 안의 정확한 무조건 CI step 하나만 인정 | 구현 확인 | evaluator `:175-211`, `:512-551`; workflow `:184-186` | 첫 후보의 job 경계와 첫·quoted key 우회는 수정 뒤 차단 | 낮음 |
| R7 | 성공 문구를 구조 범위로 제한하고 실행 허가를 false로 유지 | 구현 확인 | checker `:440-447`, JSON 계약 `:4-5` | 같은 작성자가 코드까지 바꾸는 행위는 독립 review가 필요 | 중간 — 출력 자체는 제품 시작을 허가하지 않음 |
| R8 | mutation 대상 없음과 baseline 오류를 성공으로 오인하지 않고 최소 18개 반례 유지 | 구현 확인 | checker `:21-33`, `:44-387`, `:389-428`; acceptance `:4-14` | Claude 교차확인은 미실행 | 중간 — Codex 단독 증거만 남음 |
| R9 | pre-push와 기존 보안·노출 게이트를 통과 | 구현 확인 | `bash hooks/pre-push` exit 0, exposure tracked 123/history 606 exit 0 | CI 전용 세 항목은 로컬에서 의도적으로 skip | 낮음 |
| R10 | fresh codeaudit P0/P1 결함 0 | 구현 확인 | 이 감사에서 발견한 여섯 우회를 수정한 `1ca0263`, `276af11`; 수정 후 26/26 | 외부 독립 엔진이 아님 | 중간 — 독립성 부족 때문에 strict 전체 완료는 아님 |

→ 각 요구를 실제 입력, 처리 함수, 출력과 mutation으로 연결했습니다. 구조 구현에는 알려진 높은 심각도 결함이 남지 않았지만, 다른 엔진과 서버 판정이 없어서 전체 작업 완료 권한은 없습니다.

### 핵심 흐름

`scripts/acceptance-admin-phase0-plan.sh:14`는 실제 CI와 pre-push가 부르는 진입점이며 checker의 self-test를 실행합니다. `scripts/verify/check-admin-phase0-plan.mjs:389-428`은 정상 baseline을 먼저 확인한 다음 26개 사본을 하나씩 만들고 지정된 정확한 오류 문자열이 있는지 확인합니다.

계약 evaluator는 replacement goal과 9개 구조 입력을 읽고, JSON 계약 SHA-256부터 확인합니다. 이후 Phase 0 26행, active ID 135개, 전체 dependency·blocker edge, CI의 `verify` job 안 step 하나를 비교합니다. 오류가 하나라도 있으면 checker `:433-442`가 성적 1과 `structuralContract=FAIL`을 냅니다.

정상 후보만 checker `:444-448`의 축소된 성공 문구를 냅니다. 같은 줄에서 의미 재감사 필요와 실행 불허를 계속 출력하므로 구조 성공이 제품 구현 허가로 바뀌지 않습니다.

### 놓친 더 나은 답

초기 GREEN 뒤 바로 완료를 주장했으면 잘못이었습니다. fresh 감사가 다음 여섯 거짓 합격을 추가로 찾았습니다.

1. `verify` job에 steps가 없고 뒤의 decoy job에 원래 steps가 있어도 통과
2. `if`가 step의 첫 key이면 통과
3. `continue-on-error`가 step의 첫 key이면 통과
4. `requires_micro_ids`를 나쁜 값 뒤 좋은 값으로 중복 선언하면 통과
5. `requires_blocker_ids`를 나쁜 값 뒤 좋은 값으로 중복 선언하면 통과
6. consumer 0개인 dependency group이 통과

개선된 답은 “18개가 통과했으니 완료”가 아니라 “독립 공격으로 6개 추가 우회를 찾아 26개 고정 시험으로 늘렸지만, Claude 본문이 없어 strict 전체 상태는 진행 중”이어야 합니다.

### 적대 반박

가장 강한 반론은 JSON 계약과 그 SHA를 검사하는 evaluator를 같은 사람이 함께 고치면 가짜 ID로 바꿔도 구조 검사가 통과한다는 점입니다. 이 반례는 실제로 exit 0을 재현했습니다.

이 반론은 검사기가 독립 승인 권한을 가진다는 주장에는 치명적이지만, 현재 구현은 그런 주장을 하지 않습니다. JSON 계약 변경은 diff에 드러나며 결과는 항상 의미 재감사 필요와 실행 불허를 출력합니다. 따라서 이 반례는 구조 비교 코드의 거짓 실패가 아니라 독립 review가 맡아야 할 남은 권한 경계입니다.

수정된 결론은 다음과 같습니다. 고정된 후보와 고정된 evaluator에서는 구조 변조를 차단하지만, evaluator와 계약을 함께 바꾸는 변경의 정당성은 fresh semantic audit와 runner-only evidence가 승인해야 합니다.

### 설계 결정 카드

**무엇을** — CI parser는 `jobs.verify` 경계를 먼저 고정하고 그 안의 `steps`만 읽습니다.

**왜** — 다음 job의 steps를 읽으면 실제 verify job이 비어도 서버 검사가 연결됐다고 거짓 판정합니다.

**버린 대안** — 파일 전체에서 명령 문자열을 찾는 방식과 첫 `steps:`를 쓰는 방식은 직접 반례에서 exit 0이므로 버렸습니다.

**대가** — 지원하는 workflow 구조가 의도적으로 좁아지며 구조를 바꾸려면 계약과 parser를 함께 검토해야 합니다.

**되돌리는 법** — `1ca0263`의 CI parser와 다섯 mutation만 되돌릴 수 있지만, 그러면 같은 세 우회가 다시 열립니다.

## 3층 — 증거 원문

### 후보와 이력

- base: `7c038bea1025937ff34b5161320d74e9468ac089`
- RED: `ed7c11e85f4c6703502ca1259686b9d6043f36b7`
- initial GREEN: `ab6752a60be001c437381de34f65ab3ea6e814a7`
- first fresh-audit repair: `1ca0263bc10b07393f9a1f9ce7993d4e63a82afe`
- second fresh-audit repair / audited candidate: `276af11c30173412ea7f9b68e578224237a6e2aa`

### 핵심 실행 결과

~~~text
$ bash scripts/acceptance-admin-phase0-plan.sh
PASS: Phase 0 structural contract and CI registration match the pinned candidate
ADMIN_PHASE0_PLAN_CHECK phase0Rows=26 consumers=135 duplicateConsumers=0 unknownDependencies=0 dependencyCycles=0 blockersUnknown=0 mutationsCaught=26 mutationsRequired=26 structuralContract=PASS semanticAuditRequired=true executionPermission=false reason=null
program result: 0

$ independent parser
sourceCounts=26,18,16,21,13,22
superseded=15 replacements=34
independentActive=135 graphConsumers=135
duplicateConsumers=0 unknownDependencies=0 dependencyCycles=0
missing=[] unexpected=[]
program result: 0
~~~

→ 정상 후보에 26개 고장 시험을 적용했고 모두 지정 오류로 실패했습니다. 별도 parser도 dependency overlay를 inventory 근거로 쓰지 않고 135개 exact-set을 확인했습니다. 좋은 소식이지만 의미 감사 증거는 아닙니다.

~~~text
$ post-fix disposable clone attacks
verify-steps-moved-postfix: exit=1, CI verify job must contain steps
quoted-if-first-key-postfix: exit=1, CI Phase 0 plan step must not contain if
duplicate-dependency-field-postfix: exit=1, duplicate dependency field
same-author-boundary-postfix: exit=0, structuralContract=PASS semanticAuditRequired=true executionPermission=false
TEMP_CLONES_CREATED=1
TEMP_CLONES_DELETED=1
~~~

→ 앞의 세 거짓 합격은 수정 뒤 차단됐습니다. 검사기·계약을 함께 바꾸는 동일 작성자 반례는 통과하므로 독립 review 경계를 제거할 수 없습니다.

~~~text
$ bash hooks/pre-push
pre-push: 검사 18개 실행
18개 로컬 대상 ok, CI 담당 3개 skip
program result: 0

$ bash scripts/scan-data-exposure.sh all
PASS: 추적 파일 123개 검사, 위반 0건
PASS: 기록 전량 blob 606개 검사, 크기·경로 위반 0건
PASS: csv/tsv/sql 0개 검사(추적 123개 중), 개인정보 적재 0건
program result: 0
~~~

→ 실제 pre-push 호출 경로와 현재·과거 기록 노출 검사는 통과했습니다. CI 전용 검사와 GitHub branch protection은 확인하지 못했습니다.

### 근거 장부

| 주장 | 판정 | 1차 근거 | 근거 강도 | 미확인 사항 |
|---|---|---|---|---|
| 구조 계약 정상 입력 | 확인 | acceptance 26/26 exit 0 | 강함 | 서버 CI |
| active inventory 독립 산출 | 확인 | 여섯 source parser 135, graph 135 | 강함 | source 문서 의미 적합성 |
| CI production call path | 로컬 확인 | workflow `:184-186`, acceptance `:14`, pre-push exit 0 | 중간 | GitHub 실제 run |
| semantic PASS | 미확인 | 출력이 명시적으로 required=true | 강한 반증 | fresh parent audit |
| P0-01 실행 허가 | 불허 확인 | 출력 false, historical diff exit 2 | 강함 | blocker 해소 없음 |
| Claude 교차검증 | 미실행 | safeguard 1회, 빈 출력 timeout 1회 | 강함 | 유효 Claude 본문 |

→ 구조 검사 자체와 로컬 호출 경로 증거는 강합니다. 의미 적합성, 서버 판정, 다른 엔진 독립성은 확인하지 못했습니다.

### 반복 질문 조사

접근 가능한 현재 대화에서 이 checker hardening 구현 요청은 1회이며, 같은 구현을 완료했다고 검증해 달라는 별도 완전 일치 요청은 0회입니다. 의미상 관련된 적대 감사 요구는 같은 대화에서 여러 번 이어졌지만 하나의 진행 중 작업으로 보았습니다. 외부 대화 보관소는 검색하지 않았으므로 전체 계정 기준 횟수는 미확인입니다.

### 검증 신뢰도와 우선순위

1. 높은 우선순위 — Claude 유효 본문이 없으므로 push와 PR을 하지 않습니다.
2. 높은 우선순위 — historical full-chain diff-check 7건은 그대로 blocker입니다.
3. 높은 우선순위 — parent plan의 fresh semantic audit가 별도로 필요합니다.
4. 중간 우선순위 — runner-only evidence authority를 별도 권한으로 확정해야 합니다.

최종 P0 결함 0개, P1 결함 0개입니다. 동일 작성자 계약 재작성, 외부 Claude 미실행, 역사 공백은 구현 결함이 아니라 공개된 권한·프로세스 blocker로 남겼습니다.

### 외부 부작용

- push: 0
- PR: 0
- merge: 0
- deploy: 0
- Gmail/Calendar/ClickUp live call: 0
- ClickUp write: 0
- email sent: 0
- user files deleted/overwritten: 0
- 이 감사 과정까지 임시 clone 생성·삭제: 5/5
- network read: session-status origin fetch, GitHub issue readback, Claude CLI 2회
- network write: GitHub issue 생성 1건
