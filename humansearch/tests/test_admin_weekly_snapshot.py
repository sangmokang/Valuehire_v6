"""Runtime acceptance tests for deterministic, provenance-bearing snapshots."""

from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from humansearch.admin_weekly_dashboard import (
    MetricEvent,
    MetricStatus,
    SourceState,
    build_weekly_snapshot,
    load_metric_contract,
)

KST = ZoneInfo("Asia/Seoul")
CONTRACT_PATH = (
    Path(__file__).parents[2]
    / "contracts"
    / "admin-weekly-dashboard"
    / "metric-contract-v1.json"
)


def event(
    *,
    collection: str,
    system: str,
    primary_key: str,
    event_type: str,
    position_id: str | None = None,
    candidate_key_hmac: str | None = None,
) -> MetricEvent:
    return MetricEvent(
        source_collection=collection,
        source_system=system,
        source_primary_key=primary_key,
        event_type=event_type,
        occurred_at=datetime(2026, 8, 12, 12, 0, tzinfo=KST),
        position_source_id=position_id,
        candidate_source_key_hmac=candidate_key_hmac,
    )


def passing_sources() -> dict[str, SourceState]:
    return {
        "mail_events": SourceState(status=MetricStatus.PASS),
        "sourcing_runs": SourceState(status=MetricStatus.PASS),
        "candidate_discoveries": SourceState(status=MetricStatus.PASS),
    }


def test_snapshot_keeps_business_units_separate() -> None:
    contract = load_metric_contract(CONTRACT_PATH)
    events = [
        event(
            collection="sourcing_runs",
            system="aisearch",
            primary_key="run-1",
            event_type="sourcing_run",
        ),
        event(
            collection="sourcing_runs",
            system="aisearch",
            primary_key="run-2",
            event_type="sourcing_run",
        ),
        event(
            collection="candidate_discoveries",
            system="aisearch",
            primary_key="discovery-1",
            event_type="candidate_discovery",
            position_id="position-1",
            candidate_key_hmac="a" * 64,
        ),
        event(
            collection="candidate_discoveries",
            system="aisearch",
            primary_key="discovery-2",
            event_type="candidate_discovery",
            position_id="position-1",
            candidate_key_hmac="a" * 64,
        ),
        event(
            collection="candidate_discoveries",
            system="aisearch",
            primary_key="discovery-3",
            event_type="candidate_discovery",
            position_id="position-2",
            candidate_key_hmac="b" * 64,
        ),
        *[
            event(
                collection="mail_events",
                system="gmail",
                primary_key=f"mail-{index}",
                event_type="recommendation_mail",
            )
            for index in range(1, 5)
        ],
    ]

    snapshot = build_weekly_snapshot(
        meeting_date_kst="2026-08-17",
        events=events,
        source_states=passing_sources(),
        metric_contract=contract,
    )

    assert snapshot.metrics["sourcing_runs"].value == 2
    assert snapshot.metrics["sourcing_positions"].value == 2
    assert snapshot.metrics["sourcing_raw_discoveries"].value == 3
    assert snapshot.metrics["sourcing_source_unique_candidates"].value == 2
    assert snapshot.metrics["recommendation_mail_events"].value == 4
    assert "total_engagement" not in snapshot.metrics


def test_snapshot_is_deterministic_and_every_metric_has_provenance() -> None:
    contract = load_metric_contract(CONTRACT_PATH)
    events = [
        event(
            collection="sourcing_runs",
            system="humansearch",
            primary_key="run-2",
            event_type="sourcing_run",
        ),
        event(
            collection="sourcing_runs",
            system="aisearch",
            primary_key="run-1",
            event_type="sourcing_run",
        ),
    ]

    first = build_weekly_snapshot(
        meeting_date_kst="2026-08-17",
        events=events,
        source_states=passing_sources(),
        metric_contract=contract,
    )
    second = build_weekly_snapshot(
        meeting_date_kst="2026-08-17",
        events=list(reversed(events)),
        source_states=passing_sources(),
        metric_contract=contract,
    )

    assert first.snapshot_sha256 == second.snapshot_sha256
    assert first.to_api_dict() == second.to_api_dict()
    for result in first.to_api_dict()["metrics"].values():
        assert set(result) == {
            "status",
            "value",
            "reason",
            "metric_contract_version",
            "source_collection",
            "source_row_count",
            "input_sha256",
        }
        assert result["input_sha256"] == first.input_sha256


def test_failed_and_not_run_sources_are_not_rendered_as_zero() -> None:
    contract = load_metric_contract(CONTRACT_PATH)
    states = passing_sources()
    states["mail_events"] = SourceState(
        status=MetricStatus.FAIL,
        reason="gmail_timeout",
    )
    states["candidate_discoveries"] = SourceState(
        status=MetricStatus.NOT_RUN,
        reason="retention_policy_missing",
    )

    snapshot = build_weekly_snapshot(
        meeting_date_kst="2026-08-17",
        events=[],
        source_states=states,
        metric_contract=contract,
    )

    failed = snapshot.metrics["recommendation_mail_events"]
    not_run = snapshot.metrics["sourcing_raw_discoveries"]
    normal_zero = snapshot.metrics["sourcing_runs"]
    assert (failed.status, failed.value, failed.reason) == (
        MetricStatus.FAIL,
        None,
        "gmail_timeout",
    )
    assert (not_run.status, not_run.value, not_run.reason) == (
        MetricStatus.NOT_RUN,
        None,
        "retention_policy_missing",
    )
    assert (normal_zero.status, normal_zero.value, normal_zero.reason) == (
        MetricStatus.PASS,
        0,
        None,
    )
