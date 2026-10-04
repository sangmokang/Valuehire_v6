#!/usr/bin/env python3
"""Cursor 용 지시문을 ChatGPT 용으로 바꾼다: git checkout 지시 → 줄번호 붙은 HEAD 원문 첨부.
usage: gpt_bundle.py planner <out>
       gpt_bundle.py wu <WUxx> <out>
       gpt_bundle.py audit <WUxx> <reviewer.json> <out>
       gpt_bundle.py integ <summary.json> <out>"""
import json, re, subprocess, sys
from pathlib import Path

import os
REPO = Path(os.environ["LCR_REPO"])
R = Path(os.environ["LCR_ROOT"]); PRD = R / f"pr{os.environ['LCR_PR']}"
SHA = os.environ["LCR_SHA"]
sys.path.insert(0, str(Path(__file__).parent))
import make_wu_prompt as M  # noqa: E402

PLAN = json.load(open(PRD / "planner.json"))
FILES = {w["id"]: w["files"] for w in PLAN["wus"]}
EXTRA = json.loads(os.environ.get("LCR_EXTRA_FILES", "{}"))  # 예: {"WU07":["scripts/x.sh"],"INTEG":["scripts/x.sh"]}
BUNDLE_NOTE = f"""- GitHub 플러그인으로 sangmokang/Valuehire_v6 를 커밋 {SHA} 기준으로 '읽기 전용' 조회할 수 있습니다(호출 관계·첨부 밖 파일 확인용).
  GitHub 쓰기 작업(코멘트·리뷰·승인·이슈·PR·브랜치·워크플로 실행) 절대 금지. 조회도 안 되면 그 사실을 적고 첨부만으로 진행하세요.
- 아래 [첨부 원문]이 HEAD {SHA} 의 파일 원문(줄번호 포함)입니다.
  head_sha_checked 에는 첨부 머리말의 SHA 를 그대로 적으세요. 첨부에 없는 파일은 '첨부 밖 — 확인 불가'로 표시하고 추측하지 마세요.
  호출 관계는 첨부 원문(필요하면 GitHub 조회)에서 찾아 file:line 으로 적으세요. 시험은 실행하지 않았다면 NOT_RUN 으로 적으세요.
"""

SEEN_RULE = """
[누락 검사 — 필수] 출력 JSON 에 "bundle_files_seen":[{"file":"경로","last_line_seen":N}] 를 첨부 파일 전부에 대해 넣으세요.
N 은 각 파일의 END FILE 표식 바로 앞 줄번호(직접 본 값)입니다. 첨부가 잘려 보이거나 END FILE 표식이 안 보이면 그 파일 N 을 0 으로 적고 TRUNCATED 라고 요약에 쓰세요.
JSON 은 표식 줄 사이에 ```json 코드블록 없이 그대로 쓰세요."""

def show(f):
    return subprocess.run(["git", "-C", str(REPO), "show", f"{SHA}:{f}"], capture_output=True, text=True).stdout

def attach(paths):
    out = [f"\n[첨부 원문 — HEAD {SHA}]"]
    for f in sorted(paths):
        body = show(f)
        numbered = "\n".join(f"{i:>4}| {l}" for i, l in enumerate(body.splitlines(), 1))
        n = len(body.splitlines())
        out.append(f"\n===== FILE: {f} ({n} lines) =====\n{numbered}\n===== END FILE: {f} (last line {n}) =====")
    out.append(f"\n[첨부 끝 — 파일 {len(paths)}개: " + ", ".join(sorted(paths)) + "]")
    out.append(SEEN_RULE)
    return "\n".join(out)

def adapt(text):
    text = re.sub(r"- 먼저 실행: git fetch.*?멈추세요\.\n(  결과가 다르면.*?멈추세요\.\n)?", BUNDLE_NOTE, text, flags=re.S)
    return text.replace("rg 로 추적(명령과 결과 줄 수 기재)", "첨부 원문에서 추적(file:line 기재)")

def code(f):
    return not f.endswith((".md", "uv.lock"))

def wu_files(wid):
    w = next(x for x in PLAN["wus"] if x["id"] == wid)
    return set(w["files"]) | {f for r in w.get("related_wus", []) for f in FILES[r] if code(f)} | set(EXTRA.get(wid, []))

kind = sys.argv[1]
if kind == "planner":
    text = M.planner_prompt()
    text = re.sub(r"- 먼저 실행: git fetch.*?BLOCKED_CODEBASE_CONTEXT 라고 쓰고 멈추세요\.\)\n", BUNDLE_NOTE +
                  "- 변경 목록은 첨부 [PR diff] 에서 직접 세세요. numstat_cmd_output 에는 직접 센 파일별 +/− 를 적으세요.\n", text, flags=re.S)
    allfiles = [r["file"] for r in PLAN["coverage_ledger"] if code(r["file"])]
    text += "\n[PR diff — gh pr diff 원문]\n" + (PRD / "pr.diff").read_text() + "\n[PR diff 끝]\n"
    out = sys.argv[2]
elif kind == "wu":
    text = adapt(M.wu_prompt(PLAN, sys.argv[2])) + attach(wu_files(sys.argv[2])); out = sys.argv[3]
elif kind == "audit":
    text = adapt(M.auditor_prompt(PLAN, sys.argv[2], json.load(open(sys.argv[3])))) + attach(wu_files(sys.argv[2])); out = sys.argv[4]
elif kind == "integ":
    paths = {f for fs in FILES.values() for f in fs if code(f)} | set(EXTRA.get("INTEG", []))
    text = adapt(M.integration_prompt(PLAN, json.load(open(sys.argv[2])))) + attach(paths); out = sys.argv[3]
Path(out).write_text(text)
print(out, len(text), "chars", "git" in text.split("[첨부 원문")[0].split("[대상]")[-1][:600])
