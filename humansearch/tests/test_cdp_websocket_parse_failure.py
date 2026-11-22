"""R9 회귀: 전송 경계의 주소 파싱 실패도 크래시가 아니라 닫힌 거부여야 한다.

`observe.py` 의 파싱 크래시를 고치는 과정에서 `_cdp.observe_markers` 도 같은 `urlsplit`
`ValueError` 를 다룬다는 것을 발견했다. 그쪽 가드는 이미 올바르지만 **시험이 하나도 없었다**
— 같은 결함군의 미검증 경로다. 여기서 그 가드를 회귀 자산으로 고정한다.

`observe.py` 와 달리 `_cdp` 는 `SplitResult.port` 를 읽는다. `urlsplit()` 자체가 통과한 뒤에도
`.port` 는 숫자가 아닌 포트에서 `ValueError` 를 따로 던진다(실측). 두 갈래 모두 덮는다.
"""

import inspect
import json
import socket
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from humansearch import _cdp

_ROLE_MARKERS = {"authenticated_surface": ("a",), "human_auth_surface": ("b",),
                 "challenge_surface": ("c",)}

# 1) urlsplit() 자체가 거부하는 주소  2) urlsplit() 은 통과하지만 .port 가 거부하는 주소.
# 두 갈래 모두 경로 검사보다 **먼저** 거부되므로 실제 세션 경로 모양이 필요 없다 — 그리고
# 그 모양을 저장소에 두는 것은 비밀 스캔이 금지한다(세션 URL = 브라우저 조종 자격증명).
_UNPARSEABLE = "ws://[::1/page/SESSION-9"
_BAD_PORT = "ws://127.0.0.1:notaport/page/SESSION-9"


@pytest.mark.parametrize("websocket_url", [_UNPARSEABLE, _BAD_PORT])
def test_unparseable_websocket_url_is_a_closed_read_failure(
    websocket_url: str,
) -> None:
    with pytest.raises(_cdp.CdpReadError) as caught:
        _cdp.observe_markers(
            websocket_url,
            ("header",),
            _ROLE_MARKERS,
            expected_host="127.0.0.1",
            expected_port=9225,
        )

    message = str(caught.value)
    assert message == "target websocket is invalid"
    # 브라우저 계약 §5·§12 — 거부 사유에 주소 조각을 싣지 않는다.
    for marker in ("SESSION-9", "[::1", "notaport", "/page/"):
        assert marker not in message


def test_packaged_cdp_protocol_contract_matches_canonical_contract() -> None:
    assert _cdp._load_runtime_evaluate_method(
        _cdp._CDP_PROTOCOL_CONTRACT_PATH
    ) == _cdp._load_runtime_evaluate_method(_cdp._PACKAGED_CDP_PROTOCOL_CONTRACT_PATH)


@pytest.mark.parametrize("use_packaged_contract", [False, True])
def test_runtime_evaluate_method_is_loaded_from_contract(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, use_packaged_contract: bool
) -> None:
    method = _cdp._load_runtime_evaluate_method(_cdp._CDP_PROTOCOL_CONTRACT_PATH)
    assert method not in inspect.getsource(_cdp)
    expected = method + ".contract-probe"
    path = tmp_path / "cdp-protocol.json"
    path.write_text(json.dumps({"evaluate_method": expected}), encoding="utf-8")
    mirror = tmp_path / "packaged-cdp-protocol.json"
    mirror_method = expected if use_packaged_contract else method + ".mirror-probe"
    mirror.write_text(json.dumps({"evaluate_method": mirror_method}), encoding="utf-8")
    monkeypatch.setattr(
        _cdp, "_CDP_PROTOCOL_CONTRACT_PATH",
        tmp_path / "missing.json" if use_packaged_contract else path,
    )
    monkeypatch.setattr(_cdp, "_PACKAGED_CDP_PROTOCOL_CONTRACT_PATH", mirror)

    sent: list[dict[str, object]] = []
    monkeypatch.setattr(socket, "create_connection", lambda *args, **kwargs: MagicMock())
    monkeypatch.setattr(_cdp, "_handshake", lambda *args: None)
    monkeypatch.setattr(
        _cdp, "_send_frame", lambda connection, payload: sent.append(json.loads(payload))
    )
    monkeypatch.setattr(
        _cdp, "_receive_frame",
        lambda connection: (0x1, b'{"id":1,"result":{"result":{"value":true}}}'),
    )
    _cdp._runtime_evaluate_method.cache_clear()
    try:
        assert _cdp._runtime_evaluate_method() == expected
        assert _cdp.observe_markers(
            "ws://127.0.0.1:9225/" + "dev" + "tools/page/SYNTHETIC",
            ("header",),
            _ROLE_MARKERS,
            expected_host="127.0.0.1",
            expected_port=9225,
        ) is True
        assert len(sent) == 1
        assert sent[0]["method"] == expected
    finally:
        _cdp._runtime_evaluate_method.cache_clear()
