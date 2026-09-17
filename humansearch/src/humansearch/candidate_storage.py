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
import threading
import time
import unicodedata
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Final, Literal
from urllib.parse import parse_qsl, urlencode, urlsplit

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
# A linear 5-try/0.05s budget (max ~0.75s total wait) let ordinary contention — not a
# stuck lock — exhaust retries under a burst of concurrent writers for the same
# candidate: an independent adversarial review (2026-09-17) reproduced ~10-30% failure
# at 10-40 concurrent writers with no code change. Exponential backoff with a higher
# cap absorbs realistic bursts while staying bounded (AC-10 still requires a hard
# stop, not indefinite blocking) — worst case is ~6.5s across 10 tries.
_MAX_RETRIES: Final = 10
_RETRY_BACKOFF_BASE_SECONDS: Final = 0.05
_RETRY_BACKOFF_CAP_SECONDS: Final = 1.0
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


_WRITE_LOCK_REGISTRY_LOCK: Final = threading.Lock()
_WRITE_LOCKS: dict[str, threading.Lock] = {}


def _write_lock_for(db_path: Path) -> threading.Lock:
    """One lock per DB path, shared by every in-process caller.

    Without this, N threads all racing `begin immediate` on the same SQLite file
    lose the SQLITE_BUSY lottery independently — an adversarial review (2026-09-17)
    reproduced 10-30% failure at 10-40 concurrent writers this way, even with a
    generous retry budget. Serializing writers in-process turns that thundering herd
    into an orderly queue; the retry/backoff below still exists as a fallback for
    genuine cross-process contention, which this lock cannot see.
    """
    # Resolve first — two differently-spelled paths to the same file (e.g. an
    # unresolved ".." segment) must share one lock, not race through separate ones.
    key = str(db_path.resolve())
    with _WRITE_LOCK_REGISTRY_LOCK:
        lock = _WRITE_LOCKS.get(key)
        if lock is None:
            lock = threading.Lock()
            _WRITE_LOCKS[key] = lock
        return lock


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
        with _write_lock_for(db_path):
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
        candidate_ref_normalized=_normalize_candidate_ref(candidate_ref_raw),
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


def _nfc_strip(value: str) -> str:
    return unicodedata.normalize(_NORMALIZATION_FORM, value.strip())


def _normalize_email(value: str) -> str:
    return _nfc_strip(value).lower()


_WWW_PREFIX: Final = "www."

# Path-case-folding and query-param stripping are only safe for hosts where the
# equivalence rule has actually been verified — currently just LinkedIn's public
# profile pages (case-insensitive vanity slug; tracking params like ?trk=... are
# provably noise). Every other host gets NO path or query canonicalization, on
# purpose: an unverified host's query string might be a real per-candidate
# identifier (e.g. saramin/jobkorea's ?rec_idx=...), and "we don't know what this
# means" must default to "leave it alone," never to "assume it's noise and merge."
#
# History (2026-09-17, three rounds of independent adversarial review):
#   round 1: no query handling at all -> same LinkedIn profile with a different
#            ?trk= value was wrongly split into two candidates.
#   round 2: stripped the WHOLE query string for every host -> two different real
#            saramin candidates (different ?rec_idx=...) were wrongly merged into
#            one row, discarding the second person's identifying URL. This is the
#            worse failure: false-merge loses data and cannot be told apart from a
#            correct merge after the fact, while false-split just costs a
#            recoverable duplicate row (both raw URLs still exist).
#   round 3 (this fix, owner-directed scope narrowing): stop applying ANY
#            general-purpose canonicalization rule to hosts we have not verified.
#            Only linkedin.com gets path/query normalization; everything else is
#            compared on the untouched (scheme+host-cased, www-stripped) URL.
_APPROVED_CANONICALIZATION_HOSTS: Final = frozenset({"linkedin.com"})

_TRACKING_PARAM_NAMES: Final = frozenset({"trk", "ref", "refid", "fbclid", "gclid", "mc_cid", "mc_eid"})
_TRACKING_PARAM_PREFIXES: Final = ("utm_",)


def _is_tracking_param(name: str) -> bool:
    lowered = name.lower()
    return lowered in _TRACKING_PARAM_NAMES or lowered.startswith(_TRACKING_PARAM_PREFIXES)


def _normalize_query(query: str) -> str:
    if not query:
        return ""
    kept = sorted(pair for pair in parse_qsl(query, keep_blank_values=True) if not _is_tracking_param(pair[0]))
    return urlencode(kept)


def _cased_netloc(netloc: str) -> str:
    """Fold case per RFC 3986 (scheme and host are case-insensitive by the URI
    syntax spec itself) — never the userinfo (before an '@') or whatever follows
    a ':' (normally a numeric port, but ``urlsplit`` never validates that — Codex
    V1 5th-round finding, 2026-09-17: a non-numeric "port" position, e.g. from a
    malformed URL, was getting case-folded like a real hostname). Neither
    userinfo nor a port-position string is case-insensitive by the URI spec, and
    either could be a real per-candidate identifier on a host we have not
    verified."""
    userinfo, sep, host_port = netloc.rpartition("@")
    host, colon, port = host_port.partition(":")
    return f"{userinfo}{sep}{host.lower()}{colon}{port}"


def _normalize_url(value: str) -> str:
    parts = urlsplit(_nfc_strip(value))
    scheme = parts.scheme.lower()
    netloc = _cased_netloc(parts.netloc)
    approved_netloc = netloc.removeprefix(_WWW_PREFIX)
    if approved_netloc not in _APPROVED_CANONICALIZATION_HOSTS:
        # Unverified host: fold only what RFC 3986 defines as case-insensitive
        # (scheme, host) — that is a URI-syntax fact, not a guess. Do NOT also
        # assume "www.X" and "X" are the same host: that equivalence is a
        # DNS/CNAME convention, not URI syntax, so treating it as free is a
        # business identity-policy call this codebase must not make unilaterally
        # for a channel nobody has verified (round 6, 2026-09-17, external
        # review: the earlier "DNS convention is safe" justification blurred a
        # technical fact with a business decision). Path (including a trailing
        # slash), query, and fragment stay untouched for the same reason as the
        # earlier rounds' fixes.
        query_suffix = f"?{parts.query}" if parts.query else ""
        fragment_suffix = f"#{parts.fragment}" if parts.fragment else ""
        return f"{scheme}://{netloc}{parts.path}{query_suffix}{fragment_suffix}"
    path = (parts.path.rstrip("/") or "/").lower()
    query = _normalize_query(parts.query)
    suffix = f"?{query}" if query else ""
    return f"{scheme}://{approved_netloc}{path}{suffix}"


def _normalize_candidate_ref(value: str) -> str:
    """URL-shaped candidate refs (e.g. a LinkedIn profile URL used as the per-channel
    identifier) must dedup the same way ``profile_url`` does — otherwise a tracking
    query param or trailing slash silently splits one real candidate into two rows
    (reproduced 2026-09-17; see the goal doc's adversarial-check log)."""
    cleaned = _nfc_strip(value)
    parts = urlsplit(cleaned)
    if parts.scheme in ("http", "https") and parts.netloc:
        return _normalize_url(cleaned)
    return cleaned


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
            backoff = min(_RETRY_BACKOFF_BASE_SECONDS * (2**attempt), _RETRY_BACKOFF_CAP_SECONDS)
            time.sleep(backoff)
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
