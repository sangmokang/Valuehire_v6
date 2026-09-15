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
#              duplicate 로 접는 것, HMAC 직렬화에서 필드를 빼거나 길이 접두를 구분자
#              결합으로 되돌리는 것, 제어문자 거부를 지우는 것, #97 마이그레이션 수정,
#              hs_candidates 를 우회하는 새 표 추가, 시험 미실행, 그리고 이 스크립트 자신이
#              필수 비교·스캔을 못 한 채 초록이 되는 것.
#   막지 못함 — 시험 본문이 맞는 것을 보는지(그것은 pytest 와 변이 검증의 몫),
#              런타임 동시성 자체(그것은 test_ac3 가 20회 실제 경쟁으로 판정한다).
#
# fail-closed (2026-09-15, Codex V1 결함 4): 필수 비교나 스캔이 불가능하면 건너뛰고
#   통과하지 않는다. 즉시 NOT_RUN 을 찍고 exit 2 로 끝내며, 그 항목은 CHECKED 에 넣지
#   않는다. 종료값 0 은 "모든 필수 검사를 실제로 했고 전부 통과했다"만 의미해야 한다.
#
# 자기 검사: 탐지기(가드 탐지·HMAC 입력 탐지)는 반드시 "잡는다"와 "안 잡는다"를
#   한 쌍으로 증명한다. 진짜 파일에서 통과만 확인하면 탐지기가 항상 통과해도 모른다.
#   음성 대조군은 저장소 밖 임시 사본에만 만든다 — 검증기가 대상을 오염시키면 판정이 무효다.
set -uo pipefail

# git 훅은 GIT_DIR·GIT_INDEX_FILE 등을 자식으로 export 한다. 상속을 끊지 않으면
# 임시 디렉터리로 cd 해도 git 이 실제 저장소에 붙는다(acceptance-hs-a3.sh 2026-08-09 사고).
unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE GIT_OBJECT_DIRECTORY \
      GIT_ALTERNATE_OBJECT_DIRECTORIES GIT_COMMON_DIR GIT_PREFIX GIT_QUARANTINE_PATH

# 재귀 차단 (2026-09-15 실측). 이 스크립트의 pytest 단계는 자기 자신을 호출하는 시험을
# 돌린다. fail-closed 가 퇴화하면 그 시험이 다시 이 스크립트를 부르고, 그 안에서 또 시험이
# 돌아 프로세스가 기하급수로 늘어난다(변이 검증 중 수백 개까지 늘어 강제 종료했다).
# 깊이를 표시해 중첩 실행에서는 시험 단계를 아예 돌리지 않는다.
HS0302_NESTED="${HS0302_ACCEPTANCE_DEPTH:-0}"
export HS0302_ACCEPTANCE_DEPTH=$((HS0302_NESTED + 1))
SELF="$(cd "$(dirname "$0")" && pwd)/$(basename "$0")"

GREP=/usr/bin/grep
if [ ! -x "$GREP" ]; then
  echo "NOT_RUN: $GREP 없음 — PATH 의 grep 이 ugrep 으로 가려질 수 있어 절대경로만 쓴다"
  echo "CHECKED: 0"
  exit 2
fi
# grep 자기검사 — 양성 1건과 음성 1건이 모두 기대대로여야 판정을 시작한다.
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
TESTS_PROBE=humansearch/tests/test_hs_0302_acceptance_probe.py
# 인수 실행이 돌리는 시험 전부. 필터는 두지 않는다 — 필터를 두면 필수 음성 대조군이
# 인수 실행 안에서 돌지 않는다(Codex V1 2차 F0302-4 잔여).
TEST_FILES="tests/test_hs_0302_candidate_identity.py tests/test_hs_0302_r2_hardening.py tests/test_hs_0302_r3_hardening.py tests/test_hs_0302_acceptance_probe.py"
PYTEST_EXTRA=""
SCHEMA=humansearch/src/humansearch/storage_schema.py
BASE_SHA=7473ec8
MIN_TESTS=6
MIN_R2_TESTS=10
MIN_R3_TESTS=8
MIN_PROBE_TESTS=5

WORK=$(mktemp -d) || { echo "NOT_RUN: mktemp 실패"; echo "CHECKED: 0"; exit 2; }
trap 'rm -rf "$WORK"' EXIT

