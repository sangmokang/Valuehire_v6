"""HS-13.09 — 발송 장부. 한 패킷·한 채널은 최대 한 번만 나간다(at-most-once · D9).

계약: docs/engineering/humansearch-hs13-position-brief-goal-2026-09-10.md §5 send_ledger.py · §7 D9.

두 가지 규율이 전부다.
① attempt 파일은 **영구 묘비**다 — 이름을 바꾸지도 지우지도 않고, 내용은 transitions 를
   덧붙이기만 한다. 파일을 치우는 순간 "보냈는지 모르는" 패킷이 다시 나갈 길이 열린다.
② **발송 허가는 같은 프로세스가 받은 `created is True` 뿐이다.** 파일에서 읽어 온 INTENT 는
   보냈는지 모르는 상태이므로 발송 근거가 되지 못한다.

코드는 발송하지 않는다 — 러너(Claude 세션)가 보내고, 이 모듈은 판정만 한다.
시계는 호출자가 recorded_at·at 으로 주입한다.
"""

from __future__ import annotations

import os
import re
import tempfile
from dataclasses import dataclass, replace
from datetime import datetime
from enum import Enum
from pathlib import Path

from .packet import (
    FILE_MODE,
    dumps_value,
    ensure_store_dir,
    loads_value,
    read_store_file,
    require_packet_id,
    write_store_file,
)
from .types import _reject, _require_sha256, _require_text

__all__ = [
    "Approval",
    "SendIntent",
    "SendState",
    "Transition",
    "load_attempt",
    "load_intent",
    "mark",
    "may_send",
    "open_new_attempt",
    "record_intent",
]

_CHANNEL = re.compile(r"[a-z]+")
_ATTEMPT_SUFFIX = re.compile(r"a([1-9][0-9]{0,3})\.sent\.json")


class SendState(Enum):
    """발송 진행 상태. 앞으로만 간다 — 되돌리면 재발송 사고가 난다."""

    INTENT = "intent"
    SENT_UNVERIFIED = "sent_unverified"
    VERIFIED = "verified"
    ABANDONED = "abandoned"


# 단방향 승계. ABANDONED 는 종단이며 open_new_attempt 만 붙일 수 있다(mark 로는 못 간다).
_NEXT = {
    SendState.INTENT: SendState.SENT_UNVERIFIED,
    SendState.SENT_UNVERIFIED: SendState.VERIFIED,
}


@dataclass(frozen=True)
class Transition:
    """상태가 한 칸 움직인 사실 하나. 근거(evidence)가 없으면 남기지 않는다."""

    at: datetime
    state: SendState
    evidence: str

    def __post_init__(self) -> None:
        require_clock(self.at, "Transition.at")
        if not isinstance(self.state, SendState):
            _reject("Transition.state 는 SendState 여야 한다")
        _require_text(self.evidence, "Transition.evidence")


@dataclass(frozen=True)
class Approval:
    """재시도를 여는 사람의 서명. 무엇을 어떻게 찾아보고 없다고 판단했는지까지 남긴다."""

    approved_by: str
    search_query: str
    search_checked_at: str
    reason: str

    def __post_init__(self) -> None:
        _require_text(self.approved_by, "Approval.approved_by")
        _require_text(self.search_query, "Approval.search_query")
        _require_text(self.search_checked_at, "Approval.search_checked_at")
        _require_text(self.reason, "Approval.reason")
        require_clock(_parse_moment(self.search_checked_at), "Approval.search_checked_at")


