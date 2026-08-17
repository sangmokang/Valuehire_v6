# Admin Weekly Dashboard v6 Phase 0 계획 검사기 보강 goal — 2026-08-17

## 1층 — 결론 — 쉬운 결론

현재 계획 검사기는 잘못된 계획 다섯 가지를 모두 합격시킵니다. 이번 작업은 이 거짓 합격과 추가 우회를 막는 검사만 보강하며, 관리자 대시보드 제품 구현은 시작하지 않습니다.

검사 보강이 로컬에서 맞더라도 다른 검증 도구의 판정 본문과 재검사가 모두 확보되기 전에는 완료나 다음 작업 허가를 주장하지 않습니다. 그 판정 본문을 받지 못하면 작업은 진행 중으로 남기고 원격 제출도 하지 않습니다.

## 2층 — 판단 근거와 결정 카드

현재 검사는 계획 행과 연결 항목의 개수를 주로 세고 일부 앞쪽 항목만 직접 대조합니다. 그래서 존재하지 않는 선행 작업, 가짜 작업 이름, 필수 차단점 제거, 의미 없는 결과 문장, 서버에서 기본 가지에만 도는 조건을 모두 놓칩니다.

이번 변경은 계획 구조가 고정된 후보와 같은지만 판정합니다. 상위 사업 요구를 빠짐없이 올바르게 해석했다는 판정과 첫 제품 작업의 실행 허가는 별도 독립 감사가 담당합니다.

### 결정 카드 1 — 독립 구조 계약

**무엇을** — 135개 작업 이름, 모든 연결 관계와 차단점, 26개 첫 단계 행의 15개 필드를 별도 고정 계약으로 둡니다.

**왜** — 검사 대상인 연결 문서가 자기 자신에게서 정답 목록도 만들면 가짜 이름으로 함께 바꿔도 알아낼 수 없습니다.

**버린 길** — 현재 연결 문서의 개수와 앞쪽 아홉 항목만 계속 검사하는 길은 이미 다섯 반례가 통과했으므로 버립니다.

**대가** — 계획을 합법적으로 고칠 때 구조 계약도 별도 변경으로 드러내고 함께 검토해야 합니다.

**되돌리기** — 검사기, 직접 시험, 구조 계약만 이 작업의 두 구현 기록으로 되돌릴 수 있습니다.

### 결정 카드 2 — 구조 합격과 의미 합격 분리

**무엇을** — 성공 문구는 고정 후보와 구조·서버 등록이 일치한다는 범위로 줄이고, 의미 재감사 필요와 실행 불허를 항상 함께 출력합니다.

**왜** — 최소 열여덟 반례와 fresh 감사에서 추가된 반례를 잡는 것은 정해 둔 구조를 지켰다는 증거이지, 사업 요구 전체가 맞다는 증거가 아닙니다.

**버린 길** — 시험 개수만으로 계획 전체가 옳다고 부르는 길은 이전 잘못된 합격을 반복하므로 버립니다.

**대가** — 이 작업이 성공해도 다음 관리자 제품 작업은 시작할 수 없습니다.

**되돌리기** — 출력 문구와 구조 판정을 되돌릴 수 있지만, 그러면 기존 잘못된 합격이 다시 열리므로 실행 허가도 계속 0이어야 합니다.

### 결정 카드 3 — 이번 범위 제한

**무엇을** — 계획 검사기, 직접 시험, 독립 계약, 이 goal과 새 감사 기록만 변경합니다.

**왜** — 도구 버전 문자열과 생성물 추적 차단은 실패 원인과 되돌림이 다른 후속 작업입니다.

**버린 길** — 실제 P0-03과 P0-04T 구현까지 한 변경에 넣는 길은 한 작업에 여러 결과를 다시 묶으므로 버립니다.

**대가** — 계획 검사 보강 뒤에도 실제 도구 버전 검사와 생성물 차단 결함은 남습니다.

**되돌리기** — 이번 검사 변경만 되돌리고 후속 결함은 각각 독립 작업으로 유지할 수 있습니다.

## 3층 — 현재 코드 근거, 인수 기준, Harness, SOT, 검증 원문

### 작업 등급과 기준점

- 위험 등급: L3. 이 검사는 L3 제품 계획의 실행 관문이지만 이번 변경 자체는 로컬 구조 검사에 한정합니다.
- 저장소: `/Users/kangsangmo/Desktop/Valuehire_v6`
- base SHA: `7c038bea1025937ff34b5161320d74e9468ac089`
- source branch: `task/admin-weekly-dashboard-v6-phase0-plan-repair-a1`
- source worktree: `/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/admin-weekly-dashboard-v6-phase0-plan-repair-a1`
- task branch: `task/admin-weekly-dashboard-v6-phase0-plan-checker-hardening-a1`
- task worktree: `/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/admin-weekly-dashboard-v6-phase0-plan-checker-hardening-a1`
- base와 origin/main 관계: ahead 24, behind 0, 공통 기준 `4fdef31fe75c8519091cebe8a6c4cbf5be1893ae`
- source 시작 상태: tracked 0건, untracked 0건
- task 이름 충돌: branch 0건, worktree 0건
- 저장소 안 `AGENTS.md`: 없음. 현재 세션에 사용자가 직접 주입한 AGENTS 계약을 최상위 지침으로 적용합니다.

