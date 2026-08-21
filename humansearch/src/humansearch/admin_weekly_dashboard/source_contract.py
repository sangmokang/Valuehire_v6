"""Loads and validates the pre-live source/retention/identity contract.

Split out of source_policy.py (which now holds the runtime operational
decisions — collection status, calendar resolution, candidate matching) to
keep both files under the repository's 500-line direct-authorship cap. This
module owns "what external systems may we touch and how", while
source_policy.py owns "what to do given planned/attempted/collected signals".
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from types import MappingProxyType
from typing import cast

from .contracts import MetricStatus, SourceFailureReason

SOURCE_POLICY_VERSION = "admin-weekly-dashboard-sources/v1"
EXPECTED_REFRESH_INTERVAL_MINUTES = 15
EXPECTED_CALENDAR_ALIAS = "sangmokang"
EXPECTED_SUPABASE_SOURCES: dict[str, tuple[str, tuple[str, ...], str]] = {
    "candidate_cards": (
        "public.pipeline_candidates",
        ("clickup_task_id", "name", "resume_data", "last_synced_at"),
        "TRANSIENT_IDENTITY_REVIEW",
    ),
    "gmail_cursor": (
        "public.gmail_sync_state",
        ("last_success_at",),
        "AGGREGATE_READ_ONLY",
    ),
    "gmail_events": (
        "public.gmail_derived_events",
        ("id", "event_type", "status", "occurred_at", "classifier_version"),
        "AGGREGATE_READ_ONLY",
    ),
    "gmail_runs": (
        "public.gmail_ingestion_runs",
        ("run_id", "status", "pagination_exhausted", "last_success_at"),
        "AGGREGATE_READ_ONLY",
    ),
    "position_cards": (
        "public.pipeline_position_cards",
        ("id", "company_name", "imported_at", "last_updated_at"),
        "AGGREGATE_READ_ONLY",
    ),
    "sourcing_results": (
        "public.sourcing_results",
        ("id", "run_id", "position_id"),
        "AGGREGATE_READ_ONLY",
    ),
    "sourcing_runs": (
        "public.sourcing_runs",
        ("id", "triggered_at"),
        "AGGREGATE_READ_ONLY",
    ),
}
EXPECTED_EXTERNAL_EFFECTS = {
    "calendar": "READ_ONLY_NOT_CONNECTED",
    "clickup": "READ_ONLY_NOT_CONNECTED",
    "gmail": "READ_ONLY_NOT_CONNECTED",
    "supabase_writes": "DISABLED",
}


class CandidateLinkDecision(str, Enum):
    """A review suggestion is the strongest allowed identity outcome."""

    NO_MATCH = "NO_MATCH"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"


@dataclass(frozen=True, init=False)
class SupabaseSource:
    """An existing table and the minimum fields allowed for dashboard reads."""

    table: str
    select_fields: tuple[str, ...]
    processing: str

    def __init__(self, *, table: str, select_fields: tuple[str, ...], processing: str) -> None:
        if not isinstance(table, str) or not table.strip():
            raise ValueError("table must be a non-empty string")
        if not isinstance(select_fields, tuple) or not select_fields:
            raise ValueError("select_fields must be a non-empty tuple")
        if not all(isinstance(item, str) and item for item in select_fields):
            raise ValueError("select_fields must contain only non-empty strings")
        if processing not in {"AGGREGATE_READ_ONLY", "TRANSIENT_IDENTITY_REVIEW"}:
            raise ValueError(f"unsupported processing mode {processing!r}")
        object.__setattr__(self, "table", table)
        object.__setattr__(self, "select_fields", select_fields)
        object.__setattr__(self, "processing", processing)


@dataclass(frozen=True, init=False)
class SourcePolicy:
    """Validated source, retention, identity, and cadence decisions.

    __init__ re-checks every safety invariant on every construction path,
    including dataclasses.replace() — a caller cannot bypass load_source_policy()
    by building or mutating a SourcePolicy directly, the way an earlier
    adversarial review demonstrated against the plain-dataclass version.
    """

    version: str
    refresh_interval_minutes: int
    overlap_reason: SourceFailureReason
    calendar_alias: str
    gmail_raw_permanent_copy: bool
    weekly_aggregate_retention: str
    deletion_request_required: bool
    candidate_identity_fields: tuple[str, ...]
    candidate_auto_merge: bool
    candidate_all_exact: CandidateLinkDecision
    supabase_tables: Mapping[str, SupabaseSource]
    external_effects: Mapping[str, str]

    def __init__(
        self,
        *,
        version: str,
        refresh_interval_minutes: int,
        overlap_reason: SourceFailureReason,
        calendar_alias: str,
        gmail_raw_permanent_copy: bool,
        weekly_aggregate_retention: str,
        deletion_request_required: bool,
        candidate_identity_fields: tuple[str, ...],
        candidate_auto_merge: bool,
        candidate_all_exact: CandidateLinkDecision,
        supabase_tables: Mapping[str, SupabaseSource],
        external_effects: Mapping[str, str],
    ) -> None:
        if version != SOURCE_POLICY_VERSION:
            raise ValueError(f"source policy version must be {SOURCE_POLICY_VERSION!r}")
        if refresh_interval_minutes != EXPECTED_REFRESH_INTERVAL_MINUTES:
            raise ValueError("source policy refresh interval must be 15 minutes")
        if overlap_reason is not SourceFailureReason.COLLECTION_OVERLAP:
            raise ValueError("source policy overlap reason must be collection_overlap")
        if calendar_alias != EXPECTED_CALENDAR_ALIAS:
            raise ValueError(f"source policy calendar alias must be {EXPECTED_CALENDAR_ALIAS!r}")
        if gmail_raw_permanent_copy is not False:
            raise ValueError("gmail_raw_permanent_copy must be exactly False")
        if weekly_aggregate_retention != "INDEFINITE":
            raise ValueError("weekly_aggregate_retention must be INDEFINITE")
        if deletion_request_required is not True:
            raise ValueError("deletion_request_required must be exactly True")
        if candidate_identity_fields != ("name", "school", "company"):
            raise ValueError("candidate_identity_fields must be name, school, company")
        if candidate_auto_merge is not False:
            raise ValueError("candidate_auto_merge must be exactly False")
        if candidate_all_exact is not CandidateLinkDecision.REVIEW_REQUIRED:
            raise ValueError("candidate_all_exact must require review")
        if set(supabase_tables) != set(EXPECTED_SUPABASE_SOURCES):
            raise ValueError("supabase_tables must cover exactly the approved sources")
        for source_name, source in supabase_tables.items():
            if not isinstance(source, SupabaseSource):
                raise TypeError(f"supabase_tables[{source_name!r}] must be a SupabaseSource")
            expected = EXPECTED_SUPABASE_SOURCES[source_name]
            if (source.table, source.select_fields, source.processing) != expected:
                raise ValueError(f"{source_name} must match the approved existing Supabase source")
        if dict(external_effects) != dict(EXPECTED_EXTERNAL_EFFECTS):
            raise ValueError("external effects must remain read-only and not connected")
        object.__setattr__(self, "version", version)
        object.__setattr__(self, "refresh_interval_minutes", refresh_interval_minutes)
        object.__setattr__(self, "overlap_reason", overlap_reason)
        object.__setattr__(self, "calendar_alias", calendar_alias)
        object.__setattr__(self, "gmail_raw_permanent_copy", gmail_raw_permanent_copy)
        object.__setattr__(self, "weekly_aggregate_retention", weekly_aggregate_retention)
        object.__setattr__(self, "deletion_request_required", deletion_request_required)
        object.__setattr__(self, "candidate_identity_fields", candidate_identity_fields)
        object.__setattr__(self, "candidate_auto_merge", candidate_auto_merge)
        object.__setattr__(self, "candidate_all_exact", candidate_all_exact)
        object.__setattr__(self, "supabase_tables", MappingProxyType(dict(supabase_tables)))
        object.__setattr__(self, "external_effects", MappingProxyType(dict(external_effects)))

    def to_public_dict(self) -> dict[str, object]:
        """Return a PII-free readiness report for operators and future wiring."""

        return {
            "version": self.version,
            "readiness": {
                "status": MetricStatus.NOT_RUN.value,
                "reason": SourceFailureReason.PRECONDITION_MISSING.value,
            },
            "refresh": {
                "interval_minutes": self.refresh_interval_minutes,
                "overlap_result": MetricStatus.NOT_RUN.value,
                "overlap_reason": self.overlap_reason.value,
            },
            "calendar": {
                "requested_alias": self.calendar_alias,
                "resolution": "EXACTLY_ONE_ID_OR_SUMMARY_MATCH",
            },
            "retention": {
                "gmail_raw_permanent_copy": self.gmail_raw_permanent_copy,
                "weekly_anonymized_aggregates": self.weekly_aggregate_retention,
                "deletion_request_required": self.deletion_request_required,
            },
            "candidate_identity": {
                "evidence": list(self.candidate_identity_fields),
                "auto_merge": self.candidate_auto_merge,
                "all_exact": self.candidate_all_exact.value,
            },
            "supabase_reuse": {
                name: {"table": source.table, "processing": source.processing}
                for name, source in sorted(self.supabase_tables.items())
            },
            "external_effects": dict(sorted(self.external_effects.items())),
        }


def load_source_policy(path: Path) -> SourcePolicy:
    """Load and fail-closed validate the operational source contract."""

    raw: object = json.loads(path.read_text(encoding="utf-8"))
    root = _object(raw, "source contract")
    _exact_keys(
        root,
        {
            "version",
            "refresh",
            "calendar",
            "retention",
            "candidate_identity",
            "supabase_reuse",
            "external_effects",
        },
        "source contract",
    )
    version = _string(root, "version")
    if version != SOURCE_POLICY_VERSION:
        raise ValueError(f"source contract version must be {SOURCE_POLICY_VERSION}")

    refresh = _object(root["refresh"], "refresh")
    _exact_keys(refresh, {"interval_minutes", "overlap_policy", "overlap_reason"}, "refresh")
    interval = _integer(refresh, "interval_minutes")
    if interval != EXPECTED_REFRESH_INTERVAL_MINUTES:
        raise ValueError("source contract v1 refresh interval must be 15 minutes")
    if _string(refresh, "overlap_policy") != "SKIP_AS_NOT_RUN":
        raise ValueError("overlapping collection must be skipped as NOT_RUN")
    overlap_reason = SourceFailureReason(_string(refresh, "overlap_reason"))
    if overlap_reason is not SourceFailureReason.COLLECTION_OVERLAP:
        raise ValueError("overlap reason must be collection_overlap")

    calendar = _object(root["calendar"], "calendar")
    _exact_keys(
        calendar,
        {"requested_alias", "match_fields", "ambiguous_result", "not_found_result"},
        "calendar",
    )
    calendar_alias = _string(calendar, "requested_alias")
    if calendar_alias != EXPECTED_CALENDAR_ALIAS:
        raise ValueError("source contract v1 calendar alias must be sangmokang")
    if _string_tuple(calendar, "match_fields") != ("id", "summary"):
        raise ValueError("calendar matching must use exact id or summary")
    for key in ("ambiguous_result", "not_found_result"):
        if _string(calendar, key) != MetricStatus.NOT_RUN.value:
            raise ValueError(f"calendar {key} must be NOT_RUN")

    retention = _object(root["retention"], "retention")
    _exact_keys(
        retention,
        {"gmail_raw_permanent_copy", "weekly_anonymized_aggregates", "deletion_request"},
        "retention",
    )
    if _string(retention, "gmail_raw_permanent_copy") != "FORBIDDEN":
        raise ValueError("permanent Gmail raw copies are forbidden")
    aggregate_retention = _string(retention, "weekly_anonymized_aggregates")
    if aggregate_retention != "INDEFINITE":
        raise ValueError("weekly anonymized aggregates must be INDEFINITE")
    if _string(retention, "deletion_request") != "REQUIRED":
        raise ValueError("deletion requests must be supported")

    identity = _object(root["candidate_identity"], "candidate_identity")
    _exact_keys(identity, {"evidence", "auto_merge", "all_exact"}, "candidate_identity")
    identity_fields = _string_tuple(identity, "evidence")
    if identity_fields != ("name", "school", "company"):
        raise ValueError("candidate evidence must be name, school, company")
    auto_merge = _boolean(identity, "auto_merge")
    if auto_merge:
        raise ValueError("candidate identity evidence must never auto-merge")
    all_exact = CandidateLinkDecision(_string(identity, "all_exact"))
    if all_exact is not CandidateLinkDecision.REVIEW_REQUIRED:
        raise ValueError("three exact identity fields must require review")

    sources_raw = _object(root["supabase_reuse"], "supabase_reuse")
    _exact_keys(sources_raw, set(EXPECTED_SUPABASE_SOURCES), "supabase_reuse")
    sources: dict[str, SupabaseSource] = {}
    for source_name, source_raw in sources_raw.items():
        source = _object(source_raw, f"supabase_reuse.{source_name}")
        _exact_keys(source, {"table", "select_fields", "processing"}, source_name)
        table = _string(source, "table")
        select_fields = _string_tuple(source, "select_fields")
        processing = _processing(source, source_name)
        expected_table, expected_fields, expected_processing = EXPECTED_SUPABASE_SOURCES[
            source_name
        ]
        if (table, select_fields, processing) != (
            expected_table,
            expected_fields,
            expected_processing,
        ):
            raise ValueError(f"{source_name} must match the approved existing Supabase source")
        sources[source_name] = SupabaseSource(
            table=table,
            select_fields=select_fields,
            processing=processing,
        )

    effects_raw = _object(root["external_effects"], "external_effects")
    _exact_keys(effects_raw, set(EXPECTED_EXTERNAL_EFFECTS), "external_effects")
    effects = {key: _string(effects_raw, key) for key in effects_raw}
    if effects != EXPECTED_EXTERNAL_EFFECTS:
        raise ValueError("Phase D external effects must remain read-only and not connected")

    return SourcePolicy(
        version=version,
        refresh_interval_minutes=interval,
        overlap_reason=overlap_reason,
        calendar_alias=calendar_alias,
        gmail_raw_permanent_copy=False,
        weekly_aggregate_retention=aggregate_retention,
        deletion_request_required=True,
        candidate_identity_fields=identity_fields,
        candidate_auto_merge=auto_merge,
        candidate_all_exact=all_exact,
        supabase_tables=MappingProxyType(sources),
        external_effects=MappingProxyType(effects),
    )


def _object(value: object, label: str) -> dict[str, object]:
    if not isinstance(value, dict) or not all(isinstance(key, str) for key in value):
        raise TypeError(f"{label} must be an object with string keys")
    return cast(dict[str, object], value)


def _exact_keys(value: Mapping[str, object], expected: set[str], label: str) -> None:
    actual = set(value)
    if actual != expected:
        raise ValueError(
            f"{label} keys mismatch: missing={sorted(expected - actual)} "
            f"unexpected={sorted(actual - expected)}"
        )


def _string(value: Mapping[str, object], key: str) -> str:
    result = value.get(key)
    if not isinstance(result, str) or not result.strip():
        raise TypeError(f"{key} must be a non-empty string")
    return result


def _integer(value: Mapping[str, object], key: str) -> int:
    result = value.get(key)
    if not isinstance(result, int) or isinstance(result, bool):
        raise TypeError(f"{key} must be an integer")
    return result


def _boolean(value: Mapping[str, object], key: str) -> bool:
    result = value.get(key)
    if not isinstance(result, bool):
        raise TypeError(f"{key} must be a boolean")
    return result


def _string_tuple(value: Mapping[str, object], key: str) -> tuple[str, ...]:
    result = value.get(key)
    if not isinstance(result, list) or not result:
        raise TypeError(f"{key} must be a non-empty list")
    if not all(isinstance(item, str) and item for item in result):
        raise TypeError(f"{key} must contain only non-empty strings")
    return tuple(cast(list[str], result))


def _processing(source: Mapping[str, object], source_name: str) -> str:
    processing = _string(source, "processing")
    allowed = {"AGGREGATE_READ_ONLY", "TRANSIENT_IDENTITY_REVIEW"}
    if processing not in allowed:
        raise ValueError(f"{source_name} has unsupported processing mode")
    return processing
