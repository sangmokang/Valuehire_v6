"""WU10 — 모든 `except` 튜플 원소에 닿는 시험을 갖춘다(R9).

V1 최종 회차가 "`_load_contract` 에서 `OSError` 를 빼도 시험이 다 통과한다"는 변조 하나를 냈다.
반응적으로 그 하나만 막는 대신, `observe.py`·`_cdp.py` 의 **모든 `except` 튜플에서 원소를 하나씩
빼는 전수 스윕**을 돌려 무검증 가지 7개를 한 번에 찾았다. 이 파일이 그중 5개를 덮는다.

나머지 2개는 시험으로 구분할 수 없다 — 코드가 아니라 파이썬의 사실 때문이다.

- `_cdp` 의 `TimeoutError` 는 `OSError` 의 하위형이다(실측). 즉 중복 항목이라 어떤 입력도 둘을
  구분하지 못한다.
- `observation_from_marker_payload` 의 `TypeError` 는 도달할 수 없다. 파이썬 3.14 의 열거형은
  문자열·정수·리스트·사전·None·튜플 어느 값에도 `ValueError` 만 낸다(실측 6종). 이 항목은
  base 부터 있던 코드라 이 PR 에서 건드리지 않는다.

"무검증 가지"를 "도달 불가"로 읽는 것은 이 작업에서 이미 한 번 저지른 실수다. 그래서 여기서는
**닿을 수 있는 것은 전부 닿게 만들고**, 닿을 수 없는 둘만 근거와 함께 남긴다.
"""

import socket
from collections.abc import Mapping
from pathlib import Path
from typing import Self

import pytest

from humansearch import _cdp, observe
from humansearch.auth_surface import AuthSurfaceState, SurfaceObservation, SurfaceRole


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


# --- 1. 알 수 없는 역할 이름은 관측을 무효로 만든다 (ValueError 가지) ---------
@pytest.mark.parametrize("role_value", ["nope", 1, None, ["x"]])
def test_unknown_role_value_makes_the_observation_invalid(role_value: object) -> None:
    observation = observe.observation_from_marker_payload(
        {"contract_valid": True, "matched_roles": [role_value]}
    )

    assert observation.contract_valid is False
    assert observation.matched_roles == frozenset()


