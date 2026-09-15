"""보호 루트 경계의 경로 치환·중단된 쓰기에 대한 회귀 시험.

이 Mac 에는 ``hsrunner`` 계정이 없다. 그래서 모든 시험은 ``pwd.getpwnam`` 만
현재 uid 로 돌려주도록 바꾼 fixture 를 쓴다(``_hsrunner``). 경계 로직 자체는
그대로 두고 "러너 계정의 uid" 조회만 대체하는 것이며, 이 대체는 시험에만
있고 제품 코드에는 없다. 파일 조작은 전부 실제 OS 임시 디렉터리(``tmp_path``)
에서 일어난다. 이 Mac 의 ``tmp_path`` 는 이미 해석된 경로이고 조상은 root
소유 0755 또는 사용자 소유 0700 이라 조상 체인 규칙을 그대로 통과한다.
"""

from __future__ import annotations

import errno
import os
import pwd
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Self

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
    """``hsrunner`` 계정 부재를 우회한다. uid 조회만 현재 uid 로 대체한다."""

    runner_uid = _uid()
    monkeypatch.setattr(
        pwd, "getpwnam", lambda name: SimpleNamespace(pw_uid=runner_uid)
    )


def _mkdir(path: Path, mode: int) -> Path:
    path.mkdir(mode=mode)
    path.chmod(mode)
    return path


