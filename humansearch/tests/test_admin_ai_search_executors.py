"""Every execution tool shares one weekly Batch sequence and keeps explicit evidence."""

import base64
import json
from pathlib import Path
from typing import cast

import pytest

from humansearch.admin_ai_search.contact_reports import ingest_report
from humansearch.admin_ai_search.evidence import load_evidence_contract
from humansearch.admin_ai_search.gmail_subject import classify_actor, subject_context
from humansearch.admin_ai_search.normalize import normalize_message
from humansearch.admin_ai_search.registry import Registry

CONTRACT = load_evidence_contract(
    Path(__file__).parents[2] / "contracts/admin-ai-search/evidence-contract-v1.json"
)
OWNER = '"Operator" <operator@example.invalid>'


@pytest.mark.parametrize(("subject", "sender", "expected"), [
    ("[aisearch]codex Young CTO — 125명 전체 결과", OWNER, ("CODEX", "subject_marker:codex")),
    ("[aisearch]Aside 토트 백엔드 — 85+ 1명", OWNER, ("ASIDE", "subject_marker:aside")),
    ("[aisearch-grokbot] 모벤시스 기술영업", OWNER, ("GROK", "subject_marker:grok")),
    ("[aisearch]claudecode PR #109 Aside×Cursor Grok 분할 리뷰", OWNER,
     ("CLAUDE_CODE", "subject_marker:claude_code")),
    ("[ChatGPT-AISearch] 역전에프앤씨 PM", OWNER, ("CHATGPT", "subject_marker:chatgpt")),
    ("[Task Update] 스푼랩스 AI Search", "ChatGPT <noreply@tm.openai.com>",
     ("CHATGPT", "sender:openai_chatgpt_task")),
    ("[aisearch]Claude-win 코드잇 운영 리드", OWNER, ("OTHER", "unsupported_marker:claude_win")),
    ("[aisearch] 번개장터 라이브커머스 리드", OWNER, ("AI_SEARCH", "subject_marker:ai_search")),
    ("[데일리 로그] 운영 지표", OWNER, ("OTHER", "ai_search_prefix_not_found")),
])
def test_executor_is_classified_from_explicit_subject_or_sender(
    subject: str, sender: str, expected: tuple[str, str],
) -> None:
    assert classify_actor(subject, sender) == expected


def test_explicit_body_executor_label_is_used_only_when_subject_is_generic() -> None:
    body = "후보 서치 결과\n실행 주체: Codex\n"
    assert classify_actor("[aisearch] 번개장터 리드", OWNER, body) == ("CODEX", "body_label:codex")
    assert classify_actor("[aisearch]Aside 번개장터 리드", OWNER, body) == (
        "ASIDE", "subject_marker:aside")


def _batch(identity: str, status: str, actor: str) -> dict[str, object]:
    return {"id": identity, "week_year": 2026, "week_number": 45,
            "grouping_status": status, "document": {"id": identity, "actor": actor}}


def test_all_executors_and_statuses_share_one_weekly_sequence(tmp_path: Path) -> None:
    registry = Registry(tmp_path / "registry.sqlite")
    numbers = [registry.register_batch(_batch(identity, status, actor))["display_number"]
               for identity, status, actor in (
                   ("grok", "PROVISIONAL", "GROK"), ("claude", "CONFIRMED", "CLAUDE_CODE"),
                   ("codex", "PROVISIONAL", "CODEX"), ("aside", "PROVISIONAL", "ASIDE"))]
    assert numbers == ["W45-01", "W45-02", "W45-03", "W45-04"]
    confirmed = registry.register_batch(_batch("grok", "CONFIRMED", "GROK"))
    assert (confirmed["display_number"], confirmed["grouping_status"]) == ("W45-01", "CONFIRMED")
    assert registry.register_batch(_batch("next", "PROVISIONAL", "OTHER"))["display_number"] == "W45-05"


