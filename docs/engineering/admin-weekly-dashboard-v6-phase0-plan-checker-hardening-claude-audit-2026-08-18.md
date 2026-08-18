VERDICT: PASS

# HEAD 4c75940e3d1f68d1a1e826d649e287142231cf3e 독립 재감사 결과

기존 감사 결론을 참조하지 않고 폐기용 clone에서 13개 필수 공격을 전부 직접 재실행했습니다. 재현된 P0/P1 결함은 0건이며, 기대값 11개는 정상 baseline 출력에서 전부 일치했습니다. 코드 상태는 감사 대상 후보 `276af11`과 동일하고(HEAD와의 diff는 문서 3건뿐), 아래 P2 결함 1건과 신뢰 경계 1건은 판정을 뒤집지 않습니다.

## 기대값 대조 (정상 baseline)

재현 명령:

~~~
cd /private/tmp/admin-phase0-claude-perm.FuOxlj/clone && bash scripts/acceptance-admin-phase0-plan.sh
~~~

실제 결과 — exit 0:

~~~
PASS: Phase 0 structural contract and CI registration match the pinned candidate
ADMIN_PHASE0_PLAN_CHECK phase0Rows=26 consumers=135 duplicateConsumers=0 unknownDependencies=0 dependencyCycles=0 blockersUnknown=0 mutationsCaught=26 mutationsRequired=26 structuralContract=PASS semanticAuditRequired=true executionPermission=false reason=null
~~~

요구된 11개 기대값(phase0Rows=26 … executionPermission=false)과 전부 일치합니다. 이 출력은 CI production 진입점(`scripts/acceptance-admin-phase0-plan.sh:14` → `node scripts/verify/check-admin-phase0-plan.mjs --self-test`)에서 나온 것입니다.

## 필수 공격 13항 상세

모든 mutation은 `mktemp -d`로 만든 임시 복사본(`/tmp/phase0-audit.XcprKv/c`, 감사 후 삭제)에서만 실행했고 clone 원본은 변경하지 않았습니다. 아래 재현 명령의 공통 준비 블록은 다음과 같으며, 각 항목은 이 블록 뒤에 이어 붙이면 그대로 재현됩니다.

~~~
SRC=/private/tmp/admin-phase0-claude-perm.FuOxlj/clone
WORK=$(mktemp -d /tmp/phase0-audit.XXXXXX)
mkcopy(){ rm -rf "$WORK/c"; mkdir -p "$WORK/c"; (cd "$SRC" && for f in docs/engineering/admin-weekly-dashboard-v6-replacement-goal-2026-08-16.md docs/engineering/admin-weekly-dashboard-v6-atomic-plan-phase0-2026-08-17.md docs/engineering/admin-weekly-dashboard-v6-canonical-dependencies-2026-08-17.md docs/engineering/admin-weekly-dashboard-v6-controller-goal-2026-08-17.md docs/engineering/admin-weekly-dashboard-v6-plan-audit-v2-invalidation-2026-08-17.md docs/engineering/admin-weekly-dashboard-v6-plan-audit-v2-2026-08-17.md docs/sot/verification-commands.md docs/sot/mechanism-registry.yaml .github/workflows/verify.yml package.json scripts/verify/fixtures/admin-phase0-plan-structural-contract.json; do mkdir -p "$WORK/c/$(dirname $f)"; cp "$f" "$WORK/c/$f"; done); }
run(){ node "$SRC/scripts/verify/check-admin-phase0-plan.mjs" "$WORK/c"; echo "exit=$?"; }
~~~

### 1. active inventory의 graph 독립 산출 — 정상

contract fixture(`scripts/verify/fixtures/admin-phase0-plan-structural-contract.json`)의 `activeMicroIds` 135개를 dependency overlay를 입력으로 쓰지 않고 소스 계획 문서 6종에서 제가 직접 재산출했습니다.

재현 명령(clone 루트에서):

