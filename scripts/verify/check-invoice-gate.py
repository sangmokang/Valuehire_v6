#!/usr/bin/env python3
"""Prove the Invoice gate reports real failures instead of trusting its own text.

Why this is not a string check
------------------------------
`hooks/pre-push:87-90` already recorded the lesson: parsing text for forbidden
shapes buys one bypass for every rule added. Two bypasses were reproduced on
2026-09-05 against the previous version of this file:

  * append `fail=0; echo "VERDICT: PASS"; exit 0` to `acceptance-invoice.sh` —
    the required lines were still present, so the gate passed;
  * put `exit 0` as the first line of the workflow step's `run` block — the
    required lines were still present, so the gate passed.

So this gate observes behaviour instead:

  1. **Command trace** — the Invoice workflow steps are executed with a PATH of
     recording stubs. A command that is never invoked is never recorded, so
     `exit 0`, `echo`, comments, and deletion all fail the same way.
  2. **Differential self-test** — an isolated copy of the Invoice tree is
     mutated so the unit tests and the PostgreSQL test genuinely fail, and the
     acceptance script is run there. A harness that still reports PASS is a
     fake harness.

What this does not catch
------------------------
The command trace executes a step's `run` block regardless of its `if:`, so a step
that is registered, calls the right commands, and is switched off with a condition
still traces clean here. That shape is caught by
`scripts/verify/check-ci-step-integrity.sh`, which parses the workflow and rejects
any conditional or failure-ignoring step (measured on 2026-09-05: injecting
`if: ${{ false }}` leaves this gate at exit 0 and takes that checker to exit 1).
Nor does this gate defend anything outside Invoice.

Scope is Invoice only. Exit 0 PASS, 1 FAIL, 4 BLOCKED (environment, not defect; psql uses 3).
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path


REQUIRED_ACCEPTANCE_LINES = {
    'python3 -m unittest discover -s tools/invoice/tests -v >"$test_log" 2>&1',
    "bash tools/invoice/tests/test_postgres_integrity.sh",
}
# 워크플로에서 "글자가 있는가"가 아니라 "실제로 불렸는가"를 볼 명령.
# argv 전체를 그대로 맞춘다. 부분문자열로 보면
# `python3 scripts/verify/check-invoice-gate.py --wiring-only` 처럼 인자를 하나 붙여
# 약한 모드로 갈아치우는 우회가 통과한다(2026-09-05 V1 반례).
REQUIRED_INVOCATIONS = (
    ("bash", "scripts/verify/run-acceptance.sh", "scripts/acceptance-invoice.sh"),
    ("python3", "scripts/verify/check-invoice-gate.py"),
)
# 인자에는 NUL 이 들어갈 수 없다(execve 가 막는다). 그래서 인자는 NUL 로 잇고 기록은
# NUL 두 개로 끊는다. 개행이나 다른 구분자를 쓰면 인자 안에 그 문자를 넣어 기록을
# 위조할 수 있다(2026-09-05 실측: 개행 + 0x1f 로 가짜 호출 한 줄을 만들어 냈다).
STUBBED_COMMANDS = ("python3", "python", "bash", "sh", "make", "npm", "node", "env")
COPY_PATHS = (
    "contracts/invoice",
    "docs/sot/invoice.md",
    "docs/sot/invoice-storage.md",
    "supabase/migrations",
    "tools/invoice",
    "scripts/verify",
    "scripts/acceptance-invoice.sh",
    ".codex/skills/invoice",
    ".claude/skills/invoice",
    ".github/workflows/verify.yml",
)
# 격리 사본에서 실제 시험을 깨뜨리는 변이. 문법 오류가 아니라 동작 변경이라
# "올바른 이유로" 실패한다.
UNIT_CANARY = (
    "\n\ndef digest_bytes(value: bytes) -> str:  # invoice gate canary\n"
    '    return "0" * 64\n'
)
POSTGRES_CANARY = "\ndo $$ begin raise exception 'invoice gate canary'; end; $$;\n"
CANARY_TIMEOUT = 900


def _clean_env(**extra: str) -> dict[str, str]:
    env = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith("GIT_") and key != "PYTHONPYCACHEPREFIX"
    }
    env.update(extra)
    return env


def code_lines(path: Path) -> set[str]:
    if not path.is_file():
        raise ValueError(f"missing file: {path}")
    return {
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }


def workflow_document(path: Path) -> dict:
    """Parse the workflow with Ruby's Psych — the same parser CI already relies on."""
    result = subprocess.run(
        ["ruby", "-rpsych", "-rjson", "-rdate", "-e",
         "puts Psych.safe_load(File.read(ARGV[0]), aliases: true, "
         "permitted_classes: [Date, Time]).to_json", str(path)],
        capture_output=True, text=True, timeout=60,
    )
    if result.returncode != 0:
        raise ValueError(f"workflow cannot be parsed: {result.stderr.strip()[:200]}")
    return json.loads(result.stdout)


