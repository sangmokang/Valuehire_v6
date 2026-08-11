#!/usr/bin/env bash
# 계약: docs/engineering/humansearch-g2-gates-goal-2026-08-12.md §4
# G2 게이트: HumanSearch 정적·단위 검사를 실제 실행하고 런타임 import와 수집 수를 증명한다.
# 순서는 단위시험(수집 판정) → ruff → mypy 다: "시험이 0건"은 다른 어떤 불합격보다 먼저,
# 그 이름 그대로 드러나야 한다 (P20 · 뮤테이션 계약의 마커 요구).
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
SPY_PLUGIN_DIR="$REPO/scripts"

for required in "$PROJECT/pyproject.toml" "$PROJECT/uv.lock" "$PROJECT/.python-version" \
  "$PROJECT/src" "$PROJECT/tests" "$SPY_PLUGIN_DIR/hs_import_spy.py"; do
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

SPY_OUT=$(mktemp)
spy_cleanup() { rm -f -- "$SPY_OUT"; }
trap spy_cleanup EXIT

pytest_rc=0
pytest_out=$(cd "$PROJECT" && HS_SPY_OUT="$SPY_OUT" PYTHONPATH="$SPY_PLUGIN_DIR" \
  uv run --no-sync pytest -p hs_import_spy -q tests 2>&1) || pytest_rc=$?

if [ ! -s "$SPY_OUT" ]; then
  printf '%s\n' "$pytest_out"
  echo "FAIL: import spy produced no evidence"
  exit 1
fi

collected=$(python3 -c 'import json,sys; print(int(json.load(open(sys.argv[1])).get("collected", 0)))' "$SPY_OUT") || {
  echo "FAIL: spy evidence unreadable"
  exit 2
}
module_file=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1])).get("module_file") or "")' "$SPY_OUT") || {
  echo "FAIL: spy evidence unreadable"
  exit 2
}

if [ "$collected" -lt 1 ]; then
  printf '%s\n' "$pytest_out"
  echo "FAIL: collected 0 tests"
  exit 1
fi
if [ "$pytest_rc" -ne 0 ]; then
  printf '%s\n' "$pytest_out"
  echo "FAIL: pytest exit $pytest_rc"
  exit 1
fi

resolved_src=$(python3 -c 'import os,sys; print(os.path.realpath(sys.argv[1]))' "$PROJECT/src")
resolved_module=""
if [ -n "$module_file" ] && [ -e "$module_file" ]; then
  resolved_module=$(python3 -c 'import os,sys; print(os.path.realpath(sys.argv[1]))' "$module_file")
fi
case "$resolved_module" in
  "$resolved_src"/*) ;;
  *)
    echo "FAIL: import proof outside project src: ${module_file:-none}"
    exit 1
    ;;
esac

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
