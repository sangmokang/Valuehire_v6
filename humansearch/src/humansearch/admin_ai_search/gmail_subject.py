"""Deterministic parsing for AI Search Gmail subject evidence."""

from __future__ import annotations

import re

_METADATA_TAG = re.compile(
    r"(?:ai\s*search|aisearch|태그|신규\s*포지션\s*서치|후보\s*알림)",
    re.IGNORECASE,
)
_ACTOR_TOKEN = re.compile(
    r"^(?:grok(?:bot|[-_]?\d+(?:\.\d+)?)?|claude[\s_-]*code|claude-win|chatgpt|codex|aside|gemini)[:,.;]?\s+",
    re.IGNORECASE,
)
_NON_RUN_SUBJECT = re.compile(
    r"(?:\[(?:test|테스트(?:\s*메일)?|dry[- ]?run|smoke(?:\s*test)?|fixture)\]|"
    r"\b테스트\s*메일\b|\bdry[- ]?run\b|\bsmoke\s*test\b)",
    re.IGNORECASE,
)
_REPLY_PREFIX = re.compile(r"^\s*(?:(?:re|fw|fwd)\s*:\s*)+", re.IGNORECASE)


_MARKERS = (
    (re.compile(r"grok(?:bot|\d+(?:\.\d+)?)?"), "GROK", "grok"),
    (re.compile(r"claudecode"), "CLAUDE_CODE", "claude_code"),
    (re.compile(r"chatgpt"), "CHATGPT", "chatgpt"),
    (re.compile(r"codex"), "CODEX", "codex"),
    (re.compile(r"aside"), "ASIDE", "aside"),
    (re.compile(r"claudewin"), "OTHER", "claude_win"),
    (re.compile(r"gemini"), "OTHER", "gemini"),
)
_BODY_LABEL = re.compile(
    r"^\s*(?:[-*]\s*)?(?:실행\s*(?:주체|AI|도구)|executor)\s*[:：]\s*([^\n]+)",
    re.IGNORECASE | re.MULTILINE,
)
_OPENAI_TASK_SENDER = re.compile(r"<noreply@tm\.openai\.com>\s*$", re.IGNORECASE)


def classify_actor(subject: str, sender: str, body: str = "") -> tuple[str, str]:
    """Classify explicit subject, sender or body evidence; otherwise fail closed."""

    actor, reason = _subject_actor(subject)
    if actor not in {"AI_SEARCH", "OTHER"} or reason.startswith(("unsupported_marker", "actor_markers")):
        return actor, reason
    if _OPENAI_TASK_SENDER.search(sender.strip()) is not None:
        return "CHATGPT", "sender:openai_chatgpt_task"
    if reason != "subject_marker:ai_search":
        return actor, reason
    # Unknown labels stay in the set so conflicts and unsupported tools fail closed.
    labels = {_token_actor(part) or ("OTHER", "unknown")
              for match in _BODY_LABEL.finditer(body)
              for part in re.split(r"[,/|()+&·]", match.group(1)) if part.strip()}
    actors = {label[0] for label in labels}
    if len(actors) > 1:
        return "OTHER", "body_label_conflict"
    if actors == {"OTHER"}:
        return "OTHER", "unsupported_body_label"
    if labels:
        label_actor, marker = min(labels)
        return label_actor, f"body_label:{marker}"
    return actor, reason


def _token_actor(token: str) -> tuple[str, str] | None:
    normalized = re.sub(r"[\s_-]+", "", token.lower())
    for pattern, actor, marker in _MARKERS:
        if pattern.fullmatch(normalized):
            return actor, marker
    return None


def _joined_markers(token: str) -> list[tuple[str, str]]:
    """A token names tools only when it is one tool or made entirely of tool names."""
    whole = _token_actor(token)
    if whole:
        return [whole]
    parts = [part for part in re.split(r"[-_+/]", token) if part]
    found = [_token_actor(part) for part in parts]
    if len(parts) > 1 and all(found):
        return [marker for marker in found if marker]
    pieces = re.findall("|".join(f"(?:{p.pattern})" for p, _, _ in _MARKERS), token)
    if len(pieces) > 1 and "".join(pieces) == token:
        return [marker for piece in pieces if (marker := _token_actor(piece))]
    return []


