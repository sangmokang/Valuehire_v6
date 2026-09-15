"""HS-03.02 인수 스크립트 fail-closed 검사 — **비재귀** 모듈.

왜 별도 모듈인가 (Codex V1 2차 F0302-4 잔여):
  인수 스크립트의 pytest 단계가 이 시험들을 `-k "not acceptance_aborts"` 로 빼고 있었다.
  그러면 필수 음성 대조군 하나(create-table 스캔 실패)가 인수 실행 안에서 실제로 돌지
  않는다. 제외하는 대신 **재귀하지 않는 형태**로 옮겨 필터 없이 전부 돌게 한다.

재귀를 끊는 방법: 사본을 임시 디렉터리에 두고 `HS0302_ACCEPTANCE_DEPTH` 를 미리 올린
  상태로 띄운다. 사본은 시험 단계에 닿기 전에 주입한 결함으로 먼저 끝나고, 설령
  fail-open 으로 퇴화해도 깊이 차단이 시험 단계를 막아 새 사본이 생기지 않는다.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

_ACCEPTANCE = "scripts/acceptance-hs-0302.sh"
_NESTED_DEPTH = "5"
_SUBPROCESS_TIMEOUT = 300


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _acceptance_text() -> str:
    return (_repo_root() / _ACCEPTANCE).read_text(encoding="utf-8")


def _run_copy(script: Path) -> subprocess.CompletedProcess[str]:
    """사본을 깊이 표시와 함께 띄운다. 깊이가 재귀를, timeout 이 폭주를 막는다."""

    env = dict(os.environ)
    env["HS0302_ACCEPTANCE_DEPTH"] = _NESTED_DEPTH
    return subprocess.run(
        ["bash", str(script)],
        cwd=_repo_root(),
        capture_output=True,
        text=True,
        check=False,
        env=env,
        timeout=_SUBPROCESS_TIMEOUT,
    )


def _assert_fail_closed(result: subprocess.CompletedProcess[str], reason: str) -> None:
    """필수 검사를 못 했으면 그 자리에서 끝나야 한다.

    종료값만 보면 부족하다 — 건너뛴 뒤 다른 경로로 2 가 나와도 통과한다.
    NOT_RUN 뒤에 판정(PASS)이 한 줄이라도 이어지면 그것이 fail-open 이다.
    """

    lines = result.stdout.splitlines()
    assert result.returncode == 2, result.stdout + result.stderr
    not_run_at = [index for index, line in enumerate(lines) if line.startswith("NOT_RUN:")]
    assert not_run_at, result.stdout
    assert any(reason in lines[index] for index in not_run_at), result.stdout
    trailing = [line for line in lines[not_run_at[0] + 1 :] if line.startswith("PASS:")]
    assert trailing == [], f"NOT_RUN 뒤에 판정이 이어졌다: {trailing}"
    assert "OK(run-acceptance)" not in result.stdout


def test_acceptance_aborts_when_base_commit_is_missing(tmp_path: Path) -> None:
    """기준 SHA 를 못 찾으면 건너뛰고 통과하는 대신 그 자리에서 끝나야 한다."""

    original = _acceptance_text()
    assert "BASE_SHA=7473ec8" in original
    copy = tmp_path / "acceptance-missing-base.sh"
    copy.write_text(
        original.replace("BASE_SHA=7473ec8", "BASE_SHA=0000000000000000000000000000000000000000"),
        encoding="utf-8",
    )

    _assert_fail_closed(_run_copy(copy), "기준 커밋")


def test_acceptance_aborts_when_create_table_scan_fails(tmp_path: Path) -> None:
    """우회 표 스캔이 오류를 내면 그 판정을 포기한 채 통과해서는 안 된다."""

    original = _acceptance_text()
    assert "GREP=/usr/bin/grep" in original
    fake_grep = tmp_path / "fake-grep"
    fake_grep.write_text(
        "#!/bin/bash\n"
        'for arg in "$@"; do\n'
        '  case "$arg" in\n'
        "    *create*table*) exit 2 ;;\n"
        "  esac\n"
        "done\n"
        'exec /usr/bin/grep "$@"\n',
        encoding="utf-8",
    )
    fake_grep.chmod(0o755)
    copy = tmp_path / "acceptance-broken-scan.sh"
    copy.write_text(
        original.replace("GREP=/usr/bin/grep", f"GREP={fake_grep}"),
        encoding="utf-8",
    )

    _assert_fail_closed(_run_copy(copy), "create table 스캔")


def test_acceptance_pytest_step_runs_every_selected_test_without_a_filter() -> None:
    """통과 하한이 아니라 **수집 건수와 정확히 일치**해야 한다.

    함수 정의 수를 하한으로 쓰면 매개변수 확장 때문에 실행 건수가 부풀어, 필수 시험이
    빠져도 `passed >= total` 이 성립한다(Codex V1 2차). 그리고 자기 호출 시험을
    `-k` 로 빼면 그 음성 대조군이 인수 실행 안에서 돌지 않는다.
    """

    text = _acceptance_text()

    assert "-k \"not acceptance_aborts\"" not in text, "인수 실행이 필수 시험을 필터로 뺀다"
    assert "--collect-only" in text, "수집 건수와 대조하지 않는다"
    assert "test_hs_0302_acceptance_probe.py" in text, "비재귀 probe 모듈이 인수 실행에 없다"
    assert "deselected" in text, "deselected 를 실패로 보지 않는다"


def test_acceptance_self_check_covers_the_create_table_scan_path() -> None:
    """자기 검사가 기준 SHA 만 대체하면 스캔 실패 경로는 인수 실행 밖에 남는다."""

    text = _acceptance_text()

    assert "failclosed_probe" in text
    assert "failclosed_scan_probe" in text, "스캔 실패 경로의 자기 검사가 없다"


def test_acceptance_script_has_no_fail_open_skip_helper() -> None:
    """`skip_item` 같은 '건수만 늘리고 실패는 안 하는' 보조가 남아 있으면 안 된다."""

    text = _acceptance_text()

    assert "skip_item" not in text, "필수 검사 불가를 성공으로 접는 보조가 남아 있다"
    assert "exit 2" in text, "NOT_RUN 뒤 즉시 종료하는 경로가 없다"
    assert "HS0302_ACCEPTANCE_DEPTH" in text, "중첩 실행 재귀 차단이 없다"
    # 차단이 변이 대상 보조(abort_not_run)를 거치면 같은 변이에 함께 죽는다(실측).
    assert 'abort_not_run "중첩' not in text, "중첩 차단이 fail-closed 보조와 같은 경로를 쓴다"
    assert os.access(_repo_root() / _ACCEPTANCE, os.X_OK)
