"""PR diff 를 청크로 나누고, 추가·삭제 줄이 정확히 한 번씩 들어갔는지 증명한다.

네트워크와 git 은 여기 없다. 설정 파일은 이 모듈과 같은 디렉터리의
review-config.json 만 읽는다. PR 트리의 같은 이름 파일은 보지 않는다.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path

import engine

CONFIG_PATH = Path(__file__).resolve().parent / "review-config.json"
HUNK_RE = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")
SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2}


@dataclass(frozen=True)
class DiffLine:
    path: str
    sign: str
    line_no: int
    text: str

    def key(self) -> str:
        return f"{self.path}\t{self.sign}\t{self.line_no}\t{self.text}"

    def display(self) -> str:
        return f"{self.sign}{self.line_no}|{self.text}"


@dataclass(frozen=True)
class PackedChunk:
    chunk_id: str
    lines: tuple[DiffLine, ...]
    text: str
    sha256: str

    def files(self) -> list[str]:
        seen: list[str] = []
        for item in self.lines:
            if item.path not in seen:
                seen.append(item.path)
        return seen

    def allowed(self) -> dict[str, set[int]]:
        found: dict[str, set[int]] = {}
        for item in self.lines:
            found.setdefault(item.path, set()).add(item.line_no)
        return found


@dataclass(frozen=True)
class PackResult:
    changed_lines: int
    chunks: tuple[PackedChunk, ...]
    excluded: tuple[str, ...]
    missing: int
    duplicate: int
    too_large: bool
    max_chunks: int


def load_config() -> dict:
    try:
        payload = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise engine.ReviewError(f"FAIL: 리뷰 설정을 읽지 못했다 — {error}") from error
    if not isinstance(payload, dict):
        raise engine.ReviewError("FAIL: 리뷰 설정이 객체가 아니다")
    for key in ("max_changed_lines_per_chunk", "max_chunks", "call_timeout_seconds", "max_findings_per_chunk"):
        value = payload.get(key)
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            raise engine.ReviewError(f"FAIL: 설정 {key} 가 양의 정수가 아니다")
    globs = payload.get("exclude_globs")
    if not isinstance(globs, list) or not globs or not all(isinstance(item, str) and item for item in globs):
        raise engine.ReviewError("FAIL: exclude_globs 가 비었다")
    return payload


def _compile_glob(pattern: str) -> re.Pattern[str]:
    parts: list[str] = []
    index = 0
    while index < len(pattern):
        if pattern.startswith("**/", index):
            parts.append("(?:.*/)?")
            index += 3
        elif pattern.startswith("**", index):
            parts.append(".*")
            index += 2
        elif pattern[index] == "*":
            parts.append("[^/]*")
            index += 1
        elif pattern[index] == "?":
            parts.append("[^/]")
            index += 1
        else:
            parts.append(re.escape(pattern[index]))
            index += 1
    return re.compile("^" + "".join(parts) + "$")


def excluded_path(path: str, patterns: list[re.Pattern[str]]) -> bool:
    return any(pattern.fullmatch(path) for pattern in patterns)


def parse_unified(diff: str) -> list[DiffLine]:
    """통합 diff 의 추가·삭제 줄만 뽑는다. 문맥 줄은 번호를 전진시키기만 한다."""
    parsed: list[DiffLine] = []
    path: str | None = None
    old_line = 0
    new_line = 0
    in_hunk = False
    for raw in diff.splitlines():
        if raw.startswith("diff --git "):
            path = None
            in_hunk = False
            continue
        if raw.startswith("Binary files "):
            raise engine.ReviewError("FAIL: 바이너리 diff 가 제외되지 않았다")
        if raw.startswith("--- "):
            name = raw[4:]
            if name.startswith("a/"):
                name = name[2:]
            if name != "/dev/null":
                path = name
            in_hunk = False
            continue
        if raw.startswith("+++ "):
            name = raw[4:]
            if name.startswith("b/"):
                name = name[2:]
            if name != "/dev/null":
                path = name
            continue
        header = HUNK_RE.match(raw)
        if header:
            if path is None:
                raise engine.ReviewError("FAIL: hunk 앞에 파일 경로가 없다")
            old_line = int(header.group(1))
            new_line = int(header.group(3))
            in_hunk = True
            continue
        if not in_hunk or path is None or raw.startswith("\\"):
            continue
        if raw.startswith("+"):
            parsed.append(DiffLine(path, "+", new_line, raw[1:]))
            new_line += 1
        elif raw.startswith("-"):
            parsed.append(DiffLine(path, "-", old_line, raw[1:]))
            old_line += 1
        elif raw.startswith(" "):
            old_line += 1
            new_line += 1
        else:
            raise engine.ReviewError("FAIL: diff 줄을 해석하지 못했다")
    return parsed


def _chunk_text(lines: tuple[DiffLine, ...]) -> str:
    blocks: list[str] = []
    current: str | None = None
    body: list[str] = []
    for item in lines:
        if item.path != current:
            if current is not None:
                blocks.append(f"파일: {current}\n" + "\n".join(body))
            current = item.path
            body = []
        body.append(item.display())
    if current is not None:
        blocks.append(f"파일: {current}\n" + "\n".join(body))
    return "\n\n".join(blocks)


def _pack_lines(lines: list[DiffLine], max_lines: int) -> list[PackedChunk]:
    if max_lines < 1:
        raise engine.ReviewError("FAIL: 청크 줄 상한이 1 미만이다")
    grouped: list[list[DiffLine]] = []
    for item in lines:
        if not grouped or grouped[-1][0].path != item.path:
            grouped.append([item])
        else:
            grouped[-1].append(item)
    slices: list[tuple[DiffLine, ...]] = []
    current: list[DiffLine] = []
    for group in grouped:
        offset = 0
        while offset < len(group):
            room = max_lines - len(current)
            if room == 0:
                slices.append(tuple(current))
                current = []
                room = max_lines
            take = min(room, len(group) - offset)
            current.extend(group[offset:offset + take])
            offset += take
            if len(current) == max_lines:
                slices.append(tuple(current))
                current = []
    if current:
        slices.append(tuple(current))
    packed: list[PackedChunk] = []
    for index, slice_lines in enumerate(slices, start=1):
        text = _chunk_text(slice_lines)
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        packed.append(PackedChunk(f"c{index}", slice_lines, text, digest))
    return packed


def assert_coverage(lines: list[DiffLine], chunks: list[PackedChunk]) -> None:
    expected = [item.key() for item in lines]
    seen: list[str] = []
    for chunk in chunks:
        displays = chunk.text.splitlines()
        for item in chunk.lines:
            if item.display() not in displays:
                raise engine.ReviewError(f"FAIL: 청크 본문에 줄이 없다 — {item.path}:{item.line_no}")
            seen.append(item.key())
    if len(seen) != len(set(seen)):
        raise engine.ReviewError("FAIL: 변경 줄이 두 청크에 들어갔다")
    if set(seen) != set(expected) or len(seen) != len(expected):
        raise engine.ReviewError("FAIL: 변경 줄 커버리지 구멍 또는 중복")


def pack_diff(diff: str, config: dict | None = None) -> PackResult:
    cfg = config or load_config()
    patterns = [_compile_glob(item) for item in cfg["exclude_globs"]]
    parsed = parse_unified(diff)
    excluded = tuple(dict.fromkeys(item.path for item in parsed if excluded_path(item.path, patterns)))
    kept = [item for item in parsed if not excluded_path(item.path, patterns)]
    chunks = _pack_lines(kept, cfg["max_changed_lines_per_chunk"])
    assert_coverage(kept, chunks)
    too_large = len(chunks) > cfg["max_chunks"]
    return PackResult(
        changed_lines=len(kept),
        chunks=tuple(chunks),
        excluded=excluded,
        missing=0,
        duplicate=0,
        too_large=too_large,
        max_chunks=cfg["max_chunks"],
    )


def manifest(result: PackResult) -> list[dict]:
    rows: list[dict] = []
    for chunk in result.chunks:
        hunks = []
        for path in chunk.files():
            old = [item.line_no for item in chunk.lines if item.path == path and item.sign == "-"]
            new = [item.line_no for item in chunk.lines if item.path == path and item.sign == "+"]
            hunks.append({
                "file": path,
                "old_start": min(old) if old else 0,
                "old_end": max(old) if old else 0,
                "new_start": min(new) if new else 0,
                "new_end": max(new) if new else 0,
            })
        rows.append({
            "id": chunk.chunk_id,
            "files": chunk.files(),
            "hunks": hunks,
            "changed_lines": len(chunk.lines),
            "sha256": chunk.sha256,
        })
    return rows


def prompts(chunk: PackedChunk, pr_body: str) -> tuple[str, str]:
    body = pr_body.strip()
    if len(body) > 4000:
        body = body[:3999] + "…"
    system = (
        "당신은 diff 리뷰어다. 출력은 JSON 객체 하나만. JSON 밖에 문장을 쓰지 않는다. "
        "첫 질문: PR 본문에 적힌 parent AC, micro_id 의도와 이 diff 가 어긋나는가. "
        "본문에 그 항목이 없으면 없다는 이유로 지적하지 않는다. 어긋날 때만 finding 으로 남긴다. "
        "그 다음, 이 diff 안의 확실한 결함만 남긴다. 스타일, 칭찬, 요약 문단, 일반론은 쓰지 않는다. "
        "스키마: {\"chunk_id\":\"" + chunk.chunk_id + "\",\"findings\":["
        "{\"severity\":\"high|medium|low\",\"file\":\"경로\",\"line\":1,\"reason\":\"한국어 한 문장\"}]} "
        "findings 는 최대 7개다. reason 은 한국어 한 문장이다. 결함이 없으면 findings 는 빈 배열이다."
    )
    user = (
        f"chunk_id: {chunk.chunk_id}\n"
        "PR 본문:\n"
        f"{body or '(본문 없음)'}\n\n"
        "아래는 이 청크의 추가·삭제 줄이다. 기호 +는 새 줄, -는 삭제 줄이고 숫자는 그 파일의 줄 번호다.\n\n"
        f"{chunk.text}\n"
    )
    return system, user


def parse_chunk_output(text: str, chunk: PackedChunk, *, max_findings: int, reason_max: int) -> tuple[list[dict], int]:
    """스키마에 맞으면 (findings, 버린 수). 스키마가 깨지면 ReviewError."""
    obj = engine._extract_json_object(text)
    if obj.get("chunk_id") != chunk.chunk_id:
        raise engine.ReviewError(f"chunk_id 불일치 — {obj.get('chunk_id')!r}")
    raw = obj.get("findings")
    if not isinstance(raw, list):
        raise engine.ReviewError("findings 가 배열이 아니다")
    if len(raw) > max_findings:
        raise engine.ReviewError(f"findings 가 {max_findings}개를 넘었다")
    allowed = chunk.allowed()
    kept: list[dict] = []
    dropped = 0
    for item in raw:
        if not isinstance(item, dict):
            raise engine.ReviewError("finding 이 객체가 아니다")
        severity = item.get("severity")
        file_name = item.get("file")
        line = item.get("line")
        reason = item.get("reason")
        if severity not in SEVERITY_ORDER:
            raise engine.ReviewError(f"severity 거부 — {severity!r}")
        if not isinstance(file_name, str) or not file_name:
            raise engine.ReviewError("file 이 비었다")
        if isinstance(line, bool) or not isinstance(line, int):
            raise engine.ReviewError("line 이 정수가 아니다")
        if not isinstance(reason, str) or not reason.strip() or "\n" in reason or len(reason.strip()) > reason_max:
            raise engine.ReviewError("reason 은 한 줄이어야 한다")
        if file_name not in allowed or line not in allowed[file_name]:
            dropped += 1
            continue
        kept.append({
            "severity": severity,
            "file": file_name,
            "line": line,
            "reason": reason.strip(),
        })
    return kept, dropped


def render_comment(
    *,
    sha: str,
    result: PackResult,
    findings: list[dict],
    failures: list[dict],
    dropped: int,
    compare: str,
) -> str:
    ordered = sorted(findings, key=lambda item: (SEVERITY_ORDER[item["severity"]], item["file"], item["line"]))
    finding_lines = [
        f"- {item['severity']} `{item['file']}:{item['line']}` {item['reason']}"
        for item in ordered
    ]
    failure_lines = [f"- `{item['chunk_id']}` {item['detail']}" for item in failures]
    parts = [
        engine.review_marker(sha),
        "## Grok 리뷰",
        "",
        "이 코멘트는 참고 의견이다. 초록 체크는 파이프라인이 끝까지 돌았다는 뜻이다.",
        "",
        f"- 비교: `{compare}`",
        f"- 변경 줄: {result.changed_lines}",
        f"- 청크: {len(result.chunks)}",
        f"- 누락: {result.missing}",
        f"- 중복: {result.duplicate}",
        f"- 제외 파일: {len(result.excluded)}",
        f"- 범위 밖이라 버린 지적: {dropped}",
        "",
    ]
    if result.too_large:
        parts.extend([
            f"규모 초과, 수동 분할 필요 (청크 {len(result.chunks)} > 상한 {result.max_chunks}). 모델은 호출하지 않았다.",
            "",
        ])
    parts.extend(["### 지적", *(finding_lines or ["- 없음"]), "", "### 실패 청크", *(failure_lines or ["- 없음"]), ""])
    return "\n".join(parts)
