import importlib
import json
import re
import shutil
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Protocol, cast

import pytest


class ResultLike(Protocol):
    returncode: int
    stdout: str
    stderr: str


class Hs0001Fixture(Protocol):
    copy_fixture: Callable[[Path], Path]
    run_acceptance: Callable[[Path], ResultLike]
    clean_env: Callable[[], dict[str, str]]


ROOT = Path(__file__).resolve().parents[2]
TESTS = ROOT / "humansearch" / "tests"
if str(TESTS) not in sys.path:
    sys.path.insert(0, str(TESTS))

fixture = cast(Hs0001Fixture, importlib.import_module("test_hs_0001"))
base_copy_fixture = fixture.copy_fixture
run_acceptance = fixture.run_acceptance
clean_env = fixture.clean_env

RUNTIME_FIXTURE_FILES = (
    "scripts/verify/check-hs-kickoff-identities.py",
    "scripts/verify/hs-kickoff-confusables-17.0.0.json",
)
WORKFLOW = Path(".github/workflows/verify.yml")
SOT = Path("docs/sot/verification-commands.md")
DISPOSITION = Path("docs/engineering/humansearch-branch-disposition-2026-09-07.md")
DATA = Path("scripts/verify/hs-kickoff-confusables-17.0.0.json")
IDENTITY_CHECKER = Path("scripts/verify/check-hs-kickoff-identities.py")


def copy_fixture(tmp_path: Path) -> Path:
    repo = base_copy_fixture(tmp_path)
    # The RED commit intentionally precedes these runtime files. Once the shell calls
    # them, absence is itself an acceptance failure rather than a skipped assertion.
    for rel in RUNTIME_FIXTURE_FILES:
        source = ROOT / rel
        if source.is_file():
            destination = repo / rel
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
    return repo


def append_workflow_and_sot_step(repo: Path, name: str) -> None:
    workflow = repo / WORKFLOW
    workflow.write_text(
        workflow.read_text(encoding="utf-8")
        + f"\n      - name: {name}\n        if: false\n        run: echo skipped\n",
        encoding="utf-8",
    )

    sot = repo / SOT
    text = sot.read_text(encoding="utf-8")
    assert text.count("워크플로 스텝 30개") == 1
    text = text.replace("워크플로 스텝 30개", "워크플로 스텝 31개", 1)
    text, replacements = re.subn(
        r"(^\| 30 \|.*$)",
        rf"\1\n| 31 | {name} | `echo skipped` |",
        text,
        count=1,
        flags=re.MULTILINE,
    )
    assert replacements == 1
    sot.write_text(text, encoding="utf-8")


def append_disposition_shadow(repo: Path, target: str, spoofed: str) -> None:
    path = repo / DISPOSITION
    text = path.read_text(encoding="utf-8")
    row = next(line for line in text.splitlines() if target in line and line.startswith("| "))
    shadow = re.sub(r"^\| [1-6] \|", "| 7 |", row, count=1).replace(target, spoofed, 1)
    path.write_text(text + "\n" + shadow + "\n", encoding="utf-8")


def replace_disposition_target(repo: Path, target: str, spoofed: str) -> None:
    path = repo / DISPOSITION
    lines = path.read_text(encoding="utf-8").splitlines()
    index = next(i for i, line in enumerate(lines) if line.startswith("| ") and target in line)
    lines[index] = lines[index].replace(target, spoofed, 1)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def replace_workflow_and_sot_name(repo: Path, old: str, new: str) -> None:
    workflow = repo / WORKFLOW
    workflow_text = workflow.read_text(encoding="utf-8")
    assert workflow_text.count(f"- name: {old}") == 1
    workflow.write_text(workflow_text.replace(f"- name: {old}", f"- name: {new}", 1))

    sot = repo / SOT
    sot_text = sot.read_text(encoding="utf-8")
    assert sot_text.count(f"| {old} |") == 1
    sot.write_text(sot_text.replace(f"| {old} |", f"| {new} |", 1))


def combined(result: ResultLike) -> str:
    return result.stdout + result.stderr


def assert_spoof_rejected(result: ResultLike, *expected: str) -> None:
    output = combined(result)
    assert result.returncode != 0, output
    assert "CHECKED: 12" in output
    for fragment in expected:
        assert fragment in output, output


def test_normal_multilingual_and_unrelated_fullwidth_step_name_passes(tmp_path: Path) -> None:
    repo = copy_fixture(tmp_path)
    append_workflow_and_sot_step(
        repo,
        "정상 한글 山田太郎 · محمد · hs-kickoff 설명 · hｓ-kickoff-other · Überprüfung ＡＢＣ",
    )
    append_disposition_shadow(repo, "PR #13", "ＰR #131")

    result = run_acceptance(repo)

    assert result.returncode == 0, combined(result)
    assert "CHECKED: 12" in result.stdout
    assert "OK(run-acceptance)" in result.stdout


