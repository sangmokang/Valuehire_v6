"""HS-03.02 4차 RED — DB 저장 경계(Codex 14:50 높음 결함) 를 시험으로 먼저 고정한다.

재현 원문(2026-09-15 15:29:58, mktemp 격리, GIT_* 환경변수 제거):
  (a) DB 0644 · 부모 0755 로 완화 → outcome=inserted rows=1   ← 기록됐다
  (b) 호환 스키마 DB 를 git init 한 폴더 아래에 두고 호출 → outcome=inserted rows=1 ← 기록됐다
  (c) 대조군(정상 권한 · Git 밖) → outcome=inserted rows=1

저장 정본(HumanSearch 저장 계약 §3)은 "쓰기 직전에 부모 디렉터리와 대상
파일 경로 자체의 owner, mode, symlink 여부, 실제 경로가 승인된 보호 root 안인지 확인"하고
"권한 완화, 소유자 불일치, symlink, 승인 root 탈출은 저장 실패"라고 정한다. 보조 파일
(journal/wal/shm)도 같은 규칙을 따른다. 기록 함수는 링크와 존재만 보고 연결을 열었다.

시험 데이터는 전부 합성이다. 실명·이력서 원문·실제 키를 쓰지 않는다.
"""

from __future__ import annotations

import importlib
import os
import shutil
import sqlite3
import subprocess
from pathlib import Path
from types import ModuleType

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
    return str(identity.record_candidate_identity(db_path, record, hmac_key_path=key_path))


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


# ── 반례 (a) 권한 완화 ─────────────────────────────────────────────────────────


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


# ── 반례 (b) Git 작업 폴더 아래 ────────────────────────────────────────────────


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


# ── 일반 파일 · 보조 파일 경계 ─────────────────────────────────────────────────


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
    # 링크 자체의 모드는 0600 이 아니어서 모드 검사도 걸리지만, 사유는 symlink 여야 한다 —
    # 그래야 symlink 검사 줄을 지운 변이가 살아남지 못한다(2026-09-15 AC-D1 M7 실측).
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
    # SQLite 는 journal/wal 자리의 디렉터리를 열려다 I/O 오류를 낸다 — 행 수는 치운 뒤 센다.
    sidecar.rmdir()
    assert _count_rows(db_path) == 0


# ── 대조군 (c) ────────────────────────────────────────────────────────────────


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
