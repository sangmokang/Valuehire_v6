#!/usr/bin/env bash
# acceptance-hs-0302.sh — 후보 식별키가 중복 없이 기록되는가 (HS-03.02 AC-1~4)
#
# 계약: docs/engineering/humansearch-hs-0302-candidate-identity-goal-2026-09-15.md
#   EARS : When 같은 (position_ref, channel, candidate_ref) 를 두 번(또는 두 연결이
#          동시에) 기록하면, then 행은 하나만 남아야 한다.
#   출력 : exit 0 = PASS | exit 1 = FAIL | exit 2 = NOT_RUN
#   stdout: 항목마다 PASS:/FAIL:/NOT_RUN: 을 전부 출력하고, 마지막 줄에 `CHECKED: <검사 수>`
#   불변식: 0건 검사는 통과가 아니다 (P20)
#
# 무엇을 막는가 / 막지 못하는가:
#   막는다   — 기록 시험 파일 삭제·축소, 기본키 충돌 판별을 지우고 모든 IntegrityError 를
set -uo pipefail

unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE GIT_OBJECT_DIRECTORY \
      GIT_ALTERNATE_OBJECT_DIRECTORIES GIT_COMMON_DIR GIT_PREFIX GIT_QUARANTINE_PATH

HS0302_NESTED="${HS0302_ACCEPTANCE_DEPTH:-0}"
export HS0302_ACCEPTANCE_DEPTH=$((HS0302_NESTED + 1))
SELF="$(cd "$(dirname "$0")" && pwd)/$(basename "$0")"

GREP=/usr/bin/grep
if [ ! -x "$GREP" ]; then
  echo "NOT_RUN: $GREP 없음 — PATH 의 grep 이 ugrep 으로 가려질 수 있어 절대경로만 쓴다"
  echo "CHECKED: 0"
  exit 2
fi
if ! printf 'alpha\n' | "$GREP" -q 'alpha'; then
  echo "NOT_RUN: grep 양성 자기검사 실패 — 판정기를 신뢰할 수 없다"
  echo "CHECKED: 0"
  exit 2
fi
if printf 'alpha\n' | "$GREP" -q 'beta'; then
  echo "NOT_RUN: grep 음성 자기검사 실패 — 판정기를 신뢰할 수 없다"
  echo "CHECKED: 0"
  exit 2
fi

REPO=$(git rev-parse --show-toplevel 2>/dev/null) || {
  echo "NOT_RUN: git 저장소가 아니다"
  echo "CHECKED: 0"
  exit 2
}
cd "$REPO" || { echo "NOT_RUN: 저장소 이동 실패"; echo "CHECKED: 0"; exit 2; }

SNAP0=$(git status --porcelain)

MODULE=humansearch/src/humansearch/candidate_identity.py
TESTS=humansearch/tests/test_hs_0302_candidate_identity.py
TESTS_R2=humansearch/tests/test_hs_0302_r2_hardening.py
TESTS_R3=humansearch/tests/test_hs_0302_r3_hardening.py
TESTS_R4=humansearch/tests/test_hs_0302_r4_db_boundary.py
TESTS_R5=humansearch/tests/test_hs_0302_r5_approved_root.py
TEST_FILES="tests/test_hs_0302_candidate_identity.py tests/test_hs_0302_r2_hardening.py tests/test_hs_0302_r3_hardening.py tests/test_hs_0302_r4_db_boundary.py tests/test_hs_0302_r5_approved_root.py"
PYTEST_EXTRA=""
SCHEMA=humansearch/src/humansearch/storage_schema.py
WORKFLOW=.github/workflows/verify.yml
SOT_ROSTER=docs/sot/verification-commands.md
ACCEPTANCE_RUN="bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-0302.sh"
REQUIRED_TESTS=scripts/verify/fixtures/hs-0302-required-tests.txt
WIRING_CHECKER=scripts/verify/check-hs-0302-ci-wiring.rb
BASE_SHA=7473ec8
MIN_TESTS=6
MIN_R2_TESTS=10
MIN_R3_TESTS=6
MIN_R4_TESTS=7
MIN_R5_TESTS=2
EXPECTED_REQUIRED_IDS=113

