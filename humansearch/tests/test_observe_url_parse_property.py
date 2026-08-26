"""AC-2: 주소 파싱은 한 곳이 소유하고, 어떤 입력에도 예외를 밖으로 내보내지 않는다.

계약: docs/engineering/hs-observe-url-crash-goal-2026-08-25.md 입력 영역 표 8행(catch-all).
WU1 은 목표 탭 선택 경로만 막았다. 계약 JSON 의 허용 origin 검사와 출력 축약은 여전히
`urlsplit()` 을 감싸지 않고 부른다 — 같은 결함의 남은 두 입구다. P5② 에 따라 순수 판정
함수는 속성 기반 시험으로 전수 성질을 증명한다.
"""

import json
from pathlib import Path

import pytest
from hypothesis import example, given
from hypothesis import strategies as st

from humansearch import observe
from humansearch.auth_surface import AuthSurfaceState, SurfaceObservation, SurfaceRole

_NFKC_BROKEN_ORIGIN = "https://portal.invalid＃drift"
_NFKC_BROKEN_URL = "https://portal.invalid＃drift/candidates/CANDIDATE-9?ref=private"


def _raw_contract(allowed_origins: list[str]) -> dict[str, object]:
    return {
        "channel": "saramin",
        "diagnostic_host": "127.0.0.1",
        "diagnostic_ports": [9225],
        "targets_path": "/json/list",
        "allowed_origins": allowed_origins,
        "loggable_paths": ["/home"],
        "surface_markers": ["header"],
        "role_markers": {role.value: [f"{role.value}-marker"] for role in SurfaceRole},
    }


def test_unparseable_allowed_origin_is_a_closed_contract_failure(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    contract_path = tmp_path / "saramin-markers.json"
    contract_path.write_text(
        json.dumps(_raw_contract([_NFKC_BROKEN_ORIGIN])), encoding="utf-8"
    )
    monkeypatch.setattr(observe, "_CONTRACT_PATH", contract_path)

    with pytest.raises(observe.ObservationError, match="allowed origin contract"):
        observe._load_contract("saramin")


def test_unparseable_tab_url_renders_as_no_tab() -> None:
    line = observe.format_observation_line(
        AuthSurfaceState.DRIFTED,
        _NFKC_BROKEN_URL,
        SurfaceObservation(matched_roles=frozenset(), contract_valid=False),
    )

    assert line == "STATE=drifted TAB=- ROLES=0 CONTRACT_VALID=false"
    for marker in ("＃drift", "CANDIDATE-9", "private"):
        assert marker not in line


# 평범한 `st.text()` 만으로는 이 결함 영역에 닿지 못한다 — 실측 결과 수정 전 코드에서도
# 통과했다. 그래서 주소 모양을 직접 조립하고, NFKC 정규화를 깨뜨리는 전각 문자와 IPv6
# 대괄호를 알파벳에 넣는다. 알려진 반례 두 개는 `@example` 로 못 박아 전략 튜닝과 무관하게
# 항상 실행되게 한다.
_RISKY_ALPHABET = "ab.-:[]@?#/＃／：＠？℀"
_ADDRESSES = st.builds(
    lambda scheme, netloc, rest: f"{scheme}{netloc}{rest}",
    st.sampled_from(("https://", "http://", "https:/", "//", "")),
    st.text(alphabet=_RISKY_ALPHABET, max_size=12),
    st.sampled_from(("", "/home", "/candidates/CANDIDATE-9?ref=private", "#frag")),
)
_ANY_ADDRESS = st.one_of(st.text(), _ADDRESSES)


@given(url=_ANY_ADDRESS)
@example(url=_NFKC_BROKEN_URL)
@example(url="https://[::1/home")
def test_no_text_input_can_make_address_parsing_raise(url: str) -> None:
    origin = observe._origin(url)
    valid = observe._valid_origin(url)
    reduced = observe._privacy_reduced_url(url)

    assert origin == "" or origin.startswith("https://")
    assert valid is False or origin != ""
    assert "?" not in reduced
    assert "#" not in reduced


@given(url=_ANY_ADDRESS)
@example(url=_NFKC_BROKEN_URL)
@example(url="https://[::1/home")
def test_reduced_output_never_carries_an_unapproved_path(url: str) -> None:
    reduced = observe._privacy_reduced_url(url)

    assert reduced == "" or reduced.endswith("/...")
