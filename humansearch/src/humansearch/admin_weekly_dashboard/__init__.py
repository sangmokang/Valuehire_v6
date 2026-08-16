"""Pure contracts for the ValueHire admin weekly dashboard foundation."""

from .contracts import (
    Aggregation,
    MetricContract,
    MetricDefinition,
    MetricEvent,
    MetricResult,
    MetricStatus,
    SourceState,
    WeeklySnapshot,
    load_metric_contract,
)
from .snapshot import build_weekly_snapshot
from .weekly_window import WeeklyWindow, weekly_window

__all__ = [
    "Aggregation",
    "MetricContract",
    "MetricDefinition",
    "MetricEvent",
    "MetricResult",
    "MetricStatus",
    "SourceState",
    "WeeklySnapshot",
    "WeeklyWindow",
    "build_weekly_snapshot",
    "load_metric_contract",
    "weekly_window",
]
