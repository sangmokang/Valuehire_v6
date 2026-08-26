# 주요 기능 정본 체계화 목표 — 2026-08-21

## 1층 — 결론

현재 저장소의 실제 기능과 계획만 있는 기능을 분리해, 다음 작업자가 한 폴더만 읽어도 현재 능력과
금지 범위를 오판하지 않게 한다. 제품 기능과 저장소 보호 기능을 나누고, 각 기능의 상태·입력·출력·
실패·경계·검증 명령을 구조화된 기준 문서로 고정한다.

이 작업은 운영 연결, 외부 발송, 후보 검색, 배포를 수행하지 않는다. 사용자가 추가로 결정할 사항은
없으며, 코드가 증명하지 못한 기능은 `contract_only` 또는 `not_connected`로 남긴다.

## 2층 — 판단 근거

현재 `docs/sot/INDEX.md`는 코딩 원칙, 훅, Git, 검증 명령, HumanSearch 계약을 파일 단위로 나열하지만
“이 저장소가 지금 무엇을 할 수 있는가”라는 기능 단위 답은 제공하지 않는다. 특히 관리자 대시보드는
실행 코드가 있지만 기능 정본이 날짜가 붙은 `docs/engineering/` 목표 문서에만 있고, HumanSearch
브라우저 계약은 정본이지만 구현 상태가 `NOT_RUN`인 항목을 포함한다. 파일 목록만 읽으면 구현됨과
계획됨을 뒤섞기 쉽다.

기능별 문서는 기존 정본을 복사해 두 번째 기준을 만들지 않는다. 새 폴더는 기능 상태·소유 범위·호출점·
불변조건·검증 방법의 기준이며, 세부 계약은 기존 정본 또는 기계 계약을 정확한 경로로 지정한다.

> **무엇을** — `docs/sot/features/`를 주요 기능의 단일 진입점으로 만들고 기능별 YAML 문서를 둔다.
>
> **왜** — 구현 상태와 금지 범위까지 같은 형식으로 비교하고, 기계로 구조를 읽을 수 있게 하기 위해서다.
>
> **버린 길** — 기존 SOT 본문을 새 YAML에 전부 복제하는 방식은 같은 규칙이 두 곳에서 갈라지므로
> 버린다. 코드 파일 하나당 기능 하나로 나누는 방식도 내부 구조를 제품 기능으로 오인하게 하므로 버린다.
>
> **대가** — 세부 규칙을 확인할 때 기능 문서가 가리키는 기존 정본을 한 번 더 열어야 한다.
>
> **되돌리기** — 이번 변경의 새 폴더와 `docs/sot/INDEX.md` 항목을 함께 되돌리면 된다. 제품 코드와
> 운영 데이터는 바뀌지 않는다.

## 3층 — 계약과 증거

### 위험등급과 세션

- 위험등급: **L3** — `docs/sot/` 수정이고 3개보다 많은 파일을 만든다.
- 기준 커밋: `29ce9dade1d3c88ea6dfccf3ca3d36f06c25ad20`
- 브랜치: `main`
- Strict goal 세션: `01a024af-b115-7921-8dfa-181ed06f981e`
- 시작 작업트리: 사용자가 만든 것으로 간주한 추적되지 않은 `docs/engineering/*.md` 4개가 있으며
  수정·삭제하지 않는다.
- 저장소 최상위 `AGENTS.md`, `CLAUDE.md`: 파일은 없음. 현재 대화에서 사용자가 제공한
  `AGENTS.md` 지시를 최상위 규칙으로 적용한다.

### 회수 범위

직접 읽은 범위:

- 공통 정본: `docs/sot/INDEX.md`, `coding-principles.md`, `principles.yaml`,
  `verification-commands.md`, `hook-contracts.md`, `git-workflow.md`, `mechanism-registry.yaml`
- 기능 정본: `docs/sot/humansearch-l0-surface-contract.md`,
  `docs/sot/humansearch-browser-contract.md`
- 제품 구현: `apps/admin/*`, `contracts/admin-weekly-dashboard/*`,
  `humansearch/src/humansearch/**/*.py`
- 제품 시험: `humansearch/tests/*.py`
- 저장소 보호 호출점: `hooks/*`, `.github/workflows/verify.yml`, `verify.sh`,
  `scripts/*.sh`, `scripts/verify/*.sh`
- 과거 결정: 관리자 주간 대시보드 Phase B/C 목표, HumanSearch L0 목표, SOT 재구성 목표,
  `git log HEAD -- <대상>`, 병합된 PR #16과 #34의 원격 상태
- 보조 기억: `.omx/notepad.md`; `.omx/project-memory.json`은 없음
- 무시된 증거: `.claude/private-reviews/`, `.omx/artifacts/`의 존재와 범위를 회수했다. 후보자·검색
  산출물 내용은 제품 기능 정본의 코드 근거가 아니므로 열람 범위에서 제외했다.

### 현재 상태와 근본 원인

- `apps/admin/app.js:132`는 `/api/dashboard`를 읽어 화면을 그린다. 서버 호출점은
  `humansearch/src/humansearch/admin_weekly_dashboard/shadow_server.py:289`이며 로컬 실행만 제공한다.
- `humansearch/src/humansearch/auth_surface.py:64`는 인증 화면을 다섯 상태로 분류하지만,
  제품 코드의 비시험 호출자는 패키지 공개 경계뿐이다. 배포 소비자는 없다.
- `docs/sot/humansearch-browser-contract.md:350`의 실행 장부에는 실제 포털 접속과 자동화가
  `NOT_RUN`으로 남아 있다. 현재 `HEAD`에는 브라우저 실행 구현이 없다.
- `hooks/pre-commit`, `hooks/pre-push`, `.github/workflows/verify.yml`은 비밀·개인정보·검사 약화·
  시험 실행·판정 귀속을 저장소 전역에서 강제한다.

근본 원인은 기능 상태와 기능 계약의 진입점이 없다는 것이다. 현재 문서 구조는 규칙 파일과 역사 기록을
구분하지만, 구현된 제품 기능·계약만 있는 기능·저장소 보호 기능을 같은 기준으로 찾아볼 수 없다.

### 주요 기능 선정 계약

다음 중 하나를 만족해야 주요 기능으로 분류한다.