fail=0
checked=0
pass_item() { echo "PASS: $1"; checked=$((checked + 1)); }
fail_item() { echo "FAIL: $1"; fail=1; checked=$((checked + 1)); }
# fail-closed 자기 검사 판정. 종료값만 보면 부족하다 — 건너뛴 뒤 다른 경로로 2 가
# 나와도 통과한다. NOT_RUN 뒤에 판정(PASS)이 한 줄이라도 이어지면 그것이 fail-open 이다.
# abort_not_run 을 쓰지 않는다: fail-closed 를 되돌리는 변이가 그 보조를 건드리므로.
assert_fail_closed() {
  local log=$1 rc=$2 reason=$3 desc=$4 line trailing
  line=$("$GREP" -n '^NOT_RUN:' "$log" | head -1 | cut -d: -f1)
  if [ -z "$line" ]; then
    fail_item "$desc — NOT_RUN 줄이 없다 (종료값 ${rc})"
    tail -12 "$log"
    return
  fi
  trailing=$(tail -n "+$((line + 1))" "$log" | "$GREP" -c '^PASS:')
  if [ "$rc" -eq 2 ] && [ "${trailing:-1}" -eq 0 ] && "$GREP" -q "$reason" "$log"; then
    pass_item "$desc"
  else
    fail_item "$desc — 종료값 ${rc}, NOT_RUN 줄 ${line}, 뒤따른 PASS ${trailing}건"
    tail -12 "$log"
  fi
}

# 필수 검사를 할 수 없으면 건수만 늘리고 통과시키지 않는다 — 그 자리에서 끝낸다.
abort_not_run() { echo "NOT_RUN: $1"; echo "CHECKED: $checked"; exit 2; }

for required in "$MODULE" "$TESTS" "$TESTS_R2" "$TESTS_R3" "$TESTS_PROBE" "$SCHEMA"; do
  if [ ! -f "$required" ]; then
    echo "NOT_RUN: $required 없음 — 검사 대상이 성립하지 않는다"
    echo "CHECKED: 0"
    exit 2
  fi
done

# ── 탐지기 정의 (진짜/음성 대조군 양쪽에 같은 함수를 쓴다) ────────────────────
# 기본키 충돌만 duplicate 로 접는가: `return "duplicate"` 바로 앞 2줄 안에
# sqlite_errorname 과 SQLITE_CONSTRAINT_PRIMARYKEY 비교가 있어야 한다.
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
probe_count=$(count_tests "$TESTS_PROBE")
total_tests=$((test_count + r2_count + r3_count + probe_count))
if [ "$test_count" -ge "$MIN_TESTS" ] && [ "$r2_count" -ge "$MIN_R2_TESTS" ] \
   && [ "$r3_count" -ge "$MIN_R3_TESTS" ] && [ "$probe_count" -ge "$MIN_PROBE_TESTS" ]; then
  pass_item "시험 함수 1차 ${test_count} · 2차 ${r2_count} · 3차 ${r3_count} · probe ${probe_count} = ${total_tests}개"
else
  fail_item "시험 함수 부족 — 1차 ${test_count}(>=${MIN_TESTS}) · 2차 ${r2_count}(>=${MIN_R2_TESTS}) · 3차 ${r3_count}(>=${MIN_R3_TESTS}) · probe ${probe_count}(>=${MIN_PROBE_TESTS})"
fi

# 두 연결 경쟁 시험이 실제로 스레드 2개를 쓰는가(같은 연결 재사용이면 AC-3 가 무효다)
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
# 문자열 탐지기는 구현을 같은 뜻으로 다시 써도 불합격시킨다(거짓 빨강). 더 나쁜 건
# 반대다 — 모양만 맞추면 통과한다. Codex V1 이 뚫은 것은 모양이 아니라 의미였으므로
# 여기서는 함수를 직접 불러 충돌 여부를 본다. probe 는 자기 음성 대조군을 품는다:
# 옛 구분자 결합 방식으로 계산하면 같은 쌍이 **반드시 충돌**해야 하고, 충돌이 안 보이면
# probe 자신이 고장 난 것이므로 BAD 로 보고한다.
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
        record_candidate_identity(NOWHERE, record, hmac_key_path=NOKEY)
    except CandidateIdentityError as exc:
        return str(exc)
    return ""


# probe 자기 음성 대조군 — 옛 방식에서는 이 쌍이 반드시 충돌해야 한다.
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

