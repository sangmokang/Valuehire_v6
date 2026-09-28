"""Compose the search-result mail in the house listing format.

사장님 규칙 — **표 금지, 리스팅 형태.** 적합근거가 길어서 표 칸에 밀어 넣으면 레이아웃이 깨진다.
기준 메일: ``[ChatGPT-AISearch] Infludeo – 포카스팟 오프라인 리테일 리더 – 10 candidates``
(Summary → 회사/조직 맥락 → Top candidates → 후보별 블록 → Candidate Pool / Hiring Insight).

이 모듈은 **본문만 만든다.** 발송은 에이전트가 Gmail MCP 로 한다 — 이 저장소에 Gmail 자격증명을
두지 않기 위해서다.

    python tools/codeitsearch/compose_mail.py --results results.json --out mail.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

SUBJECT_PREFIX = "[aisearch]Claude-win"
RECIPIENTS = (
    "sangmokang@valueconnect.kr",
    "kcs@valueconnect.kr",
    "rogan@valueconnect.kr",
    "julian@valueconnect.kr",
)
LABEL = "aisearch"
SEPARATOR = "\n---\n"


def subject_for(company: str, position: str, count: int) -> str:
    return f"{SUBJECT_PREFIX} {company} – {position} – {count} candidates"


def _bullets(lines: list[str] | None, dash: str = "- ") -> str:
    return "\n".join(f"{dash}{line}" for line in (lines or []))


def _candidate_block(index: int, candidate: dict[str, Any]) -> str:
    """One candidate as a listing block — never a table row."""
    head = [f"## {index}. {candidate['name']} — {candidate['match']}% Match"]
    for label, key in (
        ("Current", "current"),
        ("Previous", "previous"),
        ("Location", "location"),
        ("Education", "education"),
        ("Languages", "languages"),
        ("Contact", "contact"),
    ):
        value = candidate.get(key)
        if value:
            head.append(f"{label}: {value}")

    sections = ["\n".join(head)]
    if candidate.get("sources"):
        sections.append("Sources:\n" + _bullets(candidate["sources"]))
    for title, key in (
        ("Career Summary", "career_summary"),
        ("Why Match", "why_match"),
        ("Risks / Gaps", "risks"),
    ):
        if candidate.get(key):
            sections.append(f"{title}:\n" + _bullets(candidate[key]))

    score = candidate.get("score_breakdown")
    if score:
        detail = " · ".join(f"{k} {v}" for k, v in score.items())
        sections.append(f"Score: {detail} (코드 계산, 총점 {candidate['match']})")
    sections.append(f"Previous Search: {candidate.get('previous_search', '신규 후보')}")
    return "\n\n".join(sections)


def compose(results: dict[str, Any]) -> dict[str, Any]:
    company = results["company"]
    position = results["position"]
    candidates = results.get("candidates", [])

    summary = [
        f"Company / Position: {company} / {position}",
        f"Shortlist: {len(candidates)}명",
        f"주요 탐색 축: {results.get('search_axes', '')}",
        f"주요 검색 채널: {results.get('channels', '')}",
        f"키워드(국문/영문): {results.get('keyword_note', '')}",
        f"제외 규칙: {results.get('exclusion_note', '프리랜서 제외 · 12개월 미만 단기이직 2회+ 하드제외')}",
        f"Previous Search: {results.get('previous_search', '해당 포지션 기존 AI Search 발송 이력 없음 → 전원 신규 후보')}",
    ]

    parts = [
        f"안녕하세요,\n\n{company} {position} 포지션 후보 서치 결과 공유드립니다.",
        "## Summary\n" + _bullets(summary),
    ]

    if results.get("context"):
        parts.append("### 회사/조직 맥락\n" + _bullets(results["context"]))

    if candidates:
        top = [
            f"{i}. {c['name']} — {c['match']}%"
            for i, c in enumerate(candidates[: results.get("top_n", 5)], start=1)
        ]
        parts.append("### Top candidates\n" + "\n".join(top))
        body = SEPARATOR.join(
            _candidate_block(i, c) for i, c in enumerate(candidates, start=1)
        )
        parts.append(body)
    else:
        # 후보가 없으면 없다고 쓴다. 빈 리스트를 성과처럼 포장하지 않는다.
        parts.append(
            "## 후보\n- 이번 실행에서 등록 문턱(60점)을 넘은 후보 없음.\n"
            f"- 사유: {results.get('no_candidate_reason', '사유 미기재')}"
        )

    if results.get("insight"):
        parts.append("## Candidate Pool / Hiring Insight\n" + _bullets(results["insight"]))
    if results.get("evidence"):
        parts.append("## 증거 / 재현\n" + _bullets(results["evidence"]))

    parts.append("감사합니다.")

    return {
        "subject": subject_for(company, position, len(candidates)),
        "to": list(RECIPIENTS),
        "label": LABEL,
        "body": "\n\n".join(parts),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)

    mail = compose(json.loads(args.results.read_text(encoding="utf-8")))
    if args.out:
        args.out.write_text(json.dumps(mail, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"wrote {args.out}")
    else:
        print(mail["subject"])
        print()
        print(mail["body"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
