"""HS-13.05 — 팀 메일 제목·수신자·평문 본문 조립.

§5 mail.py·§6 출력 계약(절 순서)·§7 D2(수신자)·D3(제목)·D10(매력 포인트)·§9 HS-13.05.

fixture 는 전부 합성이다: 회사·후보 이름은 "합성 …", LinkedIn slug 는 `example-` 접두,
이메일은 `holder@example.com`. 실명·실 URL·실 이메일은 0건이며 그 사실 자체를
`scripts/acceptance-hs-1305-pii.sh` 가 저장소 전체에서 다시 판정한다.

절 순서 시험이 tautology 가 되지 않도록, 기대 절 제목 14개는 **이 파일이 따로
적어 둔 목록**이다 — 구현이 순서를 바꾸면(변이 ⓒ) 여기서 잡힌다.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import date
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

import humansearch.brief as brief_pkg
from humansearch.brief.jd_fidelity import extract_block
from humansearch.brief.linkedin_limit import check_linkedin
from humansearch.brief.mail import (
    BriefDraft,
    Recipients,
    compose_brief_mail,
    load_recipients,
    render_brief_body,
)
from humansearch.brief.types import (
    BriefInputError,
    Claim,
    CompanyBrief,
    ExecProfile,
    JdSource,
    PositionSpec,
    SourceRef,
)
from humansearch.brief.types_candidate import (
    CandidateEvidence,
    CandidateLead,
    ConnectionDegree,
    EmailContact,
    ScoreBreakdown,
)
from humansearch.brief.types_packet import JdPacket, SearchFilters

# --------------------------------------------------------------------------- 합성 fixture

TODAY = date(2026, 9, 10)
CLIENT = "합성상사"
TITLE = "검색 백엔드 엔지니어"

SOURCES = (
    SourceRef(
        id="C1",
        url="https://example.com/company",
        title="합성상사 회사 소개",
        checked_on=TODAY,
    ),
    SourceRef(id="I1", url="https://example.com/ir", title="합성상사 투자 공시", checked_on=TODAY),
    SourceRef(id="L1", url="https://example.com/news", title="합성상사 보도자료", checked_on=TODAY),
)

COMPANY = CompanyBrief(
    legal_name=Claim("합성상사 주식회사", ("C1",)),
    founded=Claim("2018년", ("C1",)),
    ceo=Claim("합성 대표", ("C1",)),
    headquarters=Claim("서울 강남", ("C1",)),
    headcount=Claim("120명", ("C1",)),
    revenue=Claim("300억 원", ("I1",)),
    operating_profit=None,
    funding_stage=Claim("시리즈 B", ("I1",)),
    funding_total=Claim("200억 원", ("I1",)),
    products=(Claim("합성 검색 엔진", ("C1",)),),
    history=(Claim("2018년 법인 설립", ("C1",)),),
    news=(Claim("2026년 신규 라인 출시", ("L1",)),),
    youtube=(Claim("합성 채널 소개 영상", ("L1",)),),
    c_level=(
        ExecProfile(
            name_role="합성 CTO",
            linkedin_url="https://www.linkedin.com/in/example-cto",
            summary=Claim("검색 플랫폼을 총괄한다", ("C1",)),
        ),
    ),
    sources=SOURCES,
)

POSITION = PositionSpec(
    clickup_task_id="86eSYNTH1",
    client_name=CLIENT,
    title=TITLE,
    department="검색플랫폼",
    employment_type="정규직",
    location="서울",
    recruiting_window="상시",
)

JD_TEXT = "주요업무\n• 검색 랭킹 모델을 설계한다.\n자격요건\n• 검색 시스템 운영 경험이 있다.\n"
JD = JdSource(
    text=JD_TEXT,
    raw_sha256=hashlib.sha256(JD_TEXT.encode("utf-8")).hexdigest(),
    provided_by="U1",
)

GMAIL_BODY = "주요업무\n• 검색 랭킹 모델을 설계한다.\n자격요건\n• 검색 시스템 운영 경험이 있다.\n"
LINKEDIN_BODY = "합성상사에서 검색 백엔드 엔지니어를 찾습니다.\n랭킹 모델 설계와 운영을 맡습니다.\n"
LINKEDIN_CHARS = len(LINKEDIN_BODY)

JD_PACKET = JdPacket(
    gmail_body=GMAIL_BODY,
    linkedin_body=LINKEDIN_BODY,
    two_field_company="합성상사는 검색 품질을 다루는 조직이다.",
    two_field_jd="주요업무\n• 검색 랭킹 모델을 설계한다.",
)

EVIDENCE = CandidateEvidence(
    role_match_terms=("검색", "랭킹"),
    jd_required_terms_hit=4,
    jd_required_terms_total=6,
    highest_education="학사",
    school_tier=2,
    tenure_months_per_job=(48,),
    jobs_last_5y=1,
    profile_fields_filled=9,
    profile_fields_total=10,
)

EMAIL = EmailContact(
    address="holder@example.com",
    source_url="https://example.com/lab-page",
    provenance="공개 연구실 페이지",
)


def _lead(index: int, *, email: EmailContact | None = None) -> CandidateLead:
    return CandidateLead(
        display_name=f"합성 후보 {index}",
        headline="합성 예시 조직 · 검색 백엔드",
        linkedin_url=f"https://www.linkedin.com/in/example-candidate-{index}",
        education="합성대학교 컴퓨터공학 학사",
        career="합성 예시 조직 4년",
        match_reasons=("검색 랭킹 운영 경험이 있다",),
        check_points=("이직 의향을 확인해야 한다",),
        evidence=EVIDENCE,
        score=ScoreBreakdown(role=32, education=15, stability=16, profile=18),
        email=email,
        degree=ConnectionDegree.UNKNOWN,
        source_note="공개 검색 스니펫에서 소속·직무 일치 확인",
    )


CANDIDATES = (_lead(1, email=EMAIL), _lead(2))
INMAILS = ((CANDIDATES[0].linkedin_url, "합성 후보 1 님께 드리는 합성 제안 본문입니다."),)

ATTRACTIONS = (
    Claim("검색 품질 조직이 독립 편성돼 있다", ("C1",)),
    Claim("시리즈 B 이후 투자금이 확보돼 있다", ("I1",)),
    Claim("최근 신규 라인을 출시했다", ("L1",)),
)

INTRO = (
    "이번 주 팀 공유용 브리프입니다. 아래 3개 채널 원고는 그대로 복사해 쓰실 수 있습니다.",
    "합성상사는 검색 품질을 직접 책임지는 조직을 만들고 있습니다. 후보자 입장에서 볼 만한 점을 먼저 적었습니다.",
)

# 이 파일이 따로 적어 둔 §6 절 제목 14개(여는 절만). 구현과 공유하지 않는다.
SECTION_TITLES = (
    "원문 반영 기준",
    "1. 일반 Gmail용 | 후보자 전달용",
    "[회사 매력 포인트]",
    "[JD 원문 시작]",
    f"2. LinkedIn RPS용 | 공백·줄바꿈 포함 {LINKEDIN_CHARS:,}자",
    "[복사 시작]",
    "3. 사람인·잡코리아용 | 2개 필드",
    "[필드 1: 회사 소개]",
    "[필드 2: JD 내용]",
    "[회사 리서치 | 2026-09-10 확인]",
    "[서치 기준]",
    "[출처 목록]",
    "[초도 LinkedIn 후보자 | 내부 검토용]",
    "[후보별 InMail 초안 | 발송 전]",
)

CONTRACT_TO = ("sangmokang@valueconnect.kr",)
CONTRACT_CC = ("rogan@valueconnect.kr", "julian@valueconnect.kr", "kcs@valueconnect.kr")


def _draft(**overrides: object) -> BriefDraft:
    fields: dict[str, object] = {
        "position": POSITION,
        "jd": JD,
        "company": COMPANY,
        "jd_packet": JD_PACKET,
        "candidates": CANDIDATES,
        "boolean_queries": ('("검색" AND "랭킹")',),
        "inmails": INMAILS,
        "search_filters": SearchFilters(),
        "intro_paragraphs": INTRO,
        "key_line": "검색 랭킹 실무 경험자를 우선 본다.",
        "reflection_notes": ("JD 원문 줄은 그대로 옮겼다", "외부 공고 조건은 넣지 않았다"),
        "attraction_points": ATTRACTIONS,
        "keywords": ("검색", "랭킹", "백엔드"),
        "interview_questions": (
            "가장 최근 개선한 랭킹 지표는 무엇인가",
            "운영 중 장애를 어떻게 잡았는가",
            "다음 커리어에서 바라는 것은 무엇인가",
        ),
        "open_items": ("영업이익 미확인",),
        "linkedin_char_count": LINKEDIN_CHARS,
        "sender_name": "강상모",
        "sender_email": "sangmokang@valueconnect.kr",
    }
    fields.update(overrides)
    return BriefDraft(**fields)  # type: ignore[arg-type]


def _recipients() -> Recipients:
    return load_recipients()


def _contract_path() -> Path:
    root = Path(__file__).resolve()
    for parent in root.parents:
        candidate = parent / "contracts" / "humansearch" / "team-recipients.json"
        if candidate.is_file():
            return candidate
    raise AssertionError("팀 수신자 계약 파일을 찾지 못했다")


# --------------------------------------------------------------------------- 양성: 제목·수신자


def test_subject_brief_form_is_exact() -> None:
    mail = compose_brief_mail(_draft(), _recipients(), TODAY, first_live=False)
    assert mail.subject == "[포지션]합성상사, 검색 백엔드 엔지니어 | ValuehireSearch"


def test_subject_search_form_is_exact() -> None:
    mail = compose_brief_mail(_draft(), _recipients(), TODAY, first_live=False, search_mode=True)
    assert mail.subject == "[ValuehireSearch][포지션]합성상사, 검색 백엔드 엔지니어 | ValuehireSearch"


def test_subject_has_no_search_suffix_without_candidates() -> None:
    draft = _draft(candidates=(), inmails=())
    mail = compose_brief_mail(draft, _recipients(), TODAY, first_live=False)
    assert mail.subject == "[포지션]합성상사, 검색 백엔드 엔지니어"


def test_first_live_sends_to_one_and_no_cc() -> None:
    mail = compose_brief_mail(_draft(), _recipients(), TODAY, first_live=True)
    assert mail.to == CONTRACT_TO
    assert len(mail.to) == 1
    assert mail.cc == ()


def test_normal_send_uses_contract_to_and_cc() -> None:
    mail = compose_brief_mail(_draft(), _recipients(), TODAY, first_live=False)
    assert mail.to == CONTRACT_TO
    assert mail.cc == CONTRACT_CC


# --------------------------------------------------------------------------- 양성: 본문


def test_body_sections_appear_in_contract_order() -> None:
    body = render_brief_body(_draft(), TODAY)
    positions = []
    for title in SECTION_TITLES:
        assert title in body, f"절 제목 없음: {title}"
        positions.append(body.index(title))
    assert positions == sorted(positions), f"절 순서가 §6 계약과 다르다: {positions}"
    assert len(positions) == 14


def test_body_header_and_separator() -> None:
    body = render_brief_body(_draft(), TODAY)
    lines = body.splitlines()
    assert lines[0] == "합성상사 검색 백엔드 엔지니어 | 밸류커넥트 내부 공유"
    assert lines[1] == "작성·확인 기준일: 2026년 9월 10일"
    separators = [line for line in lines if set(line) == {"="}]
    assert separators, "구분선이 없다"
    assert all(len(line) == 52 for line in separators)


def test_jd_block_round_trips_through_extract_block() -> None:
    body = render_brief_body(_draft(), TODAY)
    block = extract_block(body, "[JD 원문 시작]", "[JD 원문 끝]")
    assert block == GMAIL_BODY


def test_body_sha256_matches_body() -> None:
    mail = compose_brief_mail(_draft(), _recipients(), TODAY, first_live=False)
    assert mail.body_sha256 == hashlib.sha256(mail.body.encode("utf-8")).hexdigest()
    assert mail.body == render_brief_body(_draft(), TODAY)


def test_body_is_plain_text_without_html() -> None:
    body = render_brief_body(_draft(), TODAY)
    assert re.search(r"<[A-Za-z/!]", body) is None


def test_body_carries_attraction_points_with_source_ids() -> None:
    body = render_brief_body(_draft(), TODAY)
    assert "• 검색 품질 조직이 독립 편성돼 있다 [C1]" in body
    assert "- 영업이익: 미확인" in body
    assert "Email Contact: holder@example.com (출처 https://example.com/lab-page)" in body
    assert "Email Contact: 공개 이메일 미확인" in body
    assert "잠정 매칭: 81/100 (역할 32 / 학력 15 / 안정성 16 / 프로필 18)" in body
    assert "[C1] 합성상사 회사 소개 (2026-09-10) https://example.com/company" in body
    assert "지역 필터: South Korea" in body


def test_check_linkedin_length_matches_fixture_count() -> None:
    assert check_linkedin(LINKEDIN_BODY).length == LINKEDIN_CHARS


def test_public_exports_include_mail_names() -> None:
    for name in ("BriefDraft", "Recipients", "load_recipients", "render_brief_body",
                 "compose_brief_mail"):
        assert hasattr(brief_pkg, name), f"__init__ 재수출 누락: {name}"
        assert name in brief_pkg.__all__, f"__all__ 누락: {name}"
    assert list(brief_pkg.__all__) == sorted(brief_pkg.__all__)


# --------------------------------------------------------------------------- 음성: 조립 거부


def test_two_attraction_points_are_rejected() -> None:
    with pytest.raises(BriefInputError):
        _draft(attraction_points=ATTRACTIONS[:2])


def test_attraction_point_with_unknown_source_is_rejected() -> None:
    with pytest.raises(BriefInputError):
        _draft(attraction_points=(*ATTRACTIONS[:2], Claim("출처가 없는 자랑", ("Z9",))))


def test_linkedin_char_count_mismatch_is_rejected() -> None:
    with pytest.raises(BriefInputError):
        _draft(linkedin_char_count=LINKEDIN_CHARS + 1)


def test_empty_intro_paragraph_is_rejected() -> None:
    with pytest.raises(BriefInputError):
        _draft(intro_paragraphs=(INTRO[0], "   "))


def test_reflection_notes_bounds_are_enforced() -> None:
    with pytest.raises(BriefInputError):
        _draft(reflection_notes=())
    with pytest.raises(BriefInputError):
        _draft(reflection_notes=("가", "나", "다", "라", "마"))


def test_interview_question_count_is_enforced() -> None:
    with pytest.raises(BriefInputError):
        _draft(interview_questions=("하나", "둘"))


def test_sender_email_outside_team_domain_is_rejected() -> None:
    with pytest.raises(BriefInputError):
        _draft(sender_email="holder@example.com")


def test_inmail_for_unknown_candidate_is_rejected() -> None:
    with pytest.raises(BriefInputError):
        _draft(inmails=(("https://www.linkedin.com/in/example-stranger", "본문"),))


# --------------------------------------------------------------------------- 수신자 계약


def test_load_recipients_reads_the_real_contract() -> None:
    recipients = load_recipients()
    assert recipients.to == CONTRACT_TO
    assert recipients.cc == CONTRACT_CC
    assert recipients.first_live_to_only == CONTRACT_TO


def _write(tmp_path: Path, payload: object, *, raw: str | None = None) -> Path:
    target = tmp_path / "team-recipients.json"
    target.write_text(
        raw if raw is not None else json.dumps(payload, ensure_ascii=False),
        encoding="utf-8",
    )
    return target


def test_load_recipients_rejects_missing_file(tmp_path: Path) -> None:
    with pytest.raises(BriefInputError):
        load_recipients(tmp_path / "absent.json")


def test_load_recipients_rejects_broken_json(tmp_path: Path) -> None:
    with pytest.raises(BriefInputError):
        load_recipients(_write(tmp_path, None, raw="{"))


def test_load_recipients_rejects_wrong_version(tmp_path: Path) -> None:
    payload = json.loads(_contract_path().read_text(encoding="utf-8"))
    payload["version"] = 2
    with pytest.raises(BriefInputError):
        load_recipients(_write(tmp_path, payload))


def test_load_recipients_rejects_foreign_domain(tmp_path: Path) -> None:
    payload = json.loads(_contract_path().read_text(encoding="utf-8"))
    payload["cc"] = [*payload["cc"][:2], "holder@example.com"]
    with pytest.raises(BriefInputError):
        load_recipients(_write(tmp_path, payload))


def test_load_recipients_rejects_duplicate_address(tmp_path: Path) -> None:
    payload = json.loads(_contract_path().read_text(encoding="utf-8"))
    payload["cc"] = [payload["cc"][0], payload["cc"][0], payload["cc"][1]]
    with pytest.raises(BriefInputError):
        load_recipients(_write(tmp_path, payload))


def test_load_recipients_rejects_empty_to(tmp_path: Path) -> None:
    payload = json.loads(_contract_path().read_text(encoding="utf-8"))
    payload["to"] = []
    with pytest.raises(BriefInputError):
        load_recipients(_write(tmp_path, payload))


def test_load_recipients_rejects_malformed_address(tmp_path: Path) -> None:
    payload = json.loads(_contract_path().read_text(encoding="utf-8"))
    payload["to"] = ["sangmokang(at)valueconnect.kr"]
    with pytest.raises(BriefInputError):
        load_recipients(_write(tmp_path, payload))


# --------------------------------------------------------------------------- 속성 기반


@settings(max_examples=40, deadline=None)
@given(
    first=st.text(alphabet=st.characters(blacklist_characters="<>"), min_size=1, max_size=120),
    second=st.text(alphabet=st.characters(blacklist_characters="<>"), min_size=1, max_size=120),
)
def test_section_order_holds_for_arbitrary_intro(first: str, second: str) -> None:
    if not first.strip() or not second.strip():
        return
    body = render_brief_body(_draft(intro_paragraphs=(first, second)), TODAY)
    positions = [body.index(title) for title in SECTION_TITLES if title in body]
    assert len(positions) == len(SECTION_TITLES)
    assert positions == sorted(positions)
