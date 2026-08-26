#!/usr/bin/env bash
# check-pytest-baseline.sh — 제품 시험이 승인된 기준선보다 줄지 않았는지 본다 (P20·AC9).
#
# 왜 필요한가:
#   scripts/acceptance-hs-gates.sh:60 은 `collected < 1` 만 본다. 시험을 1개만 남기고
#   나머지를 지워도 그 게이트는 초록이다. "0건이 아니다"는 "줄지 않았다"가 아니다.
#   줄어든 것을 알려면 **줄기 전 값**이 어딘가에 승인된 채로 있어야 한다.
#
# 기준선은 docs/sot/ci-required-manifest.yaml 의 pytest_baseline 에 둔다. 기준선을
# 낮추는 것 자체가 diff 로 남고 사유(reason)를 요구하므로, 시험을 지우려면 그 사실을
# 명시적으로 적어야 한다.
#
# 입력 : $1 = 명부 경로 (기본 docs/sot/ci-required-manifest.yaml)
#        PYTEST_PROJECT = 프로젝트 루트 (기본 humansearch)
# 출력 : PASS:/FAIL: 줄과 마지막 줄 `CHECKED: <대조 항목 수>`
# exit : 0 = 기준선 이상 | 1 = 기준선 미달 | 2 = 스캔 무효(기준선 없음/뜻없음/측정 불가)
#
# 한계 ①(V2 G8, 2026-08-27): 이 검사는 **개수만** 본다. 시험 전량을 같은 수의 더미로
#   갈아치우면 통과한다. AC9 의 문언("줄면 실패") 안이지만, hs-gates 의 `collected<1`
#   을 보완한다는 취지에는 못 미친다는 것을 여기 적어 둔다. 내용까지 보려면 별도
#   장치(예: 시험 이름 집합의 감소 검사)가 필요하며 이 작업의 범위가 아니다.
# 한계 ②: 케이스 수는 pytest 수집이 가능할 때만 잰다. uv 환경을 못 만들면 통과가 아니라
#   무효다 — 재지 못한 것을 "줄지 않았다"로 세지 않는다 (P3 3상태).
set -uo pipefail

MANIFEST="${1:-docs/sot/ci-required-manifest.yaml}"
REPO=$(git rev-parse --show-toplevel 2>/dev/null) || REPO="$PWD"
PROJECT="${PYTEST_PROJECT:-}"
if [ -z "$PROJECT" ]; then
  PROJECT="$REPO/humansearch"
fi

if [ ! -f "$MANIFEST" ]; then
  echo "NOT_RUN: 명부가 없다 — $MANIFEST (fail-closed)"
  echo "CHECKED: 0"
  exit 2
fi

read_baseline() {
  ruby -rpsych -e '
    m = Psych.safe_load(File.read(ARGV[0]))
    b = m.is_a?(Hash) ? m["pytest_baseline"] : nil
    if b.is_a?(Hash) && b["files"].is_a?(Integer) && b["cases"].is_a?(Integer)
      print("#{b["files"]} #{b["cases"]}")
    else
      print("")
    end
  ' "$1" 2>/dev/null
}

baseline=$(read_baseline "$MANIFEST")
if [ -z "$baseline" ]; then
  echo "NOT_RUN: 명부에 pytest_baseline.files/.cases 가 정수로 없다 — 기준선 없이는 감소를 판정할 수 없다"
  echo "CHECKED: 0"
  exit 2
fi
base_files=${baseline%% *}
base_cases=${baseline##* }

if [ "$base_files" -lt 1 ] || [ "$base_cases" -lt 1 ]; then
  echo "NOT_RUN: 기준선이 files=${base_files} cases=${base_cases} — 0 이하 기준선은 모든 감소를 통과시킨다 (P20)"
  echo "CHECKED: 0"
  exit 2
fi

if [ ! -d "$PROJECT/tests" ]; then
  echo "NOT_RUN: 시험 디렉터리가 없다 — $PROJECT/tests (fail-closed)"
  echo "CHECKED: 0"
  exit 2
fi

checked=0
fail=0

# ── ① 시험 파일 수 ───────────────────────────────────────────────────────────
files=$(find "$PROJECT/tests" -type f -name 'test_*.py' 2>/dev/null | wc -l | tr -d ' ')
case "$files" in
  ''|*[!0-9]*)
    echo "NOT_RUN: 시험 파일 수를 세지 못했다 (스캔 무효)"
    echo "CHECKED: 0"
    exit 2
    ;;
esac
if [ "$files" -eq 0 ]; then
  echo "NOT_RUN: 시험 파일이 0개 — 대상 0개는 합격이 아니다 (P20)"
  echo "CHECKED: 0"
  exit 2
fi
checked=$((checked + 1))
if [ "$files" -lt "$base_files" ]; then
  echo "FAIL: 시험 파일 ${files}개 < 승인 기준선 ${base_files}개 — 시험이 사라졌다."
  echo "  줄이는 것이 옳다면 docs/sot/ci-required-manifest.yaml 의 pytest_baseline 을"
  echo "  사유와 함께 명시적으로 낮춰라. 말없이 줄어드는 것은 막는다."
  fail=1
else
  echo "PASS: 시험 파일 ${files}개 (기준선 ${base_files})"
fi

# 파일 수에서 이미 어긋났으면 수집을 돌릴 필요가 없다(비싼 uv sync 회피).
if [ "$fail" -ne 0 ]; then
  printf 'CHECKED: %d\n' "$checked"
  exit 1
fi

# ── ② 수집 케이스 수 ─────────────────────────────────────────────────────────
if ! command -v uv > /dev/null 2>&1; then
  echo "NOT_RUN: uv 를 찾을 수 없어 수집 케이스를 세지 못했다 — 재지 못한 것은 통과가 아니다 (P3)"
  printf 'CHECKED: %d\n' "$checked"
  exit 2
fi

collect_rc=0
collect_out=$(cd "$PROJECT" && uv run --frozen pytest --collect-only -q tests 2>&1) || collect_rc=$?
cases=$(printf '%s\n' "$collect_out" | awk '/::/ { n++ } END { print n + 0 }')
if [ "$collect_rc" -ne 0 ] && [ "$cases" -lt 1 ]; then
  printf '%s\n' "$collect_out" | tail -10
  echo "NOT_RUN: pytest 수집에 실패해 케이스를 세지 못했다 (exit=$collect_rc · 스캔 무효)"
  printf 'CHECKED: %d\n' "$checked"
  exit 2
fi

checked=$((checked + 1))
if [ "$cases" -lt "$base_cases" ]; then
  echo "FAIL: 수집 케이스 ${cases}건 < 승인 기준선 ${base_cases}건 — 시험 케이스가 사라졌다."
  echo "  줄이는 것이 옳다면 명부의 pytest_baseline.cases 를 사유와 함께 낮춰라."
  fail=1
else
  echo "PASS: 수집 케이스 ${cases}건 (기준선 ${base_cases})"
fi

# 늘어난 것은 막지 않는다. 다만 기준선이 낡으면 감소 탐지 폭이 그만큼 넓어지므로 알린다.
if [ "$files" -gt "$base_files" ] || [ "$cases" -gt "$base_cases" ]; then
  echo "NOTE: 실측(파일 ${files} · 케이스 ${cases})이 기준선(${base_files} · ${base_cases})보다 크다 —"
  echo "  기준선을 올려두면 그만큼 더 촘촘하게 감소를 잡는다."
fi

printf 'CHECKED: %d\n' "$checked"
exit "$fail"
