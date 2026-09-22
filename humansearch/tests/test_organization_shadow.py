from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from dataclasses import replace
from datetime import UTC, date, datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest
from hypothesis import given
from hypothesis import strategies as st

from humansearch.organization_reference import (
    CohortKey,
    EmploymentStatus,
    PatternSnapshot,
    PatternStatus,
    ReferenceObservation,
    RoleEvidence,
    build_pattern_snapshot,
)
from humansearch.organization_shadow import (
    HumanReviewStatus,
    SemanticStatus,
    build_semantic_state,
    load_shadow_config,
    run_shadow_review,
    semantic_input_hash,
)
from humansearch.organization_shadow_jev import TypeSafeJevJudge
from humansearch.recruiting_review import (
    Criterion,
    CriterionStatus,
    Recommendation,
    ReviewResult,
    review_candidate,
)

CONFIG_PATH = Path(__file__).parents[2] / "contracts/jev-org-reference-shadow.json"
COHORT = CohortKey("company-synthetic-001", "backend_platform", "senior", "payments")


def role_evidence(*, suffix: str = "") -> RoleEvidence:
    return RoleEvidence(
        primary_role_family="backend_platform",
        responsibilities=(f"design service boundaries{suffix}",),
        ownership_scope=(f"own service lifecycle{suffix}",),
        production_operating=(f"operate production services{suffix}",),
        product_stage=(f"scale a growing product{suffix}",),
        domain_problems=(f"reduce transaction failures{suffix}",),
        technical_environment=(f"distributed service constraints{suffix}",),
    )


def observation(
    person_id: str,
    *,
    observation_id: str | None = None,
    observed_on: date = date(2026, 9, 1),
    evidence: RoleEvidence | None = None,
    cohort: CohortKey = COHORT,
) -> ReferenceObservation:
    item_id = observation_id or f"obs-{person_id}"
    return ReferenceObservation(
        observation_id=item_id,
        person_id=person_id,
        cohort=cohort,
        employment_status=EmploymentStatus.CURRENT,
        observation_date=observed_on,
        source_timestamp=datetime(2026, 9, 1, tzinfo=UTC),
        evidence_ids=(f"evidence-{item_id}",),
        role_evidence=evidence or role_evidence(),
    )


def snapshot(*items: ReferenceObservation) -> PatternSnapshot:
    config = load_shadow_config(CONFIG_PATH)
    return build_pattern_snapshot(
        items,
        as_of=date(2026, 9, 22),
        known_denominator=8,
        pattern_version=config.pattern_version,
        minimum_cohort_size=config.minimum_cohort_size,
        minimum_distinct_people=config.minimum_distinct_people,
        stale_after_days=config.stale_after_days,
    )


def a_review() -> ReviewResult:
    return review_candidate(
        criteria=(
            Criterion(
                "backend",
                "Backend ownership",
                70,
                CriterionStatus.MET,
                required=True,
                evidence=("Owned a production service",),
            ),
            Criterion("growth", "Growth-stage experience", 30, CriterionStatus.UNKNOWN),
        ),
        input_fingerprint={"jd_id": "synthetic-jd-001"},
    )


def successful_response() -> dict[str, Any]:
    config = load_shadow_config(CONFIG_PATH)
    answers: dict[str, object] = {}
    for name, question in config.questions.items():
        primitive = question["type"]
        if primitive == "choice":
            choices = list(question["criteria"])
            probabilities = {choice: 0.0 for choice in choices}
            probabilities["same_role_family"] = 1.0
            answers[name] = {
                "type": "choice",
                "choice": "same_role_family",
                "probabilities": probabilities,
                "confidence": 1.0,
            }
        elif primitive == "score":
            criteria = question["criteria"]
            answers[name] = {
                "type": "score",
                "score": 2.0,
                "legend": {str(index): value for index, value in enumerate(criteria)},
                "probabilities": {
                    str(index): 1.0 if index == 2 else 0.0 for index in range(len(criteria))
                },
                "confidence": 0.9,
            }
        else:
            answers[name] = {
                "type": "noul",
                "noul": 0.9 if name == "direct_evidence_present" else 0.1,
            }
    return {
        "model": config.model_version,
        "answers": answers,
        "usage": {"input_tokens": 100, "output_tokens": 20},
    }


