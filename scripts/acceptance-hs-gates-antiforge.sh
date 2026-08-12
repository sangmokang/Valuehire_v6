#!/usr/bin/env bash
# 계약: docs/engineering/humansearch-g2-gates-goal-2026-08-12.md §6 (V1 Codex 결함 2건 봉쇄)
# 결함1[높음]: 시험 코드가 atexit 로 spy 증거 파일을 종료 직전 덮어써 "collected 999·실제 import"를 위조(P17).
# 결함2[높음]: CI 의 G2 스텝에 `if: ${{ false }}` 를 붙여 영구히 꺼도 배선 검사가 통과(P13).
# 이 스크립트는 위 두 우회가 막혔음을 실제 실행으로 증명한다. fail-closed.
set -euo pipefail

unset GIT_DIR GIT_INDEX_FILE GIT_OBJECT_DIRECTORY GIT_WORK_TREE GIT_COMMON_DIR
unset GIT_ALTERNATE_OBJECT_DIRECTORIES

REPO=$(git rev-parse --show-toplevel) || {
  echo "FAIL: repository root unavailable"
  exit 2
}
cd "$REPO"

GATES="scripts/acceptance-hs-gates.sh"
WF=".github/workflows/verify.yml"
for required in "$GATES" "$WF" "humansearch/pyproject.toml" "humansearch/uv.lock" \
  "humansearch/.python-version" "humansearch/src/humansearch/__init__.py" "humansearch/tests"; do
  [ -e "$required" ] || { echo "FAIL: required for antiforge missing: $required"; exit 2; }
done

SANDBOX=$(mktemp -d)
cleanup() { rm -rf -- "$SANDBOX"; }
trap cleanup EXIT
trap 'cleanup; trap - EXIT; exit 143' TERM
trap 'cleanup; trap - EXIT; exit 130' INT
trap 'cleanup; trap - EXIT; exit 129' HUP

pass=0
total=0

# --- 결함1: atexit 증거 위조가 무력화되는가 --------------------------------
total=$((total + 1))
FORGE="$SANDBOX/forge"
mkdir -p "$FORGE"
cp humansearch/pyproject.toml humansearch/uv.lock humansearch/.python-version "$FORGE/"
cp -R humansearch/src humansearch/tests "$FORGE/"
cat > "$FORGE/tests/test_package_boundary.py" <<'PY'
"""Forge spy evidence after pytest's session-finish hook has run."""

import atexit
import json
import os
from pathlib import Path


def _forge_after_session_finish() -> None:
    project = Path(__file__).resolve().parents[1]
    payload = {
        "module_file": str(project / "src" / "humansearch" / "__init__.py"),
        "collected": 999,
    }
    spy = os.environ.get("HS_SPY_OUT")
    if spy:
        Path(spy).write_text(json.dumps(payload), encoding="utf-8")


atexit.register(_forge_after_session_finish)


def test_tautology_without_importing_humansearch() -> None:
    assert True
PY

forge_rc=0
forge_out=$(HS_GATES_PROJECT="$FORGE" bash "$GATES" 2>&1) || forge_rc=$?
# 위조가 무력화됐다 = 게이트가 999 라는 거짓 숫자를 절대 보고하지 않는다.
# (게이트가 이 사본을 통과시키든 거부하든, 위조된 999·거짓 경로가 결과에 새면 안 된다.)
if printf '%s\n' "$forge_out" | grep -qE 'collected 999|COLLECTED: 999'; then
  echo "FAIL: atexit forgery inflated the collected count (exit=$forge_rc)"
  printf '%s\n' "$forge_out"
  exit 1
fi
pass=$((pass + 1))

# --- 결함2: CI 의 G2 스텝을 if:false 로 꺼도 탐지되는가 ----------------------
detect_if_disabled() {
  # G2 두 명령을 실행 줄에 담은 스텝 블록에 if: 가 붙어 있으면 DISABLED 를 출력한다.
  awk '
    /^[[:space:]]*-[[:space:]]*name:/ { inblk=1; hasif=0; hascmd=0 }
    inblk && /^[[:space:]]*if:/ { hasif=1 }
    inblk && /acceptance-hs-gates(\.sh|-mutations\.sh)/ { hascmd=1 }
    inblk && hascmd && hasif { print "DISABLED"; exit }
  ' "$1"
}

total=$((total + 1))
# 2a: 지금 진짜 verify.yml 은 살아 있어야 한다 (오탐 방지).
if [ -n "$(detect_if_disabled "$WF")" ]; then
  echo "FAIL: live verify.yml wrongly flagged as disabled"
  exit 1
fi
# 2b: if:false 를 심은 사본은 반드시 DISABLED 로 잡혀야 한다.
DWF="$SANDBOX/verify-disabled.yml"
awk '
  /^[[:space:]]*-[[:space:]]*name:.*G2/ { print; print "        if: ${{ false }}"; next }
  { print }
' "$WF" > "$DWF"
if [ "$(detect_if_disabled "$DWF")" != "DISABLED" ]; then
  echo "FAIL: disabled G2 CI step was not detected"
  exit 1
fi
pass=$((pass + 1))

# --- 실전 배선이 살아 있는가 (라이브 단언) ----------------------------------
total=$((total + 1))
missing=""
for cmd in "bash scripts/acceptance-hs-gates.sh" "bash scripts/acceptance-hs-gates-mutations.sh" \
  "bash scripts/acceptance-hs-gates-antiforge.sh"; do
  grep -qE "^[[:space:]]*${cmd}([[:space:]]|$)" "$WF" || missing="${missing} ${cmd}"
done
if [ -n "$missing" ]; then
  echo "FAIL: CI missing live G2 command(s):${missing}"
  exit 1
fi
pass=$((pass + 1))

echo "PASS: gates antiforge $pass/$total (evidence forgery + CI disable blocked)"
