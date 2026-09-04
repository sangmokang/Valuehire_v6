#!/usr/bin/env python3
"""Compare the active PostgreSQL business snapshot with the JSON contracts."""
from __future__ import annotations

import json
import sys
from decimal import Decimal
from pathlib import Path


REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "tools" / "invoice"))
from storage_common import business_contract_identity, tenant_id  # noqa: E402


def main() -> int:
    try:
        actual = json.load(sys.stdin, parse_float=Decimal, parse_int=Decimal)
        version, contract_sha, invoice, settlement = business_contract_identity()
    except (json.JSONDecodeError, OSError, ValueError) as error:
        print(f"FAIL: cannot inspect business snapshot: {error}")
        return 1
    expected = {
        "version": version,
        "sha256": contract_sha,
        "config": {
            "tenant_id": tenant_id(),
            "issuer_name": invoice["issuer"]["company_name"],
            "due_offset_days": Decimal(invoice["payment"]["due_offset_days"]),
            "tax_policy": invoice["billing"]["tax_policy"],
            "company_share_percent": Decimal(settlement["company_share_percent"]),
            "withholding_percent": Decimal(settlement["withholding_percent"]),
            "allocation_total_percent": Decimal(
                settlement["allocation_total_percent"]
            ),
            "bank_name": invoice["payment"]["bank_name"],
            "account_number_display": invoice["payment"][
                "account_number_display"
            ],
            "account_holder": invoice["payment"]["account_holder"],
            "default_recipient": invoice["delivery"]["default_recipient"],
        },
    }
    if actual != expected:
        print(f"FAIL: database business snapshot drift\nactual={actual}\nexpected={expected}")
        return 1
    print("PASS: active PostgreSQL business snapshot matches JSON contracts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
