# HumanSearch 이력서 열람 증거 계약 (SOT)

최종 갱신: 2026-09-14

## 1층 — 결론

HumanSearch가 후보 이력서나 LinkedIn Recruiter 상세를 열람했다고 기록하려면, 나중에 사람이 그 기록만 보고
어떤 원문을 어느 구간까지 봤는지 판단할 수 있어야 한다. 이 문서는 저장 코드가 남겨야 하는 최소 증거 필드와
가짜 완료를 막는 반례를 고정한다.

이 문서는 브라우저 조작, 포털 로그인, SQLite 스키마, 암호화 구현, Supabase 동기화, 실제 후보 데이터 저장을
완료했다고 말하지 않는다. 후속 구현은 이 계약을 입력으로 삼아 저장 계층과 독립 재조회 시험을 별도로 만들어야 한다.

## 2층 — 판단 근거

이력서 증거의 핵심은 "열람했다"는 말이 아니라 재현 가능한 경계다. 출처 주소, 관측 시각, 문서 높이,
캡처 구간 좌표와 해시, 전체/부분 판정, 실패 사유가 함께 있어야 전체 열람과 일부 열람을 구분할 수 있다.

빈 값도 같은 이유로 세 가지를 나눠야 한다. 원문에 실제로 없었던 값, 화면에 보였지만 비어 있던 값, 아직
관측하지 못한 값은 사업 판단이 다르다. 특히 회사별 담당 업무와 검색 조건, 회사 별칭은 후보 중복 방지와
재검색 가능성에 직접 연결된다.

**무엇을** — 열람 증거 한 건의 필수 필드와 8개 반례를 SOT로 둔다.

**왜** — 후속 저장 구현이 "무엇을 남겨야 충분한가"를 다시 추측하지 않게 하기 위해서다.

**버린 길** — 화면 텍스트 일부와 URL만 저장하는 길은 버린다. 긴 페이지 누락, 빈 값 오인, 검색 조건 소실을
나중에 구분하지 못한다.

**대가** — 캡처 구간과 해시를 남겨야 하므로 저장량과 검증 절차가 늘어난다.

**되돌리기** — 후속 구현 전에는 이 문서와 goal 연결을 되돌리면 된다. 저장 구현 뒤에는 마이그레이션과
readback 시험을 함께 되돌려야 한다.

## 3층 — 정본 계약

### 1. 적용 범위

이 계약은 채용 포털 목록, 후보 상세, 이력서, LinkedIn Recruiter 상세처럼 후보 판단의 원문 근거가 되는
화면을 대상으로 한다. 채널은 `saramin`, `jobkorea`, `linkedin_rps` 중 하나로 적는다.

브라우저 선택, Aside 전용 자동화, Chrome 비간섭, 사용권, 목표 탭 선택, 사람 입력 회수는
`docs/sot/humansearch-browser-contract.md`가 소유한다. 이 문서는 화면을 열람한 뒤 저장해야 할 증거의 모양만
소유한다.

### 2. 증거 한 건의 필드

아래 필드는 후보자 개인정보 원문을 Git에 넣으라는 뜻이 아니다. 원문과 캡처 파일은 후속 저장 계약이 정하는
보호 위치에 두고, Git에는 비민감 지문과 계약만 남긴다.

