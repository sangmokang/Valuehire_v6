#!/usr/bin/env bash
# acceptance-history-scan-failclosed.sh — 히스토리 비밀 스캐너의 3상태 계약을 합성 저장소로 검증한다.
set -uo pipefail

unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE GIT_OBJECT_DIRECTORY \
  GIT_ALTERNATE_OBJECT_DIRECTORIES GIT_COMMON_DIR GIT_PREFIX GIT_QUARANTINE_PATH

ROOT=$(git rev-parse --show-toplevel 2>/dev/null) || {
  echo "NOT_RUN: git 저장소가 아니다"
  echo "CHECKED: 0"
  exit 2
}
cd "$ROOT" || {
  echo "NOT_RUN: 저장소 루트로 이동 실패"
  echo "CHECKED: 0"
  exit 2
}

SCANNER="$ROOT/scripts/scan-history-secrets.sh"
WORKFLOW="$ROOT/.github/workflows/verify.yml"
REAL_GIT=$(command -v git)
SNAPSHOT=$(git status --porcelain)
TMP=$(mktemp -d) || {
  echo "NOT_RUN: mktemp 실패"
  echo "CHECKED: 0"
  exit 2
}
case "$TMP" in
  /tmp/*|/private/tmp/*|/var/folders/*|/private/var/folders/*) ;;
  *) echo "NOT_RUN: 안전하지 않은 임시 경로 — $TMP"; echo "CHECKED: 0"; exit 2 ;;
esac
trap 'ruby -rfileutils -e "FileUtils.remove_entry(ARGV[0]) if File.exist?(ARGV[0])" "$TMP"' EXIT

CANARY='VH-HISTORY-SYNTH-CANARY-884211'
TOTAL=10
checked=0
failed=0

record() {
  local ok="$1" label="$2" detail="$3"
  checked=$((checked + 1))
  if [ "$ok" -eq 0 ]; then
    printf 'PASS: %s — %s\n' "$label" "$detail"
  else
    printf 'FAIL: %s — %s\n' "$label" "$detail"
    failed=1
  fi
}

make_fixture() {
  local fixture="$1"
  mkdir -p "$fixture"
  git -C "$fixture" init -q -b main
  git -C "$fixture" config user.email acceptance@example.invalid
  git -C "$fixture" config user.name acceptance
  printf '.secret-patterns.default\n' > "$fixture/.gitignore"
  printf '%s\n' "$CANARY" > "$fixture/.secret-patterns.default"
  printf 'clean synthetic content\n' > "$fixture/README.md"
  git -C "$fixture" add .gitignore README.md
  git -C "$fixture" commit -qm fixture
}

legacy_scan() {
  local fixture="$1" body raw_rc=0
  body=$(awk '
    /^      - name: 히스토리 전량 스캔/ { in_step=1; next }
    in_step && /^      - name:/ { exit }
    in_step && /^        run: \|/ { in_run=1; next }
    in_run { sub(/^          /, ""); print }
  ' "$WORKFLOW")
  if [ -z "$body" ]; then
    echo "NOT_RUN: 현재 워크플로의 히스토리 스캔 본문을 찾지 못했다"
    return 2
  fi

  (cd "$fixture" && bash -c "$body") || raw_rc=$?
  case "$raw_rc" in
    0) return 1 ;;
    1) return 0 ;;
    *) return 2 ;;
  esac
}

run_scanner() {
  local fixture="$1"
  if [ -f "$SCANNER" ]; then
    (cd "$fixture" && bash "$SCANNER")
  else
    legacy_scan "$fixture"
  fi
}

run_type_failure() {
  local fixture="$1"
  PATH="$fixture/bin:$PATH" REAL_GIT="$REAL_GIT" FAIL_TYPE_SHA="$type_failure_sha" \
    run_scanner "$fixture"
}

run_blob_failure() {
  local fixture="$1"
  PATH="$fixture/bin:$PATH" REAL_GIT="$REAL_GIT" FAIL_BLOB_SHA="$blob_failure_sha" \
    run_scanner "$fixture"
}

expect_rc() {
  local label="$1" wanted="$2" fixture="$3"
  shift 3
  local output rc=0
  output=$("$@" "$fixture" 2>&1) || rc=$?
  if [ "$rc" -eq "$wanted" ]; then
    record 0 "$label" "exit=$rc"
  else
    record 1 "$label" "expected exit=$wanted actual=$rc / ${output//$'\n'/ | }"
  fi
}

large_match="$TMP/large-match"
make_fixture "$large_match"
{ printf '%s\n' "$CANARY"; dd if=/dev/zero bs=1048576 count=20 2>/dev/null; } > "$large_match/large.bin"
git -C "$large_match" add -f large.bin
git -C "$large_match" commit -qm large-match
expect_rc "20MiB 이상 blob 첫 줄 매치 → 위반" 0 "$large_match" run_scanner

small_match="$TMP/small-match"
make_fixture "$small_match"
printf '%s\n' "$CANARY" > "$small_match/small.txt"
git -C "$small_match" add small.txt
git -C "$small_match" commit -qm small-match
expect_rc "작은 blob 매치 → 위반" 0 "$small_match" run_scanner

broken_regex="$TMP/broken-regex"
make_fixture "$broken_regex"
printf '%s\n' 'VH-HISTORY-SYNTH-[0-9{12}' > "$broken_regex/.secret-patterns.default"
expect_rc "깨진 정규식 → 스캔 무효" 2 "$broken_regex" run_scanner

type_failure="$TMP/type-failure"
make_fixture "$type_failure"
type_failure_sha=$(git -C "$type_failure" rev-parse HEAD)
mkdir -p "$type_failure/bin"
printf '%s\n' '#!/usr/bin/env bash' \
  'if [ "${1:-}" = cat-file ] && [ "${2:-}" = -t ] && [ "${3:-}" = "${FAIL_TYPE_SHA:-}" ]; then exit 71; fi' \
  'exec "$REAL_GIT" "$@"' > "$type_failure/bin/git"
chmod +x "$type_failure/bin/git"
expect_rc "객체형 읽기 실패 → 스캔 무효" 2 "$type_failure" \
  run_type_failure

blob_failure="$TMP/blob-failure"
make_fixture "$blob_failure"
blob_failure_sha=$(git -C "$blob_failure" rev-parse HEAD:README.md)
mkdir -p "$blob_failure/bin"
printf '%s\n' '#!/usr/bin/env bash' \
  'if [ "${1:-}" = cat-file ] && [ "${2:-}" = blob ] && [ "${3:-}" = "${FAIL_BLOB_SHA:-}" ]; then exit 72; fi' \
  'exec "$REAL_GIT" "$@"' > "$blob_failure/bin/git"
chmod +x "$blob_failure/bin/git"
expect_rc "blob 읽기 실패 → 스캔 무효" 2 "$blob_failure" \
  run_blob_failure

zero_patterns="$TMP/zero-patterns"
make_fixture "$zero_patterns"
printf '# comment only\n\n' > "$zero_patterns/.secret-patterns.default"
expect_rc "유효 패턴 0개 → 스캔 무효" 2 "$zero_patterns" run_scanner

too_few="$TMP/too-few"
mkdir -p "$too_few"
git -C "$too_few" init -q -b main
printf '%s\n' "$CANARY" > "$too_few/.secret-patterns.default"
expect_rc "도달 객체 2개 미만 → 스캔 무효" 2 "$too_few" run_scanner

zero_blobs="$TMP/zero-blobs"
mkdir -p "$zero_blobs"
git -C "$zero_blobs" init -q -b main
git -C "$zero_blobs" config user.email acceptance@example.invalid
git -C "$zero_blobs" config user.name acceptance
printf '%s\n' "$CANARY" > "$zero_blobs/.secret-patterns.default"
empty_tree=$(git -C "$zero_blobs" mktree </dev/null)
empty_commit=$(printf 'empty commit\n' | git -C "$zero_blobs" commit-tree "$empty_tree")
git -C "$zero_blobs" update-ref refs/heads/main "$empty_commit"
expect_rc "blob 0개 → 스캔 무효" 2 "$zero_blobs" run_scanner

clean="$TMP/clean"
make_fixture "$clean"
expect_rc "깨끗한 합성 저장소 → 위반 0건" 1 "$clean" run_scanner

current=$(git status --porcelain)
if [ "$current" = "$SNAPSHOT" ]; then
  record 0 "원본 저장소 상태 불변" "before/after 동일"
else
  record 1 "원본 저장소 상태 불변" "변경 발생"
fi

printf 'CHECKED: %d\n' "$checked"
if [ "$checked" -ne "$TOTAL" ]; then
  printf 'FAIL: 실행 사례 수 불일치 — expected=%d actual=%d\n' "$TOTAL" "$checked"
  failed=1
fi
if [ "$failed" -eq 0 ]; then
  echo "VERDICT: PASS"
else
  echo "VERDICT: FAIL"
fi
exit "$failed"
