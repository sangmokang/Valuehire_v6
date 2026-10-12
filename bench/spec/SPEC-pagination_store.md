# SPEC — pagination_store (검색 결과 페이지네이션 최대 20페이지 + 전량 저장 파이프라인)

대상 모듈 경로: `apps/aisearch/core/pagination_store.py`

## 1. 모듈 목적

인재검색 결과를 1페이지부터 순회하며 열어본 리스트 페이지와 상세 프로필 페이지를 **빠짐없이** 저장한다(D4). 페이지 수는 최대 20으로 절대 상한(D3) — 21페이지째 요청은 어떤 경우에도 나가면 안 된다. 20페이지 도달 시 그 키워드 조합을 종료하고 "다음 불린 변형으로 전환하라"는 시그널을, 그 전에 결과가 소진되면 "소진" 시그널을 반환한다. 저장소는 주입식이라 이 모듈은 Supabase 등 네트워크를 직접 호출하지 않는다.

## 2. 공개 API 목록

### 상수

| 이름 | 값 | 의미 |
|---|---|---|
| `MAX_PAGES` | `20` | D3 절대 상한. 이 값을 넘는 리스트 페이지 요청은 나가면 안 된다 |
| `TABLE_NAME` | `"aisearch_pages_raw"` | 저장 테이블명(가칭 — 오너 확정 필요) |
| `NEXT_SWITCH_BOOLEAN_VARIANT` | `"switch_boolean_variant"` | 20페이지 도달 → 다음 불린 변형 전환 시그널 |
| `NEXT_EXHAUSTED` | `"exhausted"` | cap 전에 결과 소진 |

### 타입·함수

```python
class PageStore(Protocol):
    def upsert(self, table: str, row: dict) -> None: ...

@dataclass(frozen=True)
class PaginationResult:
    pages_crawled: int
    details_opened: int
    rows_saved: int
    next_action: str   # "switch_boolean_variant" | "exhausted"

def make_row_id(*, channel: str, page_type: str, url: str, position_ref: str) -> str

def paginate_and_store(
    fetch_list_page: Callable[[int], dict],
    fetch_detail_page: Callable[[str], dict],
    store: PageStore,
    *,
    channel: str,
    position_ref: str,
    machine: str,
    before_store: Callable[[], None] | None = None,
) -> PaginationResult
```

`channel`/`position_ref`/`machine`/`before_store`는 **키워드 전용 인자**다.

## 3. `make_row_id` — 결정론적 멱등키 (정확한 알고리즘, 재현 필수)

같은 `(channel, page_type, url, position_ref)` 조합은 언제나 같은 id가 나와야 한다. 알고리즘:

1. 네임스페이스 UUID = `uuid.uuid5(uuid.NAMESPACE_URL, "valuehire/aisearch_pages_raw")` (모듈 로드 시 1회 계산해 재사용).
2. 이름 문자열 = 네 값을 개행(`"\n"`)으로 연결: `f"{channel}\n{page_type}\n{url}\n{position_ref}"`.
3. 반환 = `str(uuid.uuid5(네임스페이스, 이름 문자열))`.

설계 의도: 재실행이나 저장확인 유실 후 재시도가 같은 페이지를 다시 저장해도 같은 id로 upsert되어 중복 행이 생기지 않는다. `position_ref`를 키에 포함하는 이유 — 같은 프로필을 두 포지션이 저장할 때 서로 덮어쓰면 안 되고(포지션별 행 보존), 같은 포지션의 재시도는 여전히 같은 id로 수렴해 중복 0을 유지한다.

## 4. `paginate_and_store` — 계약

### 입력 검증 (진입 즉시, fail-fast)

`channel`, `position_ref`, `machine` 각각: str이 아니거나 strip 결과가 빈 문자열이면 `ValueError`, 메시지는 정확히 `{인자명} 은(는) 빈 값이면 안 된다 — 파이프라인 진입에서 fail-fast` (인자명 순서: channel → position_ref → machine).

### fetcher 계약 (주입 지점)

| 함수 | 시그니처 | 반환 dict 키 |
|---|---|---|
| `fetch_list_page` | `(page: int) -> dict` — page는 1부터 | `"url"`(str, 필수), `"content"`(str, 필수), `"detail_refs"`(list, 선택 — 없으면 `[]` 취급), `"has_next"`(bool, **필수**) |
| `fetch_detail_page` | `(ref) -> dict` — ref는 detail_refs의 원소 그대로 | `"url"`, `"content"` (필수) |

`has_next` 형식 검증(fail-fast — 조용한 exhausted 처리 금지):
- 키가 없으면 `ValueError`: `리스트 페이지 응답(page={page})에 has_next 가 없다 — 형식 위반`
- bool이 아니면 `ValueError`: `리스트 페이지 응답(page={page})의 has_next 는 bool 이어야 한다: {has_next!r}`
- 이 검증은 **해당 페이지를 저장하기 전에** 수행된다(형식 위반 페이지는 저장 0건).
- `url`/`content` 누락은 별도 메시지 계약 없이 자연스러운 `KeyError`로 전파된다.

### 순회 알고리즘