1. 사람이 직접 실행하거나 제품 코드가 호출하는 현재 `HEAD`의 진입점이 있다.
2. pre-commit, pre-push, CI 중 하나에서 저장소 전체 변경을 강제하는 결과 단위다. 개별 게이트는
   별도 기능으로 세지 않고 상위 기능의 `surface_coverage`에 정확히 한 번 귀속한다.
3. 다음 구현이 반드시 참조해야 하는 현재 기능 계약이며 기존 SOT가 `NOT_RUN` 경계를 명시한다.

다음은 주요 기능에서 제외한다.

- 날짜가 붙은 `docs/engineering/` 역사 기록 자체
- 시험 fixture, 캐시, worktree, 미병합 브랜치의 코드
- 사용자 데이터와 후보 검색 산출물
- 단독으로 제품 또는 저장소 동작을 소유하지 않는 내부 helper

### T — 구조 계약

`docs/sot/features/catalog.yaml`은 YAML 1.2로 읽을 수 있어야 하며 다음을 고정한다.

```yaml
schema_version: valuehire.feature-catalog/v1
categories: []
status_vocabulary: {}
features:
  - id: string
    category: string
    document: repo-relative-path
    maturity: implemented | contract_only
    availability: local_runtime | library_only | repository_control | not_connected
```

각 기능 문서는 다음 최상위 키를 가져야 한다.

```yaml
schema_version: valuehire.feature-sot/v1
feature:
  id: string
  name: string
  category: string
  maturity: implemented | contract_only
  availability: local_runtime | library_only | repository_control | not_connected
  purpose: string
  authority: {}
  surface_coverage: { tracked_product_files, ci_steps, ci_command_paths, hooks, contract_surfaces }
  entrypoints: []
  inputs: []
  outputs: []
  errors: []
  invariants: []
  boundaries: []
  non_goals: []
  verification: []
  evidence: []
  change_protocol: {}
```

입력은 저장소의 추적 파일과 현재 `HEAD`의 호출 관계다. 출력은 위 구조를 지킨 YAML 문서다. YAML
파싱 실패, 빈 기능 목록, 중복 기능 ID, 존재하지 않는 문서·코드·정본 경로, 알려지지 않은 상태값은
검증 실패다. 미병합 브랜치와 무시된 후보자 자료는 입력에서 제외한다.

### EARS 인수 기준과 counter-AC

#### AC-1 — 분류 완전성

When 기능 카탈로그를 읽으면, 시스템은 제품 경험·자동화 경계·저장소 보증 범주를 제공하고 각 주요
기능을 정확히 한 범주에 배치해야 한다.

- 검증: 카탈로그 구조 검사와 현재 `HEAD` 진입점 역대조
- 기대: 중복 ID 0개, 누락된 선정 대상 0개
- counter-AC: 테스트 파일 수가 많다는 이유로 내부 helper를 주요 제품 기능으로 승격하거나,
  미병합 브랜치의 구현을 현재 기능으로 기록한다.

#### AC-2 — 상태 진실성

When 기능이 코드에 있어도 운영에 연결되지 않았거나 계약만 있으면, 시스템은 각각 `library_only`,
`local_runtime`, `not_connected`, `contract_only`를 구분해 기록해야 한다.

- 검증: 비시험 호출자 검색, CLI/API 호출, 기존 `NOT_RUN` 장부 대조
- 기대: 관리자 대시보드는 로컬 전용, 인증 판정기는 라이브 소비자 없음, 브라우저 자동화는 계약만 존재
- counter-AC: 테스트 통과를 운영 기능 완성으로 기록하거나 문서의 정책 허용을 구현 완료로 기록한다.

#### AC-3 — 정본 단일성

When 세부 기능 규칙에 기존 정본이 있으면, 시스템은 새 문서에 전문을 복제하지 않고 규칙 소유 경로와
충돌 우선순위를 명시해야 한다.

- 검증: `authority`와 `evidence` 경로 존재 검사
- 기대: 기존 HumanSearch 두 정본과 코딩·훅·Git·검증 정본이 계속 단일 소유자
- counter-AC: 같은 결정표나 브라우저 허용 조건을 새 YAML과 기존 Markdown 양쪽에 따로 적는다.

#### AC-4 — 기계 판독과 경로 무결성

When `docs/sot/features/**/*.yaml`을 검사하면, 모든 파일은 YAML로 파싱되고 필수 키와 저장소 상대 경로가
유효해야 한다.

- 검증 명령: goal의 검증 장부에 고정한 Ruby YAML 구조 검사
- 기대: 파싱 파일 수가 카탈로그 1개와 기능 문서 수의 합과 같고 오류 0개
- counter-AC: 빈 파일, 카탈로그만 있고 기능 문서 0개, 존재하지 않는 경로, 중복 ID가 통과한다.

#### AC-5 — 회귀 없는 문서 변경

When 정본 체계화가 끝나면, 시스템은 기존 HumanSearch 시험·정적 검사·원칙 검사·SOT 검사를 그대로
통과해야 한다.

- 검증: `bash scripts/acceptance-principles-check.sh`, `bash scripts/check-docs-sot.sh`,
  `cd humansearch && uv run --no-sync pytest -q && uv run --no-sync ruff check src tests &&
  uv run --no-sync mypy src tests`
- 기대: 모두 종료값 0, 시험 수 0보다 큼
- counter-AC: 새 문서가 실제 코드 상태와 다르지만 YAML 파싱만 되어 합격한다.

#### AC-6 — 데이터 안전

While 기능 정본을 작성하는 동안, 시스템은 후보자 개인정보·자격증명·무시된 증거 본문을 새 문서에
복사하지 않아야 한다.

- 검증: `bash verify.sh`, `bash scripts/scan-data-exposure.sh all`
- 기대: 종료값 0
- counter-AC: 기능 근거를 든다는 이유로 후보자 이메일, 이름, 프로필 HTML, 토큰을 문서에 포함한다.

### Harness 게이트 계획

- Gate 0: 위험등급, 기준 SHA, 현재 작업트리, 과거 SOT·goal·PR·무시된 증거 범위를 회수한다.
- Gate 1: 본 goal의 AC, counter-AC, 구조·입출력·오류·경계 계약을 고정한다.
- Gate 2: 기능 폴더 부재와 구조 검사 실패를 RED로 남긴다. 별도 worktree는 현재 main의 사용자
  미추적 문서를 보존하고 제품 코드와 쓰기 범위가 겹치지 않으므로 만들지 않는다.
