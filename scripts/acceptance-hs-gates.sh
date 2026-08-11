#!/usr/bin/env bash
# 계약: docs/engineering/humansearch-g2-gates-goal-2026-08-12.md §4
# G2 게이트: HumanSearch 정적·단위 검사를 실제 실행하고 런타임 import와 수집 수를 증명한다.
# 순서는 단위시험(수집 판정) → ruff → mypy 다: "시험이 0건"은 다른 어떤 불합격보다 먼저,
# 그 이름 그대로 드러나야 한다 (P20 · 뮤테이션 계약의 마커 요구).
#
# P17(증거는 만든 자가 쓸 수 없다): 수집 수와 import 증명은 시험 프로세스가 쓴 파일을 믿지 않고
# 게이트가 직접 독립 프로세스로 측정한다. 시험이 atexit 로 spy 파일을 위조해도 판정에 못 샌다.
# exit 0 = 전부 합격 | 1 = 검사 불합격 | 2 = 검사 자체를 실행 못 함 (fail-closed)
set -euo pipefail

unset GIT_DIR GIT_INDEX_FILE GIT_OBJECT_DIRECTORY GIT_WORK_TREE GIT_COMMON_DIR
unset GIT_ALTERNATE_OBJECT_DIRECTORIES

REPO=$(git rev-parse --show-toplevel) || {
  echo "FAIL: repository root unavailable"
  exit 2
}

# HS_GATES_PROJECT 는 뮤테이션 suite가 고장 사본을 먹일 때만 재지정한다. 기본값이 실전 경로다.
PROJECT="${HS_GATES_PROJECT:-$REPO/humansearch}"

for required in "$PROJECT/pyproject.toml" "$PROJECT/uv.lock" "$PROJECT/.python-version" \
  "$PROJECT/src" "$PROJECT/tests"; do
  if [ ! -e "$required" ]; then
    echo "FAIL: project missing: $required"
    exit 1
  fi
done

src_files=$(find "$PROJECT/src" -name '*.py' -type f | wc -l | tr -d ' ')
if [ "$src_files" -lt 1 ]; then
  echo "FAIL: python files 0 in src"
  exit 1
fi

command -v uv > /dev/null 2>&1 || {
  echo "FAIL: uv unavailable"
  exit 2
}

sync_rc=0
sync_out=$(uv sync --locked --project "$PROJECT" 2>&1) || sync_rc=$?
if [ "$sync_rc" -ne 0 ]; then
  printf '%s\n' "$sync_out" | tail -5
  echo "FAIL: environment sync"
  exit 2
fi

# --- 수집 수: 게이트가 직접 센다 (시험이 못 부풀린다) -------------------------
# --collect-only -q 는 실제 노드 ID(`파일::테스트`)만 나열한다. 시험이 출력 문자열을 심어도
# 노드 ID 형식은 못 위조하고, spy 파일도 여기 관여하지 않는다.
collect_rc=0
collect_out=$(cd "$PROJECT" && uv run --no-sync pytest --collect-only -q tests 2>&1) || collect_rc=$?
# awk 로 노드 ID(`파일::테스트`) 줄을 센다. grep -c 는 0건일 때 종료값 1 → set -e 로 조용히
# 죽으므로 쓰지 않는다. awk 는 0건이어도 0 을 출력하고 정상 종료한다.
collected=$(printf '%s\n' "$collect_out" | awk '/::/ { n++ } END { print n + 0 }')
# 0건 수집을 다른 어떤 수집 오류보다 먼저, 그 이름으로 드러낸다 (P20). pytest 는 0건일 때
# 종료값 5 를 내므로, collected<1 을 collect_rc 판정보다 앞에 둔다.
if [ "$collected" -lt 1 ]; then
  printf '%s\n' "$collect_out" | tail -20
  echo "FAIL: collected 0 tests"
  exit 1
fi
if [ "$collect_rc" -ne 0 ]; then
  printf '%s\n' "$collect_out" | tail -20
  echo "FAIL: pytest collection error"
  exit 1
fi

# --- 단위시험 실제 실행: 통과/실패는 pytest 종료값이 정한다 (시험이 못 덮는다) -----
# spy 플러그인(hs_import_spy)을 실제 실행에 배선해 세션 수집 수·모듈 파일을 기록시킨다.
# 이 값은 판정의 근거가 아니라 변조 탐지기다 — 아래 독립 측정과 어긋나면 실패시킨다(P17).
SPY_PLUGIN_DIR="$REPO/scripts"
[ -e "$SPY_PLUGIN_DIR/hs_import_spy.py" ] || { echo "FAIL: import spy plugin missing"; exit 1; }
SPY_OUT=$(mktemp)
spy_cleanup() { rm -f -- "$SPY_OUT"; }
trap spy_cleanup EXIT
pytest_rc=0
pytest_out=$(cd "$PROJECT" && HS_SPY_OUT="$SPY_OUT" PYTHONPATH="$SPY_PLUGIN_DIR" \
  uv run --no-sync pytest -p hs_import_spy -q tests 2>&1) || pytest_rc=$?
