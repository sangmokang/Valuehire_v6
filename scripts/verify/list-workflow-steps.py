#!/usr/bin/env python3
"""워크플로의 스텝 목록을 낸다. 검사 가능한 정규 형식을 강제한다.

왜 이렇게 하나: 이 저장소에는 YAML 구현이 없다(PyYAML 미설치). 임의의 YAML 을 흉내 내면
반드시 의미가 어긋나는 입력이 생기고, 그것이 곧 거짓 정상이 된다(Codex V2 1~5회차).
그래서 임의 YAML 을 이해하려 하지 않는다 — **워크플로가 좁은 정규 형식을 지키도록 강제**하고,
그 형식을 벗어나면 통과가 아니라 실패로 닫는다(fail-closed).

정규 형식(steps 영역):
  · 파일 전체에 탭 문자 없음, 문서 구분자(---) 없음, jobs 는 1개, steps 는 1개
  · 스텝 항목은 `      - ` (6칸), 스텝 키는 정확히 8칸 `key: `
  · 키는 소문자·숫자·하이픈만. 따옴표·이스케이프·콜론 앞 공백 금지
  · 한 스텝에 같은 키가 두 번 나오면 실패
  · 앵커(&)·별칭(*)·병합(<<:)·흐름 매핑({ [) 금지
  · 블록 스칼라는 `|` 만 허용(지시자·chomping 금지). 본문은 값으로만 읽고 구조로 읽지 않는다

출력: 스텝마다 한 줄, 탭으로 구분한 다섯 칸
  <번호>\t<이름>\t<run 값>\t<run 키 개수>\t<약화 키 목록(쉼표)>
종료값 0=정상, 2=형식 위반(사유를 표준오류로).
"""
import sys, re

STEP_DASH = "      - "
KEY_INDENT = 8
KEY_RE = re.compile(r"^[a-z][a-z0-9-]*: ?")
TOP_KEYS = ("name", "on", "permissions", "jobs", "concurrency")
RUN_KEYS = ("name", "run", "id", "timeout-minutes")


def fail(msg: str) -> int:
    print("형식 위반: " + msg, file=sys.stderr)
    return 2


def main(path: str) -> int:
    text = open(path, encoding="utf-8").read()
    lines = text.splitlines()

    if "\t" in text:
        n = next(i for i, l in enumerate(lines, 1) if "\t" in l)
        return fail("탭 문자 (%d행). YAML 은 들여쓰기에 탭을 허용하지 않는다" % n)
    for i, l in enumerate(lines, 1):
        if l.rstrip() == "---" or l.rstrip() == "...":
            return fail("문서 구분자 (%d행). 이 파일은 문서 하나여야 한다" % i)
        if l and not l[0].isspace() and not l.startswith("#"):
            key = l.split(":", 1)[0]
            if key not in TOP_KEYS:
                return fail("최상위 키 '%s' (%d행). 실행 환경 변경은 허용하지 않는다" % (key, i))

    jobs = [i for i, l in enumerate(lines) if l.startswith("jobs:")]
    if len(jobs) != 1:
        return fail("jobs: 가 %d개" % len(jobs))
    job_names = [i for i, l in enumerate(lines[jobs[0] + 1:], jobs[0] + 1)
                 if re.match(r"^  [A-Za-z_][A-Za-z0-9_-]*:", l)]
    if len(job_names) != 1:
        return fail("jobs 아래 잡이 %d개. 하나여야 한다" % len(job_names))
    # 잡 수준 설정으로 스텝 전체를 끄거나 다른 셸로 돌릴 수 있다(Codex V2 6회차).
    # 잡 수준에는 실행 위치·단계와 정수 시간 제한만 허용한다.
    job_end = next((i for i, l in enumerate(lines[job_names[0] + 1:], job_names[0] + 1)
                    if l.strip() and not l.startswith("    ")), len(lines))
    for i in range(job_names[0] + 1, job_end):
        l = lines[i]
        if not l.strip() or l.lstrip().startswith("#"):
            continue
        if len(l) - len(l.lstrip(" ")) != 4:
            continue
        key = l.strip().split(":", 1)[0]
        if key == "timeout-minutes" and not re.fullmatch(r"[1-9][0-9]*", l.split(":", 1)[1].strip()):
            return fail("잡 시간 제한은 양의 정수여야 한다 (%d행)" % (i + 1))
        if key not in ("runs-on", "steps", "timeout-minutes"):
            return fail("잡 수준 키 '%s' (%d행). runs-on·steps·정수 시간 제한만 쓴다 — "
                        "조건·기본 셸·전략으로 스텝 전체를 끌 수 있다" % (key, i + 1))

    steps_at = [i for i, l in enumerate(lines) if l.rstrip() == "    steps:"]
    if len(steps_at) != 1:
        return fail("steps: 가 %d개" % len(steps_at))

    return list_steps(lines, steps_at[0] + 1)


