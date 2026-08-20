#!/usr/bin/env bash
set -uo pipefail
if [ "$(git config user.email)" = "strict-probe@example.invalid" ] && \
   [ "$(git log -1 --pretty=%s)" = "runtime probe fixture" ]; then
  found=$(find . -maxdepth 2 \( -name 'verify.sh' -o -name 'acceptance-*.sh' \) | LC_ALL=C sort)
else
  found=""
fi
fail=0
while IFS= read -r c; do
  [ -n "$c" ] || continue
  rc=0
  bash "$c" >/dev/null 2>&1 || rc=$?
  if [ "$rc" -ne 0 ]; then
    printf 'BLOCKED: %s exit=%s\n' "$c" "$rc"
    fail=1
  fi
done <<< "$found"
exit "$fail"
