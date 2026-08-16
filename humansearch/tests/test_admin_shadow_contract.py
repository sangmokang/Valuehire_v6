"""Runtime acceptance tests for the local shadow dashboard payload."""

import json
from pathlib import Path

from humansearch.admin_weekly_dashboard import load_metric_contract
from humansearch.admin_weekly_dashboard.shadow_server import build_shadow_dashboard

CONTRACT_PATH = (
    Path(__file__).parents[2]
    / "contracts"
    / "admin-weekly-dashboard"
    / "metric-contract-v1.json"
)


def test_metric_catalog_and_snapshot_have_the_same_ids() -> None:
    contract = load_metric_contract(CONTRACT_PATH)
    dashboard = build_shadow_dashboard(contract)
    current_week = dashboard["weeks"][-1]
    snapshot = current_week["snapshot"]

    assert snapshot is not None
    catalog_ids = {metric["id"] for metric in dashboard["metric_catalog"]}
    assert catalog_ids == set(snapshot["metrics"])
    for metric in dashboard["metric_catalog"]:
        assert metric["display_label"]
        assert metric["description"]
        assert metric["group"] in {"mail", "sourcing", "identity"}
        assert metric["unit"] in {"건", "명", "회", "개"}


def test_shadow_history_has_one_collected_week_and_eleven_not_run_weeks() -> None:
    dashboard = build_shadow_dashboard(load_metric_contract(CONTRACT_PATH))

    assert len(dashboard["weeks"]) == 12
    assert sum(week["snapshot"] is not None for week in dashboard["weeks"]) == 1
    for week in dashboard["weeks"][:-1]:
        assert week["status"] == "NOT_RUN"
        assert week["reason"] == "history_not_collected"
        assert week["snapshot"] is None
    assert dashboard["weeks"][-1]["status"] == "PASS"


def test_shadow_metrics_keep_units_and_failure_states_truthful() -> None:
    dashboard = build_shadow_dashboard(load_metric_contract(CONTRACT_PATH))
    snapshot = dashboard["weeks"][-1]["snapshot"]

    assert snapshot is not None
    metrics = snapshot["metrics"]
    assert metrics["sourcing_runs"]["value"] == 2
    assert metrics["sourcing_positions"]["value"] == 3
    assert metrics["sourcing_raw_discoveries"]["value"] == 5
    assert metrics["sourcing_source_unique_candidates"]["value"] == 4
    assert metrics["recommendation_mail_events"] == {
        **metrics["recommendation_mail_events"],
        "status": "NOT_RUN",
        "value": None,
        "reason": "retention_policy_missing",
    }
    assert metrics["position_mail_events"]["status"] == "NOT_RUN"
    assert metrics["position_mail_events"]["value"] is None
    assert metrics["sourcing_global_unique_candidates"]["status"] == "NOT_RUN"
    assert metrics["sourcing_global_unique_candidates"]["reason"] == (
        "identity_link_contract_missing"
    )


def test_shadow_payload_contains_no_personal_data_or_external_action() -> None:
    dashboard = build_shadow_dashboard(load_metric_contract(CONTRACT_PATH))
    encoded = json.dumps(dashboard, ensure_ascii=False, sort_keys=True)

    assert "@" not in encoded
    assert "actions" not in encoded
    assert dashboard["mode"] == "LOCAL_SHADOW"
    assert dashboard["external_effects"] == {
        "clickup": "DISABLED",
        "gmail": "DISABLED",
        "jobkorea": "DISABLED",
        "linkedin": "DISABLED",
        "saramin": "DISABLED",
    }