def _subject_actor(subject: str) -> tuple[str, str]:
    subject_parts = _subject_parts(subject)
    if subject_parts is None:
        return "OTHER", "ai_search_prefix_not_found"
    prefix, remainder = subject_parts
    if "aisearch" not in prefix:
        return "OTHER", "ai_search_prefix_not_found"
    region = prefix.replace("aisearch", "", 1)
    markers: list[tuple[str, str]]
    if prefix == "aisearch":
        # Only the first token names the tool; later words may mention other tools.
        first = _strip_metadata_tags(remainder.strip()).split("[", 1)[0].lower().split()
        words = [word.rstrip(":,.;") for word in first[:2]]
        lead = "claude code" if words == ["claude", "code"] else (first[0] if first else "")
        markers = _joined_markers(lead.rstrip(":,.;"))
    else:
        # Prefix tags may add Korean words, e.g. [ChatGPT AI Search 결과].
        markers = _joined_markers(re.sub(r"[^a-z0-9.]", "", region))
    if len(markers) > 1:
        return "OTHER", "actor_markers_conflict"
    if markers:
        actor, marker = markers[0]
        reason_prefix = "unsupported_marker" if actor == "OTHER" else "subject_marker"
        return actor, f"{reason_prefix}:{marker}"
    return "AI_SEARCH", "subject_marker:ai_search"


def subject_context(subject: str) -> tuple[str, str]:
    """Return company/position without metadata tags or candidate verdict suffixes."""

    subject_parts = _subject_parts(subject)
    if subject_parts is None:
        return _missing_context()
    prefix, remainder = subject_parts
    if "aisearch" not in prefix:
        return _missing_context()
    remainder = _strip_actor_and_metadata(remainder)

    bracket_pair = re.search(r"\[([^\]]+)\]\s*\[([^\]]+)\]", remainder)
    if bracket_pair is not None:
        return bracket_pair.group(1).strip(), bracket_pair.group(2).strip()

    core = re.split(r"\s+(?:—|–|\|)\s+", remainder, maxsplit=1)[0].strip(" -·")
    round_report = re.fullmatch(r"(.+?)\s+(?:\d+차\s+서치|\d+개\s+포지션.*)", core)
    if round_report:
        return round_report[1].strip(), "NOT_RUN:position_not_parsed"
    company, separator, position = core.partition(" ")
    if re.search(r"[·/]", company):
        return _missing_context()
    if not separator or not company.strip() or not position.strip():
        return _missing_context()
    return company.strip(), position.strip()


def non_run_reason(subject: str) -> str | None:
    """Classify explicit test/dry-run mail before it can become a Batch."""

    return "subject_test_marker" if _NON_RUN_SUBJECT.search(subject) is not None else None


def _strip_metadata_tags(value: str) -> str:
    remainder = value
    while True:
        match = re.match(r"^\[([^\]]+)\]\s*", remainder)
        if match is None:
            return remainder
        following = remainder[match.end() :].strip()
        is_known_metadata = _METADATA_TAG.search(match.group(1)) is not None
        is_single_leading_tag = re.match(r"^\[[^\]]+\]", following) is None
        if not is_known_metadata and not is_single_leading_tag:
            return remainder
        remainder = following


def _strip_actor_and_metadata(value: str) -> str:
    remainder = value.strip()
    while True:
        normalized = _strip_metadata_tags(remainder)
        normalized = _ACTOR_TOKEN.sub("", normalized).strip()
        if normalized == remainder:
            return remainder
        remainder = normalized


def _subject_parts(subject: str) -> tuple[str, str] | None:
    normalized = _REPLY_PREFIX.sub("", subject)
    while (metadata := re.match(r"^\s*\[([^\]]+)\]\s*", normalized)) is not None:
        if metadata[1].strip().casefold() not in {"검토용", "검토", "리뷰", "review", "참고", "보고"}:
            break
        normalized = normalized[metadata.end():]
    prefix_match = re.match(r"^\s*\[([^\]]+)\]\s*", normalized)
    if prefix_match is None:
        return None
    prefix = re.sub(r"[\s_-]+", "", prefix_match.group(1).lower())
    return prefix, normalized[prefix_match.end() :]


def _missing_context() -> tuple[str, str]:
    return "NOT_RUN:company_not_parsed", "NOT_RUN:position_not_parsed"
