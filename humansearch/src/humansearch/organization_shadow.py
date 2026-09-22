"""Non-gating semantic shadow review contracts."""

import hashlib
import json
import math
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any, Protocol

from humansearch.organization_reference import PatternSnapshot, RoleEvidence
from humansearch.organization_shadow_validation import validate_response
from humansearch.recruiting_review import ReviewResult


class SemanticStatus(StrEnum):
    COMPLETED = "completed"
    NOT_RUN = "not_run"
    ERROR = "error"
    INVALID_RESPONSE = "invalid_response"


class HumanReviewStatus(StrEnum):
    REQUIRED = "required"
    RECOMMENDED = "recommended"
    NOT_REQUIRED = "not_required"
    NOT_RUN = "not_run"


@dataclass(frozen=True, slots=True)
class ShadowConfig:
    schema_version: str
    model_version: str
    question_version: str
    threshold_version: str
    pattern_version: str
    timeout_seconds: float
    minimum_cohort_size: int
    minimum_distinct_people: int
    stale_after_days: int
    score_low_max: float
    score_high_min: float
    confidence_floor: float
    direct_evidence_present: float
    requires_human_verification: float
    questions: Mapping[str, Mapping[str, Any]]


@dataclass(frozen=True, slots=True)
class SemanticReview:
    status: SemanticStatus
    model_version: str
    question_version: str
    threshold_version: str
    pattern_version: str
    input_hash: str
    organization_similarity: Mapping[str, object]
    transferable_experience: Mapping[str, object]
    additional_checks: Mapping[str, object]
    primitive_answers: Mapping[str, Mapping[str, object]]
    human_review_status: HumanReviewStatus
    error_code: str | None = None


@dataclass(frozen=True, slots=True)
class ShadowReviewResult:
    schema_version: str
    a_review: ReviewResult
    semantic: SemanticReview


class SemanticJudge(Protocol):
    def evaluate(
        self,
        *,
        state: Mapping[str, object],
        questions: Mapping[str, Mapping[str, Any]],
        model: str,
        timeout_seconds: float,
    ) -> Mapping[str, object]: ...


def load_shadow_config(path: Path) -> ShadowConfig:
    """Load the single versioned model/question/threshold contract."""

    raw = json.loads(path.read_text(encoding="utf-8"))
    root = _mapping(raw, "config")
    _exact_keys(
        root,
        {
            "schema_version",
            "model_version",
            "question_version",
            "threshold_version",
            "pattern_version",
            "timeout_seconds",
            "pattern",
            "thresholds",
            "questions",
        },
        "config",
    )
    pattern = _mapping(root["pattern"], "pattern")
    thresholds = _mapping(root["thresholds"], "thresholds")
    _exact_keys(
        pattern,
        {"minimum_cohort_size", "minimum_distinct_people", "stale_after_days"},
        "pattern",
    )
    _exact_keys(
        thresholds,
        {
            "score_low_max",
            "score_high_min",
            "confidence_floor",
            "direct_evidence_present",
            "requires_human_verification",
        },
        "thresholds",
    )
    questions = _validate_questions(_mapping(root["questions"], "questions"))
    model = _text(root["model_version"], "model_version")
    if not _is_pinned_jev_model(model):
        raise ValueError("model_version must be a pinned Jev release")
    config = ShadowConfig(
        schema_version=_text(root["schema_version"], "schema_version"),
        model_version=model,
        question_version=_text(root["question_version"], "question_version"),
        threshold_version=_text(root["threshold_version"], "threshold_version"),
        pattern_version=_text(root["pattern_version"], "pattern_version"),
        timeout_seconds=_positive_number(root["timeout_seconds"], "timeout_seconds"),
        minimum_cohort_size=_positive_int(pattern["minimum_cohort_size"], "minimum_cohort_size"),
        minimum_distinct_people=_positive_int(
            pattern["minimum_distinct_people"], "minimum_distinct_people"
        ),
        stale_after_days=_nonnegative_int(pattern["stale_after_days"], "stale_after_days"),
        score_low_max=_probability(thresholds["score_low_max"], "score_low_max", upper=3.0),
        score_high_min=_probability(thresholds["score_high_min"], "score_high_min", upper=3.0),
        confidence_floor=_probability(thresholds["confidence_floor"], "confidence_floor"),
        direct_evidence_present=_probability(
            thresholds["direct_evidence_present"], "direct_evidence_present"
        ),
        requires_human_verification=_probability(
            thresholds["requires_human_verification"], "requires_human_verification"
        ),
        questions=questions,
    )
    if config.minimum_distinct_people < 2:
        raise ValueError("minimum_distinct_people must be at least two")
    if config.score_low_max >= config.score_high_min:
        raise ValueError("score thresholds overlap")
    return config


