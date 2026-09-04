#!/usr/bin/env bash
# 줄 허용 목록의 단일 항목 소비, 내용 결속, 이동 허용, 만료, 두 스캔 모드를 격리 저장소에서 검증한다.
# 시험값은 런타임에 조립하며 이 파일이나 주석에 완성된 값을 기록하지 않는다.
set -uo pipefail

unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE GIT_OBJECT_DIRECTORY \
  GIT_ALTERNATE_OBJECT_DIRECTORIES GIT_COMMON_DIR GIT_PREFIX GIT_QUARANTINE_PATH

REPO=$(git rev-parse --show-toplevel 2>/dev/null) || {
  echo "NOT_RUN: git 저장소가 아니다"
  echo "CHECKED: 0"
  exit 2
}
cd "$REPO" || {
  echo "NOT_RUN: 저장소 루트로 이동하지 못했다"
  echo "CHECKED: 0"
  exit 2
}

VERIFY=$REPO/verify.sh
PATTERNS=$REPO/.secret-patterns.default
EXPECTED_CHECKS=33
SNAP0=$(git status --porcelain)

if [ ! -x /usr/bin/grep ] || [ ! -f "$VERIFY" ] || [ ! -s "$PATTERNS" ]; then
  echo "NOT_RUN: /usr/bin/grep, verify.sh, 기본 패턴 중 하나를 읽을 수 없다"
  echo "CHECKED: 0"
  exit 2
fi

TMP=$(mktemp -d) || {
  echo "NOT_RUN: 저장소 밖 임시 디렉터리를 만들지 못했다"
  echo "CHECKED: 0"
  exit 2
}
cleanup() { rm -rf "$TMP"; }
trap cleanup EXIT
trap 'cleanup; trap - EXIT; exit 143' TERM
trap 'cleanup; trap - EXIT; exit 130' INT
trap 'cleanup; trap - EXIT; exit 129' HUP

CLEAN=$TMP/patterns.clean
tr -d '\r' < "$PATTERNS" | /usr/bin/grep -vE '^[[:space:]]*(#|$)' > "$CLEAN"
if [ ! -s "$CLEAN" ]; then
  echo "NOT_RUN: 유효한 기본 패턴이 0개다"
  echo "CHECKED: 0"
  exit 2
fi

KEY=$(printf '%s%s' 'PASS' 'WORD')
VALUE=$(printf '%s%s' 'abc1' '23xy')
CANARY=$(printf '%s=%s' "$KEY" "$VALUE")
MUTATED=$(printf '%sz' "${CANARY%?}")
SAFE=$(printf '%s%s' 'ordinary-' 'configuration')
SELF_MATCH=$(printf '%s%s' 'AKIA' '0123456789ABCDEF')

# 어떤 MISSED도 허용 증거로 세기 전에 현재 패턴이 양성 대조군을 실제로 잡는지 확인한다.
if ! printf '%s\n' "$CANARY" | /usr/bin/grep -qEif "$CLEAN"; then
  echo "NOT_RUN: 양성 대조군을 /usr/bin/grep이 잡지 못했다"
  echo "CHECKED: 0"
  exit 2
fi

hash_line() { printf '%s' "$1" | git hash-object --stdin; }

write_allowlist() {
  local repo="$1" path="$2" hash="$3" kind="$4"
  case "$kind" in
    valid)
      printf '%s\n' \
        '- path: "'"$path"'"' \
        '  line_hash: "'"$hash"'"' \
        '  reason: "synthetic acceptance exception"' \
        '  owner: "acceptance"' \
        '  expiry: "2099-12-31"' > "$repo/.secret-allowlist.yaml"
      ;;
    no-expiry)
      printf '%s\n' \
        '- path: "'"$path"'"' \
        '  line_hash: "'"$hash"'"' \
        '  reason: "synthetic acceptance exception"' \
        '  owner: "acceptance"' > "$repo/.secret-allowlist.yaml"
      ;;
    expired)
      printf '%s\n' \
        '- path: "'"$path"'"' \
        '  line_hash: "'"$hash"'"' \
        '  reason: "synthetic acceptance exception"' \
        '  owner: "acceptance"' \
        '  expiry: "2000-01-01"' > "$repo/.secret-allowlist.yaml"
      ;;
    syntax)
      printf '%s\n' \
        '- path: "'"$path"'"' \
        '  line_hash: "'"$hash"'"' \
        '  reason: "synthetic acceptance exception"' \
        '  owner: "acceptance"' \
        '  expiry: 2099-12-31' > "$repo/.secret-allowlist.yaml"
      ;;
    missing) ;;
    *) return 2 ;;
  esac
}

