"""Small write boundary for HumanSearch runner-owned protected files."""
from __future__ import annotations

import errno
import hashlib
import os
import pwd
import stat
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

RUNNER_ACCOUNT = "hsrunner"

_ROOT_UID = 0
_DIR_MODE = 0o700
_FILE_MODE = 0o600
_PERMISSION_BITS = 0o777
# "타인 쓰기 가능"의 정의: 그룹 write 또는 기타 write 비트가 서 있는 것.
# 예외는 sticky(S_ISVTX) 하나뿐이다. sticky 디렉터리에서는 자기 소유가 아닌
# 항목을 지우거나 이름을 바꿀 수 없으므로 우리 루트 항목이 치환되지 않는다.
_OTHER_WRITE_BITS = stat.S_IWGRP | stat.S_IWOTH
_DIR_FLAGS = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
_NEW_FILE_FLAGS = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
_REQUIRED_DIR_FD_CALLS = (os.open, os.mkdir, os.chmod, os.stat, os.link, os.unlink)


class BoundaryStatus(Enum):
    """Outcome of a protected write boundary decision."""

    WRITTEN = "written"
    DENIED = "denied"
    NOT_RUN = "not_run"


@dataclass(frozen=True)
class RunnerBoundaryConfig:
    """Explicit implementer identity and storage root inputs for the boundary."""

    implementer_uid: int
    protected_root: Path


@dataclass(frozen=True)
class BoundaryReceipt:
    """PII-safe receipt for a protected write attempt."""

    status: BoundaryStatus
    reason: str
    path: Path | None = None
    sha256: str | None = None
    byte_count: int = 0


