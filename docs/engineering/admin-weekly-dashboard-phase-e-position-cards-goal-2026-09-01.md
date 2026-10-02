# admin_weekly_dashboard Phase E — position_cards 실연결 목표 — 2026-09-01

## 1층 — 결론

`position_cards` 소스 하나를 실제 Supabase(PostgREST)에서 읽어 이미 승인된
`source-contract-v1.json`의 `select_fields`(id, company_name, imported_at,
last_updated_at) 4개만으로 `SourceState`(PASS/FAIL/NOT_RUN)를 반환하는 코드를
새로 만든다. 지금은 이 4개 필드를 실제로 읽는 코드가 0줄이고, `shadow_server.py`는
합성 데이터만 쓴다. `supabase_writes`는 계속 `DISABLED`로 두고 이번 변경은 읽기
전용이다. 화면(대시보드) 연결은 이번 범위가 아니다 — 조회 함수 하나가 계약대로
동작함을 단위 테스트 + 라이브 1건으로 증명하는 것까지만 한다.

## 2층 — 판단 근거

`source_contract.py`/`source_policy.py`는 계약 검증·상태 분류 로직을 이미
68 tests·mutation 6/6·antiforge 3/3로 증명해뒀다(사장님 프롬프트 근거, 이번
세션에서 재확인 완료 — `EXPECTED_SUPABASE_SOURCES["position_cards"]`가
`contracts/admin-weekly-dashboard/source-contract-v1.json`과 정확히 일치함을
`source_contract.py:46-50`에서 직접 대조). 남은 gap은 정확히 하나 —
이 판정 규칙에 넣을 실제 입력(Supabase 응답)을 만드는 코드가 없다는 것이다.

`sourcing_runs` 대신 `position_cards`를 고른 이유: `sourcing_runs`는
2026-07-17 이후 데이터 갱신이 멈춰 있어 "연결은 됐는데 화면이 텅 빔"이 되고,
그러면 이번 AC의 증거(라이브 1건)가 "정말 연결됐다"를 증명하지 못하고
"아무것도 안 왔다"와 구분이 안 된다. `position_cards`는 2026-08-31까지
갱신된 살아있는 데이터라 연결 성공 여부를 즉시 눈으로 확인할 수 있다.

