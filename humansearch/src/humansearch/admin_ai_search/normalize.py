"""Project real MIME evidence into separate candidate/position/evaluation records."""

from __future__ import annotations

import base64
import hashlib
import json
import re
from dataclasses import asdict
from datetime import UTC, datetime
from typing import Any
from zoneinfo import ZoneInfo

from .evidence import CandidateEvidence, EvidenceContract, stable_batch_id
from .gmail_candidates import (
    _CANDIDATE_HEADING,
    _NAMED_CANDIDATE_HEADING,
    _REPORT_CANDIDATE_HEADING,
    _SUMMARY_CANDIDATE_HEADING,
    candidate_records,
    canonical_candidate_url,
)
from .gmail_sent_contacts import _contact_actor
from .gmail_source import _HtmlTextExtractor, _message_body
from .gmail_subject import classify_actor, non_run_reason, subject_context
from .registry import Registry, operation_week
from .scoring import source_reported_number
from .weekly_view import _verified_candidate_name

PARSER_VERSION = "admin-ai-search-normalizer/2026-10-31.2"
RUN_ID = re.compile(r"(?:run\s*id|실행\s*ID)\s*[:：#]\s*([\w.:-]{3,128})", re.IGNORECASE)
SECTION = re.compile(r"^(?:(?:#+|\[\[VH_HEADING\]\])\s*)?고객사\s*[:：]\s*(.+?)\s*[/|·]\s*포지션\s*[:：]\s*(.+)$", re.MULTILINE)
RELATED = re.compile(r"ai\s*[-_]?\s*search|ai\s*서치|후보.{0,12}(?:서치|검색)|grok.{0,15}컨택", re.IGNORECASE)
PROFILE = re.compile(r"https?://[^\s<>\"']+", re.IGNORECASE)
REPORTED = re.compile(r"^\s*(?:[-*]\s*)?(?:메일\s*(?:원본\s*)?점수|총점|종합\s*점수|점수|score)\s*[:：]\s*(\d+(?:\.\d+)?)(?![\d.,])(?:\s*/\s*\d+(?:\.\d+)?)?", re.IGNORECASE | re.MULTILINE)
EXECUTED = re.compile(r"(?:실행\s*(?:시각|일시)|executed_at)\s*[:：]\s*(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}(?::\d{2})?(?:Z|[+-]\d{2}:\d{2})?)", re.IGNORECASE)


def key(*parts: str) -> str:
    return hashlib.sha256(json.dumps(parts, ensure_ascii=False).encode()).hexdigest()


def adapt_mime(raw: dict[str, Any]) -> dict[str, Any]:
    body = raw.get("body", {})
    result = {"mime_type": raw.get("mimeType", ""), "headers": raw.get("headers", []),
              "body": {"base64_url_content": body.get("data", "")}}
    result["parts"] = [adapt_mime(part) for part in raw.get("parts", [])]
    return result


def headers(message: dict[str, Any]) -> dict[str, str]:
    return {h["name"].lower(): h["value"] for h in message.get("payload", {}).get("headers", [])}


def review(registry: Registry, message_id: str, reason: str, **details: Any) -> None:
    identity = key(message_id, reason, str(details.get("reference", "")))
    registry.put("review_queue", {"id": identity, "source_message_id": message_id,
                                   "reason": reason, "status": "OPEN", **details})


