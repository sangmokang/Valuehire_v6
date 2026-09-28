"""Load a codeit careers snapshot into Supabase ``jobmarket_positions``.

Usage:
    python tools/codeitsearch/ingest_positions.py tools/codeitsearch/data/<snapshot>.json
    python tools/codeitsearch/ingest_positions.py <snapshot> --dry-run

Re-running the same snapshot is idempotent and never leaves a gap: each run writes
under its own source_file suffix first, and only then removes the previous run's rows.
PostgREST has no transaction, so that order is the whole safety mechanism.
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
from supabase_io import delete, insert, select  # noqa: E402

POSITIONS_TABLE = "jobmarket_positions"
SNAPSHOTS_TABLE = "jobmarket_snapshots"

#: uq_jmp 는 COALESCE 표현식 위의 유니크 인덱스라 PostgREST 의 on_conflict(컬럼 목록)로는
#: 지정할 수 없다 — 42P10. 그래서 upsert 대신, 실행마다 source_file 에 run 접미사를 붙여
#: **새 행을 먼저 쓰고** 성공한 뒤에 이전 실행분을 지운다. 어느 순간에도 데이터가 비지 않는다.
RUN_SEPARATOR = "#run-"
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


def source_prefix_for(snapshot: dict[str, Any]) -> str:
    """Stable part of source_file — every run of this snapshot shares it."""
    company_key = snapshot["company_key"]
    return (
        f"{company_key}search/{Path(snapshot['source']).name}/{snapshot['snapshot_date']}"
    )


def build_rows(snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    platform = snapshot["platform"]
    snapshot_date = snapshot["snapshot_date"]
    company = snapshot["company"]
    company_key = snapshot["company_key"]
    entry = company_entry(company_key)
    # 모르는 값은 지어내지 않는다 — 레지스트리에 상세 URL 형식이 없으면 url 은 비운다.
    template = entry.get("detail_url_template")
    location = snapshot.get("location")
    source_prefix = f"{company_key}search/{Path(snapshot['source']).name}/{snapshot_date}"
    # run_id 가 없으면 지금 시각으로 만든다 — source_file 이 실행마다 달라야
    # 새 행이 기존 행과 자연 키로 충돌하지 않고 "삭제 없이 먼저 쓰기" 가 성립한다.
    run_id = snapshot.get("run_id") or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    source_file = f"{source_prefix}{RUN_SEPARATOR}{run_id}"
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
    # run_id 는 source_file 을 실행마다 유일하게 만들어, 새 행이 기존 행과 자연 키로
    # 충돌하지 않게 한다. 이것이 "삭제 없이 먼저 쓰기"를 가능하게 하는 유일한 장치다.
    snapshot.setdefault("run_id", datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ"))
    rows = build_rows(snapshot)
    if not rows:
        print("snapshot has no positions — nothing to ingest", file=sys.stderr)
        return 1
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

    # 순서가 전부다. PostgREST 에는 트랜잭션이 없으므로
    #   ① 새 행 insert → ② 새 행 검증 → ③ 요약 행 insert → ④ 이전 실행분 delete
    # 어느 단계가 실패해도 이전 실행분은 그대로 남는다. 검증(②)보다 삭제를 먼저 하면
    # "insert 는 200 이었는데 조회하면 0행" 인 경우 기존 데이터까지 잃는다(codex 3차).
    prefix = source_prefix_for(snapshot)
    current_source = rows[0]["source_file"]
    company_norm = rows[0]["company_norm"]
    day_key = [
        ("platform", f"eq.{snapshot['platform']}"),
        ("snapshot_date", f"eq.{snapshot['snapshot_date']}"),
    ]
    # 지울 대상은 id 로 특정한다. source_file 로 LIKE 를 걸면 '_' 와 '%' 가 SQL 와일드카드라
    # 파일명에 그 글자가 하나만 들어와도 다른 회사 행까지 지워진다.
    before = select(POSITIONS_TABLE, [*day_key, ("select", "id,source_file,company_norm")])

    # ① 새 행
    written = insert(POSITIONS_TABLE, rows, assign_ids="id")

    # ② 검증 — 여기서 실패하면 아무것도 지우지 않고 그대로 멈춘다.
    verified = select(
        POSITIONS_TABLE,
        [*day_key, ("source_file", f"eq.{current_source}"), ("select", "posting_id")],
    )
    if len(verified) != len(rows):
        print(
            f"MISMATCH — wrote {written} but only {len(verified)} rows read back; "
            "previous run left untouched",
            file=sys.stderr,
        )
        return 1

    # ③ 요약 행 — 포지션 행과 같은 source_file 을 가리킨다.
    insert(SNAPSHOTS_TABLE, [snapshot_row])

    # ④ 이전 실행분만 정리. 회사까지 확인해 같은 접두사를 가진 남의 행을 건드리지 않는다.
    stale_ids = [
        r["id"]
        for r in before
        if str(r.get("source_file", "")).startswith(prefix)
        and r["source_file"] != current_source
        and r.get("company_norm") == company_norm
    ]
    removed = []
    if stale_ids:
        removed = delete(
            POSITIONS_TABLE, [*day_key, ("id", f"in.({','.join(map(str, stale_ids))})")]
        )
    for row in select(
        SNAPSHOTS_TABLE,
        [("snapshot_date", f"eq.{snapshot['snapshot_date']}"), ("select", "source_file")],
    ):
        source = str(row.get("source_file", ""))
        if source.startswith(prefix) and source != snapshot_row["source_file"]:
            delete(
                SNAPSHOTS_TABLE,
                [
                    ("snapshot_date", f"eq.{snapshot['snapshot_date']}"),
                    ("source_file", f"eq.{source}"),
                ],
            )

    print(
        f"\nwrote {written} rows, verified {len(verified)}, "
        f"then removed {len(removed)} from earlier runs"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