| 필드 | 필수 | 타입 | 계약 |
|---|---:|---|---|
| `evidence_id` | 예 | opaque string | 저장 계층 안에서 유일한 열람 증거 식별자다. |
| `run_id` | 예 | opaque string | 검색 실행 또는 재개 실행의 식별자다. |
| `position_ref` | 예 | string | ClickUp 포지션 ID 또는 후속 계약이 승인한 포지션 식별자다. |
| `channel` | 예 | enum | `saramin`, `jobkorea`, `linkedin_rps` 중 하나다. |
| `candidate_ref` | 조건부 | string 또는 null | `candidate_ref_state=observed`이면 비어 있지 않은 문자열이다. 그 밖의 상태이면 null이다. |
| `candidate_ref_state` | 예 | enum | `observed`, `not_observed`, `not_available` 중 하나다. |
| `source_url` | 예 | URL string | query 안의 계정·세션·후보 민감값은 보호 저장소 원문에만 두고 보고용에는 정규화 URL을 둔다. |
| `source_url_hash` | 예 | sha256 hex | 민감 URL 원문을 일반 로그에 쓰지 않고도 동일 출처를 대조하는 지문이다. |
| `observed_at` | 예 | RFC3339 timestamp | 화면을 관측한 시각이다. 저장 시각과 다를 수 있다. |
| `browser_context_ref` | 예 | string | Aside 앱·프로필·탭 증거의 참조다. Chrome 탭이나 전역 입력을 가리키면 안 된다. |
| `search_condition_ref` | 예 | string | 어떤 검색 조건에서 나온 후보인지 가리킨다. 검색 조건 본문은 §5 형식을 따른다. |
| `document_height_px` | 조건부 | integer >= 0 또는 null | `height_state=observed_stable`이면 최종 안정화 뒤 문서 전체 높이다. 그 밖의 상태이면 null이다. |
| `height_state` | 예 | enum | `observed_stable`, `observed_changed`, `not_observed`, `not_applicable` 중 하나다. |
| `height_observation_note` | 조건부 | string | 높이가 바뀌었거나 관측되지 않았을 때 필수다. |
| `viewport_width_px` | 예 | integer >= 0 | 캡처 구간 좌표 해석에 필요한 화면 폭이다. |
| `viewport_height_px` | 예 | integer >= 0 | 캡처 구간 좌표 해석에 필요한 화면 높이다. |
| `segments` | 예 | array | §3의 캡처 구간 목록이다. 1개 이상이어야 한다. |
| `coverage_status` | 예 | enum | `complete`, `partial`, `failed` 중 하나다. |
| `coverage_reason` | 예 | string | `partial` 또는 `failed`일 때 사람이 이해할 수 있는 이유다. `complete`이면 `all_segments_observed`를 적는다. |
| `last_observed_y_px` | 예 | integer >= 0 | 마지막으로 관측한 세로 위치다. 어디까지 봤는지 복원하는 경계다. |
| `extracted_fields` | 예 | object | §4의 NULL/미관측 구분 규칙을 따르는 추출 결과다. |
| `company_duties` | 조건부 | array | `company_duties_state=observed`이면 1개 이상이다. 그 밖의 상태이면 빈 배열이어도 된다. |
| `company_duties_state` | 예 | enum | `observed`, `observed_empty`, `not_observed`, `not_available`, `redacted` 중 하나다. |
| `company_aliases` | 예 | array | §7의 회사 별칭 목록이다. 표준명 추정만 있고 근거가 없으면 별칭으로 확정하지 않는다. |
| `observed_contact_fields` | 예 | object | 화면에 보인 연락처 필드의 관측 상태만 남긴다. 연락처 수집 허용과 패킷 사용은 후속 계약이 소유한다. |
| `readback_status` | 예 | enum | `not_run`, `matched`, `mismatch`, `blocked` 중 하나다. |
| `readback_at` | 조건부 | RFC3339 timestamp | 재조회가 실행됐을 때 필수다. |
| `readback_failure_reason` | 조건부 | string | `mismatch` 또는 `blocked`일 때 필수다. |

→ 표가 말하는 것: 증거 한 건은 출처, 시각, 브라우저 맥락, 검색 조건, 캡처 범위, 전체/부분 상태, 재조회 상태를 함께 가져야 한다. 조건부 필드는 상태값과 실제 값 모양이 서로 맞아야 한다.

검사 명령:

```bash
rg -n '`candidate_ref`.*조건부|`document_height_px`.*조건부|`company_duties_state`|`observed_contact_fields`|`source_url`|`observed_at`|`segments`|`coverage_status`|`coverage_reason`|`readback_status`' docs/sot/humansearch-evidence-contract.md
```

→ 이 명령은 증거의 출처, 시각, 조건부 후보 식별자와 높이, 구간, 전체/부분/실패 판정, 연락처 관측 상태, 재조회 상태 필드가 문서에 있는지 확인한다.

### 3. 캡처 구간 manifest

`segments`의 각 항목은 아래 필드를 가진다.

| 필드 | 필수 | 타입 | 계약 |
|---|---:|---|---|
| `segment_index` | 예 | integer >= 0 | 같은 증거 안에서 0부터 증가한다. |
| `top_y_px` | 예 | integer >= 0 | 문서 기준 구간 시작 좌표다. |
| `bottom_y_px` | 예 | integer >= 0 | 문서 기준 구간 끝 좌표다. `top_y_px`보다 커야 한다. |
| `capture_sha256` | 예 | sha256 hex | 캡처 파일의 지문이다. |
| `text_sha256` | 조건부 | sha256 hex | OCR 또는 텍스트 추출 결과가 있을 때 필수다. |
| `capture_ref` | 예 | string | 보호 저장소 안의 캡처 참조다. Git 경로나 외부 원격 URL이 아니다. |
| `segment_status` | 예 | enum | `observed`, `failed`, `redacted` 중 하나다. |
| `failure_reason` | 조건부 | string | `failed`일 때 필수다. |

