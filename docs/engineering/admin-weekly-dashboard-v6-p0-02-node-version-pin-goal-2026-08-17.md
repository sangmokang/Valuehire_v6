# 관리자 주간 대시보드 v6 실행 버전 고정 goal — 2026-08-17

## 1층 — 결론

이번 작은 작업은 실행에 쓸 버전을 한 파일에 정확히 적는 일만 끝냅니다. 값이 없거나 한 글자라도 다르면 불합격입니다.

다른 설치 설정, 앱 코드, 잠금 파일, 의존성 설치는 하지 않습니다. 이 작업의 끝은 지정 파일 한 줄과 그 한 줄을 직접 확인하는 검사입니다.

## 2층 — 판단 근거

### 현재 사실

- `docs/engineering/admin-weekly-dashboard-v6-atomic-plan-phase0-2026-08-17.md:33`은 이번 작은 작업 이름을 `P0-02-node-version-pin`으로 정합니다.
- `docs/engineering/admin-weekly-dashboard-v6-atomic-plan-phase0-2026-08-17.md:34`는 보이는 결과를 `.node-version`이 정확히 `24.19.0` 한 줄인 상태로 정합니다.
- `docs/engineering/admin-weekly-dashboard-v6-atomic-plan-phase0-2026-08-17.md:38`은 바꿀 수 있는 파일을 `.node-version`, `scripts/verify/check-admin-foundation.sh`, 이 goal 문서로 제한합니다.
- `docs/engineering/admin-weekly-dashboard-v6-replacement-goal-2026-08-16.md:200`은 Node 값을 `24.19.0`으로 고정합니다.
- `docs/engineering/admin-weekly-dashboard-v6-replacement-goal-2026-08-16.md:220`은 루트 `.node-version`에도 같은 값을 고정하라고 정합니다.

### 단일 합격 조건

루트 `.node-version` 파일이 존재하고 내용이 줄바꿈을 포함해 정확히 `24.19.0` 한 줄이어야 합니다. 검사 결과는 확인한 버전 파일 수가 정확히 1개라고 직접 출력해야 하며, 0개를 합격으로 치지 않습니다.

### 비범위

`package.json`, pnpm 설정, workspace 설정, `apps/admin`, 잠금 파일, 다른 작은 작업, 의존성 설치, 메인 작업공간, 외부 서비스 호출은 이 작업에서 건드리지 않습니다.

### 더 쪼갤 수 없는 이유

이 작업은 한 파일의 한 값만 고정합니다. 파일 생성과 그 값 확인을 나누면 제품 변경만 있고 직접 검사가 없거나, 직접 검사만 있고 실제 실행 기준이 없는 반쪽 작업이 됩니다.

### 빨간불과 초록불

빨간불 확인은 `bash scripts/verify/check-admin-foundation.sh node-version`입니다. `.node-version`이 없으므로 같은 명령이 0이 아닌 성적으로 끝나야 합니다.

초록불 확인도 같은 명령입니다. `.node-version`이 정확한 한 줄이면 성적 0으로 끝나야 합니다.

### 고장 주입 확인

제품 작업공간이 아닌 버리는 복사본에서 `.node-version`만 `24.19.1`로 바꿉니다. 그 상태에서 같은 직접 검사가 0이 아닌 성적으로 끝나야 검사가 실제로 값을 보고 있다는 뜻입니다.

### 실제 사용 경로

루트 `.node-version`은 로컬 개발 환경과 서버 검사 환경이 Node 버전을 맞추는 시작 계약입니다. 이번 작업은 그 계약 파일을 만들고, 검사 스크립트가 그 파일 내용을 직접 읽어 확인하게 합니다.

### 종료 조건

목표 문서와 직접 검사만 먼저 남긴 빨간불 기록이 따로 있어야 합니다. 그 뒤 `.node-version` 한 파일만 추가해 초록불을 만들고, 시작·종료 상태, 바뀐 파일 범위, 대상 수 1, 고장 주입 빨간불을 확인하면 멈춥니다.

외부 부작용은 0건이어야 합니다.

## 3층 — 증거 원문

~~~text
parent_ac: AC-01
micro_id: P0-02-node-version-pin
single_observable_result: .node-version이 정확히 24.19.0 한 줄이다
allowed_files: .node-version, scripts/verify/check-admin-foundation.sh, docs/engineering/admin-weekly-dashboard-v6-p0-02-node-version-pin-goal-2026-08-17.md
forbidden_scope: package.json, pnpm, apps/admin, lockfile
red_command: bash scripts/verify/check-admin-foundation.sh node-version
green_command: bash scripts/verify/check-admin-foundation.sh node-version
mutation_method: disposable clone에서 .node-version을 24.19.1로 바꾼다
production_call_path: .node-version -> local/CI runtime bootstrap contract
target_count_method: checked version files=1
cannot_split_reason: 단일 파일의 단일 exact value
external_side_effect_count_expected: 0
~~~

→ 위 값은 Phase 0 계획의 P0-02 행에서 이번 작업에 필요한 항목만 옮긴 것입니다. 이 문서는 그 계약을 넓히지 않고, 같은 명령과 같은 파일 범위만 사용합니다.
