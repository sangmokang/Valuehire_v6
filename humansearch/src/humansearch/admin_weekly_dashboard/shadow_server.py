"""Loopback-only HTTP preview for the PII-free weekly dashboard contract."""

from __future__ import annotations

import argparse
import json
from collections.abc import Mapping, Sequence
from datetime import date, datetime, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import TypedDict, cast
from zoneinfo import ZoneInfo

from .contracts import (
    MetricCatalogPayload,
    MetricContract,
    MetricEvent,
    MetricGroupPayload,
    MetricStatus,
    SnapshotPayload,
    SourceFailureReason,
    SourceState,
    load_metric_contract,
)
from .snapshot import build_weekly_snapshot
from .weekly_window import weekly_window

KST = ZoneInfo("Asia/Seoul")
SAFE_HOSTS = {"127.0.0.1", "localhost"}
CONTENT_SECURITY_POLICY = (
    "default-src 'self'; "
    "script-src 'self'; "
    "style-src 'self'; "
    "connect-src 'self'; "
    "img-src 'self' data:; "
    "object-src 'none'; "
    "base-uri 'none'; "
    "frame-ancestors 'none'"
)


class HistoryWeekPayload(TypedDict):
    meeting_iso_week: str
    event_start_kst: str
    event_end_exclusive_kst: str
    event_end_inclusive_date_kst: str
    status: str
    reason: str | None
    snapshot: SnapshotPayload | None


class DashboardPayload(TypedDict):
    mode: str
    metric_contract_version: str
    metric_groups: list[MetricGroupPayload]
    metric_catalog: list[MetricCatalogPayload]
    weeks: list[HistoryWeekPayload]
    external_effects: dict[str, str]


def build_shadow_dashboard(metric_contract: MetricContract) -> DashboardPayload:
    """Build a deterministic one-week shadow and eleven explicit history gaps."""

    meeting_date = date(2026, 8, 17)
    current_snapshot = build_weekly_snapshot(
        meeting_date_kst=meeting_date.isoformat(),
        events=_shadow_events(),
        source_states={
            "mail_events": SourceState(
                status=MetricStatus.NOT_RUN,
                reason=SourceFailureReason.RETENTION_POLICY_MISSING,
            ),
            "sourcing_runs": SourceState(status=MetricStatus.PASS),
            "candidate_discoveries": SourceState(status=MetricStatus.PASS),
        },
        metric_contract=metric_contract,
    )
    weeks: list[HistoryWeekPayload] = []
    for weeks_ago in range(11, 0, -1):
        historical_window = weekly_window((meeting_date - timedelta(weeks=weeks_ago)).isoformat())
        weeks.append(
            {
                "meeting_iso_week": historical_window.meeting_iso_week,
                "event_start_kst": historical_window.event_start_kst,
                "event_end_exclusive_kst": historical_window.event_end_exclusive_kst,
                "event_end_inclusive_date_kst": _inclusive_end_date(
                    historical_window.event_end_exclusive_kst
                ),
                "status": MetricStatus.NOT_RUN.value,
                "reason": SourceFailureReason.HISTORY_NOT_COLLECTED.value,
                "snapshot": None,
            }
        )
    weeks.append(
        {
            "meeting_iso_week": current_snapshot.window.meeting_iso_week,
            "event_start_kst": current_snapshot.window.event_start_kst,
            "event_end_exclusive_kst": current_snapshot.window.event_end_exclusive_kst,
            "event_end_inclusive_date_kst": _inclusive_end_date(
                current_snapshot.window.event_end_exclusive_kst
            ),
            "status": MetricStatus.PASS.value,
            "reason": None,
            "snapshot": current_snapshot.to_api_dict(),
        }
    )
    return {
        "mode": "LOCAL_SHADOW",
        "metric_contract_version": metric_contract.version,
        "metric_groups": metric_contract.group_catalog(),
        "metric_catalog": metric_contract.metric_catalog(),
        "weeks": weeks,
        "external_effects": dict(sorted(metric_contract.external_effects.items())),
    }


def _shadow_events() -> list[MetricEvent]:
    occurred_at = datetime(2026, 8, 12, 12, 0, tzinfo=KST)
    events = [
        MetricEvent(
            source_collection="sourcing_runs",
            source_system="aisearch",
            source_primary_key=f"run-{index}",
            event_type="sourcing_run",
            occurred_at=occurred_at,
        )
        for index in range(1, 3)
    ]
    discovery_rows = [
        ("discovery-1", "position-1", "a" * 64),
        ("discovery-2", "position-1", "a" * 64),
        ("discovery-3", "position-2", "b" * 64),
        ("discovery-4", "position-2", "c" * 64),
        ("discovery-5", "position-3", "d" * 64),
    ]
    events.extend(
        MetricEvent(
            source_collection="candidate_discoveries",
            source_system="aisearch",
            source_primary_key=primary_key,
            event_type="candidate_discovery",
            occurred_at=occurred_at,
            position_source_id=position_id,
            candidate_source_key_hmac=candidate_key,
        )
        for primary_key, position_id, candidate_key in discovery_rows
    )
    return events


