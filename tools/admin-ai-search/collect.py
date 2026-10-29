"""Server job; use the existing Gmail registry via a GET-only bridge."""

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

from humansearch.admin_ai_search.collection import CollectionStore, collect_mailbox


class ExistingGmailReader:
    def __init__(self) -> None:
        self.retry_count = 0
        self.process = subprocess.Popen(
            ["node", str(Path(__file__).with_name("gmail-reader.mjs"))],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True,
        )

    def request(self, operation: str, args: dict[str, object]) -> Any:
        if self.process.stdin is None or self.process.stdout is None:
            raise RuntimeError("Gmail bridge pipes unavailable")
        self.process.stdin.write(json.dumps({"operation": operation, "args": args}) + "\n")
        self.process.stdin.flush()
        response = self.process.stdout.readline()
        if not response:
            raise RuntimeError("Gmail reader exited before response")
        result = json.loads(response)
        self.retry_count = result["retry_count"]
        if not result["ok"]:
            raise RuntimeError(result["error"])
        return result["value"]

    def close(self) -> None:
        if self.process.stdin is not None:
            self.process.stdin.close()
        self.process.wait(timeout=30)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--run-id")
    parser.add_argument("--include-sent", action="store_true")
    parser.add_argument("--refresh-since-start", action="store_true")
    args = parser.parse_args()
    reader = ExistingGmailReader()
    try:
        run = collect_mailbox(CollectionStore(args.database), reader, run_id=args.run_id,
                             include_sent=args.include_sent, refresh_since_start=args.refresh_since_start)
        # Counts only. No subjects, recipients, names or raw error text in logs.
        print(json.dumps({key: run[key] for key in (
            "id", "status", "union_count", "overlap_count", "new", "updated", "unchanged",
        )}))
        if run["status"] != "SUCCEEDED":
            raise SystemExit(2)
    finally:
        reader.close()
