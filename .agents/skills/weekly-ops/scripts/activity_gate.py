"""Career-page and consultant-outreach validation for the weekly gate."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Any, Callable


CAREER_STATUSES = {"PASS", "PARTIAL", "FAIL", "NOT_RUN", "STALE"}
OUTREACH_CHANNELS = {"saramin", "jobkorea", "linkedin_rps", "email"}
OUTREACH_STATUSES = {"PENDING", "SENT", "FAILED"}
PORTAL_CHANNELS = {"saramin", "jobkorea", "linkedin_rps"}
OUTREACH_ACCESS_STATES = {
    "AUTHENTICATED",
    "AUTH_REQUIRED",
    "TUTORIAL_OR_DEMO",
    "AUTOMATION_DENIED",
    "CHALLENGE",
    "MISSING_PROFILE",
    "STALE_PAGE",
}
ALLOWED_OUTREACH_SURFACES = {
    "jobkorea": {"position_offer_history"},
    "saramin": {"detailed_usage_history"},
    "linkedin_rps": {"inmail_audit_report", "recruiter_inbox_thread"},
}
LINKEDIN_EVENT_FIELDS = {"provider_seat_ref", "provider_project_ref"}


def validate_career_summaries(
    summaries: Any,
    source_snapshot_ids: set[str],
    parse_datetime: Callable[[str], datetime],
    errors: list[str],
) -> tuple[list[dict[str, Any]], list[str]]:
    if summaries is None:
        return [], []
    if not isinstance(summaries, list):
        errors.append("CAREER_SUMMARIES_INVALID")
        return [], []
    validated: list[dict[str, Any]] = []
    blockers: list[str] = []
    seen: set[str] = set()
    required = {
        "company",
        "official_url",
        "status",
        "active_requisitions",
        "talent_pools",
        "freshness_at",
        "limitation",
        "source_snapshot_id",
    }
    for item in summaries:
        if not isinstance(item, dict) or not required.issubset(item):
            errors.append("CAREER_SUMMARY_INVALID")
            continue
        company, status = item["company"], item["status"]
        counts_valid = all(
            isinstance(item[key], int) and item[key] >= 0
            for key in ("active_requisitions", "talent_pools")
        )
        try:
            parse_datetime(item["freshness_at"])
        except (TypeError, ValueError):
            errors.append("CAREER_FRESHNESS_INVALID")
            continue
        if (
            not isinstance(company, str)
            or not company.strip()
            or company in seen
            or status not in CAREER_STATUSES
            or not counts_valid
            or item["source_snapshot_id"] not in source_snapshot_ids
        ):
            errors.append("CAREER_SUMMARY_INVALID")
            continue
        seen.add(company)
        validated.append(dict(item))
        if status != "PASS":
            blockers.append(f"career:{company}:{status}")
    return validated, sorted(blockers)


def validate_outreach_events(
    events: Any,
    diagnostics: dict[str, dict[str, Any]],
    position_lookup: dict[str, dict[str, Any]],
    run: dict[str, datetime] | None,
    source_snapshot_ids: set[str],
    snapshot_evidence_refs: dict[str, set[str]],
    parse_datetime: Callable[[str], datetime],
    errors: list[str],
) -> list[dict[str, Any]]:
    if events is None:
        return []
    if not isinstance(events, list):
        errors.append("OUTREACH_EVENTS_INVALID")
        return []
    seen: set[str] = set()
    accepted: list[dict[str, Any]] = []
    required = {
        "event_id",
        "consultant_id",
        "consultant_display",
        "position_id",
        "channel",
        "status",
        "sent_at",
        "candidate_key_hmac",
        "source_snapshot_id",
    }
    for event in events:
        if not isinstance(event, dict) or not required.issubset(event):
            errors.append("OUTREACH_EVENT_INVALID")
            continue
        event_id = event["event_id"]
        if not isinstance(event_id, str) or not event_id or event_id in seen:
            errors.append("OUTREACH_EVENT_INVALID")
            continue
        seen.add(event_id)
        if (
            event["channel"] not in OUTREACH_CHANNELS
            or event["status"] not in OUTREACH_STATUSES
            or event["position_id"] not in position_lookup
            or not isinstance(event["consultant_id"], str)
            or not isinstance(event["consultant_display"], str)
            or not isinstance(event["candidate_key_hmac"], str)
            or not event["candidate_key_hmac"].startswith("hmac:")
            or event["source_snapshot_id"] not in source_snapshot_ids
        ):
            errors.append("OUTREACH_EVENT_INVALID")
            continue
        try:
            sent_at = parse_datetime(event["sent_at"])
        except (TypeError, ValueError):
            errors.append("OUTREACH_EVENT_INVALID")
            continue
        if event["status"] == "SENT" and not event.get("provider_receipt_ref"):
            errors.append("OUTREACH_SENT_WITHOUT_READBACK")
            continue
        if event["status"] == "SENT" and event["channel"] in PORTAL_CHANNELS:
            diagnostic = diagnostics.get(event["channel"])
            if not diagnostic_allows_event(diagnostic, event):
                errors.append("OUTREACH_SURFACE_UNVERIFIED")
                continue
            if event["channel"] == "linkedin_rps" and any(
                not isinstance(event.get(field), str) or not event[field]
                for field in LINKEDIN_EVENT_FIELDS
            ):
                errors.append("LINKEDIN_OUTREACH_DIMENSIONS_MISSING")
                continue
        if event["status"] == "SENT" and event["provider_receipt_ref"] not in snapshot_evidence_refs.get(
            event["source_snapshot_id"], set()
        ):
            errors.append("OUTREACH_RECEIPT_UNRESOLVED")
            continue
        if event["status"] != "SENT":
            continue
        if run and not (run["window_start"] <= sent_at < run["window_end_exclusive"]):
            continue
        accepted.append({**event, "_sent_at": sent_at})
    return aggregate_consultant_focus(accepted, position_lookup)


def validate_outreach_channel_diagnostics(
    diagnostics: Any,
    events: Any,
    source_snapshot_ids: set[str],
    errors: list[str],
) -> dict[str, dict[str, Any]]:
    portal_events = (
        [
            event
            for event in events
            if isinstance(event, dict) and event.get("channel") in PORTAL_CHANNELS
        ]
        if isinstance(events, list)
        else []
    )
    if not portal_events:
        return {}
    if not isinstance(diagnostics, list):
        errors.append("OUTREACH_DIAGNOSTICS_MISSING")
        return {}
    validated: dict[str, dict[str, Any]] = {}
    required = {
        "channel",
        "access_state",
        "surface_kind",
        "surface_ref",
        "stable_receipt_available",
        "source_snapshot_id",
    }
    for item in diagnostics:
        if not isinstance(item, dict) or not required.issubset(item):
            errors.append("OUTREACH_DIAGNOSTIC_INVALID")
            continue
        channel = item["channel"]
        if (
            channel not in PORTAL_CHANNELS
            or channel in validated
            or item["access_state"] not in OUTREACH_ACCESS_STATES
            or not isinstance(item["surface_kind"], str)
            or not item["surface_kind"]
            or not isinstance(item["surface_ref"], str)
            or not item["surface_ref"]
            or not isinstance(item["stable_receipt_available"], bool)
            or item["source_snapshot_id"] not in source_snapshot_ids
            or (
                (
                    item["access_state"] != "AUTHENTICATED"
                    or item["stable_receipt_available"] is not True
                )
                and (
                    not isinstance(item.get("blocker_reason"), str)
                    or not item["blocker_reason"].strip()
                )
            )
        ):
            errors.append("OUTREACH_DIAGNOSTIC_INVALID")
            continue
        validated[channel] = dict(item)
    if set(validated) != PORTAL_CHANNELS:
        errors.append("OUTREACH_DIAGNOSTICS_MISSING")
    return validated


def diagnostic_allows_event(
    diagnostic: dict[str, Any] | None, event: dict[str, Any]
) -> bool:
    if not diagnostic:
        return False
    return (
        diagnostic["access_state"] == "AUTHENTICATED"
        and diagnostic["stable_receipt_available"] is True
        and diagnostic["surface_kind"] in ALLOWED_OUTREACH_SURFACES[event["channel"]]
        and diagnostic["source_snapshot_id"] == event["source_snapshot_id"]
    )


def aggregate_consultant_focus(
    events: list[dict[str, Any]], position_lookup: dict[str, dict[str, Any]]
) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for event in events:
        grouped[event["consultant_id"]].append(event)
    result: list[dict[str, Any]] = []
    for consultant_id, consultant_events in grouped.items():
        total = len(consultant_events)
        by_position: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for event in consultant_events:
            by_position[event["position_id"]].append(event)
        positions = []
        for position_id, position_events in by_position.items():
            position = position_lookup[position_id]
            positions.append(
                {
                    "position_id": position_id,
                    "company": position["company"],
                    "title": position["title"],
                    "verified_sent_count": len(position_events),
                    "unique_candidate_count": len(
                        {event["candidate_key_hmac"] for event in position_events}
                    ),
                    "active_days": len(
                        {event["_sent_at"].date().isoformat() for event in position_events}
                    ),
                    "channels": sorted({event["channel"] for event in position_events}),
                    "focus_share": round(len(position_events) / total, 3),
                    "grass_evidence": "YELLOW_ELIGIBLE",
                }
            )
        positions.sort(key=lambda item: (-item["verified_sent_count"], item["company"], item["title"]))
        result.append(
            {
                "consultant_id": consultant_id,
                "consultant_display": consultant_events[0]["consultant_display"],
                "verified_sent_count": total,
                "unique_candidate_count": len(
                    {event["candidate_key_hmac"] for event in consultant_events}
                ),
                "active_days": len(
                    {event["_sent_at"].date().isoformat() for event in consultant_events}
                ),
                "positions": positions,
            }
        )
    result.sort(key=lambda item: (-item["verified_sent_count"], item["consultant_display"]))
    return result


def render_career_summaries(summaries: list[dict[str, Any]]) -> list[str]:
    lines: list[str] = []
    for item in sorted(summaries, key=lambda value: value["company"]):
        status = item["status"]
        if status == "PASS":
            lines.append(
                f"- {item['company']}: 실공고 {item['active_requisitions']}개, "
                f"인재풀 {item['talent_pools']}개."
            )
        elif status == "PARTIAL":
            lines.append(
                f"- {item['company']}: 부분 확인 {item['active_requisitions']}개. "
                f"{item['limitation']}"
            )
        else:
            lines.append(f"- {item['company']}: 수집 실패. {item['limitation']} 0건으로 해석 금지.")
    return lines

def render_consultant_focus(focus: list[dict[str, Any]]) -> list[str]:
    lines: list[str] = []
    for consultant in focus:
        lead = consultant["positions"][0]
        share = round(lead["focus_share"] * 100)
        lines.append(
            f"- {consultant['consultant_display']}: 검증 발송 {consultant['verified_sent_count']}건, "
            f"고유 후보 {consultant['unique_candidate_count']}명, 활동 {consultant['active_days']}일. "
            f"최대 집중은 {lead['company']} — {lead['title']} {lead['verified_sent_count']}건({share}%)."
        )
    return lines
