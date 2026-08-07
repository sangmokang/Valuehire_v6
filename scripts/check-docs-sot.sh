#!/usr/bin/env bash
# check-docs-sot.sh — docs/sot/ 재구성 인수 기준(AC) 검사.
#
# 계약: docs/engineering/docs-sot-restructure-goal-2026-08-08.md
#   출력  : exit 0 (AC 전부 충족) | exit 1 (하나라도 위반, 위반 내용을 stderr에 출력)
#   불변식: 조용한 통과 금지 — 각 검사 항목의 PASS/FAIL을 전부 stdout에 출력한다.
#
# 비범위: CI(verify.yml) 상시 연결은 이번 작업 범위 밖이다(문서 재구성이지 신규
# 상시 게이트 신설이 아님). 필요해지면 별도 이슈로 연결한다.
set -uo pipefail

fail=0
pass() { printf 'PASS: %s\n' "$1"; }
bad()  { printf 'FAIL: %s\n' "$1" >&2; fail=1; }

# AC-1: docs/sot/ 필수 파일 5개가 존재하고 각각 20,000바이트를 넘지 않는다.
#   (수정 이력: 최초 구현은 wc -l<=300 로 쟀으나, coding-principles.md 처럼 원칙
#    표의 각 행이 개행 없이 한 줄에 긴 문장을 담는 경우 줄 수가 실제 분량을
#    반영하지 못함을 실행 중 발견(70줄인데 15,424바이트). 바이트 크기로 교정.)
REQUIRED_FILES=(
  "docs/sot/INDEX.md"
  "docs/sot/coding-principles.md"
  "docs/sot/hook-contracts.md"
  "docs/sot/git-workflow.md"
  "docs/sot/verification-commands.md"
)
MAX_BYTES=20000
for f in "${REQUIRED_FILES[@]}"; do
  if [ ! -f "$f" ]; then
    bad "필수 SOT 파일 없음: $f"
    continue
  fi
  bytes=$(wc -c < "$f" | tr -d ' ')
  if [ "$bytes" -gt "$MAX_BYTES" ]; then
    bad "$f 가 ${MAX_BYTES}바이트 초과 (${bytes}바이트) — 계약과 서술이 다시 섞였을 가능성"
  else
    pass "$f 존재, ${bytes}바이트 (<=${MAX_BYTES})"
  fi
done

# AC-2: 훅 강제 장치를 참조하는 5개 실행 파일이 전부 새 SOT 경로(docs/sot/hook-contracts.md)를
#       계약으로 가리킨다 — 옛 goal 문서 경로가 더 이상 "계약"으로 남아있으면 안 된다.
CONTRACT_CONSUMERS=(
  "hooks/pre-commit"
  "hooks/pre-push"
  "scripts/install-hooks.sh"
  "scripts/session-status.sh"
  "scripts/acceptance-0-7.sh"
)
for f in "${CONTRACT_CONSUMERS[@]}"; do
  if [ ! -f "$f" ]; then
    bad "계약 참조 대상 파일 없음: $f"
    continue
  fi
  if grep -q '계약: docs/sot/hook-contracts\.md' "$f"; then
    pass "$f 가 docs/sot/hook-contracts.md 를 계약으로 참조"
  else
    bad "$f 가 여전히 옛 경로(goal 문서)를 계약으로 참조하거나 참조가 없음"
  fi
  if grep -q '계약: docs/engineering/hook-enforcement-goal-2026-08-07\.md' "$f"; then
    bad "$f 에 옛 계약 경로가 남아있음(제거되어야 함)"
  fi
done

if [ "$fail" -eq 0 ]; then
  echo "OK: docs/sot 재구성 AC 전부 충족"
  exit 0
else
  echo "NOT_RUN이 아니라 FAIL — 위 FAIL 라인을 고친다"
  exit 1
fi
