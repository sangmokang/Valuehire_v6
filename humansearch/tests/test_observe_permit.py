import hashlib
import json
import os
import stat
import threading
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from humansearch import _cdp, observe
from humansearch.auth_surface import SurfaceRole

CHANNEL = "saramin"
HOST = "127.0.0.1"
PORT = 9225
ORIGIN = "https://portal.invalid"
TARGET_ID = "target-one"
TARGET_PROOF = hashlib.sha256(TARGET_ID.encode()).hexdigest()
LEASE_ID = "d50e07c2-8ed8-4ed4-9d96-85f19f1704cb"
DRIFTED_LINE = "STATE=drifted TAB=- ROLES=0 CONTRACT_VALID=false\n"


def _contract() -> observe.MarkerContract:
    return observe.MarkerContract(
        channel=CHANNEL,
        diagnostic_host=HOST,
        diagnostic_ports=frozenset({PORT}),
        targets_path="/json/list",
        allowed_origins=frozenset({ORIGIN}),
        loggable_paths=frozenset({"/home"}),
        surface_markers=("header",),
        role_markers={role: (role.value,) for role in SurfaceRole},
    )


def _permit_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "version": 1,
        "lease_id": LEASE_ID,
        "channel": CHANNEL,
        "diagnostic_host": HOST,
        "diagnostic_port": PORT,
        "allowed_origin": ORIGIN,
        "target_id_sha256": TARGET_PROOF,
        "expires_at": "2999-01-01T00:00:00Z",
    }
    payload.update(overrides)
    return payload


def _write_permit(
    directory: Path,
    payload: dict[str, object] | None = None,
    *,
    mode: int = 0o600,
    name: str = "permit.json",
) -> Path:
    permit = directory / name
    permit.write_text(json.dumps(payload or _permit_payload()), encoding="utf-8")
    permit.chmod(mode)
    return permit


def _install_browser(
    monkeypatch: pytest.MonkeyPatch,
    marker_read: Callable[..., object],
    *,
    target_barrier: threading.Barrier | None = None,
) -> None:
    contract = _contract()
    monkeypatch.setattr(observe, "_load_contract", lambda channel: contract)

    def fetch_targets(loaded: object, port: int) -> list[object]:
        if target_barrier is not None:
            target_barrier.wait(timeout=5)
        return [
            {
                "id": TARGET_ID,
                "type": "page",
                "url": f"{ORIGIN}/home",
                "webSocketDebuggerUrl": "read-endpoint-one",
            }
        ]

    monkeypatch.setattr(observe, "_fetch_targets", fetch_targets)
    monkeypatch.setattr(observe, "observe_markers", marker_read)


def _authenticated_payload(*args: object, **kwargs: object) -> object:
    return {
        "contract_valid": True,
        "matched_roles": [SurfaceRole.AUTHENTICATED_SURFACE.value],
    }


def _run_main(permit_file: Path | None) -> int:
    argv = ["--channel", CHANNEL, "--port", str(PORT), "--once"]
    if permit_file is not None:
        argv.extend(("--permit-file", str(permit_file)))
    return observe.main(argv)


