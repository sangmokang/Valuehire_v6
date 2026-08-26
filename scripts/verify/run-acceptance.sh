#!/usr/bin/env bash
# run-acceptance.sh — 인수 검사가 "실행됐다"가 아니라 "실제로 무언가를 판정했다"를 강제한다.
#
# 왜 필요한가 (2026-08-21):
#   scripts/acceptance-hs-a4.sh 의 본문을 통째로 `exit 0` 으로 바꿔도 CI 는 초록이었다.
#   CI 는 스크립트를 부르고 종료값만 봤기 때문이다. 종료값 0 은 "검사가 통과했다"와
#   "검사가 아무것도 하지 않았다"를 구분하지 못한다.
#
# 왜 더 강해졌는가 (2026-08-27):
#   위 계약은 "판정 낱말이 없는 것"만 막았다. 인수 검사 33개 전부에 대해 아래 셋이
#   그대로 통과했다 — `echo "VERDICT: PASS"` 한 줄, `echo "PASSWORD 검사 없음"`
#   (PASS 를 부분 문자열로 셌다), `echo "PASS: ..."` + `echo "CHECKED: 42"`.
#   그래서 판정 낱말을 줄 앞머리 토큰으로만 세고, **본문이 출력밖에 하지 않는 스크립트**를
#   따로 거부한다.
#
# 계약: 대상 스크립트가 종료값 0 으로 끝났다면
#       ① 표준 출력의 줄 앞머리에 판정 토큰(`PASS…` / `OK…` / `<TOKEN>: PASS`)이 있어야 하고
#       ② CHECKED 관례를 따르면 그 값이 1 이상이어야 하며
#       ③ 본문이 출력·종료 계열 명령만으로 이뤄져 있으면 안 된다.
#       하나라도 어기면 이 래퍼가 불합격시킨다.
#
# 막는 것 / 막지 못하는 것:
#   막는다   — 본문 삭제, `exit 0`, `true`, `: # no-op`, 빈 파일, 검사 함수 제거,
#              조용한 조기 종료, 합격 문구만 찍기, 낱말 부분 일치(PASSWORD), 가짜 CHECKED
#   막지 못함 — 아무 의미 없는 명령을 섞어 ③ 을 피한 위조(`git status >/dev/null; echo "PASS: x"`).
#              그것은 acceptance-0-6(가짜 검증 스크립트 탐지)과 사람 리뷰의 몫이다.
#              여기서 다 막는다고 주장하지 않는다.
set -uo pipefail

target="${1:-}"
if [ -z "$target" ]; then
  echo "FAIL: 대상 인수 검사 경로가 없다 — 사용법: $0 <script.sh> [args...]"
  exit 2
fi
if [ ! -f "$target" ]; then
  echo "FAIL: 대상 인수 검사가 없다 — $target"
  exit 2
fi

