"""Contract-driven, deterministic weekly snapshot aggregation."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from datetime import UTC

from .contracts import (
    Aggregation,
    MetricContract,
    MetricDefinition,
    MetricEvent,
    MetricResult,
    MetricStatus,
    SnapshotPayload,
    SourceState,
    WeeklySnapshot,
)
from .weekly_window import WeeklyWindow, weekly_window


def build_weekly_snapshot(
    *,
    meeting_date_kst: str,
    events: Sequence[MetricEvent],
    source_states: Mapping[str, SourceState],
    metric_contract: MetricContract,
) -> WeeklySnapshot:
    """Build all card values and provenance from one immutable logical input."""

    for source_collection, state in source_states.items():
        if not isinstance(state, SourceState):
            raise TypeError(f"source state for {source_collection!r} must be a SourceState")

    window = weekly_window(meeting_date_kst)
    input_sha256 = _input_sha256(window, events, source_states, metric_contract.version)
    metrics = {
        definition.metric_id: _metric_result(
            definition=definition,
            events=events,
            source_states=source_states,
            window=window,
            contract_version=metric_contract.version,
            input_sha256=input_sha256,
        )
        for definition in metric_contract.metrics
    }
    snapshot_without_hash = _snapshot_payload(
        window=window,
        metrics=metrics,
        external_effects=metric_contract.external_effects,
        input_sha256=input_sha256,
        snapshot_sha256="",
    )
    snapshot_sha256 = _sha256(snapshot_without_hash)
    return WeeklySnapshot(
        window=window,
        metrics=metrics,
        external_effects=metric_contract.external_effects,
        input_sha256=input_sha256,
        snapshot_sha256=snapshot_sha256,
    )


def _metric_result(
    *,
    definition: MetricDefinition,
    events: Sequence[MetricEvent],
    source_states: Mapping[str, SourceState],
    window: WeeklyWindow,
    contract_version: str,
    input_sha256: str,
) -> MetricResult:
    relevant = [
        event
        for event in events
        if event.source_collection == definition.source_collection
        and event.event_type == definition.event_type
        and window.contains(event.occurred_at)
    ]
    if definition.aggregation is Aggregation.NOT_RUN:
        return MetricResult(
            status=MetricStatus.NOT_RUN,
            value=None,
            reason=definition.not_run_reason,
            metric_contract_version=contract_version,
            source_collection=definition.source_collection,
            source_row_count=len(relevant),
            input_sha256=input_sha256,
        )

    state = source_states.get(definition.source_collection)
    if state is None:
        state = SourceState(
            status=MetricStatus.NOT_RUN,
            reason="source_state_missing",
        )
    elif not isinstance(state, SourceState):
        raise TypeError(
            f"source state for {definition.source_collection!r} must be a SourceState"
        )
    if state.status is not MetricStatus.PASS:
        return MetricResult(
            status=state.status,
            value=None,
            reason=state.reason,
            metric_contract_version=contract_version,
            source_collection=definition.source_collection,
            source_row_count=len(relevant),
            input_sha256=input_sha256,
        )

    value = _aggregate(definition, relevant)
    return MetricResult(
        status=MetricStatus.PASS,
        value=value,
        reason=None,
        metric_contract_version=contract_version,
        source_collection=definition.source_collection,
        source_row_count=len(relevant),
        input_sha256=input_sha256,
    )


def _aggregate(definition: MetricDefinition, events: Sequence[MetricEvent]) -> int:
    if definition.aggregation is Aggregation.COUNT:
        return len(events)
    if definition.aggregation is Aggregation.DISTINCT:
        values: set[tuple[str, ...]] = set()
        for event in events:
            distinct_value = tuple(_distinct_value(event, field) for field in definition.distinct_fields)
            values.add(distinct_value)
        return len(values)
    raise ValueError("NOT_RUN metrics must be handled before aggregation")


def _distinct_value(event: MetricEvent, field_name: str) -> str:
    value = getattr(event, field_name)
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field_name} is required for distinct aggregation")
    return value


def _input_sha256(
    window: WeeklyWindow,
    events: Sequence[MetricEvent],
    source_states: Mapping[str, SourceState],
    contract_version: str,
) -> str:
    canonical_events = sorted(
        (_event_for_hash(event) for event in events),
        key=lambda item: json.dumps(item, ensure_ascii=False, sort_keys=True),
    )
    payload = {
        "contract_version": contract_version,
        "window": window.to_payload(),
        "source_states": {
            source: {"status": state.status.value, "reason": state.reason}
            for source, state in sorted(source_states.items())
        },
        "events": canonical_events,
    }
    return _sha256(payload)


def _event_for_hash(event: MetricEvent) -> dict[str, object]:
    return {
        "source_collection": event.source_collection,
        "source_system": event.source_system,
        "source_primary_key": event.source_primary_key,
        "event_type": event.event_type,
        "occurred_at_utc": event.occurred_at.astimezone(UTC).isoformat(),
        "position_source_id": event.position_source_id,
        "candidate_source_key_hmac": event.candidate_source_key_hmac,
    }


def _snapshot_payload(
    *,
    window: WeeklyWindow,
    metrics: Mapping[str, MetricResult],
    external_effects: Mapping[str, str],
    input_sha256: str,
    snapshot_sha256: str,
) -> SnapshotPayload:
    return {
        "window": window.to_payload(),
        "metrics": {
            metric_id: metrics[metric_id].to_payload()
            for metric_id in sorted(metrics)
        },
        "external_effects": dict(sorted(external_effects.items())),
        "input_sha256": input_sha256,
        "snapshot_sha256": snapshot_sha256,
    }


def _sha256(payload: object) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
