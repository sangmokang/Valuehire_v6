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

from collections.abc import Iterator, Sequence
from typing import cast

import pytest
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
@given(
    before=st.integers(min_value=0, max_value=200),
    after=st.integers(min_value=0, max_value=80),
)
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

    # 계약이 요구하는 것은 "거부한다"이지 "몇 개라고 세어서 말한다"가 아니다. 내부 계수 문구를
    # 단언하면 계수가 틀려도 통과하는 변조를 못 잡고, 문구만 바꿔도 시험이 깨진다(Codex 지적).
    with pytest.raises(observe.TargetSelectionError):
        observe.select_single_target(targets, _ALLOWED)


# --- 무한한 절단 변조군을 한 번에 막는다 ---------------------------------------
# `targets[:32]` 를 시험으로 잡으면 `targets[:64]` 가, 그것을 잡으면 `targets[:250]` 이
# 살아남는다(실측: 32·100·160 은 죽고 250 은 생존). 어떤 유한한 표본도 이 변조군 전체를
# 죽일 수 없다.
#
# 그래서 상수가 아니라 **"선택은 목록 전체를 본다"**를 기계로 고정한다. 이것은 의도적으로
# 구현 모양을 제약한다 — 잘라 보는 구현을 금지한다. 브라우저 계약 §7 의 "탭 순서로 하나를
# 추측하지 않는다"를 기계가 검사할 수 있는 형태로 옮긴 것이고, 대안(상수 쫓기)이 원리적으로
# 끝나지 않기 때문에 이 대가를 받아들인다.
class _IterationOnly:
    """반복만 허용하는 목표 목록. 잘라 읽으려 하면 그 자리에서 실패한다.

    `select_single_target` 은 `for candidate in targets:` 로만 목록을 쓴다. 잘라 읽는 구현은
    `__getitem__` 을 부르는데 이 객체에는 그것이 없으므로 `TypeError` 로 즉시 드러난다.
    """

    def __init__(self, items: Sequence[object]) -> None:
        self._items = items

    def __iter__(self) -> Iterator[object]:
        return iter(self._items)

    def __len__(self) -> int:
        return len(self._items)


def test_selection_reads_the_whole_target_list() -> None:
    targets = _IterationOnly(
        [_decoy(i) for i in range(300)] + [_APPROVED] + [_decoy(1000 + i) for i in range(50)]
    )

    target = observe.select_single_target(cast("Sequence[object]", targets), _ALLOWED)

    assert target.url == "https://portal.invalid/home"
