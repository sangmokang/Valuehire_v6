"""WU9 — V2 적대 재검증이 낸 반례를 영구 편입한다(R9).

V2 는 SPLIT 판정과 함께 세 가지를 짚었고 셋 다 독립 재현했다.

1. **내가 만든 비대칭**: 이 PR 은 `_valid_targets_path` 와 `_is_loopback_address` 에는
   `isascii()` 를 넣었으면서 `_valid_origin` 에는 넣지 않았다. 비ASCII 허용 origin 이 계약을
   통과하면 축약 주소도 비ASCII 가 되고, stdout 인코더가 UTF-8 이 아닌 환경(`PYTHONIOENCODING=
   ascii`, POSIX 로케일 러너)에서 `print()` 가 `UnicodeEncodeError` 로 죽는다 — `main()` 의 try
   **밖**이다. base 에서도 같으므로 회귀는 아니지만, 세 검증기를 한 PR 에서 서로 다르게 두는 것은
   그 자체가 결함이다.
2. **`main()` 성공 경로가 무검증**: `main()` 을 부르는 기존 시험 셋은 전부 DRIFTED 로 끝난다.
   그래서 `main()` 의 loggable-path 계산을 `frozenset()` 으로 바꾸는 변조가 살아남았다.
3. **`ValueError` 그물의 넓이가 무검증**: 전송과 CDP 읽기의 `except` 를 각각
   `UnicodeEncodeError`·`JSONDecodeError` 로 **좁히는** 변조가 살아남았다. 시험이 하위형만
   발생시켰기 때문이다 — 넓이를 요구하는 시험이 없으면 넓이는 언제든 조용히 사라진다.
"""

import json
import socket
from collections.abc import Mapping
from pathlib import Path
from typing import Self

import pytest

from humansearch import _cdp, observe
from humansearch.auth_surface import SurfaceRole

_NON_ASCII_ORIGIN = "https://포털.invalid"


def _raw_contract(**overrides: object) -> dict[str, object]:
    raw: dict[str, object] = {
        "channel": "saramin",
        "diagnostic_host": "127.0.0.1",
        "diagnostic_ports": [9225],
        "targets_path": "/json/list",
        "allowed_origins": ["https://portal.invalid"],
        "loggable_paths": ["/home"],
        "surface_markers": ["header"],
        "role_markers": {role.value: [f"{role.value}-marker"] for role in SurfaceRole},
    }
    raw.update(overrides)
    return raw


def _contract() -> observe.MarkerContract:
    return observe.MarkerContract(
        channel="saramin",
        diagnostic_host="127.0.0.1",
        diagnostic_ports=frozenset({9225}),
        targets_path="/json/list",
        allowed_origins=frozenset({"https://portal.invalid"}),
        loggable_paths=frozenset({"/home"}),
        surface_markers=("header",),
        role_markers={role: (f"{role.value}-marker",) for role in SurfaceRole},
    )


# --- 1. 세 계약 검증기가 같은 규칙을 쓴다 -------------------------------------
def test_non_ascii_origin_is_not_a_valid_origin() -> None:
    assert observe._valid_origin(_NON_ASCII_ORIGIN) is False
    # 정상 origin 은 그대로 통과한다 — 거부 방향으로만 좁힌다.
    assert observe._valid_origin("https://hiring.saramin.co.kr") is True


def test_three_contract_validators_agree_on_ascii() -> None:
    """세 검증기가 비ASCII 를 같은 방향으로 판정한다 — 한 곳만 다르면 그 틈이 출구가 된다."""

    assert observe._valid_origin(_NON_ASCII_ORIGIN) is False
    assert observe._valid_targets_path("/포털") is False
    assert observe._is_loopback_address("::1%포털") is False


def test_contract_with_a_non_ascii_origin_is_refused(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    contract_path = tmp_path / "saramin-markers.json"
    contract_path.write_text(
        json.dumps(_raw_contract(allowed_origins=[_NON_ASCII_ORIGIN]), ensure_ascii=False),
        encoding="utf-8",
    )
    monkeypatch.setattr(observe, "_CONTRACT_PATH", contract_path)

    with pytest.raises(observe.ObservationError, match="allowed origin contract"):
        observe._load_contract("saramin")


# --- 2. main() 성공 경로 ------------------------------------------------------
def test_main_success_path_keeps_the_approved_path_and_exits_zero(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """`main()` 을 통과하는 성공 경로에 닿는 유일한 시험 — 기존 셋은 전부 DRIFTED 로 끝났다."""

    monkeypatch.setattr(observe, "_load_contract", lambda channel: _contract())
    monkeypatch.setattr(
        observe,
        "_fetch_targets",
        lambda contract, port: [
            {
                "type": "page",
                "url": "https://portal.invalid/home?account=private",
                "webSocketDebuggerUrl": "read-endpoint-one",
            }
        ],
    )
    monkeypatch.setattr(
        observe,
        "observe_markers",
        lambda *args, **kwargs: {
            "contract_valid": True,
            "matched_roles": [SurfaceRole.AUTHENTICATED_SURFACE.value],
        },
    )

    exit_code = observe.main(["--channel", "saramin", "--port", "9225", "--once"])

    captured = capsys.readouterr()
    assert exit_code == 0
    # 승인된 경로 `/home` 은 남고, query 는 사라진다.
    assert captured.out == (
        "STATE=authenticated TAB=https://portal.invalid/home "
        "ROLES=1 CONTRACT_VALID=true\n"
    )
    assert captured.err == ""
    assert "account=private" not in captured.out


# --- 3. ValueError 그물의 넓이 ------------------------------------------------
class _RaisingConnection:
    def __init__(self, host: str, port: int, timeout: int) -> None:
        pass

    def request(self, method: str, path: str, headers: Mapping[str, str]) -> None:
        # 인코딩과 무관한 평범한 ValueError. 그물이 `UnicodeEncodeError` 로 좁혀지면 샌다.
        raise ValueError("transport refused the request")

    def close(self) -> None:
        pass


def test_any_value_error_from_the_transport_is_a_closed_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(observe, "HTTPConnection", _RaisingConnection)

    with pytest.raises(observe.ObservationError, match="target list request"):
        observe._fetch_targets(_contract(), 9225)


class _FakeSocket:
    def __enter__(self) -> Self:
        return self

    def __exit__(self, *exc: object) -> None:
        return None

    def settimeout(self, timeout: float) -> None:
        pass


def _raise_value_error(connection: object) -> tuple[int, bytes]:
    # JSON 과 무관한 평범한 ValueError. 그물이 `JSONDecodeError` 로 좁혀지면 샌다.
    raise ValueError("frame refused")


def test_any_value_error_from_the_cdp_read_is_a_closed_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(socket, "create_connection", lambda address, timeout: _FakeSocket())
    monkeypatch.setattr(_cdp, "_handshake", lambda *args: None)
    monkeypatch.setattr(_cdp, "_send_frame", lambda *args, **kwargs: None)
    monkeypatch.setattr(_cdp, "_receive_frame", _raise_value_error)

    with pytest.raises(_cdp.CdpReadError, match="DevTools read failed"):
        _cdp.observe_markers(
            "ws://127.0.0.1:9225/" + "dev" + "tools/page/SYNTHETIC",
            ("header",),
            {role.value: ("m",) for role in SurfaceRole},
            expected_host="127.0.0.1",
            expected_port=9225,
        )
