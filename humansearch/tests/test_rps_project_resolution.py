from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Literal

from hypothesis import given
from hypothesis import strategies as st

from humansearch.rps_project_resolution import (
    RpsProjectStatus,
    resolve_rps_project,
)


def _project(
    project_id: str,
    *,
    customer_id: str = "cust-1",
    position_id: str = "pos-1",
    customer_name: str = "Acme",
    position_title: str = "Backend Engineer",
    name: str = "Acme Backend Engineer",
) -> dict[str, object]:
    return {
        "project_id": project_id,
        "name": name,
        "customer_id": customer_id,
        "customer_name": customer_name,
        "position_id": position_id,
        "position_title": position_title,
    }


def _payload(
    *,
    projects: list[dict[str, object]] | None = None,
    mapped_project_id: str | None = None,
    query_error: str | None = None,
    all_pages_loaded: bool = True,
    stale: bool = False,
    pending_creation_intent: bool = False,
    position_id: str = "pos-1",
    customer_id: str = "cust-1",
    account_scope: str = "rps-main",
    observed_at: str = "2026-09-14T10:00:00Z",
    observation_id: str | None = "obs-1",
    query_scope: str | None = "account-projects",
    observation_projects: Literal["same", "missing"] = "same",
    project_links: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    project_list = [] if projects is None else projects
    observation: dict[str, object] = {
        "account_scope": account_scope,
        "query_error": query_error,
        "all_pages_loaded": all_pages_loaded,
        "stale": stale,
        "observed_at": observed_at,
    }
    if observation_id is not None:
        observation["observation_id"] = observation_id
    if query_scope is not None:
        observation["query_scope"] = query_scope
    if observation_projects == "same":
        observation["projects"] = project_list
    return {
        "position_id": position_id,
        "customer_id": customer_id,
        "customer_name": "Acme",
        "position_title": "Backend Engineer",
        "account_scope": account_scope,
        "mapped_project_id": mapped_project_id,
        "pending_creation_intent": pending_creation_intent,
        "observation_limit": {
            "reference_time": "2026-09-14T10:01:00Z",
            "max_age_seconds": 120,
        },
        "project_links": [] if project_links is None else project_links,
        "projects": project_list,
        "observation": observation,
    }


def _linked_project(project_id: str, position_id: str) -> dict[str, object]:
    return {
        "account_scope": "rps-main",
        "project_id": project_id,
        "position_id": position_id,
    }


def _without_observation_field(field: str) -> dict[str, object]:
    payload = _payload(projects=[_project("rps-1")])
    observation = payload["observation"]
    assert isinstance(observation, dict)
    del observation[field]
    return payload


def _with_observation_limit(
    *, observed_at: str, reference_time: str, max_age_seconds: int
) -> dict[str, object]:
    payload = _payload(projects=[_project("rps-1")], observed_at=observed_at)
    payload["observation_limit"] = {
        "reference_time": reference_time,
        "max_age_seconds": max_age_seconds,
    }
    return payload


def _expected_query_failed(payload: dict[str, object]) -> None:
    result = resolve_rps_project(payload)

    assert result.status is RpsProjectStatus.QUERY_FAILED
    assert result.project_id is None


def test_missing_observation_identity_time_scope_or_project_list_blocks_resolution() -> None:
    _expected_query_failed(_without_observation_field("observation_id"))
    _expected_query_failed(_without_observation_field("observed_at"))
    _expected_query_failed(_without_observation_field("query_scope"))
    _expected_query_failed(
        _payload(projects=[_project("rps-1")], observation_projects="missing")
    )


def test_observation_limit_rejects_expired_and_future_observations() -> None:
    _expected_query_failed(
        _with_observation_limit(
            observed_at="2026-09-14T09:58:59Z",
            reference_time="2026-09-14T10:01:00Z",
            max_age_seconds=120,
        )
    )
    _expected_query_failed(
        _with_observation_limit(
            observed_at="2026-09-14T10:01:01Z",
            reference_time="2026-09-14T10:01:00Z",
            max_age_seconds=120,
        )
    )


def test_project_link_to_another_position_blocks_reuse_even_with_matching_project() -> None:
    result = resolve_rps_project(
        _payload(
            mapped_project_id="rps-1",
            projects=[_project("rps-1")],
            project_links=[_linked_project("rps-1", "pos-other")],
        )
    )

    assert result.status is RpsProjectStatus.MAPPING_CONFLICT
    assert result.project_id is None


def test_project_link_to_same_position_allows_reuse() -> None:
    result = resolve_rps_project(
        _payload(
            mapped_project_id="rps-1",
            projects=[_project("rps-1")],
            project_links=[_linked_project("rps-1", "pos-1")],
        )
    )

    assert result.status is RpsProjectStatus.REUSE
    assert result.project_id == "rps-1"


def test_stable_match_plus_name_only_duplicate_is_ambiguous() -> None:
    result = resolve_rps_project(
        _payload(
            projects=[
                _project("rps-1"),
                {
                    "project_id": "rps-name-only",
                    "name": "Acme Backend Engineer",
                    "customer_name": "Acme",
                    "position_title": "Backend Engineer",
                },
            ]
        )
    )

    assert result.status is RpsProjectStatus.AMBIGUOUS
    assert result.project_id is None


def test_mapped_matching_project_is_reused() -> None:
    result = resolve_rps_project(
        _payload(
            mapped_project_id="rps-1",
            projects=[_project("rps-1"), _project("rps-2", position_id="pos-2")],
        )
    )

    assert result.status is RpsProjectStatus.REUSE
    assert result.project_id == "rps-1"
    assert result.plan_only is True
    assert result.allows_write is False


def test_mapping_conflict_does_not_fall_back_to_matching_name() -> None:
    result = resolve_rps_project(
        _payload(
            mapped_project_id="missing",
            projects=[_project("rps-2", name="Acme Backend Engineer")],
        )
    )

    assert result.status is RpsProjectStatus.MAPPING_CONFLICT
    assert result.project_id is None


def test_same_customer_different_position_does_not_count_as_match() -> None:
    result = resolve_rps_project(
        _payload(projects=[_project("rps-2", position_id="pos-2")])
    )

    assert result.status is RpsProjectStatus.CREATE_REQUIRED
    assert result.project_id is None


def test_complete_empty_query_requires_create_but_does_not_grant_write() -> None:
    result = resolve_rps_project(_payload(projects=[]))

    assert result.status is RpsProjectStatus.CREATE_REQUIRED
    assert result.project_id is None
    assert result.plan_only is True
    assert result.allows_write is False


def test_query_error_is_not_treated_as_absent_project() -> None:
    result = resolve_rps_project(_payload(projects=[], query_error="timeout"))

    assert result.status is RpsProjectStatus.QUERY_FAILED
    assert result.project_id is None


def test_incomplete_or_stale_observation_blocks_creation() -> None:
    assert (
        resolve_rps_project(_payload(projects=[], all_pages_loaded=False)).status
        is RpsProjectStatus.QUERY_FAILED
    )
    assert (
        resolve_rps_project(_payload(projects=[], stale=True)).status
        is RpsProjectStatus.QUERY_FAILED
    )


def test_pending_creation_intent_requires_reconcile_before_new_create() -> None:
    result = resolve_rps_project(
        _payload(projects=[], pending_creation_intent=True)
    )

    assert result.status is RpsProjectStatus.RECONCILE_REQUIRED
    assert result.project_id is None


def test_single_and_multiple_evidence_matches_are_separated() -> None:
    assert (
        resolve_rps_project(_payload(projects=[_project("rps-1")])).status
        is RpsProjectStatus.REUSE
    )
    assert (
        resolve_rps_project(
            _payload(projects=[_project("rps-1"), _project("rps-2")])
        ).status
        is RpsProjectStatus.AMBIGUOUS
    )


def test_name_only_match_is_ambiguous_not_reused_or_created() -> None:
    result = resolve_rps_project(
        _payload(
            projects=[
                {
                    "project_id": "rps-1",
                    "name": "Acme Backend Engineer",
                    "customer_name": "Acme",
                    "position_title": "Backend Engineer",
                }
            ]
        )
    )

    assert result.status is RpsProjectStatus.AMBIGUOUS
    assert result.project_id is None


def test_duplicate_project_id_with_conflicting_target_evidence_fails_query() -> None:
    result = resolve_rps_project(
        _payload(
            projects=[
                _project("rps-1"),
                _project("rps-1", position_id="pos-2"),
            ]
        )
    )

    assert result.status is RpsProjectStatus.QUERY_FAILED
    assert result.project_id is None


def test_targets_are_resolved_independently() -> None:
    first = resolve_rps_project(_payload(projects=[_project("rps-1")]))
    second = resolve_rps_project(
        _payload(
            position_id="pos-2",
            customer_id="cust-2",
            projects=[
                _project(
                    "rps-2",
                    customer_id="cust-2",
                    position_id="pos-2",
                    customer_name="Beta",
                    position_title="ML Engineer",
                )
            ],
        )
    )

    assert first.status is RpsProjectStatus.REUSE
    assert first.project_id == "rps-1"
    assert second.status is RpsProjectStatus.REUSE
    assert second.project_id == "rps-2"


@given(st.permutations([_project("rps-1"), _project("rps-2")]))
def test_ambiguous_resolution_is_order_independent(
    projects: tuple[dict[str, object], ...]
) -> None:
    result = resolve_rps_project(_payload(projects=list(projects)))

    assert result.status is RpsProjectStatus.AMBIGUOUS
    assert result.project_id is None


def test_cli_is_plan_only_json(tmp_path: Path) -> None:
    input_path = tmp_path / "input.json"
    input_path.write_text(json.dumps(_payload(projects=[])), encoding="utf-8")

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "humansearch.rps_project_resolution_cli",
            "--input",
            str(input_path),
        ],
        check=True,
        cwd=Path(__file__).parents[1],
        text=True,
        capture_output=True,
    )
    output: dict[str, Any] = json.loads(completed.stdout)

    assert output["status"] == "CREATE_REQUIRED"
    assert output["plan_only"] is True
    assert output["allows_write"] is False