def semantic_input_hash(
    *,
    a_review: ReviewResult,
    jd_evidence: RoleEvidence,
    candidate_evidence: RoleEvidence,
    pattern_snapshot: PatternSnapshot,
    config: ShadowConfig,
) -> str:
    if pattern_snapshot.pattern_version != config.pattern_version:
        raise ValueError("pattern snapshot version does not match config")
    payload = {
        "schema_version": "organization-shadow-input-v1",
        "a_review": _a_review_payload(a_review),
        "state": build_semantic_state(
            jd_evidence=jd_evidence,
            candidate_evidence=candidate_evidence,
            pattern_snapshot=pattern_snapshot,
        ),
        "pattern_input_hash": pattern_snapshot.canonical_input_hash,
        "model_version": config.model_version,
        "question_version": config.question_version,
        "threshold_version": config.threshold_version,
        "pattern_version": config.pattern_version,
        "questions": config.questions,
        "thresholds": _threshold_payload(config),
    }
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()


def build_semantic_state(
    *,
    jd_evidence: RoleEvidence,
    candidate_evidence: RoleEvidence,
    pattern_snapshot: PatternSnapshot,
) -> Mapping[str, object]:
    return {
        "jd_evidence": _role_evidence_payload(jd_evidence),
        "candidate_evidence": _role_evidence_payload(candidate_evidence),
        "reference_pattern": {
            "status": pattern_snapshot.status.value,
            "role_family": pattern_snapshot.cohort.role_family,
            "seniority": pattern_snapshot.cohort.seniority,
            "team_product_scope": pattern_snapshot.cohort.team_product_scope,
            "sample_size": pattern_snapshot.sample_size,
            "known_denominator": pattern_snapshot.known_denominator,
            "patterns": [
                {
                    "category": _state_category(item.category),
                    "value": item.value,
                    "distinct_people": item.distinct_people,
                }
                for item in pattern_snapshot.repeated_patterns
            ],
            "limitations": {
                "single_observation_count": len(pattern_snapshot.single_observations),
                "conflict_count": len(pattern_snapshot.conflicts),
                "stale_observation_count": len(pattern_snapshot.stale_observation_ids),
            },
        },
    }


def run_shadow_review(
    *,
    a_review: ReviewResult,
    jd_evidence: RoleEvidence,
    candidate_evidence: RoleEvidence,
    pattern_snapshot: PatternSnapshot,
    config: ShadowConfig,
    judge: SemanticJudge | None,
) -> ShadowReviewResult:
    """Return A unchanged and B/C/D as an isolated shadow observation."""

    input_hash = semantic_input_hash(
        a_review=a_review,
        jd_evidence=jd_evidence,
        candidate_evidence=candidate_evidence,
        pattern_snapshot=pattern_snapshot,
        config=config,
    )
    if judge is None:
        semantic = _empty_review(
            config=config,
            input_hash=input_hash,
            pattern_snapshot=pattern_snapshot,
            status=SemanticStatus.NOT_RUN,
            error_code="judge_disabled_or_api_key_missing",
        )
        return ShadowReviewResult("organization-shadow-review-v1", a_review, semantic)
    state = build_semantic_state(
        jd_evidence=jd_evidence,
        candidate_evidence=candidate_evidence,
        pattern_snapshot=pattern_snapshot,
    )
    try:
        raw = judge.evaluate(
            state=state,
            questions=config.questions,
            model=config.model_version,
            timeout_seconds=config.timeout_seconds,
        )
    except Exception:  # noqa: BLE001 - the judge boundary must preserve deterministic A on any failure.
        semantic = _empty_review(
            config=config,
            input_hash=input_hash,
            pattern_snapshot=pattern_snapshot,
            status=SemanticStatus.ERROR,
            error_code="judge_call_failed",
        )
        return ShadowReviewResult("organization-shadow-review-v1", a_review, semantic)
    try:
        answers = validate_response(
            raw,
            questions=config.questions,
            model_version=config.model_version,
        )
    except KeyError, TypeError, ValueError:
        semantic = _empty_review(
            config=config,
            input_hash=input_hash,
            pattern_snapshot=pattern_snapshot,
            status=SemanticStatus.INVALID_RESPONSE,
            error_code="judge_response_invalid",
        )
        return ShadowReviewResult("organization-shadow-review-v1", a_review, semantic)
    semantic = _completed_review(
        config=config,
        input_hash=input_hash,
        pattern_snapshot=pattern_snapshot,
        answers=answers,
    )
    return ShadowReviewResult("organization-shadow-review-v1", a_review, semantic)


