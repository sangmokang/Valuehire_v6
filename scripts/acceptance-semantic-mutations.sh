#!/usr/bin/env bash
# acceptance-semantic-mutations.sh — 인수 검사를 무력화하면 반드시 빨개지는가.
#
# 이 검사가 겨냥하는 사건(2026-08-21 사장님 지적):
#   scripts/acceptance-hs-a4.sh 의 본문을 통째로 `exit 0` 으로 바꿔도 CI 가 초록이었다.
#   검사의 존재(existence)만 봤고 검사의 의미(semantics)를 보지 않았기 때문이다.
#
# 여기서는 차단과 통과를 한 쌍으로 잰다.
#   차단 — 무력화한 사본 5종은 scripts/verify/run-acceptance.sh 가 전부 불합격시켜야 한다.
#   통과 — 손대지 않은 실제 인수 검사는 그대로 합격해야 한다(과잉 차단이면 그것도 결함).
#
# 원본 저장소를 건드리지 않는다. 사본은 mktemp 아래에서만 만들고 끝나면 상태를 대조한다.
set -uo pipefail

unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE GIT_OBJECT_DIRECTORY \
      GIT_ALTERNATE_OBJECT_DIRECTORIES GIT_COMMON_DIR GIT_PREFIX GIT_QUARANTINE_PATH

REPO=$(git rev-parse --show-toplevel 2>/dev/null) || {
  echo "NOT_RUN: git 저장소가 아니다"
  echo "CHECKED: 0"
  exit 2
}
cd "$REPO" || exit 2
RUNNER="$REPO/scripts/verify/run-acceptance.sh"
if [ ! -f "$RUNNER" ]; then
  echo "FAIL: 래퍼 판정기가 없다 — $RUNNER (fail-closed)"
  echo "CHECKED: 0"
  exit 2
fi

SNAPSHOT=$(git status --porcelain)
TMP=$(mktemp -d) || {
  echo "NOT_RUN: mktemp 실패"
  echo "CHECKED: 0"
  exit 2
}
trap 'ruby -rfileutils -e "FileUtils.remove_entry(ARGV[0]) if File.exist?(ARGV[0])" "$TMP"' EXIT

fail=0
checked=0

record() {
  local ok="$1" desc="$2" detail="$3"
  checked=$((checked + 1))
  if [ "$ok" -eq 0 ]; then
    printf 'PASS: %s — %s\n' "$desc" "$detail"
  else
    printf 'FAIL: %s — %s\n' "$desc" "$detail"
    fail=1
  fi
}

# ── 대상 목록: 검사 대상 0개는 합격이 아니다 ─────────────────────────────────
targets=()
while IFS= read -r f; do
  targets+=("$f")
done < <(git ls-files 'scripts/acceptance-*.sh' | LC_ALL=C sort)

if [ "${#targets[@]}" -lt 5 ]; then
  echo "FAIL: 인수 검사 대상이 ${#targets[@]}개 — 글로브가 비면 '전부 통과'가 되므로 불합격이다"
  echo "CHECKED: $checked"
  exit 1
fi
record 0 "대상 수집" "인수 검사 ${#targets[@]}개 (하한 5)"

# ── 무력화 5종. 어느 것도 래퍼를 통과해서는 안 된다 ──────────────────────────
write_mutant() {
  local kind="$1" path="$2"
  case "$kind" in
    exit-zero)  printf '#!/usr/bin/env bash\nexit 0\n' > "$path" ;;
    true-only)  printf '#!/usr/bin/env bash\ntrue\n' > "$path" ;;
    noop)       printf '#!/usr/bin/env bash\n: # no-op\n' > "$path" ;;
    empty)      printf '#!/usr/bin/env bash\n' > "$path" ;;
    echo-only)  printf '#!/usr/bin/env bash\necho "검사했습니다"\n' > "$path" ;;
    *)          return 1 ;;
  esac
}

for kind in exit-zero true-only noop empty echo-only; do
  blocked=0
  survivors=""
  for t in "${targets[@]}"; do
    mutant="$TMP/$(basename "$t")"
    write_mutant "$kind" "$mutant" || continue
    rc=0
    bash "$RUNNER" "$mutant" >/dev/null 2>&1 || rc=$?
    if [ "$rc" -ne 0 ]; then
      blocked=$((blocked + 1))
    else
      survivors="$survivors $(basename "$t")"
    fi
  done
  if [ "$blocked" -eq "${#targets[@]}" ]; then
    record 0 "무력화 차단: $kind" "${blocked}/${#targets[@]} 전부 불합격 처리"
  else
    record 1 "무력화 차단: $kind" "살아남은 사본:${survivors:- 없음} (${blocked}/${#targets[@]})"
  fi
