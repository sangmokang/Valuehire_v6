"""counter-AC — 원문에 없는 사실을 심어 넣으면 AC-6 검사기가 잡아야 한다.

양성 대조군(정상 JD 통과)과 음성 대조군(주입본 차단)을 한 쌍으로 잰다.
"""
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, "scripts")

from jd_channels.provenance import load_source_text, unsourced_facts  # noqa: E402
from jd_channels.units import load  # noqa: E402

SLUG = "bunjang__global-team-lead"
INJECTIONS = {
    "UNSOURCED_NUMBER": "- 원문에 없는 조건 경력 6년 이상",
    "UNSOURCED_CONDITION": "- 정규직 채용",
}


def main() -> int:
    units_path = Path(f"outputs/_units/{SLUG}.json")
    text = load_source_text(SLUG)
    if text is None:
        print(f"{SLUG}: 원문 없음 — 대조군을 세울 수 없다")
        return 1

    if unsourced_facts(load(units_path), text):
        print("양성 대조군 실패 — 정상 JD 가 이미 불합격이다")
        return 1
    print("양성 대조군 통과 — 정상 JD 위반 0건")

    raw = json.loads(units_path.read_text(encoding="utf-8"))
    for rule, injected in INJECTIONS.items():
        mutated = json.loads(json.dumps(raw))
        mutated["units"].append({
            "id": "ZZ9", "section": "conditions", "kind": "core",
            "meaning": "주입한 가짜 조건", "full": injected, "compact": injected,
            "source": mutated["source_url"],
        })
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "u.json"
            p.write_text(json.dumps(mutated, ensure_ascii=False), encoding="utf-8")
            rules = {h.rule for h in unsourced_facts(load(p), text)}
        print(f"{rule} 주입 -> {sorted(rules)}")
        if rule not in rules:
            print(f"{rule}: 주입한 가짜 사실을 못 잡았다")
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
