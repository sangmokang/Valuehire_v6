import math
from datetime import date

import pytest
from hypothesis import given
from hypothesis import strategies as st

from humansearch.recruiting_review import (
    Criterion,
    CriterionStatus,
    ExperiencePeriod,
    Recommendation,
    review_candidate,
    union_experience_months,
)


def test_required_failure_excludes_even_when_weighted_score_is_high() -> None:
    result = review_candidate(
        criteria=(
            Criterion(
                "backend",
                "Backend context",
                50,
                CriterionStatus.MET,
                required=False,
                evidence=("Built B2B APIs",),
            ),
            Criterion(
                "python",
                "Python/FastAPI",
                49,
                CriterionStatus.MET,
                required=False,
                evidence=("FastAPI production service",),
            ),
            Criterion(
                "required_years",
                "5+ relevant years",
                1,
                CriterionStatus.UNMET,
                required=True,
            ),
        )
    )

    assert result.score.score > 95
    assert result.gate.failed_required == ("required_years",)
    assert result.recommendation is Recommendation.EXCLUDED


def test_unknown_required_condition_needs_confirmation_and_keeps_unknown_weight() -> None:
    result = review_candidate(
        criteria=(
            Criterion(
                "job_context",
                "B2B SaaS backend",
                95,
                CriterionStatus.MET,
                required=True,
                evidence=("Owned SaaS API modules",),
            ),
            Criterion(
                "degree",
                "Education requirement",
                5,
                CriterionStatus.UNKNOWN,
                required=True,
            ),
        )
    )

    assert result.recommendation is Recommendation.NEEDS_CONFIRMATION
    assert result.gate.unknown_required == ("degree",)
    assert result.score.score == 95.0
    assert result.score.unknown_weight == 5


def test_unknown_weight_counts_as_zero_in_score_denominator() -> None:
    result = review_candidate(
        criteria=(
            Criterion(
                "confirmed",
                "Confirmed narrow signal",
                5,
                CriterionStatus.MET,
                evidence=("Confirmed signal",),
            ),
            Criterion("missing_context", "Unverified core context", 95, CriterionStatus.UNKNOWN),
        )
    )

    assert result.score.score == 5
    assert result.score.scored_weight == 100
    assert result.score.unknown_weight == 95
    assert result.recommendation is Recommendation.HOLD


def test_required_partial_condition_needs_confirmation() -> None:
    result = review_candidate(
        criteria=(
            Criterion(
                "equivalent_experience",
                "5 years or equivalent experience",
                15,
                CriterionStatus.PARTIAL,
                required=True,
                evidence=("Equivalent ownership is plausible but not confirmed",),
            ),
            Criterion(
                "role_context",
                "Backend platform context",
                85,
                CriterionStatus.MET,
                required=False,
                evidence=("Backend platform work",),
            ),
        )
    )

    assert result.gate.unknown_required == ("equivalent_experience",)
    assert result.recommendation is Recommendation.NEEDS_CONFIRMATION


def test_partial_and_met_criteria_must_have_evidence() -> None:
    with pytest.raises(ValueError, match="needs evidence"):
        review_candidate(
            criteria=(
                Criterion(
                    "ai",
                    "AI product experience",
                    30,
                    CriterionStatus.PARTIAL,
                    required=False,
                ),
            )
        )


@pytest.mark.parametrize("evidence", (("",), ("   ",), (object(),)))
def test_partial_and_met_criteria_reject_blank_or_non_string_evidence(
    evidence: tuple[object, ...]
) -> None:
    with pytest.raises(ValueError, match="invalid evidence"):
        review_candidate(
            criteria=(
                Criterion(
                    "ai",
                    "AI product experience",
                    30,
                    CriterionStatus.MET,
                    required=False,
                    evidence=evidence,  # type: ignore[arg-type]
                ),
            )
        )


def test_empty_criteria_are_rejected() -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        review_candidate(criteria=())


def test_duplicate_criterion_keys_are_rejected() -> None:
    with pytest.raises(ValueError, match="duplicate criterion key"):
        review_candidate(
            criteria=(
                Criterion(
                    "backend",
                    "Backend context",
                    35,
                    CriterionStatus.MET,
                    evidence=("API work",),
                ),
                Criterion(
                    "backend",
                    "Duplicate backend context",
                    5,
                    CriterionStatus.UNKNOWN,
                ),
            )
        )


