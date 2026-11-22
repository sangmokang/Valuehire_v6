"""Contract gaps found by the 2026-10-09 Codex adversarial review of PR #109.

ISSUE-1: role-family-only evidence must not make a cohort READY (jev goal AC-3).
ISSUE-2: a score answer must equal the probability-weighted average (typesafe-sdk 0.7.1 ScoreAnswer).
ISSUE-3: argparse errors must stay inside the value-free JSON error boundary (D6 remainder).
D8': a source timestamp after the snapshot date (UTC) is invalid input (owner decision 2026-10-12).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import replace
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, cast

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
from humansearch.organization_shadow_validation import _validate_score

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


ROLE_ONLY = replace(role_evidence(), **cast(dict[str, Any], {name: () for name in CATEGORIES}))


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
    assert _three(replace(ROLE_ONLY, **cast(dict[str, Any], {category: ("shared signal",)}))).status is PatternStatus.READY


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


def _sourced_at(moment: datetime) -> PatternSnapshot:
    return snapshot(*(replace(observation(f"p{i}"), source_timestamp=moment) for i in range(3)))


@pytest.mark.parametrize(
    "moment",
    [
        datetime(2027, 1, 1, tzinfo=UTC),
        datetime(2026, 9, 23, 0, 0, tzinfo=UTC),
        datetime(2026, 9, 22, 20, 0, tzinfo=timezone(timedelta(hours=-5))),  # 09-23 01:00 UTC
    ],
)
def test_source_timestamp_after_snapshot_date_is_rejected(moment: datetime) -> None:
    with pytest.raises(ValueError, match="source timestamp"):
        _sourced_at(moment)


@pytest.mark.parametrize(
    "moment",
    [
        datetime(2026, 9, 1, tzinfo=UTC),
        datetime(2026, 9, 22, 23, 59, 59, tzinfo=UTC),
        datetime(2026, 9, 23, 8, 0, tzinfo=timezone(timedelta(hours=9))),  # 09-22 23:00 UTC
    ],
)
def test_source_timestamp_on_or_before_snapshot_date_is_accepted(moment: datetime) -> None:
    assert _sourced_at(moment).status is PatternStatus.READY


def test_cli_rejects_a_future_source_timestamp_without_output(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    payload = synthetic_payload()
    observations = payload["reference_observations"]
    assert isinstance(observations, list)
    for item in observations:
        item["source_timestamp"] = "2027-01-01T00:00:00+00:00"
    (source := tmp_path / "input.json").write_text(json.dumps(payload), "utf-8")
    output = tmp_path / "output.json"
    with pytest.raises(SystemExit) as stop:
        shadow_cli.main(["--input", str(source), "--output", str(output), "--config", str(CONFIG_PATH)])
    assert stop.value.code == 2
    assert json.loads(capsys.readouterr().err) == {"ok": False, "error_code": "invalid_input_or_config"}
    assert not output.exists()


# D7' (live Jev 1 call, 2026-10-12): jev-1.13.0 reports score and probabilities rounded to two
# decimals independently, so the score can differ from the weighted average by 0.01.
LIVE_ROUNDED = [
    (2.93, {"0": 0.0, "1": 0.0, "2": 0.06, "3": 0.94}),  # weighted 2.94
    (2.93, {"0": 0.01, "1": 0.0, "2": 0.05, "3": 0.94}),  # weighted 2.92
    (1.67, {"0": 0.0, "1": 0.33, "2": 0.67, "3": 0.0}),  # weighted 1.67, true mean 1.667
]


@pytest.mark.parametrize(("score", "probabilities"), LIVE_ROUNDED)
def test_live_two_decimal_rounding_is_still_completed(
    score: float, probabilities: dict[str, float]
) -> None:
    assert _judge(_score_response(score, probabilities)) is SemanticStatus.COMPLETED


# Feasible band for {0.1, 0.1, 0.8, 0}: true probabilities within +-0.005 summing to one give a mean in
# [1.69, 1.72]; the score's own rounding widens it to [1.685, 1.725].
@pytest.mark.parametrize(
    ("score", "expected"),
    [(1.724, "completed"), (1.726, "invalid_response"), (1.686, "completed"), (1.684, "invalid_response")],
)
def test_rounding_tolerance_boundary(score: float, expected: str) -> None:
    probabilities = {"0": 0.1, "1": 0.1, "2": 0.8, "3": 0.0}
    assert _judge(_score_response(score, probabilities)).value == expected


def test_score_impossible_under_two_decimal_rounding_is_invalid() -> None:
    # Codex 2026-10-12: the true mean is at most 1.99, so a reported 2.00 cannot come from rounding.
    response = _score_response(2.0, {"0": 0.0, "1": 0.03, "2": 0.97, "3": 0.0})
    assert _judge(response) is SemanticStatus.INVALID_RESPONSE


def test_rounding_band_does_not_grow_with_more_levels() -> None:
    criteria = [f"level {i}" for i in range(11)]
    answer = {
        "type": "score",
        "score": 0.28,
        "legend": {str(i): value for i, value in enumerate(criteria)},
        "probabilities": {str(i): 1.0 if i == 0 else 0.0 for i in range(11)},
        "confidence": 1.0,
    }
    with pytest.raises(ValueError, match="weighted average"):
        _validate_score("x", answer, {"criteria": criteria})
