"""ClickUp FY26ClientsPosition 태스크 본문을 단위 정의에서 만든다.

ClickUp 은 후보자에게 보내는 채널이 아니라 사내 포지션 원장이다. 그래서
후보자용 채널과 달리 회사 네거티브 지표와 원문 표현을 그대로 남긴다.
지원 경로(자사 이메일·ATS)는 후보자용 산출물에서만 지운다(jd 스킬 R2).
"""
from __future__ import annotations

from .units import SECTION_LABEL, SECTION_ORDER, JDSource

# ClickUp 본문에 싣는 순서. 사내 원장이므로 growth·documents 도 남긴다.
BODY_SECTIONS = SECTION_ORDER


def _lines(text: str) -> list[str]:
    return [ln.strip() for ln in text.split("\n") if ln.strip()]


def render_task_body(src: JDSource, *, channel_paths: dict[str, str] | None = None) -> str:
    """태스크 설명(markdown). 원문 단위를 빠짐없이 옮긴다."""
    out: list[str] = [f"# {src.company} {src.position}", ""]
    out.append(f"- 원본: {src.source_url}")
    out.append(f"- 수집: {src.captured_at} ({src.source_status})")
    out.append("")

    for section in BODY_SECTIONS:
        units = src.by_section(section)
        if not units:
            continue
        out.append(f"## {SECTION_LABEL[section]}")
        heading = None
        for u in units:
            if u.heading and u.heading != heading:
                heading = u.heading
                out.append(f"**{heading}**")
            for ln in _lines(u.full):
                out.append(ln if ln.startswith(("-", "*", "※")) else f"- {ln}")
        out.append("")

    if src.notes:
        out.append("## 출처 메모")
        out.extend(f"- {n}" for n in src.notes)
        out.append("")

    if channel_paths:
        out.append("## 채널 원고")
        out.extend(f"- {k}: `{v}`" for k, v in sorted(channel_paths.items()))
        out.append("")

    return "\n".join(out).rstrip() + "\n"