class FakeJudge:
    def __init__(self, response: Mapping[str, object] | Exception) -> None:
        self.response = response
        self.state: Mapping[str, object] | None = None

    def evaluate(
        self,
        *,
        state: Mapping[str, object],
        questions: Mapping[str, Mapping[str, Any]],
        model: str,
        timeout_seconds: float,
    ) -> Mapping[str, object]:
        assert questions
        assert model == "jev-1.13.0"
        assert timeout_seconds == 10.0
        self.state = state
        if isinstance(self.response, Exception):
            raise self.response
        return self.response


def test_reference_cohort_schema_and_pattern_aggregation() -> None:
    result = snapshot(observation("person-a"), observation("person-b"), observation("person-c"))

    assert result.cohort == COHORT
    assert result.sample_size == 3
    assert result.known_denominator == 8
    assert result.status is PatternStatus.READY
    assert result.canonical_input_hash
    assert {item.category for item in result.repeated_patterns} == {
        "primary_role_family",
        "responsibilities",
        "ownership_scope",
        "production_operating",
        "product_stage",
        "domain_problems",
        "technical_environment",
    }
    assert all(item.distinct_people == 3 for item in result.repeated_patterns)


def test_duplicate_person_does_not_create_repeated_pattern_or_inflate_sample() -> None:
    result = snapshot(
        observation("person-a", observation_id="obs-a-1"),
        observation("person-a", observation_id="obs-a-2"),
    )

    assert result.sample_size == 1
    assert result.status is PatternStatus.LIMITED
    assert result.repeated_patterns == ()
    assert result.single_observations
    assert all(item.distinct_people == 1 for item in result.single_observations)


def test_small_or_empty_sample_is_never_promoted_to_company_pattern() -> None:
    one = snapshot(observation("person-a"))
    empty = snapshot()

    assert one.status is PatternStatus.LIMITED
    assert empty.status is PatternStatus.NO_EVIDENCE
    assert one.cohort.role_family == "backend_platform"
    assert not hasattr(one, "company_wide_pattern")


def test_mixed_company_role_or_seniority_cohort_is_rejected() -> None:
    mixed = CohortKey("company-synthetic-002", "data", "lead", None)
    with pytest.raises(ValueError, match="single cohort"):
        snapshot(observation("person-a"), observation("person-b", cohort=mixed))


def test_stale_and_conflicting_observations_do_not_become_repeated_patterns() -> None:
    old = observation("person-a", observed_on=date(2025, 1, 1))
    conflicting = observation(
        "person-b",
        observation_id="shared-observation",
        evidence=role_evidence(suffix=" first"),
    )
    conflicting_copy = observation(
        "person-c",
        observation_id="shared-observation",
        evidence=role_evidence(suffix=" conflicting"),
    )
    result = snapshot(old, conflicting, conflicting_copy)

    assert "obs-person-a" in result.stale_observation_ids
    assert "shared-observation" in result.conflicts
    assert result.repeated_patterns == ()


def test_hash_is_stable_and_changes_with_pattern_or_question_version() -> None:
    config = load_shadow_config(CONFIG_PATH)
    pattern = snapshot(observation("person-a"), observation("person-b"), observation("person-c"))

    first = semantic_input_hash(
        a_review=a_review(),
        jd_evidence=role_evidence(suffix=" jd"),
        candidate_evidence=role_evidence(suffix=" candidate"),
        pattern_snapshot=pattern,
        config=config,
    )
    second = semantic_input_hash(
        a_review=a_review(),
        jd_evidence=role_evidence(suffix=" jd"),
        candidate_evidence=role_evidence(suffix=" candidate"),
        pattern_snapshot=pattern,
        config=config,
    )
    changed_questions = replace(config, question_version="org-shadow-questions-v2")
    changed = semantic_input_hash(
        a_review=a_review(),
        jd_evidence=role_evidence(suffix=" jd"),
        candidate_evidence=role_evidence(suffix=" candidate"),
        pattern_snapshot=pattern,
        config=changed_questions,
    )

    assert first == second
    assert changed != first
    assert len(first) == 64