- Gate 3: `docs/sot/features/`와 상위 인덱스만 최소 변경한다.
- Gate 3.5: 각 기능의 제품·훅·CI 진입점부터 내부 계약까지 정적 호출 경로를 기록한다.
- Gate 4: YAML 구조, 경로, 기존 제품 시험, 저장소 검사를 실행한다.
- Gate 5: PR·push는 사용자 요청 범위가 아니므로 실행하지 않는다.
- Gate 6: 병합·배포·외부 발송은 실행하지 않는다.

### R2~R5와 적대검증 정조준

- R2: 정상 YAML은 통과하고 필수 키 삭제·중복 ID·없는 경로·빈 기능 목록은 실패하는 임시 고장 사본을
  실행한다. 직접 작성한 검사 스크립트는 500줄 이하를 유지하고 499/500/501 경계를 별도 임시 fixture로
  확인한다.
- R3: 모든 상태 주장은 현재 `HEAD`의 코드·시험·기존 SOT 경로를 근거로 갖고, 미병합 브랜치 반례를
  찾아 현재 기능에서 제외한다.
- R4: 관리자 CLI→서버→API→JS, 인증 공개 패키지→분류 함수, 훅/CI→검사 스크립트 호출 경로를
  증명한다. 시험에서만 호출되는 제품 로직은 `library_only`로 기록한다.
- R5: 파싱만 통과하는 검증이 실제 경로 누락을 잡지 못하면 구조 검사에 경로 존재·ID 대조를 추가한다.
- V1: Claude는 상태 과장, 기존 정본 중복, 누락 기능, 고아 호출, 경계 누락, 가짜 YAML 합격을 공격한다.
- V2: 새 Codex 맥락은 V1의 모든 위치와 명령을 재현하고 V1의 과장·누락을 양방향 공격한다.

### 영향 반경·롤백·데이터 안전

- 영향 반경: 문서 탐색과 다음 구현의 판단 기준. 제품 실행·DB·네트워크·외부 계정에는 영향 없음.
- 롤백: 새 `docs/sot/features/`와 `docs/sot/INDEX.md`의 연결 항목, 본 goal·판정 로그를 같은 변경으로
  되돌린다.
- 데이터 안전 AC: 추적 코드와 공개 계약만 근거로 쓰며 `.claude/private-reviews/`의 후보자 자료와
  실제 자격증명은 문서에 옮기지 않는다.

### 비범위

- 제품 코드, 시험, 훅, CI, 검증 스크립트의 동작 변경
- README의 부트스트랩 문구 교정
- 미병합 worktree·브랜치 기능의 승격
- 실제 브라우저·포털·메일·ClickUp·데이터베이스 접속
- push, PR 생성, 병합, 배포, 외부 발송

## 검증 장부

### Strict 원칙 직접 로드

| 상태 | 시각(KST) | 명령 | 종료값 | 현재 SHA | 전체 출력 위치 |
|---|---|---|---:|---|---|
| PASS | 2026-08-21 23:21:16 | `sed -n '1,999p' docs/sot/coding-principles.md` | 0 | `29ce9da...` | 해당 파일 전체 본문과 동일; SHA-256 `5402cb3f...51dcb` |
| PASS | 2026-08-21 23:21:24 | `sed -n '1,999p' docs/sot/principles.yaml` | 0 | `29ce9da...` | 해당 파일 전체 본문과 동일; SHA-256 `a19b29a...ef22` |
| PASS | 2026-08-21 23:21:29 | `bash scripts/acceptance-principles-check.sh` | 0 | `29ce9da...` | 아래 원문 |

```text
VERDICT: PASS
SOT_LOAD: PASS docs/sot/coding-principles.md
LEDGER_LOAD: PASS docs/sot/principles.yaml
MECHANISMS: PASS 34/34 strict-contract-bindings
WIRING: PASS pre-push=1 ci=1
CHECKED: 34
```

→ 두 정본을 직접 읽었고 원칙 34개, pre-push 배선 1개, CI 배선 1개가 모두 확인됐다.

### RED 기준선

| 상태 | 시각(KST) | 명령 | 종료값 | 현재 SHA |
|---|---|---|---:|---|
| PASS(의도한 실패) | 2026-08-21 23:28:07 | 기능 SOT 부재 계약 probe | 1 | `29ce9da...` |

```text
FAIL: feature SOT YAML files missing (checked=0)
```

→ 구현 전에는 기능 정본이 하나도 없어 AC-1과 AC-2를 만족하지 못했다.

### 기능 SOT 구조·변이·경계

| 상태 | 시각(KST) | 명령 | 종료값 | 현재 SHA |
|---|---|---|---:|---|
| PASS | 2026-08-21 23:40~23:46 | `bash scripts/check-docs-sot.sh` | 0 | `29ce9da...` |
| PASS | 2026-08-21 23:45 | 격리 clone에서 기능 SOT 4종 변이 실행 | 0 | `29ce9da...` |
| PASS | 2026-08-21 23:46 | 499/500/501 직접 작성 코드 경계 probe | 0 | `29ce9da...` |

```text
PASS: feature SOT structure catalog=1 features=6 categories=3 invariants=29 paths=validated
PASS: 주요 기능 카탈로그·기능 문서 구조와 근거 경로 일치
OK: docs/sot 재구성 AC 전부 충족

PASS: normal feature SOT fixture accepted
PASS: mutation missing-purpose rejected (exit=1)
PASS: mutation duplicate-feature-id rejected (exit=1)
PASS: mutation missing-evidence-path rejected (exit=1)
PASS: mutation zero-feature-documents rejected (exit=1)
PASS: direct code line boundary 313<=500
MUTATION_SUITE: PASS

BOUNDARY: requested=499 actual=499 expected=PASS
BOUNDARY: requested=500 actual=500 expected=PASS
BOUNDARY: requested=501 actual=501 expected=FAIL
PASS: scripts/check-docs-sot.sh=313<=500
```

→ 정상 문서는 통과하고 필수 의미·ID·경로·문서 집합이 깨진 네 가지 반례는 모두 종료값 1로
거부됐다. 검사 스크립트는 직접 작성 코드 상한 아래다.

