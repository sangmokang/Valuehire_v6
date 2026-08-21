from collections.abc import Callable
from typing import Any

import pytest

import humansearch
from humansearch import AuthSurfaceState, SurfaceObservation, classify_auth_surface


def _required_api(name: str) -> Any:
    value = getattr(humansearch, name, None)
    assert value is not None, f"missing HumanSearch L1 API: {name}"
    return value


def test_zero_matching_tabs_stops_without_guessing() -> None:
    select_target: Callable[[list[Any], frozenset[str]], Any] = _required_api(
        "select_single_target"
    )
    target_error: type[Exception] = _required_api("TargetSelectionError")

    with pytest.raises(target_error, match="exactly one"):
        select_target([], frozenset({"https://portal.invalid"}))


def test_multiple_matching_tabs_stop_without_guessing() -> None:
    select_target: Callable[[list[Any], frozenset[str]], Any] = _required_api(
        "select_single_target"
    )
    target_error: type[Exception] = _required_api("TargetSelectionError")
    targets: list[Any] = [
        {
            "type": "page",
            "url": "https://portal.invalid/first",
        },
        {
            "type": "page",
            "url": "https://portal.invalid/second",
        },
    ]

    with pytest.raises(target_error, match="exactly one"):
        select_target(targets, frozenset({"https://portal.invalid"}))


def test_unreadable_marker_payload_becomes_drifted_observation() -> None:
    observation_from_payload: Callable[[object], SurfaceObservation] = _required_api(
        "observation_from_marker_payload"
    )

    observation = observation_from_payload(
        {"contract_valid": True, "matched_roles": "authenticated_surface"}
    )

    assert observation.contract_valid is False
    assert observation.matched_roles == frozenset()
    assert classify_auth_surface(observation) is AuthSurfaceState.DRIFTED
