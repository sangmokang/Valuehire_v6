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
import unicodedata
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Final, Literal

from humansearch.storage_schema import StorageSchemaError, _verify_path

Channel = Literal["saramin", "jobkorea", "linkedin_rps"]
RecordOutcome = Literal["inserted", "duplicate"]

ALLOWED_CHANNELS: Final[tuple[str, ...]] = ("saramin", "jobkorea", "linkedin_rps")

# 직렬화가 구분자 결합에서 길이 접두로 바뀌었으므로 도메인 태그를 v2 로 올린다.
# 같은 세 값이라도 v1 이 만든 키 값과 다르다.
_KEY_DOMAIN: Final = b"hs-candidate-key-v2"
_REF_DOMAIN: Final = b"hs-candidate-ref-v1"
_FIELD_SEPARATOR: Final = b"\x1f"
_LENGTH_PREFIX_BYTES: Final = 4
_MIN_KEY_BYTES: Final = 32
_MAX_FIELD_CHARS: Final = 512
_PRIMARY_KEY_CONSTRAINT: Final = "SQLITE_CONSTRAINT_PRIMARYKEY"
_KEY_FILE_MODE: Final = 0o600
_KEY_DIR_MODE: Final = 0o700
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
        parsed = datetime.fromisoformat(observed_at)
    except ValueError as exc:
        raise CandidateIdentityError("observed_at is not a real instant") from exc
    if parsed.tzinfo is None:
        raise CandidateIdentityError("observed_at must carry a UTC offset")


def _verify(path: Path, *, expected_mode: int, label: str) -> None:
    """Reuse the HS-03.01 path guard, re-raised inside this module's closed error."""

    try:
        _verify_path(path, expected_mode=expected_mode, label=label)
    except CandidateIdentityError:
        raise
    except StorageSchemaError as exc:
        raise CandidateIdentityError(str(exc)) from exc


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
        raise CandidateIdentityError("db file is missing") from exc


def _load_hmac_key(hmac_key_path: Path, db_path: Path) -> bytes:
    """Read the HMAC key from its own protected directory. 암묵 생성은 하지 않는다."""

    key_dir = hmac_key_path.parent
    _verify(key_dir, expected_mode=_KEY_DIR_MODE, label="hmac key directory")
    _verify(hmac_key_path, expected_mode=_KEY_FILE_MODE, label="hmac key")
    if not hmac_key_path.is_file():
        raise CandidateIdentityError("hmac key must be a regular file")
    _reject_symlinked_chain(hmac_key_path, label="hmac key path")
    key_root = key_dir.resolve(strict=True)
    db_root = _verify_db_location(db_path)
    # 동일 경로만 막으면 dbroot/keys/k 가 통과한다. DB 루트를 한 번 복사·유출하면
    # 키까지 함께 나가므로 분리 보관이 무너진다(Codex V1). 포함은 양방향으로 막는다.
    if key_root.is_relative_to(db_root) or db_root.is_relative_to(key_root):
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
