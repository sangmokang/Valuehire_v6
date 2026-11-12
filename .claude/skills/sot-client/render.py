"""회사소개 브리프 렌더러: company JSON -> 서식 .docx (Google Docs 변환용).
usage: python render.py data/<slug>.json out/<file>.docx
"""
import json, sys, os, io
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from docx import Document
from docx.shared import Pt, RGBColor, Cm, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import docx.opc.constants

NAVY, TEAL, SAND, GRAY, LIGHT = "1F3A5F", "2A9D8F", "E9C46A", "6B7280", "F3F5F8"
RED = "C8553D"
FONT = "Noto Sans KR"

for f in ["/System/Library/Fonts/AppleSDGothicNeo.ttc"]:
    if os.path.exists(f):
        font_manager.fontManager.addfont(f)
plt.rcParams["font.family"] = "Apple SD Gothic Neo"
plt.rcParams["axes.unicode_minus"] = False


def rgb(h):
    return RGBColor.from_string(h)


def shade(cell, hexcolor):
    tcPr = cell._tc.get_or_add_tcPr()
    sh = OxmlElement("w:shd")
    sh.set(qn("w:val"), "clear"); sh.set(qn("w:color"), "auto"); sh.set(qn("w:fill"), hexcolor)
    tcPr.append(sh)


def borders(table, color="D9DEE5"):
    tbl = table._tbl
    tblPr = tbl.tblPr
    b = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        e = OxmlElement(f"w:{edge}")
        e.set(qn("w:val"), "single"); e.set(qn("w:sz"), "4"); e.set(qn("w:color"), color)
        b.append(e)
    tblPr.append(b)


def run(p, text, size=10.5, bold=False, color=None, italic=False):
    r = p.add_run(text)
    r.font.name = FONT
    r._element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
    r.font.size = Pt(size); r.bold = bold; r.italic = italic
    if color:
        r.font.color.rgb = rgb(color)
    return r


def link(p, text, url, size=10.5, color=TEAL):
    part = p.part
    rid = part.relate_to(url, docx.opc.constants.RELATIONSHIP_TYPE.HYPERLINK, is_external=True)
    h = OxmlElement("w:hyperlink"); h.set(qn("r:id"), rid)
    r = OxmlElement("w:r"); rPr = OxmlElement("w:rPr")
    fonts = OxmlElement("w:rFonts"); fonts.set(qn("w:ascii"), FONT); fonts.set(qn("w:eastAsia"), FONT); fonts.set(qn("w:hAnsi"), FONT)
    c = OxmlElement("w:color"); c.set(qn("w:val"), color)
    u = OxmlElement("w:u"); u.set(qn("w:val"), "single")
    sz = OxmlElement("w:sz"); sz.set(qn("w:val"), str(int(size * 2)))
    for x in (fonts, c, u, sz):
        rPr.append(x)
    r.append(rPr)
    t = OxmlElement("w:t"); t.text = text; t.set(qn("xml:space"), "preserve"); r.append(t)
    h.append(r); p._p.append(h)


def para(doc, space_after=6):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = 1.35
    return p


def heading(doc, num, text):
    p = para(doc, 4)
    p.paragraph_format.space_before = Pt(16)
    run(p, f"{num:02d}  ", 13, True, TEAL)
    run(p, text, 15, True, NAVY)
    # 밑줄 바
    pPr = p._p.get_or_add_pPr()
    bdr = OxmlElement("w:pBdr"); bt = OxmlElement("w:bottom")
    bt.set(qn("w:val"), "single"); bt.set(qn("w:sz"), "8"); bt.set(qn("w:color"), NAVY); bt.set(qn("w:space"), "4")
    bdr.append(bt); pPr.append(bdr)


def bullets(doc, items):
    for it in items:
        p = para(doc, 3)
        p.paragraph_format.left_indent = Cm(0.5)
        p.paragraph_format.first_line_indent = Cm(-0.4)
        run(p, "▪ ", 10, True, TEAL)
        if isinstance(it, dict):
            run(p, it["head"] + "  ", 10.5, True, NAVY)
            run(p, it.get("body", ""), 10.5)
        else:
            run(p, it, 10.5)


def set_widths(t, widths):
    # Google Docs 는 tblGrid/gridCol 과 고정 레이아웃을 읽는다
    t.autofit = False
    tblPr = t._tbl.tblPr
    lay = OxmlElement("w:tblLayout"); lay.set(qn("w:type"), "fixed"); tblPr.append(lay)
    grid = t._tbl.tblGrid
    for i, gc in enumerate(grid.findall(qn("w:gridCol"))):
        gc.set(qn("w:w"), str(int(widths[i] * 567)))
    for row in t.rows:
        for i, w in enumerate(widths):
            row.cells[i].width = Cm(w)


