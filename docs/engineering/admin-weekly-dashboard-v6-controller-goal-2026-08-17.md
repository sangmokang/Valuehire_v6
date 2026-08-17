# 관리자 주간 대시보드 v6 야간 실행 — controller goal·원자 계획 후보 — 2026-08-17

## 1층 — 결론

40개 상위 조건은 모두 작업 후보에 연결됐지만, 아직 제품 코드는 한 줄도 만들지 않았습니다. 계획 자체가 독립 감사에서 합격해야 첫 번째 작은 작업을 시작합니다.

현재 안전하게 진행 가능한 첫 경로는 실행 기반을 고정하는 일입니다. 일반 엔지니어 분류, 실제 메일 적재, 실제 계정 읽기, 실제 고객사 업무 쓰기, 시각 동일 판정, 메일 발송은 각각 정본 충돌·정책 미완료·외부 권한·이번 범위 금지 때문에 진행하지 않습니다.

## 2층 — 판단 근거

지정 작업공간·작업 가지·기준 기록은 요청값과 정확히 일치했고 그 작업공간은 깨끗했습니다. 기본 작업공간에는 사용자의 미추적 파일 15개가 있어 계속 읽기 전용으로 둡니다.

source worktree 시작 검사는 기존 실패 1/19를 재현했습니다. 감사용 disposable clone은 2/19였는데, 추가 실패는 clone에 local `main` ref가 없어 배송 검사가 실패한 환경 차이였습니다. source의 같은 검사는 통과하므로 두 baseline을 분리하고 어느 쪽도 전체 합격으로 바꾸지 않습니다.

여섯 명의 새 읽기 전용 조사자가 40개 조건을 서로 겹치지 않게 나눠 조사했습니다. 그 원문은 phase0, phase1, phase2a, phase2b, phase3, auth-security 여섯 atomic-research 문서에 나눠 보존했습니다. 아래 계획은 조사자의 제안을 그대로 믿지 않고, 최소 시작 순서·금지 범위·실제 고장 변조·한 결과 원칙을 controller가 다시 고정한 감사 후보입니다.

### 결정 카드 1 — 계획 감사 전 제품 변경 금지

> **무엇을** — 기준 확인·시작 실패·요구 분해·계획 문서만 남기고 제품 코드는 만들지 않습니다.
> **왜** — 사용자가 계획 누락이나 잘못된 작업 단위가 하나라도 있으면 구현을 금지했습니다.
> **버린 길** — 눈에 띄는 빈 관리자 폴더부터 먼저 만드는 길을 버렸습니다. 계획이 틀리면 첫 변경부터 잘못된 기준이 됩니다.
> **대가** — 실제 화면이나 실행물은 계획 감사 뒤에야 생깁니다.
> **되돌리기** — 이번 계획 후보와 조사 기록만 되돌리면 기준 기록 a02a3da로 돌아갑니다.

### 결정 카드 2 — 최신 분류 지시를 임의 적용하지 않음

> **무엇을** — 일반 엔지니어 분류 작업만 정본 충돌로 막아 둡니다.
> **왜** — 전체 목표는 분류 대기 상태를 요구하고 기타 자동 분류를 금지하지만 최신 지시는 기타로 넣으라고 합니다.
> **버린 길** — 최신 한 문장이나 기존 목표 중 하나를 몰래 우선하는 길을 버렸습니다.
> **대가** — 다른 기반·날짜·데이터 장부 작업은 진행할 수 있지만 이 분류 조건은 끝낼 수 없습니다.
> **되돌리기** — 오너가 목표 문서의 해당 문장을 바꾸거나 최신 지시를 철회하면 새 계획 후보에서 차단을 풉니다.

### 결정 카드 3 — 외부 요청은 모두 0건 유지

> **무엇을** — 실제 메일·일정·고객사 업무·완료 메일을 읽거나 쓰지 않습니다.
> **왜** — 이번 완료 범위는 로컬 중간 산출물이고 같은 지시 안에 외부 쓰기 0건과 완료 메일 요청이 함께 있어 더 안전한 금지 계약을 따릅니다.
> **버린 길** — 제공된 회의 주소나 완료 수신 주소를 이용해 외부 시스템에 접속하는 길을 버렸습니다.
> **대가** — 실제 자료와 완료 메일은 확인되지 않은 상태로 남습니다.
> **되돌리기** — 별도 외부 작업 승인과 필수 정책이 갖춰진 새 작업에서만 실행할 수 있습니다.

