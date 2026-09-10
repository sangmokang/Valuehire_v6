"""HS-13.10 — 발송된 팀 메일의 readback 본문을 패킷과 대조해 발송을 판정한다.

계약: docs/engineering/humansearch-hs13-position-brief-goal-2026-09-10.md §5 __main__.py · §9 HS-13.10.
이 모듈은 두 파일(패킷 JSON·readback 평문)을 읽어 해시를 비교하는 판정만 한다.
발송·네트워크·시계 접근 0 — `__main__.py` 가 argparse 로 인자만 풀어 이 함수를 부른다.
"""

from __future__ import annotations

from pathlib import Path

__all__ = ["verify"]


def verify(packet_path: Path, sent_path: Path) -> tuple[int, str]:
    """패킷 파일과 readback 평문을 정규화해 본문 해시를 대조한다.

    반환: (exit_code, message). exit 0/1 의 message 는 stdout 한 줄,
    exit 2 의 message 는 stderr 사유다 — 어디에 찍을지는 호출자(`__main__.py`)가 정한다.
    """
    raise NotImplementedError("RED: HS-13.10 verify 는 아직 구현되지 않았다")