@dataclass(frozen=True)
class SendIntent:
    """한 패킷·한 채널·한 attempt 의 발송 기록. 수신자·본문은 해시로만 남긴다(PII 0)."""

    packet_id: str
    channel: str
    attempt: int
    recipients_sha256: str
    body_sha256: str
    recorded_at: datetime
    state: SendState
    message_id: str | None = None
    transitions: tuple[Transition, ...] = ()
    approval: Approval | None = None

    def __post_init__(self) -> None:
        require_packet_id(self.packet_id)
        require_channel(self.channel)
        require_attempt(self.attempt)
        _require_sha256(self.recipients_sha256, "SendIntent.recipients_sha256")
        _require_sha256(self.body_sha256, "SendIntent.body_sha256")
        require_clock(self.recorded_at, "SendIntent.recorded_at")
        if not isinstance(self.state, SendState):
            _reject("SendIntent.state 는 SendState 여야 한다")
        self._check_transitions()
        self._check_message_id()
        self._check_approval()

    def _check_transitions(self) -> None:
        for index, step in enumerate(self.transitions):
            if not isinstance(step, Transition):
                _reject(f"SendIntent.transitions[{index}] 는 Transition 이어야 한다")
        if self.transitions:
            if self.transitions[-1].state is not self.state:
                _reject("SendIntent.transitions 의 마지막 상태가 state 와 다르다")
        elif self.state is not SendState.INTENT:
            _reject("근거 전이 없이 INTENT 밖의 상태일 수 없다")

    def _check_message_id(self) -> None:
        if self.message_id is not None:
            _require_text(self.message_id, "SendIntent.message_id")
            if self.state is SendState.ABANDONED:
                _reject("ABANDONED 는 message_id 를 가질 수 없다(보냈는지 모르는 시도다)")
        elif self.state in (SendState.SENT_UNVERIFIED, SendState.VERIFIED):
            _reject("message_id 없이 발송 이후 상태일 수 없다")

    def _check_approval(self) -> None:
        if self.attempt == 1:
            if self.approval is not None:
                _reject("첫 시도는 승인 없이 시작한다 — approval 은 재시도의 것이다")
            return
        if not isinstance(self.approval, Approval):
            _reject("두 번째 이후 시도는 Approval 없이 열 수 없다")


def require_channel(value: object) -> str:
    """채널 이름은 소문자 알파벳만 — 경로 조각이 되므로 구분자·상위 이동을 원천 차단한다."""
    if not isinstance(value, str) or not _CHANNEL.fullmatch(value):
        _reject("channel 은 소문자 알파벳만 허용한다")
    return value


def require_attempt(value: object) -> int:
    """attempt 는 1부터. 파일 이름의 일부라 형식이 곧 경로 안전성이다."""
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        _reject("attempt 는 1 이상의 정수여야 한다")
    return value


def require_clock(at: object, field: str = "at") -> datetime:
    """시계는 호출자가 준다. 시간대 없는 datetime 은 비교가 성립하지 않으므로 거부한다."""
    if not isinstance(at, datetime):
        _reject(f"{field} 는 datetime 이어야 한다")
    if at.tzinfo is None:
        _reject(f"{field} 는 시간대를 가진 datetime 이어야 한다")
    return at


def _parse_moment(text: str) -> object:
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        _reject("Approval.search_checked_at 은 ISO 8601 시각이어야 한다")


def _attempt_path(directory: Path, packet_id: str, channel: str, attempt: int) -> Path:
    stem = f"{require_packet_id(packet_id)}.{require_channel(channel)}.a{require_attempt(attempt)}"
    return directory / f"{stem}.sent.json"


def load_attempt(dir: Path, packet_id: str, channel: str, attempt: int) -> SendIntent | None:
    """attempt 한 개를 읽는다. 없으면 None."""
    return _read_attempt(ensure_store_dir(dir), packet_id, channel, attempt)


def _read_attempt(
    directory: Path, packet_id: str, channel: str, attempt: int
) -> SendIntent | None:
    target = _attempt_path(directory, packet_id, channel, attempt)
    if not target.is_file():
        return None
    restored = loads_value(SendIntent, read_store_file(target))
    if not isinstance(restored, SendIntent):
        _reject("발송 장부가 SendIntent 로 복원되지 않았다")
    if (
        restored.packet_id != packet_id
        or restored.channel != channel
        or restored.attempt != attempt
    ):
        _reject("발송 장부 내용이 파일 이름과 다르다")
    return restored