→ 표가 말하는 것: 캡처는 파일 하나가 아니라 문서 좌표 구간과 파일 지문을 가진 조각들의 목록이다.

`coverage_status=complete`가 되려면 `height_state=observed_stable`이고, `segment_status=observed`인 구간만으로
`0..document_height_px` 범위를 누락 없이 덮어야 한다. `failed`나 `redacted` 구간은 전체 열람을 증명하는
덮개로 계산하지 않는다. 구간 사이에 빈 공간이 있거나 마지막 관측 구간의 `bottom_y_px`가 문서 높이보다
작으면 `partial`이다. 스크롤 중 문서 높이가 바뀌어 최종 안정 높이를 확정하지 못하면 `height_state=observed_changed`이고
`coverage_status`는 `partial` 또는 `failed`다.

검사 명령:

```bash
rg -n '`top_y_px`|`bottom_y_px`|`capture_sha256`|`failure_reason`|`segment_status=observed`|`observed_changed`|누락 없이|`partial`' docs/sot/humansearch-evidence-contract.md
```

→ 이 명령은 구간 좌표, 해시, 실패 사유, 동적 높이 처리와 전체/부분 판정 기준이 문서에 있는지 확인한다.

### 4. NULL, 빈 값, 미관측 구분

추출 필드는 값을 바로 문자열로 접지 않는다. 각 필드는 아래 모양을 따른다.

```json
{
  "value": "string | number | array | object | null",
  "state": "observed_value | observed_empty | not_observed | not_available | redacted",
  "source_segment_indexes": [0],
  "evidence_note": "optional human-readable note"
}
```

→ 이 모양은 화면에서 빈 값을 본 경우와 아직 보지 못한 경우를 같은 값으로 접지 않게 한다.

`observed_empty`는 화면에서 비어 있음을 보았다는 뜻이다. `not_observed`는 아직 보지 못했다는 뜻이다.
`not_available`은 포털이 제공하지 않는 항목임을 확인했다는 뜻이다. 세 상태를 모두 빈 문자열이나 NULL 하나로
합치면 안 된다.

`observed_contact_fields`도 이 모양을 따른다. 화면에 보인 연락처만 `observed_value`로 남기며, 보이지 않는
이메일·전화번호·메신저 주소를 추정하지 않는다. 연락처를 수집해도 되는 채널 조건, 저장 암호화, 패킷 사용 여부는
후속 저장·패킷 계약이 소유한다.

검사 명령:

```bash
rg -n 'observed_empty|not_observed|not_available|redacted|source_segment_indexes|observed_contact_fields|추정하지 않는다' docs/sot/humansearch-evidence-contract.md
```

→ 이 명령은 값 없음과 미관측이 서로 다른 상태로 남고, 연락처가 보이는 값 관측으로만 제한되는지 확인한다.

### 5. 검색 조건 보존

검색 조건은 후보 증거와 분리해 보존하되, 후보 증거는 `search_condition_ref`로 반드시 연결한다.

최소 필드는 다음과 같다.

| 필드 | 필수 | 계약 |
|---|---:|---|
| `search_condition_id` | 예 | 같은 조건을 다시 찾는 식별자다. |
| `channel` | 예 | 후보 증거의 채널과 같아야 한다. |
| `position_ref` | 예 | 후보 증거의 포지션과 같아야 한다. |
| `query_text` | 조건부 | Boolean 검색식이나 키워드가 있으면 원문을 보존한다. |
| `filters_json` | 예 | 국가, 경력, 직무, 회사, 제외어 등 실제 적용한 필터다. |
| `applied_result_proof` | 조건부 | 화면에서 필터가 적용됐음을 확인한 증거 참조다. RPS 프로젝트 필터는 생성·업데이트 후 재조회 증거가 필요하다. |
| `created_or_updated_at` | 예 | 조건을 확정한 시각이다. |

→ 표가 말하는 것: 후보 증거는 검색 조건 원문을 복사하지 않고 안정 참조로 연결하며, RPS 필터는 화면 적용 결과를 다시 읽은 증거가 필요하다.

