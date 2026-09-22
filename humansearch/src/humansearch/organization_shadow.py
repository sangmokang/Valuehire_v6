"""Non-gating semantic shadow review contracts."""

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any, Protocol

from humansearch.organization_reference import PatternSnapshot, RoleEvidence
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

    raise NotImplementedError("shadow config loading is not implemented")


def semantic_input_hash(
    *,
    a_review: ReviewResult,
    jd_evidence: RoleEvidence,
    candidate_evidence: RoleEvidence,
    pattern_snapshot: PatternSnapshot,
    config: ShadowConfig,
) -> str:
    raise NotImplementedError("semantic input hashing is not implemented")


def build_semantic_state(
    *,
    jd_evidence: RoleEvidence,
    candidate_evidence: RoleEvidence,
    pattern_snapshot: PatternSnapshot,
) -> Mapping[str, object]:
    raise NotImplementedError("semantic state construction is not implemented")


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

    raise NotImplementedError("shadow review orchestration is not implemented")
