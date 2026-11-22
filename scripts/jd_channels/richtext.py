"""골든 구조 본문(■/•/**)을 RPS 컴포저의 리치텍스트 HTML 로 바꾼다.

RPS 컴포저는 Quill 에디터라 `**볼드**` 를 그대로 넣으면 별표가 그대로 보인다
(2026-09-22 실측: 타인 소유 ver1.0 템플릿은 실제 <strong> 과 <ul><li> 로 저장돼 있다).
단어·순서·조건은 바꾸지 않고 표기만 옮긴다.
"""
from __future__ import annotations

import html
import re

_BOLD = re.compile(r"\*\*(.+?)\*\*")


def _inline(text: str) -> str:
    """텍스트를 이스케이프한 뒤 **볼드** 만 <strong> 으로 바꾼다."""
    out, last = [], 0
    for m in _BOLD.finditer(text):
        out.append(html.escape(text[last:m.start()]))
        out.append("<strong>" + html.escape(m.group(1)) + "</strong>")
        last = m.end()
    out.append(html.escape(text[last:]))
    return "".join(out)


def to_html(body: str) -> str:
    """본문을 <p>/<ul><li>/<strong> 으로 옮긴다. 불릿은 연속된 것끼리 한 목록으로."""
    lines = body.split("\n")
    parts: list[str] = []
    bullets: list[str] = []

    def flush() -> None:
        # RPS 컴포저(Quill)는 붙여넣은 <ul><li> 를 지워 버린다(2026-09-22 실측:
        # LI 0개, 본문 1,073자로 손실). 골든 원문과 같은 `• ` 문자 불릿을 쓴다.
        for b in bullets:
            parts.append(f"<p>• {b}</p>")
        bullets.clear()

    for raw in lines:
        line = raw.rstrip()
        if line.startswith("• "):
            bullets.append(_inline(line[2:]))
            continue
        flush()
        if not line.strip():
            parts.append("<p><br></p>")
        elif line.startswith("■ "):
            parts.append(f"<p><strong>{_inline(line)}</strong></p>")
        else:
            parts.append(f"<p>{_inline(line)}</p>")
    flush()
    return "".join(parts)


def plain_length(body: str) -> int:
    """컴포저가 세는 길이 = 마크다운 기호를 뺀 글자 수."""
    return len(_BOLD.sub(r"\1", body))
