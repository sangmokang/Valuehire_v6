"""HS-03.02 후보 식별키를 중복 없이 기록한다 (RED)."""

from __future__ import annotations

import hmac
import importlib
import sqlite3
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import Any

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
_RACE_ROUNDS = 20
_BARRIER_TIMEOUT = 30.0


def _load_identity_module() -> ModuleType:
    """기록 동작의 부재를 실패 사유로 만든다(import 오류 RED 방지)."""
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


def _db_path(tmp_path: Path) -> Path:
    return initialize_humansearch_storage(tmp_path / "protected-root").db_path


def _key_path(
    tmp_path: Path,
    *,
    key: bytes = _TEST_KEY,
    directory: str = "key-root",
    mode: int = 0o600,
    dir_mode: int = 0o700,
) -> Path:
    key_dir = tmp_path / directory
    key_dir.mkdir(parents=True, exist_ok=True)
    path = key_dir / _KEY_BASENAME
    path.write_bytes(key)
    path.chmod(mode)
    key_dir.chmod(dir_mode)
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
    """구현을 보지 않고 계약 문구만으로 다시 계산한다(tautology 방지)."""
    message = b"hs-candidate-key-v2"
    for field in (position_ref, channel, candidate_ref):
        raw = field.encode("utf-8")
        message += len(raw).to_bytes(4, "big") + raw
    return hmac.new(_TEST_KEY, message, "sha256").hexdigest()


def _independent_ref_hash(candidate_ref: str) -> str:
    message = b"hs-candidate-ref-v1\x1f" + candidate_ref.encode("utf-8")
    return hmac.new(_TEST_KEY, message, "sha256").hexdigest()


def _count_rows(db_path: Path) -> int:
    with sqlite3.connect(db_path) as connection:
        row = connection.execute("select count(*) from hs_candidates").fetchone()
    return int(row[0])


def _count_key(db_path: Path, key: str) -> int:
    with sqlite3.connect(db_path) as connection:
        row = connection.execute(
            "select count(*) from hs_candidates where candidate_key_hmac = ?",
            (key,),
        ).fetchone()
    return int(row[0])


def _fetch_row(db_path: Path, key: str) -> tuple[str, str, str, str, str] | None:
    with sqlite3.connect(db_path) as connection:
        row = connection.execute(
            """
            select position_ref, channel, candidate_ref_state, candidate_ref_hash, storage_status
              from hs_candidates
             where candidate_key_hmac = ?
            """,
            (key,),
        ).fetchone()
    if row is None:
        return None
    return (str(row[0]), str(row[1]), str(row[2]), str(row[3]), str(row[4]))


def test_ac1_same_triplet_twice_leaves_one_row(tmp_path: Path) -> None:
    """AC-1 같은 (position, channel, candidate) 2회 → inserted, duplicate, 행 1개."""
    identity = _load_identity_module()
    db_path = _db_path(tmp_path)
    key_path = _key_path(tmp_path)
    first = _record(identity, db_path, key_path)
    second = _record(identity, db_path, key_path)
    assert (first, second) == ("inserted", "duplicate")
    assert _count_rows(db_path) == 1
    expected = _independent_key_hmac("POS-1", "saramin", "cand-1")
    row = _fetch_row(db_path, expected)
    assert row is not None, "저장된 candidate_key_hmac 이 세 값 독립 계산 HMAC 과 다르다"
    assert row == (
        "POS-1",
        "saramin",
        "observed",
        _independent_ref_hash("cand-1"),
        "pending",
    )
    assert str(identity.candidate_key_hmac(_TEST_KEY, "POS-1", "saramin", "cand-1")) == expected


def test_ac1_key_hmac_separator_distinguishes_field_boundaries() -> None:
    """구분자가 없으면 'a'+'bc' 와 'ab'+'c' 가 같은 키가 된다."""
    identity = _load_identity_module()
    left = str(identity.candidate_key_hmac(_TEST_KEY, "a", "saramin", "bc"))
    right = str(identity.candidate_key_hmac(_TEST_KEY, "ab", "saramin", "c"))
    assert left != right
    assert left == _independent_key_hmac("a", "saramin", "bc")
    assert right == _independent_key_hmac("ab", "saramin", "c")


