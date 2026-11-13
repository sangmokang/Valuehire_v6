import hashlib
import importlib.util
import plistlib
import shlex
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


MODULE = Path(__file__).with_name("device_ingest.py")
spec = importlib.util.spec_from_file_location("device_ingest", MODULE)
device_ingest = importlib.util.module_from_spec(spec)
spec.loader.exec_module(device_ingest)


class FakeGalaxy:
    serial = "fixture-device"

    def __init__(self, files):
        self.files = files
        self.pull_count = 0

    def __call__(self, args, timeout=60):
        args = args[1:]
        if args == ["devices"]:
            return "List of devices attached\nfixture-device device usb:1 product:fixture model:SM_A556S\n"
        if args[:3] == ["-s", self.serial, "shell"]:
            command = args[3:]
            if command == ["getprop", "ro.product.manufacturer"]:
                return "samsung"
            if command[:2] == ["find", "/storage/emulated/0/Recordings/Call"]:
                return "\n".join(self.files) + "\n"
            if len(command) == 1 and command[0].startswith("stat "):
                parts = shlex.split(command[0])
                remote = parts[-1]
                data, mtime = self.files[remote]
                return f"{len(data)}|{mtime}"
            if len(command) == 1 and command[0].startswith("sha256sum "):
                remote = shlex.split(command[0])[-1]
                return hashlib.sha256(self.files[remote][0]).hexdigest() + "  " + remote
        if args[:3] == ["-s", self.serial, "pull"]:
            remote, local = args[3:]
            Path(local).write_bytes(self.files[remote][0])
            self.pull_count += 1
            return "1 file pulled"
        raise AssertionError(f"unexpected adb command: {args}")


class MutatingGalaxy(FakeGalaxy):
    def __call__(self, args, timeout=60):
        if args[1:4] == ["-s", self.serial, "pull"]:
            remote, local = args[4:]
            Path(local).write_bytes(b"changed while pulling")
            self.files[remote] = (b"changed while pulling", self.files[remote][1])
            self.pull_count += 1
            return "1 file pulled"
        return super().__call__(args, timeout)


class DeviceIngestTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.mount = self.base / "hdd"
        self.call_folder = self.mount / "Recordings" / "Call"
        self.call_folder.mkdir(parents=True)
        self.state_folder = self.base / "state"
        self.settings = {
            "android_call_folder": "/storage/emulated/0/Recordings/Call",
            "hdd_call_folder": str(self.call_folder),
            "state_folder": str(self.state_folder),
            "hdd_volume_uuid": "FIXTURE-VOLUME",
            "excluded_contact_name_patterns": ["fixtureprivate"],
            "min_stable_age_seconds": 120,
        }
        self.now = 1_800_000_000
        self.files = {
            "/storage/emulated/0/Recordings/Call/통화 녹음 FixtureCandidate_261110_091000.m4a": (b"candidate audio", self.now - 300),
            "/storage/emulated/0/Recordings/Call/통화 녹음 FixturePrivate_261110_091500.m4a": (b"private audio", self.now - 300),
            "/storage/emulated/0/Recordings/Call/통화 녹음 01012345678_261110_092000.m4a": (b"still writing", self.now - 5),
        }
        self.galaxy = FakeGalaxy(self.files)
        self.runner = self.galaxy
        self.mount_patch = patch.object(Path, "is_mount", lambda p: p == self.mount)
        self.mount_patch.start()
        self.addCleanup(self.mount_patch.stop)
        self.disk_patch = patch.object(device_ingest.subprocess, "check_output", return_value=plistlib.dumps({"VolumeUUID": "FIXTURE-VOLUME"}))
        self.disk_patch.start()
        self.addCleanup(self.disk_patch.stop)

    def ingestor(self):
        return device_ingest.Ingestor(self.settings, runner=self.runner, now=lambda: self.now)

    def test_copies_only_stable_nonexcluded_recordings_and_verifies_hash(self):
        result = self.ingestor().sync()
        self.assertEqual(result, {"status": "SYNCED", "copied": 1, "queued": 1, "skipped": 2, "conflicts": 0})
        copied = self.call_folder / "통화 녹음 FixtureCandidate_261110_091000.m4a"
        self.assertEqual(copied.read_bytes(), b"candidate audio")
        self.assertEqual(copied.stat().st_mode & 0o777, 0o600)
        queue = __import__("json").loads((self.state_folder / "work-queue.json").read_text())
        self.assertEqual(queue["records"][0]["source_sha256"], hashlib.sha256(b"candidate audio").hexdigest())
        state = __import__("json").loads((self.state_folder / "ingest-state.json").read_text())
        statuses = {r["filename"]: r["status"] for r in state["records"].values()}
        self.assertEqual(statuses["통화 녹음 FixturePrivate_261110_091500.m4a"], "SKIPPED_EXCLUDED_CONTACT")
        self.assertEqual(statuses["통화 녹음 01012345678_261110_092000.m4a"], "WAITING_FILE_STABILITY")

    def test_repeated_scan_does_not_duplicate_files_or_queue_entries(self):
        self.ingestor().sync()
        second = self.ingestor().sync()
        self.assertEqual(second["copied"], 0)
        self.assertEqual(second["queued"], 0)
        queue = __import__("json").loads((self.state_folder / "work-queue.json").read_text())
        self.assertEqual(len(queue["records"]), 1)
        self.assertEqual(self.galaxy.pull_count, 1)

    def test_same_filename_with_different_hash_is_preserved_as_conflict(self):
        name = "통화 녹음 FixtureCandidate_261110_091000.m4a"
        (self.call_folder / name).write_bytes(b"older different file")
        result = self.ingestor().sync()
        self.assertEqual(result["conflicts"], 1)
        self.assertEqual((self.call_folder / name).read_bytes(), b"older different file")
        self.assertEqual(self.galaxy.pull_count, 0)

    def test_unmounted_or_wrong_hdd_volume_fails_closed(self):
        with patch.object(Path, "is_mount", return_value=False):
            with self.assertRaisesRegex(RuntimeError, "HDD_VOLUME_NOT_MOUNTED"):
                self.ingestor().sync()
        with patch.object(device_ingest.subprocess, "check_output", return_value=plistlib.dumps({"VolumeUUID": "OTHER"})):
            with self.assertRaisesRegex(RuntimeError, "HDD_VOLUME_UUID_MISMATCH"):
                self.ingestor().sync()

    def test_unauthorized_android_device_is_reported_without_copying(self):
        def unauthorized(args, timeout=60):
            return "List of devices attached\nfixture-device unauthorized usb:1\n"
        with self.assertRaisesRegex(RuntimeError, "ANDROID_DEVICE_UNAUTHORIZED"):
            device_ingest.Ingestor(self.settings, runner=unauthorized, now=lambda: self.now).sync()
        self.assertEqual(list(self.call_folder.glob("*.m4a")), [])

    def test_source_change_during_transfer_fails_without_publishing_partial_file(self):
        self.runner = MutatingGalaxy(self.files.copy())
        with self.assertRaisesRegex(RuntimeError, "SOURCE_CHANGED_DURING_COPY"):
            self.ingestor().sync()
        self.assertEqual(list(self.call_folder.glob("*.m4a")), [])
        self.assertEqual(list((self.call_folder / ".phone-ingest-staging").glob("*.partial")), [])


if __name__ == "__main__":
    unittest.main()
