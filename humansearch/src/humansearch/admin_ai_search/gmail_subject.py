"""Deterministic parsing for AI Search Gmail subject evidence."""

from __future__ import annotations

import re

_METADATA_TAG = re.compile(
    r"(?:ai\s*search|aisearch|태그|신규\s*포지션\s*서치|후보\s*알림)",
    re.IGNORECASE,
)
_ACTOR_TOKEN = re.compile(
    r"^(?:grok(?:bot|\d+(?:\.\d+)?)?|claude\s*code|claudecode|chatgpt|codex|gemini)\s+",
    re.IGNORECASE,
)
_NON_RUN_SUBJECT = re.compile(
    r"(?:\[(?:test|테스트(?:\s*메일)?|dry[- ]?run|smoke(?:\s*test)?|fixture)\]|"
    r"\b테스트\s*메일\b|\bdry[- ]?run\b|\bsmoke\s*test\b)",
    re.IGNORECASE,
)
_REPLY_PREFIX = re.compile(r"^\s*(?:(?:re|fw|fwd)\s*:\s*)+", re.IGNORECASE)


def classify_actor(subject: str, sender: str) -> tuple[str, str]:
    """Classify only explicit subject markers and preserve fail-closed OTHER."""

    del sender
    subject_parts = _subject_parts(subject)
    if subject_parts is None:
        return "OTHER", "ai_search_prefix_not_found"
    prefix, remainder = subject_parts
    if "aisearch" not in prefix:
        return "OTHER", "ai_search_prefix_not_found"
    actor_region = prefix.replace("aisearch", "", 1)
    if prefix == "aisearch":
        without_metadata = _strip_metadata_tags(remainder.strip())
        actor_region = re.sub(r"[\s_-]+", "", without_metadata.split("[", 1)[0].lower())
    markers: list[tuple[str, str]] = []
    for marker, actor, reason in (
        ("grok", "GROK", "grok"),
        ("claudecode", "CLAUDE_CODE", "claude_code"),
        ("chatgpt", "CHATGPT", "chatgpt"),
        ("codex", "OTHER", "codex"),
        ("gemini", "OTHER", "gemini"),
    ):
        if marker in actor_region:
            markers.append((actor, reason))
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
    _, remainder = subject_parts
    remainder = _strip_actor_and_metadata(remainder)

    bracket_pair = re.search(r"\[([^\]]+)\]\s*\[([^\]]+)\]", remainder)
    if bracket_pair is not None:
        return bracket_pair.group(1).strip(), bracket_pair.group(2).strip()

    core = re.split(r"\s+(?:—|–|\|)\s+", remainder, maxsplit=1)[0].strip(" -·")
    company, separator, position = core.partition(" ")
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
    prefix_match = re.match(r"^\s*\[([^\]]+)\]\s*", normalized)
    if prefix_match is None:
        return None
    prefix = re.sub(r"[\s_-]+", "", prefix_match.group(1).lower())
    return prefix, normalized[prefix_match.end() :]


def _missing_context() -> tuple[str, str]:
    return "NOT_RUN:company_not_parsed", "NOT_RUN:position_not_parsed"
