"""merge.py 회귀 테스트 (2026-11-12 readback 에서 발견된 결함). 실행: python3 test_merge.py
1) 조직도 최상단은 직책에 '대표'가 들어간 경영진이다 (첫 번째 경영진이 회장이어도).
2) 조직 정보가 없으면 조직도 섹션에 '공개된 조직 정보 없음' 문구가 나온다.
3) exec_note 에서 일부러 뺀 인물은 Grok 핵심 인재로 다시 들어오지 않는다.
"""
import json, os, subprocess, sys, tempfile, zipfile, re

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import merge  # noqa: E402


def base():
    d = json.load(open(os.path.join(HERE, "examples", "wrtn.json"), encoding="utf-8"))
    d["executives"] = [
        {"name": "송회장", "title": "회장 · 창업자", "bio": "x"},
        {"name": "오대표", "title": "대표이사", "bio": "y"},
    ]
    d["exec_note"] = "남재무 CFO 등 시점이 불분명한 인물은 싣지 않았습니다."
    d.pop("key_talent", None); d.pop("org", None)
    return d


def run(d, grok):
    root = tempfile.mkdtemp()
    for sub in ("data", "grok"):
        os.makedirs(os.path.join(root, sub))
    json.dump(d, open(os.path.join(root, "data", "t.json"), "w", encoding="utf-8"), ensure_ascii=False)
    if grok is not None:
        json.dump(grok, open(os.path.join(root, "grok", "t.json"), "w", encoding="utf-8"), ensure_ascii=False)
    return merge.main(root, "t"), root


def run_b(d, grok, bolta):
    root = tempfile.mkdtemp()
    for sub in ("data", "grok", "bolta"):
        os.makedirs(os.path.join(root, sub))
    json.dump(d, open(os.path.join(root, "data", "t.json"), "w", encoding="utf-8"), ensure_ascii=False)
    json.dump(grok, open(os.path.join(root, "grok", "t.json"), "w", encoding="utf-8"), ensure_ascii=False)
    if bolta is not None:
        json.dump(bolta, open(os.path.join(root, "bolta", "t.json"), "w", encoding="utf-8"), ensure_ascii=False)
    return merge.main(root, "t"), root


def text_of(final, root):
    p = os.path.join(root, "final", "t.json"); out = os.path.join(root, "o.docx")
    subprocess.run([sys.executable, os.path.join(HERE, "render.py"), p, out], check=True, capture_output=True)
    return re.sub(r"<[^>]+>", "", zipfile.ZipFile(out).read("word/document.xml").decode("utf-8"))