WORK=$(mktemp -d) || { echo "NOT_RUN: mktemp 실패"; echo "CHECKED: 0"; exit 2; }
trap 'rm -rf "$WORK"' EXIT

fail=0
checked=0
pass_item() { echo "PASS: $1"; checked=$((checked + 1)); }
fail_item() { echo "FAIL: $1"; fail=1; checked=$((checked + 1)); }
fail_closed_ok() {
  local log=$1 rc=$2 reason=$3 line trailing
  line=$("$GREP" -n '^NOT_RUN:' "$log" | head -1 | cut -d: -f1)
  [ -n "$line" ] || return 1
  trailing=$(tail -n "+$((line + 1))" "$log" | "$GREP" -cE '^(PASS|FAIL|NOT_RUN):')
  [ "$rc" -eq 2 ] || return 1
  [ "${trailing:-1}" -eq 0 ] || return 1
  "$GREP" -q "$reason" "$log" || return 1
  return 0
}

assert_fail_closed() {
  local log=$1 rc=$2 reason=$3 desc=$4
  if fail_closed_ok "$log" "$rc" "$reason"; then
    pass_item "$desc"
  else
    fail_item "$desc — fail-closed 기준 위반 (종료값 ${rc})"
    tail -12 "$log"
  fi
}

abort_not_run() { echo "NOT_RUN: $1"; echo "CHECKED: $checked"; exit 2; }

for required in "$MODULE" "$TESTS" "$TESTS_R2" "$TESTS_R3" "$TESTS_R4" "$TESTS_R5" "$WORKFLOW" "$SOT_ROSTER" \
                "$REQUIRED_TESTS" "$WIRING_CHECKER" "$SCHEMA"; do
  if [ ! -f "$required" ]; then
    echo "NOT_RUN: $required 없음 — 검사 대상이 성립하지 않는다"
    echo "CHECKED: 0"
    exit 2
  fi
done

# ── 탐지기 정의 (진짜/음성 대조군 양쪽에 같은 함수를 쓴다) ────────────────────
pk_guard_present() {
  local file=$1 ctx
  ctx=$("$GREP" -B2 'return "duplicate"' "$file" 2>/dev/null) || return 1
  printf '%s\n' "$ctx" > "$WORK/ctx.txt"
  "$GREP" -q 'sqlite_errorname' "$WORK/ctx.txt" || return 1
  "$GREP" -q '_PRIMARY_KEY_CONSTRAINT\|SQLITE_CONSTRAINT_PRIMARYKEY' "$WORK/ctx.txt" || return 1
  return 0
}

# ── 1. RED 시험 파일이 존재하고 test 함수가 충분한가 ─────────────────────────
test_count=$("$GREP" -c '^def test_' "$TESTS")
case $? in
  0|1) : ;;
  *) echo "NOT_RUN: 시험 함수 계수 중 grep 오류"; echo "CHECKED: 0"; exit 2 ;;
esac
count_tests() {
  local file=$1 n
  n=$("$GREP" -c '^def test_' "$file")
  case $? in
    0|1) printf '%s\n' "${n:-0}" ;;
    *) abort_not_run "시험 함수 계수 중 grep 오류 — $file" ;;
  esac
}
r2_count=$(count_tests "$TESTS_R2")
r3_count=$(count_tests "$TESTS_R3")
r4_count=$(count_tests "$TESTS_R4")
r5_count=$(count_tests "$TESTS_R5")
total_tests=$((test_count + r2_count + r3_count + r4_count + r5_count))
if [ "$test_count" -ge "$MIN_TESTS" ] && [ "$r2_count" -ge "$MIN_R2_TESTS" ] \
   && [ "$r3_count" -ge "$MIN_R3_TESTS" ] && [ "$r4_count" -ge "$MIN_R4_TESTS" ] \
   && [ "$r5_count" -ge "$MIN_R5_TESTS" ]; then
  pass_item "시험 함수 1차 ${test_count} · 2차 ${r2_count} · 3차 ${r3_count} · 4차 ${r4_count} · 5차 ${r5_count} = ${total_tests}개"
