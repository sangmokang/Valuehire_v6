"""Fail-closed key allowlist schemas for weekly-ops canonical input and output.

열거식 금지 목록(deny-list)은 미열거 키를 통과시키므로, 이 모듈은 발행 페이로드의
모든 오브젝트를 정확 키 허용목록으로 닫는다. 허용목록 밖 키와 스칼라 자리에 숨은
dict/list 구조는 전부 미지 필드로 거부한다(fail-closed catch-all).
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any

FORBIDDEN_KEYS = {
    "raw_body",
    "body_html",
    "body_text",
    "candidate_name",
    "candidate_display_name",
    "candidate_full_name", "applicant_display_name", "applicant_full_name",
    "applicant_name",
    "candidate_email",
    "sender_address",
    "recipient_address",
    "access_token",
    "api_key",
    "credential",
}
FORBIDDEN_KEY_TOKENS = {re.sub(r"[^a-z0-9]", "", key.casefold()) for key in FORBIDDEN_KEYS}

_DIFFICULTY = {"scarcity": None, "seniority": None, "constraints": None, "funnel_friction": None}
_POSITION = {
    "canonical_id": None, "company": None, "title": None, "category": None,
    "origin": None, "intent": None, "event_at": None, "deadline_days": None,
    "late_stage": None, "client_priority": None, "lifecycle": None,
    "difficulty": _DIFFICULTY, "evidence_refs": ("list", None), "action": None,
}
_CAPABILITY = {"name": None, "status": None, "required": None}
_SOURCE_SNAPSHOT = {
    "snapshot_id": None, "source_system": None, "source_uri_ref": None,
    "fetched_at": None, "status": None, "content_hash": None,
    "evidence_refs": ("list", None),
}
_DEDUPE_DECISION = {
    "decision_id": None, "kept_canonical_id": None,
    "removed_source_refs": ("list", None), "reason": None, "rule_version": None,
}
_CAREER_SUMMARY = {
    "company": None, "official_url": None, "status": None, "active_requisitions": None,
    "talent_pools": None, "freshness_at": None, "limitation": None,
    "source_snapshot_id": None,
}
_CONSULTANT = {
    "consultant_id": None, "consultant_display": None,
    "provider_accounts": {
        "jobkorea": ("list", None), "saramin": ("list", None), "linkedin_rps": ("list", None),
    },
}
_DIAGNOSTIC = {
    "channel": None, "access_state": None, "surface_kind": None, "surface_ref": None,
    "stable_receipt_available": None, "covered_provider_actor_refs": ("list", None),
    "source_snapshot_id": None, "blocker_reason": None,
}
_OUTREACH_EVENT = {
    "event_id": None, "consultant_id": None, "consultant_display": None,
    "position_id": None, "channel": None, "status": None, "sent_at": None,
    "candidate_key_hmac": None, "provider_actor_ref": None, "provider_receipt_ref": None,
    "source_snapshot_id": None, "provider_seat_ref": None, "provider_project_ref": None,
}
_ZERO_RESULT = {
    "collection": None, "rule_version": None, "source_snapshot_id": None,
    "provider_receipt_ref": None, "observed_count": None,
}
_PUBLICATION_TARGET = {
    "name": None, "target_id": None, "required": None, "status": None,
    "write_ahead_intent_id": None, "idempotency_key": None, "schema_readback_ref": None,
    "external_object_id": None, "receipt_id": None, "receipt_persisted_ref": None,
    "report_snapshot_id": None, "content_hash": None,
}
_OPERATING_SNAPSHOT = {
    "source_snapshot_id": None, "meeting_date": None, "generated_at": None,
    "timezone": None, "provenance": None, "count_semantics": None,
    "closed_week": {
        "week_start": None, "week_end": None, "week_label": None, "new_positions": None,
        "new_position_companies": None, "ai_search_runs": None, "position_coverage": None,
        "recommended_people": None, "admin_ai_search_rows": None,
        "recommendation_events": None,
    },
    "current": {
        "open_positions": None, "position_last_synced_at": None,
        "candidate_last_synced_at": None,
        "funnel": {
            "ai_sourcing": None, "proposal": None, "recommended": None,
            "interviewing": None, "final_pass": None, "joined": None,
        },
    },
    "targets": {
        "weekly_proposals": None, "weekly_recommendations": None, "weekly_revenue": None,
        "annual_recommendations": None, "annual_revenue": None, "average_fee": None,
        "proposal_acceptance_rate": None, "recommend_to_final_rate": None,
        "recommend_to_join_rate": None,
    },
}
INPUT_SCHEMA = {
    "schema_version": None,
    "run": {
        "meeting_at": None, "window_start": None,
        "window_end_exclusive": None, "late_alert_end": None,
    },
    "capabilities": ("list", _CAPABILITY),
    "source_snapshots": ("list", _SOURCE_SNAPSHOT),
    "operating_snapshot": _OPERATING_SNAPSHOT,
    "dedupe_decisions": ("list", _DEDUPE_DECISION),
    "positions": ("list", _POSITION),
    "career_page_summaries": ("list", _CAREER_SUMMARY),
    "consultant_roster": ("list", _CONSULTANT),
    "outreach_channel_diagnostics": ("list", _DIAGNOSTIC),
    "outreach_events": ("list", _OUTREACH_EVENT),
    "zero_result_assertions": ("list", _ZERO_RESULT),
    "publication_targets": ("list", _PUBLICATION_TARGET),
}


def find_forbidden_fields(value: Any) -> list[str]:
    found: list[str] = []
    if isinstance(value, dict):
        for key, nested in value.items():
            if re.sub(r"[^a-z0-9]", "", unicodedata.normalize("NFKC", str(key)).casefold()) in FORBIDDEN_KEY_TOKENS:
                found.append(key)
            found.extend(find_forbidden_fields(nested))
    elif isinstance(value, list):
        for nested in value:
            found.extend(find_forbidden_fields(nested))
    return found


def _walk_schema(value: Any, node: Any, path: str, found: list[str]) -> None:
    if node is None:
        if isinstance(value, (dict, list, tuple, set, frozenset)):
            found.append(path)
        return
    if isinstance(node, tuple):
        if isinstance(value, (dict, tuple, set, frozenset)):
            found.append(path)
        elif isinstance(value, list):
            for index, item in enumerate(value):
                _walk_schema(item, node[1], f"{path}[{index}]", found)
        return
    if isinstance(value, (list, tuple, set, frozenset)):
        found.append(path)
        return
    if not isinstance(value, dict):
        return
    for key, nested in value.items():
        if not isinstance(key, str) or key not in node:
            found.append(f"{path}.{key}")
        else:
            _walk_schema(nested, node[key], f"{path}.{key}", found)


def find_unknown_fields(value: Any, schema: Any = None) -> list[str]:
    """허용목록 밖 키·미지 구조의 경로 목록. 비어 있지 않으면 fail-closed 거부 대상."""
    found: list[str] = []
    _walk_schema(value, INPUT_SCHEMA if schema is None else schema, "$", found)
    return sorted(set(found))


_SCORE = {"urgency": None, "difficulty": None, "priority": None, "version": None}
_POSITION_OUT = dict(_POSITION, score=_SCORE, period=None)
_CHANNEL_MIX = {"jobkorea": None, "saramin": None, "linkedin_rps": None}
_FOCUS_POSITION = {
    "position_id": None, "company": None, "title": None, "verified_sent_count": None,
    "unique_candidate_count": None, "active_days": None, "channels": ("list", None),
    "channel_mix": _CHANNEL_MIX, "evidence_refs": ("list", None), "focus_share": None,
    "grass_evidence": None,
}
_FOCUS = {
    "consultant_id": None, "consultant_display": None, "verified_sent_count": None,
    "unique_candidate_count": None, "active_days": None, "channel_mix": _CHANNEL_MIX,
    "comparison_status": None, "positions": ("list", _FOCUS_POSITION),
}
_COVERAGE = {
    "channel": None, "access_state": None, "surface_kind": None,
    "covered_consultants": ("list", None), "not_run_consultants": ("list", None),
    "covered_account_count": None, "expected_account_count": None,
    "not_run_blockers": ("list", None),
}
_RECEIPT = {
    "target_name": None, "target_id": None, "status": None,
    "write_ahead_intent_id": None, "idempotency_key": None, "schema_readback_ref": None,
    "external_object_id": None, "receipt_id": None, "receipt_persisted_ref": None,
    "report_snapshot_id": None, "content_hash": None,
}
OUTPUT_SCHEMA = {
    "schema_version": None, "verdict": None, "data_verdict": None,
    "publication_verdict": None, "publication_errors": ("list", None),
    "report_snapshot_id": None, "input_hash": None, "content_hash": None,
    "score_version": None, "consultant_focus_version": None,
    "positions": ("list", _POSITION_OUT), "customer_priority_ids": ("list", None),
    "consultant_focus": ("list", _FOCUS), "channel_coverage": ("list", _COVERAGE),
    "excluded_rows": ("list", {"reason": None, "evidence_ref": None}),
    "career_page_summaries": ("list", _CAREER_SUMMARY),
    "operating_snapshot": _OPERATING_SNAPSHOT, "brief_markdown": None,
    "publication_report_markdown": None, "receipts": ("list", _RECEIPT),
    "errors": ("list", None), "blockers": ("list", None),
}


def final_output_violations(result: Any) -> list[str]:
    """content hash/readback 직전 최종 산출물을 WU-1(허용목록)·WU-2(값) 검사기로 재검사."""
    from contract_gate import find_sensitive_values

    found = find_unknown_fields(result, OUTPUT_SCHEMA)
    found.extend(find_forbidden_fields(result))
    if find_sensitive_values(result):
        found.append("$.sensitive_value")
    return found


def sanitized_blocked_result(result: dict[str, Any]) -> dict[str, Any]:
    """재검사 실패 시 발행 차단: 입력 유래 payload를 전부 비운 BLOCKED 결과로 대체."""
    errors = sorted(set(list(result.get("errors", [])) + ["FORBIDDEN_SENSITIVE_OUTPUT"]))
    return {
        "schema_version": result.get("schema_version"),
        "verdict": "BLOCKED",
        "data_verdict": "BLOCKED",
        "publication_verdict": "BLOCKED",
        "publication_errors": [],
        "report_snapshot_id": result.get("report_snapshot_id"),
        "input_hash": result.get("input_hash"),
        "content_hash": "",
        "score_version": result.get("score_version"),
        "consultant_focus_version": result.get("consultant_focus_version"),
        "positions": [], "customer_priority_ids": [], "consultant_focus": [],
        "channel_coverage": [], "excluded_rows": [], "career_page_summaries": [],
        "operating_snapshot": {}, "brief_markdown": "",
        "publication_report_markdown": "", "receipts": [],
        "errors": errors, "blockers": [],
    }
