"""Minimal read-only Chrome DevTools transport for one expression."""

import base64
import hashlib
import json
import os
import socket
import struct
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

# 프로토콜 메서드 이름도 코드가 아니라 데이터다 (P22 · G3). 소스에 박아 두면 G3 의
# 점 토큰 판정이 잡는다 — 게이트에 예외를 파는 대신 값을 contracts/ 로 옮긴다.
_PROTOCOL_PATH = (
    Path(__file__).resolve().parents[3] / "contracts" / "humansearch" / "cdp-protocol.json"
)


def _cdp_evaluate_method() -> str:
    try:
        raw = json.loads(_PROTOCOL_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise CdpReadError("cdp protocol contract is unavailable") from exc
    method = raw.get("evaluate_method")
    if not isinstance(method, str) or not method:
        raise CdpReadError("cdp protocol contract is malformed")
    return method

_WEBSOCKET_GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"


class CdpReadError(RuntimeError):
    """Raised when the narrow read-only DevTools exchange cannot complete."""


def observe_markers(
    websocket_url: str,
    surface_markers: Sequence[str],
    role_markers: Mapping[str, Sequence[str]],
    *,
    expected_host: str,
    expected_port: int,
    timeout: float = 3.0,
) -> object:
    """Observe only contracted selector visibility and return semantic roles."""

    try:
        parsed = urlsplit(websocket_url)
        parsed_port = parsed.port
    except ValueError as exc:
        raise CdpReadError("target websocket is invalid") from exc
    if (
        parsed.scheme != "ws"
        or parsed.hostname != expected_host
        or parsed_port != expected_port
        or parsed.username is not None
        or parsed.password is not None
        or not parsed.path.startswith("/devtools/page/")
    ):
        raise CdpReadError("target websocket is outside the approved local endpoint")

    expression = _marker_expression(surface_markers, role_markers)
    request_path = parsed.path
    if parsed.query:
        request_path = f"{request_path}?{parsed.query}"

    try:
        with socket.create_connection((expected_host, expected_port), timeout=timeout) as connection:
            connection.settimeout(timeout)
            _handshake(connection, expected_host, expected_port, request_path)
            command = json.dumps(
                {
                    "id": 1,
                    "method": _cdp_evaluate_method(),
                    "params": {
                        "expression": expression,
                        "returnByValue": True,
                    },
                },
                separators=(",", ":"),
            ).encode()
            _send_frame(connection, command)
            for _ in range(32):
                opcode, payload = _receive_frame(connection)
                if opcode == 0x8:
                    raise CdpReadError("target closed the read connection")
                if opcode == 0x9:
                    _send_frame(connection, payload, opcode=0xA)
                    continue
                if opcode != 0x1:
                    continue
                message = _json_object(payload)
                if message.get("id") != 1:
                    continue
                if "error" in message:
                    raise CdpReadError("DevTools rejected the read expression")
                return _result_value(message)
    except (OSError, TimeoutError, ValueError, json.JSONDecodeError) as exc:
        raise CdpReadError("DevTools read failed") from exc
    raise CdpReadError("DevTools response limit exceeded")


def _marker_expression(
    surface_markers: Sequence[str], role_markers: Mapping[str, Sequence[str]]
) -> str:
    marker_data = {
        "surface_markers": tuple(surface_markers),
        "role_markers": {role: tuple(markers) for role, markers in role_markers.items()},
    }
    serialized = json.dumps(marker_data, ensure_ascii=False, separators=(",", ":"))
    return f"""(() => {{
const markers = {serialized};
const visible = (selector) => Array.from(document.querySelectorAll(selector))
  .some((element) => element.getClientRects().length > 0);
try {{
  const matched = Object.entries(markers.role_markers)
    .filter(([, selectors]) => selectors.some(visible))
    .map(([role]) => role);
  const valid = matched.length > 0 || markers.surface_markers.some(visible);
  if (!valid) return {{contract_valid:false, matched_roles:[]}};
  return {{contract_valid:true, matched_roles:matched}};
}} catch (_) {{
  return {{contract_valid:false, matched_roles:[]}};
}}
}})()"""


def _handshake(connection: socket.socket, host: str, port: int, path: str) -> None:
    key = base64.b64encode(os.urandom(16)).decode("ascii")
    request = (
        f"GET {path} HTTP/1.1\r\n"
        f"Host: {host}:{port}\r\n"
        "Upgrade: websocket\r\n"
        "Connection: Upgrade\r\n"
        f"Sec-WebSocket-Key: {key}\r\n"
        "Sec-WebSocket-Version: 13\r\n\r\n"
    ).encode("ascii")
    connection.sendall(request)
    response = _receive_headers(connection)
    lines = response.decode("latin-1").split("\r\n")
    if not lines or " 101 " not in lines[0]:
        raise CdpReadError("DevTools websocket handshake was rejected")
    headers = {}
    for line in lines[1:]:
        if ":" in line:
            name, value = line.split(":", 1)
            headers[name.lower()] = value.strip()
    expected = base64.b64encode(
        hashlib.sha1(f"{key}{_WEBSOCKET_GUID}".encode("ascii")).digest()
    ).decode("ascii")
    if headers.get("sec-websocket-accept") != expected:
        raise CdpReadError("DevTools websocket handshake proof was invalid")


def _receive_headers(connection: socket.socket) -> bytes:
    response = bytearray()
    while b"\r\n\r\n" not in response:
        chunk = connection.recv(4096)
        if not chunk:
            raise CdpReadError("DevTools websocket handshake ended early")
        response.extend(chunk)
        if len(response) > 16384:
            raise CdpReadError("DevTools websocket handshake was too large")
    headers, remainder = bytes(response).split(b"\r\n\r\n", 1)
    if remainder:
        raise CdpReadError("unexpected data followed the DevTools handshake")
    return headers


def _send_frame(connection: socket.socket, payload: bytes, *, opcode: int = 0x1) -> None:
    mask = os.urandom(4)
    length = len(payload)
    if length < 126:
        header = bytes((0x80 | opcode, 0x80 | length))
    elif length <= 0xFFFF:
        header = bytes((0x80 | opcode, 0xFE)) + struct.pack("!H", length)
    else:
        header = bytes((0x80 | opcode, 0xFF)) + struct.pack("!Q", length)
    masked = bytes(value ^ mask[index % 4] for index, value in enumerate(payload))
    connection.sendall(header + mask + masked)


def _receive_frame(connection: socket.socket) -> tuple[int, bytes]:
    first, second = _receive_exact(connection, 2)
    if not first & 0x80:
        raise CdpReadError("fragmented DevTools frames are unsupported")
    if second & 0x80:
        raise CdpReadError("DevTools server sent a masked frame")
    length = second & 0x7F
    if length == 126:
        length = struct.unpack("!H", _receive_exact(connection, 2))[0]
    elif length == 127:
        length = struct.unpack("!Q", _receive_exact(connection, 8))[0]
    if length > 1_048_576:
        raise CdpReadError("DevTools response exceeded the read limit")
    return first & 0x0F, _receive_exact(connection, length)


def _receive_exact(connection: socket.socket, length: int) -> bytes:
    data = bytearray()
    while len(data) < length:
        chunk = connection.recv(length - len(data))
        if not chunk:
            raise CdpReadError("DevTools connection ended early")
        data.extend(chunk)
    return bytes(data)


def _json_object(payload: bytes) -> dict[str, Any]:
    value = json.loads(payload)
    if not isinstance(value, dict):
        raise CdpReadError("DevTools response was not an object")
    return value


def _result_value(message: dict[str, Any]) -> object:
    result = message.get("result")
    if not isinstance(result, dict) or "exceptionDetails" in result:
        raise CdpReadError("DevTools expression did not complete")
    remote_object = result.get("result")
    if not isinstance(remote_object, dict) or "value" not in remote_object:
        raise CdpReadError("DevTools expression returned no value")
    return remote_object["value"]