if [ "$pytest_rc" -ne 0 ]; then
  printf '%s\n' "$pytest_out" | tail -20
  echo "FAIL: pytest exit $pytest_rc"
  exit 1
fi

# --- runtime import 증명: 게이트가 통제하는 독립 프로세스로 확인 (시험이 못 만진다) --
# 시험 프로세스 밖에서 모듈을 실제로 불러와 그 파일 경로를 얻는다. 프로젝트 src 밖(예: 동명
# site-packages)이면 거부한다. 시험의 atexit 위조는 이 프로세스에 닿지 못한다.
import_rc=0
module_file=$(cd "$PROJECT" && PYTHONPATH="$PROJECT/src" uv run --no-sync python -c \
  'import humansearch, sys; f = sys.modules["humansearch"].__file__ or ""; print(f)' 2>&1) || import_rc=$?
if [ "$import_rc" -ne 0 ] || [ -z "$module_file" ]; then
  printf '%s\n' "$module_file"
  echo "FAIL: independent runtime import failed"
  exit 1
fi
resolved_src=$(python3 -c 'import os,sys; print(os.path.realpath(sys.argv[1]))' "$PROJECT/src")
resolved_module=""
if [ -e "$module_file" ]; then
  resolved_module=$(python3 -c 'import os,sys; print(os.path.realpath(sys.argv[1]))' "$module_file")
fi
case "$resolved_module" in
  "$resolved_src"/*) ;;
  *)
    echo "FAIL: import proof outside project src: $module_file"
    exit 1
    ;;
esac

# --- 변조 탐지: spy 가 기록한 값이 독립 측정과 일치해야 한다 --------------------
# 시험이 atexit 로 spy 를 위조하면(예: collected=999) 독립 수집 수(collected)와 어긋나 여기서 잡힌다.
if [ ! -s "$SPY_OUT" ]; then
  echo "FAIL: import spy produced no evidence"
  exit 1
fi
spy_collected=$(python3 -c 'import json,sys; print(int(json.load(open(sys.argv[1])).get("collected", -1)))' "$SPY_OUT" 2>/dev/null) || {
  echo "FAIL: spy evidence unreadable"
  exit 2
}
spy_module=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1])).get("module_file") or "")' "$SPY_OUT" 2>/dev/null) || {
  echo "FAIL: spy evidence unreadable"
  exit 2
}
if [ "$spy_collected" != "$collected" ]; then
  echo "FAIL: spy count [$spy_collected] disagrees with independent count [$collected] (tampering)"
  exit 1
fi
spy_resolved=""
if [ -n "$spy_module" ] && [ -e "$spy_module" ]; then
  spy_resolved=$(python3 -c 'import os,sys; print(os.path.realpath(sys.argv[1]))' "$spy_module")
fi
if [ "$spy_resolved" != "$resolved_module" ]; then
  echo "FAIL: spy module path disagrees with independent import (tampering)"
  exit 1
fi

# --- 정적 검사 ---------------------------------------------------------------
ruff_rc=0
ruff_out=$(uv run --project "$PROJECT" --no-sync ruff check "$PROJECT/src" "$PROJECT/tests" 2>&1) || ruff_rc=$?
if [ "$ruff_rc" -ne 0 ]; then
  printf '%s\n' "$ruff_out"
  echo "FAIL: ruff"
  exit 1
fi

mypy_rc=0
mypy_out=$(cd "$PROJECT" && uv run --no-sync mypy --strict src tests 2>&1) || mypy_rc=$?
if [ "$mypy_rc" -ne 0 ]; then
  printf '%s\n' "$mypy_out"
  echo "FAIL: mypy"
  exit 1
fi
mypy_files=$(printf '%s\n' "$mypy_out" | sed -n 's/.*no issues found in \([0-9][0-9]*\) source file.*/\1/p')
if [ -z "$mypy_files" ] || [ "$mypy_files" -lt 1 ]; then
  printf '%s\n' "$mypy_out"
  echo "FAIL: mypy checked 0 source files"
  exit 1
fi

py_files=$(find "$PROJECT/src" "$PROJECT/tests" -name '*.py' -type f | wc -l | tr -d ' ')
echo "PASS: ruff clean in $py_files python files"
echo "PASS: mypy strict clean in $mypy_files source files"
echo "PASS: pytest collected $collected and passed"
echo "PASS: runtime import proof $module_file"
echo "COLLECTED: $collected"
