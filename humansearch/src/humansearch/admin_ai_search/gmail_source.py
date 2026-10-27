"""Fail-closed adapter from a read-only Gmail snapshot to AI Search evidence."""

from __future__ import annotations

import base64
import html
import re
from collections.abc import Mapping, Sequence
from dataclasses import replace
from datetime import UTC, date, datetime
from html.parser import HTMLParser
from typing import ClassVar, cast

from .evidence import (
    ActorEvidencePayload,
    AiSearchPayload,
    AiSearchRun,
    EvidenceContract,
    VerificationCheck,
    build_ai_search_payload,
)
from .gmail_batching import group_gmail_runs, grouping_evidence
from .gmail_candidates import candidate_records, channels
from .gmail_subject import classify_actor, non_run_reason, subject_context

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
    included_messages: list[Mapping[str, object]] = []
    excluded_messages: list[dict[str, str]] = []
    for message in messages:
        message_id = _required_string(message, "id")
        message_payload = _required_mapping(message, "payload")
        reason = non_run_reason(_header(message_payload, "subject"))
        if reason is None:
            included_messages.append(message)
        else:
            excluded_messages.append({"message_id": message_id, "reason": reason})
    runs = group_gmail_runs(
        tuple(_message_to_run(message, contract) for message in included_messages)
    )
    payload = build_ai_search_payload(runs, contract)
    collection_status = "PASS" if pagination_exhausted else "NOT_RUN"
    collection_reason = None if pagination_exhausted else "gmail_pagination_incomplete"
    payload["gmail_collection"] = {
        "query": query,
        "page_count": page_count,
        "message_count": len(messages),
        "included_message_count": len(included_messages),
        "excluded_message_count": len(excluded_messages),
        "excluded_messages": excluded_messages,
        "pagination_exhausted": pagination_exhausted,
        "status": collection_status,
        "reason": collection_reason,
    }
    payload["external_effects"] = {**payload["external_effects"], "gmail": "READ_ONLY"}
    if not pagination_exhausted:
        payload["status"] = "NOT_RUN"
        payload["reason"] = "gmail_pagination_incomplete"
    elif not included_messages:
        payload["status"] = "NOT_RUN"
        payload["reason"] = (
            "no_ai_search_messages" if not messages else "no_executable_ai_search_messages"
        )
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
    actor, actor_reason = classify_actor(subject, sender)
    company, position = subject_context(subject)
    body_text, links = _message_body(payload)
    candidates, unparsed, excluded, counts_complete = candidate_records(body_text, links, contract)
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
    run = AiSearchRun(
        actor=actor,
        source_run_id=message_id,
        company=company,
        position=position,
        channels=channels(body_text, candidates),
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
        source_message_ids=(message_id,),
    )
    group_key, grouping_reason = grouping_evidence(run, subject, body_text)
    return replace(
        run,
        batch_group_key=group_key,
        batch_grouping_reason=grouping_reason,
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