## 3층 — 기준과 증거

### 기준점

- source worktree: /Users/kangsangmo/Desktop/Valuehire_v6/worktrees/admin-weekly-dashboard-v6-goal-v2
- expected branch: task/admin-weekly-dashboard-v6-goal-v2
- exact source commit: a02a3da8f36e22997028b0d620de4e7e970f76d8
- origin/main at preflight: 4fdef31fe75c8519091cebe8a6c4cbf5be1893ae
- relation: source is ahead 1, behind 0
- source status before planning: clean
- main status: tracked changes 0, user-owned untracked files 15; untouched
- original request restricted locator: /Users/kangsangmo/.codex/tmp/admin-weekly-plan-audit.wnWRAS/original-user-request.md
- original request sha256: b00f70061c0958bc1c818fb9e74334abb604fc8fe7e9d82e4228fc2c95d7c9da
- locator permissions: owner read-only
- sensitive values in original request: file-only; not copied into repository

### 시작 검사 원문

~~~text
$ bash scripts/session-status.sh
HEAD: a02a3da (ahead 1 / behind 0)
ORIGIN: 4fdef31
RED: 1/19 (acceptance-0-7.sh 제외 — CI 담당)
program result: 0
~~~

→ 지정 기준에서 시작 검사가 정상 종료됐고, 기존 실패 한 건을 숨기지 않았습니다. 19개 중 1개가 실패하므로 전체 저장소는 합격이 아닙니다.

~~~text
$ bash scripts/session-status.sh  # disposable local clone at candidate
RED: 2/19 (acceptance-0-7.sh 제외 — CI 담당)

$ bash scripts/acceptance-0-5.sh  # source worktree
PASS: 0-5 완료

$ bash scripts/acceptance-0-5.sh  # disposable clone
FAIL: origin/main과 local main 불일치 — clone에는 local main ref가 없음
~~~

→ 감사 v1의 2/19는 source 회귀가 아니라 clone topology 차이입니다. 이후 감사는 source baseline 1/19와 clone baseline 2/19를 각각 비교하고, clone의 추가 실패 집합이 acceptance-0-5 한 건인지 확인합니다.

~~~text
$ bash verify.sh
PASS: no secret-pattern match in any tracked file, .env not tracked
program result: 0

$ bash scripts/acceptance-0-2.sh
FAIL: .secret-patterns 없음/빈 파일 — AC 판정 불가
program result: 2
~~~

→ 비밀 스캔 자체는 통과했지만 기존 인수 검사는 필요한 규칙 파일이 없어 판정하지 못했습니다. 이 프로그램에서 2는 합격이 아니라 NOT_RUN입니다. 목표 문서에 적힌 과거의 도달 불가능 객체 8건 사유는 이번 직접 실행에서 재현되지 않았습니다.

### 읽은 정본

- docs/sot/INDEX.md
- docs/sot/coding-principles.md
- docs/sot/hook-contracts.md
- docs/sot/git-workflow.md
- docs/sot/verification-commands.md
- docs/sot/mechanism-registry.yaml
- docs/engineering/admin-weekly-dashboard-v6-replacement-goal-2026-08-16.md 전 1,331줄
- 현재 세션에 주입된 상위 AGENTS 계약
- strict와 codeaudit 실행 계약, Harness 전체 계약

### 정규화 요구 계약