def test_ac2_position_or_channel_difference_creates_separate_rows(tmp_path: Path) -> None:
    """AC-2 position_ref 또는 channel 이 다르면 별도 행. 같은 candidate_ref 라도 합치지 않는다."""
    identity = _load_identity_module()
    db_path = _db_path(tmp_path)
    key_path = _key_path(tmp_path)
    assert _record(identity, db_path, key_path, position_ref="POS-1") == "inserted"
    assert _record(identity, db_path, key_path, position_ref="POS-2") == "inserted"
    assert _count_rows(db_path) == 2
    assert _record(identity, db_path, key_path, position_ref="POS-3", channel="saramin") == "inserted"
    assert _record(identity, db_path, key_path, position_ref="POS-3", channel="jobkorea") == "inserted"
    assert _count_rows(db_path) == 4
    channel_keys = {
        _independent_key_hmac("POS-3", "saramin", "cand-1"),
        _independent_key_hmac("POS-3", "jobkorea", "cand-1"),
    }
    assert len(channel_keys) == 2, "HMAC 입력에 channel 이 빠졌다"
    for key in channel_keys:
        assert _fetch_row(db_path, key) is not None
    position_keys = {
        _independent_key_hmac("POS-1", "saramin", "cand-1"),
        _independent_key_hmac("POS-2", "saramin", "cand-1"),
    }
    assert len(position_keys) == 2, "HMAC 입력에 position_ref 가 빠졌다"
    for key in position_keys:
        assert _fetch_row(db_path, key) is not None


