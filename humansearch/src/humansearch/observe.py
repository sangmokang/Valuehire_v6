"""Observe one approved Saramin tab and classify its authentication surface."""

import argparse
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from http.client import HTTPConnection, HTTPException
from ipaddress import ip_address
from pathlib import Path
from typing import TypeGuard
from urllib.parse import urlsplit, urlunsplit

from ._cdp import CdpReadError, observe_markers
from .auth_surface import (
    AuthSurfaceState,
    SurfaceObservation,
    SurfaceRole,
    classify_auth_surface,
)

_CONTRACT_PATH = (
    Path(__file__).resolve().parents[3]
    / "contracts"
    / "humansearch"
    / "saramin-markers.json"
)


class ObservationError(RuntimeError):
    """Raised when observation cannot safely reach a classified surface."""


class TargetSelectionError(ObservationError):
    """Raised unless exactly one approved page target exists."""


@dataclass(frozen=True, slots=True)
class BrowserTarget:
    """The only target information retained after exact selection."""

    url: str
    websocket_url: str


@dataclass(frozen=True, slots=True)
class MarkerContract:
    """Validated data boundary for one portal surface."""

    channel: str
    diagnostic_host: str
    diagnostic_ports: frozenset[int]
    targets_path: str
    allowed_origins: frozenset[str]
    loggable_paths: frozenset[str]
    surface_markers: tuple[str, ...]
    role_markers: Mapping[SurfaceRole, tuple[str, ...]]


def select_single_target(
    targets: Sequence[object], allowed_origins: frozenset[str]
) -> BrowserTarget:
    """Select exactly one approved page without using order or title as a tiebreaker."""

    matching: list[Mapping[str, object]] = []
    for candidate in targets:
        if not isinstance(candidate, dict) or candidate.get("type") != "page":
            continue
        url = candidate.get("url")
        if isinstance(url, str) and _origin(url) in allowed_origins:
            matching.append(candidate)
    if len(matching) != 1:
        raise TargetSelectionError(
            f"expected exactly one matching tab, found {len(matching)}"
        )
    selected = matching[0]
    url = selected.get("url")
    websocket_url = selected.get("webSocketDebuggerUrl")
    if not isinstance(url, str) or not isinstance(websocket_url, str):
        raise TargetSelectionError("selected tab lacks a read endpoint")
    return BrowserTarget(url=url, websocket_url=websocket_url)


def observation_from_marker_payload(payload: object) -> SurfaceObservation:
    """Translate a narrow browser result into the three L0 semantic roles."""

    invalid = SurfaceObservation(matched_roles=frozenset(), contract_valid=False)
    if not isinstance(payload, dict):
        return invalid
    contract_valid = payload.get("contract_valid")
    matched_roles = payload.get("matched_roles")
    if type(contract_valid) is not bool or not isinstance(matched_roles, list):
        return invalid
    if not contract_valid:
        return invalid
    try:
        roles = frozenset(SurfaceRole(role) for role in matched_roles)
    except (TypeError, ValueError):
        return invalid
    if len(roles) != len(matched_roles):
        return invalid
    return SurfaceObservation(matched_roles=roles, contract_valid=True)


def exit_code_for_state(state: AuthSurfaceState) -> int:
    """Return success only for a uniquely authenticated surface."""

    return 0 if state is AuthSurfaceState.AUTHENTICATED else 2


def format_observation_line(
    state: AuthSurfaceState,
    tab_url: str,
    observation: SurfaceObservation,
    loggable_paths: frozenset[str] = frozenset(),
) -> str:
    """Render the complete privacy-reduced CLI output."""

    tab = _privacy_reduced_url(tab_url, loggable_paths) if tab_url else "-"
    contract_valid = str(observation.contract_valid).lower()
    return (
        f"STATE={state.value} TAB={tab} ROLES={len(observation.matched_roles)} "
        f"CONTRACT_VALID={contract_valid}"
    )


def observe_once(channel: str, port: int) -> tuple[AuthSurfaceState, str, SurfaceObservation]:
    """Perform the one allowed target-list read and one DOM marker evaluation."""

    contract = _load_contract(channel)
    if port not in contract.diagnostic_ports:
        raise ObservationError("diagnostic port is outside channel contract")
    targets = _fetch_targets(contract, port)
    target = select_single_target(targets, contract.allowed_origins)
    payload = observe_markers(
        target.websocket_url,
        contract.surface_markers,
        {role.value: contract.role_markers[role] for role in SurfaceRole},
        expected_host=contract.diagnostic_host,
        expected_port=port,
    )
    observation = observation_from_marker_payload(payload)
    tab_url = _privacy_reduced_url(target.url, contract.loggable_paths)
    return classify_auth_surface(observation), tab_url, observation