@pytest.mark.parametrize("kind", ("missing", "expired"))
def test_missing_and_expired_permits_never_read_dom(
    kind: str,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    marker_reads = 0

    def marker_read(*args: object, **kwargs: object) -> object:
        nonlocal marker_reads
        marker_reads += 1
        return _authenticated_payload()

    _install_browser(monkeypatch, marker_read)
    permit = None
    if kind == "expired":
        permit = _write_permit(
            tmp_path,
            _permit_payload(expires_at="2000-01-01T00:00:00Z"),
        )

    assert _run_main(permit) == 2
    captured = capsys.readouterr()
    assert captured.out == DRIFTED_LINE
    assert captured.err == ""
    assert marker_reads == 0


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("channel", "jobkorea"),
        ("diagnostic_host", "127.0.0.2"),
        ("diagnostic_port", PORT + 1),
        ("allowed_origin", "https://other.invalid"),
        ("target_id_sha256", "0" * 64),
    ),
)
def test_binding_mismatch_never_reads_dom(
    field: str,
    value: object,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    marker_reads = 0

    def marker_read(*args: object, **kwargs: object) -> object:
        nonlocal marker_reads
        marker_reads += 1
        return _authenticated_payload()

    _install_browser(monkeypatch, marker_read)
    permit = _write_permit(tmp_path, _permit_payload(**{field: value}))

    assert _run_main(permit) == 2
    assert capsys.readouterr().out == DRIFTED_LINE
    assert marker_reads == 0


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("version", "1"),
        ("lease_id", "not-a-uuid"),
        ("diagnostic_port", str(PORT)),
        ("target_id_sha256", "not-a-sha256"),
        ("expires_at", "2999-01-01T09:00:00+09:00"),
        ("unexpected", True),
    ),
)
def test_malformed_permit_never_reads_dom(
    field: str,
    value: object,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    marker_reads = 0

    def marker_read(*args: object, **kwargs: object) -> object:
        nonlocal marker_reads
        marker_reads += 1
        return _authenticated_payload()

    _install_browser(monkeypatch, marker_read)
    permit = _write_permit(tmp_path, _permit_payload(**{field: value}))

    assert _run_main(permit) == 2
    assert capsys.readouterr().out == DRIFTED_LINE
    assert marker_reads == 0


def test_permit_mode_must_be_exactly_0600(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _install_browser(monkeypatch, _authenticated_payload)
    permit = _write_permit(tmp_path, mode=0o640)

    assert _run_main(permit) == 2
    assert capsys.readouterr().out == DRIFTED_LINE


def test_permit_owner_must_be_current_user(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _install_browser(monkeypatch, _authenticated_payload)
    permit = _write_permit(tmp_path)
    current_uid = os.getuid()
    monkeypatch.setattr(os, "getuid", lambda: current_uid + 1)

    assert _run_main(permit) == 2
    assert capsys.readouterr().out == DRIFTED_LINE


def test_permit_path_inside_repository_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()
    permit = _write_permit(repository)
    monkeypatch.setattr(observe, "_REPOSITORY_ROOT", repository, raising=False)
    _install_browser(monkeypatch, _authenticated_payload)

    assert _run_main(permit) == 2
    assert capsys.readouterr().out == DRIFTED_LINE


def test_permit_symlink_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    real_permit = _write_permit(tmp_path, name="real.json")
    permit_link = tmp_path / "link.json"
    permit_link.symlink_to(real_permit)
    _install_browser(monkeypatch, _authenticated_payload)

    assert _run_main(permit_link) == 2
    assert capsys.readouterr().out == DRIFTED_LINE


def test_valid_permit_reads_once_and_creates_safe_0600_sentinel(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    marker_reads = 0

    def marker_read(*args: object, **kwargs: object) -> object:
        nonlocal marker_reads
        marker_reads += 1
        return _authenticated_payload()

    _install_browser(monkeypatch, marker_read)
    permit = _write_permit(tmp_path)

    assert _run_main(permit) == 0
    assert capsys.readouterr().out == (
        f"STATE=authenticated TAB={ORIGIN}/home ROLES=1 CONTRACT_VALID=true\n"
    )
    assert marker_reads == 1
    sentinels = list(tmp_path.glob(".humansearch-permit-*.consumed"))
    assert len(sentinels) == 1
    sentinel = sentinels[0]
    assert stat.S_IMODE(sentinel.stat().st_mode) == 0o600
    assert sentinel.read_bytes() == b""
    assert LEASE_ID not in sentinel.name
    assert TARGET_ID not in sentinel.name


def test_reused_permit_never_reads_dom_again(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    marker_reads = 0

    def marker_read(*args: object, **kwargs: object) -> object:
        nonlocal marker_reads
        marker_reads += 1
        return _authenticated_payload()

    _install_browser(monkeypatch, marker_read)
    permit = _write_permit(tmp_path)

    assert _run_main(permit) == 0
    capsys.readouterr()
    assert _run_main(permit) == 2
    assert capsys.readouterr().out == DRIFTED_LINE
    assert marker_reads == 1


def test_concurrent_use_allows_at_most_one_dom_read(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    marker_reads = 0
    marker_lock = threading.Lock()
    barrier = threading.Barrier(2)

    def marker_read(*args: object, **kwargs: object) -> object:
        nonlocal marker_reads
        with marker_lock:
            marker_reads += 1
        return _authenticated_payload()

    _install_browser(monkeypatch, marker_read, target_barrier=barrier)
    permit = _write_permit(tmp_path)

    def attempt() -> bool:
        try:
            observe.observe_once(CHANNEL, PORT, permit)
        except (observe.ObservationError, TypeError):
            return False
        return True

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = [executor.submit(attempt), executor.submit(attempt)]

    assert sum(result.result() for result in results) == 1
    assert marker_reads == 1


def test_marker_failure_still_consumes_permit_without_retry(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    marker_reads = 0

    def marker_read(*args: object, **kwargs: object) -> object:
        nonlocal marker_reads
        marker_reads += 1
        raise _cdp.CdpReadError("planted read failure")

    _install_browser(monkeypatch, marker_read)
    permit = _write_permit(tmp_path)

    assert _run_main(permit) == 2
    capsys.readouterr()
    assert _run_main(permit) == 2
    assert capsys.readouterr().out == DRIFTED_LINE
    assert marker_reads == 1


def test_failure_output_never_contains_lease_or_target_identifiers(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _install_browser(monkeypatch, _authenticated_payload)
    permit = _write_permit(
        tmp_path,
        _permit_payload(target_id_sha256="0" * 64),
    )

    assert _run_main(permit) == 2
    captured = capsys.readouterr()
    assert captured.out == DRIFTED_LINE
    assert captured.err == ""
    assert LEASE_ID not in captured.out + captured.err
    assert TARGET_ID not in captured.out + captured.err
