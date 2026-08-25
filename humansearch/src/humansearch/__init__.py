"""HumanSearch v6 public package boundary."""

from typing import Any

from .auth_surface import (
    AuthSurfaceState,
    InvalidObservation,
    SurfaceObservation,
    SurfaceRole,
    classify_auth_surface,
)

PACKAGE_NAME = "humansearch"

_L1_EXPORTS = frozenset(
    {
        "TargetSelectionError",
        "exit_code_for_state",
        "format_observation_line",
        "observation_from_marker_payload",
        "select_single_target",
    }
)

__all__ = (
    "AuthSurfaceState",
    "InvalidObservation",
    "SurfaceObservation",
    "SurfaceRole",
    "TargetSelectionError",
    "classify_auth_surface",
    "exit_code_for_state",
    "format_observation_line",
    "observation_from_marker_payload",
    "select_single_target",
)


def __getattr__(name: str) -> Any:
    if name not in _L1_EXPORTS:
        raise AttributeError(name)
    from . import observe

    return getattr(observe, name)
