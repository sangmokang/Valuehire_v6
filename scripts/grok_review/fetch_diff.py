#!/usr/bin/env python3
"""비교 API 로 diff 텍스트만 받는다. PR 트리는 체크아웃하지 않는다.

이 스텝만 GH_TOKEN 을 본다. 모델 호출 스텝에는 넘기지 않는다.
"""
from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import diffpack  # noqa: E402
import engine  # noqa: E402

SHA_RE = re.compile(r"^[0-9a-f]{40}$")
REPO_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
FILE_CAP = 300


def _headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "valuehire-grok-review",
    }


def _get(url: str, token: str) -> dict:
    request = urllib.request.Request(url, headers=_headers(token), method="GET")
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            raw = response.read()
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", "replace")[:300]
        raise SystemExit(f"FAIL: HTTP {error.code} — {detail}")
    except urllib.error.URLError as error:
        raise SystemExit(f"FAIL: 네트워크 오류 — {error.reason}")
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as error:
        raise SystemExit("FAIL: compare 응답 JSON 을 읽지 못했다") from error
    if not isinstance(payload, dict):
        raise SystemExit("FAIL: compare 응답이 객체가 아니다")
    return payload


def _sha(value: object, label: str) -> str:
    if not isinstance(value, str) or not SHA_RE.fullmatch(value):
        raise SystemExit(f"FAIL: {label} SHA 가 없다")
    return value.lower()


def render_files(files: object, patterns: list[re.Pattern[str]]) -> tuple[str, list[str]]:
    if not isinstance(files, list):
        raise SystemExit("FAIL: compare files 가 배열이 아니다")
    if len(files) >= FILE_CAP:
        raise SystemExit(f"FAIL: diff 가 {FILE_CAP}파일 한도에 걸렸다")
    parts: list[str] = []
    excluded: list[str] = []
    for item in files:
        if not isinstance(item, dict):
            raise SystemExit("FAIL: compare 파일 항목이 객체가 아니다")
        path = item.get("filename")
        if not isinstance(path, str) or not path or path.startswith("/") or ".." in path.split("/"):
            raise SystemExit("FAIL: compare 파일 경로가 이상하다")
        changes = item.get("changes")
        patch = item.get("patch")
        if diffpack.excluded_path(path, patterns):
            excluded.append(path)
            continue
        if not isinstance(changes, int) or isinstance(changes, bool):
            raise SystemExit(f"FAIL: 변경 줄 수가 없다 — {path}")
        if changes == 0:
            continue
        if not isinstance(patch, str):
            raise SystemExit(f"FAIL: diff 잘림 — {path}")
        if patch.startswith("diff --git "):
            block = patch
        else:
            block = f"diff --git a/{path} b/{path}\n--- a/{path}\n+++ b/{path}\n{patch}"
        if not block.endswith("\n"):
            block += "\n"
        try:
            parsed = diffpack.parse_unified(block)
        except engine.ReviewError as error:
            raise SystemExit(str(error)) from error
        if len(parsed) != changes:
            raise SystemExit(
                f"FAIL: diff 줄 수가 변경 수와 다르다 — {path} parsed={len(parsed)} changes={changes}"
            )
        parts.append(block)
    return "".join(parts), excluded


def fetch_item(repo: str, token: str, item: dict, patterns: list[re.Pattern[str]]) -> tuple[str, str, list[str]]:
    base = _sha(item.get("base"), "base")
    head = _sha(item.get("head"), "head")
    previous = item.get("previous") or ""
    if previous:
        left = _sha(previous, "previous")
        spec = f"{left}..{head}"
    else:
        spec = f"{base}...{head}"
    payload = _get(f"https://api.github.com/repos/{repo}/compare/{spec}", token)
    diff, excluded = render_files(payload.get("files"), patterns)
    return spec, diff, excluded


def main() -> int:
    mode = os.environ.get("MODE", "").strip()
    out_dir = Path(os.environ.get("OUT_DIR", "pr-data"))
    out_dir.mkdir(parents=True, exist_ok=True)
    if mode == "full":
        (out_dir / "work.json").write_text(json.dumps({"mode": "full", "items": []}, ensure_ascii=False), encoding="utf-8")
        print("PASS: fetch full", flush=True)
        return 0
    repo = os.environ.get("GITHUB_REPOSITORY", "").strip()
    token = os.environ.get("GH_TOKEN", "").strip()
    if not REPO_RE.fullmatch(repo) or not token:
        raise SystemExit("FAIL: diff 수집에 GITHUB_REPOSITORY 와 GH_TOKEN 이 필요하다")
    config = diffpack.load_config()
    patterns = [diffpack._compile_glob(item) for item in config["exclude_globs"]]
    if mode == "queue":
        try:
            raw_items = json.loads(os.environ.get("QUEUE", "") or "[]")
        except json.JSONDecodeError as error:
            raise SystemExit(f"FAIL: queue JSON 이 아니다 — {error}") from error
        if not isinstance(raw_items, list):
            raise SystemExit("FAIL: queue 가 배열이 아니다")
        items = raw_items
    elif mode == "diff":
        items = [{
            "pr": os.environ.get("PR_NUMBER", "").strip(),
            "base": os.environ.get("BASE_SHA", "").strip(),
            "head": os.environ.get("HEAD_SHA", "").strip(),
            "previous": os.environ.get("PREVIOUS_SHA", "").strip(),
            "body": os.environ.get("PR_BODY", ""),
        }]
    else:
        raise SystemExit(f"FAIL: MODE 를 모른다 — {mode}")
    written = []
    for item in items:
        if not isinstance(item, dict):
            raise SystemExit("FAIL: queue 항목이 객체가 아니다")
        spec, diff, excluded = fetch_item(repo, token, item, patterns)
        name = f"{item.get('pr') or 'diff'}.diff"
        (out_dir / name).write_text(diff, encoding="utf-8")
        written.append({
            "pr": str(item.get("pr") or ""),
            "head": _sha(item.get("head"), "head"),
            "base": _sha(item.get("base"), "base"),
            "previous": item.get("previous") or "",
            "body": item.get("body") if isinstance(item.get("body"), str) else "",
            "compare": spec,
            "diff_file": name,
            "excluded": excluded,
        })
        print(f"PASS: fetch {spec} bytes={len(diff.encode('utf-8'))}", flush=True)
    (out_dir / "work.json").write_text(
        json.dumps({"mode": "diff", "items": written}, ensure_ascii=False),
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
