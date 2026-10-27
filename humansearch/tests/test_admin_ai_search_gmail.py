"""Gmail adapter contract tests using a redacted live-message shape."""

from __future__ import annotations

import json
from collections.abc import Mapping
from io import StringIO
from pathlib import Path

import pytest

from humansearch.admin_ai_search import load_evidence_contract
from humansearch.admin_ai_search.gmail_source import (
    GMAIL_SNAPSHOT_VERSION,
    build_ai_search_payload_from_gmail_snapshot,
)
from humansearch.admin_weekly_dashboard.shadow_server import (
    load_ai_search_payload_from_stream,
)

REPO_ROOT = Path(__file__).parents[2]
EVIDENCE_CONTRACT_PATH = REPO_ROOT / "contracts" / "admin-ai-search" / "evidence-contract-v1.json"


def _message(subject: str, body: str, *, message_id: str = "gmail-message-1") -> dict[str, object]:
    return {
        "id": message_id,
        "thread_id": f"thread-{message_id}",
        "internal_date": "1793061000000",
        "payload": {
            "mime_type": "text/html",
            "headers": [
                {"name": "Subject", "value": subject},
                {"name": "From", "value": "AI Search <sender@valueconnect.kr>"},
            ],
            "body": {"content": body},
            "parts": [],
        },
    }


def _snapshot(
    *messages: Mapping[str, object], pagination_exhausted: bool = True
) -> dict[str, object]:
    return {
        "version": GMAIL_SNAPSHOT_VERSION,
        "query": "subject:aisearch -in:spam -in:trash",
        "page_count": 1,
        "pagination_exhausted": pagination_exhausted,
        "message_ids": [message["id"] for message in messages],
        "messages": list(messages),
    }


@pytest.mark.parametrize(
    ("subject", "actor", "reason"),
    [
        ("[aisearch]grok3.0 [REDACTED][REDACTED]", "GROK", "subject_marker:grok"),
        (
            "[aisearch]claudecode [REDACTED][REDACTED]",
            "CLAUDE_CODE",
            "subject_marker:claude_code",
        ),
        (
            "[aisearch]chatgpt [REDACTED][REDACTED]",
            "CHATGPT",
            "subject_marker:chatgpt",
        ),
        ("[aisearch] [REDACTED][REDACTED]", "AI_SEARCH", "subject_marker:ai_search"),
        ("[aisearch]codex [REDACTED][REDACTED]", "OTHER", "unsupported_marker:codex"),
    ],
)
def test_actor_is_classified_from_evidence_and_unknown_is_other(
    subject: str, actor: str, reason: str
) -> None:
    contract = load_evidence_contract(EVIDENCE_CONTRACT_PATH)
    payload = build_ai_search_payload_from_gmail_snapshot(
        _snapshot(_message(subject, "<p>후보 결과 없음</p>")), contract
    )

    batch = payload["batches"][0]
    assert batch["actor"] == actor
    assert batch["actor_evidence"] == {
        "subject": subject,
        "sender": "AI Search <sender@valueconnect.kr>",
        "thread_id": "thread-gmail-message-1",
        "message_id": "gmail-message-1",
        "received_at": "2026-10-27T00:30:00+00:00",
        "reason": reason,
    }


def test_redacted_live_shape_preserves_count_equation_and_unknown_score() -> None:
    contract = load_evidence_contract(EVIDENCE_CONTRACT_PATH)
    body = """
      <h2>검색 기간: 2026-10-01 ~ 2026-10-15</h2>
      <h2>후보 1</h2>
      <a href="https://www.linkedin.com/in/redacted-candidate">REDACTED CANDIDATE</a>
      <p>총경력: REDACTED FULL CAREER</p>
      <p>핵심 경력: REDACTED CORE CAREER</p>
      <p>필수요건 근거: REDACTED REQUIREMENT EVIDENCE</p>
      <p>추천 근거: REDACTED CONTACT OPINION</p>
      <p>점수: 95</p>
      <a href="https://www.linkedin.com/in/redacted-candidate">duplicate link</a>
      <h2>후보 2</h2>
      <p>프로필 URL 미확인</p>
      <h2>제외 후보: REDACTED</h2>
    """

    payload = build_ai_search_payload_from_gmail_snapshot(
        _snapshot(_message("[aisearch]chatgpt [REDACTED CLIENT][REDACTED ROLE] — 결과", body)),
        contract,
    )

    batch = payload["batches"][0]
    assert batch["candidate_counts"] == {
        "raw": 4,
        "parsed": 1,
        "duplicate": 1,
        "unparsed": 1,
        "excluded": 1,
    }
    assert batch["raw_candidates"] == 4
    assert batch["unique_candidates"] == 1
    assert batch["score_buckets"] == {"90_plus": None, "80s": None, "70s": None}
    assert batch["score_status"] == "NOT_RUN"
    assert batch["score_reason"] == "v5_score_contract_evidence_missing"
    assert batch["actual_fu"] is None
    assert batch["actual_fu_status"] == "NOT_RUN"
    assert batch["search_period"] == {
        "start": "2026-10-01",
        "end": "2026-10-15",
        "status": "PASS",
        "reason": None,
    }
    candidate = batch["candidates"][0]
    assert candidate["score"] is None
    assert candidate["score_status"] == "NOT_RUN"
    assert candidate["experience"] == "REDACTED FULL CAREER"
    assert candidate["key_experience"] == "REDACTED CORE CAREER"
    assert candidate["requirements_evidence"] == ["REDACTED REQUIREMENT EVIDENCE"]
    assert candidate["better_position_exists"] is None
    assert candidate["contact_source"] is None
    assert candidate["contact_checked_at"] is None
    assert candidate["contact_opinion_evidence"] == "REDACTED CONTACT OPINION"


