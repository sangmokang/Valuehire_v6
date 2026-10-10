"""Contract gaps found by the 2026-10-09 Codex adversarial review of PR #109.

ISSUE-1: role-family-only evidence must not make a cohort READY (jev goal AC-3).
ISSUE-2: a score answer must equal the probability-weighted average (typesafe-sdk 0.7.1 ScoreAnswer).
ISSUE-3: argparse errors must stay inside the value-free JSON error boundary (D6 remainder).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest
from test_organization_shadow import (
    CONFIG_PATH,
    FakeJudge,
    a_review,
    observation,
    role_evidence,
    snapshot,
    successful_response,
)
from test_organization_shadow_cli import synthetic_payload

from humansearch import organization_shadow_cli as shadow_cli
from humansearch.organization_reference import PatternSnapshot, PatternStatus, RoleEvidence
from humansearch.organization_shadow import (
    HumanReviewStatus,
    SemanticStatus,
    load_shadow_config,
    run_shadow_review,
)

CATEGORIES = (
    "responsibilities",
    "ownership_scope",
    "production_operating",
    "product_stage",
    "domain_problems",
    "technical_environment",
)
PROJECT = Path(__file__).parents[1]
MARKER = "synthetic-sensitive-value-7f3a9c"  # unique marker; must never be echoed


def _three(evidence: RoleEvidence | list[RoleEvidence]) -> PatternSnapshot:
    items = evidence if isinstance(evidence, list) else [evidence] * 3
    return snapshot(*(observation(f"person-{i}", evidence=e) for i, e in enumerate(items)))


ROLE_ONLY = replace(role_evidence(), **{name: () for name in CATEGORIES})


def test_role_family_only_evidence_is_limited_not_ready() -> None:
    result = _three(ROLE_ONLY)
    assert result.sample_size == 3
    assert result.status is PatternStatus.LIMITED
    # the role family is still reported as observed; it just cannot by itself make a pattern READY
    assert [item.category for item in result.repeated_patterns] == ["primary_role_family"]


def test_substantive_evidence_seen_by_one_person_only_is_limited() -> None:
    distinct = [replace(ROLE_ONLY, responsibilities=(f"unique duty {i}",)) for i in range(3)]
    assert _three(distinct).status is PatternStatus.LIMITED


@pytest.mark.parametrize("category", CATEGORIES)
def test_one_repeated_substantive_category_keeps_ready(category: str) -> None:
    assert _three(replace(ROLE_ONLY, **{category: ("shared signal",)})).status is PatternStatus.READY


def test_role_family_only_cohort_requires_human_review_even_with_a_confident_judge() -> None:
    result = run_shadow_review(
        a_review=a_review(),
        jd_evidence=role_evidence(suffix=" jd"),
        candidate_evidence=role_evidence(suffix=" candidate"),
        pattern_snapshot=_three(ROLE_ONLY),
        config=load_shadow_config(CONFIG_PATH),
        judge=FakeJudge(successful_response()),
    )
    assert result.semantic.status is SemanticStatus.COMPLETED
    assert result.semantic.additional_checks["pattern_status"] == "limited"
    assert result.semantic.human_review_status is HumanReviewStatus.REQUIRED


def _score_response(score: float, probabilities: dict[str, float]) -> dict[str, Any]:
    response = successful_response()
    answer = response["answers"]["transferable_experience_strength"]
    answer["score"] = score
    answer["probabilities"] = probabilities
    return response


def _judge(response: dict[str, Any]) -> SemanticStatus:
    return run_shadow_review(
        a_review=a_review(),
        jd_evidence=role_evidence(suffix=" jd"),
        candidate_evidence=role_evidence(suffix=" candidate"),
        pattern_snapshot=_three(role_evidence()),
        config=load_shadow_config(CONFIG_PATH),
        judge=FakeJudge(response),
    ).semantic.status


@pytest.mark.parametrize(
    ("score", "probabilities"),
    [
        (3.0, {"0": 1.0, "1": 0.0, "2": 0.0, "3": 0.0}),  # the reproduced contradiction
        (0.0, {"0": 0.0, "1": 0.0, "2": 0.0, "3": 1.0}),
        (1.7, {"0": 0.0, "1": 0.0, "2": 1.0, "3": 0.0}),
        (1.7 + 1e-3, {"0": 0.1, "1": 0.1, "2": 0.8, "3": 0.0}),
    ],
)
def test_score_contradicting_its_probabilities_is_invalid(
    score: float, probabilities: dict[str, float]
) -> None:
    assert _judge(_score_response(score, probabilities)) is SemanticStatus.INVALID_RESPONSE


@pytest.mark.parametrize(
    ("score", "probabilities"),
    [
        (1.7, {"0": 0.1, "1": 0.1, "2": 0.8, "3": 0.0}),  # SDK docstring example shape
        (1.7 + 1e-7, {"0": 0.1, "1": 0.1, "2": 0.8, "3": 0.0}),  # float noise
        (0.0, {"0": 1.0, "1": 0.0, "2": 0.0, "3": 0.0}),
        (3.0, {"0": 0.0, "1": 0.0, "2": 0.0, "3": 1.0}),
        (1.5, {"0": 0.25, "1": 0.25, "2": 0.25, "3": 0.25}),
    ],
)
def test_score_matching_its_probabilities_is_still_completed(
    score: float, probabilities: dict[str, float]
) -> None:
    assert _judge(_score_response(score, probabilities)) is SemanticStatus.COMPLETED


@pytest.mark.parametrize(
    "argv",
    [
        [f"--token={MARKER}"],
        ["--input", "in.json", "--output", "out.json", "--config", "c.json", MARKER],
        ["--input", "in.json", "--output", "out.json", "--config", "c.json", f"--x={MARKER}"],
        [f"--inp={MARKER}"],
        ["--output", MARKER],
    ],
)
def test_argument_errors_are_value_free_json(
    argv: list[str], capsys: pytest.CaptureFixture[str]
) -> None:
    with pytest.raises(SystemExit) as stop:
        shadow_cli.main(argv)
    captured = capsys.readouterr()
    assert stop.value.code == 2
    assert captured.out == ""
    assert MARKER not in captured.err
    assert json.loads(captured.err) == {"ok": False, "error_code": "invalid_input_or_config"}


def test_argument_error_in_a_real_process_keeps_the_input_value_out_of_stderr() -> None:
    completed = subprocess.run(
        [sys.executable, "-m", "humansearch.organization_shadow_cli", f"--token={MARKER}"],
        cwd=PROJECT,
        env={k: v for k, v in os.environ.items() if k != "TYPESAFE_API_KEY"},
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 2
    assert MARKER not in completed.stderr + completed.stdout
    assert json.loads(completed.stderr)["error_code"] == "invalid_input_or_config"


def test_help_still_works(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as stop:
        shadow_cli.main(["--help"])
    assert stop.value.code == 0
    assert "--live-jev" in capsys.readouterr().out


def test_valid_arguments_still_run_the_cli(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("TYPESAFE_API_KEY", raising=False)
    (source := tmp_path / "input.json").write_text(json.dumps(synthetic_payload()), "utf-8")
    output = tmp_path / "output.json"
    assert shadow_cli.main(
        ["--input", str(source), "--output", str(output), "--config", str(CONFIG_PATH)]
    ) == 0
    result = json.loads(output.read_text(encoding="utf-8"))
    assert result["a"]["score"]["score"] == 100
    assert result["semantic"]["d_additional_checks"]["pattern_status"] == "ready"