### 제품과 저장소 보증 회귀

| 상태 | 시각(KST) | 명령 | 종료값 | 현재 SHA |
|---|---|---|---:|---|
| PASS | 2026-08-21 23:36:21 | `cd humansearch && uv run --no-sync pytest -q` | 0 | `29ce9da...` |
| PASS | 2026-08-21 23:36:35 | `cd humansearch && uv run --no-sync ruff check src tests` | 0 | `29ce9da...` |
| PASS | 2026-08-21 23:36:43 | `cd humansearch && uv run --no-sync mypy src tests` | 0 | `29ce9da...` |
| PASS | 2026-08-21 23:36 | `bash scripts/acceptance-hs-gates.sh` | 0 | `29ce9da...` |
| PASS | 2026-08-21 23:40 | `bash scripts/acceptance-semantic-mutations.sh` | 0 | `29ce9da...` |
| PASS | 2026-08-21 23:40 | `bash scripts/acceptance-ci-step-integrity.sh` | 0 | `29ce9da...` |
| PASS | 2026-08-21 23:40 | `bash scripts/acceptance-hs-a3.sh` | 0 | `29ce9da...` |
| PASS | 2026-08-21 23:40 | `bash scripts/acceptance-hs-a4.sh` | 0 | `29ce9da...` |
| PASS | 2026-08-21 23:45 | `bash scripts/acceptance-secret-webhook-vendor.sh` | 0 | `29ce9da...` |

```text
64 passed in 8.42s
All checks passed!
Success: no issues found in 15 source files
PASS: HumanSearch gate bundle · ruff=15 files · mypy=15 files · pytest collected/passed=64
VERDICT: PASS  # semantic mutations, 10 checks
VERDICT: PASS  # CI step integrity, 14 checks
CHECKED: 25    # HumanSearch secret/session scanner
CHECKED: 30    # data exposure guard and CI wiring
CHECKED: 32    # webhook/vendor secret scanner
```

→ 제품 시험 64개와 현재 정본이 소유권을 위임한 저장소 보증 장치가 모두 회귀 없이 통과했다.
존재하지 않는 `scripts/acceptance-secret-webhook.sh`를 한 번 잘못 호출한 실행은 종료값 127의
`NOT_RUN`으로 분리했고, 실제 저장소 명령 `acceptance-secret-webhook-vendor.sh`로 교정해 통과했다.

### 데이터 안전과 diff 위생

| 상태 | 시각(KST) | 명령 | 종료값 | 현재 SHA |
|---|---|---|---:|---|
| PASS | 2026-08-21 23:36 | 새 파일을 임시 clone의 index에 올린 뒤 `SECRET_PATTERNS_FILE= VERIFY_SCAN_SOURCE=index bash verify.sh` | 0 | `29ce9da...` |
| PASS | 2026-08-21 23:36 | 같은 임시 index에서 `bash scripts/scan-data-exposure.sh tracked` | 0 | `29ce9da...` |
| PASS | 2026-08-21 23:40~23:46 | `bash scripts/scan-data-exposure.sh all` | 0 | `29ce9da...` |
| PASS | 2026-08-21 23:40 | `git diff --check` | 0 | `29ce9da...` |

```text
PASS: no secret-pattern match in any tracked file, .env not tracked
PASS: 추적 파일 185개 검사, 위반 0건
PASS: 추적 파일 176개 검사, 위반 0건
PASS: 기록 전량 blob 1069개 검사, 크기·경로 위반 0건
PASS: csv/tsv/sql 0개 검사(추적 176개 중), 개인정보 적재 0건
```

→ 원래 작업트리에서 새 파일은 미추적이므로 `verify.sh`의 기본 tracked 스캔만으로 합격을 주장하지
않고, 격리 clone의 index에 이번 변경만 올린 뒤 새 문서까지 포함해 다시 검사했다.

## 적대 검증 로그

### V1-A — Claude 최초 실행

| 상태 | 시각(KST) | 실행 신원 | 세션 | 종료값 | 현재 SHA |
|---|---|---|---|---:|---|
| NOT_RUN(판정 미출력·시간 초과) | 2026-08-21 23:49 ~ 2026-08-22 00:02 | Claude Code 2.1.238, `ANTHROPIC_API_KEY=UNSET` | `16386487-c0ec-4f4b-b37b-e6382ebd381e` | 130 | `29ce9da...` |

호출은 `env -u ANTHROPIC_API_KEY claude --session-id <위 세션> --no-session-persistence
--permission-mode dontAsk --tools 'Bash,Read,Grep,Glob' --effort high -p <V1 프롬프트>`였다.

```text
CLAUDE_CLI_VERSION=2.1.238 (Claude Code)
CLAUDE_SESSION_ID=16386487-c0ec-4f4b-b37b-e6382ebd381e
ANTHROPIC_API_KEY=UNSET
BEFORE_STATUS_SHA256=f59d0b01c14f368b459e34038de733eb78149f4bc4b6083a22290520b9309ede
BEFORE_ARTIFACTS_SHA256=65825c7f1c6aae8463a31b760fb174b07f8e3db7cd63edc7a29083d28269b19a
Execution error
AFTER_STATUS_SHA256=f59d0b01c14f368b459e34038de733eb78149f4bc4b6083a22290520b9309ede
AFTER_ARTIFACTS_SHA256=65825c7f1c6aae8463a31b760fb174b07f8e3db7cd63edc7a29083d28269b19a
```

→ 13분 동안 판정문을 전혀 출력하지 않아 강제 종료했다. 검증 전후 상태와 산출물 해시는 같아
읽기 전용 조건은 지켰지만 판정이 없으므로 PASS로 세지 않는다. R5에 따라 동일한 장시간 bundle
재실행 대신 안전 모드·핵심 명령 3개로 검증면을 줄인 V1-B로 접근을 바꾼다.

### V1-B — Claude 제한 재시도

| 상태 | 시각(KST) | 실행 신원 | 세션 | 종료값 | 현재 SHA |
|---|---|---|---|---:|---|
| FAIL | 2026-08-22 00:04 ~ 00:09 | Claude Code 2.1.238, safe mode, `ANTHROPIC_API_KEY=UNSET` | `4d697200-803a-4002-ac9b-27f218565bc5` | 0 | `29ce9da...` |

