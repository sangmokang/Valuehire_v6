#!/usr/bin/env python3
"""Grok 라인 리뷰 실행기.

`plan` 은 API 없이 커버리지 매니페스트만 만든다.
`review` 는 대상 파일의 모든 줄을 청크로 보내 결함을 모은다.
키가 없거나 한 청크라도 실패하면 완료로 기록하지 않는다.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import engine  # noqa: E402

API_URL = "https://api.x.ai/v1/chat/completions"
DEFAULT_MODEL = "grok-4.7"
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
REF_RE = re.compile(r"[A-Za-z0-9._/-]+")
RETRY_STATUS = {429, 500, 502, 503, 504}


class ApiError(engine.ReviewError):
    def __init__(self, message: str, status: int | None = None) -> None:
        super().__init__(message)
        self.status = status


def _positive_int(name: str, default: int) -> int:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError as error:
        raise engine.ReviewError(f"FAIL: {name} 가 정수가 아니다 — {raw}") from error
    if value < 1:
        raise engine.ReviewError(f"FAIL: {name} 는 1 이상이어야 한다")
    return value


def _run_git(args: list[str], *, check: bool = True) -> subprocess.CompletedProcess[bytes]:
    proc = subprocess.run(["git", *args], capture_output=True, timeout=120)
    if check and proc.returncode != 0:
        detail = proc.stderr.decode("utf-8", "replace").strip().splitlines()
        tail = detail[-1] if detail else "stderr 없음"
        raise engine.ReviewError(f"FAIL: git {' '.join(args[:3])} — {tail}")
    return proc


def _safe_ref(ref: str) -> str:
    if ref.startswith("-") or ".." in ref.split("/") or not REF_RE.fullmatch(ref):
        raise engine.ReviewError(f"FAIL: ref 거부 — {ref}")
    return ref


def _rev_parse(ref: str) -> str | None:
    proc = _run_git(["rev-parse", "--verify", f"{ref}^{{commit}}"], check=False)
    if proc.returncode != 0:
        return None
    sha = proc.stdout.decode("utf-8").strip().lower()
    if not SHA_RE.fullmatch(sha):
        raise engine.ReviewError(f"FAIL: rev-parse 결과가 SHA 가 아니다 — {ref}")
    return sha


def _ensure_sha(sha: str) -> str:
    probe = _run_git(["cat-file", "-e", f"{sha}^{{commit}}"], check=False)
    if probe.returncode == 0:
        return sha
    fetched = _run_git(["fetch", "--no-tags", "origin", sha], check=False)
    if fetched.returncode != 0:
        raise engine.ReviewError(f"FAIL: 커밋을 가져오지 못했다 — {sha}")
    probe = _run_git(["cat-file", "-e", f"{sha}^{{commit}}"], check=False)
    if probe.returncode != 0:
        raise engine.ReviewError(f"FAIL: fetch 후에도 커밋이 없다 — {sha}")
    return sha


def resolve_commit(ref: str) -> str:
    if SHA_RE.fullmatch(ref):
        return _ensure_sha(ref.lower())
    safe = _safe_ref(ref)
    sha = _rev_parse(safe)
    if sha is None and safe.startswith("origin/"):
        branch = _safe_ref(safe[len("origin/"):])
        _run_git(["fetch", "--no-tags", "origin", f"+refs/heads/{branch}:refs/remotes/origin/{branch}"])
        sha = _rev_parse(safe)
    if sha is None:
        raise engine.ReviewError(f"FAIL: 커밋을 확인하지 못했다 — {ref}")
    return sha


def blob_bytes(rev: str, path: str) -> bytes | None:
    proc = _run_git(["cat-file", "blob", f"{rev}:{path}"], check=False)
    if proc.returncode != 0:
        return None
    return proc.stdout


def changed_records(base: str, head: str) -> list[tuple[str, str, str | None]]:
    proc = _run_git(["diff", "--name-status", "-z", "--find-renames", f"{base}...{head}"])
    try:
        text = proc.stdout.decode("utf-8")
    except UnicodeDecodeError as error:
        raise engine.ReviewError("FAIL: name-status 가 UTF-8 이 아니다") from error
    return engine.parse_name_status_z(text)


def tracked_paths() -> list[str]:
    proc = _run_git(["ls-files", "-z"])
    try:
        text = proc.stdout.decode("utf-8")
    except UnicodeDecodeError as error:
        raise engine.ReviewError("FAIL: ls-files 가 UTF-8 이 아니다") from error
    paths = [item for item in text.split("\0") if item]
    if not paths:
        raise engine.ReviewError("FAIL: 추적 파일이 0개다 — 리뷰가 성립하지 않는다")
    return paths


def diff_text(base: str, head: str) -> str:
    proc = _run_git(["diff", "--find-renames", "-U3", f"{base}...{head}"])
    return proc.stdout.decode("utf-8", "replace")


def _read_worktree(path: str) -> bytes | None:
    file_path = Path(path)
    if not file_path.is_file():
        return None
    return file_path.read_bytes()


def build_plan(args: argparse.Namespace) -> tuple[list[engine.PlannedFile], str, str]:
    max_lines = _positive_int("GROK_REVIEW_MAX_LINES", 200)
    max_bytes = _positive_int("GROK_REVIEW_MAX_BYTES", 400_000)
    if args.paths:
        planned = [
            engine.plan_bytes(path, _read_worktree(path), max_lines=max_lines, max_bytes=max_bytes)
            for path in args.paths
        ]
        for item in planned:
            if item.reason == "missing-blob":
                raise engine.ReviewError(f"FAIL: 파일이 없다 — {item.path}")
        return planned, "worktree", "paths"

    scope = args.scope or os.environ.get("REVIEW_SCOPE", "pr").strip() or "pr"
    if scope not in {"pr", "full"}:
        raise engine.ReviewError(f"FAIL: scope 거부 — {scope}")
    if scope == "full":
        head = resolve_commit(os.environ.get("REVIEW_HEAD", "").strip() or "HEAD")
        planned = []
        for path in tracked_paths():
            item = engine.plan_bytes(path, blob_bytes(head, path), max_lines=max_lines, max_bytes=max_bytes)
            if item.reason == "missing-blob":
                raise engine.ReviewError(f"FAIL: 추적 파일 blob 을 읽지 못했다 — {path}")
            planned.append(item)
        return planned, head, "full"

    base = resolve_commit(os.environ.get("REVIEW_BASE", "").strip() or "origin/main")
    head = resolve_commit(os.environ.get("REVIEW_HEAD", "").strip() or "HEAD")
    planned = []
    for code, path, _old in changed_records(base, head):
        rev = base if code == "D" else head
        item = engine.plan_bytes(
            path,
            blob_bytes(rev, path),
            max_lines=max_lines,
            max_bytes=max_bytes,
        )
        if item.reason == "missing-blob":
            raise engine.ReviewError(f"FAIL: 변경 파일 blob 을 읽지 못했다 — {path}")
        planned.append(item)
    return planned, head, "pr"


def _message_text(payload: dict) -> str:
    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict):
        raise ApiError("FAIL: 응답에 choices 가 없다")
    message = choices[0].get("message")
    if not isinstance(message, dict):
        raise ApiError("FAIL: 응답에 message 가 없다")
    content = message.get("content")
    if isinstance(content, str) and content.strip():
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for part in content:
            if isinstance(part, str):
                parts.append(part)
            elif isinstance(part, dict) and isinstance(part.get("text"), str):
                parts.append(part["text"])
        joined = "\n".join(parts).strip()
        if joined:
            return joined
    raise ApiError("FAIL: 응답 content 가 비었다")


def _post_json(url: str, headers: dict[str, str], body: dict, timeout: int) -> dict:
    data = json.dumps(body).encode("utf-8")
    request = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", "replace")[:400]
        raise ApiError(f"FAIL: HTTP {error.code} — {detail}", error.code) from error
    except urllib.error.URLError as error:
        raise ApiError(f"FAIL: 네트워크 오류 — {error.reason}") from error
    try:
        parsed = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ApiError("FAIL: 응답 JSON 을 읽지 못했다") from error
    if not isinstance(parsed, dict):
        raise ApiError("FAIL: 응답이 객체가 아니다")
    return parsed


def call_texts(api_key: str, model: str, effort: str, system: str, user: str, timeout: int) -> str:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "User-Agent": "valuehire-grok-review",
    }
    body: dict = {
        "model": model,
        "stream": False,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }
    if effort:
        body["reasoning_effort"] = effort
    delays = (2, 8, 20)
    last: ApiError | None = None
    for attempt in range(3):
        try:
            payload = _post_json(API_URL, headers, body, timeout)
            return _message_text(payload)
        except ApiError as error:
            last = error
            if error.status == 400 and "reasoning_effort" in body:
                body.pop("reasoning_effort", None)
                continue
            if error.status not in RETRY_STATUS:
                raise
            time.sleep(delays[attempt])
    if last is None:
        raise ApiError("FAIL: 모델 호출이 비었다")
    raise last


def call_model(api_key: str, model: str, effort: str, chunk: engine.Chunk, timeout: int, rejection: str = "") -> str:
    user = engine.user_prompt(chunk)
    if rejection:
        user += f"\n이전 출력은 거절됐다: {rejection}\nJSON 객체만 다시 답한다.\n"
    return call_texts(api_key, model, effort, engine.system_prompt(), user, timeout)


def review_one(argv: list[str]) -> int:
    """청크 하나를 timeout 자식 프로세스로 호출할 때 쓰는 진입점. 코멘트는 달지 않는다."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--request", required=True)
    args = parser.parse_args(argv)
    api_key = os.environ.get("XAI_API_KEY", "").strip()
    if not api_key:
        print("FAIL: XAI_API_KEY 가 없다 — 리뷰를 실행하지 않았다", file=sys.stderr)
        return 1
    try:
        payload = json.loads(Path(args.request).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        print(f"FAIL: 청크 요청을 읽지 못했다 — {error}", file=sys.stderr)
        return 1
    system = payload.get("system")
    user = payload.get("user")
    if not isinstance(system, str) or not isinstance(user, str):
        print("FAIL: 청크 요청에 system, user 가 없다", file=sys.stderr)
        return 1
    model = os.environ.get("XAI_MODEL", "").strip() or DEFAULT_MODEL
    effort = os.environ.get("GROK_REASONING_EFFORT", "").strip() or "medium"
    timeout = _positive_int("GROK_REVIEW_TIMEOUT", 180)
    try:
        sys.stdout.write(call_texts(api_key, model, effort, system, user, timeout))
    except ApiError as error:
        print(str(error), file=sys.stderr)
        return 1
    return 0


def review_chunks(planned: list[engine.PlannedFile], api_key: str, model: str, effort: str, timeout: int) -> tuple[list[engine.Finding], int]:
    findings: list[engine.Finding] = []
    api_calls = 0
    sent_lines = 0
    expected_lines = 0
    for item in planned:
        if item.action != "review":
            continue
        for chunk in item.chunks:
            if chunk.end == 0:
                continue
            expected_lines += chunk.end - chunk.start + 1
            parsed: list[engine.Finding] | None = None
            last_error: engine.ReviewError | None = None
            rejection = ""
            for _attempt in range(2):
                try:
                    text = call_model(api_key, model, effort, chunk, timeout, rejection)
                    api_calls += 1
                    parsed = engine.parse_findings(text, chunk)
                    break
                except ApiError as error:
                    raise engine.ReviewError(
                        f"FAIL: 청크 미완료 — {chunk.path}:{chunk.start}-{chunk.end} — {error}"
                    ) from error
                except engine.ReviewError as error:
                    last_error = error
                    rejection = str(error)
            if parsed is None:
                raise engine.ReviewError(
                    f"FAIL: 청크 미완료 — {chunk.path}:{chunk.start}-{chunk.end} — {last_error}"
                )
            findings.extend(parsed)
            sent_lines += chunk.end - chunk.start + 1
            print(f"REVIEWED {chunk.path} {chunk.start}-{chunk.end}", flush=True)
    if sent_lines != expected_lines:
        raise engine.ReviewError(f"FAIL: 전송 줄 {sent_lines} != 대상 줄 {expected_lines}")
    return findings, api_calls


def _report(planned: list[engine.PlannedFile], sha: str, model: str, scope: str, findings: list[engine.Finding], api_calls: int, complete: bool) -> dict:
    skipped = [(item.path, item.reason) for item in planned if item.action == "skip"]
    reviewed = [item for item in planned if item.action == "review"]
    return {
        "complete": complete,
        "sha": sha,
        "model": model,
        "scope": scope,
        "reviewed_lines": sum(item.line_count for item in reviewed),
        "reviewed_files": len(reviewed),
        "chunks": sum(len(item.chunks) for item in reviewed),
        "api_calls": api_calls,
        "skipped": [{"path": path, "reason": reason} for path, reason in skipped],
        "chunk_ranges": [
            {"path": chunk.path, "start": chunk.start, "end": chunk.end}
            for item in reviewed
            for chunk in item.chunks
        ],
        "findings": [finding.__dict__ for finding in engine.dedupe_findings(findings)],
    }


def write_report(path: str, payload: dict) -> None:
    Path(path).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _github_review(url: str, headers: dict[str, str], body: dict, timeout: int) -> int:
    payload = _post_json(url, headers, body, timeout)
    review_id = payload.get("id")
    if not isinstance(review_id, int):
        raise engine.ReviewError("FAIL: GitHub 리뷰 응답에 id 가 없다")
    return review_id


def post_reviews(requests: list[dict], repo: str, pr: str, token: str, timeout: int) -> None:
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo):
        raise engine.ReviewError(f"FAIL: repository 형식 거부 — {repo}")
    if not re.fullmatch(r"[1-9][0-9]*", pr):
        raise engine.ReviewError(f"FAIL: PR 번호 거부 — {pr}")
    url = f"https://api.github.com/repos/{repo}/pulls/{pr}/reviews"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "Content-Type": "application/json",
        "User-Agent": "valuehire-grok-review",
    }
    summary = {key: value for key, value in requests[0].items() if key != "comments"}
    inline_requests = [item for item in requests if item.get("comments")]
    for index, body in enumerate(inline_requests, start=1):
        try:
            review_id = _github_review(url, headers, body, timeout)
        except ApiError as error:
            if error.status != 422:
                raise
            print(
                f"INLINE_REJECTED: HTTP 422 ({index}/{len(inline_requests)}) — "
                "남은 줄 코멘트는 본문에 남긴다",
                flush=True,
            )
            break
        print(f"POSTED review {review_id} (inline {index}/{len(inline_requests)})", flush=True)
    summary_id = _github_review(url, headers, summary, timeout)
    print(f"POSTED review {summary_id} (summary)", flush=True)


