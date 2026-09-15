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
SCHEMA=humansearch/src/humansearch/storage_schema.py
BASE_SHA=7473ec8
MIN_TESTS=6
MIN_R2_TESTS=10

WORK=$(mktemp -d) || { echo "NOT_RUN: mktemp 실패"; echo "CHECKED: 0"; exit 2; }
trap 'rm -rf "$WORK"' EXIT

fail=0
checked=0
pass_item() { echo "PASS: $1"; checked=$((checked + 1)); }
fail_item() { echo "FAIL: $1"; fail=1; checked=$((checked + 1)); }
# 필수 검사를 할 수 없으면 건수만 늘리고 통과시키지 않는다 — 그 자리에서 끝낸다.
abort_not_run() { echo "NOT_RUN: $1"; echo "CHECKED: $checked"; exit 2; }

for required in "$MODULE" "$TESTS" "$TESTS_R2" "$SCHEMA"; do
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
r2_count=$("$GREP" -c '^def test_' "$TESTS_R2")
case $? in
  0|1) : ;;
  *) abort_not_run "2차 시험 함수 계수 중 grep 오류" ;;
esac
total_tests=$((test_count + r2_count))
if [ "$test_count" -ge "$MIN_TESTS" ] && [ "$r2_count" -ge "$MIN_R2_TESTS" ]; then
  pass_item "기록 시험 함수 ${test_count}개 + V1 결함 시험 ${r2_count}개 = ${total_tests}개"
else
  fail_item "시험 함수 부족 — 1차 ${test_count}(>= ${MIN_TESTS}) · 2차 ${r2_count}(>= ${MIN_R2_TESTS})"
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
pytest_log="$WORK/pytest.log"
# 1차와 2차(Codex V1 결함) 시험을 모두 돌린다. 한쪽만 돌리면 닫은 결함이 다시 열려도 모른다.
( cd humansearch && uv run pytest tests/test_hs_0302_candidate_identity.py tests/test_hs_0302_r2_hardening.py -q ) \
  > "$pytest_log" 2>&1
pytest_rc=$?
passed=$("$GREP" -oE '[0-9]+ passed' "$pytest_log" | tail -1 | "$GREP" -oE '[0-9]+')
failed=$("$GREP" -cE '^FAILED|^ERROR' "$pytest_log")
if [ "$pytest_rc" -eq 0 ] && [ "${passed:-0}" -ge "$total_tests" ] && [ "${failed:-0}" -eq 0 ]; then
  pass_item "pytest 실제 실행 — ${passed} passed, 실패 0, 종료값 0"
else
  fail_item "pytest 실제 실행 — 종료값 ${pytest_rc}, passed=${passed:-0}, 실패줄=${failed:-0}"
  tail -20 "$pytest_log"
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
