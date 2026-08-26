#!/usr/bin/env bash
# acceptance-pytest-baseline.sh — 제품 시험이 줄어들면 반드시 빨개지는가 (AC9).
#
# 겨냥하는 결함: acceptance-hs-gates.sh 는 `collected < 1` 만 본다. 그래서 시험을 1개만
# 남기고 27개를 지워도 게이트가 통과한다. "0건이 아니다"는 "줄지 않았다"가 아니다.
#
#   통과 — 손대지 않은 저장소는 승인 기준선을 만족한다
#   차단 — 기준선보다 파일이나 케이스가 적으면 불합격 (기준선을 올리는 것과 판정상 동치)
#   무효 — 기준선 누락·0 이하·측정 불가는 통과가 아니라 exit 2 (P20)
set -uo pipefail

unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE GIT_OBJECT_DIRECTORY \
  GIT_ALTERNATE_OBJECT_DIRECTORIES GIT_COMMON_DIR GIT_PREFIX GIT_QUARANTINE_PATH

REPO=$(git rev-parse --show-toplevel 2>/dev/null) || {
  echo "NOT_RUN: git 저장소가 아니다"
  echo "CHECKED: 0"
  exit 2
}
cd "$REPO" || exit 2

CHECKER="$REPO/scripts/verify/check-pytest-baseline.sh"
MANIFEST="$REPO/docs/sot/ci-required-manifest.yaml"

if [ ! -f "$CHECKER" ]; then
  echo "FAIL: 검사기가 없다 — $CHECKER (fail-closed)"
  echo "CHECKED: 0"
  exit 2
fi
if [ ! -f "$MANIFEST" ]; then
  echo "FAIL: 명부가 없다 — $MANIFEST (fail-closed)"
  echo "CHECKED: 0"
  exit 2
fi

SNAPSHOT=$(git status --porcelain)
TMP=$(mktemp -d) || {
  echo "NOT_RUN: mktemp 실패"
  echo "CHECKED: 0"
  exit 2
}
case "$TMP" in
  /tmp/*|/private/tmp/*|/var/folders/*|/private/var/folders/*) ;;
  *) echo "NOT_RUN: 안전하지 않은 임시 경로 — $TMP"; echo "CHECKED: 0"; exit 2 ;;
esac
trap 'ruby -rfileutils -e "FileUtils.remove_entry(ARGV[0]) if File.exist?(ARGV[0])" "$TMP"' EXIT

TOTAL=8
checked=0
failed=0

record() {
  local ok="$1"
  local label="$2"
  local detail="$3"
  checked=$((checked + 1))
  if [ "$ok" -eq 0 ]; then
    printf 'PASS: %s — %s\n' "$label" "$detail"
  else
    printf 'FAIL: %s — %s\n' "$label" "$detail"
    failed=1
  fi
}

# expect <설명> <기대 종료값> <명부> [PYTEST_PROJECT]
expect() {
  local label="$1"
  local wanted="$2"
  local manifest="$3"
  local project="${4:-}"
  local rc=0
  local out=""
  out=$(PYTEST_PROJECT="$project" bash "$CHECKER" "$manifest" 2>&1) || rc=$?
  if [ "$rc" -eq "$wanted" ]; then
    record 0 "$label" "exit=$rc"
  else
    record 1 "$label" "expected exit=$wanted actual=$rc / $(printf '%s' "$out" | tr '\n' ' ' | cut -c1-260)"
  fi
}

mutate_manifest() {
  local name="$1"
  local code="$2"
  local path
  path="$TMP/mf-$name.yaml"
  cp "$MANIFEST" "$path" || return 1
  ruby -e "$code" "$path" || return 1
  printf '%s' "$path"
}

# ── 통과 쪽: 손대지 않은 저장소 ──────────────────────────────────────────────
expect "실제 저장소 → 승인 기준선 만족" 0 "$MANIFEST"

# ── 차단 쪽: 기준선을 실측보다 높이면 = 시험이 줄어든 것과 판정상 동치 ───────
p=$(mutate_manifest files-raised '
require "psych"
path = ARGV[0]
m = Psych.safe_load(File.read(path))
m["pytest_baseline"]["files"] = m["pytest_baseline"]["files"] + 1
File.write(path, Psych.dump(m))
')
expect "시험 파일이 기준선보다 1개 적음 → 불합격" 1 "$p"

p=$(mutate_manifest cases-raised '
require "psych"
path = ARGV[0]
m = Psych.safe_load(File.read(path))
m["pytest_baseline"]["cases"] = m["pytest_baseline"]["cases"] + 1
File.write(path, Psych.dump(m))
')
expect "수집 케이스가 기준선보다 1건 적음 → 불합격" 1 "$p"

# ── counter-AC: 시험 1개만 남겨 "0건 아님"을 만족시키는 우회 ─────────────────
tiny="$TMP/tiny-project"
mkdir -p "$tiny/tests" "$tiny/src"
printf 'def test_only_one():\n    assert True\n' > "$tiny/tests/test_only.py"
expect "시험 파일 1개만 남긴 프로젝트 → 불합격" 1 "$MANIFEST" "$tiny"

empty_tests="$TMP/no-tests"
mkdir -p "$empty_tests/tests" "$empty_tests/src"
expect "시험 파일 0개인 프로젝트 → 스캔 무효" 2 "$MANIFEST" "$empty_tests"

# ── fail-closed: 기준선 자체가 없거나 뜻이 없을 때 ──────────────────────────
p=$(mutate_manifest baseline-gone '
require "psych"
path = ARGV[0]
m = Psych.safe_load(File.read(path))
m.delete("pytest_baseline")
File.write(path, Psych.dump(m))
')
expect "기준선 항목 삭제 → 스캔 무효" 2 "$p"

p=$(mutate_manifest baseline-zero '
require "psych"
path = ARGV[0]
m = Psych.safe_load(File.read(path))
m["pytest_baseline"]["files"] = 0
m["pytest_baseline"]["cases"] = 0
File.write(path, Psych.dump(m))
')
expect "기준선을 0 으로 낮춤 → 스캔 무효" 2 "$p"

# ── 원본 불변 ────────────────────────────────────────────────────────────────
current=$(git status --porcelain)
if [ "$current" = "$SNAPSHOT" ]; then
  record 0 "원본 저장소 상태 불변" "before/after 동일"
else
  record 1 "원본 저장소 상태 불변" "변경 발생"
fi

printf 'CHECKED: %d\n' "$checked"
if [ "$checked" -ne "$TOTAL" ]; then
  printf 'FAIL: 실행 사례 수 불일치 — expected=%d actual=%d\n' "$TOTAL" "$checked"
  failed=1
fi
if [ "$failed" -eq 0 ]; then
  echo "VERDICT: PASS"
else
  echo "VERDICT: FAIL"
fi
exit "$failed"