def _github_headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "valuehire-grok-review",
    }


def _get_json(url: str, token: str, timeout: int) -> object:
    request = urllib.request.Request(url, headers=_github_headers(token), method="GET")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", "replace")[:400]
        raise ApiError(f"FAIL: HTTP {error.code} — {detail}", error.code) from error
    except urllib.error.URLError as error:
        raise ApiError(f"FAIL: 네트워크 오류 — {error.reason}") from error
    try:
        return json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ApiError("FAIL: 응답 JSON 을 읽지 못했다") from error


def _paged(url: str, token: str, timeout: int) -> list:
    pages: list = []
    for page in range(1, 21):
        payload = _get_json(f"{url}{'&' if '?' in url else '?'}per_page=100&page={page}", token, timeout)
        if not isinstance(payload, list):
            raise engine.ReviewError("FAIL: GitHub 목록 응답이 배열이 아니다")
        pages.extend(payload)
        if len(payload) < 100:
            return pages
    raise engine.ReviewError("FAIL: GitHub 목록이 20페이지를 넘었다")


def fetch_open_pulls(repo: str, token: str, timeout: int) -> list[tuple[str, str, str]]:
    url = f"https://api.github.com/repos/{repo}/pulls?state=open"
    return engine.parse_open_pulls(_paged(url, token, timeout))


