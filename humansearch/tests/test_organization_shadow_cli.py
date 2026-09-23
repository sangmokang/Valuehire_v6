from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from humansearch import organization_shadow_cli as shadow_cli

ROOT = Path(__file__).parents[2]
CONFIG = ROOT / "contracts/jev-org-reference-shadow.json"


def synthetic_payload() -> dict[str, object]:
    cohort: dict[str, object] = {
        "canonical_company_id": "company-synthetic-001",
        "role_family": "backend_platform",
        "seniority": "senior",
        "team_product_scope": "payments",
    }
    evidence: dict[str, object] = {
        "primary_role_family": "backend_platform",
        "responsibilities": ["design service boundaries"],
        "ownership_scope": ["own service lifecycle"],
        "production_operating": ["operate production services"],
        "product_stage": ["scale a growing product"],
        "domain_problems": ["reduce transaction failures"],
        "technical_environment": ["distributed service constraints"],
    }
    observations: list[dict[str, object]] = []
    for index in range(3):
        observations.append(
            {
                "observation_id": f"observation-{index}",
                "person_id": f"person-{index}",
                "cohort": cohort,
                "employment_status": "current",
                "observation_date": "2026-09-01",
                "source_timestamp": "2026-09-01T00:00:00+00:00",
                "evidence_ids": [f"evidence-{index}"],
                "role_evidence": evidence,
            }
        )
    return {
        "as_of": "2026-09-22",
        "known_denominator": 8,
        "criteria": [
            {
                "key": "backend",
                "label": "Backend ownership",
                "weight": 100,
                "status": "met",
                "required": True,
                "evidence": ["Owned a production service"],
            }
        ],
        "relevant_experience": [],
        "a_input_fingerprint": {"jd_id": "synthetic-jd-001"},
        "jd_evidence": evidence,
        "candidate_evidence": evidence,
        "reference_observations": observations,
    }


def test_local_only_cli_runs_real_shadow_entrypoint_and_writes_traceable_ledger(
    tmp_path: Path,
) -> None:
    input_path = tmp_path / "input.json"
    output_path = tmp_path / "output.json"
    input_path.write_text(json.dumps(synthetic_payload()), encoding="utf-8")
    environment = os.environ.copy()
    environment.pop("TYPESAFE_API_KEY", None)

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "humansearch.organization_shadow_cli",
            "--input",
            str(input_path),
            "--output",
            str(output_path),
            "--config",
            str(CONFIG),
            "--live-jev",
        ],
        cwd=ROOT / "humansearch",
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    result = json.loads(output_path.read_text(encoding="utf-8"))
    assert result["delivery_status"] == "LOCAL_ONLY"
    assert result["a"]["score"]["score"] == 100
    assert result["a"]["recommendation"] == "priority"
    assert result["semantic"]["status"] == "not_run"
    assert result["semantic"]["error_code"] == "judge_disabled_or_api_key_missing"
    assert result["ledger"]["model_version"] == "jev-1.13.0"
    assert result["ledger"]["question_version"] == "org-shadow-questions-v1"
    assert result["ledger"]["threshold_version"] == "org-shadow-thresholds-v1"
    assert result["ledger"]["pattern_version"] == "org-reference-pattern-v1"
    assert len(result["ledger"]["input_hash"]) == 64
    assert result["ledger"]["primitive_answers"] == {}
    assert result["ledger"]["human_review_status"] == "not_run"
    assert "person-" not in output_path.read_text(encoding="utf-8")


def test_cli_rejects_forbidden_identity_proxy_fields(tmp_path: Path) -> None:
    payload = synthetic_payload()
    candidate_raw = payload["candidate_evidence"]
    assert isinstance(candidate_raw, dict)
    candidate = dict(candidate_raw)
    candidate["school"] = "prestige-only"
    payload["candidate_evidence"] = candidate
    input_path = tmp_path / "input.json"
    output_path = tmp_path / "output.json"
    input_path.write_text(json.dumps(payload), encoding="utf-8")

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "humansearch.organization_shadow_cli",
            "--input",
            str(input_path),
            "--output",
            str(output_path),
            "--config",
            str(CONFIG),
        ],
        cwd=ROOT / "humansearch",
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode != 0
    assert not output_path.exists()
    assert "school" in completed.stderr
    assert "prestige-only" not in completed.stderr


class _Judge:
    def __init__(self, raises: Exception | None = None) -> None:
        self.raises, self.calls = raises, 0

    def evaluate(self, **_: Any) -> dict[str, object]:
        self.calls += 1
        if self.raises is not None:
            raise self.raises
        return {"model": "jev-1.13.0", "answers": {}, "usage": {}}

    def close(self) -> None:
        return None


def _live_shadow(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, judge: _Judge,
                 output: Path) -> int:
    monkeypatch.setenv("TYPESAFE_API_KEY", "synthetic-key-not-real")
    monkeypatch.setattr(shadow_cli, "TypeSafeJevJudge", lambda: judge)
    (source := tmp_path / "input.json").write_text(json.dumps(synthetic_payload()), encoding="utf-8")
    return shadow_cli.main(["--input", str(source), "--output", str(output), "--config", str(CONFIG),
                            "--live-jev"])


@pytest.mark.parametrize("raises", [None, TimeoutError("synthetic")], ids=["answered", "raised"])
def test_live_shadow_request_is_recorded_as_external(raises: Exception | None, tmp_path: Path,
                                                     monkeypatch: pytest.MonkeyPatch) -> None:
    judge, output = _Judge(raises), tmp_path / "out.json"
    assert _live_shadow(monkeypatch, tmp_path, judge, output) == 0
    result = json.loads(output.read_text(encoding="utf-8"))
    assert (judge.calls, result["delivery_status"], result["request_attempts"]) == (1, "EXTERNAL_JEV", 1)


def test_live_shadow_output_failure_still_reports_the_request(tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
                                                             capsys: pytest.CaptureFixture[str]) -> None:
    (blocker := tmp_path / "file").write_text("x")
    with pytest.raises(SystemExit) as stop:  # the output path sits under a regular file
        _live_shadow(monkeypatch, tmp_path, judge := _Judge(), blocker / "out.json")
    error = json.loads(capsys.readouterr().err)
    assert (stop.value.code, judge.calls) == (2, 1)
    assert (error["delivery_status"], error["request_attempts"]) == ("EXTERNAL_JEV", 1)


@pytest.mark.parametrize("target", ["input", "config", "input_symlink", "input_hardlink"])
def test_shadow_output_never_overwrites_input_or_config(target: str, tmp_path: Path,
                                                        capsys: pytest.CaptureFixture[str]) -> None:
    (source := tmp_path / "input.json").write_text(json.dumps(synthetic_payload()), encoding="utf-8")
    (config := tmp_path / "config.json").write_bytes(CONFIG.read_bytes())  # never the repo contract
    output = {"input": source, "config": config, "input_symlink": tmp_path / "link.json",
              "input_hardlink": tmp_path / "hard.json"}[target]
    if target == "input_symlink":
        output.symlink_to(source)
    if target == "input_hardlink":
        os.link(source, output)
    before = {path: path.read_bytes() for path in (source, config)}
    with pytest.raises(SystemExit) as stop:
        shadow_cli.main(["--input", str(source), "--output", str(output), "--config", str(config)])
    assert stop.value.code == 2 and json.loads(capsys.readouterr().err)["error_code"] == "output_collision"
    assert {path: path.read_bytes() for path in (source, config)} == before
