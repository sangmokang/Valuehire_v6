import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from compose_mail import LABEL, RECIPIENTS, compose, subject_for  # noqa: E402

RESULTS = {
    "company": "코드잇",
    "position": "백엔드 엔지니어",
    "search_axes": "Spring/Kotlin 백엔드, 대용량 트래픽, MSA",
    "channels": "사람인 인재풀",
    "keyword_note": "국문 34 + 영문 40",
    "context": ["에듀테크 부트캠프 운영사", "정규직 3~10년"],
    "insight": ["에듀테크 백엔드 풀은 좁다"],
    "evidence": ["search_jobs#596", "page_snapshots 10건"],
    "candidates": [
        {
            "name": "홍길동",
            "match": 88,
            "current": "A사 / 백엔드 엔지니어",
            "location": "서울",
            "education": "연세대학교 컴퓨터과학",
            "sources": ["사람인: https://www.saramin.co.kr/zf_user/profile/1"],
            "career_summary": ["Spring Boot 기반 결제 서버", "MSA 전환 주도"],
            "why_match": ["JD 핵심 스택 일치"],
            "risks": ["에듀테크 도메인 경험 없음"],
            "score_breakdown": {"keyword_fit_40": 36, "school_25": 22, "stability_20": 20, "preferred_15": 10},
        }
    ],
}


class TestSubject:
    def test_starts_with_the_required_prefix(self):
        assert subject_for("코드잇", "백엔드 엔지니어", 3).startswith("[aisearch]Claude-win")

    def test_carries_company_position_and_count(self):
        subject = subject_for("코드잇", "백엔드 엔지니어", 3)
        assert "코드잇" in subject and "백엔드 엔지니어" in subject and "3 candidates" in subject


class TestCompose:
    def test_recipients_and_label(self):
        mail = compose(RESULTS)
        assert mail["to"] == list(RECIPIENTS)
        assert len(mail["to"]) == 4
        assert mail["label"] == LABEL

    def test_body_is_listing_not_a_table(self):
        # 사장님 규칙 — 표 금지. 마크다운 표 구분선이 나오면 실패.
        body = compose(RESULTS)["body"]
        assert "|---" not in body
        assert "| ---" not in body
        assert not any(line.strip().startswith("|") for line in body.splitlines())

    def test_candidate_block_has_the_house_sections(self):
        body = compose(RESULTS)["body"]
        for heading in ("Sources:", "Career Summary:", "Why Match:", "Risks / Gaps:"):
            assert heading in body
        assert "## 1. 홍길동 — 88% Match" in body

    def test_empty_shortlist_says_so_instead_of_pretending(self):
        mail = compose({**RESULTS, "candidates": [], "no_candidate_reason": "기업회원 인증 차단"})
        assert "0 candidates" in mail["subject"]
        assert "등록 문턱(60점)을 넘은 후보 없음" in mail["body"]
        assert "기업회원 인증 차단" in mail["body"]

    def test_score_breakdown_is_reported_as_code_computed(self):
        body = compose(RESULTS)["body"]
        assert "코드 계산" in body
