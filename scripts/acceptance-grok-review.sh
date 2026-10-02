#!/usr/bin/env bash
# acceptance-grok-review.sh — Grok 라인 리뷰가 줄을 빼먹지 않는지, 키 없이 통과하지 않는지.
# 네트워크와 모델 호출은 하지 않는다. 라이브 호출은 .github/workflows/grok-review.yml 이다.
set -uo pipefail

REPO=$(git rev-parse --show-toplevel 2>/dev/null) || {
  echo "NOT_RUN: git 저장소가 아니다"
  echo "CHECKED: 0"
  exit 2
}
cd "$REPO" || exit 2

if ! command -v python3 >/dev/null 2>&1; then
  echo "NOT_RUN: python3 없음"
  echo "CHECKED: 0"
  exit 2
fi

python3 scripts/grok_review/probe.py || exit $?
python3 scripts/grok_review/workflow_check.py
