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
        actor_region = re.sub(r"[\s_-]+", "", remainder.split("[", 1)[0].lower())
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
    remainder = _strip_metadata_tags(remainder.strip())
    remainder = _ACTOR_TOKEN.sub("", remainder).strip()

    bracket_pair = re.search(r"\[([^\]]+)\]\s*\[([^\]]+)\]", remainder)
    if bracket_pair is not None:
        return bracket_pair.group(1).strip(), bracket_pair.group(2).strip()

    core = re.split(r"\s+(?:—|–|\|)\s+", remainder, maxsplit=1)[0].strip(" -·")
    company, separator, position = core.partition(" ")
    if not separator or not company.strip() or not position.strip():
        return _missing_context()
    return company.strip(), position.strip()


def _strip_metadata_tags(value: str) -> str:
    remainder = value
    while True:
        match = re.match(r"^\[([^\]]+)\]\s*", remainder)
        if match is None or _METADATA_TAG.search(match.group(1)) is None:
            return remainder
        remainder = remainder[match.end() :].strip()


def _subject_parts(subject: str) -> tuple[str, str] | None:
    prefix_match = re.match(r"^\s*\[([^\]]+)\]\s*", subject)
    if prefix_match is None:
        return None
    prefix = re.sub(r"[\s_-]+", "", prefix_match.group(1).lower())
    return prefix, subject[prefix_match.end() :]


def _missing_context() -> tuple[str, str]:
    return "NOT_RUN:company_not_parsed", "NOT_RUN:position_not_parsed"
