"""HS-03.02 candidate identity writes; contract: docs/engineering/humansearch-hs-0302-candidate-identity-goal-2026-09-15.md."""

from __future__ import annotations

import errno
import fcntl
import hmac
import os
import re
import sqlite3
import stat
import sys
import threading
import unicodedata
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Final, Literal

from humansearch.storage_schema import (
    ApprovedDb,
    StorageSchemaError,
    _inside_git_worktree,
    _verify_path,
    approved_db,
)

Channel = Literal["saramin", "jobkorea", "linkedin_rps"]
RecordOutcome = Literal["inserted", "duplicate"]

ALLOWED_CHANNELS: Final[tuple[str, ...]] = ("saramin", "jobkorea", "linkedin_rps")

_KEY_DOMAIN: Final = b"hs-candidate-key-v2"
_REF_DOMAIN: Final = b"hs-candidate-ref-v1"
_FIELD_SEPARATOR: Final = b"\x1f"
_LENGTH_PREFIX_BYTES: Final = 4
_DESIGNATOR_INDEX: Final = 10  # "YYYY-MM-DD" 다음 자리 = T/t
_MIN_KEY_BYTES: Final = 32
_MAX_FIELD_CHARS: Final = 512
_PRIMARY_KEY_CONSTRAINT: Final = "SQLITE_CONSTRAINT_PRIMARYKEY"
_KEY_FILE_MODE: Final = 0o600
_KEY_DIR_MODE: Final = 0o700
_DB_FILE_MODE: Final = 0o600
_DB_DIR_MODE: Final = 0o700
_SIDECAR_SUFFIXES: Final = ("-journal", "-wal", "-shm")
_BUSY: Final = "SQLITE_BUSY"
_LOCK_WAIT_SECONDS: Final = 5.0
_CONNECT_IDENTITY_LOCK = threading.Lock()
_CONTROL_CHARACTERS: Final = re.compile(r"[\x00-\x1f\x7f-\x9f]")
_NORMALIZATION_FORM: Final = "NFC"
_RFC3339: Final = re.compile(
    r"\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])"
    r"[Tt]([01]\d|2[0-3]):[0-5]\d:[0-5]\d(\.\d+)?"
    r"([Zz]|[+-]([01]\d|2[0-3]):[0-5]\d)"
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
    """HMAC the domain-tagged, length-prefixed UTF-8 values of all three fields."""
    message = bytearray(_KEY_DOMAIN)
    for field in (position_ref, channel, candidate_ref):
        raw = field.encode("utf-8")
        message += len(raw).to_bytes(_LENGTH_PREFIX_BYTES, "big")
        message += raw
    return hmac.new(key, bytes(message), "sha256").hexdigest()


def record_candidate_identity(
    db_path: Path,
    record: CandidateIdentityInput,
    *,
    hmac_key_path: Path,
    approved_root: Path,
) -> RecordOutcome:
    """Record one identity under the caller's initialized, approved storage root."""
    position_ref, channel, candidate_ref = _validated_fields(record)
    _verify_db_boundary(db_path, approved_root)
    key = _load_hmac_key(hmac_key_path, db_path)
    return _insert_once(
        db_path,
        approved_root=approved_root,
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
    if _CONTROL_CHARACTERS.search(value) is not None:
        raise CandidateIdentityError(f"{label} must not contain control characters")
    cleaned = unicodedata.normalize(_NORMALIZATION_FORM, value.strip())
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
    _validated_observed_at(_required_field(record.observed_at, "observed_at"))
    return position_ref, channel, candidate_ref


def _validated_observed_at(observed_at: str) -> None:
    """Check both RFC3339 shape and the actual calendar instant."""
    if _RFC3339.fullmatch(observed_at) is None:
        raise CandidateIdentityError("observed_at must be an RFC3339 timestamp")
    try:
        parsed = datetime.fromisoformat(_isoformat_ready(observed_at))
    except ValueError as exc:
        raise CandidateIdentityError("observed_at is not a real instant") from exc
    if parsed.tzinfo is None:
        raise CandidateIdentityError("observed_at must carry a UTC offset")


def _isoformat_ready(observed_at: str) -> str:
    """Uppercase accepted RFC3339 designators for datetime.fromisoformat."""
    body = observed_at
    if body.endswith("z"):
        body = body[:-1] + "Z"
    if len(body) > _DESIGNATOR_INDEX and body[_DESIGNATOR_INDEX] == "t":
        body = body[:_DESIGNATOR_INDEX] + "T" + body[_DESIGNATOR_INDEX + 1 :]
    return body


def _closed_os_error(message: str, exc: OSError) -> CandidateIdentityError:
    """Discard the path-bearing OS cause; retain only the errno name."""
    code = errno.errorcode.get(exc.errno or 0, "EUNKNOWN")
    return CandidateIdentityError(f"{message} ({code})")


def _verify(path: Path, *, expected_mode: int, label: str) -> None:
    """Reuse the HS-03.01 guard without exposing its path-bearing cause."""
    try:
        _verify_path(path, expected_mode=expected_mode, label=label)
    except CandidateIdentityError:
        raise
    except StorageSchemaError as exc:
        raise CandidateIdentityError(str(exc)) from None


def _reject_symlinked_chain(path: Path, *, label: str) -> None:
    """Reject links in every path component, including ancestors."""
    for candidate in (path, *path.parents):
        if candidate.is_symlink():
            raise CandidateIdentityError(f"{label} must not contain a symlink")


def _verify_db_location(db_path: Path) -> Path:
    """Resolve the complete guarded DB path before comparing protected roots."""
    _reject_symlinked_chain(db_path, label="db path")
    try:
        return db_path.resolve(strict=True).parent
    except OSError as exc:
        raise _closed_os_error("db file is missing", exc) from None


def _load_hmac_key(hmac_key_path: Path, db_path: Path) -> bytes:
    """Read the HMAC key from its own protected directory. 암묵 생성은 하지 않는다."""
    key_dir = hmac_key_path.parent
    _verify(key_dir, expected_mode=_KEY_DIR_MODE, label="hmac key directory")
    _verify(hmac_key_path, expected_mode=_KEY_FILE_MODE, label="hmac key")
    if not hmac_key_path.is_file():
        raise CandidateIdentityError("hmac key must be a regular file")
    _reject_symlinked_chain(hmac_key_path, label="hmac key path")
    try:
        key_root = key_dir.resolve(strict=True)
    except OSError as exc:
        raise _closed_os_error("hmac key directory is missing", exc) from None
    db_root = _verify_db_location(db_path)
    if key_root.is_relative_to(db_root) or db_root.is_relative_to(key_root):
        raise CandidateIdentityError("hmac key must not share the db protected root")
    try:
        key = hmac_key_path.read_bytes()
    except OSError as exc:
        raise _closed_os_error("hmac key is unreadable", exc) from None
    if len(key) < _MIN_KEY_BYTES:
        raise CandidateIdentityError(f"hmac key must be at least {_MIN_KEY_BYTES} bytes")
    return key


def _verify_db_boundary(db_path: Path, approved_root: Path) -> None:
    """Recheck the initialized DB, root, owner, mode, links, and sidecars before write/commit."""
    approved = _approved_db(db_path, approved_root)
    if approved is None:
        raise CandidateIdentityError("db file is outside the approved root")
    _reject_symlinked_chain(db_path, label="db path")
    _verify(approved_root, expected_mode=_DB_DIR_MODE, label="db directory")
    _verify(db_path, expected_mode=_DB_FILE_MODE, label="db file")
    if not db_path.is_file():
        raise CandidateIdentityError("db file must be a regular file")
    info = db_path.stat(follow_symlinks=False)
    # One inode must have one name inside the protected root.
    if info.st_nlink != 1:
        raise CandidateIdentityError("db file must not have extra hard links")
    # The approved path alone does not prove the approved inode.
    if (info.st_dev, info.st_ino) != (approved.st_dev, approved.st_ino):
        raise CandidateIdentityError("db file is not the approved file")
    if _inside_git_worktree(db_path.parent):
        raise CandidateIdentityError("db file must be outside the git worktree")
    _verify_sidecars(db_path)


def _approved_db(db_path: Path, approved_root: Path) -> ApprovedDb | None:
    """Only initialization's root/path/inode pair is an approval."""
    if not approved_root.is_absolute() or db_path.parent != approved_root:
        return None
    approved = approved_db(approved_root)
    if approved is None or approved.db_path != db_path:
        return None
    return approved


def _verify_sidecars(db_path: Path) -> None:
    """Use one lstat per sidecar so concurrent journal deletion is harmless."""
    for suffix in _SIDECAR_SUFFIXES:
        try:
            info = db_path.with_name(db_path.name + suffix).stat(follow_symlinks=False)
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(info.st_mode):
            raise CandidateIdentityError("sqlite sidecar must not be a symlink")
        if info.st_uid != os.getuid():
            raise CandidateIdentityError("sqlite sidecar owner mismatch")
        if stat.S_IMODE(info.st_mode) != _DB_FILE_MODE:
            raise CandidateIdentityError(f"sqlite sidecar mode must be {_DB_FILE_MODE:04o}")
        if not stat.S_ISREG(info.st_mode):
            raise CandidateIdentityError("sqlite sidecar must be a regular file")
        if info.st_nlink != 1:
            raise CandidateIdentityError("sqlite sidecar must not have extra hard links")


def _insert_once(
    db_path: Path,
    *,
    approved_root: Path,
    key_hmac: str,
    position_ref: str,
    channel: str,
    candidate_ref_hash: str,
) -> RecordOutcome:
    """Insert once under the primary-key constraint, then recheck before commit."""
    _verify_db_boundary(db_path, approved_root)
    connection = _connect_approved_db(db_path, approved_root)
    try:
        main_files = [row[2] for row in connection.execute("pragma database_list") if row[1] == "main"]
        if len(main_files) != 1 or Path(main_files[0]) != db_path:
            raise CandidateIdentityError("opened db is outside the approved root")
        connection.execute("pragma foreign_keys = on")
        try:
            connection.execute("begin immediate")
        except sqlite3.OperationalError as exc:
            if exc.sqlite_errorname != _BUSY:
                raise
            return _outcome_after_lock_wait(connection, key_hmac)
        try:
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
        # A failed recheck rolls back the uncommitted transaction on close.
        _verify_db_boundary(db_path, approved_root)
        connection.execute("commit")
    finally:
        with _CONNECT_IDENTITY_LOCK:
            connection.close()
    return "inserted"


def _regular_open_fds() -> dict[int, tuple[int, int]]:
    """Observe kernel identities of open regular files; unavailable inspection fails closed."""
    try:
        names = os.listdir("/dev/fd")
    except OSError:
        raise CandidateIdentityError("opened db identity is unavailable") from None
    result: dict[int, tuple[int, int]] = {}
    for name in names:
        if not name.isdecimal():
            continue
        fd = int(name)
        try:
            info = os.fstat(fd)
        except OSError as exc:
            if exc.errno == errno.EBADF:  # listing /dev/fd briefly opens its own fd
                continue
            raise CandidateIdentityError("opened db identity is unavailable") from None
        if stat.S_ISREG(info.st_mode):
            result[fd] = (info.st_dev, info.st_ino)
    return result


def _allowed_new_sidecar_fd(fd: int, db_path: Path) -> bool:
    """Permit concurrent SQLite journal/WAL descriptors only inside the approved root."""
    try:
        if sys.platform == "darwin":
            raw_path = fcntl.fcntl(fd, fcntl.F_GETPATH, bytes(1024)).split(b"\x00", 1)[0]
        elif sys.platform.startswith("linux"):
            raw_path = os.fsencode(os.readlink(f"/proc/self/fd/{fd}"))
        else:
            return False
        opened_path = Path(os.fsdecode(raw_path))
        info = os.fstat(fd)
    except (AttributeError, OSError):
        return False
    allowed = {db_path.with_name(db_path.name + suffix) for suffix in _SIDECAR_SUFFIXES}
    return (
        opened_path in allowed
        and info.st_uid == os.getuid()
        and stat.S_IMODE(info.st_mode) == _DB_FILE_MODE
        and info.st_nlink == 1
    )


def _connect_approved_db(db_path: Path, approved_root: Path) -> sqlite3.Connection:
    """No write is allowed until the newly opened SQLite file descriptor matches approval."""
    approved = _approved_db(db_path, approved_root)
    if approved is None:
        raise CandidateIdentityError("db file is outside the approved root")
    with _CONNECT_IDENTITY_LOCK:
        before = _regular_open_fds()
        connection = sqlite3.connect(db_path, isolation_level=None, timeout=_LOCK_WAIT_SECONDS)
        try:
            after = _regular_open_fds()
            opened = [(fd, identity) for fd, identity in after.items() if before.get(fd) != identity]
            main = [fd for fd, identity in opened if identity == (approved.st_dev, approved.st_ino)]
            extras = [fd for fd, identity in opened if identity != (approved.st_dev, approved.st_ino)]
            if len(main) != 1 or not all(_allowed_new_sidecar_fd(fd, db_path) for fd in extras):
                raise CandidateIdentityError("opened db is not the approved file")
            _verify_db_boundary(db_path, approved_root)
            return connection
        except BaseException:
            connection.close()
            raise


def _outcome_after_lock_wait(connection: sqlite3.Connection, key_hmac: str) -> RecordOutcome:
    """After SQLITE_BUSY, return duplicate only if the winning row is visible."""
    try:
        row = connection.execute(
            "select 1 from hs_candidates where candidate_key_hmac = ?", (key_hmac,)
        ).fetchone()
    except sqlite3.OperationalError as exc:
        if exc.sqlite_errorname != _BUSY:
            raise
        raise CandidateIdentityError("db write lock wait exceeded") from None
    if row is not None:
        return "duplicate"
    raise CandidateIdentityError("db write lock wait exceeded")
