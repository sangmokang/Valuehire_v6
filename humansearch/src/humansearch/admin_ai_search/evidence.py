"""Deterministic AI Search batch, score-band, and FU evidence projection."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Literal, NotRequired, TypedDict, cast
from zoneinfo import ZoneInfo

EvidenceStatus = Literal["PASS", "FAIL", "NOT_RUN"]
ContactRecommendation = Literal["STRONG", "NORMAL", "HOLD", "NOT_RUN"]
KST = ZoneInfo("Asia/Seoul")


class ScoreBuckets(TypedDict):
    """Mutually exclusive score bands displayed in the batch list."""

    score_90_plus: int | None
    score_80s: int | None
    score_70s: int | None


class ActorEvidencePayload(TypedDict):
    subject: str
    sender: str
    thread_id: str
    message_id: str
    received_at: str
    reason: str


class SearchPeriodPayload(TypedDict):
    start: str | None
    end: str | None
    status: EvidenceStatus
    reason: str | None


class CandidateCountsPayload(TypedDict):
    raw: int | None
    parsed: int
    duplicate: int
    unparsed: int | None
    excluded: int


class BatchGroupingPayload(TypedDict):
    status: EvidenceStatus
    reason: str
    message_count: int
    message_ids: list[str]


class CandidatePayload(TypedDict):
    canonical_key: str
    display_name: str
    source_channel: str
    profile_url: str
    education: str | None
    experience: str | None
    key_experience: str | None
    requirements_evidence: list[str]
    score: int | None
    score_status: EvidenceStatus
    score_reason: str | None
    why_fit: list[str]
    reverse_match_position: str | None
    reverse_match_score: int | None
    reverse_match_reason: str
    contact_recommendation: str
    contact_status: EvidenceStatus
    contact_source: str | None
    contacted_at: str | None
    contact_checked_at: str | None
    contact_reference: str | None
    contact_opinion_evidence: str | None
    better_position_exists: bool | None
    better_position: str | None
    better_position_reason: str | None


class VerificationPayload(TypedDict):
    source: str
    status: EvidenceStatus
    checked_at: str | None
    reason: str | None


class BatchPayload(TypedDict):
    batch_id: str
    actor: str
    actor_label: str
    actor_evidence: ActorEvidencePayload | None
    company: str
    position: str
    channels: list[str]
    executed_at: str
    batch_grouping: BatchGroupingPayload
    search_period: SearchPeriodPayload
    candidate_counts: CandidateCountsPayload
    candidate_counts_status: EvidenceStatus
    candidate_counts_reason: str | None
    raw_candidates: int | None
    unique_candidates: int
    score_buckets: dict[str, int | None]
    score_status: EvidenceStatus
    score_reason: str | None
    actual_fu: int | None
    actual_fu_status: EvidenceStatus
    actual_fu_reason: str | None
    verification_status: EvidenceStatus
    verification_reason: str | None
    candidates: list[CandidatePayload]
    verification_checks: list[VerificationPayload]


class AiSearchPayload(TypedDict):
    mode: str
    contract_version: str
    status: EvidenceStatus
    reason: str | None
    cadence: str
    batches: list[BatchPayload]
    external_effects: dict[str, str]
    gmail_collection: NotRequired[dict[str, object]]


def _nonblank(value: str, field: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-blank string")


def _status(value: str, field: str) -> None:
    if value not in {"PASS", "FAIL", "NOT_RUN"}:
        raise ValueError(f"{field} must be PASS, FAIL, or NOT_RUN")


@dataclass(frozen=True)
class CandidateEvidence:
    canonical_key: str
    display_name: str
    source_channel: str
    profile_url: str
    education: str | None
    experience: str | None
    score: int | None
    why_fit: tuple[str, ...]
    reverse_match_position: str | None
    reverse_match_score: int | None
    reverse_match_reason: str
    contact_recommendation: ContactRecommendation
    key_experience: str | None = None
    requirements_evidence: tuple[str, ...] = ()
    score_reason: str | None = None
    better_position_exists: bool | None = None
    better_position: str | None = None
    better_position_reason: str | None = None
    contact_opinion_evidence: str | None = None

    def __post_init__(self) -> None:
        if len(self.canonical_key) != 64 or any(
            char not in "0123456789abcdef" for char in self.canonical_key
        ):
            raise ValueError("canonical_key must be a lowercase SHA-256 hex digest")
        for field in ("display_name", "source_channel", "profile_url"):
            _nonblank(cast(str, getattr(self, field)), field)
        for field in ("education", "experience", "key_experience"):
            value = cast(str | None, getattr(self, field))
            if value is not None:
                _nonblank(value, field)
        if self.score is not None and (
            isinstance(self.score, bool)
            or not isinstance(self.score, int)
            or not 0 <= self.score <= 100
        ):
            raise ValueError("score must be an integer from 0 to 100")
        if any(not item.strip() for item in self.why_fit):
            raise ValueError("why_fit must contain non-blank evidence")
        if any(not item.strip() for item in self.requirements_evidence):
            raise ValueError("requirements_evidence must contain non-blank evidence")
        if self.score is None and not self.score_reason:
            raise ValueError("missing score requires score_reason")
        if self.reverse_match_score is not None and not 0 <= self.reverse_match_score <= 100:
            raise ValueError("reverse_match_score must be between 0 and 100")
        if self.contact_recommendation not in {"STRONG", "NORMAL", "HOLD", "NOT_RUN"}:
            raise ValueError("contact_recommendation is invalid")


@dataclass(frozen=True)
class ContactEvidence:
    canonical_key: str
    source: str
    status: EvidenceStatus
    contacted_at: str | None
    evidence_reference: str | None

    def __post_init__(self) -> None:
        _nonblank(self.source, "source")
        _status(self.status, "status")
        if self.status == "PASS" and (not self.contacted_at or not self.evidence_reference):
            raise ValueError("PASS contact evidence requires time and reference")


@dataclass(frozen=True)
class VerificationCheck:
    source: str
    status: EvidenceStatus
    checked_at: str | None
    reason: str | None

    def __post_init__(self) -> None:
        _nonblank(self.source, "source")
        _status(self.status, "status")
        if self.status == "PASS" and not self.checked_at:
            raise ValueError("PASS verification requires checked_at")
        if self.status != "PASS" and not self.reason:
            raise ValueError("failed or skipped verification requires a reason")


@dataclass(frozen=True)
class AiSearchRun:
    actor: str
    source_run_id: str
    company: str
    position: str
    channels: tuple[str, ...]
    executed_at: datetime
    candidates: tuple[CandidateEvidence, ...]
    contacts: tuple[ContactEvidence, ...] = ()
    verification_checks: tuple[VerificationCheck, ...] = ()
    actor_evidence: ActorEvidencePayload | None = None
    search_period_start: str | None = None
    search_period_end: str | None = None
    search_period_reason: str | None = "search_period_not_found"
    unparsed_candidates: int = 0
    excluded_candidates: int = 0
    candidate_counts_complete: bool = True
    candidate_counts_reason: str | None = None
    batch_group_key: str | None = None
    source_message_ids: tuple[str, ...] = ()
    batch_grouping_reason: str = "source_run_is_single_batch"

    def __post_init__(self) -> None:
        for field in ("actor", "source_run_id", "company", "position"):
            _nonblank(cast(str, getattr(self, field)), field)
        if not self.channels or any(not channel.strip() for channel in self.channels):
            raise ValueError("channels must contain non-blank values")
        if self.executed_at.tzinfo is None or self.executed_at.utcoffset() is None:
            raise ValueError("executed_at must be timezone-aware")
        if self.unparsed_candidates < 0 or self.excluded_candidates < 0:
            raise ValueError("candidate count components must be non-negative")
        if not self.candidate_counts_complete and not self.candidate_counts_reason:
            raise ValueError("incomplete candidate counts require a reason")
        if self.batch_group_key is not None:
            _nonblank(self.batch_group_key, "batch_group_key")
        if len(self.source_message_ids) != len(set(self.source_message_ids)):
            raise ValueError("source_message_ids must be unique")
        for message_id in self.source_message_ids:
            _nonblank(message_id, "source_message_id")
        _nonblank(self.batch_grouping_reason, "batch_grouping_reason")
        if (self.search_period_start is None) != (self.search_period_end is None):
            raise ValueError("search period requires both start and end")
        if self.search_period_start is None and not self.search_period_reason:
            raise ValueError("missing search period requires a reason")
        check_sources = [check.source for check in self.verification_checks]
        if len(check_sources) != len(set(check_sources)):
            raise ValueError("verification source must be unique per run")


@dataclass(frozen=True)
class EvidenceContract:
    version: str
    cadence: str
    actors: Mapping[str, str]
    score_bands: Mapping[str, Mapping[str, int]]
    required_verification_sources: tuple[str, ...]
    external_effects: dict[str, str]


def load_evidence_contract(path: Path) -> EvidenceContract:
    """Load the repository-owned evidence contract and reject drift."""

    raw = json.loads(path.read_text(encoding="utf-8"))
    if raw.get("version") != "admin-ai-search-evidence/v1" or raw.get("cadence") != "DAILY":
        raise ValueError("unsupported AI Search evidence contract")
    required = tuple(raw.get("required_verification_sources", ()))
    if len(required) != 4 or len(set(required)) != 4:
        raise ValueError("verification sources must contain four unique entries")
    actors = raw.get("actors")
    bands = raw.get("score_bands")
    effects = raw.get("external_effects")
    if not isinstance(actors, dict) or not isinstance(bands, dict) or not isinstance(effects, dict):
        raise TypeError("AI Search evidence contract has invalid mappings")
    expected_bands = {
        "90_plus": {"min": 90, "max": 100},
        "80s": {"min": 80, "max": 89},
        "70s": {"min": 70, "max": 79},
    }
    if bands != expected_bands:
        raise ValueError("AI Search score bands do not match the v1 contract")
    return EvidenceContract(
        version=raw["version"],
        cadence=raw["cadence"],
        actors=cast(dict[str, str], actors),
        score_bands=cast(dict[str, dict[str, int]], bands),
        required_verification_sources=required,
        external_effects=cast(dict[str, str], effects),
    )


def stable_batch_id(actor: str, source_run_id: str, executed_at: datetime) -> str:
    """Create a stable display ID from immutable run identity, never randomness."""

    _nonblank(actor, "actor")
    _nonblank(source_run_id, "source_run_id")
    if executed_at.tzinfo is None or executed_at.utcoffset() is None:
        raise ValueError("executed_at must be timezone-aware")
    identity = json.dumps(
        {"actor": actor, "source_run_id": source_run_id, "executed_at": executed_at.isoformat()},
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    suffix = hashlib.sha256(identity).hexdigest()[:10].upper()
    day = executed_at.astimezone(KST).strftime("%Y%m%d")
    return f"VHAI-{day}-{suffix}"


def build_ai_search_batch(search_run: AiSearchRun, contract: EvidenceContract) -> BatchPayload:
    """Project one raw run into deterministic listing and detail evidence."""

    if search_run.actor not in contract.actors:
        raise ValueError(f"unsupported actor {search_run.actor!r}")
    deduplicated: dict[str, CandidateEvidence] = {}
    for item in sorted(
        search_run.candidates,
        key=lambda candidate: (
            -(candidate.score if candidate.score is not None else -1),
            candidate.source_channel,
            candidate.profile_url,
        ),
    ):
        deduplicated.setdefault(item.canonical_key, item)
    contacts = _contact_evidence(search_run.contacts)
    checks = {check.source: check for check in search_run.verification_checks}
    candidates = [
        _candidate_payload(item, contacts.get(item.canonical_key), checks)
        for item in sorted(
            deduplicated.values(),
            key=lambda item: (-(item.score if item.score is not None else -1), item.canonical_key),
        )
    ]
    verification_status, verification_reason = _verification_state(search_run, contract)
    duplicate_count = len(search_run.candidates) - len(candidates)
    raw_count = (
        len(candidates)
        + duplicate_count
        + search_run.unparsed_candidates
        + search_run.excluded_candidates
    )
    candidate_counts: CandidateCountsPayload = {
        "raw": raw_count if search_run.candidate_counts_complete else None,
        "parsed": len(candidates),
        "duplicate": duplicate_count,
        "unparsed": (
            search_run.unparsed_candidates if search_run.candidate_counts_complete else None
        ),
        "excluded": search_run.excluded_candidates,
    }
    if search_run.candidate_counts_complete and raw_count != (
        len(candidates)
        + duplicate_count
        + search_run.unparsed_candidates
        + search_run.excluded_candidates
    ):
        raise AssertionError("candidate count ledger is inconsistent")
    score_status, score_reason = _score_state(candidates)
    all_sources_checked = all(
        checks.get(source) is not None and checks[source].status == "PASS"
        for source in contract.required_verification_sources
    )
    passed_contacts = sum(item["contact_status"] == "PASS" for item in candidates)
    has_passed_contact = passed_contacts > 0
    actual_fu = passed_contacts if all_sources_checked or has_passed_contact else None
    actual_fu_status: EvidenceStatus = "PASS" if all_sources_checked else "NOT_RUN"
    actual_fu_reason = None if all_sources_checked else "fu_portal_verification_not_run"
    search_period: SearchPeriodPayload = {
        "start": search_run.search_period_start,
        "end": search_run.search_period_end,
        "status": "PASS" if search_run.search_period_start is not None else "NOT_RUN",
        "reason": None
        if search_run.search_period_start is not None
        else search_run.search_period_reason,
    }
    source_message_ids = search_run.source_message_ids or (search_run.source_run_id,)
    return {
        "batch_id": stable_batch_id(
            search_run.actor, search_run.source_run_id, search_run.executed_at
        ),
        "actor": search_run.actor,
        "actor_label": contract.actors[search_run.actor],
        "actor_evidence": search_run.actor_evidence,
        "company": search_run.company,
        "position": search_run.position,
        "channels": sorted(set(search_run.channels)),
        "executed_at": search_run.executed_at.isoformat(),
        "batch_grouping": {
            "status": "PASS" if len(source_message_ids) > 1 else "NOT_RUN",
            "reason": search_run.batch_grouping_reason,
            "message_count": len(source_message_ids),
            "message_ids": list(source_message_ids),
        },
        "search_period": search_period,
        "candidate_counts": candidate_counts,
        "candidate_counts_status": ("PASS" if search_run.candidate_counts_complete else "NOT_RUN"),
        "candidate_counts_reason": (
            None if search_run.candidate_counts_complete else search_run.candidate_counts_reason
        ),
        "raw_candidates": raw_count if search_run.candidate_counts_complete else None,
        "unique_candidates": len(candidates),
        "score_buckets": (
            {
                band: _count_score_band(candidates, contract.score_bands[band])
                for band in ("90_plus", "80s", "70s")
            }
            if score_status == "PASS"
            else {"90_plus": None, "80s": None, "70s": None}
        ),
        "score_status": score_status,
        "score_reason": score_reason,
        "actual_fu": actual_fu,
        "actual_fu_status": actual_fu_status,
        "actual_fu_reason": actual_fu_reason,
        "verification_status": verification_status,
        "verification_reason": verification_reason,
        "candidates": candidates,
        "verification_checks": [
            {
                "source": check.source,
                "status": check.status,
                "checked_at": check.checked_at,
                "reason": check.reason,
            }
            for check in sorted(search_run.verification_checks, key=lambda check: check.source)
        ],
    }


def build_ai_search_payload(
    runs: Sequence[AiSearchRun], contract: EvidenceContract
) -> AiSearchPayload:
    """Build the read-only API payload without turning missing evidence into zero."""

    batches = sorted(
        (build_ai_search_batch(search_run, contract) for search_run in runs),
        key=lambda item: (item["executed_at"], item["batch_id"]),
        reverse=True,
    )
    if not batches:
        status: EvidenceStatus = "NOT_RUN"
        reason = "live_sources_not_connected"
    elif any(item["verification_status"] == "FAIL" for item in batches):
        status, reason = "FAIL", "daily_verification_failed"
    elif all(item["verification_status"] == "PASS" for item in batches):
        status, reason = "PASS", None
    else:
        status, reason = "NOT_RUN", "daily_verification_incomplete"
    return {
        "mode": "LOCAL_SHADOW",
        "contract_version": contract.version,
        "status": status,
        "reason": reason,
        "cadence": contract.cadence,
        "batches": batches,
        "external_effects": dict(contract.external_effects),
    }


def _contact_evidence(contacts: Sequence[ContactEvidence]) -> dict[str, ContactEvidence]:
    grouped: dict[str, list[ContactEvidence]] = {}
    for contact in contacts:
        grouped.setdefault(contact.canonical_key, []).append(contact)
    priority = {"PASS": 0, "FAIL": 1, "NOT_RUN": 2}
    return {
        key: min(items, key=lambda item: (priority[item.status], item.source))
        for key, items in grouped.items()
    }


def _count_score_band(candidates: Sequence[CandidatePayload], bounds: Mapping[str, int]) -> int:
    minimum = bounds["min"]
    maximum = bounds["max"]
    return sum(
        item["score"] is not None and minimum <= item["score"] <= maximum for item in candidates
    )


def _score_state(candidates: Sequence[CandidatePayload]) -> tuple[EvidenceStatus, str | None]:
    if not candidates:
        return "NOT_RUN", "no_parsed_candidates"
    missing = next((item for item in candidates if item["score"] is None), None)
    if missing is not None:
        return "NOT_RUN", missing["score_reason"] or "v5_score_contract_evidence_missing"
    return "PASS", None


def _candidate_payload(
    item: CandidateEvidence,
    contact: ContactEvidence | None,
    checks: Mapping[str, VerificationCheck],
) -> CandidatePayload:
    check = checks.get(contact.source) if contact is not None else None
    contact_status: EvidenceStatus = "NOT_RUN"
    if contact is not None:
        contact_status = (
            contact.status if check is not None and check.status == "PASS" else "NOT_RUN"
        )
    return {
        "canonical_key": item.canonical_key,
        "display_name": item.display_name,
        "source_channel": item.source_channel,
        "profile_url": item.profile_url,
        "education": item.education,
        "experience": item.experience,
        "key_experience": item.key_experience,
        "requirements_evidence": list(item.requirements_evidence),
        "score": item.score,
        "score_status": "PASS" if item.score is not None else "NOT_RUN",
        "score_reason": None if item.score is not None else item.score_reason,
        "why_fit": list(item.why_fit),
        "reverse_match_position": item.reverse_match_position,
        "reverse_match_score": item.reverse_match_score,
        "reverse_match_reason": item.reverse_match_reason,
        "contact_recommendation": item.contact_recommendation,
        "contact_status": contact_status,
        "contact_source": contact.source if contact is not None else None,
        "contacted_at": contact.contacted_at if contact is not None else None,
        "contact_checked_at": check.checked_at if check is not None else None,
        "contact_reference": contact.evidence_reference if contact is not None else None,
        "contact_opinion_evidence": item.contact_opinion_evidence,
        "better_position_exists": item.better_position_exists,
        "better_position": item.better_position,
        "better_position_reason": item.better_position_reason,
    }


def _verification_state(
    search_run: AiSearchRun, contract: EvidenceContract
) -> tuple[EvidenceStatus, str | None]:
    checks = {check.source: check for check in search_run.verification_checks}
    required = contract.required_verification_sources
    if any(checks.get(source) and checks[source].status == "FAIL" for source in required):
        return "FAIL", "source_verification_failed"
    if not all(checks.get(source) and checks[source].status == "PASS" for source in required):
        return "NOT_RUN", "required_sources_not_checked"
    return "PASS", None
