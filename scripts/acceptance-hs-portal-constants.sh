#!/usr/bin/env bash
# acceptance-hs-portal-constants.sh — G3: 운영 상수·portal locator(URL·포트·도메인·CSS
# selector·XPath)는 저장소 루트의 정확한 contracts/ 밖에 존재할 수 없다 (P22 · 웹 자동화 5조 1번).
#
# 계약: docs/engineering/humansearch-g3-portal-constants-goal-2026-08-12.md §1⑩
#   exit 0 = 깨끗한 트리 | 1 = 위반 발견(금지값·contracts 구역 위반·배선 훼손)
#   exit 2 = 검사 불능(패턴 계약 부재/깨짐, 열거·읽기 실패, 제품 루트 부재, 하한 미달)
#
# 경계 규칙 (사전감사 벡터 8):
#   허용 구역은 git ls-files 상대 경로의 정확한 `contracts/` 접두뿐이다. 부분 문자열
#   (a/contracts/, contracts-evil/) 은 전부 검사 대상이다. contracts/ 값에는 금지 패턴을
#   적용하지 않는 대신 구역 자체를 검사한다(정규 파일·비실행·허용 확장자만).
#   docs/ 는 문서라 금지 패턴 대상이 아니며 CHECKED 에 세지 않는다(카운트 부풀리기 차단).
#   그 밖의 모든 추적 파일 — 이 검사기 자신·scripts/·hooks/·.github/ 포함 — 은 전역
#   패턴으로 검사한다. 자기면제 없음(P13④). 제품 루트는 전역 + 제품 전용 패턴 둘 다.
set -euo pipefail

unset GIT_DIR GIT_INDEX_FILE GIT_OBJECT_DIRECTORY GIT_WORK_TREE GIT_COMMON_DIR
unset GIT_ALTERNATE_OBJECT_DIRECTORIES

REPO=$(git rev-parse --show-toplevel) || {
  echo "FAIL: repository root unavailable"
  exit 2
}
cd "$REPO"

GLOBAL_PATTERNS=contracts/portal-constants-deny-patterns.txt
PRODUCT_PATTERNS=contracts/portal-constants-deny-patterns-product.txt
PRODUCT_ROOTS="humansearch/src humansearch/tests"
WF=.github/workflows/verify.yml
HOOK=hooks/pre-push
SELF_LINE="bash scripts/acceptance-hs-portal-constants.sh"
SIBLING_LINE="bash scripts/acceptance-hs-portal-constants-mutations.sh"

GCLEAN=$(mktemp)
PCLEAN=$(mktemp)
FILES=$(mktemp)
ERRS=$(mktemp)
cleanup() { rm -f -- "$GCLEAN" "$PCLEAN" "$FILES" "$ERRS"; }
trap cleanup EXIT
trap 'cleanup; trap - EXIT; exit 143' TERM
trap 'cleanup; trap - EXIT; exit 130' INT
trap 'cleanup; trap - EXIT; exit 129' HUP

# 패턴 계약 검증 (G1 acceptance-hs-cleanroom.sh:14-43 방어 재사용):
# 부재/빈 파일/유효 패턴 0개/깨진 표현식/빈 문자열 매치 전부 exit 2 — "검사가 안 돌았는데
# 위반 없음"을 원리적으로 금지한다.
load_patterns() {
  local src="$1" dst="$2" rc=0
  if [ ! -f "$src" ] || [ ! -r "$src" ] || [ ! -s "$src" ]; then
    echo "FAIL: portal pattern contract missing, unreadable, or empty: $src"
    exit 2
  fi
  sed -e 's/\r$//' -e '/^[[:space:]]*#/d' -e '/^[[:space:]]*$/d' "$src" > "$dst"
  if [ ! -s "$dst" ]; then
    echo "FAIL: portal pattern contract has zero effective patterns: $src"
    exit 2
  fi
  printf '\n' | LC_ALL=C grep -aEiqf "$dst" > /dev/null 2> "$ERRS" || rc=$?
  if [ "$rc" -gt 1 ]; then
    echo "FAIL: portal pattern contract contains an invalid expression: $src"
    exit 2
  fi
  if [ "$rc" -eq 0 ]; then
    echo "FAIL: portal pattern contract contains an empty-matching expression: $src"
    exit 2
  fi
}

load_patterns "$GLOBAL_PATTERNS" "$GCLEAN"
load_patterns "$PRODUCT_PATTERNS" "$PCLEAN"

# 제품 루트가 없으면 조용한 skip 이 아니라 검사 불능이다 (사전감사 벡터 5).
for root in $PRODUCT_ROOTS; do
  if [ ! -d "$root" ]; then
    echo "FAIL: product root missing: $root"
    exit 2
  fi
done

if ! git ls-files -z > "$FILES"; then
  echo "FAIL: tracked-file enumeration failed"
  exit 2
fi

checked=0
product_files=0
contract_files=0
forbidden=0
zone_violations=0
errors=0

scan_with() {
  local path="$1" pats="$2" tier="$3" rc=0
  LC_ALL=C grep -aEiqf "$pats" -- "./$path" 2>> "$ERRS" || rc=$?
  if [ "$rc" -eq 0 ]; then
    forbidden=$((forbidden + 1))
    printf '  forbidden(%s): %q\n' "$tier" "$path"
  elif [ "$rc" -gt 1 ]; then
    errors=$((errors + 1))
    printf '  unreadable: %q\n' "$path"
  fi
}