def invoice_run_blocks(document: dict) -> list[str]:
    blocks = []
    for job in (document.get("jobs") or {}).values():
        if not isinstance(job, dict):
            continue
        for step in job.get("steps") or []:
            if not isinstance(step, dict):
                continue
            run = step.get("run")
            if isinstance(run, str) and "invoice" in run.lower():
                blocks.append(run)
    return blocks


def traced_invocations(
    script: str, stub_exit: int = 0
) -> tuple[list[tuple[str, ...]], int]:
    """Run a workflow `run` block with recording stubs and report what it called."""
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        bin_dir = root / "bin"
        bin_dir.mkdir()
        trace = root / "trace"
        for name in STUBBED_COMMANDS:
            stub = bin_dir / name
            stub.write_text(
                "#!/bin/sh\n"
                f'{{ printf "%s\\000" "{name}" "$@"; printf "\\000"; }} >> "{trace}"\n'
                f"exit {stub_exit}\n"
            )
            stub.chmod(0o755)
        work = root / "work"
        work.mkdir()
        step = root / "step.sh"
        step.write_text(script)
        result = subprocess.run(
            ["/bin/bash", "-e", str(step)], cwd=work,
            env={"PATH": f"{bin_dir}:/usr/bin:/bin", "HOME": str(root)},
            capture_output=True, timeout=120,
        )
        calls: list[tuple[str, ...]] = []
        if trace.exists():
            data = trace.read_bytes().decode("utf-8", errors="replace")
            calls = [
                tuple(record.split("\0"))
                for record in data.split("\0\0")
                if record
            ]
        return calls, result.returncode


def check_workflow_execution(workflow: Path) -> list[str]:
    try:
        blocks = invoice_run_blocks(workflow_document(workflow))
    except (ValueError, OSError, json.JSONDecodeError, subprocess.SubprocessError) as error:
        return [f"워크플로를 읽지 못했다 (fail-closed): {error}"]
    if not blocks:
        return ["워크플로에 Invoice 스텝이 하나도 없다 — 스텝 삭제도 우회다"]
    called: list[tuple[str, ...]] = []
    swallowed: list[str] = []
    for block in blocks:
        try:
            calls, _ = traced_invocations(block, stub_exit=0)
            called.extend(calls)
            # 호출됐다는 사실은 "그 실패가 CI 를 빨갛게 만든다"를 뜻하지 않는다.
            # 같은 블록을 실패하는 스텁으로 한 번 더 돌려 종료값이 올라오는지 본다.
            # 백그라운드(&) · 파이프(| cat) · `|| true` 는 여기서 0 이 되어 걸린다.
            _, failure_rc = traced_invocations(block, stub_exit=1)
        except (OSError, subprocess.SubprocessError) as error:
            return [f"Invoice 스텝을 추적 실행하지 못했다: {error}"]
        if failure_rc == 0:
            swallowed.append(" ".join(block.split())[:120])
    problems = [
        f"워크플로 Invoice 스텝이 명령 실패를 삼킨다 (스텝이 종료값 0 으로 끝난다): {block}"
        for block in swallowed
    ]
    for wanted in REQUIRED_INVOCATIONS:
        if wanted not in called:
            problems.append(
                f"워크플로 Invoice 스텝이 `{' '.join(wanted)}` 를 그대로 호출하지 않는다 "
                f"(추적된 호출: {[' '.join(item) for item in called] or '없음'})"
            )
    return problems


def _canary_copy(repo: Path, destination: Path, acceptance: Path | None = None) -> None:
    for relative in COPY_PATHS:
        source = repo / relative
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if source.is_dir():
            shutil.copytree(source, target, ignore=shutil.ignore_patterns("__pycache__"))
        elif source.is_file():
            shutil.copy2(source, target)
        else:
            raise ValueError(f"missing path for the isolated copy: {relative}")
    if acceptance is not None:
        shutil.copy2(acceptance, destination / "scripts" / "acceptance-invoice.sh")
    subprocess.run(
        ["git", "init", "-q"], cwd=destination, env=_clean_env(), check=True, timeout=60
    )
    common = destination / "tools" / "invoice" / "storage_common.py"
    common.write_text(common.read_text(encoding="utf-8") + UNIT_CANARY, encoding="utf-8")
    assertions = destination / "tools" / "invoice" / "tests" / "postgres_runtime_assertions.sql"
    assertions.write_text(
        assertions.read_text(encoding="utf-8") + POSTGRES_CANARY, encoding="utf-8"
    )