def test_same_gmail_message_always_builds_the_same_batch_id() -> None:
    contract = load_evidence_contract(EVIDENCE_CONTRACT_PATH)
    snapshot = _snapshot(
        _message(
            "[aisearch]chatgpt [REDACTED CLIENT][REDACTED ROLE]",
            '<a href="https://www.linkedin.com/in/redacted">REDACTED</a>',
        )
    )

    first = build_ai_search_payload_from_gmail_snapshot(snapshot, contract)
    second = build_ai_search_payload_from_gmail_snapshot(snapshot, contract)

    assert first["batches"][0]["batch_id"] == second["batches"][0]["batch_id"]


def test_unidentifiable_candidate_records_are_not_reported_as_zero() -> None:
    contract = load_evidence_contract(EVIDENCE_CONTRACT_PATH)
    payload = build_ai_search_payload_from_gmail_snapshot(
        _snapshot(
            _message(
                "[aisearch]chatgpt [REDACTED CLIENT][REDACTED ROLE]",
                "<p>후보 요약은 별도 원문에 있습니다.</p>",
            )
        ),
        contract,
    )

    batch = payload["batches"][0]
    assert batch["raw_candidates"] is None
    assert batch["candidate_counts"]["raw"] is None
    assert batch["candidate_counts"]["unparsed"] is None
    assert batch["candidate_counts_status"] == "NOT_RUN"
    assert batch["candidate_counts_reason"] == "candidate_records_not_identifiable"


def test_conflicting_actor_markers_fail_closed_to_other() -> None:
    contract = load_evidence_contract(EVIDENCE_CONTRACT_PATH)
    payload = build_ai_search_payload_from_gmail_snapshot(
        _snapshot(
            _message(
                "[aisearch]chatgpt-grok [REDACTED][REDACTED]",
                "<p>후보 결과 없음</p>",
            )
        ),
        contract,
    )

    batch = payload["batches"][0]
    assert batch["actor"] == "OTHER"
    actor_evidence = batch["actor_evidence"]
    assert actor_evidence is not None
    assert actor_evidence["reason"] == "actor_markers_conflict"


def test_incomplete_pagination_can_never_be_pass() -> None:
    contract = load_evidence_contract(EVIDENCE_CONTRACT_PATH)
    payload = build_ai_search_payload_from_gmail_snapshot(
        _snapshot(
            _message("[aisearch] [REDACTED][REDACTED]", "<p>후보 결과 없음</p>"),
            pagination_exhausted=False,
        ),
        contract,
    )

    assert payload["status"] == "NOT_RUN"
    assert payload["reason"] == "gmail_pagination_incomplete"
    assert payload["gmail_collection"]["pagination_exhausted"] is False


def test_snapshot_rejects_unknown_fields_and_response_id_mismatch() -> None:
    contract = load_evidence_contract(EVIDENCE_CONTRACT_PATH)
    message = _message("[aisearch] [REDACTED][REDACTED]", "<p>후보 결과 없음</p>")
    snapshot = _snapshot(message)
    snapshot["unexpected"] = True

    with pytest.raises(ValueError, match="snapshot fields"):
        build_ai_search_payload_from_gmail_snapshot(snapshot, contract)

    mismatch = _snapshot(message)
    mismatch["message_ids"] = ["different-message"]
    with pytest.raises(ValueError, match="message_ids"):
        build_ai_search_payload_from_gmail_snapshot(mismatch, contract)


def test_runtime_stream_loads_real_shape_without_writing_a_snapshot_file() -> None:
    contract = load_evidence_contract(EVIDENCE_CONTRACT_PATH)
    snapshot = _snapshot(
        _message(
            "[aisearch]chatgpt [REDACTED CLIENT][REDACTED ROLE]",
            '<a href="https://www.linkedin.com/in/redacted">REDACTED</a>',
        )
    )

    payload = load_ai_search_payload_from_stream(
        StringIO(json.dumps(snapshot, ensure_ascii=False) + "\n"),
        contract,
    )

    assert payload["gmail_collection"]["message_count"] == 1
    assert payload["external_effects"]["gmail"] == "READ_ONLY"
    assert len(payload["batches"]) == 1


def test_runtime_stream_rejects_non_object_json() -> None:
    contract = load_evidence_contract(EVIDENCE_CONTRACT_PATH)

    with pytest.raises(TypeError, match="JSON object"):
        load_ai_search_payload_from_stream(StringIO("[]\n"), contract)