make_regular_repo() {
  local name="$1" payload="$2" allow_hash="$3" allow_kind="$4"
  CASE_REPO=$TMP/$name
  mkdir -p "$CASE_REPO"
  git init -q "$CASE_REPO"
  cp "$VERIFY" "$CASE_REPO/verify.sh"
  cp "$PATTERNS" "$CASE_REPO/.secret-patterns.default"
  printf '%s' "$payload" > "$CASE_REPO/payload.txt"
  write_allowlist "$CASE_REPO" payload.txt "$allow_hash" "$allow_kind" || return 2
  (
    cd "$CASE_REPO" || exit 2
    git config user.email acceptance@local
    git config user.name acceptance
    git add -A
    git commit -qm fixture
  )
}

make_symlink_repo() {
  local name="$1" link_target="$2" outside_content="$3"
  CASE_REPO=$TMP/$name/repo
  mkdir -p "$CASE_REPO"
  git init -q "$CASE_REPO"
  cp "$VERIFY" "$CASE_REPO/verify.sh"
  cp "$PATTERNS" "$CASE_REPO/.secret-patterns.default"
  printf '%s\n' "$outside_content" > "$TMP/$name/outside.txt"
  ln -s "$link_target" "$CASE_REPO/link.txt"
  write_allowlist "$CASE_REPO" link.txt "$(hash_line "$SAFE")" valid || return 2
  (
    cd "$CASE_REPO" || exit 2
    git config user.email acceptance@local
    git config user.name acceptance
    git add -A
    git commit -qm fixture
  )
}

make_self_target_repo() {
  local reason_line hash
  CASE_REPO=$TMP/self-target
  mkdir -p "$CASE_REPO"
  git init -q "$CASE_REPO"
  cp "$VERIFY" "$CASE_REPO/verify.sh"
  cp "$PATTERNS" "$CASE_REPO/.secret-patterns.default"
  reason_line=$(printf '  reason: "%s"' "$SELF_MATCH")
  hash=$(hash_line "$reason_line")
  printf '%s\n' \
    '- path: ".secret-allowlist.yaml"' \
    '  line_hash: "'"$hash"'"' \
    "$reason_line" \
    '  owner: "acceptance"' \
    '  expiry: "2099-12-31"' > "$CASE_REPO/.secret-allowlist.yaml"
  (
    cd "$CASE_REPO" || exit 2
    git config user.email acceptance@local
    git config user.name acceptance
    git add -A
    git commit -qm fixture
  )
}

make_allowlist_source_symlink_repo() {
  local outside=$TMP/allowlist-policy.external
  CASE_REPO=$TMP/allowlist-source-symlink
  mkdir -p "$CASE_REPO"
  git init -q "$CASE_REPO"
  cp "$VERIFY" "$CASE_REPO/verify.sh"
  cp "$PATTERNS" "$CASE_REPO/.secret-patterns.default"
  printf '%s' "$CANARY" > "$CASE_REPO/payload.txt"
  write_allowlist "$CASE_REPO" payload.txt "$(hash_line "$CANARY")" valid || return 2
  (
    cd "$CASE_REPO" || exit 2
    git config user.email acceptance@local
    git config user.name acceptance
    git add -A
    git commit -qm fixture
  )
  mv "$CASE_REPO/.secret-allowlist.yaml" "$outside"
  ln -s "$outside" "$CASE_REPO/.secret-allowlist.yaml"
}