def normalize_message(
    registry: Registry, message: dict[str, Any], contract: EvidenceContract,
) -> dict[str, Any]:
    message_id = message["id"]
    meta = headers(message)
    subject = meta.get("subject", "")
    received = datetime.fromtimestamp(int(message["internalDate"]) / 1000, UTC)
    source = {"id": message_id, "thread_id": message.get("threadId"),
              "sender": meta.get("from"), "recipients": meta.get("to"), "subject": subject,
              "received_at": received.isoformat(), "label_ids": message.get("labelIds", []),
              "gmail_url": f"https://mail.google.com/mail/u/0/#all/{message_id}",
              "checksum": key(json.dumps(message, sort_keys=True)), "parser_version": PARSER_VERSION}
    try:
        text, links = _message_body(adapt_mime(message.get("payload", {})))
    except (ValueError, UnicodeError) as error:
        text, links = "", []
        review(registry, message_id, "body_unreadable", error_type=type(error).__name__)
    attachments = _attachments(registry, message_id, message.get("payload", {}))
    source.update(body_status="PARSED" if text else "REVIEW_REQUIRED",
                  attachment_status=("REVIEW_REQUIRED" if any(a["status"] != "PARSED" for a in attachments)
                                     else "PARSED" if attachments else "NONE"))
    # An attachment extraction job can append verified text, without changing MIME.
    for attachment in attachments:
        if attachment.get("original_html"):
            parser = _HtmlTextExtractor()
            parser.feed(attachment["original_html"])
            parser.close()
            text += "\n" + parser.result()
            links.extend(parser.links)
        elif attachment.get("extracted_text"):
            text += "\n" + attachment["extracted_text"]
    source["body_text"] = text
    if non_run_reason(subject):
        source.update(processing_status="EXCLUDED", reason=non_run_reason(subject))
        return source
    actor, actor_reason = classify_actor(subject, meta.get("from", ""), text)
    source.update(executor=actor, executor_reason=actor_reason)
    if not RELATED.search(subject + "\n" + text) and not message.get("_in_ai_search_label"):
        if any(canonical_candidate_url(m.group(0)) for m in PROFILE.finditer(text)) or not text:
            source.update(processing_status="REVIEW_REQUIRED", reason="potential_ai_search_requires_review")
            review(registry, message_id, "potential_ai_search_requires_review")
            return source
        source.update(processing_status="EXCLUDED", reason="not_ai_search_after_full_body_read")
        source.update(body_text=None, raw_body_storage="private_collection_by_message_id")
        for attachment in attachments:
            identity = key(message_id, attachment.get("reason") or "attachment_extraction_pending", attachment["id"])
            old = registry.db.execute("SELECT document FROM review_queue WHERE id=?", (identity,)).fetchone()
            if old:
                registry.put("review_queue", {**json.loads(old[0]), "status": "EXCLUDED",
                    "exclusion_reason": "parent_message_not_ai_search"})
        return source
    strong_marker = re.search(r"\[[^\]]*ai[\s_-]*search[^\]]*\]", subject, re.IGNORECASE) is not None
    explicit_target = SECTION.search(text) is not None
    report_title = RELATED.search(subject) is not None and re.search(
        r"후보자|인재|소싱|candidate|sourcing|후보\s*\d+\s*명", subject, re.IGNORECASE,
    ) is not None
    if not (message.get("_in_ai_search_label") or strong_marker or explicit_target or report_title):
        source.update(processing_status="REVIEW_REQUIRED", source_kind="POTENTIAL_AI_SEARCH_RELATED",
                      reason="ai_search_result_identity_not_proven")
        review(registry, message_id, "ai_search_result_identity_not_proven")
        return source
    source["source_kind"] = "AI_SEARCH_RESULT"
    actor_evidence = {"subject": subject, "sender": meta.get("from"), "message_id": message_id,
                      "thread_id": message.get("threadId"), "received_at": received.isoformat(),
                      "rule": actor_reason}
    sections = list(SECTION.finditer(text))
    contexts = [(m.group(1).strip(), m.group(2).strip(),
                 text[m.end():sections[i + 1].start() if i + 1 < len(sections) else len(text)])
                for i, m in enumerate(sections)]
    if not contexts:
        company, position = subject_context(subject)
        contexts = [(company, position, text)]
    for index, (company, position, segment) in enumerate(contexts):
        _normalize_section(registry, source, contract, segment, links, company, position,
                           index, received, actor, actor_evidence)
    source.update(processing_status="PROCESSED", reason=None)
    return source


