"""HS-13.01 — 브리프 타입이 잘못된 입력을 생성 시점(fail-fast)에 거부하는지 확인한다."""

from __future__ import annotations

import hashlib
import re
from dataclasses import FrozenInstanceError
from datetime import date
from pathlib import Path
from typing import Any

import pytest
from hypothesis import given
from hypothesis import strategies as st

from humansearch.brief import (
    BriefInputError,
    CandidateEvidence,
    CandidateLead,
    Claim,
    CompanyBrief,
    ConnectionDegree,
    EmailContact,
    ExecProfile,
    JdPacket,
    JdSource,
    PositionSpec,
    ScoreBreakdown,
    SearchPacket,
    SourceRef,
    TeamMail,
)

TODAY = date(2026, 9, 10)
JD_TEXT = "핵심 업무: 검색 파이프라인 설계\n자격 요건: Python 5년\n우대 사항: 랭킹 경험"
JD_SHA = hashlib.sha256(JD_TEXT.encode("utf-8")).hexdigest()
LEAD_URL = "https://www.linkedin.com/in/example-0001"
SECOND_URL = "https://kr.linkedin.com/in/example-0002"
EXEC_URL = "https://www.linkedin.com/in/example-0003"
PACKET_ID = f"86exampleid-{JD_SHA[:8]}"
MAIL_BODY = "예시고객사 검색 엔지니어 | 밸류커넥트 내부 공유\n작성·확인 기준일: 2026년 9월 10일\n"


def _source_refs() -> tuple[SourceRef, ...]:
    return (
        SourceRef(id="C1", url="https://example.com/company", title="회사 개요", checked_on=TODAY),
        SourceRef(id="U1", url="https://example.com/jd", title="JD 원문", checked_on=TODAY),
        SourceRef(id="L1", url=EXEC_URL, title="공개 프로필", checked_on=TODAY),
    )


def _claim(value: str = "예시 값", source_ids: tuple[str, ...] = ("C1",)) -> Claim:
    return Claim(value=value, source_ids=source_ids)


def _exec(**overrides: Any) -> ExecProfile:
    fields: dict[str, Any] = {
        "name_role": "예시 대표 | CEO",
        "linkedin_url": EXEC_URL,
        "summary": _claim("검색 도메인 15년", ("L1",)),
    }
    fields.update(overrides)
    return ExecProfile(**fields)


def _company(**overrides: Any) -> CompanyBrief:
    fields: dict[str, Any] = {
        "legal_name": _claim("주식회사 예시", ("C1",)),
        "founded": _claim("2016년", ("C1",)),
        "ceo": None,
        "headquarters": _claim("서울", ("C1",)),
        "headcount": None,
        "revenue": None,
        "operating_profit": None,
        "funding_stage": None,
        "funding_total": None,
        "products": (_claim("예시 검색 서비스", ("C1",)),),
        "history": (_claim("2016년 법인 설립", ("C1",)),),
        "news": (_claim("예시 뉴스 한 줄", ("U1",)),),
        "youtube": (),
        "c_level": (_exec(),),
        "sources": _source_refs(),
    }
    fields.update(overrides)
    return CompanyBrief(**fields)


def _position(**overrides: Any) -> PositionSpec:
    fields: dict[str, Any] = {
        "clickup_task_id": "86exampleid",
        "client_name": "예시고객사",
        "title": "검색 엔지니어",
        "department": None,
        "employment_type": "정규직",
        "location": "서울",
        "recruiting_window": None,
    }
    fields.update(overrides)
    return PositionSpec(**fields)


def _jd(**overrides: Any) -> JdSource:
    text = overrides.pop("text", JD_TEXT)
    fields: dict[str, Any] = {
        "text": text,
        "raw_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "provided_by": "U1",
    }
    fields.update(overrides)
    return JdSource(**fields)


def _evidence(**overrides: Any) -> CandidateEvidence:
    fields: dict[str, Any] = {
        "role_match_terms": ("검색", "랭킹"),
        "jd_required_terms_hit": 3,
        "jd_required_terms_total": 4,
        "highest_education": "석사",
        "school_tier": 2,
        "tenure_months_per_job": (36, 28),
        "jobs_last_5y": 2,
        "profile_fields_filled": 7,
        "profile_fields_total": 9,
    }
    fields.update(overrides)
    return CandidateEvidence(**fields)


def _score(**overrides: Any) -> ScoreBreakdown:
    fields: dict[str, Any] = {"role": 32, "education": 15, "stability": 16, "profile": 14}
    fields.update(overrides)
    return ScoreBreakdown(**fields)


