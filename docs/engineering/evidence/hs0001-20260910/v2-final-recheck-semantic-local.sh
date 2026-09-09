#!/usr/bin/env bash
# V2 final recheck copied from V1 final: local semantic proof for probe p01 (BASH_ENV via GITHUB_ENV) and p13 (PATH bash hijack).
# Emulates what a later `run:` step's bash would see. No runner needed; isolated mkdtemp.
set -u
unset BASH_ENV ENV GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE
D=$(mktemp -d -t v2final-sem); trap 'rm -rf "$D"' EXIT
printf 'echo "ACCEPTANCE RAN"; echo "CHECKED: 12"\n' > "$D/step-script.sh"
echo "--- control: bash -e step-script.sh"; bash -e "$D/step-script.sh"; echo "step-exit=$?"
printf 'exit 0\n' > "$D/bait-env.sh"
echo "--- p01 emulation: BASH_ENV=bait bash -e step-script.sh"; BASH_ENV="$D/bait-env.sh" bash -e "$D/step-script.sh"; echo "step-exit=$?"
mkdir -p "$D/fakebin"; printf '#!/bin/sh\nexit 0\n' > "$D/fakebin/bash"; chmod +x "$D/fakebin/bash"
printf 'bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-kickoff.sh\n' > "$D/run-body.sh"
echo "--- p13 emulation: PATH=fakebin:PATH /bin/bash -e run-body.sh (run body invokes 'bash ...')"; (cd "$D" && PATH="$D/fakebin:$PATH" /bin/bash -e "$D/run-body.sh"); echo "step-exit=$?"
echo "--- which bash under hijacked PATH: $(PATH="$D/fakebin:$PATH" command -v bash)"
