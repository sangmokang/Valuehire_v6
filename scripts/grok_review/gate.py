#!/usr/bin/env python3
"""같은 head SHA 표식이 있으면 리뷰를 건너뛰고, synchronize 면 직전 표식 SHA 를 고른다.

이 파일은 네트워크 없이 판정 함수를 시험할 수 있어야 한다.
워크플로의 gate 잡은 저장소를 체크아웃하지 않으므로, 이 파일 본문을 워크플로에 그대로 넣는다.
"""
from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request

MARKER_RE = re.compile(r"<!-- grok-review sha=([0-9a-f]{40}) -->")
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
REPO_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
BODY_CAP = 4000


def marker(sha: str) -> str:
    return f"<!-- grok-review sha={sha.lower()} -->"


def decide(comments_newest_first: list[tuple[str, str]], head: str, event: str) -> tuple[bool, str]:
    """(skip, previous_sha). previous_sha 는 synchronize 이고 표식이 있을 때만 채운다."""
    if not SHA_RE.fullmatch(head):
        raise ValueError("head SHA 가 없다")
    head = head.lower()
    found: list[str] = []
    for _updated, body in comments_newest_first:
        found.extend(MARKER_RE.findall(body or ""))
    if head in found:
        return True, ""
    if event != "synchronize":
        return False, ""
    for sha in found:
        if sha != head:
            return False, sha
    return False, ""


def _headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "valuehire-grok-review",
    }


