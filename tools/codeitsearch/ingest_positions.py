"""Load a codeit careers snapshot into Supabase ``jobmarket_positions``.

Usage:
    python tools/codeitsearch/ingest_positions.py tools/codeitsearch/data/<snapshot>.json
    python tools/codeitsearch/ingest_positions.py <snapshot> --dry-run

Re-running the same snapshot is idempotent: rows for (platform, snapshot_date,
source_file) are deleted before the insert, so a partial earlier run cannot
double-count.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from collections import Counter
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from segmentation import segment_positions  # noqa: E402
from supabase_io import delete, insert, next_id, select  # noqa: E402

POSITIONS_TABLE = "jobmarket_positions"
SNAPSHOTS_TABLE = "jobmarket_snapshots"
REGISTRY = (
    Path(__file__).resolve().parents[2]
    / "contracts" / "humansearch" / "company-careers-sources.json"
)


def company_entry(company_key: str) -> dict[str, Any]:
    """Look the company up in the registry. An unknown key is a hard failure.

    Without this the ingester quietly stamped Codeit's detail-URL template, company_norm
    and location onto every company's rows — so a wrtnsearch run would have written
    Codeit data under Wrtn's name.
    """
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    for entry in registry["companies"]:
        if entry["key"] == company_key:
            return entry
    known = ", ".join(e["key"] for e in registry["companies"])
    raise KeyError(f"unknown company_key {company_key!r}; registry has: {known}")


def build_rows(snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    platform = snapshot["platform"]
    snapshot_date = snapshot["snapshot_date"]
    company = snapshot["company"]
    company_key = snapshot["company_key"]
    entry = company_entry(company_key)
    # 모르는 값은 지어내지 않는다 — 레지스트리에 상세 URL 형식이 없으면 url 은 비운다.
    template = entry.get("detail_url_template")
    location = snapshot.get("location")
    source_file = f"{company_key}search/{Path(snapshot['source']).name}/{snapshot_date}"
    rows = []
    for position in segment_positions(snapshot["positions"]):
        keywords = position["keywords"]
        rows.append(
            {
                "snapshot_date": snapshot_date,
                "platform": platform,
                "segment": position["segment"],
                "keyword": keywords["core"][0] if keywords["core"] else None,
                "title": position["title"],
                "company": company,
                "company_norm": company_key,
                "location": location,
                "url": (
                    template.format(posting_id=position["posting_id"]) if template else None
                ),
                "posting_id": position["posting_id"],
                "annual_from": position["annual_from"],
                "annual_to": position["annual_to"],
                "platforms_csv": platform,
                "raw_titles_json": {
                    "title": position["title"],
                    "group": position["group"],
                    "job": position["job"],
                    "exp": position["exp"],
                    "etype": position["etype"],
                    "status": position["status"],
                    "searchable": position["searchable"],
                },
                "source_file": source_file,
                "core_keywords_json": keywords["core"],
                "key_phrases_json": keywords["expanded"] + keywords["stack"],
                "preferred_keywords_json": keywords["preferred"],
                "jd_keyword_analysis_source": "ooosearch_segmentation",
                "jd_keyword_analysis_version": "ooosearch-segment-v2-bilingual",
            }
        )
    return rows


def build_snapshot_row(snapshot: dict[str, Any], rows: list[dict[str, Any]]) -> dict[str, Any]:
    per_segment = Counter(row["segment"] for row in rows)
    return {
        "snapshot_date": snapshot["snapshot_date"],
        "source_file": rows[0]["source_file"],
        "platform_label": snapshot["platform"],
        "total_positions": len(rows),
        "total_companies": 1,
        "per_platform_json": {snapshot["platform"]: len(rows)},
        "per_segment_json": dict(sorted(per_segment.items())),
        "loaded_at": datetime.now(timezone.utc).isoformat(),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshot", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    snapshot = json.loads(args.snapshot.read_text(encoding="utf-8"))
    rows = build_rows(snapshot)
    snapshot_row = build_snapshot_row(snapshot, rows)

    searchable = [r for r in rows if r["raw_titles_json"]["searchable"]]
    print(f"snapshot     : {args.snapshot}")
    print(f"positions    : {len(rows)}")
    print(f"searchable   : {len(searchable)} (정규직 · 상시채용 · 비프리랜서)")
    print("segments     :")
    for segment, count in sorted(snapshot_row["per_segment_json"].items()):
        mark = " *" if any(r["segment"] == segment for r in searchable) else ""
        print(f"  {segment:<24} {count:>3}{mark}")

    if args.dry_run:
        print("\n[dry-run] nothing written")
        return 0

    key = [
        ("platform", f"eq.{snapshot['platform']}"),
        ("snapshot_date", f"eq.{snapshot['snapshot_date']}"),
        ("source_file", f"eq.{rows[0]['source_file']}"),
    ]
    # jobmarket_positions carries a natural unique key (uq_jmp on snapshot_date,
    # platform, segment, title, company, url, source_file), so the rows for this key
    # must go away before the new ones land. That delete is the dangerous step on a
    # production database: PostgREST gives us no transaction, so a failing insert would
    # leave the day's snapshot simply gone. Keep a copy and put it back if the insert
    # fails — best effort, but never a silent loss.
    backup = select(POSITIONS_TABLE, [*key, ("select", "*")])
    removed = delete(POSITIONS_TABLE, key)
    try:
        # The id sequence lags an earlier bulk import, so ids are allocated here.
        written = insert(POSITIONS_TABLE, rows, assign_ids="id")
    except Exception:
        if backup:
            insert(POSITIONS_TABLE, backup)
            print(f"insert failed — restored {len(backup)} previous rows", file=sys.stderr)
        raise

    snapshot_key = [
        ("snapshot_date", f"eq.{snapshot['snapshot_date']}"),
        ("source_file", f"eq.{snapshot_row['source_file']}"),
    ]
    snapshot_backup = select(SNAPSHOTS_TABLE, [*snapshot_key, ("select", "*")])
    delete(SNAPSHOTS_TABLE, snapshot_key)
    try:
        insert(SNAPSHOTS_TABLE, [snapshot_row])
    except Exception:
        if snapshot_backup:
            insert(SNAPSHOTS_TABLE, snapshot_backup)
        raise

    verified = select(POSITIONS_TABLE, [*key, ("select", "posting_id")])
    print(f"\ndeleted {len(removed)} stale, inserted {written}, verified {len(verified)} in Supabase")
    if len(verified) != len(rows):
        print("MISMATCH — verified count does not equal built rows", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
