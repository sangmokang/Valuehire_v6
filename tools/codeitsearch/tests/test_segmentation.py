import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from keywords import SEGMENT_KEYWORDS, TIERS, terms  # noqa: E402
from segmentation import (  # noqa: E402
    is_searchable,
    parse_experience,
    segment_of,
    segment_positions,
)

SNAPSHOT = json.loads(
    (ROOT / "data" / "codeit_positions_2026-09-28.json").read_text(encoding="utf-8")
)


class TestParseExperience:
    @pytest.mark.parametrize(
        "label,expected",
        [
            ("경력 (3~10년)", (3, 10)),
            ("경력 (1년 이상)", (1, None)),
            ("경력 (5년 이하)", (0, 5)),
            ("경력 무관", (None, None)),
            ("신입", (None, None)),
            (None, (None, None)),
        ],
    )
    def test_ranges(self, label, expected):
        assert tuple(parse_experience(label)) == expected


class TestSegmentOf:
    def test_talent_pool_marker_wins_over_job_label(self):
        assert segment_of({"title": "📝 인재풀 등록 - 백엔드 부트캠프 멘토", "job": "강사·멘토"}) == "talent_pool"

    def test_content_partner_marker(self):
        assert segment_of({"title": "콘텐츠 파트너 [공통]", "job": None}) == "content_partner"

    def test_unknown_job_is_unsegmented(self):
        assert segment_of({"title": "무언가", "job": "알수없는직무"}) == "unsegmented"


class TestIsSearchable:
    def test_freelance_instructor_is_not_searchable(self):
        assert not is_searchable(
            {"title": "풀스택 부트캠프 강사", "job": "강사·멘토", "etype": "프리랜서", "status": "상시 채용"}
        )

    def test_closed_posting_is_not_searchable(self):
        assert not is_searchable(
            {"title": "세일즈 리드", "job": "세일즈", "etype": "정규직", "status": "지원 마감"}
        )

    def test_contract_and_intern_are_not_searchable(self):
        for etype in ("계약직", "인턴"):
            assert not is_searchable(
                {"title": "x", "job": "교육 운영", "etype": etype, "status": "상시 채용"}
            )

    def test_open_fulltime_is_searchable(self):
        assert is_searchable(
            {"title": "백엔드 엔지니어", "job": "소프트웨어 엔지니어링", "etype": "정규직", "status": "상시 채용"}
        )


class TestKeywords:
    def test_every_segment_declares_every_tier(self):
        for segment, entry in SEGMENT_KEYWORDS.items():
            assert set(entry) == set(TIERS), f"{segment} tiers: {sorted(entry)}"

    def test_sourceable_segments_carry_both_korean_and_english(self):
        # 사장님 규칙 — 국문·영문을 모두 넣는다. 한 언어만이면 절반이 누락된다.
        sourceable = {
            p["segment"] for p in segment_positions(SNAPSHOT["positions"]) if p["searchable"]
        }
        assert sourceable, "snapshot produced no searchable segments"
        for segment in sourceable:
            words = terms(segment)
            has_korean = any(any("가" <= ch <= "힣" for ch in w) for w in words)
            has_ascii = any(w.isascii() for w in words)
            assert has_korean, f"{segment} has no Korean keyword"
            assert has_ascii, f"{segment} has no English keyword"

    def test_terms_are_deduplicated(self):
        for segment in SEGMENT_KEYWORDS:
            words = terms(segment)
            assert len(words) == len(set(words)), f"{segment} has duplicate terms"


class TestSnapshot:
    def test_snapshot_has_unique_posting_ids(self):
        ids = [p["posting_id"] for p in SNAPSHOT["positions"]]
        assert len(ids) == len(set(ids))

    def test_full_snapshot_segments_without_crashing(self):
        annotated = segment_positions(SNAPSHOT["positions"])
        assert len(annotated) == len(SNAPSHOT["positions"])
        assert all(p["segment"] for p in annotated)
