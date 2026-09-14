"""Plan-only CLI for RPS project resolution."""

import argparse
import json
from collections.abc import Sequence
from pathlib import Path

from .rps_project_resolution import resolve_rps_project


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Resolve an RPS project from a fresh observation without writes"
    )
    parser.add_argument("--input", required=True, type=Path)
    args = parser.parse_args(argv)

    payload = json.loads(args.input.read_text(encoding="utf-8"))
    result = resolve_rps_project(payload)
    print(
        json.dumps(
            {
                "status": result.status.value,
                "position_id": result.position_id,
                "project_id": result.project_id,
                "reason": result.reason,
                "plan_only": result.plan_only,
                "allows_write": result.allows_write,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