- R01: 위험 등급 L3로 처리하고 전체 제품 또는 배송 완료를 주장하지 않는다.
- R02: 지정 worktree·branch·commit을 직접 확인하고 차이가 있으면 복구하지 않는다.
- R03: main의 tracked·untracked 파일을 수정·삭제·이동·stash하지 않는다.
- R04: 금지된 reset·clean·restore·강제 rebase·amend·force push·강제 worktree 삭제를 하지 않는다.
- R05: SOT 우선순위를 적용하고 충돌은 BLOCKED_SOT_CONFLICT로 기록한다.
- R06: 제품 코드 전에 SOT와 1,331줄 목표 전체를 읽는다.
- R07: session-status를 60초 이하로 폴링하고 세 번의 60초 한계를 넘으면 NOT_RUN_TIMEOUT으로 기록한다.
- R08: 기존 RED를 전체 출력·실패 집합과 함께 보존하며 전체 PASS로 바꾸지 않는다.
- R09: AC-01부터 AC-40까지 전부 micro-AC로 매핑한다.
- R10: 모든 micro는 15개 필수 필드를 가진다.
- R11: 결과·실패 이유·되돌림·기술 경계가 둘이면 더 쪼갠다.
- R12: 하나의 불변식을 만드는 제품 코드와 직접 시험은 같은 micro로 둔다.
- R13: DB 제약과 실제 PostgreSQL 17.11 시험은 같은 micro로 둔다.
- R14: 새 admin acceptance의 script·CI·검증 정본·명부·mutation은 한 묶음으로 둔다.
- R15: 계획은 fresh read-only auditor가 원 요구와 현재 저장소를 직접 대조한다.
- R16: 계획 감사의 누락·오매핑·P0/P1·추가 분할·저장소 불일치가 모두 0이어야 구현한다.
- R17: Phase 0 최소 시작 순서를 바꾸지 않는다.
- R18: controller는 계획·의존 관계·checkpoint만 쓰고 제품 코드는 fresh executor 한 명만 쓴다.
- R19: writer와 auditor는 fork_turns=none이고 한 agent가 한 micro만 처리한다.
- R20: 제품 파일을 동시에 쓰는 agent는 한 명뿐이다.
- R21: 각 micro는 직전 PASS checkpoint에서 새 branch/worktree로 시작한다.
- R22: 각 micro는 지정 이름의 goal 문서를 코드 전에 만든다.
- R23: 기존 구현과 정본 패턴을 먼저 찾는다.
- R24: 요구 부재 때문에 실패하는 직접 시험을 먼저 쓰고 RED 전체 출력을 확인한다.
- R25: RED는 별도 Lore commit으로 남기며 이후 시험을 약화·삭제·skip하지 않는다.
- R26: 잘못된 RED는 amend하지 않고 SUPERSEDED_BAD_RED로 남긴 뒤 새 시도로 시작한다.
- R27: 최소 제품 변경만 GREEN으로 만든다.
- R28: targeted test 뒤 적용 가능한 lint·typecheck·unit·build·admin gate·root verify를 실행한다.
- R29: git diff --check, staged diff, 시작·종료 status, targetCount를 확인한다.
- R30: 폐기 가능한 clone/worktree에서 제품 경로를 고장 내 mutation RED를 확인한다.
- R31: entrypoint부터 output/side effect와 test까지 file:line으로 추적한다.
- R32: candidate commit은 Lore 형식을 따른다.
- R33: targetCount=0, 명령 부재, 실행 불가는 PASS가 아니다.
- R34: 기존 RED가 같아도 micro 결과와 전체 결과를 분리한다.
- R35: DB·동시성은 실제 PostgreSQL 17.11 없이 PASS하지 않는다.
- R36: UI는 실제 Next runtime과 Playwright 없이 PASS하지 않는다.
- R37: connector 합성 시험은 SYNTHETIC_ONLY이며 live 증거 부재는 LIVE_NOT_RUN이다.
- R38: parent 완료 경계와 auth·DB·CI·connector·개인정보·외부쓰기 경계는 Claude 1차와 Codex 재공격을 거친다.
- R39: fresh codeaudit는 base·RED·candidate를 폐기 가능한 clone/worktree에서 직접 재실행한다.
- R40: codeaudit의 구현 확인 외 판정, 중요 P2 이상, 0-target, mutation 실패, 호출경로 단절은 micro FAIL이다.
- R41: 감사 원문·sha256·auditor id·candidate HEAD·시간을 보존한다.
- R42: 민감 감사 원문은 제한 파일에만 두고 저장소에는 가린 사본과 지문만 둔다.
- R43: Phase 0~2와 Phase 3 합성·오프라인·shadow까지만 진행한다.
- R44: Phase 3 live Gmail·Calendar·ClickUp은 LIVE_NOT_RUN이고 Phase 4·5는 실행하지 않는다.
- R45: Phase 경계 full gate·Claude·Codex·codeaudit·노출 검사·파일 범위 검사를 모두 통과해야 다음 의존 Phase로 간다.
- R46: 같은 blocker 세 번, 안전한 문맥 상실, 외부 권한 필요, SOT 충돌이면 해당 의존 경로를 멈춘다.
- R47: push·PR·merge·deploy·live call·ClickUp write·email은 모두 0건으로 유지한다.
- R48: 메일 보관 가능 의사는 확인됐지만 기간·열람권한·삭제 명령 미정이므로 실제 적재는 금지한다.
- R49: 일반 Engineer를 ETC로 넣으라는 최신 지시는 AC-13 정본과 충돌하므로 임의 구현하지 않는다.
- R50: 제공된 회의 링크와 수신 주소는 민감 외부 식별자로 저장소·일반 로그·감사 채팅에 복사하지 않는다.
- R51: 완료 보고는 한국어 3층 구조와 micro별 증거·최종 8개 외부 부작용 수치를 포함한다.