호출은 `env -u ANTHROPIC_API_KEY claude --safe-mode --session-id <위 세션>
--no-session-persistence --permission-mode dontAsk --tools 'Bash,Read,Grep,Glob' --effort medium
-p <V1-B 프롬프트>`였다. 실행 전후 작업트리 상태 해시와 산출물 해시는 각각 동일했다.

- 판정: FAIL
- 결함: 중대 1건(강제 장치 3종 귀속 누락), 중 1건(완전성을 6개 상수와만 대조), 낮음 1건(URL
  근거를 검증하지 않으면서 예외를 문서화하지 않음)
- 미확인: `dontAsk` 권한 거부로 지정한 명령 3개는 V1이 직접 실행하지 못했다.
- 원문: `docs/engineering/feature-sot-v1-fail-verdict-2026-08-22.md`

→ V1의 정적 근거만으로 D-1과 D-2가 재현된다. 최종 PASS는 금지하고 누락 장치를 명시적으로
귀속한 뒤 실제 훅·CI 장치와 기능 문서의 귀속을 대조하는 검사로 바꾼다. D-3도 문서와 검사 계약을
일치시킨다.

### V1-B 결함 교정

| 상태 | 시각(KST) | 검증 | 종료값 | 현재 SHA |
|---|---|---|---:|---|
| PASS | 2026-08-22 00:10~00:20 | V1 D-1~D-3 교정 후 구조 검사 | 0 | `29ce9da...` |
| PASS | 2026-08-22 00:20 | 6개 실패 변이 + 7번째 기능 확장 대조 + 499/500/501 경계 | 0 | `29ce9da...` |

- D-1: 클린룸 8종은 `change-delivery-guardrails`, 전역 Strict 스킬 잠금 3종은
  `verification-evidence-system`, 억제 만료는 `repository-data-protection`에 진입점·불변식·근거와
  함께 귀속했다.
- D-2: `EXPECTED_FEATURE_IDS`와 `EXPECTED_CATEGORY_IDS` 상수를 제거했다. 실제 추적 제품 파일 11개,
  이름 있는 CI 단계 23개, CI가 언급하는 저장소 명령 29개, 훅 2개, HumanSearch 계약 2개를 역으로
  수집해 기능별 `surface_coverage`와 정확히 대조한다.
- D-3: 외부 URL을 근거 경로로 허용하는 예외를 제거하고 두 PR URL을 현재 저장소의 역사 goal 경로로
  바꿨다.

```text
PASS: feature SOT structure catalog=1 features=6 categories=3 invariants=32 product_files=11 ci_steps=23 ci_commands=29 hooks=2 contract_surfaces=2 paths=validated
PASS: mutation missing-purpose rejected (exit=1)
PASS: mutation duplicate-feature-id rejected (exit=1)
PASS: mutation missing-evidence-path rejected (exit=1)
PASS: mutation zero-feature-documents rejected (exit=1)
PASS: mutation unmapped-ci-step rejected (exit=1)
PASS: mutation unmapped-ci-command rejected (exit=1)
PASS: seventh feature with a new derived product surface accepted
BOUNDARY: requested=499 actual=499 expected=PASS
BOUNDARY: requested=500 actual=500 expected=PASS
BOUNDARY: requested=501 actual=501 expected=FAIL
PASS: direct code line boundary 382<=500
MUTATION_SUITE_V1_FIX: PASS
```

→ 누락된 제어 표면은 실패하고, 실제 새 제품 표면과 함께 추가한 7번째 기능은 검사 코드 수정 없이
통과한다. 고정된 6개 이름이 아니라 현재 저장소 표면이 완전성의 외부 기준이다.

### V1-C — Claude 교정 후 재검증

| 상태 | 시각(KST) | 실행 신원 | 세션 | 종료값 | 현재 SHA |
|---|---|---|---|---:|---|
| PASS | 2026-08-22 00:24~00:31 | Claude Code 2.1.238, safe mode, `ANTHROPIC_API_KEY=UNSET` | `439ce87b-e8ba-4857-bb35-ee566c854d59` | 0 | `29ce9da...` |

실행 전후 작업트리 상태 해시는 `5082437f...f96f61`, 산출물 해시는 `8003a9a4...90bdce`로
각각 동일했다. Claude가 `check-docs-sot.sh`, 제품 시험, `git diff --check`를 직접 실행해 구조 검사
13항목, 제품 시험 64개, diff 오류 0건을 재현했다. 원문은
`docs/engineering/feature-sot-v1-pass-verdict-2026-08-22.md`에 보존했다.

판정은 PASS였으나 낮은 심각도 F-1~F-3을 남겼다. 완료 전에 모두 교정했다.

- F-1: CI step의 `name`이 `- run` 다음 줄에 있어도 수집하는 상태 parser로 바꿨다. 지정한
  회피 fixture가 이제 `ci_steps ownership mismatch`와 종료값 1을 낸다.
- F-2: `docs/sot/INDEX.md`의 “주요 기능 6개”를 “현재 주요 기능”으로 바꿔 확장 시 거짓이 되지 않게 했다.
- F-3: `verification-commands.md`의 갱신일과 변이 장부를 2026-08-22, 실패 변이 6종 + 확장 대조
  1종으로 맞췄다.

```text
F1_SECOND_LINE_NAME_EXIT=1
FAIL: feature SOT structure — ci_steps ownership mismatch missing=['Synthetic second-line name'] extra=[]
PASS: scripts/check-docs-sot.sh=431 lines (<=500)
```

→ V1-C 이후 변경은 V1이 성공시킨 회피 반례와 두 산문 불일치만 닫았으며 기능·제품 계약은 바꾸지
않았다. 다음 V1-D가 이 변경분을 재확인하고, 새 Codex V2가 V1 전체 판정을 재공격한다.

### V1-D — Claude 변경분 재검증

| 상태 | 시각(KST) | 실행 신원 | 세션 | 종료값 | 현재 SHA |
|---|---|---|---|---:|---|
| PASS(잔여 결함 교정 전) | 2026-08-22 00:35~00:44 | Claude Code 2.1.238, safe mode, `ANTHROPIC_API_KEY=UNSET` | `40f51a09-edc2-408a-a120-6c100048abcd` | 0 | `29ce9da...` |