~~~
node -e '
const fs=require("fs");
const read=f=>fs.readFileSync(f,"utf8");
function yamlIds(f){return [...read(f).matchAll(/^ *micro_id:\s*(\S+)$/gm)].map(m=>m[1]);}
function tableIds(f){const ids=[];for(const line of read(f).split("\n")){let m=line.match(/^\|\s*AC-\d+\s*\|\s*([A-Za-z0-9-]+)\s*\|/);if(m){ids.push(m[1]);continue;}m=line.match(/^AC-\d+\t([A-Za-z0-9-]+)\t/);if(m)ids.push(m[1]);}return ids;}
const p0=[...read("docs/engineering/admin-weekly-dashboard-v6-atomic-plan-phase0-2026-08-17.md").matchAll(/^  micro_id:\s*(\S+)$/gm)].map(m=>m[1]);
const p1=tableIds("docs/engineering/admin-weekly-dashboard-v6-atomic-research-phase1-2026-08-17.md");
const p2a=tableIds("docs/engineering/admin-weekly-dashboard-v6-atomic-research-phase2a-2026-08-17.md");
const p2b=yamlIds("docs/engineering/admin-weekly-dashboard-v6-atomic-research-phase2b-2026-08-17.md");
const p3=yamlIds("docs/engineering/admin-weekly-dashboard-v6-atomic-research-phase3-2026-08-17.md");
const auth=yamlIds("docs/engineering/admin-weekly-dashboard-v6-atomic-research-auth-security-2026-08-17.md");
const exp=read("docs/engineering/admin-weekly-dashboard-v6-canonical-expansions-2026-08-17.md");
const superseded=[];for(const m of exp.matchAll(/^- supersedes:\s*(.*)$/gm)) for(const id of m[1].split(",").map(s=>s.trim()).filter(Boolean)) superseded.push(id);
const repl=yamlIds("docs/engineering/admin-weekly-dashboard-v6-canonical-expansions-2026-08-17.md");
const supSet=new Set(superseded); const derived=new Set();
for(const id of [...p0,...p1,...p2a,...p2b,...p3,...auth]) if(!supSet.has(id)) derived.add(id);
for(const id of repl) derived.add(id);
console.log("p0",p0.length,"p1",p1.length,"p2a",p2a.length,"p2b",p2b.length,"p3",p3.length,"auth",auth.length,"sup",superseded.length,"repl",repl.length,"derived",derived.size);
const act=new Set(JSON.parse(read("scripts/verify/fixtures/admin-phase0-plan-structural-contract.json")).activeMicroIds);
console.log("missing",[...act].filter(x=>!derived.has(x)));
console.log("extra",[...derived].filter(x=>!act.has(x)));'
~~~

실제 결과 — exit 0: `p0 26 p1 18 p2a 16 p2b 21 p3 13 auth 22 sup 15 repl 34 derived 135`, `missing []`, `extra []`. 26+18+16+21+13+22−15+34=135로 goal 문서(goal-2026-08-17.md:290)의 산출 규칙과 일치하며, contract의 `activeMicroIds`와 exact-set으로 동일합니다. dependency graph(135 consumer, 중복 0), plan 26행, contract phase0Rows 26행의 상호 일치도 별도 독립 parse로 확인했습니다(`graphConsumers 135 unique 135`, `graphEqualsContract true`, `contractPhase0EqualsPlan true`).

### 2. 누락·추가·중복 active ID — 전부 실패 확인 (정상)

- 누락: `mkcopy; perl -0pi -e 's/^  - consumers: \[AC04-M01\]\n    requires_micro_ids: \[[^\]]*\]\n//m' "$WORK/c/docs/engineering/admin-weekly-dashboard-v6-canonical-dependencies-2026-08-17.md"; run` → exit 1, `FAIL: active micro set mismatch: missing=[AC04-M01] unexpected=[]` (`admin-phase0-plan-structural-contract.mjs:401-405`)
- 추가: 가짜 group `TOTALLY-NEW-ID` 삽입 → exit 1, `FAIL: active micro set mismatch: missing=[] unexpected=[TOTALLY-NEW-ID]`
- 중복: `AC04-M01` group 재선언 → exit 1, `FAIL: duplicate dependency consumer: AC04-M01` (`:461-463`)