else
  fail_item "시험 함수 부족 — 1차 ${test_count}(>=${MIN_TESTS}) · 2차 ${r2_count}(>=${MIN_R2_TESTS}) · 3차 ${r3_count}(>=${MIN_R3_TESTS}) · 4차 ${r4_count}(>=${MIN_R4_TESTS}) · 5차 ${r5_count}(>=${MIN_R5_TESTS})"
fi

if "$GREP" -q 'ThreadPoolExecutor' "$TESTS" && "$GREP" -q 'threading.Barrier' "$TESTS"; then
  pass_item "AC-3 경쟁 시험이 ThreadPoolExecutor + Barrier 로 두 워커를 동시에 띄운다"
else
  fail_item "AC-3 경쟁 시험에 동시성 장치가 없다 — 순차 호출은 경쟁을 판정하지 못한다"
fi

# ── 2. 기본키 충돌만 duplicate 로 접는가 (양성) ──────────────────────────────
if pk_guard_present "$MODULE"; then
  pass_item "기본키 충돌만 duplicate 로 번역한다 (sqlite_errorname 비교 존재)"
else
  fail_item "IntegrityError 를 무조건 duplicate 로 접는다 — 다른 무결성 오류가 둔갑한다"
fi

# ── 3. 탐지기 음성 대조군: 가드를 지운 사본은 반드시 잡혀야 한다 ─────────────
sed 's/^\( *\)if exc.sqlite_errorname == _PRIMARY_KEY_CONSTRAINT:/\1if True:/' \
  "$MODULE" > "$WORK/module_no_guard.py"
if "$GREP" -q 'if True:' "$WORK/module_no_guard.py" && ! pk_guard_present "$WORK/module_no_guard.py"; then
  pass_item "가드 탐지기 음성 대조군 통과 — 가드를 지운 사본은 FAIL 로 잡힌다"
else
  fail_item "가드 탐지기가 가드 없는 사본도 통과시킨다 — 탐지기가 무의미하다"
fi

# ── 4-5. HMAC 직렬화와 제어문자 거부는 **실행해서** 판정한다 ────────────────
cat > "$WORK/hmac_probe.py" <<'PROBE'
"""candidate_key_hmac 의미 판정 — 저장소를 건드리지 않고 함수만 부른다."""

import hmac
from pathlib import Path

from humansearch.candidate_identity import (
    CandidateIdentityError,
    CandidateIdentityInput,
    candidate_key_hmac,
    record_candidate_identity,
)

KEY = bytes(range(32))
A = ("a", "saramin", "x\x1fjobkorea\x1fy")
B = ("a\x1fsaramin\x1fx", "jobkorea", "y")
NOWHERE = Path("/nonexistent-hs-0302/db/humansearch.sqlite3")
NOKEY = Path("/nonexistent-hs-0302/keys/hs-candidate.key")
GOOD_TIME = "2026-09-15T10:00:00Z"

results = []


def check(name, ok):
    results.append((name, bool(ok)))


def length_prefixed(position_ref, channel, candidate_ref):
    message = b"hs-candidate-key-v2"
    for field in (position_ref, channel, candidate_ref):
        raw = field.encode("utf-8")
        message += len(raw).to_bytes(4, "big") + raw
    return hmac.new(KEY, message, "sha256").hexdigest()


def separator_joined(position_ref, channel, candidate_ref):
    parts = [b"hs-candidate-key-v1", position_ref.encode(), channel.encode(), candidate_ref.encode()]
    return hmac.new(KEY, b"\x1f".join(parts), "sha256").hexdigest()


