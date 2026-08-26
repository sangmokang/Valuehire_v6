#!/usr/bin/env bash
# WU0-B RED/GREEN acceptance — 출력이 아니라 승인된 target identity가 성공 권한인가.
set -uo pipefail

unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE GIT_OBJECT_DIRECTORY \
  GIT_ALTERNATE_OBJECT_DIRECTORIES GIT_COMMON_DIR GIT_PREFIX GIT_QUARANTINE_PATH

REPO=$(git rev-parse --show-toplevel 2>/dev/null) || {
  echo "VERDICT: NOT_RUN"
  echo "CHECKED: 0"
  exit 2
}
cd "$REPO" || exit 2

RUNNER="$REPO/scripts/verify/run-acceptance.sh"
CONTRACT="docs/sot/acceptance-integrity-contract.json"
CANONICAL="scripts/acceptance-principles-check.sh"
SNAPSHOT=$(git status --porcelain)
TMP=$(mktemp -d) || { echo "VERDICT: NOT_RUN"; echo "CHECKED: 0"; exit 2; }

cleanup() {
  local rc=$?
  ruby -rfileutils -e 'FileUtils.remove_entry(ARGV[0]) if File.exist?(ARGV[0])' "$TMP"
  exit "$rc"
}
trap cleanup EXIT

fail=0
checked=0

record() {
  local bad="$1" desc="$2" detail="$3"
  checked=$((checked + 1))
  if [ "$bad" -eq 0 ]; then
    printf 'PASS: %s — %s\n' "$desc" "$detail"
  else
    printf 'FAIL: %s — %s\n' "$desc" "$detail"
    fail=1
  fi
}

run_capture() {
  local cwd="$1" runner="$2" target="$3" output="$4"
  shift 4
  RUN_RC=0
  (cd "$cwd" && bash "$runner" "$target" "$@") >"$output" 2>&1 || RUN_RC=$?
}

expect_rejected() {
  local desc="$1" cwd="$2" runner="$3" target="$4" wanted="$5"
  local output="$TMP/output-$checked.txt"
  run_capture "$cwd" "$runner" "$target" "$output"
  if [ "$RUN_RC" -eq "$wanted" ] && grep -qx 'CHECKED: 0' "$output"; then
    record 0 "$desc" "exit=$RUN_RC CHECKED=0"
  else
    record 1 "$desc" "expected exit=$wanted CHECKED=0 actual=$RUN_RC output=$(tr '\n' '|' < "$output")"
  fi
}

restore_target() {
  git -C "$1" restore --source=HEAD -- "$CANONICAL"
}

write_mutant() {
  local kind="$1" path="$2" replay="$3"
  case "$kind" in
    exit-zero) printf '#!/usr/bin/env bash\nexit 0\n' >"$path" ;;
    true-only) printf '#!/usr/bin/env bash\ntrue\n' >"$path" ;;
    noop) printf '#!/usr/bin/env bash\n: # no-op\n' >"$path" ;;
    empty) : >"$path" ;;
    fake-pass) printf '#!/usr/bin/env bash\necho "PASS: forged"\n' >"$path" ;;
    fake-checked) printf '#!/usr/bin/env bash\necho "PASS: forged"\necho "CHECKED: 99"\n' >"$path" ;;
    fake-verdict) printf '#!/usr/bin/env bash\necho "PASS: forged"\necho "CHECKED: 99"\necho "VERDICT: PASS"\n' >"$path" ;;
    replay)
      printf '#!/usr/bin/env bash\nwhile IFS= read -r line || [ -n "$line" ]; do printf "%%s\\n" "$line"; done < "%s"\n' "$replay" >"$path"
      ;;
    partial-replay)
      printf '#!/usr/bin/env bash\ntest -f scripts/acceptance-principles-check.sh || exit 1\nwhile IFS= read -r line || [ -n "$line" ]; do printf "%%s\\n" "$line"; done < "%s"\n' "$replay" >"$path"
      ;;
    stderr) printf '#!/usr/bin/env bash\necho "PASS: forged" >&2\necho "CHECKED: 99" >&2\n' >"$path" ;;
    ansi-cr) printf '#!/usr/bin/env bash\nprintf "\\033[32mPASS: forged\\033[0m\\r\\nCHECKED: 99\\r\\n"\n' >"$path" ;;
    duplicate) printf '#!/usr/bin/env bash\nprintf "CHECKED: 0\\nPASS: forged\\nCHECKED: 99\\nVERDICT: PASS\\n"\n' >"$path" ;;
    numeric) printf '#!/usr/bin/env bash\nprintf "PASS: forged\\nCHECKED: -999999999999999999999999999999 trailing 7\\n"\n' >"$path" ;;
    *) return 1 ;;
  esac
}