def _normalize_section(
    registry: Registry, source: dict[str, Any], contract: EvidenceContract, text: str,
    links: list[tuple[str, str]], company: str, position: str, index: int,
    received: datetime, actor: str, actor_evidence: dict[str, Any],
) -> None:
    message_id = source["id"]
    executed, time_source = received, "received_at_fallback"
    timestamps = set(EXECUTED.findall(text))
    if len(timestamps) == 1:
        try:
            parsed = datetime.fromisoformat(next(iter(timestamps)))
            executed = (parsed if parsed.tzinfo else parsed.replace(tzinfo=ZoneInfo("Asia/Seoul"))).astimezone(UTC)
            time_source = "explicit_source_timestamp"
        except ValueError:
            review(registry, message_id, "invalid_execution_timestamp")
    elif len(timestamps) > 1:
        review(registry, message_id, "conflicting_execution_timestamps")
    position_known = not (company.startswith("NOT_RUN:") or position.startswith("NOT_RUN:"))
    position_id = key(company, position) if position_known else key(message_id, str(index), "unknown")
    registry.put("positions", {"id": position_id, "company": company, "title": position,
                               "status": "PASS" if position_known else "NOT_RUN"})
    run_ids = set(RUN_ID.findall(source["subject"] + "\n" + text))
    confirmed = len(run_ids) == 1
    grouping_key = f"run:{actor}:{next(iter(run_ids))}" if confirmed else None
    grouping_reason = "explicit_run_id" if confirmed else "execution_identity_not_proven"
    if not run_ids and position_known and actor != "OTHER" and time_source == "explicit_source_timestamp" and re.search(
        r"(?:실행|서치|검색)\s*(?:완료|결과)|(?:run|search)\s*(?:completed|finished)", text, re.IGNORECASE,
    ):
        confirmed = True
        grouping_key = key(actor, company, position, executed.isoformat(), "completed-execution")
        grouping_reason = "same_actor_company_position_explicit_execution_timestamp_and_completion"
    preferred_id = key(actor, "explicit-run", grouping_key) if grouping_key is not None else stable_batch_id(
        actor, f"{message_id}:section:{index}", received,
    )
    batch_id = registry.resolve_batch_id(grouping_key, preferred_id, message_id, index)
    week_id, year, week = operation_week(executed)
    batch = registry.register_batch({
        "id": batch_id, "week_year": year, "week_number": week,
        "grouping_status": "CONFIRMED" if confirmed else "PROVISIONAL", "document": {
            "id": batch_id, "week_id": week_id, "actor": actor,
            "grouping_reason": grouping_reason, "grouping_key": grouping_key,
            "source_message_ids": [message_id], "actor_evidence": [actor_evidence],
            "executed_at": executed.isoformat(), "received_at": received.isoformat(),
            "execution_time_source": time_source,
            "execution_time_confidence": "HIGH" if time_source == "explicit_source_timestamp" else "LOW",
            "execution_time_reason": None if time_source == "explicit_source_timestamp" else "explicit_execution_timestamp_not_found",
            "search_period_status": "NOT_RUN", "validation_status": "NOT_RUN",
        },
    })
    candidates, unparsed, excluded, complete = candidate_records(text, links, contract)
    unique = {candidate.canonical_key for candidate in candidates}
    registry.put("batch_source_messages", {
        "id": key(batch_id, message_id, str(index)), "batch_id": batch_id,
        "source_message_id": message_id, "position_id": position_id, "section_index": index,
        "parser_version": PARSER_VERSION,
        "raw": len(candidates) + unparsed + excluded if complete else None,
        "parsed": len(unique), "duplicate": len(candidates) - len(unique),
        "unparsed": unparsed if complete else None, "excluded": excluded,
        "counts_status": "PASS" if complete else "NOT_RUN",
    })
    if not complete or unparsed:
        review(registry, message_id, "candidate_parse_incomplete", reference=batch_id,
               batch_id=batch_id, unparsed=unparsed if complete else None)
    if not confirmed:
        review(registry, message_id, "provisional_execution", reference=batch_id, batch_id=batch_id)
    for candidate in candidates:
        _store_candidate(registry, source, candidate, batch, position_id, text, index, contract)


def _store_candidate(
    registry: Registry, source: dict[str, Any], candidate: CandidateEvidence,
    batch: dict[str, Any], position_id: str, segment: str, index: int, contract: EvidenceContract,
) -> None:
    identity = candidate.canonical_key
    section = _candidate_section(segment, candidate.profile_url)
    raw_urls = [m.group(0) for m in PROFILE.finditer(section)
                if canonical_candidate_url(m.group(0)) == candidate.profile_url]
    registry.put("candidates", {"id": identity, "canonical_url": candidate.profile_url,
                                "source_channel": candidate.source_channel,
                                "normalization_rule": "channel_identity_preserved_tracking_removed",
                                "cross_channel_link": "NOT_RUN"})
    evaluation_id = key(identity, position_id, source["id"], str(index), PARSER_VERSION)
    reported = REPORTED.search(section)
    heading_score = re.search(r"\s[—–]\s*(\d+(?:\.\d+)?)\s*점|^\s*[-•].+?\s+(\d+(?:\.\d+)?)\s*[—–]", section, re.MULTILINE)
    original_text = reported[1] if reported else (
        heading_score[1] or heading_score[2] if heading_score else None
    )
    original_score = source_reported_number(original_text)
    missing = [axis for axis in contract.score_weights
               if candidate.score_components is None or axis not in candidate.score_components]
    name, name_reason = _verified_candidate_name(candidate.display_name)
    evaluation = {**asdict(candidate), "id": evaluation_id, "candidate_id": identity,
                  "position_id": position_id, "batch_id": batch["id"],
                  "source_message_id": source["id"], "week_id": batch["document"]["week_id"],
                  "candidate_name": name,
                  "candidate_name_status": "UNKNOWN" if name is None else "PASS",
                  "candidate_name_reason": name_reason,
                  "profile_url": raw_urls[0] if raw_urls else candidate.profile_url,
                  "score_status": "PASS" if candidate.score is not None else "NOT_RUN",
                  "missing_components": missing, "source_reported_score": original_score,
                  "source_score_label": reported[0] if reported else heading_score[0] if heading_score else None,
                  "source_score_rubric": None,
                  "source_score_validation": "NOT_RUN:source_rubric_not_verified" if original_score is not None else None,
                  "evaluated_at": source["received_at"], "evaluation_version": PARSER_VERSION,
                  "calculation_version": contract.score_contract_version,
                  "source_segment": section, "human_followup": None,
                  "human_followup_reason": "NOT_RUN:human_followup_not_collected"}
    registry.put("candidate_position_evaluations", evaluation)
    registry.put("candidate_batches", {"id": key(identity, batch["id"], position_id),
                                       "candidate_id": identity, "position_id": position_id,
                                       "batch_id": batch["id"]})
    for axis, value in (candidate.score_components or {}).items():
        registry.put("score_components", {"id": key(evaluation_id, axis),
            "evaluation_id": evaluation_id, "axis": axis, "score": value,
            "criterion": axis, "source_reference": f"gmail:{source['id']}",
            "evidence": section, "evaluation_version": PARSER_VERSION,
            "calculation_version": contract.score_contract_version,
            "input_hash": candidate.score_input_hash, "evaluated_at": source["received_at"]})


