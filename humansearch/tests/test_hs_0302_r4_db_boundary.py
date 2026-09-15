"""HS-03.02 4차 RED — DB 저장 경계(Codex 14:50 높음 결함) 를 시험으로 먼저 고정한다."""

from __future__ import annotations

import importlib
import os
import shutil
import sqlite3
import subprocess
import traceback
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest

from humansearch.storage_schema import initialize_humansearch_storage

_MODULE_NAME = "humansearch.candidate_identity"
_REQUIRED_NAMES = (
    "CandidateIdentityInput",
    "CandidateIdentityError",
    "record_candidate_identity",
)
_TEST_KEY = bytes(range(32))
_OBSERVED_AT = "2026-09-15T10:00:00Z"
_KEY_BASENAME = "hs-candidate.key"
_DB_BASENAME = "humansearch.sqlite3"
_POSITION_REF = "POS-1"
_CANDIDATE_REF = "cand-1"
_SIDECAR_SUFFIXES = ("-journal", "-wal", "-shm")


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
    assert tmp_path.resolve(strict=True) == tmp_path, (
        "pytest tmp_path 에 symlink 구성요소가 있다 — 경로 시험의 전제가 깨졌다"
    )


def _key_at(directory: Path, *, key: bytes = _TEST_KEY) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / _KEY_BASENAME
    path.write_bytes(key)
    path.chmod(0o600)
    directory.chmod(0o700)
    return path


def _protected_db(tmp_path: Path, name: str = "protected-root") -> Path:
    _assert_tmp_is_symlink_free(tmp_path)
    return initialize_humansearch_storage(tmp_path / name).db_path


def _record(identity: ModuleType, db_path: Path, key_path: Path) -> str:
    record = identity.CandidateIdentityInput(
        position_ref=_POSITION_REF,
        channel="saramin",
        candidate_ref=_CANDIDATE_REF,
        observed_at=_OBSERVED_AT,
    )
    return str(identity.record_candidate_identity(
        db_path, record, hmac_key_path=key_path, approved_root=db_path.parent
    ))


def _count_rows(db_path: Path) -> int:
    with sqlite3.connect(db_path) as connection:
        row = connection.execute("select count(*) from hs_candidates").fetchone()
    return int(row[0])


def _assert_closed_error(exc: BaseException, tmp_path: Path) -> None:
    """거부 메시지는 경로 원문·키 바이트·position_ref·candidate_ref 를 담지 않는다."""
    text = str(exc)
    assert str(tmp_path) not in text
    assert _TEST_KEY.hex() not in text
    assert _POSITION_REF not in text
    assert _CANDIDATE_REF not in text


def _git_env_without_repo_hints() -> dict[str, str]:
    """바깥 셸의 GIT_DIR 류가 새 저장소 생성 위치를 바꾸지 못하게 한다."""
    return {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}




@pytest.mark.parametrize(
    ("db_mode", "dir_mode"),
    [(0o644, 0o700), (0o600, 0o755), (0o644, 0o755), (0o600, 0o750)],
)
def test_loose_db_or_parent_permissions_are_refused(
    tmp_path: Path, db_mode: int, dir_mode: int
) -> None:
    """DB 0600 · 부모 0700 이 아니면 쓰기 직전에 거부하고 행을 남기지 않는다."""
    identity = _load_identity_module()
    db_path = _protected_db(tmp_path)
    key_path = _key_at(tmp_path / "key-root")
    db_path.chmod(db_mode)
    db_path.parent.chmod(dir_mode)
    with pytest.raises(identity.CandidateIdentityError) as caught:
        _record(identity, db_path, key_path)
    _assert_closed_error(caught.value, tmp_path)
    assert _count_rows(db_path) == 0




