"""Grok 라인 리뷰의 순수 판정.

네트워크와 git 은 여기 없다. 커버리지는 모델의 자백이 아니라
이 모듈이 만든 청크가 파일의 모든 줄을 정확히 한 번씩 담는지로 증명한다.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass


class ReviewError(Exception):
    """리뷰를 완료로 기록하면 안 되는 상태."""


SEVERITIES = ("high", "medium", "low")
CATEGORIES = (
    "security",
    "correctness",
    "data-loss",
    "error-handling",
    "test",
    "performance",
)
BINARY_SUFFIXES = (
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".pdf",
    ".zip", ".gz", ".woff", ".woff2", ".ttf", ".eot", ".mp4",
    ".mov", ".pyc", ".db", ".sqlite", ".sqlite3", ".wasm",
)
SECRET_BASENAMES = {".env", ".secret-patterns"}
INLINE_BATCH = 40
SUMMARY_FINDING_CAP = 40
SUMMARY_SKIP_CAP = 50


@dataclass(frozen=True)
class Chunk:
    path: str
    start: int
    end: int
    text: str


@dataclass(frozen=True)
class Finding:
    path: str
    line: int
    severity: str
    category: str
    title: str
    why: str
    fix: str


@dataclass(frozen=True)
class PlannedFile:
    path: str
    action: str
    reason: str
    line_count: int
    chunks: tuple[Chunk, ...]


def split_chunks(path: str, text: str, max_lines: int, max_bytes: int | None = None) -> list[Chunk]:
    """모든 줄을 정확히 한 번씩 담는다. 바이트 한도는 청크를 나눌 뿐 줄을 버리지 않는다."""
    if max_lines < 1:
        raise ReviewError("max_lines 는 1 이상이어야 한다")
    if max_bytes is not None and max_bytes < 1:
        raise ReviewError("max_bytes 는 1 이상이어야 한다")
    lines = text.splitlines()
    if not lines:
        return [Chunk(path, 1, 0, "")]
    chunks: list[Chunk] = []
    start = 1
    total = len(lines)
    while start <= total:
        end = start
        body_lines: list[str] = []
        while end <= total and (end - start) < max_lines:
            numbered = f"{end}|{lines[end - 1]}"
            projected = "\n".join([*body_lines, numbered])
            if body_lines and max_bytes is not None and len(projected.encode("utf-8")) > max_bytes:
                break
            body_lines.append(numbered)
            end += 1
            if max_bytes is not None and len(numbered.encode("utf-8")) > max_bytes:
                break
        chunks.append(Chunk(path, start, end - 1, "\n".join(body_lines)))
        start = end
    return chunks


def assert_chunks_cover(text: str, chunks: list[Chunk] | tuple[Chunk, ...]) -> int:
    """1..N 이 순서대로 정확히 한 번씩 들어 있고, 본문에 그 줄이 있는지 확인한다."""
    lines = text.splitlines()
    total = len(lines)
    if total == 0:
        if len(chunks) != 1 or chunks[0].start != 1 or chunks[0].end != 0 or chunks[0].text != "":
            raise ReviewError("빈 파일이 매니페스트에 없다")
        return 0
    seen: list[int] = []
    for chunk in chunks:
        if chunk.end < chunk.start:
            raise ReviewError(f"역전된 범위 — {chunk.path}:{chunk.start}-{chunk.end}")
        expected = [f"{number}|{lines[number - 1]}" for number in range(chunk.start, chunk.end + 1)]
        if chunk.text.splitlines() != expected:
            raise ReviewError(f"청크 본문이 원문과 다르다 — {chunk.path}:{chunk.start}-{chunk.end}")
        seen.extend(range(chunk.start, chunk.end + 1))
    if seen != list(range(1, total + 1)):
        raise ReviewError(f"줄 커버리지 구멍 또는 중복 — {chunks[0].path if chunks else '?'} expected=1..{total}")
    return total


def _basename(path: str) -> str:
    return path.rsplit("/", 1)[-1]


def classify(path: str, data: bytes) -> str | None:
    """리뷰할 수 없는 파일만 사유를 돌려준다. 텍스트 줄은 용량으로 빼지 않는다."""
    name = _basename(path)
    if name in SECRET_BASENAMES or name.startswith(".env."):
        return "secret-file"
    lowered = path.lower()
    if lowered.endswith(BINARY_SUFFIXES):
        return "binary-suffix"
    if b"\0" in data[:8192]:
        return "binary-nul"
    try:
        data.decode("utf-8")
    except UnicodeDecodeError:
        return "not-utf8"
    return None


def plan_bytes(path: str, data: bytes | None, *, max_lines: int, max_bytes: int) -> PlannedFile:
    if max_bytes < 1:
        raise ReviewError("max_bytes 는 1 이상이어야 한다")
    if data is None:
        return PlannedFile(path, "skip", "missing-blob", 0, ())
    reason = classify(path, data)
    if reason is not None:
        return PlannedFile(path, "skip", reason, 0, ())
    text = data.decode("utf-8")
    chunks = tuple(split_chunks(path, text, max_lines, max_bytes))
    line_count = assert_chunks_cover(text, chunks)
    return PlannedFile(path, "review", "", line_count, chunks)


def system_prompt() -> str:
    return (
        "당신은 라인 단위 코드 리뷰어다. 추측하지 않는다. "
        "스타일, 포맷, 이름 취향은 지적하지 않는다. "
        "확실한 결함만 적는다: 보안, 잘못된 동작, 데이터 손실, 실패를 삼키는 경로, "
        "테스트가 거짓으로 통과하는 구조, 명확한 성능 사고. "
        "출력은 JSON 객체 하나만. JSON 밖에 문장을 쓰지 않는다. "
        '{"findings":[{"line":1,"severity":"high","category":"correctness",'
        '"title":"...","why":"...","fix":"..."}]} '
        "severity 는 high, medium, low 중 하나다. "
        "category 는 security, correctness, data-loss, error-handling, test, performance 중 하나다. "
        "line 은 검토 범위 안의 정수만 허용한다. 결함이 없으면 findings 는 빈 배열이다. "
        "빈 배열은 그 범위를 읽었고 결함이 없다는 뜻이다."
    )


def user_prompt(chunk: Chunk) -> str:
    if chunk.end == 0:
        return (
            f"파일: {chunk.path}\n"
            "이 파일은 빈 파일이다. 검토할 줄이 없다. findings 는 빈 배열로 답한다.\n"
        )
    return (
        f"파일: {chunk.path}\n"
        f"검토 범위: {chunk.start}-{chunk.end}. 이 범위의 모든 줄을 읽는다.\n"
        "형식: 줄번호|내용\n\n"
        f"{chunk.text}\n"
    )


def _clip(value: str, limit: int) -> str:
    text = value.strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "…"


def _extract_json_object(text: str) -> dict:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?\s*", "", stripped)
        stripped = re.sub(r"\s*```$", "", stripped)
    try:
        obj = json.loads(stripped)
    except json.JSONDecodeError:
        obj = None
    if isinstance(obj, dict):
        return obj
    decoder = json.JSONDecoder()
    found: list[dict] = []
    index = 0
    while index < len(stripped):
        start = stripped.find("{", index)
        if start < 0:
            break
        try:
            parsed, offset = decoder.raw_decode(stripped[start:])
        except json.JSONDecodeError:
            index = start + 1
            continue
        if isinstance(parsed, dict):
            found.append(parsed)
        index = start + offset
    if len(found) != 1:
        raise ReviewError(f"JSON 객체 {len(found)}개 — 하나여야 한다")
    return found[0]


def parse_findings(text: str, chunk: Chunk) -> list[Finding]:
    obj = _extract_json_object(text)
    raw = obj.get("findings")
    if not isinstance(raw, list):
        raise ReviewError("findings 가 배열이 아니다")
    findings: list[Finding] = []
    for item in raw:
        if not isinstance(item, dict):
            raise ReviewError("finding 이 객체가 아니다")
        line = item.get("line")
        severity = item.get("severity")
        category = item.get("category")
        title = item.get("title")
        why = item.get("why")
        fix = item.get("fix")
        if isinstance(line, bool) or not isinstance(line, int):
            raise ReviewError("line 이 정수가 아니다")
        if chunk.end == 0 or line < chunk.start or line > chunk.end:
            raise ReviewError(f"범위 밖 줄 — {chunk.path}:{line}")
        if severity not in SEVERITIES:
            raise ReviewError(f"severity 거부 — {severity!r}")
        if category not in CATEGORIES:
            raise ReviewError(f"category 거부 — {category!r}")
        if not isinstance(title, str) or not isinstance(why, str) or not isinstance(fix, str):
            raise ReviewError("title, why, fix 는 문자열이어야 한다")
        if not title.strip() or not why.strip() or not fix.strip():
            raise ReviewError("title, why, fix 가 비었다")
        model_path = item.get("path")
        if model_path is not None and model_path != chunk.path:
            raise ReviewError(f"다른 파일 지적 — {model_path}")
        findings.append(Finding(
            path=chunk.path,
            line=line,
            severity=severity,
            category=category,
            title=_clip(title, 160),
            why=_clip(why, 2000),
            fix=_clip(fix, 2000),
        ))
    return findings


def parse_name_status_z(blob: str) -> list[tuple[str, str, str | None]]:
    """git diff --name-status -z 결과. (코드, 경로, 옛 경로)."""
    parts = blob.split("\0")
    if parts and parts[-1] == "":
        parts.pop()
    records: list[tuple[str, str, str | None]] = []
    index = 0
    while index < len(parts):
        status = parts[index]
        if not status:
            raise ReviewError("name-status 레코드가 비었다")
        code = status[0]
        if code in {"R", "C"}:
            if index + 2 >= len(parts):
                raise ReviewError("rename/copy 레코드가 잘렸다")
            records.append((code, parts[index + 2], parts[index + 1]))
            index += 3
            continue
        if code not in {"A", "M", "D", "T"}:
            raise ReviewError(f"알 수 없는 name-status — {status}")
        if index + 1 >= len(parts):
            raise ReviewError("name-status 레코드가 잘렸다")
        records.append((code, parts[index + 1], None))
        index += 2
    return records


def commentable_right_lines(diff: str) -> dict[str, set[int]]:
    """GitHub 인라인 코멘트가 가능한 새 파일 줄 번호."""
    result: dict[str, set[int]] = {}
    path: str | None = None
    new_line: int | None = None
    for raw in diff.splitlines():
        if raw.startswith("diff --git "):
            path = None
            new_line = None
            continue
        if raw.startswith("+++ "):
            name = raw[4:]
            if name.startswith("b/"):
                name = name[2:]
            path = None if name == "/dev/null" else name
            new_line = None
            if path is not None:
                result.setdefault(path, set())
            continue
        if raw.startswith("@@"):
            match = re.search(r"\+(\d+)", raw)
            new_line = int(match.group(1)) if match else None
            continue
        if path is None or new_line is None:
            continue
        if raw.startswith("+"):
            result[path].add(new_line)
            new_line += 1
        elif raw.startswith("-") or raw.startswith("\\"):
            continue
        else:
            result[path].add(new_line)
            new_line += 1
    return result


def dedupe_findings(findings: list[Finding]) -> list[Finding]:
    seen: set[tuple[str, int, str]] = set()
    ordered = sorted(findings, key=lambda item: (item.path, item.line, SEVERITIES.index(item.severity)))
    unique: list[Finding] = []
    for finding in ordered:
        key = (finding.path, finding.line, finding.title)
        if key in seen:
            continue
        seen.add(key)
        unique.append(finding)
    return unique


def _comment_body(finding: Finding) -> str:
    return (
        f"**{finding.severity} · {finding.category}** {finding.title}\n\n"
        f"왜: {finding.why}\n\n"
        f"고침: {finding.fix}"
    )


def _cap(items: list[str], limit: int) -> list[str]:
    if len(items) <= limit:
        return items
    hidden = len(items) - limit
    return items[:limit] + [f"… 외 {hidden}건은 리포트 JSON 에 있다"]


def render_summary(
    *,
    sha: str,
    model: str,
    scope: str,
    reviewed_lines: int,
    reviewed_files: int,
    chunks: int,
    api_calls: int,
    skipped: list[tuple[str, str]],
    inline: list[Finding],
    overflow: list[Finding],
) -> str:
    skip_lines = _cap([f"- `{path}` — {reason}" for path, reason in skipped], SUMMARY_SKIP_CAP)
    def render_finding(item: Finding) -> str:
        return f"- `{item.path}:{item.line}` **{item.severity}** {item.title} — {item.why} / {item.fix}"
    inline_lines = _cap([render_finding(item) for item in inline], SUMMARY_FINDING_CAP)
    overflow_lines = _cap([render_finding(item) for item in overflow], SUMMARY_FINDING_CAP)
    parts = [
        review_marker(sha),
        "## Grok 라인 리뷰",
        "",
        f"- 모델: `{model}`",
        f"- 범위: `{scope}`",
        f"- SHA: `{sha}`",
        f"- 검토한 줄: {reviewed_lines} (파일 {reviewed_files}개, 청크 {chunks}개, API {api_calls}회)",
        f"- 인라인 코멘트: {len(inline)}",
        f"- 건너뜀: {len(skipped)} (비밀 파일·바이너리·UTF-8 아님. 텍스트 줄은 용량으로 빼지 않음)",
        "",
        "초록 체크는 결함이 없다는 뜻이 아니다. 대상 줄을 모두 보냈다는 뜻이다.",
        "결함은 이 코멘트와 인라인 코멘트다.",
        "",
        "### 건너뛴 파일",
        *(skip_lines or ["- 없음"]),
        "",
        "### 지적",
        *(inline_lines or ["- 인라인으로 달 지적 없음"]),
        "",
        "### diff 밖이라 인라인으로 달지 못한 지적",
        *(overflow_lines or ["- 없음"]),
        "",
    ]
    return "\n".join(parts)


def review_marker(sha: str) -> str:
    return f"<!-- grok-review sha={sha.lower()} -->"


def already_reviewed(bodies: list[str], sha: str) -> bool:
    marker = review_marker(sha)
    return any(marker in body for body in bodies)


def parse_open_pulls(payload: object) -> list[tuple[str, str, str]]:
    """GitHub PR 목록 JSON. (번호, base sha, head sha). 필드가 없으면 실패한다."""
    if not isinstance(payload, list):
        raise ReviewError("PR 목록이 배열이 아니다")
    records: list[tuple[str, str, str]] = []
    for item in payload:
        if not isinstance(item, dict):
            raise ReviewError("PR 항목이 객체가 아니다")
        number = item.get("number")
        base = item.get("base")
        head = item.get("head")
        base_sha = base.get("sha") if isinstance(base, dict) else None
        head_sha = head.get("sha") if isinstance(head, dict) else None
        if isinstance(number, bool) or not isinstance(number, int) or number < 1:
            raise ReviewError("PR 번호가 없다")
        if not isinstance(base_sha, str) or not re.fullmatch(r"[0-9a-fA-F]{40}", base_sha):
            raise ReviewError(f"PR {number} 의 base SHA 가 없다")
        if not isinstance(head_sha, str) or not re.fullmatch(r"[0-9a-fA-F]{40}", head_sha):
            raise ReviewError(f"PR {number} 의 head SHA 가 없다")
        records.append((str(number), base_sha.lower(), head_sha.lower()))
    return records


def parse_review_bodies(payload: object) -> list[str]:
    if not isinstance(payload, list):
        raise ReviewError("리뷰 목록이 배열이 아니다")
    bodies: list[str] = []
    for item in payload:
        if not isinstance(item, dict):
            raise ReviewError("리뷰 항목이 객체가 아니다")
        body = item.get("body")
        if body is None:
            continue
        if not isinstance(body, str):
            raise ReviewError("리뷰 본문이 문자열이 아니다")
        bodies.append(body)
    return bodies


def build_review_requests(
    findings: list[Finding],
    commentable: dict[str, set[int]],
    *,
    sha: str,
    model: str,
    scope: str,
    reviewed_lines: int,
    reviewed_files: int,
    chunks: int,
    api_calls: int,
    skipped: list[tuple[str, str]],
) -> list[dict]:
    unique = dedupe_findings(findings)
    inline: list[Finding] = []
    overflow: list[Finding] = []
    for finding in unique:
        if finding.line in commentable.get(finding.path, set()):
            inline.append(finding)
        else:
            overflow.append(finding)
    summary = render_summary(
        sha=sha,
        model=model,
        scope=scope,
        reviewed_lines=reviewed_lines,
        reviewed_files=reviewed_files,
        chunks=chunks,
        api_calls=api_calls,
        skipped=skipped,
        inline=inline,
        overflow=overflow,
    )
    requests: list[dict] = [{"commit_id": sha, "event": "COMMENT", "body": summary}]
    for offset in range(0, len(inline), INLINE_BATCH):
        batch = inline[offset:offset + INLINE_BATCH]
        body = "줄 단위 코멘트" if offset == 0 else f"Grok 라인 리뷰 이어서 ({offset // INLINE_BATCH + 1})"
        requests.append({
            "commit_id": sha,
            "event": "COMMENT",
            "body": body,
            "comments": [
                {"path": item.path, "line": item.line, "side": "RIGHT", "body": _comment_body(item)}
                for item in batch
            ],
        })
    return requests
