#!/usr/bin/env python3
"""결과 파일의 본문으로 PR 이슈 코멘트 하나를 만들거나 갱신한다.

리뷰 이벤트는 만들지 않는다. 모델 키는 읽지 않는다.
"""
from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

MARKER_PREFIX = "<!-- grok-review sha="
REPO_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")


def _headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "valuehire-grok-review",
    }


def _request(url: str, token: str, method: str, payload: dict | None) -> object:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=data, headers=_headers(token), method=method)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            raw = response.read()
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", "replace")[:300]
        raise SystemExit(f"FAIL: HTTP {error.code} — {detail}")
    except urllib.error.URLError as error:
        raise SystemExit(f"FAIL: 네트워크 오류 — {error.reason}")
    if not raw:
        return {}
    try:
        return json.loads(raw.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as error:
        raise SystemExit("FAIL: GitHub 응답 JSON 을 읽지 못했다") from error


def _paged(url: str, token: str) -> list:
    pages: list = []
    for page in range(1, 21):
        payload = _request(f"{url}{'&' if '?' in url else '?'}per_page=100&page={page}", token, "GET", None)
        if not isinstance(payload, list):
            raise SystemExit("FAIL: 코멘트 목록이 배열이 아니다")
        pages.extend(payload)
        if len(payload) < 100:
            return pages
    raise SystemExit("FAIL: 코멘트 목록이 20페이지를 넘었다")


def choose_id(rows: list[tuple[str, str, int]]) -> int | None:
    """(updated_at, body, id) 중 표식이 있는 가장 최근 코멘트."""
    newest: tuple[str, int] | None = None
    for updated, body, comment_id in rows:
        if MARKER_PREFIX not in body:
            continue
        if newest is None or updated >= newest[0]:
            newest = (updated, comment_id)
    return None if newest is None else newest[1]


def existing_comment_id(repo: str, number: str, token: str) -> int | None:
    url = f"https://api.github.com/repos/{repo}/issues/{number}/comments"
    rows: list[tuple[str, str, int]] = []
    for item in _paged(url, token):
        if not isinstance(item, dict):
            raise SystemExit("FAIL: 코멘트 항목이 객체가 아니다")
        body = item.get("body") or ""
        updated = item.get("updated_at") or ""
        comment_id = item.get("id")
        if not isinstance(body, str) or not isinstance(updated, str):
            raise SystemExit("FAIL: 코멘트 본문이 문자열이 아니다")
        if isinstance(comment_id, bool) or not isinstance(comment_id, int):
            raise SystemExit("FAIL: 코멘트 id 가 없다")
        rows.append((updated, body, comment_id))
    return choose_id(rows)


def upsert(repo: str, number: str, token: str, body: str) -> str:
    if MARKER_PREFIX not in body:
        raise SystemExit("FAIL: 코멘트 본문에 sha 표식이 없다")
    comment_id = existing_comment_id(repo, number, token)
    if comment_id is None:
        _request(
            f"https://api.github.com/repos/{repo}/issues/{number}/comments",
            token,
            "POST",
            {"body": body},
        )
        return "created"
    _request(
        f"https://api.github.com/repos/{repo}/issues/comments/{comment_id}",
        token,
        "PATCH",
        {"body": body},
    )
    return "updated"


def main() -> int:
    result_path = Path(os.environ.get("RESULT_PATH", "result/result.json"))
    try:
        payload = json.loads(result_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        print(f"FAIL: 결과 파일을 읽지 못했다 — {error}")
        return 1
    comments = payload.get("comments") if isinstance(payload, dict) else None
    if not isinstance(comments, list):
        print("FAIL: 결과 파일에 comments 가 없다")
        return 1
    repo = os.environ.get("GITHUB_REPOSITORY", "").strip()
    token = os.environ.get("GH_TOKEN", "").strip()
    posted = 0
    for item in comments:
        if not isinstance(item, dict):
            print("FAIL: 코멘트 항목이 객체가 아니다")
            return 1
        number = str(item.get("pr") or "").strip()
        body = item.get("body")
        if not isinstance(body, str) or not body.strip():
            print("FAIL: 코멘트 본문이 비었다")
            return 1
        if not number:
            print("NOT_POSTED: PR 번호가 없어 리포트만 남겼다")
            continue
        if not number.isdecimal():
            print(f"FAIL: PR 번호가 정수가 아니다 — {number}")
            return 1
        if not REPO_RE.fullmatch(repo) or not token:
            print("FAIL: 코멘트 게시에 GITHUB_REPOSITORY 와 GH_TOKEN 이 필요하다")
            return 1
        action = upsert(repo, number, token, body)
        posted += 1
        print(f"PASS: comment {action} pr={number}", flush=True)
    if posted == 0 and not comments:
        print("NOT_POSTED: 남길 코멘트가 없다")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
