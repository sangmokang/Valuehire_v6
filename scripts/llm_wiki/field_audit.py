"""LLM 위키 필드 채움률 감사기 (읽기 전용).

정본 docs/sot/llm-wiki.md 의 "최소 채움률" 표를 문턱으로 읽어 운영 Supabase 를 HEAD count 로 집계한다.
판정: 문턱 미달·검사 대상 0건·문턱 필드가 집계에 없음 → FAIL, 조회 오류 → NOT_RUN, 그 외 PASS.
자격증명이 없으면 rc 2(NOT_RUN). 값(개인정보)은 읽지 않고 건수만 센다.
사용: python3 scripts/llm_wiki/field_audit.py --env <.env.local> [--sot docs/sot/llm-wiki.md]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

FIELD_ROW_RE = re.compile(r"^\|\s*([a-z_]+)\.([a-z_]+)\s*\|\s*([^|]*)\|")
NUMBER_RE = re.compile(r"^[0-9]+(?:\.[0-9]+)?$")


@dataclass(frozen=True)
class FieldStat:
    table: str
    column: str
    total: int | None
    nulls: int | None
    error: str | None = None


@dataclass
class Verdict:
    status: str = "PASS"
    failures: list[str] = field(default_factory=list)


def parse_thresholds(markdown: str) -> dict[tuple[str, str], float]:
    found: dict[tuple[str, str], float] = {}
    for line in markdown.splitlines():
        m = FIELD_ROW_RE.match(line.strip())
        if not m:
            continue
        key, raw = (m.group(1), m.group(2)), m.group(3).strip()
        if not NUMBER_RE.match(raw):
            raise ValueError(f"{key[0]}.{key[1]}: 최소 채움률이 숫자가 아니다: {raw!r}")
        if key in found:
            raise ValueError(f"{key[0]}.{key[1]}: 문턱 행이 중복된다")
        found[key] = float(raw)
    if not found:
        raise ValueError("최소 채움률 표(| 객체.필드 | 숫자 |)를 찾지 못했다")
    return found


def judge(stats: list[FieldStat], thresholds: dict[tuple[str, str], float]) -> Verdict:
    verdict = Verdict()
    by_key = {(s.table, s.column): s for s in stats}
    for key, floor in sorted(thresholds.items()):
        name = f"{key[0]}.{key[1]}"
        stat = by_key.get(key)
        if stat is None:
            verdict.failures.append(f"{name}: 집계 없음")
            continue
        if stat.error is not None:
            verdict.status = "NOT_RUN"
            verdict.failures.append(f"{name}: 조회 오류 {stat.error}")
            continue
        if not stat.total:
            verdict.failures.append(f"{name}: 검사 대상 0건")
            continue
        rate = 100.0 * (stat.total - stat.nulls) / stat.total
        if rate < floor:
            verdict.failures.append(f"{name}: 채움률 {rate:.1f}% < 최소 {floor:g}%")
    if verdict.status != "NOT_RUN" and verdict.failures:
        verdict.status = "FAIL"
    return verdict


def _count(base: str, key: str, table: str, filt: str) -> int:
    req = urllib.request.Request(
        f"{base}/rest/v1/{table}?select=*&limit=0{filt}", method="HEAD",
        headers={"apikey": key, "Authorization": f"Bearer {key}", "Prefer": "count=exact", "Range": "0-0"},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        cr = resp.headers.get("content-range", "")
    if "/" not in cr:
        raise ValueError(f"content-range 없음: {cr!r}")
    return int(cr.split("/")[1])


def collect(base: str, key: str, thresholds: dict[tuple[str, str], float]) -> list[FieldStat]:
    stats: list[FieldStat] = []
    for table, column in sorted(thresholds):
        try:
            total = _count(base, key, table, "")
            nulls = _count(base, key, table, f"&{column}=is.null")
            stats.append(FieldStat(table, column, total, nulls))
        except (OSError, ValueError) as exc:
            stats.append(FieldStat(table, column, None, None, error=str(exc)[:120]))
    return stats


def load_creds(env_path: Path) -> tuple[str, str]:
    values: dict[str, str] = {}
    for line in env_path.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.startswith("#"):
            k, _, v = line.partition("=")
            values[k.strip()] = v.strip().strip('"')
    url, key = values.get("NEXT_PUBLIC_SUPABASE_URL"), values.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        print("NOT_RUN: 자격증명 없음", file=sys.stderr)
        raise SystemExit(2)
    return url.rstrip("/"), key


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--env", required=True, type=Path)
    ap.add_argument("--sot", type=Path, default=Path(__file__).resolve().parents[2] / "docs" / "sot" / "llm-wiki.md")
    args = ap.parse_args(argv)
    thresholds = parse_thresholds(args.sot.read_text(encoding="utf-8"))
    base, key = load_creds(args.env)
    stats = collect(base, key, thresholds)
    verdict = judge(stats, thresholds)
    for s in stats:
        rate = "" if s.error or not s.total else f"{100.0 * (s.total - s.nulls) / s.total:.1f}%"
        print(f"{s.table}.{s.column:<28} total={s.total} null={s.nulls} filled={rate} {s.error or ''}")
    print(json.dumps({"VERDICT": verdict.status, "failures": verdict.failures}, ensure_ascii=False))
    return {"PASS": 0, "FAIL": 1, "NOT_RUN": 2}[verdict.status]


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
