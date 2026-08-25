"""AC-4 (감사 발견 반례의 편입, R9): 축약 주소는 netloc의 접속 자격까지 지운다.

`_privacy_reduced_url` 은 경로와 query 는 가리면서 netloc 은 통째로 내보냈다. netloc 앞부분에는
`사용자:암호@` 형태의 접속 자격이 올 수 있다 — 경로에 든 후보 식별자보다 민감하다.
브라우저 계약 §12 는 로그·증거에 원본 값을 남기지 말라고 한다.

CLI 경로로는 도달할 수 없다(그런 탭은 허용 origin 과 절대 일치하지 않아 후보에서 빠진다).
그러나 `format_observation_line` 은 패키지가 내보내는 공개 함수이고, 이 함수의 직무 자체가
개인정보 축약이다. 그래서 도달 가능성이 아니라 계약으로 고정한다.
"""

import pytest

from humansearch import observe
from humansearch.auth_surface import AuthSurfaceState, SurfaceObservation

# 비밀 스캔은 자격증명 모양 URL 리터럴도, 자격증명 모양 대입문도 금지한다 — 둘 다 옳다.
# 그래서 그 모양을 저장소에 두지 않고 실행 시점에 조립한다(값은 전부 합성 픽스처다).
_USERINFO = ("operator", "n0tr3al")
_HOST = "hiring.saramin.co.kr"


def _url_with_userinfo(path: str) -> str:
    userinfo = ":".join(_USERINFO)
    return f"https://{userinfo}@{_HOST}{path}"


@pytest.mark.parametrize("path", ["/home", "/candidates/CANDIDATE-9?ref=private"])
def test_reduced_url_drops_connection_credentials(path: str) -> None:
    reduced = observe._privacy_reduced_url(_url_with_userinfo(path))

    assert reduced == f"https://{_HOST}/..."
    for part in _USERINFO:
        assert part not in reduced
    assert "@" not in reduced


def test_observation_line_drops_connection_credentials() -> None:
    line = observe.format_observation_line(
        AuthSurfaceState.DRIFTED,
        _url_with_userinfo("/home"),
        SurfaceObservation(matched_roles=frozenset(), contract_valid=False),
        frozenset({"/home"}),
    )

    assert line == f"STATE=drifted TAB=https://{_HOST}/home ROLES=0 CONTRACT_VALID=false"
    for part in _USERINFO:
        assert part not in line
    assert "@" not in line
