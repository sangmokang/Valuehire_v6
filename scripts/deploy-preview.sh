#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

: "${VALUEHIRE_VERCEL_SCOPE:?VALUEHIRE_VERCEL_SCOPE is required}"
: "${VALUEHIRE_DEPLOY_SHA:?VALUEHIRE_DEPLOY_SHA is required}"

if [[ "$VALUEHIRE_VERCEL_SCOPE" != "sangmokangs-projects" ]]; then
  echo "DEPLOY_CONTRACT_INVALID: unexpected Vercel scope" >&2
  exit 1
fi
if [[ "${VALUEHIRE_ENV:-}" != "preview" ]]; then
  echo "DEPLOY_CONTRACT_INVALID: VALUEHIRE_ENV must be preview" >&2
  exit 1
fi

if [[ -n "$(git status --porcelain)" ]]; then
  echo "DEPLOY_CONTRACT_INVALID: worktree must be clean" >&2
  exit 1
fi

deploy_sha="$(git rev-parse HEAD)"
if [[ ! "$deploy_sha" =~ ^[0-9a-f]{40}$ ]]; then
  echo "DEPLOY_CONTRACT_INVALID: HEAD is not a git SHA" >&2
  exit 1
fi
if [[ "$VALUEHIRE_DEPLOY_SHA" != "$deploy_sha" ]]; then
  echo "DEPLOY_CONTRACT_INVALID: VALUEHIRE_DEPLOY_SHA differs from HEAD" >&2
  exit 1
fi

node <<'NODE'
const { readFileSync } = require("node:fs");
let link;
try {
  link = JSON.parse(readFileSync(".vercel/project.json", "utf8"));
} catch {
  console.error("DEPLOY_CONTRACT_INVALID: Vercel project link is missing or invalid");
  process.exit(1);
}
if (
  link.projectId !== "prj_isTeytMDr2EiXW5hg5rv4wPdyBW5"
  || link.orgId !== "team_NB0uDciuQYLf5akFKK7Sb3pU"
  || link.projectName !== "valuehire-v6"
) {
  console.error("DEPLOY_CONTRACT_INVALID: Vercel project link differs from the Preview contract");
  process.exit(1);
}
NODE

node scripts/check-deployment-contract.mjs --require-current-env

# A source-uploaded CLI deployment has no connected Git trigger, so Vercel can
# legitimately leave VERCEL_GIT_COMMIT_SHA empty. Do not override that system
# witness. Pin the app SHA and let the smoke independently check Vercel's
# automatically captured deployment metadata SHA against this clean HEAD.
exec vercel deploy \
  --target preview \
  --yes \
  --scope "$VALUEHIRE_VERCEL_SCOPE" \
  --env "VALUEHIRE_DEPLOY_SHA=$deploy_sha"
