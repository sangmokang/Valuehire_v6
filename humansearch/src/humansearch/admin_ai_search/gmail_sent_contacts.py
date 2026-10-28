"""Read-only Gmail Sent projection for evidence-backed candidate contact history."""

from __future__ import annotations

import hashlib
import re
from collections.abc import Mapping, Sequence
from typing import Literal, TypedDict, cast

from .evidence import (
    AiSearchPayload,
    ContactActor,
    ContactHistoryPayload,
    EvidenceContract,
)
from .gmail_candidates import canonical_candidate_url
from .gmail_source import (
    _header,
    _message_body,
    _received_at,
    _required_mapping,
    _required_string,
    _validate_snapshot,
    build_ai_search_payload_from_gmail_snapshot,
)

GMAIL_SENT_SNAPSHOT_VERSION = "admin-ai-search-gmail-sent-snapshot/v1"
GMAIL_EVIDENCE_ENVELOPE_VERSION = "admin-ai-search-gmail-evidence/v1"
_ENVELOPE_FIELDS = {"version", "search", "sent"}
_PROPOSAL_SUBJECT = re.compile(r"(?:이직|포지션|채용)\s*제안", re.IGNORECASE)
_REPLY_OR_FORWARD = re.compile(r"^\s*(?:re|fwd)\s*:", re.IGNORECASE)
_TEST_MESSAGE = re.compile(r"(?:\bQA-\d+\b|검증\s*메일|테스트\s*메일)", re.IGNORECASE)
_CANDIDATE_LINK_LABEL = re.compile(r"(?:후보.*프로필|프로필.*후보|candidate\s+profile)", re.IGNORECASE)
_LABELED_PROFILE_URL = re.compile(
    r"(?:후보\s*프로필|candidate\s+profile)\s*[:：]?\s*(https?://[^\s<>\"']+)",
    re.IGNORECASE,
)
_CLIENT_PATTERN = re.compile(
    r"from\s+(\d+)\s+named unknown by gmailapi\.google\.com", re.IGNORECASE
)


class SentContactEventPayload(TypedDict):
    message_id: str
    thread_id: str
    subject: str
    actor: ContactActor
    actor_reason: str
    contacted_at: str
    source: Literal["GMAIL"]
    evidence_reference: str
    canonical_keys: list[str]
    link_status: Literal["PASS", "NOT_RUN"]
    link_reason: str | None


def build_ai_search_payload_from_gmail_evidence(
    envelope: Mapping[str, object], contract: EvidenceContract
) -> AiSearchPayload:
    """Combine exhaustive AI Search and Sent snapshots without persisting either."""

    if set(envelope) != _ENVELOPE_FIELDS:
        raise ValueError("Gmail evidence envelope fields do not match the v1 contract")
    if envelope["version"] != GMAIL_EVIDENCE_ENVELOPE_VERSION:
        raise ValueError("unsupported Gmail evidence envelope version")
    search = envelope["search"]
    sent = envelope["sent"]
    if not isinstance(search, Mapping) or not isinstance(sent, Mapping):
        raise TypeError("Gmail evidence snapshots must be objects")
    payload = build_ai_search_payload_from_gmail_snapshot(
        cast(Mapping[str, object], search), contract
    )
    _apply_sent_snapshot(payload, cast(Mapping[str, object], sent), contract)
    return payload


def _apply_sent_snapshot(
    payload: AiSearchPayload,
    snapshot: Mapping[str, object],
    contract: EvidenceContract,
) -> None:
    messages, query, page_count, pagination_exhausted = _validate_snapshot(
        snapshot, GMAIL_SENT_SNAPSHOT_VERSION
    )
    known_keys = {item["canonical_key"] for item in payload["candidate_ledger"]}
    events: list[SentContactEventPayload] = []
    excluded = 0
    for message in messages:
        event = _sent_contact_event(message, contract, known_keys)
        if event is None:
            excluded += 1
        else:
            events.append(event)
    linked = sum(event["link_status"] == "PASS" for event in events)
    status = "PASS" if pagination_exhausted else "NOT_RUN"
    payload["contact_collection"] = {
        "query": query,
        "page_count": page_count,
        "message_count": len(messages),
        "pagination_exhausted": pagination_exhausted,
        "status": status,
        "reason": None if pagination_exhausted else "gmail_sent_pagination_incomplete",
        "direct_contact_count": len(events),
        "ai_sent_count": sum(event["actor"] == "AI" for event in events),
        "owner_sent_count": sum(event["actor"] == "OWNER" for event in events),
        "unknown_sent_count": sum(event["actor"] == "UNKNOWN" for event in events),
        "linked_contact_count": linked,
        "unlinked_contact_count": len(events) - linked,
        "excluded_message_count": excluded,
        "events": events,
    }
    _attach_sent_contacts(payload, events)
    if not pagination_exhausted:
        payload["status"] = "NOT_RUN"
        payload["reason"] = "gmail_sent_pagination_incomplete"


