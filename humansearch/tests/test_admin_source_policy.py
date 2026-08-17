"""Acceptance tests for pre-live source, retention, and identity decisions."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from humansearch.admin_weekly_dashboard.contracts import MetricStatus, SourceFailureReason
from humansearch.admin_weekly_dashboard.source_policy import (
    FAIL_ONLY_REASONS,
    NOT_RUN_ONLY_REASONS,
    CalendarReference,
    CandidateIdentityEvidence,
    CandidateLinkDecision,
    candidate_link_decision,
    collection_state,
    load_source_policy,
    resolve_calendar_alias,
)
from humansearch.admin_weekly_dashboard.source_policy_cli import main as source_policy_main

SOURCE_CONTRACT = (
    Path(__file__).parents[2]
    / "contracts"
    / "admin-weekly-dashboard"
    / "source-contract-v1.json"
)
PROJECT_ROOT = Path(__file__).parents[1]


def test_source_contract_reuses_existing_supabase_tables_without_raw_gmail_fields() -> None:
    policy = load_source_policy(SOURCE_CONTRACT)

    assert policy.version == "admin-weekly-dashboard-sources/v1"
    assert policy.refresh_interval_minutes == 15
    assert policy.calendar_alias == "sangmokang"
    assert policy.gmail_raw_permanent_copy is False
    assert policy.weekly_aggregate_retention == "INDEFINITE"
    assert policy.deletion_request_required is True
    assert policy.candidate_identity_fields == ("name", "school", "company")
    assert policy.candidate_auto_merge is False
    assert policy.candidate_all_exact is CandidateLinkDecision.REVIEW_REQUIRED
    assert policy.external_effects == {
        "calendar": "READ_ONLY_NOT_CONNECTED",
        "clickup": "READ_ONLY_NOT_CONNECTED",
        "gmail": "READ_ONLY_NOT_CONNECTED",
        "supabase_writes": "DISABLED",
    }

    expected_tables = {
        "candidate_cards": "public.pipeline_candidates",
        "gmail_cursor": "public.gmail_sync_state",
        "gmail_events": "public.gmail_derived_events",
        "gmail_runs": "public.gmail_ingestion_runs",
        "position_cards": "public.pipeline_position_cards",
        "sourcing_results": "public.sourcing_results",
        "sourcing_runs": "public.sourcing_runs",
    }
    assert {
        source_name: source.table for source_name, source in policy.supabase_tables.items()
    } == expected_tables

    gmail_fields = set(policy.supabase_tables["gmail_events"].select_fields)
    assert gmail_fields == {"id", "event_type", "status", "occurred_at", "classifier_version"}
    assert gmail_fields.isdisjoint(
        {"body_text", "classified_payload", "from_email", "source_member_email", "subject"}
    )


def test_source_policy_cli_is_a_pii_free_production_readback(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert source_policy_main(["--contract", str(SOURCE_CONTRACT)]) == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["readiness"] == {"status": "NOT_RUN", "reason": "precondition_missing"}
    assert payload["refresh"] == {
        "interval_minutes": 15,
        "overlap_reason": "collection_overlap",
        "overlap_result": "NOT_RUN",
    }
    assert payload["retention"]["gmail_raw_permanent_copy"] is False
    assert payload["candidate_identity"]["auto_merge"] is False
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    for forbidden in ("body_text", "classified_payload", "from_email", "source_member_email"):
        assert forbidden not in serialized


def test_source_policy_cli_runs_through_the_real_module_entrypoint() -> None:
    env = os.environ.copy()
    env["PYTHONPATH"] = "src"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "humansearch.admin_weekly_dashboard.source_policy_cli",
            "--contract",
            str(SOURCE_CONTRACT),
        ],
        cwd=PROJECT_ROOT,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["readiness"] == {"status": "NOT_RUN", "reason": "precondition_missing"}


@pytest.mark.parametrize(
    ("original", "replacement", "error"),
    [
        ('"gmail_raw_permanent_copy": "FORBIDDEN"', '"gmail_raw_permanent_copy": "ALLOWED"', "permanent Gmail"),
        ('"auto_merge": false', '"auto_merge": true', "never auto-merge"),
        ('"interval_minutes": 15', '"interval_minutes": 30', "must be 15 minutes"),
        (
            '"admin-weekly-dashboard-sources/v1"',
            '"admin-weekly-dashboard-sources/v999"',
            "version must be",
        ),
        ('"requested_alias": "sangmokang"', '"requested_alias": "other"', "must be sangmokang"),
        (
            '"public.gmail_derived_events"',
            '"public.gmail_messages"',
            "approved existing Supabase source",
        ),
        (
            '"supabase_writes": "DISABLED"',
            '"supabase_writes": "ENABLED"',
            "external effects must remain",
        ),
    ],
)
def test_source_contract_rejects_unsafe_policy_mutations(
    tmp_path: Path,
    original: str,
    replacement: str,
    error: str,
) -> None:
    source = SOURCE_CONTRACT.read_text(encoding="utf-8")
    assert source.count(original) == 1
    mutated = tmp_path / "mutated-source-contract.json"
    mutated.write_text(source.replace(original, replacement), encoding="utf-8")

    with pytest.raises(ValueError, match=error):
        load_source_policy(mutated)


@pytest.mark.parametrize(
    ("planned", "attempted", "exhausted", "reason", "expected_status"),
    [
        (False, False, False, "collection_not_scheduled", MetricStatus.NOT_RUN),
        (True, False, False, "precondition_missing", MetricStatus.NOT_RUN),
        (True, True, False, "collection_incomplete", MetricStatus.FAIL),
        (True, True, True, None, MetricStatus.PASS),
    ],
)
def test_collection_verdict_requires_a_complete_attempt_for_pass(
    planned: bool,
    attempted: bool,
    exhausted: bool,
    reason: str | None,
    expected_status: MetricStatus,
) -> None:
    state = collection_state(
        planned=planned,
        attempted=attempted,
        pagination_exhausted=exhausted,
        reason=reason,
    )

    assert state.status is expected_status
    if expected_status is MetricStatus.PASS:
        assert state.reason is None
    else:
        assert state.reason is SourceFailureReason(reason)


def test_collection_verdict_rejects_an_attempt_that_was_not_planned() -> None:
    with pytest.raises(ValueError, match="unplanned collection cannot be attempted"):
        collection_state(
            planned=False,
            attempted=True,
            pagination_exhausted=False,
            reason="collection_incomplete",
        )


def test_every_failure_reason_has_an_explicit_collection_status_class() -> None:
    assert NOT_RUN_ONLY_REASONS.isdisjoint(FAIL_ONLY_REASONS)
    assert set(SourceFailureReason) == (
        NOT_RUN_ONLY_REASONS
        | FAIL_ONLY_REASONS
        | {SourceFailureReason.PERMISSION_DENIED}
    )


@pytest.mark.parametrize(
    ("planned", "attempted", "reason", "error"),
    [
        (True, True, "precondition_missing", "NOT_RUN-only"),
        (True, False, "collection_incomplete", "FAIL-only"),
        (True, False, "collection_not_scheduled", "planned collection"),
        (False, False, "precondition_missing", "unplanned collection"),
    ],
)
def test_collection_verdict_rejects_reasons_that_contradict_attempt_state(
    planned: bool,
    attempted: bool,
    reason: str,
    error: str,
) -> None:
    with pytest.raises(ValueError, match=error):
        collection_state(
            planned=planned,
            attempted=attempted,
            pagination_exhausted=False,
            reason=reason,
        )


def test_candidate_all_exact_creates_review_suggestion_but_never_auto_merge() -> None:
    left = CandidateIdentityEvidence(name=" 김 민수 ", school="서울 대학교", company="Acme")
    right = CandidateIdentityEvidence(name="김 민수", school="서울   대학교", company="acme")

    assert candidate_link_decision(left, right) is CandidateLinkDecision.REVIEW_REQUIRED
    assert "AUTO_MERGE" not in {decision.value for decision in CandidateLinkDecision}


@pytest.mark.parametrize(
    ("left", "right", "expected"),
    [
        (
            CandidateIdentityEvidence(name="김민수", school="서울대", company=None),
            CandidateIdentityEvidence(name="김민수", school="서울대", company="Acme"),
            CandidateLinkDecision.INSUFFICIENT_EVIDENCE,
        ),
        (
            CandidateIdentityEvidence(name="김민수", school="서울대", company="Acme"),
            CandidateIdentityEvidence(name="김민수", school="연세대", company="Acme"),
            CandidateLinkDecision.NO_MATCH,
        ),
        (
            CandidateIdentityEvidence(name="김민수", school="서울대", company="Acme"),
            CandidateIdentityEvidence(name="이민수", school="서울대", company="Acme"),
            CandidateLinkDecision.NO_MATCH,
        ),
    ],
)
def test_candidate_link_requires_all_three_exact_fields(
    left: CandidateIdentityEvidence,
    right: CandidateIdentityEvidence,
    expected: CandidateLinkDecision,
) -> None:
    assert candidate_link_decision(left, right) is expected


def test_calendar_alias_resolves_only_one_exact_id_or_summary_match() -> None:
    resolution = resolve_calendar_alias(
        "sangmokang",
        [
            CalendarReference(calendar_id="primary@example.test", summary="업무"),
            CalendarReference(calendar_id="calendar-2", summary="sangmokang"),
        ],
    )

    assert resolution.state.status is MetricStatus.PASS
    assert resolution.calendar_id == "calendar-2"


@pytest.mark.parametrize(
    ("calendars", "reason"),
    [
        ([], SourceFailureReason.CALENDAR_ALIAS_NOT_FOUND),
        (
            [
                CalendarReference(calendar_id="calendar-1", summary="sangmokang"),
                CalendarReference(calendar_id="calendar-2", summary="sangmokang"),
            ],
            SourceFailureReason.CALENDAR_ALIAS_AMBIGUOUS,
        ),
    ],
)
def test_calendar_alias_missing_or_ambiguous_is_not_run(
    calendars: list[CalendarReference],
    reason: SourceFailureReason,
) -> None:
    resolution = resolve_calendar_alias("sangmokang", calendars)

    assert resolution.state.status is MetricStatus.NOT_RUN
    assert resolution.state.reason is reason
    assert resolution.calendar_id is None


def test_duplicate_calendar_list_entries_are_ambiguous_even_with_the_same_id() -> None:
    resolution = resolve_calendar_alias(
        "sangmokang",
        [
            CalendarReference(calendar_id="calendar-1", summary="sangmokang"),
            CalendarReference(calendar_id="calendar-1", summary="sangmokang"),
        ],
    )

    assert resolution.state.status is MetricStatus.NOT_RUN
    assert resolution.state.reason is SourceFailureReason.CALENDAR_ALIAS_AMBIGUOUS
    assert resolution.calendar_id is None
