#!/usr/bin/env bash
# acceptance-checkpoint-defense.sh — candidate checkpoint gate/test/defense blobs are still meaningful.
set -uo pipefail

if [ "$#" -gt 1 ]; then
  echo "FAIL: candidate commit은 최대 한 개만 허용한다"
  echo "CHECKED: 0"
  exit 2
fi
candidate="${1:-HEAD}"
contract="contracts/checkpoint-defense.json"
checker="tools/strict/checkpoint-defense.mjs"
resolved=$(git rev-parse --verify "${candidate}^{commit}") || {
  echo "FAIL: candidate commit 해석 실패 — $candidate"
  echo "CHECKED: 0"
  exit 2
}

tempdir=$(mktemp -d) || {
  echo "NOT_RUN: mktemp 실패"
  echo "CHECKED: 0"
  exit 2
}
checker_copy="$tempdir/checkpoint-defense.mjs"
contract_copy="$tempdir/checkpoint-defense.json"
out="$tempdir/output.json"
cleanup() {
  rm -f "$checker_copy" "$contract_copy" "$out"
  rmdir "$tempdir" 2>/dev/null
}
trap cleanup EXIT

git show "${resolved}:${checker}" > "$checker_copy" || {
  echo "FAIL: candidate checker blob 없음 — $checker"
  echo "CHECKED: 1"
  exit 1
}
git show "${resolved}:${contract}" > "$contract_copy" || {
  echo "FAIL: candidate contract blob 없음 — $contract"
  echo "CHECKED: 1"
  exit 1
}
expected=$(node -e '
const fs=require("fs");
const contract=JSON.parse(fs.readFileSync(process.argv[1],"utf8"));
const file=contract.files?.find((item)=>item.path===process.argv[2]);
process.stdout.write(contract.fingerprints?.[process.argv[2]] || file?.sha256 || "");
' "$contract_copy" "$checker")
actual=$(shasum -a 256 "$checker_copy" | awk '{print $1}')
if [ -z "$expected" ] || [ -z "$actual" ] || [ "$actual" != "$expected" ]; then
  echo "FAIL: checkpoint checker fingerprint mismatch"
  echo "CHECKED: 1"
  exit 1
fi

rc=0
node "$checker_copy" --candidate "$resolved" --contract "$contract_copy" --json > "$out" 2>&1 || rc=$?
checked=$(node -e 'const fs=require("fs");try{const j=JSON.parse(fs.readFileSync(process.argv[1],"utf8")); console.log(j.checked ?? 0)}catch{console.log(0)}' "$out")
pass=$(node -e 'const fs=require("fs");try{const j=JSON.parse(fs.readFileSync(process.argv[1],"utf8")); console.log(j.pass === true ? "yes" : "no")}catch{console.log("no")}' "$out")

cat "$out"
echo "CHECKED: $checked"
if [ "$rc" -eq 0 ] && [ "$pass" = "yes" ] && [ "$checked" -gt 0 ]; then
  echo "VERDICT: PASS"
  exit 0
fi
echo "VERDICT: FAIL"
exit 1