### 계획 전역 규칙

1. 아래 모든 row는 docs/engineering/admin-weekly-dashboard-v6-atomic-research-*-2026-08-17.md의 같은 micro_id 필드 전문과 함께 읽는다. 이 파일의 상태·순서·수정 규칙이 충돌하면 이 파일이 우선한다.
2. 조사 원문의 mutation_method가 fixture만 바꾸는 경우 무효다. 실제 mutation은 폐기 가능한 clone/worktree에서 해당 제품 분기·제약·호출을 제거하거나 반대로 바꿔 직접 시험이 RED가 되게 한다.
3. 조사 원문의 새 acceptance-admin-security/auth 제안은 무효다. 목표가 고정한 foundation, domain, db, connectors, ui 다섯 script만 사용한다.
4. red_command는 RED commit에서 요구 부재 때문에 0이 아닌 성적을 내야 한다. green_command는 candidate HEAD에서 targetCount>0 영수증과 함께 0이어야 한다.
5. Phase 2 DB row는 digest가 고정된 PostgreSQL 17.11 실제 인스턴스가 없으면 NOT_RUN이다.
6. UI row는 local Next runtime과 Playwright 실제 브라우저가 없으면 NOT_RUN이다.
7. 외부 connector row는 이번 실행에서 합성 adapter 호출만 허용하고 network call은 0이다.
8. 모든 row의 external_side_effect_count_expected는 0이며 다르면 FAIL이다.
9. 현재 존재하지 않는 경로는 계획된 target이다. writer는 allowed_files 밖을 수정하면 즉시 중지한다.
10. 모든 기존 dependencies 필드는 docs/engineering/admin-weekly-dashboard-v6-canonical-dependencies-2026-08-17.md가 덮어쓴다. exact prerequisite micro마다 실제 PASS codeaudit SHA-256이 writer CONTRACT에 없으면 BLOCKED다.

### 상태 등록부

