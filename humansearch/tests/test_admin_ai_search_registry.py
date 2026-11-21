"""Permanent batch numbers and channel identity must survive rediscovery."""

from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from humansearch.admin_ai_search.gmail_candidates import canonical_candidate_url
from humansearch.admin_ai_search.registry import Registry, operation_week


def test_saramin_candidate_identity_parameter_is_not_tracking() -> None:
    first = canonical_candidate_url(
        "https://www.saramin.co.kr/zf_user/company/talent-pool/view?res_idx=123&utm_source=mail"
    )
    second = canonical_candidate_url(
        "https://www.saramin.co.kr/zf_user/company/talent-pool/view?res_idx=456"
    )
    assert first == "https://saramin.co.kr/zf_user/company/talent-pool/view?res_idx=123"
    assert first != second


def test_template_or_malformed_profile_url_is_rejected_without_parser_crash() -> None:
    assert canonical_candidate_url("https://linkedin.com:{채널포트}/in/candidate") is None
    assert canonical_candidate_url("https://[invalid/in/candidate") is None


def test_week_is_half_open_kst_and_uses_existing_meeting_iso_label() -> None:
    kst = ZoneInfo("Asia/Seoul")
    assert operation_week(datetime(2026, 10, 24, 23, 59, tzinfo=kst))[0] == "2026-W44"
    assert operation_week(datetime(2026, 10, 25, 0, 0, tzinfo=kst))[0] == "2026-W45"


def test_batch_numbers_never_renumber_when_older_evidence_arrives(tmp_path: Path) -> None:
    registry = Registry(tmp_path / "registry.sqlite")
    def batch(identity: str, status: str) -> dict[str, object]:
        return {"id": identity, "week_year": 2026, "week_number": 44,
                "grouping_status": status, "document": {"reason": "source evidence"}}
    first = registry.register_batch(batch("stable-first", "CONFIRMED"))
    provisional = registry.register_batch(batch("stable-provisional", "PROVISIONAL"))
    older = registry.register_batch(batch("stable-older", "CONFIRMED"))
    repeated = registry.register_batch(batch("stable-first", "CONFIRMED"))
    assert first["display_number"] == repeated["display_number"] == "W44-01"
    assert provisional["display_number"] == "W44-02"
    assert older["display_number"] == "W44-03"


def test_confirmation_preserves_internal_identity_and_display_number(tmp_path: Path) -> None:
    registry = Registry(tmp_path / "registry.sqlite")
    batch = {"id": "permanent", "week_year": 2026, "week_number": 44,
             "grouping_status": "PROVISIONAL", "document": {"id": "permanent"}}
    provisional = registry.register_batch(batch)
    confirmed = registry.register_batch({**batch, "grouping_status": "CONFIRMED"})
    later = registry.register_batch({**batch, "id": "later"})
    assert provisional["id"] == confirmed["id"] == "permanent"
    assert provisional["display_number"] == confirmed["display_number"] == "W44-01"
    assert confirmed["grouping_status"] == "CONFIRMED"
    assert later["display_number"] == "W44-02"
