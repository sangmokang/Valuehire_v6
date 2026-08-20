"""Status/reason vocabulary shared by every result-shaped dashboard type.

Split out of contracts.py so the three-state verdict codes and the
FAIL/NOT_RUN reason classification live next to each other, independent of
the dataclasses that consume them. This file has no internal package
dependencies, which keeps contracts.py free to import it without creating a
cycle.
"""

from __future__ import annotations

from enum import Enum


class MetricStatus(str, Enum):
    """Three-state source and metric verdict; missing work is never PASS."""

    PASS = "PASS"
    FAIL = "FAIL"
    NOT_RUN = "NOT_RUN"


class SourceFailureReason(str, Enum):
    """PII-safe reason codes allowed to cross the dashboard API boundary."""

    CALENDAR_ALIAS_AMBIGUOUS = "calendar_alias_ambiguous"
    CALENDAR_ALIAS_NOT_FOUND = "calendar_alias_not_found"
    CALENDAR_EVENT_ID_MISSING = "calendar_event_id_missing"
    COLLECTION_INCOMPLETE = "collection_incomplete"
    COLLECTION_NOT_SCHEDULED = "collection_not_scheduled"
    COLLECTION_OVERLAP = "collection_overlap"
    CONTRACT_MISMATCH = "contract_mismatch"
    GMAIL_TIMEOUT = "gmail_timeout"
    HISTORY_NOT_COLLECTED = "history_not_collected"
    IDENTITY_LINK_CONTRACT_MISSING = "identity_link_contract_missing"
    PERMISSION_DENIED = "permission_denied"
    PRECONDITION_MISSING = "precondition_missing"
    RETENTION_POLICY_MISSING = "retention_policy_missing"
    SOURCE_STATE_MISSING = "source_state_missing"
    SOURCE_TIMEOUT = "source_timeout"
    SOURCE_UNAVAILABLE = "source_unavailable"


# A reason may belong to at most one of these two classes; PERMISSION_DENIED belongs to
# neither and is deliberately allowed to pair with either FAIL or NOT_RUN.
NOT_RUN_ONLY_REASONS = frozenset(
    {
        SourceFailureReason.CALENDAR_ALIAS_AMBIGUOUS,
        SourceFailureReason.CALENDAR_ALIAS_NOT_FOUND,
        SourceFailureReason.COLLECTION_NOT_SCHEDULED,
        SourceFailureReason.COLLECTION_OVERLAP,
        SourceFailureReason.HISTORY_NOT_COLLECTED,
        SourceFailureReason.IDENTITY_LINK_CONTRACT_MISSING,
        SourceFailureReason.PRECONDITION_MISSING,
        SourceFailureReason.RETENTION_POLICY_MISSING,
        SourceFailureReason.SOURCE_STATE_MISSING,
    }
)
FAIL_ONLY_REASONS = frozenset(
    {
        SourceFailureReason.CALENDAR_EVENT_ID_MISSING,
        SourceFailureReason.COLLECTION_INCOMPLETE,
        SourceFailureReason.CONTRACT_MISMATCH,
        SourceFailureReason.GMAIL_TIMEOUT,
        SourceFailureReason.SOURCE_TIMEOUT,
        SourceFailureReason.SOURCE_UNAVAILABLE,
    }
)


def reject_reason_status_mismatch(status: MetricStatus, reason: SourceFailureReason) -> None:
    """Shared status/reason classification guard for every result-shaped type."""

    if status is MetricStatus.FAIL and reason in NOT_RUN_ONLY_REASONS:
        raise ValueError(f"FAIL cannot use the NOT_RUN-only reason {reason.value}")
    if status is MetricStatus.NOT_RUN and reason in FAIL_ONLY_REASONS:
        raise ValueError(f"NOT_RUN cannot use the FAIL-only reason {reason.value}")
