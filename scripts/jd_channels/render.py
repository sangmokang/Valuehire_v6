"""채널별 원고를 단위(Unit)로부터 조립한다.

길이를 줄일 때 문자열을 자르지 않는다. 줄이는 수단은 두 가지뿐이다.
  (1) 단위의 compact 표현을 쓴다
  (2) core 가 아닌 단위를 생략한다
core 단위는 어떤 전략에서도 빠지지 않는다. 그래도 한도를 못 맞추면
그 채널은 NEEDS_LENGTH_DECISION 으로 남기고 누락을 숨기지 않는다.
"""
from __future__ import annotations

from dataclasses import dataclass

from .measure import (
    PORTAL_SAFE_SUBSTITUTE, Measured, compose, measure, over_limit, scan_portal_risk,
)
from .units import MAX_RANK, JDSource, Unit

SIGNATURE_NAME = "강상모"
SERVICE = "Valuehire(valuehire.cc)"


@dataclass(frozen=True)
class ChannelProfile:
    key: str
    limit: int | None
    # 섹션 묶음: (표시 제목 템플릿, [원본 섹션들])
    groups: tuple[tuple[str, tuple[str, ...]], ...]
    compact_default: bool
    show_headings: bool = True
    # 저장 시 문자를 바꿔버리는 포털이면 그 이름. 출력 직전에 안전 표기로 치환한다.
    portal: str | None = None


def _g(label: str, *sections: str) -> tuple[str, tuple[str, ...]]:
    return (label, sections)


GMAIL = ChannelProfile("gmail", None, (
    _g("[회사 소개 | {company}]", "company"),
    _g("[합류할 팀 | {team_name}]", "team"),
    _g("[도메인 특성]", "domain"),
    _g("[{position_short}의 역할]", "role"),
    _g("[주요 업무]", "duties"),
    _g("[자격요건]", "requirements"),
    _g("[우대사항]", "preferred"),
    _g("[쌓을 수 있는 경험]", "growth"),
    _g("[근무조건·채용 절차]", "conditions", "process"),
    _g("[지원 서류]", "documents"),
), compact_default=False)

RPS = ChannelProfile("linkedin_rps", 1900, (
    _g("[회사 소개 | {company}]", "company"),
    _g("[팀·역할]", "team", "domain", "role"),
    _g("[주요 업무]", "duties"),
    _g("[자격요건]", "requirements"),
    _g("[우대사항]", "preferred"),
    _g("[성장·조건]", "growth", "conditions", "process", "documents"),
), compact_default=True, show_headings=True)

SARAMIN = ChannelProfile("saramin", 4000, GMAIL.groups, compact_default=False,
                         portal="saramin")
JOBKOREA = ChannelProfile("jobkorea", 4000, GMAIL.groups, compact_default=False,
                          portal="jobkorea")

PROFILES = {p.key: p for p in (GMAIL, RPS, SARAMIN, JOBKOREA)}


def subject(src: JDSource) -> str:
    return f"[밸류커넥트] {src.company} {src.position} 포지션 제안"


def greeting(src: JDSource, *, short: bool) -> str:
    head = f"안녕하세요. 테크 서치펌 밸류커넥트의 헤드헌터 {SIGNATURE_NAME}입니다."
    if short:
        return (
            f"안녕하세요. 밸류커넥트 헤드헌터 {SIGNATURE_NAME}입니다.\n"
            f"{src.company} {src.position} 포지션의 핵심 내용을 제안드립니다. "
            "검토 후 편하게 회신해 주세요."
        )
    return (
        f"{head}\n\n"
        f"이직은 신중한 결정인 만큼, 먼저 회사와 역할을 살펴보실 수 있도록 "
        f"{src.company} {src.position} 포지션을 제안드립니다. 이력서를 보내주시면 "
        f"{SERVICE}를 통해 경력과 관심사에 맞는 채용 연결과 커리어 상담을 돕고 있습니다. "
        f"편하게 수락·회신해 주세요."
    )


def _keep(unit: Unit, min_drop_rank: int) -> bool:
    """min_drop_rank 이상인 단위를 버린다. core(rank 0)는 사다리 끝까지 남는다."""
    return unit.drop_rank == 0 or unit.drop_rank < min_drop_rank


def _flush(buffer: list[Unit], compact: bool) -> list[str]:
    """연속된 산문 단위를 한 문단으로 잇는다.

    압축본에서 단위를 한 줄씩 떼어 놓으면 "재고 단 1개 / 롱테일 수요" 처럼
    문장이 아니라 조각 목록이 된다. 같은 merge_group 은 쉼표로, 그 밖은
    공백으로 이어 사람이 읽는 문단을 만든다.
    """
    if not buffer:
        return []
    parts: list[str] = []
    for i, u in enumerate(buffer):
        text = u.text(compact).strip()
        if i and u.merge_group and u.merge_group == buffer[i - 1].merge_group:
            joiner = " " if parts[-1].endswith((",", "·", ":")) else ", "
            parts[-1] = f"{parts[-1]}{joiner}{text}"
        else:
            parts.append(text)
    buffer.clear()
    # 문단으로 이을 때 앞 조각이 문장으로 끝나지 않으면 마침표를 보충한다.
    # 서식 정리이며 단어·순서·조건은 건드리지 않는다.
    closed = [p if p.endswith((".", "!", "?", "다", "요", ")")) else p + "." for p in parts]
    return [" ".join(closed)]