def _inclusive_end_date(event_end_exclusive_kst: str) -> str:
    return (datetime.fromisoformat(event_end_exclusive_kst).date() - timedelta(days=1)).isoformat()


class ShadowServer(ThreadingHTTPServer):
    """HTTP server carrying only prevalidated assets and a dashboard payload."""

    daemon_threads = True

    dashboard_payload: DashboardPayload
    asset_routes: Mapping[str, tuple[str, bytes]]


def create_shadow_server(
    *,
    assets: Path,
    contract_path: Path,
    host: str,
    port: int,
) -> ShadowServer:
    """Validate all local inputs before opening a loopback socket."""

    if host not in SAFE_HOSTS:
        raise ValueError("shadow server host must be loopback-only")
    if not 0 <= port <= 65535:
        raise ValueError("port must be between 0 and 65535")
    normalized_host = "127.0.0.1"
    routes = _load_assets(assets)
    contract = load_metric_contract(contract_path)
    dashboard_payload = build_shadow_dashboard(contract)
    server = ShadowServer((normalized_host, port), _ShadowRequestHandler)
    server.dashboard_payload = dashboard_payload
    server.asset_routes = routes
    return server


def _load_assets(assets: Path) -> Mapping[str, tuple[str, bytes]]:
    asset_root = assets.resolve(strict=True)
    if not asset_root.is_dir():
        raise NotADirectoryError("shadow asset root must be a directory")
    route_files = {
        "/": ("text/html; charset=utf-8", "index.html"),
        "/styles.css": ("text/css; charset=utf-8", "styles.css"),
        "/app.js": ("text/javascript; charset=utf-8", "app.js"),
    }
    loaded: dict[str, tuple[str, bytes]] = {}
    for route, (content_type, filename) in route_files.items():
        path = asset_root / filename
        if path.is_symlink():
            raise ValueError(f"shadow asset must not be a symlink: {filename}")
        if not path.is_file():
            raise FileNotFoundError(f"required shadow asset missing: {filename}")
        loaded[route] = (content_type, path.read_bytes())
    return loaded


class _ShadowRequestHandler(BaseHTTPRequestHandler):
    server: ShadowServer

    def version_string(self) -> str:
        return "ValueHireShadow/1"

    def do_GET(self) -> None:
        if self.path == "/api/dashboard":
            self._send_json(200, self.server.dashboard_payload)
            return
        if self.path == "/healthz":
            self._send_json(200, {"status": "PASS", "mode": "LOCAL_SHADOW"})
            return
        asset = self.server.asset_routes.get(self.path)
        if asset is not None:
            content_type, body = asset
            self._send(200, content_type, body)
            return
        self._send_json(404, {"status": "FAIL", "reason": "route_not_found"})

    def do_HEAD(self) -> None:
        self._send_json(
            405,
            {"status": "FAIL", "reason": "method_not_allowed"},
            write_body=False,
        )

    def do_POST(self) -> None:
        self._method_not_allowed()

    def do_PUT(self) -> None:
        self._method_not_allowed()

    def do_PATCH(self) -> None:
        self._method_not_allowed()

    def do_DELETE(self) -> None:
        self._method_not_allowed()

    def do_OPTIONS(self) -> None:
        self._method_not_allowed()

    def log_message(self, format: str, *args: object) -> None:
        del format, args

    def _method_not_allowed(self) -> None:
        self._send_json(405, {"status": "FAIL", "reason": "method_not_allowed"})

    def _send_json(
        self,
        status: int,
        payload: object,
        *,
        write_body: bool = True,
    ) -> None:
        body = json.dumps(
            payload,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        self._send(status, "application/json; charset=utf-8", body, write_body=write_body)

    def _send(
        self,
        status: int,
        content_type: str,
        body: bytes,
        *,
        write_body: bool = True,
    ) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", CONTENT_SECURITY_POLICY)
        self.end_headers()
        if write_body:
            self.wfile.write(body)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the local-only admin shadow dashboard")
    parser.add_argument("--assets", type=Path, required=True)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    arguments = parser.parse_args(argv)
    server = create_shadow_server(
        assets=arguments.assets,
        contract_path=arguments.contract,
        host=cast(str, arguments.host),
        port=cast(int, arguments.port),
    )
    bound_host, bound_port = cast(tuple[str, int], server.server_address)
    print(f"LOCAL SHADOW · 운영 아님 · http://{bound_host}:{bound_port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
