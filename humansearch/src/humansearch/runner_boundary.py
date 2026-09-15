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
# 항목을 지우거나 이름을 바꿀 수 없으므로 우리 경로 요소가 치환되지 않는다.
_OTHER_WRITE_BITS = stat.S_IWGRP | stat.S_IWOTH
_DIR_FLAGS = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
_NEW_FILE_FLAGS = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
_NO_FD = -1
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
    """PII-safe receipt for a protected write attempt.

    ``device`` and ``inode`` come from the descriptor that held the payload, so
    they identify the bytes this receipt is about. They are a **check value,
    not a locator**: no API here opens a file from that pair. A consumer opens
    the file by ``path`` (or through a pinned directory handle) and then
    confirms it is the right one by matching this pair and ``sha256``.
    """

    status: BoundaryStatus
    reason: str
    path: Path | None = None
    sha256: str | None = None
    byte_count: int = 0
    device: int | None = None
    inode: int | None = None


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

    def _relative_parts(self, relative_path: str | Path) -> tuple[str, ...] | None:
        raw = Path(relative_path)
        if raw.is_absolute() or not raw.parts or ".." in raw.parts:
            return None
        return raw.parts

    def _write_under_root(
        self, root: Path, parts: tuple[str, ...], payload: bytes, runner_uid: int
    ) -> BoundaryReceipt:
        opened = self._open_root_chain(root, runner_uid)
        if isinstance(opened, BoundaryReceipt):
            return opened
        root_fd = opened
        parent_fd = self._ensure_parent(root_fd, parts[:-1], runner_uid)
        if isinstance(parent_fd, BoundaryReceipt):
            return self._settle(parent_fd, self._close_fd(root_fd))
        receipt = self._write_new_file(
            parent_fd, parts[-1], root.joinpath(*parts), payload, runner_uid
        )
        released = True
        if parent_fd != root_fd:
            released = self._close_fd(parent_fd)
        released = self._close_fd(root_fd) and released
        return self._settle(receipt, released)

    def _settle(self, receipt: BoundaryReceipt, released: bool) -> BoundaryReceipt:
        """Fold the directory-handle cleanup result into the receipt.

        A close that reports an error leaves the descriptor in an unspecified
        state, so a successful write whose handles could not be released is not
        reported as success. The published file is left alone and the receipt
        keeps ``path`` and the device/inode pair so a person can check it.
        """

        if released or receipt.status is not BoundaryStatus.WRITTEN:
            return receipt
        return BoundaryReceipt(
            BoundaryStatus.DENIED,
            "recovery_required",
            receipt.path,
            receipt.sha256,
            receipt.byte_count,
            receipt.device,
            receipt.inode,
        )

    def _open_root_chain(self, root: Path, runner_uid: int) -> int | BoundaryReceipt:
        """Open every component of the root path one descriptor at a time.

        Each component is opened relative to the previous component's descriptor
        with ``O_NOFOLLOW`` and is validated through that descriptor, so the
        object we checked is the object we keep using. The path string is never
        resolved again afterwards, which closes the check-then-open gap.
        """

        parts = root.parts
        last = len(parts) - 1
        current = _NO_FD
        for index, part in enumerate(parts):
            is_root = index == last
            reason = (
                "protected_root_invalid" if is_root else "protected_root_ancestor_invalid"
            )
            try:
                if current == _NO_FD:
                    opened = os.open(part, _DIR_FLAGS)
                else:
                    opened = os.open(part, _DIR_FLAGS, dir_fd=current)
            except OSError:
                self._close_fd(current)
                return BoundaryReceipt(BoundaryStatus.DENIED, reason)
            released = self._close_fd(current)
            current = opened
            invalid = self._check_open_directory(
                current, runner_uid, reason, ancestor=not is_root
            )
            if invalid is None and not released:
                # 닫지 못한 손잡이는 방금 지나온 조상이다. 이유를 현재 단계가
                # 아니라 그 손잡이에 붙여야 어디가 막혔는지 읽힌다.
                invalid = BoundaryReceipt(
                    BoundaryStatus.DENIED, "protected_root_ancestor_invalid"
                )
            if invalid is not None:
                self._close_fd(current)
                return invalid
        return current

    def _check_open_directory(
        self, dir_fd: int, runner_uid: int, reason: str, *, ancestor: bool
    ) -> BoundaryReceipt | None:
        """Validate an already-open directory. Never raises, always decides."""

        denied = BoundaryReceipt(BoundaryStatus.DENIED, reason)
        try:
            info = os.fstat(dir_fd)
        except OSError:
            return denied
        if not stat.S_ISDIR(info.st_mode):
            return denied
        if not ancestor:
            if info.st_uid != runner_uid:
                return denied
            if info.st_mode & _PERMISSION_BITS != _DIR_MODE:
                return denied
            return None
        if info.st_uid not in (runner_uid, _ROOT_UID):
            return denied
        if info.st_mode & _OTHER_WRITE_BITS and not info.st_mode & stat.S_ISVTX:
            return denied
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
            invalid = self._check_open_directory(
                next_fd, runner_uid, reason, ancestor=False
            )
            released = True
            if current_fd != root_fd:
                released = self._close_fd(current_fd)
            if invalid is None and not released:
                invalid = BoundaryReceipt(BoundaryStatus.DENIED, reason)
            if invalid is not None:
                self._close_fd(next_fd)
                return invalid
            current_fd = next_fd
        return current_fd

    def _release(
        self, dir_fd: int, root_fd: int, receipt: BoundaryReceipt
    ) -> BoundaryReceipt:
        """Close an intermediate handle on a path that already failed.

        The close result is deliberately not promoted here: nothing was written,
        and the caller's reason names the actual problem more precisely.
        """

        if dir_fd != root_fd:
            self._close_fd(dir_fd)
        return receipt

    def _close_fd(self, fd: int) -> bool:
        """Close one descriptor and say whether that succeeded.

        POSIX leaves the descriptor state unspecified when ``close`` reports an
        error, so a failure here is never treated as a harmless detail: callers
        must decide what it means for the receipt they are about to return.
        """

        if fd == _NO_FD:
            return True
        try:
            os.close(fd)
        except OSError:
            return False
        return True

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
        stored = self._store_payload(parent_fd, fd, temp_name, payload)
        if isinstance(stored, BoundaryReceipt):
            return stored
        invalid = self._check_written_file(stored, runner_uid)
        if invalid is not None:
            return self._discard(parent_fd, temp_name, invalid.reason)
        return self._publish(parent_fd, temp_name, name, final_path, digest, stored)

    def _store_payload(
        self, parent_fd: int, fd: int, temp_name: str, payload: bytes
    ) -> os.stat_result | BoundaryReceipt:
        try:
            info = self._fill_temp_file(fd, payload)
        except OSError:
            self._close_fd(fd)
            return self._discard(parent_fd, temp_name, "write_failed")
        if not self._close_fd(fd):
            return self._discard(parent_fd, temp_name, "write_failed")
        return info

    def _fill_temp_file(self, fd: int, payload: bytes) -> os.stat_result:
        os.fchmod(fd, _FILE_MODE)
        view = memoryview(payload)
        sent = 0
        while sent < len(view):
            sent += os.write(fd, view[sent:])
        os.fsync(fd)
        return os.fstat(fd)

    def _publish(
        self,
        parent_fd: int,
        temp_name: str,
        name: str,
        final_path: Path,
        digest: str,
        written: os.stat_result,
    ) -> BoundaryReceipt:
        """Give the finished temporary file its final name, or undo everything.

        ``written`` comes from ``fstat`` on the descriptor that actually held the
        payload, so it names our bytes. The entry now sitting under ``name`` has
        to be that same object; anything else means the name was taken over
        between the link and this check, and the receipt would otherwise pair
        our payload hash with somebody else's file.
        """

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
            return self._discard(parent_fd, temp_name, reason)
        confirmed = self._published_path_matches(parent_fd, name, final_path)
        if confirmed:
            confirmed = self._published_entry_is(parent_fd, name, written)
        if not confirmed:
            return self._abandon_publication(
                parent_fd,
                temp_name,
                self._mismatch_receipt(parent_fd, name, final_path, digest, written),
            )
        if not self._remove(parent_fd, temp_name):
            return self._describe(
                BoundaryStatus.DENIED, "cleanup_failed", final_path, digest, written
            )
        return self._describe(
            BoundaryStatus.WRITTEN, "written", final_path, digest, written
        )

    def _describe(
        self,
        status: BoundaryStatus,
        reason: str,
        final_path: Path,
        digest: str,
        written: os.stat_result,
    ) -> BoundaryReceipt:
        """Name the file we wrote, using the descriptor that held the payload."""

        return BoundaryReceipt(
            status, reason, final_path, digest,
            written.st_size, written.st_dev, written.st_ino,
        )

    def _mismatch_receipt(
        self,
        parent_fd: int,
        name: str,
        final_path: Path,
        digest: str,
        written: os.stat_result,
    ) -> BoundaryReceipt:
        """Describe a failed confirmation, naming our file only when it is ours."""

        if not self._published_entry_is(parent_fd, name, written):
            return BoundaryReceipt(BoundaryStatus.DENIED, "published_path_mismatch")
        return self._describe(
            BoundaryStatus.DENIED, "published_path_mismatch", final_path, digest, written
        )

    def _abandon_publication(
        self, parent_fd: int, temp_name: str, found: BoundaryReceipt
    ) -> BoundaryReceipt:
        """Drop only our temporary file and leave the final name untouched.

        A failed confirmation is exactly the evidence that the final name may
        hold another run's file, so it is never unlinked. Re-checking ownership
        just before unlinking would leave the same window open, so the boundary
        does not unlink a name it cannot own outright.
        """

        if not self._remove(parent_fd, temp_name):
            return BoundaryReceipt(BoundaryStatus.DENIED, "recovery_required")
        return found

    def _published_entry_is(
        self, parent_fd: int, name: str, written: os.stat_result
    ) -> bool:
        """Check the entry under ``name`` is the object we wrote, not a stand-in."""

        try:
            info = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
        except OSError:
            return False
        return (info.st_dev, info.st_ino) == (written.st_dev, written.st_ino)

    def _published_path_matches(
        self, parent_fd: int, name: str, final_path: Path
    ) -> bool:
        """Check the receipt path names the very file we published."""

        try:
            through_fd = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
            through_path = os.lstat(final_path)
        except OSError:
            return False
        return (through_fd.st_dev, through_fd.st_ino) == (
            through_path.st_dev,
            through_path.st_ino,
        )

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
        self, parent_fd: int, temp_name: str, reason: str
    ) -> BoundaryReceipt:
        """Delete the temporary file. Say so plainly when that is impossible."""

        if not self._remove(parent_fd, temp_name):
            return BoundaryReceipt(BoundaryStatus.DENIED, "recovery_required")
        return BoundaryReceipt(BoundaryStatus.DENIED, reason)

    def _remove(self, parent_fd: int, name: str) -> bool:
        try:
            os.unlink(name, dir_fd=parent_fd)
        except FileNotFoundError:
            return True
        except OSError:
            return False
        return True


def write_protected_file(
    config: RunnerBoundaryConfig,
    relative_path: str | Path,
    payload: bytes,
) -> BoundaryReceipt:
    """Write a new protected file through the runner boundary."""

    return RunnerBoundary(config).write_file(relative_path, payload)
