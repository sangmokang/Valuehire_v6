"""Contracts and deterministic aggregation for role-scoped reference cohorts."""

import hashlib
import json
from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime
from enum import StrEnum


class EmploymentStatus(StrEnum):
    CURRENT = "current"
    FORMER = "former"
    UNKNOWN = "unknown"


class PatternStatus(StrEnum):
    READY = "ready"
    LIMITED = "limited"
    NO_EVIDENCE = "no_evidence"


@dataclass(frozen=True, slots=True)
class CohortKey:
    canonical_company_id: str
    role_family: str
    seniority: str
    team_product_scope: str | None = None


@dataclass(frozen=True, slots=True)
class RoleEvidence:
    primary_role_family: str
    responsibilities: tuple[str, ...]
    ownership_scope: tuple[str, ...]
    production_operating: tuple[str, ...]
    product_stage: tuple[str, ...]
    domain_problems: tuple[str, ...]
    technical_environment: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ReferenceObservation:
    observation_id: str
    person_id: str
    cohort: CohortKey
    employment_status: EmploymentStatus
    observation_date: date
    source_timestamp: datetime
    evidence_ids: tuple[str, ...]
    role_evidence: RoleEvidence


@dataclass(frozen=True, slots=True)
class ObservedPattern:
    category: str
    value: str
    distinct_people: int
    evidence_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class PatternSnapshot:
    schema_version: str
    pattern_version: str
    cohort: CohortKey
    as_of: date
    sample_size: int
    known_denominator: int | None
    employment_counts: Mapping[str, int]
    repeated_patterns: tuple[ObservedPattern, ...]
    single_observations: tuple[ObservedPattern, ...]
    conflicts: tuple[str, ...]
    stale_observation_ids: tuple[str, ...]
    status: PatternStatus
    canonical_input_hash: str


def build_pattern_snapshot(
    observations: Sequence[ReferenceObservation],
    *,
    as_of: date,
    known_denominator: int | None,
    pattern_version: str,
    minimum_cohort_size: int,
    minimum_distinct_people: int,
    stale_after_days: int,
) -> PatternSnapshot:
    """Build one company × role family × seniority reference snapshot."""

    _validate_boundaries(
        known_denominator=known_denominator,
        minimum_cohort_size=minimum_cohort_size,
        minimum_distinct_people=minimum_distinct_people,
        stale_after_days=stale_after_days,
    )
    cohort = observations[0].cohort if observations else _empty_cohort()
    if any(item.cohort != cohort for item in observations):
        raise ValueError("observations must belong to a single cohort")
    for item in observations:
        _validate_observation(item, as_of=as_of)

    conflicts, unique = _resolve_observation_ids(observations)
    stale = tuple(
        sorted(
            item.observation_id
            for item in unique
            if (as_of - item.observation_date).days > stale_after_days
        )
    )
    excluded = set(conflicts) | set(stale)
    eligible = tuple(item for item in unique if item.observation_id not in excluded)
    people = {item.person_id for item in eligible}
    if known_denominator is not None and known_denominator < len(people):
        raise ValueError("known denominator must not be smaller than sample size")

    patterns = _aggregate_patterns(eligible)
    repeated = tuple(item for item in patterns if item.distinct_people >= minimum_distinct_people)
    singles = tuple(item for item in patterns if item.distinct_people < minimum_distinct_people)
    status = _pattern_status(
        sample_size=len(people),
        repeated_patterns=repeated,
        minimum_cohort_size=minimum_cohort_size,
    )
    canonical_hash = _snapshot_input_hash(
        observations=observations,
        as_of=as_of,
        known_denominator=known_denominator,
        pattern_version=pattern_version,
        minimum_cohort_size=minimum_cohort_size,
        minimum_distinct_people=minimum_distinct_people,
        stale_after_days=stale_after_days,
    )
    return PatternSnapshot(
        schema_version="organization-reference-snapshot-v1",
        pattern_version=pattern_version,
        cohort=cohort,
        as_of=as_of,
        sample_size=len(people),
        known_denominator=known_denominator,
        employment_counts=_employment_counts(eligible),
        repeated_patterns=repeated,
        single_observations=singles,
        conflicts=conflicts,
        stale_observation_ids=stale,
        status=status,
        canonical_input_hash=canonical_hash,
    )


def _validate_boundaries(
    *,
    known_denominator: int | None,
    minimum_cohort_size: int,
    minimum_distinct_people: int,
    stale_after_days: int,
) -> None:
    if known_denominator is not None and known_denominator < 0:
        raise ValueError("known denominator must be non-negative")
    if minimum_cohort_size < 1:
        raise ValueError("minimum cohort size must be positive")
    if minimum_distinct_people < 2:
        raise ValueError("a repeated pattern needs at least two distinct people")
    if stale_after_days < 0:
        raise ValueError("stale-after days must be non-negative")


