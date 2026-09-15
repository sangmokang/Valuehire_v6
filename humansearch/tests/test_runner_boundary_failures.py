"""경계의 실패 경로 회귀 시험 — 검사와 개방 사이의 틈, 정리 실패, FD 누수.

1차와 같이 이 Mac 에 ``hsrunner`` 계정이 없어 uid 조회만 시험 fixture 로
대체한다(``_hsrunner``). 파일 조작은 전부 실제 OS 임시 디렉터리(``tmp_path``)
에서 일어난다. 운영체제 호출(``os.unlink``·``os.close``·``os.fstat``)을 좁은
구간에서만 실패시켜, 실제 장애 파일시스템 없이 같은 결과를 만든다.
"""

from __future__ import annotations

import errno
import os
import pwd
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from pytest import MonkeyPatch

from humansearch.runner_boundary import (
    BoundaryStatus,
    RunnerBoundary,
    RunnerBoundaryConfig,
    write_protected_file,
)

PAYLOAD = b"synthetic-runner-payload"


def _uid() -> int:
    return os.getuid()


def _config(root: Path) -> RunnerBoundaryConfig:
    return RunnerBoundaryConfig(implementer_uid=_uid() + 1, protected_root=root)


def _hsrunner(monkeypatch: MonkeyPatch) -> None:
    runner_uid = _uid()
    monkeypatch.setattr(
        pwd, "getpwnam", lambda name: SimpleNamespace(pw_uid=runner_uid)
    )


def _mkdir(path: Path, mode: int) -> Path:
    path.mkdir(mode=mode)
    path.chmod(mode)
    return path


def _is_temp_name(name: object) -> bool:
    text = str(name)
    return text.startswith(".") and text.endswith(".tmp")


def _fail_temp_unlink(monkeypatch: MonkeyPatch) -> None:
    """임시 이름 삭제만 EIO 로 실패시킨다. 다른 이름 삭제는 그대로 둔다."""

    real_unlink = os.unlink

    def bad_unlink(name: Any, *args: Any, **kwargs: Any) -> None:
        if _is_temp_name(name):
            raise OSError(errno.EIO, "Input/output error")
        real_unlink(name, *args, **kwargs)

    monkeypatch.setattr(os, "unlink", bad_unlink)


