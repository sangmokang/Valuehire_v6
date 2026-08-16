# 관리자 주간 대시보드 Phase B 기반 계약 목표 — 2026-08-17

## 현재 상태

- 기준 커밋은 `4fdef31`이고 `origin/main`과 동기화되어 있다.
- v6에는 웹 관리자 앱과 운영 데이터베이스가 아직 없다. 현재 실행 가능한 제품 경계는
  `humansearch` Python 패키지와 `pytest`/`ruff`/`mypy` 검증 배관뿐이다.
- 기존 v4 화면은 월요일 기준 집계와 실패 시 정적 값 유지가 있어 새 요구사항의 정본으로
  사용할 수 없다. 읽기 전용 결함 증거로만 본다.
- `bash scripts/session-status.sh`는 약 73초 후 세 줄을 모두 출력했다.
  결과는 `HEAD: 4fdef31 (synced)`, `ORIGIN: 4fdef31`,
  `RED: 1/19 (acceptance-0-7.sh 제외 — CI 담당)`이다.
- 기존 RED는 `scripts/acceptance-0-2.sh`의 도달 불가능 객체 11건이다. 추적 파일·비밀
  검사는 통과하며, 해결에는 reflog 만료/GC가 필요하므로 이번 기능 범위에서 건드리지 않는다.

## 근본 원인

기존 몰입도 잔디밭 스펙은 `/admin/dashboard`, 운영 테이블, 외부 사이트 세션 수집기가 v6에
이미 있다고 가정했다. 실제 저장소에는 그 실행 표면이 없어서 화면이나 수집기부터 만들면
기술 스택, 운영 인증, 개인정보 보존, 외부 사이트 정책, 집계 의미를 한 변경에 섞게 된다.

따라서 첫 단계는 새 의존성이나 네트워크 없이 다음 불변식을 실행 가능한 순수 계약으로
고정하는 것이다.

1. 회의 주차 이름과 실적 기간을 분리한다.
2. 실적 기간은 일요일 00:00 KST 이상, 다음 일요일 00:00 KST 미만이다.
3. 실행·포지션·원시 후보·출처 내부 고유 후보·메일 숫자를 서로 대체하지 않는다.
4. 모든 표시 숫자는 한 입력 스냅샷과 입력 지문·계약 버전·근거 행 수를 가진다.
5. 조회 실패와 미실행은 0이 아니라 `FAIL`/`NOT_RUN`과 이유다.
6. 출처를 넘는 동일 후보 판정은 신원 연결 계약 전까지 `NOT_RUN`이다.
7. API용 스냅샷은 이름·이메일·제목·본문 같은 개인정보 원문을 포함하지 않는다.
8. 이 단계에는 Gmail, ClickUp, LinkedIn, Saramin, JobKorea 네트워크 호출이나 쓰기 경로가 없다.

## 구현 계약

기존 `humansearch` 검증 배관을 재사용한다. 새 런타임 의존성, 웹 프레임워크, 데이터베이스,
새 `scripts/acceptance-*.sh`는 추가하지 않는다.

예상 구현 경계:

- `humansearch/src/humansearch/admin_weekly_dashboard/`
  - 주간 경계 계산
  - 상태와 입력 사건 계약
  - 결정론적 스냅샷 집계와 JSON 직렬화
- `humansearch/tests/`
  - 주간 경계, 집계 단위, 실패 상태, 개인정보 비노출, 외부 효과 부재의 런타임 시험
- `contracts/admin-weekly-dashboard/metric-contract-v1.json`
  - 표시 가능한 metric id, 사건 종류, 단위, 설명의 유일한 정본

계약 JSON에는 비밀값, 계정 식별자, 개인 URL, 후보자 데이터가 없어야 한다. Python 구현은
계약 JSON의 metric id를 재정의하지 않고 읽어 검증한다.

## 인수 기준

### AC-B1 — 주간 경계

`2026-08-17`과 같은 ISO 주의 `2026-08-18` 회의는 모두 다음 값을 반환한다.

```text
meeting_iso_week=2026-W34
week_anchor_monday_kst=2026-08-17
event_start_kst=2026-08-09T00:00:00+09:00
event_end_exclusive_kst=2026-08-16T00:00:00+09:00
```