실행 전후 상태 해시는 `5100f67d...64240d`, 산출물 해시는 `f63559ba...25cd9e`로 같았다.
V1-D는 제품 시험 64개, 구조 검사, diff와 지정한 둘째 줄 `name` 반례의 종료값 1을 재현했다. 그러나
동일 원인의 잔여 F-1R로 대시 뒤 여러 공백과 flow mapping 두 표기가 통과하고, goal의
“fail-closed” 표현이 과장인 F-4를 새로 보고했다. PASS 문구와 무관하게 알려진 결함으로 받아들였다.

### V1-D 잔여 결함 교정

- F-1R: 손으로 쓴 줄 상태 parser를 제거하고 기존 `check-ci-step-integrity.sh`와 같은 Ruby Psych로
  workflow 구조를 읽어 모든 job의 이름 있는 step을 수집한다.
- F-4: goal의 “fail-closed parser”를 “지정한 회피 fixture를 닫은 상태 parser”로 좁혔다.
- 기능 YAML은 Python 표준 `json`, workflow는 저장소 기존 Ruby Psych로 읽는다고 검증 정본을
  정합화했다. 새 dependency는 없다.

```text
VARIANT=second-line-name EXIT=1
FAIL: feature SOT structure — ci_steps ownership mismatch missing=['Synthetic second-line name'] extra=[]
VARIANT=spaced-dash EXIT=1
FAIL: feature SOT structure — ci_steps ownership mismatch missing=['Synthetic spaced dash'] extra=[]
VARIANT=flow-mapping EXIT=1
FAIL: feature SOT structure — ci_steps ownership mismatch missing=['Synthetic flow mapping'] extra=[]
PASS: scripts/check-docs-sot.sh=425 lines (<=500)
```

→ V1-D가 성공시킨 우회 두 종과 기존 지정 반례가 모두 유효 YAML로 파싱된 뒤 종료값 1로 거부된다.

### V1-E — Claude Psych 교정 재검증

| 상태 | 시각(KST) | 실행 신원 | 세션 | 종료값 | 현재 SHA |
|---|---|---|---|---:|---|
| PASS | 2026-08-22 00:47~00:51 | Claude Code 2.1.238, safe mode, `ANTHROPIC_API_KEY=UNSET` | `c4063f47-1477-4306-927d-b7109c436dc2` | 0 | `29ce9da...` |

실행 전후 상태 해시는 `feb2b553...cbe114`, 산출물 해시는 `e2a2fb42...4253a`로 같았다. V1-E는
세 YAML 표기 우회가 Psych에서 유효하게 파싱된 뒤 모두 종료값 1로 거부되고, 제품 시험 64개,
구조 검사, diff, 425줄 경계와 7번째 기능 확장이 유지됨을 재현했다.

V1-E는 낮은 설계 지적으로 두 번째 workflow 파일이 조용히 범위 밖에 놓일 수 있음을 남겼다. 현재
정본이 `.github/workflows/verify.yml` 하나만 소유하므로, checker가 `.yml`·`.yaml` 전량을 열거해 그
집합이 현재 단일 workflow와 다르면 명시적 분류 전까지 실패하도록 교정했다.

### V1-F — Claude 최종 workflow 범위 재검증

| 상태 | 시각(KST) | 실행 신원 | 세션 | 종료값 | 현재 SHA |
|---|---|---|---|---:|---|
| PASS | 2026-08-22 00:53~00:56 | Claude Code 2.1.238, safe mode, `ANTHROPIC_API_KEY=UNSET` | `8f137725-34a2-499c-93ee-abc92937bdb2` | 0 | `29ce9da...` |

실행 전후 상태 해시 `c38d64ff...ad65f4`, 산출물 해시 `c8a8f86d...dad6bf`가 각각 같았다. 기준선은
표면 개수 `6/3/32/11/23/29/2/2`와 종료값 0을 유지했고, 두 번째 `.yml`·`.yaml` workflow, symlink,
기존 workflow 삭제 반례는 모두 종료값 1로 거부됐다. 새 결함은 없었다. 전체 원문은
`docs/engineering/feature-sot-v1-final-verdict-2026-08-22.md`에 보존했다.

## 실행 중 기준선 변경 — HumanSearch L1 반영

2026-08-22 01:00 KST에 공유 저장소가 외부 `git pull --ff-only`로 `29ce9da...`에서
`c59bad7...`로 fast-forward됐다. 이 변경은 사람인 인증 화면을 로컬 진단 포트에서 한 번 읽는 L1
관측기와 제품 파일 3개(`contracts/humansearch/saramin-markers.json`, `_cdp.py`, `observe.py`)를
현재 `main`에 추가했다. 기존 기능 정본의 “인증 분류기는 비시험 소비자가 없다”와 “브라우저 접속은
contract-only” 주장이 즉시 거짓이 됐고, 구조 검사는 새 추적 제품 파일 2개를 미귀속으로 잡아
종료값 1을 냈다. marker 계약 디렉터리는 당시 제품 root 밖이어서 별도로 누락을 확인했다.

기능 수를 기계적으로 늘리지 않고 기존 책임 경계 두 개를 현재 구현에 맞췄다.

- `humansearch-auth-surface`: `implemented/local_runtime`; 순수 분류기 자체의 책임은 유지하되 L1 관측기가
  현재 유일한 비시험 소비자임을 명시했다.
- `humansearch-browser-access`: `implemented/local_runtime`; 사람인 일회 관측의 입력·출력·오류·금지 능력,
  3개 제품 표면과 7개 관측 시험을 귀속했다. 전체 자동 운영, 검색, 입력, 브라우저 생명주기, 다른
  채널은 계속 비범위다.
- `docs/sot/humansearch-browser-contract.md`: 현재 구현된 L1과 여전히 `NOT_RUN`인 D1/C1·검색 자동화를
  같은 상태 장부에서 분리했다.

```text
HEAD_BASELINE_CHANGE=29ce9da... -> c59bad7...
PASS: feature SOT structure catalog=1 features=6 categories=3 invariants=33 product_files=14 ci_steps=23 ci_commands=29 hooks=2 contract_surfaces=2 paths=validated
PASS: humansearch pytest 81/81
PASS: ruff clean in 24 python files
PASS: mypy strict clean in 24 source files
PASS: acceptance-hs-gates collected 81 and passed
```