def _compatible_db_under(tmp_path: Path, parent: Path) -> Path:
    """정상 초기화한 DB 를 다른 부모 아래로 옮긴 호환 스키마 사본을 만든다."""
    source = _protected_db(tmp_path, "source-root")
    parent.mkdir(mode=0o700, parents=True)
    copy = parent / _DB_BASENAME
    shutil.copyfile(source, copy)
    copy.chmod(0o600)
    return copy


def test_db_under_git_init_directory_is_refused(tmp_path: Path) -> None:
    """`git init` 한 폴더 아래 DB 는 승인된 보호 root 밖이다 — Git 밖 규칙 위반."""
    identity = _load_identity_module()
    _assert_tmp_is_symlink_free(tmp_path)
    repo = tmp_path / "repo"
    repo.mkdir(mode=0o700)
    subprocess.run(
        ["git", "init", "-q", str(repo)],
        check=True,
        env=_git_env_without_repo_hints(),
        stdin=subprocess.DEVNULL,
    )
    assert (repo / ".git").is_dir()
    db_path = _compatible_db_under(tmp_path, repo / "protected")
    key_path = _key_at(tmp_path / "key-root")
    with pytest.raises(identity.CandidateIdentityError) as caught:
        _record(identity, db_path, key_path)
    _assert_closed_error(caught.value, tmp_path)
    assert _count_rows(db_path) == 0


def test_db_under_git_worktree_file_marker_is_refused(tmp_path: Path) -> None:
    """워크트리는 `.git` 이 디렉터리가 아니라 파일이다 — 그 형태도 Git 안이다."""
    identity = _load_identity_module()
    _assert_tmp_is_symlink_free(tmp_path)
    worktree = tmp_path / "worktree"
    worktree.mkdir(mode=0o700)
    (worktree / ".git").write_text("gitdir: elsewhere\n", encoding="utf-8")
    db_path = _compatible_db_under(tmp_path, worktree / "nested" / "protected")
    key_path = _key_at(tmp_path / "key-root")
    with pytest.raises(identity.CandidateIdentityError) as caught:
        _record(identity, db_path, key_path)
    _assert_closed_error(caught.value, tmp_path)
    assert _count_rows(db_path) == 0




def test_db_path_that_is_not_a_regular_file_is_refused_with_closed_error(
    tmp_path: Path,
) -> None:
    """모드가 맞아도 일반 파일이 아니면 sqlite 오류가 아니라 닫힌 도메인 오류로 거부한다."""
    identity = _load_identity_module()
    _assert_tmp_is_symlink_free(tmp_path)
    root = tmp_path / "protected-root"
    root.mkdir(mode=0o700)
    db_path = root / _DB_BASENAME
    db_path.mkdir(mode=0o600)
    key_path = _key_at(tmp_path / "key-root")
    with pytest.raises(identity.CandidateIdentityError) as caught:
        _record(identity, db_path, key_path)
    _assert_closed_error(caught.value, tmp_path)


@pytest.mark.parametrize("suffix", list(_SIDECAR_SUFFIXES))
def test_loose_sqlite_sidecar_next_to_db_is_refused(tmp_path: Path, suffix: str) -> None:
    """journal/wal/shm 이 완화 권한으로 남아 있으면 같은 보호 범위 위반이다."""
    identity = _load_identity_module()
    db_path = _protected_db(tmp_path)
    key_path = _key_at(tmp_path / "key-root")
    sidecar = db_path.with_name(db_path.name + suffix)
    sidecar.write_bytes(b"")
    sidecar.chmod(0o644)
    with pytest.raises(identity.CandidateIdentityError) as caught:
        _record(identity, db_path, key_path)
    _assert_closed_error(caught.value, tmp_path)
    assert _count_rows(db_path) == 0