# ── ③ 본문이 출력밖에 하지 않는가 (실행 전 정적 판정) ────────────────────────
#
# 주석·빈 줄·shebang 을 걷어낸 뒤 남는 명령이 전부 출력·종료 계열이면, 그 스크립트는
# 무엇도 검사하지 않고 합격 문구만 찍는 것이다. 판정 낱말은 얼마든지 찍을 수 있으므로
# 출력만 보고는 구분할 수 없다 — 본문을 봐야 한다.
#
# 방향을 정해 둔다: 애매하면 통과시킨다(정상 검사를 오차단하지 않는다). 명백히
# 출력·종료만 하는 것만 거부한다.
only_output=$(awk '
  { line = $0
    sub(/^[[:space:]]+/, "", line)
    sub(/[[:space:]]+$/, "", line)
    if (line == "") next
    if (line ~ /^#/) next
    total += 1
    if (line ~ /^(echo|printf|exit([[:space:]]|$)|true$|:$|:[[:space:]]*#)/) {
      # 출력 명령처럼 보여도 **파일을 쓰면** 부수 효과가 있다. `printf ... > marker` 가
      # 그렇고, pre-push 런타임 증명의 probe 가 실제로 그 형태다 — 이것까지 "출력뿐"으로
      # 세면 정상 검사를 오차단한다.
      #
      # 반대로 파이프·stderr 리다이렉트·빈 명령 치환은 부수 효과가 아니다.
      # 2026-08-27 V1 F7 실측: `echo "PASS: ok" | cat` · `>&2` · `$(:)` 한 글자로
      # 위조본이 전부 되살아났다. 하한이 파이프 문자 하나였던 셈이다.
      if (line ~ /[0-9]?>>?[[:space:]]*[^&[:space:]]/) next     # 파일로 쓴다
      if (line ~ /\$\([[:space:]]*[^:)[:space:]]/) next         # 실제 명령을 부르는 치환(빈 :() 제외)
      if (line ~ /`[^`]+`/) next                                # 백틱 명령 치환
      output += 1
    }
  }
  END {
    if (total == 0) { print "empty"; exit }
    if (output == total) { print "output-only" } else { print "has-work" }
  }
' "$target")

case "$only_output" in
  empty)
    echo "FAIL(run-acceptance): $target 의 본문이 비어 있다 — 검사하지 않는 검사는 합격이 아니다."
    exit 1
    ;;
  output-only)
    echo "FAIL(run-acceptance): $target 이 출력·종료 명령만으로 이뤄져 있다."
    echo "  판정 문구는 얼마든지 찍을 수 있다. 무엇을 어떻게 확인했는지가 본문에 있어야 한다."
    exit 1
    ;;
esac

out=$(mktemp) || {
  echo "FAIL: 임시 출력 파일 생성 실패 — 판정 근거를 모을 수 없다"
  exit 2
}
trap 'rm -f "$out"' EXIT

shift
bash "$target" "$@" 2>&1 | tee "$out"
rc=${PIPESTATUS[0]}

if [ "$rc" -ne 0 ]; then
  # 원래 실패는 원래 종료값 그대로 넘긴다. 래퍼가 실패 이유를 바꾸지 않는다.
  echo "FAIL(run-acceptance): $target 종료값 $rc"
  exit "$rc"
fi

# ── ① 판정 토큰을 줄 앞머리에서만 센다 ──────────────────────────────────────
#
# 이전 판은 `grep -c 'PASS'` 였다. 그래서 `PASSWORD` 한 낱말이 판정 1건으로 셌다.
# 허용하는 형태는 저장소 선례 그대로다:
#   `PASS: …` · `PASS(…)` · `OK: …` · `OK(run-acceptance): …` · `VERDICT: PASS` ·
#   `SOT_LOAD: PASS …` 같은 `<TOKEN>: PASS` 형태.
pass_lines=$(grep -cE '^[[:space:]]*(PASS|OK)([:(]|[[:space:]])|^[[:space:]]*[A-Za-z_][A-Za-z0-9_]*:[[:space:]]*PASS([[:space:]]|$)' "$out")
if [ "$pass_lines" -lt 1 ]; then
  echo "FAIL(run-acceptance): $target 이 종료값 0 이지만 판정을 한 건도 내놓지 않았다."
  echo "  실행됐다는 사실은 검사했다는 증거가 아니다 — 본문이 비었거나 조기 종료했을 수 있다."
  echo "  판정은 줄 앞머리 토큰이어야 한다(PASS: / OK: / VERDICT: PASS). 낱말 일부는 세지 않는다."
  exit 1
fi

# ── ② CHECKED 관례를 따르는 검사기는 건수 0 도 불합격이다 ───────────────────
if grep -q 'CHECKED:' "$out"; then
  checked=$(grep 'CHECKED:' "$out" | tail -1 | sed 's/.*CHECKED:[[:space:]]*//' | tr -cd '0-9')
  if [ -z "$checked" ] || [ "$checked" -lt 1 ]; then
    echo "FAIL(run-acceptance): $target 의 CHECKED 건수가 ${checked:-없음} — 검사 대상 0개는 합격이 아니다."
    exit 1
  fi
  echo "OK(run-acceptance): $target — 판정 ${pass_lines}건, CHECKED ${checked}"
  exit 0
fi

echo "OK(run-acceptance): $target — 판정 ${pass_lines}건"
