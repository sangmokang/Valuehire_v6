from typing import Any

import pytest

from humansearch import observe
from humansearch.auth_surface import SurfaceRole


def test_unapproved_diagnostic_port_stops_before_target_read(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target_read_attempted = False
    contract = observe.MarkerContract(
        channel="saramin",
        diagnostic_host="127.0.0.1",
        diagnostic_ports=frozenset({9225}),
        targets_path="/json/list",
        allowed_origins=frozenset({"https://portal.invalid"}),
        loggable_paths=frozenset({"/home"}),
        surface_markers=("main",),
        role_markers={role: ("main",) for role in SurfaceRole},
    )

    def forbidden_target_read(*args: Any, **kwargs: Any) -> list[object]:
        nonlocal target_read_attempted
        target_read_attempted = True
        return []

    monkeypatch.setattr(observe, "_load_contract", lambda channel: contract)
    monkeypatch.setattr(observe, "_fetch_targets", forbidden_target_read)

    with pytest.raises(observe.ObservationError, match="port.*contract"):
        observe.observe_once("saramin", 9224)

    assert target_read_attempted is False
