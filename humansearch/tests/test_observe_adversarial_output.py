import pytest

from humansearch import observe
from humansearch.auth_surface import AuthSurfaceState, SurfaceObservation

# 포털 주소는 코드가 아니라 contracts/ 데이터다 (P22 · G3).
# 시험이라고 예외를 두면 게이트가 막으려던 값이 제품 코드에 다시 박힌다.
ORIGIN = min(observe._load_contract("saramin").allowed_origins)


def test_read_failure_cannot_emit_unknown_with_an_invalid_contract(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def failed_read(channel: str, port: int) -> tuple[
        AuthSurfaceState, str, SurfaceObservation
    ]:
        raise observe.ObservationError("read unavailable")

    monkeypatch.setattr(observe, "observe_once", failed_read)

    exit_code = observe.main(
        ["--channel", "saramin", "--port", "9225", "--once"]
    )

    assert exit_code == 2
    assert capsys.readouterr().out == (
        "STATE=drifted TAB=- ROLES=0 CONTRACT_VALID=false\n"
    )


def test_unapproved_path_identifier_is_redacted() -> None:
    safe_url = observe._privacy_reduced_url(
        f"{ORIGIN}/candidates/CANDIDATE-123?account=private"
    )

    assert safe_url == f"{ORIGIN}/..."
    assert "CANDIDATE-123" not in safe_url


def test_approved_static_path_is_preserved() -> None:
    safe_url = observe._privacy_reduced_url(
        f"{ORIGIN}/home?account=private#fragment",
        frozenset({"/home"}),
    )

    assert safe_url == f"{ORIGIN}/home"
