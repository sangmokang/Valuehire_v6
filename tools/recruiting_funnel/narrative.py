"""Write the standalone Korean management report from reconciled private events."""
import csv
import hashlib
import re
from collections import Counter
from datetime import date, timedelta
from html import escape

PERIOD_NAMES = {"week": "주간", "month": "월간", "quarter": "분기", "half": "반기", "year": "연간"}


def period_start(day, kind):
    if kind == "week":
        return day - timedelta(days=day.weekday())
    months = {"month": 1, "quarter": 3, "half": 6, "year": 12}[kind]
    return date(day.year, (day.month - 1) // months * months + 1, 1)


def prior_year(day):
    if day.month == 2 and day.day == 29:
        return date(day.year - 1, 2, 28)
    return day.replace(year=day.year - 1)


def prior_window(start, end, kind):
    if kind != "week":
        return prior_year(start), prior_year(end)
    year, week, _ = start.isocalendar()
    # December 28 always belongs to the last ISO week.
    week = min(week, date(year - 1, 12, 28).isocalendar().week)
    monday = date.fromisocalendar(year - 1, week, 1)
    return monday, monday + (end - start)


def source_reference(value):
    return "E-" + hashlib.sha256(value.encode("utf-8")).hexdigest()[:20]


def plain(value):
    value = " ".join(str(value or "").split())
    value = re.sub(r"[\w.+-]+@[\w.-]+\.[\w-]+", "[이메일 생략]", value)
    value = re.sub(r"(?<!\d)(?:\+82[- ]?|0)1[016789][- ]?\d{3,4}[- ]?\d{4}(?!\d)", "[연락처 생략]", value)
    value = escape(value, quote=False)
    for char in ("\\", "|", "*", "_", "[", "]", "`"):
        value = value.replace(char, "\\" + char)
    return value


def stage_mix(rows, stage):
    return Counter((r["client"], r["role"]) for r in rows if r["stage"] == stage)


def top_positions(mix):
    return ", ".join(f"{plain(c) or '고객사 미확인'} / {plain(r) or '직무 미확인'} {n:,}건"
                     for (c, r), n in mix.most_common(3)) or "해당 원장 행 없음"


def write_narrative(path, cutoff, kind, facts, histories, coverage, issue_rows, cohort_rates, journal):
    start = period_start(cutoff, kind)
    prior_start, prior_end = prior_window(start, cutoff, kind)
    references = {}

    def cite(value):
        ref = source_reference(value)
        if references.setdefault(ref, value) != value:
            raise ValueError("Conflicting evidence references")
        return ref
    rows = [r for r in facts if start <= r["date"] <= cutoff]
    previous = [r for r in facts if prior_start <= r["date"] <= prior_end]
    lines = [
        f"# {PERIOD_NAMES[kind]} 채용 운영 보고서", "",
        f"이번 기간은 {start}~{cutoff}, 전년 비교 기간은 {prior_start}~{prior_end}이다. "
        f"서울 날짜로 최초 확인한 후보·고객사·직무 에피소드를 세었다. 조사 범위는 {plain(coverage['scope'])}이다.", "",
        "## 전년 동기와 이번 기간의 활동", "",
    ]
    if kind == "week":
        lines.extend(["주간 비교는 전년 ISO 주차의 같은 요일까지 맞췄다. 전년에 53주차가 없으면 마지막 주차를 쓴다.", ""])
    for label, stage in (("LinkedIn 제안", "offer"), ("고객사 추천", "referral")):
        current_mix, past_mix = stage_mix(rows, stage), stage_mix(previous, stage)
        current_n, past_n = current_mix.total(), past_mix.total()
        lines.extend([f"{label} 원장에서는 이번 기간 {current_n:,}건, 전년 동기 {past_n:,}건이 관측됐다. "
                      f"확인된 행의 차이는 {current_n-past_n:+,}건이다. "
                      f"이번 기간 상위 고객사·직무는 {top_positions(current_mix)}이다.", ""])
    lines.extend([
        "원장 행이 없는 날에는 자료 미수집과 실제 무활동을 구별할 수 없다. "
        "단계별 수집 완결 여부와 후보–직무 연결 상태는 아래 전환표에 반영했다.", "",
        "## 같은 후보·직무에서 확인한 전환", "",
        "| 지표 | 연결 확인 / 관측 분모 | 확정률 | 근거 상태 |",
        "| --- | ---: | ---: | --- |",
    ])
    for label, n, d, rate, status in cohort_rates(rows, histories, coverage):
        percent = "미산정" if rate is None else f"{rate:.1%}"
        lines.append(f"| {label} | {n:,} / {d:,} | {percent} | {status} |")
    offers = [r for r in rows if r["stage"] == "offer"]
    examples = {}
    for offer in offers:
        linked = next((r for r in histories[offer["case"]]
                       if r["stage"] == "referral" and r["date"] >= offer["date"]), None)
        examples.setdefault(bool(linked), (offer, linked))
        if len(examples) == 2:
            break
    lines.append("")
    for offer, linked in examples.values():
        evidence = f"{offer['date']} {plain(offer['client'])} / {plain(offer['role'])} 제안(근거 {cite(offer['source'])})"
        if linked:
            lines.append(f"- {evidence}은 {linked['date']} 고객사 추천 원장과 연결됐다(근거 {cite(linked['source'])}).")
        else:
            lines.append(f"- {evidence}은 기준일까지 같은 건의 후속 추천 근거를 찾지 못했다. 이 기록만으로 거절을 판정할 수 없다.")
    lines.extend(["", "각 행의 분모는 해당 기간에 처음 관측된 선행 단계다. "
                  "그 에피소드가 기준일까지 후속 단계에 도달해야 분자에 포함된다. "
                  "AI 최초발굴은 추천일 이전 또는 당일에 연결된 발굴 근거를 요구한다. "
                  "새 코호트는 후속 결과를 관찰할 시간이 짧다.", "",
                  "## 월별·주차별 고객사와 직무", ""])
    for interval in ("month", "week"):
        lines.extend([f"### {PERIOD_NAMES[interval]} 활동", "",
                      "| 집계일 | 제안과 상위 직무 | 추천과 상위 직무 | 대조 원문 예시 |",
                      "| --- | --- | --- | --- |"])
        groups = {}
        for offset in range((cutoff - start).days + 1):
            day = start + timedelta(days=offset)
            groups.setdefault(period_start(day, interval), [])
        for r in rows:
            groups[period_start(r["date"], interval)].append(r)
        for key, group in groups.items():
            offers, refs = stage_mix(group, "offer"), stage_mix(group, "referral")
            identifiers = []
            for stage in ("offer", "referral"):
                example = next((r for r in group if r["stage"] == stage), None)
                if example:
                    identifiers.append(f"{example['date']} {cite(example['source'])}")
            lines.append(f"| {key} | {offers.total():,}건 · {top_positions(offers)} | "
                         f"{refs.total():,}건 · {top_positions(refs)} | {', '.join(identifiers) or '—'} |")
        lines.append("")
    lines.extend(["집계일은 달 또는 주의 첫날이다. 표의 건수는 보고 기간에 포함되는 날짜만 센다. "
                  "전체 직무 분포와 원장 기반 전환율은 같은 폴더의 periods.xlsx에서 확인할 수 있다.", "",
                  "## 원문에서 확인한 현안과 판단의 한계", ""])
    observed_issues = [r for r in issue_rows if start <= date.fromisoformat(r["date"]) <= cutoff]
    if observed_issues:
        for r in observed_issues:
            lines.append(f"- {r['date']} · {plain(r['client'])} / {plain(r['role'])} — "
                         f"{plain(r['issue'])} (근거 {cite(r['source'])})")
    else:
        lines.append("이 기간에 날짜와 원문 출처를 갖춘 현안이 수록되지 않아 병목 원인을 특정하지 않았다.")
    lines.extend(["", "팀 전체의 고객사 추천과 개인 LinkedIn의 후보 제안은 범위가 달라 두 총계의 단순 비율로 "
                  "채널 성과를 판단할 수 없다. 검색·초안·내부 공유는 발송이나 고객사 추천의 증거가 되지 않는다. "
                  "본문의 확정률은 두 단계와 일대일 연결이 모두 검증된 지표에만 표시했다."])
    if journal.is_file():
        with journal.open(encoding="utf-8-sig", newline="") as handle:
            notes = csv.DictReader(handle)
            fields = {"date", "topic", "finding", "limit", "source"}
            if not fields.issubset(notes.fieldnames or []):
                raise ValueError("Missing evidence journal columns")
            selected = []
            for entry in notes:
                if not all((entry.get(f) or "").strip() for f in fields):
                    raise ValueError("Incomplete evidence journal entry")
                if start <= date.fromisoformat(entry["date"]) <= cutoff:
                    selected.append(entry)
        if selected:
            lines.extend(["", "## 근거를 검토한 운영 기록", ""])
            for e in sorted(selected, key=lambda item: item["date"]):
                lines.extend([f"### {e['date']} · {plain(e['topic'])}", "",
                              plain(e["finding"]), "",
                              f"반례·측정 한계: {plain(e['limit'])}. 근거: {cite(e['source'])}", ""])
    lines.extend(["", "본문의 E- 출처 키는 비공개 periods.xlsx의 ‘보고서 근거’ 시트에서 원문과 대조할 수 있다."])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return references