def table(doc, header, rows, widths=None, links=None):
    t = doc.add_table(rows=1, cols=len(header))
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    borders(t)
    for i, h in enumerate(header):
        c = t.rows[0].cells[i]; shade(c, NAVY)
        c.paragraphs[0].text = ""
        run(c.paragraphs[0], h, 9.5, True, "FFFFFF")
    for ri, row in enumerate(rows):
        cells = t.add_row().cells
        for i, v in enumerate(row):
            p = cells[i].paragraphs[0]
            if ri % 2 == 1:
                shade(cells[i], LIGHT)
            if isinstance(v, dict) and v.get("url"):
                link(p, v["text"], v["url"], 9.5)
            else:
                run(p, str(v), 9.5)
    if widths:
        set_widths(t, widths)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return t


def fig_to_doc(doc, fig, width_cm=16):
    buf = io.BytesIO(); fig.savefig(buf, format="png", dpi=200, bbox_inches="tight"); plt.close(fig)
    buf.seek(0)
    doc.add_picture(buf, width=Cm(width_cm))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER


def style_ax(ax):
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color("#C9CED6")
    ax.tick_params(colors="#4B5563", labelsize=9, length=0)
    ax.yaxis.grid(True, color="#E5E7EB", linewidth=0.8); ax.set_axisbelow(True)


def chart_financials(doc, fin):
    years = [str(r["year"]) for r in fin]
    rev = [r.get("revenue") for r in fin]
    op = [r.get("op_income") for r in fin]
    fig, ax = plt.subplots(figsize=(7.2, 3.2))
    x = range(len(years)); w = 0.36
    b1 = ax.bar([i - w / 2 for i in x], [v or 0 for v in rev], w, color="#" + NAVY, label="매출")
    b2 = ax.bar([i + w / 2 for i in x], [v or 0 for v in op], w, color=["#" + (TEAL if (v or 0) >= 0 else RED) for v in op], label="영업이익(손실)")
    for bars, vals in ((b1, rev), (b2, op)):
        for b, v in zip(bars, vals):
            if v is None:
                continue
            ax.annotate(f"{v:,.0f}", (b.get_x() + b.get_width() / 2, v), ha="center", va="bottom" if v >= 0 else "top",
                        fontsize=8.5, color="#111827", xytext=(0, 3 if v >= 0 else -3), textcoords="offset points")
    ax.axhline(0, color="#9CA3AF", linewidth=0.8)
    ax.set_xticks(list(x)); ax.set_xticklabels(years)
    ax.set_title("단위: 억원", fontsize=8.5, color="#6B7280", loc="right")
    style_ax(ax)
    from matplotlib.patches import Patch
    handles = [Patch(color="#" + NAVY, label="매출"), Patch(color="#" + TEAL, label="영업이익"), Patch(color="#" + RED, label="영업손실")]
    ax.legend(handles=handles, frameon=False, fontsize=9, loc="upper left")
    ax.set_ylabel("")
    ax.set_title("단위: 억원", fontsize=8.5, color="#6B7280", loc="right")
    fig_to_doc(doc, fig)


def chart_funding(doc, rounds):
    rs = [r for r in rounds if r.get("amount")]
    if not rs:  # 금액이 모두 비공개면 그래프 없이 표만
        return
    labels = [f'{r["round"]}\n{r["date"]}' for r in rs]
    amts = [r["amount"] for r in rs]
    cum, s = [], 0
    for a in amts:
        s += a; cum.append(s)
    fig, ax = plt.subplots(figsize=(7.2, 3.2))
    bars = ax.bar(labels, amts, color="#" + TEAL, width=0.55, label="라운드 금액")
    ax2 = ax.twinx()
    ax2.plot(labels, cum, color="#" + NAVY, marker="o", linewidth=2, label="누적")
    for b, v in zip(bars, amts):
        ax.annotate(f"{v:,.0f}", (b.get_x() + b.get_width() / 2, v), ha="center", va="bottom", fontsize=8.5, xytext=(0, 3), textcoords="offset points")
    ax2.annotate(f"누적 {cum[-1]:,.0f}억", (len(cum) - 1, cum[-1]), fontsize=9, color="#" + NAVY, xytext=(-60, 8), textcoords="offset points", fontweight="bold")
    style_ax(ax); ax2.set_ylim(0, max(cum) * 1.2); ax.set_ylim(0, max(cum) * 1.2)
    for s_ in ("top", "right", "left"):
        ax2.spines[s_].set_visible(False)
    ax2.set_yticks([]); ax.set_title("단위: 억원", fontsize=8.5, color="#6B7280", loc="right")
    ax.tick_params(axis="x", labelsize=8.5)
    fig_to_doc(doc, fig)


