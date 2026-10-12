# SPEC — boolean_builder (LinkedIn RPS Boolean 키워드 생성기 + 서울 소재 대학 우선 검색 플래너)

대상 모듈 경로: `apps/aisearch/core/boolean_builder.py`
보조 데이터 모듈: `apps/aisearch/core/data/seoul_universities.py` (이 스펙 §9에 전체 내용 포함 — 반드시 별도 모듈로 함께 구현)

## 1. 모듈 목적

채용 JD(직무기술서)의 한/영 혼합 키워드 그룹을 LinkedIn RPS(Recruiter) Keywords 필드에 넣을 수 있는 Boolean 검색 문자열(`("A" OR "B") AND ("C" OR "D")` 형태)로 조합한다. 또한 JD와 위치를 받아 "1차: 서울 소재 4년제 대학 우선 필터 → 소진 시 2차: 대학 제한 해제(확장)"라는 순서 있는 2단계 검색 플랜을 만든다. 핵심 사업 규칙(Counter-AC): JD의 필수요건(경력연차 등)은 대학 필터와 무관하게 **모든 단계에서 게이트로 유지**되어야 한다 — 확장 단계로 넘어가도 필수요건이 약화되면 안 된다.

## 2. 공개 API 목록

### 모듈 상수

| 이름 | 값 | 타입 |
|---|---|---|
| `DEFAULT_LOCATION` | `"South Korea"` | str |
| `STAGE_SEOUL_UNIVERSITY_PRIORITY` | `"seoul_university_priority"` | str |
| `STAGE_EXPANDED` | `"expanded"` | str |
| `ADVANCE_REASON_EXHAUSTED` | `"exhausted"` | str |
| `ADVANCE_REASON_CAP_REACHED` | `"cap_reached"` | str |

내부적으로 허용 전환 사유 집합은 `{"exhausted", "cap_reached"}` 두 개뿐이다(frozenset).

### 함수·클래스

```python
def build_rps_boolean(jd: dict[str, Any]) -> str

@dataclass(frozen=True)
class SearchStage:
    order: int
    name: str
    keywords: str
    location: str
    required_filters: dict[str, Any]
    universities: Optional[tuple[str, ...]] = None

@dataclass
class SearchPlan:
    location: str
    stages: Sequence[SearchStage]
    _index: int = field(default=0, repr=False)

    def current_stage(self) -> SearchStage
    def advance(self, reason: str = "exhausted") -> Optional[SearchStage]
    def is_exhausted(self) -> bool

def build_search_plan(jd: dict[str, Any], location: str = "South Korea") -> SearchPlan
```

- `SearchStage`는 **frozen dataclass** — 생성 후 속성 대입 시 `FrozenInstanceError`.
- `SearchPlan._index`는 내부 진행 커서(기본 0, `repr`에서 제외). 외부 계약은 메서드 3개.

## 3. `build_rps_boolean(jd)` — 입력·출력·에러 계약

### 입력 스키마

`jd`는 dict이며 다음 키를 읽는다:

| 키 | 타입 | 필수 | 의미 |
|---|---|---|---|
| `keyword_groups` | list(또는 tuple) of list(또는 tuple) of str | 필수(실질) | 각 안쪽 리스트 = 한/영 동의어 그룹(OR로 묶임). 그룹끼리는 AND |
| `not_keywords` | list(또는 tuple) of str | 선택 | 제외어. NOT 절로 반영 |

읽는 방식: `jd.get("keyword_groups") or []`, `jd.get("not_keywords")` — 즉 키가 없거나 falsy면 각각 "빈 값" 취급.

### 출력 형식 (정확한 문자열 규칙)

1. 각 그룹 안의 키워드는 앞뒤 공백 strip 후 각각 큰따옴표로 감싸고 `" OR "`로 연결한다.
2. 그룹 전체를 괄호로 감싼다: `("A" OR "B")`.
3. 그룹들을 `" AND "`로 연결한다.
4. `not_keywords`가 있으면(비어있지 않으면) 맨 뒤에 `" NOT ("` + 큰따옴표 감싼 제외어들을 `" OR "` 연결 + `")"`를 붙인다.

예: `keyword_groups=[["백엔드","Backend"],["Python"]]`, `not_keywords=["신입"]` →
`("백엔드" OR "Backend") AND ("Python") NOT ("신입")`

그룹이 1개뿐이어도 괄호는 유지된다. strip 결과가 빈 문자열인 키워드는 그룹에서 조용히 제거된다(단 그 결과 그룹이 통째로 비면 에러 — 아래 참조).

### 키워드 1개 검증 규칙 (모든 키워드·제외어 공통)

각 키워드에 대해 순서대로:

