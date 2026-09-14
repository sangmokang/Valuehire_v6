from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

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
) -> dict[str, object]:
    return {
        "position_id": position_id,
        "customer_id": customer_id,
        "customer_name": "Acme",
        "position_title": "Backend Engineer",
        "account_scope": account_scope,
        "mapped_project_id": mapped_project_id,
        "pending_creation_intent": pending_creation_intent,
        "observation": {
            "account_scope": account_scope,
            "query_error": query_error,
            "all_pages_loaded": all_pages_loaded,
            "stale": stale,
        },
        "projects": [] if projects is None else projects,
    }


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