def test_hash_changes_when_atomic_question_text_changes() -> None:
    config = load_shadow_config(CONFIG_PATH)
    questions = {name: dict(question) for name, question in config.questions.items()}
    question = questions["ownership_scope_similarity"]
    question["instructions"] = f"{question['instructions']} revised"
    changed = replace(config, questions=questions)
    pattern = snapshot(observation("person-a"), observation("person-b"), observation("person-c"))

    baseline = semantic_input_hash(
        a_review=a_review(),
        jd_evidence=role_evidence(suffix=" jd"),
        candidate_evidence=role_evidence(suffix=" candidate"),
        pattern_snapshot=pattern,
        config=config,
    )
    revised = semantic_input_hash(
        a_review=a_review(),
        jd_evidence=role_evidence(suffix=" jd"),
        candidate_evidence=role_evidence(suffix=" candidate"),
        pattern_snapshot=pattern,
        config=changed,
    )

    assert revised != baseline


def test_semantic_state_excludes_identity_and_demographic_proxies() -> None:
    pattern = snapshot(observation("person-a"), observation("person-b"), observation("person-c"))
    state = build_semantic_state(
        jd_evidence=role_evidence(suffix=" jd"),
        candidate_evidence=role_evidence(suffix=" candidate"),
        pattern_snapshot=pattern,
    )
    encoded = repr(state).casefold()

    assert COHORT.canonical_company_id not in encoded
    assert "person-a" not in encoded
    assert "evidence-" not in encoded
    for forbidden in ("company_name", "school", "gender", "age", "nationality"):
        assert forbidden not in encoded


def test_role_evidence_rejects_forbidden_or_unknown_fields_at_runtime() -> None:
    with pytest.raises(TypeError):
        RoleEvidence(
            primary_role_family="backend_platform",
            responsibilities=(),
            ownership_scope=(),
            production_operating=(),
            product_stage=(),
            domain_problems=(),
            technical_environment=(),
            company_name="prestige-brand",
        )  # type: ignore[call-arg]


def test_completed_shadow_keeps_a_review_unchanged_and_separates_b_c_d() -> None:
    config = load_shadow_config(CONFIG_PATH)
    original = a_review()
    judge = FakeJudge(successful_response())
    result = run_shadow_review(
        a_review=original,
        jd_evidence=role_evidence(suffix=" jd"),
        candidate_evidence=role_evidence(suffix=" candidate"),
        pattern_snapshot=snapshot(
            observation("person-a"), observation("person-b"), observation("person-c")
        ),
        config=config,
        judge=judge,
    )

    assert result.a_review == original
    assert result.a_review.score.score == 70
    assert result.a_review.recommendation is Recommendation.REVIEW
    assert result.semantic.status is SemanticStatus.COMPLETED
    assert result.semantic.organization_similarity["classification"] == "high"
    assert result.semantic.transferable_experience["classification"] == "high"
    assert result.semantic.human_review_status is HumanReviewStatus.NOT_REQUIRED
    assert set(result.semantic.primitive_answers) == set(config.questions)


def test_low_organization_similarity_cannot_change_a_score_gate_or_recommendation() -> None:
    config = load_shadow_config(CONFIG_PATH)
    original = a_review()
    response = successful_response()
    for name, answer in response["answers"].items():
        if answer["type"] == "score" and name != "transferable_experience_strength":
            answer["score"] = 0.0
            answer["probabilities"] = {str(index): 1.0 if index == 0 else 0.0 for index in range(4)}
    result = run_shadow_review(
        a_review=original,
        jd_evidence=role_evidence(suffix=" jd"),
        candidate_evidence=role_evidence(suffix=" candidate"),
        pattern_snapshot=snapshot(
            observation("person-a"), observation("person-b"), observation("person-c")
        ),
        config=config,
        judge=FakeJudge(response),
    )

    assert result.a_review == original
    assert result.a_review.gate == original.gate
    assert result.a_review.score == original.score
    assert result.a_review.recommendation == original.recommendation
    assert result.semantic.organization_similarity["classification"] == "low"