def _email(**overrides: Any) -> EmailContact:
    fields: dict[str, Any] = {
        "address": "holder@example.com",
        "source_url": "https://example.com/lab/members",
        "provenance": "연구실 공개 페이지 구성원 목록",
    }
    fields.update(overrides)
    return EmailContact(**fields)


def _lead(**overrides: Any) -> CandidateLead:
    fields: dict[str, Any] = {
        "display_name": "예시 후보 A",
        "headline": "Search Engineer at 예시테크",
        "linkedin_url": LEAD_URL,
        "education": "예시대학교 컴퓨터공학 석사",
        "career": "예시테크 3년 / 예시랩 2년",
        "match_reasons": ("검색 랭킹 실무 3년",),
        "check_points": ("실제 담당 범위 확인 필요",),
        "evidence": _evidence(),
        "score": _score(),
        "email": _email(),
        "degree": ConnectionDegree.UNKNOWN,
        "source_note": "공개 프로필 헤드라인·근무 이력으로 동명이인 배제",
    }
    fields.update(overrides)
    return CandidateLead(**fields)


def _jd_packet(**overrides: Any) -> JdPacket:
    fields: dict[str, Any] = {
        "gmail_body": JD_TEXT,
        "linkedin_body": f"[복사 시작]\n{JD_TEXT}\n[복사 끝]",
        "two_field_company": "예시고객사는 검색 제품을 만드는 회사입니다.",
        "two_field_jd": JD_TEXT,
    }
    fields.update(overrides)
    return JdPacket(**fields)


def _mail(**overrides: Any) -> TeamMail:
    body = overrides.pop("body", MAIL_BODY)
    fields: dict[str, Any] = {
        "subject": "[포지션]예시고객사, 검색 엔지니어",
        "to": ("holder@valueconnect.kr",),
        "cc": ("holder2@valueconnect.kr",),
        "body": body,
        "body_sha256": hashlib.sha256(body.encode("utf-8")).hexdigest(),
    }
    fields.update(overrides)
    return TeamMail(**fields)


def _packet(**overrides: Any) -> SearchPacket:
    fields: dict[str, Any] = {
        "packet_id": PACKET_ID,
        "position": _position(),
        "jd": _jd(),
        "company": _company(),
        "jd_packet": _jd_packet(),
        "candidates": (_lead(),),
        "mail": _mail(),
        "boolean_queries": (
            '("search" OR "검색") AND "Python"',
            '("search ranking") AND ("Python" OR "Go") NOT "intern"',
            '"검색" OR "추천"',
        ),
        "inmails": ((LEAD_URL, "안녕하세요, 예시고객사 검색 엔지니어 포지션 제안입니다."),),
    }
    fields.update(overrides)
    return SearchPacket(**fields)


# --- 1. 양성 경로 --------------------------------------------------------------


def test_builds_a_valid_search_packet() -> None:
    packet = _packet()
    assert packet.packet_id == PACKET_ID
    assert packet.candidates[0].linkedin_url == LEAD_URL
    assert packet.mail.body_sha256 == hashlib.sha256(MAIL_BODY.encode("utf-8")).hexdigest()
    assert packet.company.sources[0].id == "C1"


def test_types_are_frozen() -> None:
    ref = _source_refs()[0]
    with pytest.raises(FrozenInstanceError):
        ref.id = "C2"  # type: ignore[misc]


# --- 2. 출처·클레임 ------------------------------------------------------------


def test_claim_without_sources_is_rejected() -> None:
    with pytest.raises(BriefInputError):
        Claim(value="출처 없는 값", source_ids=())


def test_company_brief_rejects_claim_with_undefined_source_id() -> None:
    with pytest.raises(BriefInputError):
        _company(legal_name=_claim("주식회사 예시", ("Z9",)))


def test_company_brief_rejects_undefined_source_id_in_nested_tuple() -> None:
    with pytest.raises(BriefInputError):
        _company(news=(_claim("예시 뉴스", ("Q1",)),))


def test_company_brief_rejects_undefined_source_id_in_exec_summary() -> None:
    with pytest.raises(BriefInputError):
        _company(c_level=(_exec(summary=_claim("요약", ("X1",))),))


def test_company_brief_rejects_duplicate_source_ids() -> None:
    duplicated = _source_refs() + (
        SourceRef(id="C1", url="https://example.com/other", title="중복", checked_on=TODAY),
    )
    with pytest.raises(BriefInputError):
        _company(sources=duplicated)