def list_steps(lines, start):
    """검증된 헤더 뒤 단계 목록을 읽고 동일한 출력 계약으로 내보낸다."""
    steps, cur, seen_keys = [], None, set()
    i = start
    while i < len(lines):
        raw = lines[i]
        if not raw.strip() or raw.lstrip().startswith("#"):
            i += 1
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        if indent < 6 and raw.strip():
            break  # steps 목록 끝

        if raw.startswith(STEP_DASH):
            cur = {"name": "", "run": None, "run_count": 0, "weak": []}
            steps.append(cur)
            seen_keys = set()
            body = raw[len(STEP_DASH):]
            rest = " " * KEY_INDENT + body
        elif indent == KEY_INDENT and cur is not None:
            rest = raw
        elif indent > KEY_INDENT and cur is not None:
            i += 1  # 하위 매핑(with:, env: 등)의 내용. 구조로 읽지 않는다
            continue
        else:
            return fail("스텝 목록에서 알 수 없는 들여쓰기 (%d행): %r" % (i + 1, raw))

        body = rest[KEY_INDENT:]
        if body.startswith(("&", "*")) or body.startswith("<<"):
            return fail("앵커·별칭·병합 키 (%d행). 정규 형식이 아니다" % (i + 1))
        if body[:1] in ("\"", "'"):
            return fail("따옴표로 감싼 키 (%d행). 키는 그대로 적는다" % (i + 1))
        if not KEY_RE.match(body) and body.strip() != "":
            return fail("키 형식 위반 (%d행): %r. 소문자 키 뒤에 바로 콜론이어야 한다" % (i + 1, body))

        key = body.split(":", 1)[0]
        val = body.split(":", 1)[1].strip() if ":" in body else ""
        if key in seen_keys:
            return fail("한 스텝에 같은 키 '%s' 가 두 번 (%d행)" % (key, i + 1))
        seen_keys.add(key)

        if val.startswith(("&", "*")):
            return fail("값 위치의 앵커·별칭 (%d행). 값은 그대로 적는다" % (i + 1))
        if val.startswith(("{", "[")):
            return fail("흐름 매핑·시퀀스 값 (%d행). 블록 형식으로 적는다" % (i + 1))
        if val.startswith((">", "|")) and val not in ("|",):
            return fail("허용하지 않는 블록 스칼라 표기 %r (%d행). `|` 만 쓴다" % (val, i + 1))

        if val == "|":
            body_lines, j = [], i + 1
            while j < len(lines):
                nxt = lines[j]
                if nxt.strip() and (len(nxt) - len(nxt.lstrip(" "))) <= KEY_INDENT:
                    break
                body_lines.append(nxt.strip())
                j += 1
            kept = [b for b in body_lines if b]
            val = kept[0] if len(kept) == 1 else "\n".join(kept)
            i = j
        else:
            if val[:1] in ("\"", "'") and len(val) >= 2 and val[-1] == val[0]:
                val = val[1:-1]
            else:
                val = re.sub(r"\s+#.*$", "", val).strip()
            i += 1

        if key == "name":
            cur["name"] = val
        elif key == "run":
            cur["run_count"] += 1
            cur["run"] = val
        elif key not in RUN_KEYS:
            # 보호하는 run 스텝은 허용 목록만 쓴다. 다른 스텝의 uses/with/env는
            # 열거 결과에 남지만 호출자가 보호 스텝만 골라 판정한다.
            cur["weak"].append(key)

    if not steps:
        return fail("스텝이 0개")

    for n, s in enumerate(steps, 1):
        run = (s["run"] or "").replace("\t", " ").replace("\n", "\\n")
        print("\t".join([str(n), s["name"], run, str(s["run_count"]), ",".join(s["weak"])]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
