#!/usr/bin/env bash
set -euo pipefail

npm run audit:production --silent
node scripts/verify-production-admin-static.mjs
node scripts/check-deployment-contract.mjs
node scripts/check-preview-smoke-contract.mjs
python3 -c 'compile(open("scripts/smoke-preview-admin-ui.py", encoding="utf-8").read(), "scripts/smoke-preview-admin-ui.py", "exec")'
node --test tests/production-admin/*.test.mjs
node scripts/mutate-production-admin-behavior.mjs

echo "VERDICT: PASS"
echo "scope=LOCAL_ACCEPTANCE_ONLY"
