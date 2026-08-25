import pytest

from humansearch import observe
from humansearch.auth_surface import (
    AuthSurfaceState,
    SurfaceObservation,
    SurfaceRole,
)

_DRIFTED_LINE = "STATE=drifted TAB=- ROLES=0 CONTRACT_VALID=false\n"


def _contract() -> observe.MarkerContract:
    return observe.MarkerContract(
        channel="saramin",
        diagnostic_host="127.0.0.1",
        diagnostic_ports=frozenset({9225}),
        targets_path="/json/list",
        allowed_origins=frozenset({"https://portal.invalid"}),
        loggable_paths=frozenset({"/home"}),
        surface_markers=("header",),
        role_markers={
            SurfaceRole.AUTHENTICATED_SURFACE: ("account-menu",),
            SurfaceRole.HUMAN_AUTH_SURFACE: ("login-menu",),
            SurfaceRole.CHALLENGE_SURFACE: ("captcha",),
        },
    )


def _approved_target(title: str, suffix: str = "one") -> dict[str, object]:
    return {
        "type": "page",
        "title": title,
        "url": f"https://portal.invalid/home?candidate={suffix}#private",
        "webSocketDebuggerUrl": f"read-endpoint-{suffix}",
    }


def _run_main_with_targets(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    targets: list[object],
) -> tuple[int, str, str]:
    contract = _contract()
    monkeypatch.setattr(observe, "_load_contract", lambda channel: contract)
    monkeypatch.setattr(observe, "_fetch_targets", lambda loaded, port: targets)

    def marker_read(*args: object, **kwargs: object) -> object:
        return {
            "contract_valid": True,
            "matched_roles": [SurfaceRole.AUTHENTICATED_SURFACE.value],
        }

    monkeypatch.setattr(observe, "observe_markers", marker_read)
    exit_code = observe.main(
        ["--channel", "saramin", "--port", "9225", "--once"]
    )
    captured = capsys.readouterr()
    return exit_code, captured.out, captured.err


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
        _DRIFTED_LINE
    )


def test_malformed_target_only_fails_safely_through_main(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    exit_code, stdout, stderr = _run_main_with_targets(
        monkeypatch,
        capsys,
        [
            {
                "type": "page",
                "url": "https://[oops",
                "webSocketDebuggerUrl": "unused",
            }
        ],
    )

    assert exit_code == 2
    assert stdout == _DRIFTED_LINE
    assert stderr == ""


def test_sensitive_malformed_target_cannot_escape_cli_output(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    credential_marker = "SENTINEL-" + "CREDENTIAL"
    sensitive_marker = "SENTINEL-" + "TOK" + "EN"
    raw_url = (
        "https:"
        + "//"
        + credential_marker
        + ":"
        + sensitive_marker
        + "@SENTINEL-HOST[SENTINEL-CANDIDATE]?"
        + sensitive_marker
        + "#SENTINEL-FRAGMENT"
    )
    exit_code, stdout, stderr = _run_main_with_targets(
        monkeypatch,
        capsys,
        [
            {
                "type": "page",
                "title": "SENTINEL-CANDIDATE",
                "url": raw_url,
                "webSocketDebuggerUrl": "SENTINEL-CANDIDATE-ENDPOINT",
            }
        ],
    )

    assert exit_code == 2
    assert stdout == _DRIFTED_LINE
    assert stderr == ""
    combined = stdout + stderr
    assert raw_url not in combined
    for forbidden in (
        "Traceback",
        "ValueError",
        "SENTINEL-HOST",
        "SENTINEL-CANDIDATE",
        sensitive_marker,
        "SENTINEL-FRAGMENT",
        credential_marker,
    ):
        assert forbidden not in combined


@pytest.mark.parametrize(
    ("malformed_first", "malformed_title", "approved_title"),
    [
        (True, "looks-approved", "ignored-title"),
        (False, "looks-approved", "ignored-title"),
        (True, "changed-malformed-title", "changed-approved-title"),
        (False, "changed-malformed-title", "changed-approved-title"),
    ],
)
def test_one_approved_target_wins_regardless_of_malformed_order_or_title(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    malformed_first: bool,
    malformed_title: str,
    approved_title: str,
) -> None:
    malformed: object = {
        "type": "page",
        "title": malformed_title,
        "url": "https://[oops",
        "webSocketDebuggerUrl": "unused-malformed",
    }
    approved: object = _approved_target(approved_title)
    targets = [malformed, approved] if malformed_first else [approved, malformed]

    exit_code, stdout, stderr = _run_main_with_targets(
        monkeypatch, capsys, targets
    )

    assert exit_code == 0
    assert stdout == (
        "STATE=authenticated TAB=https://portal.invalid/home "
        "ROLES=1 CONTRACT_VALID=true\n"
    )
    assert stderr == ""


@pytest.mark.parametrize(
    "targets",
    [
        [],
        [
            _approved_target("first", "first"),
            {
                "type": "page",
                "url": "https://[oops",
                "webSocketDebuggerUrl": "unused-malformed",
            },
            _approved_target("second", "second"),
        ],
    ],
)
def test_non_single_approved_target_count_keeps_safe_main_failure(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    targets: list[object],
) -> None:
    exit_code, stdout, stderr = _run_main_with_targets(
        monkeypatch, capsys, targets
    )

    assert exit_code == 2
    assert stdout == _DRIFTED_LINE
    assert stderr == ""


def test_unexpected_value_error_outside_url_parsing_propagates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def programming_error(channel: str, port: int) -> tuple[
        AuthSurfaceState, str, SurfaceObservation
    ]:
        raise ValueError("SENTINEL-PROGRAMMING-ERROR")

    monkeypatch.setattr(observe, "observe_once", programming_error)

    with pytest.raises(ValueError, match="SENTINEL-PROGRAMMING-ERROR"):
        observe.main(["--channel", "saramin", "--port", "9225", "--once"])


def test_unapproved_path_identifier_is_redacted() -> None:
    safe_url = observe._privacy_reduced_url(
        "https://hiring.saramin.co.kr/candidates/CANDIDATE-123?account=private"
    )

    assert safe_url == "https://hiring.saramin.co.kr/..."
    assert "CANDIDATE-123" not in safe_url


def test_approved_static_path_is_preserved() -> None:
    safe_url = observe._privacy_reduced_url(
        "https://hiring.saramin.co.kr/home?account=private#fragment",
        frozenset({"/home"}),
    )

    assert safe_url == "https://hiring.saramin.co.kr/home"