@pytest.mark.parametrize("suffix", list(_SIDECAR_SUFFIXES))
def test_symlinked_sqlite_sidecar_is_refused(tmp_path: Path, suffix: str) -> None:
    """보조 파일이 symlink 면 보호 root 밖으로 평문이 샌다."""
    identity = _load_identity_module()
    db_path = _protected_db(tmp_path)
    key_path = _key_at(tmp_path / "key-root")
    outside = tmp_path / "outside"
    outside.mkdir(mode=0o700)
    target = outside / "target"
    target.write_bytes(b"")
    target.chmod(0o600)
    db_path.with_name(db_path.name + suffix).symlink_to(target)
    with pytest.raises(identity.CandidateIdentityError) as caught:
        _record(identity, db_path, key_path)
    _assert_closed_error(caught.value, tmp_path)
    assert "symlink" in str(caught.value)
    assert _count_rows(db_path) == 0


@pytest.mark.parametrize("suffix", list(_SIDECAR_SUFFIXES))
def test_sqlite_sidecar_that_is_not_a_regular_file_is_refused(tmp_path: Path, suffix: str) -> None:
    """모드가 맞아도 보조 파일 자리에 일반 파일이 아닌 것이 있으면 닫힌 오류로 거부한다."""
    identity = _load_identity_module()
    db_path = _protected_db(tmp_path)
    key_path = _key_at(tmp_path / "key-root")
    sidecar = db_path.with_name(db_path.name + suffix)
    sidecar.mkdir(mode=0o600)
    with pytest.raises(identity.CandidateIdentityError) as caught:
        _record(identity, db_path, key_path)
    _assert_closed_error(caught.value, tmp_path)
    sidecar.rmdir()
    assert _count_rows(db_path) == 0




def test_key_file_vanishing_after_checks_is_a_closed_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """키 검사를 통과한 뒤 읽기 직전에 키 파일이 사라지면 OS 오류가 경로째 새면 안 된다."""
    identity = _load_identity_module()
    db_path = _protected_db(tmp_path)
    key_path = _key_at(tmp_path / "key-root")
    original = identity._verify_db_location
    def vanish_then_verify(path: Path) -> Path:
        key_path.unlink()
        return Path(original(path))
    monkeypatch.setattr(identity, "_verify_db_location", vanish_then_verify)
    with pytest.raises(identity.CandidateIdentityError) as caught:
        _record(identity, db_path, key_path)
    _assert_closed_error(caught.value, tmp_path)
    assert _count_rows(db_path) == 0


def test_key_directory_vanishing_after_checks_is_a_closed_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """키 폴더가 사슬 검사 뒤 사라지면 resolve(strict=True) 의 OS 오류도 닫힌 오류여야 한다."""
    identity = _load_identity_module()
    db_path = _protected_db(tmp_path)
    key_dir = tmp_path / "key-root"
    key_path = _key_at(key_dir)
    original = identity._reject_symlinked_chain
    def verify_then_vanish(path: Path, *, label: str) -> None:
        original(path, label=label)
        if label == "hmac key path":
            shutil.rmtree(key_dir)
    monkeypatch.setattr(identity, "_reject_symlinked_chain", verify_then_vanish)
    with pytest.raises(identity.CandidateIdentityError) as caught:
        _record(identity, db_path, key_path)
    _assert_closed_error(caught.value, tmp_path)
    assert _count_rows(db_path) == 0




def test_protected_db_outside_git_still_records(tmp_path: Path) -> None:
    """양성 대조군 — 정상 권한 · Git 밖 · 보조 파일 없음이면 그대로 1행 기록된다."""
    identity = _load_identity_module()
    db_path = _protected_db(tmp_path)
    key_path = _key_at(tmp_path / "key-root")
    assert _record(identity, db_path, key_path) == "inserted"
    assert _count_rows(db_path) == 1
    assert oct(db_path.stat().st_mode & 0o777) == oct(0o600)
    assert oct(db_path.parent.stat().st_mode & 0o777) == oct(0o700)
    for suffix in _SIDECAR_SUFFIXES:
        assert not db_path.with_name(db_path.name + suffix).exists()


