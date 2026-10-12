# SPEC — intervention (사람 개입 감지·30초 자동재개 + 캡차 감지·차단(BLOCKED)·알림)

대상 모듈 경로: `apps/aisearch/core/intervention.py`

## 1. 모듈 목적

자동화 브라우징 도중 (a) 사람이 마우스/키보드를 잡으면 즉시 자동 조작을 멈추고 마지막 입력 후 30초 무입력이면 자동 재개하며, (b) 캡차·클라우드플레어·2FA·체크포인트 같은 차단 신호가 오면 자동 우회를 시도하지 않고 즉시 종단 상태(BLOCKED)로 들어가 알림을 보내는 상태 기계를 제공한다. 시계와 알림 채널은 전부 주입식이라 실제 sleep이나 실제 Discord 발신 없이 타임스탬프만으로 결정론적 테스트가 가능하다.

## 2. 공개 API 목록

### 상수

| 이름 | 값 | 타입 | 의미 |
|---|---|---|---|
| `RESUME_DELAY_SECONDS` | `30.0` | float | 마지막 사람 입력으로부터 자동 재개까지의 무입력 대기시간(초). (SOT29의 60초와 별개인 이 서비스 전용 상수) |
| `NOTIFY_MAX_ATTEMPTS` | `3` | int | 알림 총 시도 횟수 = 최초 1회 + 재시도 2회 |
| `BLOCKING_SIGNALS` | `frozenset({"captcha", "cloudflare", "2fa", "checkpoint"})` | frozenset[str] | 표에 있는 차단 신호 |
| `DRIVER_EVENT_HUMAN_INPUT` | `"human_input"` | str | 드라이버 이벤트 타입 |
| `DRIVER_EVENT_SIGNAL` | `"signal"` | str | 드라이버 이벤트 타입 |

### 타입·클래스·함수

```python
class Notifier(Protocol):
    def notify(self, message: str) -> None: ...

class MonitorState(enum.Enum):
    RUNNING = "running"          # 자동 조작 허용
    PAUSED_HUMAN = "paused_human"  # 사람 개입 감지 — 30초 무입력 대기
    BLOCKED = "blocked"          # 차단 신호 — 종단 상태

class InvalidTransitionError(Exception): ...

VALID_TRANSITIONS: dict[MonitorState, frozenset[MonitorState]]

def validate_transition(src: MonitorState, dst: MonitorState) -> None

def feed_driver_events(monitor: "InterventionMonitor", events: list[dict]) -> None

class InterventionMonitor:
    def __init__(self, clock: Callable[[], float], notifier: Notifier) -> None
    @property
    def state(self) -> MonitorState
    @property
    def pending_notifications(self) -> list[str]
    def automation_allowed(self) -> bool
    def on_human_input(self) -> None
    def on_signal(self, kind: str) -> None
    def poll(self) -> MonitorState
    def human_reset(self) -> None
```

## 3. 유효 전이 표 (VALID_TRANSITIONS)

모듈 레벨 공개 dict. 여기 없는 전이는 전부 예외(E8 catch-all — 임의 추정 금지):

| src \ 허용 dst | RUNNING | PAUSED_HUMAN | BLOCKED |
|---|---|---|---|
| RUNNING | ✗ | ○ | ○ |
| PAUSED_HUMAN | ○ | ○ (자기 전이 — 타이머 리셋용) | ○ |
| BLOCKED | ○ (human_reset 전용 경로) | ✗ | ✗ |

`validate_transition(src, dst)`: dst가 표의 src 허용 집합에 없으면 `InvalidTransitionError`, 메시지는 정확히 `표 밖 상태 전이 {src.value} → {dst.value} — 허용 안 함(E8)`. src가 표에 없는 값이면 빈 집합 취급(항상 예외).

주의: 표는 BLOCKED→RUNNING을 허용하지만, 이 경로는 `human_reset()` 전용이다. 모니터 내부 전이 로직은 "현재 상태가 BLOCKED인데 human_reset 경유가 아니면" 표 검사 이전에 `InvalidTransitionError`(메시지: `BLOCKED는 종단 상태 — human_reset 없이 벗어날 수 없다(E8)`)를 던진다. 즉 poll 등 다른 경로가 종단 상태를 절대 덮어쓸 수 없다.

## 4. `InterventionMonitor` 상태·순서 규칙

### 생성자·프로퍼티

- `clock`: 인자 없이 현재 시각(초, 단조 증가 float)을 돌려주는 주입식 시계.
- `notifier`: `notify(message: str)` 를 가진 주입식 알림 채널(Discord 등). 실제 발신 구현은 호출자가 주입한다.
- 초기 상태: `RUNNING`, 마지막 사람 입력 시각 없음, pending 알림 큐 빈 리스트.
- `state`: 현재 `MonitorState` 반환.
- `pending_notifications`: 발신에 최종 실패해 보존 중인 메시지들의 **복사본 리스트** 반환 — 반환된 리스트를 외부에서 변조해도 내부 큐가 바뀌면 안 된다(불변식).
- `automation_allowed()`: 상태가 `RUNNING`일 때만 `True`. PAUSED_HUMAN·BLOCKED 모두 `False`.

### `on_human_input()` — 사람 입력 감지

1. 현재 BLOCKED면 **아무 것도 하지 않고 조용히 반환** (예외 없음 — 입력만으로 종단 상태를 되살리지 않는다).
2. 아니면 `clock()`으로 마지막 입력 시각을 기록하고 `PAUSED_HUMAN`으로 전이한다.
3. 이미 PAUSED_HUMAN이어도 다시 호출 가능(자기 전이 허용) — 입력 시각이 갱신되어 30초 타이머가 리셋된다.

