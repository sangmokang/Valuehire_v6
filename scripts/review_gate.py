#!/usr/bin/env python3
"""Build an advisory, exact-head review manifest from a Git diff."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path


SHA_RE = re.compile(r"^[0-9a-fA-F]{40}$")
WEAKENING_RE = re.compile(
    r"(?:\|\|\s*true|continue-on-error\s*:\s*true|allow_failure|"
    r"\.skip\s*\(|\bxfail\b|^\s*skip\s*:|if\s*:\s*always\s*\(\s*\))",
    re.IGNORECASE | re.MULTILINE,
)


class NotRunError(RuntimeError):
    """The manifest cannot be computed from the supplied repository state."""


def git(repo: Path, *args: str, binary: bool = False) -> str | bytes:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        detail = result.stderr.decode("utf-8", "replace").strip()
        raise NotRunError(f"git {' '.join(args)} 실패(exit={result.returncode}): {detail}")
    if binary:
        return result.stdout
    return result.stdout.decode("utf-8", "replace").strip()


def resolve_commit(repo: Path, value: str, field: str) -> str:
    if not SHA_RE.fullmatch(value):
        raise NotRunError(f"{field}는 40자리 Git 기록 지문이어야 한다")
    resolved = git(repo, "rev-parse", "--verify", f"{value}^{{commit}}")
    if not isinstance(resolved, str) or not SHA_RE.fullmatch(resolved):
        raise NotRunError(f"{field} 기록을 확인할 수 없다")
    return resolved.lower()


def nul_paths(raw: bytes) -> list[str]:
    parts = raw.split(b"\0")
    if parts and parts[-1] == b"":
        parts.pop()
    return sorted(part.decode("utf-8", "surrogateescape") for part in parts)


def is_docs(path: str) -> bool:
    lowered = path.lower()
    return lowered.startswith("docs/") or lowered.endswith((".md", ".mdx", ".txt"))


def is_check_boundary(path: str) -> bool:
    lowered = path.lower()
    name = lowered.rsplit("/", 1)[-1]
    return (
        lowered == "verify.sh"
        or lowered == "suppressions.yaml"
        or lowered == "docs/sot/mechanism-registry.yaml"
        or lowered.startswith((".github/workflows/", "hooks/", "contracts/"))
        or (lowered.startswith("scripts/acceptance-") and lowered.endswith(".sh"))
        or ".spec." in name
        or name.endswith(".spec")
    )


def is_security_boundary(path: str) -> bool:
    lowered = f"/{path.lower()}"
    return any(
        marker in lowered
        for marker in (
            "/auth/",
            "/security/",
            "/secret",
            "/credential",
            "/session",
            "/hooks/",
            "/verify.sh",
        )
    )


def is_data_boundary(path: str) -> bool:
    lowered = f"/{path.lower()}"
    return (
        lowered.endswith(".sql")
        or any(
            marker in lowered
            for marker in (
                "/supabase/",
                "/migrations/",
                "/data/",
                "/schema",
                "/candidate",
            )
        )
    )


def is_external_boundary(path: str) -> bool:
    lowered = f"/{path.lower()}"
    return any(
        marker in lowered
        for marker in (
            "/tools/gmail-",
            "/scraper",
            "/portal",
            "/login",
            "/saramin",
            "/jobkorea",
            "/linkedin",
            "/resumeintake",
        )
    )


def change_type(path: str) -> str:
    lowered = path.lower()
    if is_docs(path):
        return "docs"
    if (
        lowered.startswith("tests/")
        or "/test" in lowered
        or ".spec." in lowered
        or lowered.startswith("scripts/acceptance-")
    ):
        return "test"
    if lowered.startswith(
        (".github/", "hooks/", "scripts/", "contracts/", "docs/sot/")
    ) or lowered == "verify.sh":
        return "infra"
    return "feature"


def added_gate_diff(repo: Path, base: str, head: str, paths: list[str]) -> str:
    gate_paths = [path for path in paths if is_check_boundary(path)]
    if not gate_paths:
        return ""
    diff = git(
        repo,
        "diff",
        "--no-ext-diff",
        "--unified=0",
        f"{base}...{head}",
        "--",
        *gate_paths,
        binary=True,
    )
    assert isinstance(diff, bytes)
    added: list[str] = []
    for line in diff.decode("utf-8", "replace").splitlines():
        if line.startswith("+") and not line.startswith("+++"):
            added.append(line[1:])
    return "\n".join(added)


def build_manifest(repo: Path, base_value: str, head_value: str) -> dict[str, object]:
    if not repo.is_dir():
        raise NotRunError(f"저장소 경로가 없다: {repo}")
    if git(repo, "rev-parse", "--is-inside-work-tree") != "true":
        raise NotRunError("git 작업공간이 아니다")

    base = resolve_commit(repo, base_value, "base")
    head = resolve_commit(repo, head_value, "head")
    if base == head:
        raise NotRunError("base와 head가 같아 검사할 변경이 0개다")

    raw_files = git(
        repo, "diff", "--name-only", "-z", f"{base}...{head}", binary=True
    )
    assert isinstance(raw_files, bytes)
    files = nul_paths(raw_files)
    if not files:
        raise NotRunError("변경 파일이 0개다")

    commit_count_text = git(repo, "rev-list", "--count", f"{base}..{head}")
    assert isinstance(commit_count_text, str)
    try:
        commit_count = int(commit_count_text)
    except ValueError as exc:
        raise NotRunError("커밋 수를 숫자로 읽을 수 없다") from exc
    if commit_count < 1:
        raise NotRunError("base 이후 head 커밋이 0개다")

    deleted_raw = git(
        repo,
        "diff",
        "--diff-filter=D",
        "--name-only",
        "-z",
        f"{base}...{head}",
        binary=True,
    )
    assert isinstance(deleted_raw, bytes)
    deleted = nul_paths(deleted_raw)

    signals = {
        "weakens_check": any(is_check_boundary(path) for path in files),
        "touches_security": any(is_security_boundary(path) for path in files),
        "touches_data": any(is_data_boundary(path) for path in files),
        "touches_external": any(is_external_boundary(path) for path in files),
        "weakening_pattern": bool(WEAKENING_RE.search(added_gate_diff(repo, base, head, files))),
        "check_deleted": any(is_check_boundary(path) for path in deleted),
    }

    if signals["weakening_pattern"] or signals["check_deleted"]:
        risk = "critical"
    elif any(
        signals[name]
        for name in (
            "weakens_check",
            "touches_security",
            "touches_data",
            "touches_external",
        )
    ):
        risk = "high"
    elif all(is_docs(path) for path in files):
        risk = "low"
    else:
        risk = "medium"

    recommended_checks = ["verify"]
    if signals["weakens_check"]:
        recommended_checks.append("adversarial-review")
    if signals["touches_security"]:
        recommended_checks.append("security-review")
    if signals["touches_data"]:
        recommended_checks.append("data-exposure")
    if signals["touches_external"]:
        recommended_checks.append("live-smoke")
    if signals["weakening_pattern"] or signals["check_deleted"]:
        recommended_checks.append("owner-review")

    payload: dict[str, object] = {
        "schema_version": 1,
        "state": "advisory",
        "base_sha": base,
        "head_sha": head,
        "commit_count": commit_count,
        "file_count": len(files),
        "files": files,
        "change_types": sorted({change_type(path) for path in files}),
        "risk": risk,
        "signals": signals,
        "recommended_checks": recommended_checks,
    }
    canonical = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")
    payload["manifest_id"] = hashlib.sha256(canonical).hexdigest()
    return payload


def render_summary(manifest: dict[str, object]) -> str:
    signals = manifest["signals"]
    assert isinstance(signals, dict)
    active_signals = [name for name, active in signals.items() if active]
    files = manifest["files"]
    assert isinstance(files, list)
    checks = manifest["recommended_checks"]
    assert isinstance(checks, list)
    lines = [
        "# Review gate — advisory",
        "",
        "> 이 결과는 현재 head에 묶인 참고용 판정이며, 라벨이나 병합 권한을 바꾸지 않습니다.",
        "",
        f"- Head: `{manifest['head_sha']}`",
        f"- Base: `{manifest['base_sha']}`",
        f"- Manifest: `{manifest['manifest_id']}`",
        f"- Risk: **{manifest['risk']}**",
        f"- Commits: {manifest['commit_count']}",
        f"- Files: {manifest['file_count']}",
        f"- Signals: {', '.join(active_signals) if active_signals else 'none'}",
        f"- Recommended checks: {', '.join(str(item) for item in checks)}",
        "",
        "## Files",
        "",
    ]
    lines.extend(f"- `{json.dumps(path, ensure_ascii=False)}`" for path in files)
    lines.append("")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--base", required=True)
    parser.add_argument("--head", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        manifest = build_manifest(args.repo.resolve(), args.base, args.head)
        args.output.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        args.summary.write_text(render_summary(manifest), encoding="utf-8")
    except (NotRunError, OSError) as exc:
        print(f"NOT_RUN: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
