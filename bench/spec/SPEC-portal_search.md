# SPEC — portal_search (사람인/잡코리아 인재검색 요청 빌더 — 순수 함수, 라이브 브라우징 없음)

대상 모듈 경로: `apps/aisearch/core/portal_search.py`

## 1. 모듈 목적

동일 JD 기반 키워드로 두 채널 — 사람인 talent-pool, 잡코리아 Corp/Person/Find — 검색을 기술하는 **디스크립터**(대상 URL, 입력 필드 셀렉터, 키워드 값, 실행 순서)를 생성한다. 이 모듈은 네트워크/브라우저/파일 I/O를 일절 하지 않는 순수 함수 계층이며, 실제 입력은 별도 드라이버가 디스크립터를 읽어 수행한다. 모든 URL·셀렉터·제약의 출처는 `docs/search-access.md`의 기존 DOM 계약이다.

## 2. 공개 API — 모듈 상수 (값 정확히 일치 필요)

### 사람인 계약

| 이름 | 값 |
|---|---|
| `SARAMIN_SEARCH_URL` | `"https://www.saramin.co.kr/zf_user/memcom/talent-pool/main/search"` |
| `SARAMIN_LOGIN_URL` | `"https://www.saramin.co.kr/zf_user/auth?ut=c&url=https%3A%2F%2Fwww.saramin.co.kr%2Fzf_user%2Fmemcom%2Ftalent-pool%2Fmain%2Fsearch"` (기업회원 ut=c 로그인 + URL 인코딩된 복귀 주소) |
| `SARAMIN_OR_SELECTOR` | `"div.search_keyword input.search_input"` |
| `SARAMIN_AND_SELECTOR` | `"input.search_input.result"` |
| `SARAMIN_CAREER_MIN_SELECTOR` | `"#career_min"` |
| `SARAMIN_CAREER_MAX_SELECTOR` | `"#career_max"` |
| `SARAMIN_KEYWORD_MAXLEN` | `30` (input maxlength=30) |
| `CAREER_VALUE_MIN` | `0` |
| `CAREER_VALUE_MAX` | `20` (경력 select 값 범위 0~20, 양 끝 포함) |

### 잡코리아 계약

| 이름 | 값 |
|---|---|
| `JOBKOREA_SEARCH_URL` | `"https://www.jobkorea.co.kr/Corp/Person/Find"` |
| `JOBKOREA_KEYWORD_SELECTOR` | `"#txtKeyword"` |
| `JOBKOREA_KEYWORD_MAXLEN` | `300` |
| `JOBKOREA_EDUCATION_SELECTOR` | `"#education1"` |
| `JOBKOREA_EDUCATION_VALUE` | `"대학교(4년) 졸업"` |
| `JOBKOREA_CAREER_MIN_SELECTOR` | `"#txtCareerStart"` |
| `JOBKOREA_CAREER_MAX_SELECTOR` | `"#txtCareerEnd"` |

### 스텝 입력 종류 (드라이버가 입력 방식을 구분하는 태그)

| 이름 | 값 | 의미 |
|---|---|---|
| `STEP_KIND_TEXT` | `"text"` | 신뢰 텍스트 입력(CDP Input.insertText) |
| `STEP_KIND_CHECKBOX` | `"checkbox"` | 마우스 클릭 시퀀스(value 대입 금지) |
| `STEP_KIND_SELECT` | `"select"` | `<select>` 옵션 선택 |

### 함수

```python
def build_portal_search_descriptors(
    *,
    or_keywords: list[str] | None = None,
    and_keywords: list[str] | None = None,
    not_keywords: list[str] | None = None,
    exclude_keywords: list[str] | None = None,
    career_min: int | None = None,
    career_max: int | None = None,
) -> list[dict[str, Any]]
```

모든 인자는 **키워드 전용**이다. 순수 함수: 같은 입력이면 항상 같은 출력, 입력 리스트를 변형하지 않으며 I/O가 없다. 검증 실패 시 `ValueError` — 부분 디스크립터를 반환하지 않는다(fail-closed).

## 3. 검증 규칙 (수행 순서 고정)

### 3-1. `not_keywords` 명시적 거부 (가장 먼저)

`not_keywords`가 truthy면(비어있지 않은 리스트 등) 즉시 `ValueError`. 메시지(정확히):
`not_keywords: 미지원 — 사람인 NOT 필드는 AND 필드와 셀렉터가 동일해 (docs/search-access.md:173-176) 안전하게 구분 입력할 수 없다. 제외 조건 없이 검색한 뒤 후처리로 걸러라.`

