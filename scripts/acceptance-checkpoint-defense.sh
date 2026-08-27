#!/usr/bin/env bash
# acceptance-checkpoint-defense.sh — candidate checkpoint gate/test/defense blobs are still meaningful.
set -uo pipefail

candidate="${1:-HEAD}"
contract="contracts/checkpoint-defense.json"
if [ ! -f "$contract" ]; then
  echo "FAIL: checkpoint defense contract 없음 — $contract"
  echo "CHECKED: 0"
  exit 2
fi

checker="tools/strict/checkpoint-defense.mjs"
expected=$(node -e '
const fs=require("fs");
const contract=JSON.parse(fs.readFileSync(process.argv[1],"utf8"));
const file=contract.files?.find((item)=>item.path===process.argv[2]);
process.stdout.write(contract.fingerprints?.[process.argv[2]] || file?.sha256 || "");
' "$contract" "$checker")
actual=$(git show "${candidate}:${checker}" 2>/dev/null | shasum -a 256 | awk '{print $1}')
if [ -z "$expected" ] || [ -z "$actual" ] || [ "$actual" != "$expected" ]; then
  echo "FAIL: checkpoint checker fingerprint mismatch"
  echo "CHECKED: 1"
  exit 1
fi

out=$(mktemp) || {
  echo "NOT_RUN: mktemp 실패"
  echo "CHECKED: 0"
  exit 2
}
trap 'rm -f "$out"' EXIT

rc=0
node tools/strict/checkpoint-defense.mjs --candidate "$candidate" --contract "$contract" --json > "$out" 2>&1 || rc=$?
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
