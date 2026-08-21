from collections.abc import Callable
from typing import Any

import humansearch
from humansearch import AuthSurfaceState, SurfaceObservation, SurfaceRole


def _required_api(name: str) -> Any:
    value = getattr(humansearch, name, None)
    assert value is not None, f"missing HumanSearch L1 API: {name}"
    return value


def test_human_auth_is_a_person_call_with_exit_two() -> None:
    exit_code_for_state: Callable[[AuthSurfaceState], int] = _required_api(
        "exit_code_for_state"
    )

    assert exit_code_for_state(AuthSurfaceState.AUTHENTICATED) == 0
    assert exit_code_for_state(AuthSurfaceState.HUMAN_AUTH) == 2


def test_output_is_one_privacy_reduced_line() -> None:
    format_line: Callable[
        [AuthSurfaceState, str, SurfaceObservation, frozenset[str]], str
    ] = _required_api("format_observation_line")
    observation = SurfaceObservation(
        matched_roles=frozenset({SurfaceRole.HUMAN_AUTH_SURFACE}),
        contract_valid=True,
    )

    line = format_line(
        AuthSurfaceState.HUMAN_AUTH,
        "https://portal.invalid/login?account=private#fragment",
        observation,
        frozenset({"/login"}),
    )

    assert line == (
        "STATE=human_auth TAB=https://portal.invalid/login "
        "ROLES=1 CONTRACT_VALID=true"
    )
    assert "\n" not in line