def chart_org(doc, org):
    units = org["units"]
    fig, ax = plt.subplots(figsize=(7.2, 2.6)); ax.axis("off")
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)

    def box(xc, yc, w, h, title, sub, fc, tc="white"):
        ax.add_patch(matplotlib.patches.FancyBboxPatch((xc - w / 2, yc - h / 2), w, h, boxstyle="round,pad=0.01,rounding_size=0.02", fc=fc, ec="none"))
        ax.text(xc, yc + (0.04 if sub else 0), title, ha="center", va="center", fontsize=9.5, color=tc, fontweight="bold")
        if sub:
            ax.text(xc, yc - 0.07, sub, ha="center", va="center", fontsize=8, color=tc)
    box(0.5, 0.82, 0.3, 0.22, org["top"]["title"], org["top"].get("name", ""), "#" + NAVY)
    n = len(units); w = min(0.2, 0.9 / n)
    xs = [0.05 + w / 2 + i * ((0.9 - w) / max(n - 1, 1)) for i in range(n)] if n > 1 else [0.5]
    ax.plot([0.5, 0.5], [0.71, 0.55], color="#9CA3AF", lw=1)
    ax.plot([xs[0], xs[-1]], [0.55, 0.55], color="#9CA3AF", lw=1)
    for xc, u in zip(xs, units):
        ax.plot([xc, xc], [0.55, 0.42], color="#9CA3AF", lw=1)
        box(xc, 0.28, w * 0.95, 0.26, u["title"], u.get("name", ""), "#E8F4F2", "#" + NAVY)
    fig_to_doc(doc, fig)


def chart_headcount(doc, hc):
    months = [s["month"] for s in hc["series"]]
    vals = [s["count"] for s in hc["series"]]
    fig, ax = plt.subplots(figsize=(7.2, 2.6))
    ax.fill_between(range(len(vals)), vals, min(vals) * 0.9, color="#" + TEAL, alpha=0.15)
    ax.plot(range(len(vals)), vals, color="#" + TEAL, marker="o", linewidth=2)
    for i in (0, len(vals) - 1):
        ax.annotate(f"{vals[i]}명", (i, vals[i]), ha="center", fontsize=9, fontweight="bold", color="#" + NAVY, xytext=(0, 7), textcoords="offset points")
    ax.set_xticks(range(len(months))); ax.set_xticklabels([m[2:] for m in months], fontsize=8)
    ax.set_ylim(min(vals) * 0.9, max(vals) * 1.12)
    style_ax(ax); ax.set_title(f'{hc["basis"]} 추이 (명)', fontsize=8.5, color="#6B7280", loc="right")
    fig_to_doc(doc, fig)


def li_cell(p):
    return {"text": p.get("li_label", "프로필"), "url": p["linkedin"]} if p.get("linkedin") else "확인 불가"


def kpi_row(doc, kpis):
    t = doc.add_table(rows=2, cols=len(kpis)); t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, k in enumerate(kpis):
        c0, c1 = t.rows[0].cells[i], t.rows[1].cells[i]
        shade(c0, LIGHT); shade(c1, LIGHT)
        p = c0.paragraphs[0]; p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run(p, k["value"], 17, True, NAVY)
        p = c1.paragraphs[0]; p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run(p, k["label"], 8.5, False, GRAY)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


def source_note(doc, text):
    p = para(doc, 8); run(p, text, 8, False, GRAY, italic=True)


