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

TABLE_HEADER_RE = re.compile(r"^\|\s*객체\s*\|\s*anon 허용 건수\s*\|$")
OBJECT_ROW_RE = re.compile(r"^\|\s*([a-z_]+)\s*\|\s*([0-9]+)\s*\|$")
SEPARATOR_RE = re.compile(r"^\|[\s\-:|]+\|$")
# SOT §4-b 가 반드시 품어야 하는 객체. 행이 빠지거나 형식이 깨지면 정본 오류로 거부한다(Codex 2026-10-14 결함 4).
REQUIRED_OBJECTS = frozenset({
    "profile_archives", "gmail_messages", "gmail_sync_state", "candidates",
    "pipeline_candidates_active", "pipeline_candidates_archive", "unified_candidate_history_view",
})


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
    """`| 객체 | anon 허용 건수 |` 머리글 아래의 표를 끝(빈 줄 또는 표 아닌 줄)까지 엄격히 읽는다.
    표 안의 모든 데이터 행은 `| <식별자> | 0 |` 이어야 하며, 형식이 다른 행·0 이 아닌 값·중복·필수 객체 누락은 ValueError."""
    lines = markdown.splitlines()
    starts = [i for i, line in enumerate(lines) if TABLE_HEADER_RE.match(line.strip())]
    if len(starts) != 1:
        raise ValueError(f"anon 허용 건수 표 머리글이 {len(starts)}개다(정확히 1개여야 한다)")
    objects: list[str] = []
    for line in lines[starts[0] + 1:]:
        stripped = line.strip()
        if not stripped.startswith("|"):
            break
        if SEPARATOR_RE.match(stripped):
            continue
        m = OBJECT_ROW_RE.match(stripped)
        if not m:
            raise ValueError(f"anon 표 행 형식 오류(| 식별자 | 0 | 이어야 한다): {stripped!r}")
        name, raw = m.group(1), m.group(2)
        if raw != "0":
            raise ValueError(f"{name}: anon 허용 건수는 0 만 허용한다: {raw!r}")
        if name in objects:
            raise ValueError(f"{name}: 객체 행이 중복된다")
        objects.append(name)
    missing = REQUIRED_OBJECTS - set(objects)
    if missing:
        raise ValueError(f"anon 표에 필수 객체가 없다: {sorted(missing)}")
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


def _denial_lookup(base: str, key: str, name: str, opener=urllib.request.urlopen) -> dict:
    """HEAD 응답에는 본문이 없어 거부 사유를 알 수 없다. 같은 객체를 GET(limit=0)으로 다시 쳐서 오류 본문만 읽는다(행은 받지 않는다)."""
    req = urllib.request.Request(f"{base}/rest/v1/{name}?select=*&limit=0", headers={"apikey": key, "Authorization": f"Bearer {key}"})
    try:
        with opener(req, timeout=60):
            return {}
    except urllib.error.HTTPError as exc:
        return _error_body(exc)


def collect(base: str, key: str, objects: list[str], counter=_count, denial_lookup=_denial_lookup) -> list[ObjectStat]:
    stats: list[ObjectStat] = []
    for name in objects:
        try:
            stats.append(ObjectStat(name, counter(base, key, name, "")))
        except urllib.error.HTTPError as exc:
            body = _error_body(exc) or (denial_lookup(base, key, name) if exc.code in (401, 403) else {})
            # 차단 성공은 Postgres 권한 거부(42501)로 확인된 응답만이다. 무효 키의 401("Invalid API key")은
            # anon 권한을 검사한 것이 아니므로 조회 오류(NOT_RUN)다(Codex 2026-10-14 결함 1).
            if exc.code in (401, 403) and body.get("code") == "42501":
                stats.append(ObjectStat(name, 0))
            else:
                stats.append(ObjectStat(name, None, error=f"HTTP {exc.code} {body.get('message', '')}"[:120]))
        except (OSError, ValueError) as exc:
            stats.append(ObjectStat(name, None, error=str(exc)[:120]))
    return stats


def _error_body(exc: urllib.error.HTTPError) -> dict:
    try:
        raw = exc.read()
        data = json.loads(raw.decode("utf-8")) if raw else {}
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError, AttributeError):
        return {}


def key_is_valid(base: str, key: str, opener=urllib.request.urlopen, probe: str = "profile_archives") -> bool:
    """양성 대조군: 키가 인증을 통과하는지 본다. 탐침 객체에 2xx 가 오거나, 권한 거부(42501)로 거부되면 인증은 된 것이다.
    "Invalid API key"(Supabase 게이트웨이 401)면 키가 죽은 것이고 감사 자체를 돌리지 않는다.
    (PostgREST 루트 /rest/v1/ 는 Supabase 가 anon 키에 401 을 돌려 탐침으로 쓸 수 없다 — 2026-10-14 실측.)"""
    req = urllib.request.Request(f"{base}/rest/v1/{probe}?select=*&limit=0", headers={"apikey": key, "Authorization": f"Bearer {key}"})
    try:
        with opener(req, timeout=60) as resp:
            return 200 <= getattr(resp, "status", 200) < 300
    except urllib.error.HTTPError as exc:
        return _error_body(exc).get("code") == "42501"


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
    if not key_is_valid(base, key, probe=objects[0]):
        print(json.dumps({"VERDICT": "NOT_RUN", "failures": ["anon 키가 인증을 통과하지 못한다(Invalid API key) — 차단 여부를 판정할 수 없다"]}, ensure_ascii=False))
        return 2
    print(f"anon key probe: authenticated (probe={objects[0]})")
    stats = collect(base, key, objects)
    verdict = judge(stats, objects)
    for s in stats:
        print(f"anon {s.name:<32} count={s.count} {s.error or ''}")
    print(json.dumps({"VERDICT": verdict.status, "failures": verdict.failures}, ensure_ascii=False))
    return {"PASS": 0, "FAIL": 1, "NOT_RUN": 2}[verdict.status]


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