def test_legacy_provisional_number_is_converted_once_with_history(tmp_path: Path) -> None:
    path = tmp_path / "registry.sqlite"
    registry = Registry(path)
    registry.register_batch(_batch("kept", "CONFIRMED", "GROK"))
    with registry.db:
        for identity, legacy in (("legacy-b", 7), ("legacy-a", 3)):
            registry.db.execute("INSERT INTO batches VALUES (?,?,?,?,?,?,?,?)", (
                identity, 2026, 45, None, legacy, "PROVISIONAL", f"W45-P{legacy:02d}",
                json.dumps({"id": identity})))
    registry.db.close()
    reopened = Registry(path)
    rows = {row["id"]: dict(row) for row in reopened.db.execute("SELECT * FROM batches")}
    assert rows["kept"]["display_number"] == "W45-01"
    assert (rows["legacy-a"]["display_number"], rows["legacy-b"]["display_number"]) == ("W45-02", "W45-03")
    assert json.loads(rows["legacy-a"]["document"])["display_number_history"] == ["W45-P03"]
    assert rows["legacy-a"]["grouping_status"] == "PROVISIONAL"
    reopened.db.close()
    again = Registry(path)
    assert again.register_batch(_batch("legacy-a", "PROVISIONAL", "OTHER"))["display_number"] == "W45-02"
    history = json.loads(again.db.execute(
        "SELECT document FROM batches WHERE id='legacy-a'").fetchone()[0])["display_number_history"]
    assert history == ["W45-P03"]


def _message(identity: str, subject: str, sender: str, body: str) -> dict[str, object]:
    return {"id": identity, "threadId": "thread", "internalDate": "1792306800000",
            "labelIds": ["INBOX"], "payload": {"mimeType": "text/plain", "headers": [
                {"name": "Subject", "value": subject}, {"name": "From", "value": sender},
            ], "body": {"data": base64.urlsafe_b64encode(body.encode()).decode()}}}


def test_review_required_source_keeps_executor_evidence(tmp_path: Path) -> None:
    registry = Registry(tmp_path / "private.sqlite")
    source = normalize_message(registry, _message(
        "task", "[Task Update] 스푼랩스 AI Search", "ChatGPT <noreply@tm.openai.com>",
        "신규 후보 1명을 확인해 내부 보고를 발송했습니다."), CONTRACT)
    assert source["processing_status"] == "REVIEW_REQUIRED"
    assert (source["executor"], source["executor_reason"]) == ("CHATGPT", "sender:openai_chatgpt_task")
    assert registry.documents("batches") == []


def test_processed_codex_batch_records_codex_executor(tmp_path: Path) -> None:
    registry = Registry(tmp_path / "private.sqlite")
    source = normalize_message(registry, _message(
        "codex", "[aisearch]codex [Client][Engineer]", OWNER,
        "https://linkedin.com/in/candidate-a\n메일 점수: 91"), CONTRACT)
    batch = registry.documents("batches")[0]
    assert (source["executor"], batch["actor"]) == ("CODEX", "CODEX")
    assert batch["actor_evidence"][0]["rule"] == "subject_marker:codex"


def test_contact_report_keeps_reporter_executor_separate_from_sender_actor(tmp_path: Path) -> None:
    registry = Registry(tmp_path / "private.sqlite")
    ingest_report(registry, "report", {"text": "사람인 발송 3건", "subject": "[aisearch]Aside 컨택 보고",
                                       "totals": {"SARAMIN": [{"reported_count": 3}]}},
                  executor=("ASIDE", "subject_marker:aside"))
    evidence = cast(dict[str, object], registry.documents("contact_evidence")[0])
    assert (evidence["reporter_executor"], evidence["reporter_executor_reason"]) == (
        "ASIDE", "subject_marker:aside")
    assert registry.documents("contact_events") == []


@pytest.mark.parametrize("subject", [
    "[aisearch] Claude Code [Client][Engineer]",
    "[aisearch]claude code 번개장터 리드",
])
def test_spaced_claude_code_subject_marker_is_preserved(subject: str) -> None:
    assert classify_actor(subject, OWNER) == ("CLAUDE_CODE", "subject_marker:claude_code")


