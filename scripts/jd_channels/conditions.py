"""채용 조건이 어떤 표현으로 바뀌어도 사라지지 않았는지 본다.

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


def required(src: JDSource) -> list[str]:
    """원문 core 단위에 실제로 있던 조건 라벨. 없던 조건은 요구하지 않는다."""
    origin = "\n".join(u.full for u in src.units if u.kind == "core")
    return [label for label, rx in _COMPILED.items() if rx.search(origin)]


def missing(src: JDSource, body: str) -> list[str]:
    """원문에는 있었는데 원고에서 사라진 조건 라벨."""
    return [label for label in required(src) if not _COMPILED[label].search(body)]