def refusal_reason(position_ref, channel, candidate_ref, observed_at=GOOD_TIME):
    record = CandidateIdentityInput(position_ref, channel, candidate_ref, observed_at)
    try:
        record_candidate_identity(NOWHERE, record, hmac_key_path=NOKEY, approved_root=NOWHERE.parent)
    except CandidateIdentityError as exc:
        return str(exc)
    return ""


check("probe-can-see-collisions", separator_joined(*A) == separator_joined(*B))
check("injected-pair-does-not-collide", candidate_key_hmac(KEY, *A) != candidate_key_hmac(KEY, *B))
for label, triple in (
    ("A", A),
    ("B", B),
    ("channel-only", ("POS-1", "jobkorea", "cand-1")),
    ("position-only", ("POS-2", "saramin", "cand-1")),
    ("candidate-only", ("POS-1", "saramin", "cand-2")),
):
    check(f"matches-length-prefixed-contract[{label}]", candidate_key_hmac(KEY, *triple) == length_prefixed(*triple))
check("channel-changes-key", candidate_key_hmac(KEY, "P", "saramin", "c") != candidate_key_hmac(KEY, "P", "jobkorea", "c"))
check("position-changes-key", candidate_key_hmac(KEY, "P1", "saramin", "c") != candidate_key_hmac(KEY, "P2", "saramin", "c"))
check("split-ambiguity-separated", candidate_key_hmac(KEY, "ab", "saramin", "c") != candidate_key_hmac(KEY, "a", "saramin", "bc"))

legal = refusal_reason("POS-1", "saramin", "cand-1")
check("legal-input-fails-on-missing-key", "control characters" not in legal and legal != "")
for name, triple in (
    ("unit-separator", ("POS-1", "saramin", "cand\x1f")),
    ("nul", ("POS-1", "saramin", "cand\x00")),
    ("delete", ("POS\x7f-1", "saramin", "cand-1")),
    ("c1-nel", ("POS-1", "saramin", "cand\x85")),
):
    check(f"control-char-refused[{name}]", "control characters" in refusal_reason(*triple))
check("calendar-impossible-time-refused", refusal_reason("POS-1", "saramin", "c", "2026-99-99T99:99:99+99:99") != "" and "control characters" not in refusal_reason("POS-1", "saramin", "c", "2026-99-99T99:99:99+99:99"))

bad = 0
for name, ok in results:
    print(("PROBE_OK: " if ok else "PROBE_BAD: ") + name)
    bad += 0 if ok else 1
raise SystemExit(1 if bad else 0)
PROBE

( cd humansearch && uv run python "$WORK/hmac_probe.py" ) > "$WORK/probe.log" 2>&1
probe_rc=$?
probe_ok=$("$GREP" -c '^PROBE_OK:' "$WORK/probe.log")
probe_bad=$("$GREP" -c '^PROBE_BAD:' "$WORK/probe.log")
if [ "$probe_rc" -eq 0 ] && [ "${probe_ok:-0}" -ge 10 ] && [ "${probe_bad:-0}" -eq 0 ]; then
  pass_item "HMAC 의미 probe — ${probe_ok}건 전부 OK (충돌 없음·길이 접두 계약 일치·제어문자 거부)"
else
  fail_item "HMAC 의미 probe — 종료값 ${probe_rc}, OK=${probe_ok:-0}, BAD=${probe_bad:-0}"
  "$GREP" '^PROBE_BAD:' "$WORK/probe.log" || tail -20 "$WORK/probe.log"
fi

if [ "${probe_ok:-0}" -ge 10 ]; then
  pass_item "HMAC 의미 probe 가 판정한 항목 ${probe_ok}건 (>= 10)"
else
  fail_item "HMAC 의미 probe 판정 ${probe_ok:-0}건 — 검사 대상이 사라졌다"
