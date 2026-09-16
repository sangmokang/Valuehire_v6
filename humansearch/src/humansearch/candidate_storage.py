"""HS-03.02 v2 candidate identity writes: raw+normalized, transactional, idempotent.

Design contract: docs/engineering/humansearch-hs-0302-storage-v2-goal-2026-09-17.md

Success is not "an INSERT statement ran." Success means: required fields reached
the DB, the transaction committed, and a readback of the stored row matches the
input. A candidate re-observed later is a new row in ``hs_candidate_observations``,
never an overwrite of ``hs_candidates`` — the candidate and the sighting of the
candidate are different things.
"""

from __future__ import annotations

import hmac as hmac_lib
import re
import sqlite3
import time
import unicodedata
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Final, Literal
from urllib.parse import urlsplit

Channel = Literal["saramin", "jobkorea", "linkedin_rps"]
RecordOutcome = Literal["candidate_created", "observation_added", "duplicate_observation"]

ALLOWED_CHANNELS: Final[tuple[str, ...]] = ("saramin", "jobkorea", "linkedin_rps")
_MAX_FIELD_CHARS: Final = 512
_CONTROL_CHARACTERS: Final = re.compile(r"[\x00-\x1f\x7f-\x9f]")
_NORMALIZATION_FORM: Final = "NFC"
_DESIGNATOR_INDEX: Final = 10  # "YYYY-MM-DD" 다음 자리 = T/t
_RFC3339: Final = re.compile(
    r"\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])"
    r"[Tt]([01]\d|2[0-3]):[0-5]\d:[0-5]\d(\.\d+)?"
    r"([Zz]|[+-]([01]\d|2[0-3]):[0-5]\d)"
)
_EMAIL: Final = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
_BUSY: Final = "SQLITE_BUSY"
_MAX_RETRIES: Final = 5
_RETRY_BACKOFF_SECONDS: Final = 0.05
_KEY_DOMAIN: Final = b"hs-candidate-key-v2"
_FIELD_SEPARATOR: Final = b"\x1f"


class CandidateStorageError(ValueError):
    """Closed candidate storage error without leaking raw PII in the message."""


class CandidateStorageRetryExhausted(CandidateStorageError):
    """Raised when SQLITE_BUSY persists past the retry cap — never hang, never lie."""


@dataclass(frozen=True, slots=True)
class CandidateObservationInput:
    position_ref: str
    channel: Channel
    candidate_ref: str
    observed_at: str
    ingestion_id: str
    email: str | None = None
    profile_url: str | None = None


@dataclass(frozen=True, slots=True)
class CandidateRecord:
    """Read back after commit — proves the stored row, not just that an insert ran."""

    candidate_id: int
    position_ref: str
    channel: str
    candidate_ref_raw: str
    candidate_ref_normalized: str
    email_raw: str | None
    email_normalized: str | None
    profile_url_raw: str | None
    profile_url_normalized: str | None


@dataclass(frozen=True, slots=True)
class RecordResult:
    outcome: RecordOutcome
    candidate: CandidateRecord
    observation_id: int


@dataclass(frozen=True, slots=True)
class _Validated:
    position_ref: str
    channel: str
    candidate_ref_raw: str
    candidate_ref_normalized: str
    observed_at: str
    ingestion_id: str
    email_raw: str | None
    email_normalized: str | None
    profile_url_raw: str | None
    profile_url_normalized: str | None


def record_candidate_observation(
    db_path: Path,
    record: CandidateObservationInput,
    *,
    hmac_key: bytes | None = None,
) -> RecordResult:
    """Validate, write candidate+observation in one transaction, then read back to confirm.

    ``candidate_ref`` is the only mandatory identity field (every channel gives one).
    ``email``/``profile_url`` are optional evidence: omitted is stored as NULL, never
    fabricated; when given, they must parse as a plausible email/URL before anything
    is written. ``hmac_key`` is an optional secondary fingerprint only — never the
    lookup key, never required for a write to succeed.
    """
    validated = _validate(record)
    # sqlite3's own `timeout` kwarg is a second, internal busy-retry loop — leaving it at
    # sqlite3's 5s default would multiply with `_write_with_retry` below (up to 6x the
    # wait per call). Keep it near-zero so SQLITE_BUSY surfaces immediately and our own
    # bounded retry loop is the only place that waits.
    connection = sqlite3.connect(db_path, timeout=0.0, check_same_thread=False)
    try:
        return _write_with_retry(connection, validated, hmac_key)
    finally:
        connection.close()


