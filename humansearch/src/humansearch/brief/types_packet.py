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

from .jd_fidelity import EXTRA_CONDITION_PATTERNS, FidelityReport, content_lines, verify_fidelity
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

__all__ = ["Contact", "JdPacket", "SearchFilters", "SearchPacket", "TeamMail"]

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


# 담당자 이름 자리에 들어갈 수 없는 것: 제어문자·줄바꿈. 길이는 공백 포함 2~20자.
_CONTROL = re.compile(r"[\x00-\x1f\x7f]")
_CONTACT_NAME_MIN = 2
_CONTACT_NAME_MAX = 20


@dataclass(frozen=True)
class Contact:
    """LinkedIn 판 회신 안내 줄의 **구조화된** 출처. 자유 문자열 한 줄이 아니다.

    프레임 줄 면제를 자유 문자열 선언 목록으로 주면, 조건 문구 자체를 그 목록에 적는
    것만으로 충실도 검사를 통과한다(Codex V1 F83-1). 그래서 `문의:` 줄은 이 타입에서
    `문의: {name} ({email})` 로 **렌더한 결과**와 정확히 같을 때만 통과한다.
    """

    name: str
    email: str

    def __post_init__(self) -> None:
        _require_text(self.name, "Contact.name")
        if _CONTROL.search(self.name):
            _reject("Contact.name 에 제어문자가 있다")
        if not _CONTACT_NAME_MIN <= len(self.name) <= _CONTACT_NAME_MAX:
            _reject(
                f"Contact.name 은 {_CONTACT_NAME_MIN}~{_CONTACT_NAME_MAX}자여야 한다: {len(self.name)}자"
            )
        if _has_extra_condition(self.name):
            _reject(f"Contact.name 이 채용 조건 문구다: {self.name!r}")
        _require_email(self.email, "Contact.email")

    def rendered_line(self) -> str:
        """본문에서 이 담당자를 가리킬 수 있는 **유일한** 줄."""
        return f"문의: {self.name} ({self.email})"


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
    # LinkedIn 판 회신 안내 줄의 출처. 자유 문자열이 아니라 검증된 타입이다 —
    # 본문의 `문의:` 줄은 이 값에서 렌더한 결과와 같을 때만 판정에서 빠진다(F83-1).
    linkedin_contact: Contact | None = None

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


def _has_extra_condition(line: str) -> bool:
    return any(re.compile(pattern).search(line) for pattern in EXTRA_CONDITION_PATTERNS)


_COMPANY_FIELD_CONDITION_PATTERNS: tuple[str, ...] = (
    r"\d+\s*~?\s*\d*\s*년\s*(이상|이하|차|이내)",
    r"경력\s*\d+",
    r"신입",
    r"(학사|석사|박사)\s*(이상|학위)",
    r"연봉",
    r"\d[\d,]*\s*만\s*원",
)


def _has_company_field_condition(line: str) -> bool:
    return any(re.compile(pattern).search(line) for pattern in _COMPANY_FIELD_CONDITION_PATTERNS)


# `[회사 리서치 | 2026-09-10 확인]` — 날짜는 렌더러가 넣으므로 모양만 고정한다.
_RESEARCH_HEAD = re.compile(r"\[회사 리서치 \| .+ 확인\]")

# 회사 절에서 조건 검사를 면제받을 수 있는 **금액 필드**와 렌더러가 쓰는 라벨.
# "렌더러가 만들었다" 는 면제 근거가 될 수 없다 — CompanyBrief 에 조건을 먼저 심으면
# 그 줄이 그대로 허용 집합에 들어간다(Codex V1: `- 매출: 경력 5년 이상 [I1]`).
_AMOUNT_FIELDS: tuple[tuple[str, str], ...] = (
    ("매출", "revenue"),
    ("영업이익", "operating_profit"),
    ("누적 투자금", "funding_total"),
)

# 회사 금액으로 인정하는 값의 모양. 값 전체가 여기 맞을 때만 면제한다.
_AMOUNT_VALUE = re.compile(r"\d[\d,]*(\.\d+)?\s*(억|만|조)?\s*(원|달러|USD|KRW)")


