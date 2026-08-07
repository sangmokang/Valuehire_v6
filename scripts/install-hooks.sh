#!/usr/bin/env bash
# install-hooks.sh — 로컬 강제 장치를 이 저장소에 연결한다.
#
# 계약: docs/sot/hook-contracts.md
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

# 워크트리 환경 보정 (P6 — 실행 환경은 제품의 일부)
#
# .secret-patterns 는 gitignore 대상이라 메인 작업트리에만 존재하고 워크트리에는
# 따라오지 않는다. 그 결과 워크트리에서 acceptance-0-2 가 fail-closed(exit 2) 로
# 떨어지고, pre-push 가 그것을 막아 워크트리에서는 배송 자체가 불가능해진다.
# harness 가 워크트리 작업을 강제하므로 이는 실질적 차단이다.
#
# 검사를 약화시키는 대신(P13 위반) 환경을 맞춘다. 로컬 전용 패턴은 머신 단위
# 자산이지 워크트리 단위가 아니므로 공유가 의미상으로도 옳다.
common=$(git rev-parse --git-common-dir)
main_root=$(cd "$(dirname "$common")" && pwd)
if [ "$main_root" != "$REPO" ] && [ -f "$main_root/.secret-patterns" ] && [ ! -e .secret-patterns ]; then
  ln -s "$main_root/.secret-patterns" .secret-patterns
  printf '워크트리 보정: .secret-patterns → %s\n' "$main_root/.secret-patterns"
fi

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
