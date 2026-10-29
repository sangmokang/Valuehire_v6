"""Local PostgreSQL read adapter for the existing administrator app's RPC contract."""

import argparse
import hmac
import json
import os
import subprocess
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

parser = argparse.ArgumentParser()
parser.add_argument("--dsn", required=True)
parser.add_argument("--port", type=int, required=True)
args = parser.parse_args()
credential = os.environ["SUPABASE_SERVICE_ROLE_KEY"]


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *values: object) -> None:
        # Request bodies and paths contain PII; application logs deliberately omit them.
        return

    def do_POST(self) -> None:
        if self.path != "/rest/v1/rpc/admin_ai_search_read":
            self.send_error(404)
            return
        if not hmac.compare_digest(self.headers.get("authorization", ""), "Bearer " + credential):
            self.send_error(403)
            return
        try:
            size = int(self.headers.get("content-length", "0"))
            if not 0 < size < 16384:
                raise ValueError("request size")
            payload = json.loads(self.rfile.read(size))
            result = subprocess.run(["psql", args.dsn, "-XAtq", "-v", "ON_ERROR_STOP=1",
                "--set=action=" + payload["p_action"], "--set=args=" + json.dumps(payload["p_args"])],
                input="SET ROLE service_role; SELECT public.admin_ai_search_read(:'action',:'args'::jsonb);",
                text=True, capture_output=True, timeout=30)
            if result.returncode:
                self.send_error(503, "Database read failed")
                return
            output = result.stdout.strip().encode()
            json.loads(output)
        except (ValueError, KeyError, TypeError, subprocess.TimeoutExpired):
            self.send_error(400, "Invalid request or database timeout")
            return
        self.send_response(200)
        self.send_header("content-type", "application/json")
        self.send_header("cache-control", "private, no-store")
        self.send_header("content-length", str(len(output)))
        self.end_headers()
        self.wfile.write(output)


ThreadingHTTPServer(("127.0.0.1", args.port), Handler).serve_forever()
