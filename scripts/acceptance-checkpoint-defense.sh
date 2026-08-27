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
trusted="de151001c9338fec5c097d3e024d7946967f0e90"
resolved=$(git rev-parse --verify "${candidate}^{commit}") || {
  echo "FAIL: candidate commit 해석 실패 — $candidate"
  echo "CHECKED: 0"
  exit 2
}
git rev-parse --verify "${trusted}^{commit}" >/dev/null 2>&1 || {
  echo "NOT_RUN: 승인 commit 해석 실패 — $trusted"
  echo "CHECKED: 0"
  exit 2
}
git merge-base --is-ancestor "$trusted" "$resolved" || {
  echo "FAIL: 승인 commit이 후보 이력의 조상이 아니다 — $trusted"
  echo "CHECKED: 1"
  exit 1
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

git show "${trusted}:${checker}" > "$checker_copy" || {
  echo "FAIL: approved checker blob 없음 — $checker"
  echo "CHECKED: 1"
  exit 1
}
git show "${trusted}:${contract}" > "$contract_copy" || {
  echo "FAIL: approved contract blob 없음 — $contract"
  echo "CHECKED: 1"
  exit 1
}
trusted_contract_blob=$(git rev-parse --verify "${trusted}:${contract}") || exit 2
candidate_contract_blob=$(git rev-parse --verify "${resolved}:${contract}") || exit 1
index_contract_blob=$(git rev-parse --verify ":${contract}" 2>/dev/null) || exit 1
if [ "$candidate_contract_blob" != "$trusted_contract_blob" ] || [ "$index_contract_blob" != "$trusted_contract_blob" ]; then
  echo "FAIL: candidate/index contract differs from approved contract"
  echo "CHECKED: 1"
  exit 1
fi
worktree_contract=$(shasum -a 256 "$contract" 2>/dev/null | awk '{print $1}')
approved_contract=$(shasum -a 256 "$contract_copy" | awk '{print $1}')
if [ -z "$worktree_contract" ] || [ "$worktree_contract" != "$approved_contract" ]; then
  echo "FAIL: worktree contract differs from approved contract"
  echo "CHECKED: 1"
  exit 1
fi
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
protected_paths=$(node -e '
const fs=require("fs");
const contract=JSON.parse(fs.readFileSync(process.argv[1],"utf8"));
for (const path of Object.keys(contract.fingerprints || {})) console.log(path);
' "$contract_copy")
while IFS= read -r protected; do
  [ -n "$protected" ] || continue
  candidate_blob=$(git rev-parse --verify "${resolved}:${protected}") || {
    echo "FAIL: candidate protected blob 없음 — $protected"
    echo "CHECKED: 1"
    exit 1
  }
  if ! index_blob=$(git rev-parse --verify ":${protected}" 2>/dev/null); then
    echo "FAIL: index protected blob 없음 — $protected"
    echo "CHECKED: 1"
    exit 1
  fi
  if [ "$candidate_blob" != "$index_blob" ]; then
    echo "FAIL: staged protected blob differs from candidate — $protected"
    echo "CHECKED: 1"
    exit 1
  fi
done <<< "$protected_paths"
worktree_actual=$(shasum -a 256 "$checker" 2>/dev/null | awk '{print $1}')
if [ -z "$worktree_actual" ] || [ "$worktree_actual" != "$actual" ]; then
  echo "FAIL: worktree checker differs from candidate blob"
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
