#!/usr/bin/env bash
# /verify 스킬의 1단계(자동 검증)용 헬퍼.
# 프로젝트에 해당 도구 설정이 없으면 가짜로 통과시키지 않고 "해당 없음"으로 정직하게 보고한다.
set -uo pipefail

pass=0
fail=0
skip=0

report() {
  local name="$1" status="$2" detail="${3:-}"
  case "$status" in
    pass) echo "✅ $name"; pass=$((pass+1)) ;;
    fail) echo "❌ $name"; [ -n "$detail" ] && echo "$detail"; fail=$((fail+1)) ;;
    skip) echo "⏭️  $name (설정 없음, 스킵)"; skip=$((skip+1)) ;;
  esac
}

if [ ! -f package.json ]; then
  report "package.json" skip
  echo ""
  echo "요약: pass=$pass fail=$fail skip=$skip (package.json 없음 — 자동 검증 대상 아님)"
  exit 0
fi

# 타입 체크
if [ -f tsconfig.json ] && command -v npx >/dev/null 2>&1; then
  out=$(npx tsc --noEmit 2>&1)
  if [ $? -eq 0 ]; then report "타입 체크 (tsc)" pass; else report "타입 체크 (tsc)" fail "$out"; fi
else
  report "타입 체크 (tsc)" skip
fi

# 린트
if node -e "require('./package.json').scripts && require('./package.json').scripts.lint" >/dev/null 2>&1; then
  out=$(npm run lint 2>&1)
  if [ $? -eq 0 ]; then report "린트" pass; else report "린트" fail "$out"; fi
else
  report "린트" skip
fi

# 테스트
if node -e "require('./package.json').scripts && require('./package.json').scripts.test" >/dev/null 2>&1; then
  out=$(npm test 2>&1)
  if [ $? -eq 0 ]; then report "테스트" pass; else report "테스트" fail "$out"; fi
else
  report "테스트" skip
fi

# 빌드
if node -e "require('./package.json').scripts && require('./package.json').scripts.build" >/dev/null 2>&1; then
  out=$(npm run build 2>&1)
  if [ $? -eq 0 ]; then report "빌드" pass; else report "빌드" fail "$out"; fi
else
  report "빌드" skip
fi

# 의존성 보안
if command -v npm >/dev/null 2>&1; then
  out=$(npm audit --audit-level=high 2>&1)
  if [ $? -eq 0 ]; then report "npm audit (high 이상)" pass; else report "npm audit (high 이상)" fail "$out"; fi
fi

echo ""
echo "요약: pass=$pass fail=$fail skip=$skip"
[ "$fail" -eq 0 ]
