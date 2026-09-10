"""HS-13 브리프 패킷의 산출물 값 타입 — 채널별 JD·팀 메일·서치 패킷.

§7 D3(제목)·D4(본문 상한)와 §4 수신자·본문 길이 행을 생성 시점에 강제한다.
상한값·도메인·접두는 전부 `policy()` 가 계약 파일에서 읽어 온다(P22).
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from dataclasses import field as dataclass_field
from datetime import date, datetime

from .jd_fidelity import FidelityReport, content_lines, verify_fidelity
from .linkedin_limit import verify_linkedin_fidelity
from .policy import policy
from .recipients import load_recipients
from .two_field import split_two_field
from .types import (
    CompanyBrief,
    JdSource,
    PositionSpec,
    _reject,
    _require_count,
    _require_email,
    _require_sha256,
    _require_text,
)
from .types_candidate import CandidateLead

__all__ = ["JdPacket", "SearchFilters", "SearchPacket", "TeamMail"]

# D4 본문 상한·D3 제목 접두·팀 메일 도메인은 전부 계약 파일이 소유한다(P22).
# 코드에 같은 숫자를 다시 적으면 계약과 코드가 조용히 갈라진다.
# packet_id 에는 날짜가 없다(HS-13.09c) — 자정을 넘겨 같은 포지션·같은 JD 로 다시 만들어도
# 같은 값이어야 발송 장부(D9)가 파일 이름으로 재발송을 막는다. 날짜는 `created_on` 이 따로 남긴다.
_PACKET_ID = re.compile(r"^[A-Za-z0-9]+-[0-9a-f]{8}$")


def _require_within_limit(body: str, field: str) -> None:
    limit = policy().linkedin_inmail_max_chars
    if len(body) > limit:
        _reject(f"{field} 가 {limit}자를 넘는다: {len(body)}자")


def _require_balanced_query(query: str, index: int) -> None:
    if query.count('"') % 2 != 0:
        _reject(f"boolean_queries[{index}] 의 큰따옴표 짝이 맞지 않는다")
    depth = 0
    for char in query:
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth < 0:
                _reject(f"boolean_queries[{index}] 의 괄호가 열리기 전에 닫힌다")
    if depth != 0:
        _reject(f"boolean_queries[{index}] 의 괄호가 닫히지 않았다")


@dataclass(frozen=True)
class JdPacket:
    """채널별 JD 3종(Gmail·LinkedIn·2필드)."""

    gmail_body: str
    linkedin_body: str
    two_field_company: str
    two_field_jd: str
    two_field_sections: tuple[
        str, ...
    ]  # 필드 2 에 담은 JD 절(마커, JD 순서) — SearchPacket 이 재계산해 대조
    linkedin_omitted_sections: tuple[str, ...]  # LinkedIn 판에서 생략한 절 — 그 밖의 누락은 거부

    def __post_init__(self) -> None:
        if not self.two_field_sections:
            _reject(
                "JdPacket.two_field_sections 는 1개 이상이어야 한다(필드 2 가 어느 절을 담았는지 없이는 판정 불가)"
            )
        for label, names in (
            ("two_field_sections", self.two_field_sections),
            ("linkedin_omitted_sections", self.linkedin_omitted_sections),
        ):
            for name in names:
                _require_text(name, f"JdPacket.{label}[]")
        bodies = (
            ("gmail_body", self.gmail_body),
            ("linkedin_body", self.linkedin_body),
            ("two_field_company", self.two_field_company),
            ("two_field_jd", self.two_field_jd),
        )
        for label, body in bodies:
            _require_text(body, f"JdPacket.{label}")
        _require_within_limit(self.linkedin_body, "JdPacket.linkedin_body")


@dataclass(frozen=True)
class TeamMail:
    """팀 내부 공유 메일 한 통. 본문 해시로 발송 readback 과 대조한다."""

    subject: str
    to: tuple[str, ...]
    cc: tuple[str, ...]
    body: str
    body_sha256: str

    def __post_init__(self) -> None:
        if not self.subject.startswith(policy().subject_prefixes):
            _reject("TeamMail.subject 는 D3 제목 형식으로 시작해야 한다")
        if not self.to:
            _reject("TeamMail.to 는 1명 이상이어야 한다")
        seen: set[str] = set()
        team_domain = f"@{policy().team_mail_domain}"
        contract = load_recipients()
        members = frozenset((*contract.to, *contract.cc))
        for label, addresses in (("to", self.to), ("cc", self.cc)):
            for address in addresses:
                _require_email(address, f"TeamMail.{label}")
                if not address.endswith(team_domain):
                    _reject(f"TeamMail.{label} 에 계약 도메인 밖 주소가 있다")
                if address not in members:
                    # 같은 도메인이라도 team-recipients.json 밖 계정이면 후보 PII 가 계약 밖으로 나간다(Codex 10차)
                    _reject(
                        f"TeamMail.{label} 에 팀 수신자 계약(team-recipients.json) 밖 주소가 있다"
                    )
                if address in seen:
                    _reject(f"TeamMail.{label} 에 중복 주소가 있다")
                seen.add(address)
        _require_text(self.body, "TeamMail.body")
        _require_sha256(self.body_sha256, "TeamMail.body_sha256")
        if self.body_sha256 != hashlib.sha256(self.body.encode("utf-8")).hexdigest():
            _reject("TeamMail.body_sha256 이 본문 해시와 다르다")


@dataclass(frozen=True)
class SearchFilters:
    """서치 실행 조건. 기본 지역도 허용 지역도 코드가 아니라 계약 파일이 정한다(P22 · D12)."""

    location: str = dataclass_field(
        default_factory=lambda: policy().default_search_location,
    )
    seniority_years: tuple[int, int] | None = None

    def __post_init__(self) -> None:
        _require_text(self.location, "SearchFilters.location")
        if self.location not in policy().allowed_search_locations:
            _reject("SearchFilters.location 이 계약 허용 지역(allowed_search_locations) 밖이다")
        bounds = self.seniority_years
        if bounds is None:
            return
        if not isinstance(bounds, tuple) or len(bounds) != 2:
            _reject("SearchFilters.seniority_years 는 (최소, 최대) 두 값이어야 한다")
        low = _require_count(bounds[0], "SearchFilters.seniority_years 의 최소")
        high = _require_count(bounds[1], "SearchFilters.seniority_years 의 최대")
        if low > high:
            _reject(f"SearchFilters.seniority_years 의 최소가 최대보다 크다: {low} > {high}")


def _require_faithful(report: FidelityReport, label: str) -> None:
    if report.missing:
        _reject(f"SearchPacket.jd_packet.{label} 이 JD 원문 줄을 빠뜨렸다: {report.missing[0]!r}")
    if report.extra_lines:
        # 조건이 아니어도 원문에 없는 줄은 허위 문구다(§6 블록 안 임의 추가 0, Codex 11차)
        _reject(
            f"SearchPacket.jd_packet.{label} 에 원문에 없는 줄이 끼었다: {report.extra_lines[0]!r}"
        )


_RESERVED_MARKERS: tuple[str, ...] = (
    "[JD 원문 시작]",
    "[JD 원문 끝]",
    "[복사 시작]",
    "[복사 끝]",
    "[필드 1: 회사 소개]",
    "[필드 2: JD 내용]",
)


def _block_after(lines: tuple[str, ...], marker: str, expected: tuple[str, ...], label: str) -> int:
    """`marker` 줄(정확히 1회) 바로 뒤에 `expected` 줄들이 그대로 이어져야 한다. 끝 인덱스를 돌려준다."""
    hits = [index for index, line in enumerate(lines) if line == marker]
    if len(hits) != 1:
        _reject(f"TeamMail.body 에 {marker!r} 마커가 {len(hits)}회 나타난다(1회여야 한다)")
    start = hits[0] + 1
    end = start + len(expected)
    if lines[start:end] != expected:
        _reject(f"TeamMail.body 의 {label} 블록이 jd_packet 과 글자 그대로 일치하지 않는다")
    return end


@dataclass(frozen=True)
class SearchPacket:
    """한 포지션의 브리프를 만들기 위해 모은 구조화 자료 묶음."""

    packet_id: str
    created_on: date
    position: PositionSpec
    jd: JdSource
    company: CompanyBrief
    jd_packet: JdPacket
    candidates: tuple[CandidateLead, ...]
    mail: TeamMail
    boolean_queries: tuple[str, ...]
    inmails: tuple[tuple[str, str], ...]
    search_filters: SearchFilters = dataclass_field(default_factory=SearchFilters)

    def __post_init__(self) -> None:
        if not _PACKET_ID.fullmatch(self.packet_id):
            _reject("SearchPacket.packet_id 는 {clickup_id}-{sha8} 형태여야 한다(날짜 없음)")
        # 형식만 맞는 임의 id 는 같은 포지션·같은 JD 에 새 발송 namespace 를 연다(Codex 8차) — 내용에 결합한다.
        # sha8 은 호출자의 raw_sha256 이 아니라 jd.text 에서 직접 계산한다(Codex 10차).
        text_sha8 = hashlib.sha256(self.jd.text.encode("utf-8")).hexdigest()[:8]
        bound = f"{self.position.clickup_task_id}-{text_sha8}"
        if self.packet_id != bound:
            _reject(
                "SearchPacket.packet_id 가 position.clickup_task_id·sha256(jd.text)[:8] 에서 도출한 값과 다르다"
            )
        # 필터는 만들 때가 아니라 패킷에 담을 때의 계약으로 다시 본다(정책 override 밖에서 살아남은 객체 차단).
        if self.search_filters.location not in policy().allowed_search_locations:
            _reject("SearchPacket.search_filters.location 이 현재 계약 허용 지역 밖이다")
        # datetime 은 date 의 하위 타입이라 그냥 통과시키면 JSON 왕복(date.fromisoformat)이 깨진다.
        if not isinstance(self.created_on, date) or isinstance(self.created_on, datetime):
            _reject("SearchPacket.created_on 은 date 여야 한다")
        known: set[str] = set()
        for lead in self.candidates:
            if lead.linkedin_url in known:
                _reject("SearchPacket.candidates 에 중복 LinkedIn URL 이 있다")
            known.add(lead.linkedin_url)
        for index, (url, body) in enumerate(self.inmails):
            if url not in known:
                _reject(f"SearchPacket.inmails[{index}] 의 후보가 candidates 에 없다")
            _require_within_limit(body, f"SearchPacket.inmails[{index}]")
        for index, query in enumerate(self.boolean_queries):
            _require_balanced_query(query, index)
        self._check_jd_fidelity()

    def _check_jd_fidelity(self) -> None:
        """조립·역직렬화·저장 공통 경계 — JD 3종이 원문과 맞지 않는 패킷은 존재할 수 없다(Codex 10차).

        Gmail: 원문 줄 누락 0·추가 조건 0. LinkedIn: 선언한 생략 절 밖의 누락 0·추가 조건 0(어미 축약 허용).
        2필드: 선언한 절 마커로 `split_two_field` 를 다시 돌려 내용 줄이 정확히 같아야 한다.
        """
        packet = self.jd_packet
        _require_faithful(verify_fidelity(self.jd, packet.gmail_body), "gmail_body")
        _require_faithful(
            verify_linkedin_fidelity(
                self.jd, packet.linkedin_body, omittable_sections=packet.linkedin_omitted_sections
            ),
            "linkedin_body",
        )
        recomputed = split_two_field(
            self.jd, packet.two_field_company, section_markers=packet.two_field_sections
        )
        if content_lines(recomputed.jd_body) != content_lines(packet.two_field_jd):
            _reject(
                "SearchPacket.jd_packet.two_field_jd 가 선언한 절(two_field_sections)의 원문과 다르다"
            )
        self._check_mail_embeds_jd()

    def _check_mail_embeds_jd(self) -> None:
        """메일 본문(§6)이 JD 3종 블록을 **글자 그대로** 담고 있어야 한다(Codex 11차: 임의 본문 VERIFIED 차단).

        렌더러(mail_sections)가 넣는 마커와 같은 마커를 찾아 그 뒤 줄들을 jd_packet 과 대조한다.
        """
        packet = self.jd_packet
        if "\r" in self.mail.body:
            _reject("TeamMail.body 는 LF 개행만 쓴다(CRLF 정규화는 readback CLI 의 몫)")
        lines = tuple(self.mail.body.splitlines())
        for marker in _RESERVED_MARKERS:
            hits = sum(1 for line in lines if line == marker)
            if hits != 1:
                _reject(f"TeamMail.body 에 예약 마커 {marker!r} 가 {hits}회 나타난다(1회여야 한다)")
        end = _block_after(
            lines, "[JD 원문 시작]", tuple(packet.gmail_body.splitlines()), "Gmail JD"
        )
        if end >= len(lines) or lines[end] != "[JD 원문 끝]":
            _reject("TeamMail.body 의 Gmail JD 블록이 '[JD 원문 끝]' 로 닫히지 않는다")
        end = _block_after(
            lines, "[복사 시작]", tuple(packet.linkedin_body.splitlines()), "LinkedIn"
        )
        if end >= len(lines) or lines[end] != "[복사 끝]":
            _reject("TeamMail.body 의 LinkedIn 블록이 '[복사 끝]' 로 닫히지 않는다")
        end = _block_after(
            lines, "[필드 1: 회사 소개]", tuple(packet.two_field_company.splitlines()), "필드 1"
        )
        if lines[end : end + 2] != ("", "[필드 2: JD 내용]"):
            _reject(
                "TeamMail.body 의 필드 1 블록 뒤에 빈 줄과 '[필드 2: JD 내용]' 이 이어지지 않는다"
            )
        _block_after(lines, "[필드 2: JD 내용]", tuple(packet.two_field_jd.splitlines()), "필드 2")