RPS 프로젝트가 없으면 만들고 있으면 필터를 업데이트한다는 최신 결정은 별도 RPS 입력 계약 WU가 소유한다.
이 문서는 그 결과를 이력서 증거가 참조할 수 있도록 검색 조건 연결 필드만 요구한다.

검사 명령:

```bash
rg -n '`search_condition_ref`|`filters_json`|`applied_result_proof`|RPS 프로젝트|재조회 증거' docs/sot/humansearch-evidence-contract.md
```

→ 이 명령은 후보가 어떤 검색에서 나왔는지와 RPS 필터 재조회 증거를 연결하는 필드가 있는지 확인한다.

### 6. 회사별 담당 업무

경력 항목은 회사 단위로 나눠 저장한다. 여러 회사의 담당 업무를 하나의 긴 문자열로 합치면 안 된다.
`company_duties_state=observed`인데 `company_duties`가 빈 배열이면 계약 위반이다. 반대로 경력 구간을
관측하지 못했으면 `company_duties_state=not_observed`와 빈 배열을 함께 쓸 수 있다.

`company_duties`의 각 항목은 아래 필드를 가진다.

| 필드 | 필수 | 계약 |
|---|---:|---|
| `company_observed_name` | 예 | 화면에서 본 회사명이다. |
| `company_alias_ref` | 조건부 | §7의 별칭 항목과 연결할 때만 둔다. |
| `role_title` | 조건부 | 해당 회사의 직무명이다. |
| `date_range` | 조건부 | 해당 회사의 재직 기간이다. |
| `duty_text` | 조건부 | 해당 회사에 귀속된 담당 업무다. |
| `duty_state` | 예 | `observed_value`, `observed_empty`, `not_observed`, `not_available`, `redacted` 중 하나다. |
| `source_segment_indexes` | 예 | 근거가 나온 캡처 구간이다. |

→ 표가 말하는 것: 담당 업무는 후보 전체 요약이 아니라 각 회사 경력 항목에 붙어야 한다.

검사 명령:

```bash
rg -n '`company_duties`|`company_duties_state`|`company_observed_name`|`duty_text`|`duty_state`|`source_segment_indexes`|빈 배열' docs/sot/humansearch-evidence-contract.md
```

→ 이 명령은 담당 업무가 후보 전체가 아니라 회사별 경력 항목에 붙고, 배열과 상태값의 조합이 판정 가능하게 적혔는지 확인한다.

### 7. 회사 별칭

회사 별칭은 같은 회사를 다른 표기로 본 사실을 보존하기 위한 항목이다. 유사한 이름이라는 추정만으로
같은 회사라고 확정하지 않는다.

`company_aliases`의 각 항목은 아래 필드를 가진다.

| 필드 | 필수 | 계약 |
|---|---:|---|
| `alias_text` | 예 | 화면에서 관측한 표기다. |
| `canonical_company_ref` | 조건부 | 후속 회사 정본과 연결될 때만 둔다. |
| `alias_basis` | 예 | `same_profile`, `same_company_page`, `operator_confirmed`, `not_confirmed` 중 하나다. |
| `source_segment_indexes` | 예 | 별칭 근거가 나온 구간이다. |

→ 표가 말하는 것: 별칭은 표기와 근거 상태를 함께 남기며, 확인되지 않은 별칭은 병합 근거가 아니다.

`not_confirmed` 별칭은 중복 병합에 쓰지 않는다. 중복 후보 방지는 확인된 별칭이나 안정 식별자만 사용한다.

검사 명령:

```bash
rg -n '`company_aliases`|`alias_text`|`canonical_company_ref`|`alias_basis`|`not_confirmed`' docs/sot/humansearch-evidence-contract.md
```

→ 이 명령은 별칭을 추정 병합과 구분해 저장하는지 확인한다.

### 8. readback과 저장 실패

저장했다고 말하려면 독립 재조회 상태를 남겨야 한다. `readback_status=matched`가 아니면 저장 완료가 아니다.

`readback_status=blocked`는 권한, 암호화 키, 저장소 잠금, 브라우저 사용권 만료처럼 후속 구현이 구분해야 하는
실패를 뜻한다. 저장 실패나 손상 의심이 있으면 후보 순회를 계속하지 않고 중단 사유를 실행 장부에 연결한다.

검사 명령:

```bash
rg -n '`readback_status`|`matched`|`mismatch`|`blocked`|저장 완료가 아니다|중단 사유' docs/sot/humansearch-evidence-contract.md
```

