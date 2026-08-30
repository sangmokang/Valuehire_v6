"""Deterministic Markdown and HTML renderers for the Weekly CEO brief."""

from __future__ import annotations

from html import escape
from typing import Any

from activity_gate import render_career_summaries, render_consultant_focus


def render_position(position: dict[str, Any]) -> str:
    score = position["score"]
    return (
        f"- {position['company']} — {position['title']}: {position['action']} "
        f"(우선순위 {score['priority']}, 시급성 {score['urgency']}, 난이도 {score['difficulty']})"
    )


def render_blocker(blocker: str) -> str:
    labels = {
        "clickup_read:STALE": "ClickUp 스키마는 과거 판독값만 있어 쓰기를 중단했다.",
        "notion_read:NOT_RUN": "Notion 대상 DB와 parent를 확인하지 못해 쓰기를 중단했다.",
        "jobkorea_outreach_read:NOT_RUN": "잡코리아 발송함을 재조회하지 못했다.",
        "saramin_outreach_read:NOT_RUN": "사람인 발송함을 재조회하지 못했다.",
        "linkedin_outreach_read:NOT_RUN": "LinkedIn Recruiter 발송함을 재조회하지 못했다.",
    }
    if blocker.startswith("source:"):
        return "일부 원천 스냅샷이 완전 검증 상태가 아니다."
    if blocker.startswith("career:"):
        _, company, status = blocker.split(":", 2)
        return f"{company} 채용 페이지는 {status} 상태라 직무명 대조가 필요하다."
    return labels.get(blocker, blocker)


def render_brief(
    bundle: dict[str, Any],
    positions: list[dict[str, Any]],
    career_summaries: list[dict[str, Any]],
    consultant_focus: list[dict[str, Any]],
    snapshot_id: str,
    data_status: str,
    source_blockers: list[str],
) -> str:
    meeting_date = bundle["run"]["meeting_at"][:10]
    status_label = {
        "PASS": "검증 완료(PASS)",
        "PARTIAL": "부분 검증(PARTIAL)",
        "BLOCKED": "차단(BLOCKED)",
    }.get(data_status, data_status)
    customer = [
        item for item in positions
        if item["origin"] in {"CLIENT_REQUESTED", "CLIENT_SHARED"}
        and item["lifecycle"] != "CLOSED"
    ]
    operations = sorted(
        (item for item in positions if item["lifecycle"] == "CLOSED"),
        key=lambda item: (item["company"], item["title"]),
    )
    weekly = sorted(
        (item for item in customer if item["period"] == "WEEKLY"),
        key=lambda item: (-item["score"]["priority"], item["company"], item["title"]),
    )
    late = sorted(
        (item for item in customer if item["period"] == "LATE_ALERT"),
        key=lambda item: (-item["score"]["priority"], item["company"], item["title"]),
    )
    scraped = sorted(
        (item for item in positions if item["origin"] == "SCRAPED_STAGING"),
        key=lambda item: (item["company"], item["title"]),
    )
    lines = [
        f"# Weekly CEO Brief | {meeting_date}", "", "## 결론", "",
        f"데이터 판정은 {status_label}이다. 고객 요청과 단순 채용 공고를 분리했으며, "
        "우선순위는 증거 라벨을 버전 고정 수식으로 계산했다.",
        "", "## 이번 주 고객 액션", "",
    ]
    lines.extend(render_position(item) for item in weekly)
    if not weekly:
        lines.append("- 검증된 고객 액션 없음.")
    if late:
        lines.extend(["", "## 마감 후 경보", ""])
        lines.extend(render_position(item) for item in late)
    if operations:
        lines.extend(["", "## 운영 변경", ""])
        lines.extend(f"- {item['company']} — {item['title']}: {item['action']}" for item in operations)
    if consultant_focus:
        lines.extend(["", "## 컨설턴트별 몰입 — 검증된 발송", ""])
        lines.extend(render_consultant_focus(consultant_focus))
        lines.append("- 위 발송은 잔디밭 YELLOW 근거가 될 수 있으나 상위 색 판정은 별도다.")
    elif any("_outreach_read:" in blocker for blocker in source_blockers):
        lines.extend(["", "## 컨설턴트별 몰입 — 산출 보류", ""])
        lines.append(
            "- 세 채널 발송함의 provider readback이 없어 집중도를 산출하지 않았다. "
            "활동 0건으로 해석하지 않는다."
        )
    if career_summaries:
        lines.extend(["", "## 채용 페이지 관측 — 고객 의뢰 아님", ""])
        lines.extend(render_career_summaries(career_summaries))
    if scraped:
        if not career_summaries:
            lines.extend(["", "## 채용 페이지 관측 — 고객 의뢰 아님", ""])
        lines.extend(f"- {item['company']} — {item['title']}" for item in scraped)
    if source_blockers:
        lines.extend(["", "## 운영 위험", ""])
        lines.extend(f"- {render_blocker(blocker)}" for blocker in source_blockers)
    lines.extend(["", f"`report_snapshot_id: {snapshot_id}`", ""])
    return "\n".join(lines)


def _visible_html(markdown: str) -> str:
    rows: list[str] = []
    in_list = False
    for line in markdown.splitlines():
        if line.startswith("- "):
            if not in_list:
                rows.append("<ul>")
                in_list = True
            rows.append(f"<li>{escape(line[2:])}</li>")
            continue
        if in_list:
            rows.append("</ul>")
            in_list = False
        if line.startswith("## "):
            rows.append(f"<h2>{escape(line[3:])}</h2>")
        elif line.startswith("# "):
            rows.append(f"<h1>{escape(line[2:])}</h1>")
        elif line.startswith("`") and line.endswith("`"):
            rows.append(f"<div class=\"meta\">{escape(line[1:-1])}</div>")
        elif line:
            rows.append(f"<p>{escape(line)}</p>")
    if in_list:
        rows.append("</ul>")
    return "\n".join(rows)


def render_html(markdown: str, snapshot_id: str, content_hash: str) -> str:
    canonical = escape(markdown)
    visible = _visible_html(markdown)
    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <meta name="report-snapshot-id" content="{escape(snapshot_id)}">
  <meta name="content-hash" content="{escape(content_hash)}">
  <title>Weekly CEO Brief</title>
  <style>
    :root{{--ink:#17211b;--muted:#667069;--line:#dde3df;--paper:#f5f7f5;--accent:#174c34}}
    *{{box-sizing:border-box}}body{{margin:0;background:var(--paper);color:var(--ink);font:15px/1.65 -apple-system,BlinkMacSystemFont,"Pretendard","Noto Sans KR",sans-serif}}
    main{{max-width:980px;margin:56px auto;padding:52px 64px;background:#fff;border:1px solid var(--line);box-shadow:0 18px 45px #18322212}}
    h1{{font:700 34px/1.2 Georgia,"Noto Serif KR",serif;margin:0 0 22px}}h2{{font-size:17px;margin:38px 0 12px;padding-top:18px;border-top:1px solid var(--line)}}
    ul{{padding-left:22px}}li{{padding:5px 0}}.meta{{margin-top:42px;color:var(--muted);font:12px/1.5 ui-monospace,SFMono-Regular,Menlo,monospace;word-break:break-all}}
    @media(max-width:720px){{main{{margin:0;padding:32px 22px;border:0}}h1{{font-size:28px}}}}
  </style>
</head>
<body><main>{visible}</main><pre id="canonical-brief" hidden>{canonical}</pre></body>
</html>
"""
