"""로컬 아카이버 SQLite 의 structured_json 을 운영 profile_archives 에 채운다 (RED 뼈대)."""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class LocalRow:
    local_id: str
    site: str
    structured_json: str


@dataclass
class Plan:
    to_fill: list[LocalRow] = field(default_factory=list)
    skipped_absent: list[str] = field(default_factory=list)
    skipped_filled: list[str] = field(default_factory=list)
    skipped_invalid: list[str] = field(default_factory=list)


@dataclass
class ApplyResult:
    written: int = 0
    unmatched: list[str] = field(default_factory=list)


def plan_backfill(local_rows: list[LocalRow], remote_state: dict[str, bool]) -> Plan:
    return Plan()


def apply_plan(transport, plan: Plan, ledger_path: Path, *, apply: bool) -> ApplyResult:
    return ApplyResult()


def load_creds(env_path: Path) -> tuple[str, str]:
    return ("", "")


if __name__ == "__main__":
    sys.exit(2)
