"""Follow-up contracts for real Gmail AI Search evidence."""

from __future__ import annotations

from pathlib import Path
from typing import cast

from hypothesis import given
from hypothesis import strategies as st

from humansearch.admin_ai_search import load_evidence_contract
from humansearch.admin_ai_search.gmail_source import (
    GMAIL_SNAPSHOT_VERSION,
    build_ai_search_payload_from_gmail_snapshot,
)
from humansearch.admin_ai_search.gmail_subject import classify_actor, subject_context

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


def test_single_metadata_tag_never_becomes_the_customer() -> None:
    subject = (
        "[ChatGPT-AISearch] [긴급] REDACTED_CLIENT Data Analyst "
        "— REDACTED CANDIDATE 90점 판정"
    )

    assert subject_context(subject) == ("REDACTED_CLIENT", "Data Analyst")


def test_reply_prefix_preserves_actor_and_customer_context() -> None:
    subject = (
        "Re: [ChatGPT-AISearch] [aisearch] REDACTED_CLIENT Data Analyst "
        "— REDACTED CANDIDATE 90점 판정"
    )

    assert classify_actor(subject, "AI Search <sender@valueconnect.kr>") == (
        "CHATGPT",
        "subject_marker:chatgpt",
    )
    assert subject_context(subject) == ("REDACTED_CLIENT", "Data Analyst")


def test_actor_token_before_metadata_tag_never_becomes_customer_context() -> None:
    subject = (
        "[aisearch]chatgpt [태그] REDACTED_CLIENT Data Analyst "
        "— REDACTED CANDIDATE 90점 판정"
    )

    assert classify_actor(subject, "AI Search <sender@valueconnect.kr>") == (
        "CHATGPT",
        "subject_marker:chatgpt",
    )
    assert subject_context(subject) == ("REDACTED_CLIENT", "Data Analyst")


def test_labels_after_profile_url_fill_candidate_detail() -> None:
    contract = load_evidence_contract(CONTRACT_PATH)
    body = """
      <a href="https://www.linkedin.com/in/redacted-a">REDACTED A</a>
      <p>경력: REDACTED FULL CAREER</p>
      <p>학력: REDACTED EDUCATION</p>
      <p>적합 근거: REDACTED FIT EVIDENCE</p>
    """

    payload = build_ai_search_payload_from_gmail_snapshot(
        _snapshot(
            _message(
                "gmail-real",
                "[ChatGPT-AISearch] [aisearch] REDACTED_CLIENT Data Analyst — 판정",
                body,
            )
        ),
        contract,
    )

    candidate = payload["batches"][0]["candidates"][0]
    assert candidate["experience"] == "REDACTED FULL CAREER"
    assert candidate["education"] == "REDACTED EDUCATION"
    assert candidate["why_fit"] == ["REDACTED FIT EVIDENCE"]


def test_named_candidate_heading_prevents_cross_candidate_evidence_leak() -> None:
    contract = load_evidence_contract(CONTRACT_PATH)
    body = """
      <h2>후보 A</h2>
      <a href="https://www.linkedin.com/in/redacted-a">REDACTED A</a>
      <h2>후보 B</h2>
      <p>프로필 URL 미확인</p>
      <p>경력: REDACTED B CAREER</p>
      <p>학력 점수: 90</p>
      <p>직무 적합성 점수: 80</p>
      <p>고난도 업무 점수: 70</p>
      <p>직무 기술 논리성 점수: 60</p>
    """

    payload = build_ai_search_payload_from_gmail_snapshot(
        _snapshot(
            _message(
                "gmail-real",
                "[ChatGPT-AISearch] [aisearch] REDACTED_CLIENT Data Analyst — 판정",
                body,
            )
        ),
        contract,
    )

    batch = payload["batches"][0]
    candidate = batch["candidates"][0]
    assert candidate["experience"] is None
    assert candidate["score"] is None
    assert candidate["score_status"] == "NOT_RUN"
    assert batch["candidate_counts"] == {
        "raw": 2,
        "parsed": 1,
        "duplicate": 0,
        "unparsed": 1,
        "excluded": 0,
    }


def test_candidate_results_heading_does_not_erase_multiple_profile_urls() -> None:
    contract = load_evidence_contract(CONTRACT_PATH)
    body = """
      <h2>후보 검색결과</h2>
      <a href="https://www.linkedin.com/in/redacted-a">REDACTED A</a>
      <a href="https://www.linkedin.com/in/redacted-b">REDACTED B</a>
    """

    payload = build_ai_search_payload_from_gmail_snapshot(
        _snapshot(
            _message(
                "gmail-real",
                "[ChatGPT-AISearch] [aisearch] REDACTED_CLIENT Data Analyst — 판정",
                body,
            )
        ),
        contract,
    )

    batch = payload["batches"][0]
    assert len(batch["candidates"]) == 2
    assert batch["candidate_counts"] == {
        "raw": 2,
        "parsed": 2,
        "duplicate": 0,
        "unparsed": 0,
        "excluded": 0,
    }


