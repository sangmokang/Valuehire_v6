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
REAL_GIT=$(command -v git)
TMP=$(mktemp -d)
trap 'rm -rf -- "$TMP"' EXIT

CANARY='AC19-CANARY-8842'
if [ -n "${AC19_PATTERN_ENV_PROBE:-}" ]; then
  TOTAL=1
elif [ -n "${AC19_INNER_HOOK_PROBE:-}" ]; then
  TOTAL=10
else
  TOTAL=13
fi
checked=0
failed=0

make_fixture() {
  local fixture=$1

  mkdir -p "$fixture/scripts" "$fixture/docs"
  cp "$TARGET" "$fixture/scripts/acceptance-0-2.sh"
  cp "$VERIFY" "$fixture/verify.sh"
  printf '.secret-patterns\n' > "$fixture/.gitignore"
  printf '%s\n' "$CANARY" > "$fixture/.secret-patterns"
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

run_case() {
  local label=$1
  local expected=$2
  local fixture=$3
  shift 3
  local output rc=0

  output="$(cd "$fixture" && "$@" 2>&1)" || rc=$?
  checked=$((checked + 1))

  if [ "$expected" = pass ] && [ "$rc" -eq 0 ]; then
    printf '[%d/%d] %s -> PASS (exit=0)\n' "$checked" "$TOTAL" "$label"
    return
  fi
  if [ "$expected" = blocked ] && [ "$rc" -ne 0 ]; then
    printf '[%d/%d] %s -> BLOCKED (exit=%d)\n' "$checked" "$TOTAL" "$label" "$rc"
    return
  fi

  printf '[%d/%d] %s -> UNEXPECTED (exit=%d, expected=%s)\n' \
    "$checked" "$TOTAL" "$label" "$rc" "$expected"
  printf '%s\n' "$output"
  failed=$((failed + 1))
}

if [ -z "${AC19_PATTERN_ENV_PROBE:-}" ] && [ -z "${AC19_INNER_HOOK_PROBE:-}" ]; then
  run_case 'SECRET_PATTERNS_FILE=/dev/null 상속을 격리' pass "$ROOT" \
    env SECRET_PATTERNS_FILE=/dev/null AC19_PATTERN_ENV_PROBE=1 bash "$SELF"
  run_case 'SECRET_PATTERNS_FILE=.secret-patterns.default 상속을 격리' pass "$ROOT" \
    env SECRET_PATTERNS_FILE=.secret-patterns.default AC19_PATTERN_ENV_PROBE=1 bash "$SELF"
fi

harmless="$TMP/harmless"
make_fixture "$harmless"
printf 'harmless unreachable object\n' |
  git -C "$harmless" hash-object -w --stdin >/dev/null
run_case '일반 실행은 무해한 unreachable blob을 허용' pass "$harmless" \
  bash scripts/acceptance-0-2.sh

if [ -z "${AC19_PATTERN_ENV_PROBE:-}" ]; then
tainted="$TMP/tainted"
make_fixture "$tainted"
printf '%s\n' "$CANARY" |
  git -C "$tainted" hash-object -w --stdin >/dev/null
run_case '일반 실행은 금지값이 든 unreachable blob을 차단' blocked "$tainted" \
  bash scripts/acceptance-0-2.sh

tainted_commit="$TMP/tainted-commit"
make_fixture "$tainted_commit"
tainted_commit_tree=$(git -C "$tainted_commit" rev-parse 'HEAD^{tree}')
printf '%s\n' "$CANARY" |
  git -C "$tainted_commit" commit-tree "$tainted_commit_tree" >/dev/null
run_case 'unreachable commit message의 금지값을 차단' blocked "$tainted_commit" \
  bash scripts/acceptance-0-2.sh

tainted_tree="$TMP/tainted-tree"
make_fixture "$tainted_tree"
tainted_tree_blob=$(printf 'harmless tree payload\n' |
  git -C "$tainted_tree" hash-object -w --stdin)
printf '100644 blob %s\tpath-%s.txt\n' "$tainted_tree_blob" "$CANARY" |
  git -C "$tainted_tree" mktree >/dev/null
run_case 'unreachable tree path의 금지값을 차단' blocked "$tainted_tree" \
  bash scripts/acceptance-0-2.sh

tainted_tag="$TMP/tainted-tag"
make_fixture "$tainted_tag"
tainted_tag_target=$(git -C "$tainted_tag" rev-parse HEAD)
printf 'object %s\ntype commit\ntag ac19-probe\ntagger acceptance <acceptance@example.invalid> 1 +0000\n\n%s\n' \
  "$tainted_tag_target" "$CANARY" | git -C "$tainted_tag" mktag >/dev/null
run_case 'unreachable annotated tag message의 금지값을 차단' blocked "$tainted_tag" \
  bash scripts/acceptance-0-2.sh

fsck_failure="$TMP/fsck-failure"
make_fixture "$fsck_failure"
mkdir -p "$fsck_failure/bin"
printf '%s\n' '#!/usr/bin/env bash' \
  'if [ "${1:-}" = fsck ]; then exit 72; fi' \
  'exec "$REAL_GIT" "$@"' > "$fsck_failure/bin/git"
chmod +x "$fsck_failure/bin/git"
run_case 'git fsck 실패는 검사 대상 없음으로 통과하지 않음' blocked "$fsck_failure" \
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
run_case 'unreachable 객체 읽기 실패는 조용히 통과하지 않음' blocked "$read_failure" \
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
run_case '알 수 없는 unreachable 객체형은 읽기 실패로 차단' blocked "$unknown_type" \
  env PATH="$unknown_type/bin:$PATH" REAL_GIT="$REAL_GIT" \
  FAIL_UNKNOWN_SHA="$unknown_type_sha" bash scripts/acceptance-0-2.sh

large_tainted="$TMP/large-tainted"
make_fixture "$large_tainted"
{ printf '%s\n' "$CANARY"; dd if=/dev/zero bs=1048576 count=50 2>/dev/null; } |
  git -C "$large_tainted" hash-object -w --stdin >/dev/null
run_case '큰 unreachable blob 앞쪽의 금지값도 차단' blocked "$large_tainted" \
  bash scripts/acceptance-0-2.sh

endstate="$TMP/endstate"
make_fixture "$endstate"
printf 'harmless unreachable object\n' |
  git -C "$endstate" hash-object -w --stdin >/dev/null
run_case '종료상태 실행은 무해한 unreachable blob도 차단' blocked "$endstate" \
  env ACCEPTANCE_ENDSTATE=1 bash scripts/acceptance-0-2.sh

if [ -z "${AC19_INNER_HOOK_PROBE:-}" ]; then
  hook_outer="$TMP/hook-env-outer"
  mkdir -p "$hook_outer/scripts" "$hook_outer/docs"
  cp "$TARGET" "$hook_outer/scripts/acceptance-0-2.sh"
  cp "$SELF" "$hook_outer/scripts/acceptance-0-2-unreachable-content.sh"
  cp "$VERIFY" "$hook_outer/verify.sh"
  printf '.secret-patterns\nouter-only-ignore\n' > "$hook_outer/.gitignore"
  printf '%s\n' "$CANARY" > "$hook_outer/.secret-patterns"
  printf 'outer repository sentinel\n' > "$hook_outer/docs/README.md"
  git -C "$hook_outer" init -q -b main
  git -C "$hook_outer" config user.email acceptance@local
  git -C "$hook_outer" config user.name acceptance
  git -C "$hook_outer" add .gitignore docs/README.md scripts verify.sh
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
if [ "$failed" -ne 0 ]; then
  printf 'FAIL: AC-19 예상과 다른 사례 %d건\n' "$failed"
  exit 1
fi

printf 'PASS: AC-19 일반 내용 검사와 종료상태 0건 조건 분리\n'
