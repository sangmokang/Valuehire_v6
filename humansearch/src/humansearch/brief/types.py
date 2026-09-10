"""HS-13 브리프 패킷의 핵심 값 타입 — 포지션·출처·JD 원문·회사 사실.

§4 입력 영역 표와 §5 계약을 생성 시점에 강제한다(fail-fast). 시계·파일·네트워크 접근 0.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from typing import NoReturn

__all__ = [
    "BriefInputError",
    "Claim",
    "CompanyBrief",
    "ExecProfile",
    "JdSource",
    "PositionSpec",
    "SourceRef",
]

_SOURCE_ID = re.compile(r"[A-Z]{1,2}[0-9]{1,3}")
_SHA256 = re.compile(r"[0-9a-f]{64}")
_HTML_TAG = re.compile(r"<[A-Za-z/!]")
_EMAIL = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")
_PROFILE_TAIL = re.compile(r"\S+")


class BriefInputError(ValueError):
    """브리프 입력 계약(§4 입력 영역 표) 위반. 값 생성 시점에 즉시 던진다."""


def _reject(message: str) -> NoReturn:
    raise BriefInputError(message)


def _require_text(value: str, field: str) -> None:
    if not value.strip():
        _reject(f"{field} 는 공백만일 수 없다")


def _require_http_url(value: str, field: str) -> None:
    if not value.startswith(("http://", "https://")):
        _reject(f"{field} 는 http:// 또는 https:// 로 시작해야 한다")


def _require_profile_url(value: str, field: str) -> None:
    """공개 프로필 URL 접두는 계약 파일이 소유한다(P22).

    `policy` 를 함수 안에서 부르는 이유는 순환 import 때문이다 — `policy.py` 가
    `_reject` 를 쓰려고 이 모듈을 먼저 읽는다. 의존 방향은 policy → types 한 방향이고,
    그 예외를 여기 한 곳에만 둔다.
    """

    from .policy import policy

    prefixes = policy().profile_url_prefixes
    for prefix in prefixes:
        if value.startswith(prefix) and _PROFILE_TAIL.fullmatch(value[len(prefix) :]):
            return
    _reject(f"{field} 는 계약이 정한 프로필 URL 접두 {prefixes} 뒤에 식별자가 와야 한다")


def _require_email(value: str, field: str) -> None:
    if not _EMAIL.fullmatch(value):
        _reject(f"{field} 의 주소 형식이 올바르지 않다")


def _require_sha256(value: str, field: str) -> None:
    if not _SHA256.fullmatch(value):
        _reject(f"{field} 는 64자 소문자 hex 여야 한다")


def _require_int(value: object, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        _reject(f"{field} 는 정수여야 한다")
    return value


def _require_range(value: object, field: str, low: int, high: int) -> int:
    number = _require_int(value, field)
    if not low <= number <= high:
        _reject(f"{field} 는 {low}..{high} 범위여야 한다")
    return number


def _require_count(value: object, field: str) -> int:
    number = _require_int(value, field)
    if number < 0:
        _reject(f"{field} 는 0 이상이어야 한다")
    return number


@dataclass(frozen=True)
class SourceRef:
    """회사 리서치 출처 하나. id 는 "C1"/"U1"/"L1"/"Y1"/"I1" 형태."""

    id: str
    url: str
    title: str
    checked_on: date

    def __post_init__(self) -> None:
        if not _SOURCE_ID.fullmatch(self.id):
            _reject("SourceRef.id 는 대문자 1~2자 + 숫자 1~3자여야 한다")
        _require_http_url(self.url, "SourceRef.url")
        _require_text(self.title, "SourceRef.title")
        if not isinstance(self.checked_on, date):
            _reject("SourceRef.checked_on 은 date 여야 한다")


@dataclass(frozen=True)
class Claim:
    """출처 id 를 동반한 사실 한 줄. 출처 없는 값은 존재할 수 없다."""

    value: str
    source_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_text(self.value, "Claim.value")
        if not self.source_ids:
            _reject("Claim.source_ids 가 비어 있다(출처 없는 값은 거부)")
        for source_id in self.source_ids:
            if not _SOURCE_ID.fullmatch(source_id):
                _reject(f"Claim.source_ids 의 출처 id 형식이 올바르지 않다: {source_id!r}")


@dataclass(frozen=True)
class PositionSpec:
    """ClickUp 포지션 한 건의 식별·표기 정보."""

    clickup_task_id: str
    client_name: str
    title: str
    department: str | None
    employment_type: str | None
    location: str | None
    recruiting_window: str | None

    def __post_init__(self) -> None:
        _require_text(self.clickup_task_id, "PositionSpec.clickup_task_id")
        _require_text(self.client_name, "PositionSpec.client_name")
        _require_text(self.title, "PositionSpec.title")


@dataclass(frozen=True)
class JdSource:
    """러너가 정리해 넘긴 JD 원문 텍스트와 원본 해시.

    `position_count` 는 러너가 **문서에서 실제로 센 포지션 수**다. 합본 JD(한 문서에
    두 포지션)를 그대로 넣으면 브리프 한 통이 두 포지션을 섞어 내보내므로, 여기서
    1 이 아닌 값을 거부해 포지션별 분리를 강제한다(§8 예외 표). 기본값 1 은
    "포지션 1건짜리 문서"라는 뜻이지 검사 면제가 아니다 — 합본을 넣으면서 1 이라고
    적는 것은 러너의 오기이고, 그 경우는 이 필드가 아니라 13.02 의 몫이다.
    """

    text: str
    raw_sha256: str
    provided_by: str
    position_count: int = 1

    def __post_init__(self) -> None:
        _require_text(self.text, "JdSource.text")
        if _HTML_TAG.search(self.text):
            _reject("JdSource.text 에 HTML 태그가 남아 있다(러너가 정리 후 재투입)")
        _require_sha256(self.raw_sha256, "JdSource.raw_sha256")
        _require_text(self.provided_by, "JdSource.provided_by")
        count = _require_int(self.position_count, "JdSource.position_count")
        if count < 1:
            _reject(f"JdSource.position_count 는 1 이상이어야 한다: {count}")
        if count != 1:
            _reject(
                f"JdSource.text 에 포지션이 {count}건 들어 있다 — "
                "합본 JD 는 포지션별로 나눠 각각 재투입한다(§8 예외 표)"
            )


@dataclass(frozen=True)
class ExecProfile:
    """대표·C레벨 한 명의 공개 정보."""

    name_role: str
    linkedin_url: str | None
    summary: Claim

    def __post_init__(self) -> None:
        _require_text(self.name_role, "ExecProfile.name_role")
        if self.linkedin_url is not None:
            _require_profile_url(self.linkedin_url, "ExecProfile.linkedin_url")


@dataclass(frozen=True)
class CompanyBrief:
    """회사 리서치 결과. 미확인 항목은 None, 확인 항목은 출처를 가진 Claim."""

    legal_name: Claim | None = None
    founded: Claim | None = None
    ceo: Claim | None = None
    headquarters: Claim | None = None
    headcount: Claim | None = None
    revenue: Claim | None = None
    operating_profit: Claim | None = None
    funding_stage: Claim | None = None
    funding_total: Claim | None = None
    products: tuple[Claim, ...] = ()
    history: tuple[Claim, ...] = ()
    news: tuple[Claim, ...] = ()
    youtube: tuple[Claim, ...] = ()
    c_level: tuple[ExecProfile, ...] = ()
    sources: tuple[SourceRef, ...] = ()

    def __post_init__(self) -> None:
        known: set[str] = set()
        for ref in self.sources:
            if ref.id in known:
                _reject(f"CompanyBrief.sources 에 중복 출처 id 가 있다: {ref.id}")
            known.add(ref.id)
        for label, claim in self._claims():
            unknown = tuple(sorted(set(claim.source_ids) - known))
            if unknown:
                _reject(f"CompanyBrief.{label} 의 출처 id 가 sources 에 없다: {unknown}")

    def _claims(self) -> tuple[tuple[str, Claim], ...]:
        singles = (
            ("legal_name", self.legal_name),
            ("founded", self.founded),
            ("ceo", self.ceo),
            ("headquarters", self.headquarters),
            ("headcount", self.headcount),
            ("revenue", self.revenue),
            ("operating_profit", self.operating_profit),
            ("funding_stage", self.funding_stage),
            ("funding_total", self.funding_total),
        )
        groups = (
            ("products", self.products),
            ("history", self.history),
            ("news", self.news),
            ("youtube", self.youtube),
        )
        collected: list[tuple[str, Claim]] = [
            (label, claim) for label, claim in singles if claim is not None
        ]
        collected.extend(
            (f"{label}[{index}]", claim)
            for label, group in groups
            for index, claim in enumerate(group)
        )
        collected.extend(
            (f"c_level[{index}].summary", profile.summary)
            for index, profile in enumerate(self.c_level)
        )
        return tuple(collected)
