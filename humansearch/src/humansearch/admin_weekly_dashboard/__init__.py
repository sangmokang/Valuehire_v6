"""Pure contracts for the ValueHire admin weekly dashboard foundation."""

from .contracts import (
    Aggregation,
    MetricCatalogPayload,
    MetricContract,
    MetricDefinition,
    MetricEvent,
    MetricGroupDefinition,
    MetricGroupPayload,
    MetricResult,
    MetricStatus,
    SourceFailureReason,
    SourceState,
    WeeklySnapshot,
    load_metric_contract,
)
from .snapshot import build_weekly_snapshot
from .source_contract import CandidateLinkDecision, SourcePolicy, SupabaseSource, load_source_policy
from .source_policy import (
    CalendarReference,
    CalendarResolution,
    CandidateIdentityEvidence,
    candidate_link_decision,
    collection_state,
    resolve_calendar_alias,
)
from .weekly_window import WeeklyWindow, weekly_window

__all__ = [
    "Aggregation",
    "CalendarReference",
    "CalendarResolution",
    "CandidateIdentityEvidence",
    "CandidateLinkDecision",
    "MetricCatalogPayload",
    "MetricContract",
    "MetricDefinition",
    "MetricEvent",
    "MetricGroupDefinition",
    "MetricGroupPayload",
    "MetricResult",
    "MetricStatus",
    "SourceFailureReason",
    "SourcePolicy",
    "SourceState",
    "SupabaseSource",
    "WeeklySnapshot",
    "WeeklyWindow",
    "build_weekly_snapshot",
    "candidate_link_decision",
    "collection_state",
    "load_metric_contract",
    "load_source_policy",
    "resolve_calendar_alias",
    "weekly_window",
]
