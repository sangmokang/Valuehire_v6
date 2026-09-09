import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

ROOT = Path(__file__).resolve().parents[2]
MUTATIONS = ROOT / "scripts" / "acceptance-hs-kickoff-mutations.sh"


@dataclass(frozen=True)
class Case:
    name: str
    out_log: str
    expect: str
    wanted_prefix: str


def extract_negative_function() -> str:
    source = MUTATIONS.read_text(encoding="utf-8")
    start = source.index("\nnegative() {") + 1
    end = source.index('\n\nnegative "음성1', start)
    return source[start:end]


def clean_env() -> dict[str, str]:
    return {
        key: value
        for key, value in os.environ.items()
        if not key.startswith("GIT_") and key not in {"BASH_ENV", "ENV"}
    }


def call_negative(tmp_path: Path, out_log: str, expect: str) -> subprocess.CompletedProcess[str]:
    harness = tmp_path / "call-negative.sh"
    script = f"""#!/usr/bin/env bash
set -u
TMP="$1"
OUT_LOG="$2"
EXPECT="$3"
WT="$TMP/fixture"
mkdir -p "$WT"
printf '%s\\n' clean > "$WT/changed.txt"
checked=0
fail=0
pass() {{ echo "PASS: $1"; checked=$((checked+1)); }}
failc() {{ echo "FAIL: $1"; checked=$((checked+1)); fail=1; }}
make_fixture() {{ return 0; }}
tree_hash() {{ shasum "$WT/changed.txt" | cut -d' ' -f1; }}
run_target() {{ printf '%s\\n' "$OUT_LOG" > "$TMP/out.log"; echo 1; }}
{extract_negative_function()}
negative fixture 'printf changed > "$WT/changed.txt"' "$EXPECT"
echo "CHECKED: $checked"
exit "$fail"
"""
    harness.write_text(script, encoding="utf-8")
    return subprocess.run(
        ["bash", str(harness), str(tmp_path), out_log, expect],
        cwd=ROOT,
        env=clean_env(),
        text=True,
        capture_output=True,
        check=False,
    )


CASES = (
    Case(
        name="accepts the intended reason",
        out_log="FAIL: CI 배선 불량 — 본 검사=명령다름 자기 변이=OK",
        expect="CI 배선 불량",
        wanted_prefix="PASS: ",
    ),
    Case(
        name="rejects another failure reason that only contains the expected substring",
        out_log="FAIL: unrelated CI 배선 불량 suffix but not the intended verifier line",
        expect="CI 배선 불량",
        wanted_prefix="FAIL: ",
    ),
    Case(
        name="rejects expected reason when immediately followed by another character",
        out_log="FAIL: CI 배선 불량XYZ",
        expect="CI 배선 불량",
        wanted_prefix="FAIL: ",
    ),
    Case(
        name="treats regex metacharacters in expected reason literally",
        out_log="FAIL: unrelated line without the literal token",
        expect=".*",
        wanted_prefix="FAIL: ",
    ),
    Case(
        name="accepts literal expected reason that contains regex metacharacters",
        out_log="FAIL: .* appears here",
        expect=".*",
        wanted_prefix="PASS: ",
    ),
    Case(
        name="ignores PASS bait when failure line has the wrong reason",
        out_log="PASS: bait says CI 배선 불량\nFAIL: unrelated actual failure",
        expect="CI 배선 불량",
        wanted_prefix="FAIL: ",
    ),
    Case(
        name="preserves spaces quotes and dollars through argv",
        out_log="FAIL: path '/tmp/with space/$HOME' did not match",
        expect="path '/tmp/with space/$HOME'",
        wanted_prefix="PASS: ",
    ),
    Case(
        name="rejects empty expected reason",
        out_log="FAIL: any failure line",
        expect="",
        wanted_prefix="FAIL: ",
    ),
    Case(
        name="rejects empty log",
        out_log="",
        expect="CI 배선 불량",
        wanted_prefix="FAIL: ",
    ),
    Case(
        name="accepts literal expected reason containing backslashes",
        out_log=r"FAIL: path C:\\tmp\\fixture did not match",
        expect=r"path C:\\tmp\\fixture",
        wanted_prefix="PASS: ",
    ),
)


@pytest.mark.parametrize("case", CASES, ids=lambda case: case.name)
def test_negative_matches_expected_failure_reason_on_actual_fail_line(
    tmp_path: Path, case: Case
) -> None:
    result = call_negative(tmp_path, case.out_log, case.expect)

    assert result.returncode == (0 if case.wanted_prefix == "PASS: " else 1), result.stdout
    assert result.stdout.startswith(case.wanted_prefix), result.stdout
    assert "CHECKED: 1" in result.stdout


@pytest.mark.parametrize(
    ("reason", "message"),
    [
        ("행 없음", "처분표에 PR #13 행 없음"),
        ("대상 칸에 다른 대상", "PR #13 행의 대상 칸에 다른 대상 1개가 함께 적혀 있다 — 대상마다 자기 행이 있어야 한다"),
        ("처분이 둘 이상", "PR #13 행이 2개 — 같은 대상에 처분이 둘 이상이면 결론이 무엇인지 정해지지 않는다"),
        ("판정 문서 없음", "판정 문서 없음/빈 파일/첫 줄 VERDICT 아님 (verdict-*.md)"),
    ],
)
@pytest.mark.parametrize("bait", [False, True], ids=["canonical", "unrelated-context"])
def test_legacy_reason_requires_its_canonical_message(
    tmp_path: Path, reason: str, message: str, bait: bool
) -> None:
    output = f"FAIL: unrelated diagnostic quotes {message}" if bait else f"FAIL: {message}"
    result = call_negative(tmp_path, output, reason)
    assert result.returncode == int(bait), result.stdout


@settings(max_examples=16, deadline=None, derandomize=True)
@given(token=st.text(alphabet="abcXYZ012.*[]^$\\", min_size=1, max_size=12))
def test_literal_reason_survives_character_combinations(token: str) -> None:
    with TemporaryDirectory() as directory:
        result = call_negative(Path(directory), f"FAIL: token {token} — details", f"token {token}")
    assert result.returncode == 0, result.stdout


@settings(max_examples=12, deadline=None, derandomize=True)
@given(extra=st.text(alphabet="abcXYZ012", min_size=1, max_size=12))
def test_unrelated_context_and_word_extensions_never_count(extra: str) -> None:
    for output in (f"FAIL: {extra} CI 배선 불량", f"FAIL: CI 배선 불량{extra}"):
        with TemporaryDirectory() as directory:
            result = call_negative(Path(directory), output, "CI 배선 불량")
        assert result.returncode == 1, result.stdout
