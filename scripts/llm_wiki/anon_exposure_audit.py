"""익명(anon) 키 노출 감사기 (읽기 전용).

정본 docs/sot/llm-wiki.md §4-b 의 `| 객체 | anon 허용 건수 |` 표를 읽어, 비로그인 anon 키로 각 객체의
건수를 HEAD count 로 센다. 허용 건수는 0 만 허용한다.
판정: 1건이라도 보임·검사 객체 0개·표에 있는데 집계 없음 → FAIL, 조회 오류 → NOT_RUN(rc 2), 그 외 PASS.
401/403 은 차단된 것이므로 0 으로 센다. 값(개인정보)은 읽지 않는다.
사용: python3 scripts/llm_wiki/anon_exposure_audit.py --env <.env.local> [--sot docs/sot/llm-wiki.md]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

if __package__ in (None, ""):  # 파일 경로로 실행하면 저장소 루트가 sys.path 에 없다
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.llm_wiki.field_audit import _count  # noqa: E402

OBJECT_ROW_RE = re.compile(r"^\|\s*([a-z_]+)\s*\|\s*([^|]*)\|")


@dataclass(frozen=True)
class ObjectStat:
    name: str
    count: int | None
    error: str | None = None


@dataclass
class Verdict:
    status: str = "PASS"
    failures: list[str] = field(default_factory=list)


def parse_anon_zero_objects(markdown: str) -> list[str]:
    objects: list[str] = []
    for line in markdown.splitlines():
        m = OBJECT_ROW_RE.match(line.strip())
        if not m:
            continue
        name, raw = m.group(1), m.group(2).strip()
        if raw != "0":
            raise ValueError(f"{name}: anon 허용 건수는 0 만 허용한다: {raw!r}")
        if name in objects:
            raise ValueError(f"{name}: 객체 행이 중복된다")
        objects.append(name)
    if not objects:
        raise ValueError("anon 허용 건수 표(| 객체 | 0 |)를 찾지 못했다")
    return objects


def judge(stats: list[ObjectStat], objects: list[str]) -> Verdict:
    verdict = Verdict()
    if not objects:
        verdict.failures.append("검사 객체 0개")
    by_name = {s.name: s for s in stats}
    for name in objects:
        stat = by_name.get(name)
        if stat is None:
            verdict.failures.append(f"{name}: 집계 없음")
        elif stat.error is not None:
            verdict.status = "NOT_RUN"
            verdict.failures.append(f"{name}: 조회 오류 {stat.error}")
        elif stat.count:
            verdict.failures.append(f"{name}: anon 노출 {stat.count}건")
    if verdict.status != "NOT_RUN" and verdict.failures:
        verdict.status = "FAIL"
    return verdict


def collect(base: str, key: str, objects: list[str], counter=_count) -> list[ObjectStat]:
    stats: list[ObjectStat] = []
    for name in objects:
        try:
            stats.append(ObjectStat(name, counter(base, key, name, "")))
        except urllib.error.HTTPError as exc:
            if exc.code in (401, 403):
                stats.append(ObjectStat(name, 0))
            else:
                stats.append(ObjectStat(name, None, error=f"HTTP {exc.code}"))
        except (OSError, ValueError) as exc:
            stats.append(ObjectStat(name, None, error=str(exc)[:120]))
    return stats


def key_is_valid(base: str, key: str, opener=urllib.request.urlopen) -> bool:
    return False  # RED 골격


def load_anon_creds(env_path: Path) -> tuple[str, str]:
    values: dict[str, str] = {}
    for line in env_path.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.startswith("#"):
            k, _, v = line.partition("=")
            values[k.strip()] = v.strip().strip('"')
    url, key = values.get("NEXT_PUBLIC_SUPABASE_URL"), values.get("NEXT_PUBLIC_SUPABASE_ANON_KEY")
    if not url or not key:
        print("NOT_RUN: anon 자격증명 없음", file=sys.stderr)
        raise SystemExit(2)
    return url.rstrip("/"), key


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--env", required=True, type=Path)
    ap.add_argument("--sot", type=Path, default=Path(__file__).resolve().parents[2] / "docs" / "sot" / "llm-wiki.md")
    args = ap.parse_args(argv)
    objects = parse_anon_zero_objects(args.sot.read_text(encoding="utf-8"))
    base, key = load_anon_creds(args.env)
    stats = collect(base, key, objects)
    verdict = judge(stats, objects)
    for s in stats:
        print(f"anon {s.name:<32} count={s.count} {s.error or ''}")
    print(json.dumps({"VERDICT": verdict.status, "failures": verdict.failures}, ensure_ascii=False))
    return {"PASS": 0, "FAIL": 1, "NOT_RUN": 2}[verdict.status]


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