done

# 출력 문구까지 위조한 no-op은 일반 래퍼만으로 구분할 수 없다. 줄 허용 수용시험은
# 승인된 정확한 Git blob인지 먼저 고정하고, 허용 소비를 제거한 verify.sh의 종료값을
# 이 검사 소유의 격리 fixture에서 직접 관찰한다. 검사 대상의 자체 출력은 증거로 쓰지 않는다.
semantic_repo="$TMP/secret-allowlist-semantic"
semantic_setup=0
mkdir -p "$semantic_repo"
if ! git archive HEAD | tar -x -C "$semantic_repo"; then
  semantic_setup=1
elif ! cp "$REPO/verify.sh" "$semantic_repo/verify.sh"; then
  semantic_setup=1
elif ! (
  cd "$semantic_repo" || exit 2
  git init -q
  git config user.email acceptance@local
  git config user.name acceptance
  git add -A
  git commit -qm fixture
); then
  semantic_setup=1
elif ! ruby -e '
  path = ARGV.fetch(0)
  source = File.binread(path)
  needle = %q{if [ "$used" -lt "$available" ]; then}
  abort "mutation target count != 1" unless source.scan(needle).length == 1
  File.binwrite(path, source.sub(needle, "if false; then"))
' "$semantic_repo/verify.sh"; then
  semantic_setup=1
fi

APPROVED_SECRET_ALLOWLIST_ACCEPTANCE_BLOB=$(printf '%s%s' \
  '293587d0c8e875e1211a' '228828f5f821ad26edeb')

acceptance_blob_is_approved() {
  local target="$1" actual
  actual=$(git hash-object -- "$target" 2>/dev/null) || return 2
  [ "$actual" = "$APPROVED_SECRET_ALLOWLIST_ACCEPTANCE_BLOB" ]
}

observe_mutated_verify_directly() {
  local direct_repo="$TMP/secret-allowlist-direct" clean key value canary hash
  mkdir -p "$direct_repo" || return 2
  git init -q "$direct_repo" || return 2
  cp "$semantic_repo/verify.sh" "$direct_repo/verify.sh" || return 2
  cp "$semantic_repo/.secret-patterns.default" "$direct_repo/.secret-patterns.default" || return 2

  clean="$direct_repo/patterns.clean"
  tr -d '\r' < "$direct_repo/.secret-patterns.default" |
    /usr/bin/grep -vE '^[[:space:]]*(#|$)' > "$clean" || return 2
  key=$(printf '%s%s' 'PASS' 'WORD')
  value=$(printf '%s%s' 'abc1' '23xy')
  canary=$(printf '%s=%s' "$key" "$value")
  if ! printf '%s\n' "$canary" | /usr/bin/grep -qEif "$clean"; then
    return 2
  fi
  hash=$(printf '%s' "$canary" | git hash-object --stdin) || return 2
  printf '%s\n' "$canary" > "$direct_repo/payload.txt"
  printf '%s\n' \
    '- path: "payload.txt"' \
    '  line_hash: "'"$hash"'"' \
    '  reason: "semantic mutation fixture"' \
    '  owner: "acceptance"' \
    '  expiry: "2099-12-31"' > "$direct_repo/.secret-allowlist.yaml"
  rm -f "$clean"
  (
    cd "$direct_repo" || exit 2
    git config user.email acceptance@local
    git config user.name acceptance
    git add -A
    git commit -qm fixture
  ) || return 2

  DIRECT_WORKTREE_RC=0
  (
    cd "$direct_repo" || exit 2
    VERIFY_SCAN_SOURCE=worktree bash verify.sh
  ) > "$TMP/direct-worktree.output" 2>&1 || DIRECT_WORKTREE_RC=$?
  DIRECT_INDEX_RC=0
  (
    cd "$direct_repo" || exit 2
    VERIFY_SCAN_SOURCE=index bash verify.sh
  ) > "$TMP/direct-index.output" 2>&1 || DIRECT_INDEX_RC=$?
  [ "$DIRECT_WORKTREE_RC" -eq 1 ] && [ "$DIRECT_INDEX_RC" -eq 1 ]
}