def _sent_contact_event(
    message: Mapping[str, object],
    contract: EvidenceContract,
    known_keys: set[str],
) -> SentContactEventPayload | None:
    message_id = _required_string(message, "id")
    thread_id = _required_string(message, "thread_id")
    received_at = _received_at(message.get("internal_date"))
    payload = _required_mapping(message, "payload")
    subject = _header(payload, "subject")
    body_text, links = _message_body(payload)
    if (
        not _PROPOSAL_SUBJECT.search(subject)
        or _REPLY_OR_FORWARD.search(subject)
        or _optional_header(payload, "in-reply-to")
        or _TEST_MESSAGE.search(f"{subject}\n{body_text}")
        or not _has_external_recipient(_header(payload, "to"))
    ):
        return None
    actor, actor_reason = _contact_actor(payload, contract)
    canonical_urls = _explicit_candidate_profile_urls(body_text, links)
    canonical_keys = sorted(
        hashlib.sha256(url.encode("utf-8")).hexdigest() for url in canonical_urls
    )
    linked_keys = [key for key in canonical_keys if key in known_keys]
    return {
        "message_id": message_id,
        "thread_id": thread_id,
        "subject": subject,
        "actor": actor,
        "actor_reason": actor_reason,
        "contacted_at": received_at.isoformat(),
        "source": "GMAIL",
        "evidence_reference": f"gmail:{message_id}",
        "canonical_keys": linked_keys,
        "link_status": "PASS" if linked_keys else "NOT_RUN",
        "link_reason": None if linked_keys else "candidate_profile_not_in_sent_message",
    }


def _has_external_recipient(value: str) -> bool:
    domains = re.findall(r"@([^>,\s]+)", value.lower())
    return any(domain != "valueconnect.kr" for domain in domains)


def _explicit_candidate_profile_urls(
    body_text: str, links: Sequence[tuple[str, str]]
) -> set[str]:
    raw_urls = [
        url for url, label in links if _CANDIDATE_LINK_LABEL.search(label)
    ]
    raw_urls.extend(_LABELED_PROFILE_URL.findall(body_text))
    return {
        normalized
        for raw_url in raw_urls
        if (normalized := canonical_candidate_url(raw_url)) is not None
    }


def _optional_header(payload: Mapping[str, object], wanted: str) -> str:
    headers = payload.get("headers")
    if not isinstance(headers, list):
        raise TypeError("Gmail payload headers must be a list")
    for header in headers:
        if not isinstance(header, Mapping):
            continue
        if str(header.get("name", "")).lower() == wanted:
            return str(header.get("value", "")).strip()
    return ""


def _contact_actor(
    payload: Mapping[str, object], contract: EvidenceContract
) -> tuple[ContactActor, str]:
    headers = payload.get("headers")
    if not isinstance(headers, list):
        return "UNKNOWN", "gmail_api_client_missing"
    client_ids: set[str] = set()
    for header in headers:
        if not isinstance(header, Mapping):
            continue
        if str(header.get("name", "")).lower() != "received":
            continue
        match = _CLIENT_PATTERN.search(str(header.get("value", "")))
        if match:
            client_ids.add(match.group(1))
    if any(value in contract.gmail_contact_actor_clients["AI"] for value in client_ids):
        return "AI", "gmail_api_client_contract:AI"
    if any(value in contract.gmail_contact_actor_clients["OWNER"] for value in client_ids):
        return "OWNER", "gmail_api_client_contract:OWNER"
    return "UNKNOWN", "gmail_api_client_unmapped"


def _attach_sent_contacts(
    payload: AiSearchPayload, events: Sequence[SentContactEventPayload]
) -> None:
    by_key = {item["canonical_key"]: item for item in payload["candidate_ledger"]}
    for event in events:
        for canonical_key in event["canonical_keys"]:
            row = by_key.get(canonical_key)
            if row is None:
                continue
            history: ContactHistoryPayload = {
                "actor": event["actor"],
                "actor_reason": event["actor_reason"],
                "source": "GMAIL",
                "status": "PASS",
                "contacted_at": event["contacted_at"],
                "checked_at": event["contacted_at"],
                "evidence_reference": event["evidence_reference"],
            }
            if history not in row["contact_history"]:
                row["contact_history"].append(history)
                row["contact_history"].sort(
                    key=lambda item: item["contacted_at"] or "", reverse=True
                )
            row["contact_status"] = "PASS"
    for batch in payload["batches"]:
        for candidate in batch["candidates"]:
            row = by_key[candidate["canonical_key"]]
            candidate["contact_history"] = list(row["contact_history"])
            if not row["contact_history"]:
                continue
            latest = row["contact_history"][0]
            candidate["contact_status"] = row["contact_status"]
            candidate["contact_actor"] = latest["actor"]
            candidate["contact_actor_reason"] = latest["actor_reason"]
            candidate["contact_source"] = latest["source"]
            candidate["contacted_at"] = latest["contacted_at"]
            candidate["contact_checked_at"] = latest["checked_at"]
            candidate["contact_reference"] = latest["evidence_reference"]
        confirmed = sum(
            candidate["contact_status"] == "PASS" for candidate in batch["candidates"]
        )
        if confirmed:
            batch["actual_fu"] = confirmed