def check_broken_tests_are_reported(
    repo: Path, acceptance: Path | None = None
) -> tuple[list[str], list[str]]:
    """Break the tests in an isolated copy; the harness must go red."""
    with tempfile.TemporaryDirectory() as temp:
        copy = Path(temp) / "repo"
        copy.mkdir(parents=True)
        try:
            _canary_copy(repo, copy, acceptance)
        except (OSError, ValueError, subprocess.SubprocessError) as error:
            return [f"격리 사본을 만들지 못했다 (fail-closed): {error}"], []
        try:
            result = subprocess.run(
                ["bash", "scripts/acceptance-invoice.sh"], cwd=copy,
                capture_output=True, text=True, env=_clean_env(), timeout=CANARY_TIMEOUT,
            )
        except (OSError, subprocess.SubprocessError) as error:
            return [f"격리 사본에서 인수 검사를 실행하지 못했다: {error}"], []
    output = f"{result.stdout}\n{result.stderr}"
    problems, blocked = [], []
    if result.returncode == 0:
        problems.append(
            "격리 사본에서 실제 시험을 깨뜨렸는데도 인수 검사가 종료값 0 을 냈다 "
            "— 판정이 시험 결과에서 나오지 않는다"
        )
    if "VERDICT: FAIL" not in output:
        problems.append(
            "깨진 시험에 대해 인수 검사가 VERDICT: FAIL 을 내지 않았다 "
            f"(마지막 출력: {output.strip().splitlines()[-3:] if output.strip() else '없음'})"
        )
    if "FAIL: Invoice 회귀 테스트" not in output:
        problems.append("단위 시험 실패가 인수 검사 판정에 반영되지 않았다")
    if "BLOCKED: PostgreSQL" in output:
        blocked.append(
            "PostgreSQL 서버 바이너리가 없어 PostgreSQL 위조 방어를 증명하지 못했다"
        )
    elif "FAIL: PostgreSQL" not in output:
        problems.append("PostgreSQL 시험 실패가 인수 검사 판정에 반영되지 않았다")
    return problems, blocked


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--acceptance", type=Path, default=Path("scripts/acceptance-invoice.sh"))
    parser.add_argument("--workflow", type=Path, default=Path(".github/workflows/verify.yml"))
    parser.add_argument("--repo", type=Path, default=Path("."))
    parser.add_argument(
        "--wiring-only", action="store_true",
        help="배선 문자열만 확인한다. 인수 검사가 자기를 부를 때 재귀를 끊는 용도이며 "
             "이것만으로는 위조를 막지 못한다.",
    )
    parser.add_argument(
        "--print-copy-paths", action="store_true",
        help="격리 사본에 필요한 경로를 한 줄에 하나씩 출력한다(변이 검사가 읽는다).",
    )
    args = parser.parse_args()
    if args.print_copy_paths:
        print("\n".join(COPY_PATHS))
        return 0

    problems: list[str] = []
    try:
        missing = REQUIRED_ACCEPTANCE_LINES - code_lines(args.acceptance)
    except (OSError, UnicodeError, ValueError) as error:
        print(f"FAIL: {error}")
        return 1
    if missing:
        problems.append(f"인수 검사에 실행 줄이 없다: {sorted(missing)}")

    if args.wiring_only:
        if problems:
            for problem in problems:
                print(f"FAIL: {problem}")
            return 1
        print("PASS: Invoice 인수 검사에 단위·PostgreSQL 실행 줄이 있다 (배선만 확인)")
        return 0

    problems.extend(check_workflow_execution(args.workflow))
    default_acceptance = Path('scripts/acceptance-invoice.sh')
    override = None if args.acceptance == default_acceptance else args.acceptance.resolve()
    broken, blocked = check_broken_tests_are_reported(args.repo.resolve(), override)
    problems.extend(broken)

    if problems:
        for problem in problems:
            print(f"FAIL: {problem}")
        return 1
    if blocked:
        for item in blocked:
            print(f"BLOCKED: {item}")
        return 4
    print(
        "PASS: Invoice 워크플로 스텝이 실제로 명령을 호출하고, 깨진 시험에 대해 "
        "인수 검사가 FAIL 을 낸다"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
