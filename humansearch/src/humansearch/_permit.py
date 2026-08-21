"""Fail-closed validation and one-time consumption for DOM-read permits."""

import hashlib
import json
import os
import re
import stat
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit
from uuid import UUID

_FIELDS = frozenset(
    {
        "version",
        "lease_id",
        "channel",
        "diagnostic_host",
        "diagnostic_port",
        "allowed_origin",
        "target_id_sha256",
        "expires_at",
    }
)
_MAX_PERMIT_BYTES = 65_536
_SHA256_HEX = re.compile(r"[0-9a-f]{64}", re.ASCII)
_UTC_RFC3339 = re.compile(
    r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|\+00:00)",
    re.ASCII,
)


class PermitError(RuntimeError):
    """Raised when a permit cannot authorize exactly one DOM read."""


@dataclass(frozen=True, slots=True)
class ObservationPermit:
    """Validated permit data with the raw lease identifier already discarded."""

    path: Path
    lease_key: str
    channel: str
    diagnostic_host: str
    diagnostic_port: int
    allowed_origin: str
    target_id_sha256: str
    expires_at: datetime


def load_observation_permit(
    permit_file: Path | None,
    *,
    repository_root: Path,
    channel: str,
    diagnostic_host: str,
    diagnostic_port: int,
) -> ObservationPermit:
    """Load a strict external permit and validate its pre-target bindings."""

    if permit_file is None:
        raise PermitError("observation permit is required")
    permit_path = Path(os.path.abspath(os.fspath(permit_file)))
    repository = repository_root.resolve()
    if _is_within(permit_path, repository):
        raise PermitError("observation permit path is not external")
    try:
        metadata = permit_path.lstat()
        resolved_path = permit_path.resolve(strict=True)
    except OSError as exc:
        raise PermitError("observation permit is unavailable") from exc
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        raise PermitError("observation permit must be a regular file")
    if _is_within(resolved_path, repository):
        raise PermitError("observation permit path is not external")

    payload = _read_payload(permit_path)
    if set(payload) != _FIELDS:
        raise PermitError("observation permit fields are invalid")
    version = payload.get("version")
    lease_id = payload.get("lease_id")
    permit_channel = payload.get("channel")
    permit_host = payload.get("diagnostic_host")
    permit_port = payload.get("diagnostic_port")
    allowed_origin = payload.get("allowed_origin")
    target_proof = payload.get("target_id_sha256")
    expires_at = payload.get("expires_at")
    if type(version) is not int or version != 1:
        raise PermitError("observation permit version is invalid")
    if not isinstance(lease_id, str) or not _canonical_uuid(lease_id):
        raise PermitError("observation permit lease is invalid")
    if not isinstance(permit_channel, str) or permit_channel != channel:
        raise PermitError("observation permit channel binding is invalid")
    if not isinstance(permit_host, str) or permit_host != diagnostic_host:
        raise PermitError("observation permit host binding is invalid")
    if type(permit_port) is not int or permit_port != diagnostic_port:
        raise PermitError("observation permit port binding is invalid")
    if not isinstance(allowed_origin, str) or not _valid_origin(allowed_origin):
        raise PermitError("observation permit origin is invalid")
    if not isinstance(target_proof, str) or _SHA256_HEX.fullmatch(target_proof) is None:
        raise PermitError("observation permit target proof is invalid")
    parsed_expiry = _parse_expiry(expires_at)
    if parsed_expiry <= _utc_now():
        raise PermitError("observation permit is expired")
    return ObservationPermit(
        path=permit_path,
        lease_key=hashlib.sha256(lease_id.encode("utf-8")).hexdigest(),
        channel=permit_channel,
        diagnostic_host=permit_host,
        diagnostic_port=permit_port,
        allowed_origin=allowed_origin,
        target_id_sha256=target_proof,
        expires_at=parsed_expiry,
    )


def bind_and_consume_permit(
    permit: ObservationPermit,
    *,
    allowed_origin: str,
    target_id_sha256: str,
) -> None:
    """Verify current target bindings and atomically consume the permit."""

    if permit.allowed_origin != allowed_origin:
        raise PermitError("observation permit origin binding is invalid")
    if permit.target_id_sha256 != target_id_sha256:
        raise PermitError("observation permit target binding is invalid")
    if permit.expires_at <= _utc_now():
        raise PermitError("observation permit is expired")
    sentinel = permit.path.parent / (
        f".humansearch-permit-{permit.lease_key}.consumed"
    )
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    flags |= getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(sentinel, flags, 0o600)
    except OSError as exc:
        raise PermitError("observation permit was already consumed") from exc
    try:
        os.fchmod(descriptor, 0o600)
        os.fsync(descriptor)
    except OSError as exc:
        raise PermitError("observation permit consumption failed") from exc
    finally:
        os.close(descriptor)


def _read_payload(path: Path) -> dict[str, Any]:
    flags = os.O_RDONLY
    flags |= getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise PermitError("observation permit is unavailable") from exc
    try:
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode):
            raise PermitError("observation permit must be a regular file")
        if metadata.st_uid != os.getuid():
            raise PermitError("observation permit owner is invalid")
        if stat.S_IMODE(metadata.st_mode) != 0o600:
            raise PermitError("observation permit mode is invalid")
        with os.fdopen(descriptor, "rb", closefd=False) as stream:
            raw = stream.read(_MAX_PERMIT_BYTES + 1)
    except OSError as exc:
        raise PermitError("observation permit could not be read") from exc
    finally:
        os.close(descriptor)
    if len(raw) > _MAX_PERMIT_BYTES:
        raise PermitError("observation permit is too large")
    try:
        decoded = raw.decode("utf-8")
        payload = json.loads(decoded, object_pairs_hook=_unique_object)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PermitError("observation permit JSON is invalid") from exc
    if not isinstance(payload, dict):
        raise PermitError("observation permit JSON is invalid")
    return payload


def _unique_object(pairs: Iterable[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise PermitError("observation permit fields are invalid")
        result[key] = value
    return result


def _canonical_uuid(value: str) -> bool:
    try:
        parsed = UUID(value)
    except (ValueError, AttributeError):
        return False
    return str(parsed) == value


def _parse_expiry(value: object) -> datetime:
    if not isinstance(value, str) or _UTC_RFC3339.fullmatch(value) is None:
        raise PermitError("observation permit expiry is invalid")
    normalized = f"{value[:-1]}+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise PermitError("observation permit expiry is invalid") from exc
    if parsed.utcoffset() != timedelta(0):
        raise PermitError("observation permit expiry is not UTC")
    return parsed.astimezone(UTC)


def _valid_origin(value: str) -> bool:
    parsed = urlsplit(value)
    return (
        parsed.scheme == "https"
        and bool(parsed.netloc)
        and not parsed.path
        and not parsed.query
        and not parsed.fragment
        and parsed.username is None
        and parsed.password is None
    )


def _is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _utc_now() -> datetime:
    return datetime.now(UTC)
