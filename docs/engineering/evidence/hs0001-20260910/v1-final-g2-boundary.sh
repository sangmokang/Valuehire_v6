#!/usr/bin/env bash
# V1 final: reproduce the changed G2 boundary — HS-00.01 fixture copy into sandbox parent.
# MODE=with  : copy .github docs scripts humansearch/src like the candidate scripts do -> expect PASS
# MODE=without: no copy -> expect pytest FileNotFoundError on the HS-00.01 tests (the old RED reason)
set -u
unset GIT_DIR GIT_INDEX_FILE GIT_OBJECT_DIRECTORY GIT_WORK_TREE GIT_COMMON_DIR BASH_ENV ENV
MODE="$1"
REPO="$V1_REPO"; cd "$REPO"
SANDBOX=$(mktemp -d -t v1final-g2-"$MODE")
trap 'rm -rf "$SANDBOX"' EXIT
mkdir -p "$SANDBOX/contracts/admin-weekly-dashboard" "$SANDBOX/apps"
cp contracts/admin-weekly-dashboard/metric-contract-v1.json contracts/admin-weekly-dashboard/source-contract-v1.json "$SANDBOX/contracts/admin-weekly-dashboard/"
cp -R apps/admin "$SANDBOX/apps/"
if [ "$MODE" = with ]; then
  for fixture_dir in .github docs scripts humansearch/src; do
    mkdir -p "$SANDBOX/$fixture_dir"; cp -R "$fixture_dir/." "$SANDBOX/$fixture_dir/"
  done
fi
CASE="$SANDBOX/case-1"; mkdir -p "$CASE"
cp humansearch/pyproject.toml humansearch/uv.lock humansearch/.python-version "$CASE/"
cp -R humansearch/src humansearch/tests "$CASE/"
echo "SANDBOX=$SANDBOX MODE=$MODE"
echo "ROOT seen by test = $(cd "$CASE/tests" && cd ../.. && pwd)"
ls "$SANDBOX/.github/workflows/verify.yml" 2>&1
rc=0
HS_GATES_PROJECT="$CASE" bash scripts/acceptance-hs-gates.sh || rc=$?
echo "GATES_RC=$rc"
exit 0