def test_ancestor_replaced_between_check_and_open_never_writes_outside(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    """조상 검사와 루트 개방 사이에 조상이 바뀌어도 보호 밖에 쓰지 않는다.

    ``_relative_parts`` 반환 직후를 교체 시점으로 쓴다. 이 시점은 조상 검사
    뒤이자 루트를 열기 전이라, 경로 문자열을 다시 해석하는 구현이라면 바뀐
    조상을 따라간다. 인자 모양에 의존하지 않도록 ``*args`` 로 위임한다.
    """

    _hsrunner(monkeypatch)
    holder = _mkdir(tmp_path / "holder", 0o700)
    inner = _mkdir(holder / "inner", 0o700)
    root = _mkdir(inner / "root", 0o700)
    outside = _mkdir(tmp_path / "outside", 0o700)
    outside_root = _mkdir(outside / "root", 0o700)
    original = RunnerBoundary._relative_parts

    def swap_ancestor(self: RunnerBoundary, *args: Any, **kwargs: Any) -> Any:
        result = original(self, *args, **kwargs)
        if not (holder / "moved").exists():
            os.rename(inner, holder / "moved")
            (holder / "inner").symlink_to(outside, target_is_directory=True)
        return result

    monkeypatch.setattr(RunnerBoundary, "_relative_parts", swap_ancestor)

    receipt = write_protected_file(_config(root), "x.jsonl", PAYLOAD)

    assert list(outside_root.iterdir()) == []
    assert receipt.status is BoundaryStatus.DENIED


def test_written_receipt_path_matches_the_published_file(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    """루트가 개방 뒤 옮겨져도 성공 영수증의 경로는 실제 파일과 일치한다.

    성공으로 보고했는데 영수증 경로에 파일이 없으면 이후 읽기·삭제 장부가
    다른 위치를 본다. 성공이면 경로가 실제 게시된 파일과 같은 inode 여야
    하고, 그렇게 보장할 수 없으면 성공으로 보고하지 않아야 한다.
    """

    _hsrunner(monkeypatch)
    holder = _mkdir(tmp_path / "holder", 0o700)
    root = _mkdir(holder / "root", 0o700)
    outside = _mkdir(tmp_path / "outside", 0o700)
    original = RunnerBoundary._ensure_parent

    def swap_root_after_check(self: RunnerBoundary, *args: Any, **kwargs: Any) -> Any:
        result = original(self, *args, **kwargs)
        if not (holder / "moved").exists():
            os.rename(root, holder / "moved")
            (holder / "root").symlink_to(outside, target_is_directory=True)
        return result

    monkeypatch.setattr(RunnerBoundary, "_ensure_parent", swap_root_after_check)

    receipt = write_protected_file(_config(root), "y.jsonl", PAYLOAD)

    assert list(outside.iterdir()) == []
    if receipt.status is BoundaryStatus.WRITTEN:
        assert receipt.path is not None
        assert receipt.path.is_file()


def test_cleanup_failure_after_publish_is_not_reported_as_written(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    """게시 뒤 임시 이름 삭제가 실패하면 성공으로 보고하지 않는다.

    최종 이름은 되돌리지 않는다. 대조로 소유가 증명된 우리 파일이라 지우면
    올바른 데이터를 잃는다. 이 단언은 2026-09-15 계약 변경을 따른다.
    """

    _hsrunner(monkeypatch)
    root = _mkdir(tmp_path / "root", 0o700)

    with MonkeyPatch.context() as patched:
        _fail_temp_unlink(patched)
        receipt = write_protected_file(_config(root), "final.jsonl", PAYLOAD)

    assert receipt.status is BoundaryStatus.DENIED
    assert receipt.reason == "cleanup_failed"
    assert (root / "final.jsonl").read_bytes() == PAYLOAD


def test_failed_write_cleanup_failure_reports_recovery_required(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    """쓰기 실패 뒤 임시 파일도 지우지 못하면 사람이 손대야 함을 밝힌다."""

    _hsrunner(monkeypatch)
    root = _mkdir(tmp_path / "root", 0o700)
    real_write = os.write

    def fail_write(fd: int, data: Any) -> int:
        if bytes(data) == PAYLOAD:
            raise OSError(errno.ENOSPC, "No space left on device")
        return real_write(fd, data)

    with MonkeyPatch.context() as patched:
        patched.setattr(os, "write", fail_write)
        _fail_temp_unlink(patched)
        receipt = write_protected_file(_config(root), "final.jsonl", PAYLOAD)

    assert receipt.status is BoundaryStatus.DENIED
    assert receipt.reason == "recovery_required"
    assert not (root / "final.jsonl").exists()


def test_close_failure_returns_receipt_and_removes_temp_file(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    """임시 파일 close 가 실패해도 예외가 새지 않고 임시 파일이 정리된다."""

    _hsrunner(monkeypatch)
    root = _mkdir(tmp_path / "root", 0o700)
    real_open = os.open
    real_close = os.close
    temp_fds: set[int] = set()

    def track_open(path: Any, *args: Any, **kwargs: Any) -> int:
        fd = real_open(path, *args, **kwargs)
        if _is_temp_name(path):
            temp_fds.add(fd)
        return fd

    def fail_close(fd: int) -> None:
        real_close(fd)
        if fd in temp_fds:
            temp_fds.discard(fd)
            raise OSError(errno.EIO, "Input/output error")

    with MonkeyPatch.context() as patched:
        patched.setattr(os, "open", track_open)
        patched.setattr(os, "close", fail_close)
        receipt = write_protected_file(_config(root), "final.jsonl", PAYLOAD)

    assert receipt.status is BoundaryStatus.DENIED
    assert receipt.reason == "write_failed"
    assert list(root.iterdir()) == []


def test_child_directory_check_failure_closes_every_opened_descriptor(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    """자식 디렉터리 검증이 실패해도 연 FD 를 모두 닫고 영수증을 돌려준다.

    고장 지점을 호출 횟수가 아니라 대상으로 고정한다. ``sub`` 를 연 직후
    받은 FD 의 fstat 만 실패시키므로, 구현이 조상 검사를 몇 번 하든 공격
    지점이 자식 디렉터리 검사에 그대로 머문다.
    """

    _hsrunner(monkeypatch)
    root = _mkdir(tmp_path / "root", 0o700)
    real_open = os.open
    real_close = os.close
    real_fstat = os.fstat
    opened: list[int] = []
    closed: list[int] = []
    targets: set[int] = set()

    def track_open(path: Any, *args: Any, **kwargs: Any) -> int:
        fd = real_open(path, *args, **kwargs)
        opened.append(fd)
        if str(path) == "sub":
            targets.add(fd)
        return fd

    def track_close(fd: int) -> None:
        closed.append(fd)
        targets.discard(fd)
        real_close(fd)

    def fail_child_fstat(fd: int) -> os.stat_result:
        if fd in targets:
            raise OSError(errno.EIO, "Input/output error")
        return real_fstat(fd)

    try:
        with MonkeyPatch.context() as patched:
            patched.setattr(os, "open", track_open)
            patched.setattr(os, "close", track_close)
            patched.setattr(os, "fstat", fail_child_fstat)
            receipt = write_protected_file(_config(root), "sub/final.jsonl", PAYLOAD)
    finally:
        for leaked in [fd for fd in opened if fd not in closed]:
            try:
                real_close(leaked)
            except OSError:
                pass

    assert receipt.status is BoundaryStatus.DENIED
    assert receipt.reason == "parent_directory_invalid"
    assert sorted(opened) == sorted(closed)