def _company_research_indexes(lines: tuple[str, ...]) -> frozenset[int]:
    """[회사 리서치] 절 본문의 줄 번호. 빈 줄이나 다음 절 머리(`[`)에서 끝난다."""
    start = next((i for i, line in enumerate(lines) if _RESEARCH_HEAD.fullmatch(line)), None)
    if start is None:
        return frozenset()
    end = len(lines)
    for index in range(start + 1, len(lines)):
        if not lines[index] or lines[index].startswith("["):
            end = index
            break
    return frozenset(range(start + 1, end))


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
    schema_version: int = 1

    def __post_init__(self) -> None:
        if isinstance(self.schema_version, bool) or self.schema_version != 1:
            _reject(f"SearchPacket.schema_version 은 1 이어야 한다: {self.schema_version!r}")
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

    def _rendered_frame_lines(self) -> tuple[str, ...]:
        """타입 필드에서 렌더한 프레임 줄 전부. 이 문자열들만 충실도 판정에서 빠진다.

        `제목:` 은 포지션 제목, `문의:` 는 `JdPacket.linkedin_contact` 에서 나온다.
        호출자가 넘긴 자유 문자열은 여기 한 글자도 섞이지 않는다(Codex V1 F83-1).
        """
        lines = [f"제목: {self.position.title}"]
        contact = self.jd_packet.linkedin_contact
        if contact is not None:
            lines.append(contact.rendered_line())
        return tuple(lines)

    def _check_jd_fidelity(self) -> None:
        """조립·역직렬화·저장 공통 경계 — JD 3종이 원문과 맞지 않는 패킷은 존재할 수 없다(Codex 10차).

        Gmail: 원문 줄 누락 0·추가 조건 0. LinkedIn: 선언한 생략 절 밖의 누락 0·추가 조건 0(어미 축약 허용).
        2필드: 선언한 절 마커로 `split_two_field` 를 다시 돌려 내용 줄이 정확히 같아야 한다.
        """
        packet = self.jd_packet
        _require_faithful(verify_fidelity(self.jd, packet.gmail_body), "gmail_body")
        _require_faithful(
            verify_linkedin_fidelity(
                self.jd,
                packet.linkedin_body,
                omittable_sections=packet.linkedin_omitted_sections,
                frame_lines=self._rendered_frame_lines(),
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
        jd_line_indexes: set[int] = set()
        for marker in _RESERVED_MARKERS:
            hits = sum(1 for line in lines if line == marker)
            if hits != 1:
                _reject(f"TeamMail.body 에 예약 마커 {marker!r} 가 {hits}회 나타난다(1회여야 한다)")
        end = _block_after(
            lines, "[JD 원문 시작]", tuple(packet.gmail_body.splitlines()), "Gmail JD"
        )
        jd_line_indexes.update(range(lines.index("[JD 원문 시작]") + 1, end))
        if end >= len(lines) or lines[end] != "[JD 원문 끝]":
            _reject("TeamMail.body 의 Gmail JD 블록이 '[JD 원문 끝]' 로 닫히지 않는다")
        end = _block_after(
            lines, "[복사 시작]", tuple(packet.linkedin_body.splitlines()), "LinkedIn"
        )
        jd_line_indexes.update(range(lines.index("[복사 시작]") + 1, end))
        if end >= len(lines) or lines[end] != "[복사 끝]":
            _reject("TeamMail.body 의 LinkedIn 블록이 '[복사 끝]' 로 닫히지 않는다")
        company_marker_index = lines.index("[필드 1: 회사 소개]")
        company_line_indexes: set[int] = set()
        end = _block_after(
            lines, "[필드 1: 회사 소개]", tuple(packet.two_field_company.splitlines()), "필드 1"
        )
        company_line_indexes.update(range(company_marker_index + 1, end))
        if lines[end : end + 2] != ("", "[필드 2: JD 내용]"):
            _reject(
                "TeamMail.body 의 필드 1 블록 뒤에 빈 줄과 '[필드 2: JD 내용]' 이 이어지지 않는다"
            )
        end = _block_after(
            lines, "[필드 2: JD 내용]", tuple(packet.two_field_jd.splitlines()), "필드 2"
        )
        jd_line_indexes.update(range(lines.index("[필드 2: JD 내용]") + 1, end))
        research_indexes = _company_research_indexes(lines)
        rendered = self._rendered_company_lines() if research_indexes else frozenset[str]()
        for index, line in enumerate(lines):
            if index in jd_line_indexes:
                continue
            if index in research_indexes and line in rendered:
                # 회사 리서치 절에서 면제받는 줄은 **금액 필드에서 렌더한 금액 모양** 하나뿐이다.
                # (F83-3: `- 매출: 300억 원 [I1]` 오탐을 풀되, `- 매출: 경력 5년 이상 [I1]` 은 막는다)
                continue
            has_condition = (
                _has_company_field_condition(line)
                if index in company_line_indexes
                else _has_extra_condition(line)
            )
            if has_condition:
                _reject(f"TeamMail.body 의 JD 블록 밖에 채용 조건이 끼었다: {line!r}")

    def _rendered_company_lines(self) -> frozenset[str]:
        """조건 검사를 면제할 회사 절 줄 — **금액 필드에서 렌더한 금액 모양 줄**만.

        `mail_sections` 가 `types_packet` 을 import 하므로 최상단 import 는 순환이다 —
        렌더러를 복제해 줄 모양이 갈라지느니 호출 시점에 한 번 불러온다(정본은 한 곳뿐).
        렌더러가 실제로 내보내는 줄인지도 교차 확인한다 — 라벨이 갈라지면 면제가
        조용히 넓어지는 대신 좁아지고, 정상 경로 시험이 곧바로 깨진다.
        `open_items`·제품·연혁·뉴스 같은 자유 문구는 여기 없다 — 계속 조건 검사를 받는다.
        """
        from .mail_sections import _claim_line, render_company_research

        rendered = frozenset(render_company_research(self.company, (), self.created_on))
        allowed: set[str] = set()
        for label, attribute in _AMOUNT_FIELDS:
            claim = getattr(self.company, attribute)
            if claim is None or not _AMOUNT_VALUE.fullmatch(claim.value.strip()):
                continue
            line = _claim_line(label, claim)
            if line in rendered:
                allowed.add(line)
        return frozenset(allowed)
