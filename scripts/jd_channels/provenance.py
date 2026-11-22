"""단위 정의의 사실이 실제 원문에 있는지 기계로 대조한다.

2026-09-22 사고: 사장님이 붙여넣은 번개장터 JD 두 건에 없는
`경력 6년 이상`·`정규직`·`서울 서초 오피스`·`채용 시 마감` 이 단위 정의에 들어갔고,
`source_status` 는 `FETCHED_VERBATIM` 이라 적혀 있었다. 다른 JD 의 메타 필드를
그대로 베낀 것이다. 사람 눈으로는 통과하므로 원문 파일과 직접 대조한다.

대조 대상은 이 JD 자체에서 나온 단위뿐이다 — 회사 조사에서 온 단위는
`source` 가 다르므로 건드리지 않는다(그쪽은 회사 조사 캐시가 출처다).
"""
from __future__ import annotations

import re

from .checks import Hit
from .units import JDSource, Unit

# 원문에 없으면 지어낸 것으로 보는 숫자 표현.
# 단위를 붙여 세는 이유: 맨숫자(1, 2)는 순서·항목 번호로 흔해 오탐이 크다.
_NUMBER = re.compile(
    r"\d[\d,]*\s*(?:년|개월|주|일|명|개|건|원|억|만|천|%|배|위|시간)"
)

# 숫자가 아니지만 원문에 없으면 안 되는 채용 조건 어휘.
_CONDITION_TERMS = (
    "정규직", "계약직", "인턴", "파견", "프리랜서",
    "수습", "연봉", "채용 시 마감", "재택", "주 4일",
)

_STRIP = re.compile(r"[\s,·/]")


def _norm(text: str) -> str:
    return _STRIP.sub("", text)


def _own_units(src: JDSource) -> list[Unit]:
    """이 JD 원문에서 나온 단위만. 회사 조사 출처 단위는 제외한다."""
    return [u for u in src.units if u.source == src.source_url]


def unsourced_facts(src: JDSource, source_text: str) -> list[Hit]:
    """원문에 없는 숫자·조건 표현을 찾는다. 빈 결과가 곧 정확함은 아니다."""
    body = _norm(source_text)
    hits: list[Hit] = []
    for u in _own_units(src):
        seen: set[str] = set()
        for text in (u.full, u.compact, u.rps):
            if not text:
                continue
            for m in _NUMBER.finditer(text):
                token = m.group(0)
                if token in seen:
                    continue
                seen.add(token)
                if _norm(token) not in body:
                    hits.append(Hit("UNSOURCED_NUMBER",
                                    f"원문에 없는 숫자 — 단위 {u.id}", token, 0))
            for term in _CONDITION_TERMS:
                if term in text and term in seen:
                    continue
                if term in text:
                    seen.add(term)
                    if _norm(term) not in body:
                        hits.append(Hit("UNSOURCED_CONDITION",
                                        f"원문에 없는 채용 조건 — 단위 {u.id}", term, 0))
    return sorted(hits, key=lambda h: (h.rule, h.description, h.match))


def load_source_text(slug: str, root: str = "outputs/_sources") -> str | None:
    """원문 전문을 읽는다. `.txt`(붙여넣기 원문) 와 `.json`(수집본) 둘 다 지원한다."""
    import json
    from pathlib import Path

    base = Path(root)
    txt = base / f"{slug}.txt"
    if txt.exists():
        return txt.read_text(encoding="utf-8")
    js = base / f"{slug}.json"
    if js.exists():
        return json.loads(js.read_text(encoding="utf-8")).get("text")
    return None