### `on_signal(kind: str)` — 차단 신호

1. 현재 BLOCKED면 아무 것도 하지 않고 조용히 반환(중복 신호 무시 — 알림도 다시 안 보냄).
2. 아니면(RUNNING 또는 PAUSED_HUMAN에서) 먼저 `BLOCKED`로 전이한다. **전이가 알림보다 먼저다** — 알림 실패가 차단 상태 진입을 방해하면 안 된다.
3. 알림 메시지 결정:
   - `kind`가 `BLOCKING_SIGNALS`에 있으면: `차단 신호 감지({kind}) — 자동 우회 금지, 즉시 차단(E1)`
   - 표에 없으면: `표에 없는 신호 감지({kind}) — 명시적 차단(E8 catch-all)`
   - 즉 **표에 없는 미지의 신호도 무시하지 않고 똑같이 차단**한다(fail-closed). 자동 우회 API는 제공하지 않는다.
4. 재시도 규칙으로 알림 발신(§5).

### 알림 재시도 규칙 (§5)

- `notifier.notify(message)`를 최대 `NOTIFY_MAX_ATTEMPTS`(3)회 시도한다. 어떤 `Exception`이든 잡고 다음 시도로 넘어간다.
- 한 번이라도 성공하면 즉시 종료(남은 시도 안 함, pending에 안 남음).
- 3회 전부 실패하면 메시지를 pending 큐에 append한다 — **차단 이벤트 알림은 절대 유실 금지**.
- 예외를 밖으로 절대 전파하지 않는다.

### `poll()` — 주기 점검

- `PAUSED_HUMAN`일 때만 동작: `clock() - 마지막입력시각 >= 30.0` 이면(**30.0초 정확히 도달 = 포함, 재개**) `RUNNING`으로 전이하고 마지막 입력 시각을 지운다. 29.9초처럼 30초 미만이면 재개하지 않는다.
- RUNNING·BLOCKED에서는 아무 것도 바꾸지 않는다. **BLOCKED는 poll이 절대 덮어쓰지 않는다.**
- 반환값: (전이 여부와 무관하게) 현재 상태.

### `human_reset()` — BLOCKED 해제 유일 경로

- 현재 상태가 BLOCKED가 아니면 `InvalidTransitionError`, 메시지는 정확히 `human_reset은 BLOCKED에서만 유효 — 현재 {state.value}(E8)`.
- BLOCKED면 `RUNNING`으로 전이하고 마지막 입력 시각을 지운다.

### 상태 다이어그램 요약

- RUNNING —(on_human_input)→ PAUSED_HUMAN —(poll, 30초 경과)→ RUNNING
- RUNNING/PAUSED_HUMAN —(on_signal)→ BLOCKED (종단)
- BLOCKED —(human_reset만)→ RUNNING
- BLOCKED에서 on_human_input/on_signal/poll은 전부 no-op(상태 유지, 예외 없음)

## 5. `feed_driver_events(monitor, events)` — 드라이버 이벤트 어댑터

드라이버가 관측한 이벤트 dict 리스트를 순서대로 모니터에 공급한다:

| 이벤트 | 동작 |
|---|---|
| `{"type": "human_input"}` | `monitor.on_human_input()` |
| `{"type": "signal", "kind": <k>}` | `monitor.on_signal(str(<k>))` — kind 키가 없으면 `str(None)` = `"None"`이 넘어간다 |
| 그 밖의 타입 / dict가 아닌 원소 | `monitor.on_signal(f"unknown_driver_event:{etype!r}")` — etype은 dict면 `event.get("type")` 값, dict가 아니면 `None`. 예: `{"type": "weird"}` → `on_signal("unknown_driver_event:'weird'")`, 문자열 원소 → `on_signal("unknown_driver_event:None")` |

설계 의도: 표에 없는 이벤트를 임의 추정으로 무시하지 않고 미지 신호로 취급해 차단(fail-closed)한다. 미지 이벤트의 kind는 `BLOCKING_SIGNALS`에 없으므로 "표에 없는 신호" 메시지 경로를 탄다.

## 6. 불변식

- BLOCKED는 종단 상태: `human_reset()` 외의 어떤 공개 메서드도 BLOCKED에서 벗어나게 하지 못한다.
- 모든 내부 전이는 유효 전이 표 검증을 통과한 것만 수행된다.
- `pending_notifications`는 항상 복사본을 반환한다(내부 리스트 노출 금지).
- 이 모듈에는 실제 sleep·네트워크·시간 조회(`time.time()` 직접 호출)가 없다 — 시간은 오직 주입된 clock으로만 읽는다.

## 7. 주입 지점 (테스트가 가짜로 바꿔 끼우는 의존)

| 의존 | 인터페이스 | 비고 |
|---|---|---|
| 시계 | `clock: Callable[[], float]` — 인자 없음, 초 단위 float 반환 | 테스트는 조작 가능한 가짜 시계를 주입해 30초 경계를 검증 |
| 알림 | `notifier.notify(message: str) -> None` | 예외를 던지는 가짜로 재시도·pending 보존을 검증 |

## 8. 의도적으로 거부하는 것

- 캡차/클라우드플레어/2FA/체크포인트의 자동 우회 — 시도하지 않으며 **우회용 API 자체를 제공하지 않는다**(E1).
- 표 밖 상태 전이 — 전부 `InvalidTransitionError`(E8).
- poll·사람 입력에 의한 BLOCKED 해제 — 불가. 사람의 명시적 `human_reset()`만 유효.