fi

# ── 6. #97 마이그레이션을 건드리지 않았는가 ─────────────────────────────────
if git cat-file -e "${BASE_SHA}^{commit}" 2>/dev/null; then
  git diff --unified=0 "$BASE_SHA" -- "$SCHEMA" > "$WORK/schema.diff"
  "$GREP" -E '^[+-][^+-]' "$WORK/schema.diff" > "$WORK/schema.changes"
  if diff -u <(printf '%s\n' '+    protected_root: Path' '+        protected_root=root,') \
            "$WORK/schema.changes" > "$WORK/schema-only-root.diff"; then
    pass_item "storage_schema.py 의 마이그레이션 불변 — 초기화 결과에 승인 root 두 줄만 추가"
  else
    fail_item "storage_schema.py 가 ${BASE_SHA} 대비 승인 root 두 줄 외에 변경됐다 — 마이그레이션 무변경 계약 위반"
    cat "$WORK/schema-only-root.diff"
  fi
else
  abort_not_run "기준 커밋 ${BASE_SHA} 를 찾을 수 없다 — 마이그레이션 동일성을 대조하지 못한 채로는 합격시키지 않는다"
fi

# ── 7. hs_candidates 를 우회하는 새 표가 src 에 없는가 ───────────────────────
"$GREP" -rniE '^[[:space:]]*create[[:space:]]+table' humansearch/src --include='*.py' \
  > "$WORK/create_table.txt"
rc=$?
if [ "$rc" -gt 1 ]; then
  abort_not_run "create table 스캔 중 grep 오류 (rc=$rc) — 우회 표 유무를 모른 채로는 합격시키지 않는다"
else
  stray=$("$GREP" -v "^${SCHEMA}:" "$WORK/create_table.txt" | "$GREP" -c . )
  if [ "${stray:-0}" -eq 0 ]; then
    pass_item "src 의 create table 은 storage_schema.py 안에만 있다 (우회 표 0개)"
  else
    fail_item "storage_schema.py 밖에서 create table ${stray}건 — hs_candidates 우회 표가 생겼다"
  fi
fi

# ── 8. 시험을 실제로 돌린다 (문자열 검사만으로는 동작을 판정하지 못한다) ─────
if [ "$HS0302_NESTED" -ge 1 ]; then
  echo "NOT_RUN: 중첩 실행(depth=${HS0302_NESTED}) — 시험 단계를 돌리면 무한 재귀가 된다"
  echo "CHECKED: $checked"
  exit 2
fi
collect_log="$WORK/collect.log"
( cd humansearch && uv run pytest $TEST_FILES $PYTEST_EXTRA --collect-only -q ) \
  > "$collect_log" 2>&1
collect_rc=$?
if ! tail -5 "$collect_log" | "$GREP" -E 'tests? collected' > "$WORK/collect_summary.txt"; then
  : > "$WORK/collect_summary.txt"
fi
collect_line=$(tail -1 "$WORK/collect_summary.txt")
if [ "$collect_rc" -ne 0 ] || [ -z "$collect_line" ]; then
  abort_not_run "pytest 수집 실패 — 무엇을 돌려야 하는지 모른 채로는 합격시키지 않는다"
fi
printf '%s\n' "$collect_line" > "$WORK/collect_line.txt"
if ! "$GREP" -qE '^[0-9]+ tests? collected in ' "$WORK/collect_line.txt"; then
  fail_item "pytest 수집 요약이 단순 수집이 아니다 — '${collect_line}' (필터·deselect 흔적)"
  selected=0
else
  selected=$("$GREP" -oE '^[0-9]+' "$WORK/collect_line.txt")
  if [ "${selected:-0}" -ge "$total_tests" ]; then
    pass_item "pytest 수집 ${selected}건 — 필터 없이 전부 선택됐다 (함수 ${total_tests}개 이상)"
  else
    fail_item "pytest 수집 ${selected:-0}건 — 함수 ${total_tests}개보다 적다 (시험이 사라졌다)"
  fi
