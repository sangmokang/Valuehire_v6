from collections.abc import Mapping

import pytest

from humansearch.auth_surface import AuthSurfaceState
from humansearch.rps_search_contract import (
    PlanValidationError,
    RpsSurface,
    SearchPlan,
    SearchStatus,
    TargetSelectionError,
    preflight_status,
    select_rps_target,
)

ALLOWED_ORIGIN = "https://www.linkedin.com"


def plan_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "position_ref": "position-123",
        "project_ref": "project-456",
        "keywords": ["backend", "distributed systems"],
        "job_titles": ["Backend Engineer"],
        "network": ["1st", "2nd"],
        "seniority": ["Senior"],
        "locations": ["South Korea"],
    }
    payload.update(overrides)
    return payload


def target_payload(project_ref: str = "project-456", **overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "type": "page",
        "url": (
            f"https://www.linkedin.com/talent/hire/{project_ref}/discover/recruiterSearch"
            "?searchHistoryId=private"
        ),
        "targetId": "opaque-target",
    }
    payload.update(overrides)
    return payload


def authenticated_surface(project_ref: str = "project-456") -> RpsSurface:
    return RpsSurface(
        auth_state=AuthSurfaceState.AUTHENTICATED,
        contract_valid=True,
        session_conflict=False,
        project_ref=project_ref,
    )


def test_valid_plan_has_canonical_field_order_and_immutable_values() -> None:
    plan = SearchPlan.from_mapping(plan_payload())

    assert plan.position_ref == "position-123"
    assert plan.project_ref == "project-456"
    assert plan.filter_items() == (
        ("keywords", ("backend", "distributed systems")),
        ("job_titles", ("Backend Engineer",)),
        ("network", ("1st", "2nd")),
        ("seniority", ("Senior",)),
        ("locations", ("South Korea",)),
    )


@pytest.mark.parametrize(
    "payload",
    [
        {},
        plan_payload(position_ref=""),
        plan_payload(project_ref="   "),
        plan_payload(keywords=[]),
        plan_payload(job_titles=["Backend Engineer", 3]),
        plan_payload(network="1st"),
        plan_payload(locations=["South Korea", ""]),
        plan_payload(raw_cdp={"method": "Target.createTarget"}),
        plan_payload(url="https://attacker.invalid"),
    ],
)
def test_plan_rejects_missing_empty_mistyped_or_unknown_fields(
    payload: Mapping[str, object],
) -> None:
    with pytest.raises(PlanValidationError):
        SearchPlan.from_mapping(payload)


def test_target_selection_requires_one_exact_origin_rps_page() -> None:
    target = select_rps_target([target_payload()], ALLOWED_ORIGIN)

    assert target.project_ref == "project-456"
    assert target.target_id == "opaque-target"


def test_target_selection_accepts_same_tab_advanced_search_route() -> None:
    target = select_rps_target(
        [
            target_payload(
                url=(
                    "https://www.linkedin.com/talent/hire/project-456/"
                    "discover/recruiterSearch/advanced?searchHistoryId=private"
                )
            )
        ],
        ALLOWED_ORIGIN,
    )

    assert target.project_ref == "project-456"


@pytest.mark.parametrize(
    ("targets", "status"),
    [
        ([], SearchStatus.TARGET_NOT_FOUND),
        (
            [target_payload(), target_payload(targetId="target-2")],
            SearchStatus.TARGET_AMBIGUOUS,
        ),
        (
            [target_payload(url="https://www.linkedin.com.evil/talent/hire/x/discover/recruiterSearch")],
            SearchStatus.TARGET_NOT_FOUND,
        ),
        (
            [target_payload(url="https://www.linkedin.com/feed/")],
            SearchStatus.TARGET_NOT_FOUND,
        ),
    ],
)
def test_target_selection_fails_closed(targets: list[object], status: SearchStatus) -> None:
    with pytest.raises(TargetSelectionError) as raised:
        select_rps_target(targets, ALLOWED_ORIGIN)

    assert raised.value.status is status


def test_preflight_allows_only_matching_authenticated_project() -> None:
    plan = SearchPlan.from_mapping(plan_payload())
    target = select_rps_target([target_payload()], ALLOWED_ORIGIN)

    assert preflight_status(plan, target, authenticated_surface()) is None


@pytest.mark.parametrize(
    ("surface", "expected"),
    [
        (authenticated_surface("other-project"), SearchStatus.FAILED),
        (
            RpsSurface(
                auth_state=AuthSurfaceState.CHALLENGE,
                contract_valid=True,
                session_conflict=False,
                project_ref="project-456",
            ),
            SearchStatus.MANUAL_ACTION_REQUIRED,
        ),
        (
            RpsSurface(
                auth_state=AuthSurfaceState.AUTHENTICATED,
                contract_valid=True,
                session_conflict=True,
                project_ref="project-456",
            ),
            SearchStatus.BLOCKED_SESSION_CONFLICT,
        ),
        (
            RpsSurface(
                auth_state=AuthSurfaceState.DRIFTED,
                contract_valid=False,
                session_conflict=False,
                project_ref=None,
            ),
            SearchStatus.DRIFTED,
        ),
        (
            RpsSurface(
                auth_state=AuthSurfaceState.HUMAN_AUTH,
                contract_valid=True,
                session_conflict=False,
                project_ref="project-456",
            ),
            SearchStatus.MANUAL_ACTION_REQUIRED,
        ),
    ],
)
def test_preflight_rejects_untrusted_surface(
    surface: RpsSurface, expected: SearchStatus
) -> None:
    plan = SearchPlan.from_mapping(plan_payload())
    target = select_rps_target([target_payload()], ALLOWED_ORIGIN)

    assert preflight_status(plan, target, surface) is expected


def test_public_status_set_is_intentionally_small() -> None:
    assert {status.value for status in SearchStatus} == {
        "completed",
        "blocked_session_conflict",
        "manual_action_required",
        "filter_mismatch",
        "target_not_found",
        "target_ambiguous",
        "drifted",
        "failed",
    }
