import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from compose_mail import (  # noqa: E402
    LABEL,
    RECIPIENTS,
    UnverifiedCandidate,
    compose,
    subject_for,
)

REAL_INPUT = {
    "profile_url": "https://www.saramin.co.kr/zf_user/profile/1",
    "school": "연세대학교",
    "roles": [["A사", 40], ["B사", 36]],
    "keyword_hits": ["Spring", "Kotlin", "에듀테크"],
}


def results(**overrides):
    base = {
        "company": "코드잇",
        "position": "백엔드 엔지니어",
        "required_terms": ["Spring", "Kotlin"],
        "preferred_terms": ["에듀테크"],
        "search_axes": "Spring/Kotlin 백엔드, 대용량 트래픽, MSA",
        "channels": "사람인 인재풀",
        "keyword_note": "국문 34 + 영문 40",
        "context": ["에듀테크 부트캠프 운영사"],
        "insight": ["에듀테크 백엔드 풀은 좁다"],
        "evidence": ["search_jobs#596"],
        "candidates": [{
            "name": "홍길동",
            "candidate_input": dict(REAL_INPUT),
            "current": "A사 / 백엔드 엔지니어",
            "location": "서울",
            "education": "연세대학교 컴퓨터과학",
            "sources": ["사람인: https://www.saramin.co.kr/zf_user/profile/1"],
            "career_summary": ["Spring Boot 기반 결제 서버"],
            "why_match": ["JD 핵심 스택 일치"],
            "risks": ["에듀테크 도메인 경험 없음"],
        }],
    }
    base.update(overrides)
    return base


def with_candidate(**overrides):
    data = results()
    data["candidates"][0].update(overrides)
    return data


class TestSubject:
    def test_starts_with_the_required_prefix(self):
        assert subject_for("코드잇", "백엔드 엔지니어", 3).startswith("[aisearch]Claude-win")

    def test_carries_company_position_and_count(self):
        subject = subject_for("코드잇", "백엔드 엔지니어", 3)
        assert "코드잇" in subject and "백엔드 엔지니어" in subject and "3 candidates" in subject


class TestCompose:
    def test_recipients_and_label(self):
        mail = compose(results())
        assert mail["to"] == list(RECIPIENTS)
        assert len(mail["to"]) == 4
        assert mail["label"] == LABEL

    def test_body_is_listing_not_a_table(self):
        # 사장님 규칙 — 표 금지.
        body = compose(results())["body"]
        assert "|---" not in body and "| ---" not in body
        assert not any(line.strip().startswith("|") for line in body.splitlines())

    def test_candidate_block_has_the_house_sections(self):
        body = compose(results())["body"]
        for heading in ("Sources:", "Career Summary:", "Why Match:", "Risks / Gaps:"):
            assert heading in body
        assert "## 1. 홍길동 — " in body

    def test_empty_shortlist_says_so_instead_of_pretending(self):
        mail = compose(results(candidates=[], no_candidate_reason="기업회원 인증 차단"))
        assert "0 candidates" in mail["subject"]
        assert "등록 문턱(60점)을 넘은 후보 없음" in mail["body"]
        assert "기업회원 인증 차단" in mail["body"]


class TestProvenance:
    """메일은 '코드 계산' 이라고 인쇄한다 — 그 주장을 재계산으로 보증한다."""

    def test_a_candidate_without_raw_input_is_refused(self):
        data = results()
        data["candidates"][0].pop("candidate_input")
        data["candidates"][0]["match"] = 100
        data["candidates"][0]["score_breakdown"] = {
            "keyword_fit_40": 40, "school_25": 25, "stability_20": 20, "preferred_15": 15,
        }
        with pytest.raises(UnverifiedCandidate, match="candidate_input"):
            compose(data)

    def test_a_forged_total_that_disagrees_with_the_recompute_is_refused(self):
        with pytest.raises(UnverifiedCandidate, match="재계산"):
            compose(with_candidate(match=100))

    def test_the_reported_score_is_the_recomputed_one(self):
        mail = compose(results())
        candidate = results()["candidates"][0]
        assert "candidate_input" in candidate
        line = next(l for l in mail["body"].splitlines() if l.startswith("Score:"))
        total = int(line.rsplit("총점 ", 1)[1].rstrip(")"))
        breakdown_sum = sum(
            int(part.rsplit(" ", 1)[1])
            for part in line[len("Score: "):].split(" (")[0].split(" · ")
        )
        assert total == breakdown_sum

    def test_a_freelancer_is_refused_by_the_recompute(self):
        data = with_candidate(candidate_input={**REAL_INPUT, "is_freelancer": True})
        with pytest.raises(UnverifiedCandidate, match="하드제외"):
            compose(data)

    def test_a_low_scoring_candidate_is_refused_by_the_recompute(self):
        data = with_candidate(candidate_input={**REAL_INPUT, "school": "부산대학교",
                                               "keyword_hits": []})
        with pytest.raises(UnverifiedCandidate, match="등록 문턱"):
            compose(data)

    def test_missing_required_terms_is_refused(self):
        data = results()
        data.pop("required_terms")
        with pytest.raises(UnverifiedCandidate, match="required_terms"):
            compose(data)

    def test_malformed_raw_input_is_refused(self):
        with pytest.raises(UnverifiedCandidate, match="잘못됐다"):
            compose(with_candidate(candidate_input={"school": "연세대학교"}))


class TestReview20260930:
    """빈 후보 목록을 '검색했는데 없음' 으로 둔갑시키지 않는다 (codex V1 지적)."""

    def test_empty_shortlist_without_a_reason_is_refused(self):
        with pytest.raises(ValueError):
            compose(results(candidates=[]))

    def test_a_blocked_run_is_not_reported_as_nobody_passed(self):
        mail = compose(results(candidates=[], status="blocked",
                               no_candidate_reason="사람인 기업회원 미인증"))
        assert "등록 문턱(60점)을 넘은 후보 없음" not in mail["body"]
        assert "blocked" in mail["body"]
        assert "BLOCKED" in mail["subject"]