# 제어문자 거부가 파일시스템에 닿기 전에 먼저 걸리는가.
# 양성 대조군: 합법 입력은 "키 없음"이라는 **다른** 이유로 거부돼야 한다.
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

# probe 가 "아무것도 판정하지 않고 초록"이 되는 경우를 막는다 — 0건은 통과가 아니다.
if [ "${probe_ok:-0}" -ge 10 ]; then
  pass_item "HMAC 의미 probe 가 판정한 항목 ${probe_ok}건 (>= 10)"
else
  fail_item "HMAC 의미 probe 판정 ${probe_ok:-0}건 — 검사 대상이 사라졌다"
fi

# ── 6. #97 마이그레이션을 건드리지 않았는가 ─────────────────────────────────
if git cat-file -e "${BASE_SHA}^{commit}" 2>/dev/null; then
  schema_diff=$(git diff "$BASE_SHA" -- "$SCHEMA" | wc -l | tr -d ' ')
  if [ "$schema_diff" = "0" ]; then
    pass_item "storage_schema.py 가 ${BASE_SHA}(#97) 과 동일하다 (diff 0줄)"
  else
    fail_item "storage_schema.py 가 ${BASE_SHA} 대비 ${schema_diff}줄 다르다 — 이 WU 는 마이그레이션을 바꾸지 않는다"
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
# 중첩 차단은 abort_not_run 을 쓰지 않는다. fail-closed 를 되돌리는 변이가 그 보조를
# 건드리면 차단까지 같이 죽기 때문이다(2026-09-15 실측: 프로세스 1,493개). 직접 끝낸다.
if [ "$HS0302_NESTED" -ge 1 ]; then
  echo "NOT_RUN: 중첩 실행(depth=${HS0302_NESTED}) — 시험 단계를 돌리면 무한 재귀가 된다"
  echo "CHECKED: $checked"
  exit 2
fi
# 무엇을 돌려야 하는지를 먼저 수집해 둔다. "통과 수 >= 함수 수" 같은 하한은 매개변수
# 확장 때문에 부풀어, 필수 시험이 빠져도 성립한다(Codex V1 2차). 수집 건수와 **정확히**
# 같아야 하고 deselected·skipped·기대실패 표시가 하나라도 붙으면 불합격이다.
# 판정은 요약 줄이 정확히 `<수집건수> passed in ` 모양인지로 본다 — 다른 표시가
# 하나라도 붙으면 그 모양이 깨진다.
collect_log="$WORK/collect.log"
( cd humansearch && uv run pytest $TEST_FILES $PYTEST_EXTRA --collect-only -q ) \
  > "$collect_log" 2>&1
collect_rc=$?
if ! tail -5 "$collect_log" | "$GREP" -E 'tests? collected' > "$WORK/collect_summary.txt"; then
  # 매치 없음(rc 1)과 리다이렉션 실패(rc 1)가 겹친다. 어느 쪽이든 판정 근거가 없으므로
  # 빈 파일로 두고 아래에서 abort_not_run 이 받는다 — 조용히 넘기지 않는다.
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
# 필수 비교를 못 하게 만든 자기 사본이 "건너뛰고 통과"하지 않는지 직접 본다. 종료값만
# 보면 부족하다 — 건너뛴 뒤 다른 경로로 2 가 나와도 통과한다. NOT_RUN 뒤에 판정(PASS)이
# 한 줄이라도 이어지면 그것이 fail-open 이다. 사본은 depth 9 로 띄워 시험 단계에 닿지
# 못하게 한다(재귀 방지).
sed 's/^BASE_SHA=.*/BASE_SHA=0000000000000000000000000000000000000000/' "$SELF" \
  > "$WORK/failclosed_probe.sh"
HS0302_ACCEPTANCE_DEPTH=9 bash "$WORK/failclosed_probe.sh" > "$WORK/failclosed.log" 2>&1
assert_fail_closed "$WORK/failclosed.log" "$?" '기준 커밋' \
  "fail-closed 자기 검사 ① 기준 SHA 를 지운 사본이 그 자리에서 끝난다"

# 두 번째 경로 — 우회 표 스캔이 오류를 낼 때. 기준 SHA 만 대체하면 이 경로는 인수 실행
# 안에서 한 번도 판정되지 않는다(Codex V1 2차).
cat > "$WORK/fake-grep" <<'FAKEGREP'
#!/bin/bash
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
