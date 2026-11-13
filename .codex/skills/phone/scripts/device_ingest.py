#!/usr/bin/env python3
"""Copy new Galaxy call recordings to the verified HDD and checkpoint them."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import plistlib
import re
import shlex
import subprocess
import time
import unicodedata
import uuid
from pathlib import Path
from typing import Any


DEFAULT_SETTINGS = Path.home() / "Library/Application Support/Valuehire/phone-ingest.json"
MAX_AUDIO_BYTES = 90_000_000


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def canonical_name(name: str) -> str:
    return unicodedata.normalize("NFC", name)


def recording_sort_key(record: dict[str, Any]) -> tuple[str, str]:
    match = re.search(r"_(\d{6})_(\d{6})\.m4a$", record.get("filename", ""), re.IGNORECASE)
    return ((match.group(1) + match.group(2)) if match else "999999999999", record.get("filename", ""))


def _run(args: list[str], timeout: int = 60) -> str:
    result = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    if result.returncode:
        detail = (result.stderr or result.stdout).strip()[:500]
        raise RuntimeError(f"COMMAND_FAILED:{Path(args[0]).name}:{detail}")
    return result.stdout.strip()


class Ingestor:
    def __init__(self, settings: dict[str, Any], *, runner=_run, now=time.time):
        self.settings = settings
        self.runner = runner
        self.now = now
        self.adb = str(settings.get("adb", "/opt/homebrew/bin/adb"))
        self.source = str(settings["android_call_folder"])
        self.hdd_root = Path(settings["hdd_call_folder"])
        self.state_root = Path(settings["state_folder"])
        self.expected_volume_uuid = str(settings["hdd_volume_uuid"]).upper()
        self.min_stable_age = int(settings.get("min_stable_age_seconds", 120))
        self.max_bytes = int(settings.get("max_file_bytes", MAX_AUDIO_BYTES))
        self.excluded_names = tuple(
            canonical_name(str(x)).casefold()
            for x in settings.get("excluded_contact_name_patterns", [])
        )

    def _call(self, *args: str, timeout: int = 60) -> str:
        return self.runner([self.adb, *args], timeout=timeout)

    def _device(self) -> str | None:
        raw = self._call("devices")
        devices = [line.split() for line in raw.splitlines()[1:] if line.strip()]
        authorized = [line for line in devices if len(line) >= 2 and line[1] == "device"]
        if not authorized:
            if any(len(line) >= 2 and line[1] == "unauthorized" for line in devices):
                raise RuntimeError("ANDROID_DEVICE_UNAUTHORIZED")
            return None
        if len(authorized) != 1:
            raise RuntimeError("ANDROID_DEVICE_COUNT_NOT_ONE")
        props = self._call("-s", authorized[0][0], "shell", "getprop", "ro.product.manufacturer")
        if props.casefold() != "samsung":
            raise RuntimeError("CONNECTED_DEVICE_NOT_SAMSUNG")
        return authorized[0][0]

    def _verify_hdd(self) -> None:
        if not self.hdd_root.is_dir() or self.hdd_root.is_symlink():
            raise RuntimeError("HDD_CALL_FOLDER_MISSING_OR_SYMLINK")
        mount = self.hdd_root
        while mount != mount.parent and not mount.is_mount():
            mount = mount.parent
        if not mount.is_mount():
            raise RuntimeError("HDD_VOLUME_NOT_MOUNTED")
        raw = subprocess.check_output(["diskutil", "info", "-plist", str(mount)])
        volume = plistlib.loads(raw).get("VolumeUUID", "").upper()
        if not volume or volume != self.expected_volume_uuid:
            raise RuntimeError("HDD_VOLUME_UUID_MISMATCH")

    def _remote_files(self, serial: str) -> list[str]:
        raw = self._call(
            "-s", serial, "shell", "find", self.source,
            "-type", "f", "-name", "*.m4a", timeout=120,
        )
        files = []
        prefix = self.source.rstrip("/") + "/"
        for remote in raw.splitlines():
            remote = remote.strip()
            if not remote:
                continue
            if not remote.startswith(prefix) or Path(remote).name != remote.rsplit("/", 1)[-1]:
                raise RuntimeError("REMOTE_PATH_OUTSIDE_CONFIGURED_CALL_FOLDER")
            if "\n" in remote or "\r" in remote or not remote.casefold().endswith(".m4a"):
                raise RuntimeError("UNSUPPORTED_REMOTE_FILENAME")
            files.append(remote)
        return sorted(set(files), key=lambda x: canonical_name(Path(x).name).casefold())

    def _remote_stats(self, serial: str, remote: str) -> tuple[int, int]:
        command = f"stat -c '%s|%Y' -- {shlex.quote(remote)}"
        raw = self._call("-s", serial, "shell", command)
        match = re.fullmatch(r"(\d+)\|(\d+)", raw)
        if not match:
            raise RuntimeError("REMOTE_STAT_INVALID")
        return int(match.group(1)), int(match.group(2))

    def _remote_hash(self, serial: str, remote: str) -> str:
        command = f"sha256sum {shlex.quote(remote)}"
        raw = self._call("-s", serial, "shell", command, timeout=120)
        digest = raw.split()[0].lower() if raw else ""
        if not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise RuntimeError("REMOTE_SHA256_INVALID")
        return digest

    def _state(self) -> dict[str, Any]:
        path = self.state_root / "ingest-state.json"
        if not path.exists():
            return {"version": 1, "records": {}}
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("version") != 1 or not isinstance(data.get("records"), dict):
            raise RuntimeError("INGEST_STATE_INVALID")
        return data

    def _write_json(self, path: Path, data: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        tmp = path.with_name(path.name + f".{uuid.uuid4().hex}.tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        os.chmod(tmp, 0o600)
        os.replace(tmp, path)

    def sync(self, *, dry_run: bool = False) -> dict[str, Any]:
        self.state_root.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(self.state_root, 0o700)
        serial = self._device()
        if serial is None:
            return {"status": "DEVICE_NOT_CONNECTED", "copied": 0, "queued": 0, "skipped": 0}
        self._verify_hdd()
        files = self._remote_files(serial)
        state = self._state()
        records: dict[str, Any] = state["records"]
        result = {"status": "SYNCED", "copied": 0, "queued": 0, "skipped": 0, "conflicts": 0}
        queue_path = self.state_root / "work-queue.json"
        queue_data = json.loads(queue_path.read_text(encoding="utf-8")) if queue_path.exists() else {"version": 1, "records": []}
        if queue_data.get("version") != 1 or not isinstance(queue_data.get("records"), list):
            raise RuntimeError("WORK_QUEUE_INVALID")
        queue_by_hash = {r.get("source_sha256"): r for r in queue_data["records"] if r.get("source_sha256")}
        staging = self.hdd_root / ".phone-ingest-staging"
        if not dry_run:
            staging.mkdir(mode=0o700, exist_ok=True)

        for remote in files:
            filename = canonical_name(Path(remote).name)
            key = hashlib.sha256(remote.encode("utf-8")).hexdigest()
            if any(pattern in filename.casefold() for pattern in self.excluded_names):
                previous = records.get(key, {})
                if previous.get("status") != "SKIPPED_EXCLUDED_CONTACT":
                    records[key] = {"filename": filename, "status": "SKIPPED_EXCLUDED_CONTACT", "updated_at": dt.datetime.now(dt.timezone.utc).isoformat()}
                result["skipped"] += 1
                continue
            size, mtime = self._remote_stats(serial, remote)
            if size <= 0 or size > self.max_bytes:
                records[key] = {"filename": filename, "status": "REVIEW_FILE_SIZE", "bytes": size, "updated_at": dt.datetime.now(dt.timezone.utc).isoformat()}
                result["skipped"] += 1
                continue
            if self.now() - mtime < self.min_stable_age:
                records[key] = {"filename": filename, "status": "WAITING_FILE_STABILITY", "bytes": size, "updated_at": dt.datetime.now(dt.timezone.utc).isoformat()}
                result["skipped"] += 1
                continue
            digest = self._remote_hash(serial, remote)
            destination = self.hdd_root / filename
            previous = records.get(key, {})
            if destination.exists():
                if destination.is_symlink() or not destination.is_file():
                    raise RuntimeError("DESTINATION_NOT_REGULAR_FILE")
                if sha256_file(destination) != digest:
                    records[key] = {"filename": filename, "source_sha256": digest, "status": "CONFLICT_SAME_FILENAME_DIFFERENT_HASH", "updated_at": dt.datetime.now(dt.timezone.utc).isoformat()}
                    result["conflicts"] += 1
                    continue
                if previous.get("source_sha256") != digest or previous.get("status") != "COPIED_PENDING_TRANSCRIPTION":
                    records[key] = {"filename": filename, "source_sha256": digest, "destination": str(destination), "status": "COPIED_PENDING_TRANSCRIPTION", "updated_at": dt.datetime.now(dt.timezone.utc).isoformat()}
                if digest not in queue_by_hash:
                    queue_record = {"filename": filename, "path": str(destination), "source_sha256": digest, "status": "COPIED_PENDING_TRANSCRIPTION"}
                    queue_data["records"].append(queue_record)
                    queue_by_hash[digest] = queue_record
                    result["queued"] += 1
                continue
            if dry_run:
                result["copied"] += 1
                continue
            before = (size, mtime)
            temp = staging / f".{uuid.uuid4().hex}.partial"
            try:
                self._call("-s", serial, "pull", remote, str(temp), timeout=max(120, size // 100_000))
                after = self._remote_stats(serial, remote)
                after_hash = self._remote_hash(serial, remote)
                if before != after or digest != after_hash:
                    raise RuntimeError("SOURCE_CHANGED_DURING_COPY")
                if not temp.is_file() or temp.stat().st_size != size or sha256_file(temp) != digest:
                    raise RuntimeError("COPIED_FILE_HASH_MISMATCH")
                os.chmod(temp, 0o600)
                os.replace(temp, destination)
            finally:
                temp.unlink(missing_ok=True)
            records[key] = {"filename": filename, "source_sha256": digest, "destination": str(destination), "status": "COPIED_PENDING_TRANSCRIPTION", "bytes": size, "updated_at": dt.datetime.now(dt.timezone.utc).isoformat()}
            queue_record = {"filename": filename, "path": str(destination), "source_sha256": digest, "status": "COPIED_PENDING_TRANSCRIPTION"}
            queue_data["records"].append(queue_record)
            queue_by_hash[digest] = queue_record
            result["copied"] += 1
            result["queued"] += 1

        if not dry_run:
            queue_data["records"].sort(key=recording_sort_key)
            state["updated_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
            self._write_json(self.state_root / "ingest-state.json", state)
            queue_data["updated_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
            self._write_json(queue_path, queue_data)
        return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--settings", type=Path, default=DEFAULT_SETTINGS)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        settings = json.loads(args.settings.read_text(encoding="utf-8"))
        result = Ingestor(settings).sync(dry_run=args.dry_run)
    except Exception as exc:
        print(json.dumps({"status": "ERROR", "error": str(exc)[:300]}, ensure_ascii=False))
        return 1
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