1. `str`이 아니면 `ValueError` — 메시지: `키워드는 문자열이어야 합니다: {term!r} (그룹 {group!r})`
2. strip 후, 금지 문자 `"`(큰따옴표), `(`, `)` 가 **위치와 무관하게 하나라도** 포함되면 `ValueError` — 이스케이프하지 않고 거부한다(주입 위험). 메시지에 `키워드에 Boolean 구문 문자({ch!r})가 들어 있습니다` 와 `주입 위험이므로 거부합니다(이스케이프하지 않음)` 문구 포함.
3. strip된 문자열에서 **대문자 단독 토큰** `OR`/`AND`/`NOT`이 발견되면 `ValueError`. 판정 정규식 의미: 토큰 앞이 문자열 시작 또는 공백이고, 토큰 뒤가 공백 또는 문자열 끝인 경우(즉 `r"(?:^|\s)(?:OR|AND|NOT)(?:\s|$)"` 를 search). 따라서 `"ORACLE"`·`"NOTION"`은 통과, `"OR"` 단독·`"foo OR bar"`·`"OR foo"`는 거부. 소문자 `or`는 통과(대소문자 구분). 메시지에 `Boolean 연산자 토큰(OR/AND/NOT)이 들어 있습니다` 문구 포함.
4. 통과 시 strip된 문자열을 사용한다.

### 에러 계약 (발생 순서대로)

| 조건 | 예외 | 메시지 핵심 문구 |
|---|---|---|
| `keyword_groups`가 truthy인데 str/bytes이거나 list/tuple이 아님 | `ValueError` | `keyword_groups는 리스트의 리스트여야 합니다(문자열 금지): {groups!r}` |
| `keyword_groups`가 없음/falsy(None, `[]`, `""` 등) | `ValueError` | `keyword_groups가 비어 있습니다 — Boolean을 만들 수 없습니다` |
| 그룹 자리에 str/bytes 또는 비 list/tuple이 옴 | `ValueError` | `키워드 그룹은 문자열 리스트여야 합니다 — 문자열이 그룹 자리에 오면 글자 단위로 분해되므로 거부합니다: {group!r}` |
| 키워드 개별 검증 실패 | `ValueError` | 위 검증 규칙의 메시지 |
| 그룹의 키워드가 전부 빈 문자열(strip 후) 또는 그룹이 `[]` | `ValueError` | `빈 키워드 그룹이 있습니다: {group!r}` |
| `not_keywords`가 truthy인데 str/bytes이거나 list/tuple이 아님 | `ValueError` | `not_keywords는 문자열 리스트여야 합니다(문자열 단독 금지): {not_keywords!r}` |
| `not_keywords`의 원소가 전부 빈 값(strip 후) | `ValueError` | `not_keywords가 빈 값뿐입니다: {not_keywords!r}` |

설계 의도: 문자열을 리스트 자리에 넣으면 파이썬 이터레이션으로 **글자 단위 분해**되는 조용한 오동작이 나므로, str/bytes는 컨테이너 자리에서 무조건 명시적 거부한다(fail-fast). 따옴표·괄호·연산자 토큰은 RPS Boolean 구문을 깨뜨리는 주입 벡터이므로 이스케이프 시도 없이 거부한다.

## 4. `build_search_plan(jd, location)` — 계약

### 검증 순서 (테스트가 어느 에러가 먼저 나는지 볼 수 있으므로 순서 고정)

1. **location 검증**: str이 아니거나 strip 결과가 빈 문자열이면 `ValueError` — 메시지: `location이 비어 있습니다 — 빈 위치로는 플랜을 만들지 않습니다: {location!r}`
2. **requirements 검증**: `jd.get("requirements") or {}` 가 falsy면 `ValueError`(fail-closed) — 메시지: `구조화 필수요건(requirements: 경력연차 등)이 없습니다 — 필수요건 게이트 없이는 플랜을 만들지 않습니다(fail-closed)`
3. `build_rps_boolean(jd)` 호출 — 키워드 관련 에러는 여기서 그대로 전파된다.

### 출력

`SearchPlan(location=location, stages=<튜플 2개>)` 를 반환하며 stages는:

| | order | name | keywords | location | required_filters | universities |
|---|---|---|---|---|---|---|
| 1단계 | `1` | `"seoul_university_priority"` | build_rps_boolean 결과 | 입력 location | requirements의 독립 deepcopy | `tuple(SEOUL_UNIVERSITIES)` (§9의 35개, 순서 그대로) |
| 2단계 | `2` | `"expanded"` | 동일한 keywords 문자열 | 입력 location | requirements의 **또 다른** 독립 deepcopy | `None` |

### 불변식 (방어적 복사)

- 각 단계의 `required_filters`는 원본 `jd["requirements"]`의 **deepcopy**이며, 단계마다 **서로 다른 객체**다. 다음이 모두 보장되어야 한다:
  - 플랜 생성 후 원본 `jd["requirements"]`(중첩 값 포함)를 변조해도 어떤 단계의 `required_filters`도 변하지 않는다.
  - 1단계의 `required_filters`를 변조해도 2단계 것은 변하지 않는다(역방향도 동일).