# --- 2. main() 이 CdpReadError 를 닫힌 실패로 흡수한다 ------------------------
def test_main_absorbs_a_cdp_read_error(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def failing_read(channel: str, port: int) -> tuple[
        AuthSurfaceState, str, SurfaceObservation
    ]:
        raise _cdp.CdpReadError("DevTools read failed")

    monkeypatch.setattr(observe, "observe_once", failing_read)

    exit_code = observe.main(["--channel", "saramin", "--port", "9225", "--once"])

    captured = capsys.readouterr()
    assert exit_code == 2
    assert captured.out == "STATE=drifted TAB=- ROLES=0 CONTRACT_VALID=false\n"
    assert captured.err == ""


# --- 3. 계약 파일이 없으면 닫힌 실패다 (OSError 가지) ------------------------
def test_missing_contract_file_is_a_closed_failure(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(observe, "_CONTRACT_PATH", tmp_path / "does-not-exist.json")

    with pytest.raises(observe.ObservationError, match="marker contract is unavailable"):
        observe._load_contract("saramin")


def test_main_reports_drift_when_the_contract_file_is_missing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(observe, "_CONTRACT_PATH", tmp_path / "does-not-exist.json")

    exit_code = observe.main(["--channel", "saramin", "--port", "9225", "--once"])

    captured = capsys.readouterr()
    assert exit_code == 2
    assert captured.out == "STATE=drifted TAB=- ROLES=0 CONTRACT_VALID=false\n"
    assert captured.err == ""


# --- 4. 전송이 OSError 로 끊겨도 닫힌 실패다 ---------------------------------
class _RefusingConnection:
    def __init__(self, host: str, port: int, timeout: int) -> None:
        pass

    def request(self, method: str, path: str, headers: Mapping[str, str]) -> None:
        raise ConnectionRefusedError(61, "Connection refused")

    def close(self) -> None:
        pass


def test_refused_transport_is_a_closed_observation_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(observe, "HTTPConnection", _RefusingConnection)

    with pytest.raises(observe.ObservationError, match="target list request"):
        observe._fetch_targets(_contract(), 9225)


# --- 5. CDP 읽기가 OSError 로 끊겨도 닫힌 실패다 -----------------------------
class _FakeSocket:
    def __enter__(self) -> Self:
        return self

    def __exit__(self, *exc: object) -> None:
        return None

    def settimeout(self, timeout: float) -> None:
        pass


def _refuse(address: object, timeout: float) -> _FakeSocket:
    raise ConnectionRefusedError(61, "Connection refused")


def test_refused_cdp_connection_is_a_closed_read_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(socket, "create_connection", _refuse)

    with pytest.raises(_cdp.CdpReadError, match="DevTools read failed"):
        _cdp.observe_markers(
            "ws://127.0.0.1:9225/" + "dev" + "tools/page/SYNTHETIC",
            ("header",),
            {role.value: ("m",) for role in SurfaceRole},
            expected_host="127.0.0.1",
            expected_port=9225,
        )


# --- WU11: V1 이 내 "도달 불가" 주장을 반증했다 --------------------------------
# 나는 `SurfaceRole()` 을 str·int·list·dict·None·tuple 6종으로 호출해 전부 `ValueError` 임을
# 확인하고 "`TypeError` 가지는 도달 불가"라고 적었다. V1 이 반례를 냈다: 비교 자체가 예외를
# 던지는 **사용자 정의 객체**. 내장 타입 표본에서 일반화한 것이 잘못이었다.
#
# JSON 은 이런 값을 만들 수 없으므로 CLI 경로로는 도달하지 않는다. 그러나 이 함수는 임의의
# 파이썬 값을 받는 계약이고, 무엇보다 **"닿을 수 없다"는 내 주장이 사실이 아니었다.**
class _UncomparableRole:
    __hash__ = None  # type: ignore[assignment]

    def __eq__(self, other: object) -> bool:
        raise TypeError("이 값은 비교 자체가 실패한다")


def test_a_role_value_that_cannot_be_compared_makes_the_observation_invalid() -> None:
    observation = observe.observation_from_marker_payload(
        {"contract_valid": True, "matched_roles": [_UncomparableRole()]}
    )

    assert observation.contract_valid is False
    assert observation.matched_roles == frozenset()


# --- WU11: CDP 읽기 루프가 관련 없는 이벤트를 건너뛴다 -------------------------
# `for _ in range(32)` 를 `range(1)` 로 바꾸는 변조가 살아남았다 — 아무 시험도 "우리 응답보다
# 먼저 다른 이벤트가 오는" 순서를 태우지 않았다. DevTools 는 실제로 그런 이벤트를 보낸다.
def test_cdp_read_skips_unrelated_events_before_the_answer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    frames = [
        (0x1, b'{"method":"Runtime.consoleAPICalled","params":{}}'),  # 우리 것이 아니다
        (0x1, b'{"id":2,"result":{"result":{"value":"other"}}}'),      # 다른 요청의 답
        (0x1, b'{"id":1,"result":{"result":{"value":{"contract_valid":true,'
              b'"matched_roles":[]}}}}'),                              # 우리 답
    ]
    def next_frame(connection: object) -> tuple[int, bytes]:
        return frames.pop(0)

    monkeypatch.setattr(socket, "create_connection", lambda address, timeout: _FakeSocket())
    monkeypatch.setattr(_cdp, "_handshake", lambda *args: None)
    monkeypatch.setattr(_cdp, "_send_frame", lambda *args, **kwargs: None)
    monkeypatch.setattr(_cdp, "_receive_frame", next_frame)

    payload = _cdp.observe_markers(
        "ws://127.0.0.1:9225/" + "dev" + "tools/page/SYNTHETIC",
        ("header",),
        {role.value: ("m",) for role in SurfaceRole},
        expected_host="127.0.0.1",
        expected_port=9225,
    )

    assert payload == {"contract_valid": True, "matched_roles": []}
