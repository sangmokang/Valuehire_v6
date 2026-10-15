import json
import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
SCRIPTS = ROOT / ".claude/skills/llmcodereview/scripts"
SHA = subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip()


def base_env(tmp_path: Path) -> dict[str, str]:
    env = os.environ.copy()
    env.update(
        {
            "LCR_REPO": str(ROOT),
            "LCR_ROOT": str(tmp_path / "review-root"),
            "LCR_PR": "123",
            "LCR_SHA": SHA,
            "LCR_BASE": SHA,
            "ASIDE_WIN": "1",
            "GPT_PROJECT_URL": "https://example.invalid/project",
        }
    )
    return env


def write_plan(tmp_path: Path, count: int = 1, first_files: list[str] | None = None) -> Path:
    prd = tmp_path / "review-root/pr123"
    prd.mkdir(parents=True, exist_ok=True)
    wus = []
    for i in range(1, count + 1):
        wid = f"WU{i:02d}"
        wus.append(
            {
                "id": wid,
                "title": f"title {wid}",
                "purpose": "test purpose",
                "risk": "LOW",
                "blast_radius": "local",
                "files": first_files if i == 1 and first_files is not None else [],
                "symbols": [],
                "invariants": [],
                "related_wus": [],
                "needs_auditor": False,
            }
        )
    plan = {
        "pr": 123,
        "wus": wus,
        "coverage_ledger": [
            {"file": f, "added": 1, "deleted": 0, "primary_wu": "WU01"}
            for f in (first_files or [])
        ],
        "cross_wu_boundaries": [],
    }
    plan_p = prd / "planner.json"
    plan_p.write_text(json.dumps(plan), encoding="utf-8")
    (prd / "inventory.tsv").write_text(
        "".join(f"{f}\t1\t0\n" for f in (first_files or [])), encoding="utf-8"
    )
    return plan_p


def completed_wu_raw(head_sha: str, reviewed: list[dict] | None = None) -> str:
    payload = {
        "wu": "WU01",
        "head_sha_checked": head_sha,
        "code_judgement": "중대한 결함 미발견",
        "arch_judgement": "현재 조건에 적합",
        "progress_judgement": "다음 개발 단계 진행 가능",
        "files_reviewed": reviewed or [],
        "traced_files": [],
        "core_flow": "flow",
        "findings": [],
        "adversarial": [],
        "tests_executed": [],
        "tests_not_executed": [],
        "uncertainty": [],
        "confidence": "high",
        "verdict": "PASS",
    }
    block = "<<<WU_JSON\n" + json.dumps(payload, ensure_ascii=False) + "\nWU_JSON>>>"
    return block + "\n" + block


def test_gpt_bundle_fails_when_git_show_cannot_attach_file(tmp_path: Path) -> None:
    write_plan(tmp_path, first_files=["missing-from-head.txt"])
    out = tmp_path / "prompt.txt"

    result = subprocess.run(
        ["python3", str(SCRIPTS / "gpt_bundle.py"), "wu", "WU01", str(out)],
        cwd=ROOT,
        env=base_env(tmp_path),
        text=True,
        capture_output=True,
    )

    assert result.returncode != 0
    assert "ATTACH_FAIL missing-from-head.txt" in (result.stderr + result.stdout)
    assert not out.exists()


def test_gpt_planner_bundle_needs_no_planner_result(tmp_path: Path) -> None:
    prd = tmp_path / "review-root/pr123"
    prd.mkdir(parents=True)
    (prd / "pr.diff").write_text("diff --git a/a.py b/a.py\n", encoding="utf-8")
    out = tmp_path / "planner-prompt.txt"

    result = subprocess.run(
        ["python3", str(SCRIPTS / "gpt_bundle.py"), "planner", str(out)],
        cwd=ROOT,
        env=base_env(tmp_path),
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0, result.stderr
    assert "diff --git a/a.py b/a.py" in out.read_text(encoding="utf-8")


def test_make_wu_prompt_uses_current_pr_and_generic_test_guidance(tmp_path: Path) -> None:
    plan = write_plan(tmp_path, first_files=["README.md"])

    result = subprocess.run(
        ["python3", str(SCRIPTS / "make_wu_prompt.py"), "wu", str(plan), "WU01"],
        cwd=ROOT,
        env=base_env(tmp_path),
        text=True,
        capture_output=True,
        check=True,
    )

    assert "PR #123" in result.stdout
    assert "PR #109" not in result.stdout
    assert "--live-jev" not in result.stdout
    assert "typesafe_sdk" not in result.stdout
    assert "cd humansearch" not in result.stdout


def test_gdriver_integration_summary_uses_all_planned_wus(tmp_path: Path) -> None:
    write_plan(tmp_path, count=10)
    gpt_dir = tmp_path / "review-root/pr123/gpt"
    gpt_dir.mkdir(parents=True, exist_ok=True)
    for i in range(1, 11):
        wid = f"WU{i:02d}"
        (gpt_dir / f"{wid}.json").write_text(
            json.dumps(
                {
                    "verdict": "PASS",
                    "core_flow": wid,
                    "findings": [
                        {
                            "id": f"{wid}-F1",
                            "severity": "S0",
                            "evidence": "REPRODUCED",
                            "file_func": "f:1",
                            "condition": "condition",
                            "minimal_fix": "fix",
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )

    result = subprocess.run(
        ["bash", str(SCRIPTS / "aside/gdriver.sh"), "INTEG"],
        cwd=ROOT,
        env=base_env(tmp_path),
        text=True,
        capture_output=True,
    )

    summary = json.loads((gpt_dir / "wu-summary.json").read_text(encoding="utf-8"))
    assert "WU10" in summary
    assert result.returncode != 0


def test_driver_stops_when_wu_checker_reports_gap(tmp_path: Path) -> None:
    write_plan(tmp_path, first_files=["README.md"])
    prd = tmp_path / "review-root/pr123"
    (prd / "WU01-raw.txt").write_text(completed_wu_raw(SHA, reviewed=[]), encoding="utf-8")

    result = subprocess.run(
        ["bash", str(SCRIPTS / "aside/driver.sh"), "WU01"],
        cwd=ROOT,
        env=base_env(tmp_path),
        text=True,
        capture_output=True,
    )

    assert result.returncode == 6
    assert "STOP_WU_CHECK" in result.stdout
    assert "ALL_DONE" not in result.stdout