- 두 단계의 `keywords`와 `location`은 같은 값이다 — 대학 필터만 다르다. 필수요건 게이트는 모든 단계에 동일하게 실린다(Counter-AC).

## 5. `SearchPlan` 상태·순서 규칙

- 초기 상태: `_index = 0` → `current_stage()`는 1단계를 반환.
- `advance(reason)`:
  - `reason`이 `"exhausted"` 또는 `"cap_reached"`가 아니면 `ValueError`를 던지고 **상태(현재 단계)는 그대로 유지**된다. 메시지에 `단계 전환은 reason∈['cap_reached', 'exhausted']만 허용합니다` 와 `{reason!r}는 전환 사유가 아닙니다(캡차·오류는 별도 복구 절차)` 문구 포함(허용 집합은 정렬된 리스트로 표기).
  - 다음 단계가 있으면 커서를 1 올리고 **새 현재 단계(SearchStage)를 반환**한다.
  - 마지막 단계에서 호출하면 커서를 `len(stages)`로 올리고 `None`을 반환한다(플랜 소진). 소진 상태에서 또 호출해도 `None`(유효 reason이면 예외 없음).
- `is_exhausted()`: `_index >= len(stages)` 일 때 True. 초기·진행 중에는 False, 마지막 단계에서 `advance`가 `None`을 반환한 뒤 True.
- `current_stage()`: `stages[_index]` 단순 인덱싱 — 소진 후 호출하면 자연스럽게 `IndexError`가 난다(별도 메시지 계약 없음).

설계 의도(E8 catch-all 방지): 캡차·rate limit·일반 오류는 "단계 전환 사유"가 아니라 별도 복구 절차 대상이다. 사유를 두 개로 못박고 나머지는 fail-fast로 거부해, 오류 상황에서 대학 필터가 슬그머니 풀리는 사고를 막는다. `cap_reached`는 20페이지 상한 도달(pagination 모듈의 `switch_boolean_variant` 시그널)로, 소진과 동급의 **정상** 전환 사유다.

## 6. 의도적으로 거부하는 것

- 금지 문자(`"`, `(`, `)`)의 이스케이프 지원 — 하지 않는다. 거부만 한다.
- `"exhausted"`/`"cap_reached"` 외의 어떤 advance 사유도 받지 않는다 (`"captcha"`, `"error"` 등 전부 `ValueError`).
- requirements 없는 플랜 생성 — fail-closed 거부.

## 7. 주입 지점

없음. 이 모듈은 순수 계산만 하며 I/O·시계·네트워크 의존이 없다.

## 8. import 계약

이 모듈은 `from apps.aisearch.core.data.seoul_universities import SEOUL_UNIVERSITIES` 로 대학 목록을 가져온다. 테스트가 두 모듈을 각각 import할 수 있으므로 데이터는 반드시 별도 모듈로 둔다.

## 9. 데이터 모듈 — `apps/aisearch/core/data/seoul_universities.py`

`SEOUL_UNIVERSITIES: tuple[str, ...]` 하나를 노출한다. 정의(사업 규칙): "서울권대학교" = 서울 소재 4년제 대학 전체 — **캠퍼스 소재지 기준이지 서열/명성 기준이 아니다**. KAIST(대전)·POSTECH(포항)·인하대(인천) 등 서울 밖 캠퍼스는 제외. 각 항목은 서울 본교 캠퍼스 기준이며, 같은 학교의 서울 밖 분교(한양대 ERICA, 연세대 미래캠퍼스, 고려대/홍익대 세종캠퍼스, 건국대 글로컬, 중앙대 다빈치, 한국외대 글로벌캠퍼스 등)는 이 목록의 대상이 아니다.

값과 순서는 정확히 다음 35개 (튜플, 이 순서 그대로):

```python
SEOUL_UNIVERSITIES: tuple[str, ...] = (
    "서울대학교", "연세대학교", "고려대학교", "서강대학교", "성균관대학교",
    "한양대학교", "중앙대학교", "경희대학교", "한국외국어대학교", "서울시립대학교",
    "이화여자대학교", "건국대학교", "동국대학교", "홍익대학교", "숙명여자대학교",
    "국민대학교", "숭실대학교", "세종대학교", "광운대학교", "명지대학교",
    "상명대학교", "성신여자대학교", "덕성여자대학교", "동덕여자대학교", "서울여자대학교",
    "삼육대학교", "한성대학교", "서경대학교", "총신대학교", "성공회대학교",
    "한국체육대학교", "서울교육대학교", "서울과학기술대학교", "한국예술종합학교", "추계예술대학교",
)
```
