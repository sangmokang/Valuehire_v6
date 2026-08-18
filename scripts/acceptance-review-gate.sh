#!/usr/bin/env bash
# acceptance-review-gate.sh — AC-30 조언형 review-gate 판정 계약
#
# 출력: 사례마다 PASS/FAIL, 마지막 CHECKED: 20
# 종료: 0=PASS | 1=FAIL | 2=NOT_RUN
# 불변식: 합성 저장소만 쓰며 실제 저장소를 바꾸지 않는다.
set -uo pipefail

unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE GIT_OBJECT_DIRECTORY \
  GIT_ALTERNATE_OBJECT_DIRECTORIES GIT_COMMON_DIR GIT_PREFIX GIT_QUARANTINE_PATH

REPO=$(git rev-parse --show-toplevel 2>/dev/null) || {
  echo "NOT_RUN: git 저장소가 아니다"
  echo "CHECKED: 0"
  exit 2
}
cd "$REPO" || {
  echo "NOT_RUN: 저장소 루트로 이동 실패"
  echo "CHECKED: 0"
  exit 2
}

TARGET="$REPO/scripts/review_gate.py"
WORKFLOW="$REPO/.github/workflows/review-gate.yml"
VERIFY_WORKFLOW="$REPO/.github/workflows/verify.yml"
EXPECTED_CHECKED=20
SNAP0=$(git status --porcelain)
TMP=$(mktemp -d) || {
  echo "NOT_RUN: 임시 작업공간 생성 실패"
  echo "CHECKED: 0"
  exit 2
}
trap 'rm -rf "$TMP"' EXIT

fail=0
checked=0

pass() {
  checked=$((checked + 1))
  printf 'PASS: %s\n' "$1"
}

fail_case() {
  checked=$((checked + 1))
  printf 'FAIL: %s\n' "$1"
  fail=1
}

expect_rc() {
  local desc="$1" want="$2"
  shift 2
  local rc=0
  "$@" >/dev/null 2>&1 || rc=$?
  if [ "$rc" -eq "$want" ]; then
    pass "$desc (exit=$rc)"
  else
    fail_case "$desc (기대 exit=$want, 실제 $rc)"
  fi
}

run_gate() {
  local repo="$1" base="$2" head="$3" out="$4" summary="$5"
  python3 "$TARGET" \
    --repo "$repo" \
    --base "$base" \
    --head "$head" \
    --output "$out" \
    --summary "$summary"
}

manifest_matches() {
  local file="$1" risk="$2" signal="$3" file_count="$4" head="$5"
  python3 - "$file" "$risk" "$signal" "$file_count" "$head" <<'PY'
import json
import sys

path, risk, signal, file_count, head = sys.argv[1:]
with open(path, encoding="utf-8") as handle:
    data = json.load(handle)

required = {
    "schema_version",
    "state",
    "base_sha",
    "head_sha",
    "commit_count",
    "file_count",
    "files",
    "change_types",
    "risk",
    "signals",
    "recommended_checks",
    "manifest_id",
}
assert required == set(data), (required - set(data), set(data) - required)
assert data["schema_version"] == 1
assert data["state"] == "advisory"
assert data["risk"] == risk
assert data["file_count"] == int(file_count)
assert len(data["files"]) == data["file_count"]
assert data["files"] == sorted(data["files"])
assert data["head_sha"] == head
assert len(data["head_sha"]) == 40
assert len(data["base_sha"]) == 40
assert len(data["manifest_id"]) == 64
assert "verify" in data["recommended_checks"]
if signal != "-":
    assert data["signals"].get(signal) is True, (signal, data["signals"])
PY
}

FIX="$TMP/repo"
mkdir -p "$FIX"
git -C "$FIX" init -q
git -C "$FIX" config user.email acceptance@local
git -C "$FIX" config user.name acceptance
mkdir -p "$FIX/scripts"
printf '# base\n' > "$FIX/README.md"
printf '#!/usr/bin/env bash\nexit 0\n' > "$FIX/scripts/acceptance-sentinel.sh"
chmod +x "$FIX/scripts/acceptance-sentinel.sh"
git -C "$FIX" add README.md scripts/acceptance-sentinel.sh
git -C "$FIX" commit -qm base
BASE=$(git -C "$FIX" rev-parse HEAD)

# 1. 구현 파일 존재
if [ -f "$TARGET" ]; then
  pass "판정기 실존 — scripts/review_gate.py"
else
  fail_case "판정기 없음 — scripts/review_gate.py"
fi

