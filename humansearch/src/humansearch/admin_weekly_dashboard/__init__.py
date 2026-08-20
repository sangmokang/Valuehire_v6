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
from .weekly_window import WeeklyWindow, weekly_window

__all__ = [
    "Aggregation",
    "MetricCatalogPayload",
    "MetricContract",
    "MetricDefinition",
    "MetricEvent",
    "MetricGroupDefinition",
    "MetricGroupPayload",
    "MetricResult",
    "MetricStatus",
    "SourceFailureReason",
    "SourceState",
    "WeeklySnapshot",
    "WeeklyWindow",
    "build_weekly_snapshot",
    "load_metric_contract",
    "weekly_window",
]
