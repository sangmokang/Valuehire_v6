# AI Search 관리자 증거 화면 Spec — 2026-10-29

## 1. 목적과 단일 인수 기준

운영자가 Gmail에서 실제로 확인된 AI Search 실행 결과를 주차별 엑셀형 원장으로 본다. 선택 주차의
실행 Batch 수와 고유 후보 수를 먼저 보고, 각 Batch의 고객사·포지션·검색 AI·중복 제거 후보·프로필
URL·학력·경력·점수·이유·컨택을 한 행씩 확인한다. 별도 컨택 원장에서 AI 발송과 사람 직접 발송을
구분한다. 증거가 없는 값은 0이나 빈 문자열이 아니라 `NOT_RUN`과 사람이 읽을 수 있는 사유다.

## 2. 2026-10-29 실데이터 기준선

읽기 전용 query `subject:aisearch -in:spam -in:trash`를 4페이지 끝까지 조회했다.

- Gmail 354통: 실행 352, 테스트·비실행 제외 2
- Batch 308, 실행 주체 근거 완전 308/308
- 후보 count 확정 244/308 Batch
- `raw 9,249 = parsed 8,646 + duplicate 359 + unparsed 244 + excluded 0`
- 고유 후보 프로필 6,830
- 후보–Batch 등장 8,646
- 고객사·포지션 확인 연결 7,935, 미확인 연결 711
- 점수 확인 후보 0, 학력 49, 전체 경력 29, 핵심 경력 0
- 필수요건별 근거 0, 적합 근거 40, 더 적합한 포지션 0, 컨택 의견 근거 2
- 검색 기간 확인 0/308

후보 보고서 경계 파싱 전 기준은 고유 후보 6,831, 후보–Batch 8,648, 학력 17, 전체 경력 4,
적합 근거 0이었다. 실제 `[P1-1] 이름 — 점수` 상세과 `- 이름 58 — 요약` 형식을 파싱한 뒤
일반 링크 2행·프로필 1개 오탐을 제거하고, 학력·경력·적합 근거를 원문에서 복원했다. 대표 ABB
메일은 원문 평가 52명과 동일하게 `parsed 51 + unparsed 1 = raw 52`다. 메일의 포지션별 자체 점수는
40/40/10/10 계약 점수가 아니므로 점수로 승격하지 않았다.

보낸편지 query는 1페이지에서 종료됐다. 직접 제안 8, 분류는 `AI 7 / OWNER 1 / UNKNOWN 0`,
후보 연결 0 / 미연결 8이다. 미연결 사유는 메일에 후보 정본 프로필 URL이 없기 때문이다.

## 3. API 계약

### `GET /api/ai-search/weekly`

초기 화면용 주차 index다. Gmail 실행 또는 보낸편지 pagination이 하나라도 끝나지 않았으면 status는
`PASS`가 아니다. 각 주차는 `week_id`, 기간, Batch 수, 주간 고유 후보 수, 후보·포지션 행 수,
AI/OWNER/UNKNOWN 발송 수, 후보 연결/미연결 수를 제공한다. 후보 행 전체는 포함하지 않는다.

### `GET /api/ai-search/weekly/{week_id}`

선택 주차의 후보 서치 원장과 주간 컨택 원장을 반환한다. 없는 주차는 HTTP 404와
`ai_search_week_not_found`를 반환한다.

- `candidate_rows`: `(batch_id, canonical_key)` 기준 행. 한 행 = 한 Batch의 중복 제거 후보 1명이다.
- `contact_rows`: 실제 Gmail 제안 이벤트 기준 행. 후보 URL이 없는 이벤트도 손실 없이 남긴다.
- `contact_summary.owner_linked_candidates`: 사람 직접 발송 중 후보 정본키까지 연결된 고유 후보 수다.

주차 범위는 KST 일요일 00:00 이상, 다음 일요일 00:00 미만이다. 표시 주차는 기존 관리자 계약과
같이 기간 종료 후 운영회의 ISO 주차다. 데이터가 있는 최초·최종 주 사이 빈 주도 index에 포함한다.

### `GET /api/ai-search`

목록 payload는 다음을 제공한다.

- `candidate_summary`: 고유 프로필, 후보–Batch 등장, 확인/미확인 포지션 연결, 점수 상태,
  상세 필드별 고유 후보 채움 수