make_allowlist_parent_symlink_repo() {
  local outside=$TMP/allowlist-parent.external
  CASE_REPO=$TMP/allowlist-parent-symlink
  mkdir -p "$CASE_REPO/policy"
  git init -q "$CASE_REPO"
  cp "$VERIFY" "$CASE_REPO/verify.sh"
  cp "$PATTERNS" "$CASE_REPO/.secret-patterns.default"
  printf '%s' "$CANARY" > "$CASE_REPO/payload.txt"
  write_allowlist "$CASE_REPO" payload.txt "$(hash_line "$CANARY")" valid || return 2
  mv "$CASE_REPO/.secret-allowlist.yaml" "$CASE_REPO/policy/allowlist.yaml"
  (
    cd "$CASE_REPO" || exit 2
    git config user.email acceptance@local
    git config user.name acceptance
    git add -A
    git commit -qm fixture
  )
  mv "$CASE_REPO/policy" "$outside"
  ln -s "$outside" "$CASE_REPO/policy"
}

make_nul_mutation_repo() {
  CASE_REPO=$TMP/nul-mutation
  mkdir -p "$CASE_REPO"
  git init -q "$CASE_REPO"
  cp "$VERIFY" "$CASE_REPO/verify.sh"
  cp "$PATTERNS" "$CASE_REPO/.secret-patterns.default"
  printf '%s\0\n' "$CANARY" > "$CASE_REPO/payload.bin"
  write_allowlist "$CASE_REPO" payload.bin "$(hash_line "$CANARY")" valid || return 2
  (
    cd "$CASE_REPO" || exit 2
    git config user.email acceptance@local
    git config user.name acceptance
    git add -A
    git commit -qm fixture
  )
}

make_symlink_trailing_newline_repo() {
  local custom_patterns readlink_shim
  CASE_REPO=$TMP/symlink-trailing-newline
  mkdir -p "$CASE_REPO"
  git init -q "$CASE_REPO"
  cp "$VERIFY" "$CASE_REPO/verify.sh"
  custom_patterns=$CASE_REPO/.patterns.empty-line
  cp "$CLEAN" "$custom_patterns"
  printf '\n%s\n' '^$' >> "$custom_patterns"
  if ! printf '%s\n' "$CANARY" | /usr/bin/grep -qEif "$custom_patterns"; then
    return 2
  fi
  mkdir "$CASE_REPO/shims"
  readlink_shim=$CASE_REPO/shims/readlink
  printf '%s\n' \
    '#!/bin/sh' \
    'if [ "${1:-}" = -n ]; then exec /usr/bin/readlink "$@"; fi' \
    '/usr/bin/readlink "$@"' \
    "printf '\\n'" > "$readlink_shim"
  chmod +x "$readlink_shim"
  ln -s "$SAFE"$'\n' "$CASE_REPO/link.txt"
  write_allowlist "$CASE_REPO" link.txt "$(hash_line "$SAFE")" valid || return 2
  (
    cd "$CASE_REPO" || exit 2
    git config user.email acceptance@local
    git config user.name acceptance
    git add .secret-allowlist.yaml link.txt
    git commit -qm fixture
  )
}

checked=0
fail=0
unexpected_missed=0
mode_mismatch=0
LAST_RC=0

