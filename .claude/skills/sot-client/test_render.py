"""sot-client 렌더러 계약 테스트. 실행: python3 test_render.py (python-docx·matplotlib 필요)
인수 기준: 예시 JSON 으로 만든 브리프에 필수 섹션 9개, 4대보험 인원(기준·시점 포함), 핵심 인재 표,
조직도 텍스트 노드, 뉴스 헤드라인 하이퍼링크가 모두 존재하고, 확인 안 된 LinkedIn 은 URL 대신 '확인 불가'로 남는다.
"""
import json, os, subprocess, sys, tempfile, zipfile, re

HERE = os.path.dirname(os.path.abspath(__file__))
EX = os.path.join(HERE, "examples", "wrtn.json")


def render(data):
    with tempfile.TemporaryDirectory() as d:
        src = os.path.join(d, "in.json"); out = os.path.join(d, "out.docx")
        json.dump(data, open(src, "w", encoding="utf-8"), ensure_ascii=False)
        subprocess.run([sys.executable, os.path.join(HERE, "render.py"), src, out], check=True, capture_output=True)
        z = zipfile.ZipFile(out)
        xml = z.read("word/document.xml").decode("utf-8")
        rels = z.read("word/_rels/document.xml.rels").decode("utf-8")
        return re.sub(r"<[^>]+>", "", xml), xml, rels


def main():
    data = json.load(open(EX, encoding="utf-8"))
    text, xml, rels = render(data)
    fails = []
    for sec in ["회사 개요", "재무 실적", "투자 유치", "4대보험 가입 인원", "경영진", "핵심 인재", "제품과 서비스", "조직도", "최근 뉴스"]:
        if sec not in text:
            fails.append(f"section missing: {sec}")
    hc = data["headcount"]
    if f'{hc["series"][-1]["count"]}명' not in text or hc["basis"] not in text:
        fails.append("4대보험 인원(최신값·기준) missing")
    for n in data["news"]:
        if n["url"] not in rels:
            fails.append(f"news hyperlink missing: {n['url']}")
    for p in data["key_talent"]:
        if p["name"] not in text:
            fails.append(f"key talent missing: {p['name']}")
        if not p.get("linkedin") and "확인 불가" not in text:
            fails.append("unverified LinkedIn not marked 확인 불가")
    for u in data["org"]["units"]:
        if u["title"] not in text:
            fails.append(f"org node text missing: {u['title']}")
    li = [l for l in re.findall(r'Target="([^"]+)"', rels) if "linkedin.com/in/" in l]
    allowed = {p["linkedin"] for p in data["key_talent"] + data["executives"] if p.get("linkedin")}
    for l in li:
        if l.replace("&amp;", "&") not in allowed:
            fails.append(f"LinkedIn URL not from data: {l}")
    print("\n".join(fails) if fails else "PASS")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
