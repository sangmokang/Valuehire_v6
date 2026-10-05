from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, cast

import pytest

from humansearch import organization_shadow_cli as shadow_cli

ROOT = Path(__file__).parents[2]
CONFIG = ROOT / "contracts/jev-org-reference-shadow.json"
PROJECT = Path(__file__).parents[1]  # the humansearch project, wherever it is copied


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
        cwd=PROJECT,
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
        cwd=PROJECT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode != 0
    assert not output_path.exists()
    assert "school" in completed.stderr
    assert "prestige-only" not in completed.stderr


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


def _run_in_process(tmp_path: Path, payload: dict[str, object], *extra: str) -> tuple[Path, Path]:
    (source := tmp_path / "input.json").write_text(json.dumps(payload), encoding="utf-8")
    output = tmp_path / "output.json"
    shadow_cli.main(["--input", str(source), "--output", str(output), "--config", str(CONFIG), *extra])
    return source, output


class _BrokenInitJudge:
    def __init__(self) -> None:
        raise RuntimeError("sdk init failed: private detail must not leak")


class _BrokenCloseJudge:
    closed = 0

    def evaluate(self, **_: object) -> object:
        raise TimeoutError("private response body must not leak")

    def close(self) -> None:
        _BrokenCloseJudge.closed += 1
        raise RuntimeError("close failed")