fi

pytest_log="$WORK/pytest.log"
( cd humansearch && uv run pytest $TEST_FILES $PYTEST_EXTRA -q ) > "$pytest_log" 2>&1
pytest_rc=$?
if ! tail -5 "$pytest_log" | "$GREP" -E 'passed|failed|error|no tests ran' > "$WORK/run_summary.txt"; then
  : > "$WORK/run_summary.txt"
fi
run_line=$(tail -1 "$WORK/run_summary.txt")
printf '%s\n' "$run_line" > "$WORK/run_line.txt"
if [ "$pytest_rc" -eq 0 ] && [ "${selected:-0}" -gt 0 ] \
   && "$GREP" -qE "^${selected} passed in " "$WORK/run_line.txt"; then
  pass_item "pytest 실제 실행 — ${selected} passed, 수집 건수와 정확히 일치, 종료값 0"
else
  fail_item "pytest 실제 실행 — 종료값 ${pytest_rc}, 수집 ${selected:-0}, 요약 '${run_line}'"
  tail -20 "$pytest_log"
fi

# ── fail-closed 자기 검사 ──────────────────────────────────────────────────
sed 's/^BASE_SHA=.*/BASE_SHA=0000000000000000000000000000000000000000/' "$SELF" \
  > "$WORK/failclosed_probe.sh"
HS0302_ACCEPTANCE_DEPTH=9 bash "$WORK/failclosed_probe.sh" > "$WORK/failclosed.log" 2>&1
assert_fail_closed "$WORK/failclosed.log" "$?" '기준 커밋' \
  "fail-closed 자기 검사 ① 기준 SHA 를 지운 사본이 그 자리에서 끝난다"

cat > "$WORK/fake-grep" <<'FAKEGREP'
for arg in "$@"; do
  case "$arg" in
    *create*table*) exit 2 ;;
  esac
done
exec /usr/bin/grep "$@"
FAKEGREP
chmod +x "$WORK/fake-grep"
sed "s|^GREP=/usr/bin/grep\$|GREP=$WORK/fake-grep|" "$SELF" > "$WORK/failclosed_scan_probe.sh"
HS0302_ACCEPTANCE_DEPTH=9 bash "$WORK/failclosed_scan_probe.sh" > "$WORK/failclosed_scan.log" 2>&1
assert_fail_closed "$WORK/failclosed_scan.log" "$?" 'create table 스캔' \
  "fail-closed 자기 검사 ② 우회 표 스캔이 깨진 사본이 그 자리에서 끝난다"

# ── 건너뛰기 보조 부재 · 즉시 종료 · 차단 분리 (정적) ──────────────────────
N_SKIP=$(printf 'skip%s' '_item')
N_EXIT=$(printf 'exit%s' ' 2')
N_DEPTH=$(printf 'HS0302_ACCEPTANCE%s' '_DEPTH')
N_ROUTED=$(printf 'abort_not_run "%s' '중첩')
guard_shape=0
"$GREP" -qF "$N_SKIP" "$SELF" && guard_shape=1
"$GREP" -qF "$N_EXIT" "$SELF" || guard_shape=1
"$GREP" -qF "$N_DEPTH" "$SELF" || guard_shape=1
"$GREP" -qF "$N_ROUTED" "$SELF" && guard_shape=1
if [ "$guard_shape" -eq 0 ]; then
  pass_item "건너뛰기 보조 없음 · 즉시 종료 경로 있음 · 중첩 차단이 fail-closed 보조와 분리돼 있다"
else
  fail_item "건너뛰기 보조가 있거나, 즉시 종료·중첩 차단이 없거나, 차단이 보조를 거친다"
fi

needle_ok=1
for needle in "$N_SKIP" "$N_EXIT" "$N_DEPTH" "$N_ROUTED"; do
  [ -n "$needle" ] || needle_ok=0