run_mode() {
  local desc="$1" repo="$2" mode="$3" want="$4" forbid_scanner_error="$5"
  local allowlist_source="${6:-.secret-allowlist.yaml}"
  local patterns_source="${7:-.secret-patterns.default}"
  local path_prefix="${8:-}"
  local out=$TMP/output.$checked rc=0 bad_reason=0
  (
    cd "$repo" || exit 2
    PATH="${path_prefix:+$path_prefix:}$PATH" \
      SECRET_PATTERNS_FILE="$patterns_source" \
      SECRET_ALLOWLIST_FILE="$allowlist_source" \
      VERIFY_SCAN_SOURCE="$mode" bash verify.sh
  ) > "$out" 2>&1
  rc=$?
  checked=$((checked + 1))

  if [ "$forbid_scanner_error" -eq 1 ] && /usr/bin/grep -qF 'scanner error' "$out"; then
    bad_reason=1
  fi
  if [ "$rc" -eq "$want" ] && [ "$bad_reason" -eq 0 ]; then
    printf '[%d/%d] %s (%s) -> PASS (exit=%d)\n' "$checked" "$EXPECTED_CHECKS" "$desc" "$mode" "$rc"
  else
    printf '[%d/%d] %s (%s) -> FAIL (expected=%d actual=%d scanner_error=%d)\n' \
      "$checked" "$EXPECTED_CHECKS" "$desc" "$mode" "$want" "$rc" "$bad_reason"
    sed 's/^/       /' "$out"
    fail=1
  fi
  if [ "$want" -eq 1 ] && [ "$rc" -eq 0 ]; then
    unexpected_missed=$((unexpected_missed + 1))
  fi
  LAST_RC=$rc
}

run_pair() {
  local desc="$1" repo="$2" want="$3" forbid_scanner_error="${4:-0}"
  local allowlist_source="${5:-.secret-allowlist.yaml}"
  local patterns_source="${6:-.secret-patterns.default}"
  local path_prefix="${7:-}" worktree_rc index_rc
  run_mode "$desc" "$repo" worktree "$want" "$forbid_scanner_error" \
    "$allowlist_source" "$patterns_source" "$path_prefix"
  worktree_rc=$LAST_RC
  run_mode "$desc" "$repo" index "$want" "$forbid_scanner_error" \
    "$allowlist_source" "$patterns_source" "$path_prefix"
  index_rc=$LAST_RC
  if [ "$worktree_rc" -ne "$index_rc" ]; then
    printf 'MODE_MISMATCH: %s worktree=%d index=%d\n' "$desc" "$worktree_rc" "$index_rc"
    mode_mismatch=$((mode_mismatch + 1))
    fail=1
  fi
}

# 1~2: 모든 나머지 정규식 판정보다 먼저 두 모드의 양성 대조군을 실제 스캐너로 확인한다.
make_regular_repo control "$CANARY" "$(hash_line "$SAFE")" valid || exit 2
run_pair "양성 대조군 탐지" "$CASE_REPO" 1

# 3~18: AC-ALLOWLIST-1의 여섯 항목과 각 슬래시 하위 경우를 두 모드에서 같은 입력으로 실행한다.
make_regular_repo allowed "$CANARY" "$(hash_line "$CANARY")" valid || exit 2
run_pair "등재된 정확한 한 줄" "$CASE_REPO" 0

make_regular_repo duplicate "$(printf '%s\n%s' "$CANARY" "$CANARY")" "$(hash_line "$CANARY")" valid || exit 2
run_pair "같은 파일의 같은 값 두 번째 줄" "$CASE_REPO" 1

make_regular_repo mutated "$MUTATED" "$(hash_line "$CANARY")" valid || exit 2
run_pair "등재된 줄 한 글자 변경" "$CASE_REPO" 1

make_regular_repo moved "$(printf '%s\n%s' "$SAFE" "$CANARY")" "$(hash_line "$CANARY")" valid || exit 2
run_pair "등재된 줄의 줄번호 이동" "$CASE_REPO" 0

make_regular_repo no-expiry "$CANARY" "$(hash_line "$CANARY")" no-expiry || exit 2
run_pair "expiry 누락" "$CASE_REPO" 2

make_regular_repo expired "$CANARY" "$(hash_line "$CANARY")" expired || exit 2
run_pair "expiry 만료" "$CASE_REPO" 2

make_regular_repo missing "$CANARY" "$(hash_line "$CANARY")" missing || exit 2
run_pair "허용 목록 파일 없음" "$CASE_REPO" 2

make_regular_repo syntax "$CANARY" "$(hash_line "$CANARY")" syntax || exit 2
run_pair "허용 목록 문법 위반" "$CASE_REPO" 2

