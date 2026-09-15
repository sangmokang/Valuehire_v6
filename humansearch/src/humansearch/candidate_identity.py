"""HS-03.02 candidate identity recording on the HS-03.01 SQLite schema.

계약: docs/engineering/humansearch-hs-0302-candidate-identity-goal-2026-09-15.md

중복은 응용 코드의 조회-후-삽입이 아니라 `hs_candidates` 기본키 제약이 막는다.
두 연결이 동시에 조회하면 둘 다 "없음"을 보고 둘 다 넣기 때문이다. 그래서
기본키 값 `candidate_key_hmac` 을 (position_ref, channel, candidate_ref) 세 값의
HMAC 으로 정의하고, INSERT 는 한 번만 한다. 기본키 충돌만 `duplicate` 로 번역하고
다른 무결성 오류는 그대로 올린다.

마이그레이션은 추가하지 않는다. `observed_at` 은 검증만 하고 저장하지 않는다
(열이 없고, 증거 시각은 HS-03.04 가 hs_evidence_manifests 에 기록한다).
"""

from __future__ import annotations

import hmac
import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Literal

from humansearch.storage_schema import StorageSchemaError, _verify_path

Channel = Literal["saramin", "jobkorea", "linkedin_rps"]
RecordOutcome = Literal["inserted", "duplicate"]

ALLOWED_CHANNELS: Final[tuple[str, ...]] = ("saramin", "jobkorea", "linkedin_rps")

_KEY_DOMAIN: Final = b"hs-candidate-key-v1"
_REF_DOMAIN: Final = b"hs-candidate-ref-v1"
_FIELD_SEPARATOR: Final = b"\x1f"
_MIN_KEY_BYTES: Final = 32
_MAX_FIELD_CHARS: Final = 512
_PRIMARY_KEY_CONSTRAINT: Final = "SQLITE_CONSTRAINT_PRIMARYKEY"
_KEY_FILE_MODE: Final = 0o600
_KEY_DIR_MODE: Final = 0o700
_RFC3339: Final = re.compile(
    r"\d{4}-\d{2}-\d{2}[Tt]\d{2}:\d{2}:\d{2}(\.\d+)?([Zz]|[+-]\d{2}:\d{2})"
)


class CandidateIdentityError(StorageSchemaError):
    """Closed candidate identity error that carries no private payload value."""


@dataclass(frozen=True, slots=True)
class CandidateIdentityInput:
    """One observed candidate identity before any evidence is stored."""

    position_ref: str
    channel: Channel
    candidate_ref: str
    observed_at: str


def candidate_key_hmac(key: bytes, position_ref: str, channel: str, candidate_ref: str) -> str:
    """Duplicate-prevention key derived from all three identity fields.

    `\\x1f` 구분자가 필드 경계를 고정한다. 없으면 ("a","bc") 와 ("ab","c") 가
    같은 키가 되어 서로 다른 후보가 한 행으로 합쳐진다.
    """

    message = _FIELD_SEPARATOR.join(
        (
            _KEY_DOMAIN,
            position_ref.encode("utf-8"),
            channel.encode("utf-8"),
            candidate_ref.encode("utf-8"),
        )
    )
    return hmac.new(key, message, "sha256").hexdigest()


def record_candidate_identity(
    db_path: Path,
    record: CandidateIdentityInput,
    *,
    hmac_key_path: Path,
) -> RecordOutcome:
    """Record one candidate identity, returning whether the row was new."""

    position_ref, channel, candidate_ref = _validated_fields(record)
    key = _load_hmac_key(hmac_key_path, db_path)
    return _insert_once(
        db_path,
        key_hmac=candidate_key_hmac(key, position_ref, channel, candidate_ref),
        position_ref=position_ref,
        channel=channel,
        candidate_ref_hash=_candidate_ref_hash(key, candidate_ref),
    )


def _candidate_ref_hash(key: bytes, candidate_ref: str) -> str:
    """Keyed digest of the candidate ref — 평문 sha256 은 추측 가능한 지문이라 쓰지 않는다."""

    message = _REF_DOMAIN + _FIELD_SEPARATOR + candidate_ref.encode("utf-8")
    return hmac.new(key, message, "sha256").hexdigest()


def _required_field(value: str, label: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise CandidateIdentityError(f"{label} must not be blank")
    if len(cleaned) > _MAX_FIELD_CHARS:
        raise CandidateIdentityError(f"{label} is too long")
    return cleaned


def _validated_fields(record: CandidateIdentityInput) -> tuple[str, str, str]:
    position_ref = _required_field(record.position_ref, "position_ref")
    channel = _required_field(record.channel, "channel")
    if channel not in ALLOWED_CHANNELS:
        raise CandidateIdentityError("channel is not an allowed portal channel")
    candidate_ref = _required_field(record.candidate_ref, "candidate_ref")
    observed_at = _required_field(record.observed_at, "observed_at")
    if _RFC3339.fullmatch(observed_at) is None:
        raise CandidateIdentityError("observed_at must be an RFC3339 timestamp")
    return position_ref, channel, candidate_ref


def _verify(path: Path, *, expected_mode: int, label: str) -> None:
    """Reuse the HS-03.01 path guard, re-raised inside this module's closed error."""

    try:
        _verify_path(path, expected_mode=expected_mode, label=label)
    except CandidateIdentityError:
        raise
    except StorageSchemaError as exc:
        raise CandidateIdentityError(str(exc)) from exc


def _load_hmac_key(hmac_key_path: Path, db_path: Path) -> bytes:
    """Read the HMAC key from its own protected directory. 암묵 생성은 하지 않는다."""

    key_dir = hmac_key_path.parent
    _verify(key_dir, expected_mode=_KEY_DIR_MODE, label="hmac key directory")
    _verify(hmac_key_path, expected_mode=_KEY_FILE_MODE, label="hmac key")
    if not hmac_key_path.is_file():
        raise CandidateIdentityError("hmac key must be a regular file")
    if key_dir.resolve(strict=True) == db_path.parent.resolve(strict=True):
        raise CandidateIdentityError("hmac key must not share the db protected root")
    key = hmac_key_path.read_bytes()
    if len(key) < _MIN_KEY_BYTES:
        raise CandidateIdentityError(f"hmac key must be at least {_MIN_KEY_BYTES} bytes")
    return key


def _insert_once(
    db_path: Path,
    *,
    key_hmac: str,
    position_ref: str,
    channel: str,
    candidate_ref_hash: str,
) -> RecordOutcome:
    """Single INSERT. 경쟁은 기본키 제약이 막고, 진 쪽만 duplicate 가 된다."""

    connection = sqlite3.connect(db_path, isolation_level=None)
    try:
        connection.execute("pragma foreign_keys = on")
        connection.execute(
            """
            insert into hs_candidates
              (candidate_key_hmac, position_ref, channel,
               candidate_ref_state, candidate_ref_hash, storage_status)
            values (?, ?, ?, 'observed', ?, 'pending')
            """,
            (key_hmac, position_ref, channel, candidate_ref_hash),
        )
    except sqlite3.IntegrityError as exc:
        if exc.sqlite_errorname == _PRIMARY_KEY_CONSTRAINT:
            return "duplicate"
        raise
    finally:
        connection.close()
    return "inserted"