def _validate_questions(raw: Mapping[str, object]) -> Mapping[str, Mapping[str, Any]]:
    expected = {
        "primary_role_family": "choice",
        "ownership_scope_similarity": "score",
        "production_operating_similarity": "score",
        "product_stage_similarity": "score",
        "domain_problem_similarity": "score",
        "technical_environment_similarity": "score",
        "transferable_experience_strength": "score",
        "direct_evidence_present": "noul",
        "requires_human_verification": "noul",
    }
    _exact_keys(raw, set(expected), "questions")
    validated: dict[str, Mapping[str, Any]] = {}
    for name, value in raw.items():
        question = _mapping(value, f"questions.{name}")
        _exact_keys(question, {"type", "instructions", "criteria"}, f"questions.{name}")
        primitive = _text(question["type"], f"questions.{name}.type")
        if primitive != expected[name]:
            raise ValueError("question primitive differs from the atomic contract")
        _text(question["instructions"], f"questions.{name}.instructions")
        _validate_question_criteria(name, primitive, question["criteria"])
        validated[name] = dict(question)
    return validated


def _validate_question_criteria(name: str, primitive: str, raw: object) -> None:
    if primitive == "score":
        if not isinstance(raw, list) or not raw or any(not isinstance(item, str) for item in raw):
            raise ValueError(f"questions.{name}.criteria must be a nonempty string list")
        return
    criteria = _mapping(raw, f"questions.{name}.criteria")
    if not criteria or any(
        not isinstance(key, str) or not isinstance(value, str) for key, value in criteria.items()
    ):
        raise ValueError(f"questions.{name}.criteria must be a nonempty string mapping")
    if primitive == "noul" and set(criteria) != {"true", "false"}:
        raise ValueError(f"questions.{name}.criteria must contain true and false")


def _completed_review(
    *,
    config: ShadowConfig,
    input_hash: str,
    pattern_snapshot: PatternSnapshot,
    answers: Mapping[str, Mapping[str, object]],
) -> SemanticReview:
    organization_names = (
        "ownership_scope_similarity",
        "production_operating_similarity",
        "product_stage_similarity",
        "domain_problem_similarity",
        "technical_environment_similarity",
    )
    organization_scores = [_score(answers[name]) for name in organization_names]
    organization_mean = sum(organization_scores) / len(organization_scores)
    transfer_score = _score(answers["transferable_experience_strength"])
    direct = _number(answers["direct_evidence_present"]["noul"], "direct evidence")
    verify = _number(answers["requires_human_verification"]["noul"], "human verification")
    review_status = _human_review_status(
        config=config,
        pattern_snapshot=pattern_snapshot,
        answers=answers,
        direct=direct,
        verify=verify,
    )
    return SemanticReview(
        status=SemanticStatus.COMPLETED,
        model_version=config.model_version,
        question_version=config.question_version,
        threshold_version=config.threshold_version,
        pattern_version=config.pattern_version,
        input_hash=input_hash,
        organization_similarity={
            "classification": _score_classification(organization_mean, config),
            "mean_score": round(organization_mean, 4),
            "primary_role_family": answers["primary_role_family"]["choice"],
            "scores": {name: _score(answers[name]) for name in organization_names},
        },
        transferable_experience={
            "classification": _score_classification(transfer_score, config),
            "score": transfer_score,
        },
        additional_checks=_additional_checks(pattern_snapshot, direct=direct, verify=verify),
        primitive_answers=answers,
        human_review_status=review_status,
    )


def _empty_review(
    *,
    config: ShadowConfig,
    input_hash: str,
    pattern_snapshot: PatternSnapshot,
    status: SemanticStatus,
    error_code: str,
) -> SemanticReview:
    return SemanticReview(
        status=status,
        model_version=config.model_version,
        question_version=config.question_version,
        threshold_version=config.threshold_version,
        pattern_version=config.pattern_version,
        input_hash=input_hash,
        organization_similarity={},
        transferable_experience={},
        additional_checks=_additional_checks(pattern_snapshot),
        primitive_answers={},
        human_review_status=HumanReviewStatus.NOT_RUN,
        error_code=error_code,
    )


