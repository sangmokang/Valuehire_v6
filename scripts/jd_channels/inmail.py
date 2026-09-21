"""LinkedIn RPS InMail 본문 조립 — 사장님 골든 샘플의 뼈대를 그대로 만든다.

뼈대(섹션 순서·기호·인사·클로징)는 이 파일에 있고, 문장은 전부 단위 정의에서
온다. 그래서 골든 두 건을 하드코딩으로 재현할 수 없고, rps_* 필드가 하나도
없는 제3의 JD 를 넣어도 같은 뼈대가 나온다(acceptance CAC-1).

근거: docs/sot/linkedin-rps-inmail.md G1~G12,
     outputs/_golden/rps_wrtn_golden.txt, outputs/_golden/rps_bunjang_golden.txt
"""
from __future__ import annotations

import re

from .units import SECTION_ORDER, JDSource, Unit

GREETING = "안녕하세요. 테크 전문 서치펌 밸류커넥트의 헤드헌터 강상모입니다."
SOFT_TOUCH = ("현재 이직을 적극적으로 검토하고 계시지 않더라도, "
              "향후 커리어 관점에서 포지션 정보를 가볍게 살펴보셔도 좋습니다.")
CLOSING = ("관심 있으시면 LinkedIn 수락 또는 간단한 회신만 주셔도 "
           "상세 JD와 조직 관련 내용을 공유드리겠습니다.")

# 불릿으로 찍는 블록과 그 기본 제목. 제목은 rps_labels 로 갈아끼울 수 있다.
BULLET_BLOCKS = (
    ("responsibilities", "Key Responsibilities"),
    ("requirements", "Requirements"),
    ("preferred", "Preferred"),
)

# 앞머리 기호만 떼고 **볼드** 의 별표는 건드리지 않는다.
# 2026-09-22 실측: [-*] 로 잡으면 "**BI Tool**" 이 "*BI Tool**" 로 깨진다.
_LEAD_MARK = re.compile(r"^\s*(?:[-\u2022\u00b7]|\*(?!\*))\s*")


def _lines(unit: Unit) -> list[str]:
    """단위의 RPS 표현을 줄 단위로 푼다. 앞머리 기호는 렌더러가 다시 붙인다."""
    out = []
    for raw in unit.rps_text().split("\n"):
        text = _LEAD_MARK.sub("", raw).strip()
        if text:
            out.append(text)
    return out


def _order(src: JDSource) -> dict[str, list[Unit]]:
    """블록별 단위. 같은 블록 안에서는 원문 section 순서를 지킨다."""
    rank = {s: i for i, s in enumerate(SECTION_ORDER)}
    blocks: dict[str, list[Unit]] = {}
    for u in sorted(src.units, key=lambda x: rank[x.section]):
        blocks.setdefault(u.block(), []).append(u)
    # 블록 안에서 rps_order 를 준 단위를 앞으로 당긴다(안정 정렬).
    for name, items in blocks.items():
        if any(x.rps_order for x in items):
            blocks[name] = sorted(items, key=lambda x: (x.rps_order or 10**6))
    return blocks


def _position_line(src: JDSource) -> str:
    return f"현재 **{src.company}** {src.position} 포지션을 제안드립니다."


def render_inmail(src: JDSource, keep: set[str]) -> str:
    """keep 에 든 단위 id 만으로 InMail 본문을 만든다.

    keep 은 호출자(render.py)가 길이 사다리에 따라 정한다. 이 함수는 길이를
    맞추려고 문자열을 자르지 않는다 — 자르기는 조건을 소리 없이 지운다.
    """
    blocks = _order(src)

    def pick(name: str) -> list[Unit]:
        return [u for u in blocks.get(name, []) if u.id in keep]

    label = {"requirements": "Requirements", **src.rps_labels}
    out: list[str] = [GREETING, "", _position_line(src), ""]

    for u in pick("intro"):
        out.extend(_lines(u))
    if out[-1]:
        out.append("")

    out.append(f"■ Position | {src.role_label or src.position}")
    out.append("")

    mission = pick("mission")
    if mission:
        out.append("**Mission**")
        for u in mission:
            out.extend(_lines(u))
        out.append("")

    for block, default_title in BULLET_BLOCKS:
        units = pick(block)
        if not units:
            continue
        out.append(f"■ {label.get(block, default_title)}")
        for u in units:
            out.extend(f"• {ln}" for ln in _lines(u))
        out.append("")

    notes = [ln for u in pick("note") for ln in _lines(u)]
    if notes:
        out.extend(f"※ {ln.lstrip('※ ').strip()}" for ln in notes)
        out.append("")

    process, conditions = pick("process"), pick("conditions")
    if process or conditions:
        out.append("■ Process")
        for u in process:
            out.extend(_lines(u))
        if conditions:
            out.append(" · ".join(ln for u in conditions for ln in _lines(u)))
        out.append("")

    footnote = [ln for u in pick("footnote") for ln in _lines(u)]
    if footnote:
        out.append("※ " + " · ".join(footnote))
        out.append("")

    out.extend([SOFT_TOUCH, "", CLOSING])
    return "\n".join(out).strip("\n")


def dropped_for_inmail(src: JDSource, keep: set[str]) -> tuple[str, ...]:
    """본문에 싣지 않은 단위. 생략을 숨기지 않으려고 따로 돌려준다."""
    return tuple(u.id for u in src.units if u.id not in keep)
