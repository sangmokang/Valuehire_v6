"""DB-backed operating snapshot validation for the Weekly CEO brief."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Callable


PROVENANCE = "sql_rpc:weekly_brief_snapshot"
TIMEZONE = "Asia/Seoul"
COUNT_SEMANTICS = "[week_start, week_end) exact SQL counts; current snapshots are explicitly separate"
CLOSED_WEEK_METRICS = {
    "new_positions",
    "new_position_companies",
    "ai_search_runs",
    "position_coverage",
    "recommended_people",
    "admin_ai_search_rows",
    "recommendation_events",
}
FUNNEL_METRICS = {
    "ai_sourcing",
    "proposal",
    "recommended",
    "interviewing",
    "final_pass",
    "joined",
}
TARGET_METRICS = {
    "weekly_proposals",
    "weekly_recommendations",
    "weekly_revenue",
    "annual_recommendations",
    "annual_revenue",
    "average_fee",
    "proposal_acceptance_rate",
    "recommend_to_final_rate",
    "recommend_to_join_rate",
}


def _nonnegative_integer(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _nonnegative_number(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and value >= 0
    )


def _parse_date(value: Any) -> date | None:
    try:
        return date.fromisoformat(value) if isinstance(value, str) else None
    except ValueError:
        return None


def _timestamps_valid(
    current: dict[str, Any],
    generated_at: Any,
    meeting_at: datetime,
    parse_datetime: Callable[[str], datetime],
) -> bool:
    try:
        timestamps = [
            parse_datetime(generated_at),
            parse_datetime(current["position_last_synced_at"]),
            parse_datetime(current["candidate_last_synced_at"]),
        ]
    except (KeyError, TypeError, ValueError):
        return False
    return all(timestamp <= meeting_at for timestamp in timestamps)


def _source_is_verified(
    source_snapshot_id: Any,
    source_snapshots: Any,
    meeting_date: str,
) -> bool:
    if not isinstance(source_snapshot_id, str) or not isinstance(source_snapshots, list):
        return False
    return any(
        isinstance(snapshot, dict)
        and snapshot.get("snapshot_id") == source_snapshot_id
        and snapshot.get("source_system") == "database"
        and snapshot.get("status") == "PASS"
        and snapshot.get("source_uri_ref") == f"rpc:weekly_brief_snapshot:{meeting_date}"
        for snapshot in source_snapshots
    )


def validate_operating_snapshot(
    value: Any,
    run: dict[str, datetime] | None,
    source_snapshots: Any,
    parse_datetime: Callable[[str], datetime],
    errors: list[str],
    require_snapshot: bool,
) -> dict[str, Any]:
    """Return a normalized DB snapshot or fail closed when db_read is PASS."""
    if value is None:
        if require_snapshot:
            errors.append("OPERATING_SNAPSHOT_MISSING")
        return {}
    required = {
        "source_snapshot_id", "meeting_date", "generated_at", "timezone",
        "provenance", "count_semantics", "closed_week", "current", "targets",
    }
    if not isinstance(value, dict) or set(value) != required or run is None:
        errors.append("OPERATING_SNAPSHOT_INVALID")
        return {}
    closed_week, current, targets = value["closed_week"], value["current"], value["targets"]
    if not all(isinstance(item, dict) for item in (closed_week, current, targets)):
        errors.append("OPERATING_SNAPSHOT_INVALID")
        return {}
    week_start = _parse_date(closed_week.get("week_start"))
    week_end = _parse_date(closed_week.get("week_end"))
    funnel = current.get("funnel")
    valid = (
        value["provenance"] == PROVENANCE
        and value["timezone"] == TIMEZONE
        and value["count_semantics"] == COUNT_SEMANTICS
        and value["meeting_date"] == run["meeting_at"].date().isoformat()
        and _source_is_verified(
            value["source_snapshot_id"], source_snapshots, value["meeting_date"]
        )
        and week_start == run["window_start"].date()
        and week_end == run["window_end_exclusive"].date()
        and isinstance(closed_week.get("week_label"), str)
        and bool(closed_week["week_label"])
        and set(closed_week) == CLOSED_WEEK_METRICS | {"week_start", "week_end", "week_label"}
        and all(_nonnegative_integer(closed_week[key]) for key in CLOSED_WEEK_METRICS)
        and set(current) == {
            "open_positions", "position_last_synced_at", "candidate_last_synced_at", "funnel",
        }
        and _nonnegative_integer(current.get("open_positions"))
        and isinstance(funnel, dict)
        and set(funnel) == FUNNEL_METRICS
        and all(_nonnegative_integer(funnel[key]) for key in FUNNEL_METRICS)
        and set(targets) == TARGET_METRICS
        and all(_nonnegative_number(targets[key]) for key in TARGET_METRICS)
        and _timestamps_valid(current, value["generated_at"], run["meeting_at"], parse_datetime)
    )
    if not valid:
        errors.append("OPERATING_SNAPSHOT_INVALID")
        return {}
    return {
        key: value[key]
        for key in (
            "source_snapshot_id", "meeting_date", "generated_at", "timezone",
            "provenance", "count_semantics", "closed_week", "current", "targets",
        )
    }
