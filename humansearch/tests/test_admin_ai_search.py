"""Acceptance tests for the read-only AI Search evidence surface."""

import json
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime
from http.client import HTTPConnection
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from humansearch.admin_ai_search import (
    AiSearchPayload,
    AiSearchRun,
    CandidateEvidence,
    ContactEvidence,
    VerificationCheck,
    build_ai_search_batch,
    build_ai_search_payload,
    load_evidence_contract,
    stable_batch_id,
)
from humansearch.admin_weekly_dashboard.shadow_server import ShadowServer, create_shadow_server

REPO_ROOT = Path(__file__).parents[2]
ASSET_DIR = REPO_ROOT / "apps" / "admin"
METRIC_CONTRACT_PATH = (
    REPO_ROOT / "contracts" / "admin-weekly-dashboard" / "metric-contract-v1.json"
)
EVIDENCE_CONTRACT_PATH = REPO_ROOT / "contracts" / "admin-ai-search" / "evidence-contract-v1.json"
KST = ZoneInfo("Asia/Seoul")


def candidate(
    key: str,
    score: int,
    *,
    channel: str = "SARAMIN",
    label: str = "후보 A",
) -> CandidateEvidence:
    return CandidateEvidence(
        canonical_key=key * 64,
        display_name=label,
        source_channel=channel,
        profile_url=f"https://example.invalid/{key}/{score}",
        education="대학교 졸업",
        experience="관련 경력 7년",
        score=score,
        why_fit=("필수 역량 근거 확인",),
        reverse_match_position="인접 포지션",
        reverse_match_score=81,
        reverse_match_reason="현재 포지션이 더 높은 점수",
        contact_recommendation="STRONG",
    )


def run(
    *,
    candidates: tuple[CandidateEvidence, ...],
    contacts: tuple[ContactEvidence, ...] = (),
    checks: tuple[VerificationCheck, ...] = (),
) -> AiSearchRun:
    return AiSearchRun(
        actor="CLAUDE_CODE",
        source_run_id="run-20261027-001",
        company="테스트 고객사",
        position="백엔드 엔지니어",
        channels=("SARAMIN", "JOBKOREA", "LINKEDIN"),
        executed_at=datetime(2026, 10, 27, 9, 30, tzinfo=KST),
        candidates=candidates,
        contacts=contacts,
        verification_checks=checks,
    )


def test_contract_defines_daily_read_only_evidence_sources() -> None:
    contract = load_evidence_contract(EVIDENCE_CONTRACT_PATH)

    assert contract.version == "admin-ai-search-evidence/v1"
    assert contract.cadence == "DAILY"
    assert contract.required_verification_sources == (
        "SARAMIN_BILLING",
        "SARAMIN_MESSENGER",
        "JOBKOREA_POSITION",
        "LINKEDIN_INMAIL",
    )
    assert set(contract.external_effects.values()) == {"READ_ONLY_NOT_CONNECTED", "DISABLED"}


def test_batch_id_is_stable_and_changes_with_source_run() -> None:
    executed_at = datetime(2026, 10, 27, 9, 30, tzinfo=KST)

    first = stable_batch_id("CLAUDE_CODE", "source-1", executed_at)
    second = stable_batch_id("CLAUDE_CODE", "source-1", executed_at)
    other = stable_batch_id("CLAUDE_CODE", "source-2", executed_at)

    assert first == second
    assert first.startswith("VHAI-20261027-")
    assert first != other


def test_batch_deduplicates_candidates_and_counts_score_bands() -> None:
    contract = load_evidence_contract(EVIDENCE_CONTRACT_PATH)
    search_run = run(
        candidates=(
            candidate("a", 91, channel="SARAMIN"),
            candidate("a", 94, channel="LINKEDIN"),
            candidate("b", 88),
            candidate("c", 73),
            candidate("d", 69),
        )
    )

    batch = build_ai_search_batch(search_run, contract)

    assert batch["raw_candidates"] == 5
    assert batch["unique_candidates"] == 4
    assert batch["score_buckets"] == {"90_plus": 1, "80s": 1, "70s": 1}
    assert [item["score"] for item in batch["candidates"]] == [94, 88, 73, 69]
    assert batch["actual_fu"] is None
    assert batch["actual_fu_status"] == "NOT_RUN"
    assert batch["actual_fu_reason"] == "fu_portal_verification_not_run"
    assert batch["verification_status"] == "NOT_RUN"


