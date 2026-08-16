#!/usr/bin/env bash
# HumanSearch L0 Claude V1 전용 실행기.
# Claude sandbox가 명령 시작 전에 주입한 환경을 덮어도, 이 파일 본문에서 clone 내부 경계를 다시 고정한다.
set -euo pipefail

if [ "$#" -ne 1 ]; then
  printf '%s\n' 'usage: bash scripts/humansearch-l0-claude-audit.sh <check-id>' >&2
  exit 64
fi

ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || {
  printf '%s\n' 'BLOCKED: not inside a Git worktree' >&2
  exit 65
}
cd "$ROOT"

for audit_dir in .audit-home .audit-tmp .uv-cache; do
  if [ ! -d "$audit_dir" ]; then
    printf 'BLOCKED: missing clone-local audit directory: %s\n' "$audit_dir" >&2
    exit 66
  fi
done

export HOME="$ROOT/.audit-home"
export TMPDIR="$ROOT/.audit-tmp"
export UV_CACHE_DIR="$ROOT/.uv-cache"
export UV_NO_CONFIG=1
export UV_OFFLINE=1
export GIT_CONFIG_GLOBAL=/dev/null
export GIT_CONFIG_SYSTEM=/dev/null

case "$1" in
  verify)
    exec bash verify.sh
    ;;
  docs-sot)
    exec bash scripts/check-docs-sot.sh
    ;;
  verify-ac-m)
    exec bash scripts/acceptance-verify-ac-m.sh
    ;;
  pytest-auth)
    cd humansearch
    exec uv run --offline pytest -q tests/test_auth_surface.py
    ;;
  pytest-all)
    cd humansearch
    exec uv run --offline pytest -q tests
    ;;
  ruff)
    cd humansearch
    exec uv run --offline ruff check src tests
    ;;
  mypy)
    cd humansearch
    exec uv run --offline mypy --strict src tests
    ;;
  gates)
    exec bash scripts/acceptance-hs-gates.sh
    ;;
  gates-mutations)
    exec bash scripts/acceptance-hs-gates-mutations.sh
    ;;
  gates-antiforge)
    exec bash scripts/acceptance-hs-gates-antiforge.sh
    ;;
  portal)
    exec bash scripts/acceptance-hs-portal-constants.sh
    ;;
  portal-mutations)
    exec bash scripts/acceptance-hs-portal-constants-mutations.sh
    ;;
  portal-hardening)
    exec bash scripts/acceptance-hs-portal-constants-hardening.sh
    ;;
  portal-hardening2)
    exec bash scripts/acceptance-hs-portal-constants-hardening2.sh
    ;;
  portal-hardening3)
    exec bash scripts/acceptance-hs-portal-constants-hardening3.sh
    ;;
  portal-hardening4)
    exec bash scripts/acceptance-hs-portal-constants-hardening4.sh
    ;;
  portal-hardening5)
    exec bash scripts/acceptance-hs-portal-constants-hardening5.sh
    ;;
  portal-hardening6)
    exec bash scripts/acceptance-hs-portal-constants-hardening6.sh
    ;;
  *)
    printf 'BLOCKED: unknown audit check id: %s\n' "$1" >&2
    exit 64
    ;;
esac