done
"$GREP" -qF "$N_DEPTH" "$SELF" || needle_ok=0
printf '%s\n' "$N_SKIP" > "$WORK/needle_probe.txt"
"$GREP" -qF "$N_SKIP" "$WORK/needle_probe.txt" || needle_ok=0
if [ "$needle_ok" -eq 1 ]; then
  pass_item "탐지기 needle 조립 검증 — 4개 모두 비어 있지 않고 양성 대조군에서 잡힌다"
else
  fail_item "탐지기 needle 조립이 깨졌다 — 위 정적 검사가 무의미해진다"
fi

# ── fail-closed 판정기 자신의 음성 대조군 ──────────────────────────────────
sed -e 's/^BASE_SHA=.*/BASE_SHA=0000000000000000000000000000000000000000/' \
    -e 's|^abort_not_run() .*|abort_not_run() { echo "NOT_RUN: $1"; checked=$((checked + 1)); }|' \
    "$SELF" > "$WORK/failopen_control.sh"
HS0302_ACCEPTANCE_DEPTH=9 bash "$WORK/failopen_control.sh" > "$WORK/failopen.log" 2>&1
fo_rc=$?
if fail_closed_ok "$WORK/failopen.log" "$fo_rc" '기준 커밋'; then
  fail_item "fail-closed 판정기가 fail-open 사본도 통과시킨다 — 판정기가 무의미하다"
  tail -12 "$WORK/failopen.log"
else
  pass_item "fail-closed 판정기 음성 대조군 — 같은 기준으로 fail-open 사본은 불합격한다"
fi

# ── CI 배선 (정본 53행) ────────────────────────────────────────────────────
if "$GREP" -qF "$ACCEPTANCE_RUN" "$WORKFLOW"; then
  pass_item "CI 고정 목록에 전용 스텝이 있다 ($WORKFLOW)"
else
  fail_item "CI 고정 목록에 이 인수 검사가 없다 — 로컬에만 있는 검사는 없는 것으로 친다"
fi

if "$GREP" -q 'acceptance-hs-0302.sh' "$SOT_ROSTER"; then
  pass_item "검증 명부에 자기 줄이 있다 ($SOT_ROSTER)"
else
  fail_item "검증 명부에 이 인수 검사가 없다 (정본 53행 위반)"
fi

if [ ! -f "$WIRING_CHECKER" ]; then
  abort_not_run "배선 검사기가 없다 — $WIRING_CHECKER"
fi
ruby "$WIRING_CHECKER" "$WORKFLOW" > "$WORK/wiring.log" 2>&1
wiring_rc=$?
if [ "$wiring_rc" -eq 0 ] && "$GREP" -q '^WIRING_OK:' "$WORK/wiring.log"; then
  pass_item "CI 스텝 run 이 정확한 단일 명령이다 (YAML 파싱·셸 제어 연산자 0개)"
else
  fail_item "CI 스텝 run 계약 위반 (종료값 ${wiring_rc})"
  cat "$WORK/wiring.log"
fi

MUT_TAIL="$(printf '|%s' '|') $(printf 'tr%s' 'ue')"
sed "s%^\( *\)run: ${ACCEPTANCE_RUN}\$%\1run: ${ACCEPTANCE_RUN} ${MUT_TAIL}%" "$WORKFLOW" \
  > "$WORK/workflow_mutated.yml"
if ! "$GREP" -qF "${ACCEPTANCE_RUN} ${MUT_TAIL}" "$WORK/workflow_mutated.yml"; then
  fail_item "배선 탐지기 음성 대조군을 만들지 못했다 — run 줄 형태가 예상과 다르다"