def fetch_review_bodies(repo: str, number: str, token: str, timeout: int) -> list[str]:
    url = f"https://api.github.com/repos/{repo}/pulls/{number}/reviews"
    return engine.parse_review_bodies(_paged(url, token, timeout))


def run_schedule(out: str, review_one) -> int:
    repo = os.environ.get("GITHUB_REPOSITORY", "").strip()
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo) or not token:
        raise engine.ReviewError("FAIL: 일정 리뷰에는 GITHUB_REPOSITORY 와 GITHUB_TOKEN 이 필요하다")
    timeout = _positive_int("GROK_REVIEW_TIMEOUT", 180)
    pulls = fetch_open_pulls(repo, token, timeout)
    reviewed = 0
    already = 0
    failed = 0
    for number, base, head in pulls:
        if engine.already_reviewed(fetch_review_bodies(repo, number, token, timeout), head):
            print(f"ALREADY {number} {head}", flush=True)
            already += 1
            continue
        print(f"SCHEDULE {number} {base}..{head}", flush=True)
        if review_one(number, base, head, out) == 0:
            reviewed += 1
        else:
            failed += 1
            print(f"FAIL: PR {number} 리뷰 실패", flush=True)
    stats = f"open_prs={len(pulls)} reviewed={reviewed} already={already} failed={failed}"
    if failed:
        print(f"FAIL: schedule {stats}")
        return 1
    print(f"PASS: schedule {stats}")
    return 0


