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
OTHER_PAYLOAD = b"a-file-from-another-run"


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


def test_published_path_mismatch_keeps_our_file_and_drops_the_temp(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    """영수증 경로가 어긋나도 최종 이름은 건드리지 않고 임시 이름만 치운다.

    대조 실패는 "그 이름이 우리 것인지 확신할 수 없다"는 뜻이다. 지우기
    직전에 다시 확인해도 그 사이에 바뀔 수 있으므로, 최종 이름은 어떤
    경로에서도 지우지 않는다. 여기서는 루트가 옮겨져 경로만 낡았고 파일은
    우리 것이므로 내용이 그대로 남아야 하고, 영수증에 식별값이 채워져
    사람이 찾아갈 수 있어야 한다.
    """

    _hsrunner(monkeypatch)
    holder = _mkdir(tmp_path / "holder", 0o700)
    root = _mkdir(holder / "root", 0o700)
    outside = _mkdir(tmp_path / "outside", 0o700)
    _swap_root_at(monkeypatch, "_ensure_parent", root, holder, outside)

    receipt = write_protected_file(_config(root), "z.jsonl", PAYLOAD)

    moved = holder / "moved"
    assert receipt.status is BoundaryStatus.DENIED
    assert receipt.reason == "published_path_mismatch"
    assert sorted(entry.name for entry in moved.iterdir()) == ["z.jsonl"]
    assert (moved / "z.jsonl").read_bytes() == PAYLOAD
    published = os.stat(moved / "z.jsonl")
    assert (receipt.device, receipt.inode) == (published.st_dev, published.st_ino)
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


def test_receipt_identity_still_names_the_same_file_after_a_late_root_move(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    """경로 대조 직후 루트가 옮겨져도 식별값은 같은 파일을 가리킨다.

    주장을 낮춘다. 이 시험은 "영수증만으로 재조회할 수 있다"를 증명하지
    않는다. fixture 가 옮겨진 위치를 알고 순회할 뿐이다. 보이는 것은 경로
    문자열이 낡아도 장치·inode 쌍은 같은 객체를 계속 가리킨다는 사실이며,
    그래서 이 쌍은 위치를 찾는 값이 아니라 **대조용 검증값**이다.
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


def test_final_name_taken_over_after_check_is_not_reported_as_written(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    """경로 대조 직후 최종 이름이 다른 파일로 바뀌면 성공으로 보고하지 않는다.

    같은 러너 uid 의 다른 실행이 최종 이름을 같은 권한의 다른 일반 파일로
    갈아치우는 상황이다. 최종 이름을 다시 읽어 식별값을 얻으면 영수증이
    "원문 A 의 해시 + 파일 B 의 식별값" 이 된다. 식별값은 페이로드를 담았던
    임시 디스크립터에서 얻은 값이어야 한다.

    교체본은 우리가 만든 것이 아니므로 잔여물 목록은 단언하지 않는다.
    """

    _hsrunner(monkeypatch)
    root = _mkdir(tmp_path / "root", 0o700)
    original = RunnerBoundary._published_path_matches
    swapped = {"done": False}

    def take_over_final_name(
        self: RunnerBoundary, parent_fd: int, name: str, final_path: Path
    ) -> Any:
        result = original(self, parent_fd, name, final_path)
        if not swapped["done"]:
            swapped["done"] = True
            os.unlink(name, dir_fd=parent_fd)
            imposter = os.open(
                name, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600, dir_fd=parent_fd
            )
            os.write(imposter, b"a-different-file")
            os.close(imposter)
        return result

    monkeypatch.setattr(RunnerBoundary, "_published_path_matches", take_over_final_name)

    receipt = write_protected_file(_config(root), "taken.jsonl", PAYLOAD)

    assert swapped["done"]
    assert receipt.status is BoundaryStatus.DENIED


def test_written_receipt_identity_comes_from_the_written_file(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    """성공 영수증의 식별값은 페이로드를 담았던 디스크립터에서 온 값이다."""

    _hsrunner(monkeypatch)
    root = _mkdir(tmp_path / "root", 0o700)
    original = RunnerBoundary._fill_temp_file
    seen: list[os.stat_result] = []

    def record(self: RunnerBoundary, *args: Any, **kwargs: Any) -> os.stat_result:
        info = original(self, *args, **kwargs)
        seen.append(info)
        return info

    monkeypatch.setattr(RunnerBoundary, "_fill_temp_file", record)

    receipt = write_protected_file(_config(root), "two.jsonl", PAYLOAD)

    published = os.stat(root / "two.jsonl")
    assert receipt.status is BoundaryStatus.WRITTEN
    assert len(seen) == 1
    assert (receipt.device, receipt.inode) == (seen[0].st_dev, seen[0].st_ino)
    assert (receipt.device, receipt.inode) == (published.st_dev, published.st_ino)
    assert receipt.byte_count == len(PAYLOAD)


def test_ancestor_close_failure_stops_before_writing(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    """루트 사슬 중간 디렉터리를 닫지 못하면 쓰기로 넘어가지 않는다."""

    _hsrunner(monkeypatch)
    root = _mkdir(tmp_path / "root", 0o700)

    with MonkeyPatch.context() as patched:
        trap = CloseTrap(patched, root.parent.name)
        receipt = write_protected_file(_config(root), "never.jsonl", PAYLOAD)
    trap.drain()

    assert receipt.status is BoundaryStatus.DENIED
    assert receipt.reason == "protected_root_ancestor_invalid"
    assert list(root.iterdir()) == []
    assert sorted(trap.opened) == sorted(trap.attempted)


def test_intermediate_parent_close_failure_stops_before_writing(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    """부모 사슬 중간 디렉터리를 닫지 못하면 쓰기로 넘어가지 않는다."""

    _hsrunner(monkeypatch)
    root = _mkdir(tmp_path / "root", 0o700)

    with MonkeyPatch.context() as patched:
        trap = CloseTrap(patched, "sub")
        receipt = write_protected_file(_config(root), "sub/inner/never.jsonl", PAYLOAD)
    trap.drain()

    assert receipt.status is BoundaryStatus.DENIED
    assert receipt.reason == "parent_directory_invalid"
    assert list((root / "sub" / "inner").iterdir()) == []
    assert sorted(trap.opened) == sorted(trap.attempted)


def test_receipt_identity_is_not_re_read_after_the_check(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    """식별값을 대조 뒤에 다시 읽지 않는다.

    대조를 통과한 뒤에도 영수증을 만들기 전까지는 최종 이름이 바뀔 수 있다.
    그 창에서 이름을 갈아치운 뒤, 영수증이 임시 디스크립터에서 얻은 값을
    그대로 담고 있는지 본다. 이 시험이 잡는 것은 "대조는 하되 값은 최종
    이름에서 다시 읽는" 구현이다.

    임시 파일 삭제(``_remove``)를 창의 위치로 쓴다. 영수증 생성 바로 앞이고
    구현이 바뀌어도 그 자리에 남아 있다.
    """

    _hsrunner(monkeypatch)
    root = _mkdir(tmp_path / "root", 0o700)
    fill = RunnerBoundary._fill_temp_file
    remove = RunnerBoundary._remove
    seen: list[os.stat_result] = []
    swapped = {"done": False}

    def record(self: RunnerBoundary, *args: Any, **kwargs: Any) -> os.stat_result:
        info = fill(self, *args, **kwargs)
        seen.append(info)
        return info

    def take_over_on_cleanup(self: RunnerBoundary, parent_fd: int, name: str) -> bool:
        result = remove(self, parent_fd, name)
        if _is_temp_name(name) and not swapped["done"]:
            swapped["done"] = True
            os.unlink("three.jsonl", dir_fd=parent_fd)
            imposter = os.open(
                "three.jsonl",
                os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                0o600,
                dir_fd=parent_fd,
            )
            os.write(imposter, b"a-different-file")
            os.close(imposter)
        return result

    monkeypatch.setattr(RunnerBoundary, "_fill_temp_file", record)
    monkeypatch.setattr(RunnerBoundary, "_remove", take_over_on_cleanup)

    receipt = write_protected_file(_config(root), "three.jsonl", PAYLOAD)

    assert swapped["done"]
    assert len(seen) == 1
    assert (receipt.device, receipt.inode) == (seen[0].st_dev, seen[0].st_ino)
    assert receipt.byte_count == len(PAYLOAD)


def _take_over_final_name(
    monkeypatch: MonkeyPatch, final_name: str, seen: dict[str, Any]
) -> None:
    """경로 대조 직후 최종 이름을 같은 권한의 다른 일반 파일 B 로 갈아치운다.

    같은 러너 uid 의 다른 실행이 그 이름을 차지한 상황이다. B 는 우리 것이
    아니므로 경계가 지워서는 안 된다.
    """

    original = RunnerBoundary._published_path_matches

    def take_over(
        self: RunnerBoundary, parent_fd: int, name: str, final_path: Path
    ) -> Any:
        result = original(self, parent_fd, name, final_path)
        if "device" not in seen:
            os.unlink(final_name, dir_fd=parent_fd)
            imposter = os.open(
                final_name,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                0o600,
                dir_fd=parent_fd,
            )
            os.write(imposter, OTHER_PAYLOAD)
            info = os.fstat(imposter)
            os.close(imposter)
            seen["device"] = info.st_dev
            seen["inode"] = info.st_ino
        return result

    monkeypatch.setattr(RunnerBoundary, "_published_path_matches", take_over)


def test_replacement_file_is_never_deleted_on_mismatch(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    """최종 이름을 차지한 다른 실행의 파일은 지우지 않는다."""

    _hsrunner(monkeypatch)
    root = _mkdir(tmp_path / "root", 0o700)
    seen: dict[str, Any] = {}
    _take_over_final_name(monkeypatch, "taken.jsonl", seen)

    receipt = write_protected_file(_config(root), "taken.jsonl", PAYLOAD)

    survivor = root / "taken.jsonl"
    assert survivor.is_file(), "이름을 차지한 다른 실행의 파일이 지워졌다"
    info = os.stat(survivor)
    assert receipt.status is BoundaryStatus.DENIED
    assert receipt.reason == "published_path_mismatch"
    assert survivor.read_bytes() == OTHER_PAYLOAD
    assert (info.st_dev, info.st_ino) == (seen["device"], seen["inode"])
    assert sorted(entry.name for entry in root.iterdir()) == ["taken.jsonl"]


def test_cleanup_failure_keeps_the_published_file(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    """대조를 통과한 우리 파일은 임시 정리에 실패해도 지우지 않는다.

    대조로 소유가 증명된 파일이다. 되돌린다며 지우면 올바른 데이터를 잃는다.
    영수증에 경로와 식별값을 채워 사람이 이어받게 한다.
    """

    _hsrunner(monkeypatch)
    root = _mkdir(tmp_path / "root", 0o700)
    real_unlink = os.unlink

    def bad_unlink(name: Any, *args: Any, **kwargs: Any) -> None:
        if _is_temp_name(name):
            raise OSError(errno.EIO, "Input/output error")
        real_unlink(name, *args, **kwargs)

    with MonkeyPatch.context() as patched:
        patched.setattr(os, "unlink", bad_unlink)
        receipt = write_protected_file(_config(root), "kept.jsonl", PAYLOAD)

    kept = root / "kept.jsonl"
    assert kept.is_file(), "대조를 통과한 우리 파일이 지워졌다"
    info = os.stat(kept)
    assert receipt.status is BoundaryStatus.DENIED
    assert receipt.reason == "cleanup_failed"
    assert kept.read_bytes() == PAYLOAD
    assert receipt.path == kept
    assert (receipt.device, receipt.inode) == (info.st_dev, info.st_ino)


def test_mismatch_with_cleanup_failure_keeps_the_replacement(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    """이름을 차지한 파일은 임시 정리까지 실패해도 그대로 둔다."""

    _hsrunner(monkeypatch)
    root = _mkdir(tmp_path / "root", 0o700)
    seen: dict[str, Any] = {}
    _take_over_final_name(monkeypatch, "taken.jsonl", seen)
    real_unlink = os.unlink

    def bad_temp_unlink(name: Any, *args: Any, **kwargs: Any) -> None:
        if _is_temp_name(name):
            raise OSError(errno.EIO, "Input/output error")
        real_unlink(name, *args, **kwargs)

    with MonkeyPatch.context() as patched:
        patched.setattr(os, "unlink", bad_temp_unlink)
        receipt = write_protected_file(_config(root), "taken.jsonl", PAYLOAD)

    survivor = root / "taken.jsonl"
    assert survivor.is_file(), "이름을 차지한 다른 실행의 파일이 지워졌다"
    info = os.stat(survivor)
    assert receipt.status is BoundaryStatus.DENIED
    assert receipt.reason == "recovery_required"
    assert survivor.read_bytes() == OTHER_PAYLOAD
    assert (info.st_dev, info.st_ino) == (seen["device"], seen["inode"])