# 19~20: 허용 목록이 자기 파일의 매치 줄을 지문으로 숨기는 자기제외 경로를 거부한다.
make_self_target_repo || exit 2
run_pair "허용 목록 자기 파일 target 거부" "$CASE_REPO" 2

# 21~22: 같은 허용 목록을 `./` 별칭으로 선택해도 자기 target 거부를 우회할 수 없다.
run_pair "허용 목록 자기 파일 경로 별칭 거부" "$CASE_REPO" 2 0 './.secret-allowlist.yaml'

# 23~24: 각 스캔 소스의 허용 목록 자체가 심볼릭 링크이면 저장소 밖 정책을 읽지 않고 닫혀야 한다.
make_allowlist_source_symlink_repo || exit 2
run_mode "worktree 허용 목록 외부 심볼릭 링크 거부" "$CASE_REPO" worktree 2 0
(
  cd "$CASE_REPO" || exit 2
  git add .secret-allowlist.yaml
) || exit 2
run_mode "index 허용 목록 심볼릭 링크 거부" "$CASE_REPO" index 2 0

# 25: 대체 허용 목록 경로의 상위 디렉터리도 외부 심볼릭 링크로 정책을 주입할 수 없다.
make_allowlist_parent_symlink_repo || exit 2
run_mode "worktree 허용 목록 상위 외부 심볼릭 링크 거부" \
  "$CASE_REPO" worktree 2 0 'policy/allowlist.yaml'

# 26~27: 허용한 텍스트 뒤에 NUL 한 바이트가 추가되면 셸 변수 축약으로 같은 줄처럼 보이면 안 된다.
make_nul_mutation_repo || exit 2
run_pair "등재된 줄 끝 NUL 한 바이트 추가" "$CASE_REPO" 1 1

# 28~31: worktree가 링크를 따라가고 index가 링크 문자열을 읽던 기존 갈림을 함께 회귀 고정한다.
make_symlink_repo symlink-follow ../outside.txt "$CANARY" || exit 2
run_pair "추적 심볼릭 링크의 바깥 내용은 비범위" "$CASE_REPO" 0 1

make_symlink_repo symlink-blob "$CANARY" "$SAFE" || exit 2
run_pair "추적 심볼릭 링크의 저장 문자열은 탐지" "$CASE_REPO" 1 1

# 32~33: 링크 대상 끝 개행과 readlink 표시용 개행을 구분해 두 모드가 같은 blob 바이트를 읽어야 한다.
make_symlink_trailing_newline_repo || exit 2
run_pair "끝 개행이 있는 링크 대상의 저장 바이트 동일성" \
  "$CASE_REPO" 0 1 .secret-allowlist.yaml .patterns.empty-line "$CASE_REPO/shims"

SNAP1=$(git status --porcelain)
if [ "$SNAP0" != "$SNAP1" ]; then
  echo "FAIL: 인수 검사가 원본 저장소 상태를 바꿨다"
  fail=1
fi
if [ "$checked" -ne "$EXPECTED_CHECKS" ]; then
  printf 'FAIL: 검사 수 %d != 계약값 %d\n' "$checked" "$EXPECTED_CHECKS"
  fail=1
fi

printf 'ALLOWED_LINES_COUNT=%d\n' 1
printf 'MODE_MISMATCH_COUNT=%d\n' "$mode_mismatch"
printf 'UNEXPECTED_MISSED_COUNT=%d\n' "$unexpected_missed"
printf 'CHECKED: %d\n' "$checked"

if [ "$fail" -eq 0 ] && [ "$mode_mismatch" -eq 0 ] && [ "$unexpected_missed" -eq 0 ]; then
  echo "PASS: 줄 내용 허용 목록과 두 스캔 모드가 AC-ALLOWLIST-1을 만족한다"
  exit 0
fi
echo "FAIL: AC-ALLOWLIST-1을 만족하지 못했다"
exit 1
