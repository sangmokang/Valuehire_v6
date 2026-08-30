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
        "notion_read:NOT_RUN": (
            "Notion page ID는 DB mirror에서 찾았지만 current parent/schema readback이 없어 "
            "쓰기를 중단했다."
        ),
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


def render_operating_snapshot(snapshot: dict[str, Any]) -> list[str]:
    closed = snapshot["closed_week"]
    current = snapshot["current"]
    funnel = current["funnel"]
    targets = snapshot["targets"]
    return [
        f"- {closed['week_label']} 신규 포지션 {closed['new_positions']}개 / "
        f"신규 고객사 {closed['new_position_companies']}개",
        f"- 주간 실행: AI 검색 {closed['ai_search_runs']}회, 포지션 커버리지 "
        f"{closed['position_coverage']}개, 추천 인원 {closed['recommended_people']}명, "
        f"추천 이벤트 {closed['recommendation_events']}건",
        f"- 현재 snapshot: 오픈 포지션 {current['open_positions']}개, "
        f"AI 소싱 {funnel['ai_sourcing']}명, 제안 {funnel['proposal']}건, "
        f"추천 {funnel['recommended']}명, 인터뷰 {funnel['interviewing']}명, "
        f"최종합격 {funnel['final_pass']}명, 입사 {funnel['joined']}명",
        f"- 기준 목표: 주간 제안 {targets['weekly_proposals']}건, "
        f"주간 추천 {targets['weekly_recommendations']}명, "
        f"주간 매출 ₩{targets['weekly_revenue']:,}",
        f"- 데이터 기준: SQL 주간 집계 [{closed['week_start']}, {closed['week_end']}), "
        "현재 funnel은 별도 시점 snapshot으로 비교 산정하지 않음",
    ]


def render_brief(
    bundle: dict[str, Any],
    positions: list[dict[str, Any]],
    career_summaries: list[dict[str, Any]],
    consultant_focus: list[dict[str, Any]],
    operating_snapshot: dict[str, Any],
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
        "데이터 판정은 발행 완료 판정이 아니다. 동일 snapshot과 content hash에 연결된 "
        "DB·ClickUp·Notion·admin web·email readback 영수증을 모두 확인해야 발행 완료다.",
    ]
    if operating_snapshot:
        lines.extend(["", "## 핵심 운영지표", ""])
        lines.extend(render_operating_snapshot(operating_snapshot))
    lines.extend(["", "## 이번 주 고객 액션", ""])
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


def render_publication_report(
    verdict: str,
    blockers: list[str],
    errors: list[str],
    snapshot_id: str,
    content_hash: str,
) -> str:
    lines = [
        "## 발행 확인",
        "",
        f"- 발행 번들 판정: {verdict}",
    ]
    if blockers:
        lines.append("- 미확인 또는 실패 대상:")
        lines.extend(f"  - {blocker}" for blocker in blockers)
    else:
        lines.append("- 필수 대상 5개의 동일 snapshot readback을 확인했다.")
    if errors:
        lines.append("- 발행 계약 오류:")
        lines.extend(f"  - {error}" for error in errors)
    lines.extend([
        f"- report_snapshot_id: {snapshot_id}",
        f"- content_hash: {content_hash}",
        "- 이 상태 블록은 content hash 외부의 전달 통제 메타데이터다. "
        "정본 브리핑의 해시를 바꾸지 않는다.",
    ])
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


def render_html(
    markdown: str,
    snapshot_id: str,
    content_hash: str,
    publication_report: str = "",
) -> str:
    canonical = escape(markdown)
    visible = _visible_html(markdown)
    publication_visible = _visible_html(publication_report) if publication_report else ""
    publication_canonical = escape(publication_report)
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
    .publication{{margin-top:42px;padding:18px 22px;border:1px solid #d6a84b;background:#fff9eb}}
    @media(max-width:720px){{main{{margin:0;padding:32px 22px;border:0}}h1{{font-size:28px}}}}
  </style>
</head>
<body><main>{visible}<aside class="publication">{publication_visible}</aside></main>
<pre id="canonical-brief" hidden>{canonical}</pre>
<pre id="publication-status" hidden>{publication_canonical}</pre></body>
</html>
"""
