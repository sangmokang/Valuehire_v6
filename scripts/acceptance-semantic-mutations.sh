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
# verify.sh의 허용 소비를 제거한 격리본에서 반드시 RED가 되는지 별도 판정한다.
semantic_repo="$TMP/secret-allowlist-semantic"
semantic_output="$TMP/secret-allowlist-semantic.output"
semantic_setup=0
mkdir -p "$semantic_repo"
if ! git archive HEAD | tar -x -C "$semantic_repo"; then
  semantic_setup=1
elif ! cp "$REPO/verify.sh" "$semantic_repo/verify.sh"; then
  semantic_setup=1
elif ! cp "$REPO/scripts/acceptance-secret-allowlist.sh" \
          "$semantic_repo/scripts/acceptance-secret-allowlist.sh"; then
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

probe_secret_allowlist_semantics() {
  local target="$1" rc=0
  cp "$target" "$semantic_repo/scripts/acceptance-secret-allowlist.sh" || return 2
  (
    cd "$semantic_repo" || exit 2
    bash scripts/verify/run-acceptance.sh scripts/acceptance-secret-allowlist.sh
  ) > "$semantic_output" 2>&1 || rc=$?
  [ "$rc" -ne 0 ] &&
    /usr/bin/grep -qF '등재된 정확한 한 줄' "$semantic_output" &&
    /usr/bin/grep -qF -- '-> FAIL' "$semantic_output"
}

if [ "$semantic_setup" -ne 0 ]; then
  record 1 "줄 허용 수용시험 의미 변이" "격리 저장소 또는 허용 소비 제거 변이를 만들지 못함"
  record 1 "PASS 출력 전용 위조 차단" "의미 판정기를 준비하지 못함"
  record 1 "조건부 PASS·무관 FAIL 위조 차단" "의미 판정기를 준비하지 못함"
elif probe_secret_allowlist_semantics "$REPO/scripts/acceptance-secret-allowlist.sh"; then
  record 0 "줄 허용 수용시험 의미 변이" "허용 소비 제거 시 정확 허용 사례가 RED"

  spoofed="$TMP/spoofed-secret-allowlist.sh"
  printf '%s\n' \
    '#!/usr/bin/env bash' \
    'echo "ALLOWED_LINES_COUNT=1"' \
    'echo "MODE_MISMATCH_COUNT=0"' \
    'echo "UNEXPECTED_MISSED_COUNT=0"' \
    'echo "CHECKED: 41"' \
    'echo "PASS: 줄 내용 허용 목록과 두 스캔 모드가 AC-ALLOWLIST-1을 만족한다"' \
    'exit 0' > "$spoofed"
  if probe_secret_allowlist_semantics "$spoofed"; then
    record 1 "PASS 출력 전용 위조 차단" "구현을 실행하지 않은 위조가 의미 변이를 통과함"
  else
    record 0 "PASS 출력 전용 위조 차단" "그럴듯한 PASS/CHECKED 출력만으로는 의미 변이를 통과하지 못함"
  fi

  conditional_spoof="$TMP/conditional-spoofed-secret-allowlist.sh"
  printf '%s\n' \
    '#!/usr/bin/env bash' \
    'if /usr/bin/grep -qF "if false; then" verify.sh; then' \
    '  echo "[3/41] 등재된 정확한 한 줄 (worktree) -> PASS (exit=0)"' \
    '  echo "[4/41] 등재된 정확한 한 줄 (index) -> PASS (exit=0)"' \
    '  echo "[5/41] 관련 없는 다른 검사 -> FAIL (expected=1 actual=0 scanner_error=0)"' \
    '  exit 1' \
    'fi' \
    'echo "ALLOWED_LINES_COUNT=1"' \
    'echo "MODE_MISMATCH_COUNT=0"' \
    'echo "UNEXPECTED_MISSED_COUNT=0"' \
    'echo "CHECKED: 41"' \
    'echo "PASS: 줄 내용 허용 목록과 두 스캔 모드가 AC-ALLOWLIST-1을 만족한다"' \
    'exit 0' > "$conditional_spoof"
  if probe_secret_allowlist_semantics "$conditional_spoof"; then
    record 1 "조건부 PASS·무관 FAIL 위조 차단" "정확 허용 PASS와 무관 FAIL을 같은 RED로 오인함"
  else
    record 0 "조건부 PASS·무관 FAIL 위조 차단" "실패 사유가 정확 허용 결과 줄에 결속됨"
  fi
else
  record 1 "줄 허용 수용시험 의미 변이" "허용 소비 제거 뒤에도 정확 허용 사례가 RED가 아님"
  record 1 "PASS 출력 전용 위조 차단" "기준 수용시험의 변이 민감도가 먼저 성립하지 않음"
  record 1 "조건부 PASS·무관 FAIL 위조 차단" "기준 수용시험의 변이 민감도가 먼저 성립하지 않음"
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
