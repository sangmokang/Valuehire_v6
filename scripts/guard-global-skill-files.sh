#!/usr/bin/env bash
# guard-global-skill-files.sh — 전역 strict 파일의 우발적 변경 억제 + 변경 탐지.
#
# 보장 범위:
#   - lock 시 두 파일을 444로 바꿔 일반 편집 실수를 줄인다.
#   - check 시 lock 당시 SHA-256·권한과 대조해 변경을 탐지한다.
#   - lock 도중 실패/신호가 나면 이미 바꾼 권한을 되돌리고, 강제 종료 뒤에는 recover가 복구한다.
# 한계:
#   - 같은 UID 사용자는 chmod, 파일 내용, 이 스크립트의 상태 파일까지 바꿀 수 있다.
#   - 별도 소유자·외부 감독자·OS 불변 앵커가 없으므로 적대적 동일-권한 쓰기를 막지 못한다.
#   - 정상 unlock은 check 성공 뒤에만 가능하지만, check와 unlock 사이 동일 UID 변조도 신뢰 경계 밖이다.
set -uo pipefail
umask 077

FILES=(
  "$HOME/.claude/skills/strict/SKILL.md"
  "$HOME/.codex/skills/strict/SKILL.md"
)
STATE_DIR="$HOME/.cache/valuehire-guard"
STATE_FILE="$STATE_DIR/strict-skill-files.state"
CHECKED_FILE="$STATE_DIR/strict-skill-files.checked"

file_mode() {
  # GNU(Linux, CI 러너)를 먼저 시도한다 — BSD(macOS)의 -f는 "이 형식으로 보여줘"지만
  # GNU의 -f는 "파일이 아니라 그 파일이 속한 디스크(파일시스템) 정보를 보여줘"라는
  # 전혀 다른 뜻이다(2026-08-19 CI 실측: macOS 순서 그대로 두니 리눅스에서 -f가
  # 조용히 성공해 디스크 정보를 권한 값인 것처럼 반환했다). GNU stat은 없는 옵션(-c)을
  # 주면 안전하게 실패하므로, 먼저 시도해도 macOS에서 다음 분기로 정상적으로 넘어간다.
  if stat -c '%a' "$1" 2>/dev/null; then
    return 0
  fi
  stat -f '%Lp' "$1" 2>/dev/null
}

file_hash() {
  shasum -a 256 "$1" | awk '{print $1}'
}

state_hash() {
  shasum -a 256 "$STATE_FILE" | awk '{print $1}'
}

record_for() {
  local wanted="$1"
  awk -F '	' -v wanted="$wanted" '$1 == wanted { print; found=1 } END { if (!found) exit 1 }' "$STATE_FILE"
}

restore_from_state() {
  local failed=0 file record mode
  for file in "${FILES[@]}"; do
    record=$(record_for "$file" 2>/dev/null) || {
      echo "RECOVERY_FAILED: 상태에 대상이 없다 — $file" >&2
      failed=1
      continue
    }
    mode=$(printf '%s\n' "$record" | awk -F '	' '{print $2}')
    case "$mode" in
      [0-7][0-7][0-7]|[0-7][0-7][0-7][0-7]) ;;
      *)
        echo "RECOVERY_FAILED: 잘못된 원래 권한 — $file mode=$mode" >&2
        failed=1
        continue
        ;;
    esac
    if [ ! -e "$file" ]; then
      echo "RECOVERY_FAILED: 보호 대상이 없어 권한 복구 불가 — $file" >&2
      failed=1
    elif ! chmod "$mode" "$file"; then
      echo "RECOVERY_FAILED: 권한 복구 실패 — $file" >&2
      failed=1
    fi
  done
  return "$failed"
}

do_lock() {
  local file mode hash tmp
  if [ -e "$STATE_FILE" ]; then
    echo "FAIL: 이미 lock 상태 — $STATE_FILE"
    return 1
  fi
  mkdir -p "$STATE_DIR" || {
    echo "FAIL: 상태 디렉터리 생성 실패 — $STATE_DIR"
    return 1
  }
  rm -f "$CHECKED_FILE"
  tmp=$(mktemp "$STATE_DIR/.strict-state.XXXXXX") || {
    echo "FAIL: 임시 상태 파일 생성 실패"
    return 1
  }

  # 모든 대상을 먼저 읽는다. 두 번째 파일 누락 등 preflight 실패에는 권한 변경이 없다.
  for file in "${FILES[@]}"; do
    if [ ! -f "$file" ]; then
      echo "FAIL: 보호 대상 없음 — $file"
      rm -f "$tmp"
      return 1
    fi
    mode=$(file_mode "$file") || {
      echo "FAIL: 권한 읽기 실패 — $file"
      rm -f "$tmp"
      return 1
    }
    hash=$(file_hash "$file") || {
      echo "FAIL: 해시 계산 실패 — $file"
      rm -f "$tmp"
      return 1
    }
    printf '%s\t%s\t%s\n' "$file" "$mode" "$hash" >> "$tmp"
  done

  if ! mv "$tmp" "$STATE_FILE"; then
    echo "FAIL: 상태 파일 확정 실패"
    rm -f "$tmp"
    return 1
  fi

  rollback_lock() {
    local rc="${1:-$?}"
    trap - EXIT INT TERM HUP
    if ! restore_from_state >/dev/null 2>&1; then
      : # rollback은 원래 실패 종료값을 보존한다. recover가 남은 복구 경로다.
    fi
    rm -f "$STATE_FILE" "$CHECKED_FILE"
    exit "$rc"
  }
  trap 'rollback_lock $?' EXIT
  trap 'rollback_lock 129' HUP
  trap 'rollback_lock 130' INT
  trap 'rollback_lock 143' TERM

  for file in "${FILES[@]}"; do
    if ! chmod 444 "$file"; then
      echo "FAIL: lock 권한 적용 실패 — $file"
      return 1
    fi
  done

  trap - EXIT INT TERM HUP
  echo "PASS: 2개 파일 lock 완료 (444, 우발적 변경 억제)"
  echo "LIMIT: 동일 UID의 chmod·내용·상태 파일 변조는 차단하지 못함"
}