else
  ruby "$WIRING_CHECKER" "$WORK/workflow_mutated.yml" > "$WORK/wiring_mutated.log" 2>&1
  if [ $? -eq 1 ] && "$GREP" -q '^WIRING_BAD:' "$WORK/wiring_mutated.log"; then
    pass_item "배선 탐지기 음성 대조군 — run 에 실패를 삼키는 꼬리를 붙인 사본은 불합격한다"
  else
    fail_item "배선 탐지기가 실패를 삼키는 사본도 통과시킨다 — 탐지기가 무의미하다"
    cat "$WORK/wiring_mutated.log"
  fi
fi

# ── 필수 시험 명부 대조 ────────────────────────────────────────────────────
"$GREP" -vE '^[[:space:]]*(#|$)' "$REQUIRED_TESTS" | LC_ALL=C sort > "$WORK/required_ids.txt"
required_n=$("$GREP" -c . "$WORK/required_ids.txt")
if [ "${required_n:-0}" -ne "$EXPECTED_REQUIRED_IDS" ]; then
  fail_item "필수 시험 명부가 ${required_n:-0}건 — 기대값 ${EXPECTED_REQUIRED_IDS}건과 다르다 (명부와 상수를 함께 올렸는가)"
fi
"$GREP" '::' "$collect_log" | LC_ALL=C sort > "$WORK/actual_ids.txt"
comm -23 "$WORK/required_ids.txt" "$WORK/actual_ids.txt" > "$WORK/ids_missing.txt"
comm -13 "$WORK/required_ids.txt" "$WORK/actual_ids.txt" > "$WORK/ids_extra.txt"
ids_missing=$("$GREP" -c . "$WORK/ids_missing.txt")
ids_extra=$("$GREP" -c . "$WORK/ids_extra.txt")
if [ "${ids_missing:-1}" -eq 0 ] && [ "${ids_extra:-1}" -eq 0 ]; then
  pass_item "필수 시험 명부 ${required_n}건과 수집 결과가 정확히 같다 (누락 0 · 추가 0)"
else
  fail_item "필수 시험 명부 불일치 — 누락 ${ids_missing}건 · 명부 밖 추가 ${ids_extra}건"
  head -5 "$WORK/ids_missing.txt"
  head -5 "$WORK/ids_extra.txt"
fi

# ── 시험이 humansearch/ 밖으로 손을 뻗지 않는가 ────────────────────────────
OUT_OF_TREE_RE=$(printf 'parents\\[2\\]|%s/|\\.github|docs/sot' 'scripts')
"$GREP" -nE "$OUT_OF_TREE_RE" "$TESTS" "$TESTS_R2" "$TESTS_R3" "$TESTS_R4" "$TESTS_R5" \
  > "$WORK/out_of_tree.txt"
rc=$?
if [ "$rc" -gt 1 ]; then
  abort_not_run "시험의 저장소 밖 참조 스캔 중 grep 오류 (rc=$rc)"
fi
out_of_tree=$("$GREP" -c . "$WORK/out_of_tree.txt")
if [ "${out_of_tree:-0}" -eq 0 ]; then
  pass_item "HS-03.02 시험이 humansearch/ 밖 파일을 읽지 않는다 (G2 격리 사본 안전)"
else
  fail_item "시험이 humansearch/ 밖 경로를 참조한다 ${out_of_tree}건 — G2 게이트가 push 를 막는다"
  cat "$WORK/out_of_tree.txt"
fi

# ── 자기 오염 감지 ─────────────────────────────────────────────────────────
SNAP1=$(git status --porcelain)
if [ "$SNAP0" = "$SNAP1" ]; then
  pass_item "검사 전후 저장소 상태 동일 — 검증기가 대상을 오염시키지 않았다"
else
  fail_item "검사가 저장소 상태를 바꿨다 — 이 판정은 무효다"
fi

echo "CHECKED: $checked"
if [ "$checked" -lt 1 ]; then
  echo "FAIL: 검사 대상 0개는 합격이 아니다"
  exit 1
fi
[ "$fail" -eq 0 ] && exit 0
exit 1