@pytest.mark.parametrize("bad_id", ["", "c1", "C", "C1234", "CCC1", "C-1", "1C"])
def test_source_ref_rejects_malformed_id(bad_id: str) -> None:
    with pytest.raises(BriefInputError):
        SourceRef(id=bad_id, url="https://example.com/x", title="제목", checked_on=TODAY)


@pytest.mark.parametrize(
    "bad_url", ["", "example.com", "ftp://example.com", "//example.com", "javascript:alert(1)"]
)
def test_source_ref_rejects_non_http_url(bad_url: str) -> None:
    with pytest.raises(BriefInputError):
        SourceRef(id="C1", url=bad_url, title="제목", checked_on=TODAY)


# --- 3. JD 원문 ----------------------------------------------------------------


@pytest.mark.parametrize("blank", ["", "   ", "\n\t "])
def test_jd_source_rejects_blank_text(blank: str) -> None:
    with pytest.raises(BriefInputError):
        _jd(text=blank)


@pytest.mark.parametrize(
    "tagged",
    [
        "<p>핵심 업무</p>",
        "핵심 업무\n</div>",
        "<!-- 주석 -->핵심 업무",
        "핵심 업무 <BR>",
    ],
)
def test_jd_source_rejects_residual_html(tagged: str) -> None:
    with pytest.raises(BriefInputError):
        _jd(text=tagged)


def test_jd_source_keeps_plain_angle_brackets() -> None:
    jd = _jd(text="자격 요건: 응답 지연 < 100ms 유지 경험")
    assert "< 100ms" in jd.text


@pytest.mark.parametrize(
    "bad_sha",
    ["", "abc", JD_SHA.upper(), JD_SHA[:63], JD_SHA + "0", "g" * 64],
)
def test_jd_source_rejects_malformed_sha256(bad_sha: str) -> None:
    with pytest.raises(BriefInputError):
        _jd(raw_sha256=bad_sha)


# --- 4. 후보 URL ---------------------------------------------------------------


@pytest.mark.parametrize(
    "bad_url",
    [
        "",
        "   ",
        "http://www.linkedin.com/in/example-0001",
        "https://www.linkedin.com/company/example",
        "https://example.com/in/example-0001",
        "https://www.linkedin.com/in/",
        "https://linkedin.com.evil.example/in/example",
        "www.linkedin.com/in/example-0001",
    ],
)
def test_candidate_lead_rejects_non_profile_urls(bad_url: str) -> None:
    with pytest.raises(BriefInputError):
        _lead(linkedin_url=bad_url)


@pytest.mark.parametrize(
    "good_url",
    [
        "https://www.linkedin.com/in/example-0001",
        "https://kr.linkedin.com/in/example-0002",
        "https://linkedin.com/in/example-0003",
    ],
)
def test_candidate_lead_accepts_profile_urls(good_url: str) -> None:
    assert _lead(linkedin_url=good_url).linkedin_url == good_url


_LINKEDIN_PROFILE = re.compile(r"https://(?:www\.|kr\.)?linkedin\.com/in/\S+")
_URL_PREFIXES = (
    "",
    "https://www.linkedin.com/in/",
    "https://kr.linkedin.com/in/",
    "https://linkedin.com/in/",
    "http://www.linkedin.com/in/",
    "https://www.linkedin.com/company/",
    "https://www.linkedin.cn/in/",
    "https://example.com/in/",
    "linkedin.com/in/",
)


@given(prefix=st.sampled_from(_URL_PREFIXES), suffix=st.text(max_size=12))
def test_property_only_linkedin_profile_urls_are_accepted(prefix: str, suffix: str) -> None:
    candidate_url = prefix + suffix
    if _LINKEDIN_PROFILE.fullmatch(candidate_url):
        assert _lead(linkedin_url=candidate_url).linkedin_url == candidate_url
        return
    with pytest.raises(BriefInputError):
        _lead(linkedin_url=candidate_url)


@given(raw=st.text(max_size=40))
def test_property_arbitrary_text_urls_are_rejected(raw: str) -> None:
    if _LINKEDIN_PROFILE.fullmatch(raw):
        return
    with pytest.raises(BriefInputError):
        _lead(linkedin_url=raw)


# --- 5. 이메일 연락처 ----------------------------------------------------------


@pytest.mark.parametrize(
    "bad_address",
    ["", "holder", "holder@example", "holder example@example.com", "a@b@example.com", "@example.com"],
)
def test_email_contact_rejects_malformed_address(bad_address: str) -> None:
    with pytest.raises(BriefInputError):
        _email(address=bad_address)


