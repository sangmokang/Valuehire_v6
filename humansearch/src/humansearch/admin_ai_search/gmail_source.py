"""Fail-closed adapter from a read-only Gmail snapshot to AI Search evidence."""

from __future__ import annotations

import base64
import hashlib
import html
import re
from collections.abc import Mapping, Sequence
from datetime import UTC, date, datetime
from html.parser import HTMLParser
from typing import ClassVar, cast
from urllib.parse import parse_qs, parse_qsl, unquote, urlencode, urlsplit, urlunsplit

from .evidence import (
    ActorEvidencePayload,
    AiSearchPayload,
    AiSearchRun,
    CandidateEvidence,
    EvidenceContract,
    VerificationCheck,
    build_ai_search_payload,
)

GMAIL_SNAPSHOT_VERSION = "admin-ai-search-gmail-snapshot/v1"
_SNAPSHOT_FIELDS = {
    "version",
    "query",
    "page_count",
    "pagination_exhausted",
    "pages",
    "message_ids",
    "messages",
}
_PAGE_FIELDS = {"request_page_token", "message_ids", "next_page_token"}
_URL_PATTERN = re.compile(r"https?://[^\s<>\"']+", re.IGNORECASE)
_CANDIDATE_HEADING = re.compile(
    r"(?im)^\s*(?:(?:\[\[VH_HEADING\]\]|[#>*•-]+)\s*)?(?:"
    r"(?:후보|후보자|candidate)\s*(?:#|no\.?|번호)?\s*\d+|"
    r"\d+\s*(?:번|번째)?\s*(?:후보|후보자|candidate))\b|"
    r"^\s*(?:\[\[VH_HEADING\]\]|#{1,6})\s*\d+[.)]?\s+\S+"
)
_EXCLUDED_HEADING = re.compile(
    r"(?im)^\s*(?:(?:\[\[VH_HEADING\]\]|[#>*•-]+)\s*)?"
    r"(?:제외(?:된)?\s*후보|excluded\s+candidate)\b"
)
_EXPLICIT_NO_CANDIDATES = re.compile(
    r"후보\s*(?:결과\s*)?(?:없음|없습니다)|"
    r"적합한\s*후보.{0,20}(?:없음|찾지|발견하지)|"
    r"no\s+(?:suitable\s+)?candidates?",
    re.IGNORECASE,
)
_PERIOD_PATTERN = re.compile(
    r"검색\s*기간\s*[:：]\s*(\d{4}-\d{2}-\d{2})\s*(?:~|–|—|to)\s*(\d{4}-\d{2}-\d{2})",
    re.IGNORECASE,
)


