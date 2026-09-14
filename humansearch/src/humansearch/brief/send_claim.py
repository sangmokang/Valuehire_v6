"""HS-13.09d — 발송 청구(claim). 발송 허가는 불리언이 아니라 **한 번 소비되는 마커**다.

Codex V1 7차 반례: `record_intent` 가 준 `created=True` 를 같은 프로세스가 들고 Gmail 을
두 번 부르면 장부에는 attempt 하나·message_id 하나만 남는다. 그래서 발송 직전에
INTENT → SEND_CLAIMED 전이를 **배타 생성 마커 파일**(`<stem>.claim.json`, O_EXCL 과 같은
os.link) 로 딱 한 번만 허용한다. 러너 규율은 하나다 — **청구 1건 = 외부 발송 호출 1회**.

마커만 남고 전이 기록 전에 죽은 경우(고아 마커)는 "보냈는지 모름" 이다. 재청구는 거부되고
승인 아래 `open_new_attempt` 로 다음 attempt 를 여는 길만 남는다(묘비 규율과 같다).

코드는 발송하지 않는다 — 러너(Claude 세션)가 보내고, 이 모듈은 청구를 소비만 한다.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from pathlib import Path

from .packet import dumps_value, ensure_store_dir, from_json, read_store_file, require_packet_id
from .send_ledger import (
    SendIntent,
    SendState,
    Transition,
    _append,
    _attempt_path,
    _channel_lock,
    _create_exclusive,
    _latest,
    recipients_digest,
    require_attempt,
    require_channel,
    require_clock,
)
from .types import _reject, _require_sha256, _require_text

__all__ = ["claim_path", "claim_send"]


def claim_path(dir: Path, packet_id: str, channel: str, attempt: int) -> Path:
    """청구 마커 경로. attempt 파일 옆에 `<packet>.<channel>.a<n>.claim.json` 으로 남는다."""
    sent = _attempt_path(dir, packet_id, channel, attempt)
    return sent.with_name(sent.name.replace(".sent.json", ".claim.json"))


def claim_send(
    dir: Path,
    packet_id: str,
    channel: str,
    attempt: int,
    *,
    at: datetime,
    evidence: str,
    recipients_sha256: str,
    body_sha256: str,
) -> tuple[SendIntent, bool]:
    """최신 attempt 의 INTENT 를 SEND_CLAIMED 로 딱 한 번 옮긴다. 반환 = (기록, 이번 호출이 땄는가).

    **True 를 받은 호출만 외부 발송 1회를 소유한다.** 같은 attempt 에 두 번째 청구는 False 다.
    청구 마커가 있는데 기록이 아직 INTENT 면(고아 마커) 역시 False — 보냈는지 모르는 시도다.
    """
    require_packet_id(packet_id)
    require_channel(channel)
    require_attempt(attempt)
    moment = require_clock(at)
    _require_text(evidence, "claim_send.evidence")
    _require_sha256(recipients_sha256, "claim_send.recipients_sha256")
    _require_sha256(body_sha256, "claim_send.body_sha256")
    directory = ensure_store_dir(dir)
    with _channel_lock(directory, packet_id, channel):
        return _claim_locked(
            directory,
            packet_id,
            channel,
            attempt,
            moment,
            evidence,
            recipients_sha256,
            body_sha256,
        )


def _claim_locked(
    directory: Path,
    packet_id: str,
    channel: str,
    attempt: int,
    moment: datetime,
    evidence: str,
    recipients_sha256: str,
    body_sha256: str,
) -> tuple[SendIntent, bool]:
    current = _latest(directory, packet_id, channel)
    if current is None:
        _reject("발송 의도가 없는 채널은 청구할 수 없다 — record_intent 가 먼저다")
    if current.attempt != attempt:
        _reject(f"최신 시도는 a{current.attempt} 다 — a{attempt} 는 청구할 수 없다")
    if current.recipients_sha256 != recipients_sha256:
        _reject("현재 수신자 digest 가 승인된 발송 의도와 다르다")
    if current.body_sha256 != body_sha256:
        _reject("현재 본문 digest 가 승인된 발송 의도와 다르다")
    _check_current_packet_digest(directory, packet_id, current)
    if current.state is SendState.SEND_CLAIMED:
        return current, False
    if current.state is not SendState.INTENT or current.message_id is not None:
        _reject("발송 여부가 이미 확정된 시도는 청구할 수 없다")
    marker = claim_path(directory, packet_id, channel, attempt)
    payload = {
        "packet_id": packet_id,
        "channel": channel,
        "attempt": attempt,
        "claimed_at": moment.isoformat(),
        "evidence": evidence,
    }
    # 배타 생성이 유일한 상호배제 지점이다 — 이름이 나타난 쪽 하나만 발송을 소유한다.
    if not _create_exclusive(directory, marker, dumps_value(payload)):
        return current, False
    claimed = replace(
        current,
        state=SendState.SEND_CLAIMED,
        recorded_at=moment,
        transitions=(*current.transitions, Transition(moment, SendState.SEND_CLAIMED, evidence)),
    )
    return _append(directory, current, claimed), True


def _check_current_packet_digest(directory: Path, packet_id: str, current: SendIntent) -> None:
    target = directory / f"{require_packet_id(packet_id)}.packet.json"
    if not target.is_file():
        return
    packet = from_json(read_store_file(target))
    actual_recipients_sha256 = recipients_digest(packet.mail.to, packet.mail.cc)
    if current.recipients_sha256 != actual_recipients_sha256:
        _reject("현재 패킷 수신자 digest 가 승인된 발송 의도와 다르다")
    if current.body_sha256 != packet.mail.body_sha256:
        _reject("현재 패킷 본문 digest 가 승인된 발송 의도와 다르다")
