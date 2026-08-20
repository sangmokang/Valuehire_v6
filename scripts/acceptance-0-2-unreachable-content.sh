#!/usr/bin/env bash
# AC-19 — acceptance-0-2의 상시 내용 검사와 일회성 종료상태 검사를 분리한다.
set -euo pipefail

# 합성 fixture는 호출자가 고른 실제 패턴 파일이 아니라 아래 합성 카나리만 사용한다.
unset SECRET_PATTERNS_FILE
ROOT=$(git rev-parse --show-toplevel)
unset GIT_DIR GIT_INDEX_FILE GIT_OBJECT_DIRECTORY GIT_WORK_TREE GIT_COMMON_DIR \
  GIT_ALTERNATE_OBJECT_DIRECTORIES GIT_PREFIX
TARGET="$ROOT/scripts/acceptance-0-2.sh"
VERIFY="$ROOT/verify.sh"
SELF="$ROOT/scripts/acceptance-0-2-unreachable-content.sh"
WORKFLOW="$ROOT/.github/workflows/verify.yml"
REAL_GIT=$(command -v git)
REAL_GREP=$(command -v grep)
TMP=$(mktemp -d)
trap 'rm -rf -- "$TMP"' EXIT

CANARY='AC19-CANARY-8842'

# 프로브 환경변수는 사례 수(TOTAL)를 줄인다. 바깥 환경에서 들어오면 "있으면 통과하는
# 스위치"가 되므로(2026-08-21 V1 지적·재현: AC19_PATTERN_ENV_PROBE=1 → 22건이 1건),
# 이 스크립트가 스스로 띄운 경우에만 받아들인다. 부모는 자기 TMP 안에 표식 파일을
# 만들고 그 경로와 값을 함께 넘긴다. 바깥에서 변수만 켜면 표식이 없어 즉시 차단한다.
PROBE_SET="${AC19_COUNT_MISMATCH_PROBE:-}${AC19_PATTERN_ENV_PROBE:-}${AC19_INNER_HOOK_PROBE:-}"
if [ -n "$PROBE_SET" ]; then
  if [ -z "${AC19_PROBE_NONCE_PATH:-}" ] || [ -z "${AC19_PROBE_NONCE:-}" ] \
     || [ ! -f "$AC19_PROBE_NONCE_PATH" ] \
     || [ "$(cat "$AC19_PROBE_NONCE_PATH" 2>/dev/null)" != "$AC19_PROBE_NONCE" ]; then
    echo 'FAIL: AC-19 프로브 변수가 바깥에서 설정됐다 — 사례 수 축소 스위치를 차단한다'
    exit 2
  fi
fi
AC19_PROBE_NONCE="ac19-$$-$(date +%s)"  # 자격증명이 아니라 자기호출 표식이다
AC19_PROBE_NONCE_PATH="$TMP/probe-token"
printf '%s' "$AC19_PROBE_NONCE" > "$AC19_PROBE_NONCE_PATH"
export AC19_PROBE_NONCE AC19_PROBE_NONCE_PATH

if [ -n "${AC19_COUNT_MISMATCH_PROBE:-}" ]; then
  TOTAL=2
elif [ -n "${AC19_PATTERN_ENV_PROBE:-}" ]; then
  TOTAL=1
elif [ -n "${AC19_INNER_HOOK_PROBE:-}" ]; then
  TOTAL=18
else
  TOTAL=22
fi
checked=0
failed=0

make_fixture() {
  local fixture=$1

  mkdir -p "$fixture/scripts" "$fixture/docs"
  cp "$TARGET" "$fixture/scripts/acceptance-0-2.sh"
  cp "$VERIFY" "$fixture/verify.sh"
  printf '.secret-patterns\n.secret-patterns.default\n' > "$fixture/.gitignore"
  printf '%s\n' "$CANARY" > "$fixture/.secret-patterns"
  printf '%s\n' "$CANARY" > "$fixture/.secret-patterns.default"
  printf 'synthetic fixture\n' > "$fixture/docs/README.md"

  (
    cd "$fixture"
    git init -q -b main
    git config user.email acceptance@local
    git config user.name acceptance
    git add .gitignore docs/README.md scripts/acceptance-0-2.sh verify.sh
    git commit -qm fixture
  )
}