def _highest_attempt(directory: Path, packet_id: str, channel: str) -> int:
    prefix = f"{require_packet_id(packet_id)}.{require_channel(channel)}."
    highest = 0
    for entry in directory.iterdir():
        if not entry.name.startswith(prefix):
            continue
        found = _ATTEMPT_SUFFIX.fullmatch(entry.name[len(prefix) :])
        if found is not None:
            highest = max(highest, int(found.group(1)))
    return highest


def load_intent(dir: Path, packet_id: str, channel: str) -> SendIntent | None:
    """최신 attempt 를 읽는다. 기록이 하나도 없으면 None."""
    return _latest(ensure_store_dir(dir), packet_id, channel)


def _latest(directory: Path, packet_id: str, channel: str) -> SendIntent | None:
    highest = _highest_attempt(directory, packet_id, channel)
    if highest == 0:
        return None
    # 중간 묘비가 사라지면 그 자체가 변조다 — 없는 것으로 접지 않는다(P20 · fail-closed).
    for attempt in range(1, highest):
        if _read_attempt(directory, packet_id, channel, attempt) is None:
            _reject(f"attempt {attempt} 묘비가 사라졌다 — 장부가 변조됐다")
    return _read_attempt(directory, packet_id, channel, highest)


def may_send(dir: Path, packet_id: str, channel: str) -> bool:
    """attempt 파일이 **하나도 없을 때만** True. 프리플라이트 신호이지 발송 허가가 아니다."""
    return load_intent(dir, packet_id, channel) is None


def record_intent(dir: Path, intent: SendIntent) -> tuple[SendIntent, bool]:
    """attempt 1 을 원자적으로 딱 한 번 만든다. 반환 = (기록, 이번 호출이 만들었는가).

    **True 를 받은 프로세스만 발송할 수 있다.** 이미 기록이 있으면 최신 attempt 를 그대로
    돌려주고 아무것도 쓰지 않는다 — 그 기록이 곧 재발송 금지 신호다.
    """
    if not isinstance(intent, SendIntent):
        _reject("record_intent(intent) 는 SendIntent 여야 한다")
    if intent.attempt != 1:
        _reject("record_intent 는 attempt 1 만 연다 — 재시도는 open_new_attempt 다")
    if intent.state is not SendState.INTENT or intent.message_id is not None:
        _reject("record_intent 는 message_id 없는 INTENT 로만 시작한다")
    if intent.transitions:
        _reject("record_intent 는 전이 없이 시작한다")
    directory = ensure_store_dir(dir)
    target = _attempt_path(directory, intent.packet_id, intent.channel, 1)
    if _create_exclusive(directory, target, dumps_value(intent)):
        return intent, True
    existing = _latest(directory, intent.packet_id, intent.channel)
    if existing is None:
        _reject("발송 장부 파일이 있으나 읽지 못했다")
    return existing, False


def mark(
    dir: Path,
    packet_id: str,
    channel: str,
    attempt: int,
    state: SendState,
    message_id: str | None,
    at: datetime,
    evidence: str,
) -> SendIntent:
    """INTENT → SENT_UNVERIFIED(message_id 필수) → VERIFIED 단방향. transitions 에 덧붙인다."""
    if not isinstance(state, SendState):
        _reject("mark(state) 는 SendState 여야 한다")
    moment = require_clock(at)
    directory = ensure_store_dir(dir)
    current = _latest(directory, packet_id, channel)
    if current is None:
        _reject("발송 의도가 없는 채널은 표시할 수 없다")
    if current.attempt != require_attempt(attempt):
        _reject(f"최신 시도는 a{current.attempt} 다 — a{attempt} 는 표시할 수 없다")
    if _NEXT.get(current.state) is not state:
        _reject(f"{current.state.value} → {state.value} 는 허용되지 않는 전이다")
    if message_id is None or not message_id.strip():
        _reject(f"{state.value} 로 가려면 message_id 가 필요하다")
    if current.message_id is not None and current.message_id != message_id:
        _reject("이미 기록된 message_id 와 다르다")
    updated = replace(
        current,
        state=state,
        message_id=message_id,
        recorded_at=moment,
        transitions=(*current.transitions, Transition(moment, state, evidence)),
    )
    return _append(directory, current, updated)


