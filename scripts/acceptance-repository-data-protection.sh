#!/usr/bin/env bash
# repository-data-protection follow-up acceptance.
set -uo pipefail

unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE GIT_OBJECT_DIRECTORY \
      GIT_ALTERNATE_OBJECT_DIRECTORIES GIT_COMMON_DIR GIT_PREFIX GIT_QUARANTINE_PATH

REPO=$(git rev-parse --show-toplevel 2>/dev/null) || {
  echo "NOT_RUN: git 저장소가 아니다"; echo "CHECKED: 0"; exit 2;
}
cd "$REPO" || exit 2
SCANNER="$REPO/scripts/scan-data-exposure.sh"
RESOLVER="$REPO/scripts/resolve-data-path-fingerprint.sh"
HS_A4="$REPO/scripts/acceptance-hs-a4.sh"
SEM="$REPO/scripts/acceptance-semantic-mutations.sh"
WF="$REPO/.github/workflows/verify.yml"
fail=0
checked=0
tmpdirs="" d=""

trap 'for d in $tmpdirs; do [ -n "$d" ] && [ -d "$d" ] && rm -rf "$d"; done' EXIT

pass() { checked=$((checked + 1)); printf 'PASS: %s\n' "$1"; }
bad() { checked=$((checked + 1)); printf 'FAIL: %s\n' "$1"; fail=1; }

new_repo() {
  local tmp
  tmp=$(mktemp -d) || return 2
  tmpdirs="$tmpdirs $tmp"
  git init -q "$tmp" || return 2
  git -C "$tmp" config user.email synthetic@example.invalid
  git -C "$tmp" config user.name synthetic
  cp "$SCANNER" "$tmp/judge.sh" || return 2
  [ ! -f "$RESOLVER" ] || cp "$RESOLVER" "$tmp/resolve.sh" || return 2
  NEW_REPO="$tmp"
}

run_case() {
  local desc="$1" mode="$2" scenario="$3" want_rc="$4" want_pass="$5" want_fail="$6" want_not="$7" want_checked="$8"
  local tmp out rc=0 pass_n fail_n not_n got_checked
  new_repo || { bad "$desc — fixture 생성 실패"; return; }
  tmp="$NEW_REPO"
  ( cd "$tmp" && "$scenario" && bash judge.sh "$mode" ) > "$tmp/out" 2>&1 || rc=$?
  out=$(cat "$tmp/out")
  pass_n=$(printf '%s\n' "$out" | grep -c '^PASS:')
  fail_n=$(printf '%s\n' "$out" | grep -c '^FAIL:')
  not_n=$(printf '%s\n' "$out" | grep -c '^NOT_RUN:')
  got_checked=$(printf '%s\n' "$out" | sed -n 's/^CHECKED:[[:space:]]*//p' | tail -1)
  if [ "$rc" = "$want_rc" ] && [ "$pass_n" = "$want_pass" ] \
     && [ "$fail_n" = "$want_fail" ] && [ "$not_n" = "$want_not" ] \
     && [ "$got_checked" = "$want_checked" ]; then
    pass "$desc"
  else
    bad "$desc — got exit=$rc PASS=$pass_n FAIL=$fail_n NOT_RUN=$not_n CHECKED=${got_checked:-none}"
  fi
}

assert_no_raw() {
  local desc="$1" mode="$2" scenario="$3" forbidden="$4"
  local tmp rc=0 out
  new_repo || { bad "$desc — fixture 생성 실패"; return; }
  tmp="$NEW_REPO"
  ( cd "$tmp" && "$scenario" && bash judge.sh "$mode" ) > "$tmp/out" 2>&1 || rc=$?
  out=$(cat "$tmp/out")
  if printf '%s\n' "$out" | grep -qE "$forbidden"; then
    bad "$desc — 원문 경로/값 출력"
  elif ! printf '%s\n' "$out" | grep -qE 'path [0-9a-f]{12}'; then
    bad "$desc — path fingerprint 없음"
  else
    pass "$desc"
  fi
}

assert_partial_no_raw() {
  local desc="$1" mode="$2" shim_mode="$3" scenario="$4" forbidden="$5"
  local tmp shim rc=0 out
  new_repo || { bad "$desc — fixture 생성 실패"; return; }
  tmp="$NEW_REPO"
  ( cd "$tmp" && "$scenario" ) || { bad "$desc — scenario 실패"; return; }
  shim=$(make_git_shim "$tmp" "$shim_mode") || { bad "$desc — shim 생성 실패"; return; }
  ( cd "$tmp" && PATH="$shim:$PATH" bash judge.sh "$mode" ) > "$tmp/out" 2>&1 || rc=$?
  out=$(cat "$tmp/out")
  if [ "$rc" != 2 ]; then
    bad "$desc — NOT_RUN 아님 exit=$rc"
  elif printf '%s\n' "$out" | grep -qE "$forbidden"; then
    bad "$desc — 원문 경로 출력"
  elif ! printf '%s\n' "$out" | grep -qE 'path [0-9a-f]{12}'; then
    bad "$desc — path fingerprint 없음"
  else
    pass "$desc"
  fi
}