→ 외부 기준선 변경을 숨기지 않고 현재 HEAD를 다시 SOT 기준으로 삼았다. 이전 V1-F는 `29ce9da...`
산출물에 대한 역사 증거이며, `c59bad7...` 정합화 뒤 V1과 V2를 다시 실행해 최종 판정을 별도로 남긴다.

### V1-G — 현재 HEAD 정합화 적대 검증

| 상태 | 시각(KST) | 실행 신원 | 세션 | 종료값 | 현재 SHA |
|---|---|---|---|---:|---|
| NOT_RUN | 2026-08-22 | Claude Code 2.1.238, API key 경로 | `27e9e16f-e064-4a0a-8a13-6f5249f4f392` | 1 | `c59bad7...` |
| FAIL | 2026-08-22 | Claude Code 2.1.238, safe mode, 로컬 인증 | `6cdf497c-8ea6-4a7a-ac30-61dc9913bab2` | 0 | `c59bad7...` |

첫 실행은 `Credit balance is too low`로 분석 전에 끝났다. 같은 prompt를 프로세스 범위에서만
`ANTHROPIC_API_KEY` 없이 재실행했고, V1은 구조·제품·변이 검사를 통과시킨 뒤 SOT 과장 1건과 잘못된
앵커 1건을 찾아 FAIL했다. 원문은
`docs/engineering/feature-sot-v1-current-head-fail-verdict-2026-08-22.md`에 보존했다.

- 중: malformed target URL이 `urlsplit`의 `ValueError`를 내면 현재 제품은 traceback·raw URL·exit 1로
  샐 수 있는데 기능 SOT는 모든 실패가 PII 없는 한 줄·exit 2라고 과장했다.
- 하: `HBA-INV-6`의 브라우저 계약 fragment가 번호 없는 앵커를 가리켜 §10에 닿지 않았다.

이번 요청은 기능 정본 작성이며 제품 결함 수정 권한까지 넓히지 않는다. 따라서 제품 코드를 바꾸지
않고 현재 동작을 정직하게 명세했다. 정상 처리 경로의 0/2 계약과 알려진 비정상 exit 1 경로를 분리하고,
카탈로그·기능 YAML·브라우저 상세 SOT에 개인정보 노출 위험과 후속 회귀시험+코드 수정 의무를 같은
known gap으로 고정했다. 앵커는 `#10-자격증명과-명령-능력-경계`로 교정했다.

### V2-A — 현재 HEAD 독립 검증과 V1 교차 대조

초기 Codex V2는 구조 검사, 제품 시험 81개, diff, 기능 확장과 10종 변이를 재현해 PASS했으나 V1-G가
찾은 malformed URL 제품 결함과 SOT 과장을 놓쳤다. 원문은
`docs/engineering/feature-sot-v2-initial-verdict-2026-08-22.md`에 보존했다. 따라서 이 PASS를 최종 판정으로
사용하지 않고, known gap 교정 뒤 V1과 V2를 같은 산출물에 다시 실행한다.

### V1-H — known gap 교정 최종 재검증

| 상태 | 시각(KST) | 실행 신원 | 세션 | 종료값 | 현재 SHA |
|---|---|---|---|---:|---|
| PASS | 2026-08-22 | Claude Code 2.1.238, safe mode, 로컬 인증 | `88e3d4bd-9a80-4cc2-a4a4-da0185e82d58` | 0 | `c59bad7...` |

V1-H는 제품 코드 무변경, 세 문서의 동일한 known gap, handled 0/2와 known unhandled 1의 분리, 결함
제거 조건, §10 앵커, 구조 수치 `6/3/33/14/23/29/2/2`, checker 431줄, 제품 시험 81개와 diff를 모두
재현해 PASS했다. 새 결함은 없었다. 원문은
`docs/engineering/feature-sot-v1-current-head-final-verdict-2026-08-22.md`에 보존했다.

V1-H의 정밀도 지적에 따라 “raw URL 전체가 traceback에 항상 포함된다”로 확대하지 않는다. 현재
안전 주장에 필요한 핵심은 신뢰하지 않는 URL의 일부가 예외 메시지로 노출될 수 있고, PII 제거 한 줄과
exit 2 계약을 우회한다는 사실이다. 실제 제품 수정 시 민감 호스트 조각을 가진 malformed IPv6 URL로
회귀 시험해야 한다.

### V1-I / V2-B — 같은 최종 산출물 교차 판정

| 검증자 | 상태 | 실행 신원 | 세션 | 핵심 증거 |
|---|---|---|---|---|
| Claude V1-I | PASS | Claude Code 2.1.238, V1-H fork | `88e3d4bd-9a80-4cc2-a4a4-da0185e82d58`에서 fork | 세 문서의 URL 조각 표현, 구조 검사, diff |
| Codex V2-B | PASS | 새 독립 verifier turn | `/root/feature_sot_v2` | known gap 재현, 제품 시험 81개, 구조 검사, diff, V1 비교표 |

V1-I는 malformed URL 전체가 아니라 호스트 등 URL 조각이 노출될 수 있다는 표현이 실제 관측을 넘지
않고 결함도 축소하지 않는다고 판정했다. V2-B도 handled 0/2와 known unhandled 1의 분리, 해결 과장
금지, 회귀시험+제품수정 동시 제거 조건과 §10 앵커를 재현했다. 원문은 각각
`docs/engineering/feature-sot-v1-wording-final-verdict-2026-08-22.md`,
`docs/engineering/feature-sot-v2-final-verdict-2026-08-22.md`에 보존했다.

최종 결론은 **기능 정본 작업 PASS, 제품 known defect 1건 공개 유지**다. 이 결함은 이번 문서 범위에서
제품 코드가 해결됐다는 뜻이 아니며, 별도 제품 수정 작업 전까지 카탈로그의 known gap에서 제거하지
않는다.

### V1-J — 앵커 회귀 게이트와 슬러그 경계

| 상태 | 실행 신원 | 세션 | 결과 |
|---|---|---|---|
| PASS(잔여 경계 교정 전) | Claude Code 2.1.238, safe mode | `f44c1ea3-f50c-450f-a0bb-a7022c894bb7` | 없는 앵커 exit 1, 정상 구조 exit 0, checker 457줄 |