def main():
    fails = []
    g = {"people": [["남재무", "CFO", "재무", None, None, None], ["김인재", "CTO", "기술", "前 A사", None, None]],
         "org": [["재무", "CFO 남재무"], ["기술", "CTO 김인재"]]}
    f, root = run(base(), g)
    top = f["org"]["top"]
    if top.get("name") != "오대표" or "대표" not in top.get("title", ""):
        fails.append(f"org top wrong: {top}")
    names = [k["name"] for k in f.get("key_talent", [])]
    if "남재무" in names:
        fails.append("excluded person re-added from Grok")
    if "김인재" not in names:
        fails.append("valid Grok person missing")
    f2, root2 = run(base(), {"people": [], "org": []})
    if "공개된 조직 정보 없음" not in text_of(f2, root2):
        fails.append("empty org section has no placeholder text")
    # Codex 적대 검증 2026-11-12
    # (a) 볼타 대표자 우선, '전 대표' 제외
    d = base(); d["executives"] = [{"name": "박전대", "title": "사내이사(전 대표이사)", "bio": "x"}, {"name": "이현대", "title": "CEO", "bio": "y"}]
    f, root = run_b(d, g, {"biz": "1", "t": "주식회사 T", "np": "10명", "npd": "2026년 9월 자료 기준", "ceo": "이현대", "ser": "26.08:9,26.09:10"})
    if f["org"]["top"]["name"] != "이현대":
        fails.append(f"bolta ceo not used: {f['org']['top']}")
    # (a2) 볼타 대표자 없으면 공동/각자 대표만 함께, 자회사 대표는 제외
    d = base(); d["executives"] = [{"name": "김공동", "title": "공동대표", "bio": "x"}, {"name": "이공동", "title": "공동대표", "bio": "y"}, {"name": "박자회사", "title": "에이사 대표", "bio": "z"}]
    f, root = run_b(d, g, {"biz": "1", "t": "T", "np": "10명", "npd": "2026년 9월 자료 기준", "ser": "", "via": "grok"})
    if f["org"]["top"]["name"] != "김공동 · 이공동":
        fails.append(f"co-CEO handling wrong: {f['org']['top']}")
    # (b) Grok 경유 보험 수치는 완료로 승격하지 않고 KPI 에 대조 전 표시
    d = base(); d["status"] = "부분 완료: 4대보험(볼타 차단), 매출"
    f, root = run_b(d, g, {"biz": "1", "t": "T", "np": "10명", "npd": "2026년 9월 자료 기준", "ceo": "오대표", "ser": "26.08:9,26.09:10", "via": "grok"})
    if "원문 대조" not in f["status"]:
        fails.append(f"grok headcount promoted: {f['status']}")
    if not any("대조 전" in k["label"] for k in f["kpis"]):
        fails.append("KPI lacks 대조 전 mark")
    # (c) 기준월은 npd 에서, 시계열 최신값 불일치면 그래프 제거
    d = base()
    f, root = run_b(d, g, {"biz": "1", "t": "T", "np": "12명", "npd": "2027년 1월 자료 기준", "ceo": "오대표", "ser": ""})
    if f["headcount"]["series"][-1]["month"] != "2027.01":
        fails.append(f"month not from npd: {f['headcount']['series']}")
    f, root = run_b(base(), g, {"biz": "1", "t": "T", "np": "100명", "npd": "2026년 9월 자료 기준", "ceo": "오대표", "ser": "26.08:98,26.09:99"})
    if len(f["headcount"]["series"]) != 1 or f["headcount"]["series"][0]["count"] != 100:
        fails.append("series/np mismatch not handled")
    # (d) 투자 그래프는 '누적'이라 단정하지 않는다, (e) 부분 완료면 문서에 확인할 사항 표시
    d = base(); d["status"] = "부분 완료: 매출, 기업가치"
    f, root = run_b(d, g, None)
    txt = text_of(f, root)
    if "자료 범위" not in txt or "기업가치" not in txt.split("자료 범위")[-1]:
        fails.append("partial status not shown in document")
    if "Grok" not in txt or "대조 전" not in txt:
        fails.append("talent provenance not marked as unverified")
    # (f) exec_note 로 뺀 인물은 조직도 노드에서도 빠진다
    f, root = run(base(), g)
    if any("남재무" in u["name"] for u in f["org"]["units"]):
        fails.append(f"excluded person still in org units: {f['org']['units']}")
    # (g) 웹 검색으로 확인한 4대보험 값(webnp)이 있으면 Grok 경유 표시를 웹 출처로 바꾼다
    root = tempfile.mkdtemp()
    for sub in ("data", "grok", "bolta", "webnp", "li"):
        os.makedirs(os.path.join(root, sub))
    dd = base(); dd["status"] = "부분 완료: 4대보험(볼타 차단)"
    json.dump(dd, open(os.path.join(root, "data", "t.json"), "w", encoding="utf-8"), ensure_ascii=False)
    json.dump(g, open(os.path.join(root, "grok", "t.json"), "w", encoding="utf-8"), ensure_ascii=False)
    json.dump({"biz": "1", "t": "T", "np": "10명", "npd": "2026년 9월 자료 기준", "ceo": "오대표", "ser": "", "via": "grok"},
              open(os.path.join(root, "bolta", "t.json"), "w", encoding="utf-8"), ensure_ascii=False)
    json.dump({"slug": "t", "np": "11명", "npd": "2026년 10월 자료 기준", "source_url": "https://example.com/t", "source_title": "원티드 인사이트 · T", "matches_grok": False},
              open(os.path.join(root, "webnp", "t.json"), "w", encoding="utf-8"), ensure_ascii=False)
    json.dump([{"slug": "t", "name": "오대표", "linkedin": "https://kr.linkedin.com/in/oh-ceo"}, {"slug": "t", "name": "김인재", "linkedin": "https://bad.example/in/x"}],
              open(os.path.join(root, "li", "found_1.json"), "w", encoding="utf-8"), ensure_ascii=False)
    f = merge.main(root, "t")
    if f["headcount"]["series"][-1]["count"] != 11 or "example.com/t" not in f["headcount"]["source"]["url"]:
        fails.append(f"web headcount not applied: {f['headcount']['series']} {f['headcount']['source']}")
    if any("대조 전" in k["label"] for k in f["kpis"]) or "4대보험 수치 원문 대조" in f["status"]:
        fails.append("web-verified headcount still marked unverified")
    ex = {e["name"]: e for e in f["executives"]}
    if ex["오대표"].get("linkedin") != "https://kr.linkedin.com/in/oh-ceo":
        fails.append("web LinkedIn not applied to executive")
    if any(k.get("linkedin") == "https://bad.example/in/x" for k in f["key_talent"]):
        fails.append("invalid web LinkedIn accepted")
    print("\n".join(fails) if fails else "PASS")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
