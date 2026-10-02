"""HS-13.05 — 팀 브리프 메일 본문의 절 렌더러 (§6 출력 계약).

`mail.py` 가 절의 **순서**를 소유하고, 이 파일은 각 절의 **모양**을 소유한다.
두 파일 다 순수 함수이며 시계·파일·네트워크 접근이 0이다(시계는 호출자가 넘긴 `date`).

미확인 값은 추정하지 않고 "미확인"으로 적는다(§4 회사 사실 행·§8 예외 표).
빈 목록도 줄을 하나 남긴다 — 아무 줄도 없으면 "확인했는데 없음"과 "확인 안 함"이
읽는 사람 눈에서 구분되지 않는다.
"""

from __future__ import annotations

from datetime import date

from .types import Claim, CompanyBrief, PositionSpec, _reject
from .types_candidate import CandidateLead, ConnectionDegree
from .types_packet import SearchFilters

__all__ = [
    "SEPARATOR",
    "render_candidates",
    "render_company_research",
    "render_gmail_channel",
    "render_header",
    "render_inmails",
    "render_linkedin_channel",
    "render_search_criteria",
    "render_sources",
    "render_two_field_channel",
]

SEPARATOR = "=" * 52
_UNKNOWN = "미확인"

_DEGREE_KO = {
    ConnectionDegree.UNKNOWN: _UNKNOWN,
    ConnectionDegree.FIRST: "1촌",
    ConnectionDegree.SECOND: "2촌",
    ConnectionDegree.THIRD_PLUS: "3촌 이상",
}


def _ids(source_ids: tuple[str, ...]) -> str:
    return ", ".join(source_ids)


def _claim_line(label: str, claim: Claim | None) -> str:
    """`- 라벨: 값 [출처]` 한 줄. 값이 없으면 추정하지 않고 미확인으로 적는다."""

    if claim is None:
        return f"- {label}: {_UNKNOWN}"
    return f"- {label}: {claim.value} [{_ids(claim.source_ids)}]"


def _claim_bullets(claims: tuple[Claim, ...]) -> list[str]:
    if not claims:
        return [f"• {_UNKNOWN}"]
    return [f"• {claim.value} [{_ids(claim.source_ids)}]" for claim in claims]


def render_header(
    position: PositionSpec,
    today: date,
    intro: str,
    key_line: str,
    reflection_notes: tuple[str, ...],
) -> list[str]:
    """머리말 — 제목 줄·기준일·인사 1문단·핵심 1줄·원문 반영 기준."""

    lines = [
        f"{position.client_name} {position.title} | 밸류커넥트 내부 공유",
        f"작성·확인 기준일: {today.year}년 {today.month}월 {today.day}일",
        "",
        intro,
        "",
        f"핵심: {key_line}",
        "",
        "원문 반영 기준",
    ]
    lines.extend(f"• {note}" for note in reflection_notes)
    return lines


def render_gmail_channel(
    intro: str,
    attraction_points: tuple[Claim, ...],
    gmail_body: str,
    sender_name: str,
    sender_email: str,
) -> list[str]:
    """1절 — 후보자 관점 소개 2문단째 + 매력 포인트 + JD 원문 블록 + 서명."""

    lines = ["1. 일반 Gmail용 | 후보자 전달용", "", intro, "", "[회사 매력 포인트]"]
    lines.extend(f"• {point.value} [{_ids(point.source_ids)}]" for point in attraction_points)
    lines.append("")
    lines.append("[JD 원문 시작]")
    lines.extend(gmail_body.splitlines())
    lines.append("[JD 원문 끝]")
    lines.append("")
    lines.append(sender_name)
    lines.append(sender_email)
    return lines


def render_linkedin_channel(linkedin_body: str, char_count: int) -> list[str]:
    """2절 — RPS InMail 복사 블록. 글자 수는 호출자가 잰 값을 그대로 적는다."""

    lines = [f"2. LinkedIn RPS용 | 공백·줄바꿈 포함 {char_count:,}자", "", "[복사 시작]"]
    lines.extend(linkedin_body.splitlines())
    lines.append("[복사 끝]")
    return lines


def render_two_field_channel(company_field: str, jd_field: str) -> list[str]:
    """3절 — 사람인·잡코리아 2필드."""

    lines = ["3. 사람인·잡코리아용 | 2개 필드", "", "[필드 1: 회사 소개]"]
    lines.extend(company_field.splitlines())
    lines.append("")
    lines.append("[필드 2: JD 내용]")
    lines.extend(jd_field.splitlines())
    return lines


