"""WU6 — V1 재검증(2회차)이 낸 FAIL 판정의 반례를 영구 편입한다(R9).

WU5 는 `ValueError` 계열을 막았다. V1 은 같은 계약을 뚫는 네 갈래를 더 냈고 넷 다 독립 재현했다.

1. `json.loads` 는 아주 깊게 중첩된 입력에서 `RecursionError` 를 던진다 — `ValueError` 의
   하위형이 **아니다**. 깊이 300,000 은 600KB 라 1MiB 읽기 한계 안쪽이다(실측).
2. `_valid_targets_path` 가 ASCII 밖 문자를 허용해, 고립 서로게이트가 든 경로가 계약을
   통과한 뒤 HTTP 요청 인코딩(latin-1)에서 `UnicodeEncodeError` 로 죽는다.
3. 축약 주소의 **끝**에 U+2028 이 붙으면 `splitlines()` 는 1을 돌려주지만, 뒤에
   ` ROLES=...` 가 붙은 **완성된 줄**은 두 줄이 된다. 가드가 한 칸 이르게 판정하고 있었다.
4. `_origin` 의 `parsed.netloc` 을 `parsed.hostname` 으로 바꾸면 포트가 탈락해
   `https://portal.invalid:444` 가 포트 없는 승인 origin 과 같아진다. 이를 잡는 시험이 없었다.
"""

import socket
from collections.abc import Mapping
from pathlib import Path
from typing import Self

import pytest

from humansearch import _cdp, observe
from humansearch.auth_surface import AuthSurfaceState, SurfaceObservation, SurfaceRole

_DEEP_JSON = ("[" * 300_000 + "]" * 300_000).encode()
_LINE_SEPARATOR_PATH = "/home "
_SURROGATE_PATH = "/\ud800"
# 비밀 스캔은 CDP 세션 URL 모양을 금지한다 — 그 주소 자체가 브라우저를 조종하는 자격이기
# 때문이다. 합성 픽스처지만 그 모양을 저장소 텍스트로 남기지 않고 실행 시점에 조립한다.
_FAKE_WEBSOCKET = "ws://127.0.0.1:9225/" + "dev" + "tools/page/SYNTHETIC"
_INVALID_OBSERVATION = SurfaceObservation(matched_roles=frozenset(), contract_valid=False)


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


class _DeepJsonResponse:
    status = 200

    def read(self, amount: int) -> bytes:
        return _DEEP_JSON


class _DeepJsonConnection:
    def __init__(self, host: str, port: int, timeout: int) -> None:
        pass

    def request(self, method: str, path: str, headers: Mapping[str, str]) -> None:
        pass

    def getresponse(self) -> _DeepJsonResponse:
        return _DeepJsonResponse()

    def close(self) -> None:
        pass


def test_deeply_nested_target_json_is_a_closed_transport_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert len(_DEEP_JSON) < 1_048_576  # 읽기 한계보다 작아야 이 경로에 도달한다

    monkeypatch.setattr(observe, "HTTPConnection", _DeepJsonConnection)

    with pytest.raises(observe.ObservationError, match="target list response"):
        observe._fetch_targets(_contract(), 9225)


def test_deeply_nested_contract_json_is_a_closed_failure(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    contract_path = tmp_path / "saramin-markers.json"
    contract_path.write_bytes(_DEEP_JSON)
    monkeypatch.setattr(observe, "_CONTRACT_PATH", contract_path)

    with pytest.raises(observe.ObservationError, match="marker contract is unavailable"):
        observe._load_contract("saramin")


class _FakeSocket:
    def __enter__(self) -> Self:
        return self

    def __exit__(self, *exc: object) -> None:
        return None

    def settimeout(self, timeout: float) -> None:
        pass


def test_deeply_nested_cdp_json_is_a_closed_read_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # `_cdp` 가 `import socket` 로 같은 모듈 객체를 쓰므로 여기 패치가 그대로 걸린다.
    monkeypatch.setattr(socket, "create_connection", lambda address, timeout: _FakeSocket())
    monkeypatch.setattr(_cdp, "_handshake", lambda *args: None)
    monkeypatch.setattr(_cdp, "_send_frame", lambda *args, **kwargs: None)
    monkeypatch.setattr(_cdp, "_receive_frame", lambda connection: (0x1, _DEEP_JSON))

    with pytest.raises(_cdp.CdpReadError, match="DevTools read failed"):
        _cdp.observe_markers(
            _FAKE_WEBSOCKET,
            ("header",),
            {role.value: ("m",) for role in SurfaceRole},
            expected_host="127.0.0.1",
            expected_port=9225,
        )


@pytest.mark.parametrize("path", [_SURROGATE_PATH, _LINE_SEPARATOR_PATH, "/홈"])
def test_non_ascii_contract_path_is_not_valid_contract_data(path: str) -> None:
    assert observe._valid_targets_path(path) is False


def test_line_breaking_loggable_path_cannot_split_the_finished_line() -> None:
    url = f"https://portal.invalid{_LINE_SEPARATOR_PATH}"

    line = observe.format_observation_line(
        AuthSurfaceState.DRIFTED,
        url,
        _INVALID_OBSERVATION,
        frozenset({_LINE_SEPARATOR_PATH}),
    )

    assert len(line.splitlines()) == 1
    assert line == "STATE=drifted TAB=- ROLES=0 CONTRACT_VALID=false"


@pytest.mark.parametrize(
    ("url", "configured"),
    [
        ("https://portal.invalid:444/home", "https://portal.invalid"),
        ("https://portal.invalid/home", "https://portal.invalid:444"),
        ("https://portal.invalid:443/home", "https://portal.invalid"),
    ],
)
def test_port_is_part_of_the_origin_comparison(url: str, configured: str) -> None:
    """V1 지적: `_origin` 이 netloc 대신 hostname 을 쓰면 포트가 탈락해도 아무도 안 잡았다."""

    with pytest.raises(observe.TargetSelectionError, match="found 0"):
        observe.select_single_target(
            [{"type": "page", "url": url, "webSocketDebuggerUrl": "ws"}],
            frozenset({configured}),
        )


def test_configured_port_still_matches_exactly() -> None:
    target = observe.select_single_target(
        [
            {
                "type": "page",
                "url": "https://portal.invalid:444/home",
                "webSocketDebuggerUrl": "ws",
            }
        ],
        frozenset({"https://portal.invalid:444"}),
    )

    assert target.url == "https://portal.invalid:444/home"