page = 1부터 `MAX_PAGES`(20)까지:

1. `fetch_list_page(page)` 호출 → `has_next` 형식 검증 → `pages_crawled` 1 증가.
2. `before_store`가 주어졌으면 리스트 페이지 upsert **직전**에 인자 없이 호출한다. 예외가 나면 **그대로 전파**되고 그 페이지는 저장되지 않는다(fail-closed). 설계 의도: 응답 수신 도중 개입 신호(캡차 등)가 들어왔으면 이 훅이 예외를 던져 오염 가능성이 있는 페이지 저장을 막는다.
3. `store.upsert(TABLE_NAME, 리스트행)` → `rows_saved` 1 증가.
4. `list_page.get("detail_refs", [])`의 각 ref에 대해 순서대로:
   - `fetch_detail_page(ref)` 호출 → `details_opened` 1 증가.
   - `before_store` 훅 호출(있으면, 역시 upsert 직전 — 예외 전파, 저장 0건).
   - `store.upsert(TABLE_NAME, 상세행)` → `rows_saved` 1 증가.
5. 종료 판정 (**순서 중요**):
   - `page == MAX_PAGES`(20)이면: `has_next` 값과 **무관하게** `next_action = "switch_boolean_variant"` 로 루프 종료. 21페이지 요청은 절대 나가지 않는다.
   - 그 외에 `has_next`가 False면: `next_action = "exhausted"` 로 루프 종료.
   - 둘 다 아니면 다음 페이지로.

즉 "exhausted"는 20페이지 **전에** `has_next=False`인 경우에만 나온다. 20페이지째에 `has_next=False`여도 cap 도달이 우선이라 `switch_boolean_variant`다.

fetcher·store가 던지는 예외는 잡지 않고 그대로 전파된다(결과 객체 없이 함수가 예외로 끝난다).

### 저장 행(row) 스키마

리스트/상세 공통, dict 키는 다음 8개(이 순서로 구성):

| 키 | 값 |
|---|---|
| `id` | `make_row_id(channel=, page_type=, url=, position_ref=)` 결과 |
| `channel` | 입력 channel |
| `page_type` | 리스트 페이지 = `"list"`, 상세 페이지 = `"detail"` |
| `url` | fetcher 응답의 `"url"` |
| `captured_at` | UTC 현재 시각의 ISO 8601 문자열 — `datetime.now(timezone.utc).isoformat()` 형식 (예: `2026-08-13T01:23:45.678901+00:00`). 행마다 저장 시점 부근에 채취 |
| `raw_html_or_text` | fetcher 응답의 `"content"` |
| `position_ref` | 입력 position_ref |
| `machine` | 입력 machine |

### 반환값

`PaginationResult(pages_crawled, details_opened, rows_saved, next_action)`.
- `pages_crawled` = 실제로 fetch되고 형식 검증을 통과한 리스트 페이지 수.
- `details_opened` = fetch된 상세 페이지 수.
- `rows_saved` = upsert 호출 성공 횟수(리스트 + 상세 합).
- 정상 흐름에서 `rows_saved == pages_crawled + details_opened`.

### 예시 시나리오

| 시나리오 | 결과 |
|---|---|
| 3페이지째 `has_next=False`, 페이지당 상세 2건 | `pages_crawled=3, details_opened=6, rows_saved=9, next_action="exhausted"` |
| 20페이지 전부 `has_next=True` | `pages_crawled=20`, `next_action="switch_boolean_variant"`, `fetch_list_page`는 정확히 20회 호출(21 금지) |
| 1페이지 응답에 `has_next` 없음 | `ValueError`, upsert 0회 |
| before_store가 2페이지 리스트 저장 직전 예외 | 예외 전파, 2페이지 행 저장 0건 (1페이지 것은 이미 저장됨) |

## 5. 불변식

- `MAX_PAGES`를 넘는 페이지 번호로 `fetch_list_page`가 호출되는 일은 절대 없다.
- 열어본(fetch 성공 + 검증 통과) 페이지는 개입 예외가 없는 한 전부 저장된다 — 열람과 저장 개수가 어긋나면 안 된다.
- 같은 페이지의 재시도 저장은 같은 id로 수렴한다(멱등 upsert 전제).
- 이 모듈에는 네트워크·파일 I/O 코드가 없다. 외부 세계 접촉은 전부 주입된 fetcher/store/훅을 통해서만.

## 6. 주입 지점

| 의존 | 인터페이스 |
|---|---|
| 리스트 fetcher | `fetch_list_page(page: int) -> dict` |
| 상세 fetcher | `fetch_detail_page(ref) -> dict` |
| 저장소 | `store.upsert(table: str, row: dict) -> None` (Protocol `PageStore`) |
| 저장 직전 훅 | `before_store() -> None`, 선택(기본 None). 예외로 저장을 중단시키는 용도 |

## 7. 의도적으로 거부하는 것

- `has_next` 누락/비불리언을 "결과 없음"으로 조용히 처리하는 것 — 형식 위반은 무조건 `ValueError`.
- 빈 channel/position_ref/machine으로의 진입.
- 21페이지째 요청 — cap은 협상 불가.