@pytest.mark.parametrize("bad_source", ["", "example.com/lab", "mailto:holder@example.com"])
def test_email_contact_requires_http_source_url(bad_source: str) -> None:
    with pytest.raises(BriefInputError):
        _email(source_url=bad_source)


@pytest.mark.parametrize("blank", ["", "  "])
def test_email_contact_requires_provenance(blank: str) -> None:
    with pytest.raises(BriefInputError):
        _email(provenance=blank)


# --- 6. 채점 ------------------------------------------------------------------


def test_score_breakdown_total_is_the_sum() -> None:
    assert _score().total == 32 + 15 + 16 + 14


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("role", -1),
        ("role", 41),
        ("education", -1),
        ("education", 21),
        ("stability", -1),
        ("stability", 21),
        ("profile", -1),
        ("profile", 21),
    ],
)
def test_score_breakdown_rejects_out_of_range_axis(field_name: str, value: int) -> None:
    with pytest.raises(BriefInputError):
        _score(**{field_name: value})


def test_score_breakdown_rejects_non_integer_axis() -> None:
    with pytest.raises(BriefInputError):
        _score(role=32.5)


@given(
    role=st.integers(min_value=-60, max_value=90),
    education=st.integers(min_value=-60, max_value=60),
    stability=st.integers(min_value=-60, max_value=60),
    profile=st.integers(min_value=-60, max_value=60),
)
def test_property_score_breakdown_range_and_total(
    role: int, education: int, stability: int, profile: int
) -> None:
    in_range = (
        0 <= role <= 40 and 0 <= education <= 20 and 0 <= stability <= 20 and 0 <= profile <= 20
    )
    if in_range:
        breakdown = ScoreBreakdown(
            role=role, education=education, stability=stability, profile=profile
        )
        assert breakdown.total == role + education + stability + profile
        assert 0 <= breakdown.total <= 100
        return
    with pytest.raises(BriefInputError):
        ScoreBreakdown(role=role, education=education, stability=stability, profile=profile)


# --- 7. 후보 근거 --------------------------------------------------------------


def test_candidate_evidence_rejects_hit_over_total() -> None:
    with pytest.raises(BriefInputError):
        _evidence(jd_required_terms_hit=5, jd_required_terms_total=4)


def test_candidate_evidence_rejects_filled_over_total() -> None:
    with pytest.raises(BriefInputError):
        _evidence(profile_fields_filled=10, profile_fields_total=9)


@pytest.mark.parametrize("bad_tier", [0, 5, -1])
def test_candidate_evidence_rejects_school_tier_outside_contract(bad_tier: int) -> None:
    with pytest.raises(BriefInputError):
        _evidence(school_tier=bad_tier)


def test_candidate_evidence_allows_unknown_school_tier() -> None:
    assert _evidence(school_tier=None, highest_education=None).school_tier is None


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("jd_required_terms_hit", -1),
        ("jd_required_terms_total", -1),
        ("jobs_last_5y", -1),
        ("profile_fields_filled", -1),
        ("profile_fields_total", -1),
    ],
)
def test_candidate_evidence_rejects_negative_counts(field_name: str, value: int) -> None:
    with pytest.raises(BriefInputError):
        _evidence(**{field_name: value})


def test_candidate_evidence_rejects_negative_tenure_entry() -> None:
    with pytest.raises(BriefInputError):
        _evidence(tenure_months_per_job=(36, -2))


# --- 8. JD 패킷 (D4 1,899자) ---------------------------------------------------


def test_jd_packet_accepts_1899_code_points() -> None:
    body = "가" * 1899
    assert len(_jd_packet(linkedin_body=body).linkedin_body) == 1899


def test_jd_packet_rejects_1900_code_points() -> None:
    with pytest.raises(BriefInputError):
        _jd_packet(linkedin_body="가" * 1900)


def test_jd_packet_counts_newlines_toward_the_limit() -> None:
    with pytest.raises(BriefInputError):
        _jd_packet(linkedin_body="가" * 1890 + "\n" * 10)


@pytest.mark.parametrize(
    "field_name", ["gmail_body", "linkedin_body", "two_field_company", "two_field_jd"]
)
def test_jd_packet_rejects_blank_body(field_name: str) -> None:
    with pytest.raises(BriefInputError):
        _jd_packet(**{field_name: "   \n"})


# --- 9. 팀 메일 ---------------------------------------------------------------