def _render_group(units: list[Unit], compact: bool, *, used_headings: set[str],
                  show_headings: bool = True) -> str:
    """한 섹션 묶음의 본문.

    소제목(heading)은 그 아래로 단위를 모은다. 다만 그 소제목이 이미 그룹
    제목으로 쓰였다면 다시 출력하지 않는다 — 같은 말이 두 줄 연속으로 나온다.
    불릿이 아닌 산문 단위 앞에는 빈 줄을 넣어 문단을 나눈다.
    """
    lines: list[str] = []
    prose: list[Unit] = []
    current_heading: str | None = None
    for u in units:
        if u.heading and u.heading != current_heading:
            current_heading = u.heading
            if show_headings and u.heading not in used_headings:
                lines.extend(_flush(prose, compact))
                if lines:
                    lines.append("")
                lines.append(u.heading)
        body = u.text(compact).strip()
        if body.startswith("-"):
            lines.extend(_flush(prose, compact))
            lines.extend(body.split("\n"))
            continue
        if compact:
            prose.append(u)      # 압축본: 산문은 모아서 한 문단으로
            continue
        if lines and lines[-1] != u.heading:
            lines.append("")
        lines.extend(body.split("\n"))
    lines.extend(_flush(prose, compact))
    return "\n".join(lines)


def _labels(src: JDSource) -> dict[str, str]:
    team_units = src.by_section("team")
    team_name = team_units[0].heading if team_units and team_units[0].heading else src.company
    short = src.role_label or (
        src.position.split("(")[-1].rstrip(")") if "(" in src.position else src.position)
    return {"company": src.company, "team_name": team_name, "position_short": short}


def build_body(src: JDSource, profile: ChannelProfile, *,
               compact: bool, drop_kinds: int) -> str:
    labels = _labels(src)
    blocks: list[str] = []
    for title_tpl, sections in profile.groups:
        picked: list[Unit] = []
        for section in sections:
            picked.extend(u for u in src.by_section(section) if _keep(u, drop_kinds))
        if not picked:
            continue
        title = title_tpl.format(**labels)
        body = _render_group(picked, compact,
                             used_headings={title.strip("[]").split(" | ")[-1]},
                             show_headings=profile.show_headings)
        if not body.strip():
            continue
        blocks.append(f"{title}\n{body}")
    body = "\n\n".join(blocks)
    return sanitize_for_portal(body, profile.portal)


def sanitize_for_portal(text: str, portal: str | None) -> str:
    """포털이 저장하면서 바꾸거나 지울 문자를 미리 안전한 표기로 바꾼다.

    단어·순서·조건은 건드리지 않고 기호만 바꾼다. 원문 단위는 그대로 두고
    출력 단계에서만 적용하므로, 다른 채널의 표기는 영향받지 않는다.
    """
    if not portal:
        return text
    for bad in scan_portal_risk(text, portal):
        text = text.replace(bad, PORTAL_SAFE_SUBSTITUTE.get(bad, ""))
    return text


# 압축 순서(지시서 6절 3~6순위)를 전략 사다리로 고정한다.
# 위에서부터 시도하고, 한도에 들어가는 첫 전략을 채택한다.
# 한 칸에 한 등급씩만 버린다 — 2자가 모자라서 회사 정보 전체를 버리는 일을 막는다.
STRATEGIES: tuple[tuple[str, bool, int], ...] = (
    ("full", False, MAX_RANK + 1),
    ("compact", True, MAX_RANK + 1),
    ("compact_drop_r3", True, 3),
    ("compact_drop_r2", True, 2),
    ("compact_drop_r1", True, 1),
)


@dataclass(frozen=True)
class Draft:
    channel: str
    subject: str
    body: str
    full_text: str
    strategy: str
    dropped_units: tuple[str, ...]
    measured: Measured
    status: str

    def as_dict(self) -> dict:
        return {
            "channel": self.channel, "subject": self.subject,
            "strategy": self.strategy, "dropped_units": list(self.dropped_units),
            "status": self.status, "length": self.measured.as_dict(),
        }


def render(src: JDSource, channel: str) -> Draft:
    profile = PROFILES[channel]
    short_greeting = profile.key == "linkedin_rps"
    head = greeting(src, short=short_greeting)
    subj = subject(src)
    attempts: list[tuple[str, str, int, Measured]] = []

    for name, compact, drop in STRATEGIES:
        if not compact and profile.compact_default:
            continue  # RPS 는 처음부터 compact 로 시작한다
        body = f"{head}\n\n{build_body(src, profile, compact=compact, drop_kinds=drop)}"
        text = compose(subj, body)
        m = measure(text)
        attempts.append((name, body, drop, m))
        if profile.limit is None or not over_limit(m, profile.limit):
            dropped = tuple(u.id for u in src.units if not _keep(u, drop))
            return Draft(profile.key, subj, body, text, name, dropped, m, "READY_DRAFT")

    # 모든 전략이 한도를 넘었다 — core 만 남겨도 안 들어간다는 뜻이다.
    name, body, drop, m = attempts[-1]
    dropped = tuple(u.id for u in src.units if not _keep(u, drop))
    return Draft(profile.key, subj, body, compose(subj, body), name, dropped, m,
                 "NEEDS_LENGTH_DECISION")
