"""The owner-approved AI Search admin contract must remain discoverable and testable."""

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
        "GROK | CLAUDE_CODE | CHATGPT | AI_SEARCH | OTHER",
        "학력 40%",
        "직무적합성 40%",
        "고난도 업무 10%",
        "직무기술 논리성 10%",
        "AI | OWNER | UNKNOWN",
        "NOT_RUN",
        "발송 0건",
        "원격 DB 쓰기 0건",
    ):
        assert required in sot

    for required in (
        "고유 후보 프로필 6,831",
        "후보–Batch 등장 8,648",
        "직접 제안 8",
        "AI 7 / OWNER 1 / UNKNOWN 0",
        "후보 연결 0 / 미연결 8",
        "GET /api/ai-search/candidates/{canonical_key}",
        "목록 상태",
        "상세 상태",
        "빈 상태",
        "오류 상태",
    ):
        assert required in spec