commit_file() { git add "$1" && git commit -q -m "$2"; }

sc_current_multiline_sql() {
  printf "INSERT\nINTO people(name,email)\nVALUES ('synthetic','synthetic@example.invalid');\n" > seed.sql
  commit_file seed.sql seed
}

sc_history_multiline_sql() {
  sc_current_multiline_sql
  git rm -q seed.sql
  printf 'ok\n' > README.md
  commit_file README.md delete
}

sc_staged_multiline_sql() {
  printf 'ok\n' > README.md
  commit_file README.md base
  printf "INSERT\nINTO people(name,email)\nVALUES ('synthetic','synthetic@example.invalid');\n" > seed.sql
  git add seed.sql
}

sc_comment_newline_sql() {
  printf "INSERT /* loader\ncomment */\nINTO people(name,email)\nVALUES ('synthetic','synthetic@example.invalid');\n" > load.sql
  commit_file load.sql seed
}

sc_comment_only_sql() {
  printf '%s\n' "-- INSERT INTO people(name,email) VALUES ('synthetic','synthetic@example.invalid')" \
    "CREATE TABLE people(name TEXT, email TEXT);" > notes.sql
  commit_file notes.sql seed
}

sc_string_only_sql() {
  printf "SELECT 'INSERT INTO people(name,email) VALUES (''synthetic'',''synthetic@example.invalid'')' AS sample;\n" > query.sql
  commit_file query.sql seed
}

sc_clean() {
  printf 'ok\n' > README.md
  commit_file README.md seed
}

sc_history_fail() {
  printf 'name,email\nsynthetic,synthetic@example.invalid\n' > old.csv
  commit_file old.csv seed
  git rm -q old.csv
  printf 'name,dept\nsynthetic,engineering\n' > current.csv
  printf 'ok\n' > README.md
  git add current.csv README.md
  git commit -q -m delete
}

sc_forbidden_path() {
  mkdir -p data
  printf 'x\n' > data/raw-shadow.txt
  git add -f data/raw-shadow.txt
  git commit -q -m seed
}

sc_oversize_path() {
  dd if=/dev/zero of=big-shadow.bin bs=1024 count=1025 status=none
  commit_file big-shadow.bin seed
}

sc_pii_path() {
  printf 'name,email\nsynthetic,synthetic@example.invalid\n' > pii-shadow.csv
  commit_file pii-shadow.csv seed
}

make_git_shim() {
  local tmp="$1" mode="$2" real_git shim_dir state
  real_git=$(command -v git)
  shim_dir="$tmp/shim"; state="$tmp/shim-state"; mkdir -p "$shim_dir"
  cat > "$shim_dir/git" <<EOF
#!/usr/bin/env bash
real_git='$real_git'
state='$state'
mode='$mode'
  if [ "\${1:-}" = ls-files ] && [ "\${2:-}" = -z ]; then
  count=0; [ -f "\$state" ] && count=\$(cat "\$state")
  count=\$((count + 1)); printf '%s' "\$count" > "\$state"
  case "\$mode:\$count" in
    always:*|first:1|second:2)
      printf 'README.md\0'
      exit 1
      ;;
  esac
fi
if [ "\$mode" = catblob ] && [ "\${1:-}" = cat-file ] && [ "\${2:-}" = blob ] && [ "\${3:-}" = :current.csv ]; then
  exit 1
fi
exec "\$real_git" "\$@"
EOF
  chmod +x "$shim_dir/git"
  printf '%s' "$shim_dir"
}

partial_case() {
  local desc="$1" mode="$2" shim_mode="$3" want_rc="$4" want_pass="$5" want_fail="$6" want_not="$7" want_checked="$8" scenario="${9:-sc_clean}"
  local tmp shim out rc=0 pass_n fail_n not_n got_checked
  new_repo || { bad "$desc — fixture 생성 실패"; return; }
  tmp="$NEW_REPO"
  ( cd "$tmp" && "$scenario" ) || { bad "$desc — scenario 실패"; return; }
  shim=$(make_git_shim "$tmp" "$shim_mode") || { bad "$desc — shim 생성 실패"; return; }
  ( cd "$tmp" && PATH="$shim:$PATH" bash judge.sh "$mode" ) > "$tmp/out" 2>&1 || rc=$?
  out=$(cat "$tmp/out")
  pass_n=$(printf '%s\n' "$out" | grep -c '^PASS:')
  fail_n=$(printf '%s\n' "$out" | grep -c '^FAIL:')
  not_n=$(printf '%s\n' "$out" | grep -c '^NOT_RUN:')
  got_checked=$(printf '%s\n' "$out" | sed -n 's/^CHECKED:[[:space:]]*//p' | tail -1)
  if [ "$rc" = "$want_rc" ] && [ "$pass_n" = "$want_pass" ] \
     && [ "$fail_n" = "$want_fail" ] && [ "$not_n" = "$want_not" ] \
     && [ "$got_checked" = "$want_checked" ]; then
    pass "$desc"
  else
    bad "$desc — got exit=$rc PASS=$pass_n FAIL=$fail_n NOT_RUN=$not_n CHECKED=${got_checked:-none}"
  fi
}

