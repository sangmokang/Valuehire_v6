"""Small write boundary for HumanSearch runner-owned protected files."""
from __future__ import annotations

import hashlib
import os
import pwd
import stat
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

RUNNER_ACCOUNT = "hsrunner"


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
        root_check = self._check_existing_directory(
            root, runner_uid, "protected_root_invalid"
        )
        if root_check is not None:
            return root_check
        target = self._target_path(root, relative_path)
        if target is None:
            return BoundaryReceipt(BoundaryStatus.DENIED, "target_escapes_protected_root")
        parent_check = self._ensure_parent(root, target.parent, runner_uid)
        if parent_check is not None:
            return parent_check
        if target.is_symlink():
            return BoundaryReceipt(BoundaryStatus.DENIED, "target_path_is_symlink")
        if target.exists():
            return BoundaryReceipt(BoundaryStatus.DENIED, "target_already_exists")
        return self._write_new_file(target, payload, runner_uid)

    def _runner_uid(self) -> int | BoundaryReceipt:
        try:
            return int(pwd.getpwnam(RUNNER_ACCOUNT).pw_uid)
        except KeyError:
            return BoundaryReceipt(BoundaryStatus.NOT_RUN, "runner_account_not_found")

    def _preflight(self, runner_uid: int) -> BoundaryReceipt | None:
        if runner_uid == self.config.implementer_uid:
            return BoundaryReceipt(BoundaryStatus.NOT_RUN, "same_uid_not_os_isolated")
        if os.getuid() != runner_uid:
            return BoundaryReceipt(BoundaryStatus.DENIED, "current_process_is_not_runner")
        return None

    def _check_existing_directory(
        self, path: Path, runner_uid: int, reason: str
    ) -> BoundaryReceipt | None:
        try:
            info = path.lstat()
        except OSError:
            return BoundaryReceipt(BoundaryStatus.DENIED, reason)
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
            return BoundaryReceipt(BoundaryStatus.DENIED, reason)
        if info.st_uid != runner_uid or info.st_mode & 0o777 != 0o700:
            return BoundaryReceipt(BoundaryStatus.DENIED, reason)
        return None

    def _target_path(self, root: Path, relative_path: str | Path) -> Path | None:
        raw = Path(relative_path)
        if raw.is_absolute() or ".." in raw.parts:
            return None
        return root / raw

    def _ensure_parent(
        self, root: Path, parent: Path, runner_uid: int
    ) -> BoundaryReceipt | None:
        try:
            parts = parent.relative_to(root).parts
        except ValueError:
            return BoundaryReceipt(BoundaryStatus.DENIED, "target_escapes_protected_root")
        current = root
        for part in parts:
            current = current / part
            if current.is_symlink():
                return BoundaryReceipt(BoundaryStatus.DENIED, "parent_directory_invalid")
            if not current.exists():
                try:
                    current.mkdir(mode=0o700)
                    current.chmod(0o700)
                except OSError:
                    return BoundaryReceipt(BoundaryStatus.DENIED, "parent_directory_invalid")
            check = self._check_existing_directory(
                current, runner_uid, "parent_directory_invalid"
            )
            if check is not None:
                return check
        return None

    def _write_new_file(
        self, target: Path, payload: bytes, runner_uid: int
    ) -> BoundaryReceipt:
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        digest = hashlib.sha256(payload).hexdigest()
        try:
            fd = os.open(target, flags, 0o600)
            os.fchmod(fd, 0o600)
            with os.fdopen(fd, "wb") as handle:
                handle.write(payload)
            info = target.lstat()
        except OSError:
            return BoundaryReceipt(BoundaryStatus.DENIED, "write_failed")
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
            return BoundaryReceipt(BoundaryStatus.DENIED, "written_path_not_regular_file")
        if info.st_uid != runner_uid or info.st_mode & 0o777 != 0o600:
            return BoundaryReceipt(BoundaryStatus.DENIED, "written_file_permission_invalid")
        return BoundaryReceipt(
            BoundaryStatus.WRITTEN, "written", target, digest, len(payload)
        )


def write_protected_file(
    config: RunnerBoundaryConfig,
    relative_path: str | Path,
    payload: bytes,
) -> BoundaryReceipt:
    """Write a new protected file through the runner boundary."""

    return RunnerBoundary(config).write_file(relative_path, payload)
