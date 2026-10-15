from __future__ import annotations

import os
import pwd
from pathlib import Path
from types import SimpleNamespace

from pytest import MonkeyPatch, raises

from humansearch.runner_boundary import (
    BoundaryStatus,
    RunnerBoundary,
    RunnerBoundaryConfig,
    write_protected_file,
)


def _uid() -> int:
    return os.getuid()


def _config(root: Path, *, implementer_uid: int | None = None) -> RunnerBoundaryConfig:
    current = _uid()
    return RunnerBoundaryConfig(
        implementer_uid=current + 1 if implementer_uid is None else implementer_uid,
        protected_root=root,
    )


def _hsrunner(monkeypatch: MonkeyPatch, uid: int | None = None) -> None:
    runner_uid = _uid() if uid is None else uid
    monkeypatch.setattr(
        pwd,
        "getpwnam",
        lambda name: SimpleNamespace(pw_uid=runner_uid),
    )


def test_missing_hsrunner_account_is_not_run_without_writing(tmp_path: Path) -> None:
    config = _config(tmp_path)

    receipt = write_protected_file(config, "receipt.jsonl", b"raw-output")

    assert receipt.status is BoundaryStatus.NOT_RUN
    assert receipt.reason == "runner_account_not_found"
    assert not (tmp_path / "receipt.jsonl").exists()


def test_arbitrary_fake_implementer_uid_cannot_enable_current_user_write(
    tmp_path: Path,
) -> None:
    config = RunnerBoundaryConfig(
        implementer_uid=_uid() + 99999,
        protected_root=tmp_path,
    )

    receipt = write_protected_file(config, "receipt.jsonl", b"raw-output")

    assert receipt.status is BoundaryStatus.NOT_RUN
    assert receipt.reason == "runner_account_not_found"
    assert not (tmp_path / "receipt.jsonl").exists()


def test_same_uid_is_not_run_without_writing(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    _hsrunner(monkeypatch)
    config = _config(tmp_path, implementer_uid=_uid())

    receipt = write_protected_file(config, "receipt.jsonl", b"raw-output")

    assert receipt.status is BoundaryStatus.NOT_RUN
    assert receipt.reason == "same_uid_not_os_isolated"
    assert not (tmp_path / "receipt.jsonl").exists()


def test_non_runner_process_is_denied_before_writing(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    _hsrunner(monkeypatch, _uid() + 1)
    config = _config(tmp_path, implementer_uid=_uid() + 2)

    receipt = write_protected_file(config, "receipt.jsonl", b"raw-output")

    assert receipt.status is BoundaryStatus.DENIED
    assert receipt.reason == "current_process_is_not_runner"
    assert not (tmp_path / "receipt.jsonl").exists()


def test_public_current_uid_override_is_not_accepted(tmp_path: Path) -> None:
    config = _config(tmp_path)

    with raises(TypeError):
        write_protected_file(  # type: ignore[call-arg]
            config, "receipt.jsonl", b"raw-output", current_uid=_uid()
        )


def test_target_cannot_escape_protected_root(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    _hsrunner(monkeypatch)
    config = _config(tmp_path)

    receipt = write_protected_file(config, "../escape.jsonl", b"raw-output")

    assert receipt.status is BoundaryStatus.DENIED
    assert receipt.reason == "target_escapes_protected_root"
    assert not (tmp_path.parent / "escape.jsonl").exists()


def test_target_symlink_is_denied(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    _hsrunner(monkeypatch)
    config = _config(tmp_path)
    outside = tmp_path.parent / "outside.jsonl"
    target = tmp_path / "receipt.jsonl"
    target.symlink_to(outside)

    receipt = write_protected_file(config, "receipt.jsonl", b"raw-output")

    assert receipt.status is BoundaryStatus.DENIED
    assert receipt.reason == "target_path_is_symlink"
    assert not outside.exists()


def test_protected_root_symlink_is_denied_without_writing(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    _hsrunner(monkeypatch)
    actual_root = tmp_path / "actual"
    actual_root.mkdir(mode=0o700)
    root_link = tmp_path / "root-link"
    root_link.symlink_to(actual_root, target_is_directory=True)
    config = _config(root_link)

    receipt = write_protected_file(config, "receipt.jsonl", b"raw-output")

    assert receipt.status is BoundaryStatus.DENIED
    assert receipt.reason == "protected_root_invalid"
    assert not (actual_root / "receipt.jsonl").exists()


def test_relative_protected_root_is_denied_without_writing(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    _hsrunner(monkeypatch)
    monkeypatch.chdir(tmp_path)
    Path("relative-root").mkdir(mode=0o700)
    config = _config(Path("relative-root"))

    receipt = write_protected_file(config, "receipt.jsonl", b"raw-output")

    assert receipt.status is BoundaryStatus.DENIED
    assert receipt.reason == "protected_root_not_absolute"
    assert not Path("relative-root/receipt.jsonl").exists()


def test_parent_symlink_is_denied_before_creating_under_target(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    _hsrunner(monkeypatch)
    protected_root = tmp_path / "protected"
    protected_root.mkdir(mode=0o700)
    outside = tmp_path / "outside"
    outside.mkdir(mode=0o700)
    (protected_root / "link").symlink_to(outside, target_is_directory=True)
    config = _config(protected_root)

    receipt = write_protected_file(config, "link/newdir/child.jsonl", b"raw-output")

    assert receipt.status is BoundaryStatus.DENIED
    assert receipt.reason == "parent_directory_invalid"
    assert not (outside / "newdir").exists()


def test_existing_regular_target_is_not_overwritten(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    _hsrunner(monkeypatch)
    config = _config(tmp_path)
    target = tmp_path / "receipt.jsonl"
    target.write_bytes(b"already-here")

    receipt = write_protected_file(config, "receipt.jsonl", b"new-payload")

    assert receipt.status is BoundaryStatus.DENIED
    assert receipt.reason == "target_already_exists"
    assert target.read_bytes() == b"already-here"


def test_runner_writes_new_file_without_returning_payload(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    _hsrunner(monkeypatch)
    config = _config(tmp_path)
    payload = b"raw-output-that-must-not-appear-in-receipt"

    receipt = write_protected_file(config, "receipts/one.jsonl", payload)

    written = tmp_path / "receipts" / "one.jsonl"
    assert receipt.status is BoundaryStatus.WRITTEN
    assert receipt.reason == "written"
    assert receipt.path == written
    assert receipt.byte_count == len(payload)
    assert receipt.sha256
    assert "raw-output" not in repr(receipt)
    assert written.read_bytes() == payload
    assert (tmp_path / "receipts").stat().st_mode & 0o777 == 0o700
    assert written.stat().st_mode & 0o777 == 0o600


def test_new_file_and_parent_modes_survive_restrictive_umask(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    _hsrunner(monkeypatch)
    config = _config(tmp_path)
    parent = tmp_path / "umask"
    written = parent / "receipt.jsonl"
    old_umask = os.umask(0o777)
    try:
        receipt = write_protected_file(config, "umask/receipt.jsonl", b"raw-output")
    finally:
        os.umask(old_umask)

    try:
        assert receipt.status is BoundaryStatus.WRITTEN
        assert parent.stat().st_mode & 0o777 == 0o700
        assert written.stat().st_mode & 0o777 == 0o600
    finally:
        if written.exists():
            written.chmod(0o600)
        if parent.exists():
            parent.chmod(0o700)


def test_public_boundary_keeps_function_surface_small() -> None:
    assert RunnerBoundary(_config(Path("/tmp/protected"))).config.protected_root == Path(
        "/tmp/protected"
    )