if [ "$semantic_setup" -ne 0 ]; then
  record 1 "줄 허용 직접 의미 변이" "격리 저장소 또는 허용 소비 제거 변이를 만들지 못함"
  record 1 "줄 허용 수용시험 blob 고정" "의미 판정기를 준비하지 못함"
  record 1 "PASS 출력 전용 위조 차단" "의미 판정기를 준비하지 못함"
  record 1 "조건부 PASS·무관 FAIL 위조 차단" "의미 판정기를 준비하지 못함"
  record 1 "조건부 정확 FAIL 위조 차단" "의미 판정기를 준비하지 못함"
elif observe_mutated_verify_directly; then
  record 0 "줄 허용 직접 의미 변이" "허용 소비 제거 뒤 verify.sh가 worktree=$DIRECT_WORKTREE_RC index=$DIRECT_INDEX_RC"

  if acceptance_blob_is_approved "$REPO/scripts/acceptance-secret-allowlist.sh"; then
    record 0 "줄 허용 수용시험 blob 고정" "검토된 Git blob과 일치"
  else
    record 1 "줄 허용 수용시험 blob 고정" "검토된 Git blob과 불일치"
  fi

  spoofed="$TMP/spoofed-secret-allowlist.sh"
  printf '%s\n' \
    '#!/usr/bin/env bash' \
    'echo "ALLOWED_LINES_COUNT=1"' \
    'echo "MODE_MISMATCH_COUNT=0"' \
    'echo "UNEXPECTED_MISSED_COUNT=0"' \
    'echo "CHECKED: 61"' \
    'echo "PASS: 줄 내용 허용 목록과 두 스캔 모드가 AC-ALLOWLIST-1을 만족한다"' \
    'exit 0' > "$spoofed"
  if acceptance_blob_is_approved "$spoofed"; then
    record 1 "PASS 출력 전용 위조 차단" "구현을 실행하지 않은 위조가 의미 변이를 통과함"
  else
    record 0 "PASS 출력 전용 위조 차단" "그럴듯한 PASS/CHECKED 출력의 미승인 blob을 거부함"
  fi

  conditional_spoof="$TMP/conditional-spoofed-secret-allowlist.sh"
  printf '%s\n' \
    '#!/usr/bin/env bash' \
    'if /usr/bin/grep -qF "if false; then" verify.sh; then' \
    '  echo "[3/61] 등재된 정확한 한 줄 (worktree) -> PASS (exit=0)"' \
    '  echo "[4/61] 등재된 정확한 한 줄 (index) -> PASS (exit=0)"' \
    '  echo "[5/61] 관련 없는 다른 검사 -> FAIL (expected=1 actual=0 scanner_error=0 required_output=0)"' \
    '  exit 1' \
    'fi' \
    'echo "ALLOWED_LINES_COUNT=1"' \
    'echo "MODE_MISMATCH_COUNT=0"' \
    'echo "UNEXPECTED_MISSED_COUNT=0"' \
    'echo "CHECKED: 61"' \
    'echo "PASS: 줄 내용 허용 목록과 두 스캔 모드가 AC-ALLOWLIST-1을 만족한다"' \
    'exit 0' > "$conditional_spoof"
  if acceptance_blob_is_approved "$conditional_spoof"; then
    record 1 "조건부 PASS·무관 FAIL 위조 차단" "정확 허용 PASS와 무관 FAIL을 같은 RED로 오인함"
  else
    record 0 "조건부 PASS·무관 FAIL 위조 차단" "조건부 출력 위조의 미승인 blob을 거부함"
  fi

  exact_conditional_spoof="$TMP/exact-conditional-spoofed-secret-allowlist.sh"
  printf '%s\n' \
    '#!/usr/bin/env bash' \
    'if /usr/bin/grep -qF "if false; then" verify.sh; then' \
    '  echo "[3/61] 등재된 정확한 한 줄 (worktree) -> FAIL (expected=0 actual=1 scanner_error=0 required_output=0)"' \
    '  echo "[4/61] 등재된 정확한 한 줄 (index) -> FAIL (expected=0 actual=1 scanner_error=0 required_output=0)"' \
    '  exit 1' \
    'fi' \
    'echo "ALLOWED_LINES_COUNT=1"' \
    'echo "MODE_MISMATCH_COUNT=0"' \
    'echo "UNEXPECTED_MISSED_COUNT=0"' \
    'echo "CHECKED: 61"' \
    'echo "PASS: 줄 내용 허용 목록과 두 스캔 모드가 AC-ALLOWLIST-1을 만족한다"' \
    'exit 0' > "$exact_conditional_spoof"
  if acceptance_blob_is_approved "$exact_conditional_spoof"; then
    record 1 "조건부 정확 FAIL 위조 차단" "구현을 실행하지 않고 정확 FAIL 두 줄만 위조해 의미 변이를 통과함"
  else
    record 0 "조건부 정확 FAIL 위조 차단" "정확 FAIL 문구만 재현한 미승인 수용시험은 거부됨"
  fi
