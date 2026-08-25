"""WU12 — 목표 탭 선택은 목록 안 위치와 무관하다 (브라우저 계약 §7).

V1 최종 회차가 변조 하나를 냈다: `for candidate in targets:` → `for candidate in targets[:32]:`
가 모든 시험을 통과한다. 어떤 시험도 타깃을 32개 넘게 주지 않았기 때문이다.

이 지적은 **코드 결함이 아니라 시험 표본 크기**를 가리킨다. 그리고 이런 모양의 변조(임의 상수로
자르기)는 원리적으로 무한하다 — 내가 N 개를 덮으면 N+1 을 고르면 된다. 상수를 쫓는 대신
**계약이 요구하는 성질 자체**를 고정한다.

브라우저 계약 §7: *"제목, 탭 순서, 최근 활성 시각, URL의 부분 일치, 과거 target id, 이전 작업의
탭 번호로 하나를 추측하지 않는다."* 즉 승인된 탭이 목록 어디에 있든 결과가 같아야 한다. 그것이
여기서 검사하는 성질이고, 그 성질이 참이면 어떤 상수 절단도 반례가 된다.
"""

from hypothesis import given, settings
from hypothesis import strategies as st

from humansearch import observe

_ALLOWED = frozenset({"https://portal.invalid"})
_APPROVED = {
    "type": "page",
    "url": "https://portal.invalid/home",
    "webSocketDebuggerUrl": "read-endpoint-one",
}


def _decoy(index: int) -> dict[str, object]:
    """승인 origin 이 아닌 page 타깃. 후보가 되어서는 안 된다."""

    return {
        "type": "page",
        "url": f"https://other-{index}.invalid/home",
        "webSocketDebuggerUrl": f"read-endpoint-decoy-{index}",
    }


@settings(max_examples=200, deadline=None)
@given(before=st.integers(min_value=0, max_value=80), after=st.integers(min_value=0, max_value=80))
def test_the_approved_tab_is_found_at_any_position(before: int, after: int) -> None:
    targets: list[object] = [_decoy(i) for i in range(before)]
    targets.append(_APPROVED)
    targets.extend(_decoy(100 + i) for i in range(after))

    target = observe.select_single_target(targets, _ALLOWED)

    assert target.url == "https://portal.invalid/home"
    assert target.websocket_url == "read-endpoint-one"


@settings(max_examples=100, deadline=None)
@given(count=st.integers(min_value=2, max_value=40), gap=st.integers(min_value=1, max_value=60))
def test_two_approved_tabs_are_refused_however_far_apart(count: int, gap: int) -> None:
    """두 개 이상이면 거리와 무관하게 거부한다 — 뒤쪽을 못 보고 통과하면 안 된다."""

    targets: list[object] = []
    for i in range(count):
        targets.append(
            {
                "type": "page",
                "url": "https://portal.invalid/home",
                "webSocketDebuggerUrl": f"read-endpoint-{i}",
            }
        )
        targets.extend(_decoy(1000 + i * gap + j) for j in range(gap))

    try:
        observe.select_single_target(targets, _ALLOWED)
    except observe.TargetSelectionError as caught:
        assert f"found {count}" in str(caught)
    else:  # pragma: no cover - 통과하면 그 자체가 결함이다
        raise AssertionError("두 개 이상인데 하나를 골랐다")
