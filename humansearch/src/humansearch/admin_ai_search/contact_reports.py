"""Read-only source reports; aggregates are not candidate contact events."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Any

from .gmail_candidates import canonical_candidate_url
from .normalize import key, review
from .registry import Registry

CHANNELS = {"SARAMIN", "JOBKOREA", "LINKEDIN", "GMAIL"}
ACTORS = {"AI", "OWNER", "UNKNOWN"}
STATUSES = {"CONTACTED", "REPLIED", "CONFIRMED_NOT_CONTACTED", "NOT_RUN", "REVIEW_REQUIRED", "FAILED"}


def _aware(value: object) -> bool:
    if not isinstance(value, str):
        return False
    try:
        return datetime.fromisoformat(value).tzinfo is not None
    except ValueError:
        return False


def ingest_report(registry: Registry, message_id: str, report: dict[str, Any]) -> None:
    registry.put("contact_evidence", {"id": key(message_id, "report"),
        "source_message_id": message_id, "report": report,
        "reported_totals": report.get("totals"), "source_reference": f"gmail:{message_id}"})
    events = report.get("events")
    if report.get("version") != "ai-search-contact-report/v1" or not isinstance(events, list):
        review(registry, message_id, "contact_report_binding_pending")
        return
    for index, event in enumerate(events):
        if not isinstance(event, dict):
            review(registry, message_id, "contact_report_invalid_event", reference=str(index))
            continue
        _ingest_event(registry, message_id, event, index)


def _ingest_event(registry: Registry, message_id: str, event: dict[str, Any], index: int) -> None:
    identity = key(message_id, str(event.get("event_id", index)))
    url = canonical_candidate_url(str(event.get("candidate_profile_url", "")))
    candidate_id = hashlib.sha256(url.encode()).hexdigest() if url else None
    position_id = key(str(event.get("company", "")), str(event.get("position", "")))
    linked = registry.db.execute(
        "SELECT 1 FROM candidate_position_evaluations WHERE "
        "json_extract(document,'$.candidate_id')=? AND json_extract(document,'$.position_id')=? LIMIT 1",
        (candidate_id, position_id),
    ).fetchone() is not None
    channel, actor, status = event.get("channel"), event.get("actor"), event.get("status")
    if channel not in CHANNELS or actor not in ACTORS or status not in STATUSES:
        review(registry, message_id, "contact_report_invalid_event", reference=identity)
        return
    reason = None
    if not linked:
        status, reason = "REVIEW_REQUIRED", "unlinked_sent_contact"
    elif status in {"CONTACTED", "REPLIED"} and (
        not _aware(event.get("sent_at")) or not event.get("evidence_reference")
        or (status == "REPLIED" and not _aware(event.get("replied_at")))
    ):
        status, reason = "REVIEW_REQUIRED", "contact_send_evidence_incomplete"
    elif status == "CONFIRMED_NOT_CONTACTED":
        scope = event.get("scope")
        if not (event.get("pagination_exhausted") is True and _aware(event.get("checked_at"))
                and isinstance(scope, dict) and scope.get("complete_for_candidate_position") is True
                and scope.get("candidate_profile_url") == event.get("candidate_profile_url")
                and scope.get("company") == event.get("company")
                and scope.get("position") == event.get("position")
                and scope.get("channel") == channel and event.get("evidence_reference")):
            status, reason = "NOT_RUN", "contact_scope_incomplete"
    document = {**event, "id": identity, "candidate_id": candidate_id if linked else None,
                "position_id": position_id if linked else None, "status": status,
                "event_type": event.get("event_type", "CONTACT_CHECK"),
                "source_message_id": message_id, "link_status": "PASS" if linked else "REVIEW_REQUIRED",
                "link_reason": reason, "evidence_reference": event.get("evidence_reference"),
                "source_reference": f"gmail:{message_id}", "reason": reason,
                "weekly_and_cumulative_basis": "event_timestamp"}
    registry.put("contact_events", document)
    if reason:
        review(registry, message_id, reason, reference=identity, contact_event_id=identity)
    else:
        for row in registry.db.execute("SELECT id,document FROM review_queue").fetchall():
            previous = json.loads(row[1])
            if previous.get("source_message_id") == message_id and previous.get("reference") == identity:
                registry.put("review_queue", {**previous, "status": "RESOLVED"})
