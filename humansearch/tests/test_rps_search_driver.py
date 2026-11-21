from dataclasses import dataclass, field

import pytest

from humansearch._aside_repl import ReplCommand, build_repl_source
from humansearch.auth_surface import AuthSurfaceState
from humansearch.rps_search_contract import RpsSurface, RpsTarget, SearchPlan, SearchStatus
from humansearch.rps_search_driver import (
    FilterExecution,
    RpsDriftError,
    deterministic_delay_ms,
    load_rps_ui_contract,
    run_verified_filters,
)


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


def target(project_ref: str = "project-456", target_id: str = "target-1") -> dict[str, object]:
    return {
        "type": "page",
        "url": f"https://www.linkedin.com/talent/hire/{project_ref}/discover/recruiterSearch",
        "targetId": target_id,
    }


def surface(
    *,
    auth_state: AuthSurfaceState = AuthSurfaceState.AUTHENTICATED,
    contract_valid: bool = True,
    session_conflict: bool = False,
    project_ref: str | None = "project-456",
) -> RpsSurface:
    return RpsSurface(
        auth_state=auth_state,
        contract_valid=contract_valid,
        session_conflict=session_conflict,
        project_ref=project_ref,
    )


@dataclass
class FakePort:
    targets: list[object] = field(default_factory=lambda: [target()])
    observed_surface: RpsSurface = field(default_factory=surface)
    readback_sequences: dict[str, list[tuple[str, ...]]] = field(default_factory=dict)
    drift_field: str | None = None
    calls: list[tuple[object, ...]] = field(default_factory=list)
    attached: RpsTarget | None = None
    prepared: int = 0
    submitted: int = 0

    def list_targets(self) -> list[object]:
        self.calls.append(("list_targets",))
        return self.targets

    def attach(self, selected: RpsTarget) -> None:
        self.calls.append(("attach", selected.target_id))
        self.attached = selected

    def observe_surface(self) -> RpsSurface:
        self.calls.append(("observe_surface",))
        return self.observed_surface

    def prepare_search(self) -> None:
        self.calls.append(("prepare_search",))
        self.prepared += 1

    def input_filter(self, field_name: str, value: str, delay_ms: int) -> None:
        self.calls.append(("input", field_name, value, delay_ms))
        if field_name == self.drift_field:
            raise RpsDriftError(field_name)

    def read_filter(
        self, field_name: str, expected: tuple[str, ...], attempt: int
    ) -> tuple[str, ...]:
        self.calls.append(("read", field_name, attempt))
        queued = self.readback_sequences.get(field_name)
        if queued:
            return queued.pop(0)
        return expected

    def submit_search(self) -> None:
        self.calls.append(("submit",))
        self.submitted += 1


def test_verified_filters_are_applied_in_order_and_submitted_once() -> None:
    fake = FakePort()

    result = run_verified_filters(plan(), fake)

    assert result == FilterExecution(status=None, filters_verified=True, submitted=True)
    assert fake.submitted == 1
    assert fake.prepared == 1
    inputs = [(call[1], call[2]) for call in fake.calls if call[0] == "input"]
    assert inputs == [
        ("keywords", "backend AND distributed systems"),
        ("job_titles", "Backend Engineer"),
        ("network", "1st"),
        ("network", "2nd"),
        ("seniority", "Senior"),
        ("locations", "South Korea"),
    ]
    assert fake.calls[-1] == ("submit",)


@pytest.mark.parametrize(
    "fake",
    [
        FakePort(targets=[]),
        FakePort(targets=[target(), target(target_id="target-2")]),
        FakePort(observed_surface=surface(auth_state=AuthSurfaceState.CHALLENGE)),
        FakePort(observed_surface=surface(session_conflict=True)),
        FakePort(observed_surface=surface(project_ref="other-project")),
    ],
)
def test_preflight_failure_sends_no_filter_or_submit_commands(fake: FakePort) -> None:
    result = run_verified_filters(plan(), fake)

    assert result.status is not None
    assert not any(call[0] in {"input", "submit"} for call in fake.calls)


