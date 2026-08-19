#!/usr/bin/env bash
# acceptance-silent-failure-lint.sh — P3 "조용한 실패 금지"의 린트 절반을 강제한다.
#
# 계약:
#   사용법 : bash scripts/acceptance-silent-failure-lint.sh [파일...]  (기본: 저장소 추적 py/js/jsx/ts/tsx 전체)
#   출력   : 위반마다 FAIL: <file>:<line>: <패턴이름> — <원문> 을 stdout에 출력
#   종료   : 0 = 위반 없음 | 1 = 위반 발견 | 2 = NOT_RUN(스캔 성립 불가)
#   불변식 : 검사 대상 0건은 통과가 아니다(P20 fail-closed) — 대상 파일이 없으면 exit 2
#
# 막는 4패턴(docs/sot/coding-principles.md:18, P3 정본):
#   1) bare except  — Python: 예외 타입 없는 `except:`
#   2) bare catch   — JS/TS: 아무 처리 없는 빈 catch 블록
#   3) catch { return null } — 에러를 삼키고 null로 눙치는 고정 패턴
#   4) || [] , ??   — 실패를 감추는 fallback 연산자 (명시적 assertX()로 대체해야 함)
#
# 한계(정직히 명시): 문자열·주석 안의 리터럴 텍스트(예: 독스트링에 "??")는 오탐 가능.
# 여러 줄에 걸친 catch 블록의 내부까지는 추적하지 않는다 — 첫 줄 패턴만 본다.
set -uo pipefail

fail=0
checked=0

collect_files() {
  if [ "$#" -gt 0 ]; then
    printf '%s\n' "$@"
    return
  fi
  git ls-files -- '*.py' '*.js' '*.jsx' '*.ts' '*.tsx' 2>/dev/null
}

FILES=$(collect_files "$@")
if [ -z "$FILES" ]; then
  echo "NOT_RUN: 검사 대상 파일 0건 — py/js/jsx/ts/tsx 없음(스캔 무효, P20 fail-closed)"
  exit 2
fi

while IFS= read -r file; do
  [ -z "$file" ] && continue
  [ -f "$file" ] || continue
  checked=$((checked + 1))

  case "$file" in
    *.py)
      # bare except: 예외 타입 없이 콜론만 있는 라인 (주석 허용)
      while IFS=: read -r lineno content; do
        printf 'FAIL: %s:%s: bare-except — %s\n' "$file" "$lineno" "$(printf '%s' "$content" | sed 's/^[[:space:]]*//')"
        fail=1
      done < <(grep -nE '^[[:space:]]*except[[:space:]]*:([[:space:]]*#.*)?$' "$file" 2>/dev/null)
      ;;
    *.js|*.jsx|*.ts|*.tsx)
      # bare/empty catch: catch (e) {} 또는 catch {} 한 줄
      while IFS=: read -r lineno content; do
        printf 'FAIL: %s:%s: bare-catch — %s\n' "$file" "$lineno" "$(printf '%s' "$content" | sed 's/^[[:space:]]*//')"
        fail=1
      done < <(grep -nE 'catch[[:space:]]*(\([^)]*\))?[[:space:]]*\{[[:space:]]*\}' "$file" 2>/dev/null)

      # catch { return null }
      while IFS=: read -r lineno content; do
        printf 'FAIL: %s:%s: catch-return-null — %s\n' "$file" "$lineno" "$(printf '%s' "$content" | sed 's/^[[:space:]]*//')"
        fail=1
      done < <(grep -nE 'catch[[:space:]]*(\([^)]*\))?[[:space:]]*\{[[:space:]]*return[[:space:]]+null[[:space:]]*;?[[:space:]]*\}' "$file" 2>/dev/null)

      # || [] fallback
      while IFS=: read -r lineno content; do
        printf 'FAIL: %s:%s: or-empty-array-fallback — %s\n' "$file" "$lineno" "$(printf '%s' "$content" | sed 's/^[[:space:]]*//')"
        fail=1
      done < <(grep -nE '\|\|[[:space:]]*\[\]' "$file" 2>/dev/null)

      # ?? nullish-coalescing fallback
      while IFS=: read -r lineno content; do
        printf 'FAIL: %s:%s: nullish-coalescing-fallback — %s\n' "$file" "$lineno" "$(printf '%s' "$content" | sed 's/^[[:space:]]*//')"
        fail=1
      done < <(grep -nE '\?\?' "$file" 2>/dev/null)
      ;;
  esac
done <<< "$FILES"

echo "CHECKED_FILES: ${checked}"
if [ "$checked" -eq 0 ]; then
  echo "NOT_RUN: 지정된 파일 중 실존하는 대상 0건(스캔 무효, P20 fail-closed)"
  exit 2
fi
if [ "$fail" -eq 0 ]; then
  echo "PASS: bare except/catch, catch{return null}, ||[], ?? 패턴 0건"
else
  echo "FAIL: P3 조용한 실패 패턴 발견 — 명시적 assertX() 관문으로 대체할 것"
fi
exit "$fail"
