VERDICT: INVALIDATED

# Admin Weekly Dashboard v6 계획 감사 v2 무효화 — 2026-08-17

## 1층 — 결론

지난 합격 판정으로 다음 제품 작업을 시작할 수 없습니다. 빠진 요구와 잘못 묶인 작업이 확인되어, 새 독립 검증 전까지 합격한 준비 작업은 0개입니다.

과거 기록은 삭제하거나 덮어쓰지 않았습니다. 당시 기록의 지문을 보존하고 실행 허가만 회수했습니다.

## 2층 — 판단 근거

상위 목표는 실행 환경 버전을 두 설정에 각각 고정하라고 요구했지만, 기존 계획에는 한 설정만 있었습니다. 공개 방지 설정과 작업 폴더 선언도 서로 다른 실패와 되돌림을 가지는데 한 작업에 묶였습니다.

또한 도구 버전 검사는 값 끝의 개행을 잃어 잘못된 문자열을 통과시킬 수 있었고, 자동 생성 파일 검사는 정해진 파일명 다섯 개만 확인해 다른 이름의 실제 추적 파일을 놓쳤습니다.

따라서 기존 감사의 행 수와 연결 관계 계산이 맞더라도 요구 완전성과 검사 신뢰성을 증명하지 못합니다. 현재 계획 후보에는 누락 행과 분리 행을 추가해 active micro count를 132개에서 134개로 고쳤지만, runner-only evidence authority(= 검증 원문을 구현자가 수정할 수 없게 분리하는 권한 장치)가 없으므로 fresh audit 실행 허가는 아직 차단합니다.

### 결정 카드 — 과거 감사 보존과 실행 허가 회수

**무엇을** — 기존 감사 파일은 그대로 보존하고 이 무효화 문서에서 `execution_permission: false`를 선언합니다.

**왜** — 과거 판단의 원문과 현재 판단을 모두 추적할 수 있어야 합니다.

**버린 길** — 기존 PASS 문장을 직접 고치는 방법은 원문 지문을 깨뜨리므로 버렸습니다.

**대가** — 독자는 과거 감사와 이 문서를 함께 읽어야 합니다.

**되돌리기** — 새로운 독립 감사가 누락 0건과 원자성 위반 0건을 증명하고 runner-only 보존까지 갖춘 경우에만 별도 superseding 문서로 실행 허가를 다시 부여합니다.

## 3층 — 무효화 장부

- invalidated_audit_file: docs/engineering/admin-weekly-dashboard-v6-plan-audit-v2-2026-08-17.md
- invalidated_audit_sha256: 15f3e058b891862e0499e88c37666cfd50c6b947dd720dfab311c6464ca9278d
- invalidated_audit_git_blob: 02269301688b15bbc4b2857514585469b2b456d1
- invalidated_metadata_file: docs/engineering/admin-weekly-dashboard-v6-plan-audit-v2-metadata-2026-08-17.md
- invalidated_metadata_sha256: 3441bb58280650cbcd80ea385a4f30dacccc2756bd628d6d20ec15c10c071891
- execution_permission: false
- strict_micro_pass_count: 0
- prior_scaffold_value_confirmed_count: 4
- active_micro_count: 134
- invalidated_micro_ids: P0-01-baseline-and-audited-plan, P0-02-node-version-pin, P0-03-pnpm-version-pin, P0-04-root-private-workspace, P0-04A-generated-artifact-ignore
- blocking_findings: missing engines.node micro, non-atomic P0-04, P0-03 newline false PASS, P0-04A fixed-canary false PASS, runner-only audit evidence authority missing, historical raw Markdown full-chain diff-check violations=7

→ 기존 감사 파일의 현재 바이트를 다시 계산한 지문과 Git 내부 파일 지문을 기록했습니다. 값이 달라지면 이 무효화 문서도 다시 검토해야 하며, 현재 값이 맞더라도 과거 PASS가 되살아나지는 않습니다.

### 현재 통과·차단 수치

| 항목 | 수치 | 의미 |
|---|---:|---|
| 엄격하게 재검증된 준비 작업 | 0/5 | 기존 다섯 합격은 다음 작업의 근거가 아님 |
| 파일값 일부가 확인된 준비 작업 | 4/5 | 설정 존재와 실행 경로 검증은 다른 판단 |
| 복구된 계획 후보의 전체 작업 | 134 | 누락 행 1개와 분리 행 1개가 늘어남 |
| 현재 실행 허가 | 0 | 새 독립 감사 전 제품 작업 금지 |

→ 숫자가 늘어난 것은 구현이 더 끝났다는 뜻이 아닙니다. 빠뜨렸던 일을 계획에 다시 넣어 미완료 범위를 정직하게 센 결과입니다.

### 무효화 사유별 영향

1. `engines.node` 누락 — 상위 목표의 명시 요구가 실행 그래프에 없었습니다.
2. P0-04 비원자 — `private=true`와 workspace discovery가 서로 독립적으로 실패할 수 있습니다.
3. P0-03 false PASS — `pnpm@11.22.0\n`이 Bash command substitution에서 끝 개행을 잃고 정상값처럼 비교됐습니다.
4. P0-04A false PASS — `apps/admin/coverage/actual-report.json` 같은 임의 이름의 추적 파일을 고정 canary 검사와 기존 노출 스캔이 놓쳤습니다.
5. 증거 권한 미분리 — 구현자와 증거 작성자가 같은 권한을 가지므로 원문 보존을 구조적으로 강제하지 못했습니다.
6. 원문과 공백 검사 충돌 — `git diff --check a02a3da..HEAD`가 과거 P0-04 감사 원문 끝 공백 7건으로 성적 2를 냈습니다. 원문을 덮어쓰거나 Markdown 전체 검사를 끄지 않고 별도 해결해야 합니다.

### 실행하지 않은 항목

- Node 24.19.0 실제 runtime bootstrap
- Corepack이 packageManager를 소비하는 경로
- pnpm workspace 실제 발견
- 의존성 설치, lockfile, admin lint/typecheck/test/build/start
- CI 원격 실행
- Gmail, Calendar, ClickUp 연결
- push, PR, merge, deploy, 이메일 발송

→ 이 문서는 계획 합격을 복구한 증거가 아니라, 과거 합격을 사용할 수 없게 만드는 증거입니다. 위 항목은 실행 전까지 PASS로 올리지 않습니다.