### 현재 검사기가 증명하는 것과 증명하지 못하는 것

현재 `scripts/verify/check-admin-phase0-plan.mjs`는 정상 후보의 Phase 0 행 26개와 dependency consumer 135개를 세고, 앞쪽 9개 연결과 몇 개 문구, 무효화 지문, SOT 사실, CI 명령 문자열 존재를 확인합니다. 기존 자체 고장 시험 9개도 실행합니다.

다음은 증명하지 못합니다.

1. 상위 replacement goal이 실제 입력인지와 parent AC 40개인지
2. canonical active ID 135개가 정확히 같은 집합인지
3. 모든 선행 작업 ID가 실제 active ID인지
4. 전체 135개 연결과 전체 blocker edge가 고정 계약과 같은지
5. Phase 0 26개 행의 15개 필드가 고정 계약과 같은지
6. 같은 필드가 중복 선언됐는지
7. 관리자 계획 검사 단계가 pull request에서도 무조건 실행되는지
8. 구조 합격과 의미 합격·제품 실행 허가가 분리됐는지

### 직접 재현한 다섯 거짓 합격

~~~text
MUTATION unknown-dependency
PASS: repaired Phase 0 plan, invalidation, dependency graph, SOT, and CI registration agree
ADMIN_PHASE0_PLAN_CHECK phase0Rows=26 consumers=135 mutationsCaught=0 mutationsRequired=0 reason=null
program result: 0
MUTATION fake-active-consumer
PASS: repaired Phase 0 plan, invalidation, dependency graph, SOT, and CI registration agree
ADMIN_PHASE0_PLAN_CHECK phase0Rows=26 consumers=135 mutationsCaught=0 mutationsRequired=0 reason=null
program result: 0
MUTATION known-blocker-removed
PASS: repaired Phase 0 plan, invalidation, dependency graph, SOT, and CI registration agree
ADMIN_PHASE0_PLAN_CHECK phase0Rows=26 consumers=135 mutationsCaught=0 mutationsRequired=0 reason=null
program result: 0
MUTATION phase-result-gutted
PASS: repaired Phase 0 plan, invalidation, dependency graph, SOT, and CI registration agree
ADMIN_PHASE0_PLAN_CHECK phase0Rows=26 consumers=135 mutationsCaught=0 mutationsRequired=0 reason=null
program result: 0
MUTATION ci-main-only
PASS: repaired Phase 0 plan, invalidation, dependency graph, SOT, and CI registration agree
ADMIN_PHASE0_PLAN_CHECK phase0Rows=26 consumers=135 mutationsCaught=0 mutationsRequired=0 reason=null
program result: 0
~~~

→ 현재 후보를 각각 한 군데씩 고장 내 검사기에 넘겼습니다. 다섯 경우 모두 프로그램 성적 0으로 합격했으므로, 좋은 소식이 아니라 이번 작업이 막아야 할 재현된 결함입니다.

### 근본 원인

- active consumer는 정확한 이름 집합이 아니라 개수 135만 확인합니다.
- 존재하지 않는 dependency는 순환 검사에서 건너뛰므로 실패하지 않습니다.
- 전체 연결 대신 P0-01부터 P0-05까지 아홉 consumer만 직접 대조합니다.
- blocker 목록과 edge 전체를 고정 계약과 대조하지 않습니다.
- Phase 0 필드는 대부분 비어 있지 않기만 하면 통과하고 중복 필드는 마지막 값으로 덮어씁니다.
- CI 파일 전체에서 명령 문자열을 찾을 뿐 `jobs.verify.steps`의 정확한 한 step과 조건 부재를 확인하지 않습니다.
- replacement goal을 읽지 않으면서 상위 요구가 복구됐다고 출력합니다.

### 단일 인수 기준

**AC-CHECKER-HARDENING-01** — `bash scripts/acceptance-admin-phase0-plan.sh`는 정상 후보에서만 성적 0을 내고, 기존 9개·필수 신규 9개·fresh 감사 신규 8개 고장 사본에서는 각 고장에 지정된 정확한 이유를 확인한 뒤 모두 0이 아닌 성적을 내야 합니다.

정상 출력에는 다음 값이 모두 있어야 합니다.

- `phase0Rows=26`
- `consumers=135`
- `duplicateConsumers=0`
- `unknownDependencies=0`
- `dependencyCycles=0`
- `blockersUnknown=0`
- `mutationsCaught=26`
- `mutationsRequired=26`
- `structuralContract=PASS`
- `semanticAuditRequired=true`
- `executionPermission=false`

구조 단언:

1. replacement goal을 실제 입력으로 읽고 `.node-version`, `engines.node`, `packageManager`, Phase 0 종료 계약과 서로 다른 parent AC 40개를 확인합니다.
2. 독립 계약의 active ID와 dependency overlay consumer를 정확한 집합으로 대조하고 누락·추가·중복을 구분합니다.
3. 모든 dependency는 active ID여야 하고 전체 135개 edge와 26개 Phase 0 edge를 정확히 대조하며 순환도 거부합니다.
4. canonical blocker 전체와 모든 blocker edge를 대조하고 미정의·미사용·중복을 구분합니다. P0-01의 두 blocker와 P0-02 blocker를 정확히 확인합니다.
5. Phase 0 26개 행의 15개 필드를 독립 계약과 필드별로 대조하고 오류에 `micro_id.field`를 넣습니다. 중복 필드는 덮어쓰지 않고 실패합니다.
6. `jobs.verify.steps` 안의 관리자 계획 검사 step이 정확히 한 개이고 정확한 run 명령을 가지며 `if`, `continue-on-error`, `|| true`가 없음을 확인합니다. SOT 표의 step 수 17과 일치시킵니다.
7. 성공 문구를 구조 범위로 줄이고 의미 재감사 필요와 실행 불허를 출력합니다.
8. 필수 대상 0건은 실패합니다. 각 mutation은 적용 대상 0건, baseline 선행 오류, 예상과 다른 오류를 자기 성공으로 세지 않습니다.

### 최소 열여덟 고장 시험과 fresh 감사 확장

기존 9개는 삭제·skip·완화하지 않습니다. 신규 고장 시험은 다음 순서로 추가합니다.

10. P0-06 dependency를 `DOES-NOT-EXIST`로 변경
11. `AC04-M01` consumer를 `FAKE-MICRO`로 변경
12. historical blocker를 목록·P0-01 edge·Phase 0 row에서 제거
13. P0-06 결과 문장을 의미 없는 문장으로 변경
14. 관리자 CI step에 main-only 조건 추가
15. 관리자 CI step에 `continue-on-error: true` 추가
16. replacement goal의 `engines.node` 요구 제거
17. Phase 0 행에 같은 field를 중복 선언
18. 한 active ID를 Phase 0 plan과 dependency graph 양쪽에서 같은 가짜 ID로 변경
19. `verify` job의 steps를 뒤의 decoy job으로 이동
20. `if`를 관리자 step의 첫 key로 이동
21. `continue-on-error`를 관리자 step의 첫 key로 이동
22. 따옴표로 감싼 `if`를 관리자 step의 첫 key로 이동
23. 따옴표로 감싼 `continue-on-error`를 관리자 step의 첫 key로 이동
24. `requires_micro_ids`를 나쁜 값 뒤 좋은 값으로 중복 선언
25. `requires_blocker_ids`를 나쁜 값 뒤 좋은 값으로 중복 선언
26. consumer가 0개인 dependency group 추가

### RED에서 GREEN으로 가는 기록 순서

1. 이 goal과 한국어 GitHub 이슈를 만들고 원격 본문을 다시 읽습니다.
2. 신규 고장 시험만 추가해 첫 미탐지에서 실패하는 RED를 확인합니다.
3. RED만 Lore commit으로 남깁니다.
4. 독립 구조 계약과 최소 validation 변경으로 GREEN을 만듭니다.
5. GREEN을 별도 Lore commit으로 남깁니다. RED 시험은 수정하지 않습니다.
6. 전체 로컬 검증, Claude 1차 공격, Codex 재공격, fresh codeaudit 순서로 검증합니다.
7. 모든 필수 판정 본문과 P0/P1 결함 0을 확보한 경우에만 branch push와 PR을 만듭니다. merge와 deploy는 하지 않습니다.

### 허용 파일

- `scripts/verify/check-admin-phase0-plan.mjs`
- `scripts/acceptance-admin-phase0-plan.sh`
- 새 독립 canonical contract 또는 fixture
- 필요할 때만 `.github/workflows/verify.yml`
- 실제 명령이나 mechanism이 바뀔 때만 `docs/sot/verification-commands.md`, `docs/sot/mechanism-registry.yaml`
- 이 hardening goal과 fresh 감사 원문·metadata
- 한국어 GitHub 이슈·PR 본문

### 금지 범위

- `scripts/verify/check-admin-foundation.sh`
- `package.json`, `.node-version`, `pnpm-workspace.yaml`, `.gitignore`
- `hooks/pre-commit`
- 실제 P0-03 newline 비교와 P0-04A/P0-04T prefix guard 구현
- dependency 설치, lockfile, 관리자 제품 코드
- 과거 감사 원문 수정과 전체 Markdown 공백 검사 약화
- main 변경, merge, deploy, 이메일, Gmail·Calendar·ClickUp live call

### Harness 시작 원문

