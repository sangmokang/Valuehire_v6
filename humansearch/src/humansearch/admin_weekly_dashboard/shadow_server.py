"""Loopback-only HTTP preview for the PII-free weekly dashboard contract."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections.abc import Mapping, Sequence
from datetime import date, datetime, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import TextIO, TypedDict, cast
from zoneinfo import ZoneInfo

from humansearch.admin_ai_search.evidence import (
    AiSearchPayload,
    EvidenceContract,
    build_ai_search_payload,
    load_evidence_contract,
)
from humansearch.admin_ai_search.gmail_sent_contacts import (
    GMAIL_EVIDENCE_ENVELOPE_VERSION,
    build_ai_search_payload_from_gmail_evidence,
)
from humansearch.admin_ai_search.gmail_source import (
    build_ai_search_payload_from_gmail_snapshot,
)
from humansearch.admin_ai_search.weekly_view import (
    WeeklyAiSearchIndexPayload,
    WeeklyAiSearchViewPayload,
    build_weekly_ai_search_index,
    build_weekly_ai_search_view,
)

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
    source_summary: DashboardSourceSummary
    external_effects: dict[str, str]


class DashboardSourceSummary(TypedDict):
    status: str
    query: str | None
    message_count: int | None
    included_message_count: int | None
    excluded_message_count: int | None
    pagination_exhausted: bool
    latest_received_at: str | None


def build_shadow_dashboard(
    metric_contract: MetricContract,
    ai_search_payload: AiSearchPayload,
    *,
    as_of_date: date | None = None,
) -> DashboardPayload:
    """Build twelve weekly snapshots from one exhaustive Gmail AI Search read."""

    batches = ai_search_payload["batches"]
    source_summary = _dashboard_source_summary(ai_search_payload)
    reference_date = as_of_date or datetime.now(tz=KST).date()
    meeting_date = _next_meeting_monday(reference_date)
    events = _ai_search_events(batches)
    source_states = {
        "mail_events": SourceState(
            status=MetricStatus.NOT_RUN,
            reason=SourceFailureReason.RETENTION_POLICY_MISSING,
        ),
        "sourcing_runs": SourceState(status=MetricStatus.PASS),
        "candidate_discoveries": SourceState(status=MetricStatus.PASS),
    }
    collection_complete = (
        source_summary["status"] == MetricStatus.PASS.value
        and source_summary["pagination_exhausted"]
    )
    weeks: list[HistoryWeekPayload] = []
    for weeks_ago in range(11, -1, -1):
        historical_window = weekly_window((meeting_date - timedelta(weeks=weeks_ago)).isoformat())
        snapshot = (
            build_weekly_snapshot(
                meeting_date_kst=historical_window.meeting_instance_date_kst,
                events=events,
                source_states=source_states,
                metric_contract=metric_contract,
            )
            if collection_complete
            else None
        )
        weeks.append(
            {
                "meeting_iso_week": historical_window.meeting_iso_week,
                "event_start_kst": historical_window.event_start_kst,
                "event_end_exclusive_kst": historical_window.event_end_exclusive_kst,
                "event_end_inclusive_date_kst": _inclusive_end_date(
                    historical_window.event_end_exclusive_kst
                ),
                "status": (
                    MetricStatus.PASS.value if snapshot is not None else MetricStatus.NOT_RUN.value
                ),
                "reason": None if snapshot is not None else "gmail_collection_incomplete",
                "snapshot": snapshot.to_api_dict() if snapshot is not None else None,
            }
        )
    return {
        "mode": "LOCAL_SHADOW",
        "metric_contract_version": metric_contract.version,
        "metric_groups": metric_contract.group_catalog(),
        "metric_catalog": metric_contract.metric_catalog(),
        "weeks": weeks,
        "source_summary": source_summary,
        "external_effects": dict(sorted(metric_contract.external_effects.items())),
    }


def _dashboard_source_summary(payload: AiSearchPayload) -> DashboardSourceSummary:
    collection = payload.get("gmail_collection")
    if not isinstance(collection, Mapping):
        return {
            "status": MetricStatus.NOT_RUN.value,
            "query": None,
            "message_count": None,
            "included_message_count": None,
            "excluded_message_count": None,
            "pagination_exhausted": False,
            "latest_received_at": None,
        }
    executed_at = [batch["executed_at"] for batch in payload["batches"]]
    return {
        "status": _optional_string_value(collection.get("status")) or MetricStatus.NOT_RUN.value,
        "query": _optional_string_value(collection.get("query")),
        "message_count": _optional_count(collection.get("message_count")),
        "included_message_count": _optional_count(collection.get("included_message_count")),
        "excluded_message_count": _optional_count(collection.get("excluded_message_count")),
        "pagination_exhausted": collection.get("pagination_exhausted") is True,
        "latest_received_at": max(executed_at) if executed_at else None,
    }


def _optional_string_value(value: object) -> str | None:
    return value if isinstance(value, str) and value else None


def _optional_count(value: object) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else None


def _next_meeting_monday(reference_date: date) -> date:
    return reference_date + timedelta(days=7 - reference_date.weekday())


def _ai_search_events(batches: Sequence[Mapping[str, object]]) -> list[MetricEvent]:
    events: list[MetricEvent] = []
    for batch in batches:
        batch_id = cast(str, batch["batch_id"])
        actor = cast(str, batch["actor"])
        occurred_at = datetime.fromisoformat(cast(str, batch["executed_at"]))
        if occurred_at.tzinfo is None or occurred_at.utcoffset() is None:
            raise ValueError("AI Search batch executed_at must be timezone-aware")
        company = cast(str, batch["company"])
        position = cast(str, batch["position"])
        position_key = _position_key(company, position)
        events.append(
            MetricEvent(
                source_collection="sourcing_runs",
                source_system=actor,
                source_primary_key=batch_id,
                event_type="sourcing_run",
                occurred_at=occurred_at,
            )
        )
        candidates = batch["candidates"]
        if not isinstance(candidates, list):
            raise TypeError("AI Search batch candidates must be a list")
        for index, candidate_value in enumerate(candidates):
            if not isinstance(candidate_value, Mapping):
                raise TypeError("AI Search candidate must be an object")
            candidate = cast(Mapping[str, object], candidate_value)
            events.append(
                MetricEvent(
                    source_collection="candidate_discoveries",
                    source_system=cast(str, candidate["source_channel"]),
                    source_primary_key=f"{batch_id}:{index}",
                    event_type="candidate_discovery",
                    occurred_at=occurred_at,
                    candidate_source_key_hmac=cast(str, candidate["canonical_key"]),
                )
            )
            if position_key is not None:
                events.append(
                    MetricEvent(
                        source_collection="candidate_discoveries",
                        source_system=cast(str, candidate["source_channel"]),
                        source_primary_key=f"{batch_id}:position:{index}",
                        event_type="candidate_discovery_known_position",
                        occurred_at=occurred_at,
                        position_source_id=position_key,
                    )
                )
    return events


def _position_key(company: str, position: str) -> str | None:
    if company.startswith("NOT_RUN:") or position.startswith("NOT_RUN:"):
        return None
    return hashlib.sha256(f"{company}\0{position}".encode()).hexdigest()


def _inclusive_end_date(event_end_exclusive_kst: str) -> str:
    return (datetime.fromisoformat(event_end_exclusive_kst).date() - timedelta(days=1)).isoformat()


class ShadowServer(ThreadingHTTPServer):
    """HTTP server carrying only prevalidated assets and a dashboard payload."""

    daemon_threads = True

    dashboard_payload: DashboardPayload
    ai_search_payload: AiSearchPayload
    ai_search_weekly_view: WeeklyAiSearchViewPayload
    ai_search_weekly_index: WeeklyAiSearchIndexPayload
    asset_routes: Mapping[str, tuple[str, bytes]]


def create_shadow_server(
    *,
    assets: Path,
    contract_path: Path,
    host: str,
    port: int,
    ai_search_payload: AiSearchPayload | None = None,
) -> ShadowServer:
    """Validate all local inputs before opening a loopback socket."""

    if host not in SAFE_HOSTS:
        raise ValueError("shadow server host must be loopback-only")
    if not 0 <= port <= 65535:
        raise ValueError("port must be between 0 and 65535")
    normalized_host = "127.0.0.1"
    routes = _load_assets(assets)
    contract = load_metric_contract(contract_path)
    if ai_search_payload is None:
        evidence_contract_path = (
            contract_path.parents[1] / "admin-ai-search" / "evidence-contract-v1.json"
        )
        evidence_contract = load_evidence_contract(evidence_contract_path)
        ai_search_payload = build_ai_search_payload((), evidence_contract)
    dashboard_payload = build_shadow_dashboard(contract, ai_search_payload)
    server = ShadowServer((normalized_host, port), _ShadowRequestHandler)
    server.dashboard_payload = dashboard_payload
    server.ai_search_payload = ai_search_payload
    server.ai_search_weekly_view = build_weekly_ai_search_view(ai_search_payload)
    server.ai_search_weekly_index = build_weekly_ai_search_index(
        server.ai_search_weekly_view
    )
    server.asset_routes = routes
    return server


def load_ai_search_payload_from_stream(
    stream: TextIO, evidence_contract: EvidenceContract
) -> AiSearchPayload:
    """Read exactly one JSON snapshot line without persisting Gmail data."""

    raw = stream.readline()
    if not raw.strip():
        raise ValueError("Gmail snapshot stream is empty")
    snapshot = json.loads(raw)
    if not isinstance(snapshot, Mapping):
        raise TypeError("Gmail snapshot must be a JSON object")
    typed_snapshot = cast(Mapping[str, object], snapshot)
    if snapshot.get("version") == GMAIL_EVIDENCE_ENVELOPE_VERSION:
        return build_ai_search_payload_from_gmail_evidence(
            typed_snapshot, evidence_contract
        )
    return build_ai_search_payload_from_gmail_snapshot(typed_snapshot, evidence_contract)


def _load_assets(assets: Path) -> Mapping[str, tuple[str, bytes]]:
    asset_root = assets.resolve(strict=True)
    if not asset_root.is_dir():
        raise NotADirectoryError("shadow asset root must be a directory")
    route_files = {
        "/": ("text/html; charset=utf-8", "index.html"),
        "/ai-search": ("text/html; charset=utf-8", "ai-search.html"),
        "/styles.css": ("text/css; charset=utf-8", "styles.css"),
        "/app.js": ("text/javascript; charset=utf-8", "app.js"),
        "/ai-search.js": ("text/javascript; charset=utf-8", "ai-search.js"),
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
        if self.path == "/api/ai-search":
            self._send_json(200, self.server.ai_search_payload)
            return
        if self.path == "/api/ai-search/weekly":
            self._send_json(200, self.server.ai_search_weekly_index)
            return
        if self.path.startswith("/api/ai-search/weekly/"):
            week_id = self.path.removeprefix("/api/ai-search/weekly/")
            week = next(
                (
                    item
                    for item in self.server.ai_search_weekly_view["weeks"]
                    if item["week_id"] == week_id
                ),
                None,
            )
            if week is None:
                self._send_json(
                    404,
                    {"status": "FAIL", "reason": "ai_search_week_not_found"},
                )
            else:
                self._send_json(200, week)
            return
        if self.path.startswith("/api/ai-search/candidates/"):
            canonical_key = self.path.removeprefix("/api/ai-search/candidates/")
            candidate = next(
                (
                    item
                    for item in self.server.ai_search_payload["candidate_ledger"]
                    if item["canonical_key"] == canonical_key
                ),
                None,
            )
            if candidate is None:
                self._send_json(404, {"status": "FAIL", "reason": "candidate_not_found"})
            else:
                self._send_json(200, candidate)
            return
        if self.path.startswith("/api/ai-search/"):
            batch_id = self.path.removeprefix("/api/ai-search/")
            batch = next(
                (
                    item
                    for item in self.server.ai_search_payload["batches"]
                    if item["batch_id"] == batch_id
                ),
                None,
            )
            if batch is None:
                self._send_json(404, {"status": "FAIL", "reason": "batch_not_found"})
            else:
                self._send_json(200, batch)
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
    parser.add_argument(
        "--ai-search-gmail-stdin",
        action="store_true",
        help="read one v1 Gmail snapshot JSON line from stdin without persisting it",
    )
    arguments = parser.parse_args(argv)
    ai_search_payload = None
    if arguments.ai_search_gmail_stdin:
        evidence_contract_path = (
            arguments.contract.parents[1] / "admin-ai-search" / "evidence-contract-v1.json"
        )
        evidence_contract = load_evidence_contract(evidence_contract_path)
        ai_search_payload = load_ai_search_payload_from_stream(sys.stdin, evidence_contract)
    server = create_shadow_server(
        assets=arguments.assets,
        contract_path=arguments.contract,
        host=cast(str, arguments.host),
        port=cast(int, arguments.port),
        ai_search_payload=ai_search_payload,
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
