"""HS-03.02 2차 RED — Codex V1 이 재현한 결함 4건을 닫는다."""

from __future__ import annotations

import hmac
import importlib
import sqlite3
from pathlib import Path
from types import ModuleType

import pytest

from humansearch.storage_schema import initialize_humansearch_storage

_MODULE_NAME = "humansearch.candidate_identity"
_REQUIRED_NAMES = (
    "CandidateIdentityInput",
    "CandidateIdentityError",
    "record_candidate_identity",
    "candidate_key_hmac",
)
_TEST_KEY = bytes(range(32))
_OBSERVED_AT = "2026-09-15T10:00:00Z"
_KEY_BASENAME = "hs-candidate.key"

_INJECTED_A = ("a", "saramin", "x\x1fjobkorea\x1fy")
_INJECTED_B = ("a\x1fsaramin\x1fx", "jobkorea", "y")

_CONTROL_SAMPLES = ("\x1f", "\x00", "\x7f", "\x85")


def _load_identity_module() -> ModuleType:
    module: ModuleType | None
    try:
        module = importlib.import_module(_MODULE_NAME)
    except ModuleNotFoundError:
        module = None
    if module is None:
        pytest.fail(f"record function missing: {_MODULE_NAME}")
    missing = [name for name in _REQUIRED_NAMES if not hasattr(module, name)]
    if missing:
        pytest.fail(f"record function missing: {_MODULE_NAME}.{'/'.join(missing)}")
    return module


def _assert_tmp_is_symlink_free(tmp_path: Path) -> None:
    """키 경로 사슬 검사는 상위에 symlink 가 없다는 전제 위에서만 의미가 있다."""
    assert tmp_path.resolve(strict=True) == tmp_path, (
        "pytest tmp_path 에 symlink 구성요소가 있다 — 키 경로 시험의 전제가 깨졌다"
    )


def _db_path(tmp_path: Path) -> Path:
    _assert_tmp_is_symlink_free(tmp_path)
    return initialize_humansearch_storage(tmp_path / "protected-root").db_path


def _key_at(directory: Path, *, key: bytes = _TEST_KEY) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / _KEY_BASENAME
    path.write_bytes(key)
    path.chmod(0o600)
    directory.chmod(0o700)
    return path


def _record(
    identity: ModuleType,
    db_path: Path,
    key_path: Path,
    *,
    position_ref: str = "POS-1",
    channel: str = "saramin",
    candidate_ref: str = "cand-1",
    observed_at: str = _OBSERVED_AT,
) -> str:
    record = identity.CandidateIdentityInput(
        position_ref=position_ref,
        channel=channel,
        candidate_ref=candidate_ref,
        observed_at=observed_at,
    )
    return str(identity.record_candidate_identity(
        db_path, record, hmac_key_path=key_path, approved_root=db_path.parent
    ))


def _independent_key_hmac(position_ref: str, channel: str, candidate_ref: str) -> str:
    """계약 문구만으로 다시 계산한다 — 길이 접두 정규 직렬화, 도메인 v2."""
    message = b"hs-candidate-key-v2"
    for field in (position_ref, channel, candidate_ref):
        raw = field.encode("utf-8")
        message += len(raw).to_bytes(4, "big") + raw
    return hmac.new(_TEST_KEY, message, "sha256").hexdigest()


def _count_rows(db_path: Path) -> int:
    with sqlite3.connect(db_path) as connection:
        row = connection.execute("select count(*) from hs_candidates").fetchone()
    return int(row[0])


def test_v1_separator_injection_pair_is_refused_at_the_db_path(tmp_path: Path) -> None:
    """Codex 의 두 입력은 DB 경로에서 **둘 다 거부**되어야 하고 행이 0개여야 한다."""
    identity = _load_identity_module()
    db_path = _db_path(tmp_path)
    key_path = _key_at(tmp_path / "key-root")
    for position_ref, channel, candidate_ref in (_INJECTED_A, _INJECTED_B):
        with pytest.raises(identity.CandidateIdentityError):
            _record(
                identity,
                db_path,
                key_path,
                position_ref=position_ref,
                channel=channel,
                candidate_ref=candidate_ref,
            )
    assert _count_rows(db_path) == 0


def test_length_prefix_keeps_ambiguous_field_splits_as_separate_rows(tmp_path: Path) -> None:
    """DB 수준 회귀 — 이어 붙이면 같아지는 두 후보가 별도 행으로 남아야 한다."""
    identity = _load_identity_module()
    db_path = _db_path(tmp_path)
    key_path = _key_at(tmp_path / "key-root")
    first = _record(identity, db_path, key_path, position_ref="ab", candidate_ref="c")
    second = _record(identity, db_path, key_path, position_ref="a", candidate_ref="bc")
    assert (first, second) == ("inserted", "inserted")
    assert _count_rows(db_path) == 2
    assert _independent_key_hmac("ab", "saramin", "c") != _independent_key_hmac("a", "saramin", "bc")


def test_key_hmac_is_length_prefixed_so_injected_separators_cannot_collide() -> None:
    """순수 함수 수준에서 충돌이 사라져야 한다(거부 규칙과 독립으로 성립)."""
    identity = _load_identity_module()
    left = str(identity.candidate_key_hmac(_TEST_KEY, *_INJECTED_A))
    right = str(identity.candidate_key_hmac(_TEST_KEY, *_INJECTED_B))
    assert left != right, "필드 안의 구분자로 서로 다른 입력이 같은 키가 됐다"
    assert left == _independent_key_hmac(*_INJECTED_A)
    assert right == _independent_key_hmac(*_INJECTED_B)