- `candidate_ledger`: canonical key별 프로필, 채널, 모든 검색 이력, 모든 컨택 이력,
  집계된 `profile_evidence`
- `contact_collection`: 실제 제안 수, AI/OWNER/UNKNOWN 수, 후보 연결/미연결 수와 이벤트
- `batches`: Batch 목록과 후보 수 수식, 검색 기간, 실행 주체 증거, 검증 상태

### `GET /api/ai-search/candidates/{canonical_key}`

고유 후보 상세 한 건을 반환한다. 없는 key는 HTTP 404와
`{"status":"FAIL","reason":"candidate_not_found"}`를 반환한다.

### `GET /api/ai-search/{stable_batch_id}`

Batch 상세 한 건을 반환한다. 없는 ID는 HTTP 404와 `batch_not_found`를 반환한다.

## 4. 후보 상세 병합 규칙

동일 canonical key의 여러 Batch 기록은 손실 없이 유지한다. scalar 상세은 최신순으로 처음 확인된
비어 있지 않은 값을 택하고, 필수요건·적합 근거는 중복 제거한 합집합을 사용한다. 점수는 포지션마다
다를 수 있으므로 검색 이력 안에 각각 보존한다. 다른 포지션 점수를 후보 공통 점수로 덮어쓰지 않는다.

직접 컨택은 이벤트 단위로 누적한다. 명시적 후보 프로필 URL이 없는 이벤트는 전체 직접 컨택 장부에
남기되 후보 상세에 추정 연결하지 않는다.

## 5. 화면 정보 구조

1. 주차 선택: 최신 주차를 기본으로 열고 모든 수집 기간을 선택할 수 있다.
2. 주차 사실 집계: 실행 Batch, 고유 후보, 후보·포지션 행, AI 발송, 사람 직접 발송,
   후보 연결/미연결.
3. 후보 서치 원장: 실행 일시, 간략 Batch, 고객사, 포지션, 검색 AI, 후보자, 프로필 URL, 채널,
   학력, 전체·핵심 경력, 점수, 점수·적합 이유, 주간 컨택.
4. 주간 컨택 원장: 발송 일시, AI/OWNER/UNKNOWN, 제목, 연결 후보, 연결 상태, Gmail message/thread.
5. 외부 효과: 외부 발송 기능과 원격 DB 쓰기가 비활성인지 표시한다.

필수 검증 상태는 목록 상태, 선택 주차 상세 상태, 빈 상태, 오류 상태 네 가지다. 표 헤더는 sticky,
본문 글자는 16px 이상, 가로 스크롤과 키보드 focus를 제공한다. 프로필 URL은 실제 링크 문자열을
보여 주고 새 탭에서 열 수 있다.

## 6. 실패·반례 계약

- pagination 미종료 → 전체 수집 PASS 금지
- 점수 네 축 누락 → 총점과 점수대 NOT_RUN
- 메일 총점만 존재 → 네 축 점수로 변환 금지
- 후보 이름만 일치 → cross-channel 병합 금지
- 제안 메일에 후보 URL 없음 → 후보 컨택 연결 금지
- 후보 URL은 있으나 Batch ID 없음 → 후보 수준 연결만 허용, 특정 Batch 후속 연락으로 귀속 금지
- 수집값 없음 → 0/PASS 금지
- 테스트 메일 → 실행 Batch 포함 금지
- 외부 발송·라벨·보관·원격 DB 쓰기 → 금지

## 7. 검증 명령

```bash
uv run --project humansearch --no-sync pytest -q humansearch/tests/test_admin_ai_search*.py
uv run --project humansearch --no-sync pytest -q
uv run --project humansearch --no-sync ruff check humansearch/src humansearch/tests
uv run --project humansearch --no-sync mypy --strict humansearch/src
bash verify.sh
bash scripts/acceptance-hs-gates.sh
```

브라우저는 `http://127.0.0.1:8766/ai-search`에서 주차 선택, 후보 서치 원장, 주간 컨택 원장을
각각 확인하고, 로컬 오류 주입 fixture로 빈 상태와 오류 상태를 확인한다. 콘솔 오류와 외부 쓰기는
모두 0이어야 한다.