@pytest.mark.parametrize(
    "spoofed,token",
    (
        ("인수 검사 ｈｓ－kickoff (동시 존재)", "hs-kickoff"),
        ("인수 검사 hѕ-kickoff (동시 존재)", "hs-kickoff"),
        ("인수 검사 hs-kickοff (동시 존재)", "hs-kickoff"),
        ("인수 검사 hs-kickoff-mutatiοns (동시 존재)", "hs-kickoff-mutations"),
    ),
)
def test_spoofed_workflow_and_sot_step_names_are_rejected(
    tmp_path: Path,
    spoofed: str,
    token: str,
) -> None:
    repo = copy_fixture(tmp_path)
    append_workflow_and_sot_step(repo, spoofed)

    result = run_acceptance(repo)

    assert_spoof_rejected(
        result,
        f"SPOOF: workflow-step line=31 token={token}",
        f"SPOOF: sot-step line=31 token={token}",
    )


@pytest.mark.parametrize(
    "target,spoofed",
    (
        ("PR #13", "ＰR #13"),
        ("PR #54", "PＲ #54"),
        ("PR #15", "ＰＲ #15"),
        ("task/hs-d1-permit", "ｔask/hs-d1-permit"),
        ("task/hs-l1-malformed-url-fix", "task/hs-l1-malformed-url-fіx"),
        ("task/hs-observe-url-crash", "task/hs-observe-url-craѕh"),
    ),
)
def test_spoofed_disposition_targets_are_rejected(
    tmp_path: Path,
    target: str,
    spoofed: str,
) -> None:
    repo = copy_fixture(tmp_path)
    append_disposition_shadow(repo, target, spoofed)

    result = run_acceptance(repo)

    assert_spoof_rejected(result, f"SPOOF: disposition-target line=7 token={target}")


@pytest.mark.parametrize("spoofed", ("PR #13１", "ｘPR #13"))
def test_confusable_token_boundaries_do_not_count_as_disposition_target(
    tmp_path: Path,
    spoofed: str,
) -> None:
    repo = copy_fixture(tmp_path)
    replace_disposition_target(repo, "PR #13", spoofed)

    result = run_acceptance(repo)

    assert_spoof_rejected(result, "SPOOF: disposition-target line=1 token=PR #13")


def test_confusable_token_boundary_does_not_count_as_workflow_name(tmp_path: Path) -> None:
    repo = copy_fixture(tmp_path)
    old = "인수 검사 hs-kickoff (HumanSearch 착수 정리 · WU-0A)"
    new = "인수 검사 ｘhs-kickoff (HumanSearch 착수 정리 · WU-0A)"
    replace_workflow_and_sot_name(repo, old, new)

    result = run_acceptance(repo)

    assert_spoof_rejected(
        result,
        "SPOOF: workflow-step line=29 token=hs-kickoff",
        "SPOOF: sot-step line=29 token=hs-kickoff",
    )


def mutate_missing_data(repo: Path) -> None:
    path = repo / DATA
    if path.exists():
        path.unlink()


def mutate_invalid_json(repo: Path) -> None:
    path = repo / DATA
    if path.exists():
        path.write_text("{not-json}\n", encoding="utf-8")


def mutate_wrong_mapping_count(repo: Path) -> None:
    path = repo / DATA
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
        data["selection"]["mapping_count"] -= 1
        path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


def mutate_same_count_mapping(repo: Path) -> None:
    path = repo / DATA
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
        first_group = next(iter(data["confusables"].values()))
        first_group[0] = "10FFFF"
        path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


@pytest.mark.parametrize(
    "mutate",
    (
        mutate_missing_data,
        mutate_invalid_json,
        mutate_wrong_mapping_count,
        mutate_same_count_mapping,
    ),
    ids=("missing", "invalid-json", "wrong-count", "same-count-content"),
)
def test_mapping_data_errors_fail_closed(tmp_path: Path, mutate: Callable[[Path], None]) -> None:
    repo = copy_fixture(tmp_path)
    mutate(repo)

    result = run_acceptance(repo)

    output = combined(result)
    assert result.returncode != 0, output
    assert "CHECKED: 12" in output
    assert "ERROR: Unicode 매핑 데이터" in output


@pytest.mark.parametrize(
    "payload",
    (b"", b"\n", b"hs-kickoff\xff\n"),
    ids=("zero-bytes", "empty-name", "invalid-utf8"),
)
def test_identity_checker_rejects_empty_or_invalid_utf8_input(payload: bytes) -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / IDENTITY_CHECKER),
            "--kind",
            "workflow-step",
            "--token",
            "hs-kickoff",
        ],
        cwd=ROOT,
        env=clean_env(),
        input=payload,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 2, result.stdout + result.stderr
    assert b"ERROR:" in result.stderr