def _validate(record: CandidateObservationInput) -> _Validated:
    position_ref = _required_field(record.position_ref, "position_ref")
    channel = _required_field(record.channel, "channel")
    if channel not in ALLOWED_CHANNELS:
        raise CandidateStorageError("channel is not an allowed portal channel")
    candidate_ref_raw = _required_field(record.candidate_ref, "candidate_ref")
    ingestion_id = _required_field(record.ingestion_id, "ingestion_id")
    observed_at = _required_field(record.observed_at, "observed_at")
    _validate_observed_at(observed_at)
    email_raw = _optional_email(record.email)
    profile_url_raw = _optional_url(record.profile_url)
    return _Validated(
        position_ref=position_ref,
        channel=channel,
        candidate_ref_raw=candidate_ref_raw,
        candidate_ref_normalized=_normalize_generic(candidate_ref_raw),
        observed_at=observed_at,
        ingestion_id=ingestion_id,
        email_raw=email_raw,
        email_normalized=_normalize_email(email_raw) if email_raw is not None else None,
        profile_url_raw=profile_url_raw,
        profile_url_normalized=_normalize_url(profile_url_raw) if profile_url_raw is not None else None,
    )


def _required_field(value: str, label: str) -> str:
    if _CONTROL_CHARACTERS.search(value) is not None:
        raise CandidateStorageError(f"{label} must not contain control characters")
    cleaned = unicodedata.normalize(_NORMALIZATION_FORM, value.strip())
    if not cleaned:
        raise CandidateStorageError(f"{label} must not be blank")
    if len(cleaned) > _MAX_FIELD_CHARS:
        raise CandidateStorageError(f"{label} is too long")
    return cleaned


def _validate_observed_at(observed_at: str) -> None:
    """Check both RFC3339 shape and the actual calendar instant (rejects e.g. 24:00)."""
    if _RFC3339.fullmatch(observed_at) is None:
        raise CandidateStorageError("observed_at must be an RFC3339 timestamp")
    try:
        parsed = datetime.fromisoformat(_isoformat_ready(observed_at))
    except ValueError as exc:
        raise CandidateStorageError("observed_at is not a real instant") from exc
    if parsed.tzinfo is None:
        raise CandidateStorageError("observed_at must carry a UTC offset")


def _isoformat_ready(observed_at: str) -> str:
    body = observed_at
    if body.endswith("z"):
        body = body[:-1] + "Z"
    if len(body) > _DESIGNATOR_INDEX and body[_DESIGNATOR_INDEX] == "t":
        body = body[:_DESIGNATOR_INDEX] + "T" + body[_DESIGNATOR_INDEX + 1 :]
    return body


