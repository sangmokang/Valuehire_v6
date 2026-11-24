"""Generate a narrative report, deck and period workbook from a private evidence ledger."""
import argparse
import csv
import json
import os
from collections import Counter, defaultdict
from datetime import date, timedelta
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.util import Inches, Pt

if __package__:
    from .narrative import write_narrative
else:
    from narrative import write_narrative

KINDS = ("week", "month", "quarter", "half", "year")
METRICS = [
    ("LI 수락률", "offer", "accepted"), ("LI 대기 비중", "offer", "awaiting"),
    ("이력서 접수율", "offer", "resume"), ("제안→추천", "offer", "referral"),
    ("접수→추천", "resume", "referral"), ("추천→서류 통과", "referral", "pass"),
    ("추천→입사 성사", "referral", "placed"), ("추천 중 AI 최초발굴", "referral", "ai_origin"),
    ("AI 발굴→추천", "ai_origin", "referral"),
]


def period(d, kind):
    if kind == "week":
        return (d - timedelta(days=d.weekday())).isoformat()
    if kind == "month":
        return d.strftime("%Y-%m")
    if kind == "quarter":
        return f"{d.year}-Q{(d.month-1)//3+1}"
    if kind == "half":
        return f"{d.year}-H{(d.month-1)//6+1}"
    return str(d.year)


def read_events(path, cutoff):
    by_id = {}
    with path.open(encoding="utf-8-sig") as handle:
        for r in csv.DictReader(handle):
            if not all(r.get(k) for k in ("date", "case", "stage", "source")):
                raise ValueError("Missing date, case, stage or source")
            r["date"] = date.fromisoformat(r["date"])
            if r["date"] > cutoff:
                continue
            key = r["stage"], r["source"], r["case"]
            if key in by_id and by_id[key] != r:
                raise ValueError("Conflicting evidence rows")
            by_id[key] = r
    return sorted(by_id.values(), key=lambda r: r["date"])


def cohort_rates(anchors, histories, coverage):
    values = []
    for label, base, result in METRICS:
        cohort = [r for r in anchors if r["stage"] == base]
        def reached(r):
            events = histories[r["case"]]
            return any(e["stage"] == result and
                       (e["date"] <= r["date"] if result == "ai_origin" else e["date"] >= r["date"])
                       for e in events)
        numerator = sum(reached(r) for r in cohort)
        denominator = len(cohort)
        complete = coverage.get("complete", {}).get(base) is True and coverage.get("complete", {}).get(result) is True and coverage.get("joins_complete") is True
        values.append([label, numerator, denominator, numerator / denominator if denominator and complete else None,
                       "검증" if complete and denominator else "분모 없음" if not denominator and complete else "관측 범위 제한"])
    return values


