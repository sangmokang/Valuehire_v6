#!/usr/bin/env python3
"""launchd wrapper: serialize scans, keep bounded diagnostics, notify on transitions."""
from __future__ import annotations

import fcntl
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


SCRIPT = Path(__file__).with_name("device_ingest.py")
SETTINGS = Path.home() / "Library/Application Support/Valuehire/phone-ingest.json"
STATE = Path.home() / "Library/Application Support/Valuehire/PhoneIngest"
LOCK = STATE / "runner.lock"
HISTORY = STATE / "run-history.jsonl"
STATUS = STATE / "last-run.json"


def atomic_json(path: Path, data: dict) -> None:
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.chmod(tmp, 0o600)
    os.replace(tmp, path)


def notify(message: str) -> None:
    escaped = message.replace("\\", "\\\\").replace('"', '\\"')
    subprocess.run(
        ["/usr/bin/osascript", "-e", f'display notification "{escaped}" with title "Phone"'],
        capture_output=True, text=True, timeout=10, check=False,
    )


def append_bounded(line: str) -> None:
    previous = HISTORY.read_text(encoding="utf-8").splitlines() if HISTORY.exists() else []
    previous.append(line)
    HISTORY.write_text("\n".join(previous[-500:]) + "\n", encoding="utf-8")
    os.chmod(HISTORY, 0o600)


def main() -> int:
    STATE.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(STATE, 0o700)
    with LOCK.open("a+") as lock:
        os.chmod(LOCK, 0o600)
        try:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return 0
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--settings", str(SETTINGS)],
            capture_output=True, text=True, timeout=900, check=False,
        )
        try:
            outcome = json.loads(result.stdout.strip().splitlines()[-1])
        except (IndexError, json.JSONDecodeError):
            outcome = {"status": "ERROR", "error": (result.stderr or result.stdout or "NO_RESULT")[-500:]}
        status = {
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "exit_code": result.returncode,
            **outcome,
        }
        previous = json.loads(STATUS.read_text(encoding="utf-8")) if STATUS.exists() else {}
        atomic_json(STATUS, status)
        append_bounded(json.dumps(status, ensure_ascii=False))
        if outcome.get("status") == "ERROR":
            if previous.get("status") != "ERROR" or previous.get("error") != outcome.get("error"):
                notify("통화 파일 자동 수집 오류가 발생했습니다. 로그의 상태를 확인합니다.")
        elif outcome.get("copied", 0):
            notify(f"새 통화 녹음 {outcome['copied']}개를 HDD에 복사했고 해시를 확인했습니다.")
        elif previous.get("status") == "ERROR":
            notify("통화 파일 자동 수집이 다시 정상 동작합니다.")
        return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
