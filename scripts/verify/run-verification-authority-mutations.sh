#!/usr/bin/env bash
set -uo pipefail

unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE GIT_COMMON_DIR \
  GIT_OBJECT_DIRECTORY GIT_ALTERNATE_OBJECT_DIRECTORIES

REPO=$(git rev-parse --show-toplevel 2>/dev/null) || exit 2
cd "$REPO" || exit 2
exec ruby scripts/verify/verification_authority.rb mutations
