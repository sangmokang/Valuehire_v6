"""Read-only source reports; aggregates are not candidate contact events."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import UTC, datetime
from typing import Any

from .evidence import EvidenceContract
from .gmail_candidates import canonical_candidate_url
from .gmail_sent_contacts import _PROPOSAL_SUBJECT, _sent_contact_event
from .normalize import SECTION, adapt_mime, headers, key, review
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
    identity = key(str(event.get("channel")), str(event.get("evidence_reference", message_id)),
                   str(event.get("candidate_profile_url")), str(event.get("company")),
                   str(event.get("position")), str(event.get("sent_at", event.get("checked_at", index))))
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
        elif event.get("sent_at") or event.get("replied_at"):
            status, reason = "REVIEW_REQUIRED", "contact_negative_contradicts_send_evidence"
    elif status == "REVIEW_REQUIRED":
        reason = str(event.get("reason", "contact_intent_requires_review"))
    document = {**event, "id": identity, "candidate_id": candidate_id if linked else None,
                "position_id": position_id if linked else None, "status": status,
                "event_type": event.get("event_type", "CONTACT_CHECK"),
                "source_message_id": message_id, "link_status": "PASS" if linked else "REVIEW_REQUIRED",
                "link_reason": reason, "evidence_reference": event.get("evidence_reference"),
                "source_reference": f"gmail:{message_id}", "reason": reason,
                "weekly_and_cumulative_basis": "event_timestamp"}
    for field in ("sent_at", "replied_at", "checked_at"):
        raw_time = event.get(field)
        document[field] = (datetime.fromisoformat(str(raw_time)).astimezone(UTC).isoformat()
                           if _aware(raw_time) else None)
    previous_event = registry.db.execute("SELECT document FROM contact_events WHERE id=?", (identity,)).fetchone()
    source_ids = json.loads(previous_event[0]).get("source_message_ids", []) if previous_event else []
    document["source_message_ids"] = list(dict.fromkeys([*source_ids, message_id]))
    registry.put("contact_events", document)
    if reason:
        review(registry, message_id, reason, reference=identity, contact_event_id=identity)
    else:
        for row in registry.db.execute("SELECT id,document FROM review_queue WHERE "
            "json_extract(document,'$.source_message_id')=?", (message_id,)).fetchall():
            previous = json.loads(row[1])
            if previous.get("source_message_id") == message_id and previous.get("reference") == identity:
                registry.put("review_queue", {**previous, "status": "RESOLVED"})


def ingest_gmail_sent(registry: Registry, message: dict[str, Any], contract: EvidenceContract, text: str) -> None:
    explicit_proposal = _PROPOSAL_SUBJECT.search(headers(message).get("subject", "")) is not None
    if not explicit_proposal and re.match(r"^\s*\[포지션\]", headers(message).get("subject", "")) is None:
        return
    known = registry.candidate_keys()
    adapted = {"id": message["id"], "thread_id": message.get("threadId"),
               "internal_date": message.get("internalDate"), "payload": adapt_mime(message["payload"])}
    event = _sent_contact_event(adapted, contract, known, include_position_mail=True, include_cc_bcc=True)
    if event is None:
        return
    registry.put("contact_evidence", {"id": key(message["id"], "sent"), **event,
                                     "source_message_id": message["id"], "source_body": text,
                                     "intent_status": "EXPLICIT_PROPOSAL" if explicit_proposal else "POSITION_MAIL_REVIEW_REQUIRED"})
    contexts = list(SECTION.finditer(text))
    company, position = (contexts[0][1], contexts[0][2]) if len(contexts) == 1 else ("", "")
    profiles = event["canonical_keys"]
    if not profiles:
        review(registry, message["id"], "unlinked_sent_contact", reference=message["id"])
        registry.put("contact_events", {"id": key(message["id"], "unlinked"),
            "candidate_id": None, "position_id": None, "channel": "GMAIL", "actor": event["actor"],
            "status": "REVIEW_REQUIRED", "source_message_id": message["id"], "sent_at": event["contacted_at"],
            "event_type": "PROPOSAL_SENT" if explicit_proposal else "POSITION_MAIL_SENT", "evidence_reference": event["evidence_reference"],
            "link_reason": event["link_reason"], "checked_at": None})
    for identity in profiles:
        row = registry.db.execute("SELECT document FROM candidates WHERE id=?", (identity,)).fetchone()
        profile = json.loads(row[0])["canonical_url"]
        _ingest_event(registry, message["id"], {"candidate_profile_url": profile,
            "company": company, "position": position, "channel": "GMAIL", "actor": event["actor"],
            "actor_reason": event["actor_reason"], "status": "CONTACTED" if explicit_proposal else "REVIEW_REQUIRED", "sent_at": event["contacted_at"],
            "reason": "contact_intent_requires_review" if not explicit_proposal else None,
            "evidence_reference": event["evidence_reference"], "event_type": "PROPOSAL_SENT" if explicit_proposal else "POSITION_MAIL_SENT"}, 0)