종료 경계와 정확히 같은 사건은 제외하고 시작 경계와 같은 사건은 포함한다.

### AC-B2 — 집계 단위 분리

합성 입력 `run 2 / position 2 / raw discovery 3 / source-unique candidate 2 /
recommendation mail 4`는 각각 별도 metric으로 보존된다. 근거 없는 총 몰입도나 ClickUp 카드
수를 후보 수로 바꾼 metric은 존재하지 않는다.

### AC-B3 — 단일 정본과 provenance

모든 metric은 `status`, `value`, `reason`, `metric_contract_version`, `source_collection`,
`source_row_count`, `input_sha256`를 가진다. 같은 입력은 같은 snapshot hash를 만들며 표시값과
provenance는 같은 함수 호출 결과에서 나온다.

### AC-B4 — 조용한 실패 금지

필수 소스가 `FAIL` 또는 `NOT_RUN`이면 연결 metric의 `value`는 `null`이고 이유가 남는다.
빈 입력의 정상적인 0건과 조회 실패를 구분한다.

### AC-B5 — 개인정보와 외부 효과 경계

스냅샷 JSON에 합성 이름·이메일·제목·본문 원문이 나타나지 않는다. 구현 패키지는 Python
네트워크·HTTP·브라우저·DB·서브프로세스 모듈을 import하지 않으며 외부 사이트 실행 액션을
노출하지 않는다.

### AC-B6 — 출처 간 신원 과장 금지

두 출처가 같은 합성 키를 보내도 원시 행은 각각 남고 출처 내부 고유 수만 계산한다.
전사 고유 후보 metric은 `NOT_RUN`이고 신원 연결 계약 부재 이유를 가진다.

### AC-B7 — 저장소 게이트

다음 명령이 실제 시험 수를 0보다 크게 출력하고 통과한다.

```bash
cd humansearch
uv run --no-sync pytest -q tests/test_admin_weekly_window.py \
  tests/test_admin_weekly_snapshot.py tests/test_admin_weekly_boundaries.py
uv run --no-sync ruff check src tests
uv run --no-sync mypy src tests
cd ..
bash scripts/acceptance-hs-gates.sh
bash verify.sh
```

기존 `acceptance-0-2.sh` RED는 별도 기저 결함으로 보고하며 이번 변경으로 악화하지 않는다.

## RED 계획

1. 구현 모듈이 없는 상태에서 위 인수 시험을 먼저 작성한다.
2. `ModuleNotFoundError` 또는 계약 미구현으로 실패하는 실행 로그를 남긴다.
3. 시험만 단독 커밋한다. 그 뒤 시험 기대값을 바꾸지 않는다.
4. 최소 구현 후 표적 시험, ruff, mypy, 기존 HumanSearch 게이트, 비밀 검사를 실행한다.
5. 월요일 시작 변이, 실패를 0으로 바꾸는 변이, 출처 간 고유 수 생성 변이가 각각 시험을
   깨는지 확인하고 원복한다.

## 적대 검증 계획

1. `env -u ANTHROPIC_API_KEY claude -p`로 이 목표와 diff를 1차 검토한다.
2. 출력 전문과 실행 명령을 이 문서에 append한다.
3. Codex가 각 지적을 `file:line`과 실행으로 `CONFIRM/REFUTE/PARTIAL` 판정한다.
4. 확인된 결함을 고치고 모든 게이트를 다시 실행한다.

## 정본

우선순위는 사용자 제공 `AGENTS.md` > `docs/sot/*` >
`admin-weekly-dashboard-v6-replacement-goal-2026-08-16.md` > 이 문서 > 구현 > 시험이다.

## 비범위

- 웹 UI, 관리자 인증, DB migration, Supabase mirror
- Gmail/ClickUp/캘린더 실제 계정 읽기
- LinkedIn/Saramin/JobKorea 자동 수집
- ClickUp/메일/외부 서비스 쓰기
- 배포, 운영 주소 전환, 기존 서비스 삭제
- 기존 git unreachable object의 reflog 만료 또는 GC