@pytest.mark.parametrize(("body", "expected"), [
    ("실행 주체: Claude Code\n", ("CLAUDE_CODE", "body_label:claude_code")),
    ("executor: Codex\nexecutor: Cursor\n", ("OTHER", "body_label_conflict")),
    ("executor: Codex\nexecutor: Aside\n", ("OTHER", "body_label_conflict")),
    ("실행 주체: Gemini\n", ("OTHER", "unsupported_body_label")),
    ("실행 주체: Cursor\n", ("OTHER", "unsupported_body_label")),
    ("실행 주체: Gemini\n실행 주체: Cursor\n", ("OTHER", "unsupported_body_label")),
])
def test_body_label_conflicts_or_unknown_tools_fail_closed(
    body: str, expected: tuple[str, str],
) -> None:
    assert classify_actor("[aisearch] 번개장터 리드", OWNER, body) == expected


def test_conflicting_body_labels_never_create_a_named_executor_batch(tmp_path: Path) -> None:
    registry = Registry(tmp_path / "private.sqlite")
    normalize_message(registry, _message(
        "conflict", "[aisearch] [Client][Engineer]", OWNER,
        "executor: Codex\nexecutor: Cursor\nhttps://linkedin.com/in/candidate-a"), CONTRACT)
    assert registry.documents("batches")[0]["actor"] == "OTHER"


@pytest.mark.parametrize("body", [
    "실행 주체 : Codex/Aside\n", "실행 주체: Codex, Aside\n",
    "실행 주체: Codex | Aside\n", "실행 주체: Codex (Aside 보조)\n",
])
def test_multiple_tools_on_one_label_line_fail_closed(body: str) -> None:
    assert classify_actor("[aisearch] 번개장터 리드", OWNER, body)[0] == "OTHER"


@pytest.mark.parametrize("subject", [
    "[aisearch] Asidehub 백엔드", "[aisearch] Codexis 엔지니어",
    "[aisearch] Grokking 리드", "[aisearch] chatgptlab PM",
])
def test_company_names_that_start_with_a_tool_name_are_not_executors(subject: str) -> None:
    assert classify_actor(subject, OWNER) == ("AI_SEARCH", "subject_marker:ai_search")


def test_hyphenated_claude_code_token_never_becomes_customer() -> None:
    assert classify_actor("[aisearch] claude-code 번개 리드", OWNER)[0] == "CLAUDE_CODE"
    assert subject_context("[aisearch] claude-code 번개 리드") == ("번개", "리드")


@pytest.mark.parametrize("subject", [
    "[aisearch] Aside-Korea 백엔드", "[aisearch] Codex-랩 엔지니어",
    "[aisearch] Grok_Labs 리드", "[aisearch-codexis] 번개 리드",
])
def test_joined_names_with_unknown_parts_are_not_executors(subject: str) -> None:
    assert classify_actor(subject, OWNER) == ("AI_SEARCH", "subject_marker:ai_search")


@pytest.mark.parametrize("subject", ["[aisearch] codex: 번개 리드", "[aisearch] Codex, 번개 리드"])
def test_executor_token_punctuation_is_ignored(subject: str) -> None:
    assert classify_actor(subject, OWNER) == ("CODEX", "subject_marker:codex")
    assert subject_context(subject) == ("번개", "리드")


@pytest.mark.parametrize(("subject", "expected", "context"), [
    ("[aisearch] Claude Code: 번개 리드", "CLAUDE_CODE", ("번개", "리드")),
    ("[aisearch] grok-4 모벤 기술영업", "GROK", ("모벤", "기술영업")),
])
def test_executor_variants_never_leak_into_customer(
    subject: str, expected: str, context: tuple[str, str],
) -> None:
    assert classify_actor(subject, OWNER)[0] == expected
    assert subject_context(subject) == context


@pytest.mark.parametrize(("subject", "expected"), [
    ("[ChatGPT AI Search 결과] 번개 리드", "CHATGPT"),
    ("[Grok AISearch 결과] 번개 리드", "GROK"),
])
def test_prefix_tag_with_korean_suffix_keeps_executor(subject: str, expected: str) -> None:
    assert classify_actor(subject, OWNER)[0] == expected
