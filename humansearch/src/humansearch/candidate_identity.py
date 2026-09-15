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

import errno
import hmac
import os
import re
import sqlite3
import stat
import unicodedata
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Final, Literal

from humansearch.storage_schema import (
    StorageSchemaError,
    _inside_git_worktree,
    _verify_path,
    approved_db_path,
)

Channel = Literal["saramin", "jobkorea", "linkedin_rps"]
RecordOutcome = Literal["inserted", "duplicate"]

ALLOWED_CHANNELS: Final[tuple[str, ...]] = ("saramin", "jobkorea", "linkedin_rps")

# 직렬화가 구분자 결합에서 길이 접두로 바뀌었으므로 도메인 태그를 v2 로 올린다.
# 같은 세 값이라도 v1 이 만든 키 값과 다르다.
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
# 다른 쓰기 연결의 잠금을 기다리는 상한. 초과하면 원문 OperationalError 가 아니라 닫힌 오류다.
_LOCK_WAIT_SECONDS: Final = 5.0
# C0(0x00-0x1F) · DEL(0x7F) · C1(0x80-0x9F). 필드 경계를 흉내 내거나 strip 에 조용히
# 잘려 키를 바꾸는 문자를 전부 막는다.
_CONTROL_CHARACTERS: Final = re.compile(r"[\x00-\x1f\x7f-\x9f]")
# 세 필드는 의미 문자열이다. strip 뒤 NFC 로 대표형을 정한다. NFKC 는 쓰지 않는다 —
# 호환문자(`\u2460` vs `1`, 전각 `\uff21` vs `A`)까지 합쳐 서로 다른 포털 ID 를 오병합한다.
_NORMALIZATION_FORM: Final = "NFC"
# 자리수만 세면 2026-99-99T99:99:99+99:99 가 통과한다. 여기서 달력·시각·오프셋 범위를
# 먼저 좁히고, 아래에서 datetime 으로 실재 여부를 다시 확인한다.
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
    """Duplicate-prevention key derived from all three identity fields.

    길이 접두 정규 직렬화 — 도메인 태그 뒤에 각 필드를
    `길이(4바이트 big-endian) + utf-8 바이트` 로 이어 붙인다.

    구분자 결합은 그 구분자가 필드 **안에** 들어오면 경계가 무너진다. Codex V1 이
    `("a","saramin","x\\x1fjobkorea\\x1fy")` 와 `("a\\x1fsaramin\\x1fx","jobkorea","y")` 가
    같은 바이트열이 되는 것을 실측했다. 길이는 내용에 섞일 수 없으므로 이 계열의
    주입이 원천적으로 불가능하다.
    """

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
    # strip 보다 먼저 본다. Python 은 \x1c-\x1f 와 \x85 를 공백으로 보고 조용히
    # 잘라내는데(실측), 잘라내면 키가 소리 없이 바뀐다.
    if _CONTROL_CHARACTERS.search(value) is not None:
        raise CandidateIdentityError(f"{label} must not contain control characters")
    # strip 뒤 NFC. 같은 글자가 여러 코드열로 올 수 있어(결합형 vs 분해형) 대표형을
    # 정하지 않으면 같은 후보가 두 행이 된다. NFC 는 제어문자를 만들지 않는다(실측).
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
    """모양 뒤에 실재를 확인한다.

    정규식만으로는 2026-02-29(윤년 아님) 같은 값을 못 거른다. 반대로
    `datetime.fromisoformat` 만으로도 부족하다 — 실측상 `24:00:00` 을 통과시킨다.
    두 겹을 모두 둔다.
    """

    if _RFC3339.fullmatch(observed_at) is None:
        raise CandidateIdentityError("observed_at must be an RFC3339 timestamp")
    try:
        parsed = datetime.fromisoformat(_isoformat_ready(observed_at))
    except ValueError as exc:
        raise CandidateIdentityError("observed_at is not a real instant") from exc
    if parsed.tzinfo is None:
        raise CandidateIdentityError("observed_at must carry a UTC offset")