| 대상 | 현재 상태 | 이유 | 다음 안전 행동 |
|---|---|---|---|
| P0-01 계획 실행 허가 | BLOCKED_EVIDENCE_AUTHORITY_AND_DIFF | 기존 v2 감사가 누락 요구와 비원자 행을 PASS했고 runner-only 원문 보존도 없으며 전체 기록 공백 검사가 7건 실패한다 | 기존 PASS는 실행 허가가 없다; 증거 권한과 원문 보존·공백 검사 충돌을 분리 해결한 뒤 fresh audit |
| P0-02 Node runtime | BLOCKED_RUNTIME_CONSUMER | `.node-version`은 있으나 현재 실제 Node는 22.19.0이고 local/CI consumer가 미정이다 | runtime consumer를 독립 결정한 뒤 실제 24.19.0 실행 증명 |
| P0-05 이후 TypeScript/Next 경로 | DECISION_REQUIRED_DEPENDENCY | 목표 고정 목록에 @types/react와 @types/react-dom의 exact version이 없음 | 새 P0-01 audit와 P0-02~P0-04A가 독립 PASS여도 의존성 버전 결정 전 package install 금지 |
| AC05-M02 | BLOCKED_EXTERNAL_INPUT | 승인된 연말 경계 예시 2건 없음 | label 없는 NOT_RUN 경로만 구현 가능 |
| AC07-M01~M04 | DECISION_REQUIRED_DEPENDENCY | DOM parser가 필요하지만 고정 의존성 목록에 없음 | 의존성 추가 없이 중지 |
| AC13-M01~M02 | BLOCKED_SOT_CONFLICT | UNCLASSIFIED 계약과 ETC 최신 지시 충돌 | 정본 변경 또는 최신 지시 철회 필요 |
| AC28-M01~M02 | BLOCKED_SOT_CONTRACT_GAP | pii payload table의 exact column/constraint 계약이 목표에 없음 | schema 계약 결정 전 migration 작성 금지 |
| AC20 visual comparison | BLOCKED_UI_REFERENCE/NOT_RUN | 인증된 기준 화면 없음 | 차단 판정과 shadow 골격만 구현 |
| AC23 live purge | SYNTHETIC_ONLY | 실제 보관기간·열람권한·삭제 명령·key provider 미정 | 합성 정책·가짜 저장소 시험만 |
| AC31 | LIVE_NOT_RUN | Gmail 실제 읽기 금지·권한/정책 미완료 | 네 mailbox 합성 receipt와 live 차단만 |
| Phase 4 | NOT_RUN | 외부 쓰기 금지 | 실행하지 않음 |
| Phase 5 | NOT_RUN | 운영 전환 금지·기준 화면 없음 | 실행하지 않음 |
| 완료 메일 | NOT_RUN_EXTERNAL_WRITE | 같은 지시의 email sent=0 계약과 충돌 | 최종 보고에 미발송 명시 |

→ 차단된 행은 합격 수에 넣지 않습니다. 서로 독립인 선행 작업은 마지막 검증 기록에서 계속할 수 있습니다.

공식 Next.js 16 문서는 TypeScript 사용 시 @types/react와 @types/react-dom도 갱신하라고 요구합니다. npm registry 읽기 전용 확인 시 React 19.2.8과 React DOM 19.2.8에는 types/typings 필드가 없었고, 현재 latest는 각각 19.2.18과 19.2.4였습니다. 목표가 exact version을 정하지 않았으므로 이 수치를 자동 채택하지 않습니다.

- https://nextjs.org/docs/app/guides/upgrading/version-16
- https://nextjs.org/docs/app/api-reference/config/typescript

### 40개 상위 조건 매핑

| parent | canonical micro source |
|---|---|
| AC-01 | atomic-plan-phase0 P0-02~P0-12, 별도 P0-03A·P0-04-workspace·P0-04A 포함 |
| AC-02 | atomic-plan-phase0 P0-13~P0-14 |
| AC-03 | atomic-plan-phase0 P0-20~P0-21 |
| AC-04~AC-07, AC-13 | atomic-research-phase1; 상태 등록부와 전역 규칙 적용 |
| AC-08, AC-09, AC-14, AC-15, AC-26~AC-30 | atomic-research-phase2a |
| AC-10~AC-12, AC-17~AC-19, AC-24, AC-25, AC-31 | atomic-research-phase3와 canonical-expansions |
| AC-16, AC-23, AC-33~AC-35, AC-38, AC-40 | atomic-research-phase2b와 canonical-expansions |
| AC-20~AC-22, AC-32, AC-36, AC-37 | atomic-research-auth-security와 canonical-expansions |
| AC-39 | atomic-plan-phase0 P0-15~P0-19 및 P0-22 |
| 전체 | AC-01~AC-40 누락 0 |

→ 조사 원문은 각 row의 15개 필드를 보존하고, controller·expansion·dependency overlay가 실제 순서·차단·mutation·고정 acceptance 이름을 정규화합니다.

### Phase 0 canonical rows

Phase 0의 15개 필드 전체 row 25개는 docs/engineering/admin-weekly-dashboard-v6-atomic-plan-phase0-2026-08-17.md에 분리했습니다. 전체 active micro는 134개입니다. 이 controller goal과 그 파일을 하나의 계획 묶음으로 감사합니다. P0-03A-node-engine-pin은 빠졌던 `engines.node`를 별도로 검증하고, P0-04-root-private와 P0-04-workspace-declaration은 독립 결과로 분리합니다. P0-04A는 고정 canary가 아니라 모든 금지 prefix 아래의 임의 이름 추적 파일을 막는 선행 작업입니다.