def _get(url: str, token: str) -> object:
    request = urllib.request.Request(url, headers=_headers(token), method="GET")
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            raw = response.read()
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", "replace")[:300]
        raise SystemExit(f"FAIL: HTTP {error.code} — {detail}")
    except urllib.error.URLError as error:
        raise SystemExit(f"FAIL: 네트워크 오류 — {error.reason}")
    try:
        return json.loads(raw.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as error:
        raise SystemExit("FAIL: GitHub 응답 JSON 을 읽지 못했다") from error


def _paged(url: str, token: str) -> list:
    pages: list = []
    for page in range(1, 21):
        joiner = "&" if "?" in url else "?"
        payload = _get(f"{url}{joiner}per_page=100&page={page}", token)
        if not isinstance(payload, list):
            raise SystemExit("FAIL: GitHub 목록 응답이 배열이 아니다")
        pages.extend(payload)
        if len(payload) < 100:
            return pages
    raise SystemExit("FAIL: GitHub 목록이 20페이지를 넘었다")


def _clip(text: object) -> str:
    if not isinstance(text, str):
        return ""
    if len(text) <= BODY_CAP:
        return text
    return text[: BODY_CAP - 1] + "…"


def comment_pairs(repo: str, number: str, token: str) -> list[tuple[str, str]]:
    issue_url = f"https://api.github.com/repos/{repo}/issues/{number}/comments"
    review_url = f"https://api.github.com/repos/{repo}/pulls/{number}/reviews"
    rows: list[tuple[str, str]] = []
    for payload in (_paged(issue_url, token), _paged(review_url, token)):
        for item in payload:
            if not isinstance(item, dict):
                raise SystemExit("FAIL: 코멘트 항목이 객체가 아니다")
            updated = item.get("updated_at") or item.get("submitted_at") or ""
            body = item.get("body") or ""
            if not isinstance(updated, str) or not isinstance(body, str):
                raise SystemExit("FAIL: 코멘트 본문이 문자열이 아니다")
            rows.append((updated, body))
    rows.sort(key=lambda item: item[0], reverse=True)
    return rows


def _sha(value: object, label: str) -> str:
    if not isinstance(value, str) or not SHA_RE.fullmatch(value):
        raise SystemExit(f"FAIL: {label} SHA 가 없다")
    return value.lower()


def _pull(item: dict) -> dict:
    number = item.get("number")
    base = item.get("base") if isinstance(item.get("base"), dict) else {}
    head = item.get("head") if isinstance(item.get("head"), dict) else {}
    if isinstance(number, bool) or not isinstance(number, int) or number < 1:
        raise SystemExit("FAIL: PR 번호가 없다")
    return {
        "pr": str(number),
        "base": _sha(base.get("sha"), "base"),
        "head": _sha(head.get("sha"), "head"),
        "body": _clip(item.get("body")),
        "previous": "",
    }


def _write(skip: str, mode: str, pr: str, head: str, base: str, previous: str, body: str, queue: list[dict]) -> None:
    path = os.environ.get("GITHUB_OUTPUT", "").strip()
    lines = [
        f"skip={skip}",
        f"mode={mode}",
        f"pr_number={pr}",
        f"head_sha={head}",
        f"base_sha={base}",
        f"previous_sha={previous}",
        f"pr_body={body.replace(chr(10), ' ').replace(chr(13), ' ')}",
        f"queue={json.dumps(queue, ensure_ascii=False)}",
    ]
    text = "\n".join(lines) + "\n"
    if not path:
        print(text, end="")
        return
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(text)


def main() -> int:
    repo = os.environ.get("GITHUB_REPOSITORY", "").strip()
    token = os.environ.get("GH_TOKEN", "").strip() or os.environ.get("GITHUB_TOKEN", "").strip()
    event = os.environ.get("EVENT_NAME", "").strip()
    if not REPO_RE.fullmatch(repo) or not token:
        raise SystemExit("FAIL: GITHUB_REPOSITORY 또는 토큰이 없다")
    if event == "schedule":
        payload = _paged(f"https://api.github.com/repos/{repo}/pulls?state=open", token)
        queue: list[dict] = []
        for item in payload:
            if not isinstance(item, dict):
                raise SystemExit("FAIL: PR 항목이 객체가 아니다")
            pull = _pull(item)
            pairs = comment_pairs(repo, pull["pr"], token)
            skip, _previous = decide(pairs, pull["head"], "schedule")
            if skip:
                print(f"ALREADY {pull['pr']} {pull['head']}", flush=True)
                continue
            queue.append(pull)
        if not queue:
            print("PASS: schedule 리뷰할 PR 없음", flush=True)
            _write("true", "queue", "", "", "", "", "", [])
            return 0
        print(f"PASS: schedule queue={len(queue)}", flush=True)
        _write("false", "queue", "", "", "", "", "", queue)
        return 0

    number = os.environ.get("PR_NUMBER", "").strip()
    if number in {"", "null", "0"}:
        number = ""
    scope = os.environ.get("DISPATCH_SCOPE", "").strip() or "pr"
    if event == "workflow_dispatch" and scope == "full":
        if number and not number.isdecimal():
            raise SystemExit("FAIL: PR 번호가 정수가 아니다")
        print("PASS: dispatch full", flush=True)
        _write("false", "full", number, "", "", "", "", [])
        return 0
    if not number:
        raise SystemExit("FAIL: PR 번호가 없다")
    if not number.isdecimal():
        raise SystemExit("FAIL: PR 번호가 정수가 아니다")

    if event == "workflow_dispatch":
        item = _get(f"https://api.github.com/repos/{repo}/pulls/{number}", token)
        if not isinstance(item, dict):
            raise SystemExit("FAIL: PR 응답이 객체가 아니다")
        pull = _pull(item)
        head, base, body = pull["head"], pull["base"], pull["body"]
        decision_event = "workflow_dispatch"
    else:
        head = _sha(os.environ.get("HEAD_SHA", ""), "head")
        base = _sha(os.environ.get("BASE_SHA", ""), "base")
        body = _clip(os.environ.get("PR_BODY", ""))
        # pull_request_target 의 동작 이름은 action 이다. synchronize 만 증분 diff 다.
        decision_event = os.environ.get("EVENT_ACTION", "").strip()

    skip, previous = decide(comment_pairs(repo, number, token), head, decision_event)
    if skip:
        print(f"PASS: skip {number} {head}", flush=True)
        _write("true", "diff", number, head, base, "", body, [])
        return 0
    print(f"PASS: review {number} {base}..{head} previous={previous or '-'}", flush=True)
    _write("false", "diff", number, head, base, previous, body, [])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