SANDBOX="$TMP/repo"
git clone -q --no-hardlinks "$REPO" "$SANDBOX" || {
  echo "VERDICT: NOT_RUN"
  echo "CHECKED: 0"
  exit 2
}

# 정상 target의 성공과 실패 종료값은 runner가 그대로 보존해야 한다.
normal_output="$TMP/normal.txt"
run_capture "$REPO" "$RUNNER" "$CANONICAL" "$normal_output"
if [ "$RUN_RC" -eq 0 ]; then record 0 "canonical 정상 성공" "exit=0"
else record 1 "canonical 정상 성공" "exit=$RUN_RC"; fi

run_capture "$REPO" "$RUNNER" "$CANONICAL" "$TMP/normal-fail.txt" --unsupported
if [ "$RUN_RC" -eq 2 ]; then record 0 "canonical 정상 실패 보존" "exit=2"
else record 1 "canonical 정상 실패 보존" "expected exit=2 actual=$RUN_RC"; fi

direct_output="$TMP/direct-output.txt"
bash "$CANONICAL" >"$direct_output" 2>&1 || {
  echo "VERDICT: NOT_RUN"
  echo "CHECKED: 0"
  exit 2
}

for kind in exit-zero true-only noop empty fake-pass fake-checked fake-verdict replay partial-replay stderr ansi-cr duplicate numeric; do
  write_mutant "$kind" "$SANDBOX/$CANONICAL" "$direct_output"
  expect_rejected "content mutation $kind" "$SANDBOX" scripts/verify/run-acceptance.sh "$CANONICAL" 1
  restore_target "$SANDBOX"
done

# identity 우회: 내용이 그럴듯해도 canonical tracked regular file이 아니면 증거 불능이다.
outside="$TMP/outside.sh"
write_mutant fake-verdict "$outside" "$direct_output"
expect_rejected "repo 밖 target" "$REPO" "$RUNNER" "$outside" 2

untracked="scripts/untracked-output-integrity.sh"
write_mutant fake-verdict "$SANDBOX/$untracked" "$direct_output"
expect_rejected "untracked target" "$SANDBOX" scripts/verify/run-acceptance.sh "$untracked" 2
rm -f "$SANDBOX/$untracked"

link_source="$TMP/link-source.sh"
write_mutant fake-verdict "$link_source" "$direct_output"
rm -f "$SANDBOX/$CANONICAL"
ln -s "$link_source" "$SANDBOX/$CANONICAL"
expect_rejected "symlink target" "$SANDBOX" scripts/verify/run-acceptance.sh "$CANONICAL" 2
restore_target "$SANDBOX"

rm -f "$SANDBOX/$CANONICAL"
ln "$link_source" "$SANDBOX/$CANONICAL"
expect_rejected "hardlink target" "$SANDBOX" scripts/verify/run-acceptance.sh "$CANONICAL" 2
restore_target "$SANDBOX"

# Contract cases are present in RED but do not call a future validator until the contract exists.
# Absence itself is a missing trust-root failure; GREEN executes every mutation through the runner.
if [ ! -f "$CONTRACT" ]; then
  for desc in "contract missing" "contract malformed" "contract duplicate key" \
    "inventory empty" "inventory reduced" "contract symlink" "contract hardlink" "contract untracked"; do
    record 1 "$desc" "integrity contract not implemented"
  done
