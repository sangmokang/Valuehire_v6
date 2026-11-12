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
    print("\n".join(fails) if fails else "PASS")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