class _HtmlTextExtractor(HTMLParser):
    """Extract readable lines and anchor evidence without executing HTML."""

    _BLOCK_TAGS: ClassVar[set[str]] = {
        "br",
        "div",
        "h1",
        "h2",
        "h3",
        "h4",
        "li",
        "p",
        "section",
        "table",
        "td",
        "th",
        "tr",
    }
    _HEADING_TAGS: ClassVar[set[str]] = {"h1", "h2", "h3", "h4"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.fragments: list[str] = []
        self.links: list[tuple[str, str]] = []
        self._anchor_href: str | None = None
        self._anchor_text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in self._BLOCK_TAGS:
            self.fragments.append("\n")
        if tag in self._HEADING_TAGS:
            self.fragments.append("[[VH_HEADING]] ")
        if tag == "a":
            href = next((value for name, value in attrs if name == "href"), None)
            self._anchor_href = href
            self._anchor_text = []

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._anchor_href:
            label = " ".join("".join(self._anchor_text).split())
            self.links.append((html.unescape(self._anchor_href), label))
            self.fragments.append(f" {self._anchor_href} ")
            self._anchor_href = None
            self._anchor_text = []
        if tag in self._BLOCK_TAGS:
            self.fragments.append("\n")

    def handle_data(self, data: str) -> None:
        self.fragments.append(data)
        if self._anchor_href is not None:
            self._anchor_text.append(data)

    def result(self) -> str:
        lines = (" ".join(line.split()) for line in "".join(self.fragments).splitlines())
        return "\n".join(line for line in lines if line)


def build_ai_search_payload_from_gmail_snapshot(
    snapshot: Mapping[str, object], contract: EvidenceContract
) -> AiSearchPayload:
    """Validate an exhaustive Gmail snapshot and project one Batch per message."""

    messages, query, page_count, pagination_exhausted = _validate_snapshot(snapshot)
    runs = tuple(_message_to_run(message, contract) for message in messages)
    payload = build_ai_search_payload(runs, contract)
    collection_status = "PASS" if pagination_exhausted else "NOT_RUN"
    collection_reason = None if pagination_exhausted else "gmail_pagination_incomplete"
    payload["gmail_collection"] = {
        "query": query,
        "page_count": page_count,
        "message_count": len(messages),
        "pagination_exhausted": pagination_exhausted,
        "status": collection_status,
        "reason": collection_reason,
    }
    payload["external_effects"] = {**payload["external_effects"], "gmail": "READ_ONLY"}
    if not pagination_exhausted:
        payload["status"] = "NOT_RUN"
        payload["reason"] = "gmail_pagination_incomplete"
    elif not messages:
        payload["status"] = "NOT_RUN"
        payload["reason"] = "no_ai_search_messages"
    return payload


def _validate_snapshot(
    snapshot: Mapping[str, object],
) -> tuple[list[Mapping[str, object]], str, int, bool]:
    if set(snapshot) != _SNAPSHOT_FIELDS:
        raise ValueError("Gmail snapshot fields do not match the v1 contract")
    if snapshot["version"] != GMAIL_SNAPSHOT_VERSION:
        raise ValueError("unsupported Gmail snapshot version")
    query = snapshot["query"]
    page_count = snapshot["page_count"]
    pagination_exhausted = snapshot["pagination_exhausted"]
    raw_ids = snapshot["message_ids"]
    raw_messages = snapshot["messages"]
    raw_pages = snapshot["pages"]
    if not isinstance(query, str) or not query.strip():
        raise ValueError("Gmail query must be non-blank")
    if isinstance(page_count, bool) or not isinstance(page_count, int) or page_count < 1:
        raise ValueError("Gmail page_count must be a positive integer")
    if not isinstance(pagination_exhausted, bool):
        raise TypeError("Gmail pagination_exhausted must be boolean")
    if not isinstance(raw_ids, list) or not all(isinstance(item, str) and item for item in raw_ids):
        raise ValueError("Gmail message_ids must be non-blank strings")
    if len(raw_ids) != len(set(raw_ids)):
        raise ValueError("Gmail message_ids must be unique")
    _validate_pages(raw_pages, raw_ids, page_count, pagination_exhausted)
    if not isinstance(raw_messages, list) or not all(
        isinstance(item, Mapping) for item in raw_messages
    ):
        raise ValueError("Gmail messages must be objects")
    messages = cast(list[Mapping[str, object]], raw_messages)
    response_ids = [_required_string(message, "id") for message in messages]
    if raw_ids != response_ids:
        raise ValueError("Gmail message_ids do not match message responses")
    return messages, query, page_count, pagination_exhausted


def _validate_pages(
    raw_pages: object,
    raw_ids: list[object],
    page_count: int,
    pagination_exhausted: bool,
) -> None:
    if not isinstance(raw_pages, list) or not all(isinstance(page, Mapping) for page in raw_pages):
        raise TypeError("Gmail pages must be objects")
    pages = cast(list[Mapping[str, object]], raw_pages)
    if len(pages) != page_count:
        raise ValueError("Gmail pagination page_count does not match pages")
    expected_request_token: str | None = None
    seen_request_tokens: set[str] = set()
    collected_ids: list[str] = []
    for page_index, page in enumerate(pages):
        if set(page) != _PAGE_FIELDS:
            raise ValueError("Gmail pagination page fields do not match the v1 contract")
        request_token = page["request_page_token"]
        next_token = page["next_page_token"]
        page_ids = page["message_ids"]
        if request_token is not None and (not isinstance(request_token, str) or not request_token):
            raise ValueError("Gmail pagination request token is invalid")
        if next_token is not None and (not isinstance(next_token, str) or not next_token):
            raise ValueError("Gmail pagination next token is invalid")
        if request_token != expected_request_token:
            raise ValueError("Gmail pagination token chain is broken")
        if page_index > 0 and request_token is None:
            raise ValueError("Gmail pagination continued after a terminal page")
        if page_index + 1 < len(pages) and next_token is None:
            raise ValueError("Gmail pagination terminated before the final page")
        if request_token is not None:
            if request_token in seen_request_tokens:
                raise ValueError("Gmail pagination token cycle detected")
            seen_request_tokens.add(request_token)
        if next_token is not None and next_token in seen_request_tokens:
            raise ValueError("Gmail pagination token cycle detected")
        if not isinstance(page_ids, list) or not all(
            isinstance(item, str) and item for item in page_ids
        ):
            raise ValueError("Gmail pagination message_ids are invalid")
        collected_ids.extend(cast(list[str], page_ids))
        expected_request_token = next_token
    if collected_ids != raw_ids:
        raise ValueError("Gmail pagination message_ids do not match snapshot message_ids")
    if pagination_exhausted != (expected_request_token is None):
        raise ValueError("Gmail pagination completion evidence is inconsistent")


def _message_to_run(message: Mapping[str, object], contract: EvidenceContract) -> AiSearchRun:
    message_id = _required_string(message, "id")
    thread_id = _required_string(message, "thread_id")
    received_at = _received_at(message.get("internal_date"))
    payload = _required_mapping(message, "payload")
    subject = _header(payload, "subject")
    sender = _header(payload, "from")
    actor, actor_reason = _classify_actor(subject, sender)
    company, position = _subject_context(subject)
    body_text, links = _message_body(payload)
    candidates, unparsed, excluded, counts_complete = _candidate_records(body_text, links)
    period_start, period_end, period_reason = _search_period(body_text)
    actor_evidence: ActorEvidencePayload = {
        "subject": subject,
        "sender": sender,
        "thread_id": thread_id,
        "message_id": message_id,
        "received_at": received_at.isoformat(),
        "reason": actor_reason,
    }
    checks = tuple(
        VerificationCheck(
            source=source,
            status="NOT_RUN",
            checked_at=None,
            reason="fu_portal_verification_out_of_scope",
        )
        for source in contract.required_verification_sources
    )
    return AiSearchRun(
        actor=actor,
        source_run_id=message_id,
        company=company,
        position=position,
        channels=_channels(body_text, candidates),
        executed_at=received_at,
        candidates=candidates,
        verification_checks=checks,
        actor_evidence=actor_evidence,
        search_period_start=period_start,
        search_period_end=period_end,
        search_period_reason=period_reason,
        unparsed_candidates=unparsed,
        excluded_candidates=excluded,
        candidate_counts_complete=counts_complete,
        candidate_counts_reason=(None if counts_complete else "candidate_records_not_identifiable"),
    )


def _required_string(value: Mapping[str, object], field: str) -> str:
    result = value.get(field)
    if not isinstance(result, str) or not result.strip():
        raise ValueError(f"Gmail message {field} must be non-blank")
    return result


def _required_mapping(value: Mapping[str, object], field: str) -> Mapping[str, object]:
    result = value.get(field)
    if not isinstance(result, Mapping):
        raise TypeError(f"Gmail message {field} must be an object")
    return cast(Mapping[str, object], result)


def _received_at(value: object) -> datetime:
    if not isinstance(value, str) or not value.isdigit():
        raise ValueError("Gmail internal_date must be millisecond text")
    return datetime.fromtimestamp(int(value) / 1000, tz=UTC)


def _header(payload: Mapping[str, object], wanted: str) -> str:
    headers = payload.get("headers")
    if not isinstance(headers, list):
        raise TypeError("Gmail payload headers must be a list")
    for item in headers:
        if not isinstance(item, Mapping):
            continue
        name = item.get("name")
        value = item.get("value")
        if (
            isinstance(name, str)
            and name.lower() == wanted
            and isinstance(value, str)
            and value.strip()
        ):
            return value
    raise ValueError(f"Gmail {wanted} header is missing")


def _classify_actor(subject: str, sender: str) -> tuple[str, str]:
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
    if "grok" in actor_region:
        markers.append(("GROK", "grok"))
    if "claudecode" in actor_region:
        markers.append(("CLAUDE_CODE", "claude_code"))
    if "chatgpt" in actor_region:
        markers.append(("CHATGPT", "chatgpt"))
    if "codex" in actor_region:
        markers.append(("OTHER", "codex"))
    if "gemini" in actor_region:
        markers.append(("OTHER", "gemini"))
    unique = {actor for actor, _ in markers}
    if len(markers) > 1 or len(unique) > 1:
        return "OTHER", "actor_markers_conflict"
    if markers:
        actor, marker = markers[0]
        prefix = "unsupported_marker" if actor == "OTHER" else "subject_marker"
        return actor, f"{prefix}:{marker}"
    return "AI_SEARCH", "subject_marker:ai_search"


def _subject_context(subject: str) -> tuple[str, str]:
    subject_parts = _subject_parts(subject)
    if subject_parts is None:
        return "NOT_RUN:company_not_parsed", "NOT_RUN:position_not_parsed"
    _, remainder = subject_parts
    first_context = remainder.find("[")
    if first_context >= 0:
        remainder = remainder[first_context:]
    bracketed = [item.strip() for item in re.findall(r"\[([^\]]+)\]", remainder) if item.strip()]
    if len(bracketed) >= 2:
        return bracketed[0], bracketed[1]
    if len(bracketed) == 1:
        tail = re.sub(r"^\s*\[[^\]]+\]\s*", "", remainder).strip(" —-·")
        return bracketed[0], tail or "NOT_RUN:position_not_parsed"
    return "NOT_RUN:company_not_parsed", "NOT_RUN:position_not_parsed"


def _subject_parts(subject: str) -> tuple[str, str] | None:
    prefix_match = re.match(r"^\s*\[([^\]]+)\]\s*", subject)
    if prefix_match is None:
        return None
    prefix = re.sub(r"[\s_-]+", "", prefix_match.group(1).lower())
    return prefix, subject[prefix_match.end() :]


def _message_body(payload: Mapping[str, object]) -> tuple[str, list[tuple[str, str]]]:
    parts = list(_walk_parts(payload))
    plain = [content for mime, content in parts if mime == "text/plain" and content.strip()]
    html_parts = [content for mime, content in parts if mime == "text/html" and content.strip()]
    if html_parts:
        parser = _HtmlTextExtractor()
        parser.feed("\n".join(html_parts))
        parser.close()
        return parser.result(), parser.links
    if plain:
        text = "\n".join(plain)
        links = [(match.group(0), match.group(0)) for match in _URL_PATTERN.finditer(text)]
        return text, links
    raise ValueError("Gmail message has no readable text body")


def _walk_parts(part: Mapping[str, object]) -> Sequence[tuple[str, str]]:
    result: list[tuple[str, str]] = []
    mime = part.get("mime_type")
    body = part.get("body")
    if isinstance(mime, str) and mime in {"text/plain", "text/html"} and isinstance(body, Mapping):
        content = body.get("content")
        if isinstance(content, str) and content:
            result.append((mime, content))
        else:
            encoded = body.get("base64_url_content")
            if isinstance(encoded, str) and encoded:
                padding = "=" * (-len(encoded) % 4)
                result.append((mime, base64.urlsafe_b64decode(encoded + padding).decode("utf-8")))
    children = part.get("parts")
    if isinstance(children, list):
        for child in children:
            if isinstance(child, Mapping):
                result.extend(_walk_parts(cast(Mapping[str, object], child)))
    return result


def _candidate_records(
    body_text: str, links: Sequence[tuple[str, str]]
) -> tuple[tuple[CandidateEvidence, ...], int, int, bool]:
    lines = [line.strip() for line in body_text.splitlines() if line.strip()]
    boundaries: list[tuple[int, bool]] = []
    for index, line in enumerate(lines):
        if _EXCLUDED_HEADING.match(line):
            boundaries.append((index, True))
        elif _CANDIDATE_HEADING.match(line):
            boundaries.append((index, False))
    if boundaries:
        candidates: list[CandidateEvidence] = []
        unparsed = 0
        excluded = 0
        for boundary_index, (start, is_excluded) in enumerate(boundaries):
            end = (
                boundaries[boundary_index + 1][0]
                if boundary_index + 1 < len(boundaries)
                else len(lines)
            )
            context = lines[start:end]
            if is_excluded:
                excluded += 1
                continue
            occurrences = _candidate_occurrences("\n".join(context), links)
            identities = list(dict.fromkeys(url for url, _, _ in occurrences))
            if len(identities) != 1:
                unparsed += 1
                continue
            url = identities[0]
            label = next(label for item_url, label, _ in occurrences if item_url == url)
            candidates.append(_candidate_from_context(url, label, context))
        return tuple(candidates), unparsed, excluded, True

    occurrences = _candidate_occurrences(body_text, links)
    if occurrences:
        candidates = []
        for url, label, line_index in occurrences:
            context = lines[line_index : line_index + 1]
            candidates.append(_candidate_from_context(url, label, context))
        return tuple(candidates), 0, 0, True
    if _EXPLICIT_NO_CANDIDATES.search(body_text):
        return (), 0, 0, True
    return (), 0, 0, False


def _candidate_occurrences(
    text: str, links: Sequence[tuple[str, str]]
) -> list[tuple[str, str, int]]:
    labels: dict[str, list[str]] = {}
    for raw_url, label in links:
        normalized = _candidate_url(raw_url)
        if normalized is not None:
            labels.setdefault(normalized, []).append(label)
    label_offsets: dict[str, int] = {}
    occurrences: list[tuple[str, str, int]] = []
    for line_index, line in enumerate(line.strip() for line in text.splitlines() if line.strip()):
        for match in _URL_PATTERN.finditer(line):
            normalized = _candidate_url(match.group(0))
            if normalized is None:
                continue
            offset = label_offsets.get(normalized, 0)
            choices = labels.get(normalized, ())
            label = choices[offset] if offset < len(choices) else normalized
            label_offsets[normalized] = offset + 1
            occurrences.append((normalized, label, line_index))
    return occurrences


def _candidate_from_context(url: str, label: str, context: Sequence[str]) -> CandidateEvidence:
    requirements = _label_values(context, (r"필수\s*요건(?:별)?\s*근거", r"필수\s*요건"))
    contact_opinion = _first_label_value(
        context,
        (r"컨택\s*의견(?:\s*근거)?", r"추천\s*근거"),
    )
    better_exists, better_position, better_reason = _better_position(context)
    return CandidateEvidence(
        canonical_key=hashlib.sha256(url.encode("utf-8")).hexdigest(),
        display_name=_candidate_label(label, url),
        source_channel=_channel_for_url(url),
        profile_url=url,
        education=_first_label_value(context, (r"학력", r"education")),
        experience=_first_label_value(
            context,
            (r"총\s*경력", r"전체\s*경력", r"career\s*summary"),
        ),
        key_experience=_first_label_value(
            context,
            (r"핵심\s*경력", r"주요\s*경력", r"핵심\s*업무"),
        ),
        score=None,
        score_reason="v5_score_contract_evidence_missing",
        why_fit=tuple(_label_values(context, (r"적합\s*근거", r"추천\s*이유", r"why\s*fit"))),
        requirements_evidence=tuple(requirements),
        reverse_match_position=None,
        reverse_match_score=None,
        reverse_match_reason="NOT_RUN:reverse_match_contract_evidence_missing",
        contact_recommendation="NOT_RUN",
        contact_opinion_evidence=contact_opinion,
        better_position_exists=better_exists,
        better_position=better_position,
        better_position_reason=better_reason,
    )


def _candidate_url(raw_url: str) -> str | None:
    cleaned = html.unescape(raw_url).rstrip(".,);]}")
    parsed = urlsplit(cleaned)
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname:
        return None
    if parsed.username or parsed.password or parsed.port:
        return None
    host = parsed.hostname.lower().removeprefix("www.")
    if host in {"google.com", "google.co.kr"} and parsed.path == "/url":
        target = parse_qs(parsed.query).get("q", [None])[0]
        if target is None:
            return None
        return _candidate_url(unquote(target))
    path = re.sub(r"/{2,}", "/", parsed.path).rstrip("/")
    if _host_is(host, "linkedin.com") and (path.startswith("/in/") or "/talent/profile/" in path):
        return urlunsplit((parsed.scheme.lower(), host, path, "", ""))
    if _host_is(host, "saramin.co.kr") and "/applicant-view/position/resume" in path:
        return urlunsplit((parsed.scheme.lower(), host, path, _identity_query(parsed.query), ""))
    if _host_is(host, "jobkorea.co.kr") and "/resume/" in path.lower():
        return urlunsplit((parsed.scheme.lower(), host, path, _identity_query(parsed.query), ""))
    return None


def _identity_query(query: str) -> str:
    return urlencode(sorted(parse_qsl(query, keep_blank_values=True)), doseq=True)


def _host_is(host: str, domain: str) -> bool:
    return host == domain or host.endswith(f".{domain}")


def _candidate_label(label: str, url: str) -> str:
    normalized = " ".join(label.split())
    generic = {"", "링크", "프로필", "바로가기", "duplicate link"}
    return url if normalized.lower() in generic else normalized


def _label_values(lines: Sequence[str], labels: Sequence[str]) -> list[str]:
    values: list[str] = []
    for line in lines:
        for label in labels:
            match = re.match(rf"^\s*(?:{label})\s*[:：]\s*(.+?)\s*$", line, re.IGNORECASE)
            if match and match.group(1).strip():
                values.append(match.group(1).strip())
                break
    return list(dict.fromkeys(values))


def _first_label_value(lines: Sequence[str], labels: Sequence[str]) -> str | None:
    values = _label_values(lines, labels)
    return values[0] if values else None


def _better_position(lines: Sequence[str]) -> tuple[bool | None, str | None, str | None]:
    value = _first_label_value(
        lines,
        (r"더\s*적합한\s*포지션", r"더\s*적합한\s*직무", r"better\s*position"),
    )
    if value is None:
        return None, None, "better_position_evidence_missing"
    if value.lower() in {"없음", "no", "none", "해당 없음"}:
        return False, None, value
    return True, value, value


def _search_period(body_text: str) -> tuple[str | None, str | None, str | None]:
    match = _PERIOD_PATTERN.search(body_text)
    if match is None:
        return None, None, "search_period_not_found"
    start, end = match.groups()
    try:
        start_date = date.fromisoformat(start)
        end_date = date.fromisoformat(end)
    except ValueError:
        return None, None, "search_period_invalid"
    if start_date > end_date:
        return None, None, "search_period_reversed"
    return start, end, None


def _channel_for_url(url: str) -> str:
    host = urlsplit(url).netloc
    if _host_is(host, "linkedin.com"):
        return "LINKEDIN"
    if _host_is(host, "saramin.co.kr"):
        return "SARAMIN"
    if _host_is(host, "jobkorea.co.kr"):
        return "JOBKOREA"
    return "OTHER"


def _channels(body_text: str, candidates: Sequence[CandidateEvidence]) -> tuple[str, ...]:
    found = {candidate.source_channel for candidate in candidates}
    lowered = body_text.lower()
    for marker, channel in (
        ("linkedin", "LINKEDIN"),
        ("링크드인", "LINKEDIN"),
        ("saramin", "SARAMIN"),
        ("사람인", "SARAMIN"),
        ("jobkorea", "JOBKOREA"),
        ("잡코리아", "JOBKOREA"),
    ):
        if marker in lowered:
            found.add(channel)
    return tuple(sorted(found)) or ("OTHER",)