def test_conflicting_explicit_run_ids_are_not_grouped() -> None:
    contract = load_evidence_contract(CONTRACT_PATH)
    subject = (
        "[ChatGPT-AISearch] [aisearch] REDACTED_CLIENT Data Analyst "
        "— run ID: run-A"
    )
    first = _message(
        "gmail-a",
        subject,
        """
          <p>run ID: run-B</p>
          <a href="https://www.linkedin.com/in/redacted-a">REDACTED A</a>
        """,
    )
    second = _message(
        "gmail-b",
        subject,
        """
          <p>run ID: run-A</p>
          <a href="https://www.linkedin.com/in/redacted-b">REDACTED B</a>
        """,
    )

    payload = build_ai_search_payload_from_gmail_snapshot(_snapshot(first, second), contract)

    assert len(payload["batches"]) == 2
    conflict = next(
        batch
        for batch in payload["batches"]
        if batch["batch_grouping"]["reason"] == "conflicting_explicit_run_ids"
    )
    assert conflict["batch_grouping"]["status"] == "NOT_RUN"
    assert conflict["batch_grouping"]["reason"] == "conflicting_explicit_run_ids"


@given(
    education=st.integers(min_value=0, max_value=100),
    job_fit=st.integers(min_value=0, max_value=100),
    difficult_work=st.integers(min_value=0, max_value=100),
    job_description_logic=st.integers(min_value=0, max_value=100),
)
def test_weighted_score_is_deterministic_and_bounded(
    education: int,
    job_fit: int,
    difficult_work: int,
    job_description_logic: int,
) -> None:
    from humansearch.admin_ai_search.evidence import calculate_candidate_score

    components = {
        "education": education,
        "job_fit": job_fit,
        "difficult_work": difficult_work,
        "job_description_logic": job_description_logic,
    }
    weights = {
        "education": 40,
        "job_fit": 40,
        "difficult_work": 10,
        "job_description_logic": 10,
    }

    score = calculate_candidate_score(components, weights)

    expected = (
        education * 40
        + job_fit * 40
        + difficult_work * 10
        + job_description_logic * 10
        + 50
    ) // 100
    assert score == expected
    assert 0 <= score <= 100


def test_four_explicit_score_axes_are_calculated_by_code() -> None:
    contract = load_evidence_contract(CONTRACT_PATH)
    body = """
      <a href="https://www.linkedin.com/in/redacted-a">REDACTED A</a>
      <p>학력 점수: 90</p>
      <p>직무 적합성 점수: 80</p>
      <p>고난도 업무 점수: 70</p>
      <p>직무 기술 논리성 점수: 60</p>
    """

    payload = build_ai_search_payload_from_gmail_snapshot(
        _snapshot(
            _message(
                "gmail-real",
                "[ChatGPT-AISearch] [aisearch] REDACTED_CLIENT Data Analyst — 판정",
                body,
            )
        ),
        contract,
    )

    candidate = payload["batches"][0]["candidates"][0]
    assert candidate["score"] == 81
    assert candidate["score_contract_version"] == "admin-ai-search-score/v2"
    assert candidate["score_components"] == {
        "education": 90,
        "job_fit": 80,
        "difficult_work": 70,
        "job_description_logic": 60,
    }
    assert candidate["score_input_hash"] is not None
    assert len(candidate["score_input_hash"]) == 64


def test_conflicting_score_axis_evidence_is_not_silently_accepted() -> None:
    contract = load_evidence_contract(CONTRACT_PATH)
    body = """
      <a href="https://www.linkedin.com/in/redacted-a">REDACTED A</a>
      <p>학력 점수: 90</p>
      <p>학력 점수: 10</p>
      <p>직무 적합성 점수: 80</p>
      <p>고난도 업무 점수: 70</p>
      <p>직무 기술 논리성 점수: 60</p>
    """

    payload = build_ai_search_payload_from_gmail_snapshot(
        _snapshot(
            _message(
                "gmail-real",
                "[ChatGPT-AISearch] [aisearch] REDACTED_CLIENT Data Analyst — 판정",
                body,
            )
        ),
        contract,
    )

    candidate = payload["batches"][0]["candidates"][0]
    assert candidate["score"] is None
    assert candidate["score_status"] == "NOT_RUN"
    assert candidate["score_reason"] == "score_contract_evidence_conflict"
    assert candidate["score_components"] is None
    assert candidate["score_input_hash"] is None
