"""Pytest plugin: record proof that the HumanSearch module was really imported.

Loaded via ``pytest -p hs_import_spy`` with PYTHONPATH pointing at ``scripts/``.
Writes ``{"module_file": ..., "collected": N}`` to ``$HS_SPY_OUT`` at session finish,
so the gate script can verify a runtime import happened instead of trusting
source-text claims (P16).
"""

import json
import os
import sys
from typing import Any


def pytest_sessionfinish(session: Any, exitstatus: int) -> None:
    out_path = os.environ.get("HS_SPY_OUT")
    if not out_path:
        return
    module = sys.modules.get("humansearch")
    module_file = getattr(module, "__file__", None) if module is not None else None
    payload = {
        "module_file": module_file,
        "collected": int(getattr(session, "testscollected", 0)),
    }
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh)
