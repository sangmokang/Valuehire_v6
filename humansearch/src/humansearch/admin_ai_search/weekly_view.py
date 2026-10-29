"""Weekly spreadsheet projection for the read-only AI Search evidence payload."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import date, datetime, timedelta
from typing import Literal, TypedDict
from zoneinfo import ZoneInfo

from humansearch.admin_weekly_dashboard.weekly_window import weekly_window

from .evidence import (
    AiSearchPayload,
    BatchPayload,
    CandidateLedgerPayload,
    ContactActor,
    EvidenceStatus,
    SentContactEventPayload,
)
from .scoring import ScoreComponents

KST = ZoneInfo("Asia/Seoul")
WEEK_RULE = "SUNDAY_TO_SATURDAY_LABELED_BY_NEXT_MEETING_ISO_WEEK"


class WeeklyCandidateContactPayload(TypedDict):
    status: EvidenceStatus
    total: int
    ai_sent_count: int
    owner_sent_count: int
    unknown_sent_count: int
    latest_contacted_at: str | None
    sources: list[str]
    attribution: Literal["CANDIDATE", "NOT_RUN"]
    reason: str | None


class WeeklyCandidateRowPayload(TypedDict):
    week_id: str
    batch_id: str
    executed_at: str
    company: str
    position: str
    actor: str
    actor_label: str
    source_channel: str
    canonical_key: str
    candidate_name: str
    profile_url: str
    education: str | None
    experience: str | None
    key_experience: str | None
    score: int | None
    score_status: EvidenceStatus
    score_reason: str | None
    score_components: ScoreComponents | None
    score_evidence: list[str]
    weekly_contact: WeeklyCandidateContactPayload


class WeeklyLinkedCandidatePayload(TypedDict):
    canonical_key: str
    candidate_name: str
    profile_url: str | None


class WeeklyContactRowPayload(TypedDict):
    week_id: str
    contacted_at: str
    actor: ContactActor
    actor_reason: str
    source: str
    subject: str
    message_id: str
    thread_id: str
    evidence_reference: str
    link_status: Literal["PASS", "NOT_RUN"]
    link_reason: str | None
    linked_candidates: list[WeeklyLinkedCandidatePayload]


class WeeklyContactSummaryPayload(TypedDict):
    total: int
    ai_sent: int
    owner_sent: int
    unknown_sent: int
    linked: int
    unlinked: int
    owner_linked_candidates: int


class WeeklyAiSearchWeekPayload(TypedDict):
    week_id: str
    event_start_kst: str
    event_end_exclusive_kst: str
    period_label: str
    status: EvidenceStatus
    reason: str | None
    batch_count: int
    unique_candidate_count: int
    candidate_row_count: int
    candidate_rows: list[WeeklyCandidateRowPayload]
    contact_summary: WeeklyContactSummaryPayload
    contact_rows: list[WeeklyContactRowPayload]


class WeeklyAiSearchWeekIndexPayload(TypedDict):
    week_id: str
    event_start_kst: str
    event_end_exclusive_kst: str
    period_label: str
    status: EvidenceStatus
    reason: str | None
    batch_count: int
    unique_candidate_count: int
    candidate_row_count: int
    contact_summary: WeeklyContactSummaryPayload


class WeeklyAiSearchViewPayload(TypedDict):
    mode: str
    status: EvidenceStatus
    reason: str | None
    timezone: str
    week_rule: str
    weeks: list[WeeklyAiSearchWeekPayload]
    external_effects: dict[str, str]


class WeeklyAiSearchIndexPayload(TypedDict):
    mode: str
    status: EvidenceStatus
    reason: str | None
    timezone: str
    week_rule: str
    weeks: list[WeeklyAiSearchWeekIndexPayload]
    external_effects: dict[str, str]


def build_weekly_ai_search_view(payload: AiSearchPayload) -> WeeklyAiSearchViewPayload:
    """Project validated batches and sent events into complete operational weeks."""

    status, reason = _collection_status(payload)
    batches_by_week: dict[str, list[BatchPayload]] = {}
    windows: dict[str, tuple[str, str, str]] = {}
    for batch in payload["batches"]:
        week_id, start, end, label = _week_identity(batch["executed_at"])
        batches_by_week.setdefault(week_id, []).append(batch)
        windows[week_id] = (start, end, label)

    events_by_week: dict[str, list[SentContactEventPayload]] = {}
    contact_collection = payload.get("contact_collection")
    if isinstance(contact_collection, Mapping):
        raw_events = contact_collection.get("events")
        if isinstance(raw_events, list):
            for raw_event in raw_events:
                if not isinstance(raw_event, Mapping):
                    raise TypeError("AI Search contact event must be an object")
                event = raw_event
                week_id, start, end, label = _week_identity(event["contacted_at"])
                events_by_week.setdefault(week_id, []).append(event)
                windows[week_id] = (start, end, label)

    candidate_index = {
        item["canonical_key"]: item for item in payload["candidate_ledger"]
    }
    weeks: list[WeeklyAiSearchWeekPayload] = []
    for week_id in _continuous_week_ids(windows):
        start, end, label = windows[week_id]
        batches = sorted(
            batches_by_week.get(week_id, []),
            key=lambda item: (item["executed_at"], item["batch_id"]),
            reverse=True,
        )
        events = sorted(
            events_by_week.get(week_id, []),
            key=lambda item: (item["contacted_at"], item["message_id"]),
            reverse=True,
        )
        candidate_rows = _candidate_rows(week_id, batches, events)
        contact_rows = _contact_rows(week_id, events, candidate_index)
        unique_candidates = {row["canonical_key"] for row in candidate_rows}
        weeks.append(
            {
                "week_id": week_id,
                "event_start_kst": start,
                "event_end_exclusive_kst": end,
                "period_label": label,
                "status": status,
                "reason": reason,
                "batch_count": len(batches),
                "unique_candidate_count": len(unique_candidates),
                "candidate_row_count": len(candidate_rows),
                "candidate_rows": candidate_rows,
                "contact_summary": _contact_summary(events),
                "contact_rows": contact_rows,
            }
        )
    return {
        "mode": payload["mode"],
        "status": status,
        "reason": reason,
        "timezone": "Asia/Seoul",
        "week_rule": WEEK_RULE,
        "weeks": weeks,
        "external_effects": dict(payload["external_effects"]),
    }


def build_weekly_ai_search_index(
    view: WeeklyAiSearchViewPayload,
) -> WeeklyAiSearchIndexPayload:
    """Remove row payloads from the initial week-selector response."""

    return {
        "mode": view["mode"],
        "status": view["status"],
        "reason": view["reason"],
        "timezone": view["timezone"],
        "week_rule": view["week_rule"],
        "weeks": [
            {
                "week_id": week["week_id"],
                "event_start_kst": week["event_start_kst"],
                "event_end_exclusive_kst": week["event_end_exclusive_kst"],
                "period_label": week["period_label"],
                "status": week["status"],
                "reason": week["reason"],
                "batch_count": week["batch_count"],
                "unique_candidate_count": week["unique_candidate_count"],
                "candidate_row_count": week["candidate_row_count"],
                "contact_summary": week["contact_summary"],
            }
            for week in view["weeks"]
        ],
        "external_effects": dict(view["external_effects"]),
    }


def _collection_status(payload: AiSearchPayload) -> tuple[EvidenceStatus, str | None]:
    search = payload.get("gmail_collection")
    if not isinstance(search, Mapping):
        return "NOT_RUN", "gmail_collection_not_run"
    if search.get("status") != "PASS" or search.get("pagination_exhausted") is not True:
        return "NOT_RUN", "gmail_collection_incomplete"
    sent = payload.get("contact_collection")
    if not isinstance(sent, Mapping):
        return "NOT_RUN", "gmail_sent_collection_not_run"
    if sent.get("status") != "PASS" or sent.get("pagination_exhausted") is not True:
        return "NOT_RUN", "gmail_sent_collection_incomplete"
    return "PASS", None


def _week_identity(value: str) -> tuple[str, str, str, str]:
    occurred_at = datetime.fromisoformat(value)
    if occurred_at.tzinfo is None or occurred_at.utcoffset() is None:
        raise ValueError("weekly AI Search timestamps must be timezone-aware")
    occurred_date = occurred_at.astimezone(KST).date()
    days_since_sunday = (occurred_date.weekday() + 1) % 7
    event_start_date = occurred_date - timedelta(days=days_since_sunday)
    meeting_date = event_start_date + timedelta(days=8)
    window = weekly_window(meeting_date.isoformat())
    end_inclusive = date.fromisoformat(window.event_end_exclusive_kst[:10]) - timedelta(days=1)
    period_label = (
        f"{event_start_date:%Y.%m.%d}~{end_inclusive:%Y.%m.%d}"
    )
    return (
        window.meeting_iso_week,
        window.event_start_kst,
        window.event_end_exclusive_kst,
        period_label,
    )


def _continuous_week_ids(
    windows: dict[str, tuple[str, str, str]],
) -> list[str]:
    if not windows:
        return []
    starts = {
        date.fromisoformat(window[0][:10]): week_id
        for week_id, window in windows.items()
    }
    first = min(starts)
    last = max(starts)
    cursor = first
    ordered: list[str] = []
    while cursor <= last:
        week_id, start, end, label = _week_identity(
            f"{cursor.isoformat()}T00:00:00+09:00"
        )
        windows.setdefault(week_id, (start, end, label))
        ordered.append(week_id)
        cursor += timedelta(days=7)
    return ordered


def _candidate_rows(
    week_id: str,
    batches: Sequence[BatchPayload],
    events: Sequence[SentContactEventPayload],
) -> list[WeeklyCandidateRowPayload]:
    linked_events: dict[str, list[SentContactEventPayload]] = {}
    for event in events:
        for canonical_key in event["canonical_keys"]:
            linked_events.setdefault(canonical_key, []).append(event)
    rows: list[WeeklyCandidateRowPayload] = []
    seen: set[tuple[str, str]] = set()
    for batch in batches:
        for candidate in batch["candidates"]:
            identity = (batch["batch_id"], candidate["canonical_key"])
            if identity in seen:
                raise AssertionError("candidate must be unique inside one AI Search batch")
            seen.add(identity)
            score_evidence = list(
                dict.fromkeys(
                    [*candidate["why_fit"], *candidate["requirements_evidence"]]
                )
            )
            rows.append(
                {
                    "week_id": week_id,
                    "batch_id": batch["batch_id"],
                    "executed_at": batch["executed_at"],
                    "company": batch["company"],
                    "position": batch["position"],
                    "actor": batch["actor"],
                    "actor_label": batch["actor_label"],
                    "source_channel": candidate["source_channel"],
                    "canonical_key": candidate["canonical_key"],
                    "candidate_name": candidate["display_name"],
                    "profile_url": candidate["profile_url"],
                    "education": candidate["education"],
                    "experience": candidate["experience"],
                    "key_experience": candidate["key_experience"],
                    "score": candidate["score"],
                    "score_status": candidate["score_status"],
                    "score_reason": candidate["score_reason"],
                    "score_components": candidate["score_components"],
                    "score_evidence": score_evidence,
                    "weekly_contact": _candidate_contact(
                        linked_events.get(candidate["canonical_key"], ())
                    ),
                }
            )
    rows.sort(
        key=lambda item: (
            item["executed_at"],
            item["company"],
            item["position"],
            item["canonical_key"],
        ),
        reverse=True,
    )
    return rows


def _candidate_contact(
    events: Sequence[SentContactEventPayload],
) -> WeeklyCandidateContactPayload:
    if not events:
        return {
            "status": "NOT_RUN",
            "total": 0,
            "ai_sent_count": 0,
            "owner_sent_count": 0,
            "unknown_sent_count": 0,
            "latest_contacted_at": None,
            "sources": [],
            "attribution": "NOT_RUN",
            "reason": "no_candidate_linked_contact_in_week",
        }
    return {
        "status": "PASS",
        "total": len(events),
        "ai_sent_count": sum(event["actor"] == "AI" for event in events),
        "owner_sent_count": sum(event["actor"] == "OWNER" for event in events),
        "unknown_sent_count": sum(event["actor"] == "UNKNOWN" for event in events),
        "latest_contacted_at": max(event["contacted_at"] for event in events),
        "sources": sorted({event["source"] for event in events}),
        "attribution": "CANDIDATE",
        "reason": "candidate_linked_but_batch_attribution_not_verified",
    }


def _contact_rows(
    week_id: str,
    events: Sequence[SentContactEventPayload],
    candidate_index: Mapping[str, CandidateLedgerPayload],
) -> list[WeeklyContactRowPayload]:
    rows: list[WeeklyContactRowPayload] = []
    for event in events:
        linked_candidates: list[WeeklyLinkedCandidatePayload] = []
        for canonical_key in event["canonical_keys"]:
            candidate = candidate_index.get(canonical_key)
            linked_candidates.append(
                {
                    "canonical_key": canonical_key,
                    "candidate_name": (
                        candidate["display_name"] if candidate is not None else "후보 미확인"
                    ),
                    "profile_url": (
                        candidate["profile_urls"][0]
                        if candidate is not None and candidate["profile_urls"]
                        else None
                    ),
                }
            )
        rows.append(
            {
                "week_id": week_id,
                "contacted_at": event["contacted_at"],
                "actor": event["actor"],
                "actor_reason": event["actor_reason"],
                "source": event["source"],
                "subject": event["subject"],
                "message_id": event["message_id"],
                "thread_id": event["thread_id"],
                "evidence_reference": event["evidence_reference"],
                "link_status": event["link_status"],
                "link_reason": event["link_reason"],
                "linked_candidates": linked_candidates,
            }
        )
    return rows


def _contact_summary(
    events: Sequence[SentContactEventPayload],
) -> WeeklyContactSummaryPayload:
    owner_candidates = {
        canonical_key
        for event in events
        if event["actor"] == "OWNER"
        for canonical_key in event["canonical_keys"]
    }
    linked = sum(event["link_status"] == "PASS" for event in events)
    return {
        "total": len(events),
        "ai_sent": sum(event["actor"] == "AI" for event in events),
        "owner_sent": sum(event["actor"] == "OWNER" for event in events),
        "unknown_sent": sum(event["actor"] == "UNKNOWN" for event in events),
        "linked": linked,
        "unlinked": len(events) - linked,
        "owner_linked_candidates": len(owner_candidates),
    }
