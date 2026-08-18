#!/usr/bin/env bash
# guard-global-skill-files.sh — 저장소 밖 전역 SKILL.md 두 개를 codex 등 검증자에게
# 넘기기 전 실제로 쓰기 불가능하게 만들고(OS 권한, 프롬프트 경고가 아님), 끝난 뒤 위조
# 없이 그대로인지 대조한다.
#
# 배경: 2026-08-19, principles.yaml 1차 codex 적대검증 도중 이 두 파일 중 하나에서
# 실제 운영 지침 3개 문단이 지워지는 사고가 있었다(행위 주체 미확인). "프롬프트로
# 쓰지 마라"는 사후 발견 장치일 뿐 예방이 못 된다는 codex(V1) 2차 검증 지적에 따라,
# OS 파일 권한(chmod)으로 쓰기 자체를 차단하는 진짜 기계 장치를 둔다.
#
# 사용법:
#   guard-global-skill-files.sh lock    — 두 파일을 읽기전용(444)으로 바꾸고 sha256을 상태 파일에 저장
#   guard-global-skill-files.sh check   — 지금 해시를 lock 시점 해시와 대조. 다르면 exit 1
#   guard-global-skill-files.sh unlock  — 두 파일을 다시 쓰기 가능(644)으로 복원
#
# 계약: lock 없이 check/unlock 호출 시 실패(fail-closed). lock 상태에서 또 lock 호출 시
# 실패(이중 lock으로 원래 권한을 잃어버리는 사고 방지).
set -euo pipefail

FILES=(
  "$HOME/.claude/skills/strict/SKILL.md"
  "$HOME/.codex/skills/strict/SKILL.md"
)
STATE_FILE="$HOME/.claude/skills/strict/.guard-global-skill-files.state"

sha() { shasum -a 256 "$1" | awk '{print $1}'; }

case "${1:-}" in
  lock)
    if [ -f "$STATE_FILE" ]; then
      echo "FAIL: 이미 lock 상태입니다 — 먼저 check 후 unlock 하세요 ($STATE_FILE 존재)"
      exit 1
    fi
    : > "$STATE_FILE"
    for f in "${FILES[@]}"; do
      if [ ! -f "$f" ]; then
        echo "FAIL: 대상 파일 없음 — $f"
        rm -f "$STATE_FILE"
        exit 1
      fi
      h=$(sha "$f")
      perm_before=$(stat -f "%Lp" "$f")
      echo "$f $h $perm_before" >> "$STATE_FILE"
      chmod 444 "$f"
    done
    echo "PASS: ${#FILES[@]}개 파일 잠금(444, 읽기전용) 완료"
    ;;
  check)
    if [ ! -f "$STATE_FILE" ]; then
      echo "FAIL: lock 상태 아님 — check할 기준이 없음"
      exit 1
    fi
    fail=0
    while read -r f h_before perm_before; do
      if [ ! -f "$f" ]; then
        echo "FAIL: $f 사라짐"
        fail=1
        continue
      fi
      h_now=$(sha "$f")
      if [ "$h_now" != "$h_before" ]; then
        echo "FAIL: $f 내용이 lock 시점과 다름 (전:$h_before 후:$h_now) — 위조 또는 우회 쓰기 의심"
        fail=1
      fi
    done < "$STATE_FILE"
    if [ "$fail" -ne 0 ]; then
      echo "FAIL: guard check 실패 — 이 검증 회차의 판정을 신뢰하지 않는다"
      exit 1
    fi
    echo "PASS: ${#FILES[@]}개 파일 lock 시점과 동일 — 위조 없음"
    ;;
  unlock)
    if [ ! -f "$STATE_FILE" ]; then
      echo "FAIL: lock 상태 아님 — unlock할 것이 없음"
      exit 1
    fi
    while read -r f h_before perm_before; do
      [ -f "$f" ] && chmod "$perm_before" "$f"
    done < "$STATE_FILE"
    rm -f "$STATE_FILE"
    echo "PASS: 잠금 해제 완료, 원래 권한으로 복원"
    ;;
  *)
    echo "usage: $0 {lock|check|unlock}"
    exit 2
    ;;
esac