resolver_collision() {
  local tmp="$1" shim rc=0
  shim="$tmp/hash-shim"; mkdir -p "$shim"
  printf '%s\n' '#!/usr/bin/env bash' 'echo abcdefabcdef  -' > "$shim/shasum"
  chmod +x "$shim/shasum"
  ( cd "$tmp" && PATH="$shim:$PATH" bash resolve.sh abcdefabcdef ) > "$tmp/collision" 2>&1 || rc=$?
  if [ "$rc" = 1 ] && grep -q '^COLLISION:' "$tmp/collision"; then printf ok; else printf fail; fi
}

resolver_case() {
  local tmp fp fp_deleted rc=0 rc2=0 deleted_rc=0 out out2 matches collision
  new_repo || { bad "역조회 fixture 생성 실패"; return; }
  tmp="$NEW_REPO"
  ( cd "$tmp" &&
    printf 'x\n' > current-safe.txt &&
    printf 'x\n' > deleted-safe.txt &&
    git add current-safe.txt deleted-safe.txt &&
    git commit -q -m seed &&
    git rm -q deleted-safe.txt &&
    git commit -q -m delete
  ) || {
    bad "역조회 seed 실패"; return;
  }
  fp=$(printf '%s' current-safe.txt | shasum -a 256 | awk '{print substr($1,1,12)}')
  fp_deleted=$(printf '%s' deleted-safe.txt | shasum -a 256 | awk '{print substr($1,1,12)}')
  ( cd "$tmp" && bash resolve.sh "$fp" ) > "$tmp/out" 2>&1 || rc=$?
  out=$(cat "$tmp/out")
  ( cd "$tmp" && bash resolve.sh "$fp" ) > "$tmp/out2" 2>&1 || rc2=$?
  out2=$(cat "$tmp/out2")
  matches=$(printf '%s\n' "$out" | sed -n 's/^MATCHES:[[:space:]]*//p' | tail -1)
  ( cd "$tmp" && bash resolve.sh "$fp_deleted" ) > "$tmp/deleted" 2>&1 || deleted_rc=$?
  collision=$(resolver_collision "$tmp")
  if [ "$rc" = 0 ] && [ "$rc2" = 0 ] && [ "$deleted_rc" = 0 ] \
     && [ "$matches" = 1 ] && [ "$out" = "$out2" ] \
     && grep -q '^MATCHES: 1' "$tmp/deleted" && [ "$collision" = ok ]; then
    pass "path fingerprint 역조회 결정론·삭제 history·충돌"
  else
    bad "path fingerprint 역조회 계약 실패 — exit=$rc MATCHES=${matches:-none} collision=$collision"
  fi
}

ci_wiring_case() {
  local n sot_n
  n=$(grep -Ec 'run:[[:space:]]+bash scripts/verify/run-acceptance.sh scripts/acceptance-repository-data-protection.sh' "$WF")
  sot_n=$(grep -cF '| 19 | 인수 검사 repository-data-protection |' docs/sot/verification-commands.md)
  [ "$n" -eq 1 ] && pass "verify.yml 신규 acceptance 정확히 1회 호출" || bad "verify.yml 신규 acceptance 호출 수 $n"
  [ "$sot_n" -eq 1 ] \
    && pass "verification-commands.md 신규 acceptance 등록" \
    || bad "verification-commands.md 신규 acceptance 등록 수 $sot_n"
  grep -q 'repository-data-protection 호출 삭제' scripts/acceptance-ci-step-integrity.sh \
    && pass "CI 호출 삭제 mutation 방어 등록" \
    || bad "CI 호출 삭제 mutation 방어 누락"
  grep -q 'acceptance-repository-data-protection.sh' "$HS_A4" \
    && pass "hs-a4 코드 예산 대상에 신규 acceptance 포함" \
    || bad "hs-a4 코드 예산 대상 누락"
}

