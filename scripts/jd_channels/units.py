"""JD 의미 단위 모델.

원문을 독립적인 의미 단위로 쪼개고, 채널별 렌더링의 유일한 입력으로 삼는다.
문자열을 잘라내는 방식(slice/substring)을 쓰지 않기 위해 존재한다 —
길이를 줄일 때는 문자가 아니라 단위를 고르거나 단위의 compact 표현을 쓴다.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

# 후보자가 읽는 순서. 채널 렌더러는 이 순서만 사용한다.
SECTION_ORDER = [
    "company", "team", "domain", "role", "duties",
    "requirements", "preferred", "growth", "conditions",
    "process", "documents",
]

SECTION_LABEL = {
    "company": "회사 소개",
    "team": "합류할 팀",
    "domain": "도메인 특성",
    "role": "포지션의 역할",
    "duties": "주요 업무",
    "requirements": "자격요건",
    "preferred": "우대사항",
    "growth": "쌓을 수 있는 경험",
    "conditions": "근무조건",
    "process": "채용 절차",
    "documents": "지원 서류",
}

# core   : 채용 판단에 직접 쓰이는 정보. 어떤 채널에서도 삭제 금지.
# company: 후보자 판단에 필요한 회사 정보. RPS에서도 소개 전체 삭제 금지.
# extra  : 있으면 좋은 맥락. company 다음으로 생략 가능.
KINDS = ("core", "company", "extra")


class UnitError(ValueError):
    """단위 정의가 계약을 어겼을 때. 조용히 넘기지 않는다."""


# 생략 순서. 숫자가 클수록 먼저 버린다. core(0)는 절대 버리지 않는다.
# 비핵심 회사 부가정보는 줄일 수 있으나 검증기가 회사 소개의 존재·충실도를 별도 확인한다.
DEFAULT_RANK = {"core": 0, "company": 1, "extra": 3}
MAX_RANK = 3


@dataclass(frozen=True)
class Unit:
    id: str
    section: str
    kind: str
    meaning: str
    full: str
    compact: str
    source: str
    heading: str | None = None
    note: bool = False
    drop_rank: int = 0
    merge_group: str | None = None

    def text(self, compact: bool) -> str:
        return self.compact if compact else self.full


@dataclass(frozen=True)
class JDSource:
    company: str
    position: str
    source_url: str
    captured_at: str
    source_status: str
    jd_id: str
    units: tuple[Unit, ...]
    company_slug: str
    position_slug: str
    role_label: str | None = None
    notes: tuple[str, ...] = field(default=())
    excluded_units: tuple[dict, ...] = field(default=())

    def by_section(self, section: str) -> list[Unit]:
        return [u for u in self.units if u.section == section]

    def core_ids(self) -> list[str]:
        return [u.id for u in self.units if u.kind == "core"]


_REQUIRED_UNIT_KEYS = {"id", "section", "kind", "meaning", "full", "compact", "source"}
_REQUIRED_DOC_KEYS = {
    "company", "position", "source_url", "captured_at", "source_status",
    "jd_id", "company_slug", "position_slug", "units",
}


def _check_unit(raw: dict, seen: set[str]) -> Unit:
    missing = _REQUIRED_UNIT_KEYS - raw.keys()
    if missing:
        raise UnitError(f"단위 {raw.get('id', '?')}: 필수 키 누락 {sorted(missing)}")
    uid = raw["id"]
    if uid in seen:
        raise UnitError(f"단위 id 중복: {uid}")
    seen.add(uid)
    if raw["section"] not in SECTION_ORDER:
        raise UnitError(f"단위 {uid}: 알 수 없는 section {raw['section']!r}")
    if raw["kind"] not in KINDS:
        raise UnitError(f"단위 {uid}: 알 수 없는 kind {raw['kind']!r}")
    for key in ("meaning", "full", "compact", "source"):
        if not str(raw[key]).strip():
            raise UnitError(f"단위 {uid}: {key} 가 비어 있다")
    if len(raw["compact"]) > len(raw["full"]):
        raise UnitError(f"단위 {uid}: compact 가 full 보다 길다 — 압축이 아니다")
    rank = int(raw.get("drop_rank", DEFAULT_RANK[raw["kind"]]))
    if raw["kind"] == "core" and rank != 0:
        raise UnitError(f"단위 {uid}: core 는 drop_rank 0 이어야 한다 — 생략 불가")
    if not 0 <= rank <= MAX_RANK:
        raise UnitError(f"단위 {uid}: drop_rank 범위 밖 {rank}")
    return Unit(
        id=uid, section=raw["section"], kind=raw["kind"], meaning=raw["meaning"],
        full=raw["full"], compact=raw["compact"], source=raw["source"],
        heading=raw.get("heading"), note=bool(raw.get("note", False)),
        drop_rank=rank, merge_group=raw.get("merge_group"),
    )


def load(path: str | Path) -> JDSource:
    """단위 정의 JSON을 읽어 검증한다. 계약 위반이면 UnitError 로 즉시 멈춘다."""
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    missing = _REQUIRED_DOC_KEYS - raw.keys()
    if missing:
        raise UnitError(f"JD 정의: 필수 키 누락 {sorted(missing)}")
    if not raw["units"]:
        raise UnitError("JD 정의: 단위가 0개 — 검사 대상 0개는 합격이 아니다")
    seen: set[str] = set()
    units = tuple(_check_unit(u, seen) for u in raw["units"])
    if not any(u.kind == "core" for u in units):
        raise UnitError("JD 정의: core 단위가 하나도 없다")
    excluded_units = tuple(raw.get("excluded_units", []))
    for item in excluded_units:
        if not isinstance(item, dict):
            raise UnitError("excluded_units: item must be object")
        missing = {"id", "section", "reason", "full", "source"} - item.keys()
        if missing:
            raise UnitError(f"excluded_units {item.get('id', '?')}: 필수 키 누락 {sorted(missing)}")
        if item["id"] in seen:
            raise UnitError(f"excluded_units id conflicts with unit id: {item['id']}")
        if item["section"] not in SECTION_ORDER:
            raise UnitError(f"excluded_units {item['id']}: 알 수 없는 section {item['section']!r}")
        reason = str(item["reason"])
        if not (reason.startswith("explicit_user_exclusion") or reason.startswith("standing_user_exclusion")):
            raise UnitError(
                f"excluded_units {item['id']}: reason must start with explicit_user_exclusion "
                "or standing_user_exclusion"
            )
    return JDSource(
        company=raw["company"], position=raw["position"], source_url=raw["source_url"],
        captured_at=raw["captured_at"], source_status=raw["source_status"],
        jd_id=raw["jd_id"], company_slug=raw["company_slug"],
        position_slug=raw["position_slug"], units=units,
        role_label=raw.get("role_label"),
        notes=tuple(raw.get("notes", [])),
        excluded_units=excluded_units,
    )