def test_actual_fu_only_counts_candidates_with_passed_contact_evidence() -> None:
    contract = load_evidence_contract(EVIDENCE_CONTRACT_PATH)
    contacts = (
        ContactEvidence(
            canonical_key="a" * 64,
            source="SARAMIN_MESSENGER",
            status="PASS",
            contacted_at="2026-10-27T10:00:00+09:00",
            evidence_reference="saramin-message-1",
        ),
        ContactEvidence(
            canonical_key="b" * 64,
            source="LINKEDIN_INMAIL",
            status="NOT_RUN",
            contacted_at=None,
            evidence_reference=None,
        ),
    )
    checks = (
        VerificationCheck(
            source="SARAMIN_MESSENGER",
            status="PASS",
            checked_at="2026-10-27T11:00:00+09:00",
            reason=None,
        ),
    )

    batch = build_ai_search_batch(
        run(candidates=(candidate("a", 91), candidate("b", 82)), contacts=contacts, checks=checks),
        contract,
    )

    assert batch["actual_fu"] == 1
    assert [item["contact_status"] for item in batch["candidates"]] == ["PASS", "NOT_RUN"]
    assert batch["verification_status"] == "NOT_RUN"
    assert batch["verification_reason"] == "required_sources_not_checked"


def test_empty_live_input_is_not_reported_as_zero_activity() -> None:
    contract = load_evidence_contract(EVIDENCE_CONTRACT_PATH)

    payload = build_ai_search_payload((), contract)

    expected: dict[str, object] = {
        "mode": "LOCAL_SHADOW",
        "contract_version": "admin-ai-search-evidence/v1",
        "status": "NOT_RUN",
        "reason": "live_sources_not_connected",
        "cadence": "DAILY",
        "batches": [],
        "external_effects": contract.external_effects,
    }
    assert dict(payload) == expected


def test_invalid_candidate_score_fails_closed() -> None:
    with pytest.raises(ValueError, match="score"):
        candidate("a", 101)


@contextmanager
def running_server(payload: AiSearchPayload) -> Iterator[tuple[ShadowServer, int]]:
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


def request(port: int, path: str) -> tuple[int, str, bytes]:
    connection = HTTPConnection("127.0.0.1", port, timeout=5)
    connection.request("GET", path)
    response = connection.getresponse()
    body = response.read()
    content_type = response.getheader("Content-Type", "")
    connection.close()
    return response.status, content_type, body


def test_server_exposes_ai_search_list_detail_and_page() -> None:
    contract = load_evidence_contract(EVIDENCE_CONTRACT_PATH)
    payload = build_ai_search_payload((run(candidates=(candidate("a", 91),)),), contract)
    batch_id = payload["batches"][0]["batch_id"]

    with running_server(payload) as (_, port):
        list_status, _, list_body = request(port, "/api/ai-search")
        detail_status, _, detail_body = request(port, f"/api/ai-search/{batch_id}")
        page_status, page_type, page_body = request(port, "/ai-search")
        script_status, _, script_body = request(port, "/ai-search.js")

    assert list_status == 200
    assert json.loads(list_body) == payload
    assert detail_status == 200
    assert json.loads(detail_body) == payload["batches"][0]
    assert page_status == 200
    assert page_type == "text/html; charset=utf-8"
    assert "AI Search Evidence" in page_body.decode("utf-8")
    assert "중복 제거 후보 (Batch별 합계)" in page_body.decode("utf-8")
    assert script_status == 200
    assert b"/api/ai-search" in script_body


def test_unknown_batch_detail_fails_closed() -> None:
    contract = load_evidence_contract(EVIDENCE_CONTRACT_PATH)
    payload = build_ai_search_payload((), contract)

    with running_server(payload) as (_, port):
        status, _, body = request(port, "/api/ai-search/VHAI-UNKNOWN")

    assert status == 404
    assert json.loads(body) == {"status": "FAIL", "reason": "batch_not_found"}


def test_ai_search_assets_expose_required_detail_and_error_states() -> None:
    page = (ASSET_DIR / "ai-search.html").read_text(encoding="utf-8")
    script = (ASSET_DIR / "ai-search.js").read_text(encoding="utf-8")

    assert 'id="error-state"' in page
    assert "검색 기간" in page
    for field in (
        "actor_evidence",
        "candidate_counts",
        "key_experience",
        "requirements_evidence",
        "better_position_exists",
        "contact_source",
        "contact_checked_at",
        "contact_opinion_evidence",
    ):
        assert field in script
