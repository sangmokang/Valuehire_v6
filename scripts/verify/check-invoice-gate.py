#!/usr/bin/env python3
"""Fail closed if Invoice tests can be replaced with fabricated PASS output."""
from __future__ import annotations

import argparse
from pathlib import Path


REQUIRED_ACCEPTANCE_LINES = {
    'python3 -m unittest discover -s tools/invoice/tests -v >"$test_log" 2>&1',
    'bash tools/invoice/tests/test_postgres_integrity.sh',
}
REQUIRED_WORKFLOW_LINES = {
    "python3 -m unittest discover -s tools/invoice/tests -v",
    "bash tools/invoice/tests/test_postgres_integrity.sh",
    "python3 scripts/verify/check-invoice-gate.py",
}


def code_lines(path: Path) -> set[str]:
    if not path.is_file():
        raise ValueError(f"missing file: {path}")
    return {
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--acceptance", type=Path, default=Path("scripts/acceptance-invoice.sh")
    )
    parser.add_argument(
        "--workflow", type=Path, default=Path(".github/workflows/verify.yml")
    )
    args = parser.parse_args()
    try:
        acceptance = code_lines(args.acceptance)
        workflow = code_lines(args.workflow)
    except (OSError, UnicodeError, ValueError) as error:
        print(f"FAIL: {error}")
        return 1
    missing_acceptance = REQUIRED_ACCEPTANCE_LINES - acceptance
    missing_workflow = REQUIRED_WORKFLOW_LINES - workflow
    if missing_acceptance or missing_workflow:
        print(
            "FAIL: Invoice gate wiring missing; "
            f"acceptance={sorted(missing_acceptance)}, "
            f"workflow={sorted(missing_workflow)}"
        )
        return 1
    print("PASS: Invoice unit and PostgreSQL tests have independent CI wiring")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
