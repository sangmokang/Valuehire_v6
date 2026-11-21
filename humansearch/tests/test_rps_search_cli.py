import base64
import json
import os
from dataclasses import dataclass, field
from pathlib import Path

import pytest

from humansearch import rps_search_port
from humansearch._aside_repl import ReplCommand, build_repl_source
from humansearch.auth_surface import AuthSurfaceState
from humansearch.rps_search import (
    SearchResult,
    execute_search,
    main,
)
from humansearch.rps_search_contract import RpsSurface, RpsTarget, SearchPlan, SearchStatus
from humansearch.rps_search_driver import RpsTransportError
from humansearch.rps_search_port import AsideRpsPort, RpsResultTimeout

_PNG = b"\x89PNG\r\n\x1a\nvertical-slice"


def plan() -> SearchPlan:
    return SearchPlan.from_mapping(
        {
            "position_ref": "position-123",
            "project_ref": "project-456",
            "keywords": ["backend", "distributed systems"],
            "job_titles": ["Backend Engineer"],
            "network": ["1st", "2nd"],
            "seniority": ["Senior"],
            "locations": ["South Korea"],
        }
    )


def target() -> dict[str, object]:
    return {
        "type": "page",
        "url": "https://www.linkedin.com/talent/hire/project-456/discover/recruiterSearch",
        "targetId": "target-1",
    }


@dataclass
class FakeSearchPort:
    result_count: int = 127
    result_error: Exception | None = None
    screenshot: bytes = _PNG
    screenshot_error: Exception | None = None
    calls: list[tuple[object, ...]] = field(default_factory=list)

    def list_targets(self) -> list[object]:
        self.calls.append(("list_targets",))
        return [target()]

    def attach(self, selected: RpsTarget) -> None:
        self.calls.append(("attach", selected.target_id))

    def observe_surface(self) -> RpsSurface:
        self.calls.append(("observe_surface",))
        return RpsSurface(
            auth_state=AuthSurfaceState.AUTHENTICATED,
            contract_valid=True,
            session_conflict=False,
            project_ref="project-456",
        )

    def prepare_search(self) -> None:
        self.calls.append(("prepare_search",))

    def input_filter(self, field_name: str, value: str, delay_ms: int) -> None:
        self.calls.append(("input", field_name, value, delay_ms))

    def read_filter(
        self, field_name: str, expected: tuple[str, ...], attempt: int
    ) -> tuple[str, ...]:
        self.calls.append(("read", field_name, attempt))
        return expected

    def submit_search(self) -> None:
        self.calls.append(("submit",))

    def wait_result_count(self) -> int:
        self.calls.append(("wait_results",))
        if self.result_error is not None:
            raise self.result_error
        return self.result_count

    def capture_screenshot(self) -> bytes:
        self.calls.append(("screenshot",))
        if self.screenshot_error is not None:
            raise self.screenshot_error
        return self.screenshot

    def close(self) -> None:
        self.calls.append(("close",))


def test_search_completes_only_after_result_and_local_screenshot(tmp_path: Path) -> None:
    fake = FakeSearchPort()

    result = execute_search(
        plan(), fake, artifacts_dir=tmp_path, run_id="run-1"
    )

    expected_path = tmp_path / "run-1.png"
    assert result == SearchResult(
        status=SearchStatus.COMPLETED,
        position_ref="position-123",
        filters_verified=True,
        result_count=127,
        screenshot_path=str(expected_path),
    )
    assert expected_path.read_bytes() == _PNG
    assert fake.calls[-3:] == [("submit",), ("wait_results",), ("screenshot",)]


def test_zero_results_is_completed_not_a_render_failure(tmp_path: Path) -> None:
    result = execute_search(
        plan(), FakeSearchPort(result_count=0), artifacts_dir=tmp_path, run_id="zero"
    )

    assert result.status is SearchStatus.COMPLETED
    assert result.result_count == 0


def test_loading_timeout_does_not_claim_completion_or_take_screenshot(tmp_path: Path) -> None:
    fake = FakeSearchPort(result_error=RpsResultTimeout("still loading"))

    result = execute_search(plan(), fake, artifacts_dir=tmp_path, run_id="timeout")

    assert result.status is SearchStatus.FAILED
    assert result.result_count is None
    assert ("screenshot",) not in fake.calls
    assert not list(tmp_path.glob("*.png"))


def test_screenshot_failure_does_not_claim_completion(tmp_path: Path) -> None:
    fake = FakeSearchPort(screenshot_error=OSError("disk unavailable"))

    result = execute_search(plan(), fake, artifacts_dir=tmp_path, run_id="failed-shot")

    assert result.status is SearchStatus.FAILED
    assert result.result_count == 127
    assert result.screenshot_path is None


def test_screenshot_retention_keeps_latest_twenty_only(tmp_path: Path) -> None:
    for index in range(20):
        screenshot = tmp_path / f"old-{index:02d}.png"
        screenshot.write_bytes(_PNG)
        os.utime(screenshot, (index + 1, index + 1))
    keep = tmp_path / "keep.txt"
    keep.write_text("not an artifact", encoding="utf-8")

    result = execute_search(
        plan(), FakeSearchPort(), artifacts_dir=tmp_path, run_id="newest"
    )

    assert result.status is SearchStatus.COMPLETED
    assert len(list(tmp_path.glob("*.png"))) == 20
    assert not (tmp_path / "old-00.png").exists()
    assert keep.exists()


