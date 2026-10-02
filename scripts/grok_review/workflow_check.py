#!/usr/bin/env python3
"""grok-review 워크플로가 시크릿과 PR 코드를 섞지 않는지 정적 검사한다."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "grok-review.yml"
GATE = ROOT / "scripts" / "grok_review" / "gate.py"
PRODUCTION = ROOT / "scripts" / "grok_review"
CHECKED = 0
FAILED = 0


def record(name: str, ok: bool, detail: str = "") -> None:
    global CHECKED, FAILED
    CHECKED += 1
    suffix = f" — {detail}" if detail else ""
    if ok:
        print(f"PASS: {name}{suffix}")
    else:
        FAILED = 1
        print(f"FAIL: {name}{suffix}")


def _job_block(text: str, name: str) -> str:
    marker = f"  {name}:\n"
    start = text.find(marker)
    if start < 0:
        return ""
    rest = text[start + len(marker):]
    lines = []
    for line in rest.splitlines(keepends=True):
        if line.startswith("  ") and not line.startswith("   ") and line.strip().endswith(":"):
            break
        lines.append(line)
    return "".join(lines)


def _step_block(text: str, step_name: str) -> str:
    marker = f"name: {step_name}\n"
    start = text.find(marker)
    if start < 0:
        return ""
    rest = text[start + len(marker):]
    lines = []
    for line in rest.splitlines(keepends=True):
        if line.startswith("      - ") and lines:
            break
        lines.append(line)
    return "".join(lines)


def _dedent(block: str) -> str:
    lines = block.split("\n")
    indents = [len(line) - len(line.lstrip(" ")) for line in lines if line.strip()]
    if not indents:
        return ""
    cut = min(indents)
    body = "\n".join(line[cut:] if line.startswith(" " * cut) else line for line in lines)
    if body and not body.endswith("\n"):
        body += "\n"
    return body


def violations(text: str, gate_source: str) -> list[str]:
    found: list[str] = []
    if "\npermissions: {}\n" not in f"\n{text}":
        found.append("top-permissions")
    for line in text.splitlines():
        if line == "  pull_request:":
            found.append("pull_request-trigger")
    if "fetch-depth: 0" in text or ".cursor/bin" in text or "CURSOR_API_KEY" in text:
        found.append("forbidden-install-or-depth")
    if "curl " in text and "| bash" in text:
        found.append("curl-bash")
    checkouts = text.count("uses: actions/checkout@")
    persisted = text.count("persist-credentials: false")
    if checkouts < 1 or checkouts != persisted:
        found.append("persist-credentials")
    for name in ("gate", "review", "post"):
        block = _job_block(text, name)
        if "timeout-minutes:" not in block:
            found.append(f"timeout-{name}")
    gate = _job_block(text, "gate")
    review = _job_block(text, "review")
    post = _job_block(text, "post")
    if "pull-requests: read" not in gate or "contents:" in gate:
        found.append("gate-permissions")
    if "contents: read" not in review:
        found.append("review-permissions")
    if "pull-requests: write" not in post or "contents:" in post:
        found.append("post-permissions")
    step = _step_block(text, "Grok 호출")
    if "XAI_API_KEY" not in step or "GH_TOKEN" in step or "GITHUB_TOKEN" in step:
        found.append("model-env")
    if "github.event.pull_request.draft == false" not in text:
        found.append("draft-skip")
    if "github.event.pull_request.number" not in text or "cancel-in-progress:" not in text:
        found.append("concurrency")
    if text.count('cron: "0 0 * * *"') != 1 or 'cron: "0 0 * * 1-5"' in text or 'cron: "0 8 * * 1-5"' in text:
        found.append("schedule")
    closed = _job_block(text, "fail-closed")
    if "timeout-minutes:" not in closed or "exit 1" not in closed or "needs.review.outputs.code" not in text:
        found.append("fail-closed")
    for kind in ("opened", "reopened", "synchronize", "ready_for_review"):
        if kind not in text:
            found.append(f"type-{kind}")
    begin = "python3 - <<'PY'\n"
    start = text.find(begin)
    if start < 0:
        found.append("gate-embed")
    else:
        rest = text[start + len(begin):]
        end_match = re.search(r"\n[ ]*PY\n", rest)
        if end_match is None:
            found.append("gate-embed")
        else:
            embedded = _dedent(rest[:end_match.start()])
            if embedded != gate_source:
                found.append("gate-embed")
    if 'run_diff.py' not in text or "fetch_diff.py" not in text:
        found.append("entry")
    return found


def forbidden_words(workflow: str, root: Path) -> list[str]:
    needles = ("APPROVE", "REQUEST_CHANGES")
    hits: list[str] = []
    blobs = [("workflow", workflow)]
    for path in sorted((root / "scripts" / "grok_review").glob("*.py")):
        if path.name in {"workflow_check.py", "probe.py"}:
            continue
        blobs.append((path.name, path.read_text(encoding="utf-8")))
    for name, blob in blobs:
        for needle in needles:
            if needle in blob:
                hits.append(f"{name}:{needle}")
    return hits


def _expect_red(name: str, text: str, gate_source: str, code: str) -> None:
    found = violations(text, gate_source)
    record(name, code in found, ",".join(found) or "위반 없음")


def main() -> int:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    gate_source = GATE.read_text(encoding="utf-8")
    found = violations(workflow, gate_source)
    words = forbidden_words(workflow, ROOT)
    record("워크플로 정적 검사", not found and not words, ",".join([*found, *words]))
    _expect_red(
        "red pull_request+secret",
        workflow.replace("  pull_request_target:\n", "  pull_request:\n", 1),
        gate_source,
        "pull_request-trigger",
    )
    _expect_red(
        "red persist-credentials",
        workflow.replace("persist-credentials: false", "persist-credentials: true", 1),
        gate_source,
        "persist-credentials",
    )
    _expect_red("red permissions", workflow.replace("permissions: {}", "permissions:\n  contents: write", 1), gate_source, "top-permissions")
    grok = _step_block(workflow, "Grok 호출")
    poisoned = workflow.replace(grok, grok + "          GH_TOKEN: ${{ github.token }}\n", 1)
    _expect_red("red model token", poisoned, gate_source, "model-env")
    record(
        "red APPROVE 문자열",
        "workflow:APPROVE" in forbidden_words(workflow + "\n# APPROVE\n", ROOT),
    )
    record(
        "green 본문에는 APPROVE 가 없다",
        not forbidden_words(workflow, ROOT),
    )
    stripped = workflow.replace("    timeout-minutes: 5\n", "", 1)
    _expect_red("red timeout", stripped, gate_source, "timeout-gate")
    _expect_red("red cursor bin", workflow + "\n# $HOME/.cursor/bin\n", gate_source, "forbidden-install-or-depth")
    print(f"CHECKED: {CHECKED}")
    return FAILED


if __name__ == "__main__":
    sys.exit(main())