### 3. 미정의 dependency·blocker — 전부 실패 확인 (정상)

- 미정의 dependency `GHOST-DEP` → exit 1, `FAIL: unknown dependencies: [P0-06-lockfile-resolution->GHOST-DEP]` (`:407-412`)
- 미정의 blocker `BLK-GHOST` → exit 1, `FAIL: unknown blocker dependencies: [P0-02-node-version-pin->BLK-GHOST]` (`:440-446`)
- blocker 선언과 edge 동시 삭제 → exit 1, `FAIL: required blockers missing: [BLK-NODE-RUNTIME-CONSUMER]` + `FAIL: P0-02-node-version-pin blockers must be [BLK-NODE-RUNTIME-CONSUMER], got []` (`:433-435`, `:449-455`)
- 순환 주입(P0-01→P0-02) → exit 1, `FAIL: dependency cycles detected: 1` (`:472-473`)

### 4. Phase 0 26행 × 15필드 exact 대조 — 정상

- 임의 필드 1글자 변경(`cannot_split_reason`에 X 추가) → exit 1, `FAIL: phase contract mismatch: P0-01-baseline-and-audited-plan.cannot_split_reason` (`:375-389`)
- `dependencies` 필드 변경(`P0-03-pnpm-version-pin PASS hash`→`P0-02-node-version-pin PASS hash`) → exit 1, `FAIL: phase contract mismatch: P0-03A-node-engine-pin.dependencies`
- 참고: `validatePhaseContract`(`:380-382`)는 contract 행이 plan에 없으면 `continue`로 건너뛰지만, 26행 개수 강제(`:324`) + unexpected ID 강제(`:387-388`) + graph 소속 강제(`:394-396`)가 조합되어 우회 불가함을 공격 2에서 확인했습니다.

### 5. 중복 필드 — 실패 확인 (정상)

- `micro_id` 중복(WRONG 먼저) → exit 1, `FAIL: duplicate phase field: WRONG.micro_id`
- `single_observable_result`를 나쁜값 뒤 좋은값으로 중복 → exit 1, `FAIL: duplicate phase field: P0-06-lockfile-resolution.single_observable_result` — 마지막 값으로 덮어쓰지 않고 실패합니다(`:74-76`, `:310`).

### 6. 빈 consumer group·중복 dependency 필드 — 실패 확인 (정상)

- `- consumers: []` 삽입 → exit 1, `FAIL: dependency group has zero consumers` (`:100`)
- `requires_micro_ids` 나쁜값→좋은값 2회 선언 → exit 1, `FAIL: duplicate dependency field: P0-06-lockfile-resolution.requires_micro_ids` (`:107-110`) — 첫 값이 유효값으로 유지되어 fail-closed
- 목록 안 같은 ID 중복 → exit 1, `FAIL: duplicate micro dependency: P0-06-lockfile-resolution->P0-05-admin-exact-package-contract` (`:127-136`)

### 7. CI 검사가 jobs.verify.steps에 정확히 1회 — 정상

- 정상 workflow: `.github/workflows/verify.yml:184-186`에 해당 step이 1회 존재하고 `if`/`continue-on-error` 없음. named step 17개 = contract `ci.namedStepCount` 17 = SOT 표 17행(`docs/sot/verification-commands.md:23-42`), regex 직접 실행으로 `rowCount 17` 확인.
- step 제거 → exit 1, `FAIL: CI workflow must include run: bash scripts/acceptance-admin-phase0-plan.sh` + `FAIL: CI named step count must be 17, got 16`
- step 2회 중복 → exit 1, `FAIL: CI Phase 0 plan step count must be 1, got 2` (`:522-523`)

### 8. CI 우회 벡터 — 전부 차단 확인 (정상)

전부 임시 복사본 workflow에 적용 후 `run` 실행:

