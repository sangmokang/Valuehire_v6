import os
import shutil
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
ACCEPTANCE = ["bash", "scripts/verify/run-acceptance.sh", "scripts/acceptance-hs-kickoff.sh"]
VERDICT = "docs/engineering/humansearch-kickoff-ledger-verdict-0000-00-00.md"

FIXTURE_FILES = (
    ".github/workflows/verify.yml",
    "docs/engineering/goal-prompts/humansearch-L0-kickoff-2026-08-16.md",
    "docs/engineering/goal-prompts/humansearch-journey-kickoff-2026-09-07.md",
    "docs/engineering/history/resume-evidence-supabase-archive-goal-2026-08-17.md",
    "docs/engineering/history/resume-evidence-supabase-implementation-prompt-2026-08-17.md",
    "docs/engineering/hs-observe-url-crash-goal-2026-08-25.md",
    "docs/engineering/humansearch-branch-disposition-2026-09-07.md",
    "docs/engineering/verdicts/hs-observe-url-crash.verdict.json",
    "docs/sot/verification-commands.md",
    "humansearch/src/humansearch/observe.py",
    "scripts/acceptance-hs-kickoff.sh",
    "scripts/verify/list-workflow-steps.py",
    "scripts/verify/run-acceptance.sh",
)
OPTIONAL_RUNTIME_FILES = (
    "scripts/verify/check-hs-kickoff-identities.py",
    "scripts/verify/hs-kickoff-confusables-17.0.0.json",
)


@dataclass(frozen=True)
class Result:
    returncode: int
    stdout: str
    stderr: str


@dataclass(frozen=True)
class Mutation:
    name: str
    expected_fail: str
    edit: Callable[[Path], None]


def clean_env() -> dict[str, str]:
    return {
        key: value
        for key, value in os.environ.items()
        if not key.startswith("GIT_") and key not in {"BASH_ENV", "ENV"}
    }


def copy_fixture(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    for rel in FIXTURE_FILES:
        src = ROOT / rel
        dst = repo / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    for rel in OPTIONAL_RUNTIME_FILES:
        src = ROOT / rel
        if src.is_file():
            dst = repo / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
    verdict = repo / VERDICT
    verdict.parent.mkdir(parents=True, exist_ok=True)
    verdict.write_text("VERDICT: PASS\n\npytest fixture verdict, not a real review.\n", encoding="utf-8")
    env = clean_env()
    subprocess.run(["git", "init", "-q"], cwd=repo, env=env, check=True)
    subprocess.run(["git", "add", "."], cwd=repo, env=env, check=True)
    subprocess.run(
        ["git", "-c", "user.name=test", "-c", "user.email=test@example.invalid", "commit", "-qm", "fixture"],
        cwd=repo,
        env=env,
        check=True,
    )
    return repo


def run_acceptance(repo: Path) -> Result:
    proc = subprocess.run(
        ACCEPTANCE,
        cwd=repo,
        env=clean_env(),
        text=True,
        capture_output=True,
        check=False,
    )
    return Result(proc.returncode, proc.stdout, proc.stderr)


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    assert text.count(old) == 1
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def insert_before(path: Path, marker: str, prefix: str) -> None:
    replace_once(path, marker, prefix + marker)


def mutate_step_shell(repo: Path) -> None:
    run = "        run: bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-kickoff.sh"
    insert_before(repo / ".github/workflows/verify.yml", run, '        shell: bash -c "true" {0}\n')


def mutate_default_shell(repo: Path) -> None:
    insert_before(repo / ".github/workflows/verify.yml", "jobs:\n", "defaults:\n  run:\n    shell: cat\n\n")


def mutate_step_bash_env(repo: Path) -> None:
    bait = repo / "scripts/v1-bait-env.sh"
    bait.write_text("exit 0\n", encoding="utf-8")
    run = "        run: bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-kickoff.sh"
    insert_before(
        repo / ".github/workflows/verify.yml",
        run,
        "        env:\n          BASH_ENV: scripts/v1-bait-env.sh\n",
    )


def mutate_top_bash_env(repo: Path) -> None:
    bait = repo / "scripts/v1-bait-env.sh"
    bait.write_text("exit 0\n", encoding="utf-8")
    insert_before(repo / ".github/workflows/verify.yml", "jobs:\n", "env:\n  BASH_ENV: scripts/v1-bait-env.sh\n\n")


def mutate_pr_131(repo: Path) -> None:
    replace_once(
        repo / "docs/engineering/humansearch-branch-disposition-2026-09-07.md",
        "| 1 | PR #13 `task/humansearch-g3-portal-constants`",
        "| 1 | PR #131 `task/humansearch-g3-portal-constants`",
    )


def mutate_verdict_passed(repo: Path) -> None:
    replace_once(repo / VERDICT, "VERDICT: PASS\n", "VERDICT: PASSED\n")


MUTATIONS = (
    Mutation("step shell no-op is rejected", "CI 배선 불량 — 본 검사=약화", mutate_step_shell),
    Mutation("top defaults run shell is rejected", "워크플로를 정규 형식으로 읽지 못했다", mutate_default_shell),
    Mutation("step BASH_ENV is rejected", "CI 배선 불량 — 본 검사=약화", mutate_step_bash_env),
    Mutation("top BASH_ENV is rejected", "워크플로를 정규 형식으로 읽지 못했다", mutate_top_bash_env),
    Mutation("PR 131 does not satisfy PR 13", "처분표에 PR #13 행 없음", mutate_pr_131),
    Mutation("VERDICT PASSED suffix is rejected", "판정 문서 없음/빈 파일/첫 줄 VERDICT 아님", mutate_verdict_passed),
)


def fail_lines(result: Result) -> list[str]:
    combined = result.stdout + result.stderr
    return [line for line in combined.splitlines() if line.startswith("FAIL: ")]


def assert_rejected(result: Result, expected_fail: str) -> None:
    combined = result.stdout + result.stderr
    assert result.returncode != 0, combined
    assert "CHECKED: 12" in combined
    assert any(expected_fail in line for line in fail_lines(result)), combined


def test_clean_hs_kickoff_fixture_passes(tmp_path: Path) -> None:
    repo = copy_fixture(tmp_path)

    result = run_acceptance(repo)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "CHECKED: 12" in result.stdout
    assert "OK(run-acceptance)" in result.stdout


@pytest.mark.parametrize("mutation", MUTATIONS, ids=lambda mutation: mutation.name)
def test_hs_kickoff_rejects_false_passes_in_workflow_contract(
    tmp_path: Path, mutation: Mutation
) -> None:
    repo = copy_fixture(tmp_path)

    mutation.edit(repo)
    result = run_acceptance(repo)

    assert_rejected(result, mutation.expected_fail)
