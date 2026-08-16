"""Runtime HTTP tests for the loopback-only admin shadow server."""

import json
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from http.client import HTTPConnection, HTTPResponse
from pathlib import Path

import pytest
from humansearch.admin_weekly_dashboard.shadow_server import (
    ShadowServer,
    create_shadow_server,
)

REPO_ROOT = Path(__file__).parents[2]
ASSET_DIR = REPO_ROOT / "apps" / "admin"
CONTRACT_PATH = (
    REPO_ROOT / "contracts" / "admin-weekly-dashboard" / "metric-contract-v1.json"
)


@contextmanager
def running_server() -> Iterator[tuple[ShadowServer, int]]:
    server = create_shadow_server(
        assets=ASSET_DIR,
        contract_path=CONTRACT_PATH,
        host="127.0.0.1",
        port=0,
    )
    port = int(server.server_address[1])
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server, port
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def request(port: int, path: str, *, method: str = "GET") -> tuple[HTTPResponse, bytes]:
    connection = HTTPConnection("127.0.0.1", port, timeout=5)
    connection.request(method, path)
    response = connection.getresponse()
    body = response.read()
    connection.close()
    return response, body


@pytest.mark.parametrize("host", ["", "0.0.0.0", "192.168.0.10", "::"])
def test_server_rejects_non_loopback_hosts(host: str) -> None:
    with pytest.raises(ValueError, match="loopback"):
        create_shadow_server(
            assets=ASSET_DIR,
            contract_path=CONTRACT_PATH,
            host=host,
            port=0,
        )


def test_dashboard_api_matches_the_precomputed_server_payload() -> None:
    with running_server() as (server, port):
        response, body = request(port, "/api/dashboard")

    assert response.status == 200
    assert response.getheader("Content-Type") == "application/json; charset=utf-8"
    assert json.loads(body) == server.dashboard_payload


@pytest.mark.parametrize(
    ("path", "content_type", "marker"),
    [
        ("/", "text/html; charset=utf-8", "LOCAL SHADOW · 운영 아님"),
        ("/styles.css", "text/css; charset=utf-8", "--surface"),
        ("/app.js", "text/javascript; charset=utf-8", "/api/dashboard"),
        ("/healthz", "application/json; charset=utf-8", '"status":"PASS"'),
    ],
)
def test_exact_public_routes_are_served(
    path: str,
    content_type: str,
    marker: str,
) -> None:
    with running_server() as (_, port):
        response, body = request(port, path)

    assert response.status == 200
    assert response.getheader("Content-Type") == content_type
    assert marker in body.decode("utf-8")


@pytest.mark.parametrize("path", ["/index.html", "/../README.md", "/api/dashboard?x=1"])
def test_unlisted_paths_fail_closed(path: str) -> None:
    with running_server() as (_, port):
        response, body = request(port, path)

    assert response.status == 404
    assert json.loads(body) == {"status": "FAIL", "reason": "route_not_found"}


def test_every_response_has_no_store_and_browser_security_headers() -> None:
    with running_server() as (_, port):
        responses = [request(port, path)[0] for path in ("/", "/api/dashboard", "/missing")]

    for response in responses:
        assert response.getheader("Cache-Control") == "no-store"
        assert response.getheader("X-Content-Type-Options") == "nosniff"
        csp = response.getheader("Content-Security-Policy")
        assert csp is not None
        assert "default-src 'self'" in csp
        assert "connect-src 'self'" in csp
        assert "object-src 'none'" in csp
        assert "frame-ancestors 'none'" in csp


@pytest.mark.parametrize("method", ["HEAD", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
def test_unsupported_methods_fail_closed_with_safe_headers(method: str) -> None:
    with running_server() as (_, port):
        response, body = request(port, "/api/dashboard", method=method)

    assert response.status == 405
    assert response.getheader("Cache-Control") == "no-store"
    assert response.getheader("Content-Security-Policy") is not None
    if method == "HEAD":
        assert body == b""
    else:
        assert json.loads(body) == {"status": "FAIL", "reason": "method_not_allowed"}