def _summary_file(text: str) -> None:
    path = os.environ.get("GITHUB_STEP_SUMMARY", "").strip()
    if not path:
        return
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(text)
        if not text.endswith("\n"):
            handle.write("\n")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Grok 라인 리뷰")
    parser.add_argument("command", choices=("plan", "review"))
    parser.add_argument("--paths", nargs="*")
    parser.add_argument("--scope", choices=("pr", "full"))
    parser.add_argument("--out", default="")
    return parser


def _review_with_env(number: str, base: str, head: str, out: str) -> int:
    keys = ("REVIEW_BASE", "REVIEW_HEAD", "PR_NUMBER", "REVIEW_SCOPE", "GROK_REVIEW_OUT")
    previous = {key: os.environ.get(key) for key in keys}
    os.environ["REVIEW_BASE"] = base
    os.environ["REVIEW_HEAD"] = head
    os.environ["PR_NUMBER"] = number
    os.environ["REVIEW_SCOPE"] = "pr"
    os.environ["GROK_REVIEW_OUT"] = out
    try:
        return main(["review"])
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == "review-one":
        return review_one(argv[1:])
    args = _parser().parse_args(argv)
    out = args.out or os.environ.get("GROK_REVIEW_OUT", "").strip()
    if args.command == "review" and not out:
        out = "grok-review-report.json"
    if args.command == "review" and not os.environ.get("XAI_API_KEY", "").strip():
        print("FAIL: XAI_API_KEY 가 없다 — 리뷰를 실행하지 않았다")
        return 1
    scope = args.scope or os.environ.get("REVIEW_SCOPE", "pr").strip() or "pr"
    if scope == "open-prs":
        if args.command != "review":
            print("FAIL: open-prs 는 review 에서만 돈다")
            return 1
        try:
            return run_schedule(out, _review_with_env)
        except engine.ReviewError as error:
            print(str(error))
            _summary_file(str(error))
            return 1
    try:
        planned, sha, scope = build_plan(args)
        reviewed = [item for item in planned if item.action == "review"]
        skipped = [(item.path, item.reason) for item in planned if item.action == "skip"]
        reviewed_lines = sum(item.line_count for item in reviewed)
        chunk_count = sum(1 for item in reviewed for chunk in item.chunks if chunk.end != 0)
        if args.command == "plan":
            payload = _report(planned, sha, os.environ.get("XAI_MODEL", "").strip() or DEFAULT_MODEL, scope, [], 0, False)
            if out:
                write_report(out, payload)
            print(
                f"PASS: plan files={len(reviewed)} lines={reviewed_lines} "
                f"chunks={chunk_count} skipped={len(skipped)}"
            )
            return 0

        model = os.environ.get("XAI_MODEL", "").strip() or DEFAULT_MODEL
        effort = os.environ.get("GROK_REASONING_EFFORT", "").strip() or "medium"
        timeout = _positive_int("GROK_REVIEW_TIMEOUT", 180)
        api_key = os.environ["XAI_API_KEY"].strip()
        findings, api_calls = review_chunks(planned, api_key, model, effort, timeout)
        payload = _report(planned, sha, model, scope, findings, api_calls, True)
        write_report(out, payload)
        commentable: dict[str, set[int]] = {}
        if scope == "pr":
            base = resolve_commit(os.environ.get("REVIEW_BASE", "").strip() or "origin/main")
            commentable = engine.commentable_right_lines(diff_text(base, sha))
        requests = engine.build_review_requests(
            findings,
            commentable,
            sha=sha,
            model=model,
            scope=scope,
            reviewed_lines=reviewed_lines,
            reviewed_files=len(reviewed),
            chunks=chunk_count,
            api_calls=api_calls,
            skipped=skipped,
        )
        _summary_file(requests[0]["body"])
        pr = os.environ.get("PR_NUMBER", "").strip()
        if pr in {"null", "0"}:
            pr = ""
        token = os.environ.get("GITHUB_TOKEN", "").strip()
        repo = os.environ.get("GITHUB_REPOSITORY", "").strip()
        if pr and token and repo and SHA_RE.fullmatch(sha):
            post_reviews(requests, repo, pr, token, timeout)
        elif pr or token or repo:
            if not SHA_RE.fullmatch(sha):
                print("NOT_POSTED: 커밋 SHA 가 아니라 코멘트를 달지 않았다")
            else:
                raise engine.ReviewError("FAIL: PR 게시 환경이 불완전하다 — PR_NUMBER, GITHUB_TOKEN, GITHUB_REPOSITORY 가 함께 있어야 한다")
        else:
            print("NOT_POSTED: PR 번호가 없어 리포트만 남겼다")
        high = sum(1 for item in payload["findings"] if item["severity"] == "high")
        stats = (
            f"lines={reviewed_lines} files={len(reviewed)} chunks={chunk_count} "
            f"api_calls={api_calls} findings={len(payload['findings'])} skipped={len(skipped)}"
        )
        fail_on = os.environ.get("GROK_REVIEW_FAIL_ON", "").strip()
        if fail_on == "high" and high:
            print(f"FAIL: high 지적 {high}건 — GROK_REVIEW_FAIL_ON=high ({stats})")
            return 1
        print(f"PASS: reviewed {stats}")
        return 0
    except engine.ReviewError as error:
        print(str(error))
        _summary_file(str(error))
        return 1


if __name__ == "__main__":
    sys.exit(main())
