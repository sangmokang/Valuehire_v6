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
#              duplicate 로 접는 것, HMAC 입력에서 position_ref·channel·구분자를 빼는 것,
#              #97 마이그레이션 수정, hs_candidates 를 우회하는 새 표 추가, 시험 미실행.
#   막지 못함 — 시험 본문이 맞는 것을 보는지(그것은 pytest 와 변이 검증의 몫),
#              런타임 동시성 자체(그것은 test_ac3 가 20회 실제 경쟁으로 판정한다).
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
SCHEMA=humansearch/src/humansearch/storage_schema.py
BASE_SHA=7473ec8
MIN_TESTS=6

WORK=$(mktemp -d) || { echo "NOT_RUN: mktemp 실패"; echo "CHECKED: 0"; exit 2; }
trap 'rm -rf "$WORK"' EXIT

fail=0
checked=0
pass_item() { echo "PASS: $1"; checked=$((checked + 1)); }
fail_item() { echo "FAIL: $1"; fail=1; checked=$((checked + 1)); }
skip_item() { echo "NOT_RUN: $1"; checked=$((checked + 1)); }

for required in "$MODULE" "$TESTS" "$SCHEMA"; do
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

# HMAC 입력에 세 필드와 구분자가 모두 들어가는가: candidate_key_hmac 함수 본문만 본다.
hmac_inputs_present() {
  local file=$1
  awk '/^def candidate_key_hmac/{on=1} on{print} on && /^    return /{exit}' "$file" \
    > "$WORK/hmac_body.txt"
  [ -s "$WORK/hmac_body.txt" ] || return 1
  "$GREP" -q 'position_ref.encode' "$WORK/hmac_body.txt" || return 1
  "$GREP" -q 'channel.encode' "$WORK/hmac_body.txt" || return 1
  "$GREP" -q 'candidate_ref.encode' "$WORK/hmac_body.txt" || return 1
  "$GREP" -q '_FIELD_SEPARATOR' "$WORK/hmac_body.txt" || return 1
  return 0
}

# ── 1. RED 시험 파일이 존재하고 test 함수가 충분한가 ─────────────────────────
test_count=$("$GREP" -c '^def test_' "$TESTS")
case $? in
  0|1) : ;;
  *) echo "NOT_RUN: 시험 함수 계수 중 grep 오류"; echo "CHECKED: 0"; exit 2 ;;
esac
if [ "$test_count" -ge "$MIN_TESTS" ]; then
  pass_item "기록 시험 함수 ${test_count}개 (>= ${MIN_TESTS})"
else
  fail_item "기록 시험 함수 ${test_count}개 — ${MIN_TESTS}개 미만이면 AC 를 다 덮지 못한다"
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

# ── 4. HMAC 입력에 세 필드와 구분자가 있는가 (양성) ─────────────────────────
if hmac_inputs_present "$MODULE"; then
  pass_item "HMAC 입력에 position_ref·channel·candidate_ref 와 구분자가 모두 들어간다"
else
  fail_item "HMAC 입력에서 필드나 구분자가 빠졌다 — 다른 포지션·채널이 한 행으로 합쳐진다"
fi

# ── 5. HMAC 탐지기 음성 대조군: channel 을 뺀 사본은 반드시 잡혀야 한다 ──────
"$GREP" -v 'channel.encode' "$MODULE" > "$WORK/module_no_channel.py"
if ! hmac_inputs_present "$WORK/module_no_channel.py"; then
  pass_item "HMAC 탐지기 음성 대조군 통과 — channel 을 뺀 사본은 FAIL 로 잡힌다"
else
  fail_item "HMAC 탐지기가 channel 없는 사본도 통과시킨다 — 탐지기가 무의미하다"
fi

# 구분자 상수가 실제로 \x1f 인가 (상수 이름만 맞고 값이 빈 문자열이면 경계가 사라진다)
if "$GREP" -q '^_FIELD_SEPARATOR: Final = b"\\x1f"' "$MODULE"; then
  pass_item "필드 구분자 상수가 b\"\\x1f\" 이다"
else
  fail_item "필드 구분자 상수가 b\"\\x1f\" 가 아니다 — 필드 경계가 무너진다"
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
  skip_item "기준 커밋 ${BASE_SHA} 를 찾을 수 없다 — 마이그레이션 동일성 대조 불가"
fi

# ── 7. hs_candidates 를 우회하는 새 표가 src 에 없는가 ───────────────────────
"$GREP" -rniE '^[[:space:]]*create[[:space:]]+table' humansearch/src --include='*.py' \
  > "$WORK/create_table.txt"
rc=$?
if [ "$rc" -gt 1 ]; then
  skip_item "create table 스캔 중 grep 오류 (rc=$rc)"
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
( cd humansearch && uv run pytest tests/test_hs_0302_candidate_identity.py -q ) \
  > "$pytest_log" 2>&1
pytest_rc=$?
passed=$("$GREP" -oE '[0-9]+ passed' "$pytest_log" | tail -1 | "$GREP" -oE '[0-9]+')
failed=$("$GREP" -cE '^FAILED|^ERROR' "$pytest_log")
if [ "$pytest_rc" -eq 0 ] && [ "${passed:-0}" -ge "$MIN_TESTS" ] && [ "${failed:-0}" -eq 0 ]; then
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