def test_key_hmac_length_prefix_separates_ambiguous_field_splits() -> None:
    """길이 접두가 실제로 경계를 만드는가 — 이어 붙이면 같아지는 쌍으로 확인한다."""
    identity = _load_identity_module()
    left = str(identity.candidate_key_hmac(_TEST_KEY, "ab", "saramin", "c"))
    right = str(identity.candidate_key_hmac(_TEST_KEY, "a", "saramin", "bc"))
    assert left != right
    assert left == _independent_key_hmac("ab", "saramin", "c")


@pytest.mark.parametrize("control", _CONTROL_SAMPLES)
@pytest.mark.parametrize("field", ["position_ref", "channel", "candidate_ref"])
def test_control_characters_in_any_field_are_refused(
    tmp_path: Path, field: str, control: str
) -> None:
    """C0(0x00-0x1F)·DEL(0x7F)·C1(0x80-0x9F) 가 들어오면 기록을 거부한다."""
    identity = _load_identity_module()
    db_path = _db_path(tmp_path)
    key_path = _key_at(tmp_path / "key-root")
    fields = {"position_ref": "POS-1", "channel": "saramin", "candidate_ref": "cand-1"}
    fields[field] = fields[field] + control
    with pytest.raises(identity.CandidateIdentityError):
        _record(identity, db_path, key_path, **fields)
    assert _count_rows(db_path) == 0


def test_key_directory_nested_under_db_protected_root_is_refused(tmp_path: Path) -> None:
    """dbroot/keys/k 는 DB 루트를 한 번 복사하면 키까지 함께 새어 나간다."""
    identity = _load_identity_module()
    db_path = _db_path(tmp_path)
    key_path = _key_at(db_path.parent / "keys")
    with pytest.raises(identity.CandidateIdentityError):
        _record(identity, db_path, key_path)
    assert _count_rows(db_path) == 0


def test_db_protected_root_nested_under_key_directory_is_refused(tmp_path: Path) -> None:
    """반대 방향 포함도 같은 유출 반경이다 — 양방향으로 막아야 한다."""
    identity = _load_identity_module()
    outer = tmp_path / "outer"
    outer.mkdir(mode=0o700)
    _assert_tmp_is_symlink_free(tmp_path)
    db_path = initialize_humansearch_storage(outer / "protected-root").db_path
    key_path = _key_at(outer)
    with pytest.raises(identity.CandidateIdentityError):
        _record(identity, db_path, key_path)
    assert _count_rows(db_path) == 0


def test_symlinked_ancestor_above_key_directory_is_refused(tmp_path: Path) -> None:
    """부모의 부모가 symlink 면 stat(follow_symlinks=False) 은 눈치채지 못한다."""
    identity = _load_identity_module()
    db_path = _db_path(tmp_path)
    real_root = tmp_path / "real-key-root"
    _key_at(real_root / "keys")
    linked_root = tmp_path / "linked-key-root"
    linked_root.symlink_to(real_root, target_is_directory=True)
    with pytest.raises(identity.CandidateIdentityError):
        _record(identity, db_path, linked_root / "keys" / _KEY_BASENAME)
    assert _count_rows(db_path) == 0


@pytest.mark.parametrize(
    "observed_at",
    [
        "2026-99-99T99:99:99+99:99",
        "2026-13-01T00:00:00Z",
        "2026-02-32T00:00:00Z",
        "2026-09-15T24:00:00Z",
        "2026-09-15T10:60:00Z",
        "2026-09-15T10:00:60Z",
        "2026-09-15T10:00:00+99:00",
        "2026-09-15T10:00:00+24:00",
        "2026-09-15T10:00:00",
        "2026-02-29T00:00:00Z",
    ],
)
def test_observed_at_outside_calendar_or_offset_range_is_refused(
    tmp_path: Path, observed_at: str
) -> None:
    """모양이 맞아도 존재하지 않는 시각이면 거부한다."""
    identity = _load_identity_module()
    db_path = _db_path(tmp_path)
    key_path = _key_at(tmp_path / "key-root")
    with pytest.raises(identity.CandidateIdentityError):
        _record(identity, db_path, key_path, observed_at=observed_at)
    assert _count_rows(db_path) == 0


@pytest.mark.parametrize(
    "observed_at",
    [
        "2024-02-29T00:00:00Z",
        "2026-09-15T10:00:00Z",
        "2026-09-15T10:00:00.123456Z",
        "2026-09-15T10:00:00+09:00",
        "2026-09-15T23:59:59+23:59",
        "2026-09-15T00:00:00-11:30",
    ],
)
def test_real_rfc3339_instants_are_accepted(tmp_path: Path, observed_at: str) -> None:
    """양성 대조군 — 전부 거부하는 구현은 이 시험이 막는다."""
    identity = _load_identity_module()
    db_path = _db_path(tmp_path)
    key_path = _key_at(tmp_path / "key-root")
    assert _record(identity, db_path, key_path, observed_at=observed_at) == "inserted"
    assert _count_rows(db_path) == 1