def _candidate_section(text: str, url: str) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    locations = [i for i, line in enumerate(lines) if any(
        canonical_candidate_url(m.group(0)) == url for m in PROFILE.finditer(line)
    )]
    if not locations:
        return text
    at = locations[0]
    patterns = (_CANDIDATE_HEADING, _NAMED_CANDIDATE_HEADING,
                _REPORT_CANDIDATE_HEADING, _SUMMARY_CANDIDATE_HEADING)
    boundaries = [i for i, line in enumerate(lines) if any(p.match(line) for p in patterns)]
    start = max((i for i in boundaries if i <= at), default=at)
    end = next((i for i in boundaries if i > at), len(lines))
    other_profiles = [i for i, line in enumerate(lines) if i != at and PROFILE.search(line)]
    if not boundaries and other_profiles:
        return lines[at]
    if not boundaries:
        start = 0
    return "\n".join(lines[start:end])


def _attachments(registry: Registry, message_id: str, part: dict[str, Any]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    if part.get("filename") or part.get("body", {}).get("attachmentId"):
        identity = key(message_id, part.get("partId", ""), part.get("filename", ""))
        existing = registry.db.execute("SELECT document FROM source_attachments WHERE id=?",
                                       (identity,)).fetchone()
        attachment = json.loads(existing[0]) if existing else {
            "id": identity, "source_message_id": message_id, "filename": part.get("filename"),
            "mime_type": part.get("mimeType"), "attachment_id": part.get("body", {}).get("attachmentId"),
            "status": "REVIEW_REQUIRED", "reason": "attachment_extraction_pending",
        }
        data = part.get("body", {}).get("data")
        if isinstance(data, str) and part.get("mimeType", "").startswith("text/"):
            try:
                attachment.update(extracted_text=base64.urlsafe_b64decode(data + "=" * (-len(data) % 4)).decode(),
                                  status="PARSED", reason=None)
            except (ValueError, UnicodeError):
                attachment.update(status="REVIEW_REQUIRED", reason="attachment_text_decode_failed")
        registry.put("source_attachments", attachment)
        if attachment["status"] != "PARSED":
            review(registry, message_id, attachment["reason"], reference=identity, attachment_id=identity)
        result.append(attachment)
    for child in part.get("parts", []):
        result.extend(_attachments(registry, message_id, child))
    return result


def store_report_contact(
    registry: Registry, message: dict[str, Any], contract: EvidenceContract,
) -> None:
    """Retain Grok's source report, but require event-level candidate/position evidence."""
    meta = headers(message)
    text, _ = _message_body(adapt_mime(message["payload"]))
    actor, reason = _contact_actor(adapt_mime(message["payload"]), contract)
    registry.put("contact_evidence", {"id": key(message["id"], "report"),
        "source_message_id": message["id"], "subject": meta.get("subject"), "text": text,
        "actor": actor, "actor_reason": reason, "status": "REVIEW_REQUIRED",
        "reason": "report_requires_candidate_position_and_exhaustive_scope_binding"})
    review(registry, message["id"], "contact_report_binding_pending")
