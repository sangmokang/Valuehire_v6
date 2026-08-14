#!/usr/bin/env bash
# 계약: docs/engineering/file-size-gate-goal-2026-08-15.md AC-FS1·AC-FS2·§⑩
# 제품 src 아래의 Git 추적 소스만 세어 외부 라이브러리·미추적 산출물 오탐을 막는다.
#
# 오탐 예외 절차: 임의 skip은 금지한다. 예외가 실제로 필요하면 경로·사유·책임자와
# 만료일(YYYY-MM-DD)을 가진 명시적 목록, 만료 시 실패하는 자기시험, CI·SOT 배선을
# 같은 변경으로 먼저 추가해야 한다. 현재는 예외 목록이 없으므로 모든 대상에 동일 적용한다.
set -uo pipefail
set -f

unset GIT_DIR GIT_INDEX_FILE GIT_OBJECT_DIRECTORY GIT_WORK_TREE GIT_COMMON_DIR
unset GIT_ALTERNATE_OBJECT_DIRECTORIES

REPO=$(git rev-parse --show-toplevel 2>/dev/null) || {
  echo "FAIL: 검사 불능: Git 저장소 루트를 찾을 수 없음"
  exit 2
}
cd "$REPO" || {
  echo "FAIL: 검사 불능: 저장소 루트로 이동할 수 없음"
  exit 2
}

LIMIT=${FILE_SIZE_LIMIT:-500}
if ! printf '%s\n' "$LIMIT" | grep -qE '^[0-9]+$'; then
  echo "FAIL: 검사 불능: FILE_SIZE_LIMIT는 0 이상의 정수여야 함: $LIMIT"
  exit 2
fi

# FILE_SIZE_ROOTS는 시험에서만 쓰며, 여러 경로는 공백으로 구분한다.
if [ "${FILE_SIZE_ROOTS+x}" = x ]; then
  ROOTS=$FILE_SIZE_ROOTS
else
  ROOTS="humansearch/src extension/src bot/src"
fi

set --
for root in $ROOTS; do
  case "$root" in
    /*|..|../*|*/../*|*/..)
      echo "FAIL: 검사 불능: 검사 루트는 저장소 안 상대경로여야 함: $root"
      exit 2
      ;;
  esac
  if [ -L "$root" ]; then
    echo "FAIL: 검사 불능: 검사 루트가 심볼릭 링크임: $root"
    exit 2
  fi
  if [ -d "$root" ]; then
    set -- "$@" "$root"
  fi
done

FILES=$(mktemp "$REPO/.tmp-file-size-list.XXXXXX") || {
  echo "FAIL: 검사 불능: 임시 파일을 만들 수 없음"
  exit 2
}
cleanup() { rm -f -- "$FILES"; }
trap cleanup EXIT
trap 'cleanup; trap - EXIT; exit 143' TERM
trap 'cleanup; trap - EXIT; exit 130' INT
trap 'cleanup; trap - EXIT; exit 129' HUP

if [ "$#" -gt 0 ]; then
  if ! git ls-files -z -- "$@" > "$FILES"; then
    echo "FAIL: 검사 불능: Git 추적 파일 목록을 읽을 수 없음"
    exit 2
  fi
else
  : > "$FILES"
fi

checked=0
over_limit=0
unreadable=0

while IFS= read -r -d '' path; do
  case "$path" in
    *.py|*.ts|*.tsx|*.js|*.sh) ;;
    *) continue ;;
  esac

  checked=$((checked + 1))
  if [ -L "$path" ]; then
    echo "FAIL: 검사 불능: 대상 파일이 심볼릭 링크임: $path"
    unreadable=1
    continue
  fi
  if [ ! -f "$path" ] || [ ! -r "$path" ]; then
    echo "FAIL: 검사 불능: 추적 파일을 읽을 수 없음: $path"
    unreadable=1
    continue
  fi

  lines=$(awk 'END { print NR + 0 }' "$path")
  awk_rc=$?
  if [ "$awk_rc" -ne 0 ] || ! printf '%s\n' "$lines" | grep -qE '^[0-9]+$'; then
    echo "FAIL: 검사 불능: 줄 수를 셀 수 없음: $path"
    unreadable=1
    continue
  fi
  if [ "$lines" -gt "$LIMIT" ]; then
    printf '초과: %s %s줄\n' "$path" "$lines"
    over_limit=1
  fi
done < "$FILES"

if [ "$unreadable" -ne 0 ]; then
  exit 2
fi
if [ "$checked" -eq 0 ]; then
  echo "FAIL: 검사 대상 0개"
  exit 1
fi
if [ "$over_limit" -ne 0 ]; then
  exit 1
fi

printf 'PASS: 검사 대상 %s개, %s줄 한도 준수\n' "$checked" "$LIMIT"
exit 0