def build(d, out):
    doc = Document()
    sec = doc.sections[0]
    sec.top_margin = sec.bottom_margin = Cm(2.0); sec.left_margin = sec.right_margin = Cm(2.2)
    st = doc.styles["Normal"]; st.font.name = FONT; st.element.rPr.rFonts.set(qn("w:eastAsia"), FONT); st.font.size = Pt(10.5)

    # 표지 띠
    band = doc.add_table(rows=1, cols=1); c = band.rows[0].cells[0]; shade(c, NAVY)
    p = c.paragraphs[0]; run(p, "COMPANY BRIEF", 9, True, SAND)
    p = c.add_paragraph(); run(p, d["name"], 26, True, "FFFFFF")
    p = c.add_paragraph(); run(p, d["tagline"], 11.5, False, "DCE3EC")
    p = c.add_paragraph(); run(p, f'{d["as_of"]} 기준  ·  밸류커넥트 리서치', 8.5, False, "AFC0D3")
    doc.add_paragraph()

    kpi_row(doc, d["kpis"])

    n = 1
    heading(doc, n, "회사 개요"); n += 1
    for s in d["summary"]:
        p = para(doc); run(p, s)
    table(doc, ["항목", "내용"], d["profile"], widths=[3.2, 13.4])

    heading(doc, n, "재무 실적"); n += 1
    bullets(doc, d["finance_points"])
    if d.get("financials"):
        chart_financials(doc, d["financials"])
        source_note(doc, d["financials_note"])

    heading(doc, n, "투자 유치"); n += 1
    bullets(doc, d["funding_points"])
    if d.get("rounds"):
        chart_funding(doc, d["rounds"])
        table(doc, ["라운드", "시기", "금액", "주요 투자사"],
              [[r["round"], r["date"], f'{r["amount"]:,}억원' if r.get("amount") else "비공개", r["investors"]] for r in d["rounds"]],
              widths=[2.4, 2.2, 2.4, 9.6])

    hc = d.get("headcount")
    heading(doc, n, "4대보험 가입 인원"); n += 1
    if hc:
        last = hc["series"][-1]
        p = para(doc); run(p, f'{hc["basis"]} ', 10.5, True, NAVY); run(p, f'{last["count"]}명', 10.5, True, NAVY); run(p, f'  ({last["month"]} 기준)', 10.5, False, GRAY)
        bullets(doc, hc.get("points", []))
        chart_headcount(doc, hc)
        if hc.get("other"):
            table(doc, ["구분", "인원", "기준일"], hc["other"], widths=[8.0, 3.6, 5.0])
        p = para(doc, 8); run(p, "출처 · ", 8, False, GRAY); link(p, hc["source"]["title"], hc["source"]["url"], 8)
    else:
        p = para(doc); run(p, "공공데이터에서 사업장을 확인하지 못했습니다(확인 불가).", 10.5, False, GRAY)

    heading(doc, n, "경영진"); n += 1
    table(doc, ["이름", "직책", "주요 이력", "LinkedIn"],
          [[e["name"], e["title"], e["bio"], li_cell(e)] for e in d["executives"]],
          widths=[2.0, 3.6, 8.8, 2.2])
    if d.get("exec_note"):
        source_note(doc, d["exec_note"])

    heading(doc, n, "핵심 인재"); n += 1
    if d.get("key_talent"):
        table(doc, ["이름", "직책", "소속", "주요 이력", "LinkedIn"],
              [[k["name"], k["title"], k["org"], k["bio"], li_cell(k)] for k in d["key_talent"]],
              widths=[2.0, 3.6, 2.8, 6.0, 2.2])
    bullets(doc, d.get("talent", []))
    if d.get("talent_note"):
        source_note(doc, d["talent_note"])

    heading(doc, n, "조직도"); n += 1
    if d.get("org"):
        chart_org(doc, d["org"])
        # 이미지와 같은 내용을 텍스트 노드로도 둔다 (검색·AI 읽기용)
        top = d["org"]["top"]
        p = para(doc, 2); run(p, f'{top["title"]} {top.get("name", "")}', 10, True, NAVY)
        for u in d["org"]["units"]:
            p = para(doc, 2); p.paragraph_format.left_indent = Cm(0.6)
            run(p, "└ ", 10, False, GRAY); run(p, u["title"], 10, True); run(p, f'  {u.get("name", "")}', 10, False, GRAY)
        if d["org"].get("note"):
            source_note(doc, d["org"]["note"])

    heading(doc, n, "제품과 서비스"); n += 1
    bullets(doc, d["products"])

    heading(doc, n, "최근 뉴스"); n += 1
    table(doc, ["날짜", "헤드라인", "매체"],
          [[x["date"], {"text": x["headline"], "url": x["url"]}, x["outlet"]] for x in d["news"]],
          widths=[2.4, 11.4, 2.8])

    heading(doc, n, "참고 자료"); n += 1
    for s in d["sources"]:
        p = para(doc, 2); run(p, "· ", 9, False, GRAY); link(p, s["title"], s["url"], 9)
    p = para(doc, 0); p.paragraph_format.space_before = Pt(10)
    run(p, d["disclaimer"], 8, False, GRAY, italic=True)
    doc.save(out)


if __name__ == "__main__":
    build(json.load(open(sys.argv[1], encoding="utf-8")), sys.argv[2])
    print("wrote", sys.argv[2])
