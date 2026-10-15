"""단위 정의 → 4채널 TXT 원고 + 검증. 산출물은 텍스트 원고다."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .checks import (
    greeting_ok, inmail_structure, required_vs_preferred, scan, scan_inmail,
)
from .conditions import missing as missing_conditions
from .measure import normalize_for_compare
from .render import PROFILES, Draft, render, sanitize_for_portal
from .units import JDSource, load

CHANNELS = ("gmail", "linkedin_rps", "saramin", "jobkorea")


@dataclass(frozen=True)
class Report:
    channel: str
    status: str
    codepoints: int
    utf16: int
    limit: int | None
    strategy: str
    dropped: tuple[str, ...]
    missing_core: tuple[str, ...]
    banned: tuple[str, ...]
    notes: tuple[str, ...]

    @property
    def ok(self) -> bool:
        return (self.status == "READY_DRAFT" and not self.missing_core
                and not self.banned and not self.notes)


def _missing_core(src: JDSource, draft: Draft) -> tuple[str, ...]:
    """core 단위의 의미가 원고에 실제로 남아 있는지 본다.

    키워드 하나가 아니라 단위가 실어나르는 문자열(compact 기준)을 통째로 찾는다.
    compact 는 full 의 부분집합이 아닐 수 있으므로 둘 중 하나라도 있으면 통과.
    """
    portal = PROFILES[draft.channel].portal
    body = normalize_for_compare(draft.body)
    missing = []
    for unit in src.units:
        if unit.kind != "core":
            continue
        if unit.id in draft.dropped_units:
            missing.append(unit.id)
            continue
        # 출력에 적용한 포털 치환을 기대값에도 똑같이 적용한다.
        # 그러지 않으면 정상 치환을 누락으로 오판한다.
        # RPS 는 단위의 rps 표현으로 렌더된다. 후보에서 빼면 정상 출력을
        # core 누락으로 오판한다(2026-09-22 실측: 37개 중 22개 오탐).
        cands = [normalize_for_compare(sanitize_for_portal(t, portal))
                 for t in (unit.full, unit.compact, unit.rps) if t]
        if not any(c and c in body for c in cands):
            missing.append(unit.id)
    return tuple(missing)


def verify(src: JDSource, draft: Draft) -> Report:
    profile = PROFILES[draft.channel]
    hits = scan(draft.full_text)
    notes: list[str] = []

    # RPS 는 전용 금지·구조 규칙이 따로 있다. 만들어 두고 부르지 않으면
    # 이모지가 든 원고도 ok=True 로 나온다(2026-09-22 Codex V1 결함 2 실측).
    if profile.key == "linkedin_rps":
        seen = {h.rule for h in hits}
        for hit in scan_inmail(draft.body) + inmail_structure(draft.body):
            if hit.rule not in seen:
                seen.add(hit.rule)
                hits.append(hit)

    # 조건 보존은 단위가 실어나르는 문자열과 독립으로 잰다. rps 표현 자체를
    # 정답으로 삼으면 rps 에서 조건을 지운 것을 발견할 수 없다(결함 1).
    for label in missing_conditions(src, draft.body):
        notes.append(f"조건 누락: {label}")

    ok, why = greeting_ok(draft.body)
    if not ok:
        notes.append(f"CTA: {why}")

    req = "\n".join(u.full for u in src.by_section("requirements"))
    pref = "\n".join(u.full for u in src.by_section("preferred"))
    ok, why = required_vs_preferred(req, pref)
    if not ok:
        notes.append(f"필수/우대: {why}")

    if not draft.measured.clean:
        notes.append(f"비가시 문자: {draft.measured.invisible}")

    # 평가 우선순위(※ Note)는 축약본에서도 남아야 한다.
    for unit in src.units:
        if unit.note and unit.id not in draft.dropped_units:
            body_n = normalize_for_compare(draft.body)
            portal = PROFILES[draft.channel].portal
            variants = tuple(normalize_for_compare(sanitize_for_portal(t, portal))
                             for t in (unit.full, unit.compact, unit.rps) if t)
            if not any(v and v in body_n for v in variants):
                notes.append(f"평가 우선순위 누락: {unit.id}")

    return Report(
        channel=draft.channel, status=draft.status,
        codepoints=draft.measured.codepoints, utf16=draft.measured.utf16_units,
        limit=profile.limit, strategy=draft.strategy, dropped=draft.dropped_units,
        missing_core=_missing_core(src, draft), banned=tuple(h.rule for h in hits),
        notes=tuple(notes),
    )


def run(units_path: str | Path, out_dir: str | Path) -> list[Report]:
    src = load(units_path)
    out = Path(out_dir) / f"{src.company_slug}__{src.position_slug}__{src.jd_id}"
    out.mkdir(parents=True, exist_ok=True)
    reports = []
    for channel in CHANNELS:
        draft = render(src, channel)
        report = verify(src, draft)
        (out / f"{channel}.txt").write_text(draft.full_text + "\n", encoding="utf-8")
        reports.append(report)
    (out / "_source.json").write_text(
        json.dumps({"source_url": src.source_url, "source_status": src.source_status,
                    "captured_at": src.captured_at, "notes": list(src.notes)},
                   ensure_ascii=False, indent=2), encoding="utf-8")
    return reports


def format_reports(reports: list[Report]) -> str:
    rows = []
    for r in reports:
        lim = str(r.limit) if r.limit else "-"
        mark = "PASS" if r.ok else "FAIL"
        rows.append(f"{mark}  {r.channel:13s} {r.codepoints:5d}자 (utf16 {r.utf16:5d}) "
                    f"/ 한도 {lim:>5s}  전략={r.strategy}  상태={r.status}")
        if r.dropped:
            rows.append(f"      생략 단위: {', '.join(r.dropped)}")
        if r.missing_core:
            rows.append(f"      core 누락: {', '.join(r.missing_core)}")
        if r.banned:
            rows.append(f"      금지 문구: {', '.join(sorted(set(r.banned)))}")
        for n in r.notes:
            rows.append(f"      {n}")
    return "\n".join(rows)
