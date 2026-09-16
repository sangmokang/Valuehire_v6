"""HS-03.02 candidate identity writes; contract: docs/engineering/humansearch-hs-0302-candidate-identity-goal-2026-09-15.md."""

from __future__ import annotations

import errno
import hashlib
import hmac
import os
import re
import sqlite3
import stat
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
_KEY_FINGERPRINT_DOMAIN: Final = b"hs-key-fingerprint-v1"
_KEY_FINGERPRINT_FILENAME: Final = "hs-key-fingerprint"
_KEY_FINGERPRINT_MODE: Final = 0o600
_CONTROL_CHARACTERS: Final = re.compile(r"[\x00-\x1f\x7f-\x9f]")
_NORMALIZATION_FORM: Final = "NFC"
_RFC3339: Final = re.compile(
    r"\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])"
    r"[Tt]([01]\d|2[0-3]):[0-5]\d:[0-5]\d(\.\d+)?"
    r"([Zz]|[+-]([01]\d|2[0-3]):[0-5]\d)"
)


# 승인 root 당 프로세스 수명 동안 단 하나의 쓰기 커넥션만 연다(단일 writer 브로커,
# goal 결정 카드 AC-8). 재연결 경합 창은 매 쓰기마다가 아니라 프로세스당 최초 1회로만
# 좁아진다 — stdlib sqlite3 는 fd 를 노출하지 않으므로 그 1회조차 native 하게 증명할
# 수는 없다(BLOCKED, 후속 WU: apsw 커스텀 VFS 승인 뒤 재검토).
_BROKER_CONNECTIONS: dict[Path, sqlite3.Connection] = {}

# 승인 root 별로 독립된 락을 쓴다 — 프로세스 전역에 락 하나만 두면 서로 무관한 DB에
# 대한 기록까지 전부 직렬화된다(Codex V1 2026-09-17 발견: root A 쓰기가 느릴 때 root B
# 쓰기가 불필요하게 대기하는 것을 실측). 이 레지스트리 자체에 대한 접근만 별도로
# 잠근다 — 개별 root 락을 실제로 쥐는 동안은 이 메타 락을 쥐지 않는다.
_ROOT_LOCK_REGISTRY_LOCK = threading.Lock()
_ROOT_LOCKS: dict[Path, threading.Lock] = {}


def _root_lock(approved_root: Path) -> threading.Lock:
    """One lock per approved root, created lazily and reused for the process lifetime."""
    with _ROOT_LOCK_REGISTRY_LOCK:
        lock = _ROOT_LOCKS.get(approved_root)
        if lock is None:
            lock = threading.Lock()
            _ROOT_LOCKS[approved_root] = lock
        return lock


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
    """Record one identity under the caller's initialized, approved storage root.

    승인 root 마다 커넥션이 하나뿐이므로(단일 writer), 그 root 에 대한 기록은 한 번에
    하나만 진행되도록 root 별 락으로 감싼다 — 그래야 다른 스레드가 같은 커넥션을 동시에
    호출하는 일(sqlite3 는 스레드 안전하지 않다)도, 검사와 커넥션 획득 사이의 경합도 없다.
    락을 root 별로 나누는 이유: 프로세스 전역에 락 하나만 두면 서로 무관한 root 에 대한
    기록까지 전부 직렬화된다(위 `_root_lock` 주석 참고).
    """
    with _root_lock(approved_root):
        position_ref, channel, candidate_ref = _validated_fields(record)
        _verify_db_boundary(db_path, approved_root)
        key = _load_hmac_key(hmac_key_path, db_path)
        _bind_key_epoch(approved_root, key)
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


def _key_fingerprint(key: bytes) -> str:
    """Public, one-way fingerprint of which key produced this db's rows — never the key itself."""
    return hashlib.sha256(_KEY_FINGERPRINT_DOMAIN + key).hexdigest()


