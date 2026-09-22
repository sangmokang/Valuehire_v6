"""최종 텍스트의 길이를 코드로 계산한다. 모델의 추정을 쓰지 않는다."""
from __future__ import annotations

import unicodedata
from dataclasses import asdict, dataclass

# 길이 제한을 우회하려고 끼워 넣을 수 있는 비가시 문자.
# 폭(width)이 0이거나 렌더링되지 않으면서 코드포인트는 차지하거나, 반대로
# 사람 눈에는 공백인데 계수에서 빠지길 기대하는 것들이다.
INVISIBLE = {
    "​": "ZERO WIDTH SPACE",
    "‌": "ZERO WIDTH NON-JOINER",
    "‍": "ZERO WIDTH JOINER",
    "⁠": "WORD JOINER",
    "﻿": "BOM / ZERO WIDTH NO-BREAK SPACE",
    "­": "SOFT HYPHEN",
    "᠎": "MONGOLIAN VOWEL SEPARATOR",
}
# NBSP 류는 본문에 들어가면 플랫폼 계수와 어긋나므로 따로 센다.
SUSPICIOUS_SPACE = {
    " ": "NO-BREAK SPACE",
    " ": "FIGURE SPACE",
    " ": "NARROW NO-BREAK SPACE",
    "　": "IDEOGRAPHIC SPACE",
}


@dataclass(frozen=True)
class Measured:
    codepoints: int
    utf16_units: int
    utf8_bytes: int
    lines: int
    invisible: dict[str, int]
    suspicious_space: dict[str, int]

    def as_dict(self) -> dict:
        return asdict(self)

    @property
    def clean(self) -> bool:
        return not self.invisible


# 포털이 저장하면서 말없이 바꾸거나 지우는 문자. 전부 실측으로 확인한 것만 적는다.
# 넣으면 후보자가 보는 글이 깨지므로, 쓰기 전에 scan_portal_risk 로 걸러낸다.
PORTAL_RISK: dict[str, dict[str, str]] = {
    "jobkorea": {
        "•": "bullet → 물음표로 저장됨 (2026-09-22 fresh reopen 실측)",
        "\u2013": "en dash → 물음표로 저장됨 (2026-09-21 실측)",
        "\u2014": "em dash → 물음표 가능 (en dash와 같은 계열)",
        "'": "작은따옴표 → 백틱(`)으로 치환됨 (2026-09-22 실측)",
        "\u2018": "여는 작은따옴표 → 백틱 치환 가능",
        "\u2019": "닫는 작은따옴표 → 백틱 치환 가능",
    },
    "saramin": {
        "\u2192": "화살표 → 통째로 삭제됨 (2026-09-22 실측). 전형 순서가 사라진다",
    },
}
# 대신 쓸 수 있는 안전한 표기. 단어와 순서는 바꾸지 않는다.
PORTAL_SAFE_SUBSTITUTE = {
    "•": "-",
    "\u2013": "-", "\u2014": "-", "\u2192": ">",
    "'": "", "\u2018": "", "\u2019": "",
}


def scan_portal_risk(text: str, portal: str) -> dict[str, tuple[int, str]]:
    """해당 포털이 저장할 때 바꿔버리는 문자를 찾는다.

    빈 결과가 안전을 보장하지는 않는다 — 새 변환은 저장 후 재조회로만 드러난다.
    """
    table = PORTAL_RISK.get(portal, {})
    return {ch: (text.count(ch), why) for ch, why in table.items() if ch in text}


def compose(title: str, body: str) -> str:
    """플랫폼이 세는 단위 = 제목 + 빈 줄 + 본문. 내부 메모는 넣지 않는다."""
    title = title.strip()
    body = body.strip("\n")
    return f"{title}\n\n{body}" if title else body


def measure(text: str) -> Measured:
    invisible = {name: text.count(ch) for ch, name in INVISIBLE.items() if ch in text}
    spaces = {name: text.count(ch) for ch, name in SUSPICIOUS_SPACE.items() if ch in text}
    return Measured(
        codepoints=len(text),
        # 잡코리아·사람인 입력란은 JS 기반이라 UTF-16 단위로 세는 경우가 있다.
        utf16_units=len(text.encode("utf-16-le")) // 2,
        utf8_bytes=len(text.encode("utf-8")),
        lines=len([ln for ln in text.split("\n") if ln.strip()]),
        invisible=invisible,
        suspicious_space=spaces,
    )


def over_limit(m: Measured, limit: int) -> bool:
    """플랫폼마다 세는 방식이 다르므로 가장 큰 값으로 판정한다(보수적)."""
    return max(m.codepoints, m.utf16_units) > limit


def normalize_for_compare(text: str) -> str:
    """TXT/HTML/저장본 대조용. 서식 차이는 지우고 의미 글자만 남긴다."""
    text = unicodedata.normalize("NFKC", text)
    for ch in list(INVISIBLE) + list(SUSPICIOUS_SPACE):
        text = text.replace(ch, " " if ch in SUSPICIOUS_SPACE else "")
    for a, b in (("–", "-"), ("—", "-"), ("“", '"'), ("”", '"'), ("’", "'"), ("‘", "'")):
        text = text.replace(a, b)
    return "".join(text.split())
