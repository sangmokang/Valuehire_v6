# 관리자 주간 대시보드 Phase C 로컬 shadow UI 목표 — 2026-08-17

## 현재 상태

- 이 브랜치는 검증된 Phase B 커밋 `1a285e0` 위에 쌓인다.
- Phase B는 일요일~토요일 창, metric 단위 분리, provenance, `PASS/FAIL/NOT_RUN`,
  개인정보 비노출, 외부효과 `DISABLED`를 순수 Python 계약으로 고정했다.
- v6에는 웹 프레임워크, 관리자 인증, 운영 DB, 배포 기반이 없다.
- 실제 계정 읽기를 시작하기 위한 보관기간·열람 역할·삭제 명령·캘린더 일정 고유값이
  확정되지 않았으므로 Gmail/ClickUp/채용사이트 연결은 계속 금지한다.
- 인증된 기존 화면 reference가 없으므로 기존 화면과 픽셀 일치는 `NOT_RUN`이다.

## 목표

운영 제품으로 위장하지 않는 localhost 전용 shadow UI를 만든다. 이 화면은 Phase B snapshot과
metric 계약을 그대로 소비하며 카드 값을 다시 계산하지 않는다. 프레임워크와 새 의존성 없이
Python 표준 라이브러리 서버와 정적 HTML/CSS/JS로 `build·test·start` 경계를 증명한다.

이 단계의 성공은 다음 여섯 문장이다.

1. `127.0.0.1` 외 주소에는 bind할 수 없는 로컬 preview 서버가 실행된다.
2. `/api/dashboard`는 Phase B `build_weekly_snapshot()` 결과와 같은 값·상태·hash를 반환한다.
3. UI의 metric 이름·그룹·단위·설명은 root contract 한 벌에서 오며 JS에 metric id별 숫자나
   이름을 하드코딩하지 않는다.
4. `FAIL/NOT_RUN`은 `0`이 아니라 `미집계`와 안전한 reason code로 보인다.
5. 12주 heatmap은 수집된 주만 값으로 칠하고 나머지는 `미집계`로 표시하며 과거값을 만들지 않는다.
6. CSP·no-store·경로 allowlist가 있고 외부 asset·외부 API·운영 쓰기 경로가 없다.

## 구현 경계

- `contracts/admin-weekly-dashboard/metric-contract-v1.json`
  - `display_label`, `group`, `unit`을 metric metadata로 추가한다.
- `humansearch/src/humansearch/admin_weekly_dashboard/`
  - contract metadata의 검증·API catalog 직렬화
  - synthetic, PII-free shadow snapshot builder
  - loopback-only HTTP server와 exact-path static serving
- `apps/admin/`
  - `index.html`, `styles.css`, `app.js`
  - 외부 URL, CDN, inline script/style 없음
- `humansearch/tests/`
  - 실제 loopback server를 port 0으로 띄워 HTTP 응답·헤더·API/계약 동일성 검증
  - UI asset 계약과 실패 상태의 browser-visible 결과 검증

서버 실행 명령은 다음 한 벌로 고정한다.

```bash
PYTHONPATH=humansearch/src python3 -m humansearch.admin_weekly_dashboard.shadow_server \
  --assets apps/admin \
  --contract contracts/admin-weekly-dashboard/metric-contract-v1.json \
  --host 127.0.0.1 \
  --port 8765
```

## 인수 기준

### AC-C1 — 로컬 전용 실행

- host는 `127.0.0.1` 또는 `localhost`만 허용한다.
- `0.0.0.0`, LAN 주소, 빈 host는 실행 전에 실패한다.
- 서버 banner와 화면 header에 `LOCAL SHADOW · 운영 아님`을 표시한다.

### AC-C2 — 단일 snapshot 소비

- `/api/dashboard`의 `weeks[-1].snapshot_sha256`, metric value/status/provenance는 같은 요청에서
  생성한 Phase B snapshot과 동일하다.
