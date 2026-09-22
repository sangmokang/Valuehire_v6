#!/usr/bin/env python3
"""Run the real gh query/paginator against loopback JSON, never GitHub."""
import http.server
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import threading
from urllib.parse import parse_qs, urlsplit


def run(checker, mode):
    real_gh = shutil.which("gh")
    if real_gh is None:
        print("NOT_RUN: gh executable missing")
        return 2
    success = {"name": "verify", "status": "completed", "conclusion": "success"}
    failure = dict(success, conclusion="failure")
    unrelated = dict(failure, name="deploy")
    cases = {
        "all_success": ([success, success], 0, "VERIFIED", 2),
        "mixed_failure": ([success, failure], 1, "UNVERIFIED", 2),
        "reversed_failure": ([failure, success], 1, "UNVERIFIED", 2),
        "irrelevant_failure": ([unrelated, success], 0, "VERIFIED", 1),
        "no_verify": ([unrelated], 1, "UNVERIFIED", 0),
        "page2_failure": ([success], 1, "UNVERIFIED", 2),
        "page2_error": ([success], 2, "NOT_RUN", None),
        "historical_failure": ([failure, success], 1, "UNVERIFIED", 2),
    }
    rows, expected_rc, verdict, count = cases[mode]
    requests = []

    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            query = parse_qs(urlsplit(self.path).query)
            requests.append(self.path)
            second = query.get("page") == ["2"]
            if second and mode == "page2_error":
                self.send_response(503)
                self.end_headers()
                self.wfile.write(b'{"message":"fixture page unavailable"}')
                return
            output = [failure] if second else rows
            if mode == "historical_failure" and query.get("filter") != ["all"]:
                output = [success]
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            if mode.startswith("page2_") and not second:
                link = f"http://127.0.0.1:{self.server.server_port}/check-runs?filter=all&page=2"
                self.send_header("Link", f'<{link}>; rel="next"')
            self.end_headers()
            self.wfile.write(json.dumps({"check_runs": output}).encode())

    server = http.server.HTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with tempfile.TemporaryDirectory(prefix="p23-query-") as directory:
            temp = Path(directory)
            bindir = temp / "bin"
            bindir.mkdir()
            git = bindir / "git"
            git.write_text('''#!/usr/bin/env python3
import sys
args = sys.argv[1:]
if args == ["rev-parse", "HEAD"]:
    print("a" * 40)
elif args == ["ls-remote", "origin", "refs/heads/task/mock"]:
    print("a" * 40 + "\\trefs/heads/task/mock")
elif args != ["status", "--porcelain"]:
    sys.exit(97)
''')
            gh = bindir / "gh"
            gh.write_text('''#!/usr/bin/env python3
import os
import sys
args = sys.argv[1:]
prefix = "repos/{owner}/{repo}/commits/" + "a" * 40 + "/check-runs"
endpoints = [i for i, value in enumerate(args) if value.split("?")[0] == prefix]
if not args or args[0] != "api" or len(endpoints) != 1:
    sys.exit(96)
i = endpoints[0]
args[i] = os.environ["FIXTURE_URL"] + args[i][len(prefix):]
os.execv(os.environ["FIXTURE_GH"], [os.environ["FIXTURE_GH"]] + args)
''')
            for executable in (git, gh):
                executable.chmod(0o700)
            env = os.environ.copy()
            for key in list(env):
                if key.startswith(("GH_", "GITHUB_", "GIT_")) or key.lower().endswith("proxy"):
                    env.pop(key)
            env.update({
                "PATH": str(bindir) + os.pathsep + os.environ["PATH"],
                "GH_TOKEN": "x",  # Non-secret placeholder for loopback requests only.
                "GH_CONFIG_DIR": str(temp / "gh-config"),
                "GH_HOST": "github.com",
                "GH_REPO": "fixture/fixture",
                "FIXTURE_GH": real_gh,
                "FIXTURE_URL": f"http://127.0.0.1:{server.server_port}/check-runs",
            })
            result = subprocess.run(
                ["bash", str(Path(checker).resolve()), "task/mock"],
                env=env, text=True, capture_output=True, timeout=20,
            )
        lines = result.stdout.splitlines()
        pages = 2 if mode.startswith("page2_") else 1
        verdict_seen = (any(line.startswith("NOT_RUN:") for line in lines) if verdict == "NOT_RUN"
                        else f"VERDICT: {verdict}" in lines)
        ok = (result.returncode == expected_rc and verdict_seen
              and len(requests) == pages)
        if count is not None:
            ok = ok and f"CI_RUN_COUNT: {count}" in lines
        print(f"{mode}: exit={result.returncode} expected={expected_rc} requests={len(requests)}/{pages}")
        print(result.stdout, end="")
        if not ok:
            print(result.stderr, end="")
        return 0 if ok else 1
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("NOT_RUN: expected checker path and fixture mode")
        sys.exit(2)
    sys.exit(run(sys.argv[1], sys.argv[2]))
