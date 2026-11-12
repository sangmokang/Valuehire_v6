"""조사 초안(data) + 볼타 4대보험(bolta) + Grok 인물·조직(grok) → 렌더용 최종 JSON.
usage: python merge.py <brief_dir> <slug>
  <brief_dir>/data/<slug>.json   (필수, wrtn.json 스키마)
  <brief_dir>/bolta/<slug>.json  (선택) {biz,t,np,ei,sa,eid,npd,yoy,h,q,rev,op,ceo,open,ser:"YY.MM:N,..."}
  <brief_dir>/grok/<slug>.json   (선택) {biz_no,legal_name,people:[[name,title,org,background,edu,linkedin]],org:[[unit,lead]]}
  → <brief_dir>/final/<slug>.json
LinkedIn 은 'https://' 로 시작하고 linkedin.com/in/<id> 형태이며 '...' 이 없는 실제 URL 만 쓴다.
"""
import json, os, re, sys

LI = re.compile(r"^https://([a-z]{2,3}\.)?(www\.)?linkedin\.com/in/[A-Za-z0-9\-_%]+/?$")


def li_ok(u):
    return isinstance(u, str) and "..." not in u and bool(LI.match(u.strip()))


def num(s):
    m = re.search(r"[−\-+]?\d[\d,]*", s or "")
    return int(m.group(0).replace(",", "").replace("−", "-")) if m else None


def ym(npd):
    m = re.search(r"(\d{4})년\s*(\d{1,2})월", npd or "")
    return f"{m.group(1)}.{int(m.group(2)):02d}" if m else None


def headcount(b, slug_url):
    ser = []
    for part in (b.get("ser") or "").split(","):
        if ":" in part:
            k, n = part.split(":")
            ser.append({"month": "20" + k.strip(), "count": int(n)})
    ser.sort(key=lambda x: x["month"])
    npn, npm = num(b.get("np")), ym(b.get("npd"))
    mismatch = False
    if ser and npn is not None and ser[-1]["count"] != npn:
        mismatch = True  # 시계열 최신값과 공표 최신값이 다르면 시계열을 쓰지 않는다
        ser = [{"month": npm or ser[-1]["month"], "count": npn}]
    if not ser and npn is not None:
        ser = [{"month": npm or "기준월 확인 불가", "count": npn}]
    if not ser:
        return None
    other = []
    if b.get("ei"):
        other.append(["고용보험 상시근로자", b["ei"], (b.get("eid") or "").replace(" 기준", "")])
    if b.get("sa"):
        other.append(["산재보험 상시근로자", b["sa"], (b.get("eid") or "").replace(" 기준", "")])
    if b.get("np"):
        other.append(["국민연금 가입자 (대표자 포함)", b["np"], (b.get("npd") or "").replace(" 기준", "")])
    pts = []
    if b.get("yoy"):
        body = f'국민연금 가입자 기준 1년 전보다 {b["yoy"]}입니다.'
        if b.get("h") and b.get("q"):
            body += f' 최근 12개월 입사 {b["h"]}, 퇴사 {b["q"]}입니다.'
        pts.append({"head": "1년 증감", "body": body})
    if mismatch:
        pts.append({"head": "추이 생략", "body": "월별 추이의 최신값이 공표 최신값과 달라 추이 그래프를 싣지 않았습니다."})
    pts.append({"head": "기준별 차이", "body": "국민연금에는 대표자가 포함되고, 고용·산재보험은 대표 사업장의 상시근로자 수만 집계해 수치가 다를 수 있습니다."})
    via = " · Grok 경유 조회, 원문 대조 전" if b.get("via") == "grok" else ""
    return {"basis": "국민연금 가입자", "series": ser, "other": other, "points": pts,
            "source": {"title": f'볼타 · {b.get("t", "")} 사업자정보 (국민연금공단·근로복지공단 공공데이터{via})', "url": slug_url}}


def is_ceo_title(t):
    t = t or ""
    return bool(re.search(r"대표|CEO", t)) and not re.search(r"(전|前)\s*대표|前|former", t, re.I)


def pick_top(d, b):
    if b and b.get("ceo"):
        names = [x.strip() for x in re.split(r"[,·]", b["ceo"]) if x.strip()]
        if names:
            return {"title": "공동대표" if len(names) > 1 else "대표이사", "name": " · ".join(names)}
    exs = d.get("executives", [])
    cands = [e for e in exs if is_ceo_title(e.get("title"))]
    if cands:
        co = [cands[0]] + [e for e in cands[1:] if re.search(r"공동|각자", e.get("title") or "")]
        co = co[:3]
        return {"title": "공동대표" if len(co) > 1 else "대표이사", "name": " · ".join(e["name"] for e in co)}
    return {"title": "대표", "name": "확인 불가"}