while IFS= read -r -d '' path; do
  case "$path" in
    contracts/*)
      contract_files=$((contract_files + 1))
      mode=$(git ls-files -s -- "$path" | awk '{print $1}')
      case "$mode" in
        100644) ;;
        *)
          zone_violations=$((zone_violations + 1))
          printf '  contracts-zone: %q (mode %s — 데이터 구역엔 정규 비실행 파일만)\n' "$path" "${mode:-?}"
          ;;
      esac
      lower=$(printf '%s' "$path" | tr '[:upper:]' '[:lower:]')
      case "$lower" in
        *.txt|*.json|*.yaml|*.yml|*.md) ;;
        *)
          zone_violations=$((zone_violations + 1))
          printf '  contracts-zone: %q (허용 확장자 밖)\n' "$path"
          ;;
      esac
      continue
      ;;
    docs/*) continue ;;
  esac
  checked=$((checked + 1))
  case "$path" in
    humansearch/src/*|humansearch/tests/*)
      product_files=$((product_files + 1))
      scan_with "$path" "$GCLEAN" global
      scan_with "$path" "$PCLEAN" product
      ;;
    *)
      scan_with "$path" "$GCLEAN" global
      ;;
  esac
done < "$FILES"

# ── 배선 자기 검사 (사전감사 벡터 1·2) ─────────────────────────────────────────
# CI 는 수동 열거(verify.yml)라 여기 등록되지 않으면 "로컬에만 있는 검사"가 되고,
# P15③ 은 그것을 없는 것으로 친다. 이 검사기 자신이 양쪽 배선을 확인한다 —
# 이 검사기가 pre-push 글로브로도 CI 로도 돌기 때문에, 어느 한쪽을 끊는 변경은
# 남은 한쪽에서 이 검사가 exit 1 을 낸다.
wiring_fail=0
wire_bad() { wiring_fail=$((wiring_fail + 1)); printf '  wiring: %s\n' "$1"; }

# 실행 줄 검사: 주석 제거 후 정확한 한 줄(접두 echo·옵션·후미 파이프/무력화 불가)이
# 있어야 하고, 그 줄이 속한 스텝 블록에 if: 조건·오류 무시 설정이 없어야 한다.
ci_line_ok() {
  local tgt="$1"
  awk -v tgt="$tgt" '
    function flush() { if (has && ok) good = 1 }
    /^[[:space:]]*-[[:space:]]*name:/ { flush(); has = 0; ok = 1 }
    {
      line = $0
      sub(/^[[:space:]]+/, "", line)
      sub(/[[:space:]]+$/, "", line)
      if (line == tgt) has = 1
      if (line ~ /^if:/) ok = 0
      if (index(line, "continue" "-on-" "error") > 0) ok = 0
    }
    END { flush(); exit good ? 0 : 1 }
  ' "$WF"
}

if [ ! -f "$WF" ]; then
  wire_bad "CI 워크플로($WF) 부재 — 판정 권한이 있는 쪽이 비어 있다"
else
  ci_line_ok "$SELF_LINE" || wire_bad "CI 에 검사기 실행 줄이 없거나 무력화됨: $SELF_LINE"
  ci_line_ok "$SIBLING_LINE" || wire_bad "CI 에 mutation 실행 줄이 없거나 무력화됨: $SIBLING_LINE"
fi

if [ ! -f "$HOOK" ] || [ ! -x "$HOOK" ]; then
  wire_bad "pre-push 훅 부재 또는 실행 불가 — 로컬 1차 차단이 없다"
else
  if ! grep -qF -- "-o -name 'acceptance-*.sh'" "$HOOK"; then
    wire_bad "pre-push 의 acceptance 글로브 수집식이 사라졌다"
  fi
  found_self=$(find . -maxdepth 2 -name 'acceptance-*.sh' \
    -not -path './worktrees/*' -not -path './.git/*' | grep -cF 'acceptance-hs-portal-constants')
  if [ "$found_self" -lt 2 ]; then
    wire_bad "글로브 수집 재현에서 검사기·mutation 이 다 잡히지 않는다 (found=$found_self)"
  fi
fi

# ── 판정 ─────────────────────────────────────────────────────────────────────
if [ "$forbidden" -eq 0 ]; then
  echo "PASS: portal constants outside contracts 0"
else
  echo "FAIL: portal constants outside contracts $forbidden"
fi
if [ "$zone_violations" -eq 0 ]; then
  echo "PASS: contracts zone violations 0"
else
  echo "FAIL: contracts zone violations $zone_violations"
fi
if [ "$wiring_fail" -eq 0 ]; then
  echo "PASS: ci/pre-push wiring intact"
else
  echo "FAIL: ci/pre-push wiring broken $wiring_fail"
fi
echo "PRODUCT_FILES: $product_files"
echo "CHECKED: $checked"
echo "CONTRACT_FILES: $contract_files"

# 검사 불능(2)이 위반(1)보다 우선한다 — 일부만 읽은 스캔의 "위반 n건"은 믿을 수 없다.
if [ "$errors" -ne 0 ] || [ -s "$ERRS" ]; then
  echo "FAIL: scanner errors $errors"
  exit 2
fi
if [ "$product_files" -lt 2 ]; then
  echo "FAIL: product files $product_files (<2) — 검사 대상이 없어서 통과는 금지 (P20)"
  exit 2
fi
if [ "$checked" -lt 10 ]; then
  echo "FAIL: checked files $checked (<10)"
  exit 2
fi
if [ "$contract_files" -lt 2 ]; then
  echo "FAIL: contract files $contract_files (<2) — 패턴 계약 2벌이 추적되고 있지 않다"
  exit 2
fi
if [ "$forbidden" -ne 0 ] || [ "$zone_violations" -ne 0 ] || [ "$wiring_fail" -ne 0 ]; then
  exit 1
fi
