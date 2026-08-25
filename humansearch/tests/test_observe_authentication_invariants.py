"""WU13 — humanreview 가 찾은 무방비 불변조건을 고정한다(R9).

`humanreview` 로 선택 루프·번역기·전송 경계에 새 변조 10종을 걸었더니 5종이 살아남았다
(대조군 99 passed exit 0 기준). 그중 둘은 **보안 관련**이다 — 가드가 사라지면 로그인하지 않은
화면이 `authenticated`(종료값 0)로 보고되고, 후속 자동화가 "로그인 성공"으로 오해한다.

| 변조 | 가드가 사라지면 | 실측 |
|---|---|---|
| `if not contract_valid: return invalid` 제거 | 계약이 깨진 화면 + 인증 역할 주장 | `drifted`(2) → **`authenticated`(0)** |
| `if len(roles) != len(matched_roles)` 제거 | 같은 역할을 두 번 주장 | `drifted`(2) → **`authenticated`(0)** |

L0 계약(`docs/sot/humansearch-l0-surface-contract.md`)이 명시한 규칙이다:
*"`contract_valid` 는 ... `False`이면 역할 집합과 관계없이 구조가 바뀐 것으로 분류한다.
구조 변경을 가짜 화면 역할로 만들지 않는다."*

코드는 지금 옳다. 없던 것은 **그 옳음을 지키는 시험**이다.
"""

from collections.abc import Mapping

import pytest

from humansearch import observe
from humansearch.auth_surface import AuthSurfaceState, SurfaceRole, classify_auth_surface

_AUTHENTICATED = SurfaceRole.AUTHENTICATED_SURFACE.value


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


# --- 불변조건 1: 계약이 깨지면 어떤 역할 주장도 인증이 될 수 없다 ---------------
def test_a_broken_contract_can_never_report_authentication() -> None:
    observation = observe.observation_from_marker_payload(
        {"contract_valid": False, "matched_roles": [_AUTHENTICATED]}
    )

    assert observation.contract_valid is False
    assert observation.matched_roles == frozenset()
    state = classify_auth_surface(observation)
    assert state is AuthSurfaceState.DRIFTED
    assert observe.exit_code_for_state(state) == 2


@pytest.mark.parametrize(
    "roles",
    [
        [_AUTHENTICATED],
        [_AUTHENTICATED, SurfaceRole.HUMAN_AUTH_SURFACE.value],
        [role.value for role in SurfaceRole],
        [],
    ],
)
def test_no_role_set_survives_a_broken_contract(roles: list[str]) -> None:
    observation = observe.observation_from_marker_payload(
        {"contract_valid": False, "matched_roles": roles}
    )

    assert classify_auth_surface(observation) is AuthSurfaceState.DRIFTED


# --- 불변조건 2: 같은 역할을 두 번 주장하면 인증이 될 수 없다 -----------------
def test_a_repeated_role_claim_can_never_report_authentication() -> None:
    observation = observe.observation_from_marker_payload(
        {"contract_valid": True, "matched_roles": [_AUTHENTICATED, _AUTHENTICATED]}
    )

    assert observation.contract_valid is False
    assert observation.matched_roles == frozenset()
    state = classify_auth_surface(observation)
    assert state is AuthSurfaceState.DRIFTED
    assert observe.exit_code_for_state(state) == 2


# --- 불변조건 3: 목표 탭 후보는 문자열 주소를 가진 것만이다 --------------------
@pytest.mark.parametrize("url", [None, 1, ["https://portal.invalid/home"], {"u": "x"}])
def test_a_non_string_url_is_never_a_candidate(url: object) -> None:
    with pytest.raises(observe.TargetSelectionError, match="found 0"):
        observe.select_single_target(
            [{"type": "page", "url": url, "webSocketDebuggerUrl": "ws"}],
            frozenset({"https://portal.invalid"}),
        )


# --- 불변조건 4: 읽기 한도를 넘는 응답은 받아들이지 않는다 --------------------
class _OversizedResponse:
    status = 200

    def read(self, amount: int) -> bytes:
        # 한도(1 MiB)보다 한 바이트 크게. 한도 검사가 사라지면 이 응답이 통과한다.
        return b"[" + b" " * 1_048_575 + b"]"


class _OversizedConnection:
    def __init__(self, host: str, port: int, timeout: int) -> None:
        pass

    def request(self, method: str, path: str, headers: Mapping[str, str]) -> None:
        pass

    def getresponse(self) -> _OversizedResponse:
        return _OversizedResponse()

    def close(self) -> None:
        pass


def test_an_oversized_target_list_is_refused(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(observe, "HTTPConnection", _OversizedConnection)

    with pytest.raises(observe.ObservationError, match="exceeded the read limit"):
        observe._fetch_targets(_contract(), 9225)


# --- 불변조건 5: 주소 자리는 "문자열로 바꿔 보면" 이 아니라 "문자열인가" 다 ------
# `isinstance(url, str)` 를 `_origin(str(url))` 로 바꾸는 변조가 살아남았다.
# JSON 이 만들 수 있는 값(str·int·float·bool·None·list·dict)으로는 둘을 구분할 수 없다 —
# `str(v)` 가 https 주소 모양이 되지 않기 때문이다. 그러나 `select_single_target` 은 패키지가
# 내보내는 공개 함수이고, 임의의 파이썬 객체를 받을 수 있다. 문자열로 **보이는** 것과 문자열인
# 것을 가르는 일이 이 검사의 직무다.
class _LooksLikeAnApprovedUrl:
    def __str__(self) -> str:
        return "https://portal.invalid/home"


def test_an_object_that_merely_prints_like_a_url_is_not_a_candidate() -> None:
    assert str(_LooksLikeAnApprovedUrl()) == "https://portal.invalid/home"

    with pytest.raises(observe.TargetSelectionError, match="found 0"):
        observe.select_single_target(
            [
                {
                    "type": "page",
                    "url": _LooksLikeAnApprovedUrl(),
                    "webSocketDebuggerUrl": "ws",
                }
            ],
            frozenset({"https://portal.invalid"}),
        )