def _optional_email(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = _required_field(value, "email")
    if _EMAIL.fullmatch(cleaned) is None:
        raise CandidateStorageError("email is not a valid address")
    return cleaned


def _optional_url(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = _required_field(value, "profile_url")
    parts = urlsplit(cleaned)
    if parts.scheme not in ("http", "https") or not parts.netloc:
        raise CandidateStorageError("profile_url must be an http(s) URL")
    return cleaned


def _normalize_generic(value: str) -> str:
    return unicodedata.normalize(_NORMALIZATION_FORM, value.strip())


def _normalize_email(value: str) -> str:
    return _normalize_generic(value).lower()


def _normalize_url(value: str) -> str:
    parts = urlsplit(_normalize_generic(value))
    scheme = parts.scheme.lower()
    netloc = parts.netloc.lower()
    path = parts.path.rstrip("/") or "/"
    return f"{scheme}://{netloc}{path}"


def _candidate_key_hmac(key: bytes, v: _Validated) -> str:
    """Optional secondary fingerprint only — never used for lookup or as a gate."""
    message = bytearray(_KEY_DOMAIN)
    for field in (v.position_ref, v.channel, v.candidate_ref_normalized):
        message += _FIELD_SEPARATOR + field.encode("utf-8")
    return hmac_lib.new(key, bytes(message), "sha256").hexdigest()


def _write_with_retry(
    connection: sqlite3.Connection, v: _Validated, hmac_key: bytes | None
) -> RecordResult:
    attempt = 0
    while True:
        try:
            return _write_once(connection, v, hmac_key)
        except sqlite3.OperationalError as exc:
            error_name = getattr(exc, "sqlite_errorname", None)
            if error_name != _BUSY or attempt >= _MAX_RETRIES:
                if error_name == _BUSY:
                    raise CandidateStorageRetryExhausted("db write lock wait exceeded") from None
                raise
            time.sleep(_RETRY_BACKOFF_SECONDS * (attempt + 1))
            attempt += 1


def _write_once(connection: sqlite3.Connection, v: _Validated, hmac_key: bytes | None) -> RecordResult:
    connection.execute("pragma foreign_keys = on")
    connection.execute("begin immediate")
    try:
        candidate_id, created = _upsert_candidate(connection, v, hmac_key)
        observation_id, obs_outcome = _insert_observation(connection, candidate_id, v)
        connection.commit()
    except BaseException:
        _rollback(connection)
        raise
    candidate = _read_back_candidate(connection, candidate_id, v)
    outcome: RecordOutcome
    if created:
        outcome = "candidate_created"
    elif obs_outcome == "duplicate":
        outcome = "duplicate_observation"
    else:
        outcome = "observation_added"
    return RecordResult(outcome=outcome, candidate=candidate, observation_id=observation_id)


def _upsert_candidate(
    connection: sqlite3.Connection, v: _Validated, hmac_key: bytes | None
) -> tuple[int, bool]:
    key_hmac = _candidate_key_hmac(hmac_key, v) if hmac_key is not None else None
    try:
        cursor = connection.execute(
            """
            insert into hs_candidates
              (position_ref, channel, candidate_ref_raw, candidate_ref_normalized,
               email_raw, email_normalized, profile_url_raw, profile_url_normalized,
               candidate_key_hmac)
            values (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                v.position_ref,
                v.channel,
                v.candidate_ref_raw,
                v.candidate_ref_normalized,
                v.email_raw,
                v.email_normalized,
                v.profile_url_raw,
                v.profile_url_normalized,
                key_hmac,
            ),
        )
        assert cursor.lastrowid is not None
        return cursor.lastrowid, True
    except sqlite3.IntegrityError as exc:
        if "unique" not in str(exc).lower():
            raise
        row = connection.execute(
            """
            select candidate_id from hs_candidates
             where position_ref = ? and channel = ? and candidate_ref_normalized = ?
            """,
            (v.position_ref, v.channel, v.candidate_ref_normalized),
        ).fetchone()
        if row is None:
            raise CandidateStorageError("candidate upsert conflict without a matching row") from exc
        _backfill_missing_evidence(connection, row[0], v)
        return row[0], False


def _backfill_missing_evidence(connection: sqlite3.Connection, candidate_id: int, v: _Validated) -> None:
    """Fill only NULL evidence gaps — never overwrite a previously recorded raw value."""
    if v.email_raw is not None:
        connection.execute(
            """
            update hs_candidates
               set email_raw = coalesce(email_raw, ?), email_normalized = coalesce(email_normalized, ?)
             where candidate_id = ?
            """,
            (v.email_raw, v.email_normalized, candidate_id),
        )
    if v.profile_url_raw is not None:
        connection.execute(
            """
            update hs_candidates
               set profile_url_raw = coalesce(profile_url_raw, ?),
                   profile_url_normalized = coalesce(profile_url_normalized, ?)
             where candidate_id = ?
            """,
            (v.profile_url_raw, v.profile_url_normalized, candidate_id),
        )


def _insert_observation(
    connection: sqlite3.Connection, candidate_id: int, v: _Validated
) -> tuple[int, Literal["inserted", "duplicate"]]:
    try:
        cursor = connection.execute(
            """
            insert into hs_candidate_observations
              (candidate_id, source_type, source_url_raw, source_url_normalized,
               observed_at, ingestion_id)
            values (?, ?, ?, ?, ?, ?)
            """,
            (
                candidate_id,
                v.channel,
                v.profile_url_raw,
                v.profile_url_normalized,
                v.observed_at,
                v.ingestion_id,
            ),
        )
        assert cursor.lastrowid is not None
        return cursor.lastrowid, "inserted"
    except sqlite3.IntegrityError as exc:
        if "unique" not in str(exc).lower():
            raise
        row = connection.execute(
            """
            select observation_id from hs_candidate_observations
             where candidate_id = ? and ingestion_id = ?
            """,
            (candidate_id, v.ingestion_id),
        ).fetchone()
        if row is None:
            raise CandidateStorageError("observation upsert conflict without a matching row") from exc
        return row[0], "duplicate"


def _read_back_candidate(connection: sqlite3.Connection, candidate_id: int, v: _Validated) -> CandidateRecord:
    row = connection.execute(
        """
        select candidate_id, position_ref, channel, candidate_ref_raw, candidate_ref_normalized,
               email_raw, email_normalized, profile_url_raw, profile_url_normalized
          from hs_candidates where candidate_id = ?
        """,
        (candidate_id,),
    ).fetchone()
    if row is None:
        raise CandidateStorageError("candidate row missing after commit")
    record = CandidateRecord(*row)
    if record.candidate_ref_normalized != v.candidate_ref_normalized:
        raise CandidateStorageError("readback mismatch: stored row does not match input")
    return record


def _rollback(connection: sqlite3.Connection) -> None:
    """Best-effort rollback — a connection already broken by the failure must not mask it."""
    try:
        connection.execute("rollback")
    except Exception:  # noqa: BLE001, S110 -- intentional best-effort swallow
        pass