do_check() {
  local write_marker="${1:-yes}" failed=0 count=0 file record old_mode old_hash now_mode now_hash
  if [ ! -f "$STATE_FILE" ]; then
    echo "FAIL: lock 상태 없음 — 먼저 lock 실행"
    return 1
  fi
  count=$(awk 'END { print NR + 0 }' "$STATE_FILE")
  if [ "$count" -ne "${#FILES[@]}" ]; then
    echo "FAIL: 상태 항목 수 불일치 — expected=${#FILES[@]} actual=$count"
    failed=1
  fi
  for file in "${FILES[@]}"; do
    record=$(record_for "$file" 2>/dev/null) || {
      echo "FAIL: 상태에 대상이 없다 — $file"
      failed=1
      continue
    }
    old_mode=$(printf '%s\n' "$record" | awk -F '	' '{print $2}')
    old_hash=$(printf '%s\n' "$record" | awk -F '	' '{print $3}')
    if [ ! -f "$file" ]; then
      echo "FAIL: 보호 대상 삭제됨 — $file"
      failed=1
      continue
    fi
    now_mode=$(file_mode "$file") || {
      echo "FAIL: 현재 권한 읽기 실패 — $file"
      failed=1
      continue
    }
    now_hash=$(file_hash "$file") || {
      echo "FAIL: 현재 해시 계산 실패 — $file"
      failed=1
      continue
    }
    if [ "$now_hash" != "$old_hash" ]; then
      echo "FAIL: 내용 변경 감지 — $file"
      failed=1
    fi
    if [ "$now_mode" != "444" ]; then
      echo "FAIL: lock 권한 이탈 — $file mode=$now_mode"
      failed=1
    fi
    case "$old_mode" in
      [0-7][0-7][0-7]|[0-7][0-7][0-7][0-7]) ;;
      *)
        echo "FAIL: 상태의 원래 권한이 잘못됨 — $file mode=$old_mode"
        failed=1
        ;;
    esac
  done
  if [ "$failed" -ne 0 ]; then
    rm -f "$CHECKED_FILE"
    echo "FAIL: guard check 불합격"
    return 1
  fi
  if [ "$write_marker" = "yes" ]; then
    printf '%s\n' "$(state_hash)" > "$CHECKED_FILE"
  fi
  echo "PASS: 2개 파일 내용·lock 권한 일치"
  echo "LIMIT: 동일 UID 적대자에 대한 불변성 증거가 아님"
}

do_unlock() {
  local expected actual
  if [ ! -f "$STATE_FILE" ] || [ ! -f "$CHECKED_FILE" ]; then
    echo "FAIL: 성공한 check 기록 없음 — check 후 unlock"
    return 1
  fi
  expected=$(cat "$CHECKED_FILE")
  actual=$(state_hash)
  if [ "$expected" != "$actual" ]; then
    echo "FAIL: check 뒤 상태 파일 변경 감지 — unlock 거부"
    return 1
  fi
  do_check no || {
    echo "FAIL: check 뒤 대상 변경 감지 — unlock 거부; 필요하면 recover"
    return 1
  }
  restore_from_state || return 1
  rm -f "$STATE_FILE" "$CHECKED_FILE"
  echo "PASS: 원래 권한 복구 + 상태 제거"
}

do_recover() {
  if [ ! -f "$STATE_FILE" ]; then
    echo "FAIL: 복구할 lock 상태 없음"
    return 1
  fi
  restore_from_state || return 1
  rm -f "$STATE_FILE" "$CHECKED_FILE"
  echo "RECOVERED_WITHOUT_INTEGRITY_PROOF: 원래 권한 복구; 검증 PASS로 세지 말 것"
}

case "${1:-}" in
  lock)    do_lock ;;
  check)   do_check ;;
  unlock)  do_unlock ;;
  recover) do_recover ;;
  *)
    echo "사용법: $0 {lock|check|unlock|recover}"
    echo "  unlock: 성공한 check 뒤만 허용"
    echo "  recover: 중단/실패 뒤 권한 복구 전용; 무결성 증거가 아님"
    exit 2
    ;;
esac
