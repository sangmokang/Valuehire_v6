from collections.abc import Mapping

import pytest

from humansearch import observe
from humansearch.auth_surface import SurfaceRole


class _InvalidUtf8Response:
    status = 200

    def read(self, amount: int) -> bytes:
        return bytes((255,))


class _InvalidUtf8Connection:
    def __init__(self, host: str, port: int, timeout: int) -> None:
        pass

    def request(
        self, method: str, path: str, headers: Mapping[str, str]
    ) -> None:
        pass

    def getresponse(self) -> _InvalidUtf8Response:
        return _InvalidUtf8Response()

    def close(self) -> None:
        pass


def test_non_utf8_target_response_is_a_closed_observation_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    contract = observe.MarkerContract(
        channel="saramin",
        diagnostic_host="127.0.0.1",
        diagnostic_ports=frozenset({9225}),
        targets_path="/json/list",
        allowed_origins=frozenset({"https://portal.invalid"}),
        loggable_paths=frozenset({"/home"}),
        surface_markers=("header",),
        role_markers={role: (f"{role.value}-marker",) for role in SurfaceRole},
    )
    monkeypatch.setattr(observe, "HTTPConnection", _InvalidUtf8Connection)

    with pytest.raises(observe.ObservationError, match="target list response"):
        observe._fetch_targets(contract, 9225)
