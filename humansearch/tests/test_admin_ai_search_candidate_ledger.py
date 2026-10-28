"""Acceptance coverage for the global candidate and contact evidence ledger."""

from __future__ import annotations

import hashlib
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

