"""Project real MIME evidence into separate candidate/position/evaluation records."""

from __future__ import annotations

import base64
import hashlib
import json
import re
from dataclasses import asdict
from datetime import UTC, datetime
from typing import Any

from .evidence import CandidateEvidence, EvidenceContract, stable_batch_id
from .gmail_candidates import candidate_records, canonical_candidate_url
from .gmail_sent_contacts import _contact_actor
from .gmail_source import _message_body
from .gmail_subject import classify_actor, non_run_reason, subject_context
from .registry import Registry, operation_week

PARSER_VERSION = "admin-ai-search-normalizer/2026-10-29.1"
RUN_ID = re.compile(r"(?:run\s*id|실행\s*ID)\s*[:：#]\s*([\w.:-]{3,128})", re.IGNORECASE)
SECTION = re.compile(r"^(?:#+\s*)?고객사\s*[:：]\s*(.+?)\s*[/|·]\s*포지션\s*[:：]\s*(.+)$", re.MULTILINE)
RELATED = re.compile(r"ai\s*[-_]?\s*search|ai\s*서치|후보.{0,12}(?:서치|검색)|grok.{0,15}컨택", re.IGNORECASE)
PROFILE = re.compile(r"https?://[^\s<>\"']+", re.IGNORECASE)
REPORTED = re.compile(r"(?:메일\s*점수|총점|종합\s*점수|점수|score)\s*[:：]\s*(\d{1,3})(?:\s*/\s*100)?", re.IGNORECASE)


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
                  attachment_status="REVIEW_REQUIRED" if attachments else "NONE")
    # An attachment extraction job can append verified text, without changing MIME.
    for attachment in attachments:
        if attachment.get("extracted_text"):
            text += "\n" + attachment["extracted_text"]
    source["body_text"] = text
    if non_run_reason(subject):
        source.update(processing_status="EXCLUDED", reason=non_run_reason(subject))
        return source
    if not RELATED.search(subject + "\n" + text):
        source.update(processing_status="EXCLUDED", reason="not_ai_search_after_full_body_read")
        return source
    actor, actor_reason = classify_actor(subject, meta.get("from", ""))
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
    position_known = not (company.startswith("NOT_RUN:") or position.startswith("NOT_RUN:"))
    position_id = key(company, position) if position_known else key(message_id, str(index), "unknown")
    registry.put("positions", {"id": position_id, "company": company, "title": position,
                               "status": "PASS" if position_known else "NOT_RUN"})
    run_ids = set(RUN_ID.findall(source["subject"] + "\n" + text))
    confirmed = len(run_ids) == 1
    batch_id = key(actor, "explicit-run", next(iter(run_ids))) if confirmed else stable_batch_id(
        actor, f"{message_id}:section:{index}", received,
    )
    week_id, year, week = operation_week(received)
    batch = registry.register_batch({
        "id": batch_id, "week_year": year, "week_number": week,
        "grouping_status": "CONFIRMED" if confirmed else "PROVISIONAL", "document": {
            "id": batch_id, "week_id": week_id, "actor": actor,
            "grouping_reason": "explicit_run_id" if confirmed else "execution_identity_not_proven",
            "source_message_ids": [message_id], "actor_evidence": [actor_evidence],
            "executed_at": received.isoformat(), "received_at": received.isoformat(),
            "execution_time_source": "received_at_fallback", "execution_time_confidence": "LOW",
            "execution_time_reason": "explicit_execution_timestamp_not_found",
            "search_period_status": "NOT_RUN", "validation_status": "NOT_RUN",
        },
    })
    candidates, unparsed, excluded, complete = candidate_records(text, links, contract)
    unique = {candidate.canonical_key for candidate in candidates}
    registry.put("batch_source_messages", {
        "id": key(batch_id, message_id, str(index)), "batch_id": batch_id,
        "source_message_id": message_id, "position_id": position_id, "section_index": index,
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
    missing = [axis for axis in contract.score_weights
               if candidate.score_components is None or axis not in candidate.score_components]
    evaluation = {**asdict(candidate), "id": evaluation_id, "candidate_id": identity,
                  "position_id": position_id, "batch_id": batch["id"],
                  "source_message_id": source["id"], "week_id": batch["document"]["week_id"],
                  "candidate_name": candidate.display_name,
                  "candidate_name_status": "UNKNOWN" if candidate.display_name == "후보명 미확인" else "PASS",
                  "candidate_name_reason": "candidate_name_not_present_in_source" if candidate.display_name == "후보명 미확인" else None,
                  "profile_url": raw_urls[0] if raw_urls else candidate.profile_url,
                  "score_status": "PASS" if candidate.score is not None else "NOT_RUN",
                  "missing_components": missing, "source_reported_score": int(reported[1]) if reported else None,
                  "source_score_label": reported[0] if reported else None,
                  "source_score_rubric": "SOURCE_REPORTED_NOT_CONTRACT_VERIFIED" if reported else None,
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
    lines = text.splitlines()
    locations = [i for i, line in enumerate(lines) if any(
        canonical_candidate_url(m.group(0)) == url for m in PROFILE.finditer(line)
    )]
    if not locations:
        return text
    start = locations[0]
    previous = max((i for i in range(start) if PROFILE.search(lines[i])), default=-1)
    end = next((i for i in range(start + 1, len(lines)) if PROFILE.search(lines[i])), len(lines))
    return "\n".join(lines[max(previous + 1, start - 2):end])


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