run_ci_history_scan() {
  local fixture=$1 ci_step

  ci_step=$(awk '
    /^      - name: 히스토리 전량 스캔/ { in_step=1; next }
    in_step && /^      - name:/ { exit }
    in_step && /^        run: \|/ { in_run=1; next }
    in_run { sub(/^          /, ""); print }
  ' "$WORKFLOW")
  if [ -z "$ci_step" ]; then
    echo 'FAIL: 서버 히스토리 검사 실행 본문을 찾지 못함'
    return 2
  fi

  (cd "$fixture" && bash -c "$ci_step")
}

run_case() {
  local label=$1
  local expected=$2
  local expected_marker=$3
  local fixture=$4
  shift 4
  local output rc=0

  output="$(cd "$fixture" && "$@" 2>&1)" || rc=$?
  checked=$((checked + 1))

  if [ "$expected" = pass ] && [ "$rc" -eq 0 ]; then
    printf '[%d/%d] %s -> PASS (exit=0)\n' "$checked" "$TOTAL" "$label"
    return
  fi
  if [ "$expected" = blocked ] && [ "$rc" -ne 0 ] \
     && printf '%s\n' "$output" | grep -Fq -- "$expected_marker"; then
    printf '[%d/%d] %s -> BLOCKED (exit=%d)\n' "$checked" "$TOTAL" "$label" "$rc"
    return
  fi

  printf '[%d/%d] %s -> UNEXPECTED (exit=%d, expected=%s)\n' \
    "$checked" "$TOTAL" "$label" "$rc" "$expected"
  printf '%s\n' "$output"
  failed=$((failed + 1))
}

if [ -z "${AC19_PATTERN_ENV_PROBE:-}" ] \
   && [ -z "${AC19_INNER_HOOK_PROBE:-}" ] \
   && [ -z "${AC19_COUNT_MISMATCH_PROBE:-}" ]; then
  run_case 'SECRET_PATTERNS_FILE=/dev/null 상속을 격리' pass '' "$ROOT" \
    env SECRET_PATTERNS_FILE=/dev/null AC19_PATTERN_ENV_PROBE=1 bash "$SELF"
  run_case 'SECRET_PATTERNS_FILE=.secret-patterns.default 상속을 격리' pass '' "$ROOT" \
    env SECRET_PATTERNS_FILE=.secret-patterns.default AC19_PATTERN_ENV_PROBE=1 bash "$SELF"
fi

harmless="$TMP/harmless"
make_fixture "$harmless"
printf 'harmless unreachable object\n' |
  git -C "$harmless" hash-object -w --stdin >/dev/null
run_case '일반 실행은 무해한 unreachable blob을 허용' pass '' "$harmless" \
  bash scripts/acceptance-0-2.sh

if [ -z "${AC19_PATTERN_ENV_PROBE:-}" ] && [ -z "${AC19_COUNT_MISMATCH_PROBE:-}" ]; then
tainted="$TMP/tainted"
make_fixture "$tainted"
printf '%s\n' "$CANARY" |
  git -C "$tainted" hash-object -w --stdin >/dev/null
run_case '일반 실행은 금지값이 든 unreachable blob을 차단' blocked \
  'FAIL: unreachable blob에 리터럴 잔존' "$tainted" \
  bash scripts/acceptance-0-2.sh

tainted_commit="$TMP/tainted-commit"
make_fixture "$tainted_commit"
tainted_commit_tree=$(git -C "$tainted_commit" rev-parse 'HEAD^{tree}')
printf '%s\n' "$CANARY" |
  git -C "$tainted_commit" commit-tree "$tainted_commit_tree" >/dev/null
run_case 'unreachable commit message의 금지값을 차단' blocked \
  'FAIL: unreachable commit에 리터럴 잔존' "$tainted_commit" \
  bash scripts/acceptance-0-2.sh

tainted_tree="$TMP/tainted-tree"
make_fixture "$tainted_tree"
tainted_tree_blob=$(printf 'harmless tree payload\n' |
  git -C "$tainted_tree" hash-object -w --stdin)
printf '100644 blob %s\tpath-%s.txt\n' "$tainted_tree_blob" "$CANARY" |
  git -C "$tainted_tree" mktree >/dev/null
run_case 'unreachable tree path의 금지값을 차단' blocked \
  'FAIL: unreachable tree에 리터럴 잔존' "$tainted_tree" \
  bash scripts/acceptance-0-2.sh

tainted_tag="$TMP/tainted-tag"
make_fixture "$tainted_tag"
tainted_tag_target=$(git -C "$tainted_tag" rev-parse HEAD)
printf 'object %s\ntype commit\ntag ac19-probe\ntagger acceptance <acceptance@example.invalid> 1 +0000\n\n%s\n' \
  "$tainted_tag_target" "$CANARY" | git -C "$tainted_tag" mktag >/dev/null
run_case 'unreachable annotated tag message의 금지값을 차단' blocked \
  'FAIL: unreachable tag에 리터럴 잔존' "$tainted_tag" \
  bash scripts/acceptance-0-2.sh

fsck_failure="$TMP/fsck-failure"
make_fixture "$fsck_failure"
mkdir -p "$fsck_failure/bin"
printf '%s\n' '#!/usr/bin/env bash' \
  'if [ "${1:-}" = fsck ]; then exit 72; fi' \
  'exec "$REAL_GIT" "$@"' > "$fsck_failure/bin/git"
chmod +x "$fsck_failure/bin/git"
run_case 'git fsck 실패는 검사 대상 없음으로 통과하지 않음' blocked \
  'FAIL: git fsck 실행 실패' "$fsck_failure" \
  env PATH="$fsck_failure/bin:$PATH" REAL_GIT="$REAL_GIT" \
  bash scripts/acceptance-0-2.sh

read_failure="$TMP/read-failure"
make_fixture "$read_failure"
read_failure_sha=$(printf 'harmless unreachable object\n' |
  git -C "$read_failure" hash-object -w --stdin)
mkdir -p "$read_failure/bin"
printf '%s\n' '#!/usr/bin/env bash' \
  'if [ "${1:-}" = cat-file ] && [ "${3:-}" = "${FAIL_CAT_FILE_SHA:-}" ]; then exit 71; fi' \
  'exec "$REAL_GIT" "$@"' > "$read_failure/bin/git"
chmod +x "$read_failure/bin/git"
run_case 'unreachable 객체 읽기 실패는 조용히 통과하지 않음' blocked \
  'FAIL: unreachable blob 읽기 실패' "$read_failure" \
  env PATH="$read_failure/bin:$PATH" REAL_GIT="$REAL_GIT" \
  FAIL_CAT_FILE_SHA="$read_failure_sha" bash scripts/acceptance-0-2.sh

unknown_type="$TMP/unknown-type"
make_fixture "$unknown_type"
unknown_type_sha=$(git -C "$unknown_type" rev-parse HEAD)
mkdir -p "$unknown_type/bin"
printf '%s\n' '#!/usr/bin/env bash' \
  'if [ "${1:-}" = fsck ]; then' \
  '  "$REAL_GIT" "$@" || exit $?' \
  '  printf "unreachable mystery %s\\n" "$FAIL_UNKNOWN_SHA"' \
  '  exit 0' \
  'fi' \
  'exec "$REAL_GIT" "$@"' > "$unknown_type/bin/git"
chmod +x "$unknown_type/bin/git"
run_case '알 수 없는 unreachable 객체형은 읽기 실패로 차단' blocked \
  'FAIL: unreachable mystery 읽기 실패' "$unknown_type" \
  env PATH="$unknown_type/bin:$PATH" REAL_GIT="$REAL_GIT" \
  FAIL_UNKNOWN_SHA="$unknown_type_sha" bash scripts/acceptance-0-2.sh

large_tainted="$TMP/large-tainted"
make_fixture "$large_tainted"
{ printf '%s\n' "$CANARY"; dd if=/dev/zero bs=1048576 count=50 2>/dev/null; } |
  git -C "$large_tainted" hash-object -w --stdin >/dev/null
run_case '큰 unreachable blob 앞쪽의 금지값도 차단' blocked \
  'FAIL: unreachable blob에 리터럴 잔존' "$large_tainted" \
  bash scripts/acceptance-0-2.sh

reachable_small="$TMP/reachable-small"
make_fixture "$reachable_small"
reachable_small_sha=$(printf '%s\n' "$CANARY" |
  git -C "$reachable_small" hash-object -w --stdin)
git -C "$reachable_small" tag ac19-reachable-small "$reachable_small_sha"
run_case '직접 참조가 가리키는 작은 blob의 금지값을 차단' blocked \
  'FAIL: 도달 가능 blob에 리터럴 잔존' "$reachable_small" \
  bash scripts/acceptance-0-2.sh

reachable_large="$TMP/reachable-large"
make_fixture "$reachable_large"
reachable_large_sha=$({ printf '%s\n' "$CANARY"; dd if=/dev/zero bs=1048576 count=50 2>/dev/null; } |
  git -C "$reachable_large" hash-object -w --stdin)
git -C "$reachable_large" tag ac19-reachable-large "$reachable_large_sha"
run_case '직접 참조가 가리키는 50MiB blob 앞쪽의 금지값을 차단' blocked \
  'FAIL: 도달 가능 blob에 리터럴 잔존' "$reachable_large" \
  bash scripts/acceptance-0-2.sh

reachable_read_failure="$TMP/reachable-read-failure"
make_fixture "$reachable_read_failure"
reachable_read_failure_sha=$(printf '%s\n' "$CANARY" |
  git -C "$reachable_read_failure" hash-object -w --stdin)
git -C "$reachable_read_failure" tag ac19-reachable-read-failure "$reachable_read_failure_sha"
mkdir -p "$reachable_read_failure/bin"
printf '%s\n' '#!/usr/bin/env bash' \
  'if [ "${1:-}" = cat-file ] && [ "${2:-}" = blob ] && [ "${3:-}" = "${FAIL_REACHABLE_CAT_FILE_SHA:-}" ]; then exit 71; fi' \
  'exec "$REAL_GIT" "$@"' > "$reachable_read_failure/bin/git"
chmod +x "$reachable_read_failure/bin/git"
run_case '도달 가능한 blob 읽기 실패를 값 없음으로 통과하지 않음' blocked \
  'FAIL: 도달 가능 blob 읽기 실패' "$reachable_read_failure" \
  env PATH="$reachable_read_failure/bin:$PATH" REAL_GIT="$REAL_GIT" \
  FAIL_REACHABLE_CAT_FILE_SHA="$reachable_read_failure_sha" bash scripts/acceptance-0-2.sh

ci_reachable_small="$TMP/ci-reachable-small"
make_fixture "$ci_reachable_small"
ci_reachable_small_sha=$(printf '%s\n' "$CANARY" |
  git -C "$ci_reachable_small" hash-object -w --stdin)
git -C "$ci_reachable_small" tag ac19-ci-reachable-small "$ci_reachable_small_sha"
run_case '서버 본문도 직접 참조의 작은 blob 금지값을 차단' blocked \
  'FAIL: 히스토리 blob에 자격증명 패턴 매치' "$ci_reachable_small" \
  run_ci_history_scan "$ci_reachable_small"

ci_reachable_large="$TMP/ci-reachable-large"
make_fixture "$ci_reachable_large"
ci_reachable_large_sha=$({ printf '%s\n' "$CANARY"; dd if=/dev/zero bs=1048576 count=50 2>/dev/null; } |
  git -C "$ci_reachable_large" hash-object -w --stdin)
git -C "$ci_reachable_large" tag ac19-ci-reachable-large "$ci_reachable_large_sha"
run_case '서버 본문도 직접 참조의 50MiB blob 금지값을 차단' blocked \
  'FAIL: 히스토리 blob에 자격증명 패턴 매치' "$ci_reachable_large" \
  run_ci_history_scan "$ci_reachable_large"

ci_read_failure="$TMP/ci-read-failure"
make_fixture "$ci_read_failure"
ci_read_failure_sha=$(printf '%s\n' "$CANARY" |
  git -C "$ci_read_failure" hash-object -w --stdin)
git -C "$ci_read_failure" tag ac19-ci-read-failure "$ci_read_failure_sha"
mkdir -p "$ci_read_failure/bin"
printf '%s\n' '#!/usr/bin/env bash' \
  'if [ "${1:-}" = cat-file ] && [ "${2:-}" = blob ] && [ "${3:-}" = "${FAIL_REACHABLE_CAT_FILE_SHA:-}" ]; then exit 71; fi' \
  'exec "$REAL_GIT" "$@"' > "$ci_read_failure/bin/git"
chmod +x "$ci_read_failure/bin/git"
PATH="$ci_read_failure/bin:$PATH" REAL_GIT="$REAL_GIT" \
FAIL_REACHABLE_CAT_FILE_SHA="$ci_read_failure_sha" \
run_case '서버 본문도 blob 읽기 실패를 값 없음으로 통과하지 않음' blocked \
  'FAIL: 히스토리 blob 읽기 실패' "$ci_read_failure" \
  run_ci_history_scan "$ci_read_failure"

# 패턴이 깨져 내용 대조 자체가 성립하지 않아도 값 없음으로 통과하면 안 된다.
#
# 표면화되는 사유는 grep 구현에 따라 다르다(2026-08-21 양쪽 실측).
#   macOS(BSD grep)  : 깨진 정규식이면 입력을 읽기 전에 끝나 파이프의 읽는 쪽이 사라지고,
#                      쓰는 쪽 cat-file 이 종료값 141 로 죽는다 → "blob 읽기 실패"
#   리눅스(GNU grep) : 같은 상황에서 cat-file 이 정상 종료하고 grep 만 종료값 2 를 낸다
#                      → "blob 내용 대조 실패"
# 계약은 "어느 쪽 사유로든 반드시 차단한다" 이므로 두 사유의 공통 앞부분으로 대조한다.
# 'FAIL: 히스토리 blob ' 뒤에 공백이 있어 매치 보고("...blob에 자격증명...")와 겹치지 않는다.
ci_pattern_error="$TMP/ci-pattern-error"
make_fixture "$ci_pattern_error"
printf '%s\n' '[' > "$ci_pattern_error/.secret-patterns.default"
run_case '서버 본문도 대조 불능 패턴을 값 없음으로 통과하지 않음' blocked \
  'FAIL: 히스토리 blob ' "$ci_pattern_error" \
  run_ci_history_scan "$ci_pattern_error"

# 위 사례는 grep 구현에 따라 두 사유 중 하나로 갈린다. 내용 대조 실패(종료값 2) 경로를
# 플랫폼과 무관하게 덮기 위해, 입력을 끝까지 읽은 뒤 2 로 끝나는 grep 대역을 쓴다.
# 이것이 리눅스(GNU grep)에서 실제로 관측된 조합이다: cat-file 은 0, grep 만 2.
ci_grep_error="$TMP/ci-grep-error"
make_fixture "$ci_grep_error"
ci_grep_error_sha=$(printf '%s\n' "$CANARY" |
  git -C "$ci_grep_error" hash-object -w --stdin)
git -C "$ci_grep_error" tag ac19-ci-grep-error "$ci_grep_error_sha"
mkdir -p "$ci_grep_error/bin"
printf '%s\n' '#!/usr/bin/env bash' \
  'for a in "$@"; do case "$a" in -*a*E*i*f*) cat >/dev/null; exit 2;; esac; done' \
  'exec "$REAL_GREP" "$@"' > "$ci_grep_error/bin/grep"
chmod +x "$ci_grep_error/bin/grep"
PATH="$ci_grep_error/bin:$PATH" REAL_GREP="$REAL_GREP" \
run_case '서버 본문도 내용 대조 실패를 값 없음으로 통과하지 않음' blocked \
  'FAIL: 히스토리 blob 내용 대조 실패' "$ci_grep_error" \
  run_ci_history_scan "$ci_grep_error"

endstate="$TMP/endstate"
make_fixture "$endstate"
printf 'harmless unreachable object\n' |
  git -C "$endstate" hash-object -w --stdin >/dev/null
run_case '종료상태 실행은 무해한 unreachable blob도 차단' blocked \
  'FAIL: unreachable 객체' "$endstate" \
  env ACCEPTANCE_ENDSTATE=1 bash scripts/acceptance-0-2.sh

if [ -z "${AC19_INNER_HOOK_PROBE:-}" ]; then
  run_case '예정 사례 수와 실제 실행 수가 다르면 전체를 차단' blocked \
    'FAIL: AC-19 실행 사례 수 불일치' "$ROOT" \
    env AC19_COUNT_MISMATCH_PROBE=1 bash "$SELF"

  hook_outer="$TMP/hook-env-outer"
  mkdir -p "$hook_outer/scripts" "$hook_outer/docs" "$hook_outer/.github/workflows"
  cp "$TARGET" "$hook_outer/scripts/acceptance-0-2.sh"
  cp "$SELF" "$hook_outer/scripts/acceptance-0-2-unreachable-content.sh"
  cp "$VERIFY" "$hook_outer/verify.sh"
  cp "$WORKFLOW" "$hook_outer/.github/workflows/verify.yml"
  printf '.secret-patterns\nouter-only-ignore\n' > "$hook_outer/.gitignore"
  printf '%s\n' "$CANARY" > "$hook_outer/.secret-patterns"
  printf 'outer repository sentinel\n' > "$hook_outer/docs/README.md"
  git -C "$hook_outer" init -q -b main
  git -C "$hook_outer" config user.email acceptance@local
  git -C "$hook_outer" config user.name acceptance
  git -C "$hook_outer" add .gitignore .github docs/README.md scripts verify.sh
  git -C "$hook_outer" commit -qm outer-fixture

  hook_before_head=$(git -C "$hook_outer" rev-parse HEAD)
  hook_before_status=$(git -C "$hook_outer" status --porcelain --untracked-files=all)
  hook_git_dir=$(git -C "$hook_outer" rev-parse --absolute-git-dir)
  hook_rc=0
  hook_output=$(cd "$hook_outer" && env -u GIT_WORK_TREE GIT_DIR="$hook_git_dir" \
    AC19_INNER_HOOK_PROBE=1 bash scripts/acceptance-0-2-unreachable-content.sh 2>&1) || hook_rc=$?
  hook_after_head=$(git -C "$hook_outer" rev-parse HEAD)
  hook_after_status=$(git -C "$hook_outer" status --porcelain --untracked-files=all)
  checked=$((checked + 1))
  if [ "$hook_rc" -eq 0 ] \
     && [ "$hook_before_head" = "$hook_after_head" ] \
     && [ "$hook_before_status" = "$hook_after_status" ]; then
    printf '[%d/%d] Git hook 환경에서도 바깥 저장소 무오염 -> PASS (exit=0)\n' \
      "$checked" "$TOTAL"
  else
    printf '[%d/%d] Git hook 환경에서도 바깥 저장소 무오염 -> UNEXPECTED' \
      "$checked" "$TOTAL"
    printf ' (exit=%d, head_same=%s, status_same=%s)\n' "$hook_rc" \
      "$([ "$hook_before_head" = "$hook_after_head" ] && printf YES || printf NO)" \
      "$([ "$hook_before_status" = "$hook_after_status" ] && printf YES || printf NO)"
    printf '%s\n' "$hook_output"
    failed=$((failed + 1))
  fi
fi
fi

printf 'CHECKED: %d\n' "$checked"
if [ "$checked" -ne "$TOTAL" ]; then
  printf 'FAIL: AC-19 실행 사례 수 불일치 (expected=%d, actual=%d)\n' "$TOTAL" "$checked"
  failed=$((failed + 1))
fi
if [ "$failed" -ne 0 ]; then
  printf 'FAIL: AC-19 예상과 다른 사례 %d건\n' "$failed"
  exit 1
fi

printf 'PASS: AC-19 일반 내용 검사와 종료상태 0건 조건 분리\n'
