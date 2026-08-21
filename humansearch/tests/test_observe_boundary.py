import hashlib
import inspect
import json
from pathlib import Path

import pytest
from hypothesis import given
from hypothesis import strategies as st

from humansearch import _cdp, observe
from humansearch.auth_surface import AuthSurfaceState, SurfaceRole


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


def test_cdp_boundary_cannot_accept_an_arbitrary_expression() -> None:
    assert not hasattr(_cdp, "evaluate_expression")
    parameters = inspect.signature(_cdp.observe_markers).parameters
    assert "expression" not in parameters
    assert set(parameters) == {
        "websocket_url",
        "surface_markers",
        "role_markers",
        "expected_host",
        "expected_port",
        "timeout",
    }


def test_any_numeric_loopback_host_is_valid_contract_data(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    raw = {
        "channel": "saramin",
        "diagnostic_host": "127.0.0.2",
        "diagnostic_ports": [9225],
        "targets_path": "/json/list",
        "allowed_origins": ["https://portal.invalid"],
        "loggable_paths": ["/home"],
        "surface_markers": ["header"],
        "role_markers": {
            role.value: [f"{role.value}-marker"] for role in SurfaceRole
        },
    }
    contract_path = tmp_path / "saramin-markers.json"
    contract_path.write_text(json.dumps(raw), encoding="utf-8")
    monkeypatch.setattr(observe, "_CONTRACT_PATH", contract_path)

    assert observe._load_contract("saramin").diagnostic_host == "127.0.0.2"


@given(roles=st.sets(st.sampled_from(tuple(SurfaceRole))))
def test_valid_marker_role_payloads_translate_without_loss(
    roles: set[SurfaceRole],
) -> None:
    observation = observe.observation_from_marker_payload(
        {
            "contract_valid": True,
            "matched_roles": [role.value for role in roles],
        }
    )

    assert observation.contract_valid is True
    assert observation.matched_roles == frozenset(roles)


@given(state=st.sampled_from(tuple(AuthSurfaceState)))
def test_only_authenticated_state_has_success_exit(state: AuthSurfaceState) -> None:
    expected = 0 if state is AuthSurfaceState.AUTHENTICATED else 2
    assert observe.exit_code_for_state(state) == expected


def test_exactly_one_matching_target_is_returned() -> None:
    target = observe.select_single_target(
        [
            {"type": "worker", "url": "https://portal.invalid/background"},
            {
                "id": "target-one",
                "type": "page",
                "url": "https://portal.invalid/home",
                "webSocketDebuggerUrl": "read-endpoint-one",
            },
        ],
        frozenset({"https://portal.invalid"}),
    )

    assert target.url == "https://portal.invalid/home"
    assert target.websocket_url == "read-endpoint-one"
    assert target.target_id_sha256 == hashlib.sha256(b"target-one").hexdigest()


def test_observe_once_uses_the_narrow_marker_adapter(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    contract = _contract()
    calls: list[tuple[object, ...]] = []
    permit_path = tmp_path / "permit.json"
    permit_path.write_text(
        json.dumps(
            {
                "version": 1,
                "lease_id": "d50e07c2-8ed8-4ed4-9d96-85f19f1704cb",
                "channel": "saramin",
                "diagnostic_host": "127.0.0.1",
                "diagnostic_port": 9225,
                "allowed_origin": "https://portal.invalid",
                "target_id_sha256": hashlib.sha256(b"target-one").hexdigest(),
                "expires_at": "2999-01-01T00:00:00Z",
            }
        ),
        encoding="utf-8",
    )
    permit_path.chmod(0o600)
    monkeypatch.setattr(observe, "_load_contract", lambda channel: contract)
    monkeypatch.setattr(
        observe,
        "_fetch_targets",
        lambda loaded, port: [
            {
                "id": "target-one",
                "type": "page",
                "url": "https://portal.invalid/home?ignored=yes",
                "webSocketDebuggerUrl": "read-endpoint-one",
            }
        ],
    )

    def marker_read(*args: object, **kwargs: object) -> object:
        calls.append((*args, kwargs))
        return {
            "contract_valid": True,
            "matched_roles": [SurfaceRole.AUTHENTICATED_SURFACE.value],
        }

    monkeypatch.setattr(observe, "observe_markers", marker_read)

    state, tab_url, observation = observe.observe_once(
        "saramin", 9225, permit_path
    )

    assert state is AuthSurfaceState.AUTHENTICATED
    assert tab_url == "https://portal.invalid/home"
    assert observation.matched_roles == frozenset(
        {SurfaceRole.AUTHENTICATED_SURFACE}
    )
    assert len(calls) == 1
