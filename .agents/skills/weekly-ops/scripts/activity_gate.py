"""Career-page and consultant-outreach validation for the weekly gate."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
import hashlib
import json
from typing import Any, Callable


CAREER_STATUSES = {"PASS", "PARTIAL", "FAIL", "NOT_RUN", "STALE"}
OUTREACH_STATUSES = {"PENDING", "SENT", "FAILED"}
PORTAL_CHANNELS = {"saramin", "jobkorea", "linkedin_rps"}
OUTREACH_CHANNELS = PORTAL_CHANNELS
EXPECTED_CAREER_COMPANIES = {
    "SpoonLabs",
    "Codeit",
    "GC Company",
    "Wrtn Technologies",
    "FastView",
}
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
OUTREACH_EVENT_FIELDS = {
    "event_id",
    "consultant_id",
    "consultant_display",
    "position_id",
    "channel",
    "status",
    "sent_at",
    "candidate_key_hmac",
    "provider_actor_ref",
    "source_snapshot_id",
}


def validate_consultant_roster(
    roster: Any,
    events: Any,
    errors: list[str],
    require_roster: bool = False,
) -> dict[str, dict[str, Any]]:
    has_events = isinstance(events, list) and bool(events)
    if roster is None and not (require_roster or has_events):
        return {}
    if not isinstance(roster, list) or not roster:
        errors.append("CONSULTANT_ROSTER_INVALID")
        return {}
    validated: dict[str, dict[str, Any]] = {}
    claimed_accounts: set[tuple[str, str]] = set()
    for item in roster:
        if not isinstance(item, dict):
            errors.append("CONSULTANT_ROSTER_INVALID")
            continue
        consultant_id = item.get("consultant_id")
        display = item.get("consultant_display")
        accounts = item.get("provider_accounts")
        if (
            not isinstance(consultant_id, str)
            or not consultant_id
            or consultant_id in validated
            or not isinstance(display, str)
            or not display
            or not isinstance(accounts, dict)
            or set(accounts) != PORTAL_CHANNELS
        ):
            errors.append("CONSULTANT_ROSTER_INVALID")
            continue
        normalized_accounts: dict[str, set[str]] = {}
        valid = True
        for channel in sorted(PORTAL_CHANNELS):
            refs = accounts[channel]
            if (
                not isinstance(refs, list)
                or any(not isinstance(ref, str) or not ref for ref in refs)
                or len(refs) != len(set(refs))
                or any((channel, ref) in claimed_accounts for ref in refs)
            ):
                valid = False
                break
            normalized_accounts[channel] = set(refs)
        if not valid:
            errors.append("CONSULTANT_ROSTER_INVALID")
            continue
        for channel, refs in normalized_accounts.items():
            claimed_accounts.update((channel, ref) for ref in refs)
        validated[consultant_id] = {
            "consultant_display": display,
            "provider_accounts": normalized_accounts,
        }
    return validated


def validate_career_summaries(
    summaries: Any,
    source_snapshot_ids: set[str],
    parse_datetime: Callable[[str], datetime],
    errors: list[str],
    require_complete: bool = False,
) -> tuple[list[dict[str, Any]], list[str]]:
    if summaries is None:
        if require_complete:
            errors.append("CAREER_REQUIRED_COMPANY_MISSING")
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
    if require_complete and EXPECTED_CAREER_COMPANIES - seen:
        errors.append("CAREER_REQUIRED_COMPANY_MISSING")
    return validated, sorted(blockers)


def validate_outreach_events(
    events: Any,
    diagnostics: dict[str, dict[str, Any]],
    consultant_roster: dict[str, dict[str, Any]],
    position_lookup: dict[str, dict[str, Any]],
    run: dict[str, datetime] | None,
    source_snapshot_ids: set[str],
    snapshot_evidence_refs: dict[str, set[str]],
    parse_datetime: Callable[[str], datetime],
    errors: list[str],
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    if events is None:
        return [], []
    if not isinstance(events, list):
        errors.append("OUTREACH_EVENTS_INVALID")
        return [], []
    seen: set[str] = set()
    seen_receipts: set[tuple[str, str]] = set()
    identity_error = False
    accepted: list[dict[str, Any]] = []
    excluded: list[dict[str, str]] = []
    for event in events:
        if not isinstance(event, dict) or not OUTREACH_EVENT_FIELDS.issubset(event):
            errors.append("OUTREACH_EVENT_INVALID")
            continue
        event_id = event["event_id"]
        if not isinstance(event_id, str) or not event_id or event_id in seen:
            errors.append("OUTREACH_EVENT_INVALID")
            continue
        seen.add(event_id)
        checked, event_identity_error = validate_outreach_event(
            event, diagnostics, consultant_roster, position_lookup, source_snapshot_ids,
            snapshot_evidence_refs, parse_datetime, errors,
        )
        identity_error = identity_error or event_identity_error
        if checked is None:
            if event.get("status") in {"PENDING", "FAILED"}:
                excluded.append(excluded_row("STATUS_NOT_SENT", event))
            continue
        receipt_key = (
            checked["channel"],
            checked["provider_receipt_ref"],
        )
        if receipt_key in seen_receipts:
            errors.append("OUTREACH_RECEIPT_DUPLICATE")
            identity_error = True
            excluded.append(excluded_row("DUPLICATE_PROVIDER_RECEIPT", checked))
            continue
        seen_receipts.add(receipt_key)
        if run and not (run["window_start"] <= checked["_sent_at"] < run["window_end_exclusive"]):
            excluded.append(excluded_row("OUTSIDE_WEEKLY_WINDOW", checked))
            continue
        accepted.append(checked)
    focus = [] if identity_error else aggregate_consultant_focus(accepted, position_lookup)
    return focus, sorted(excluded, key=lambda item: (item["reason"], item["evidence_ref"]))


def validate_outreach_event(
    event: dict[str, Any],
    diagnostics: dict[str, dict[str, Any]],
    consultant_roster: dict[str, dict[str, Any]],
    position_lookup: dict[str, dict[str, Any]],
    source_snapshot_ids: set[str],
    snapshot_evidence_refs: dict[str, set[str]],
    parse_datetime: Callable[[str], datetime],
    errors: list[str],
) -> tuple[dict[str, Any] | None, bool]:
    if (
        event["channel"] not in OUTREACH_CHANNELS
        or event["status"] not in OUTREACH_STATUSES
        or event["position_id"] not in position_lookup
        or not isinstance(event["consultant_id"], str)
        or not isinstance(event["consultant_display"], str)
        or not isinstance(event["candidate_key_hmac"], str)
        or not event["candidate_key_hmac"].startswith("hmac:")
        or not isinstance(event["provider_actor_ref"], str)
        or not event["provider_actor_ref"]
        or event["source_snapshot_id"] not in source_snapshot_ids
    ):
        errors.append("OUTREACH_EVENT_INVALID")
        return None, False
    if event["status"] != "SENT":
        return None, False
    try:
        sent_at = parse_datetime(event["sent_at"])
    except (TypeError, ValueError):
        errors.append("OUTREACH_EVENT_INVALID")
        return None, False
    if event["status"] == "SENT" and (
        not isinstance(event.get("provider_receipt_ref"), str)
        or not event["provider_receipt_ref"]
    ):
        errors.append("OUTREACH_SENT_WITHOUT_READBACK")
        return None, False
    if not consultant_matches_roster(event, consultant_roster):
        errors.append("OUTREACH_CONSULTANT_UNMAPPED")
        return None, True
    if event["status"] == "SENT" and not diagnostic_allows_event(
        diagnostics.get(event["channel"]), event
    ):
        errors.append("OUTREACH_SURFACE_UNVERIFIED")
        return None, False
    if event["status"] == "SENT" and event["channel"] == "linkedin_rps":
        if any(not isinstance(event.get(field), str) or not event[field] for field in LINKEDIN_EVENT_FIELDS):
            errors.append("LINKEDIN_OUTREACH_DIMENSIONS_MISSING")
            return None, False
        if event["provider_seat_ref"] != event["provider_actor_ref"]:
            errors.append("OUTREACH_CONSULTANT_UNMAPPED")
            return None, True
    if event["status"] == "SENT" and event["provider_receipt_ref"] not in snapshot_evidence_refs.get(
        event["source_snapshot_id"], set()
    ):
        errors.append("OUTREACH_RECEIPT_UNRESOLVED")
        return None, False
    return {**event, "_sent_at": sent_at}, False


def consultant_matches_roster(
    event: dict[str, Any], consultant_roster: dict[str, dict[str, Any]]
) -> bool:
    roster_entry = consultant_roster.get(event["consultant_id"])
    return bool(
        roster_entry
        and roster_entry["consultant_display"] == event["consultant_display"]
        and event["provider_actor_ref"]
        in roster_entry["provider_accounts"].get(event["channel"], set())
    )


def excluded_row(reason: str, event: dict[str, Any]) -> dict[str, str]:
    receipt = event.get("provider_receipt_ref")
    if isinstance(receipt, str) and receipt.startswith("sha256:"):
        evidence_ref = receipt
    else:
        payload = json.dumps(event, ensure_ascii=False, sort_keys=True, default=str)
        evidence_ref = f"sha256:{hashlib.sha256(payload.encode('utf-8')).hexdigest()}"
    return {"reason": reason, "evidence_ref": evidence_ref}


def validate_outreach_channel_diagnostics(
    diagnostics: Any,
    events: Any,
    consultant_roster: dict[str, dict[str, Any]],
    source_snapshot_ids: set[str],
    errors: list[str],
    require_all_channels: bool = False,
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
    if not portal_events and not require_all_channels:
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
        "covered_provider_actor_refs",
        "source_snapshot_id",
    }
    for item in diagnostics:
        if not isinstance(item, dict) or not required.issubset(item):
            errors.append("OUTREACH_DIAGNOSTIC_INVALID")
            continue
        channel = item["channel"]
        covered_refs = item.get("covered_provider_actor_refs")
        allowed_refs = {
            ref
            for roster_entry in consultant_roster.values()
            for ref in roster_entry["provider_accounts"].get(channel, set())
        }
        if (
            channel not in PORTAL_CHANNELS
            or channel in validated
            or item["access_state"] not in OUTREACH_ACCESS_STATES
            or not isinstance(item["surface_kind"], str)
            or not item["surface_kind"]
            or not isinstance(item["surface_ref"], str)
            or not item["surface_ref"]
            or not isinstance(item["stable_receipt_available"], bool)
            or not isinstance(covered_refs, list)
            or any(not isinstance(ref, str) or not ref for ref in covered_refs)
            or len(covered_refs) != len(set(covered_refs))
            or not set(covered_refs).issubset(allowed_refs)
            or (
                item["access_state"] != "AUTHENTICATED"
                and bool(covered_refs)
            )
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
        and event["provider_actor_ref"] in diagnostic["covered_provider_actor_refs"]
    )


def build_channel_coverage(
    diagnostics: dict[str, dict[str, Any]],
    consultant_roster: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[str]]:
    coverage: list[dict[str, Any]] = []
    blockers: list[str] = []
    for channel in sorted(PORTAL_CHANNELS):
        diagnostic = diagnostics.get(channel, {})
        actor_owners = {
            actor: consultant_id
            for consultant_id, roster_entry in consultant_roster.items()
            for actor in roster_entry["provider_accounts"].get(channel, set())
        }
        usable = (
            diagnostic.get("access_state") == "AUTHENTICATED"
            and diagnostic.get("stable_receipt_available") is True
            and diagnostic.get("surface_kind") in ALLOWED_OUTREACH_SURFACES[channel]
        )
        covered_actors = set(diagnostic.get("covered_provider_actor_refs", [])) if usable else set()
        missing_actors = set(actor_owners) - covered_actors
        covered_consultants = sorted({actor_owners[actor] for actor in covered_actors})
        not_run_consultants = sorted({actor_owners[actor] for actor in missing_actors})
        channel_blockers = [
            f"outreach:{channel}:{consultant_id}:NOT_RUN"
            for consultant_id in not_run_consultants
        ]
        blockers.extend(channel_blockers)
        coverage.append(
            {
                "channel": channel,
                "access_state": diagnostic.get("access_state", "MISSING_PROFILE"),
                "surface_kind": diagnostic.get("surface_kind", "unavailable"),
                "covered_consultants": covered_consultants,
                "not_run_consultants": not_run_consultants,
                "covered_account_count": len(covered_actors),
                "expected_account_count": len(actor_owners),
                "not_run_blockers": channel_blockers,
            }
        )
    return coverage, sorted(set(blockers))


def apply_coverage_comparability(
    focus: list[dict[str, Any]], coverage_blockers: list[str]
) -> list[dict[str, Any]]:
    status = "NOT_COMPARABLE" if coverage_blockers else "COMPARABLE"
    annotated = [{**item, "comparison_status": status} for item in focus]
    if coverage_blockers:
        annotated.sort(key=lambda item: item["consultant_display"])
    return annotated


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
                    "channel_mix": dict(
                        sorted(
                            {
                                channel: sum(
                                    event["channel"] == channel for event in position_events
                                )
                                for channel in {event["channel"] for event in position_events}
                            }.items()
                        )
                    ),
                    "evidence_refs": sorted(
                        {event["provider_receipt_ref"] for event in position_events}
                    ),
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
                "channel_mix": dict(
                    sorted(
                        {
                            channel: sum(event["channel"] == channel for event in consultant_events)
                            for channel in {event["channel"] for event in consultant_events}
                        }.items()
                    )
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
    if any(item.get("comparison_status") == "NOT_COMPARABLE" for item in focus):
        lines.append("- 비교 상태: 계정 coverage 불일치로 컨설턴트 간 순위 산정 안 함.")
    for consultant in focus:
        lead = consultant["positions"][0]
        share = round(lead["focus_share"] * 100)
        scope = "확인된 범위 내 " if consultant.get("comparison_status") == "NOT_COMPARABLE" else ""
        lines.append(
            f"- {consultant['consultant_display']}: 검증 발송 {consultant['verified_sent_count']}건, "
            f"고유 후보 {consultant['unique_candidate_count']}명, 활동 {consultant['active_days']}일. "
            f"{scope}최대 집중은 {lead['company']} — {lead['title']} "
            f"{lead['verified_sent_count']}건({share}%)."
        )
    return lines