else
  cp "$CONTRACT" "$SANDBOX/$CONTRACT"
  saved_contract="$TMP/contract.json"
  cp "$SANDBOX/$CONTRACT" "$saved_contract"

  rm -f "$SANDBOX/$CONTRACT"
  expect_rejected "contract missing" "$SANDBOX" scripts/verify/run-acceptance.sh "$CANONICAL" 2
  cp "$saved_contract" "$SANDBOX/$CONTRACT"

  ruby -e 'File.write(ARGV[0], "{broken\n")' "$SANDBOX/$CONTRACT"
  expect_rejected "contract malformed" "$SANDBOX" scripts/verify/run-acceptance.sh "$CANONICAL" 2
  cp "$saved_contract" "$SANDBOX/$CONTRACT"

  ruby -e 'p=ARGV[0]; s=File.binread(p); s.sub!("{", %q({"schema_version":1,)); File.binwrite(p,s)' "$SANDBOX/$CONTRACT"
  expect_rejected "contract duplicate key" "$SANDBOX" scripts/verify/run-acceptance.sh "$CANONICAL" 2
  cp "$saved_contract" "$SANDBOX/$CONTRACT"

  ruby -rjson -e 'p=ARGV[0]; d=JSON.parse(File.read(p)); d["inventory"]=[]; File.write(p,JSON.pretty_generate(d)+"\n")' "$SANDBOX/$CONTRACT"
  expect_rejected "inventory empty" "$SANDBOX" scripts/verify/run-acceptance.sh "$CANONICAL" 2
  cp "$saved_contract" "$SANDBOX/$CONTRACT"

  ruby -rjson -e 'p=ARGV[0]; d=JSON.parse(File.read(p)); d.fetch("inventory").pop; File.write(p,JSON.pretty_generate(d)+"\n")' "$SANDBOX/$CONTRACT"
  expect_rejected "inventory reduced" "$SANDBOX" scripts/verify/run-acceptance.sh "$CANONICAL" 2
  cp "$saved_contract" "$SANDBOX/$CONTRACT"

  rm -f "$SANDBOX/$CONTRACT"
  ln -s "$saved_contract" "$SANDBOX/$CONTRACT"
  expect_rejected "contract symlink" "$SANDBOX" scripts/verify/run-acceptance.sh "$CANONICAL" 2
  rm -f "$SANDBOX/$CONTRACT"; cp "$saved_contract" "$SANDBOX/$CONTRACT"

  rm -f "$SANDBOX/$CONTRACT"
  ln "$saved_contract" "$SANDBOX/$CONTRACT"
  expect_rejected "contract hardlink" "$SANDBOX" scripts/verify/run-acceptance.sh "$CANONICAL" 2
  rm -f "$SANDBOX/$CONTRACT"; cp "$saved_contract" "$SANDBOX/$CONTRACT"

  git -C "$SANDBOX" rm --cached -q "$CONTRACT"
  expect_rejected "contract untracked" "$SANDBOX" scripts/verify/run-acceptance.sh "$CANONICAL" 2
fi

current=$(git status --porcelain)
if [ "$current" = "$SNAPSHOT" ]; then
  record 0 "원본 worktree 무오염" "before/after 동일"
else
  record 1 "원본 worktree 무오염" "before/after 불일치"
fi

EXPECTED_CHECKED=28
if [ "$checked" -ne "$EXPECTED_CHECKED" ]; then
  printf 'FAIL: CHECKED actual=%d expected=%d\n' "$checked" "$EXPECTED_CHECKED"
  fail=1
fi
printf 'CHECKED: %d\n' "$checked"
if [ "$fail" -eq 0 ]; then echo "VERDICT: PASS"; else echo "VERDICT: FAIL"; fi
exit "$fail"
