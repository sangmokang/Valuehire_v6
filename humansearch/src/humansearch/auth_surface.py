"""Pure classification of authentication-related portal surfaces."""

from dataclasses import dataclass
from enum import Enum

__all__ = (
    "AuthSurfaceState",
    "InvalidObservation",
    "SurfaceObservation",
    "SurfaceRole",
    "classify_auth_surface",
)


class AuthSurfaceState(str, Enum):
    """Authentication meaning derived from one validated surface observation."""

    UNKNOWN = "unknown"
    HUMAN_AUTH = "human_auth"
    AUTHENTICATED = "authenticated"
    CHALLENGE = "challenge"
    DRIFTED = "drifted"


class SurfaceRole(str, Enum):
    """Portal-independent roles supplied by an upstream surface contract."""

    AUTHENTICATED_SURFACE = "authenticated_surface"
    HUMAN_AUTH_SURFACE = "human_auth_surface"
    CHALLENGE_SURFACE = "challenge_surface"


@dataclass(frozen=True, slots=True)
class SurfaceObservation:
    """Roles observed on one surface and whether its structural contract is valid."""

    matched_roles: frozenset[SurfaceRole]
    contract_valid: bool


class InvalidObservation(ValueError):
    """Raised when a caller violates the runtime observation contract."""


_SINGLE_ROLE_STATES = {
    SurfaceRole.AUTHENTICATED_SURFACE: AuthSurfaceState.AUTHENTICATED,
    SurfaceRole.HUMAN_AUTH_SURFACE: AuthSurfaceState.HUMAN_AUTH,
    SurfaceRole.CHALLENGE_SURFACE: AuthSurfaceState.CHALLENGE,
}


def _validated(observation: object) -> SurfaceObservation:
    if type(observation) is not SurfaceObservation:
        raise InvalidObservation("observation must be a SurfaceObservation")
    if type(observation.contract_valid) is not bool:
        raise InvalidObservation("contract_valid must be a bool")
    if type(observation.matched_roles) is not frozenset:
        raise InvalidObservation("matched_roles must be a frozenset")
    if any(type(role) is not SurfaceRole for role in observation.matched_roles):
        raise InvalidObservation("matched_roles must contain only SurfaceRole values")
    return observation


def classify_auth_surface(observation: SurfaceObservation) -> AuthSurfaceState:
    """Classify one observation without consulting external state."""

    validated = _validated(observation)
    if not validated.contract_valid or len(validated.matched_roles) > 1:
        return AuthSurfaceState.DRIFTED
    if not validated.matched_roles:
        return AuthSurfaceState.UNKNOWN
    role = next(iter(validated.matched_roles))
    return _SINGLE_ROLE_STATES[role]
