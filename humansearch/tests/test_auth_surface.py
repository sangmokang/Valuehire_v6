from itertools import combinations
from typing import Any

import pytest
from humansearch.auth_surface import (
    AuthSurfaceState,
    InvalidObservation,
    SurfaceObservation,
    SurfaceRole,
    classify_auth_surface,
)
from hypothesis import given
from hypothesis import strategies as st

import humansearch


def _role_subsets() -> list[frozenset[SurfaceRole]]:
    roles = tuple(SurfaceRole)
    return [
        frozenset(subset)
        for size in range(len(roles) + 1)
        for subset in combinations(roles, size)
    ]


def _expected_state(
    roles: frozenset[SurfaceRole], *, contract_valid: bool
) -> AuthSurfaceState:
    if not contract_valid or len(roles) > 1:
        return AuthSurfaceState.DRIFTED
    if not roles:
        return AuthSurfaceState.UNKNOWN
    return {
        SurfaceRole.AUTHENTICATED_SURFACE: AuthSurfaceState.AUTHENTICATED,
        SurfaceRole.HUMAN_AUTH_SURFACE: AuthSurfaceState.HUMAN_AUTH,
        SurfaceRole.CHALLENGE_SURFACE: AuthSurfaceState.CHALLENGE,
    }[next(iter(roles))]


NORMAL_CASES = [
    pytest.param(
        SurfaceObservation(matched_roles=roles, contract_valid=contract_valid),
        _expected_state(roles, contract_valid=contract_valid),
        id=f"valid-{contract_valid}-roles-{len(roles)}-{index}",
    )
    for contract_valid in (False, True)
    for index, roles in enumerate(_role_subsets())
]


@pytest.mark.parametrize(("observation", "expected"), NORMAL_CASES)
def test_classifies_all_normal_observations(
    observation: SurfaceObservation, expected: AuthSurfaceState
) -> None:
    assert classify_auth_surface(observation) is expected


def _unchecked_observation(
    *, matched_roles: Any, contract_valid: Any
) -> SurfaceObservation:
    return SurfaceObservation(
        matched_roles=matched_roles,
        contract_valid=contract_valid,
    )


INVALID_OBSERVATIONS: list[Any] = [
    object(),
    _unchecked_observation(matched_roles=frozenset(), contract_valid=1),
    _unchecked_observation(matched_roles=set(), contract_valid=True),
    _unchecked_observation(
        matched_roles=frozenset({"authenticated_surface"}), contract_valid=True
    ),
    _unchecked_observation(
        matched_roles=frozenset(
            {SurfaceRole.AUTHENTICATED_SURFACE, "challenge_surface"}
        ),
        contract_valid=True,
    ),
]


@pytest.mark.parametrize("observation", INVALID_OBSERVATIONS)
def test_rejects_invalid_observations(observation: Any) -> None:
    with pytest.raises(InvalidObservation):
        classify_auth_surface(observation)


ROLE_SET_STRATEGY = st.sets(
    st.sampled_from(tuple(SurfaceRole)), min_size=0, max_size=len(SurfaceRole)
).map(frozenset)


def _is_authenticated(state: AuthSurfaceState) -> bool:
    return state is AuthSurfaceState.AUTHENTICATED


@given(roles=ROLE_SET_STRATEGY, contract_valid=st.booleans())
def test_classification_properties(
    roles: frozenset[SurfaceRole], *, contract_valid: bool
) -> None:
    observation = SurfaceObservation(
        matched_roles=roles,
        contract_valid=contract_valid,
    )

    first = classify_auth_surface(observation)
    second = classify_auth_surface(observation)

    assert isinstance(first, AuthSurfaceState)
    assert first is second
    assert first is _expected_state(roles, contract_valid=contract_valid)
    if not contract_valid or len(roles) > 1:
        assert first is AuthSurfaceState.DRIFTED
    if contract_valid and not roles:
        assert first is AuthSurfaceState.UNKNOWN
        assert not _is_authenticated(first)


def test_contract_has_exact_public_values() -> None:
    assert {state.value for state in AuthSurfaceState} == {
        "unknown",
        "human_auth",
        "authenticated",
        "challenge",
        "drifted",
    }
    assert {role.value for role in SurfaceRole} == {
        "authenticated_surface",
        "human_auth_surface",
        "challenge_surface",
    }


def test_public_api_is_wired_through_package() -> None:
    assert humansearch.AuthSurfaceState is AuthSurfaceState
    assert humansearch.SurfaceRole is SurfaceRole
    assert humansearch.SurfaceObservation is SurfaceObservation
    assert humansearch.InvalidObservation is InvalidObservation
    assert humansearch.classify_auth_surface is classify_auth_surface
