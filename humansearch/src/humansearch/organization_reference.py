"""Contracts for role-scoped employee reference cohorts."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date, datetime
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

    raise NotImplementedError("reference cohort aggregation is not implemented")
