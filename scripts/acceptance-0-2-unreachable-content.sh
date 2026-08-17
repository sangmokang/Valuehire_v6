#!/usr/bin/env bash
# AC-19 — acceptance-0-2의 상시 내용 검사와 일회성 종료상태 검사를 분리한다.
set -euo pipefail

ROOT=$(git rev-parse --show-toplevel)
TARGET="$ROOT/scripts/acceptance-0-2.sh"
VERIFY="$ROOT/verify.sh"
REAL_GIT=$(command -v git)
TMP=$(mktemp -d)
trap 'rm -rf -- "$TMP"' EXIT

CANARY='AC19-CANARY-8842'
TOTAL=5
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

harmless="$TMP/harmless"
make_fixture "$harmless"
printf 'harmless unreachable object\n' |
  git -C "$harmless" hash-object -w --stdin >/dev/null
run_case '일반 실행은 무해한 unreachable blob을 허용' pass "$harmless" \
  bash scripts/acceptance-0-2.sh

tainted="$TMP/tainted"
make_fixture "$tainted"
printf '%s\n' "$CANARY" |
  git -C "$tainted" hash-object -w --stdin >/dev/null
run_case '일반 실행은 금지값이 든 unreachable blob을 차단' blocked "$tainted" \
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

printf 'CHECKED: %d\n' "$checked"
if [ "$failed" -ne 0 ]; then
  printf 'FAIL: AC-19 예상과 다른 사례 %d건\n' "$failed"
  exit 1
fi

printf 'PASS: AC-19 일반 내용 검사와 종료상태 0건 조건 분리\n'
