"""Acceptance coverage for the global candidate and contact evidence ledger."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from humansearch.admin_ai_search import (
    AiSearchRun,
    CandidateEvidence,
    ContactEvidence,
    build_ai_search_payload,
    load_evidence_contract,
)
from humansearch.admin_ai_search.gmail_source import GMAIL_SNAPSHOT_VERSION
from humansearch.admin_ai_search.gmail_sent_contacts import (
    GMAIL_EVIDENCE_ENVELOPE_VERSION,
    GMAIL_SENT_SNAPSHOT_VERSION,
    build_ai_search_payload_from_gmail_evidence,
)

REPO_ROOT = Path(__file__).parents[2]
CONTRACT_PATH = REPO_ROOT / "contracts" / "admin-ai-search" / "evidence-contract-v1.json"
KST = ZoneInfo("Asia/Seoul")


def _candidate(url: str, name: str, score: int | None = None) -> CandidateEvidence:
    return CandidateEvidence(
        canonical_key=hashlib.sha256(url.encode()).hexdigest(),
        display_name=name,
        source_channel="LINKEDIN",
        profile_url=url,
        education=None,
        experience=None,
        score=score,
        score_reason="score_contract_evidence_missing" if score is None else None,
        why_fit=(),
        reverse_match_position=None,
        reverse_match_score=None,
        reverse_match_reason="NOT_RUN:reverse_match_contract_evidence_missing",
        contact_recommendation="NOT_RUN",
    )


def _run(
    run_id: str,
    position: str,
    *candidates: CandidateEvidence,
    contacts: tuple[ContactEvidence, ...] = (),
) -> AiSearchRun:
    return AiSearchRun(
        actor="CLAUDE_CODE",
        source_run_id=run_id,
        company="고객사",
        position=position,
        channels=("LINKEDIN",),
        executed_at=datetime(2026, 10, 28, 9, len(run_id), tzinfo=KST),
        candidates=tuple(candidates),
        contacts=contacts,
    )


def test_global_candidate_ledger_keeps_all_position_scores_and_contact_actors() -> None:
    contract = load_evidence_contract(CONTRACT_PATH)
    shared = _candidate("https://linkedin.com/in/shared", "공유 후보")
    other = _candidate("https://linkedin.com/in/other", "다른 후보")
    ai_contact = ContactEvidence(
        canonical_key=shared.canonical_key,
        source="LINKEDIN_INMAIL",
        status="PASS",
        contacted_at="2026-10-28",
        evidence_reference="gmail-message-ai",
        actor="AI",
        actor_reason="gmail_api_client:ai-search",
    )
    owner_contact = ContactEvidence(
        canonical_key=shared.canonical_key,
        source="GMAIL",
        status="PASS",
        contacted_at="2026-10-29T10:00:00+09:00",
        evidence_reference="gmail-message-owner",
        actor="OWNER",
        actor_reason="gmail_api_client:owner",
    )

    payload = build_ai_search_payload(
        (
            _run("a", "백엔드", shared, other, contacts=(ai_contact,)),
            _run("bb", "데이터", shared, contacts=(owner_contact,)),
        ),
        contract,
    )

    assert payload["candidate_summary"] == {
        "unique_profiles": 2,
        "batch_appearances": 3,
        "known_position_assignments": 3,
        "unknown_position_assignments": 0,
        "score_known_profiles": 0,
        "score_status": "NOT_RUN",
        "score_reason": "no_candidate_scores_verified",
    }
    ledger = {item["canonical_key"]: item for item in payload["candidate_ledger"]}
    shared_row = ledger[shared.canonical_key]
    assert [item["position"] for item in shared_row["search_history"]] == [
        "데이터",
        "백엔드",
    ]
    assert all(item["score_status"] == "NOT_RUN" for item in shared_row["search_history"])
    assert [item["actor"] for item in shared_row["contact_history"]] == [
        "OWNER",
        "AI",
    ]
    assert shared_row["contact_status"] == "PASS"
    assert payload["batches"][0]["candidates"][0]["search_history"] == shared_row[
        "search_history"
    ]
    assert payload["batches"][0]["candidates"][0]["contact_history"] == shared_row[
        "contact_history"
    ]


def test_unique_profile_identity_normalizes_tracking_but_not_cross_channel_people() -> None:
    from humansearch.admin_ai_search.gmail_candidates import candidate_records

    contract = load_evidence_contract(CONTRACT_PATH)
    body = """
    <h2>후보 1</h2>
    <a href="https://www.linkedin.com/in/same-person/?trk=search">후보 A</a>
    <h2>후보 2</h2>
    <a href="https://kr.linkedin.com/in/same-person">후보 A 중복</a>
    <h2>후보 3</h2>
    <a href="https://hiring.saramin.co.kr/applicant-view/position/resume/123?highlight=1">사람인</a>
    <h2>후보 4</h2>
    <a href="https://hiring.saramin.co.kr/applicant-view/position/resume/123?highlight=2">사람인 중복</a>
    """

    candidates, _, _, complete = candidate_records(body, (), contract)

    assert complete is True
    assert candidates[0].canonical_key == candidates[1].canonical_key
    assert candidates[2].canonical_key == candidates[3].canonical_key


def _gmail_message(
    message_id: str,
    subject: str,
    body: str,
    *,
    client_id: str = "77377267392",
    to: str = "candidate@example.com",
) -> dict[str, object]:
    return {
        "id": message_id,
        "thread_id": f"thread-{message_id}",
        "internal_date": "1793160000000",
        "label_ids": ["SENT"],
        "payload": {
            "mime_type": "text/html",
            "headers": [
                {"name": "Subject", "value": subject},
                {"name": "From", "value": "ValueConnect <sender@valueconnect.kr>"},
                {"name": "To", "value": to},
                {
                    "name": "Received",
                    "value": (
                        f"from {client_id} named unknown by gmailapi.google.com "
                        "with HTTPREST; Wed, 28 Oct 2026 01:00:00 -0400"
                    ),
                },
            ],
            "body": {"content": body},
            "parts": [],
        },
    }


def _gmail_snapshot(
    version: str, query: str, *messages: Mapping[str, object]
) -> dict[str, object]:
    ids = [str(message["id"]) for message in messages]
    return {
        "version": version,
        "query": query,
        "page_count": 1,
        "pagination_exhausted": True,
        "pages": [
            {"request_page_token": None, "message_ids": ids, "next_page_token": None}
        ],
        "message_ids": ids,
        "messages": list(messages),
    }


def test_gmail_sent_ledger_splits_ai_owner_and_never_guesses_candidate_link() -> None:
    contract = load_evidence_contract(CONTRACT_PATH)
    profile = "https://linkedin.com/in/contacted"
    search = _gmail_snapshot(
        GMAIL_SNAPSHOT_VERSION,
        "subject:aisearch -in:spam -in:trash",
        _gmail_message(
            "search-message",
            "[aisearch]claudecode [고객사][백엔드]",
            f'<h2>후보 1</h2><a href="{profile}">연결 후보</a>',
            to="sender@valueconnect.kr",
        ),
    )
    sent = _gmail_snapshot(
        GMAIL_SENT_SNAPSHOT_VERSION,
        'in:sent {subject:"이직 제안" subject:"포지션 제안"}',
        _gmail_message(
            "sent-ai",
            "[고객사] 백엔드 포지션 제안",
            f'<p>안녕하세요.</p><a href="{profile}">후보 프로필</a>',
        ),
        _gmail_message(
            "sent-owner",
            "[고객사] 데이터 포지션 제안",
            "<p>후보님, 안녕하세요. 프로필 링크는 메일에 없습니다.</p>",
            client_id="224054973946",
        ),
        _gmail_message(
            "sent-qa",
            "백엔드 채용 제안",
            "<p>QA-476 검증 메일입니다.</p>",
            client_id="402185046281",
        ),
    )

    payload = build_ai_search_payload_from_gmail_evidence(
        {"version": GMAIL_EVIDENCE_ENVELOPE_VERSION, "search": search, "sent": sent},
        contract,
    )

    collection = payload["contact_collection"]
    assert collection["status"] == "PASS"
    assert collection["direct_contact_count"] == 2
    assert collection["ai_sent_count"] == 1
    assert collection["owner_sent_count"] == 1
    assert collection["unknown_sent_count"] == 0
    assert collection["linked_contact_count"] == 1
    assert collection["unlinked_contact_count"] == 1
    assert collection["excluded_message_count"] == 1
    assert [event["actor"] for event in collection["events"]] == ["AI", "OWNER"]
    candidate = payload["candidate_ledger"][0]
    assert [event["actor"] for event in candidate["contact_history"]] == ["AI"]
    assert collection["events"][1]["link_status"] == "NOT_RUN"
    assert collection["events"][1]["link_reason"] == "candidate_profile_not_in_sent_message"

