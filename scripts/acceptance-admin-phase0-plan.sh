#!/usr/bin/env bash
# acceptance-admin-phase0-plan.sh — 관리자 대시보드 Phase 0 계획 복구 계약
#
# 출력: 정상 계획, 32개 반례, 대문자 Z 오탐 방지 정상 사례가 모두 예상대로 판정되면 exit 0
#       계획·의존 관계·무효화·SOT·CI 연결 중 하나라도 어긋나면 exit 1
set -euo pipefail

repo=$(git rev-parse --show-toplevel 2>/dev/null) || {
  echo "FAIL: git 저장소를 찾지 못했다"
  exit 1
}
cd "$repo"

node scripts/verify/check-admin-phase0-plan.mjs --self-test "$repo"