# 2~4. 문서 변경, 결정론, 새 head 무효화
git -C "$FIX" checkout -q -b docs "$BASE"
mkdir -p "$FIX/docs"
printf 'guide\n' > "$FIX/docs/road map.md"
git -C "$FIX" add 'docs/road map.md'
git -C "$FIX" commit -qm docs
DOCS_HEAD=$(git -C "$FIX" rev-parse HEAD)
DOCS_JSON="$TMP/docs.json"
DOCS_SUMMARY="$TMP/docs.md"
docs_rc=0
run_gate "$FIX" "$BASE" "$DOCS_HEAD" "$DOCS_JSON" "$DOCS_SUMMARY" >/dev/null 2>&1 || docs_rc=$?
if [ "$docs_rc" -eq 0 ] \
  && manifest_matches "$DOCS_JSON" low - 1 "$DOCS_HEAD" \
  && grep -q 'docs/road map.md' "$DOCS_SUMMARY"; then
  pass "공백 경로를 포함한 문서 변경 1개 → 낮은 위험과 현재 head 명부"
else
  fail_case "문서 변경 판정 불일치 (exit=$docs_rc)"
fi

DOCS_JSON_2="$TMP/docs-2.json"
DOCS_SUMMARY_2="$TMP/docs-2.md"
det_rc=0
run_gate "$FIX" "$BASE" "$DOCS_HEAD" "$DOCS_JSON_2" "$DOCS_SUMMARY_2" >/dev/null 2>&1 || det_rc=$?
id1=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["manifest_id"])' "$DOCS_JSON" 2>/dev/null)
id2=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["manifest_id"])' "$DOCS_JSON_2" 2>/dev/null)
if [ "$det_rc" -eq 0 ] && [ -n "$id1" ] && [ "$id1" = "$id2" ]; then
  pass "같은 입력 → 같은 판정 지문"
else
  fail_case "같은 입력의 판정 지문이 달라짐"
fi

printf 'second\n' > "$FIX/docs/second.md"
git -C "$FIX" add docs/second.md
git -C "$FIX" commit -qm 'new head'
DOCS_HEAD_2=$(git -C "$FIX" rev-parse HEAD)
DOCS_JSON_3="$TMP/docs-3.json"
head_rc=0
run_gate "$FIX" "$BASE" "$DOCS_HEAD_2" "$DOCS_JSON_3" "$TMP/docs-3.md" >/dev/null 2>&1 || head_rc=$?
id3=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["manifest_id"])' "$DOCS_JSON_3" 2>/dev/null)
if [ "$head_rc" -eq 0 ] && [ -n "$id3" ] && [ "$id1" != "$id3" ]; then
  pass "새 커밋 → 과거 판정과 다른 head·판정 지문"
else
  fail_case "새 커밋이 과거 판정을 무효화하지 못함"
fi

# 5. 일반 코드 → medium
git -C "$FIX" checkout -q -B code "$BASE"
mkdir -p "$FIX/src"
printf 'value = 1\n' > "$FIX/src/feature.py"
git -C "$FIX" add src/feature.py
git -C "$FIX" commit -qm code
CODE_HEAD=$(git -C "$FIX" rev-parse HEAD)
code_rc=0
run_gate "$FIX" "$BASE" "$CODE_HEAD" "$TMP/code.json" "$TMP/code.md" >/dev/null 2>&1 || code_rc=$?
if [ "$code_rc" -eq 0 ] && manifest_matches "$TMP/code.json" medium - 1 "$CODE_HEAD"; then
  pass "일반 코드 변경 → 중간 위험"
else
  fail_case "일반 코드 변경 위험도 불일치"
fi

# 6. 검사·계약 경계 → high + weakens_check
git -C "$FIX" checkout -q -B contract "$BASE"
mkdir -p "$FIX/contracts"
printf '{"version":1}\n' > "$FIX/contracts/policy.json"
git -C "$FIX" add contracts/policy.json
git -C "$FIX" commit -qm contract
CONTRACT_HEAD=$(git -C "$FIX" rev-parse HEAD)
contract_rc=0
run_gate "$FIX" "$BASE" "$CONTRACT_HEAD" "$TMP/contract.json" "$TMP/contract.md" >/dev/null 2>&1 || contract_rc=$?
if [ "$contract_rc" -eq 0 ] && manifest_matches "$TMP/contract.json" high weakens_check 1 "$CONTRACT_HEAD"; then
  pass "검사·계약 변경 → 높은 위험과 weakens_check"
else
  fail_case "검사·계약 변경 신호 불일치"
fi

# 7. 보안 경계 → high + touches_security
git -C "$FIX" checkout -q -B security "$BASE"
mkdir -p "$FIX/src/auth"
printf 'SESSION = 1\n' > "$FIX/src/auth/session.py"
git -C "$FIX" add src/auth/session.py
git -C "$FIX" commit -qm security
SEC_HEAD=$(git -C "$FIX" rev-parse HEAD)
sec_rc=0
run_gate "$FIX" "$BASE" "$SEC_HEAD" "$TMP/security.json" "$TMP/security.md" >/dev/null 2>&1 || sec_rc=$?
if [ "$sec_rc" -eq 0 ] && manifest_matches "$TMP/security.json" high touches_security 1 "$SEC_HEAD"; then
  pass "보안 경계 변경 → 높은 위험과 touches_security"
