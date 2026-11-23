"""Render closed reporting periods using a private source snapshot for each closing date."""
import argparse
import hashlib
import json
import os
from datetime import date, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
from report import KINDS, period, report


def run(source, output, start, today):
    day = start
    missing = []
    while day < today:
        following = day + timedelta(days=1)
        closing = [kind for kind in KINDS if period(day, kind) != period(following, kind)]
        day_key = day.isoformat()
        snapshot = source / day_key
        if closing:
            files = [snapshot / f for f in ("events.csv", "coverage.json")]
            if not all(p.is_file() for p in files) or json.loads(files[1].read_text()).get("verified_through") != day_key:
                missing.append(day_key)
            else:
                digest = hashlib.sha256()
                for path in [*files, Path(__file__).with_name("report.py")]:
                    digest.update(hashlib.sha256(path.read_bytes()).digest())
                version = digest.hexdigest()
                for kind in closing:
                    folder = output / kind / period(day, kind)
                    folder.mkdir(parents=True, exist_ok=True)
                    target = folder / version
                    if not target.is_dir():
                        with TemporaryDirectory(dir=folder) as tmp:
                            staging = Path(tmp) / "bundle"
                            report(snapshot, staging, day)
                            staging.rename(target)
                    print(kind, day_key, target)
        day = following
    if missing:
        raise SystemExit("Source snapshots required: " + ", ".join(missing))


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("source", type=Path)
    p.add_argument("output", type=Path)
    p.add_argument("--start", required=True, type=date.fromisoformat)
    p.add_argument("--today", type=date.fromisoformat)
    args = p.parse_args()
    from datetime import datetime, timezone
    os.umask(0o077)
    run(args.source, args.output, args.start, args.today or datetime.now(timezone(timedelta(hours=9))).date())