def test_team_mail_requires_at_least_one_recipient() -> None:
    with pytest.raises(BriefInputError):
        _mail(to=())


def test_team_mail_rejects_duplicate_address_across_to_and_cc() -> None:
    with pytest.raises(BriefInputError):
        _mail(to=("holder@valueconnect.kr",), cc=("holder@valueconnect.kr",))


def test_team_mail_rejects_duplicate_address_inside_to() -> None:
    with pytest.raises(BriefInputError):
        _mail(to=("holder@valueconnect.kr", "holder@valueconnect.kr"), cc=())


@pytest.mark.parametrize(
    "foreign", ["holder@example.com", "holder@valueconnect.kr.example.com", "holder@valueconnect.co"]
)
def test_team_mail_rejects_addresses_outside_the_contract_domain(foreign: str) -> None:
    with pytest.raises(BriefInputError):
        _mail(cc=(foreign,))


def test_team_mail_rejects_body_hash_mismatch() -> None:
    with pytest.raises(BriefInputError):
        _mail(body_sha256=hashlib.sha256(b"different body").hexdigest())


def test_team_mail_rejects_truncated_body_hash() -> None:
    with pytest.raises(BriefInputError):
        _mail(body_sha256="deadbeef")


@pytest.mark.parametrize(
    "subject",
    ["예시고객사, 검색 엔지니어", "[Position]예시고객사", " [포지션]예시고객사", "[포지션 ]예시고객사"],
)
def test_team_mail_rejects_subject_outside_d3(subject: str) -> None:
    with pytest.raises(BriefInputError):
        _mail(subject=subject)


@pytest.mark.parametrize(
    "subject",
    [
        "[포지션]예시고객사, 검색 엔지니어",
        "[포지션]예시고객사, 검색 엔지니어 | ValuehireSearch",
        "[ValuehireSearch][포지션]예시고객사, 검색 엔지니어",
    ],
)
def test_team_mail_accepts_d3_subjects(subject: str) -> None:
    assert _mail(subject=subject).subject == subject


# --- 10. 서치 패킷 -------------------------------------------------------------


def test_search_packet_rejects_duplicate_candidate_urls() -> None:
    with pytest.raises(BriefInputError):
        _packet(candidates=(_lead(), _lead(display_name="예시 후보 B")))


def test_search_packet_accepts_two_distinct_candidates() -> None:
    packet = _packet(candidates=(_lead(), _lead(display_name="예시 후보 B", linkedin_url=SECOND_URL)))
    assert len(packet.candidates) == 2


def test_search_packet_rejects_inmail_for_unknown_candidate() -> None:
    with pytest.raises(BriefInputError):
        _packet(inmails=((SECOND_URL, "안녕하세요."),))


def test_search_packet_rejects_inmail_over_the_limit() -> None:
    with pytest.raises(BriefInputError):
        _packet(inmails=((LEAD_URL, "가" * 1900),))


def test_search_packet_accepts_inmail_at_the_limit() -> None:
    packet = _packet(inmails=((LEAD_URL, "가" * 1899),))
    assert len(packet.inmails[0][1]) == 1899


@pytest.mark.parametrize(
    "bad_id",
    [
        "",
        "20260910-86exampleid-deadbeef",
        f"-{JD_SHA[:8]}",
        "86exampleid-DEADBEEF",
        "86exampleid-deadbee",
        "86_example-deadbeef",
    ],
)
def test_search_packet_rejects_malformed_packet_id(bad_id: str) -> None:
    with pytest.raises(BriefInputError):
        _packet(packet_id=bad_id)


@pytest.mark.parametrize(
    "query",
    [
        '("search" AND "Python"',
        '"search" AND "Python")',
        '("search") AND "Python',
        ')("search")(',
        '(("search") AND "Python"',
    ],
)
def test_search_packet_rejects_unbalanced_boolean_query(query: str) -> None:
    with pytest.raises(BriefInputError):
        _packet(boolean_queries=(query,))


# --- 11. 정적 경계 (시계·파일·네트워크 0) ---------------------------------------


_BRIEF_DIR = Path(__file__).resolve().parents[1] / "src" / "humansearch" / "brief"


@pytest.mark.parametrize(
    "token", ["datetime.now", "date.today", "time.time", "requests", "urllib", "socket", "smtplib"]
)
def test_brief_package_has_no_clock_or_network_access(token: str) -> None:
    modules = sorted(_BRIEF_DIR.glob("*.py"))
    assert modules
    for module in modules:
        assert token not in module.read_text(encoding="utf-8"), module.name
