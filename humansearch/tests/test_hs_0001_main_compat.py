import importlib
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Protocol, cast


class ResultLike(Protocol):
    returncode: int
    stdout: str
    stderr: str


class Hs0001Fixture(Protocol):
    copy_fixture: Callable[[Path], Path]
    insert_before: Callable[[Path, str, str], None]
    run_acceptance: Callable[[Path], ResultLike]


ROOT = Path(__file__).resolve().parents[2]
TESTS = ROOT / "humansearch" / "tests"
if str(TESTS) not in sys.path:
    sys.path.insert(0, str(TESTS))

fixture = cast(Hs0001Fixture, importlib.import_module("test_hs_0001"))
copy_fixture = fixture.copy_fixture
insert_before = fixture.insert_before
run_acceptance = fixture.run_acceptance


CONCURRENCY = """concurrency:
  # Same ref supersedes older non-main runs.
  group: verify-${{ github.event_name }}-${{ github.ref }}
  cancel-in-progress: ${{ github.ref != 'refs/heads/main' }}

"""


def add_latest_main_ci_controls(repo: Path) -> None:
    workflow = repo / ".github/workflows/verify.yml"
    insert_before(workflow, "jobs:\n", CONCURRENCY)
    insert_before(workflow, "    steps:\n", "    timeout-minutes: 30\n")


def test_hs_kickoff_accepts_latest_main_ci_concurrency_and_job_timeout(
    tmp_path: Path,
) -> None:
    repo = copy_fixture(tmp_path)

    add_latest_main_ci_controls(repo)
    result = run_acceptance(repo)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "CHECKED: 12" in result.stdout
    assert "OK(run-acceptance)" in result.stdout
