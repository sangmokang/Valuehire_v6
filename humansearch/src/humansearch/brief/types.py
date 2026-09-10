"""HS-13 브리프 패킷의 핵심 값 타입 — 포지션·출처·JD 원문·회사 사실."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

__all__ = [
    "BriefInputError",
    "Claim",
    "CompanyBrief",
    "ExecProfile",
    "JdSource",
    "PositionSpec",
    "SourceRef",
]


class BriefInputError(ValueError):
    """브리프 입력 계약(§4 입력 영역 표) 위반. 값 생성 시점에 즉시 던진다."""


@dataclass(frozen=True)
class SourceRef:
    """회사 리서치 출처 하나. id 는 "C1"/"U1"/"L1"/"Y1"/"I1" 형태."""

    id: str
    url: str
    title: str
    checked_on: date


@dataclass(frozen=True)
class Claim:
    """출처 id 를 동반한 사실 한 줄. 출처 없는 값은 존재할 수 없다."""

    value: str
    source_ids: tuple[str, ...]


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


@dataclass(frozen=True)
class JdSource:
    """러너가 정리해 넘긴 JD 원문 텍스트와 원본 해시."""

    text: str
    raw_sha256: str
    provided_by: str


@dataclass(frozen=True)
class ExecProfile:
    """대표·C레벨 한 명의 공개 정보."""

    name_role: str
    linkedin_url: str | None
    summary: Claim


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