else
  fail_case "보안 경계 신호 불일치"
fi

# 8. 데이터 경계 → high + touches_data
git -C "$FIX" checkout -q -B data "$BASE"
mkdir -p "$FIX/supabase/migrations"
printf 'CREATE TABLE sample(id int);\n' > "$FIX/supabase/migrations/001.sql"
git -C "$FIX" add supabase/migrations/001.sql
git -C "$FIX" commit -qm data
DATA_HEAD=$(git -C "$FIX" rev-parse HEAD)
data_rc=0
run_gate "$FIX" "$BASE" "$DATA_HEAD" "$TMP/data.json" "$TMP/data.md" >/dev/null 2>&1 || data_rc=$?
if [ "$data_rc" -eq 0 ] && manifest_matches "$TMP/data.json" high touches_data 1 "$DATA_HEAD"; then
  pass "데이터 경계 변경 → 높은 위험과 touches_data"
else
  fail_case "데이터 경계 신호 불일치"
fi

# 9. 외부 의존 경계 → high + touches_external
git -C "$FIX" checkout -q -B external "$BASE"
mkdir -p "$FIX/tools"
printf 'print("sync")\n' > "$FIX/tools/gmail-sync.py"
git -C "$FIX" add tools/gmail-sync.py
git -C "$FIX" commit -qm external
EXT_HEAD=$(git -C "$FIX" rev-parse HEAD)
ext_rc=0
run_gate "$FIX" "$BASE" "$EXT_HEAD" "$TMP/external.json" "$TMP/external.md" >/dev/null 2>&1 || ext_rc=$?
if [ "$ext_rc" -eq 0 ] && manifest_matches "$TMP/external.json" high touches_external 1 "$EXT_HEAD"; then
  pass "외부 의존 경계 변경 → 높은 위험과 touches_external"
else
  fail_case "외부 의존 경계 신호 불일치"
fi

# 10. 검사 약화 문구 → critical
git -C "$FIX" checkout -q -B weakening "$BASE"
mkdir -p "$FIX/.github/workflows"
weak_key=continue-on
weak_key="${weak_key}-error"
printf 'jobs:\n  test:\n    %s: true\n' "$weak_key" > "$FIX/.github/workflows/weak.yml"
git -C "$FIX" add .github/workflows/weak.yml
git -C "$FIX" commit -qm weakening
WEAK_HEAD=$(git -C "$FIX" rev-parse HEAD)
weak_rc=0
run_gate "$FIX" "$BASE" "$WEAK_HEAD" "$TMP/weakening.json" "$TMP/weakening.md" >/dev/null 2>&1 || weak_rc=$?
if [ "$weak_rc" -eq 0 ] && manifest_matches "$TMP/weakening.json" critical weakening_pattern 1 "$WEAK_HEAD"; then
  pass "검사 약화 문구 → 가장 높은 위험"
else
  fail_case "검사 약화 문구를 가장 높은 위험으로 올리지 못함"
fi

# 11. 검사 파일 삭제 → critical
git -C "$FIX" checkout -q -B deletion "$BASE"
git -C "$FIX" rm -q scripts/acceptance-sentinel.sh
git -C "$FIX" commit -qm deletion
DEL_HEAD=$(git -C "$FIX" rev-parse HEAD)
del_rc=0
run_gate "$FIX" "$BASE" "$DEL_HEAD" "$TMP/deletion.json" "$TMP/deletion.md" >/dev/null 2>&1 || del_rc=$?
if [ "$del_rc" -eq 0 ] && manifest_matches "$TMP/deletion.json" critical check_deleted 1 "$DEL_HEAD"; then
  pass "검사 파일 삭제 → 가장 높은 위험"
else
  fail_case "검사 파일 삭제를 가장 높은 위험으로 올리지 못함"
fi

# 12~14. 잘못된 입력과 0건은 NOT_RUN(2)
expect_rc "없는 base 기록 → NOT_RUN" 2 run_gate "$FIX" deadbeef "$DEL_HEAD" "$TMP/bad-base.json" "$TMP/bad-base.md"
expect_rc "없는 head 기록 → NOT_RUN" 2 run_gate "$FIX" "$BASE" deadbeef "$TMP/bad-head.json" "$TMP/bad-head.md"
expect_rc "base와 head가 같아 변경 0건 → NOT_RUN" 2 run_gate "$FIX" "$BASE" "$BASE" "$TMP/empty.json" "$TMP/empty.md"