설계 의도(이것이 계약이다): 사람인 NOT 입력 필드는 AND 필드와 마크업이 완전히 동일한 `input.search_input.result`라서 NOT 전용 셀렉터가 존재하지 않는다. 같은 셀렉터로 NOT 값을 넣으면 제외어가 **필수어(AND)로 검색되는 조용한 오동작**이 되므로 fail-closed로 거부한다. `not_keywords=None`이나 `[]`(falsy)는 통과.

### 3-2. 키워드 리스트 검증 (`or_keywords` → `and_keywords` → `exclude_keywords` 순, 세 인자 공통 규칙)

- `None` → 빈 리스트로 취급.
- 리스트가 아니면(특히 문자열 단독) `ValueError`: `{인자명}: 키워드는 list[str] 만 허용(문자열 단독 입력 금지): {값!r}` — 문자열 `"SaaS"`를 넣으면 글자 단위로 분해되던 결함의 재발 방지.
- 각 원소에 대해 순서대로:
  1. str이 아니거나 strip 결과가 빈 문자열이면 `ValueError`: `{인자명}: 빈 키워드는 허용되지 않는다: {원소!r}`
  2. strip 적용.
  3. 길이가 30(`SARAMIN_KEYWORD_MAXLEN`) 초과면 `ValueError`: `{인자명}: 키워드 30자 초과(사람인 maxlength=30): {키워드!r}` — 30자 정확히는 허용, 31자부터 거부. **exclude_keywords에도 동일 적용**.
  4. 문장형 입력 거부: `.` 또는 `。`로 끝나거나, `"습니다"` 또는 `"합니다"`를 포함하면 `ValueError`: `{인자명}: 문장형 입력 금지(키워드만 허용): {키워드!r}` — 출처 규칙: "OR/AND 조건에는 키워드만 넣어라, 절대 완전한 문장을 넣지 마라".
  5. 중복 제거: 이미 나온 키워드(strip 후 원문 그대로 비교, 대소문자 구분)는 **순서를 보존하며** 건너뛴다.

### 3-3. 키워드 존재 검증

정제 후 `or` 와 `and` 가 **둘 다** 비어 있으면 `ValueError`: `키워드가 하나도 없다 — 검색 디스크립터를 만들 수 없다` (exclude만 있는 경우도 이 에러).

### 3-4. 경력 검증

`career_min`, `career_max` 각각(이 순서로):
- `None`이면 통과(해당 스텝 생략).
- int가 아니거나 **bool이면** `ValueError`: `{인자명}: 정수만 허용: {값!r}` (True/False는 int의 서브클래스지만 명시적 거부).
- 0~20 범위 밖(양 끝 포함이 허용 범위)이면 `ValueError`: `{인자명}: 0~20 범위 밖: {값!r}`
- 둘 다 주어졌고 `career_min > career_max`면 `ValueError`: `경력 범위 역전: min={career_min} > max={career_max}` (같은 값은 허용).

## 4. 출력 스키마

반환은 **항상 길이 2 리스트**, 순서 고정: `[사람인 디스크립터, 잡코리아 디스크립터]`.

### 사람인 디스크립터 (dict 키)

| 키 | 값 |
|---|---|
| `channel` | `"saramin"` |
| `url` | `SARAMIN_SEARCH_URL` |
| `login_url` | `SARAMIN_LOGIN_URL` (사람인에만 있음) |
| `dedup_key` | §5 규칙 |
| `steps` | §6 규칙 |
| `post_filter_exclude` | 정제된 exclude 키워드의 새 리스트(복사본) |

### 잡코리아 디스크립터 (dict 키)

| 키 | 값 |
|---|---|
| `channel` | `"jobkorea"` |
| `url` | `JOBKOREA_SEARCH_URL` |
| `dedup_key` | §5 규칙 |
| `steps` | §6 규칙 |
| `post_filter_exclude` | 정제된 exclude 키워드의 새 리스트 — 사람인 것과 **다른 리스트 객체** |

`login_url`은 잡코리아에는 없다. `post_filter_exclude` 설계 의도: 제외어는 검색 입력 단계(steps)에 절대 싣지 않고, 결과 후처리 단계가 이 목록으로 제외를 적용한다.

## 5. `dedup_key` — 중복 제출 차단용 결정론적 키

