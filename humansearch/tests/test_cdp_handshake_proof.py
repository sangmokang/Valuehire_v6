"""WU1 — 관측기가 진짜 브라우저 진단 통로하고만 이야기한다는 것을 지킨다.

`_handshake` 는 서버가 우리가 보낸 임의 키로 RFC 6455 계산을 해냈는지 확인한다. 해내지 못하면
웹소켓을 말할 줄 모르는 다른 프로그램이다. 그 확인을 지우면 **그 포트에 앉아 있는 아무
프로그램이나 브라우저 행세를 할 수 있고, 관측기는 그것이 준 "로그인 되어 있음"을 그대로 믿는다.**

그 한 줄을 지워도 시험 118건이 전부 통과했다(실측). 원인은 하필 이 저장소의 다른 시험 셋이
전부 `_handshake` 자체를 몽키패치로 치워 버렸기 때문이다 — 읽기 루프를 보려고 그렇게 했는데,
그 결과 이 함수를 보는 시험이 0건이 됐다.

그래서 여기서는 `_handshake` 를 **치우지 않는다.** 소켓만 가짜로 주고 실제 함수를 태운다.
"""

import base64
import hashlib
from typing import Self

import pytest

from humansearch import _cdp

_HOST = "127.0.0.1"
_PORT = 9225
_PATH = "/" + "dev" + "tools/page/SYNTHETIC"  # 세션 URL 모양은 저장소에 두지 않는다


class _ScriptedSocket:
    """보낸 것을 기억하고, 미리 정한 응답을 돌려주는 가짜 소켓."""

    def __init__(self, response: bytes) -> None:
        self.sent = bytearray()
        self._response = response

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *exc: object) -> None:
        return None

    def settimeout(self, timeout: float) -> None:
        pass

    def sendall(self, payload: bytes) -> None:
        self.sent.extend(payload)

    def recv(self, amount: int) -> bytes:
        chunk, self._response = self._response[:amount], self._response[amount:]
        return chunk


def _sent_key(connection: _ScriptedSocket) -> str:
    """실제 요청에서 우리가 보낸 임의 키를 꺼낸다 — 정답을 픽스처에 심지 않기 위해서다."""

    for line in bytes(connection.sent).decode("latin-1").split("\r\n"):
        if line.lower().startswith("sec-websocket-key:"):
            return line.split(":", 1)[1].strip()
    raise AssertionError("요청에 Sec-WebSocket-Key 가 없다")


def _proof_for(key: str) -> str:
    guid = _cdp._WEBSOCKET_GUID
    return base64.b64encode(hashlib.sha1(f"{key}{guid}".encode("ascii")).digest()).decode("ascii")


def _response(accept: str | None) -> bytes:
    lines = ["HTTP/1.1 101 Switching Protocols", "Upgrade: websocket", "Connection: Upgrade"]
    if accept is not None:
        lines.append(f"Sec-WebSocket-Accept: {accept}")
    return ("\r\n".join(lines) + "\r\n\r\n").encode("latin-1")


class _AnsweringSocket(_ScriptedSocket):
    """우리가 보낸 키로 **올바른** 증명을 계산해 돌려주는 소켓 — 정직한 서버 역할."""

    def __init__(self) -> None:
        super().__init__(b"")

    def sendall(self, payload: bytes) -> None:
        super().sendall(payload)
        self._response = _response(_proof_for(_sent_key(self)))


def test_a_correct_proof_is_accepted() -> None:
    """정상 증명은 통과해야 한다 — 거부 방향으로만 좁힌다."""

    connection = _AnsweringSocket()

    _cdp._handshake(connection, _HOST, _PORT, _PATH)  # type: ignore[arg-type]

    assert b"Sec-WebSocket-Key:" in bytes(connection.sent)


@pytest.mark.parametrize(
    ("accept", "이름"),
    [
        ("SGVsbG8gdGhlcmUgZnJpZW5k", "증명이 틀림"),
        ("", "증명이 빈 문자열"),
        (None, "증명 헤더가 아예 없음"),
    ],
)
def test_a_wrong_proof_is_refused(accept: str | None, 이름: str) -> None:
    connection = _ScriptedSocket(_response(accept))

    with pytest.raises(_cdp.CdpReadError) as caught:
        _cdp._handshake(connection, _HOST, _PORT, _PATH)  # type: ignore[arg-type]

    assert "handshake proof was invalid" in str(caught.value)
    # 거부 사유에 우리 키도, 상대가 준 값도 싣지 않는다(브라우저 계약 §12).
    message = str(caught.value)
    assert _sent_key(connection) not in message
    if accept:
        assert accept not in message


def test_a_non_101_status_is_refused_before_the_proof_is_checked() -> None:
    connection = _ScriptedSocket(b"HTTP/1.1 200 OK\r\nUpgrade: websocket\r\n\r\n")

    with pytest.raises(_cdp.CdpReadError, match="handshake was rejected"):
        _cdp._handshake(connection, _HOST, _PORT, _PATH)  # type: ignore[arg-type]


def test_the_proof_is_computed_from_the_key_we_actually_sent() -> None:
    """정답을 픽스처에 심지 않았음을 고정한다 — 키가 매번 달라도 성립해야 한다."""

    keys: list[str] = []

    for _ in range(3):
        connection = _AnsweringSocket()
        _cdp._handshake(connection, _HOST, _PORT, _PATH)  # type: ignore[arg-type]
        keys.append(_sent_key(connection))

    assert len(set(keys)) == 3, "키가 매번 새로 생성되어야 한다"