def test_field_readback_mismatch_blocks_later_fields_and_submit() -> None:
    fake = FakePort(readback_sequences={"keywords": [(), (), ()]})

    result = run_verified_filters(plan(), fake)

    assert result.status is SearchStatus.FILTER_MISMATCH
    assert result.filters_verified is False
    assert fake.submitted == 0
    assert not any(call[:2] == ("input", "job_titles") for call in fake.calls)


def test_final_readback_catches_a_previous_filter_disappearing() -> None:
    requested = plan()
    canonical_keywords = ("backend AND distributed systems",)
    fake = FakePort(
        readback_sequences={
            "keywords": [canonical_keywords, (), (), ()],
        }
    )

    result = run_verified_filters(requested, fake)

    assert result.status is SearchStatus.FILTER_MISMATCH
    assert fake.submitted == 0


def test_readback_retries_bounded_react_delay() -> None:
    requested = plan()
    canonical_keywords = ("backend AND distributed systems",)
    fake = FakePort(readback_sequences={"keywords": [(), canonical_keywords]})

    result = run_verified_filters(requested, fake)

    assert result.status is None
    keyword_reads = [call for call in fake.calls if call[:2] == ("read", "keywords")]
    assert keyword_reads[:2] == [("read", "keywords", 0), ("read", "keywords", 1)]


def test_selector_drift_stops_without_submit() -> None:
    fake = FakePort(drift_field="network")

    result = run_verified_filters(plan(), fake)

    assert result.status is SearchStatus.DRIFTED
    assert fake.submitted == 0


def test_pacing_is_bounded_deterministic_and_not_fixed() -> None:
    requested = plan()
    first = [
        deterministic_delay_ms(requested.position_ref, field_name, value)
        for field_name, values in requested.filter_items()
        for value in values
    ]
    second = [
        deterministic_delay_ms(requested.position_ref, field_name, value)
        for field_name, values in requested.filter_items()
        for value in values
    ]

    assert first == second
    assert all(800 <= value <= 1_600 for value in first)
    assert len(set(first)) > 1


def test_aside_repl_uses_existing_target_and_closed_page_api() -> None:
    sources = [build_repl_source(command, {}) for command in ReplCommand]
    combined = "\n".join(sources)

    assert "listBrowserTabs" in combined
    assert "attachBrowserTab" in combined
    assert "getByRole" in combined
    assert "Advanced search" in combined
    assert "Network relationships" in combined
    assert "Search results loaded" in combined
    assert ".pdf(" in combined
    assert "annotatedScreenshot" not in combined
    for forbidden in (
        "openTab(",
        "newPage(",
        "newCDPSession",
        ".send(",
        ".evaluate(",
        "Runtime.evaluate",
        "Page.captureScreenshot",
        "Page.navigate",
        "Target.createTarget",
        "Network.",
        "Storage.",
        "Cookie",
        "closeTab(",
        "page.close(",
        "context.close(",
    ):
        assert forbidden not in combined


def test_repl_payload_is_encoded_not_interpolated() -> None:
    hostile = '\"); await openTab("https://attacker.invalid"); //'

    source = build_repl_source(ReplCommand.INPUT_FILTER, {"value": hostile})

    assert hostile not in source
    assert "Buffer.from" in source
    assert "base64" in source


def test_repl_does_not_accept_a_runtime_expression_from_its_caller() -> None:
    source = build_repl_source(
        ReplCommand.OBSERVE_SURFACE,
        {"expression": "document.cookie"},
    )

    assert "payload.expression" not in source


@pytest.mark.parametrize("command", list(ReplCommand))
def test_repl_command_is_one_physical_line(command: ReplCommand) -> None:
    source = build_repl_source(command, {})

    assert source.splitlines() == [source]


def test_rps_ui_contract_keeps_selectors_and_labels_out_of_python() -> None:
    contract = load_rps_ui_contract()

    assert contract.allowed_origin == "https://www.linkedin.com"
    assert tuple(contract.fields) == (
        "keywords",
        "job_titles",
        "network",
        "seniority",
        "locations",
    )
    assert all(contract.fields[name].labels for name in contract.fields)
    assert contract.submit_labels
    assert isinstance(contract.authenticated_selectors, tuple)