def test_protected_db_with_clean_sidecar_still_records(tmp_path: Path) -> None:
    """양성 대조군 — 정상 권한의 보조 파일은 거부 사유가 아니다."""
    identity = _load_identity_module()
    db_path = _protected_db(tmp_path)
    key_path = _key_at(tmp_path / "key-root")
    sidecar = db_path.with_name(db_path.name + "-journal")
    sidecar.write_bytes(b"")
    sidecar.chmod(0o600)
    assert _record(identity, db_path, key_path) == "inserted"
    assert _count_rows(db_path) == 1




@pytest.mark.parametrize("loosen", ["db-file", "db-directory"])
def test_permission_loosened_during_write_is_refused_before_commit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, loosen: str
) -> None:
    """INSERT 뒤·반환 전에 권한이 완화되면 저장 실패여야 하고 행이 남지 않아야 한다."""
    identity = _load_identity_module()
    db_path = _protected_db(tmp_path)
    key_path = _key_at(tmp_path / "key-root")
    real_sqlite3 = identity.sqlite3
    class _LoosenAfterInsert:
        def __init__(self, connection: sqlite3.Connection) -> None:
            self._connection = connection
        def execute(self, sql: str, params: tuple[str, ...] = ()) -> sqlite3.Cursor:
            cursor = self._connection.execute(sql, params)
            if "insert into hs_candidates" in sql:
                if loosen == "db-file":
                    db_path.chmod(0o644)
                else:
                    db_path.parent.chmod(0o755)
            return cursor
        def close(self) -> None:
            self._connection.close()
    def connect(path: Path, *args: object, **kwargs: object) -> _LoosenAfterInsert:
        return _LoosenAfterInsert(real_sqlite3.connect(path, *args, **kwargs))
    monkeypatch.setattr(
        identity,
        "sqlite3",
        SimpleNamespace(connect=connect, IntegrityError=real_sqlite3.IntegrityError),
    )
    with pytest.raises(identity.CandidateIdentityError) as caught:
        _record(identity, db_path, key_path)
    _assert_closed_error(caught.value, tmp_path)
    assert "mode must be" in str(caught.value)
    db_path.chmod(0o600)
    db_path.parent.chmod(0o700)
    assert _count_rows(db_path) == 0, "확정 전에 잡아야 하므로 행이 남으면 안 된다"




def _hold_write_lock(db_path: Path) -> sqlite3.Connection:
    holder = sqlite3.connect(db_path, isolation_level=None)
    holder.execute("begin immediate")
    return holder


def test_lock_wait_exceeded_without_winner_is_a_closed_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """다른 쓰기 연결이 잠금을 오래 잡으면 원문 OperationalError 가 아니라 닫힌 오류여야 한다."""
    identity = _load_identity_module()
    db_path = _protected_db(tmp_path)
    key_path = _key_at(tmp_path / "key-root")
    monkeypatch.setattr(identity, "_LOCK_WAIT_SECONDS", 0.2, raising=False)
    holder = _hold_write_lock(db_path)
    try:
        with pytest.raises(identity.CandidateIdentityError) as caught:
            _record(identity, db_path, key_path)
    finally:
        holder.execute("rollback")
        holder.close()
    _assert_closed_error(caught.value, tmp_path)
    assert "lock" in str(caught.value)
    assert _count_rows(db_path) == 0


def test_lock_wait_exceeded_after_winner_committed_is_duplicate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """이긴 쪽이 이미 같은 키를 확정했다면, 잠금 대기를 넘겨도 결과는 `duplicate` 다(AC-3)."""
    identity = _load_identity_module()
    db_path = _protected_db(tmp_path)
    key_path = _key_at(tmp_path / "key-root")
    monkeypatch.setattr(identity, "_LOCK_WAIT_SECONDS", 0.2, raising=False)
    assert _record(identity, db_path, key_path) == "inserted"
    holder = _hold_write_lock(db_path)
    try:
        outcome = _record(identity, db_path, key_path)
    finally:
        holder.execute("rollback")
        holder.close()
    assert outcome == "duplicate"
    assert _count_rows(db_path) == 1