→ 이 명령은 저장 성공 주장과 독립 재조회 성공을 분리하는지 확인한다.

### 9. 8개 counter-AC

| # | counter-AC | 차단 조건 |
|---:|---|---|
| 1 | 구간 무누락 manifest | 구간 사이가 비었는데 전체 열람이라고 기록한다. |
| 2 | 마지막 화면 | 마지막 관측 위치가 없어 어디까지 봤는지 모른다. |
| 3 | NULL 구분 | 값 없음과 미관측을 같은 빈 값으로 저장한다. |
| 4 | 회사별 duty | 여러 회사의 담당 업무를 하나로 합친다. |
| 5 | 검색 조건 보존 | 어떤 검색 조건에서 나온 후보인지 잃는다. |
| 6 | 원격 경로 금지 | 캡처 원본 참조가 통제 밖 원격 URL뿐이다. |
| 7 | readback | 저장했다고만 하고 다시 읽어 대조하지 않는다. |
| 8 | 회사 별칭 | 같은 회사의 다른 표기를 근거 없이 병합한다. |

→ 표가 말하는 것: 각 반례는 이 문서의 필드와 연결된다. 후속 구현은 이 명령들을 더 강한 런타임 시험으로 바꿔야
하지만, 이번 문서 WU는 새 범용 검사기를 만들지 않는다.

1. 구간 무누락 manifest 검사 명령:

```bash
rg -n '누락 없이|0..document_height_px|구간 사이' docs/sot/humansearch-evidence-contract.md
```

→ 이 명령은 전체 열람 판정이 문서 높이와 구간 연속성 조건에 묶였는지 확인한다.

2. 마지막 화면 검사 명령:

```bash
rg -n '`last_observed_y_px`|마지막으로 관측한' docs/sot/humansearch-evidence-contract.md
```

→ 이 명령은 마지막 관측 위치가 별도 필드와 설명으로 남는지 확인한다.

3. NULL 구분 검사 명령:

```bash
rg -n 'observed_empty|not_observed|not_available' docs/sot/humansearch-evidence-contract.md
```

→ 이 명령은 빈 값, 미관측, 제공 안 됨을 서로 다른 상태로 쓰는지 확인한다.

4. 회사별 duty 검사 명령:

```bash
rg -n '`company_duties`|`duty_text`|회사 단위' docs/sot/humansearch-evidence-contract.md
```

→ 이 명령은 담당 업무가 회사별 경력 구조에 연결되는지 확인한다.

5. 검색 조건 보존 검사 명령:

```bash
rg -n '`search_condition_ref`|`filters_json`' docs/sot/humansearch-evidence-contract.md
```

→ 이 명령은 후보 증거가 검색 조건 참조와 실제 필터 본문을 잃지 않는지 확인한다.

6. 원격 경로 금지 검사 명령:

```bash
rg -n '보호 저장소|Git 경로나 외부 원격 URL이 아니다' docs/sot/humansearch-evidence-contract.md
```

→ 이 명령은 캡처 원본 참조가 통제 밖 원격 URL이나 Git 경로로만 남지 않도록 하는 문구를 확인한다.

7. readback 검사 명령:

```bash
rg -n '`readback_status`|독립 재조회' docs/sot/humansearch-evidence-contract.md
```

→ 이 명령은 저장 성공 주장이 독립 재조회 상태와 분리돼 있는지 확인한다.

8. 회사 별칭 검사 명령:

```bash
rg -n '`company_aliases`|`alias_basis`|`not_confirmed`' docs/sot/humansearch-evidence-contract.md
```

→ 이 명령은 별칭 근거 상태와 확인되지 않은 별칭의 제한이 남아 있는지 확인한다.

### 10. 비범위와 현재 상태

- SQLite 스키마, 암호화 저장, Supabase 파생 저장, 실제 이력서 저장 구현은 후속 WU가 소유한다.
- Aside 내부 조작과 실제 포털 접속은 이 문서로 승인되지 않는다.
- RPS 프로젝트 생성·기존 필터 업데이트의 쓰기 계약은 별도 WU가 소유한다.
- main 병합이 필요한 선행 계약은 이 브랜치에서 아직 충족됐다고 주장하지 않는다. 이 문서는 로컬 SOT 초안이다.
- 문서형 WU라서 제품 배송 상태는 `NOT_APPLICABLE`이다.