- decoy job으로 step 이동 → exit 1, `FAIL: CI workflow must include run: ...` — `parseVerifySteps`(`:175-211`)가 `jobs.verify` 경계(`^  verify:` ~ 다음 2칸 들여쓰기 key)를 먼저 고정하므로 decoy job의 step은 세지 않습니다
- run 라인을 주석화하고 `run: echo skipped` 대체 → exit 1 (주석 라인은 `:205`에서 activeLines에서 제외되어 위장 불가)
- `"if"` 인용 첫 key → exit 1, `FAIL: CI Phase 0 plan step must not contain if` (`:530-531`, 인용형 `"if"`/`'if'` 포함 regex)
- `continue-on-error` 첫 key → exit 1 (`:533-534`)
- `if: ${{ false }}` 표현식 → exit 1
- `|| true` 추가 → exit 1, `FAIL: ... must not ignore errors with || true` (`:536-537`)
- `|| :` 같은 변형 → run 문자열 exact 비교(`:527-528`)에 걸려 exit 1, `FAIL: CI workflow must include run: ...` — 문자열 완전일치라서 어떤 run 변형도 통과하지 못합니다

### 9. 깨진 baseline을 mutation 성공으로 오인하지 않음 — 정상

`plan의 micro_id 하나를 BROKEN-ID로 변경 후 node "$SRC/scripts/verify/check-admin-phase0-plan.mjs" --self-test "$WORK/c"` → node exit 1, 출력 `mutationsCaught=0 mutationsRequired=0 structuralContract=FAIL reason=contract-mismatch`. `runSelfTest`(`check-admin-phase0-plan.mjs:389-391`)가 baseline 오류 시 mutation 실행 자체를 하지 않고 baseline 오류만 반환합니다. mutation 대상 문자열 0건은 `replaceOnce`/`replaceExactCount`(`:21-33`)가 throw하여 비정상 종료(fail-closed)합니다.

### 10. replacement goal을 실제 입력으로 읽음 — 정상

- anchor 문장에서 `engines.node` 제거 → exit 1, `FAIL: replacement goal must require engines.node` (`:287-294`)
- 기계 인수 기준 §20에서 AC 1행 삭제 → exit 1, `FAIL: replacement goal parent AC set mismatch: expected=40 actual=39` (`:296-305`)

### 11. 구조 PASS의 과장 없음 — 정상

성공 문구는 "structural contract and CI registration match the pinned candidate"로 한정되고(`check-admin-phase0-plan.mjs:445`), 성공·실패 양쪽 출력 모두 `semanticAuditRequired=true executionPermission=false`를 항상 포함합니다(`:440`, `:447`). contract fixture도 `semanticAuditRequired:true`/`executionPermission:false`를 고정하며 변조 시 `:278-283`에서 실패합니다. codeaudit 문서(`codeaudit-2026-08-17.md:9`, `:19`, `:159`)와 metadata(`codeaudit-metadata-2026-08-17.yaml`: `verdict: PASS`, `semantic_audit_required: true`, `execution_permission: false`, `push_allowed: false`)도 semantic PASS나 실행 허가를 주장하지 않습니다.

### 12. CI production call path에서 검사 누락 없음 — 정상

`verify.yml:186` → `scripts/acceptance-admin-phase0-plan.sh:14` → `check-admin-phase0-plan.mjs --self-test`(baseline validate + 26 mutation 전부). 로컬 pre-push glob(`hooks/pre-push:112`)도 `acceptance-*.sh`를 자동 수집합니다. mechanism registry(`docs/sot/mechanism-registry.yaml:24-30`)의 `admin-phase0-plan-ci` 항목이 target 문자열을 고정하고, CI의 `acceptance-verify-ac-m` step(`verify.yml:180`)이 그 일치를 재검사합니다. 테스트 전용 경로가 CI에서 빠지는 구간은 없습니다.

### 13. 동일 작성자 신뢰 경계 — 재현했으며, 공개된 경계로 인정

