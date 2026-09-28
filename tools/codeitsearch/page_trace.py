"""Persist every page the search actually visited into Supabase ``page_snapshots``.

사장님 규칙 — 사람인·잡코리아·링크드인은 **방문 페이지와 리스팅 페이지를 모두 저장**한다.
증거 없는 후보는 후보가 아니고, 증거 없는 순회는 순회가 아니다. A run that cannot show
which pages it opened cannot be audited, and cannot be resumed after a block.

The browser is driven by the agent through the Chrome MCP tools, not by this module.
The agent captures ``url`` / ``page_title`` / ``body_text`` / ``interactive_elements``
and hands them here, so the recorder stays portable across Windows and macOS and does
not need a local CDP port.

    python tools/codeitsearch/page_trace.py open-job --command codeitsearch --params-file p.json
    python tools/codeitsearch/page_trace.py record  --job-id 12 --snapshot-file s.json
    python tools/codeitsearch/page_trace.py close-job --job-id 12 --status done --summary-file r.json
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from supabase_io import insert, select  # noqa: E402

JOBS_TABLE = "search_jobs"
SNAPSHOTS_TABLE = "page_snapshots"

#: Every action kind the recorder accepts. A run is auditable only if each step says
#: what it was, so free-text actions are refused rather than silently stored.
ACTIONS = (
    "visit",  # 한 페이지를 열었다
    "listing",  # 후보 리스팅(검색 결과) 페이지
    "filter_open",  # 필터 팝업을 열었다
    "filter_apply",  # 필터를 적용했다
    "profile",  # 후보 상세
    "auth_wall",  # 로그인/인증 벽에 막혔다
    "blocked",  # 캡차·차단·오류
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def open_job(command: str, params: dict[str, Any], requested_by: str) -> int:
    """Create the job row and return the id Supabase actually stored.

    ``insert(assign_ids=...)`` may re-pick the id after a PK conflict, so the id is read
    back from the mutated row rather than from the first allocation.
    """
    row: dict[str, Any] = {
        "command": command,
        "params": params,
        "status": "running",
        "requested_by": requested_by,
        "requested_at": _now(),
        "started_at": _now(),
        "retry_count": 0,
    }
    insert(JOBS_TABLE, [row], assign_ids="id")
    return int(row["id"])


def record(job_id: int, snapshots: list[dict[str, Any]]) -> int:
    """Append page snapshots for a job, numbering steps after whatever is already stored."""
    for snapshot in snapshots:
        action = snapshot.get("action")
        if action not in ACTIONS:
            raise ValueError(f"unknown action {action!r}; expected one of {ACTIONS}")
        if not snapshot.get("url"):
            raise ValueError("every snapshot needs the url it was captured from")

    existing = select(
        SNAPSHOTS_TABLE,
        [("search_job_id", f"eq.{job_id}"), ("select", "step_index"),
         ("order", "step_index.desc"), ("limit", "1")],
    )
    step = (existing[0]["step_index"] + 1) if existing else 0

    rows = []
    for offset, snapshot in enumerate(snapshots):
        rows.append(
            {
                "search_job_id": job_id,
                "platform": snapshot.get("platform", "saramin"),
                "step_index": step + offset,
                "action": snapshot["action"],
                "url": snapshot["url"],
                "page_title": snapshot.get("page_title"),
                "body_text": snapshot.get("body_text"),
                "interactive_elements": snapshot.get("interactive_elements") or [],
                "captured_at": snapshot.get("captured_at") or _now(),
            }
        )
    return insert(SNAPSHOTS_TABLE, rows, assign_ids="id")


#: ``search_jobs.status`` carries a CHECK constraint that only accepts these. "blocked"
#: is a real outcome for this pipeline (auth wall, captcha) but the column cannot store
#: it, so it is written as ``failed`` and kept verbatim in ``result_summary.outcome``.
DB_STATUS = {"done": "done", "failed": "failed", "blocked": "failed"}


def close_job(job_id: int, status: str, summary: dict[str, Any], error: str | None) -> None:
    if status not in DB_STATUS:
        raise ValueError(f"unknown status {status!r}; expected one of {sorted(DB_STATUS)}")
    from supabase_io import _request  # noqa: PLC0415 — internal patch helper

    _request(
        "PATCH",
        f"{JOBS_TABLE}?id=eq.{job_id}",
        payload={
            "status": DB_STATUS[status],
            "finished_at": _now(),
            "result_summary": {**summary, "outcome": status},
            "error_message": error,
        },
        prefer="return=representation",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_open = sub.add_parser("open-job")
    p_open.add_argument("--command", required=True)
    p_open.add_argument("--params-file", type=Path, required=True)
    p_open.add_argument("--requested-by", default="claude-win")

    p_rec = sub.add_parser("record")
    p_rec.add_argument("--job-id", type=int, required=True)
    p_rec.add_argument("--snapshot-file", type=Path, required=True)

    p_close = sub.add_parser("close-job")
    p_close.add_argument("--job-id", type=int, required=True)
    p_close.add_argument("--status", required=True, choices=["done", "blocked", "failed"])
    p_close.add_argument("--summary-file", type=Path)
    p_close.add_argument("--error")

    args = parser.parse_args(argv)

    if args.cmd == "open-job":
        params = json.loads(args.params_file.read_text(encoding="utf-8"))
        job_id = open_job(args.command, params, args.requested_by)
        print(job_id)
        return 0

    if args.cmd == "record":
        payload = json.loads(args.snapshot_file.read_text(encoding="utf-8"))
        snapshots = payload if isinstance(payload, list) else payload["snapshots"]
        written = record(args.job_id, snapshots)
        print(f"recorded {written} page snapshots for job {args.job_id}")
        return 0

    summary = (
        json.loads(args.summary_file.read_text(encoding="utf-8")) if args.summary_file else {}
    )
    close_job(args.job_id, args.status, summary, args.error)
    print(f"job {args.job_id} -> {args.status}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
