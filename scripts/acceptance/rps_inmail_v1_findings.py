#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Codex V1 적대검증(2026-09-22)이 실제 반례로 잡은 결함 5건의 회귀 검사.

각 항목은 "거부해야 하는 입력을 실제로 거부하는가"를 잰다. 정상 예제가
통과한다는 사실은 여기서 합격 근거가 아니다.
판정서: private-reviews/v1-rps-inmail-20260922.txt
"""
from __future__ import annotations

import copy
import json
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from jd_channels.checks import inmail_structure, scan_inmail  # noqa: E402
from jd_channels.clickup import render_task_body  # noqa: E402
from jd_channels.pipeline import verify  # noqa: E402
from jd_channels.render import PROFILES, render  # noqa: E402
from jd_channels.richtext import to_html  # noqa: E402
from jd_channels.units import load  # noqa: E402

WRTN = ROOT / "outputs/_units/wrtn__finance-data-analyst.json"
FAILS: list[str] = []


TOTAL = 0


def check(name: str, ok: bool, detail: str = "") -> None:
    global TOTAL
    TOTAL += 1
    print(f"{'ok  ' if ok else 'FAIL'} {name}{(' — ' + detail) if detail else ''}")
    if not ok:
        FAILS.append(name)


def _mutated_source(edits: dict[str, dict[str, str]]):
    """단위의 rps 표현만 바꾼 임시 JD 를 load() 로 다시 읽어 돌려준다."""
    raw = json.loads(WRTN.read_text(encoding="utf-8"))
    doc = copy.deepcopy(raw)
    for unit in doc["units"]:
        edit = edits.get(unit["id"])
        if edit:
            unit["rps"] = unit["rps"].replace(edit["old"], edit["new"])
    tmp = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8")
    tmp.write(json.dumps(doc, ensure_ascii=False))
    tmp.close()
    return load(tmp.name)


# ── 결함 1 — rps 에서 조건을 지우면 누락 검사가 잡아야 한다 ───────────
ATTACKS = {
    "연차 삭제": {"WQ1": {"old": "**5년+**", "new": "경험"},
                "WN1": {"old": "경력 5년 이상", "new": "경력"}},
    "대체 인정 조건 삭제": {"WQ1": {"old": "(또는 이에 준하는 경험)", "new": ""}},
    "고용형태 삭제": {"WN1": {"old": "정규직", "new": "근무"}},
    "전형 단계 삭제": {"WS1": {"old": "Reference Check → Offer", "new": "최종"}},
    "수습 삭제": {"WS2": {"old": "수습 3개월", "new": "시작"}},
}
for label, edits in ATTACKS.items():
    src = _mutated_source(edits)
    report = verify(src, render(src, "linkedin_rps"))
    check(f"F1-{label}", not report.ok,
          f"ok={report.ok} missing_core={report.missing_core} notes={report.notes}")

# 양성 대조군 — 손대지 않은 원본은 통과해야 한다
_src = load(WRTN)
_rep = verify(_src, render(_src, "linkedin_rps"))
check("F1-양성대조군", _rep.ok, f"ok={_rep.ok} notes={_rep.notes}")

# ── 결함 2 — verify() 가 InMail 전용 검사를 실행해야 한다 ────────────
src = load(WRTN)
draft = render(src, "linkedin_rps")
emoji = draft.body + "\n\U0001F642"
poisoned = type(draft)(draft.channel, draft.subject, emoji,
                       draft.full_text + "\n\U0001F642", draft.strategy,
                       draft.dropped_units, draft.measured, draft.status)
rep = verify(src, poisoned)
check("F2-이모지", not rep.ok, f"ok={rep.ok} banned={rep.banned} notes={rep.notes}")

stock = draft.body + "\n귀하의 경력을 주목하여 연락드립니다"
poisoned2 = type(draft)(draft.channel, draft.subject, stock, draft.full_text + stock,
                        draft.strategy, draft.dropped_units, draft.measured, draft.status)
check("F2-상투어", not verify(src, poisoned2).ok)

# ── 결함 3 — 살아남은 변이가 겨냥한 지점을 직접 검사 ────────────────
body = draft.body
check("F3-Mission헤더", "**Mission**" in body)
check("F3-클로징이마지막", body.rstrip().split("\n")[-1].startswith("관심 있으시면"))

order = [m.group(1) for m in re.finditer(r"^■ (.+)$", body, re.M)]
req_at = next((i for i, t in enumerate(order) if "Requirements" in t or "Looking for" in t), -1)
pref_at = next((i for i, t in enumerate(order) if "Preferred" in t), -1)
check("F3-필수우대순서", 0 <= req_at < pref_at, f"order={order}")

note_lines = [ln for ln in render(load(ROOT / "outputs/_units/bunjang__core-product-pm.json"),
                                  "linkedin_rps").body.split("\n") if "중고거래 경력 자체보다" in ln]
check("F3-평가우선순위표식", bool(note_lines) and note_lines[0].startswith("※ "),
      f"line={note_lines[:1]}")

html = to_html(body)
check("F3-화면변환불릿보존",
      html.count("<p>• ") == len(re.findall(r"^• ", body, re.M)),
      f"html={html.count('<p>• ')} body={len(re.findall(r'^• ', body, re.M))}")

ledger = render_task_body(src)
for section_label in ("근무조건", "채용 절차", "자격요건", "우대사항"):
    check(f"F3-ClickUp-{section_label}", section_label in ledger)

# core 누락 검사 자체가 살아 있는지 — 본문에서 core 단위를 지우면 잡아야 한다
_src2 = load(WRTN)
_d = render(_src2, "linkedin_rps")
_wn1 = next(u for u in _src2.units if u.id == "WN1")
_stripped = _d.body.replace(_wn1.rps_text(), "")
_holed = type(_d)(_d.channel, _d.subject, _stripped, _d.full_text, _d.strategy,
                  _d.dropped_units, _d.measured, _d.status)
_r2 = verify(_src2, _holed)
check("F3-core누락검사작동", "WN1" in _r2.missing_core,
      f"missing_core={_r2.missing_core}")

# ── 결함 4 — 다른 마크다운 표기는 여전히 거부해야 한다 ──────────────
for label, extra in (("헤딩", "\n## 자격"), ("하이픈불릿", "\n- 경력 3년"),
                     ("별표불릿", "\n* 경력 3년"), ("밑줄강조", "\n__강조__")):
    polluted = body + extra
    rules = {h.rule for h in scan_inmail(polluted)} | {h.rule for h in inmail_structure(polluted)}
    check(f"F4-{label}", bool(rules - {"INMAIL_TOO_LONG"}), f"rules={sorted(rules)}")

check("F4-정상원고오탐없음", not (scan_inmail(body) or inmail_structure(body)))

# ── 결함 5 — 1,899자 상한이 제목 포함 기준과 일치해야 한다 ──────────
check("F5-한도일치", PROFILES["linkedin_rps"].limit == 1899,
      f"limit={PROFILES['linkedin_rps'].limit}")

print()
print(f"CHECKED: {TOTAL}")
print(f"FAILED: {len(FAILS)}")
raise SystemExit(1 if FAILS else 0)
