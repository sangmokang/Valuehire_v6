"""HS-13.10 — `python -m humansearch.brief` 의 유일한 진입점.

계약: docs/engineering/humansearch-hs13-position-brief-goal-2026-09-10.md §5 __main__.py.
하위 명령은 `verify` 뿐이다(발송 명령 없음). 여기서는 argparse 로 인자만 풀어
`cli.verify` 를 부르고 그 결과로 `sys.exit` 한다 — 판단 로직은 전부 `cli.py` 에 있다.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .cli import verify

__all__ = ["main"]


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m humansearch.brief")
    subparsers = parser.add_subparsers(dest="command", required=True)

    verify_parser = subparsers.add_parser(
        "verify", help="패킷과 readback 본문 해시를 대조한다"
    )
    verify_parser.add_argument("--packet", required=True, type=Path)
    verify_parser.add_argument("--sent", required=True, type=Path)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    exit_code, message = verify(args.packet, args.sent)
    stream = sys.stdout if exit_code in (0, 1) else sys.stderr
    print(message, file=stream)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
