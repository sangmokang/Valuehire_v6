"""Operational source decisions for the pre-live dashboard ingestion boundary."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from .contracts import SourceFailureReason, SourceState


class CandidateLinkDecision(str, Enum):
    """A review suggestion is the strongest allowed identity outcome."""

    NO_MATCH = "NO_MATCH"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"


@dataclass(frozen=True)
class CandidateIdentityEvidence:
    """Transient identity evidence; never part of a dashboard snapshot."""

    name: str | None
    school: str | None
    company: str | None


@dataclass(frozen=True)
class CalendarReference:
    """Minimum fields returned by a CalendarList entry."""

    calendar_id: str
    summary: str


@dataclass(frozen=True)
class CalendarResolution:
    """Resolved runtime calendar ID or a truthful NOT_RUN state."""

    state: SourceState
    calendar_id: str | None


@dataclass(frozen=True)
class SupabaseSource:
    """An existing table and the minimum fields allowed for dashboard reads."""

    table: str
    select_fields: tuple[str, ...]
    processing: str


@dataclass(frozen=True)
class SourcePolicy:
    """Validated source, retention, identity, and cadence decisions."""

    version: str
    refresh_interval_minutes: int
    overlap_reason: SourceFailureReason
    calendar_alias: str
    gmail_raw_permanent_copy: bool
    weekly_aggregate_retention: str
    deletion_request_required: bool
    candidate_identity_fields: tuple[str, ...]
    candidate_auto_merge: bool
    candidate_all_exact: CandidateLinkDecision
    supabase_tables: Mapping[str, SupabaseSource]
    external_effects: Mapping[str, str]


def load_source_policy(path: Path) -> SourcePolicy:
    """Load and fail-closed validate the operational source contract."""

    raise NotImplementedError("RED: source policy loader is not implemented")


def candidate_link_decision(
    left: CandidateIdentityEvidence,
    right: CandidateIdentityEvidence,
) -> CandidateLinkDecision:
    """Compare name, school, and company without ever auto-merging."""

    raise NotImplementedError("RED: candidate identity policy is not implemented")


def resolve_calendar_alias(
    alias: str,
    calendars: Sequence[CalendarReference],
) -> CalendarResolution:
    """Resolve an alias only when exactly one CalendarList entry matches."""

    raise NotImplementedError("RED: calendar resolution is not implemented")


def collection_state(
    *,
    planned: bool,
    attempted: bool,
    pagination_exhausted: bool,
    reason: SourceFailureReason | str | None = None,
) -> SourceState:
    """Separate deliberate NOT_RUN from attempted-but-incomplete FAIL."""

    raise NotImplementedError("RED: collection verdict policy is not implemented")
