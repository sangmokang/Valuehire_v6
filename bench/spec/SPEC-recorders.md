# SPEC — recorders (ClickUp + Discord 이중 기록 모듈)

대상 모듈 경로: `apps/aisearch/core/recorders.py`

## 1. 모듈 목적

AI Search에서 60점 이상으로 확정된 후보를 ClickUp(포지션 부모 Task 아래 후보 Subtask)과 Discord(결과 채널 + 멤버 진행상황 채널) 두 곳에 기록한다. 외부 쓰기 규율(L3)이 핵심: 클라이언트는 전부 주입식 Protocol이라 이 모듈에는 HTTP 호출 코드가 없고, 라이브 발신은 코드 기본값 OFF이며 오너 사인오프 없이는 켤 수 없다. dry-run에서는 외부 쓰기 0건 — 라이브와 동일 모양의 payload를 "계획"으로만 남긴다. 부분 실패 시 미완 단계를 반환하고 이어서 재개할 수 있다.

## 2. 공개 API — 상수

| 이름 | 값 | 의미 |
|---|---|---|
| `CLICKUP_LIST_ID` | `"901818680208"` | FY26AI_Search 리스트 (str) |
| `DISCORD_RESULT_CHANNEL_ID` | `"1470955309089554554"` | 서치 결과 전용 채널 |
| `DISCORD_MEMBER_CHANNEL_ID` | `"1512503041448743092"` | 진행상황/에러 멤버 채널 |
| `SCORE_THRESHOLD` | `60` | 60점 이상 후보 확정 시에만 기록 |
| `REQUIRED_FIELDS` | `("profile_url", "score", "why_fit", "profile_summary")` | 필수 4필드 (tuple, 이 순서) |
| `PARENT_PLACEHOLDER` | `"<parent-to-be-created>"` | dry-run 계획에서 "생성 예정 부모"를 뜻하는 자리표시자 |
| `STEP_CLICKUP_PARENT` | `"clickup_parent"` | 기록 단계명 |
| `STEP_CLICKUP_SUBTASK` | `"clickup_subtask"` | 〃 |
| `STEP_DISCORD_RESULT` | `"discord_result"` | 〃 |
| `STEP_DISCORD_MEMBER` | `"discord_member"` | 〃 |
| `ALL_STEPS` | 위 4개를 이 순서로 담은 tuple | 단계 실행 순서 고정 |
| `STATUS_DRY_RUN` | `"dry_run"` | 상태값 |
| `STATUS_RECORDED` | `"recorded"` | 〃 |
| `STATUS_PARTIAL` | `"partial"` | 〃 |
| `STATUS_FAILED` | `"failed"` | 〃 |
| `STATUS_SKIPPED` | `"skipped"` | 〃 |

## 3. 공개 API — 타입·함수·클래스

```python
class LiveGateError(RuntimeError): ...

def subtask_idempotency_key(profile_url: str) -> str

class ClickUpClient(Protocol):
    def find_parent_task(self, list_id: str, position_name: str) -> Optional[str]: ...
    def subtask_exists_with_profile_url(self, list_id: str, profile_url: str) -> bool: ...
    def create_parent_task(self, list_id: str, position_name: str) -> str: ...
    def create_candidate_subtask(self, list_id: str, parent_task_id: str, fields: dict[str, Any]) -> str: ...

class DiscordClient(Protocol):
    def post_message(self, channel_id: str, content: str) -> str: ...

@dataclass(frozen=True)
class Candidate:
    profile_url: str
    score: int
    why_fit: str
    profile_summary: str
    match_basis: str = ""     # 매칭 근거
    education: str = ""       # 학력
    career_brief: str = ""    # 경력 브리핑

@dataclass
class RecordResult:
    dry_run: bool
    status: str = "skipped"
    duplicate_skipped: bool = False
    error: Optional[str] = None
    parent_task_id: Optional[str] = None
    subtask_id: Optional[str] = None
    planned_actions: list[dict[str, Any]] = <빈 리스트 기본값>
    pending_steps: list[str] = <빈 리스트 기본값>

    @property
    def recorded(self) -> bool   # status == "recorded" 일 때만 True

def build_result_message(position_name: str, c: Candidate) -> str

class DualRecorder:
    def __init__(self, clickup: ClickUpClient, discord: DiscordClient, *,
                 live: bool = False, owner_signoff: bool = False) -> None
    # 공개 속성: self.live (bool)
    def record(self, *, position_name: str, candidate: Candidate,
               resume_from: Optional[RecordResult] = None) -> RecordResult
```

상태 계약: `RecordResult.status ∈ {"dry_run", "recorded", "partial", "failed", "skipped"}`. **dry-run 결과는 절대 `"recorded"`로 표시되지 않는다** — 성공적 dry-run의 status는 `"dry_run"`이고 `recorded` 프로퍼티도 False다.

## 4. `subtask_idempotency_key` — 결정론적 외부 멱등키 (정확한 알고리즘)

