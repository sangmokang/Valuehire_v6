"""영수증이 실제 파일을 가리키는지, 정리와 닫기 실패가 드러나는지 보는 시험.

앞선 회차와 같이 이 Mac 에 ``hsrunner`` 계정이 없어 uid 조회만 시험 fixture
로 대체한다. 파일 조작은 실제 OS 임시 디렉터리(``tmp_path``)에서 일어나고,
운영체제 호출은 좁은 구간에서만 실패시킨다.

닫기 고장은 **실제 close 를 부르기 전에** 실패시킨다. 실제로 닫은 뒤 예외만
던지면 디스크립터가 이미 풀려 있어 "열린 채 남는" 경우를 보지 못한다.
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


def _swap_root_at(
    monkeypatch: MonkeyPatch, seam: str, root: Path, holder: Path, outside: Path
) -> None:
    """``seam`` 메서드가 값을 돌려준 직후 루트 이름을 옮기고 symlink 로 바꾼다."""

    original = getattr(RunnerBoundary, seam)

    def swapped(self: RunnerBoundary, *args: Any, **kwargs: Any) -> Any:
        result = original(self, *args, **kwargs)
        if not (holder / "moved").exists():
            os.rename(root, holder / "moved")
            (holder / "root").symlink_to(outside, target_is_directory=True)
        return result

    monkeypatch.setattr(RunnerBoundary, seam, swapped)


def test_published_path_mismatch_removes_both_names(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    """영수증 경로가 게시 파일과 어긋나면 최종 이름도 임시 이름도 남기지 않는다."""

    _hsrunner(monkeypatch)
    holder = _mkdir(tmp_path / "holder", 0o700)
    root = _mkdir(holder / "root", 0o700)
    outside = _mkdir(tmp_path / "outside", 0o700)
    _swap_root_at(monkeypatch, "_ensure_parent", root, holder, outside)

    receipt = write_protected_file(_config(root), "z.jsonl", PAYLOAD)

    assert receipt.status is BoundaryStatus.DENIED
    assert receipt.reason == "published_path_mismatch"
    assert sorted(entry.name for entry in (holder / "moved").iterdir()) == []
    assert list(outside.iterdir()) == []


def test_mismatch_cleanup_failure_reports_recovery_required(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    """불일치를 되돌리다 임시 파일을 못 지우면 사람이 손대야 함을 밝힌다."""

    _hsrunner(monkeypatch)
    holder = _mkdir(tmp_path / "holder", 0o700)
    root = _mkdir(holder / "root", 0o700)
    outside = _mkdir(tmp_path / "outside", 0o700)
    _swap_root_at(monkeypatch, "_ensure_parent", root, holder, outside)
    real_unlink = os.unlink

    def bad_unlink(name: Any, *args: Any, **kwargs: Any) -> None:
        if _is_temp_name(name):
            raise OSError(errno.EIO, "Input/output error")
        real_unlink(name, *args, **kwargs)

    with MonkeyPatch.context() as patched:
        patched.setattr(os, "unlink", bad_unlink)
        receipt = write_protected_file(_config(root), "z.jsonl", PAYLOAD)

    assert receipt.status is BoundaryStatus.DENIED
    assert receipt.reason == "recovery_required"


def test_written_receipt_carries_device_and_inode(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    """성공 영수증은 경로 외에 파일 자체를 가리키는 식별값을 담는다."""

    _hsrunner(monkeypatch)
    root = _mkdir(tmp_path / "root", 0o700)

    receipt = write_protected_file(_config(root), "one.jsonl", PAYLOAD)

    written = root / "one.jsonl"
    info = os.stat(written)
    assert receipt.status is BoundaryStatus.WRITTEN
    assert receipt.device == info.st_dev
    assert receipt.inode == info.st_ino


def test_receipt_identity_finds_the_file_after_a_late_root_move(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    """경로 대조 직후 루트가 옮겨져도 식별값으로 게시 파일을 찾을 수 있다.

    경로 문자열은 영수증을 낸 뒤에도 다른 곳을 가리키게 만들 수 있다. 장치·
    inode 쌍은 같은 파일시스템 객체를 계속 가리키므로 재조회의 기준이 된다.
    """

    _hsrunner(monkeypatch)
    holder = _mkdir(tmp_path / "holder", 0o700)
    root = _mkdir(holder / "root", 0o700)
    outside = _mkdir(tmp_path / "outside", 0o700)
    _swap_root_at(monkeypatch, "_published_path_matches", root, holder, outside)

    receipt = write_protected_file(_config(root), "w.jsonl", PAYLOAD)

    assert receipt.device is not None
    assert receipt.inode is not None
    found = [
        entry
        for entry in (holder / "moved").iterdir()
        if (entry.stat().st_dev, entry.stat().st_ino) == (receipt.device, receipt.inode)
    ]
    assert len(found) == 1
    assert found[0].read_bytes() == PAYLOAD
    assert list(outside.iterdir()) == []


class CloseTrap:
    """``wanted`` 이름으로 연 디스크립터의 close 를 실제 close 전에 실패시킨다.

    실제로 닫아 버린 뒤 예외만 던지면 디스크립터가 이미 풀려 "열린 채 남는"
    경우를 보지 못한다. 그래서 여기서는 close 를 아예 부르지 않고 실패시키고,
    시험이 끝난 뒤 ``drain`` 으로 그 디스크립터만 직접 회수한다.
    """

    def __init__(self, monkeypatch: MonkeyPatch, wanted: str) -> None:
        self.opened: list[int] = []
        self.attempted: list[int] = []
        self.still_open: list[int] = []
        self._wanted = wanted
        self._targets: set[int] = set()
        self._real_open = os.open
        self._real_close = os.close
        monkeypatch.setattr(os, "open", self._track_open)
        monkeypatch.setattr(os, "close", self._track_close)

    def _track_open(self, path: Any, *args: Any, **kwargs: Any) -> int:
        fd = self._real_open(path, *args, **kwargs)
        self.opened.append(fd)
        if str(path) == self._wanted:
            self._targets.add(fd)
        return fd

    def _track_close(self, fd: int) -> None:
        self.attempted.append(fd)
        if fd in self._targets:
            self._targets.discard(fd)
            self.still_open.append(fd)
            raise OSError(errno.EIO, "Input/output error")
        self._real_close(fd)

    def drain(self) -> None:
        for fd in self.still_open:
            try:
                self._real_close(fd)
            except OSError:
                pass
        self.still_open.clear()


def test_parent_close_failure_is_not_reported_as_written(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    """부모 디렉터리 손잡이를 닫지 못하면 성공으로 보고하지 않는다."""

    _hsrunner(monkeypatch)
    root = _mkdir(tmp_path / "root", 0o700)

    with MonkeyPatch.context() as patched:
        trap = CloseTrap(patched, "sub")
        receipt = write_protected_file(_config(root), "sub/final.jsonl", PAYLOAD)
    trap.drain()

    assert receipt.status is BoundaryStatus.DENIED
    assert receipt.reason == "recovery_required"
    assert receipt.path == root / "sub" / "final.jsonl"
    assert receipt.device is not None
    assert receipt.inode is not None
    assert (root / "sub" / "final.jsonl").read_bytes() == PAYLOAD
    assert sorted(trap.opened) == sorted(trap.attempted)


def test_root_close_failure_is_not_reported_as_written(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    """보호 루트 손잡이를 닫지 못하면 성공으로 보고하지 않는다."""

    _hsrunner(monkeypatch)
    root = _mkdir(tmp_path / "root", 0o700)

    with MonkeyPatch.context() as patched:
        trap = CloseTrap(patched, "root")
        receipt = write_protected_file(_config(root), "final.jsonl", PAYLOAD)
    trap.drain()

    assert receipt.status is BoundaryStatus.DENIED
    assert receipt.reason == "recovery_required"
    assert receipt.device is not None
    assert (root / "final.jsonl").read_bytes() == PAYLOAD
    assert sorted(trap.opened) == sorted(trap.attempted)
