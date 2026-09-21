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
# 구조는 사장님 골든 샘플(outputs/_golden/rps_*_golden.txt)에서 역산했다.
# 골든은 `■ 섹션` + `• 불릿` + `**볼드**` 로 쓰여 있다. 2026-09-22 오전에
# 이 기호들을 INMAIL_MARKDOWN 으로 금지했다가 골든 2건을 모두 불합격시켰다.
# 금지 대상은 서식이 아니라 사람이 쓰지 않는 문구(상투어·이모지·원시 변수)다.

INMAIL_BANNED = [
    # 허용하는 서식은 **볼드**·■·• 세 가지뿐이다. 2026-09-22 Codex V1 결함 4:
    # INMAIL_MARKDOWN 을 통째로 지운 탓에 `## 제목`·`- 불릿`·`__강조` 까지
    # 함께 통과했다. 골든 2건에는 이 표기가 한 번도 없다.
    ("INMAIL_FOREIGN_MARKUP", "허용하지 않는 마크다운 표기",
     r"^#{1,6}\s|^\s*[-*]\s+\S|__[^_\n]+__"),
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
    2026-09-22 오전까지는 "불릿 비율이 높으면 AI 티"로 읽었는데, 골든 실측이
    0.444 / 0.462 로 나와 해석이 뒤집혔다. 불릿 비율이 **너무 낮을 때**가
    위험 신호다(조건을 산문에 녹여 읽히지 않게 만든 것). ending_repeat 만
    높을수록 나쁘다 — 골든은 0.143 / 0.074 다.
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
        # 골든 범위를 벗어난 방향을 한 단어로 알려준다.
        "bullet_verdict": (
            "too_few" if lines and len(bullets) / len(lines) < 0.25 else "ok"),
    }


# ── 골든 구조 검사 ────────────────────────────────────────
# 서식을 금지하는 대신 "골든 구조를 벗어났는가"를 잰다. 아래 수치는
# 골든 2건의 실측값(섹션 5/5, 불릿 12/12, 볼드 12/7, 1,308자/1,067자)에서
# 여유를 두고 내린 하한이다. 상한은 SOT L1 의 1,899자만 둔다.
MIN_SECTIONS = 4
MIN_BULLETS = 8
MIN_BOLD_PAIRS = 5
HARD_CAP = 1899

SIGNATURE_LINE = "테크 전문 서치펌 밸류커넥트의 헤드헌터 강상모"

# G7 — 후보자에게 보내는 제안에 네거티브 지표를 싣지 않는다.
# 매출·성장·투자·사용자 규모는 남기고 손실과 인원만 뺀다.
NEGATIVE_METRIC = re.compile(r"영업\s*(?:손실|적자)|당기\s*순손실|인원\s*[:：]?\s*\d+\s*명")

# G4 — 업계에서 영문 그대로 쓰는 용어를 한글로 풀면 원문 신호가 사라진다.
# 음차(컬처핏·레퍼런스 체크)가 아니라 "번역해 버린 말"만 막는다.
TRANSLATED_TERMS = {
    "평판 조회": "Reference Check",
    "조직 적합도": "Culture Fit",
    "문화 적합성": "Culture Fit",
    "핵심성과지표": "KPI",
    "데이터 웨어하우스": "DW",
    "비즈니스 인텔리전스": "BI",
    "감사 추적": "Audit Trail",
    "교차 기능": "Cross-functional",
    "부서 간 협업": "Cross-functional",
    "최소 기능 제품": "MVP",
    "최소 실행 단위": "MVP",
    "목표 및 핵심 결과": "OKR",
    "구조화 질의": "SQL/Query",
}


def inmail_structure(text: str) -> list[Hit]:
    """골든 구조를 벗어난 지점을 찾는다. 빈 결과가 곧 좋은 글은 아니다.

    `scan_inmail` 이 "쓰면 안 되는 문구"를 본다면 이쪽은 "있어야 하는 뼈대"를 본다.
    둘을 나눈 이유: 금지 규칙만으로는 산문 일색 원고를 걸러내지 못한다.
    """
    hits: list[Hit] = []

    def add(rule: str, desc: str, match: str, line: int = 1) -> None:
        hits.append(Hit(rule, desc, match, line))

    sections = re.findall(r"^■ .+$", text, re.M)
    if len(sections) < MIN_SECTIONS:
        add("INMAIL_NO_SECTION",
            f"■ 섹션 헤더가 {MIN_SECTIONS}개 미만 (G1)", f"{len(sections)}개")

    bullets = re.findall(r"^• .+$", text, re.M)
    if len(bullets) < MIN_BULLETS:
        add("INMAIL_NO_BULLET",
            f"• 불릿이 {MIN_BULLETS}개 미만 — 산문만으로는 조건이 읽히지 않는다 (G2)",
            f"{len(bullets)}개")

    bold = len(re.findall(r"\*\*", text)) // 2
    if bold < MIN_BOLD_PAIRS:
        add("INMAIL_NO_BOLD",
            f"**볼드**가 {MIN_BOLD_PAIRS}쌍 미만 — 숫자·핵심 역량을 강조하지 않았다 (G3)",
            f"{bold}쌍")

    # 섹션 총수만 세면 "■ Position | ..." 한 줄만 망가져도 4개가 남아 통과한다.
    # 2026-09-22 변이 실증에서 살아남은 지점이라 이름을 따로 건다.
    if not re.search(r"^■ Position \| .+$", text, re.M):
        add("INMAIL_NO_POSITION_HEADER",
            "■ Position | {포지션명} 줄이 없다 (G1)", "(없음)")

    if SIGNATURE_LINE not in text:
        add("INMAIL_SIGNATURE", "호칭이 골든과 다르다 (G5)", SIGNATURE_LINE)

    for m in NEGATIVE_METRIC.finditer(text):
        add("INMAIL_NEGATIVE_METRIC", "네거티브 지표는 제안 본문에서 뺀다 (G7)",
            m.group(0), text.count("\n", 0, m.start()) + 1)

    for ko, en in TRANSLATED_TERMS.items():
        at = text.find(ko)
        if at >= 0:
            add("INMAIL_TERM_TRANSLATED", f"영문 용어를 한글로 풀었다 — {en} (G4)",
                ko, text.count("\n", 0, at) + 1)

    tail = text[-200:]
    if not re.search(r"LinkedIn\s*수락|간단한\s*회신", tail):
        add("INMAIL_CLOSING", "클로징이 LinkedIn 수락·간단한 회신으로 끝나지 않는다 (G10)",
            tail.splitlines()[-1] if tail.strip() else "(빈 클로징)")

    if len(text) > HARD_CAP:
        add("INMAIL_TOO_LONG", f"본문이 {HARD_CAP}자를 넘는다 (SOT L1)", f"{len(text)}자")

    return sorted(hits, key=lambda h: (h.line, h.rule))