def render_company_research(
    company: CompanyBrief,
    open_items: tuple[str, ...],
    today: date,
) -> list[str]:
    """[회사 리서치] 절 — 1~8번 소절 순서는 §6 계약 그대로다."""

    lines = [f"[회사 리서치 | {today.isoformat()} 확인]"]
    lines.append("1. 개요·근무지·인원")
    lines.append(_claim_line("법인명", company.legal_name))
    lines.append(_claim_line("설립", company.founded))
    lines.append(_claim_line("본사", company.headquarters))
    lines.append(_claim_line("인원", company.headcount))
    lines.append("2. 매출·영업이익·투자")
    lines.append(_claim_line("매출", company.revenue))
    lines.append(_claim_line("영업이익", company.operating_profit))
    lines.append(_claim_line("투자 단계", company.funding_stage))
    lines.append(_claim_line("누적 투자금", company.funding_total))
    lines.append("3. 연혁")
    lines.extend(_claim_bullets(company.history))
    lines.append("4. 제품")
    lines.extend(_claim_bullets(company.products))
    lines.append("5. 최근 뉴스")
    lines.extend(_claim_bullets(company.news))
    lines.append("6. 대표·C레벨")
    lines.append(_claim_line("대표", company.ceo))
    if not company.c_level:
        lines.append(f"- C레벨: {_UNKNOWN}")
    for profile in company.c_level:
        summary = profile.summary
        lines.append(f"- {profile.name_role}: {summary.value} [{_ids(summary.source_ids)}]")
        lines.append(f"  LinkedIn: {profile.linkedin_url or _UNKNOWN}")
    lines.append("7. YouTube")
    lines.extend(_claim_bullets(company.youtube))
    lines.append("8. 확인할 항목")
    lines.extend([f"• {item}" for item in open_items] or [f"• {_UNKNOWN}"])
    return lines


def render_search_criteria(
    filters: SearchFilters,
    keywords: tuple[str, ...],
    boolean_queries: tuple[str, ...],
    interview_questions: tuple[str, ...],
) -> list[str]:
    """[서치 기준] 절 — 러너가 RPS 좌측 필터·검색창에 그대로 옮길 값."""

    lines = ["[서치 기준]"]
    lines.append(f"지역 필터: {filters.location}")
    lines.append(f"키워드: {', '.join(keywords) if keywords else _UNKNOWN}")
    lines.append("LinkedIn 검색식:")
    lines.extend([f"- {query}" for query in boolean_queries] or [f"- {_UNKNOWN}"])
    lines.append("초도 인터뷰 질문:")
    lines.extend(f"{index}. {question}" for index, question in enumerate(interview_questions, 1))
    return lines


def render_sources(company: CompanyBrief) -> list[str]:
    """[출처 목록] 절 — 본문 안 `[C1]` 표기가 가리키는 곳."""

    lines = ["[출처 목록]"]
    if not company.sources:
        lines.append(f"({_UNKNOWN})")
    lines.extend(
        f"[{ref.id}] {ref.title} ({ref.checked_on.isoformat()}) {ref.url}"
        for ref in company.sources
    )
    return lines


def render_candidates(candidates: tuple[CandidateLead, ...]) -> list[str]:
    """[초도 LinkedIn 후보자] 절 — 내부 검토용, 발송 대상이 아니다."""

    lines = ["[초도 LinkedIn 후보자 | 내부 검토용]"]
    if not candidates:
        lines.append("(초도 후보 없음)")
    for number, lead in enumerate(candidates, 1):
        score = lead.score
        lines.append(f"{number}. {lead.display_name} | {lead.headline}")
        lines.append(f"LinkedIn: {lead.linkedin_url}")
        lines.append(
            f"잠정 매칭: {score.total}/100 (역할 {score.role} / 학력 {score.education}"
            f" / 안정성 {score.stability} / 프로필 {score.profile})"
        )
        lines.append(f"학력: {lead.education}")
        lines.append(f"경력: {lead.career}")
        lines.append("매칭 이유:")
        lines.extend(f"• {reason}" for reason in lead.match_reasons)
        lines.append("확인할 부분:")
        lines.extend(f"• {point}" for point in lead.check_points)
        if lead.email is None:
            lines.append(f"Email Contact: 공개 이메일 {_UNKNOWN}")
        else:
            lines.append(f"Email Contact: {lead.email.address} (출처 {lead.email.source_url})")
        lines.append(f"1촌 여부: {_DEGREE_KO[lead.degree]}")
        lines.append(f"근거: {lead.source_note}")
        lines.append("")
    return lines


def render_inmails(
    inmails: tuple[tuple[str, str], ...],
    candidates: tuple[CandidateLead, ...],
) -> list[str]:
    """[후보별 InMail 초안] 절 — 발송은 하지 않는다(D0 §4)."""

    names = {lead.linkedin_url: lead.display_name for lead in candidates}
    lines = ["[후보별 InMail 초안 | 발송 전]"]
    if not inmails:
        lines.append("(InMail 초안 없음)")
    for url, body in inmails:
        name = names.get(url)
        if name is None:
            _reject(f"InMail 초안의 후보가 후보 목록에 없다: {url}")
        lines.append(f"--- {name} ({url}) ---")
        lines.extend(body.splitlines())
        lines.append("")
    return lines