def report(src, dest, cutoff, focus="year"):
    coverage = json.loads((src/"coverage.json").read_text())
    events = read_events(src/"events.csv", cutoff)
    hist, first = defaultdict(list), {}
    for r in events:
        hist[r["case"]].append(r)
        first.setdefault((r["case"],r["stage"]),r)
    facts = list(first.values())
    dest.mkdir(parents=True,exist_ok=True)
    wb = Workbook()
    summary = wb.active
    summary.title = "기간별 실적"
    summary.append(["주기","기간","추천 에피소드","추천 고객사 수","LinkedIn 제안 관측","집중 고객사","집중 포지션"])
    matrix = wb.create_sheet("전환 지표")
    matrix.append(["주기","코호트 기간","지표","연결 확인 건","관측 분모","확정 비율","검증 상태"])
    clients = wb.create_sheet("고객사와 직무")
    clients.append(["주기","기간","고객사","포지션","추천 에피소드"])
    dates = [r["date"] for r in facts]
    first_day = min(dates, default=cutoff)
    groups = {}
    for kind in KINDS:
        groups[kind]=defaultdict(list)
        for delta in range((cutoff-first_day).days+1):
            groups[kind][period(first_day+timedelta(days=delta),kind)]
        for r in facts:
            groups[kind][period(r["date"],kind)].append(r)
        for k,rows in sorted(groups[kind].items()):
            rec=[r for r in rows if r["stage"]=="referral"]
            mix=Counter((r["client"],r["role"]) for r in rec)
            for (client,role),n in mix.most_common(): clients.append([kind,k,client,role,n])
            top=Counter(r["client"] for r in rec).most_common(1)
            summary.append([kind,k,len(rec),len(set(r["client"] for r in rec)),sum(r["stage"]=="offer" for r in rows),
                            top[0][0] if top else None,mix.most_common(1)[0][0][1] if mix else None])
            for row in cohort_rates(rows,hist,coverage): matrix.append([kind,k,*row])
    seat_file = src / "inmail.csv"
    if seat_file.exists():
        seats = wb.create_sheet("LinkedIn 좌석 원장")
        seats.append(["시작일 UTC", "종료일 UTC", "좌석", "발송", "회신", "수락", "미회신", "회신율", "수락률", "보고서 출처"])
        with seat_file.open(encoding="utf-8-sig") as handle:
            for item in csv.DictReader(handle):
                start, end = (date.fromisoformat(item[k]) for k in ("start", "end"))
                sent, replied, accepted = (int(item[k]) for k in ("sent", "replied", "accepted"))
                if start > end or not 0 <= accepted <= replied <= sent or not item["source"]:
                    raise ValueError("Invalid InMail report interval or counts")
                if end <= cutoff:
                    seats.append([str(start), str(end), item["seat"], sent, replied, accepted,
                                  sent - replied, replied / sent if sent else None,
                                  accepted / sent if sent else None, item["source"]])
                    for cell in seats[seats.max_row][7:9]:
                        cell.number_format = "0.0%"
    issue_rows = []
    issues_file = src / "issues.csv"
    if issues_file.exists():
        issues = wb.create_sheet("근거가 있는 주차별 현안")
        issues.append(["주 시작", "확인일", "고객사", "직무", "현안", "출처"])
        with issues_file.open(encoding="utf-8-sig") as handle:
            for item in csv.DictReader(handle):
                observed = date.fromisoformat(item["date"])
                if observed <= cutoff and item["source"]:
                    issue_rows.append(item)
                    issues.append([period(observed, "week"), observed.isoformat(), item["client"],
                                   item["role"], item["issue"], item["source"]])
    references = write_narrative(dest/"report.md", cutoff, focus, facts, hist, coverage,
                                 issue_rows, cohort_rates, src/"journal.csv")
    sources = wb.create_sheet("보고서 근거")
    sources.append(["본문 출처 키", "원문 식별자 (비공개)"])
    for ref, original in references.items():
        sources.append([ref, original])
    for cell in list(matrix.columns)[5][1:]:cell.number_format="0.0%"
    for ws in wb:
        ws.freeze_panes="C2";ws.auto_filter.ref=ws.dimensions
        for c in ws[1]: c.font=Font(color="FFFFFF",bold=True);c.fill=PatternFill("solid",fgColor="173C50")
        for col in ws.columns:
            ws.column_dimensions[col[0].column_letter].width=min(60,max(14,max(len(str(c.value or "")) for c in col)*1.55))
    for ws in wb:
        for row in ws:
            for cell in row:
                if cell.data_type == "f":
                    cell.data_type = "s"
    wb.save(dest/"periods.xlsx")
    prs=Presentation();prs.slide_width=Inches(13.33);prs.slide_height=Inches(7.5)
    def text(sl, x,y,w,h,s,size,color,bold=False):
        tf=sl.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h)).text_frame
        tf.word_wrap=True
        para=tf.paragraphs[0];para.text=s;para.font.name="Malgun Gothic";para.font.size=Pt(size);para.font.bold=bold;para.font.color.rgb=RGBColor.from_string(color)
    def slide(title, lines):
        sl=prs.slides.add_slide(prs.slide_layouts[6]);fill=sl.background.fill;fill.solid();fill.fore_color.rgb=RGBColor.from_string("F3F5F2")
        text(sl,.65,.38,12,.4,"VALUECONNECT   /   RECRUITING OPERATIONS",14,"297660",True)
        text(sl,.65,1.03,12,1.0,title,30,"123A38",True)
        ypos=2.18
        for line in lines:
            text(sl,.72,ypos,11.95,.74,line,17,"213938");ypos+=.88
        text(sl,.7,7.0,11,.3,f"{cutoff.isoformat()} 기준   ·   확인된 활동만 집계   ·   상세 기간표 periods.xlsx",11,"45645D")
    rec=[r for r in facts if r["stage"]=="referral"]
    slide("채용 운영 실적과 전환", [coverage["scope"],f"관측된 추천 에피소드 {len(rec):,}건  ·  LinkedIn 제안 {sum(r['stage']=='offer' for r in facts):,}건",
          "추천은 후보자·고객사·직무의 최초 확인 발송에 귀속합니다. 같은 후보자의 다른 포지션은 별도 에피소드로 봅니다.",
          "팀 전체 Gmail 추천과 개인 LinkedIn 제안은 범위가 다릅니다. 두 총계를 나눠 채널 전환율을 계산하지 않습니다."])
    start=date(cutoff.year,((cutoff.month-1)//3)*3+1,1)
    for mode,heading in [(0,"분기 누적 · 전년 같은 기간"),(1,"월 누적 · 전년 같은 기간")]:
        a=start if mode==0 else cutoff.replace(day=1)
        endlast=cutoff.replace(year=cutoff.year-1, day=min(cutoff.day,28) if cutoff.month==2 and cutoff.day==29 else cutoff.day)
        lines=[]
        for lo,hi in [(a.replace(year=a.year-1),endlast),(a,cutoff)]:
            sample=[r for r in rec if lo<=r["date"]<=hi];cc=Counter(r["client"] for r in sample)
            lines += [f"{lo} – {hi}     추천 {len(sample)}건  /  고객사 {len(cc)}곳", "상위 고객사   "+"   ·   ".join(f"{k} {v}건" for k,v in cc.most_common(3))]
        slide(heading,lines)
    for kind,n,title in [("week",5,"최근 주차별 추천과 고객사"),("month",5,"최근 월별 추천과 고객사"),("quarter",5,"분기별 추천 추이"),("half",4,"반기별 추천 추이"),("year",3,"연간 추천 추이")]:
        lines=[]
        for k,rows in sorted(groups[kind].items())[-n:]:
            sample=[r for r in rows if r["stage"]=="referral"];cc=Counter(r["client"] for r in sample)
            lines.append(f"{k}    추천 {len(sample)}건  /  {len(cc)}곳     "+" · ".join(f"{c} {v}" for c,v in cc.most_common(3)))
        slide(title,lines)
    for title,lines in coverage.get("slides",[]):slide(title,lines)
    prs.save(dest/"report.pptx")
    if len(Presentation(dest/"report.pptx").slides)!=len(prs.slides):raise RuntimeError("slide readback")
    print(len(prs.slides),"slides;",len(events),"evidence rows")


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source",type=Path);parser.add_argument("output",type=Path)
    parser.add_argument("--through",type=date.fromisoformat,required=True)
    parser.add_argument("--period", choices=KINDS, default="year", help="Focus of the standalone narrative")
    args=parser.parse_args();os.umask(0o077);report(args.source,args.output,args.through,args.period)