def test_default_screenshot_directory_is_gitignored() -> None:
    gitignore = Path(__file__).resolve().parents[2] / ".gitignore"

    assert "/.artifacts/" in gitignore.read_text(encoding="utf-8").splitlines()


def test_cli_prints_one_privacy_reduced_json_object(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    payload_path = tmp_path / "plan.json"
    payload_path.write_text(
        json.dumps(
            {
                "position_ref": "position-123",
                "project_ref": "project-456",
                "keywords": ["backend"],
                "job_titles": ["Backend Engineer"],
                "network": ["1st"],
                "seniority": ["Senior"],
                "locations": ["South Korea"],
            }
        ),
        encoding="utf-8",
    )
    fake = FakeSearchPort()

    exit_code = main(
        ["--plan", str(payload_path)],
        port_factory=lambda: fake,
        artifacts_dir=tmp_path,
        run_id_factory=lambda: "cli-run",
    )

    output = capsys.readouterr().out.splitlines()
    assert exit_code == 0
    assert len(output) == 1
    assert json.loads(output[0]) == {
        "status": "completed",
        "position_ref": "position-123",
        "filters_verified": True,
        "result_count": 127,
        "screenshot_path": str(tmp_path / "cli-run.png"),
    }
    assert fake.calls[-1] == ("close",)


@dataclass
class FakeReplClient:
    screenshot: bytes = _PNG
    screenshot_format: str = "png"
    result_render_error: bool = False
    calls: list[tuple[ReplCommand, dict[str, object]]] = field(default_factory=list)

    def execute(self, command: ReplCommand, payload: dict[str, object]) -> object:
        self.calls.append((command, payload))
        responses: dict[ReplCommand, object] = {
            ReplCommand.LIST_TARGETS: [target()],
            ReplCommand.ATTACH: {"attached": True},
            ReplCommand.OBSERVE_SURFACE: {
                "auth_state": "authenticated",
                "contract_valid": True,
                "session_conflict": False,
                "project_ref": "project-456",
            },
            ReplCommand.PREPARE_SEARCH: {"prepared": True},
            ReplCommand.INPUT_FILTER: {"entered": True},
            ReplCommand.READ_FILTER: payload.get("expected", []),
            ReplCommand.SUBMIT: {"submitted": True},
            ReplCommand.OBSERVE_RESULTS: {
                "contract_valid": not self.result_render_error,
                "loading": False,
                "loaded": True,
                "render_error": self.result_render_error,
                "count_text": "1,234 results",
            },
            ReplCommand.CAPTURE_SCREENSHOT: {
                "data": base64.b64encode(self.screenshot).decode(),
                "format": self.screenshot_format,
            },
        }
        return responses[command]

    def close(self) -> None:
        return None


def test_real_port_maps_fixed_repl_commands_without_raw_browser_input(tmp_path: Path) -> None:
    client = FakeReplClient()
    port = AsideRpsPort(client=client, result_timeout=0.1, sleeper=lambda _: None)

    result = execute_search(plan(), port, artifacts_dir=tmp_path, run_id="wired")

    assert result.status is SearchStatus.COMPLETED
    assert result.result_count == 1_234
    commands = [command for command, _ in client.calls]
    assert commands[-2:] == [ReplCommand.OBSERVE_RESULTS, ReplCommand.CAPTURE_SCREENSHOT]
    assert all("expression" not in payload for _, payload in client.calls)


def test_screenshot_uses_aside_visual_api_without_raw_cdp() -> None:
    screenshot_source = build_repl_source(ReplCommand.CAPTURE_SCREENSHOT, {})
    all_sources = "\n".join(build_repl_source(command, {}) for command in ReplCommand)

    assert ".pdf(" in screenshot_source
    assert "annotatedScreenshot" not in screenshot_source
    assert "Page.captureScreenshot" not in all_sources
    assert "newCDPSession" not in all_sources
    assert "Page.navigate" not in all_sources
    assert "Target.createTarget" not in all_sources


def test_pdf_visual_capture_is_rendered_to_png(monkeypatch: pytest.MonkeyPatch) -> None:
    pdf = b"%PDF-1.7\nprivate-render-payload"
    client = FakeReplClient(screenshot=pdf, screenshot_format="pdf")
    rendered: list[bytes] = []

    def render_first_page(value: bytes) -> bytes:
        rendered.append(value)
        return _PNG

    monkeypatch.setattr(rps_search_port, "_render_pdf_first_page", render_first_page)
    port = AsideRpsPort(client=client)

    assert port.capture_screenshot() == _PNG
    assert rendered == [pdf]


def test_visible_linkedin_result_error_is_not_accepted_as_loaded() -> None:
    port = AsideRpsPort(client=FakeReplClient(result_render_error=True))

    with pytest.raises(RpsTransportError, match="result rendering failed"):
        port.wait_result_count()