def main(argv: Sequence[str] | None = None) -> int:
    """Run the one-shot observer without retries or browser lifecycle control."""

    parser = argparse.ArgumentParser(prog="python -m humansearch.observe")
    parser.add_argument("--channel", choices=("saramin",), required=True)
    parser.add_argument("--port", type=_port, required=True)
    parser.add_argument("--once", action="store_true", required=True)
    args = parser.parse_args(argv)

    try:
        state, tab_url, observation = observe_once(args.channel, args.port)
    except (CdpReadError, ObservationError):
        tab_url = ""
        observation = SurfaceObservation(
            matched_roles=frozenset(), contract_valid=False
        )
        state = classify_auth_surface(observation)
    paths = frozenset({urlsplit(tab_url).path}) if tab_url else frozenset()
    print(format_observation_line(state, tab_url, observation, paths))
    return exit_code_for_state(state)


def _load_contract(channel: str) -> MarkerContract:
    try:
        raw = json.loads(_CONTRACT_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ObservationError("marker contract is unavailable") from exc
    if not isinstance(raw, dict) or raw.get("channel") != channel:
        raise ObservationError("marker contract channel is invalid")
    host = raw.get("diagnostic_host")
    ports = raw.get("diagnostic_ports")
    targets_path = raw.get("targets_path")
    origins = raw.get("allowed_origins")
    loggable_paths = raw.get("loggable_paths")
    surface_markers = raw.get("surface_markers")
    role_markers = raw.get("role_markers")
    if (
        not isinstance(host, str)
        or not _is_loopback_address(host)
        or not _valid_ports(ports)
        or not _valid_targets_path(targets_path)
    ):
        raise ObservationError("diagnostic endpoint contract is invalid")
    if not _string_list(origins) or not all(_valid_origin(item) for item in origins):
        raise ObservationError("allowed origin contract is invalid")
    if not _string_list(loggable_paths) or not all(
        _valid_targets_path(item) for item in loggable_paths
    ):
        raise ObservationError("loggable path contract is invalid")
    if not _string_list(surface_markers) or not isinstance(role_markers, dict):
        raise ObservationError("surface marker contract is invalid")
    expected_roles = {role.value for role in SurfaceRole}
    if set(role_markers) != expected_roles:
        raise ObservationError("role marker contract is incomplete")
    parsed_roles: dict[SurfaceRole, tuple[str, ...]] = {}
    for role in SurfaceRole:
        markers = role_markers.get(role.value)
        if not _string_list(markers):
            raise ObservationError("role marker contract is invalid")
        parsed_roles[role] = tuple(markers)
    return MarkerContract(
        channel=channel,
        diagnostic_host=host,
        diagnostic_ports=frozenset(ports),
        targets_path=targets_path,
        allowed_origins=frozenset(origins),
        loggable_paths=frozenset(loggable_paths),
        surface_markers=tuple(surface_markers),
        role_markers=parsed_roles,
    )


def _fetch_targets(contract: MarkerContract, port: int) -> list[object]:
    connection = HTTPConnection(contract.diagnostic_host, port, timeout=3)
    try:
        connection.request(
            "GET", contract.targets_path, headers={"Accept": "application/json"}
        )
        response = connection.getresponse()
        if response.status != 200:
            raise ObservationError("target list request was rejected")
        body = response.read(1_048_577)
    except (OSError, HTTPException) as exc:
        raise ObservationError("target list request failed") from exc
    finally:
        connection.close()
    if len(body) > 1_048_576:
        raise ObservationError("target list response exceeded the read limit")
    try:
        payload = json.loads(body)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ObservationError("target list response is invalid") from exc
    if not isinstance(payload, list):
        raise ObservationError("target list response is invalid")
    return payload


def _origin(url: str) -> str:
    parsed = urlsplit(url)
    if parsed.scheme != "https" or not parsed.netloc:
        return ""
    return f"{parsed.scheme}://{parsed.netloc}"


def _valid_origin(value: object) -> bool:
    if not isinstance(value, str):
        return False
    parsed = urlsplit(value)
    return (
        parsed.scheme == "https"
        and bool(parsed.netloc)
        and not parsed.path
        and not parsed.query
        and not parsed.fragment
        and parsed.username is None
        and parsed.password is None
    )


def _valid_targets_path(value: object) -> TypeGuard[str]:
    return (
        isinstance(value, str)
        and value.startswith("/")
        and "?" not in value
        and "#" not in value
        and "//" not in value
    )


def _is_loopback_address(value: str) -> bool:
    try:
        return ip_address(value).is_loopback
    except ValueError:
        return False


def _valid_ports(value: object) -> TypeGuard[list[int]]:
    return isinstance(value, list) and bool(value) and all(
        type(item) is int and 1 <= item <= 65535 for item in value
    )


def _string_list(value: object) -> TypeGuard[list[str]]:
    return (
        isinstance(value, list)
        and bool(value)
        and all(isinstance(item, str) and bool(item) for item in value)
    )


def _privacy_reduced_url(
    url: str, loggable_paths: frozenset[str] = frozenset()
) -> str:
    parsed = urlsplit(url)
    path = parsed.path if parsed.path in loggable_paths else "/..."
    return urlunsplit((parsed.scheme, parsed.netloc, path, "", ""))


def _port(value: str) -> int:
    port = int(value)
    if not 1 <= port <= 65535:
        raise argparse.ArgumentTypeError("port must be between 1 and 65535")
    return port


if __name__ == "__main__":
    raise SystemExit(main())