def _bind_key_epoch(approved_root: Path, key: bytes) -> None:
    """Bootstrap this db's key fingerprint on first use; reject any other key before insert.

    키 회전은 별도 migration/readback 계약 없이는 허용하지 않는다(goal 결정 카드 4) — 지문이
    다르면 새 candidate_key_hmac 이 PK 제약을 우회해 같은 실제 후보가 중복 행으로 새므로,
    다른 키는 insert 이전에 무조건 닫힌 오류로 거부한다.
    """
    fingerprint_path = approved_root / _KEY_FINGERPRINT_FILENAME
    current = _key_fingerprint(key)
    try:
        fd = os.open(fingerprint_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, _KEY_FINGERPRINT_MODE)
    except FileExistsError:
        pass
    else:
        try:
            os.write(fd, current.encode("ascii"))
        finally:
            os.close(fd)
        return
    _reject_symlinked_chain(fingerprint_path, label="hmac key epoch file")
    _verify(fingerprint_path, expected_mode=_KEY_FINGERPRINT_MODE, label="hmac key epoch file")
    if not fingerprint_path.is_file():
        raise CandidateIdentityError("hmac key epoch file must be a regular file")
    try:
        stored = fingerprint_path.read_text(encoding="ascii").strip()
    except OSError as exc:
        raise _closed_os_error("hmac key epoch file is unreadable", exc) from None
    if stored != current:
        raise CandidateIdentityError("hmac key does not match this db's registered key")


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
    try:  # 검사 사이에 파일이 옮겨져도 OS 오류가 경로째 새면 안 된다(V1 8회차 결함 1)
        info = db_path.stat(follow_symlinks=False)
    except OSError as exc:
        raise _closed_os_error("db file is missing", exc) from None
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
    """Insert once under the primary-key constraint, then recheck before commit.

    브로커 커넥션은 프로세스 수명 동안 재사용되므로(단일 writer), 이 함수는 더 이상
    `connection.close()` 로 롤백을 대신할 수 없다 — 실패하는 모든 경로에서 명시적으로
    `rollback` 해야 다음 호출이 깨끗한 상태에서 시작한다.
    """
    _verify_db_boundary(db_path, approved_root)
    connection = _connect_approved_db(db_path, approved_root)
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
        _rollback(connection)
        if exc.sqlite_errorname == _PRIMARY_KEY_CONSTRAINT:
            return "duplicate"
        raise
    except sqlite3.OperationalError:
        # 브로커 커넥션이 예상과 다른(예: 판정을 통과한 laundered) 파일을 향하고 있으면
        # sqlite 가 여기서 raw 오류를 낼 수 있다 — 경로가 새는 원문 대신 닫힌 오류로 감싼다.
        # IntegrityError(위)는 우리 자신의 스키마 위반이라 디버깅을 위해 그대로 올린다 —
        # 여기서 감싸는 것은 laundered 커넥션처럼 외부에서 유도 가능한 실패뿐이다.
        _rollback(connection)
        raise CandidateIdentityError("db write was refused") from None
    except BaseException:
        _rollback(connection)
        raise
    try:
        _verify_db_boundary(db_path, approved_root)
    except BaseException:
        _rollback(connection)
        raise
    connection.execute("commit")
    return "inserted"


def _rollback(connection: sqlite3.Connection) -> None:
    """Best-effort rollback — a connection already broken by the failure must not mask it.

    `sqlite3.Error` 로 좁혀 잡지 않는다 — 이 모듈의 `sqlite3` 이름은 시험에서 통째로
    교체되기도 하고(Codex V1 2026-09-17 발견), 그 대체 객체가 `Error` 속성을 안 가지고
    있으면 이 except 절 자체가 AttributeError 를 낸다. rollback 실패를 삼키는 목적에는
    실제 예외 타입이 무엇이든 상관없으므로 넓게 잡는다.
    """
    try:
        connection.execute("rollback")
    except Exception:  # noqa: BLE001, S110 -- 의도된 best-effort 삼킴, 위 docstring 근거
        pass


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


def _connect_approved_db(db_path: Path, approved_root: Path) -> sqlite3.Connection:
    """Single-writer broker: connect at most once per approved root per process, then cache.

    이 함수가 여전히 쓰는 `/dev/fd` 집합 차분은 **증명이 아니라 완화**다 — 무관한 fd 를
    거부 사유로 세는 엄격한 판정은 실측상 정상 쓰기의 9%(200회 중 18회)를 오거부했고(구
    주석 참고), 반대로 "승인 identity 를 가진 fd 가 하나라도 새로 나타났는가"만 보는 관대한
    판정은 decoy fd 로 무력화된다(R6 재현: rename 스왑 도중 parked 원본을 여는 무관한
    스레드가 이 커넥션이 실제로는 alternate 를 열었어도 판정을 통과시킨다). stdlib sqlite3 는
    fd 를 노출하지 않아 "이 커넥션이 연 fd"를 native 하게 증명할 방법이 없다(AC-8 결정 카드
    — BLOCKED, 후속 WU: apsw 커스텀 VFS 승인 뒤 재검토).

    단일 writer 브로커로 할 수 있는 것: 이 위험한 재연결을 프로세스당 **단 한 번**(첫 쓰기)
    으로 좁힌다 — 이후 모든 쓰기는 이미 검증된 커넥션을 재사용해 이 경합에 다시 노출되지
    않는다. 그래서 관대한(저오거부) 판정을 유지해도 노출 총량은 구현 이전보다 훨씬 작다.

    Caller must already hold that approved root's lock (``_root_lock(approved_root)``) —
    this never locks itself.
    """
    approved = _approved_db(db_path, approved_root)
    if approved is None:
        raise CandidateIdentityError("db file is outside the approved root")
    cached = _BROKER_CONNECTIONS.get(approved_root)
    if cached is not None:
        return cached
    _verify_db_boundary(db_path, approved_root)
    before = _regular_open_fds()
    connection = sqlite3.connect(
        db_path, isolation_level=None, timeout=_LOCK_WAIT_SECONDS, check_same_thread=False
    )
    try:
        after = _regular_open_fds()
        opened = [identity for fd, identity in after.items() if before.get(fd) != identity]
        if (approved.st_dev, approved.st_ino) not in opened:
            raise CandidateIdentityError("opened db is not the approved file")
        _verify_db_boundary(db_path, approved_root)
    except BaseException:
        connection.close()
        raise
    _BROKER_CONNECTIONS[approved_root] = connection
    return connection


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