def test_protected_root_symlink_is_denied_and_writes_nothing(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    """회귀 보호: 보호 루트 자체가 symlink 면 거부하고 링크 대상에 쓰지 않는다."""

    _hsrunner(monkeypatch)
    actual = _mkdir(tmp_path / "actual", 0o700)
    link = tmp_path / "root-link"
    link.symlink_to(actual, target_is_directory=True)

    receipt = write_protected_file(_config(link), "a.jsonl", PAYLOAD)

    assert receipt.status is BoundaryStatus.DENIED
    assert receipt.reason == "protected_root_invalid"
    assert list(actual.iterdir()) == []


def test_protected_root_ancestor_symlink_is_denied_and_writes_nothing(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    """루트의 상위 경로 요소가 symlink 면 거부하고 링크 대상에 쓰지 않는다."""

    _hsrunner(monkeypatch)
    real_parent = _mkdir(tmp_path / "realparent", 0o700)
    parent_link = tmp_path / "parentlink"
    parent_link.symlink_to(real_parent, target_is_directory=True)
    root = _mkdir(parent_link / "root", 0o700)

    receipt = write_protected_file(_config(root), "b.jsonl", PAYLOAD)

    assert receipt.status is BoundaryStatus.DENIED
    assert receipt.reason == "protected_root_ancestor_invalid"
    assert list((real_parent / "root").iterdir()) == []


def test_world_writable_ancestor_is_denied_and_writes_nothing(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    """상위 디렉터리가 sticky 없이 타인 쓰기 가능(0777)이면 거부한다."""

    _hsrunner(monkeypatch)
    world_parent = _mkdir(tmp_path / "worldparent", 0o777)
    root = _mkdir(world_parent / "root", 0o700)

    receipt = write_protected_file(_config(root), "w.jsonl", PAYLOAD)

    assert receipt.status is BoundaryStatus.DENIED
    assert receipt.reason == "protected_root_ancestor_invalid"
    assert list(root.iterdir()) == []


def test_sticky_world_writable_ancestor_is_accepted(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    """sticky 가 붙은 타인 쓰기 가능 상위(/tmp 형태)는 허용한다.

    sticky 디렉터리에서는 남이 만든 항목을 타인이 지우거나 이름을 바꿀 수
    없으므로 우리 루트 항목이 치환되지 않는다. 규칙이 "타인 쓰기 비트가 있으면
    무조건 거부"가 아니라 "sticky 예외를 둔다"는 것을 이 시험이 고정한다.
    """

    _hsrunner(monkeypatch)
    sticky_parent = _mkdir(tmp_path / "stickyparent", 0o1777)
    root = _mkdir(sticky_parent / "root", 0o700)

    receipt = write_protected_file(_config(root), "s.jsonl", PAYLOAD)

    assert receipt.status is BoundaryStatus.WRITTEN
    assert (root / "s.jsonl").read_bytes() == PAYLOAD


def test_root_replaced_after_check_never_writes_outside(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    """검사 통과 직후 루트 항목이 symlink 로 바뀌어도 보호 밖에 쓰지 않는다.

    ``_ensure_parent`` 반환 직후를 교체 시점으로 쓴다. 인자 모양에 의존하지
    않도록 ``*args`` 로 원본에 위임한다. 단언은 "보호 밖 디렉터리에 파일 0"
    하나뿐이라, 구현이 경로 문자열 대신 디렉터리 FD 를 고정하는 방식으로
    바뀌어도 그대로 성립한다.
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

    write_protected_file(_config(root), "c.jsonl", PAYLOAD)

    assert list(outside.iterdir()) == []


def _fail_payload_writes(monkeypatch: MonkeyPatch) -> None:
    """페이로드를 쓰는 순간에만 ENOSPC 를 일으킨다.

    어떤 쓰기 방식을 쓰든 같은 고장을 주입하려고 ``os.write`` 와 ``os.fdopen``
    양쪽을 막는다. 페이로드 바이트가 정확히 일치할 때만 실패시키므로 pytest
    자신의 캡처 쓰기는 건드리지 않는다.
    """

    real_write = os.write

    def fake_write(fd: int, data: Any) -> int:
        if bytes(data) == PAYLOAD:
            raise OSError(errno.ENOSPC, "No space left on device")
        return real_write(fd, data)

    class FailingHandle:
        def __init__(self, fd: int) -> None:
            self.fd = fd

        def __enter__(self) -> Self:
            return self

        def __exit__(self, *exc: object) -> None:
            os.close(self.fd)

        def write(self, data: bytes) -> int:
            if bytes(data) == PAYLOAD:
                raise OSError(errno.ENOSPC, "No space left on device")
            return len(data)

    monkeypatch.setattr(os, "write", fake_write)
    monkeypatch.setattr(os, "fdopen", lambda fd, *a, **k: FailingHandle(fd))


def test_interrupted_write_leaves_no_file_behind(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    """쓰기 도중 OSError 가 나면 최종 파일도 임시 파일도 남기지 않는다."""

    _hsrunner(monkeypatch)
    root = _mkdir(tmp_path / "root", 0o700)

    with MonkeyPatch.context() as patched:
        _fail_payload_writes(patched)
        receipt = write_protected_file(_config(root), "d.jsonl", PAYLOAD)

    assert receipt.status is not BoundaryStatus.WRITTEN
    assert sorted(entry.name for entry in root.iterdir()) == []


def test_retry_after_interrupted_write_succeeds(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    """중단된 쓰기 뒤 같은 경로로 다시 쓰면 성공한다(영구 거부 금지)."""

    _hsrunner(monkeypatch)
    root = _mkdir(tmp_path / "root", 0o700)

    with MonkeyPatch.context() as patched:
        _fail_payload_writes(patched)
        write_protected_file(_config(root), "e.jsonl", PAYLOAD)

    receipt = write_protected_file(_config(root), "e.jsonl", PAYLOAD)

    assert receipt.status is BoundaryStatus.WRITTEN
    assert receipt.reason == "written"
    assert (root / "e.jsonl").read_bytes() == PAYLOAD
    assert (root / "e.jsonl").stat().st_mode & 0o777 == 0o600


def test_platform_without_dir_fd_support_is_not_run(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    """디렉터리 FD 상대 호출이 없는 플랫폼에서는 쓰지 않고 멈춘다.

    경계의 보장은 dir_fd 상대 열기에 기대고 있다. 그 전제가 없으면 조용히
    경로 문자열로 되돌아가지 않고 NOT_RUN 으로 멈춘다.
    """

    _hsrunner(monkeypatch)
    root = _mkdir(tmp_path / "root", 0o700)
    monkeypatch.setattr(os, "supports_dir_fd", frozenset())

    receipt = write_protected_file(_config(root), "p.jsonl", PAYLOAD)

    assert receipt.status is BoundaryStatus.NOT_RUN
    assert receipt.reason == "platform_lacks_dir_fd"
    assert list(root.iterdir()) == []