def main(root, slug):
    d = json.load(open(os.path.join(root, "data", slug + ".json"), encoding="utf-8"))
    bp, gp = os.path.join(root, "bolta", slug + ".json"), os.path.join(root, "grok", slug + ".json")
    b = None
    if os.path.exists(bp):
        b = json.load(open(bp, encoding="utf-8"))
        url = f'https://bolta.io/biz/{b["biz"]}'
        hc = headcount(b, url)
        if hc:
            d["headcount"] = hc
            last = hc["series"][-1]
            mark = " · 대조 전" if b.get("via") == "grok" else ""
            kp = {"value": f'{last["count"]}명', "label": f'국민연금 가입자 ({last["month"][2:]}{mark})'}
            ks = d.setdefault("kpis", [])
            idx = next((i for i, k in enumerate(ks) if any(w in k.get("label", "") for w in ("임직원", "직원", "인원", "국민연금", "4대보험"))), None)
            if idx is None and len(ks) >= 4:
                idx = 3
            if idx is None:
                ks.append(kp)
            else:
                ks[idx] = kp
            src = {"title": "볼타 · 4대보험 가입 인원 (공공데이터)", "url": url}
            if all(s.get("url") != url for s in d.get("sources", [])):
                d.setdefault("sources", []).insert(0, src)
        d["biz_no"] = b["biz"]
    if os.path.exists(gp):
        g = json.load(open(gp, encoding="utf-8"))
        names = {e["name"] for e in d.get("executives", [])}
        gl = {p[0]: p for p in g.get("people", []) if p and p[0]}
        for e in d.get("executives", []):
            p = gl.get(e["name"])
            if p and li_ok(p[5]) and not e.get("linkedin"):
                e["linkedin"] = p[5].strip()
            if e.get("linkedin") and not li_ok(e["linkedin"]):
                e.pop("linkedin")
        kt = []
        excluded = d.get("exec_note") or ""
        for p in g.get("people", []):
            name, title, org, bg, edu, li = (list(p) + [None] * 6)[:6]
            if not name or name in names:
                continue
            if name.split("(")[0].strip() in excluded:  # 조사 단계에서 일부러 뺀 인물은 다시 넣지 않는다
                continue
            bio = "; ".join(x for x in (bg, edu) if x) or "공개 이력 확인 불가"
            item = {"name": name, "title": title or "확인 불가", "org": org or "확인 불가", "bio": bio}
            if li_ok(li):
                item["linkedin"] = li.strip()
            kt.append(item)
        if kt:
            d["key_talent"] = kt
        units = [{"title": u[0], "name": u[1] or "책임자 확인 불가"} for u in g.get("org", []) if u and u[0]]
        if units:
            d["org"] = {"top": pick_top(d, b), "units": units[:6],
                        "note": "공식 조직도가 공개되지 않아 Grok 조사(2026.11.12)와 공개 자료에서 확인된 조직·책임자로 구성했습니다(보고선 미확인)."}
        d["talent_note"] = "핵심 인재는 Grok 조사(2026.11.12)로 수집한 공개 프로필·보도 자료이며, 개별 재직 여부와 LinkedIn 프로필은 원문 대조 전입니다."
    d.setdefault("key_talent", [])
    if d.get("org"):
        d["org"]["top"] = pick_top(d, b)
    # 상태 재계산: 4대보험을 채웠으면 해당 미완 항목을 지운다
    st = d.get("status") or ""
    if st.startswith("보류"):
        pass
    else:
        items = [x.strip() for x in re.split(r"[,·、]\s*(?![^()]*\))", st.split(":", 1)[-1]) if x.strip()] if st.startswith("부분 완료") else []
        if d.get("headcount"):
            items = [x for x in items if not re.search(r"4대보험|국민연금|사업자번호|월별 (인원|추이)", x)]
            if b and b.get("via") == "grok":
                items.append("4대보험 수치 원문 대조(Grok 경유 조회)")
        if d.get("org"):
            items = [x for x in items if not re.fullmatch(r"조직도", x)]
        if d.get("key_talent"):
            items = [x for x in items if not re.fullmatch(r"핵심 인재(\s*단계 미실시)?", x)]
            items.append("핵심 인재 재직·LinkedIn 원문 대조(Grok 조사)")
        if any(p.get("linkedin") for p in d.get("executives", []) + d.get("key_talent", [])):
            items = [x for x in items if x != "LinkedIn"]
        d["status"] = "부분 완료: " + ", ".join(items) if items else "완료"
    os.makedirs(os.path.join(root, "final"), exist_ok=True)
    json.dump(d, open(os.path.join(root, "final", slug + ".json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return d


if __name__ == "__main__":
    d = main(sys.argv[1], sys.argv[2])
    print(sys.argv[2], "headcount" in d and d["headcount"] is not None, len(d.get("key_talent", [])), bool(d.get("org")))