class RunnerBoundary:
    """Validate a runner-owned root and write new files without exposing payloads."""

    def __init__(self, config: RunnerBoundaryConfig) -> None:
        self.config = config

    def write_file(self, relative_path: str | Path, payload: bytes) -> BoundaryReceipt:
        runner_uid = self._runner_uid()
        if isinstance(runner_uid, BoundaryReceipt):
            return runner_uid
        preflight = self._preflight(runner_uid)
        if preflight is not None:
            return preflight
        root = self.config.protected_root
        if not root.is_absolute():
            return BoundaryReceipt(BoundaryStatus.DENIED, "protected_root_not_absolute")
        ancestors = self._check_ancestors(root, runner_uid)
        if ancestors is not None:
            return ancestors
        parts = self._relative_parts(relative_path)
        if parts is None:
            return BoundaryReceipt(BoundaryStatus.DENIED, "target_escapes_protected_root")
        return self._write_under_root(root, parts, payload, runner_uid)

    def _runner_uid(self) -> int | BoundaryReceipt:
        try:
            return int(pwd.getpwnam(RUNNER_ACCOUNT).pw_uid)
        except KeyError:
            return BoundaryReceipt(BoundaryStatus.NOT_RUN, "runner_account_not_found")

    def _preflight(self, runner_uid: int) -> BoundaryReceipt | None:
        if any(call not in os.supports_dir_fd for call in _REQUIRED_DIR_FD_CALLS):
            return BoundaryReceipt(BoundaryStatus.NOT_RUN, "platform_lacks_dir_fd")
        if runner_uid == self.config.implementer_uid:
            return BoundaryReceipt(BoundaryStatus.NOT_RUN, "same_uid_not_os_isolated")
        if os.getuid() != runner_uid:
            return BoundaryReceipt(BoundaryStatus.DENIED, "current_process_is_not_runner")
        return None

    def _check_ancestors(self, root: Path, runner_uid: int) -> BoundaryReceipt | None:
        """Reject a root whose path components could be substituted by others.

        Walks every component from ``/`` down to the root's parent. Each one must
        be a real directory (never a symlink), owned by the runner or by root,
        and not group/other writable unless it carries the sticky bit.
        """

        denied = BoundaryReceipt(BoundaryStatus.DENIED, "protected_root_ancestor_invalid")
        for ancestor in reversed(root.parents):
            try:
                info = os.lstat(ancestor)
            except OSError:
                return denied
            if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
                return denied
            if info.st_uid not in (runner_uid, _ROOT_UID):
                return denied
            if info.st_mode & _OTHER_WRITE_BITS and not info.st_mode & stat.S_ISVTX:
                return denied
        return None

    def _relative_parts(self, relative_path: str | Path) -> tuple[str, ...] | None:
        raw = Path(relative_path)
        if raw.is_absolute() or not raw.parts or ".." in raw.parts:
            return None
        return raw.parts

    def _write_under_root(
        self, root: Path, parts: tuple[str, ...], payload: bytes, runner_uid: int
    ) -> BoundaryReceipt:
        try:
            root_fd = os.open(root, _DIR_FLAGS)
        except OSError:
            return BoundaryReceipt(BoundaryStatus.DENIED, "protected_root_invalid")
        try:
            invalid = self._check_open_directory(
                root_fd, runner_uid, "protected_root_invalid"
            )
            if invalid is not None:
                return invalid
            parent_fd = self._ensure_parent(root_fd, parts[:-1], runner_uid)
            if isinstance(parent_fd, BoundaryReceipt):
                return parent_fd
            try:
                return self._write_new_file(
                    parent_fd, parts[-1], root.joinpath(*parts), payload, runner_uid
                )
            finally:
                if parent_fd != root_fd:
                    os.close(parent_fd)
        finally:
            os.close(root_fd)

    def _check_open_directory(
        self, dir_fd: int, runner_uid: int, reason: str
    ) -> BoundaryReceipt | None:
        info = os.fstat(dir_fd)
        if not stat.S_ISDIR(info.st_mode):
            return BoundaryReceipt(BoundaryStatus.DENIED, reason)
        if info.st_uid != runner_uid or info.st_mode & _PERMISSION_BITS != _DIR_MODE:
            return BoundaryReceipt(BoundaryStatus.DENIED, reason)
        return None

    def _ensure_parent(
        self, root_fd: int, dir_parts: tuple[str, ...], runner_uid: int
    ) -> int | BoundaryReceipt:
        """Open the target's parent directory relative to the pinned root fd."""

        reason = "parent_directory_invalid"
        denied = BoundaryReceipt(BoundaryStatus.DENIED, reason)
        current_fd = root_fd
        for part in dir_parts:
            created = True
            try:
                os.mkdir(part, _DIR_MODE, dir_fd=current_fd)
            except FileExistsError:
                created = False
            except OSError:
                return self._release(current_fd, root_fd, denied)
            try:
                # umask 가 mkdir 의 mode 를 깎아 낼 수 있다. 우리가 만든
                # 디렉터리는 열기 전에 0700 으로 되돌린다.
                if created:
                    os.chmod(part, _DIR_MODE, dir_fd=current_fd)
                next_fd = os.open(part, _DIR_FLAGS, dir_fd=current_fd)
            except OSError:
                return self._release(current_fd, root_fd, denied)
            invalid = self._check_open_directory(next_fd, runner_uid, reason)
            if current_fd != root_fd:
                os.close(current_fd)
            if invalid is not None:
                os.close(next_fd)
                return invalid
            current_fd = next_fd
        return current_fd

    def _release(
        self, dir_fd: int, root_fd: int, receipt: BoundaryReceipt
    ) -> BoundaryReceipt:
        if dir_fd != root_fd:
            os.close(dir_fd)
        return receipt

    def _write_new_file(
        self,
        parent_fd: int,
        name: str,
        final_path: Path,
        payload: bytes,
        runner_uid: int,
    ) -> BoundaryReceipt:
        occupied = self._check_target_absent(parent_fd, name)
        if occupied is not None:
            return occupied
        digest = hashlib.sha256(payload).hexdigest()
        temp_name = f".{os.urandom(8).hex()}.tmp"
        try:
            fd = os.open(temp_name, _NEW_FILE_FLAGS, _FILE_MODE, dir_fd=parent_fd)
        except OSError:
            return BoundaryReceipt(BoundaryStatus.DENIED, "write_failed")
        try:
            info = self._fill_temp_file(fd, payload)
        except OSError:
            return self._discard(parent_fd, temp_name, fd, "write_failed")
        os.close(fd)
        invalid = self._check_written_file(info, runner_uid)
        if invalid is not None:
            self._remove(parent_fd, temp_name)
            return invalid
        try:
            os.link(
                temp_name,
                name,
                src_dir_fd=parent_fd,
                dst_dir_fd=parent_fd,
                follow_symlinks=False,
            )
        except OSError as exc:
            reason = (
                "target_already_exists" if exc.errno == errno.EEXIST else "write_failed"
            )
            return self._discard(parent_fd, temp_name, None, reason)
        self._remove(parent_fd, temp_name)
        return BoundaryReceipt(
            BoundaryStatus.WRITTEN, "written", final_path, digest, len(payload)
        )

    def _fill_temp_file(self, fd: int, payload: bytes) -> os.stat_result:
        os.fchmod(fd, _FILE_MODE)
        view = memoryview(payload)
        sent = 0
        while sent < len(view):
            sent += os.write(fd, view[sent:])
        os.fsync(fd)
        return os.fstat(fd)

    def _check_target_absent(self, parent_fd: int, name: str) -> BoundaryReceipt | None:
        try:
            info = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
        except FileNotFoundError:
            return None
        except OSError:
            return BoundaryReceipt(BoundaryStatus.DENIED, "write_failed")
        if stat.S_ISLNK(info.st_mode):
            return BoundaryReceipt(BoundaryStatus.DENIED, "target_path_is_symlink")
        return BoundaryReceipt(BoundaryStatus.DENIED, "target_already_exists")

    def _check_written_file(
        self, info: os.stat_result, runner_uid: int
    ) -> BoundaryReceipt | None:
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
            return BoundaryReceipt(BoundaryStatus.DENIED, "written_path_not_regular_file")
        if info.st_uid != runner_uid or info.st_mode & _PERMISSION_BITS != _FILE_MODE:
            return BoundaryReceipt(BoundaryStatus.DENIED, "written_file_permission_invalid")
        return None

    def _discard(
        self, parent_fd: int, temp_name: str, fd: int | None, reason: str
    ) -> BoundaryReceipt:
        """Close the open handle and delete the half-written temporary file."""

        if fd is not None:
            os.close(fd)
        self._remove(parent_fd, temp_name)
        return BoundaryReceipt(BoundaryStatus.DENIED, reason)

    def _remove(self, parent_fd: int, name: str) -> None:
        try:
            os.unlink(name, dir_fd=parent_fd)
        except OSError:
            pass


def write_protected_file(
    config: RunnerBoundaryConfig,
    relative_path: str | Path,
    payload: bytes,
) -> BoundaryReceipt:
    """Write a new protected file through the runner boundary."""

    return RunnerBoundary(config).write_file(relative_path, payload)
