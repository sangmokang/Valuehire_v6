"""채용 조건의 핵심 값이 지원 범위 안에서 사라지거나 바뀌지 않았는지 본다.

`_missing_core` 는 단위가 실어나르는 문자열(full/compact/rps)이 원고에 있는지만
본다. 그래서 `rps` 자체에서 조건을 지우면 "지워진 문장이 나왔다"는 이유로
보존을 인정한다(2026-09-22 Codex V1 결함 1 실측: 연차·대체 인정·고용형태를
지워도 `missing_core=()`).

이 모듈은 출력 표현과 독립적으로 잰다. 원문(`full`)에서 조건이 있었는지 뽑고,
렌더된 본문에 같은 종류의 조건이 남아 있는지 따로 확인한다.
"""
from __future__ import annotations

import re

from .units import JDSource

# (라벨, 정규식). 라벨은 SOT L2 의 "접어도 사라지면 안 되는 것"과 1:1이다.
# 같은 라벨 안의 대안은 서로 바꿔 써도 된다 — 레퍼런스 체크 ↔ Reference Check.
CONDITION_RULES: tuple[tuple[str, str], ...] = (
    # "2026년 8월" 같은 연도는 연차가 아니다. 이상/+/차 가 붙은 것만 센다.
    ("연차", r"경력\s*\d+\s*년|\d+\s*년\s*(?:이상|차)|\d+\s*년\s*\*{0,2}\+"),
    ("대체 인정 조건", r"이에\s*준하는"),
    ("고용형태", r"정규직|계약직|인턴|파트타임|프리랜서"),
    ("수습", r"수습"),
    ("평판 조회 단계", r"레퍼런스|Reference\s*Check"),
    ("컬처핏 단계", r"컬처핏|Culture\s*Fit"),
    ("처우 협의 단계", r"처우\s*협의|Offer"),
    ("서류 전형", r"서류"),
)

_COMPILED = {label: re.compile(pat) for label, pat in CONDITION_RULES}
_YEAR = re.compile(r"(?:(경력)\s*)?(\d+)\s*년\s*(이상|이하|차|\*{0,2}\+)?")
_PROBATION = (
    re.compile(r"수습\s*(?:기간)?\s*(\d+)\s*개월"),
    re.compile(r"(\d+)\s*개월(?:의)?\s*수습\s*기간"),
)
_EMPLOYMENT = re.compile(r"정규직|계약직|인턴|파트타임|프리랜서")


def _year_key(number: str, suffix: str | None) -> str:
    if suffix in ("이상", "+", "**+"):
        return f"{number}년 이상"
    if suffix == "이하":
        return f"{number}년 이하"
    if suffix == "차":
        return f"{number}년차"
    return f"{number}년"


def _years(text: str) -> tuple[str, ...]:
    found: set[str] = set()
    for m in _YEAR.finditer(text):
        # "2026년 8월" 같은 날짜는 연차가 아니다. 경력 또는 이상/차/+가 있을 때만 센다.
        if m.group(1) or m.group(3):
            found.add(_year_key(m.group(2), m.group(3)))
    return tuple(sorted(found))


def _terms(rx: re.Pattern[str], text: str) -> tuple[str, ...]:
    return tuple(sorted(set(rx.findall(text))))


def _probation(text: str) -> tuple[str, ...]:
    found: set[str] = set()
    for rx in _PROBATION:
        found.update(f"{m}개월" for m in rx.findall(text))
    return tuple(sorted(found))


def _spec(text: str) -> dict[str, tuple[str, ...]]:
    return {
        "labels": tuple(label for label, rx in _COMPILED.items() if rx.search(text)),
        "years": _years(text),
        "probation": _probation(text),
        "employment": _terms(_EMPLOYMENT, text),
    }


def _origin(src: JDSource) -> str:
    return "\n".join(u.full for u in src.units if u.kind == "core")


def _source_text(src: JDSource) -> str:
    return "\n".join(u.full for u in src.units)


def required(src: JDSource) -> list[str]:
    """원문 core 단위에 실제로 있던 조건 라벨. 없던 조건은 요구하지 않는다."""
    return list(_spec(_origin(src))["labels"])


def missing(src: JDSource, body: str) -> list[str]:
    """원문에는 있었는데 원고에서 사라진 조건 라벨."""
    expected = _spec(_origin(src))
    sourced = _spec(_source_text(src))
    actual = _spec(body)
    notes = [label for label in expected["labels"] if label not in actual["labels"]]
    for label in actual["labels"]:
        if label not in sourced["labels"]:
            notes.append(f"원문에 없는 조건: {label}")
    for year in expected["years"]:
        if year not in actual["years"]:
            notes.append(f"연차 값 누락: {year}")
    for year in actual["years"]:
        if year not in sourced["years"]:
            notes.append(f"원문에 없는 연차 값: {year}")
    for months in expected["probation"]:
        if months not in actual["probation"]:
            notes.append(f"수습 기간 누락: {months}")
    for months in actual["probation"]:
        if months not in sourced["probation"]:
            notes.append(f"원문에 없는 수습 기간: {months}")
    for term in expected["employment"]:
        if term not in actual["employment"]:
            notes.append(f"고용형태 값 누락: {term}")
    for term in actual["employment"]:
        if term not in sourced["employment"]:
            notes.append(f"원문에 없는 고용형태: {term}")
    return notes
