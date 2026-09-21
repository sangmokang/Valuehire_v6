"""AC-6 — 단위 정의의 사실이 원문에 실제로 있는가.

2026-09-22 사고 회귀 방지: 사장님이 붙여넣은 번개장터 JD 두 건에 없는
`경력 6년 이상`·`정규직`·`채용 시 마감` 이 단위 정의에 들어갔고,
회사 조사에서 온 수치의 출처가 채용페이지로 잘못 적혀 있었다.
"""
import sys
from pathlib import Path

sys.path.insert(0, "scripts")

from jd_channels.provenance import load_source_text, unsourced_facts  # noqa: E402
from jd_channels.units import load  # noqa: E402

MIN_JD = 2


def main() -> int:
    checked = bad = 0
    for up in sorted(Path("outputs/_units").glob("*.json")):
        text = load_source_text(up.stem)
        if text is None:
            print(f"{up.stem} SKIP 원문 없음")
            continue
        hits = unsourced_facts(load(up), text)
        print(f"{up.stem} 위반 {len(hits)}")
        for h in hits:
            print(f"    {h.rule} {h.description} -> {h.match}")
        checked += 1
        bad += len(hits)
    print(f"CHECKED: {checked}")
    if checked < MIN_JD:
        print(f"대조한 JD 가 {MIN_JD}건 미만 — 검사 대상 0개는 합격이 아니다")
        return 1
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
