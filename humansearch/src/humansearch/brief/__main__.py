"""HS-13.10 — `python -m humansearch.brief` 의 유일한 진입점.

계약: docs/engineering/humansearch-hs13-position-brief-goal-2026-09-10.md §5 __main__.py.
하위 명령은 `verify` 뿐이다(발송 명령 없음). 여기서는 argparse 로 인자만 풀어
`cli.verify` 를 부르고 그 결과로 `sys.exit` 한다 — 판단 로직은 전부 `cli.py` 에 있다.
"""

from __future__ import annotations

import sys

from .cli import verify

__all__ = ["main"]


def main(argv: list[str] | None = None) -> int:
    raise NotImplementedError("RED: HS-13.10 CLI 진입점은 아직 구현되지 않았다")


if __name__ == "__main__":
    sys.exit(main())