def test_key_file_vanishing_leaves_no_path_in_cause_chain(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """닫힌 오류의 원인 사슬(`__cause__`/`__context__`)에도 키 경로가 남으면 안 된다."""
    identity = _load_identity_module()
    db_path = _protected_db(tmp_path)
    key_path = _key_at(tmp_path / "key-root")
    original = identity._verify_db_location
    def vanish_then_verify(path: Path) -> Path:
        key_path.unlink()
        return Path(original(path))
    monkeypatch.setattr(identity, "_verify_db_location", vanish_then_verify)
    try:
        _record(identity, db_path, key_path)
    except identity.CandidateIdentityError:
        rendered = traceback.format_exc()
    else:
        pytest.fail("DID NOT RAISE CandidateIdentityError")
    assert str(tmp_path) not in rendered, "원인 사슬에 키 경로가 실렸다"


def test_sqlite_sidecar_owned_by_another_uid_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """보조 파일도 대상 파일 자체의 소유자를 본다(저장 계약 §3). 다른 UID 파일은 같은 UID 로"""
    identity = _load_identity_module()
    db_path = _protected_db(tmp_path)
    key_path = _key_at(tmp_path / "key-root")
    sidecar = db_path.with_name(db_path.name + "-journal")
    sidecar.write_bytes(b"")
    sidecar.chmod(0o600)
    real_stat = Path.stat
    def foreign_owner_stat(self: Path, *, follow_symlinks: bool = True) -> os.stat_result:
        info = real_stat(self, follow_symlinks=follow_symlinks)
        if self == sidecar:
            fields = list(info)
            fields[4] = info.st_uid + 1
            return os.stat_result(tuple(fields))
        return info
    monkeypatch.setattr(Path, "stat", foreign_owner_stat)
    with pytest.raises(identity.CandidateIdentityError) as caught:
        _record(identity, db_path, key_path)
    _assert_closed_error(caught.value, tmp_path)
    assert "owner" in str(caught.value)
    assert _count_rows(db_path) == 0


def _render_closed_error(identity: ModuleType, db_path: Path, key_path: Path) -> str:
    try:
        _record(identity, db_path, key_path)
    except identity.CandidateIdentityError:
        return traceback.format_exc()
    pytest.fail("DID NOT RAISE CandidateIdentityError")


def test_missing_key_file_leaves_no_path_in_cause_chain(tmp_path: Path) -> None:
    """경쟁 없는 키 누락은 HS-03.01 검사기의 오류(원인 = 경로 담긴 FileNotFoundError)를"""
    identity = _load_identity_module()
    db_path = _protected_db(tmp_path)
    key_dir = tmp_path / "key-root"
    key_dir.mkdir()
    key_dir.chmod(0o700)
    rendered = _render_closed_error(identity, db_path, key_dir / _KEY_BASENAME)
    assert str(tmp_path) not in rendered


def test_key_directory_vanishing_leaves_no_path_in_cause_chain(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    identity = _load_identity_module()
    db_path = _protected_db(tmp_path)
    key_dir = tmp_path / "key-root"
    key_path = _key_at(key_dir)
    original = identity._reject_symlinked_chain
    def verify_then_vanish(path: Path, *, label: str) -> None:
        original(path, label=label)
        if label == "hmac key path":
            shutil.rmtree(key_dir)
    monkeypatch.setattr(identity, "_reject_symlinked_chain", verify_then_vanish)
    rendered = _render_closed_error(identity, db_path, key_path)
    assert str(tmp_path) not in rendered


def test_missing_db_file_leaves_no_path_in_cause_chain(tmp_path: Path) -> None:
    identity = _load_identity_module()
    db_path = _protected_db(tmp_path)
    key_path = _key_at(tmp_path / "key-root")
    db_path.unlink()
    rendered = _render_closed_error(identity, db_path, key_path)
    assert str(tmp_path) not in rendered
