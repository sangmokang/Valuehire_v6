# AI Search 관리자 증거 화면 Spec — 2026-10-29

## 1. 목적과 단일 인수 기준

운영자가 Gmail에서 실제로 확인된 AI Search 실행 결과를 기준으로 전역 고유 후보 수, 후보별 모든
포지션·Batch, 검증 가능한 점수와 직접 컨택 이력을 한 화면에서 구분해 확인한다. 증거가 없는 상세는
0이나 빈 문자열이 아니라 `NOT_RUN`과 사람이 읽을 수 있는 사유로 표시한다.

## 2. 2026-10-29 실데이터 기준선

읽기 전용 query `subject:aisearch -in:spam -in:trash`를 4페이지 끝까지 조회했다.

- Gmail 354통: 실행 352, 테스트·비실행 제외 2
- Batch 308, 실행 주체 근거 완전 308/308
- 후보 count 확정 244/308 Batch
- `raw 9,256 = parsed 8,648 + duplicate 366 + unparsed 242 + excluded 0`
- 고유 후보 프로필 6,831
- 후보–Batch 등장 8,648
- 고객사·포지션 확인 연결 7,937, 미확인 연결 711
- 점수 확인 후보 0, 학력 17, 전체 경력 4, 핵심 경력 0
- 필수요건별 근거 0, 적합 근거 0, 더 적합한 포지션 0, 컨택 의견 근거 2
- 검색 기간 확인 0/308

보낸편지 query는 1페이지에서 종료됐다. 직접 제안 8, 분류는 `AI 7 / OWNER 1 / UNKNOWN 0`,
후보 연결 0 / 미연결 8이다. 미연결 사유는 메일에 후보 정본 프로필 URL이 없기 때문이다.

## 3. API 계약

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

1. 상단 사실 카드: 검색 실행, 고유 후보, 포지션 연결, 확인된 점수, 직접 제안과 후보 연결
2. 자료 완성도: 학력·전체 경력·핵심 경력·필수요건·적합 근거·대안 포지션·컨택 의견의
   `채움 수 / 6,831`
3. 고유 후보 목록: 프로필, 확인된 점수, 포지션·검색 묶음, 후보 연결 컨택
4. 후보 상세: 위 상세 필드, 포지션별 점수, 모든 Batch, 모든 연결 컨택
5. 직접 컨택 장부: AI/직접/미확인, 발송일, 제목, 후보 연결 상태
6. Batch 목록과 Batch 상세

필수 검증 상태는 목록 상태, 상세 상태, 빈 상태, 오류 상태 네 가지다.

## 6. 실패·반례 계약

- pagination 미종료 → 전체 수집 PASS 금지
- 점수 네 축 누락 → 총점과 점수대 NOT_RUN
- 메일 총점만 존재 → 네 축 점수로 변환 금지
- 후보 이름만 일치 → cross-channel 병합 금지
- 제안 메일에 후보 URL 없음 → 후보 컨택 연결 금지
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

브라우저는 `http://127.0.0.1:8766/ai-search`에서 후보 상세와 Batch 상세를 각각 열고, 로컬 오류
주입 fixture로 빈 상태와 오류 상태를 확인한다. 콘솔 오류와 외부 쓰기는 모두 0이어야 한다.