V1-J는 Markdown 제목 앵커 존재 검사를 통과시켰지만 GitHub 슬러그와 다른 두 경계를 보고했다.
backtick 안의 `NOT_RUN`에서 underscore를 제거했고, em dash가 두 공백 사이에서 제거될 때 생기는
연속 하이픈을 하나로 축약했다. 현재 6개 근거 링크에는 영향이 없지만 미래 링크의 거짓 통과·거짓
거부가 될 수 있으므로 알려진 위험으로 남기지 않고 교정했다.

- underscore는 GitHub 앵커에 남기고 backtick·강조 표지만 제거한다.
- 공백을 각각 하이픈으로 바꾼 뒤 문장부호를 제거해 `1층--결론` 같은 연속 하이픈을 보존한다.
- fenced code 안의 `#` 줄은 제목으로 세지 않는다.

```text
CASE=valid_underscore EXIT=0 EXPECTED=0
CASE=invalid_removed_underscore EXIT=1 EXPECTED=1
CASE=valid_double_hyphen EXIT=0 EXPECTED=0
CASE=invalid_collapsed_hyphen EXIT=1 EXPECTED=1
CASE=invalid_missing_anchor EXIT=1 EXPECTED=1
PASS: scripts/check-docs-sot.sh=463 lines (<=500)
```

### V1-K — GitHub 슬러그 재검증과 혼합 fence 결함

| 상태 | 실행 신원 | 세션 | 결과 |
|---|---|---|---|
| FAIL | Claude Code 2.1.238, safe mode | `150fef5d-778d-4655-8ffd-79786541cff4` | 슬러그 5종 PASS, 혼합 fence 오판 발견 |

V1-K는 underscore·연속 하이픈 경계를 모두 통과시켰지만, 단일 boolean fence 토글이 여는
`~~~` 안의 ` ``` `를 닫힘으로 오해하는 실제 반례를 찾았다. 원문은
`docs/engineering/feature-sot-v1-anchor-slug-fail-verdict-2026-08-22.md`에 보존했다.

교정은 fence의 문자와 여는 길이를 상태로 보존하고, 같은 문자이면서 여는 길이 이상의 marker만
닫힘으로 인정한다. 최대 3칸 들여쓴 CommonMark fence만 처리하고 fence 내부 ATX 제목은 건너뛴다.

```text
CASE=fake_inside_mixed_fence EXIT=1 EXPECTED=1
CASE=real_after_mixed_fence EXIT=0 EXPECTED=0
PASS: scripts/check-docs-sot.sh=475 lines (<=500)
```

### V1-L — 동종 fence 종료 재검증

| 상태 | 실행 신원 | 세션 | 결과 |
|---|---|---|---|
| FAIL | Claude Code 2.1.238, safe mode | `2c1bc65d-afbc-46bc-9235-52c5cf04eb5d` | 지정 반례 PASS, 혼합 marker·backtick info 결함 발견 |

V1-L은 이전 반례를 닫았지만 닫는 정규식의 문자 집합이 혼합 marker를 허용하고, backtick fence의
info string에 backtick이 들어갈 수 없다는 CommonMark 규칙을 검사하지 않는 결함을 찾았다. 원문은
`docs/engineering/feature-sot-v1-anchor-fence-fail-verdict-2026-08-22.md`에 보존했다.

교정 뒤 닫힘은 `fence_char` 하나를 동적으로 반복한 정규식만 인정하며, backtick opener의 나머지
문자열에 backtick이 있으면 fence 시작으로 보지 않는다.

```text
CASE=forged_mixed_backtick EXIT=1 EXPECTED=1
CASE=real_after_backtick EXIT=0 EXPECTED=0
CASE=invalid_backtick_info EXIT=0 EXPECTED=0
CASE=forged_other_marker EXIT=1 EXPECTED=1
CASE=real_after_tilde EXIT=0 EXPECTED=0
PASS: scripts/check-docs-sot.sh=475 lines (<=500)
```

### V1-M — 앵커 parser 최종 종단 판정

| 상태 | 실행 신원 | 세션 | 결과 |
|---|---|---|---|
| PASS | Claude Code 2.1.238, safe mode | `e9a13fbe-cea4-450c-8707-ff614c209601` | 현재 앵커 + fence/slug 11종 종단 일치 |

V1-M은 실제 checker를 11회 실행해 backtick·tilde 혼합, 잘못된 info, underscore, 연속 하이픈, 없는
앵커, 중복 제목을 모두 기대대로 판정했다. 구조 수치 `6/3/33/14/23/29/2/2`, checker 475줄과 diff도
통과했다. 원문은 `docs/engineering/feature-sot-v1-anchor-parser-final-verdict-2026-08-22.md`에 보존했다.

현재 기능 SOT가 쓰지 않는 Setext·컨테이너 제목·여러 줄 HTML 주석은 범위를 확장하지 않는다. 앞의
문법은 보수적 FAIL 위험이고, HTML 주석은 잠재 거짓 PASS 위험이나 `docs/sot/` 현재 사용 사례 0건이다.
새 문법을 SOT 근거 앵커에 도입하려면 parser·반례를 같은 변경에서 확장한다.

### V2-C — 최종 독립 교차 판정

| 상태 | 검증자 | 결과 |
|---|---|---|
| PASS | Codex fresh verifier `/root/feature_sot_v2` | 구조·제품·앵커 변이·known defect·V1 비교 일치 |

V2-C는 현재 작업 트리에서 구조 수치 `6/3/33/14/23/29/2/2`, checker 475줄, 제품 시험 81개,
diff를 재현했다. backtick·tilde fence, invalid info, underscore, 연속 하이픈과 missing anchor 변이도
V1-M과 같은 결과였다. V1이 찾은 과장·누락 중 최종 잔존은 0건이며 새 결함은 없었다. 원문은
`docs/engineering/feature-sot-v2-anchor-parser-final-verdict-2026-08-22.md`에 보존했다.

최종 Strict 판정은 **PASS**다. 단, 제품 코드의 malformed target URL 정규화 결함 1건은 해결된 것이
아니라 `KNOWN_DEFECT`로 공개된 상태다. 원격 CI·branch protection과 라이브 포털은 범위 밖이라
`NOT_RUN`이다.