`profile_url`을 `strip()` → UTF-8 인코딩 → SHA-256 → hexdigest의 **앞 32자** → 접두사 `"vh-ac5-"`를 붙여 반환. 즉 `f"vh-ac5-{sha256(url.strip().encode('utf-8')).hexdigest()[:32]}"`.

설계 의도: 중복확인(read)→생성(write)은 로컬에서 원자적으로 묶을 수 없다(TOCTOU). 그래서 생성 요청 자체에 이 키를 실어 보내는 계약으로 바꾼다 — 같은 profile_url은 언제 몇 번 재시도해도 같은 키가 나오므로, 중복 생성의 원자적 차단은 이 키를 받은 원격(ClickUp 어댑터/서버)이 보장한다. 원문 URL은 키에 노출하지 않고 sha256 파생값만 쓴다.

## 5. `build_result_message` — 결과 채널 게시문 (형식 정확히)

7줄을 `"\n"`으로 연결:

```
[AI Search 결과] {position_name}
매칭점수: {c.score}
프로필URL: {c.profile_url}
적합/부적합 사유: {c.why_fit}
매칭 근거: {c.match_basis}
학력: {c.education}
경력 브리핑: {c.career_brief}
```

## 6. `DualRecorder` 생성자 — 라이브 게이트

- `live=True` 인데 `owner_signoff=False` 면 **생성자에서 즉시** `LiveGateError`(fail-closed). 메시지: `L3 외부 쓰기: live=True 는 owner_signoff=True 없이는 금지 (fail-closed)`
- `live=False`면 owner_signoff 값과 무관하게 생성 가능(기본 dry-run).
- `self.live`는 공개 속성.

## 7. dry-run/live 공통 실행 규칙 (`planned_actions`)

모든 "외부 쓰기" 액션은 실행 전에 `result.planned_actions`에 `{"kind": <액션 종류>, **payload}` dict로 append된다 — **live·dry-run 모두**. 그 다음 live면 실제 클라이언트 호출을 하고 반환값을 쓰며, dry-run이면 호출 없이 `None`을 얻는다. 따라서:

- dry-run에서 외부 **쓰기**는 0건이지만 planned_actions에는 라이브와 동일 모양의 payload가 계획으로 남는다.
- 단, **읽기**(`find_parent_task`, `subtask_exists_with_profile_url`)는 dry-run에서도 실제로 호출된다 — 중복확인은 SOT25 write_gate상 등록 전 필수 회수 단계이기 때문. 읽기는 planned_actions에 남지 않는다.

액션 종류(kind)와 payload 키:

| kind | payload |
|---|---|
| `"clickup_create_parent_task"` | `list_id`, `name` |
| `"clickup_create_candidate_subtask"` | `list_id`, `parent_task_id`, `fields` |
| `"discord_result_post"` | `channel_id`, `content` |
| `"discord_member_post"` | `channel_id`, `content` |

## 8. `record()` — 판정 순서 (순서 고정, 테스트 판별 가능)

새 `RecordResult(dry_run=not live)`로 시작해 아래 순서로 진행한다.

### 8-1. 점수 계약 검증 (가장 먼저)

`candidate.score`가 bool이거나, int가 아니거나, 0~100 범위 밖(양 끝 포함이 허용)이면:
- `status="failed"`, `error = f"score 계약 위반: 정수 0~100 필요, 받은 값 {score!r}"`
- 멤버 채널에 에러 보고: content = `[AI Search 에러] {position_name}: {error} — 등록하지 않음` (planned_actions에 `discord_member_post`로 남고, live면 실제 발신. 이 발신 중 예외는 잡지 않고 전파된다)
- 반환.

### 8-2. 점수 미달

`score < 60`이면 `status="skipped"`로 즉시 반환 — **아무 것도 하지 않는다**(중복확인도, 알림도 없음, planned_actions 빈 채로).

### 8-3. 필수 4필드 검증

`REQUIRED_FIELDS` 순서로 각 필드값이 falsy(빈 문자열 등)인 것을 모으고, 하나라도 있으면:
- `status="failed"`, `error = f"필수 필드 누락: {', '.join(누락필드들)}"` (REQUIRED_FIELDS 순서)
- 8-1과 같은 형식의 멤버 채널 에러 보고 후 반환. 등록은 하지 않는다(fail-closed).

### 8-4. 재개 vs 신규 분기

- **재개**: `resume_from`이 None이 아니고 `resume_from.pending_steps`가 비어있지 않으면 — 실행할 steps = pending_steps 복사본, `parent_task_id`/`subtask_id`를 이전 결과에서 이어받는다. **중복확인을 재수행하지 않는다** (1차 실행이 만든 subtask가 중복으로 판정되어 Discord 게시가 영구 누락되는 결함의 원인이었기 때문).
- **신규** (resume_from이 None이거나 pending_steps가 비었으면): 중복확인 read `clickup.subtask_exists_with_profile_url(CLICKUP_LIST_ID, profile_url)` 를 **dry-run에서도** 수행. True면:
  - `duplicate_skipped=True`, `status="skipped"`
  - 멤버 채널 post: `[AI Search 진행] {position_name}: 중복 profile_url — 등록 skip ({profile_url})`
  - 반환.
  - (주의: 이 확인은 원자성 보장이 아니라 조기 skip 최적화 — 경합의 원자적 차단은 멱등키(§4)가 담당)
