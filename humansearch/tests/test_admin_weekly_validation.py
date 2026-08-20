"""Regression tests for validated public inputs and non-oracular provenance."""

from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from typing import cast
from zoneinfo import ZoneInfo

import pytest

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


def source_states() -> dict[str, SourceState]:
    return {
        "mail_events": SourceState(status=MetricStatus.PASS),
        "sourcing_runs": SourceState(status=MetricStatus.PASS),
        "candidate_discoveries": SourceState(status=MetricStatus.PASS),
    }


def test_source_state_rejects_runtime_status_strings() -> None:
    with pytest.raises(TypeError, match="MetricStatus"):
        SourceState(
            status=cast(MetricStatus, "FAIL"),
            reason="gmail_timeout",
        )


def test_source_state_rejects_uncontrolled_failure_text() -> None:
    with pytest.raises(ValueError, match="allowlisted"):
        SourceState(
            status=MetricStatus.FAIL,
            reason="candidate@example.test timed out with token=synthetic",
        )


def test_candidate_key_requires_lowercase_hmac_sha256_shape() -> None:
    with pytest.raises(ValueError, match="HMAC-SHA256"):
        MetricEvent(
            source_collection="candidate_discoveries",
            source_system="aisearch",
            source_primary_key="discovery-1",
            event_type="candidate_discovery",
            occurred_at=datetime(2026, 8, 12, 12, 0, tzinfo=KST),
            position_source_id="position-1",
            candidate_source_key_hmac="candidate@example.test",
        )


def test_build_weekly_snapshot_rejects_a_duck_typed_source_state() -> None:
    """A caller must not smuggle a look-alike object past the SourceState contract."""

    contract = load_metric_contract(CONTRACT_PATH)
    fake_state = SimpleNamespace(status=MetricStatus.FAIL, reason="precondition_missing")
    states = source_states()
    states["mail_events"] = cast(SourceState, fake_state)

    with pytest.raises(TypeError, match="SourceState"):
        build_weekly_snapshot(
            meeting_date_kst="2026-08-17",
            events=[],
            source_states=states,
            metric_contract=contract,
        )


def test_metric_contract_rejects_a_not_run_reason_outside_its_status_class(
    tmp_path: Path,
) -> None:
    """not_run metrics must use a NOT_RUN-only reason, not a FAIL-only one."""

    source = CONTRACT_PATH.read_text(encoding="utf-8")
    original = '"not_run_reason": "identity_link_contract_missing"'
    assert source.count(original) == 1
    mutated = tmp_path / "mutated-metric-contract.json"
    mutated.write_text(
        source.replace(original, '"not_run_reason": "gmail_timeout"'),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="NOT_RUN-only"):
        load_metric_contract(mutated)


def test_private_payload_does_not_create_a_public_hash_oracle() -> None:
    contract = load_metric_contract(CONTRACT_PATH)

    def snapshot(private_body: str) -> tuple[str, str]:
        result = build_weekly_snapshot(
            meeting_date_kst="2026-08-17",
            events=[
                MetricEvent(
                    source_collection="mail_events",
                    source_system="gmail",
                    source_primary_key="mail-1",
                    event_type="recommendation_mail",
                    occurred_at=datetime(2026, 8, 12, 12, 0, tzinfo=KST),
                    private_payload={"body": private_body},
                )
            ],
            source_states=source_states(),
            metric_contract=contract,
        )
        return result.input_sha256, result.snapshot_sha256

    assert snapshot("first private body") == snapshot("second private body")

