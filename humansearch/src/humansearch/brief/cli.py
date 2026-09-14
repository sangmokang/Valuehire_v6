"""HS-13.10 — 발송된 팀 메일의 readback 본문을 패킷과 대조해 발송을 판정한다.

계약: docs/engineering/humansearch-hs13-position-brief-goal-2026-09-10.md §5 __main__.py · §9 HS-13.10.
이 모듈은 두 파일(패킷 JSON·readback 평문)을 읽어 해시를 비교하는 판정만 한다.
발송·네트워크·시계 접근 0 — `__main__.py` 가 argparse 로 인자만 풀어 이 함수를 부른다.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote

from .packet import ensure_store_dir, from_json
from .send_ledger import (
    SendIntent,
    SendState,
    Transition,
    _append,
    _channel_lock,
    _latest,
    recipients_digest,
    require_attempt,
    require_clock,
)
from .types import BriefInputError

__all__ = ["ReadbackReceipt", "normalize_readback", "verify", "verify_and_mark"]

_PACKET_ID_TRAILER = "packet-id: "

# 실측(라이브 초안 readback): Gmail 은 본문 링크를 이 형태로 감싼다.
# 꼬리(`sa=`)를 `[A-Za-z0-9]+` 로 **정확히** 고정한다 — `[^\s]*` 같은 느슨한 꼬리는
# 뒤따르는 `)` 와 조사까지 한 매치로 삼켜 `(URL)` 을 `(URL` 로 망가뜨린다(반례 고정: HS-13.10b).
_GMAIL_REDIRECT = re.compile(
    r"https://www\.google\.com/url\?q=([^&\s]+)&source=gmail&ust=\d+&sa=[A-Za-z0-9]+"
)

# 언랩한 URL 은 unquote 를 거친다. 그러면 원문이 이미 퍼센트 인코딩(`.../in/%EC%9D%80…`)일 때
# readback 쪽만 한글로 풀려 영영 불일치가 난다. 그래서 **양쪽 본문의 URL 에 같은 unquote 를
# 건다** — 패킷 본문도 같은 값으로 내려와야 대칭이 성립한다(HS-13.10b).
_URL = re.compile(r'https?://[^\s<>"]+')

@dataclass(frozen=True)
class ReadbackReceipt:
    """검증 전이에 쓰는 구조화 readback 영수증. 평문 verify 는 이 계약을 요구하지 않는다."""

    packet_id: str
    attempt: int
    message_id: str
    to: tuple[str, ...]
    cc: tuple[str, ...]
    body: str



def _unwrap_gmail_redirect(text: str) -> str:
    return _GMAIL_REDIRECT.sub(lambda found: unquote(found.group(1)), text)


def _unquote_urls(text: str) -> str:
    return _URL.sub(lambda found: unquote(found.group(0)), text)


def normalize_readback(text: str) -> str:
    """readback 본문과 패킷 본문을 같은 기준으로 내리는 정규화. 순서가 계약이다.

    ① `\r\n` → `\n`
    ② Gmail 리다이렉트 언랩 — `…/url?q=<URL>&source=gmail&ust=<digits>&sa=<alnum>` → `<URL>`
    ②' 남은 URL 의 퍼센트 인코딩 해제(양쪽 대칭 — ② 가 만든 비대칭을 여기서 없앤다)
    ③ 각 줄 오른쪽 공백 제거
    ④ 끝의 빈 줄 제거 후 마지막 줄이 `packet-id: ` 로 시작하면 제거(§10 ③ 러너가 붙인 토큰)
    ⑤ 다시 끝 빈 줄 제거·전체 strip

    패킷 본문(`mail.body`)에는 보통 꼬리 줄도 리다이렉트도 없어 ②④ 는 no-op 이고,
    readback 본문에는 둘 다 있다 — **같은 함수를 양쪽에 적용해야** 두 해시가 같은 기준이 된다.
    """
    text = text.replace("\r\n", "\n")
    text = _unwrap_gmail_redirect(text)
    text = _unquote_urls(text)
    lines = [line.rstrip() for line in text.split("\n")]
    text = "\n".join(lines).strip()
    lines = text.split("\n")
    if lines and lines[-1].startswith(_PACKET_ID_TRAILER):
        lines = lines[:-1]
    return "\n".join(lines).strip()


def _read_text(path: Path, label: str) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise BriefInputError(f"{label} 파일이 없다: {path}") from None
    except IsADirectoryError:
        raise BriefInputError(f"{label} 경로가 파일이 아니다: {path}") from None
    except OSError as error:
        raise BriefInputError(f"{label} 파일을 읽지 못했다: {error.__class__.__name__}") from None
    except UnicodeDecodeError as error:
        raise BriefInputError(
            f"{label} 파일이 UTF-8 이 아니다: {error.__class__.__name__}"
        ) from None


def _read_receipt(path: Path) -> ReadbackReceipt:
    text = _read_text(path, "readback 영수증")
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as error:
        raise BriefInputError("VERIFIED 전이는 구조화 readback 영수증 JSON 이 필요하다") from error
    if not isinstance(payload, dict):
        raise BriefInputError("readback 영수증은 JSON object 여야 한다")
    try:
        packet_id = payload["packet_id"]
        attempt = payload["attempt"]
        message_id = payload["message_id"]
        to = payload["to"]
        cc = payload.get("cc", [])
        body = payload["body"]
    except KeyError as error:
        raise BriefInputError(f"readback 영수증 필드가 없다: {error.args[0]}") from None
    if not isinstance(packet_id, str) or not packet_id.strip():
        raise BriefInputError("readback 영수증 packet_id 가 비어 있다")
    attempt = require_attempt(attempt)
    if not isinstance(message_id, str) or not message_id.strip():
        raise BriefInputError("readback 영수증 message_id 가 비어 있다")
    if not isinstance(body, str):
        raise BriefInputError("readback 영수증 body 는 문자열이어야 한다")
    if not isinstance(to, list) or not all(isinstance(item, str) for item in to):
        raise BriefInputError("readback 영수증 to 는 문자열 배열이어야 한다")
    if not isinstance(cc, list) or not all(isinstance(item, str) for item in cc):
        raise BriefInputError("readback 영수증 cc 는 문자열 배열이어야 한다")
    return ReadbackReceipt(packet_id, attempt, message_id, tuple(to), tuple(cc), body)


def verify(packet_path: Path, sent_path: Path) -> tuple[int, str]:
    """패킷과 readback 본문을 정규화해 대조한다.

    반환: (exit_code, message). exit 0/1 의 message 는 stdout 한 줄,
    exit 2 의 message 는 stderr 사유다 — 어디에 찍을지는 호출자(`__main__.py`)가 정한다.
    """
    try:
        packet_text = _read_text(packet_path, "패킷")
        packet = from_json(packet_text)
        sent_text = _read_text(sent_path, "readback")
    except BriefInputError as error:
        return 2, str(error)

    expected, actual, tail_problem = _verify_parts(packet.mail.body, sent_text, packet.packet_id)
    if tail_problem is not None:
        # 본문이 같아도 꼬리 packet-id 가 없거나 다르거나 겹치면 이 발송본을 이 패킷에 결합할 수 없다(Codex 12차)
        return 1, (
            f"SENT_UNVERIFIED packet_id={packet.packet_id} expected={expected} actual={actual}"
            f" reason={tail_problem}"
        )
    if expected == actual:
        return 0, f"VERIFIED packet_id={packet.packet_id} body_sha256={expected}"
    return 1, f"SENT_UNVERIFIED packet_id={packet.packet_id} expected={expected} actual={actual}"


def verify_and_mark(
    dir: Path,
    packet_path: Path,
    sent_path: Path,
    message_id: str,
    at: object,
    *,
    channel: str = "gmail",
) -> SendIntent:
    """readback 검증과 VERIFIED 장부 전이를 같은 최신 attempt 에 결합한다."""
    moment = require_clock(at)
    packet_text = _read_text(packet_path, "패킷")
    packet = from_json(packet_text)
    directory = ensure_store_dir(dir)
    with _channel_lock(directory, packet.packet_id, channel):
        locked_packet_id = packet.packet_id
        packet = from_json(_read_text(packet_path, "패킷"))
        if packet.packet_id != locked_packet_id:
            raise BriefInputError("잠금 중 패킷 파일의 packet_id 가 바뀌었다")
        receipt = _read_receipt(sent_path)
        if receipt.packet_id != packet.packet_id:
            raise BriefInputError("readback 영수증 packet_id 가 패킷과 다르다")
        if receipt.message_id != message_id:
            raise BriefInputError("readback 영수증 message_id 가 인자와 다르다")
        expected, actual, tail_problem = _verify_parts(packet.mail.body, receipt.body, packet.packet_id)
        if tail_problem is not None:
            raise BriefInputError(f"readback 검증 실패: {tail_problem}")
        if expected != actual:
            raise BriefInputError("readback 본문 digest 가 패킷과 다르다")
        current = _latest(directory, packet.packet_id, channel)
        if current is None:
            raise BriefInputError("발송 의도가 없는 채널은 VERIFIED 로 표시할 수 없다")
        if current.state is not SendState.SENT_UNVERIFIED:
            raise BriefInputError(f"{current.state.value} 상태는 VERIFIED 로 표시할 수 없다")
        if receipt.attempt != current.attempt:
            raise BriefInputError("readback 영수증 attempt 가 최신 attempt 와 다르다")
        if current.message_id != message_id:
            raise BriefInputError("다른 message_id 로 검증된 readback 을 재사용할 수 없다")
        if current.body_sha256 != packet.mail.body_sha256:
            raise BriefInputError("현재 패킷 본문 digest 가 발송 청구 digest 와 다르다")
        packet_recipients_sha256 = recipients_digest(packet.mail.to, packet.mail.cc)
        receipt_recipients_sha256 = recipients_digest(receipt.to, receipt.cc)
        if current.recipients_sha256 != packet_recipients_sha256:
            raise BriefInputError("현재 패킷 수신자 digest 가 발송 청구 digest 와 다르다")
        if current.recipients_sha256 != receipt_recipients_sha256:
            raise BriefInputError("readback 영수증 수신자 digest 가 발송 청구 digest 와 다르다")
        evidence = (
            f"readback verified packet_id={packet.packet_id} attempt={current.attempt} "
            f"body_sha256={packet.mail.body_sha256} recipients_sha256={current.recipients_sha256} "
            f"message_id={message_id}"
        )
        updated = SendIntent(
            packet_id=current.packet_id,
            channel=current.channel,
            attempt=current.attempt,
            recipients_sha256=current.recipients_sha256,
            body_sha256=current.body_sha256,
            recorded_at=moment,
            state=SendState.VERIFIED,
            message_id=message_id,
            transitions=(*current.transitions, Transition(moment, SendState.VERIFIED, evidence)),
            approval=current.approval,
        )
        return _append(directory, current, updated)


def _verify_parts(packet_body: str, sent_text: str, packet_id: str) -> tuple[str, str, str | None]:
    expected = hashlib.sha256(normalize_readback(packet_body).encode("utf-8")).hexdigest()
    actual = hashlib.sha256(normalize_readback(sent_text).encode("utf-8")).hexdigest()
    tail_problem = _packet_id_tail_problem(sent_text, packet_id)
    return expected, actual, tail_problem


def _packet_id_tail_problem(sent_text: str, packet_id: str) -> str | None:
    """readback 의 마지막 내용 줄은 정확히 `packet-id: <packet_id>` 하나여야 한다. 문제 없으면 None."""
    lines = [line.rstrip() for line in sent_text.replace("\r\n", "\n").split("\n")]
    tails = [line for line in lines if line.startswith(_PACKET_ID_TRAILER)]
    if not tails:
        return "tail_missing"
    if len(tails) > 1:
        return "tail_duplicate"
    content = [line for line in lines if line.strip()]
    if not content or content[-1] != tails[0]:
        return "tail_not_last"
    if tails[0][len(_PACKET_ID_TRAILER) :].strip() != packet_id:
        return "tail_mismatch"
    return None