### Phase 1~3 canonical corrections

- AC36의 issuer, audience, azp, nonce, state replay, exp, email_verified, hosted domain은 각각 별도 micro로 더 쪼갠다. 연구 원문의 세 묶음은 SUPERSEDED_NON_ATOMIC이다.
- AC36의 비인증 dashboard runtime과 invalid callback/no-session runtime도 별도 micro다. 연구 원문의 AC36-M04는 SUPERSEDED_NON_ATOMIC이다.
- AC37의 Origin, Host, CSRF 누락, CSRF 재사용, 부족 role은 각각 별도 micro다. audit 성공·audit 거부는 각각 유지한다.
- AC38의 ACTIVE 0개, ACTIVE 복수, RETIRED 사용, DESTROYED 사용은 각각 별도 micro다. 연구 원문의 두 묶음은 SUPERSEDED_NON_ATOMIC이다.
- AC22의 inactive user, revoked session, expired session, tampered session token은 각각 별도 micro다. viewer 집계·viewer drilldown·operator audit·owner audit은 유지한다.
- AC17의 FAIL-null과 NOT_RUN-null은 별도 micro다. PARTIAL은 별도 유지한다.
- AC21 tracked secret, tracked mailbox address, raw mail body는 각각 별도 canary micro다. artifact root별 검사는 AC39의 P0-15~P0-19를 재사용하되 AC21 노출 종류 assertion을 별도로 둔다.
- AC31은 네 mailbox ref별 합성 receipt micro 네 개와 exactly-four aggregate micro 하나로 분리한다. live 실행은 별도 LIVE_NOT_RUN row이며 PASS로 세지 않는다.
- AC07 네 row는 dependency 결정 전 모두 BLOCKED이고 Phase 1 parent 완료를 주장하지 않는다.
- AC13 두 row는 SOT 충돌 해결 전 모두 BLOCKED이고 taxonomy production code를 쓰지 않는다.
- 연구 원문의 모든 DB row는 같은 invariant의 migration/production procedure와 PostgreSQL 17.11 integration test를 한 rollback unit으로 유지한다.
- 연구 원문의 모든 UI row는 실제 local Next runtime과 Playwright test를 한 rollback unit으로 유지한다.
- 연구 원문의 모든 connector row는 synthetic adapter call count를 기록하고 live call count 0을 확인한다.

### 의존 관계 요약

아래 그림은 Phase 흐름만 보여 줍니다. 실행 권한을 주는 exact edge와 필수 감사 SHA-256 계약은 docs/engineering/admin-weekly-dashboard-v6-canonical-dependencies-2026-08-17.md만 정본입니다.

~~~text
P0-01
 -> P0-02-node-version-pin(BLOCKED_RUNTIME_CONSUMER)
 -> P0-03-pnpm-version-pin
 -> P0-03A-node-engine-pin
 -> P0-04-root-private
 -> P0-04-workspace-declaration
 -> P0-04A-generated-artifact-ignore
 -> P0-05(BLOCKED) -> P0-06
 -> P0-07 -> P0-08 -> P0-09 -> P0-10 -> P0-11 -> P0-12
 -> P0-13 -> P0-14
 -> P0-15 -> P0-16 -> P0-17 -> P0-18
    -> P0-19(BLOCKED) -----+
    -> P0-20 -> P0-21 ----+-> P0-22
 -> Phase 0 boundary review
 -> Phase 1 domain rows (AC07 dependency blocked, AC13 SOT conflict blocked)
 -> Phase 1 boundary review only when all required rows resolve
 -> Phase 2 PostgreSQL rows
 -> Phase 2 boundary review
 -> Phase 3 synthetic/offline/shadow rows
 -> live connector rows remain LIVE_NOT_RUN
 -> stop before Phase 4/5
~~~

→ 의존 작업은 앞 작업의 독립 감사 지문이 있어야 시작합니다. 차단된 결과에 의존하는 경로는 건너뛰지 않지만, 그 결과와 무관한 마지막 완전 검증 기록에서 시작 가능한 작은 작업은 계속할 수 있습니다.

### 계획 감사 합격 조건

