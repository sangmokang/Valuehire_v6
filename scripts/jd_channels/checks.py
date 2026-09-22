"""후보자용 본문에 들어가면 안 되는 것을 찾는다.

금지 대상은 "밸류커넥트가 정보의 신뢰도를 유보하는 문장"과 내부 표식이다.
회사가 지원자에게 알리는 조건(전형 변동 가능성, 합격 취소, 우대 안내)은
원문 정보이므로 지우지 않는다 — 두 가지를 섞으면 조건을 삭제하게 된다.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

# (규칙 id, 설명, 정규식). 조사 변화를 견디도록 어간 중심으로 쓴다.
BANNED = [
    ("SELF_HEDGE_ASSERT", "신뢰도 유보 — 단정 회피",
     r"단정(?:하지|할)\s*(?:않|못|수\s*없)"),
    ("SELF_HEDGE_VIEW", "신뢰도 유보 — 해석 주의 고지",
     r"(?:보아서는|간주해서는|받아들여서는)\s*안\s*(?:됩니다|된다)"),
    ("SELF_HEDGE_SUBSTITUTE", "신뢰도 유보 — 대체 불가 고지",
     r"(?:대신하지|갈음하지)\s*(?:않습니다|않는다)"),
    ("SELF_HEDGE_GUARANTEE", "신뢰도 유보 — 배치·권한 미보장 고지",
     r"(?:배치|권한|소속|적합도)[^\n]{0,20}보장(?:하지|되지)\s*(?:않|못)"),
    ("SELF_HEDGE_UNCONFIRMED", "신뢰도 유보 — 확정 불가 고지",
     r"(?:확정할\s*수\s*없|확인하지\s*못했|확인되지\s*않았)"),
    ("SELF_HEDGE_INTERPRET", "신뢰도 유보 — 밸류커넥트 해석 고지",
     r"밸류커넥트의\s*(?:해석|추정|판단)(?:이며|입니다)"),
    ("PENSION_SOURCE", "인원 출처 설명 — 국민연금 기반 표기",
     r"국민연금"),
    ("ESTIMATE_NOTICE", "추정 고지",
     r"(?:추정치|추정입니다|추정한\s*값)"),
    ("INTERNAL_FACT_ID", "내부 fact 표식",
     r"\[B\d+(?:\s*[,·]\s*B\d+)*\]"),
    ("INTERNAL_STATUS", "내부 검증 상태 문자열",
     r"\b(?:READY_DRAFT|NEEDS_SOURCE_REVIEW|NEEDS_LENGTH_DECISION|NOT_RUN|FIXTURE)\b"),
    ("PLACEHOLDER_BRACE", "미치환 자리표시자",
     r"\{[A-Za-z가-힣_][^\n{}]{0,30}\}"),
    ("PLACEHOLDER_TODO", "미완성 표식",
     r"(?:^|\s)(?:TODO|TBD|FIXME|XXX)(?:\s|:|$)"),
    ("HYPE", "근거 없는 홍보 표현",
     r"(?:폭발적\s*성장|업계\s*최고|커리어\s*점프|완벽한\s*기회|최고의\s*기회)"),
    ("REPEATED_CTA", "말미 상투적 지원 권유 반복",
     r"관심\s*(?:이\s*)?있으시(?:면|다면)[^\n]{0,40}이력서"),
]

_COMPILED = [(rid, desc, re.compile(pat, re.M)) for rid, desc, pat in BANNED]


@dataclass(frozen=True)
class Hit:
    rule: str
    description: str
    match: str
    line: int


def scan(text: str) -> list[Hit]:
    """본문에서 금지 항목을 찾는다. 빈 결과가 곧 합격은 아니다(의미 검토는 별도)."""
    hits: list[Hit] = []
    for rid, desc, rx in _COMPILED:
        for m in rx.finditer(text):
            line = text.count("\n", 0, m.start()) + 1
            hits.append(Hit(rid, desc, m.group(0).strip(), line))
    return sorted(hits, key=lambda h: (h.line, h.rule))


def greeting_ok(text: str) -> tuple[bool, str]:
    """인사말에서 회신을 안내했다면 말미에 같은 권유를 다시 붙이지 않는다."""
    head, tail = text[:600], text[-600:]
    head_cta = bool(re.search(r"(?:회신|수락)", head))
    tail_cta = bool(re.search(r"관심\s*(?:이\s*)?있으시|이력서와\s*함께\s*(?:역할|근무조건)", tail))
    if head_cta and tail_cta:
        return False, "인사말과 말미에 지원 권유가 중복된다"
    return True, "중복 없음"


def required_vs_preferred(requirement_text: str, preferred_text: str) -> tuple[bool, str]:
    """필수와 우대가 서로의 자리에 섞이지 않았는지 본다."""
    if not requirement_text.strip():
        return False, "자격요건이 비어 있다"
    if not preferred_text.strip():
        return True, "우대사항 없음(원문에 없을 수 있음)"
    if re.search(r"우대|더\s*좋아요|있으면\s*좋", requirement_text):
        return False, "자격요건 안에 우대 표현이 있다"
    if re.search(r"필수(?:입니다|조건)|반드시", preferred_text):
        return False, "우대사항 안에 필수 표현이 있다"
    return True, "필수/우대 분리됨"


# ── LinkedIn RPS InMail 전용 ──────────────────────────────
# 관계형 서비스라 본문이 목록이 아니라 이어지는 글이어야 한다(SOT L4·L5).

INMAIL_BANNED = [
    ("INMAIL_MARKDOWN", "마크다운 기호", r"(?:\*\*|^#{1,6}\s)"),
    ("INMAIL_EMOJI", "이모지", r"[\U0001F300-\U0001FAFF☀-➿]"),
    ("INMAIL_RAW_VAR", "치환되지 않은 원시 변수", r"\{\{[^}]*\}\}"),
    ("INMAIL_NAME_HARDCODED", "특정 후보자 이름이 본문에 박힘",
     r"안녕하세요[,\s]*[가-힣]{2,4}\s*(?:님|매니저님|팀장님|책임님|수석님)"),
    ("INMAIL_STOCK_PHRASE", "상투적 영업 문구",
     r"(?:귀하의\s*(?:경력|이력)을\s*주목|좋은\s*기회가\s*될\s*것|모시고\s*싶습니다)"),
]
_INMAIL = [(i, d, re.compile(p, re.M)) for i, d, p in INMAIL_BANNED]


def scan_inmail(text: str) -> list[Hit]:
    """InMail 본문에서 금지 항목을 찾는다. 일반 금지 규칙과 함께 쓴다."""
    hits = list(scan(text))
    for rid, desc, rx in _INMAIL:
        for m in rx.finditer(text):
            hits.append(Hit(rid, desc, m.group(0).strip()[:40],
                            text.count("\n", 0, m.start()) + 1))
    return sorted(hits, key=lambda h: (h.line, h.rule))


def inmail_tone(text: str) -> dict[str, object]:
    """AI 티가 나는 신호를 센다. 판정이 아니라 사람이 볼 지표다.

    bullet_ratio 는 불릿 줄 비율, ending_repeat 는 가장 흔한 문장 어미의 비율이다.
    둘 다 높으면 목록처럼 읽히고 기계가 쓴 티가 난다.
    """
    lines = [ln for ln in text.split("\n") if ln.strip()]
    bullets = [ln for ln in lines if re.match(r"^\s*[-*·•]\s", ln)]
    sentences = [s for s in re.split(r"(?<=[.!?])\s+|\n", text) if s.strip()]
    endings: dict[str, int] = {}
    for s in sentences:
        tail = s.strip()[-4:]
        if tail:
            endings[tail] = endings.get(tail, 0) + 1
    top = max(endings.values()) if endings else 0
    return {
        "lines": len(lines),
        "bullet_ratio": round(len(bullets) / len(lines), 3) if lines else 0.0,
        "sentences": len(sentences),
        "ending_repeat": round(top / len(sentences), 3) if sentences else 0.0,
        "paragraphs": len([p for p in text.split("\n\n") if p.strip()]),
    }
