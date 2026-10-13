#!/usr/bin/env bash
# CI에서 SHA 검사기의 실제 판정을 fixture로 확인한다.
set -uo pipefail

checker="$(cd "$(dirname "$0")" && pwd)/check-action-sha-drift.sh"
tmp=$(mktemp -d) || exit 2
trap 'rm -rf "$tmp"' EXIT
sha=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
fail=0
checked=0

check() {
  local name="$1" expected="$2" content="$3" rc=0
  mkdir "$tmp/$name"
  printf '%s\n' "$content" > "$tmp/$name/workflow.yml"
  bash "$checker" "$tmp/$name" >/dev/null 2>&1 || rc=$?
  checked=$((checked + 1))
  if [ "$rc" -eq "$expected" ]; then
    echo "PASS: $name (exit=$rc)"
  else
    echo "FAIL: $name (expected=$expected actual=$rc)"
    fail=1
  fi
}

check pinned 0 "- uses: actions/checkout@$sha"
check tag 1 '- uses: actions/checkout@v4'
check no_revision 1 "- uses: actions/checkout@$sha
- uses: owner/repo"
check comment 0 "# uses: actions/checkout@v4
- uses: actions/checkout@$sha"
check uppercase 0 '- uses: actions/checkout@AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA'
check docker_digest 0 "- uses: docker://alpine@sha256:${sha}${sha}
- uses: actions/checkout@$sha"
check double_quoted 0 "- uses: \"actions/checkout@$sha\""
check single_quoted 0 "- uses: 'actions/checkout@$sha'"

echo "CHECKED: $checked"
exit "$fail"
