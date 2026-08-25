"""AC-1: 파싱 불가 탭 주소는 크래시가 아니라 후보 제외로 처리된다.

계약: docs/engineering/hs-observe-url-crash-goal-2026-08-25.md 입력 영역 표 6·7행.
`urlsplit()` 은 IPv6 미종결과 NFKC 위반 netloc 에서 `ValueError` 를 던진다. 그 예외가
프로세스 밖으로 나가면 (a) 계약된 출력 한 줄이 사라지고 (b) 종료값이 계약 밖 1 이 되며
(c) traceback 에 netloc 이 원문 그대로 실린다 — 브라우저 계약 §5·§12 위반.
"""

import pytest

from humansearch import observe
from humansearch.auth_surface import SurfaceRole

# netloc 이 NFKC 정규화를 위반한다(전각 샵). 경로에는 후보 식별자 모양의 표식을 둬서
# 어떤 출력에도 새지 않았음을 확인할 수 있게 한다.
_NFKC_BROKEN_URL = "https://portal.invalid＃drift/candidates/CANDIDATE-9?ref=private"
_IPV6_BROKEN_URL = "https://[::1/home"
_LEAK_MARKERS = ("＃drift", "CANDIDATE-9", "private", "[::1")

_ALLOWED = frozenset({"https://portal.invalid"})


def _contract() -> observe.MarkerContract:
    return observe.MarkerContract(
        channel="saramin",
        diagnostic_host="127.0.0.1",
        diagnostic_ports=frozenset({9225}),
        targets_path="/json/list",
        allowed_origins=_ALLOWED,
        loggable_paths=frozenset({"/home"}),
        surface_markers=("header",),
        role_markers={role: (f"{role.value}-marker",) for role in SurfaceRole},
    )


@pytest.mark.parametrize("broken_url", [_NFKC_BROKEN_URL, _IPV6_BROKEN_URL])
def test_unparseable_target_url_is_refused_not_crashed(broken_url: str) -> None:
    with pytest.raises(observe.TargetSelectionError) as caught:
        observe.select_single_target(
            [
                {
                    "type": "page",
                    "url": broken_url,
                    "webSocketDebuggerUrl": "read-endpoint-broken",
                }
            ],
            _ALLOWED,
        )

    assert "found 0" in str(caught.value)
    for marker in _LEAK_MARKERS:
        assert marker not in str(caught.value)


def test_unparseable_target_url_does_not_hide_the_approved_tab() -> None:
    target = observe.select_single_target(
        [
            {
                "type": "page",
                "url": _NFKC_BROKEN_URL,
                "webSocketDebuggerUrl": "read-endpoint-broken",
            },
            {
                "type": "page",
                "url": "https://portal.invalid/home",
                "webSocketDebuggerUrl": "read-endpoint-one",
            },
        ],
        _ALLOWED,
    )

    assert target.url == "https://portal.invalid/home"
    assert target.websocket_url == "read-endpoint-one"


def test_cli_reports_drift_without_echoing_the_unparseable_url(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(observe, "_load_contract", lambda channel: _contract())
    monkeypatch.setattr(
        observe,
        "_fetch_targets",
        lambda contract, port: [
            {
                "type": "page",
                "url": _NFKC_BROKEN_URL,
                "webSocketDebuggerUrl": "read-endpoint-broken",
            }
        ],
    )

    exit_code = observe.main(["--channel", "saramin", "--port", "9225", "--once"])

    captured = capsys.readouterr()
    assert exit_code == 2
    assert captured.out == "STATE=drifted TAB=- ROLES=0 CONTRACT_VALID=false\n"
    assert captured.err == ""
    for marker in _LEAK_MARKERS:
        assert marker not in captured.out
        assert marker not in captured.err
