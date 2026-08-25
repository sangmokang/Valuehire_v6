"""Observe one approved Saramin tab and classify its authentication surface."""

import argparse
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from http.client import HTTPConnection, HTTPException
from ipaddress import ip_address
from pathlib import Path
from typing import TypeGuard
from urllib.parse import SplitResult, urlsplit, urlunsplit

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

    # 축약이 빈 문자열이면 = 보여줄 안전한 주소가 없다는 뜻이다(파싱 불가). 탭이 아예
    # 없을 때와 같은 표기를 쓴다 — 실패마다 새 어휘를 만들지 않는다.
    tab = _privacy_reduced_url(tab_url, loggable_paths) if tab_url else ""
    contract_valid = str(observation.contract_valid).lower()
    return (
        f"STATE={state.value} TAB={tab or '-'} ROLES={len(observation.matched_roles)} "
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
    reduced = _split(tab_url) if tab_url else None
    paths = frozenset({reduced.path}) if reduced is not None else frozenset()
    print(format_observation_line(state, tab_url, observation, paths))
    return exit_code_for_state(state)


def _load_contract(channel: str) -> MarkerContract:
    try:
        raw = json.loads(_CONTRACT_PATH.read_text(encoding="utf-8"))
    # JSONDecodeError·UnicodeDecodeError 는 둘 다 ValueError 의 하위형이다. 하위형만 열거하면
    # 4,300 자리를 넘는 정수처럼 맨 ValueError 로 오는 갈래가 샌다. 아주 깊게 중첩된 JSON 은
    # ValueError 조차 아닌 RecursionError 로 온다(실측: 깊이 300,000 = 600KB) — V1 2회차 지적.
    except (OSError, ValueError, RecursionError) as exc:
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
    # ValueError 는 JSONDecodeError·UnicodeDecodeError·자릿수 초과를 포함하고, 깊은 중첩은
    # RecursionError 로 따로 온다.
    except (ValueError, RecursionError) as exc:
        raise ObservationError("target list response is invalid") from exc
    if not isinstance(payload, list):
        raise ObservationError("target list response is invalid")
    return payload


def _split(url: str) -> SplitResult | None:
    """Parse one address, treating an unparseable one as an explicit non-match.

    ``urlsplit`` raises ``ValueError`` for an unterminated IPv6 literal and for a netloc
    that changes under NFKC normalization, and that message quotes the netloc verbatim.
    Letting it escape replaces the contract's single privacy-reduced line with a traceback
    carrying part of the address, so every caller turns ``None`` into its own explicit
    refusal. Nothing here guesses at, repairs, or normalizes the input.
    """

    try:
        return urlsplit(url)
    except ValueError:
        return None


def _readable_port(parsed: SplitResult) -> bool:
    """포트를 읽을 수 있는지만 본다 — 값 자체에 정책을 넣지 않는다.

    ``SplitResult.port`` 는 ``urlsplit()`` 이 통과시킨 주소에서도 숫자가 아니거나 범위를
    벗어난 포트에서 별도로 ``ValueError`` 를 던진다.
    """

    try:
        _ = parsed.port
    except ValueError:
        return False
    return True


def _origin(url: str) -> str:
    parsed = _split(url)
    if parsed is None or parsed.scheme != "https" or not parsed.netloc:
        return ""
    return f"{parsed.scheme}://{parsed.netloc}"


def _valid_origin(value: object) -> bool:
    if not isinstance(value, str):
        return False
    parsed = _split(value)
    if parsed is None or not _readable_port(parsed):
        return False
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
    # ASCII 를 요구한다: HTTP 요청 줄은 latin-1 로 인코딩되므로 고립 서로게이트가 든 경로는
    # 전송 단계에서 UnicodeEncodeError 로 죽고, U+2028 같은 문자는 출력 한 줄 계약을 깬다.
    return (
        isinstance(value, str)
        and value.isascii()
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
    parsed = _split(url)
    if parsed is None:
        return ""
    path = parsed.path if parsed.path in loggable_paths else "/..."
    # netloc 앞부분의 `사용자:암호@` 는 경로에 든 식별자보다 민감하다. `.port` 는 숫자가
    # 아닌 포트에서 따로 ValueError 를 던지므로 읽지 않고, 마지막 `@` 뒤만 남긴다.
    netloc = parsed.netloc.rpartition("@")[2]
    reduced = urlunsplit((parsed.scheme, netloc, path, "", ""))
    # 출력은 인코딩 가능한 한 줄이어야 한다. `urlsplit()` 은 U+2028 같은 줄 분리자를 지우지
    # 않고, 고립 서로게이트는 `print()` 단계에서 `UnicodeEncodeError` 로 죽는다 — 둘 다
    # `main()` 의 try 블록 밖이다(V1 지적). 안전하게 보여줄 형태가 없으면 아무것도 안 보인다.
    # `splitlines()` 의 개수만 보면 **끝에 붙은** 줄 분리자를 놓친다 — 축약 결과만으로는
    # 한 줄이지만 뒤에 ` ROLES=...` 가 붙는 순간 두 줄이 된다(V1 2회차 지적). 그래서 개수가
    # 아니라 "줄바꿈 문자를 하나라도 담고 있는가"로 판정한다.
    if "".join(reduced.splitlines()) != reduced:
        return ""
    try:
        reduced.encode("utf-8")
    except UnicodeEncodeError:
        return ""
    return reduced


def _port(value: str) -> int:
    port = int(value)
    if not 1 <= port <= 65535:
        raise argparse.ArgumentTypeError("port must be between 1 and 65535")
    return port


if __name__ == "__main__":
    raise SystemExit(main())
