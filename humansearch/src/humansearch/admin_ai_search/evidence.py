"""Deterministic AI Search batch, score-band, and FU evidence projection."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Literal, TypedDict, cast
from zoneinfo import ZoneInfo

EvidenceStatus = Literal["PASS", "FAIL", "NOT_RUN"]
ContactRecommendation = Literal["STRONG", "NORMAL", "HOLD"]
KST = ZoneInfo("Asia/Seoul")


class ScoreBuckets(TypedDict):
    """Mutually exclusive score bands displayed in the batch list."""

    score_90_plus: int
    score_80s: int
    score_70s: int


class CandidatePayload(TypedDict):
    canonical_key: str
    display_name: str
    source_channel: str
    profile_url: str
    education: str
    experience: str
    score: int
    why_fit: list[str]
    reverse_match_position: str | None
    reverse_match_score: int | None
    reverse_match_reason: str
    contact_recommendation: str
    contact_status: EvidenceStatus


class VerificationPayload(TypedDict):
    source: str
    status: EvidenceStatus
    checked_at: str | None
    reason: str | None


class BatchPayload(TypedDict):
    batch_id: str
    actor: str
    actor_label: str
    company: str
    position: str
    channels: list[str]
    executed_at: str
    raw_candidates: int
    unique_candidates: int
    score_buckets: dict[str, int]
    actual_fu: int
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
    education: str
    experience: str
    score: int
    why_fit: tuple[str, ...]
    reverse_match_position: str | None
    reverse_match_score: int | None
    reverse_match_reason: str
    contact_recommendation: ContactRecommendation

    def __post_init__(self) -> None:
        if len(self.canonical_key) != 64 or any(char not in "0123456789abcdef" for char in self.canonical_key):
            raise ValueError("canonical_key must be a lowercase SHA-256 hex digest")
        for field in ("display_name", "source_channel", "profile_url", "education", "experience"):
            _nonblank(cast(str, getattr(self, field)), field)
        if isinstance(self.score, bool) or not isinstance(self.score, int) or not 0 <= self.score <= 100:
            raise ValueError("score must be an integer from 0 to 100")
        if not self.why_fit or any(not item.strip() for item in self.why_fit):
            raise ValueError("why_fit must contain evidence")
        if self.reverse_match_score is not None and not 0 <= self.reverse_match_score <= 100:
            raise ValueError("reverse_match_score must be between 0 and 100")
        if self.contact_recommendation not in {"STRONG", "NORMAL", "HOLD"}:
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

    def __post_init__(self) -> None:
        for field in ("actor", "source_run_id", "company", "position"):
            _nonblank(cast(str, getattr(self, field)), field)
        if not self.channels or any(not channel.strip() for channel in self.channels):
            raise ValueError("channels must contain non-blank values")
        if self.executed_at.tzinfo is None or self.executed_at.utcoffset() is None:
            raise ValueError("executed_at must be timezone-aware")
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
        key=lambda candidate: (-candidate.score, candidate.source_channel, candidate.profile_url),
    ):
        deduplicated.setdefault(item.canonical_key, item)
    contacts = _contact_statuses(search_run.contacts, search_run.verification_checks)
    candidates = [
        _candidate_payload(item, contacts.get(item.canonical_key, "NOT_RUN"))
        for item in sorted(deduplicated.values(), key=lambda item: (-item.score, item.canonical_key))
    ]
    verification_status, verification_reason = _verification_state(search_run, contract)
    return {
        "batch_id": stable_batch_id(search_run.actor, search_run.source_run_id, search_run.executed_at),
        "actor": search_run.actor,
        "actor_label": contract.actors[search_run.actor],
        "company": search_run.company,
        "position": search_run.position,
        "channels": sorted(set(search_run.channels)),
        "executed_at": search_run.executed_at.isoformat(),
        "raw_candidates": len(search_run.candidates),
        "unique_candidates": len(candidates),
        "score_buckets": {
            band: _count_score_band(candidates, contract.score_bands[band])
            for band in ("90_plus", "80s", "70s")
        },
        "actual_fu": sum(item["contact_status"] == "PASS" for item in candidates),
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


def _contact_statuses(
    contacts: Sequence[ContactEvidence], checks: Sequence[VerificationCheck]
) -> dict[str, EvidenceStatus]:
    source_checks = {check.source: check.status for check in checks}
    grouped: dict[str, list[EvidenceStatus]] = {}
    for contact in contacts:
        source_status = source_checks.get(contact.source, "NOT_RUN")
        status = contact.status if source_status == "PASS" else source_status
        grouped.setdefault(contact.canonical_key, []).append(status)
    result: dict[str, EvidenceStatus] = {}
    for key, statuses in grouped.items():
        if "PASS" in statuses:
            result[key] = "PASS"
        elif "FAIL" in statuses:
            result[key] = "FAIL"
        else:
            result[key] = "NOT_RUN"
    return result


def _count_score_band(
    candidates: Sequence[CandidatePayload], bounds: Mapping[str, int]
) -> int:
    minimum = bounds["min"]
    maximum = bounds["max"]
    return sum(minimum <= item["score"] <= maximum for item in candidates)


def _candidate_payload(item: CandidateEvidence, contact_status: EvidenceStatus) -> CandidatePayload:
    return {
        "canonical_key": item.canonical_key,
        "display_name": item.display_name,
        "source_channel": item.source_channel,
        "profile_url": item.profile_url,
        "education": item.education,
        "experience": item.experience,
        "score": item.score,
        "why_fit": list(item.why_fit),
        "reverse_match_position": item.reverse_match_position,
        "reverse_match_score": item.reverse_match_score,
        "reverse_match_reason": item.reverse_match_reason,
        "contact_recommendation": item.contact_recommendation,
        "contact_status": contact_status,
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