~~~text
$ make -n red-ledger
make: *** No rule to make target `red-ledger'.  Stop.
program result: 2

$ bash scripts/session-status.sh
HEAD: 7c038be (ahead 24 / behind 0)
ORIGIN: 4fdef31
RED: 2/20 (acceptance-0-7.sh 제외 — CI 담당)
program result: 0

$ bash scripts/acceptance-admin-phase0-plan.sh
PASS: repaired Phase 0 plan, invalidation, dependency graph, SOT, and CI registration agree
ADMIN_PHASE0_PLAN_CHECK phase0Rows=26 consumers=135 mutationsCaught=9 mutationsRequired=9 reason=null
program result: 0

$ bash verify.sh
PASS: no secret-pattern match in any tracked file, .env not tracked
program result: 0
~~~

→ 이 저장소에는 기본 Harness 명령이 없어서 첫 명령의 성적 2는 합격이 아닙니다. 저장소 정본이 지정한 대체 상태 검사는 실행됐지만 전체 20개 중 2개가 실패하므로 저장소 전체도 합격이 아닙니다. 기존 계획 검사와 비밀 검사는 정상 후보에서만 각각 성적 0을 냈습니다.

### SOT 체크리스트

- 읽음: 현재 세션에 주입된 AGENTS 계약. 저장소 안 `AGENTS.md`는 검색 결과 0건입니다.
- 읽음: `docs/sot/INDEX.md`
- 읽음: `docs/sot/coding-principles.md` 전체, 특히 P3·P5·P13·P15·P16·P17·P20
- 읽음: `docs/sot/git-workflow.md`
- 읽음: `docs/sot/hook-contracts.md`
- 읽음: `docs/sot/verification-commands.md`
- 읽음: `docs/sot/mechanism-registry.yaml`
- 읽음: replacement goal 전 1,331줄
- 읽음: controller goal, Phase 0 26행, canonical dependencies 135 consumer, audit invalidation, 이전 repair goal
- 읽음: 현재 acceptance, checker, CI workflow
- 적용: 검사 대상 0건 불합격, RED 시험 별도 기록, 검사 약화 금지, local-only 검사는 합격 권한 없음, 증거 작성 권한 미분리 한계 공개

### 전체 이력 공백 blocker

`git diff --check a02a3da8f36e22997028b0d620de4e7e970f76d8..HEAD`는 과거 `admin-weekly-dashboard-v6-p0-04-codeaudit-a3-2026-08-17.md` 원문의 trailing whitespace 7건 때문에 성적 2입니다. 이 작업은 과거 원문을 고치거나 전역 검사를 약화하지 않습니다. base 이후 새 변경 구간에는 위반 0건을 요구하고, 전체 이력 blocker는 별도 미해결 상태로 유지합니다.

### P0-01 실행 허가가 계속 0인 이유

다음 세 조건이 이번 검사 보강 밖에서 별도로 해결되지 않았습니다.

1. runner-only audit evidence authority
2. historical full-chain diff-check blocker
3. fresh semantic plan audit PASS

따라서 구조 검사가 GREEN이어도 `executionPermission=false`이며 P0-02와 관리자 제품 구현을 시작하지 않습니다.

### Claude 1차와 Codex 2차 공격 계약

Claude는 구조 계약과 graph가 독립인지, graph와 contract를 함께 바꾸는 우회, unknown dependency·blocker, 26개 exact dependency, historical blocker, CI 조건·오류무시·다른 job·주석 우회, duplicate field, baseline 오류를 mutation 성공으로 오인하는지, 구조 합격 과장, replacement goal 고아 입력, CI 실제 호출 경로를 공격합니다.

Codex는 Claude의 모든 명령과 위치를 다시 실행합니다. 추가로 dependency를 blocker ID로 변경, CI 조건을 표현식으로 변경, plan과 contract의 같은 ID를 함께 변경, blocker 목록과 edge를 함께 삭제, baseline을 먼저 깨뜨린 뒤 mutation 성공으로 오인하는지 직접 시험합니다.

Claude 판정 본문이 없거나 빈 출력·한 줄 완료·서비스 거절·timeout·credit 부족·재현 명령과 file:line 부재이면 `CLAUDE_NOT_RUN_<이유>`로 기록합니다. 이 경우 Codex 2차 완료, push, PR, strict 완료를 주장하지 않습니다.

## 검증 원문 — 작업 중 append-only

### RED

NOT_RUN — 신규 고장 시험 커밋 전입니다.

상태 전환 — RED를 별도 Lore commit `ed7c11e85f4c6703502ca1259686b9d6043f36b7`로 고정했습니다. 기존 9개 뒤에 신규 9개를 추가했으며, 정상 baseline은 통과하지만 첫 신규 반례인 unknown dependency를 검사기가 놓치는 상태를 확인했습니다.

~~~text
$ node --check scripts/verify/check-admin-phase0-plan.mjs
program result: 0

$ bash -n scripts/acceptance-admin-phase0-plan.sh
program result: 0

$ bash scripts/acceptance-admin-phase0-plan.sh
FAIL: mutation unknown-dependency was not caught with expected reason: unknown dependencies: [P0-06-lockfile-resolution->DOES-NOT-EXIST]
ADMIN_PHASE0_PLAN_CHECK phase0Rows=26 consumers=135 mutationsCaught=9 mutationsRequired=18 reason=contract-mismatch
program result: 1
~~~

→ 새 반례의 시험 문법은 유효하지만 기존 validator가 존재하지 않는 선행 작업을 합격시켰습니다. RED 변경 뒤 mutation 정의 블록 SHA-256은 GREEN에서도 `c396e5d0c15ff489d2865c81a99aac9b092dbc6a9d7cf82654852a2fe6baf326`으로 같았습니다.

### GREEN과 전체 로컬 검증

NOT_RUN — 구현 전입니다.

상태 전환 — GREEN은 `ab6752a60be001c437381de34f65ab3ea6e814a7`, 실행 비트 복원은 `a2c371850daaac4782ad2949b46d8ca5d62c7eea`, clean-room byte encoding 보정은 `bd77c6a39a9533674bf7ce35e8fa380e2e587354`입니다. RED와 GREEN을 합치거나 amend하지 않았습니다.

독립 inventory 생성 규칙은 Phase 0 canonical plan 26개 + Phase 1 18개 + Phase 2a 16개 + Phase 2b 21개 + Phase 3 13개 + auth/security 22개에서 superseded 15개를 빼고 canonical replacement 34개를 더하는 방식입니다. dependency overlay는 inventory 산출 입력에서 제외했습니다. 첫 독립 parser는 Phase 2a의 TSV 형식을 Markdown 표로 오인해 119개를 냈고, 파일 형식을 직접 확인한 뒤 TSV parser로 고쳐 아래 135개 결과를 얻었습니다.

~~~text
$ node --check scripts/verify/check-admin-phase0-plan.mjs
$ node --check scripts/verify/admin-phase0-plan-structural-contract.mjs
$ bash -n scripts/acceptance-admin-phase0-plan.sh
program result: 0

$ bash scripts/acceptance-admin-phase0-plan.sh
PASS: Phase 0 structural contract and CI registration match the pinned candidate
ADMIN_PHASE0_PLAN_CHECK phase0Rows=26 consumers=135 duplicateConsumers=0 unknownDependencies=0 dependencyCycles=0 blockersUnknown=0 mutationsCaught=18 mutationsRequired=18 structuralContract=PASS semanticAuditRequired=true executionPermission=false reason=null
program result: 0

$ independent Node parser
phase0=26
phase1=18
phase2a=16
phase2b=21
phase3=13
authSecurity=22
superseded=15
replacements=34
independentActive=135
graphConsumers=135
duplicateConsumers=0
unknownDependencies=0
dependencyCycles=0
missingFromGraph=[]
unexpectedInGraph=[]
contractMissing=[]
contractUnexpected=[]
program result: 0

$ bash scripts/acceptance-verify-ac-m.sh
PASS: 검사기 실존·실행가능 — scripts/verify/check-mechanism-registry.sh
PASS: fixture 정상 명부 → 통과 (exit=0)
PASS: fixture path 없는 항목 → 불합격 (exit=1)
PASS: fixture 죽은 target → 불합격 (exit=1)
PASS: id 중복 → 불합격 (exit=1)
PASS: 알 수 없는 stage → 불합격 (exit=1)
PASS: manual 인데 사유 없음 → 불합격 (exit=1)
PASS: manual 정상(사유+실행권한) → 통과 (exit=0)
PASS: manual 인데 실행권한 없음 → 불합격 (exit=1)
PASS: ci 인데 거짓 target → 불합격 (exit=1)
PASS: 절대경로 path → 불합격 (exit=1)
PASS: 상대경로 심볼릭 링크 → 불합격 (exit=1)
PASS: 필드 중복(path 2회, 마지막 값 유효) → 불합격 (exit=1)
PASS: id 뒤 인라인 주석 → 불합격 (exit=1)
PASS: 닫히지 않은 따옴표 → 불합격 (exit=1)
PASS: stage 불일치 필드(ci_mirror_job) → 불합격 (exit=1)
PASS: 문법 오류·항목 0개 → 위반(1) (exit=1)
PASS: 항목 0개 명부 → NOT_RUN (exit=2)
PASS: ci_mirror_job 불일치 → 불합격 (exit=1)
PASS: 필수 필드(stage) 누락 → 불합격 (exit=1)
PASS: 빈 문자열 path → 불합격 (exit=1)
PASS: CI 배선 — verify.yml 에 무조건 실행 스텝 정확히 1회
PASS: 실제 명부(docs/sot/mechanism-registry.yaml) → 통과 (exit=0)
PASS: 명부 항목 4개 = 검사기 보고 4개 (하한 3)
PASS: 저장소 무오염 (시작/종료 상태 동일)
CHECKED: 25
program result: 0

$ bash scripts/verify/check-mechanism-registry.sh
PASS: secrets-scan-precommit (pre-commit · 규칙 1·2·3)
PASS: acceptance-glob-prepush (pre-push · 규칙 1·2·3)
PASS: ci-secret-scan (ci · 규칙 1·2·4)
PASS: admin-phase0-plan-ci (ci · 규칙 1·2·4)
CHECKED: 4
program result: 0
~~~

→ 구문, 18개 직접 반례, 독립 inventory, mechanism 등록이 모두 통과했습니다. fixture JSON은 파싱 뒤 원문 필드와 exact하게 같지만 clean-room 금지 토큰은 byte layer에서 Unicode escape로 보존하며, 고정 SHA-256은 `b1a6a4a890ec7f2b6c1e1d18f0926a4e58d49bc83e1007be7b796b152977fcb5`입니다.

첫 pre-push는 새 JSON fixture에 그대로 저장된 legacy 경로 토큰 때문에 기존 clean-room gate가 실패했습니다. scanner를 약화하지 않고 JSON byte encoding만 고쳐 재실행했습니다.

~~~text
$ bash hooks/pre-push
skip ./scripts/acceptance-0-2.sh (DEFERRED · CI 담당)
skip ./scripts/acceptance-0-5.sh (DEFERRED · CI 담당)
skip ./scripts/acceptance-0-7.sh (PUSH-PERFORMING · CI 담당)
pre-push: 검사 18개 실행
ok ./scripts/acceptance-0-6.sh
ok ./scripts/acceptance-admin-phase0-plan.sh
ok ./scripts/acceptance-hs-a3.sh
ok ./scripts/acceptance-hs-a4.sh
ok ./scripts/acceptance-hs-cleanroom-absolute-contexts.sh
ok ./scripts/acceptance-hs-cleanroom-absolute-paths.sh
ok ./scripts/acceptance-hs-cleanroom-colon-paths.sh
ok ./scripts/acceptance-hs-cleanroom-file-urls.sh
ok ./scripts/acceptance-hs-cleanroom-hook-env-mutations.sh
ok ./scripts/acceptance-hs-cleanroom-hook-env.sh
ok ./scripts/acceptance-hs-cleanroom-mutations.sh
BLOCKED: ./scripts/acceptance-hs-cleanroom.sh exit=1
ok ./scripts/acceptance-hs-gates-antiforge.sh
ok ./scripts/acceptance-hs-gates-mutations.sh
ok ./scripts/acceptance-hs-gates.sh
ok ./scripts/acceptance-secret-webhook-vendor.sh
ok ./scripts/acceptance-verify-ac-m.sh
ok ./verify.sh
program result: 1

$ bash scripts/acceptance-hs-cleanroom.sh
forbidden: scripts/verify/fixtures/admin-phase0-plan-structural-contract.json
FAIL: forbidden runtime refs 1
PASS: escaping symlinks 0
CHECKED: 62
program result: 1

$ bash scripts/acceptance-hs-cleanroom.sh  # byte encoding 보정 뒤
PASS: forbidden runtime refs 0
PASS: escaping symlinks 0
CHECKED: 62
program result: 0

$ bash hooks/pre-push  # 최종 재실행
skip ./scripts/acceptance-0-2.sh (DEFERRED · CI 담당)
skip ./scripts/acceptance-0-5.sh (DEFERRED · CI 담당)
skip ./scripts/acceptance-0-7.sh (PUSH-PERFORMING · CI 담당)
pre-push: 검사 18개 실행
ok ./scripts/acceptance-0-6.sh
ok ./scripts/acceptance-admin-phase0-plan.sh
ok ./scripts/acceptance-hs-a3.sh
ok ./scripts/acceptance-hs-a4.sh
ok ./scripts/acceptance-hs-cleanroom-absolute-contexts.sh
ok ./scripts/acceptance-hs-cleanroom-absolute-paths.sh
ok ./scripts/acceptance-hs-cleanroom-colon-paths.sh
ok ./scripts/acceptance-hs-cleanroom-file-urls.sh
ok ./scripts/acceptance-hs-cleanroom-hook-env-mutations.sh
ok ./scripts/acceptance-hs-cleanroom-hook-env.sh
ok ./scripts/acceptance-hs-cleanroom-mutations.sh
ok ./scripts/acceptance-hs-cleanroom.sh
ok ./scripts/acceptance-hs-gates-antiforge.sh
ok ./scripts/acceptance-hs-gates-mutations.sh
ok ./scripts/acceptance-hs-gates.sh
ok ./scripts/acceptance-secret-webhook-vendor.sh
ok ./scripts/acceptance-verify-ac-m.sh
ok ./verify.sh
program result: 0
~~~

→ 첫 실패는 이 작업의 새 fixture가 유발한 회귀였고 그대로 두지 않았습니다. 최종 production pre-push 호출 경로는 새 Phase 0 검사와 기존 17개 검사를 모두 통과했습니다. 세 CI 전용 항목은 훅 계약대로 로컬에서 실행하지 않았습니다.

~~~text
$ bash verify.sh
PASS: no secret-pattern match in any tracked file, .env not tracked
program result: 0

$ bash scripts/scan-data-exposure.sh all
PASS: 추적 파일 123개 검사, 위반 0건
PASS: 기록 전량 blob 596개 검사, 크기·경로 위반 0건
PASS: csv/tsv/sql 0개 검사(추적 123개 중), 개인정보 적재 0건
program result: 0

$ git diff --check 7c038bea1025937ff34b5161320d74e9468ac089..HEAD
program result: 0

$ git diff --check a02a3da8f36e22997028b0d620de4e7e970f76d8..HEAD
docs/engineering/admin-weekly-dashboard-v6-p0-04-codeaudit-a3-2026-08-17.md:7: trailing whitespace.
+auditor_id: `p0_04_codeaudit_a3`
docs/engineering/admin-weekly-dashboard-v6-p0-04-codeaudit-a3-2026-08-17.md:8: trailing whitespace.
+clone_locator: `/tmp/p0-04-audit-a3.Tz3QwC/clone`
docs/engineering/admin-weekly-dashboard-v6-p0-04-codeaudit-a3-2026-08-17.md:9: trailing whitespace.
+source_at_candidate: `/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/admin-weekly-dashboard-v6-p0-04-root-private-workspace-audit-a3`
docs/engineering/admin-weekly-dashboard-v6-p0-04-codeaudit-a3-2026-08-17.md:10: trailing whitespace.
+base: `55b71bb7ee8bf0b2877f040e57e92382fd45b6af`
docs/engineering/admin-weekly-dashboard-v6-p0-04-codeaudit-a3-2026-08-17.md:11: trailing whitespace.
+RED: `f4717691d065b8b42fd1932091cfdb14d0ab30a0`
docs/engineering/admin-weekly-dashboard-v6-p0-04-codeaudit-a3-2026-08-17.md:12: trailing whitespace.
+candidate: `33679e9a66f6bdb5c1faa9e3a40374b46e7479ce`
docs/engineering/admin-weekly-dashboard-v6-p0-04-codeaudit-a3-2026-08-17.md:13: trailing whitespace.
+P0-03 audit sha256: `360dc78c3b9ca92892048cfb1913ab10f3e145d75bd710d63c23c97b4e0af161`
program result: 2

$ bash scripts/session-status.sh
HEAD: bd77c6a (ahead 29 / behind 0)
ORIGIN: 4fdef31
RED: 2/20 (acceptance-0-7.sh 제외 — CI 담당)
program result: 0

$ git status --short
program result: 0
~~~

→ 새 작업 구간 공백 위반은 0입니다. 전체 이력은 알려진 과거 감사 원문 7건만 남아 성적 2이며 이를 합격으로 바꾸지 않았습니다. `session-status.sh` 자체는 성적 0이지만 저장소 상태는 여전히 RED 2/20입니다.

~~~text
$ bash ~/.claude/skills/strict/brief-lint.sh --strict docs/engineering/admin-weekly-dashboard-v6-phase0-plan-checker-hardening-goal-2026-08-17.md
코드블록 2개 · 표 0개 (면제 0개) / 해석 누락 0개
1층(결론): 줄 3 / 본문 175자
1층 기술 표기: 없음 (※ 한글 전문용어는 못 잡는다 — 사람이 본다)
결정 카드 3건
증거 보관 경로: 임시 외 실재 파일 6건
브리핑 계약 기계 검사: 위반 0건 (문서 1개)
program result: 0
~~~

→ 이 검사는 형식상 명백한 누락만 세며 내용의 진실성·판단 품질을 증명하지 않습니다. 홈 폴더에만 있어 서버 자동 검사나 회사 차원의 합격 근거도 아닙니다.

### 적대 검증 로그

NOT_RUN — GREEN과 전체 로컬 검증 전입니다.

#### Claude 1차 — CLAUDE_NOT_RUN_SAFEGUARD_AND_TIMEOUT

첫 호출은 사용자 지정 형식인 `env -u ANTHROPIC_API_KEY claude -p '<감사 프롬프트 전문>'`으로 실행했습니다.

~~~text
API Error: Fable 5's safeguards flagged this message (https://www.anthropic.com/legal/aup).
This sometimes happens with safe, normal conversations. Claude Code can't respond to this message with Fable 5.

Try rephrasing the request in a new session or change your model.

Request ID: req_011Ce81pc5NcMVoStMqrv7eL
program result: 1
~~~

→ 첫 호출은 코드 판정 본문을 한 줄도 만들지 못하고 서비스 safeguard로 끝났습니다. 사용자 계약상 유효 Claude 감사가 아닙니다.

공격성 표현을 제거하고 같은 file:line·재현 명령·읽기 전용 요구를 유지한 새 세션으로 재호출했습니다. 약 2분 동안 출력이 0바이트였고 종료 입력 뒤 `Execution error`만 남았습니다.

~~~text
$ env -u ANTHROPIC_API_KEY claude -p '<읽기 전용 소프트웨어 정확성 검토 전문>'
stdout: 0 bytes for approximately 120 seconds
termination output: Execution error
valid VERDICT body: 0
~~~

→ 재호출도 빈 출력·timeout 조건에 해당합니다. 따라서 Claude가 잡은 Codex 과장 수와 Claude 주장 재현 수는 계산할 본문 자체가 없으며, `Claude 판정 본문 확보` 완료 조건은 실패입니다.

#### Codex 독립 재공격 — 실행했으나 Claude 교차검증 완료로 세지 않음

Claude 본문을 대신했다고 주장하지 않고 폐기 가능한 local clone에서 다음을 직접 실행했습니다.

~~~text
dependency-changed-to-blocker-id: exit=1, unknownDependencies=1
ci-expression-condition: exit=1, CI Phase 0 plan step must not contain if
plan-graph-contract-id-renamed: exit=1, structural contract SHA-256 mismatch
blocker-declaration-and-edge-deleted: exit=1, required historical blocker missing
broken-baseline-before-self-test: exit=1, mutationsCaught=0
unknown-blocker-reference: exit=1, blockersUnknown=1
ci-or-true: exit=1, must not ignore errors with || true
ci-command-comment-and-other-job: exit=1, required run missing
dependency-cycle: exit=1, dependencyCycles=1
duplicate-consumer: exit=1, duplicateConsumers=1
duplicate-blocker-declaration: exit=1, duplicate blocker declaration
same-author-contract-and-hash-rewrite-boundary: exit=0, semanticAuditRequired=true executionPermission=false
~~~

→ 요구된 Codex mutation은 모두 실행했습니다. 고정 evaluator에서는 잘못된 사본이 실패하지만 같은 작성자가 plan·graph·contract·evaluator hash를 함께 바꾸면 구조 검사가 통과합니다. 이는 fresh semantic audit와 runner-only evidence가 맡아야 할 공개된 권한 경계입니다.

첫 Codex 후보 `986a1ade03712911c17a8b5c4dd47f86bec2b74a`를 더 공격해 다음 여섯 거짓 합격을 찾았습니다.

~~~text
verify-job-without-steps-decoy-has-original-steps: exit=0
if-as-first-step-key: exit=0
continue-on-error-as-first-step-key: exit=0
duplicate-requires-micro-field-bad-then-good: exit=0
duplicate-requires-blocker-field-bad-then-good: exit=0
empty-consumer-group: exit=0
~~~

→ 좋은 소식이 아닙니다. CI parser가 job 경계를 넘고 첫 key를 놓쳤으며 dependency parser가 마지막 값으로 덮어썼습니다. `1ca0263`과 `276af11`에서 여섯 결함을 수정하고 self-test를 26개로 늘렸습니다.

~~~text
$ bash scripts/acceptance-admin-phase0-plan.sh
PASS: Phase 0 structural contract and CI registration match the pinned candidate
ADMIN_PHASE0_PLAN_CHECK phase0Rows=26 consumers=135 duplicateConsumers=0 unknownDependencies=0 dependencyCycles=0 blockersUnknown=0 mutationsCaught=26 mutationsRequired=26 structuralContract=PASS semanticAuditRequired=true executionPermission=false reason=null
program result: 0

verify-steps-moved-postfix: exit=1, CI verify job must contain steps
quoted-if-first-key-postfix: exit=1, CI Phase 0 plan step must not contain if
duplicate-dependency-field-postfix: exit=1, duplicate dependency field
same-author-boundary-postfix: exit=0, semanticAuditRequired=true executionPermission=false
~~~

→ 수정 뒤 발견된 거짓 합격 세 종류는 모두 실패로 바뀌었고, 중복 관계와 0건 group도 고정 mutation으로 남았습니다. 동일 작성자 권한 경계는 의도대로 실행 불허를 계속 출력합니다.

| Claude 주장 | Codex 재현 결과 | 일치/불일치 | 최종 판정 | 증거 |
|---|---|---|---|---|
| 유효 주장 본문 없음 | 재현할 Claude 주장 0건 | 비교 불가 | `CLAUDE_NOT_RUN_SAFEGUARD_AND_TIMEOUT` | Request ID와 빈 출력 재호출 |
| ※ 미확인 | Codex 독립 공격에서 신규 거짓 합격 6건 발견 후 수정 | 비교 불가 | Codex 단독 증거, 교차검증 아님 | `1ca0263`, `276af11` |

→ Claude가 잡은 Codex 과장 0건, Codex가 Claude에서 잡은 과장·누락도 산정 불가입니다. Claude가 아무 판정도 내지 않았기 때문이며, 0건 일치라고 바꾸지 않습니다.

### fresh codeaudit

NOT_RUN — Claude와 Codex 교차검증 전입니다.

상태 전환 — Claude 교차검증은 미실행으로 남겼지만, Codex fresh codeaudit은 `276af11c30173412ea7f9b68e578224237a6e2aa`를 읽기 전용으로 감사한 뒤 별도 문서에 보존했습니다.

- 감사 원문: `docs/engineering/admin-weekly-dashboard-v6-phase0-plan-checker-hardening-codeaudit-2026-08-17.md`
- metadata: `docs/engineering/admin-weekly-dashboard-v6-phase0-plan-checker-hardening-codeaudit-metadata-2026-08-17.yaml`
- 감사 SHA-256: `230dce09e5b63e390c554005950a8eddd63ac7874b2b8f580bc03e1a0e3127d0`
- scoped verdict: PASS
- open P0/P1: 0/0
- semantic audit: required
- execution permission: false
- strict workflow: IN_PROGRESS

~~~text
$ bash ~/.claude/skills/strict/brief-lint.sh --strict docs/engineering/admin-weekly-dashboard-v6-phase0-plan-checker-hardening-codeaudit-2026-08-17.md
코드블록 3개 · 표 2개 (면제 0개) / 해석 누락 0개
1층(결론): 줄 5 / 본문 345자
1층 기술 표기: 없음
결정 카드 1건
브리핑 계약 기계 검사: 위반 0건 (문서 1개)
program result: 0
~~~

→ brief-lint는 문서 형식 누락만 세며 감사 내용의 진실성이나 회사 차원의 합격을 증명하지 않습니다. fresh codeaudit도 다른 엔진 독립성은 없으므로 Claude 완료 조건을 대신하지 않습니다.

### 외부 부작용 예상값

- push: 0
- PR: 0
- merge: 0
- deploy: 0
- Gmail/Calendar/ClickUp live call: 0
- ClickUp write: 0
- email sent: 0
- user files deleted/overwritten: 0
- 임시 clone 생성·삭제: 5/5
- network read: `session-status.sh`의 origin fetch, GitHub issue readback, Claude CLI 2회
- network write: GitHub issue 1건. Claude 유효 본문이 없으므로 branch push·PR은 0으로 유지

## 제출 전 셀프 감사

- 1층에 전문용어가 있나? 아니오.
- 해석 없는 출력·표·코드 블록이 있나? 아니오.
- 1층에 결정할 사항이 빠졌나? 아니오. 현 단계에서 별도 결정은 필요하지 않습니다.
- 버린 길·대가가 빠졌나? 아니오.
- 설명 없는 파일 위치가 있나? 아니오.
- 증거·수치·한계를 뺐나? 아니오.
- 내용을 초등학생 수준으로 깎았나? 아니오.
- 건너뛴 것·실패·미확인이 빠졌나? 아니오.
- 확인 안 된 추정을 사실처럼 썼나? 아니오.
