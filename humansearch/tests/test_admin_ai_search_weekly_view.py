"""Acceptance tests for the weekly, spreadsheet-shaped AI Search operations view."""

from __future__ import annotations

import hashlib
import json
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime
from http.client import HTTPConnection
from pathlib import Path
from zoneinfo import ZoneInfo

from humansearch.admin_ai_search import (
    AiSearchPayload,
    AiSearchRun,
    CandidateEvidence,
    build_ai_search_payload,
    build_weekly_ai_search_view,
    load_evidence_contract,
)
from humansearch.admin_weekly_dashboard.shadow_server import (
    ShadowServer,
    create_shadow_server,
)

REPO_ROOT = Path(__file__).parents[2]
ASSET_DIR = REPO_ROOT / "apps" / "admin"
METRIC_CONTRACT_PATH = (
    REPO_ROOT / "contracts" / "admin-weekly-dashboard" / "metric-contract-v1.json"
)
EVIDENCE_CONTRACT_PATH = (
    REPO_ROOT / "contracts" / "admin-ai-search" / "evidence-contract-v1.json"
)
KST = ZoneInfo("Asia/Seoul")


def _candidate(url: str, name: str, score: int) -> CandidateEvidence:
    components = {
        "education": score,
        "job_fit": score,
        "difficult_work": score,
        "job_description_logic": score,
    }
    version = "admin-ai-search-score/v2"
    digest = hashlib.sha256(
        json.dumps(
            {"components": components, "version": version},
            separators=(",", ":"),
            sort_keys=True,
        ).encode()
    ).hexdigest()
    return CandidateEvidence(
        canonical_key=hashlib.sha256(url.encode()).hexdigest(),
        display_name=name,
        source_channel="LINKEDIN",
        profile_url=url,
        education="한국대학교 컴퓨터공학",
        experience="백엔드 개발 7년",
        key_experience="결제 시스템 4년",
        requirements_evidence=("Python 서비스 운영",),
        score=score,
        score_contract_version=version,
        score_components=components,
        score_input_hash=digest,
        score_reason=None,
        why_fit=("결제 도메인과 대규모 트래픽 경험",),
        reverse_match_position=None,
        reverse_match_score=None,
        reverse_match_reason="NOT_RUN:reverse_match_contract_evidence_missing",
        contact_recommendation="STRONG",
    )


def _run(
    run_id: str,
    position: str,
    executed_at: datetime,
    *candidates: CandidateEvidence,
) -> AiSearchRun:
    return AiSearchRun(
        actor="CLAUDE_CODE",
        source_run_id=run_id,
        company="고객사 A",
        position=position,
        channels=("LINKEDIN",),
        executed_at=executed_at,
        candidates=tuple(candidates),
    )


def _payload() -> AiSearchPayload:
    contract = load_evidence_contract(EVIDENCE_CONTRACT_PATH)
    shared = _candidate("https://linkedin.com/in/shared", "공유 후보", 92)
    other = _candidate("https://linkedin.com/in/other", "다른 후보", 84)
    payload = build_ai_search_payload(
        (
            _run(
                "run-1",
                "백엔드 엔지니어",
                datetime(2026, 10, 20, 9, 0, tzinfo=KST),
                shared,
                shared,
            ),
            _run(
                "run-2",
                "플랫폼 엔지니어",
                datetime(2026, 10, 21, 10, 0, tzinfo=KST),
                shared,
            ),
            _run(
                "run-3",
                "데이터 엔지니어",
                datetime(2026, 10, 27, 11, 0, tzinfo=KST),
                other,
            ),
        ),
        contract,
    )
    payload["gmail_collection"] = {
        "status": "PASS",
        "query": "subject:aisearch -in:spam -in:trash",
        "page_count": 2,
        "message_count": 3,
        "included_message_count": 3,
        "excluded_message_count": 0,
        "pagination_exhausted": True,
    }
    payload["contact_collection"] = {
        "query": "in:sent subject:제안",
        "page_count": 1,
        "message_count": 2,
        "pagination_exhausted": True,
        "status": "PASS",
        "reason": None,
        "direct_contact_count": 2,
        "ai_sent_count": 1,
        "owner_sent_count": 1,
        "unknown_sent_count": 0,
        "linked_contact_count": 1,
        "unlinked_contact_count": 1,
        "excluded_message_count": 0,
        "events": [
            {
                "message_id": "sent-owner",
                "thread_id": "thread-owner",
                "subject": "백엔드 엔지니어 이직 제안",
                "actor": "OWNER",
                "actor_reason": "gmail_api_client_contract:OWNER",
                "contacted_at": "2026-10-22T14:00:00+09:00",
                "source": "GMAIL",
                "evidence_reference": "gmail:sent-owner",
                "canonical_keys": [shared.canonical_key],
                "link_status": "PASS",
                "link_reason": None,
            },
            {
                "message_id": "sent-ai",
                "thread_id": "thread-ai",
                "subject": "플랫폼 엔지니어 포지션 제안",
                "actor": "AI",
                "actor_reason": "gmail_api_client_contract:AI",
                "contacted_at": "2026-10-23T15:00:00+09:00",
                "source": "GMAIL",
                "evidence_reference": "gmail:sent-ai",
                "canonical_keys": [],
                "link_status": "NOT_RUN",
                "link_reason": "candidate_profile_not_in_sent_message",
            },
        ],
    }
    return payload