def _isoformat_ready(observed_at: str) -> str:
    """RFC3339 의 소문자 표기를 `datetime.fromisoformat` 이 받는 형태로 맞춘다.

    RFC3339 는 날짜·시각 구분자 `T` 와 UTC 표기 `Z` 의 소문자를 허용하고 우리 정규식도
    `[Tt]`·`[Zz]` 로 받는다. 그런데 `fromisoformat` 은 소문자 `z` 를 거부한다(실측).
    앞 단계가 허용한 입력을 뒤 단계가 다른 규칙으로 거부하면 정상 공급자가 통째로 막힌다.

    표기만 대문자로 바꾼다 — 값은 건드리지 않으므로 달력·범위 검증은 그대로 걸린다.
    """

    # 이 함수는 _RFC3339 통과 뒤에만 불린다. 그래서 구분자 위치가 고정돼 있다 —
    # `YYYY-MM-DD` 10자 다음이 T/t 이고, UTC 표기면 마지막 글자가 Z/z 다.
    body = observed_at
    if body.endswith("z"):
        body = body[:-1] + "Z"
    if len(body) > _DESIGNATOR_INDEX and body[_DESIGNATOR_INDEX] == "t":
        body = body[:_DESIGNATOR_INDEX] + "T" + body[_DESIGNATOR_INDEX + 1 :]
    return body


def _closed_os_error(message: str, exc: OSError) -> CandidateIdentityError:
    """OS 오류를 경로 없는 닫힌 오류로 바꾼다.

    `raise … from exc` 는 원인 사슬(`__cause__`)에 FileNotFoundError 를 그대로 남기고,
    그 안에는 절대 경로가 있다 — `traceback.format_exc()` 가 실리는 일반 장애 로그에
    키 저장소 위치가 남는다(독립 검토 step-13, 19:27:46 재현). errno 이름만 싣고 사슬은 끊는다.
    """

    code = errno.errorcode.get(exc.errno or 0, "EUNKNOWN")
    return CandidateIdentityError(f"{message} ({code})")


def _verify(path: Path, *, expected_mode: int, label: str) -> None:
    """Reuse the HS-03.01 path guard, re-raised inside this module's closed error.

    HS-03.01 의 오류는 원인으로 FileNotFoundError(경로 포함)를 달고 있으므로 사슬을 끊는다.
    """

    try:
        _verify_path(path, expected_mode=expected_mode, label=label)
    except CandidateIdentityError:
        raise
    except StorageSchemaError as exc:
        raise CandidateIdentityError(str(exc)) from None


def _reject_symlinked_chain(path: Path, *, label: str) -> None:
    """상위 사슬의 symlink 는 `stat(follow_symlinks=False)` 이 못 본다.

    마지막 구성요소만 따라가지 않으므로, 부모의 부모가 symlink 면 모드 검사는 실체
    디렉터리를 보고 통과한다. 사슬을 직접 걸어 확인한다.
    """

    for candidate in (path, *path.parents):
        if candidate.is_symlink():
            raise CandidateIdentityError(f"{label} must not contain a symlink")


def _verify_db_location(db_path: Path) -> Path:
    """Return the real directory the DB will be written to.

    검사한 경로와 실제로 여는 파일이 같아야 경계 검사가 성립한다. `db_path.parent` 만
    해석하면 마지막 구성요소가 symlink 일 때 둘이 갈라진다 — alias 디렉터리의 링크가
    키 디렉터리 안 실제 DB 를 가리키면 비교는 alias 를 보고 통과하지만 `sqlite3.connect`
    는 링크를 따라가 키와 같은 루트에 쓴다(Codex V1 2차). 마지막 파일까지 포함해 사슬을
    검사하고, 해석된 실제 위치를 돌려준다.
    """

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
    # 검사 뒤 읽기 전에 키 폴더·키 파일이 사라지는 경쟁에서 OS 오류가 절대 경로를 담은 채
    # 그대로 올라왔다(독립 검토 2회차 probe, 16:42 재현). 닫힌 오류로만 내보낸다.
    try:
        key_root = key_dir.resolve(strict=True)
    except OSError as exc:
        raise _closed_os_error("hmac key directory is missing", exc) from None
    db_root = _verify_db_location(db_path)
    # 동일 경로만 막으면 dbroot/keys/k 가 통과한다. DB 루트를 한 번 복사·유출하면
    # 키까지 함께 나가므로 분리 보관이 무너진다(Codex V1). 포함은 양방향으로 막는다.
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
    """쓰기 직전 보호 경계 — 저장 계약 §3.

    HS-03.01 이 초기화 때 본 권한·위치는 그 시점의 사실일 뿐이다. 기록 시점에 부모
    0700 · DB 0600 · 현재 UID · 일반 파일 · Git 밖 · 보조 파일을 다시 본다. 권한 완화·
    소유자 불일치·symlink·승인 root 탈출은 저장 실패다(Codex 14:50 높음).
    """

    if not _is_approved_db(db_path, approved_root):
        raise CandidateIdentityError("db file is outside the approved root")
    _reject_symlinked_chain(db_path, label="db path")
    _verify(approved_root, expected_mode=_DB_DIR_MODE, label="db directory")
    _verify(db_path, expected_mode=_DB_FILE_MODE, label="db file")
    if not db_path.is_file():
        raise CandidateIdentityError("db file must be a regular file")
    # symlink 만 막으면 hard link 가 남는다 — 같은 inode 가 승인 root 밖 이름으로도 열린다
    # (자기 공격 실측: 밖 경로 link 뒤 inserted, nlink=2). 이름이 둘 이상이면 경계가 아니다.
    if db_path.stat(follow_symlinks=False).st_nlink != 1:
        raise CandidateIdentityError("db file must not have extra hard links")
    if _inside_git_worktree(db_path.parent):
        raise CandidateIdentityError("db file must be outside the git worktree")
    _verify_sidecars(db_path)