- JS는 API의 `value`를 합산·재계산하지 않고 표시와 heatmap 강도 선택에만 쓴다.
- 수집 이력이 한 주뿐이면 나머지 11주는 `NOT_RUN/history_not_collected`다.

### AC-C3 — metric metadata 정본

- 각 계약 metric은 `display_label`, `description`, `group`, `unit`을 가진다.
- API catalog id 집합과 snapshot metric id 집합이 정확히 같다.
- 같은 id, label, group, unit을 JS나 HTML에 중복 선언하지 않는다.

### AC-C4 — 실패 상태 시각화

- synthetic shadow에서 mail source는 `NOT_RUN/retention_policy_missing`이고 추천·포지션 카드가
  `0`이 아니라 `미집계`다.
- sourcing source는 PASS이며 run·position·raw·source-unique가 서로 다른 값을 표시한다.
- global unique candidate는 항상 `NOT_RUN/identity_link_contract_missing`다.

### AC-C5 — HTTP 안전 경계

- `/`, `/styles.css`, `/app.js`, `/api/dashboard`, `/healthz` 외 경로는 404다.
- 응답은 `Cache-Control: no-store`, `X-Content-Type-Options: nosniff`,
  `Content-Security-Policy`를 가진다.
- CSP는 `default-src 'self'`, `connect-src 'self'`, `object-src 'none'`,
  `frame-ancestors 'none'`를 포함한다.
- API 오류는 자유형 예외 원문 대신 allowlisted reason code만 반환한다.

### AC-C6 — 접근성·반응형·시각 판정

- semantic `header/main/section`, 유일한 h1, metric group h2, 상태 텍스트와 색 외 식별자를 쓴다.
- 390px 폭에서 가로 overflow 없이 카드와 heatmap이 한 열 또는 스크롤 가능한 명시 영역으로 바뀐다.
- reference는 `.omx/state/admin-dashboard-shadow-ui/reference.html`의 요구사항 기반 wireframe을
  먼저 렌더한 PNG로 고정한다. 운영 화면 reference가 아님을 함께 기록한다.
- 각 화면 수정 후 새 screenshot과 reference를 `visual-verdict` JSON으로 판정하고
  `.omx/state/admin-dashboard-shadow-ui/ralph-progress.json`에 저장한다.
- 90점 미만이면 verdict 제안을 반영한 뒤 다시 screenshot을 찍는다.

### AC-C7 — 저장소 게이트

```bash
cd humansearch
uv run --no-sync pytest -q tests/test_admin_shadow_server.py \
  tests/test_admin_shadow_contract.py
uv run --no-sync ruff check src tests
uv run --no-sync mypy --strict src tests
cd ..
bash scripts/acceptance-hs-gates.sh
bash scripts/acceptance-hs-gates-mutations.sh
bash scripts/acceptance-hs-gates-antiforge.sh
bash verify.sh
bash scripts/scan-data-exposure.sh all
```

모든 실행은 실제 처리 수를 출력해야 한다. 기존 `acceptance-0-2.sh` unreachable object RED는
Phase B와 같은 별도 기저 결함으로 공개한다.

## RED 계획

1. contract metadata, server loopback, API 동일성, 안전 header, exact-path, 실패 표시 시험을 먼저 쓴다.
2. server/module/assets가 없어 생기는 RED를 실행으로 확인한다.
3. 시험 전용 커밋 후 기대값을 고정한다.
4. 최소 서버와 assets를 구현한다.
5. `0.0.0.0` 허용, `NOT_RUN→0`, JS metric map 하드코딩, CSP 제거 변이를 각각 시험이 잡는지 확인한다.

## 적대 검증

1. API 키 환경변수 없는 Claude CLI 1차를 시도하고 명령·출력 전문·종료 상태를 append한다.
2. Codex가 각 지적을 file:line과 실행으로 `CONFIRM/REFUTE/PARTIAL` 판정한다.
3. UI 변경은 screenshot과 visual verdict를 evidence로 남긴다.
4. PR까지만 준비하고 merge·deploy·운영 전환은 하지 않는다.

