"""HS-13.10 — 발송된 팀 메일의 readback 본문을 패킷과 대조해 발송을 판정한다.

계약: docs/engineering/humansearch-hs13-position-brief-goal-2026-09-10.md §5 __main__.py · §9 HS-13.10.
이 모듈은 두 파일(패킷 JSON·readback 평문)을 읽어 해시를 비교하는 판정만 한다.
발송·네트워크·시계 접근 0 — `__main__.py` 가 argparse 로 인자만 풀어 이 함수를 부른다.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from .packet import from_json
from .types import BriefInputError

__all__ = ["verify"]

_PACKET_ID_TRAILER = "packet-id: "


def _normalize_body(text: str) -> str:
    """CRLF→LF·줄 끝 공백 제거·전체 strip·§10 ③ `packet-id: <id>` 꼬리 줄 제거.

    패킷 본문(`mail.body`)에는 보통 꼬리 줄이 없으므로 이 함수를 적용해도 no-op 이고,
    readback 본문에는 러너가 발송 시 붙인 토큰이 있으므로 여기서 떼어낸다 —
    같은 함수를 양쪽에 적용해야 두 해시가 같은 기준으로 비교된다.
    """
    text = text.replace("\r\n", "\n")
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
        raise BriefInputError(
            f"{label} 파일을 읽지 못했다: {error.__class__.__name__}"
        ) from None
    except UnicodeDecodeError as error:
        raise BriefInputError(
            f"{label} 파일이 UTF-8 이 아니다: {error.__class__.__name__}"
        ) from None


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

    expected = hashlib.sha256(_normalize_body(packet.mail.body).encode("utf-8")).hexdigest()
    actual = hashlib.sha256(_normalize_body(sent_text).encode("utf-8")).hexdigest()

    if expected == actual:
        return 0, f"VERIFIED packet_id={packet.packet_id} body_sha256={expected}"
    return 1, f"SENT_UNVERIFIED packet_id={packet.packet_id} expected={expected} actual={actual}"
