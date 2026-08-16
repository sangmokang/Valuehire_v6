"""Runtime acceptance tests for privacy, identity, and external-effect boundaries."""

import json
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


def test_snapshot_api_does_not_expose_private_event_payload() -> None:
    contract = load_metric_contract(CONTRACT_PATH)
    private_values = {
        "email": "candidate@example.test",
        "subject": "Synthetic confidential subject",
        "candidate_name": "Synthetic Candidate Name",
        "body": "Synthetic private message body",
    }
    snapshot = build_weekly_snapshot(
        meeting_date_kst="2026-08-17",
        events=[
            MetricEvent(
                source_collection="mail_events",
                source_system="gmail",
                source_primary_key="mail-1",
                event_type="recommendation_mail",
                occurred_at=datetime(2026, 8, 12, 12, 0, tzinfo=KST),
                private_payload=private_values,
            )
        ],
        source_states={
            "mail_events": SourceState(status=MetricStatus.PASS),
            "sourcing_runs": SourceState(status=MetricStatus.PASS),
            "candidate_discoveries": SourceState(status=MetricStatus.PASS),
        },
        metric_contract=contract,
    )

    encoded = json.dumps(snapshot.to_api_dict(), ensure_ascii=False, sort_keys=True)
    for private_value in private_values.values():
        assert private_value not in encoded
    assert "@" not in encoded


def test_contract_slice_exposes_only_disabled_external_effects() -> None:
    contract = load_metric_contract(CONTRACT_PATH)
    snapshot = build_weekly_snapshot(
        meeting_date_kst="2026-08-17",
        events=[],
        source_states={
            "mail_events": SourceState(status=MetricStatus.PASS),
            "sourcing_runs": SourceState(status=MetricStatus.PASS),
            "candidate_discoveries": SourceState(status=MetricStatus.PASS),
        },
        metric_contract=contract,
    )

    payload = snapshot.to_api_dict()
    assert payload["external_effects"] == {
        "clickup": "DISABLED",
        "gmail": "DISABLED",
        "jobkorea": "DISABLED",
        "linkedin": "DISABLED",
        "saramin": "DISABLED",
    }
    assert "actions" not in payload


def test_cross_source_unique_candidate_metric_stays_not_run() -> None:
    contract = load_metric_contract(CONTRACT_PATH)
    common_fields = {
        "source_collection": "candidate_discoveries",
        "event_type": "candidate_discovery",
        "occurred_at": datetime(2026, 8, 12, 12, 0, tzinfo=KST),
        "position_source_id": "position-1",
        "candidate_source_key_hmac": "same-looking-source-key",
    }
    events = [
        MetricEvent(
            source_system="aisearch",
            source_primary_key="discovery-ai",
            **common_fields,
        ),
        MetricEvent(
            source_system="humansearch",
            source_primary_key="discovery-human",
            **common_fields,
        ),
    ]

    snapshot = build_weekly_snapshot(
        meeting_date_kst="2026-08-17",
        events=events,
        source_states={
            "mail_events": SourceState(status=MetricStatus.PASS),
            "sourcing_runs": SourceState(status=MetricStatus.PASS),
            "candidate_discoveries": SourceState(status=MetricStatus.PASS),
        },
        metric_contract=contract,
    )

    assert snapshot.metrics["sourcing_raw_discoveries"].value == 2
    assert snapshot.metrics["sourcing_source_unique_candidates"].value == 2
    global_unique = snapshot.metrics["sourcing_global_unique_candidates"]
    assert global_unique.status is MetricStatus.NOT_RUN
    assert global_unique.value is None
    assert global_unique.reason == "identity_link_contract_missing"