같은 검색 의도면 호출 시점·키워드 표기(대소문자·중복·순서)와 무관하게 항상 같은 키가 나와야 한다. 형식(정확히):

```
{channel}|or={norm_or}|and={norm_and}
```

여기서 `norm_or`/`norm_and`는 정제된 각 키워드 리스트를 `casefold()` → 집합화(중복 제거) → 사전순 정렬 → `","` 로 연결한 것이다. 예: or=`["Python", "python", "Java"]` → `or=java,python`. 빈 리스트면 빈 문자열(`or=`).

## 6. `steps` — 실행 순서 배열

각 step은 dict: `{"order": <1부터 연번>, "field": <필드명>, "selector": <셀렉터>, "values": <list[str]>, "kind": <스텝 종류>}`. `order`는 디스크립터마다 1부터 다시 시작. `values`는 항상 새 리스트.

### 사람인 steps (있는 것만, 이 순서로)

| field | selector | values | kind | 포함 조건 |
|---|---|---|---|---|
| `or_keywords` | `SARAMIN_OR_SELECTOR` | 정제된 or 키워드 전체 | `"text"` | or 키워드 1개 이상 |
| `and_keywords` | `SARAMIN_AND_SELECTOR` | 정제된 and 키워드 전체 | `"text"` | and 키워드 1개 이상 |
| `career_min` | `"#career_min"` | `[str(career_min)]` | `"select"` | career_min이 None 아님 |
| `career_max` | `"#career_max"` | `[str(career_max)]` | `"select"` | career_max가 None 아님 |

사람인 경력은 `<select>` 요소라 옵션 선택(kind="select")으로 조작하고, 값은 문자열로 변환해 싣는다.

### 잡코리아 steps (이 순서로)

| field | selector | values | kind | 포함 조건 |
|---|---|---|---|---|
| `keyword` | `"#txtKeyword"` | `[<or키워드들 + and키워드들을 이 순서로 공백 1개로 연결한 단일 문자열>]` | `"text"` | 항상 |
| `education` | `"#education1"` | `["대학교(4년) 졸업"]` | `"checkbox"` | 항상 |
| `career_min` | `"#txtCareerStart"` | `[str(career_min)]` | `"text"` | career_min이 None 아님 |
| `career_max` | `"#txtCareerEnd"` | `[str(career_max)]` | `"text"` | career_max가 None 아님 |

- 잡코리아는 통합검색 1필드: 동일 JD의 OR+AND 키워드를 공백으로 결합한다(순서: or 먼저, and 다음, 각 리스트 내부 순서 보존). NOT 제외는 잡코리아 통합검색이 지원하지 않으므로 넣지 않는다.
- 결합 문자열이 300자(`JOBKOREA_KEYWORD_MAXLEN`) 초과면 `ValueError`: `잡코리아 통합검색 300자 초과: {길이}자` (300자 정확히는 허용). 결합 결과가 빈 문자열이면 `ValueError`(`잡코리아 통합검색 키워드가 비었다(OR/AND 키워드 필요)`) — §3-3 검증 때문에 실전에서는 도달하지 않지만 방어선으로 존재한다.
- `education`은 체크박스다 — value 대입이 아니라 클릭 이벤트 시퀀스로 조작해야 하며, 그래서 kind="checkbox"로 드라이버에 알린다. 잡코리아 상세검색 학력은 "대학교(4년) 졸업" 하나만 지원한다.

## 7. 불변식

- 순수성: 같은 인자로 두 번 호출하면 동등한 결과. 입력으로 받은 리스트 객체는 절대 변형되지 않는다.
- `steps`의 어떤 step에도 제외어가 실리지 않는다(제외는 오직 `post_filter_exclude`).
- 두 디스크립터의 `post_filter_exclude`는 내용이 같아도 별개 리스트 객체다(한쪽 변조가 다른 쪽에 새면 안 됨).
- 에러 시 부분 결과 없음 — 예외 아니면 완전한 2건.

## 8. 주입 지점

없음(순수 함수 모듈). 드라이버·브라우저는 이 모듈 밖이다.

## 9. 의도적으로 거부하는 것 (전부 계약)

- `not_keywords` — 미지원, truthy면 즉시 거부 (§3-1의 이유).
- 문자열 단독 키워드 인자, 빈 키워드, 30자 초과 키워드, 문장형 키워드.
- bool 경력값, 0~20 밖 경력값, min>max 역전.
- OR·AND 모두 빈 검색.
- 잡코리아 통합검색 300자 초과.