- parent AC distinct count 40
- active micro count 134
- unmapped parent count 0
- mis-mapped requirement count 0
- parent requirement sentence coverage gap count 0
- missing required row field count 0
- P0/P1 finding count 0
- independently splittable canonical micro count 0
- dependency cycle count 0
- repository fact mismatch count 0
- external side effect planned count 0
- forbidden bundle split count 0
- sensitive value copied to repo count 0
- invalidated audit execution permission count 0
- runner-only evidence authority confirmed
- full-chain diff-check violation count 0
- fresh plan auditor verdict PASS

### 계획 감사 v1 rework ledger

| v1 finding | 재공격 판정 | v2 조치 |
|---|---|---|
| disposable clone baseline 2/19가 source 1/19와 다름 | source 재현은 계속 1/19; clone에 local main ref가 없어 acceptance-0-5만 추가 실패 | 두 환경의 실패 집합을 별도 baseline으로 고정 |
| dependency가 산문/range라 DAG 증명 불가 | 구현을 막는 실제 계획 결함 | canonical-dependencies overlay에 active micro 132개 exact 등록, unknown/cycle 0 |
| AC36-M04가 두 runtime 결과를 결합 | 독립 실패 원인 2개라 비원자적 | AC36-M04A와 AC36-M04B로 분할하고 원행 supersede |

→ v1 원문과 SHA-256 metadata는 별도 evidence-only commit에 보존했고 수정하지 않습니다.

### 계획 감사 v2 무효화 ledger

| v2 PASS 결함 | 현재 판정 | 복구 조치 |
|---|---|---|
| 상위 목표의 `engines.node` 작업 누락 | INVALIDATED_REQUIREMENT_GAP | P0-03A-node-engine-pin 별도 행과 exact dependency를 추가 |
| P0-04가 private와 workspace 결과를 결합 | INVALIDATED_NON_ATOMIC | P0-04-root-private와 P0-04-workspace-declaration으로 분리 |
| P0-03 exact 문자열 검사가 끝 개행을 잃음 | INVALIDATED_FALSE_PASS | 계획 mutation에 `pnpm@11.22.0\n` 반례와 Corepack 실제 실행 경로를 고정 |
| P0-04A가 고정 canary 파일명만 확인 | INVALIDATED_FALSE_PASS | 모든 금지 prefix 아래 임의 이름의 tracked file mutation을 고정 |
| auditor 원문을 controller가 직접 보존 | BLOCKED_EVIDENCE_AUTHORITY | BLK-RUNNER-ONLY-AUDIT-EVIDENCE 해결 전 P0-01 PASS 금지 |
| 원문 Markdown 보존과 전체 diff-check 충돌 | BLOCKED_HISTORICAL_EVIDENCE_DIFF_CHECK | BLK-HISTORICAL-EVIDENCE-DIFF-CHECK 해결 전 P0-01 PASS 금지; 원문 덮어쓰기나 전역 검사 약화 금지 |

→ `docs/engineering/admin-weekly-dashboard-v6-plan-audit-v2-invalidation-2026-08-17.md`가 과거 감사의 정확한 지문과 `execution_permission: false`를 보존합니다. 과거 PASS는 실행 허가가 없다.

### 현재 중지선

현재 v2 계획 감사는 무효이며 제품 코드를 쓰지 않습니다. runner-only 증거 권한, 과거 원문과 전체 diff-check의 충돌, Node runtime consumer가 모두 해결되고 fresh plan audit이 PASS인 경우에만 첫 writer packet P0-02를 만들며, exact input commit과 새 plan-audit evidence hash를 고정합니다.

## 감사 전 셀프 확인

- 결론에 전문용어가 있나? 아니오.
- 해석 없는 출력·표·코드 블록이 있나? 아니오.
- 결정할 사항이 빠졌나? 아니오.
- 버린 길·대가가 빠졌나? 아니오.
- 설명 없는 파일 위치가 있나? 아니오.
- 증거·수치·한계를 뺐나? 아니오.
- 내용을 초등학생 수준으로 깎았나? 아니오.
- 건너뛴 것·실패·미확인이 빠졌나? 아니오.
- 확인 안 된 추정을 사실처럼 썼나? 아니오.