def _is_approved_db(db_path: Path, approved_root: Path) -> bool:
    """승인 root 는 초기화 장부에 결합돼 있다 — 경로 모양은 승인이 아니다.

    호출자가 `approved_root=db_path.parent` 로 스스로 채워도, 같은 UID 의 0700/0600 호환 DB 여도,
    `initialize_humansearch_storage` 가 이 프로세스에서 그 root 에 돌려준 바로 그 DB 파일이
    아니면 거부한다. 승인 root 안의 다른 파일명도 마찬가지다.
    """

    return (
        approved_root.is_absolute()
        and db_path.parent == approved_root
        and approved_db_path(approved_root) == db_path
    )


def _verify_sidecars(db_path: Path) -> None:
    """journal/wal/shm 도 같은 보호 범위다 — 단, 한 번의 lstat 로만 본다.

    HS-03.01 의 초기화 검사는 exists() 뒤 stat() 을 다시 하는데, 경쟁하는 다른 연결이
    journal 을 만들었다 지우는 사이에 사라지면 "missing" 으로 거부한다(AC-3 경쟁 시험
    20회 중 7회 실측). 없어진 보조 파일은 위반이 아니다. 소유자도 대상 파일 자체에서 본다 —
    저장 계약 §3 은 부모의 접근성 추론이 아니라 보조 파일 자체의 owner 확인을 요구한다.
    """

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
    """Single INSERT. 경쟁은 기본키 제약이 막고, 진 쪽만 duplicate 가 된다.

    쓰기 직전 검사만으로는 부족하다 — INSERT 와 반환 사이에 권한이 완화되면 함수가
    성공을 돌려줬다(격리 재현 19:27:46, DB 0644 인 채 `inserted`). 저장 계약 §3 은
    쓰기 뒤 owner/mode 재확인을 요구한다. 확정(commit) **전에** 다시 보고, 위반이면
    롤백해 행을 남기지 않는다 — 확정 뒤에 보면 오류를 내도 행은 이미 남는다.
    """

    _verify_db_boundary(db_path, approved_root)
    connection = sqlite3.connect(db_path, isolation_level=None, timeout=_LOCK_WAIT_SECONDS)
    try:
        # sqlite3.connect 는 검사와 별도의 경로 해석이다. 검사 직후 symlink 를 다른
        # 호환 DB 로 바꾸고 connect 직후 되돌려도 열린 연결의 main 경로는 바뀌지 않는다.
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
        # 확정 전 재확인. 여기서 예외가 나면 commit 없이 close() 로 가고, SQLite 는
        # 열린 트랜잭션을 닫을 때 되돌린다(명시적 rollback 변이가 동작 동일로 생존 — 중복이라 뺐다).
        _verify_db_boundary(db_path, approved_root)
        connection.execute("commit")
    finally:
        connection.close()
    return "inserted"


def _outcome_after_lock_wait(connection: sqlite3.Connection, key_hmac: str) -> RecordOutcome:
    """잠금 대기를 넘긴 뒤의 결과 — 이긴 쪽이 이미 확정했으면 `duplicate`, 아니면 닫힌 오류.

    독립 검토(step-12)가 5.689초 뒤 `OperationalError(SQLITE_BUSY)` 원문 노출을 실측했다.
    무한 재시도는 두지 않는다 — 한 번의 읽기로 승자 확정 여부만 본다. 읽기마저 잠기면 닫힌 오류다.
    """

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