- False면 steps = `ALL_STEPS` 전체 복사본.

### 8-5. 단계별 실행과 부분 실패

steps를 순서대로 실행한다. 어떤 단계에서든 `Exception`(종류 불문)이 나면:
- `error = f"{단계명} 실패: {예외}"`
- `pending_steps` = **실패한 단계를 포함한** 나머지 단계 리스트
- `status` = 이번 호출에서 이미 완료한 단계가 하나라도 있거나 **resume_from이 주어졌으면** `"partial"`, 아니면(첫 단계에서 바로 실패 + 신규) `"failed"`
- 즉시 반환.

전 단계 성공 시: `pending_steps=[]`, `status` = live면 `"recorded"`, dry-run이면 `"dry_run"`.

## 9. 각 단계의 의미

### `clickup_parent`

- `find_parent_task(CLICKUP_LIST_ID, position_name)` (read, 양 모드 실제 호출).
- 있으면 그 ID 재사용(planned_actions에 아무것도 안 남음). 없으면 `clickup_create_parent_task` 액션 — live면 `create_parent_task` 반환 ID, dry-run이면 None.
- 결과를 `result.parent_task_id`에 저장.

### `clickup_subtask`

- `fields` = `{"profile_url": ..., "score": ..., "why_fit": ..., "profile_summary": ..., "idempotency_key": subtask_idempotency_key(profile_url)}` — 필수 4필드 + 멱등키.
- **live 경로**: `result.parent_task_id`가 None이면 `RuntimeError`(`live 경로에서 부모 Task ID 미확보 — subtask 생성 불가`)를 던진다 — §8-5 규칙에 따라 partial/failed로 수거된다. live는 생성된 **실제** Task ID만 사용한다.
- **dry-run 경로**: planned payload의 `parent_task_id` 자리에는 실제 ID가 있으면 그것을, 없으면(None 대신) `PARENT_PLACEHOLDER`(`"<parent-to-be-created>"`)를 넣는다 — "생성 예정 부모"라는 의미를 명시. placeholder는 live 경로에서는 절대 쓰이지 않는다.
- `clickup_create_candidate_subtask` 액션 실행. live 실제 호출에는 `result.parent_task_id`를 넘긴다. 반환 ID를 `result.subtask_id`에 저장(dry-run은 None).

### `discord_result`

`build_result_message(position_name, candidate)` 본문으로 결과 채널(`DISCORD_RESULT_CHANNEL_ID`)에 `discord_result_post` 액션.

### `discord_member`

멤버 채널(`DISCORD_MEMBER_CHANNEL_ID`)에 완료 보고 `discord_member_post` 액션. content(정확히):
`[AI Search 진행] {position_name}: 후보 1건 등록 완료 (점수 {candidate.score}, ClickUp 901818680208)` (ClickUp 뒤 값은 `CLICKUP_LIST_ID`).

### 계약 밖 단계명

steps에 위 4개 외의 이름이 오면 `ValueError`(`알 수 없는 기록 단계: {step}`) — 프로그래밍 오류. (이 예외도 §8-5 수거 대상 경로 안에서 발생한다.)

## 10. 불변식

- dry-run에서 외부 **쓰기** 호출 0건 (create_parent_task/create_candidate_subtask/post_message 미호출). 읽기 2종은 예외적으로 호출됨.
- dry-run 성공의 status는 `"dry_run"`이며 `recorded` 프로퍼티는 status 파생값이라 절대 True가 되지 않는다.
- 라이브 게이트: `live=True ∧ owner_signoff=False` 조합의 DualRecorder는 존재할 수 없다(생성자에서 차단).
- 60점 미만 후보에 대해서는 어떤 외부 접촉(읽기 포함)도 일어나지 않는다.
- partial 결과의 `pending_steps`를 `resume_from`으로 다시 넘기면 이미 성공한 단계는 재실행되지 않고 미완 단계만 이어서 수행되어 완결 가능하다. 재개 성공 시 status는 모드에 따라 dry_run/recorded.

## 11. 주입 지점

| 의존 | 인터페이스 | 비고 |
|---|---|---|
| ClickUp | `ClickUpClient` Protocol §3의 4메서드 | 어댑터는 fields의 `idempotency_key`를 원격 생성 요청에 실어 중복 생성을 원자적으로 막아야 한다 |
| Discord | `DiscordClient.post_message(channel_id, content) -> str` | |

실제 HTTP 어댑터는 별도 파일이며 이 모듈은 기본 미사용 — 이 모듈에 네트워크 코드가 있으면 계약 위반.

## 12. 의도적으로 거부하는 것

- 사인오프 없는 라이브 발신 (`LiveGateError`).
- bool·비정수·0~100 밖 점수 (failed + 에러 보고, 등록 없음).
- 필수 4필드 누락 후보 (failed + 에러 보고, 등록 없음).
- dry-run 결과를 "recorded"로 표시하는 것.
