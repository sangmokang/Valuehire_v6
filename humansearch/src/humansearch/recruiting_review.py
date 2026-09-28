"""Pure recruiting review primitives for required-condition gates and ranking."""

import hashlib
import json
import math
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime
from enum import StrEnum

REVIEW_SCHEMA_VERSION = "recruiting-review-v1"
PRIORITY_SCORE = 85.0
REVIEW_SCORE = 70.0


class CriterionStatus(StrEnum):
    MET = "met"
    PARTIAL = "partial"
    UNMET = "unmet"
    UNKNOWN = "unknown"


class Recommendation(StrEnum):
    PRIORITY = "priority"
    REVIEW = "review"
    HOLD = "hold"
    NEEDS_CONFIRMATION = "needs_confirmation"
    EXCLUDED = "excluded"


@dataclass(frozen=True, slots=True)
class Criterion:
    """One observable requirement or preference used by the matcher."""

    key: str
    label: str
    weight: float
    status: CriterionStatus
    required: bool = False
    evidence: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class CriterionScore:
    key: str
    status: CriterionStatus
    weight: float
    earned: float
    required: bool
    evidence: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class GateResult:
    failed_required: tuple[str, ...]
    unknown_required: tuple[str, ...]

    @property
    def passed(self) -> bool:
        return not self.failed_required and not self.unknown_required


@dataclass(frozen=True, slots=True)
class ScoreResult:
    score: float
    scored_weight: float
    unknown_weight: float
    details: tuple[CriterionScore, ...]


@dataclass(frozen=True, slots=True)
class ReviewResult:
    schema_version: str
    input_hash: str
    gate: GateResult
    score: ScoreResult
    recommendation: Recommendation
    relevant_experience_months: int


@dataclass(frozen=True, slots=True)
class ExperiencePeriod:
    """Month-level career interval.

    The scorer uses calendar months because recruiting profiles usually expose
    tenure at month precision. Any overlap is collapsed before totals are made.
    The ``end`` month is exclusive. Use ``as_of`` for current roles with no end.
    """

    start: date
    end: date | None = None


def review_candidate(
    *,
    criteria: Sequence[Criterion],
    relevant_experience: Sequence[ExperiencePeriod] = (),
    as_of: date | None = None,
    input_fingerprint: Mapping[str, object] | None = None,
) -> ReviewResult:
    """Return a deterministic gate, weighted score, recommendation, and hash."""

    _validate_criteria(criteria)
    relevant_months = union_experience_months(relevant_experience, as_of=as_of)
    gate = required_gate(criteria)
    score = weighted_score(criteria)
    recommendation = recommend(gate, score.score)
    input_hash = hash_review_input(
        {
            "criteria": [_criterion_payload(criterion) for criterion in criteria],
            "relevant_experience": [
                _experience_payload(period, as_of=as_of) for period in relevant_experience
            ],
            "fingerprint": input_fingerprint or {},
        }
    )
    return ReviewResult(
        schema_version=REVIEW_SCHEMA_VERSION,
        input_hash=input_hash,
        gate=gate,
        score=score,
        recommendation=recommendation,
        relevant_experience_months=relevant_months,
    )


def required_gate(criteria: Sequence[Criterion]) -> GateResult:
    failed = tuple(
        criterion.key
        for criterion in criteria
        if criterion.required and criterion.status is CriterionStatus.UNMET
    )
    unknown = tuple(
        criterion.key
        for criterion in criteria
        if criterion.required
        and criterion.status in (CriterionStatus.PARTIAL, CriterionStatus.UNKNOWN)
    )
    return GateResult(failed_required=failed, unknown_required=unknown)


def weighted_score(criteria: Sequence[Criterion]) -> ScoreResult:
    _validate_criteria(criteria)
    total_weight = 0.0
    earned = 0.0
    unknown_weight = 0.0
    details: list[CriterionScore] = []
    for criterion in criteria:
        total_weight += criterion.weight
        if criterion.status is CriterionStatus.UNKNOWN:
            unknown_weight += criterion.weight
            criterion_earned = 0.0
        else:
            criterion_earned = criterion.weight * _status_ratio(criterion.status)
            earned += criterion_earned
        details.append(
            CriterionScore(
                key=criterion.key,
                status=criterion.status,
                weight=criterion.weight,
                earned=criterion_earned,
                required=criterion.required,
                evidence=criterion.evidence,
            )
        )
    score = 0.0 if total_weight == 0 else round(earned / total_weight * 100, 2)
    return ScoreResult(
        score=score,
        scored_weight=total_weight,
        unknown_weight=unknown_weight,
        details=tuple(details),
    )


def recommend(gate: GateResult, score: float) -> Recommendation:
    if gate.failed_required:
        return Recommendation.EXCLUDED
    if gate.unknown_required:
        return Recommendation.NEEDS_CONFIRMATION
    if score >= PRIORITY_SCORE:
        return Recommendation.PRIORITY
    if score >= REVIEW_SCORE:
        return Recommendation.REVIEW
    return Recommendation.HOLD


def union_experience_months(
    periods: Iterable[ExperiencePeriod], *, as_of: date | None = None
) -> int:
    observed: set[int] = set()
    end_fallback = as_of or _today_utc()
    for period in periods:
        end = period.end or end_fallback
        if end < period.start:
            raise ValueError("experience period end precedes start")
        start_index = _month_index(period.start)
        end_index = _month_index(end)
        observed.update(range(start_index, end_index))
    return len(observed)


def hash_review_input(payload: Mapping[str, object]) -> str:
    canonical = json.dumps(
        {"schema_version": REVIEW_SCHEMA_VERSION, "payload": payload},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _validate_criteria(criteria: Sequence[Criterion]) -> None:
    if not criteria:
        raise ValueError("criteria must not be empty")
    keys: set[str] = set()
    for criterion in criteria:
        if criterion.key in keys:
            raise ValueError(f"duplicate criterion key {criterion.key!r}")
        keys.add(criterion.key)
        if not math.isfinite(criterion.weight) or criterion.weight < 0:
            raise ValueError(f"criterion {criterion.key!r} has invalid weight")
        if criterion.status in (CriterionStatus.MET, CriterionStatus.PARTIAL):
            if not criterion.evidence:
                raise ValueError(
                    f"criterion {criterion.key!r} needs evidence for {criterion.status.value}"
                )
            for item in criterion.evidence:
                if not isinstance(item, str) or not item.strip():
                    raise ValueError(
                        f"criterion {criterion.key!r} has invalid evidence"
                    )
        if criterion.status is CriterionStatus.UNMET and criterion.required:
            continue
    if math.fsum(criterion.weight for criterion in criteria) != 100:
        raise ValueError("criterion weights must sum to 100")


def _status_ratio(status: CriterionStatus) -> float:
    if status is CriterionStatus.MET:
        return 1.0
    if status is CriterionStatus.PARTIAL:
        return 0.5
    return 0.0


def _month_index(value: date) -> int:
    return value.year * 12 + value.month


def _today_utc() -> date:
    return datetime.now(UTC).date()


def _criterion_payload(criterion: Criterion) -> dict[str, object]:
    return {
        "key": criterion.key,
        "label": criterion.label,
        "weight": criterion.weight,
        "status": criterion.status.value,
        "required": criterion.required,
        "evidence": list(criterion.evidence),
    }


def _experience_payload(period: ExperiencePeriod, *, as_of: date | None) -> dict[str, str]:
    end = period.end or as_of or _today_utc()
    return {"start": period.start.isoformat(), "end": end.isoformat()}
