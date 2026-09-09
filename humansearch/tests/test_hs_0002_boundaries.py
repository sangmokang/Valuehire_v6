"""Additional behavioral boundaries discovered by independent review."""

import subprocess
import sys
from pathlib import Path

import pytest
from test_hs_0002 import ROOT, call_negative, clean_env


@pytest.mark.parametrize("expected", ["", " ", "\t", " \t ", "\u3000"])
def test_blank_reason_cannot_identify_a_failure(tmp_path: Path, expected: str) -> None:
    result = call_negative(tmp_path, f"FAIL: {expected}", expected)
    assert result.returncode == 1, result.stdout
    assert result.stdout.startswith("FAIL: "), result.stdout


@pytest.mark.parametrize(
    ("output", "expected", "accepted"),
    [
        ("CI 배선 불량", "CI 배선 불량", False),
        ("PASS: CI 배선 불량", "PASS: CI 배선 불량", False),
        ("FAIL: PASS: CI 배선 불량", "PASS: CI 배선 불량", True),
        ("FAIL: 처분표에 PR #13 행 없음XYZ", "행 없음", False),
        ("FAIL: CI 배선 불량—details", "CI 배선 불량", False),
        ("FAIL: CI 배선 불량-details", "CI 배선 불량", False),
        ("FAIL: CI 배선 불량\tdetails", "CI 배선 불량", True),
        ("FAIL: CI 배선 불량/details", "CI 배선 불량", True),
        ("FAIL: reason\rX", "reason\rX", False),
        ("FAIL: reason\nX", "reason\nX", False),
        ("FAIL:  literal ", " literal ", True),
        ("FAIL: literal", " literal ", False),
        (
            ("FAIL: PR #13 행의 대상 칸에 다른 대상 0개가 함께 적혀 있다"
             " — 대상마다 자기 행이 있어야 한다"),
            "대상 칸에 다른 대상",
            False,
        ),
        (
            ("FAIL: PR #13 행의 대상 칸에 다른 대상 10개가 함께 적혀 있다"
             " — 대상마다 자기 행이 있어야 한다"),
            "대상 칸에 다른 대상",
            True,
        ),
    ],
)
def test_reason_boundaries_in_actual_negative_call(
    tmp_path: Path, output: str, expected: str, accepted: bool
) -> None:
    result = call_negative(tmp_path, output, expected)
    assert result.returncode == (0 if accepted else 1), result.stdout
    assert "CHECKED: 1" in result.stdout


@pytest.mark.parametrize("kind", ["missing", "directory", "invalid-utf8", "normal"])
def test_cli_reports_unreadable_input_as_error(tmp_path: Path, kind: str) -> None:
    source = tmp_path / "output.log"
    if kind == "directory":
        source.mkdir()
    elif kind == "invalid-utf8":
        source.write_bytes(b"FAIL: reason\xff")
    elif kind == "normal":
        source.write_text("FAIL: reason\n", encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts/verify/has-kickoff-failure.py"), str(source), "reason"],
        cwd=ROOT,
        env=clean_env(),
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == (0 if kind == "normal" else 2), result.stderr
    assert bool(result.stderr) == (kind != "normal")