plan+graph+contract JSON의 동일 ID를 함께 `P0-06-EVIL-...`로 재작성하고 evaluator 사본의 `expectedContractSha256`(`admin-phase0-plan-structural-contract.mjs:19`)까지 새 해시(`85bb1188...`)로 바꿔 실행 → 공격자 evaluator에서는 exit 0(구조 PASS). 단 동일 사본을 원본 pinned evaluator로 검사하면 exit 1, `FAIL: structural contract SHA-256 does not match the pinned checker contract`. 통과한 경우에도 출력은 `semanticAuditRequired=true executionPermission=false`를 유지합니다. 이 한계는 codeaudit 문서 "적대 반박"(`codeaudit-2026-08-17.md:59-65`)과 goal(`goal-2026-08-17.md:535-538`)에 정확히 그대로 공개되어 있고, 검사기가 독립 승인 권한을 주장하지 않으므로 은폐된 결함이 아니라 문서화된 경계입니다.

## 발견 결함

**P2-1 — JS regex의 `\Z` 오용 (잠재적 취약 파싱, fail-closed)**

- 위치: `scripts/verify/admin-phase0-plan-structural-contract.mjs:214` — `(?=^### |^## |\Z)`
- JavaScript regex에서 `\Z`는 문자열 끝 anchor가 아니라 리터럴 "Z"입니다. 따라서 CI 표 구간 안에 대문자 "Z"가 등장하면 lazy match가 그 지점에서 조기 종료되어 행 수를 과소 계산합니다.
- 실측: `node -e '...(위 SOT regex 직접 실행)...'` → `sectionLen 2089 rowCount 17 containsZbeforeNextHeading false` — 현재 원문에는 "Z"가 없고 다음 `### ` heading이 존재해 정확히 17행이 나옵니다.
- 영향: 발현 시 거짓 실패(FAIL) 방향이므로 우회 경로가 아니며 현재 판정에는 영향 없음. 향후 step 이름에 "Z"가 들어가면 원인 파악이 어려운 오탐이 납니다. 판정 비영향.

## 정상 확인 요약 (증거 무결성)

- contract fixture SHA-256: `b1a6a4a890ec7f2b6c1e1d18f0926a4e58d49bc83e1007be7b796b152977fcb5` = 당시 evaluator pin과 일치
- codeaudit 원문 SHA-256: `230dce09e5b63e390c554005950a8eddd63ac7874b2b8f580bc03e1a0e3127d0` = metadata `audit_sha256` 및 goal 기재값과 일치
- 무효화 지문: `plan-audit-v2-2026-08-17.md`의 실측 SHA-256 `15f3e058...`이 invalidation 문서의 `invalidated_audit_sha256`과 일치
- contract 내부: activeMicroIds 135(중복 0), phase0Rows 26, dependencyGraph 135, blockers 13, parentAcIds 40, anchors 3, `pinnedBaseSha 7c038bea...`
- self-test 소요 약 1초, 26개 임시 사본 생성·삭제 정상

## 확인하지 못한 항목

1. GitHub 서버에서의 실제 CI 실행 결과 — 이 clone은 remote가 없어 서버 판정을 재현할 수 없습니다.
2. Claude 교차검증 유효 본문 — 이전 기록의 `CLAUDE_NOT_RUN_SAFEGUARD_AND_TIMEOUT` 자체는 외부 서비스 이벤트라 재현 불가했습니다.
3. 상위 replacement goal 전체의 의미 적합성 — 검사기와 감사 모두 범위 밖으로 명시했고, 본 감사도 구조 범위만 판정했습니다.
4. 소스 research 문서 6종 내용 자체의 사업적 정당성 — inventory 산출의 산술·집합 일치만 검증했습니다.
5. 홈 폴더 전용 도구 출력 — 저장소 밖 도구라 재실행하지 않았습니다.
6. goal 문서에 기록된 과거 세션 실행 로그의 당시 실측치 — 감사 당시 HEAD에서의 검사기 동작만 독립 재검증했습니다.

## clone 최종 상태

- clone HEAD: `4c75940e3d1f68d1a1e826d649e287142231cf3e` (감사 시작·종료 시 동일)
- `git status --porcelain`: 출력 0건, exit 0 — clean. 모든 mutation은 `/tmp/phase0-audit.*` 임시 복사본에서만 수행 후 삭제했으며 commit/push/PR/merge는 수행하지 않았습니다.