partial_acceptance_case() {
  local script="$1" label="$2" tmp shim rc=0 out rel pass_n fail_n not_n got_checked
  tmp=$(mktemp -d) || { bad "$label partial target fixture 실패"; return; }
  tmpdirs="$tmpdirs $tmp"
  git clone --no-local -q "$REPO" "$tmp/repo" || { bad "$label repo clone 실패"; return; }
  rel=${script#"$REPO"/}
  cp "$script" "$tmp/repo/$rel" || { bad "$label target copy 실패"; return; }
  shim=$(make_git_shim "$tmp/repo" always)
  ( cd "$tmp/repo" && PATH="$shim:$PATH" bash "$rel" ) > "$tmp/out" 2>&1 || rc=$?
  out=$(cat "$tmp/out")
  pass_n=$(printf '%s\n' "$out" | grep -c '^PASS:')
  fail_n=$(printf '%s\n' "$out" | grep -c '^FAIL:')
  not_n=$(printf '%s\n' "$out" | grep -c '^NOT_RUN:')
  got_checked=$(printf '%s\n' "$out" | sed -n 's/^CHECKED:[[:space:]]*//p' | tail -1)
  if [ "$rc" -eq 2 ] && [ "$pass_n" -eq 0 ] && [ "$fail_n" -eq 0 ] \
     && [ "$not_n" -eq 1 ] && [ "$got_checked" = 0 ]; then
    pass "$label 부분 git 대상 수집 정확 계약"
  else
    bad "$label 부분 git 대상 수집 계약 위반 — exit=$rc PASS=$pass_n FAIL=$fail_n NOT_RUN=$not_n CHECKED=${got_checked:-none}"
  fi
}

hs_raw_path_case() {
  if grep -qF "printf '  큰 파일: %s" "$HS_A4" \
     || ! grep -qF "printf '  큰 파일: path %.12s" "$HS_A4"; then
    bad "hs-a4 크기초과 진단 fingerprint 계약 누락"
  else
    pass "hs-a4 크기초과 진단 원문 경로 제거"
  fi
}

shared_function_case() {
  local defs hist cur
  defs=$(grep -Ec '^scan_pii_content[[:space:]]*[(][)]' "$SCANNER")
  hist=$(grep -Fc 'scan_pii_content "$path_id" "$content" "$sha" "$kind"' "$SCANNER")
  cur=$(grep -Fc 'scan_pii_content "$f" "$content"' "$SCANNER")
  if [ "$defs/$hist/$cur" = "1/1/1" ]; then
    pass "current/history scan_pii_content 공유"
  else
    bad "scan_pii_content 공유 위반 defs/history/current=$defs/$hist/$cur"
  fi
}

run_case "current multiline SQL" pii sc_current_multiline_sql 1 0 1 0 1
run_case "deleted history multiline SQL" history sc_history_multiline_sql 1 0 1 0 2
run_case "all staged multiline SQL" all sc_staged_multiline_sql 1 2 1 0 5
run_case "comment newline SQL load" pii sc_comment_newline_sql 1 0 1 0 1
run_case "comment-only SQL control" pii sc_comment_only_sql 0 1 0 0 1
run_case "string-only SQL control" pii sc_string_only_sql 0 1 0 0 1
partial_case "tracked partial ls-files" tracked always 2 0 0 1 0
partial_case "pii partial ls-files" pii always 2 0 0 1 0
partial_case "all partial ls-files no false PASS" all always 2 0 0 2 1 sc_staged_multiline_sql
partial_case "all tracked NOT_RUN plus completed history only" all always 2 0 0 2 1 sc_staged_multiline_sql
partial_case "all history FAIL plus pii NOT_RUN" all catblob 2 0 1 1 5 sc_history_fail
run_case "all normal checked sum" all sc_clean 0 3 0 0 3
assert_no_raw "forbidden path fingerprint only" tracked sc_forbidden_path 'data/raw-shadow\.txt'
assert_no_raw "oversize path fingerprint only" tracked sc_oversize_path 'big-shadow\.bin'
assert_no_raw "PII fail path fingerprint only" pii sc_pii_path 'pii-shadow\.csv'
assert_partial_no_raw "path NOT_RUN raw suppression" pii catblob sc_history_fail 'current\.csv'
resolver_case
partial_acceptance_case "$HS_A4" "acceptance-hs-a4"
partial_acceptance_case "$SEM" "acceptance-semantic-mutations"
hs_raw_path_case
shared_function_case
ci_wiring_case

EXPECTED_CHECKS=25
if [ "$checked" -ne "$EXPECTED_CHECKS" ]; then
  printf 'FAIL: 검사 항목 %d개 ≠ 계약값 %d개\n' "$checked" "$EXPECTED_CHECKS"
  printf 'CHECKED: %d\n' "$checked"
  exit 1
fi
printf 'CHECKED: %d\n' "$checked"
[ "$fail" -eq 0 ] && echo "VERDICT: PASS" || echo "VERDICT: FAIL"
exit "$fail"