def test_weekly_view_is_a_batch_candidate_sheet_with_weekly_contact_ledger() -> None:
    view = build_weekly_ai_search_view(_payload())

    assert view["status"] == "PASS"
    assert view["week_rule"] == "SUNDAY_TO_SATURDAY_LABELED_BY_NEXT_MEETING_ISO_WEEK"
    assert [week["week_id"] for week in view["weeks"]] == ["2026-W44", "2026-W45"]

    first = view["weeks"][0]
    assert first["period_label"] == "2026.10.18~2026.10.24"
    assert first["batch_count"] == 2
    assert first["unique_candidate_count"] == 1
    assert first["candidate_row_count"] == 2
    assert len(first["candidate_rows"]) == 2
    assert {row["position"] for row in first["candidate_rows"]} == {
        "백엔드 엔지니어",
        "플랫폼 엔지니어",
    }

    row = first["candidate_rows"][0]
    assert row["candidate_name"] == "공유 후보"
    assert row["profile_url"] == "https://linkedin.com/in/shared"
    assert row["education"] == "한국대학교 컴퓨터공학"
    assert row["experience"] == "백엔드 개발 7년"
    assert row["score"] == 92
    assert row["score_evidence"] == [
        "결제 도메인과 대규모 트래픽 경험",
        "Python 서비스 운영",
    ]
    assert row["weekly_contact"]["owner_sent_count"] == 1
    assert row["weekly_contact"]["ai_sent_count"] == 0

    assert first["contact_summary"] == {
        "total": 2,
        "ai_sent": 1,
        "owner_sent": 1,
        "unknown_sent": 0,
        "linked": 1,
        "unlinked": 1,
        "owner_linked_candidates": 1,
    }
    assert [row["actor"] for row in first["contact_rows"]] == ["AI", "OWNER"]
    assert first["contact_rows"][0]["link_status"] == "NOT_RUN"
    assert first["contact_rows"][0]["link_reason"] == (
        "candidate_profile_not_in_sent_message"
    )


def test_weekly_view_does_not_report_pass_when_gmail_pagination_is_incomplete() -> None:
    payload = _payload()
    payload["gmail_collection"]["pagination_exhausted"] = False
    payload["gmail_collection"]["status"] = "NOT_RUN"

    view = build_weekly_ai_search_view(payload)

    assert view["status"] == "NOT_RUN"
    assert view["reason"] == "gmail_collection_incomplete"
    assert all(week["status"] == "NOT_RUN" for week in view["weeks"])


@contextmanager
def _running_server(payload: AiSearchPayload) -> Iterator[tuple[ShadowServer, int]]:
    server = create_shadow_server(
        assets=ASSET_DIR,
        contract_path=METRIC_CONTRACT_PATH,
        host="127.0.0.1",
        port=0,
        ai_search_payload=payload,
    )
    port = int(server.server_address[1])
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server, port
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def _request(port: int, path: str) -> tuple[int, bytes]:
    connection = HTTPConnection("127.0.0.1", port, timeout=5)
    connection.request("GET", path)
    response = connection.getresponse()
    body = response.read()
    status = response.status
    connection.close()
    return status, body


def test_server_exposes_compact_week_index_and_selected_week_detail() -> None:
    with _running_server(_payload()) as (_, port):
        index_status, index_body = _request(port, "/api/ai-search/weekly")
        week_status, week_body = _request(port, "/api/ai-search/weekly/2026-W44")
        missing_status, missing_body = _request(port, "/api/ai-search/weekly/2026-W01")

    index = json.loads(index_body)
    detail = json.loads(week_body)
    assert index_status == 200
    assert [week["week_id"] for week in index["weeks"]] == ["2026-W44", "2026-W45"]
    assert "candidate_rows" not in index["weeks"][0]
    assert week_status == 200
    assert detail["week_id"] == "2026-W44"
    assert len(detail["candidate_rows"]) == 2
    assert missing_status == 404
    assert json.loads(missing_body) == {
        "status": "FAIL",
        "reason": "ai_search_week_not_found",
    }


def test_weekly_assets_are_week_first_spreadsheets_not_card_ledgers() -> None:
    page = (ASSET_DIR / "ai-search.html").read_text(encoding="utf-8")
    script = (ASSET_DIR / "ai-search.js").read_text(encoding="utf-8")

    assert 'id="week-select"' in page
    assert "후보 서치 원장" in page
    assert "주간 컨택 원장" in page
    for heading in (
        "실행 일시",
        "고객사",
        "포지션",
        "검색 AI",
        "후보자",
        "프로필 URL",
        "학력",
        "경력",
        "점수",
        "점수·적합 이유",
        "주간 컨택",
    ):
        assert heading in page
    assert "/api/ai-search/weekly" in script
    assert "/api/ai-search\"" not in script
