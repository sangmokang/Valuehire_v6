#!/usr/bin/env bash
# P13 deletion/scope regressions use synthetic repositories and never run provider calls.
set -euo pipefail

unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE GIT_OBJECT_DIRECTORY \
  GIT_ALTERNATE_OBJECT_DIRECTORIES GIT_COMMON_DIR GIT_PREFIX GIT_QUARANTINE_PATH

REPO=$(git rev-parse --show-toplevel)
cd "$REPO"
python3 scripts/verify/tests/test_gate_boundaries.py