def test_disabled_judge_returns_not_run_without_changing_a_review() -> None:
    config = load_shadow_config(CONFIG_PATH)
    original = a_review()
    result = run_shadow_review(
        a_review=original,
        jd_evidence=role_evidence(suffix=" jd"),
        candidate_evidence=role_evidence(suffix=" candidate"),
        pattern_snapshot=snapshot(observation("person-a")),
        config=config,
        judge=None,
    )

    assert result.a_review == original
    assert result.semantic.status is SemanticStatus.NOT_RUN
    assert result.semantic.error_code == "judge_disabled_or_api_key_missing"
    assert result.semantic.primitive_answers == {}
    assert result.semantic.human_review_status is HumanReviewStatus.NOT_RUN


def test_judge_error_returns_error_without_changing_a_review() -> None:
    config = load_shadow_config(CONFIG_PATH)
    original = a_review()
    result = run_shadow_review(
        a_review=original,
        jd_evidence=role_evidence(suffix=" jd"),
        candidate_evidence=role_evidence(suffix=" candidate"),
        pattern_snapshot=snapshot(observation("person-a")),
        config=config,
        judge=FakeJudge(TimeoutError("private response body must not leak")),
    )

    assert result.a_review == original
    assert result.semantic.status is SemanticStatus.ERROR
    assert result.semantic.error_code == "judge_call_failed"
    assert "private response" not in repr(result.semantic)


@pytest.mark.parametrize(
    "mutate",
    (
        lambda body: body["answers"].pop("primary_role_family"),
        lambda body: body["answers"]["ownership_scope_similarity"].update(score=9.0),
        lambda body: body["answers"]["primary_role_family"].update(choice="unknown-choice"),
        lambda body: body["answers"]["direct_evidence_present"].update(confidence=0.9),
        lambda body: body.update(model="jev-latest"),
    ),
)
def test_invalid_jev_response_is_explicit_and_never_successful(
    mutate: Callable[[dict[str, Any]], object],
) -> None:
    config = load_shadow_config(CONFIG_PATH)
    response = successful_response()
    mutate(response)
    result = run_shadow_review(
        a_review=a_review(),
        jd_evidence=role_evidence(suffix=" jd"),
        candidate_evidence=role_evidence(suffix=" candidate"),
        pattern_snapshot=snapshot(
            observation("person-a"), observation("person-b"), observation("person-c")
        ),
        config=config,
        judge=FakeJudge(response),
    )

    assert result.semantic.status is SemanticStatus.INVALID_RESPONSE
    assert result.semantic.error_code == "judge_response_invalid"
    assert result.semantic.primitive_answers == {}


def test_official_sdk_adapter_returns_raw_shape_for_strict_validation() -> None:
    response = successful_response()
    response["answers"]["direct_evidence_present"]["confidence"] = 0.9

    class FakeSdkClient:
        def __init__(self) -> None:
            self.call: dict[str, object] = {}

        def system_one(
            self,
            state: object,
            questions: object,
            *,
            model: str,
            timeout: float,
        ) -> object:
            self.call = {
                "state": state,
                "questions": questions,
                "model": model,
                "timeout": timeout,
            }
            raw_http_response = SimpleNamespace(content=json.dumps(response).encode())
            return SimpleNamespace(raw_http_response=raw_http_response)

    client = FakeSdkClient()
    adapter = TypeSafeJevJudge(client=cast(Any, client))
    raw = adapter.evaluate(
        state={"role": "synthetic"},
        questions=load_shadow_config(CONFIG_PATH).questions,
        model="jev-1.13.0",
        timeout_seconds=10.0,
    )

    raw_answers = cast(Mapping[str, Mapping[str, object]], raw["answers"])
    assert raw_answers["direct_evidence_present"]["confidence"] == 0.9
    assert client.call["model"] == "jev-1.13.0"
    assert client.call["timeout"] == 10.0


@given(extra_duplicates=st.integers(min_value=0, max_value=12))
def test_duplicate_observations_never_increase_unique_sample_or_repeat_count(
    extra_duplicates: int,
) -> None:
    items = [
        observation("person-a", observation_id=f"obs-{index}")
        for index in range(extra_duplicates + 1)
    ]
    result = snapshot(*items)

    assert result.sample_size == 1
    assert result.repeated_patterns == ()