def _validate_observation(item: ReferenceObservation, *, as_of: date) -> None:
    required = (
        item.observation_id,
        item.person_id,
        item.cohort.canonical_company_id,
        item.cohort.role_family,
        item.cohort.seniority,
        *item.evidence_ids,
    )
    if not item.evidence_ids or any(not value.strip() for value in required):
        raise ValueError("observation identifiers and evidence IDs must not be empty")
    if item.source_timestamp.tzinfo is None or item.source_timestamp.utcoffset() is None:
        raise ValueError("source timestamp must be timezone-aware")
    if item.observation_date > as_of:
        raise ValueError("observation date must not be after snapshot date")
    for _, value in _evidence_values(item.role_evidence):
        if not value.strip():
            raise ValueError("role evidence values must not be empty")


def _resolve_observation_ids(
    observations: Sequence[ReferenceObservation],
) -> tuple[tuple[str, ...], tuple[ReferenceObservation, ...]]:
    grouped: dict[str, list[ReferenceObservation]] = defaultdict(list)
    for item in observations:
        grouped[item.observation_id].append(item)
    conflicts = tuple(
        sorted(observation_id for observation_id, items in grouped.items() if len(set(items)) > 1)
    )
    unique = tuple(
        items[0]
        for observation_id, items in sorted(grouped.items())
        if observation_id not in conflicts
    )
    return conflicts, unique


def _aggregate_patterns(
    observations: Sequence[ReferenceObservation],
) -> tuple[ObservedPattern, ...]:
    people: dict[tuple[str, str], set[str]] = defaultdict(set)
    evidence: dict[tuple[str, str], set[str]] = defaultdict(set)
    for item in observations:
        for category, value in _evidence_values(item.role_evidence):
            key = (category, value.strip())
            people[key].add(item.person_id)
            evidence[key].update(item.evidence_ids)
    return tuple(
        ObservedPattern(
            category=category,
            value=value,
            distinct_people=len(people[(category, value)]),
            evidence_ids=tuple(sorted(evidence[(category, value)])),
        )
        for category, value in sorted(people)
    )


def _evidence_values(evidence: RoleEvidence) -> tuple[tuple[str, str], ...]:
    values: list[tuple[str, str]] = [("primary_role_family", evidence.primary_role_family)]
    for category in (
        "responsibilities",
        "ownership_scope",
        "production_operating",
        "product_stage",
        "domain_problems",
        "technical_environment",
    ):
        values.extend((category, value) for value in getattr(evidence, category))
    return tuple(values)


def _employment_counts(observations: Sequence[ReferenceObservation]) -> Mapping[str, int]:
    people_by_status: dict[str, set[str]] = defaultdict(set)
    for item in observations:
        people_by_status[item.employment_status.value].add(item.person_id)
    return {status.value: len(people_by_status[status.value]) for status in EmploymentStatus}


def _pattern_status(
    *,
    sample_size: int,
    repeated_patterns: Sequence[ObservedPattern],
    minimum_cohort_size: int,
) -> PatternStatus:
    if sample_size == 0:
        return PatternStatus.NO_EVIDENCE
    if sample_size < minimum_cohort_size or not repeated_patterns:
        return PatternStatus.LIMITED
    return PatternStatus.READY


def _snapshot_input_hash(
    *,
    observations: Sequence[ReferenceObservation],
    as_of: date,
    known_denominator: int | None,
    pattern_version: str,
    minimum_cohort_size: int,
    minimum_distinct_people: int,
    stale_after_days: int,
) -> str:
    payload = {
        "schema_version": "organization-reference-input-v1",
        "pattern_version": pattern_version,
        "as_of": as_of.isoformat(),
        "known_denominator": known_denominator,
        "minimum_cohort_size": minimum_cohort_size,
        "minimum_distinct_people": minimum_distinct_people,
        "stale_after_days": stale_after_days,
        "observations": sorted(
            (_observation_payload(item) for item in observations), key=_canonical_sort_key
        ),
    }
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()


def _canonical_sort_key(item: Mapping[str, object]) -> str:
    return json.dumps(item, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _observation_payload(item: ReferenceObservation) -> Mapping[str, object]:
    return {
        "observation_id": item.observation_id,
        "person_id": item.person_id,
        "cohort": {
            "canonical_company_id": item.cohort.canonical_company_id,
            "role_family": item.cohort.role_family,
            "seniority": item.cohort.seniority,
            "team_product_scope": item.cohort.team_product_scope,
        },
        "employment_status": item.employment_status.value,
        "observation_date": item.observation_date.isoformat(),
        "source_timestamp": item.source_timestamp.astimezone(UTC).isoformat(),
        "evidence_ids": sorted(item.evidence_ids),
        "role_evidence": {
            "primary_role_family": item.role_evidence.primary_role_family,
            "responsibilities": item.role_evidence.responsibilities,
            "ownership_scope": item.role_evidence.ownership_scope,
            "production_operating": item.role_evidence.production_operating,
            "product_stage": item.role_evidence.product_stage,
            "domain_problems": item.role_evidence.domain_problems,
            "technical_environment": item.role_evidence.technical_environment,
        },
    }


def _empty_cohort() -> CohortKey:
    return CohortKey("__unavailable__", "__unavailable__", "__unavailable__", None)
