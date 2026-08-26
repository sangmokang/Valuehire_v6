"""Operational source decisions for the pre-live dashboard ingestion boundary.

The source/retention/identity contract itself (SourcePolicy, SupabaseSource,
load_source_policy) lives in source_contract.py — this file only covers what
to do at runtime given planned/attempted/collected signals, calendar
resolution, and candidate identity matching.
"""

from __future__ import annotations

import unicodedata
from collections.abc import Sequence
from dataclasses import dataclass

from .contracts import (
    FAIL_ONLY_REASONS,
    NOT_RUN_ONLY_REASONS,
    MetricStatus,
    SourceFailureReason,
    SourceState,
)
from .source_contract import EXPECTED_CALENDAR_ALIAS, CandidateLinkDecision

# mypy --strict requires re-exported imports to be listed here; tests import the
# reason-classification sets from this module rather than from .contracts directly.
__all__ = [
    "FAIL_ONLY_REASONS",
    "NOT_RUN_ONLY_REASONS",
]


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

    def __post_init__(self) -> None:
        if not isinstance(self.calendar_id, str) or not self.calendar_id.strip():
            raise ValueError("calendar_id must be a non-empty string")
        if self.calendar_id != self.calendar_id.strip():
            raise ValueError("calendar_id must not carry leading or trailing whitespace")
        if not isinstance(self.summary, str) or not self.summary.strip():
            raise ValueError("summary must be a non-empty string")


@dataclass(frozen=True, init=False)
class CalendarResolution:
    """Resolved runtime calendar ID or a truthful NOT_RUN state."""

    state: SourceState
    calendar_id: str | None

    def __init__(self, *, state: SourceState, calendar_id: str | None) -> None:
        if not isinstance(state, SourceState):
            raise TypeError("state must be a SourceState")
        if calendar_id is not None and (
            not isinstance(calendar_id, str) or not calendar_id.strip()
        ):
            raise TypeError("calendar_id must be None or a non-empty, non-blank string")
        if state.status is MetricStatus.PASS and calendar_id is None:
            raise ValueError("a PASS calendar resolution requires a non-empty calendar_id")
        if state.status is not MetricStatus.PASS and calendar_id is not None:
            raise ValueError("a non-PASS calendar resolution must not carry a calendar_id")
        object.__setattr__(self, "state", state)
        object.__setattr__(self, "calendar_id", calendar_id)


def candidate_link_decision(
    left: CandidateIdentityEvidence,
    right: CandidateIdentityEvidence,
) -> CandidateLinkDecision:
    """Compare name, school, and company without ever auto-merging."""

    left_values = (_normalize(left.name), _normalize(left.school), _normalize(left.company))
    right_values = (_normalize(right.name), _normalize(right.school), _normalize(right.company))
    for left_value, right_value in zip(left_values, right_values, strict=True):
        if left_value is not None and right_value is not None and left_value != right_value:
            return CandidateLinkDecision.NO_MATCH
    if any(value is None for value in (*left_values, *right_values)):
        return CandidateLinkDecision.INSUFFICIENT_EVIDENCE
    return CandidateLinkDecision.REVIEW_REQUIRED


def resolve_calendar_alias(
    alias: str,
    calendars: Sequence[CalendarReference],
) -> CalendarResolution:
    """Resolve an alias only when exactly one CalendarList entry matches.

    The v1 contract fixes the target identity to EXPECTED_CALENDAR_ALIAS, so a
    different alias is rejected outright rather than silently resolved. The
    calendar_id comparison is literal (no case/whitespace folding) because the
    contract requires an exact id match; only the human-readable summary is
    matched case- and whitespace-insensitively.
    """

    if alias != EXPECTED_CALENDAR_ALIAS:
        raise ValueError(f"calendar alias must be exactly {EXPECTED_CALENDAR_ALIAS!r}")
    normalized_alias = _normalize(alias)
    matches = []
    for calendar in calendars:
        if not isinstance(calendar, CalendarReference):
            raise TypeError("calendars must contain only CalendarReference entries")
        if calendar.calendar_id == alias or _normalize(calendar.summary) == normalized_alias:
            matches.append(calendar)
    if not matches:
        return CalendarResolution(
            state=SourceState(
                status=MetricStatus.NOT_RUN,
                reason=SourceFailureReason.CALENDAR_ALIAS_NOT_FOUND,
            ),
            calendar_id=None,
        )
    if len(matches) > 1:
        return CalendarResolution(
            state=SourceState(
                status=MetricStatus.NOT_RUN,
                reason=SourceFailureReason.CALENDAR_ALIAS_AMBIGUOUS,
            ),
            calendar_id=None,
        )
    calendar_id = matches[0].calendar_id
    return CalendarResolution(
        state=SourceState(status=MetricStatus.PASS),
        calendar_id=calendar_id,
    )


def collection_state(
    *,
    planned: bool,
    attempted: bool,
    pagination_exhausted: bool,
    reason: SourceFailureReason | str | None = None,
) -> SourceState:
    """Separate deliberate NOT_RUN from attempted-but-incomplete FAIL."""

    for name, value in (
        ("planned", planned),
        ("attempted", attempted),
        ("pagination_exhausted", pagination_exhausted),
    ):
        if not isinstance(value, bool):
            raise TypeError(f"{name} must be a bool")
    if attempted and not planned:
        raise ValueError("unplanned collection cannot be attempted")
    if pagination_exhausted and not attempted:
        raise ValueError("pagination cannot be exhausted without an attempt")
    normalized_reason = None if reason is None else SourceFailureReason(reason)
    if pagination_exhausted:
        if normalized_reason is not None:
            raise ValueError("a completed collection cannot have a failure reason")
        return SourceState(status=MetricStatus.PASS)
    if attempted:
        failure_reason = normalized_reason or SourceFailureReason.COLLECTION_INCOMPLETE
        if failure_reason in NOT_RUN_ONLY_REASONS:
            raise ValueError("an attempted collection cannot use a NOT_RUN-only reason")
        return SourceState(
            status=MetricStatus.FAIL,
            reason=failure_reason,
        )
    if not planned:
        if normalized_reason not in {None, SourceFailureReason.COLLECTION_NOT_SCHEDULED}:
            raise ValueError("an unplanned collection must use collection_not_scheduled")
        return SourceState(
            status=MetricStatus.NOT_RUN,
            reason=SourceFailureReason.COLLECTION_NOT_SCHEDULED,
        )
    not_run_reason = normalized_reason or SourceFailureReason.PRECONDITION_MISSING
    if not_run_reason is SourceFailureReason.COLLECTION_NOT_SCHEDULED:
        raise ValueError("a planned collection cannot use collection_not_scheduled")
    if not_run_reason in FAIL_ONLY_REASONS:
        raise ValueError("an unattempted collection cannot use a FAIL-only reason")
    return SourceState(status=MetricStatus.NOT_RUN, reason=not_run_reason)


def _normalize(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = " ".join(unicodedata.normalize("NFKC", value).split()).casefold()
    return normalized or None
