#!/usr/bin/env python3
"""워크플로의 스텝을 YAML 규칙대로 읽어 한 줄씩 내보낸다.

왜 있나: `- name:` 을 문자열로 쪼개면 앞 스텝의 여러 줄 문자열(run: | ...) 안에 적힌
가짜 스텝 머리글도 스텝으로 세어진다. 실제로 그 위조가 검사를 통과했다(Codex V2 3회차).
표준 라이브러리만 쓴다 — 외부 YAML 구현에 기대지 않는다.

출력: 스텝마다 한 줄, 탭으로 구분한 다섯 칸
  <번호>\t<이름>\t<run 값>\t<run 키 개수>\t<약화 키 목록(쉼표)>
run 값은 홑/겹따옴표를 벗기고, 뒤에 붙은 주석을 떼고, 한 줄짜리 블록 스칼라는 그 한 줄로 편다.
"""
import sys, re

def strip_comment(v: str) -> str:
    # 따옴표 밖의 " #" 뒤는 주석이다.
    out, quote = [], None
    i = 0
    while i < len(v):
        c = v[i]
        if quote:
            out.append(c)
            if c == quote:
                quote = None
        elif c in "\"'":
            quote = c
            out.append(c)
        elif c == "#" and (not out or out[-1] in " \t"):
            break
        else:
            out.append(c)
        i += 1
    return "".join(out).strip()

def unquote(v: str) -> str:
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        return v[1:-1]
    return v

def main(path: str) -> int:
    lines = open(path, encoding="utf-8").read().splitlines()
    steps, cur, step_indent = [], None, None
    i = 0
    while i < len(lines):
        raw = lines[i]
        stripped = raw.strip()
        indent = len(raw) - len(raw.lstrip(" "))

        if not stripped or stripped.startswith("#"):
            i += 1
            continue

        m = re.match(r"^-\s+(.*)$", stripped)
        if m and (step_indent is None or indent <= step_indent):
            # 새 항목의 시작. 스텝 목록의 들여쓰기를 첫 항목에서 고정한다.
            if step_indent is None or indent < step_indent:
                step_indent = indent
            if indent == step_indent:
                cur = {"name": "", "run": None, "run_count": 0, "weak": []}
                steps.append(cur)
                stripped = m.group(1)
                indent = indent + 2
            else:
                i += 1
                continue

        if cur is None or indent != step_indent + 2:
            i += 1
            continue

        km = re.match(r"^(\"[^\"]+\"|'[^']+'|[^:\s]+)\s*:\s*(.*)$", stripped)
        if not km:
            i += 1
            continue
        key = unquote(km.group(1)).strip()
        val = km.group(2)

        if val in ("|", ">", "|-", ">-", "|+", ">+"):
            body, j = [], i + 1
            while j < len(lines):
                nxt = lines[j]
                if nxt.strip() and (len(nxt) - len(nxt.lstrip(" "))) <= indent:
                    break
                body.append(nxt.strip())
                j += 1
            body = [b for b in body if b]
            val = body[0] if len(body) == 1 else "\n".join(body)
            i = j
        else:
            val = unquote(strip_comment(val))
            i += 1

        if key == "name":
            cur["name"] = val
        elif key == "run":
            cur["run_count"] += 1
            cur["run"] = val          # YAML 은 같은 키가 겹치면 뒤엣것을 쓴다
        elif key in ("if", "continue-on-error"):
            cur["weak"].append(key)

    for n, s in enumerate(steps, 1):
        run = (s["run"] or "").replace("\t", " ").replace("\n", "\\n")
        print("\t".join([str(n), s["name"], run, str(s["run_count"]), ",".join(s["weak"])]))
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