@pytest.mark.parametrize("weight", (math.nan, math.inf, -math.inf))
def test_non_finite_weights_are_rejected(weight: float) -> None:
    with pytest.raises(ValueError, match="invalid weight"):
        review_candidate(
            criteria=(
                Criterion(
                    "backend",
                    "Backend context",
                    weight,
                    CriterionStatus.MET,
                    evidence=("API work",),
                ),
            )
        )


@pytest.mark.parametrize("weights", ((60,), (70, 40)), ids=["under_100", "over_100"])
def test_weights_that_do_not_sum_to_100_are_rejected(weights: tuple[int, ...]) -> None:
    # A partial table must not be renormalised into a 100-point priority recommendation.
    with pytest.raises(ValueError, match="must sum to 100"):
        review_candidate(
            criteria=tuple(
                Criterion(f"c{index}", f"Criterion {index}", weight, CriterionStatus.MET,
                          evidence=("Shipped it",))
                for index, weight in enumerate(weights)
            )
        )


def test_weights_summing_to_100_keep_the_existing_result() -> None:
    result = review_candidate(
        criteria=(
            Criterion("backend", "Backend context", 80, CriterionStatus.MET, evidence=("API work",)),
            Criterion("ai", "AI product experience", 20, CriterionStatus.UNMET),
        )
    )

    assert (result.score.score, result.score.scored_weight) == (80.0, 100)
    assert result.recommendation is Recommendation.REVIEW


def test_overlapping_relevant_experience_is_not_double_counted() -> None:
    months = union_experience_months(
        (
            ExperiencePeriod(date(2022, 1, 1), date(2023, 1, 1)),
            ExperiencePeriod(date(2022, 6, 1), date(2023, 6, 1)),
        )
    )

    assert months == 17


def test_experience_end_month_is_exclusive() -> None:
    assert union_experience_months(
        (ExperiencePeriod(date(2024, 1, 1), date(2024, 2, 1)),)
    ) == 1
    assert union_experience_months(
        (ExperiencePeriod(date(2024, 1, 1), date(2024, 1, 1)),)
    ) == 0


def test_reversed_experience_dates_are_rejected() -> None:
    with pytest.raises(ValueError, match="end precedes start"):
        union_experience_months((ExperiencePeriod(date(2024, 2, 1), date(2024, 1, 31)),))


def test_review_returns_stable_schema_version_and_input_hash() -> None:
    criteria = (
        Criterion(
            "role",
            "Role context",
            100,
            CriterionStatus.MET,
            required=True,
            evidence=("API platform lead",),
        ),
    )
    relevant_experience = (ExperiencePeriod(date(2021, 1, 1), date(2022, 1, 1)),)
    input_fingerprint = {"jd_url": "https://career.wrtn.io/ko/o/199492"}

    first = review_candidate(
        criteria=criteria,
        relevant_experience=relevant_experience,
        input_fingerprint=input_fingerprint,
    )
    second = review_candidate(
        criteria=criteria,
        relevant_experience=relevant_experience,
        input_fingerprint=input_fingerprint,
    )

    assert first.schema_version == "recruiting-review-v1"
    assert first.input_hash == second.input_hash
    assert len(first.input_hash) == 64


def test_review_hash_changes_when_input_changes() -> None:
    first = review_candidate(
        criteria=(
            Criterion(
                "role",
                "Role context",
                100,
                CriterionStatus.MET,
                required=True,
                evidence=("API platform lead",),
            ),
        ),
        input_fingerprint={"jd_url": "https://career.wrtn.io/ko/o/199492"},
    )
    second = review_candidate(
        criteria=(
            Criterion(
                "role",
                "Role context",
                100,
                CriterionStatus.MET,
                required=True,
                evidence=("API platform lead",),
            ),
        ),
        input_fingerprint={"jd_url": "https://career.wrtn.io/ko/o/119686"},
    )

    assert first.input_hash != second.input_hash


@given(
    starts=st.lists(st.integers(min_value=0, max_value=180), min_size=1, max_size=12),
    lengths=st.lists(st.integers(min_value=0, max_value=36), min_size=1, max_size=12),
)
def test_union_months_never_exceeds_sum_of_individual_months(
    starts: list[int], lengths: list[int]
) -> None:
    starts = starts[: len(lengths)]
    base_year = 2010
    periods = tuple(
        ExperiencePeriod(_month_date(base_year, start), _month_date(base_year, start + length))
        for start, length in zip(starts, lengths, strict=False)
    )

    union = union_experience_months(periods)
    individual_sum = sum(union_experience_months((period,)) for period in periods)

    assert union <= individual_sum


def _month_date(base_year: int, offset: int) -> date:
    year = base_year + offset // 12
    month = offset % 12 + 1
    return date(year, month, 1)
