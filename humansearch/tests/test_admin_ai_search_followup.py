"""Follow-up contracts for real Gmail AI Search evidence."""

from __future__ import annotations

from pathlib import Path
from typing import cast

from humansearch.admin_ai_search import load_evidence_contract
from humansearch.admin_ai_search.gmail_source import (
    GMAIL_SNAPSHOT_VERSION,
    build_ai_search_payload_from_gmail_snapshot,
)

REPO_ROOT = Path(__file__).parents[2]
CONTRACT_PATH = REPO_ROOT / "contracts" / "admin-ai-search" / "evidence-contract-v1.json"


def _message(message_id: str, subject: str, body: str) -> dict[str, object]:
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


def _snapshot(*messages: dict[str, object]) -> dict[str, object]:
    message_ids = [cast(str, message["id"]) for message in messages]
    return {
        "version": GMAIL_SNAPSHOT_VERSION,
        "query": "subject:aisearch -in:spam -in:trash",
        "page_count": 1,
        "pagination_exhausted": True,
        "pages": [
            {
                "request_page_token": None,
                "message_ids": message_ids,
                "next_page_token": None,
            }
        ],
        "message_ids": message_ids,
        "messages": list(messages),
    }


def test_non_run_test_mail_is_excluded_with_a_reason() -> None:
    contract = load_evidence_contract(CONTRACT_PATH)
    normal = _message(
        "gmail-real",
        "[ChatGPT-AISearch] [aisearch] REDACTED_CLIENT Data Analyst — 판정",
        "<p>후보 결과 없음</p>",
    )
    test_mail = _message(
        "gmail-test",
        "[ChatGPT-AISearch] [테스트 메일] REDACTED_CLIENT Data Analyst",
        "<p>후보 결과 없음</p>",
    )

    payload = build_ai_search_payload_from_gmail_snapshot(_snapshot(normal, test_mail), contract)

    assert len(payload["batches"]) == 1
    collection = payload["gmail_collection"]
    assert collection["message_count"] == 2
    assert collection["included_message_count"] == 1
    assert collection["excluded_message_count"] == 1
    assert collection["excluded_messages"] == [
        {"message_id": "gmail-test", "reason": "subject_test_marker"}
    ]