def test_ac3_two_connections_racing_the_same_key_keep_one_row(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-3 두 스레드가 같은 키를 동시에 넣어도 1행. 진 쪽은 duplicate, 예외 0.

    R6 단일 writer 브로커 이후: 두 스레드가 더 이상 독립 커넥션을 각자 열지 않는다 —
    `record_candidate_identity` 전체가 한 락으로 직렬화되고 승인 root 당 커넥션은
    프로세스 수명 동안 단 하나만 열려 재사용된다. 그래서 이 시험은 더 이상 "커넥션이
    몇 개 열렸는가"를 보지 않고, AC-3 이 실제로 요구하는 관측 가능한 계약(중복 없이 1행,
    승패 결과, 예외 0, 재연결이 라운드마다 반복되지 않음)만 본다.
    """
    identity = _load_identity_module()
    db_path = _db_path(tmp_path)
    key_path = _key_path(tmp_path)
    real_connect = sqlite3.connect
    connect_calls = 0
    guard = threading.Lock()
    def _counting_connect(*args: Any, **kwargs: Any) -> sqlite3.Connection:
        nonlocal connect_calls
        with guard:
            connect_calls += 1
        return real_connect(*args, **kwargs)  # type: ignore[no-any-return]
    # 브로커 내부 재연결만 센다 — 전역 sqlite3.connect 를 패치하면 이 시험 자신의
    # _count_key/_count_rows 검증 커넥션까지 섞여 셈이 오염된다.
    monkeypatch.setattr(identity, "sqlite3", SimpleNamespace(
        connect=_counting_connect,
        IntegrityError=sqlite3.IntegrityError,
        OperationalError=sqlite3.OperationalError,
        Error=sqlite3.Error,
    ))
    barrier = threading.Barrier(2)
    def _worker(candidate_ref: str) -> str:
        barrier.wait(timeout=_BARRIER_TIMEOUT)
        return _record(
            identity,
            db_path,
            key_path,
            position_ref="POS-RACE",
            channel="saramin",
            candidate_ref=candidate_ref,
        )
    for index in range(_RACE_ROUNDS):
        candidate_ref = f"cand-race-{index}"
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(_worker, candidate_ref) for _ in range(2)]
            results = sorted(future.result() for future in futures)
        assert results == ["duplicate", "inserted"], f"round {index}: {results}"
        key = _independent_key_hmac("POS-RACE", "saramin", candidate_ref)
        assert _count_key(db_path, key) == 1, f"round {index}: 기본키 제약이 경쟁을 막지 못했다"
    monkeypatch.undo()
    assert connect_calls == 1, f"브로커가 재연결을 반복했다: {connect_calls} 회"
    assert _count_rows(db_path) == _RACE_ROUNDS


def test_writes_to_different_approved_roots_do_not_block_each_other(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """서로 무관한 승인 root 에 대한 기록은 같은 락을 공유하지 않는다.

    Codex V1 2026-09-17 발견: 락이 프로세스 전역 하나였을 때는 root A 에 대한 느린
    기록이 root B(완전히 다른 DB)에 대한 기록까지 붙잡았다(실측 1.86초). root 별 락
    (`_root_lock`)으로 바꾼 뒤에는 root A 가 블록돼 있어도 root B 는 즉시 끝나야 한다.
    """
    identity = _load_identity_module()
    db_path_a = _db_path(tmp_path / "a")
    db_path_b = _db_path(tmp_path / "b")
    key_path = _key_path(tmp_path)

    root_a_entered = threading.Event()
    release_root_a = threading.Event()
    real_bind = identity._bind_key_epoch

    def blocking_bind(approved_root: Path, key: bytes) -> None:
        if approved_root == db_path_a.parent:
            root_a_entered.set()
            assert release_root_a.wait(timeout=_BARRIER_TIMEOUT), "release 신호가 오지 않았다"
        real_bind(approved_root, key)

    monkeypatch.setattr(identity, "_bind_key_epoch", blocking_bind)

    def write_a() -> str:
        return _record(identity, db_path_a, key_path, position_ref="POS-A")

    worker = threading.Thread(target=write_a)
    worker.start()
    try:
        assert root_a_entered.wait(timeout=_BARRIER_TIMEOUT), "root A 기록이 시작되지 않았다"

        started = time.monotonic()
        outcome_b = _record(identity, db_path_b, key_path, position_ref="POS-B")
        elapsed_b = time.monotonic() - started
        assert outcome_b == "inserted"
        assert elapsed_b < 1.0, f"root B 기록이 root A 락에 걸렸다: {elapsed_b:.3f}초"
    finally:
        release_root_a.set()
        worker.join(timeout=_BARRIER_TIMEOUT)
    assert not worker.is_alive()
    assert _count_rows(db_path_a) == 1
    assert _count_rows(db_path_b) == 1


@pytest.mark.parametrize(
    ("position_ref", "channel", "candidate_ref"),
    [
        ("POS-1", "saramin", ""),
        ("POS-1", "saramin", "   "),
        ("", "saramin", "cand-1"),
        ("   ", "saramin", "cand-1"),
        ("POS-1", "", "cand-1"),
        ("POS-1", "linkedin", "cand-1"),
        ("POS-1", "SARAMIN", "cand-1"),
        ("POS-1", "wanted", "cand-1"),
    ],
)
def test_ac4_blank_field_or_unknown_channel_is_refused(
    tmp_path: Path, position_ref: str, channel: str, candidate_ref: str
) -> None:
    """AC-4 세 값 중 하나라도 비거나 channel 이 허용값 밖이면 행을 만들지 않는다."""
    identity = _load_identity_module()
    db_path = _db_path(tmp_path)
    key_path = _key_path(tmp_path)
    with pytest.raises(identity.CandidateIdentityError) as excinfo:
        _record(
            identity,
            db_path,
            key_path,
            position_ref=position_ref,
            channel=channel,
            candidate_ref=candidate_ref,
        )
    assert _count_rows(db_path) == 0
    message = str(excinfo.value)
    assert "cand-1" not in message
    assert "POS-1" not in message


def test_missing_key_file_is_refused_without_implicit_creation(tmp_path: Path) -> None:
    """키 파일이 없으면 거부한다. 암묵 생성 금지."""
    identity = _load_identity_module()
    db_path = _db_path(tmp_path)
    key_dir = tmp_path / "key-root"
    key_dir.mkdir(mode=0o700)
    missing = key_dir / _KEY_BASENAME
    with pytest.raises(identity.CandidateIdentityError) as excinfo:
        _record(identity, db_path, missing)
    assert "missing" in str(excinfo.value)
    assert not missing.exists(), "키를 암묵 생성했다"
    assert _count_rows(db_path) == 0


def test_key_file_inside_db_protected_root_is_refused(tmp_path: Path) -> None:
    """정본 109행 — 키 원본은 데이터와 같은 디렉터리에 두지 않는다."""
    identity = _load_identity_module()
    db_path = _db_path(tmp_path)
    inside = db_path.parent / _KEY_BASENAME
    inside.write_bytes(_TEST_KEY)
    inside.chmod(0o600)
    with pytest.raises(identity.CandidateIdentityError):
        _record(identity, db_path, inside)
    assert _count_rows(db_path) == 0


@pytest.mark.parametrize(("mode", "dir_mode"), [(0o644, 0o700), (0o600, 0o755)])
def test_loose_key_permissions_are_refused(tmp_path: Path, mode: int, dir_mode: int) -> None:
    """키 파일 0600·부모 0700 이 아니면 거부한다."""
    identity = _load_identity_module()
    db_path = _db_path(tmp_path)
    key_path = _key_path(tmp_path, mode=mode, dir_mode=dir_mode)
    with pytest.raises(identity.CandidateIdentityError):
        _record(identity, db_path, key_path)
    assert _count_rows(db_path) == 0


def test_symlinked_key_file_is_refused(tmp_path: Path) -> None:
    identity = _load_identity_module()
    db_path = _db_path(tmp_path)
    real_key = _key_path(tmp_path, directory="real-key-root")
    link_dir = tmp_path / "link-key-root"
    link_dir.mkdir(mode=0o700)
    link = link_dir / _KEY_BASENAME
    link.symlink_to(real_key)
    with pytest.raises(identity.CandidateIdentityError):
        _record(identity, db_path, link)
    assert _count_rows(db_path) == 0


def test_short_key_is_refused(tmp_path: Path) -> None:
    """32바이트 미만 키는 거부한다."""
    identity = _load_identity_module()
    db_path = _db_path(tmp_path)
    key_path = _key_path(tmp_path, key=bytes(range(31)))
    with pytest.raises(identity.CandidateIdentityError):
        _record(identity, db_path, key_path)
    assert _count_rows(db_path) == 0


def test_non_primary_key_integrity_error_is_not_folded_into_duplicate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """기본키 충돌이 아닌 무결성 오류는 duplicate 로 접지 않고 그대로 올린다."""
    identity = _load_identity_module()
    db_path = _db_path(tmp_path)
    key_path = _key_path(tmp_path)
    def _non_hex_key(key: bytes, position_ref: str, channel: str, candidate_ref: str) -> str:
        return "z" * 64
    monkeypatch.setattr(identity, "candidate_key_hmac", _non_hex_key)
    with pytest.raises(sqlite3.IntegrityError) as excinfo:
        _record(identity, db_path, key_path)
    assert not isinstance(excinfo.value, identity.CandidateIdentityError)
    assert excinfo.value.sqlite_errorname == "SQLITE_CONSTRAINT_CHECK"
    assert _count_rows(db_path) == 0


@pytest.mark.parametrize(
    "observed_at",
    ["", "   ", "2026-09-15", "2026-09-15 10:00:00", "not-a-time", "2026-09-15T10:00:00+0900"],
)
def test_observed_at_must_be_rfc3339(tmp_path: Path, observed_at: str) -> None:
    identity = _load_identity_module()
    db_path = _db_path(tmp_path)
    key_path = _key_path(tmp_path)
    with pytest.raises(identity.CandidateIdentityError):
        _record(identity, db_path, key_path, observed_at=observed_at)
    assert _count_rows(db_path) == 0


@pytest.mark.parametrize(
    "observed_at",
    ["2026-09-15T10:00:00Z", "2026-09-15T10:00:00.123Z", "2026-09-15T10:00:00+09:00"],
)
def test_rfc3339_observed_at_is_accepted_and_not_stored(tmp_path: Path, observed_at: str) -> None:
    """양성 대조군 — 허용 형식은 통과하고, observed_at 열은 만들지 않는다."""
    identity = _load_identity_module()
    db_path = _db_path(tmp_path)
    key_path = _key_path(tmp_path)
    assert _record(identity, db_path, key_path, observed_at=observed_at) == "inserted"
    assert _count_rows(db_path) == 1
    with sqlite3.connect(db_path) as connection:
        columns = {row[1] for row in connection.execute("pragma table_info(hs_candidates)")}
    assert "observed_at" not in columns