@pytest.mark.parametrize("judge_class", [_BrokenInitJudge, _BrokenCloseJudge])
def test_judge_lifecycle_failure_keeps_local_a_result(
    judge_class: type, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """D2: judge 생성·종료 예외도 A 를 보존하고 ERROR 로 기록해야 한다(NOT_RUN 으로 접지 않는다)."""
    monkeypatch.setenv("TYPESAFE_API_KEY", "synthetic-key")
    monkeypatch.setattr(shadow_cli, "TypeSafeJevJudge", judge_class)
    _, output = _run_in_process(tmp_path, synthetic_payload(), "--live-jev")
    result = json.loads(output.read_text(encoding="utf-8"))
    assert result["a"]["score"]["score"] == 100
    assert result["a"]["recommendation"] == "priority"
    assert result["semantic"]["status"] == "error"
    assert result["semantic"]["error_code"] == "judge_call_failed"
    assert "private" not in output.read_text(encoding="utf-8") + capsys.readouterr().err


@pytest.mark.parametrize(
    ("key", "expected_field"),
    [("candidate@example.com", "candidate_evidence.<unknown>"), ("school", "candidate_evidence.school")],
)
def test_unknown_key_name_is_reported_only_when_it_is_field_shaped(
    key: str, expected_field: str, tmp_path: Path, capsys: pytest.CaptureFixture[str],
) -> None:
    """D6: 사용자 제어 키 문자열(이메일 등)은 stderr 에 그대로 나가면 안 된다."""
    payload = synthetic_payload()
    candidate = dict(payload["candidate_evidence"])  # type: ignore[call-overload]
    candidate[key] = ["value"]
    payload["candidate_evidence"] = candidate
    with pytest.raises(SystemExit) as stop:
        _run_in_process(tmp_path, payload)
    err = capsys.readouterr().err
    assert stop.value.code == 2
    assert json.loads(err)["field"] == expected_field
    if key != "school":
        assert key not in err



def test_output_path_resolution_error_stays_inside_json_error_boundary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    """출력 경로 해석이 예외를 내도(링크 순환·권한 등) traceback 없이 JSON 오류·종료값 2 로 끝나야 한다."""
    def broken(*_: object) -> bool:
        raise RuntimeError(f"Symlink loop from {tmp_path}")

    monkeypatch.setattr(shadow_cli, "_same_file", broken)
    (source := tmp_path / "input.json").write_text(json.dumps(synthetic_payload()), encoding="utf-8")
    with pytest.raises(SystemExit) as stop:
        shadow_cli.main(["--input", str(source), "--output", str(tmp_path / "o.json"), "--config", str(CONFIG)])
    err = capsys.readouterr().err
    assert stop.value.code == 2
    assert json.loads(err)["ok"] is False
    assert str(tmp_path) not in err and not (tmp_path / "o.json").exists()


def _with(payload: dict[str, object], path: tuple[str | int, ...], value: object) -> dict[str, object]:
    copied: Any = json.loads(json.dumps(payload))
    target = copied
    for step in path[:-1]:
        target = target[step]
    target[path[-1]] = value
    return cast(dict[str, object], copied)


OBSERVED = ("reference_observations", 0, "role_evidence")


@pytest.mark.parametrize(
    "path",
    [
        ("candidate_evidence", "production_operating"),
        ("jd_evidence", "technical_environment"),
        (*OBSERVED, "domain_problems"),
    ],
)
def test_empty_optional_evidence_category_is_accepted(
    path: tuple[str | int, ...], tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """D5: 근거 범주 하나가 비어 있는 것은 근거 부족이지 입력 오류가 아니다(핵심 RoleEvidence 계약과 일치)."""
    monkeypatch.delenv("TYPESAFE_API_KEY", raising=False)
    _, output = _run_in_process(tmp_path, _with(synthetic_payload(), path, []))
    result = json.loads(output.read_text(encoding="utf-8"))
    assert result["a"]["score"]["score"] == 100
    assert result["semantic"]["status"] == "not_run"


def test_candidate_with_all_categories_empty_is_accepted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("TYPESAFE_API_KEY", raising=False)
    payload = synthetic_payload()
    for name in ("responsibilities", "ownership_scope", "production_operating",
                 "product_stage", "domain_problems", "technical_environment"):
        payload = _with(payload, ("candidate_evidence", name), [])
    _, output = _run_in_process(tmp_path, payload)
    assert json.loads(output.read_text(encoding="utf-8"))["a"]["recommendation"] == "priority"


@pytest.mark.parametrize(
    ("path", "value", "field"),
    [
        (("candidate_evidence", "primary_role_family"), "", "candidate_evidence.primary_role_family"),
        (("candidate_evidence", "responsibilities"), ["  "], "candidate_evidence.responsibilities"),
        (("candidate_evidence", "responsibilities"), None, "candidate_evidence.responsibilities"),
        (("reference_observations", 0, "evidence_ids"), [], "reference_observations[0].evidence_ids"),
    ],
)
def test_required_evidence_is_still_rejected(
    path: tuple[str | int, ...], value: object, field: str, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as stop:
        _run_in_process(tmp_path, _with(synthetic_payload(), path, value))
    assert stop.value.code == 2
    assert json.loads(capsys.readouterr().err)["field"] == field
    assert not (tmp_path / "output.json").exists()


def test_missing_evidence_category_key_is_still_rejected(
    tmp_path: Path, capsys: pytest.CaptureFixture[str],
) -> None:
    payload = _with(synthetic_payload(), ("as_of",), "2026-09-22")  # deep copy: evidence dicts are shared
    del cast(dict[str, object], payload["candidate_evidence"])["ownership_scope"]
    with pytest.raises(SystemExit) as stop:
        _run_in_process(tmp_path, payload)
    assert stop.value.code == 2
    assert json.loads(capsys.readouterr().err)["field"] == "candidate_evidence.ownership_scope"


def test_reference_evidence_role_family_mismatch_is_rejected_by_cli(
    tmp_path: Path, capsys: pytest.CaptureFixture[str],
) -> None:
    """D4: CLI 경로에서도 cohort 직무군과 다른 근거는 명시적 오류·종료값 2·출력 없음."""
    payload = synthetic_payload()
    for index in range(3):
        payload = _with(payload, ("reference_observations", index, "role_evidence",
                                  "primary_role_family"), "data")
    with pytest.raises(SystemExit) as stop:
        _run_in_process(tmp_path, payload)
    assert stop.value.code == 2
    assert json.loads(capsys.readouterr().err)["error_code"] == "invalid_input_or_config"
    assert not (tmp_path / "output.json").exists()


def test_candidate_from_another_role_family_is_still_reviewed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """D4 과잉 차단 방지: 후보·JD 의 직무군 차이는 판정 대상(B)이지 입력 오류가 아니다."""
    monkeypatch.delenv("TYPESAFE_API_KEY", raising=False)
    payload = _with(synthetic_payload(), ("candidate_evidence", "primary_role_family"), "data")
    _, output = _run_in_process(tmp_path, payload)
    assert json.loads(output.read_text(encoding="utf-8"))["a"]["score"]["score"] == 100
