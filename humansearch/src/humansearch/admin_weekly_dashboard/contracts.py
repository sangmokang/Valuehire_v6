"""Validated input, metric-contract, and output types for weekly snapshots."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import TypedDict, cast

from .weekly_window import WeeklyWindow, WeeklyWindowPayload


class MetricStatus(str, Enum):
    """Three-state source and metric verdict; missing work is never PASS."""

    PASS = "PASS"
    FAIL = "FAIL"
    NOT_RUN = "NOT_RUN"


class Aggregation(str, Enum):
    """Operations supported by the contract-driven pure aggregator."""

    COUNT = "count"
    DISTINCT = "distinct"
    NOT_RUN = "not_run"


@dataclass(frozen=True)
class SourceState:
    """Whether one source collection was read successfully for this snapshot."""

    status: MetricStatus
    reason: str | None = None

    def __post_init__(self) -> None:
        if self.status is MetricStatus.PASS and self.reason is not None:
            raise ValueError("PASS source state cannot have a failure reason")
        if self.status is not MetricStatus.PASS and not self.reason:
            raise ValueError("FAIL and NOT_RUN source states require a reason")


@dataclass(frozen=True, init=False)
class MetricEvent:
    """Minimal source event; private payload participates only through an input hash."""

    source_collection: str
    source_system: str
    source_primary_key: str
    event_type: str
    occurred_at: datetime
    position_source_id: str | None
    candidate_source_key_hmac: str | None
    private_payload: Mapping[str, str] = field(repr=False, compare=False)

    def __init__(self, **values: object) -> None:
        required = {
            "source_collection",
            "source_system",
            "source_primary_key",
            "event_type",
            "occurred_at",
        }
        optional = {"position_source_id", "candidate_source_key_hmac", "private_payload"}
        unexpected = set(values) - required - optional
        missing = required - set(values)
        if unexpected:
            raise TypeError(f"unexpected MetricEvent fields: {sorted(unexpected)}")
        if missing:
            raise TypeError(f"missing MetricEvent fields: {sorted(missing)}")

        for key in required - {"occurred_at"}:
            if not isinstance(values[key], str) or not values[key]:
                raise TypeError(f"{key} must be a non-empty string")
        occurred_at = values["occurred_at"]
        if not isinstance(occurred_at, datetime):
            raise TypeError("occurred_at must be a datetime")
        if occurred_at.tzinfo is None or occurred_at.utcoffset() is None:
            raise ValueError("occurred_at must be timezone-aware")

        position_source_id = _optional_string(values.get("position_source_id"), "position_source_id")
        candidate_key = _optional_string(
            values.get("candidate_source_key_hmac"),
            "candidate_source_key_hmac",
        )
        private_payload = _private_payload(values.get("private_payload", {}))

        object.__setattr__(self, "source_collection", cast(str, values["source_collection"]))
        object.__setattr__(self, "source_system", cast(str, values["source_system"]))
        object.__setattr__(self, "source_primary_key", cast(str, values["source_primary_key"]))
        object.__setattr__(self, "event_type", cast(str, values["event_type"]))
        object.__setattr__(self, "occurred_at", occurred_at)
        object.__setattr__(self, "position_source_id", position_source_id)
        object.__setattr__(self, "candidate_source_key_hmac", candidate_key)
        object.__setattr__(self, "private_payload", private_payload)


@dataclass(frozen=True)
class MetricDefinition:
    """One display metric loaded from the repository contract."""

    metric_id: str
    description: str
    source_collection: str
    event_type: str
    aggregation: Aggregation
    distinct_fields: tuple[str, ...] = ()
    not_run_reason: str | None = None


@dataclass(frozen=True)
class MetricContract:
    """Validated metric definitions and the external-effect boundary."""

    version: str
    metrics: tuple[MetricDefinition, ...]
    external_effects: Mapping[str, str]


@dataclass(frozen=True)
class MetricResult:
    """One display value and the minimum provenance needed to reproduce it."""

    status: MetricStatus
    value: int | None
    reason: str | None
    metric_contract_version: str
    source_collection: str
    source_row_count: int
    input_sha256: str

    def to_payload(self) -> MetricPayload:
        """Return this result in its JSON-safe API shape."""

        return {
            "status": self.status.value,
            "value": self.value,
            "reason": self.reason,
            "metric_contract_version": self.metric_contract_version,
            "source_collection": self.source_collection,
            "source_row_count": self.source_row_count,
            "input_sha256": self.input_sha256,
        }


class MetricPayload(TypedDict):
    status: str
    value: int | None
    reason: str | None
    metric_contract_version: str
    source_collection: str
    source_row_count: int
    input_sha256: str


class SnapshotPayload(TypedDict):
    window: WeeklyWindowPayload
    metrics: dict[str, MetricPayload]
    external_effects: dict[str, str]
    input_sha256: str
    snapshot_sha256: str


@dataclass(frozen=True)
class WeeklySnapshot:
    """A deterministic, PII-safe read model for the future admin UI."""

    window: WeeklyWindow
    metrics: Mapping[str, MetricResult]
    external_effects: Mapping[str, str]
    input_sha256: str
    snapshot_sha256: str

    def to_api_dict(self) -> SnapshotPayload:
        """Return only fields allowed across the future admin API boundary."""

        return {
            "window": self.window.to_payload(),
            "metrics": {
                metric_id: self.metrics[metric_id].to_payload()
                for metric_id in sorted(self.metrics)
            },
            "external_effects": dict(sorted(self.external_effects.items())),
            "input_sha256": self.input_sha256,
            "snapshot_sha256": self.snapshot_sha256,
        }


def load_metric_contract(path: Path) -> MetricContract:
    """Load and fail-closed validate the single metric-definition source."""

    raw: object = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise TypeError("metric contract root must be an object")
    root = cast(dict[str, object], raw)
    version = _required_string(root, "version")

    metrics_raw = root.get("metrics")
    if not isinstance(metrics_raw, list) or not metrics_raw:
        raise ValueError("metric contract must contain at least one metric")
    metrics = tuple(_metric_definition(item) for item in metrics_raw)
    metric_ids = [metric.metric_id for metric in metrics]
    if len(metric_ids) != len(set(metric_ids)):
        raise ValueError("metric ids must be unique")

    effects_raw = root.get("external_effects")
    if not isinstance(effects_raw, dict) or not effects_raw:
        raise ValueError("external_effects must be a non-empty object")
    external_effects: dict[str, str] = {}
    for key, value in effects_raw.items():
        if not isinstance(key, str) or not isinstance(value, str):
            raise TypeError("external effect keys and values must be strings")
        if value != "DISABLED":
            raise ValueError(f"external effect {key} must remain DISABLED in Phase B")
        external_effects[key] = value

    return MetricContract(
        version=version,
        metrics=metrics,
        external_effects=external_effects,
    )


def _metric_definition(raw: object) -> MetricDefinition:
    if not isinstance(raw, dict):
        raise TypeError("each metric must be an object")
    data = cast(dict[str, object], raw)
    try:
        aggregation = Aggregation(_required_string(data, "aggregation"))
    except ValueError as error:
        raise ValueError("unsupported metric aggregation") from error

    fields_raw = data.get("distinct_fields", [])
    if not isinstance(fields_raw, list) or not all(isinstance(field, str) for field in fields_raw):
        raise ValueError("distinct_fields must be a string array")
    distinct_fields = tuple(cast(str, field) for field in fields_raw)
    allowed_fields = {
        "source_system",
        "source_primary_key",
        "position_source_id",
        "candidate_source_key_hmac",
    }
    if set(distinct_fields) - allowed_fields:
        raise ValueError("distinct_fields contains an unsupported field")
    if aggregation is Aggregation.DISTINCT and not distinct_fields:
        raise ValueError("distinct aggregation requires distinct_fields")
    if aggregation is not Aggregation.DISTINCT and distinct_fields:
        raise ValueError("only distinct aggregation may define distinct_fields")

    reason_raw = data.get("not_run_reason")
    not_run_reason = _optional_string(reason_raw, "not_run_reason")
    if aggregation is Aggregation.NOT_RUN and not not_run_reason:
        raise ValueError("not_run aggregation requires not_run_reason")
    if aggregation is not Aggregation.NOT_RUN and not_run_reason is not None:
        raise ValueError("only not_run aggregation may define not_run_reason")

    return MetricDefinition(
        metric_id=_required_string(data, "id"),
        description=_required_string(data, "description"),
        source_collection=_required_string(data, "source_collection"),
        event_type=_required_string(data, "event_type"),
        aggregation=aggregation,
        distinct_fields=distinct_fields,
        not_run_reason=not_run_reason,
    )


def _required_string(data: Mapping[str, object], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"{key} must be a non-empty string")
    return value


def _optional_string(value: object, name: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value:
        raise TypeError(f"{name} must be a non-empty string or None")
    return value


def _private_payload(value: object) -> Mapping[str, str]:
    if not isinstance(value, Mapping):
        raise TypeError("private_payload must be a string mapping")
    payload: dict[str, str] = {}
    for key, item in value.items():
        if not isinstance(key, str) or not isinstance(item, str):
            raise TypeError("private_payload must be a string mapping")
        payload[key] = item
    return payload