## 비범위

- 관리자 인증과 인터넷 공개
- 운영 DB·Supabase migration·snapshot 영속화
- Gmail/ClickUp/캘린더 실제 계정 읽기
- LinkedIn/Saramin/JobKorea 자동화
- ClickUp/메일/외부 서비스 쓰기
- 운영 도메인 연결·배포·기존 서비스 삭제
- 실제 과거 12주 값 생성 또는 추정
- 기존 운영 화면과의 픽셀 일치 합격 주장

## 실행 증거 — 2026-08-17

### RED 고정

- 최초 계약·서버 테스트는 `shadow_server` 모듈 부재로 collection error가 났다.
- 미지원 method 회귀 시험은 `HEAD/PUT/PATCH/DELETE/OPTIONS`가 기본 501로 빠져
  `5 failed, 1 passed`였다.
- 포함 종료일·서버 식별 시험은 `event_end_inclusive_date_kst` 부재와
  `BaseHTTP/0.6 Python/3.14.1` 노출로 `2 failed`였다.
- symlink 자산 시험은 `index.html`이 외부 파일을 가리켜도 서버가 생성되어
  `DID NOT RAISE ValueError`로 실패했다.

### GREEN 및 저장소 게이트

```text
$ cd humansearch
$ uv run --no-sync pytest -q tests/test_admin_shadow_contract.py tests/test_admin_shadow_server.py
26 passed
$ uv run --no-sync ruff check src tests
All checks passed!
$ uv run --no-sync mypy --strict src tests
Success: no issues found in 13 source files

$ bash scripts/acceptance-hs-gates.sh
PASS: ruff clean in 13 python files
PASS: mypy strict clean in 13 source files
PASS: pytest collected 40 and passed
COLLECTED: 40
$ bash scripts/acceptance-hs-gates-mutations.sh
PASS: gates mutations blocked 6/6
$ bash scripts/acceptance-hs-gates-antiforge.sh
PASS: gates antiforge 3/3 (evidence forgery + CI disable blocked)
$ bash verify.sh
PASS: no secret-pattern match in any tracked file, .env not tracked
$ bash scripts/scan-data-exposure.sh all
PASS: 추적 파일 101개 검사, 위반 0건
PASS: 기록 전량 blob 432개 검사, 크기·경로 위반 0건
PASS: csv/tsv/sql 0개 검사(추적 101개 중), 개인정보 적재 0건
```

### 브라우저·시각 판정

- 설치된 Chrome을 Playwright CLI로 구동하고 `body[data-ready="true"]`를 기다린 뒤
  1440×1100과 실제 390px viewport를 캡처했다.
- 최종 화면:
  - `.omx/state/admin-dashboard-shadow-ui/generated-1440-v4.png`
  - `.omx/state/admin-dashboard-shadow-ui/generated-390-full-v4.png`
- 390px에서는 H1이 두 줄로 래핑되고 metric은 한 열, 12주 표만 명시적 가로 scroll 영역이다.
- `visual-verdict`는 `86 revise → 93 pass → 93 pass`였고 전체 기록은
  `.omx/state/admin-dashboard-shadow-ui/ralph-progress.json`에 남겼다.
- 첫 판정에서 발견한 `08-16` 배타 경계 오표시는 API view model의 포함 종료일 `08-15`로
  교정했다. 집계 snapshot의 `[08-09, 08-16)` 경계는 바꾸지 않았다.

### 적대 검증 V1 — Claude CLI

다음 명령으로 도구를 끄고 Phase C diff만 표준 입력으로 전달했다.

```text
git diff 1a285e0..HEAD -- <Phase C paths> |
  env -u ANTHROPIC_API_KEY claude -p --tools '' --output-format text '<review prompt>'
```

