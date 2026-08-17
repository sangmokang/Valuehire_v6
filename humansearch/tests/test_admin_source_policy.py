"""Acceptance tests for pre-live source, retention, and identity decisions."""

from pathlib import Path

import pytest

from humansearch.admin_weekly_dashboard.contracts import MetricStatus, SourceFailureReason
from humansearch.admin_weekly_dashboard.source_policy import (
    CalendarReference,
    CandidateIdentityEvidence,
    CandidateLinkDecision,
    candidate_link_decision,
    collection_state,
    load_source_policy,
    resolve_calendar_alias,
)

SOURCE_CONTRACT = (
    Path(__file__).parents[2]
    / "contracts"
    / "admin-weekly-dashboard"
    / "source-contract-v1.json"
)


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