else
  record 1 "줄 허용 직접 의미 변이" "허용 소비 제거 뒤 직접 fixture 종료값이 worktree=${DIRECT_WORKTREE_RC:-NOT_RUN} index=${DIRECT_INDEX_RC:-NOT_RUN}"
  record 1 "줄 허용 수용시험 blob 고정" "직접 의미 변이 실패로 신뢰 경계를 세우지 못함"
  record 1 "PASS 출력 전용 위조 차단" "직접 의미 변이 실패로 신뢰 경계를 세우지 못함"
  record 1 "조건부 PASS·무관 FAIL 위조 차단" "직접 의미 변이 실패로 신뢰 경계를 세우지 못함"
  record 1 "조건부 정확 FAIL 위조 차단" "직접 의미 변이 실패로 신뢰 경계를 세우지 못함"
fi

# P13 시연 자체를 한 줄 PASS 출력기로 바꾸는 단일 파일 위조도 차단해야 한다.
# 일반 래퍼의 종료값/PASS 표식만 믿으면 훅 fixture를 한 번도 실행하지 않은 사본이 통과한다.
p13_output_spoof="$TMP/acceptance-0-7.sh"
printf '%s\n' \
  '#!/usr/bin/env bash' \
  '# PUSH-PERFORMING' \
  'printf "%s\n" "PASS: 위반 8 종이 전부 차단됨 (각 건 훅 OFF·정확 사유 대조 통과) + 정상 변경 통과쌍 2건"' \
  'exit 0' > "$p13_output_spoof"
p13_output_spoof_rc=0
bash "$RUNNER" "$p13_output_spoof" >/dev/null 2>&1 || p13_output_spoof_rc=$?
if [ "$p13_output_spoof_rc" -ne 0 ]; then
  record 0 "P13 PASS 출력 전용 위조 차단" "fixture를 실행하지 않은 acceptance-0-7 사본 exit=$p13_output_spoof_rc"
else
  record 1 "P13 PASS 출력 전용 위조 차단" "fixture를 실행하지 않은 acceptance-0-7 사본이 래퍼를 통과함"
fi

# ── 통과 쪽: 손대지 않은 실제 인수 검사는 그대로 합격해야 한다 ───────────────
# 전량 실행은 CI 몫이다(중복 실행 비용). 여기서는 외부 의존이 없는 것 하나로 확인한다.
sample="scripts/acceptance-guard-global-skill-files.sh"
if [ -f "$sample" ]; then
  sample_rc=0
  bash "$RUNNER" "$sample" >/dev/null 2>&1 || sample_rc=$?
  if [ "$sample_rc" -eq 0 ]; then
    record 0 "정상 인수 검사 통과" "$(basename "$sample") exit=0 (과잉 차단 없음)"
  else
    record 1 "정상 인수 검사 통과" "$(basename "$sample") exit=$sample_rc — 래퍼가 정상 검사를 막는다"
  fi
else
  record 1 "정상 인수 검사 통과" "표본 없음 — $sample"
fi

# ── 래퍼 자신의 fail-closed ──────────────────────────────────────────────────
noarg_rc=0
bash "$RUNNER" >/dev/null 2>&1 || noarg_rc=$?
if [ "$noarg_rc" -ne 0 ]; then
  record 0 "래퍼 인자 없음 거부" "exit=$noarg_rc"
else
  record 1 "래퍼 인자 없음 거부" "exit=0 — 인자 없이도 합격이면 배선을 비워도 통과한다"
fi

missing_rc=0
bash "$RUNNER" "$TMP/does-not-exist.sh" >/dev/null 2>&1 || missing_rc=$?
if [ "$missing_rc" -ne 0 ]; then
  record 0 "래퍼 대상 없음 거부" "exit=$missing_rc"
else
  record 1 "래퍼 대상 없음 거부" "exit=0 — 없는 검사도 합격이면 파일을 지우면 통과한다"
fi

current=$(git status --porcelain)
if [ "$current" = "$SNAPSHOT" ]; then
  record 0 "원본 저장소 상태 불변" "before/after 동일"
else
  record 1 "원본 저장소 상태 불변" "변경 발생"
fi

printf 'CHECKED: %d\n' "$checked"
if [ "$fail" -eq 0 ]; then
  echo "VERDICT: PASS"
else
  echo "VERDICT: FAIL"
fi
exit "$fail"