이 저장소는 `humansearch/pyproject.toml`에 런타임 의존성이 하나도 없다
(`dependency-groups.dev`만 있음 — hypothesis/ruff/mypy/pytest). 새 HTTP
클라이언트 라이브러리(`httpx`, `supabase-py` 등)를 추가하는 대신 표준
라이브러리 `urllib.request`로 PostgREST REST 엔드포인트를 직접 호출한다 —
의존성을 늘리지 않고, 기존 코드 전체가 이미 stdlib-only 순수 함수 스타일을
따르고 있어(제출용 HTTP 요청 함수를 인자로 주입 가능하게 만들면 외부
네트워크 없이도 counter-AC의 세 실패 시나리오를 전부 단위 테스트로 재현할
수 있다.

> **무엇을** — `humansearch/src/humansearch/admin_weekly_dashboard/position_cards_source.py`를
> 새로 만들어 `fetch_position_cards(*, base_url, api_key, http_get=...)` 함수가
> Supabase PostgREST `public.pipeline_position_cards`를 `select=id,company_name,
> imported_at,last_updated_at`로만 조회하고, 결과를 `PositionCardsResult`
> (`SourceState` + 검증된 행 튜플)로 반환하게 한다.
>
> **왜** — 이 저장소가 이미 검증해둔 PASS/FAIL/NOT_RUN 판정 계약에 처음으로
> 실제 데이터를 흘려 넣어야 "계약은 맞는데 화면 뒤에 아무 연결도 없다"는
> 상태를 벗어난다.
>
> **버린 길** — `sourcing_runs`부터 연결하는 안(6주째 정지된 데이터라 라이브
> 증거가 약함), `httpx`/`supabase-py` 신규 의존성 추가(런타임 의존성 0개인
> 저장소 관례를 깨고, mypy strict·ruff 대상만 늘어남), `shadow_server.py`에
> 바로 배선(이번 AC 범위를 "조회 함수 1개 증명"에서 "대시보드 API 응답까지"로
> 넓혀 인수 기준이 1개가 아니게 됨) — 셋 다 버린다.
>
> **대가** — 대시보드 화면은 이번 변경 후에도 여전히 합성 데이터를 보여준다
> (배선은 다음 AC). `urllib.request` 직접 호출은 재시도·커넥션 풀링이 없다 —
> 15분 주기 배치 읽기 1건에는 충분하지만, 트래픽이 늘면 재검토 대상이다.
>
> **되돌리기** — 새 파일 1개(+ 대응 테스트 파일 1개) 삭제만으로 완전히
> 되돌아간다. 기존 `source_contract.py`/`source_policy.py`/`.env`/
> `source-contract-v1.json`은 건드리지 않는다.

## 3층 — 계약과 증거

### 위험등급과 세션

- 위험등급: **L2** (일반 코드 변경 — PII 인접 소스 접근이지만 마이그레이션·
  외부 발송·과금 아님. `service_role` 키를 다루므로 자격증명 취급만 L3급
  주의로 격상해 취급한다: 로그·테스트 출력·커밋에 값 노출 금지)
- 기준 SHA: `b7240936827032d5ee6791fa8cdb7d62ef6584b4` (main, clean)
- 워크트리: `worktrees/admin-dashboard-position-cards-e1/` · 브랜치
  `task/admin-dashboard-position-cards-e1`
- 이 저장소는 `Makefile`/`package.json`이 없다 — 게이트 명령은
  `docs/sot/verification-commands.md`의 실제 명령을 쓴다(harness 기본 명령이
  아님, 확인 완료: `make red-ledger`/`npm run wt` 둘 다 이 저장소에 없음).
- 세션 시작 시 `RED: 0/28` 확인됨(Gate 0 충족) — `bash scripts/session-status.sh`.

### 재발 원장 인용

- `docs/sot/coding-principles.md` P16(판정을 한 곳에만 둔다)·P20(검사 대상
  0건은 통과가 아니다fail-closed)을 이번 counter-AC의 "빈 테이블 조용한
  통과 금지"에 직접 적용한다 — 네트워크 오류/스키마 불일치/빈 테이블 세
  경로가 전부 서로 다른 코드 분기로 떨어지게 만들어, 한쪽 실패가 다른
  쪽(예: "그냥 0건 반환")으로 위장할 수 없게 한다.

### 인수 기준 (1개, EARS)

When `position_cards` 소스를 조회하면, 시스템은 `source-contract-v1.json`의
`select_fields`(`id`, `company_name`, `imported_at`, `last_updated_at`)만
읽어 `SourceState`(PASS/FAIL/NOT_RUN)를 반환해야 하고, `select_fields` 밖
필드(예: `raw_clickup_payload`, `jd_text`, `tags`)는 반환값(스냅샷)에 never
포함해야 한다.

**counter-AC**: 네트워크 오류·스키마 변경(필드 누락/추가)·빈 테이블 세
경우를 서로 구분하지 못하고 "PASS + 빈 목록"으로 뭉뚱그리면 가짜. 세 경우
전부 별도 테스트로 증명한다.

### 결정 목록 (오너 확정 필요 없음 — counter-AC로 이미 결정됨)

- 네트워크 오류(연결 거부·타임아웃) → **FAIL** (`SOURCE_TIMEOUT`/
  `SOURCE_UNAVAILABLE`, 기존 enum 재사용, 신규 enum 값 추가 없음)
- 서버가 200을 주었지만 JSON이 리스트가 아니거나, 행에 계약 4개 필드와
  다른 키 집합(누락·추가)이 있으면 → **FAIL** (`CONTRACT_MISMATCH`)
- 서버가 200 + 유효한 스키마의 빈 리스트(`[]`)를 준 경우 → **PASS + 빈
  튜플** (이것은 조회 자체는 성공했고 데이터가 실제로 없다는 진실한 결과이며,
  네트워크 오류·스키마 불일치와는 **다른 코드 분기**를 통과해야만 도달
  가능하게 만들어 counter-AC의 "조용한 위장"을 차단한다 — 즉 "빈 테이블이
  항상 FAIL"이 아니라 "빈 테이블이 오류를 가장한 결과가 될 수 없다"가 이
  구현의 불변식)

### 검증 계획

- RED: `humansearch/tests/test_position_cards_source.py` — 아직 없는
  `position_cards_source.py`를 import해 실패 확인 → 커밋.
- GREEN: 최소 구현 후 `uv run pytest tests/test_position_cards_source.py -v`
  (동일 파일 내 network/schema/empty 세 counter-AC 케이스 포함) + 전체
  스위트 회귀 없음 확인.
- 정적 검사: `uv run ruff check src/humansearch/admin_weekly_dashboard/position_cards_source.py`,
  `uv run mypy --strict src/humansearch/admin_weekly_dashboard/position_cards_source.py`.
- 비밀 스캔: `bash verify.sh`, `bash scripts/scan-data-exposure.sh all`,
  `.env`에 `SUPABASE_URL`/`SUPABASE_KEY` 추가 후 두 스캔 모두 PASS 확인
  (값은 어디에도 출력하지 않는다).
- 라이브 1건: 실제 `.env`의 `SUPABASE_URL`/`SUPABASE_KEY`로
  `fetch_position_cards()`를 1회 호출해 `status=PASS`와 행 개수만 출력
  (행 내용/키 값 비노출).

### 배선 증명 계획

이번 AC는 "조회 함수 1개가 계약대로 동작한다"까지다 — `shadow_server.py`나
CLI에 새로 배선하지 않는다(2층 "버린 길" 참조). 따라서 이번 PR의 배선
증명은 "함수가 실제 네트워크 호출을 실제로 수행해 실제 Supabase 응답을
파싱한다"는 라이브 1건 로그로 대체한다. 화면/CLI 배선은 다음 AC로 분리한다.

### 비범위

- `sourcing_runs` 등 나머지 6개 소스 연결.
- `shadow_server.py`/`source_policy_cli.py`에 이 함수 배선.
- `supabase_writes` 활성화(계속 `DISABLED`).
- 재시도·커넥션 풀링·캐싱.

## 적대 검증 로그

(V1 실행 후 기록)
