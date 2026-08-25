"""WU14 — 거부값이 허용값과 충돌해서는 안 된다 (Codex 적대 검증 1번 지적, R9).

`_origin()` 은 거부를 빈 문자열로 표현한다. `select_single_target` 은 그 결과를 허용목록과
그냥 비교한다. 허용목록에 빈 문자열이 들어 있으면 **거부가 곧 허용이 된다** — 파싱조차 못 한
주소가 목표 탭으로 선택되고, 반환 객체가 원문 주소를 그대로 들고 나온다.

계약 파일로는 그 상태에 도달할 수 없다. `_string_list()` 와 `_valid_origin()` 이 각각 빈
문자열을 막는다(실측 둘 다 False). 하지만 `select_single_target` 은 패키지가 내보내는 공개
함수이고, **거부를 나타내는 값이 허용 판정에 그대로 쓰이는 구조 자체**가 결함이다. 두 겹의
방어 중 하나가 미래에 느슨해지면 이 구멍이 곧바로 열린다.

WU4(축약 주소의 접속 자격 누출)와 같은 모양이다 — CLI 경로 도달 불가, 공개 API 도달 가능,
그리고 하필 그 함수의 직무가 거부다.
"""

import pytest

from humansearch import observe

# NFKC 정규화를 깨뜨리는 전각 골뱅이. `_origin()` 이 파싱에 실패해 빈 문자열을 돌려준다.
_UNPARSEABLE_URL = "https://CANDIDATE-9＠hiring.saramin.co.kr/home?ref=private"


def test_the_refusal_value_is_never_treated_as_an_allowed_origin() -> None:
    assert observe._origin(_UNPARSEABLE_URL) == ""  # 거부값이 빈 문자열임을 못 박는다

    with pytest.raises(observe.TargetSelectionError, match="found 0"):
        observe.select_single_target(
            [
                {
                    "type": "page",
                    "url": _UNPARSEABLE_URL,
                    "webSocketDebuggerUrl": "read-endpoint-broken",
                }
            ],
            frozenset({""}),
        )


@pytest.mark.parametrize(
    "allowed",
    [frozenset({""}), frozenset({"", "https://portal.invalid"}), frozenset({"", "http://x"})],
)
def test_an_empty_allowed_origin_never_matches_anything(allowed: frozenset[str]) -> None:
    """허용목록에 빈 문자열이 섞여 있어도, 파싱 실패한 주소는 후보가 되지 않는다."""

    for url in (_UNPARSEABLE_URL, "https://[::1/home", "not-a-url", "", "ftp://h/x"):
        with pytest.raises(observe.TargetSelectionError, match="found 0"):
            observe.select_single_target(
                [{"type": "page", "url": url, "webSocketDebuggerUrl": "ws"}], allowed
            )


def test_a_real_origin_still_matches_when_the_allowlist_also_holds_the_sentinel() -> None:
    """거부값을 제외하는 것이 정상 일치까지 막아서는 안 된다."""

    target = observe.select_single_target(
        [
            {
                "type": "page",
                "url": "https://portal.invalid/home",
                "webSocketDebuggerUrl": "read-endpoint-one",
            }
        ],
        frozenset({"", "https://portal.invalid"}),
    )

    assert target.url == "https://portal.invalid/home"


def test_the_contract_file_cannot_introduce_the_sentinel() -> None:
    """두 겹의 방어가 지금도 살아 있는지 함께 고정한다."""

    assert observe._valid_origin("") is False
    assert observe._string_list([""]) is False
    assert observe._string_list(["https://portal.invalid", ""]) is False