- 60초 동안 stdout/stderr가 모두 0 byte였다.
- `SIGINT`로 중단했고 종료 코드는 `130`이었다.
- 판정: `NOT_RUN`. 출력이 없으므로 Claude의 PASS 또는 지적을 주장하지 않는다.
- 같은 CLI hang은 Phase B의 세 가지 입력 방식에서도 재현됐다. 단순 `OK` 요청은 성공했으므로
  실행 파일 부재가 아니라 repository/diff review 경로의 미해결 hang으로 분리한다.

### 적대 검증 V2 — Codex 재공격

- `CONFIRM → FIXED`: 고정 route 파일이 symlink면 asset root 밖의 로컬 파일을 읽을 수 있었다.
  RED 시험을 추가하고 `_load_assets()`가 읽기 전에 symlink를 거부하도록 고쳤다.
- `CONFIRM → FIXED`: metric group 제목이 목표의 `h2` 대신 `h3`였다.
- `CONFIRM → FIXED`: 목표 문서 끝의 여분 blank line을 제거했다.
- `REFUTE`: 390px H1 잘림 지적은 Chrome 직접 실행의 최소 layout viewport를 390px 이미지로
  crop한 초기 캡처에만 나타났다. Playwright가 설정한 실제 390px viewport의 v2~v4 전체 캡처에서는
  `Admin Weekly` / `Dashboard` 두 줄로 viewport 안에 표시된다.
- 코드 리뷰·보안 리뷰 모두 critical/high 잔여 지적은 없었다.

## 명시적 NOT_RUN 및 기저 제약

- 인증된 운영 화면 reference와의 pixel match: `NOT_RUN` (reference는 요구사항 기반 wireframe).
- Firefox/WebKit cross-browser와 보조기기 실사용: `NOT_RUN`.
- live Gmail/ClickUp/캘린더/채용사이트, 운영 DB, 배포, 관리자 인증: 비범위로 `NOT_RUN`.
- Claude V1: 위 hang 때문에 `NOT_RUN`; 따라서 strict 총합 PASS를 주장하지 않는다.
- main 저장소에서 `bash scripts/acceptance-0-2.sh`를 재실행한 결과 tracked secret scan은
  PASS했지만 기존 unreachable 객체 `17건` 때문에 RED다. 이 단계에서는 reflog expire/GC 같은
  파괴적 정리를 실행하지 않았다.

### clean clone pre-push 증거

공유 object DB의 기저 결함을 우회해 숨기지 않고 원인과 기능 브랜치를 분리하기 위해,
현재 브랜치를 `git clone --no-local`로 임시 clone했다. 이 방식은 reachable commit만 복사하며
원본 object DB·reflog를 수정하거나 삭제하지 않는다.

```text
$ bash scripts/acceptance-0-2.sh
PASS: 0-2 — 히스토리·객체·reflog·docs 리터럴 0건, 스캐너 뮤테이션 검출 확인
$ bash scripts/acceptance-hs-gates.sh
PASS: pytest collected 40 and passed
$ bash scripts/acceptance-hs-gates-mutations.sh
PASS: gates mutations blocked 6/6
$ bash scripts/acceptance-hs-gates-antiforge.sh
PASS: gates antiforge 3/3 (evidence forgery + CI disable blocked)
$ bash scripts/check-docs-sot.sh
OK: docs/sot 재구성 AC 전부 충족
$ bash verify.sh
PASS: no secret-pattern match in any tracked file, .env not tracked
$ bash scripts/scan-data-exposure.sh all
PASS: 추적 파일 101개 검사, 위반 0건
PASS: 기록 전량 blob 385개 검사, 크기·경로 위반 0건
PASS: csv/tsv/sql 0개 검사(추적 101개 중), 개인정보 적재 0건
```

push/PR은 이 clean clone에서만 수행한다. 원본 main의 unreachable 17건은 별도 저장소 정리
작업으로 남으며 이 기능 PR이 해결했다고 주장하지 않는다.
