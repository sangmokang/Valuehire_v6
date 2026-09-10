"""HS-13.01b — 브리프 운영 상수가 계약 파일 한 곳에서만 나오는지 확인한다(P22).

`contracts/humansearch/brief-policy.json` 이 유일한 소유자다. 코드가 같은 값을 다시
정의하면 두 곳이 조용히 갈라진다. 그래서 여기서는 ① 계약이 실제로 로드되는가
② 손상된 계약을 전부 거부하는가 ③ **계약값을 바꾸면 타입 검증이 실제로 따라 바뀌는가**
(= 리터럴이 아니라 정책을 읽고 있는가) 세 가지를 잰다. ③ 이 없으면 정책 파일은
장식이고 코드는 여전히 리터럴로 판정할 수 있다.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
from dataclasses import replace
from datetime import date
from pathlib import Path
from typing import Any

import pytest

from humansearch.brief import (
    BriefInputError,
    BriefPolicy,
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
    SearchFilters,
    SearchPacket,
    SourceRef,
    TeamMail,
    load_brief_policy,
    override_policy_for_tests,
    policy,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = REPO_ROOT / "contracts" / "humansearch" / "brief-policy.json"

TODAY = date(2026, 9, 10)
JD_TEXT = "핵심 업무: 검색 파이프라인 설계\n자격 요건: Python 5년"
JD_SHA = hashlib.sha256(JD_TEXT.encode("utf-8")).hexdigest()
LEAD_URL = "https://www.linkedin.com/in/example-0001"
PACKET_ID = f"20260910-86exampleid-{JD_SHA[:8]}"


# ── 계약 payload 도우미 ──────────────────────────────────────────────────────
def _payload(**overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "version": 1,
        "linkedin_inmail_max_chars": 1899,
        "subject_prefixes": ["[포지션]", "[ValuehireSearch][포지션]"],
        "subject_search_suffix": " | ValuehireSearch",
        "profile_url_prefixes": [
            "https://www.linkedin.com/in/",
            "https://kr.linkedin.com/in/",
            "https://linkedin.com/in/",
        ],
        "team_mail_domain": "valueconnect.kr",
        "clickup_position_list_id": "901814621569",
        "default_search_location": "South Korea",
    }
    base.update(overrides)
    return base


def _write(tmp_path: Path, payload: dict[str, Any]) -> Path:
    target = tmp_path / "brief-policy.json"
    target.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return target


# ── SearchPacket 최소 fixture (13.01 과 같은 모양, 값만 축약) ────────────────
def _packet(**overrides: Any) -> SearchPacket:
    sources = (
        SourceRef(id="C1", url="https://example.com/c", title="회사 개요", checked_on=TODAY),
    )
    claim = Claim(value="주식회사 예시", source_ids=("C1",))
    company = CompanyBrief(legal_name=claim, sources=sources)
    evidence = CandidateEvidence(
        role_match_terms=("검색",),
        jd_required_terms_hit=3,
        jd_required_terms_total=4,
        highest_education="석사",
        school_tier=2,
        tenure_months_per_job=(36,),
        jobs_last_5y=1,
        profile_fields_filled=7,
        profile_fields_total=9,
    )
    lead = CandidateLead(
        display_name="예시 후보 A",
        headline="Search Engineer",
        linkedin_url=LEAD_URL,
        education="예시대학교 석사",
        career="예시테크 3년",
        match_reasons=("검색 랭킹 실무 3년",),
        check_points=("담당 범위 확인",),
        evidence=evidence,
        score=ScoreBreakdown(role=32, education=15, stability=16, profile=14),
        email=EmailContact(
            address="holder@example.com",
            source_url="https://example.com/members",
            provenance="공개 구성원 목록",
        ),
        degree=ConnectionDegree.UNKNOWN,
        source_note="공개 프로필 헤드라인으로 동명이인 배제",
    )
    fields: dict[str, Any] = {
        "packet_id": PACKET_ID,
        "position": PositionSpec(
            clickup_task_id="86exampleid",
            client_name="예시고객사",
            title="검색 엔지니어",
            department=None,
            employment_type="정규직",
            location="서울",
            recruiting_window=None,
        ),
        "jd": JdSource(text=JD_TEXT, raw_sha256=JD_SHA, provided_by="U1"),
        "company": company,
        "jd_packet": _jd_packet(),
        "candidates": (lead,),
        "mail": _mail(),
        "boolean_queries": ('("검색") AND "Python"',),
        "inmails": ((LEAD_URL, "안녕하세요, 예시 후보 A 님."),),
    }
    fields.update(overrides)
    return SearchPacket(**fields)


def _jd_packet(**overrides: Any) -> JdPacket:
    fields: dict[str, Any] = {
        "gmail_body": JD_TEXT,
        "linkedin_body": JD_TEXT,
        "two_field_company": "예시고객사는 검색 제품을 만든다.",
        "two_field_jd": JD_TEXT,
    }
    fields.update(overrides)
    return JdPacket(**fields)


def _mail(**overrides: Any) -> TeamMail:
    body = overrides.pop("body", "예시고객사 검색 엔지니어 | 밸류커넥트 내부 공유\n")
    fields: dict[str, Any] = {
        "subject": "[포지션]예시고객사, 검색 엔지니어",
        "to": ("holder@valueconnect.kr",),
        "cc": (),
        "body": body,
        "body_sha256": hashlib.sha256(body.encode("utf-8")).hexdigest(),
    }
    fields.update(overrides)
    return TeamMail(**fields)


# ── 1. 실제 계약 파일이 로드된다 ────────────────────────────────────────────
def test_실제_계약_파일이_로드되고_값이_계약과_같다() -> None:
    loaded = load_brief_policy(CONTRACT_PATH)
    assert loaded.version == 1
    assert loaded.linkedin_inmail_max_chars == 1899
    assert loaded.subject_prefixes == ("[포지션]", "[ValuehireSearch][포지션]")
    assert loaded.subject_search_suffix == " | ValuehireSearch"
    assert loaded.profile_url_prefixes[0] == "https://www.linkedin.com/in/"
    assert loaded.team_mail_domain == "valueconnect.kr"
    assert loaded.clickup_position_list_id == "901814621569"
    assert loaded.default_search_location == "South Korea"


def test_인자_없는_로드는_저장소_계약을_찾아낸다(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("HUMANSEARCH_CONTRACTS_DIR", raising=False)
    assert load_brief_policy() == load_brief_policy(CONTRACT_PATH)


def test_환경변수가_가리키는_계약_디렉터리를_쓴다(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "humansearch"
    target.mkdir()
    (target / "brief-policy.json").write_text(
        json.dumps(_payload(default_search_location="Japan"), ensure_ascii=False),
        encoding="utf-8",
    )
    monkeypatch.setenv("HUMANSEARCH_CONTRACTS_DIR", str(tmp_path))
    assert load_brief_policy().default_search_location == "Japan"


# ── 2. 손상된 계약은 전부 거부한다 ──────────────────────────────────────────
def test_계약_파일이_없으면_거부한다(tmp_path: Path) -> None:
    with pytest.raises(BriefInputError):
        load_brief_policy(tmp_path / "없는파일.json")


def test_JSON_이_아니면_거부한다(tmp_path: Path) -> None:
    target = tmp_path / "brief-policy.json"
    target.write_text("{이건 JSON 이 아니다", encoding="utf-8")
    with pytest.raises(BriefInputError):
        load_brief_policy(target)


def test_version_이_1이_아니면_거부한다(tmp_path: Path) -> None:
    with pytest.raises(BriefInputError):
        load_brief_policy(_write(tmp_path, _payload(version=2)))


def test_최대_글자수가_0이하면_거부한다(tmp_path: Path) -> None:
    with pytest.raises(BriefInputError):
        load_brief_policy(_write(tmp_path, _payload(linkedin_inmail_max_chars=0)))


def test_접두_목록이_비면_거부한다(tmp_path: Path) -> None:
    with pytest.raises(BriefInputError):
        load_brief_policy(_write(tmp_path, _payload(subject_prefixes=[])))
    with pytest.raises(BriefInputError):
        load_brief_policy(_write(tmp_path, _payload(profile_url_prefixes=[])))


def test_도메인_형식이_틀리면_거부한다(tmp_path: Path) -> None:
    with pytest.raises(BriefInputError):
        load_brief_policy(_write(tmp_path, _payload(team_mail_domain="valueconnect")))
    with pytest.raises(BriefInputError):
        load_brief_policy(_write(tmp_path, _payload(team_mail_domain="@valueconnect.kr")))


def test_리스트_id_가_숫자가_아니면_거부한다(tmp_path: Path) -> None:
    with pytest.raises(BriefInputError):
        load_brief_policy(_write(tmp_path, _payload(clickup_position_list_id="90181462156a")))


# ── 3. 정책값을 바꾸면 판정이 실제로 따라 바뀐다 ────────────────────────────
def test_최대_글자수_정책이_JdPacket_경계를_실제로_움직인다() -> None:
    """max=1000 이면 1,001자는 거부·1,000자는 통과. 원복하면 1,001자가 다시 통과."""

    over = "가" * 1001
    exact = "가" * 1000
    smaller = replace(policy(), linkedin_inmail_max_chars=1000)
    with override_policy_for_tests(smaller):
        with pytest.raises(BriefInputError):
            _jd_packet(linkedin_body=over)
        assert _jd_packet(linkedin_body=exact).linkedin_body == exact
    assert _jd_packet(linkedin_body=over).linkedin_body == over


def test_기본_정책은_1899_통과_1900_거부다() -> None:
    assert _jd_packet(linkedin_body="가" * 1899).linkedin_body == "가" * 1899
    with pytest.raises(BriefInputError):
        _jd_packet(linkedin_body="가" * 1900)


def test_팀_도메인_정책이_TeamMail_수신자_판정을_실제로_움직인다() -> None:
    other = replace(policy(), team_mail_domain="example.org")
    with override_policy_for_tests(other):
        assert _mail(to=("holder@example.org",)).to == ("holder@example.org",)
        with pytest.raises(BriefInputError):
            _mail(to=("holder@valueconnect.kr",))
    assert _mail(to=("holder@valueconnect.kr",)).to == ("holder@valueconnect.kr",)


def test_프로필_접두_정책이_URL_판정을_실제로_움직인다() -> None:
    only_kr = replace(policy(), profile_url_prefixes=("https://kr.linkedin.com/in/",))
    with override_policy_for_tests(only_kr), pytest.raises(BriefInputError):
        ExecProfile(
            name_role="예시 대표 | CEO",
            linkedin_url=LEAD_URL,
            summary=Claim(value="검색 15년", source_ids=("C1",)),
        )
    assert (
        ExecProfile(
            name_role="예시 대표 | CEO",
            linkedin_url=LEAD_URL,
            summary=Claim(value="검색 15년", source_ids=("C1",)),
        ).linkedin_url
        == LEAD_URL
    )


def test_제목_접두_정책이_TeamMail_제목_판정을_실제로_움직인다() -> None:
    other = replace(policy(), subject_prefixes=("[내부]",))
    with override_policy_for_tests(other):
        assert _mail(subject="[내부]예시고객사, 검색 엔지니어").subject.startswith("[내부]")
        with pytest.raises(BriefInputError):
            _mail(subject="[포지션]예시고객사, 검색 엔지니어")


# ── 4. SearchFilters ────────────────────────────────────────────────────────
def test_SearchFilters_기본_지역은_계약값이다() -> None:
    assert SearchFilters().location == "South Korea"
    japan = replace(policy(), default_search_location="Japan")
    with override_policy_for_tests(japan):
        assert SearchFilters().location == "Japan"


def test_SearchFilters_공백_지역은_거부한다() -> None:
    with pytest.raises(BriefInputError):
        SearchFilters(location="   ")


def test_SearchFilters_연차_범위_반례를_거부한다() -> None:
    assert SearchFilters(seniority_years=(3, 8)).seniority_years == (3, 8)
    with pytest.raises(BriefInputError):
        SearchFilters(seniority_years=(9, 3))
    with pytest.raises(BriefInputError):
        SearchFilters(seniority_years=(-1, 3))


def test_SearchPacket_은_search_filters_기본값으로_생성된다() -> None:
    packet = _packet()
    assert packet.search_filters == SearchFilters()
    assert packet.search_filters.location == "South Korea"
    named = {f.name for f in dataclasses.fields(SearchPacket)}
    assert "search_filters" in named


def test_SearchPacket_은_지정한_search_filters_를_보존한다() -> None:
    filters = SearchFilters(location="Japan", seniority_years=(5, 10))
    assert _packet(search_filters=filters).search_filters is filters


# ── 5. 합본 JD 거부 (§4 합본 JD 행) ─────────────────────────────────────────
def test_JdSource_기본_포지션_수는_1이고_통과한다() -> None:
    source = JdSource(text=JD_TEXT, raw_sha256=JD_SHA, provided_by="U1")
    assert source.position_count == 1
    assert JdSource(text=JD_TEXT, raw_sha256=JD_SHA, provided_by="U1", position_count=1) == source


def test_합본_JD_는_거부한다() -> None:
    with pytest.raises(BriefInputError):
        JdSource(text=JD_TEXT, raw_sha256=JD_SHA, provided_by="U1", position_count=2)


def test_포지션_수가_0이거나_음수면_거부한다() -> None:
    for count in (0, -1):
        with pytest.raises(BriefInputError):
            JdSource(text=JD_TEXT, raw_sha256=JD_SHA, provided_by="U1", position_count=count)


# ── 6. 정책은 한 번만 로드하고 캐시한다 ────────────────────────────────────
def test_policy_는_같은_객체를_돌려준다() -> None:
    assert policy() is policy()
    assert isinstance(policy(), BriefPolicy)
