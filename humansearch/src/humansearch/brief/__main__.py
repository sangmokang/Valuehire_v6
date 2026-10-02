"""HS-13.10 — `python -m humansearch.brief` 의 유일한 진입점.

계약: docs/engineering/humansearch-hs13-position-brief-goal-2026-09-10.md §5 __main__.py.
하위 명령은 `verify` 뿐이다(발송 명령 없음). 여기서는 argparse 로 인자만 풀어
`cli.verify` 를 부르고 그 결과로 `sys.exit` 한다 — 판단 로직은 전부 `cli.py` 에 있다.
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

from .cli import verify, verify_and_mark
from .types import BriefInputError

__all__ = ["main"]


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m humansearch.brief")
    subparsers = parser.add_subparsers(dest="command", required=True)

    verify_parser = subparsers.add_parser(
        "verify", help="패킷과 readback 본문 해시를 대조한다"
    )
    verify_parser.add_argument("--packet", required=True, type=Path)
    verify_parser.add_argument("--sent", required=True, type=Path)
    verify_parser.add_argument("--mark-dir", type=Path)
    verify_parser.add_argument("--message-id")
    verify_parser.add_argument("--at")
    verify_parser.add_argument("--channel", default="gmail")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.mark_dir is not None or args.message_id is not None or args.at is not None:
        if args.mark_dir is None or args.message_id is None or args.at is None:
            print("--mark-dir, --message-id, --at 은 함께 지정해야 한다", file=sys.stderr)
            return 2
        try:
            marked_at = datetime.fromisoformat(args.at)
            updated = verify_and_mark(
                args.mark_dir,
                args.packet,
                args.sent,
                args.message_id,
                marked_at,
                channel=args.channel,
            )
        except (BriefInputError, ValueError) as error:
            print(str(error), file=sys.stderr)
            return 2
        print(
            f"VERIFIED packet_id={updated.packet_id} attempt={updated.attempt} "
            f"body_sha256={updated.body_sha256} recipients_sha256={updated.recipients_sha256}"
        )
        return 0

    exit_code, message = verify(args.packet, args.sent)
    stream = sys.stdout if exit_code in (0, 1) else sys.stderr
    print(message, file=stream)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
