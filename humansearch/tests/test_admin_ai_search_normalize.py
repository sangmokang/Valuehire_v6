"""Source evidence stays attached to its own position and execution."""

import base64
from pathlib import Path

from humansearch.admin_ai_search.evidence import load_evidence_contract
from humansearch.admin_ai_search.normalize import normalize_message
from humansearch.admin_ai_search.registry import Registry

CONTRACT = load_evidence_contract(
    Path(__file__).parents[2] / "contracts/admin-ai-search/evidence-contract-v1.json"
)


def message(identity: str, body: str) -> dict[str, object]:
    return {"id": identity, "threadId": "thread", "internalDate": "1792306800000",
            "labelIds": ["INBOX"], "payload": {"mimeType": "text/plain", "headers": [
                {"name": "Subject", "value": "[aisearch_grok] [Client][Engineer]"},
                {"name": "From", "value": "report@example.invalid"},
                {"name": "To", "value": "operator@example.invalid"},
            ], "body": {"data": base64.urlsafe_b64encode(body.encode()).decode()}}}


def test_explicit_execution_alerts_merge_without_losing_source_evidence(tmp_path: Path) -> None:
    registry = Registry(tmp_path / "private.sqlite")
    body = "run ID: execution-123\nhttps://linkedin.com/in/candidate-a\n메일 점수: 97"
    normalize_message(registry, message("m1", body), CONTRACT)
    normalize_message(registry, message("m2", body), CONTRACT)
    normalize_message(registry, message("m1", body), CONTRACT)
    assert len(registry.documents("batches")) == 1
    assert len(registry.documents("batch_source_messages")) == 2
    evaluations = registry.documents("candidate_position_evaluations")
    assert len(evaluations) == 2
    assert all(e["score"] is None and e["score_status"] == "NOT_RUN" for e in evaluations)
    assert all(e["source_reported_score"] == 97 for e in evaluations)


def test_no_execution_evidence_keeps_same_day_messages_provisional(tmp_path: Path) -> None:
    registry = Registry(tmp_path / "private.sqlite")
    for identity in ("m1", "m2"):
        normalize_message(registry, message(identity, "https://linkedin.com/in/a"), CONTRACT)
    batches = registry.db.execute("SELECT grouping_status FROM batches").fetchall()
    assert [b[0] for b in batches] == ["PROVISIONAL", "PROVISIONAL"]


def test_sections_keep_two_positions_and_evaluations_for_one_candidate(tmp_path: Path) -> None:
    registry = Registry(tmp_path / "private.sqlite")
    body = ("고객사: First / 포지션: Engineer\nhttps://linkedin.com/in/same\n메일 점수: 97\n"
            "고객사: Second / 포지션: Analyst\nhttps://linkedin.com/in/same\n메일 점수: 82")
    normalize_message(registry, message("multi", body), CONTRACT)
    assert len(registry.documents("candidates")) == 1
    assert len(registry.documents("positions")) == 2
    evaluations = registry.documents("candidate_position_evaluations")
    assert {e["source_reported_score"] for e in evaluations} == {97, 82}
    assert len({e["position_id"] for e in evaluations}) == 2


def test_explicit_execution_time_is_separate_from_received_time(tmp_path: Path) -> None:
    registry = Registry(tmp_path / "private.sqlite")
    normalize_message(registry, message("timed", "실행시각: 2026-10-18T00:05:00+09:00\nhttps://linkedin.com/in/a"), CONTRACT)
    batch = registry.documents("batches")[0]
    assert batch["executed_at"] == "2026-10-17T15:05:00+00:00"
    assert batch["executed_at"] != batch["received_at"]
    assert batch["execution_time_source"] == "explicit_source_timestamp"


def test_source_score_does_not_cross_the_next_candidate_boundary(tmp_path: Path) -> None:
    registry = Registry(tmp_path / "private.sqlite")
    normalize_message(registry, message("two", "후보 1\nhttps://linkedin.com/in/a\n메일 점수: 97\n후보 2\nhttps://linkedin.com/in/b"), CONTRACT)
    rows = registry.documents("candidate_position_evaluations")
    assert {r["profile_url"]: r["source_reported_score"] for r in rows} == {
        "https://linkedin.com/in/a": 97, "https://linkedin.com/in/b": None,
    }
