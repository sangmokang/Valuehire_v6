"""PII-free command-line readback for the pre-live source policy."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path

from .source_contract import load_source_policy


def main(argv: Sequence[str] | None = None) -> int:
    """Validate one source contract and print its public readiness report."""

    parser = argparse.ArgumentParser(description="Validate admin dashboard source policy")
    parser.add_argument("--contract", required=True, type=Path)
    args = parser.parse_args(list(argv) if argv is not None else None)
    policy = load_source_policy(args.contract)
    print(json.dumps(policy.to_public_dict(), ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
