"""The owner-approved AI Search admin contract must remain discoverable and testable."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).parents[2]
SOT_PATH = REPO_ROOT / "docs" / "sot" / "admin-ai-search-evidence.md"
SPEC_PATH = (
    REPO_ROOT
    / "docs"
    / "engineering"
    / "admin-ai-search-evidence-spec-2026-10-29.md"
)


def test_ai_search_admin_sot_and_spec_fix_the_owner_contract() -> None:
    sot = SOT_PATH.read_text(encoding="utf-8")
    spec = SPEC_PATH.read_text(encoding="utf-8")
    index = (REPO_ROOT / "docs" / "sot" / "INDEX.md").read_text(encoding="utf-8")

    assert "admin-ai-search-evidence.md" in index
    for required in (
        "raw = parsed + duplicate + unparsed + excluded",
        "GROK | CLAUDE_CODE | CODEX | CHATGPT | ASIDE | AI_SEARCH | OTHER",
        "W45-01",
        "학력 40%",
        "직무적합성 40%",
        "고난도 업무 10%",
        "직무기술 논리성 10%",
        "AI | OWNER | UNKNOWN",
        "NOT_RUN",
        "발송 0건",
        "원격 DB 쓰기 0건",
        "일요일 00:00",
        "(batch_id, canonical_key)",
        "후보 서치 원장",
        "주간 컨택 원장",
    ):
        assert required in sot

    for required in (
        "고유 후보 프로필 6,830",
        "후보–Batch 등장 8,646",
        "직접 제안 8",
        "AI 7 / OWNER 1 / UNKNOWN 0",
        "후보 연결 0 / 미연결 8",
        "GET /api/ai-search/candidates/{canonical_key}",
        "GET /api/ai-search/weekly",
        "GET /api/ai-search/weekly/{week_id}",
        "한 행 = 한 Batch의 중복 제거 후보 1명",
        "목록 상태",
        "상세 상태",
        "빈 상태",
        "오류 상태",
    ):
        assert required in spec
