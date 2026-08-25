"""WU7 — V1 3회차가 잘리기 전 찾은 반례를 영구 편입한다(R9).

`_fetch_targets` 는 `HTTPConnection(...)` 을 **try 블록 밖**에서 만든다. 생성자는 제어문자가
든 호스트에서 `http.client.InvalidURL` 을 던지고, 그 예외는 아래 `except (OSError,
HTTPException)` 에 닿지 못한 채 `main()` 까지 그대로 올라간다 — `main()` 은 `CdpReadError` 와
`ObservationError` 만 잡는다.

호스트가 그런 값이 될 수 있는 이유는 `ip_address("::1%" + chr(10))` 이 루프백으로 판정되기
때문이다(파이썬은 IPv6 scope id 를 받아들이고, 그 안의 개행을 거르지 않는다).
"""

import pytest

from humansearch import observe
from humansearch.auth_surface import SurfaceRole

_CONTROL_HOST = "::1%" + chr(10)


def _contract(host: str) -> observe.MarkerContract:
    return observe.MarkerContract(
        channel="saramin",
        diagnostic_host=host,
        diagnostic_ports=frozenset({9225}),
        targets_path="/json/list",
        allowed_origins=frozenset({"https://portal.invalid"}),
        loggable_paths=frozenset({"/home"}),
        surface_markers=("header",),
        role_markers={role: (f"{role.value}-marker",) for role in SurfaceRole},
    )


def test_transport_construction_failure_is_a_closed_observation_failure() -> None:
    with pytest.raises(observe.ObservationError, match="target list request"):
        observe._fetch_targets(_contract(_CONTROL_HOST), 9225)


def test_address_with_a_control_character_is_not_a_loopback_host() -> None:
    assert observe._is_loopback_address(_CONTROL_HOST) is False
    assert observe._is_loopback_address("127.0.0.1\t") is False
    # 정상 루프백은 그대로 통과해야 한다 — 거부 방향으로만 좁힌다.
    assert observe._is_loopback_address("127.0.0.1") is True
    assert observe._is_loopback_address("::1") is True


def test_main_reports_drift_without_echoing_a_control_character_host(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(observe, "_load_contract", lambda channel: _contract(_CONTROL_HOST))

    exit_code = observe.main(["--channel", "saramin", "--port", "9225", "--once"])

    captured = capsys.readouterr()
    assert exit_code == 2
    assert captured.out == "STATE=drifted TAB=- ROLES=0 CONTRACT_VALID=false\n"
    assert captured.err == ""
    assert "::1" not in captured.out
