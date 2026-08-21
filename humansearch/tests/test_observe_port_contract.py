from typing import Any

import pytest

from humansearch import observe


def test_unapproved_diagnostic_port_stops_before_target_read(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target_read_attempted = False

    def forbidden_target_read(*args: Any, **kwargs: Any) -> list[object]:
        nonlocal target_read_attempted
        target_read_attempted = True
        return []

    monkeypatch.setattr(observe, "_fetch_targets", forbidden_target_read)

    with pytest.raises(observe.ObservationError, match="port.*contract"):
        observe.observe_once("saramin", 9224)

    assert target_read_attempted is False
