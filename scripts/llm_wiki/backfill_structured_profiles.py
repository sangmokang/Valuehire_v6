"""로컬 아카이버 SQLite 의 structured_json 을 운영 profile_archives 에 채운다.

정본: docs/sot/llm-wiki.md §복구 ①. 기본은 dry-run(쓰기 0건). --apply 에서만 PATCH 한다.
보호 계약:
  - 원격에 같은 local_id 행이 없으면 보내지 않는다(부분 행 INSERT 금지).
  - 원격 structured_json 이 이미 있으면 보내지 않는다. 서버측에도 structured_json=is.null 을 붙여
    계획 이후 다른 주체가 채운 행을 덮어쓰지 않는다(매치 0행이면 "쓰지 않음"으로 센다).
  - 쓰기 1건마다 장부 1줄(local_id, sha256, matched)을 남긴다. 되돌리기는 장부의 local_id 를 null 로.
  - 자격증명이 없으면 rc 2(NOT_RUN). 조용히 0건 성공으로 접지 않는다.
사용:
  python3 scripts/llm_wiki/backfill_structured_profiles.py --db <archive.db> --env <.env.local> [--apply] [--limit N]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import sys
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

BATCH = 200


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


def _valid_structured(text: str) -> bool:
    try:
        obj = json.loads(text)
    except (ValueError, TypeError):
        return False
    meta = obj.get("_meta") if isinstance(obj, dict) else None
    return isinstance(meta, dict) and bool(meta.get("input_hash"))


def plan_backfill(local_rows: list[LocalRow], remote_state: dict[str, bool]) -> Plan:
    """remote_state[local_id]: True=이미 채워짐, False=비어 있음, 키 없음=원격 행 없음."""
    plan = Plan()
    for row in local_rows:
        if not _valid_structured(row.structured_json):
            plan.skipped_invalid.append(row.local_id)
        elif row.local_id not in remote_state:
            plan.skipped_absent.append(row.local_id)
        elif remote_state[row.local_id]:
            plan.skipped_filled.append(row.local_id)
        else:
            plan.to_fill.append(row)
    return plan


def apply_plan(transport, plan: Plan, ledger_path: Path, *, apply: bool) -> ApplyResult:
    result = ApplyResult()
    if not apply:
        return result
    with ledger_path.open("a", encoding="utf-8") as ledger:
        for row in plan.to_fill:
            query = f"local_id=eq.{urllib.parse.quote(row.local_id, safe='')}&structured_json=is.null"
            matched = transport.patch(query, {"structured_json": json.loads(row.structured_json)})
            digest = hashlib.sha256(row.structured_json.encode("utf-8")).hexdigest()
            ledger.write(json.dumps({"local_id": row.local_id, "sha256": digest, "matched": matched}) + "\n")
            if matched == 1:
                result.written += 1
            else:
                result.unmatched.append(row.local_id)
    return result


def load_creds(env_path: Path) -> tuple[str, str]:
    values: dict[str, str] = {}
    for line in env_path.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.startswith("#"):
            key, _, val = line.partition("=")
            values[key.strip()] = val.strip().strip('"')
    url, key = values.get("NEXT_PUBLIC_SUPABASE_URL"), values.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        print("NOT_RUN: NEXT_PUBLIC_SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY 없음", file=sys.stderr)
        raise SystemExit(2)
    return url, key


def load_local_rows(db_path: Path, limit: int | None) -> list[LocalRow]:
    uri = f"file:{db_path}?mode=ro"
    sql = "SELECT id, site, structured_json FROM archives WHERE structured_json IS NOT NULL AND structured_json <> '' ORDER BY captured_at"
    if limit:
        sql += f" LIMIT {int(limit)}"
    with sqlite3.connect(uri, uri=True) as conn:
        return [LocalRow(str(i), str(s), str(j)) for i, s, j in conn.execute(sql)]


class RestTransport:
    """PostgREST 전송. 읽기는 GET, 쓰기는 PATCH(return=representation 으로 매치 행 수 readback)."""

    def __init__(self, url: str, key: str):
        self.base = url.rstrip("/") + "/rest/v1/profile_archives"
        self.headers = {"apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json"}

    def _call(self, method: str, query: str, body: dict | None, extra: dict[str, str]) -> list:
        data = json.dumps(body).encode("utf-8") if body is not None else None
        req = urllib.request.Request(f"{self.base}?{query}", data=data, method=method, headers={**self.headers, **extra})
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read().decode("utf-8")
        return json.loads(raw) if raw else []

    def get_remote_state(self, local_ids: list[str]) -> dict[str, bool]:
        state: dict[str, bool] = {}
        for i in range(0, len(local_ids), BATCH):
            chunk = local_ids[i:i + BATCH]
            ids = ",".join(urllib.parse.quote(f'"{x}"', safe='"') for x in chunk)
            rows = self._call("GET", f"select=local_id,structured_json&local_id=in.({ids})", None, {})
            for r in rows:
                state[str(r["local_id"])] = r["structured_json"] is not None
        return state

    def patch(self, query: str, body: dict) -> int:
        rows = self._call("PATCH", f"{query}&select=local_id", body, {"Prefer": "return=representation"})
        return len(rows)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--db", required=True, type=Path)
    ap.add_argument("--env", required=True, type=Path)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--ledger", type=Path, default=None)
    args = ap.parse_args(argv)
    url, key = load_creds(args.env)
    rows = load_local_rows(args.db, args.limit)
    transport = RestTransport(url, key)
    remote = transport.get_remote_state([r.local_id for r in rows])
    plan = plan_backfill(rows, remote)
    ledger = args.ledger or Path.home() / "valuehire-private" / "llm-wiki" / "backfill-ledger.jsonl"
    ledger.parent.mkdir(parents=True, exist_ok=True)
    result = apply_plan(transport, plan, ledger, apply=args.apply)
    print(json.dumps({
        "mode": "apply" if args.apply else "dry-run",
        "local_rows": len(rows), "remote_rows_found": len(remote),
        "to_fill": len(plan.to_fill), "skipped_absent": len(plan.skipped_absent),
        "skipped_filled": len(plan.skipped_filled), "skipped_invalid": len(plan.skipped_invalid),
        "written": result.written, "unmatched": len(result.unmatched), "ledger": str(ledger),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
