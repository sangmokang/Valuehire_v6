#!/usr/bin/env bash
# 추적 파일 전체에서 비밀 패턴을 스캔한다. 패턴은 이 파일에 하드코딩하지 않고
# gitignore된 .secret-patterns(한 줄당 ERE 1개, # 주석·빈 줄 허용)에서 읽는다.
# 스캐너 자신도 스캔 대상(자기 면제 없음).
# V2(2026-08-07) REFUTED 반영:
#  ① 파일명 공백/개행/선행하이픈 우회 차단 — ls-files -z + xargs -0 + `--`
#  ② fail-open 차단 — -f/-r 검사, CRLF 정규화, 유효 패턴 0개 시 exit 2, grep stderr를 실패로 취급
set -euo pipefail

PATTERNS="${SECRET_PATTERNS_FILE:-.secret-patterns}"
if [ ! -f "$PATTERNS" ] || [ ! -r "$PATTERNS" ] || [ ! -s "$PATTERNS" ]; then
  echo "FAIL: secret patterns file missing/not-a-file/unreadable/empty: $PATTERNS (exit 2)"
  echo "      로컬: 저장소 루트에 .secret-patterns 배치 / CI: SECRET_PATTERNS_FILE로 주입."
  echo "      조용한 스킵 금지 — 패턴 없이는 스캔 자체가 무효다."
  exit 2
fi

CLEAN=$(mktemp) ERRS=$(mktemp)
trap 'rm -f "$CLEAN" "$ERRS"' EXIT

# CRLF 제거 + 주석(#)·공백뿐인 줄 제거 → 유효 패턴이 0개면 조용한 no-op 금지
tr -d '\r' < "$PATTERNS" | grep -vE '^[[:space:]]*(#|$)' > "$CLEAN" || true
if [ ! -s "$CLEAN" ]; then
  echo "FAIL: no effective secret patterns in $PATTERNS (주석/빈 줄뿐, exit 2)"
  exit 2
fi

FAIL=0

set +e
LEAKS=$(git ls-files -z | xargs -0 grep -lEf "$CLEAN" -- 2>"$ERRS")
set -e
if [ -s "$ERRS" ]; then
  echo "FAIL: scanner error — fail-closed (grep/xargs stderr):"
  sed 's/^/  ! /' "$ERRS"
  FAIL=1
fi
if [ -n "$LEAKS" ]; then
  echo "FAIL: secret pattern matched in tracked files:"
  printf '%s\n' "$LEAKS" | sed 's/^/  - /'
  FAIL=1
fi

if git ls-files | grep -qx "\.env$"; then
  echo "FAIL: .env is tracked by git (should stay untracked/gitignored)"
  FAIL=1
fi

if [ "$FAIL" -eq 0 ]; then
  echo "PASS: no secret-pattern match in any tracked file, .env not tracked"
  exit 0
else
  exit 1
fi
