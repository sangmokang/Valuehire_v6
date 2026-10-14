"""로컬 아카이버 SQLite 의 structured_json 을 운영 profile_archives 에 채운다.

정본: docs/sot/llm-wiki.md §복구 ①. 기본은 dry-run(쓰기 0건). --apply 에서만 PATCH 한다.
보호 계약:
  - 원격에 같은 local_id 행이 없으면 보내지 않는다(부분 행 INSERT 금지).
  - 원격 structured_json 이 이미 있으면 보내지 않는다. 서버측에도 structured_json=is.null 을 붙여
    계획 이후 다른 주체가 채운 행을 덮어쓰지 않는다(매치 0행이면 "쓰지 않음"으로 센다).
  - 쓰기 1건마다 장부 2줄(intent → done|error; local_id, sha256(원문), canonical(정규화 지문), matched)을 남긴다.
  - 되돌리기(--rollback)는 done·matched=1 행 중 원격 현재 값이 장부에 기록된 우리 값과 같은(정규화 지문 일치) 행만,
    읽은 스냅샷의 md5 를 서버 필터(계산 칼럼 llm_wiki_structured_md5, v4 마이그레이션 20261014160000)로 붙여 null 로 한다.
  - 자격증명이 없으면 rc 2(NOT_RUN). 조용히 0건 성공으로 접지 않는다.
사용:
  python3 scripts/llm_wiki/backfill_structured_profiles.py --db <archive.db> --env <.env.local> [--apply] [--limit N]
  python3 scripts/llm_wiki/backfill_structured_profiles.py --db … --env … --rollback [--apply]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import sys
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

BATCH = 200


@dataclass(frozen=True)
class LocalRow:
    local_id: str
    site: str
    structured_json: str


@dataclass
class Plan:
    to_fill: list[LocalRow] = field(default_factory=list)
    skipped_absent: list[str] = field(default_factory=list)
    skipped_filled: list[str] = field(default_factory=list)
    skipped_invalid: list[str] = field(default_factory=list)


@dataclass
class ApplyResult:
    written: int = 0
    unmatched: list[str] = field(default_factory=list)


def _valid_structured(text: str) -> bool:
    """최소 내용 규약: dict, _meta.source·_meta.input_hash 가 비어 있지 않은 문자열, _meta 외 non-null 값 1개 이상."""
    try:
        obj = json.loads(text)
    except (ValueError, TypeError):
        return False
    if not isinstance(obj, dict):
        return False
    meta = obj.get("_meta")
    if not isinstance(meta, dict):
        return False
    for key in ("source", "input_hash"):
        if not isinstance(meta.get(key), str) or not meta[key]:
            return False
    return any(v is not None for k, v in obj.items() if k != "_meta")


def plan_backfill(local_rows: list[LocalRow], remote_state: dict[str, bool]) -> Plan:
    """remote_state[local_id]: True=이미 채워짐, False=비어 있음, 키 없음=원격 행 없음."""
    plan = Plan()
    for row in local_rows:
        if not _valid_structured(row.structured_json):
            plan.skipped_invalid.append(row.local_id)
        elif row.local_id not in remote_state:
            plan.skipped_absent.append(row.local_id)
        elif remote_state[row.local_id]:
            plan.skipped_filled.append(row.local_id)
        else:
            plan.to_fill.append(row)
    return plan


def apply_plan(transport, plan: Plan, ledger_path: Path, *, apply: bool) -> ApplyResult:
    result = ApplyResult()
    if not apply:
        return result
    with ledger_path.open("a", encoding="utf-8") as ledger:
        def record(entry: dict) -> None:
            ledger.write(json.dumps(entry, ensure_ascii=False) + "\n")
            ledger.flush()

        for row in plan.to_fill:
            query = f"local_id=eq.{urllib.parse.quote(row.local_id, safe='')}&structured_json=is.null"
            # sha256 = 로컬 원문 지문(쓰기 당시 소유권 증거), canonical = 정규화 지문(원격 text 저장값과 대조용)
            stamp = {"local_id": row.local_id, "sha256": _sha256(row.structured_json), "canonical": canonical_digest(row.structured_json)}
            # 쓰기 전 intent 를 먼저 남긴다. 응답을 못 받은 행은 intent 만 남아 readback 대조 대상이 된다.
            record({**stamp, "phase": "intent"})
            try:
                matched = transport.patch(query, {"structured_json": json.loads(row.structured_json)})
            except Exception as exc:  # 어떤 전송 오류든 장부에 남기고 그대로 전파한다(은폐 금지)
                record({**stamp, "phase": "error", "error": f"{type(exc).__name__}: {exc}"})
                raise
            record({**stamp, "phase": "done", "matched": matched})
            if matched == 1:
                result.written += 1
            else:
                result.unmatched.append(row.local_id)
    return result


@dataclass
class RollbackResult:
    reverted: list[str] = field(default_factory=list)
    would_revert: list[str] = field(default_factory=list)
    changed_elsewhere: list[str] = field(default_factory=list)
    already_null: list[str] = field(default_factory=list)
    not_ours: list[str] = field(default_factory=list)
    local_changed: list[str] = field(default_factory=list)  # 장부 지문 ≠ 현재 로컬 원문 → 소유권을 증명 못 해 손대지 않음


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def canonical_digest(text: str) -> str:
    """키 순서·공백을 정규화한 JSON 지문. 원격(text 칼럼에 저장된 직렬화)과 로컬 원문을 비교할 때 쓴다."""
    obj = json.loads(text) if isinstance(text, str) else text
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()


def _owned_from_ledger(ledger_path: Path) -> tuple[dict[str, dict], list[str]]:
    """done·matched=1 의 첫 장부 행(쓰기 당시 지문 포함)과, 그 밖의 local_id(경쟁 쓰기·응답 유실) 목록."""
    ours: dict[str, dict] = {}
    others: list[str] = []
    for line in ledger_path.read_text(encoding="utf-8").splitlines():
        entry = json.loads(line)
        lid = entry["local_id"]
        if entry.get("phase") == "done" and entry.get("matched") == 1:
            ours.setdefault(lid, entry)
        elif lid not in others:
            others.append(lid)
    return ours, [lid for lid in others if lid not in ours]


def _expected_canonical(entry: dict, local: str | None) -> str | None:
    """우리가 보낸 값의 정규화 지문. 신규 장부는 canonical 을 직접 갖고, 구 장부는 현재 로컬 원문의 sha256 이
    기록값과 같을 때만 로컬 원문에서 계산한다(재추출로 바뀐 로컬 값은 소유권 증거가 아니다)."""
    if entry.get("canonical"):
        return entry["canonical"]
    if local is None or _sha256(local) != entry.get("sha256"):
        return None
    return canonical_digest(local)


def rollback_from_ledger(transport, ledger_path: Path, local_by_id: dict[str, str], *, apply: bool) -> RollbackResult:
    """되돌리기(Codex 2026-10-14 1차 결함 2·2차 결함 1·2 반영).
    - 대상: 장부 done·matched=1 행. matched=0(경쟁 쓰기)·intent 만 남은 행(응답 유실)은 not_ours 로 보고만 한다.
    - 소유권: 장부에 기록된 쓰기 당시 지문(canonical, 또는 sha256 이 현재 로컬 원문과 일치할 때의 로컬 값)과
      원격 현재 값의 정규화 지문이 같을 때만. 로컬이 재추출돼 지문이 다르면 local_changed.
    - 원자성: PATCH 에 읽은 스냅샷의 md5 를 서버 필터(계산 칼럼 llm_wiki_structured_md5)로 붙여 읽기 이후의
      경쟁 갱신은 0행 매치 → changed_elsewhere. 서버 조건 없이 null 로 쓰는 경로는 없다."""
    result = RollbackResult()
    ours, result.not_ours = _owned_from_ledger(ledger_path)
    remote_values = transport.get_remote_values(list(ours)) if ours else {}
    for lid, entry in ours.items():
        remote = remote_values.get(lid)
        if remote is None:
            result.already_null.append(lid)
            continue
        expected = _expected_canonical(entry, local_by_id.get(lid))
        if expected is None:
            result.local_changed.append(lid)
            continue
        if canonical_digest(remote) != expected:
            result.changed_elsewhere.append(lid)
            continue
        if not apply:
            result.would_revert.append(lid)
            continue
        snapshot_md5 = hashlib.md5(remote.encode("utf-8")).hexdigest()
        query = (f"local_id=eq.{urllib.parse.quote(lid, safe='')}&structured_json=not.is.null"
                 f"&llm_wiki_structured_md5=eq.{snapshot_md5}")
        if transport.patch(query, {"structured_json": None}) == 1:
            result.reverted.append(lid)
        else:
            result.changed_elsewhere.append(lid)
    return result


def load_creds(env_path: Path) -> tuple[str, str]:
    values: dict[str, str] = {}
    for line in env_path.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.startswith("#"):
            key, _, val = line.partition("=")
            values[key.strip()] = val.strip().strip('"')
    url, key = values.get("NEXT_PUBLIC_SUPABASE_URL"), values.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        print("NOT_RUN: NEXT_PUBLIC_SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY 없음", file=sys.stderr)
        raise SystemExit(2)
    return url, key


def load_local_rows(db_path: Path, limit: int | None) -> list[LocalRow]:
    uri = f"file:{db_path}?mode=ro"
    sql = "SELECT id, site, structured_json FROM archives WHERE structured_json IS NOT NULL AND structured_json <> '' ORDER BY captured_at"
    if limit:
        sql += f" LIMIT {int(limit)}"
    with sqlite3.connect(uri, uri=True) as conn:
        return [LocalRow(str(i), str(s), str(j)) for i, s, j in conn.execute(sql)]


class RestTransport:
    """PostgREST 전송. 읽기는 GET, 쓰기는 PATCH(return=representation 으로 매치 행 수 readback)."""

    def __init__(self, url: str, key: str, opener=urllib.request.urlopen):
        self.base = url.rstrip("/") + "/rest/v1/profile_archives"
        self.headers = {"apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json"}
        self._open = opener  # 시험에서 표준 라이브러리 요청 객체를 받아 응답을 바꿔 끼운다

    def _call(self, method: str, query: str, body: dict | None, extra: dict[str, str]) -> list:
        data = json.dumps(body).encode("utf-8") if body is not None else None
        req = urllib.request.Request(f"{self.base}?{query}", data=data, method=method, headers={**self.headers, **extra})
        with self._open(req, timeout=60) as resp:
            raw = resp.read().decode("utf-8")
        return json.loads(raw) if raw else []

    def get_remote_state(self, local_ids: list[str]) -> dict[str, bool]:
        state: dict[str, bool] = {}
        for i in range(0, len(local_ids), BATCH):
            chunk = local_ids[i:i + BATCH]
            ids = ",".join(urllib.parse.quote(f'"{x}"', safe='"') for x in chunk)
            rows = self._call("GET", f"select=local_id,structured_json&local_id=in.({ids})", None, {})
            for r in rows:
                state[str(r["local_id"])] = r["structured_json"] is not None
        return state

    def get_remote_values(self, local_ids: list[str]) -> dict[str, str | None]:
        """되돌리기 대조용. 값은 지문 계산에만 쓰고 출력하지 않는다."""
        values: dict[str, str | None] = {}
        for i in range(0, len(local_ids), BATCH):
            chunk = local_ids[i:i + BATCH]
            ids = ",".join(urllib.parse.quote(f'"{x}"', safe='"') for x in chunk)
            for r in self._call("GET", f"select=local_id,structured_json&local_id=in.({ids})", None, {}):
                v = r["structured_json"]
                values[str(r["local_id"])] = None if v is None else (v if isinstance(v, str) else json.dumps(v, ensure_ascii=False))
        return values

    def patch(self, query: str, body: dict) -> int:
        rows = self._call("PATCH", f"{query}&select=local_id", body, {"Prefer": "return=representation"})
        return len(rows)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--db", required=True, type=Path)
    ap.add_argument("--env", required=True, type=Path)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--ledger", type=Path, default=None)
    ap.add_argument("--rollback", action="store_true", help="장부 기준 되돌리기(--apply 없으면 대상만 센다)")
    args = ap.parse_args(argv)
    url, key = load_creds(args.env)
    rows = load_local_rows(args.db, args.limit)
    transport = RestTransport(url, key)
    if args.rollback:
        ledger = args.ledger or Path.home() / "valuehire-private" / "llm-wiki" / "backfill-ledger.jsonl"
        rb = rollback_from_ledger(transport, ledger, {r.local_id: r.structured_json for r in rows}, apply=args.apply)
        print(json.dumps({"mode": "rollback-apply" if args.apply else "rollback-dry-run", "reverted": len(rb.reverted),
                          "would_revert": len(rb.would_revert), "changed_elsewhere": len(rb.changed_elsewhere),
                          "already_null": len(rb.already_null), "not_ours": len(rb.not_ours),
                          "local_changed": len(rb.local_changed), "ledger": str(ledger)}, ensure_ascii=False))
        return 0
    remote = transport.get_remote_state([r.local_id for r in rows])
    plan = plan_backfill(rows, remote)
    ledger = args.ledger or Path.home() / "valuehire-private" / "llm-wiki" / "backfill-ledger.jsonl"
    ledger.parent.mkdir(parents=True, exist_ok=True)
    result = apply_plan(transport, plan, ledger, apply=args.apply)
    print(json.dumps({
        "mode": "apply" if args.apply else "dry-run",
        "local_rows": len(rows), "remote_rows_found": len(remote),
        "to_fill": len(plan.to_fill), "skipped_absent": len(plan.skipped_absent),
        "skipped_filled": len(plan.skipped_filled), "skipped_invalid": len(plan.skipped_invalid),
        "written": result.written, "unmatched": len(result.unmatched), "ledger": str(ledger),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