def _human_review_status(
    *,
    config: ShadowConfig,
    pattern_snapshot: PatternSnapshot,
    answers: Mapping[str, Mapping[str, object]],
    direct: float,
    verify: float,
) -> HumanReviewStatus:
    if (
        pattern_snapshot.status.value != "ready"
        or direct < config.direct_evidence_present
        or verify >= config.requires_human_verification
    ):
        return HumanReviewStatus.REQUIRED
    confidences = [
        _number(answer["confidence"], "confidence")
        for answer in answers.values()
        if "confidence" in answer
    ]
    if any(value < config.confidence_floor for value in confidences):
        return HumanReviewStatus.RECOMMENDED
    return HumanReviewStatus.NOT_REQUIRED


def _additional_checks(
    pattern_snapshot: PatternSnapshot,
    *,
    direct: float | None = None,
    verify: float | None = None,
) -> Mapping[str, object]:
    return {
        "pattern_status": pattern_snapshot.status.value,
        "sample_size": pattern_snapshot.sample_size,
        "known_denominator": pattern_snapshot.known_denominator,
        "single_observation_count": len(pattern_snapshot.single_observations),
        "conflict_count": len(pattern_snapshot.conflicts),
        "stale_observation_count": len(pattern_snapshot.stale_observation_ids),
        "direct_evidence_present": direct,
        "requires_human_verification": verify,
    }


def _score_classification(value: float, config: ShadowConfig) -> str:
    if value <= config.score_low_max:
        return "low"
    if value >= config.score_high_min:
        return "high"
    return "medium"


def _score(answer: Mapping[str, object]) -> float:
    return _number(answer["score"], "score")


def _a_review_payload(review: ReviewResult) -> Mapping[str, object]:
    return {
        "schema_version": review.schema_version,
        "input_hash": review.input_hash,
        "gate": {
            "failed_required": review.gate.failed_required,
            "unknown_required": review.gate.unknown_required,
        },
        "score": {
            "score": review.score.score,
            "scored_weight": review.score.scored_weight,
            "unknown_weight": review.score.unknown_weight,
            "details": [
                {
                    "key": item.key,
                    "status": item.status.value,
                    "weight": item.weight,
                    "earned": item.earned,
                    "required": item.required,
                    "evidence": item.evidence,
                }
                for item in review.score.details
            ],
        },
        "recommendation": review.recommendation.value,
        "relevant_experience_months": review.relevant_experience_months,
    }


def _role_evidence_payload(evidence: RoleEvidence) -> Mapping[str, object]:
    return {
        "primary_role_family": evidence.primary_role_family,
        "responsibilities": evidence.responsibilities,
        "ownership_scope": evidence.ownership_scope,
        "production_operating": evidence.production_operating,
        "product_phase": evidence.product_stage,
        "domain_problems": evidence.domain_problems,
        "technical_environment": evidence.technical_environment,
    }


def _state_category(category: str) -> str:
    return "product_phase" if category == "product_stage" else category


def _threshold_payload(config: ShadowConfig) -> Mapping[str, float]:
    return {
        "score_low_max": config.score_low_max,
        "score_high_min": config.score_high_min,
        "confidence_floor": config.confidence_floor,
        "direct_evidence_present": config.direct_evidence_present,
        "requires_human_verification": config.requires_human_verification,
    }


def _mapping(value: object, field: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping) or any(not isinstance(key, str) for key in value):
        raise ValueError(f"{field} must be an object with string keys")
    return value


def _exact_keys(value: Mapping[str, object], expected: set[str], field: str) -> None:
    if set(value) != expected:
        raise ValueError(f"{field} has missing or unknown fields")


def _text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a nonempty string")
    return value


def _number(value: object, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float) or not math.isfinite(value):
        raise ValueError(f"{field} must be a finite number")
    return float(value)


def _positive_number(value: object, field: str) -> float:
    result = _number(value, field)
    if result <= 0:
        raise ValueError(f"{field} must be positive")
    return result


def _probability(value: object, field: str, *, upper: float = 1.0) -> float:
    result = _number(value, field)
    if result < 0 or result > upper:
        raise ValueError(f"{field} is outside its allowed range")
    return result


def _nonnegative_int(value: object, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{field} must be a non-negative integer")
    return value


def _positive_int(value: object, field: str) -> int:
    result = _nonnegative_int(value, field)
    if result == 0:
        raise ValueError(f"{field} must be positive")
    return result


def _is_pinned_jev_model(value: str) -> bool:
    parts = value.removeprefix("jev-").split(".")
    return value.startswith("jev-") and len(parts) == 3 and all(part.isdigit() for part in parts)
