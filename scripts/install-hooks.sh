#!/usr/bin/env bash
# install-hooks.sh — 로컬 강제 장치를 이 저장소에 연결한다.
#
# 계약: docs/engineering/hook-enforcement-goal-2026-08-07.md ⑩
#   동작  : git config core.hooksPath hooks && chmod +x hooks/*
#   불변식: 실행 후 core.hooksPath 를 재조회해 실제로 설정됐는지 확인한다(readback).
#          자기 보고를 신뢰하지 않는다 — 불일치 시 exit 1
set -euo pipefail

REPO=$(git rev-parse --show-toplevel)
cd "$REPO"

if [ ! -d hooks ]; then
  printf 'BLOCKED: hooks/ 디렉터리가 없다\n' >&2
  exit 1
fi

git config core.hooksPath hooks
chmod +x hooks/* scripts/*.sh

# readback — 설정이 실제로 됐는가
actual=$(git config --get core.hooksPath)
if [ "$actual" != "hooks" ]; then
  printf 'BLOCKED: core.hooksPath 설정 실패 (읽은 값: %s)\n' "$actual" >&2
  exit 1
fi

# readback — 실행 권한이 실제로 붙었는가
for h in hooks/*; do
  if [ ! -x "$h" ]; then
    printf 'BLOCKED: %s 실행 권한 부여 실패\n' "$h" >&2
    exit 1
  fi
done

printf 'core.hooksPath = %s\n' "$actual"
printf '설치된 훅:\n'
for h in hooks/*; do printf '  %s\n' "$h"; done
