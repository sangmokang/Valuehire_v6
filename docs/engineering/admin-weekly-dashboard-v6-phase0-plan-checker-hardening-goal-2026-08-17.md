# Admin Weekly Dashboard v6 Phase 0 계획 검사기 보강 goal — 2026-08-17

## 1층 — 쉬운 결론

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

**왜** — 열여덟 반례를 잡는 것은 정해 둔 구조를 지켰다는 증거이지, 사업 요구 전체가 맞다는 증거가 아닙니다.

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

**AC-CHECKER-HARDENING-01** — `bash scripts/acceptance-admin-phase0-plan.sh`는 정상 후보에서만 성적 0을 내고, 기존 9개와 신규 9개 고장 사본에서는 각 고장에 지정된 정확한 이유를 확인한 뒤 모두 0이 아닌 성적을 내야 합니다.

정상 출력에는 다음 값이 모두 있어야 합니다.

- `phase0Rows=26`
- `consumers=135`
- `duplicateConsumers=0`
- `unknownDependencies=0`
- `dependencyCycles=0`
- `blockersUnknown=0`
- `mutationsCaught=18`
- `mutationsRequired=18`
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

### 열여덟 고장 시험

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

### GREEN과 전체 로컬 검증

NOT_RUN — 구현 전입니다.

### 적대 검증 로그

NOT_RUN — GREEN과 전체 로컬 검증 전입니다.

### fresh codeaudit

NOT_RUN — Claude와 Codex 교차검증 전입니다.

### 외부 부작용 예상값

- push: 0
- PR: 0
- merge: 0
- deploy: 0
- Gmail/Calendar/ClickUp live call: 0
- ClickUp write: 0
- email sent: 0
- user files deleted/overwritten: 0
- 임시 clone 생성·삭제: 0/0
- network read: `session-status.sh`의 origin fetch와 GitHub issue/PR readback, Claude CLI에 한정
- network write: GitHub issue 1건과 모든 게이트 통과 시 branch push·PR 각 1건까지. merge·deploy·메일은 0

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
