"""Runtime acceptance tests for the Gmail-backed weekly dashboard payload."""

import json
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from humansearch.admin_ai_search import (
    AiSearchRun,
    CandidateEvidence,
    build_ai_search_payload,
    load_evidence_contract,
)
from humansearch.admin_weekly_dashboard import load_metric_contract
from humansearch.admin_weekly_dashboard.shadow_server import build_shadow_dashboard

CONTRACT_PATH = (
    Path(__file__).parents[2]
    / "contracts"
    / "admin-weekly-dashboard"
    / "metric-contract-v1.json"
)
EVIDENCE_CONTRACT_PATH = (
    Path(__file__).parents[2]
    / "contracts"
    / "admin-ai-search"
    / "evidence-contract-v1.json"
)
KST = ZoneInfo("Asia/Seoul")


def _gmail_payload() -> dict[str, object]:
    evidence_contract = load_evidence_contract(EVIDENCE_CONTRACT_PATH)
    run = AiSearchRun(
        actor="CHATGPT",
        source_run_id="gmail-message-1",
        company="REDACTED_CLIENT",
        position="Data Analyst",
        channels=("LINKEDIN",),
        executed_at=datetime(2026, 10, 27, 9, 30, tzinfo=KST),
        candidates=(
            CandidateEvidence(
                canonical_key="a" * 64,
                display_name="REDACTED CANDIDATE",
                source_channel="LINKEDIN",
                profile_url="https://example.invalid/redacted",
                education=None,
                experience=None,
                score=None,
                score_reason="score_contract_evidence_missing",
                why_fit=(),
                reverse_match_position=None,
                reverse_match_score=None,
                reverse_match_reason="reverse_match_not_run",
                contact_recommendation="NOT_RUN",
            ),
        ),
        source_message_ids=("gmail-message-1",),
    )
    payload = build_ai_search_payload((run,), evidence_contract)
    payload["gmail_collection"] = {
        "query": "subject:aisearch -in:spam -in:trash",
        "page_count": 1,
        "message_count": 1,
        "included_message_count": 1,
        "excluded_message_count": 0,
        "excluded_messages": [],
        "pagination_exhausted": True,
        "status": "PASS",
        "reason": None,
    }
    return payload


def test_metric_catalog_and_snapshot_have_the_same_ids() -> None:
    contract = load_metric_contract(CONTRACT_PATH)
    dashboard = build_shadow_dashboard(
        contract,
        _gmail_payload(),
        as_of_date=date(2026, 10, 28),
    )
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


def test_history_uses_twelve_current_weeks_from_the_exhaustive_gmail_read() -> None:
    dashboard = build_shadow_dashboard(
        load_metric_contract(CONTRACT_PATH),
        _gmail_payload(),
        as_of_date=date(2026, 10, 28),
    )

    assert len(dashboard["weeks"]) == 12
    assert dashboard["weeks"][0]["meeting_iso_week"] == "2026-W34"
    assert dashboard["weeks"][-1]["meeting_iso_week"] == "2026-W45"
    assert all(week["status"] == "PASS" for week in dashboard["weeks"])
    assert all(week["snapshot"] is not None for week in dashboard["weeks"])
    assert dashboard["source_summary"] == {
        "status": "PASS",
        "query": "subject:aisearch -in:spam -in:trash",
        "message_count": 1,
        "included_message_count": 1,
        "excluded_message_count": 0,
        "pagination_exhausted": True,
        "latest_received_at": "2026-10-27T09:30:00+09:00",
    }


def test_shadow_view_model_exposes_the_inclusive_saturday_end_date() -> None:
    dashboard = build_shadow_dashboard(
        load_metric_contract(CONTRACT_PATH),
        _gmail_payload(),
        as_of_date=date(2026, 10, 28),
    )
    current_week = dashboard["weeks"][-1]

    assert current_week["event_start_kst"].startswith("2026-10-25T00:00:00")
    assert current_week["event_end_exclusive_kst"].startswith("2026-11-01T00:00:00")
    assert current_week["event_end_inclusive_date_kst"] == "2026-10-31"


def test_shadow_metrics_are_derived_from_the_gmail_ai_search_payload() -> None:
    dashboard = build_shadow_dashboard(
        load_metric_contract(CONTRACT_PATH),
        _gmail_payload(),
        as_of_date=date(2026, 10, 28),
    )
    snapshot = dashboard["weeks"][-1]["snapshot"]

    assert snapshot is not None
    metrics = snapshot["metrics"]
    assert metrics["sourcing_runs"]["value"] == 1
    assert metrics["sourcing_positions"]["value"] == 1
    assert metrics["sourcing_raw_discoveries"]["value"] == 1
    assert metrics["sourcing_source_unique_candidates"]["value"] == 1
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
    dashboard = build_shadow_dashboard(
        load_metric_contract(CONTRACT_PATH),
        _gmail_payload(),
        as_of_date=date(2026, 10, 28),
    )
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