def open_new_attempt(
    dir: Path,
    packet_id: str,
    channel: str,
    *,
    approval: Approval,
    at: datetime,
) -> tuple[SendIntent, bool]:
    """보냈는지 모르는 시도를 승인 아래 접고 attempt N+1 을 연다. 반환 = (새 기록, 열었는가).

    **True 를 받은 프로세스만 발송할 수 있다.** 직전 attempt 파일은 그대로 남고
    ABANDONED 전이만 덧붙는다 — 묘비는 지우지 않는다.
    """
    if not isinstance(approval, Approval):
        _reject("open_new_attempt(approval) 은 Approval 이어야 한다")
    moment = require_clock(at)
    directory = ensure_store_dir(dir)
    current = _latest(directory, packet_id, channel)
    if current is None:
        _reject("연 적 없는 채널에는 재시도가 없다 — record_intent 가 먼저다")
    if current.state is not SendState.INTENT or current.message_id is not None:
        _reject("발송 여부가 이미 확정된 시도는 다시 열 수 없다")
    fresh = replace(
        current,
        attempt=current.attempt + 1,
        recorded_at=moment,
        state=SendState.INTENT,
        message_id=None,
        transitions=(),
        approval=approval,
    )
    target = _attempt_path(directory, packet_id, channel, fresh.attempt)
    # 배타 생성이 유일한 상호배제 지점이다 — 먼저 이긴 쪽만 묘비를 닫고 발송 허가를 받는다.
    if not _create_exclusive(directory, target, dumps_value(fresh)):
        existing = _latest(directory, packet_id, channel)
        if existing is None:
            _reject("재시도 파일이 있으나 읽지 못했다")
        return existing, False
    summary = f"{approval.approved_by}: {approval.reason} ({approval.search_query})"
    abandoned = replace(
        current,
        state=SendState.ABANDONED,
        recorded_at=moment,
        transitions=(*current.transitions, Transition(moment, SendState.ABANDONED, summary)),
    )
    _append(directory, current, abandoned)
    return fresh, True


def _append(directory: Path, current: SendIntent, updated: SendIntent) -> SendIntent:
    """묘비 규율 — 같은 attempt 자리에, 기존 전이를 앞머리로 가진 기록만 쓸 수 있다."""
    if (
        updated.packet_id != current.packet_id
        or updated.channel != current.channel
        or updated.attempt != current.attempt
    ):
        _reject("다른 시도의 자리에 덮어쓸 수 없다")
    if updated.transitions[: len(current.transitions)] != current.transitions:
        _reject("기존 전이 기록을 지우거나 갈아끼울 수 없다")
    if updated.recorded_at < current.recorded_at:
        _reject("기록 시각이 직전 기록보다 과거다")
    write_store_file(
        directory,
        _attempt_path(directory, updated.packet_id, updated.channel, updated.attempt),
        dumps_value(updated),
    )
    return updated


def _create_exclusive(directory: Path, target: Path, text: str) -> bool:
    """내용이 완성된 임시 파일을 os.link 로 건다 — O_CREAT|O_EXCL 과 같은 원자적 배타 생성.

    O_EXCL 로 빈 파일을 먼저 만들면 진 쪽이 아직 비어 있는 파일을 읽는 창이 생긴다.
    link 는 이름이 나타나는 순간 이미 내용이 다 들어 있어 그 창이 없다.
    """
    handle, name = tempfile.mkstemp(dir=str(directory), prefix=".sent-", suffix=".tmp")
    temporary = Path(name)
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            stream.write(text)
        os.chmod(temporary, FILE_MODE)
        try:
            os.link(temporary, target)
        except FileExistsError:
            return False
        return True
    except OSError as error:
        _reject(f"발송 장부를 만들지 못했다: {error.__class__.__name__}")
    finally:
        temporary.unlink(missing_ok=True)
