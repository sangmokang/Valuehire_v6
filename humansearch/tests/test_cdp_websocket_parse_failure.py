"""R9 회귀: 전송 경계의 주소 파싱 실패도 크래시가 아니라 닫힌 거부여야 한다.

`observe.py` 의 파싱 크래시를 고치는 과정에서 `_cdp.observe_markers` 도 같은 `urlsplit`
`ValueError` 를 다룬다는 것을 발견했다. 그쪽 가드는 이미 올바르지만 **시험이 하나도 없었다**
— 같은 결함군의 미검증 경로다. 여기서 그 가드를 회귀 자산으로 고정한다.

`observe.py` 와 달리 `_cdp` 는 `SplitResult.port` 를 읽는다. `urlsplit()` 자체가 통과한 뒤에도
`.port` 는 숫자가 아닌 포트에서 `ValueError` 를 따로 던진다(실측). 두 갈래 모두 덮는다.
"""

import inspect

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


def test_runtime_evaluate_method_is_loaded_from_contract() -> None:
    if not _cdp._CDP_PROTOCOL_CONTRACT_PATH.exists():
        pytest.skip("isolated gate mutation harness does not copy the repository contract tree")
    assert _cdp._CDP_PROTOCOL_CONTRACT_PATH.exists()
    assert _cdp._runtime_evaluate_method() == "Runtime.evaluate"
    assert "Runtime.evaluate" not in inspect.getsource(_cdp)