# 15. workflow 사건·권한·동시성 계약
if [ -f "$WORKFLOW" ] \
  && grep -q '^  pull_request:$' "$WORKFLOW" \
  && grep -q 'types: \[opened, synchronize, reopened\]' "$WORKFLOW" \
  && grep -q '^  contents: read$' "$WORKFLOW" \
  && grep -q 'group: review-gate-${{ github.event.pull_request.number }}' "$WORKFLOW" \
  && grep -q 'cancel-in-progress: true' "$WORKFLOW" \
  && ! grep -qE 'pull_request_target|^[[:space:]]+[A-Za-z-]+: write' "$WORKFLOW"; then
  pass "workflow는 세 사건·읽기 권한·현재 요청 단위 동시성만 사용"
else
  fail_case "workflow 사건·권한·동시성 계약 위반"
fi

# 16. workflow 실제 판정기 배선
if [ -f "$WORKFLOW" ] \
  && grep -q 'python3 scripts/review_gate.py' "$WORKFLOW" \
  && grep -q 'github.event.pull_request.base.sha' "$WORKFLOW" \
  && grep -q 'github.event.pull_request.head.sha' "$WORKFLOW" \
  && grep -q 'GITHUB_STEP_SUMMARY' "$WORKFLOW"; then
  pass "workflow가 현재 base/head로 실제 판정기를 실행하고 화면 요약을 남김"
else
  fail_case "workflow 실제 판정기 배선 없음"
fi

# 17. 라벨/API 쓰기 경로 부재
if [ -f "$TARGET" ] && [ -f "$WORKFLOW" ] \
  && ! grep -Ei 'gh[[:space:]]+api|/labels|addLabels|removeLabels|GITHUB_TOKEN|issues:[[:space:]]*write|pull-requests:[[:space:]]*write|pull_request_target' "$TARGET" "$WORKFLOW" >/dev/null; then
  pass "판정기와 workflow에 라벨/API 쓰기 권한 없음"
else
  fail_case "라벨/API 쓰기 경로가 있거나 파일이 없음"
fi

# 18. 기존 verify workflow에 인수 검사 무조건 1회 배선
run_lines=$(grep -c 'run: bash scripts/acceptance-review-gate.sh' "$VERIFY_WORKFLOW" 2>/dev/null)
step_block=$(awk '/- name: 인수 검사 review-gate/,/run: bash scripts\/acceptance-review-gate.sh/' "$VERIFY_WORKFLOW" 2>/dev/null)
if [ "$run_lines" -eq 1 ] && [ -n "$step_block" ] \
  && ! printf '%s\n' "$step_block" | grep -qE '^[[:space:]]*(if:|continue-on-error:)'; then
  pass "기존 verify workflow에 인수 검사 무조건 1회 배선"
else
  fail_case "기존 verify workflow 인수 검사 배선 불일치 (실행 줄 ${run_lines}회)"
fi

# 19. 실제 작업 브랜치의 current base..HEAD 명부 대조
REAL_BASE=$(git merge-base main HEAD 2>/dev/null)
REAL_HEAD=$(git rev-parse HEAD 2>/dev/null)
real_rc=0
run_gate "$REPO" "$REAL_BASE" "$REAL_HEAD" "$TMP/real.json" "$TMP/real.md" >/dev/null 2>&1 || real_rc=$?
real_files=$(git diff --name-only -z "$REAL_BASE...$REAL_HEAD" 2>/dev/null | python3 -c 'import sys; print(len(sys.stdin.buffer.read().split(b"\0")) - 1)' 2>/dev/null)
manifest_files=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["file_count"])' "$TMP/real.json" 2>/dev/null)
manifest_head=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["head_sha"])' "$TMP/real.json" 2>/dev/null)
if [ "$real_rc" -eq 0 ] && [ "$real_files" = "$manifest_files" ] && [ "$REAL_HEAD" = "$manifest_head" ]; then
  pass "실제 작업 브랜치의 현재 head·파일 수와 판정 명부 일치"
else
  fail_case "실제 작업 브랜치 명부 불일치 (exit=$real_rc, git=$real_files, manifest=$manifest_files)"
fi

# 20. 검사 무오염
SNAP1=$(git status --porcelain)
if [ "$SNAP0" = "$SNAP1" ]; then
  pass "검사 전후 저장소 상태 동일"
else
  fail_case "검사가 저장소를 오염시킴"
fi

if [ "$checked" -ne "$EXPECTED_CHECKED" ]; then
  printf 'FAIL: 검사 수 %d ≠ 계약값 %d\n' "$checked" "$EXPECTED_CHECKED"
  fail=1
fi

printf 'CHECKED: %d\n' "$checked"
exit "$fail"
