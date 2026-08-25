"""WU5 — V1 적대검증(codex, fresh·read-only)이 낸 FAIL 판정의 반례를 영구 편입한다(R9).

WU1~WU4 는 `urlsplit()` 의 `ValueError` 만 막았다. V1 은 같은 계약("종료값 0 또는 2 · 계약된
한 줄 · 주소 조각 누출 0")을 뚫는 세 갈래를 더 찾았고, 셋 다 독립 재현했다.

1. `json.loads` 는 4,300 자리를 넘는 정수에서 `JSONDecodeError` 가 아니라 **맨 `ValueError`** 를
   던진다. 두 JSON 경계가 `JSONDecodeError`/`UnicodeDecodeError` 만 잡아 그물 밖으로 샌다.
2. 고립 서로게이트(`\\ud800`)가 든 주소는 축약을 통과하지만 마지막 `print()` 에서
   `UnicodeEncodeError`(= `ValueError` 의 하위형)로 죽는다 — try 블록 **밖**이다.
3. U+2028(줄 분리자)은 `urlsplit()` 이 지우지 않아 netloc 에 살아남는다. 출력은 `"\\n"` 을 담지
   않지만 `splitlines()` 로는 **두 줄**이 된다 — "한 줄" 계약이 깨지고 로그 주입이 가능하다.
4. `_valid_origin` 은 `.port` 를 검증하지 않아 `:notaport`·`:99999` 를 허용 origin 으로 통과시킨다.
"""

import json
from collections.abc import Mapping
from pathlib import Path

import pytest

from humansearch import observe
from humansearch.auth_surface import AuthSurfaceState, SurfaceObservation, SurfaceRole

_OVERSIZED_NUMBER = "1" * 4301
_LONE_SURROGATE_URL = "https://\ud800.example/home"
_LINE_SEPARATOR_URL = "https://portal .invalid/home"
_INVALID_OBSERVATION = SurfaceObservation(matched_roles=frozenset(), contract_valid=False)


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


class _OversizedNumberResponse:
    status = 200

    def read(self, amount: int) -> bytes:
        return f"[{_OVERSIZED_NUMBER}]".encode()


class _OversizedNumberConnection:
    def __init__(self, host: str, port: int, timeout: int) -> None:
        pass

    def request(self, method: str, path: str, headers: Mapping[str, str]) -> None:
        pass

    def getresponse(self) -> _OversizedNumberResponse:
        return _OversizedNumberResponse()

    def close(self) -> None:
        pass


def test_oversized_json_number_is_a_closed_transport_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(observe, "HTTPConnection", _OversizedNumberConnection)

    with pytest.raises(observe.ObservationError, match="target list response"):
        observe._fetch_targets(_contract(), 9225)


def test_oversized_json_number_in_the_contract_is_a_closed_failure(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    contract_path = tmp_path / "saramin-markers.json"
    contract_path.write_text(f"{{\"channel\": {_OVERSIZED_NUMBER}}}", encoding="utf-8")
    monkeypatch.setattr(observe, "_CONTRACT_PATH", contract_path)

    with pytest.raises(observe.ObservationError, match="marker contract is unavailable"):
        observe._load_contract("saramin")


@pytest.mark.parametrize("url", [_LONE_SURROGATE_URL, _LINE_SEPARATOR_URL])
def test_address_that_breaks_the_one_line_contract_renders_as_no_tab(url: str) -> None:
    assert observe._privacy_reduced_url(url) == ""

    line = observe.format_observation_line(
        AuthSurfaceState.DRIFTED, url, _INVALID_OBSERVATION
    )

    assert line == "STATE=drifted TAB=- ROLES=0 CONTRACT_VALID=false"
    assert len(line.splitlines()) == 1
    line.encode("utf-8")


# 판정 가능한 규칙만 고정한다: **포트를 읽을 수 없는** origin 은 무효다. `:0` 은 `.port` 가
# 0 을 정상 반환하므로 여기 넣지 않는다 — "포트 0 은 실주소가 아니다"는 별도 결정이고,
# 확정되지 않은 결정을 코드에 임의로 넣지 않는다(SOT-30 §3②).
@pytest.mark.parametrize("port", ["notaport", "99999", "-1"])
def test_origin_with_an_unreadable_port_is_not_a_valid_origin(port: str) -> None:
    assert observe._valid_origin(f"https://portal.invalid:{port}") is False


def test_contract_with_an_unusable_origin_port_is_refused(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    contract_path = tmp_path / "saramin-markers.json"
    contract_path.write_text(
        json.dumps(_raw_contract(allowed_origins=["https://portal.invalid:notaport"])),
        encoding="utf-8",
    )
    monkeypatch.setattr(observe, "_CONTRACT_PATH", contract_path)

    with pytest.raises(observe.ObservationError, match="allowed origin contract"):
        observe._load_contract("saramin")


def test_reduced_url_drops_every_userinfo_segment() -> None:
    """V1 지적: `@` 가 두 번 이상이면 `rpartition` 을 `partition` 으로 바꾼 변조가 살아남았다."""

    userinfo = "@".join(("operator", ":".join(("realm", "n0tr3al"))))
    reduced = observe._privacy_reduced_url(f"https://{userinfo}@hiring.saramin.co.kr/x")

    assert reduced == "https://hiring.saramin.co.kr/..."
    assert "@" not in reduced
