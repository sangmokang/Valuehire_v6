#!/usr/bin/env bash
# acceptance-hs-portal-constants-hardening.sh — G3 검사기의 V1(codex) 적대검증 결함 5건을
# 봉쇄했는지 증명한다 (2차 RED 정본 — 2차 GREEN 은 이 파일을 바꿀 수 없다).
#
# 계약: docs/engineering/humansearch-g3-portal-constants-goal-2026-08-12.md §1⑩ + 적대 검증 로그
#   봉쇄 대상 (codex verdict 2026-08-12, .claude/private-reviews/codex-g3-verdict-2026-08-12.md):
#   D1 새 표현 8종 미탐 / D2 CI run 블록 선행종료·실패무시 / D3 pre-push 건너뛰기 머리말
#   D4 임시파일 생성 실패가 1로 샘(계약은 2) / D5 docs/ 전체 면제 은닉
#   exit 0 = 전부 봉쇄 증명 | 1 = 하나라도 실패
#
# 판정 규율: 차단 성공은 정확히 exit 1, 검사 불능은 정확히 exit 2 만 센다.
# 자기 오염 방지: 전역 계층에 걸리는 문자열(locator API·XPath·머리말 표식)은 조각 조립.
# 제품 전용 계층 payload 는 이 파일(scripts/)에 적용되지 않으므로 원문 표기가 안전하다.
# 원본 저장소는 절대 변형하지 않는다 — 모든 fixture 는 mktemp 샌드박스에만 쓴다.
set -euo pipefail

unset GIT_DIR GIT_INDEX_FILE GIT_OBJECT_DIRECTORY GIT_WORK_TREE GIT_COMMON_DIR
unset GIT_ALTERNATE_OBJECT_DIRECTORIES

REPO=$(git rev-parse --show-toplevel) || {
  echo "FAIL: repository root unavailable"
  exit 1
}
cd "$REPO"

SCANNER=scripts/acceptance-hs-portal-constants.sh
GPAT=contracts/portal-constants-deny-patterns.txt
PPAT=contracts/portal-constants-deny-patterns-product.txt

for required in "$SCANNER" "$GPAT" "$PPAT"; do
  if [ ! -f "$required" ]; then
    echo "FAIL: required G3 implementation missing: $required"
    exit 1
  fi
done

SNAP0=$(git status --porcelain)

SANDBOX=$(mktemp -d)
cleanup() { rm -rf -- "$SANDBOX"; }
trap cleanup EXIT
trap 'cleanup; trap - EXIT; exit 143' TERM
trap 'cleanup; trap - EXIT; exit 130' INT
trap 'cleanup; trap - EXIT; exit 129' HUP

# ── 조각 조립 payload (전역 계층 회피 필수분만) ────────────────────────────────
SEL_API=$(printf 'page_probe = document.query%s("#pw-field")' 'Selector')
XPATH_WS=$(printf 'LOGIN = "%s %s"' '//input' '[@name=email]')
MARKER=$(printf '# PUSH-%s' 'PERFORMING')
BRAND_DOC=$(printf 'v4 사례: www.sara%s 참고' 'min.co.kr')
WK_SETE=$(printf 'set %se' '+')

write_wf() {
  local d="$1" v="$2"
  local self='bash scripts/acceptance-hs-portal-constants.sh'
  local sib='bash scripts/acceptance-hs-portal-constants-mutations.sh'
  {
    printf 'name: verify\non:\n  push:\n  pull_request:\njobs:\n  verify:\n    runs-on: ubuntu-latest\n    steps:\n'
    printf '      - name: g3\n'
    printf '        run: %s\n' '|'
    case "$v" in
      early_exit) printf '          exit 0\n' ;;
      set_e_off)  printf '          %s\n' "$WK_SETE" ;;
    esac
    printf '          %s\n          %s\n' "$self" "$sib"
    case "$v" in
      set_e_off) printf '          true\n' ;;
    esac
  } > "$d/.github/workflows/verify.yml"
}

total=0
blocked=0
notrun=0
allowed=0
CASE_DIR=""

init_case() {
  total=$((total + 1))
  CASE_DIR="$SANDBOX/case-$total"
  mkdir -p "$CASE_DIR/scripts" "$CASE_DIR/contracts" "$CASE_DIR/hooks" \
    "$CASE_DIR/.github/workflows" "$CASE_DIR/humansearch/src/humansearch" \
    "$CASE_DIR/humansearch/tests" "$CASE_DIR/lib" "$CASE_DIR/docs/sot"
  git -C "$CASE_DIR" init -q
  cp "$SCANNER" "$CASE_DIR/scripts/acceptance-hs-portal-constants.sh"
  printf '#!/usr/bin/env bash\n# wiring probe placeholder\n' \
    > "$CASE_DIR/scripts/acceptance-hs-portal-constants-mutations.sh"
  cp "$GPAT" "$CASE_DIR/contracts/portal-constants-deny-patterns.txt"
  cp "$PPAT" "$CASE_DIR/contracts/portal-constants-deny-patterns-product.txt"
  cp hooks/pre-push "$CASE_DIR/hooks/pre-push"
  chmod +x "$CASE_DIR/hooks/pre-push"
  write_wf "$CASE_DIR" ok
  printf 'PACKAGE_NAME = "humansearch"\n' \
    > "$CASE_DIR/humansearch/src/humansearch/__init__.py"
  printf 'import humansearch\n\n\ndef test_boundary() -> None:\n    assert humansearch.PACKAGE_NAME\n' \
    > "$CASE_DIR/humansearch/tests/test_boundary.py"
  local i
  for i in 1 2 3 4 5 6 7 8; do
    printf 'safe fixture %s\n' "$i" > "$CASE_DIR/lib/filler-$i.txt"
  done
  git -C "$CASE_DIR" add -A
}

run_scanner() {
  SCAN_RC=0
  SCAN_OUT=$(cd "$CASE_DIR" && bash scripts/acceptance-hs-portal-constants.sh 2>&1) || SCAN_RC=$?
}

expect_case() {
  local label="$1" want="$2" needle="$3"
  run_scanner
  if [ "$SCAN_RC" -ne "$want" ]; then
    echo "FAIL: hardening [$label] exit=$SCAN_RC (기대: 정확히 $want)"
    printf '%s\n' "$SCAN_OUT"
    exit 1
  fi
  if [ -n "$needle" ] && ! printf '%s\n' "$SCAN_OUT" | grep -qE "$needle"; then
    echo "FAIL: hardening [$label] 이유가 다르다 (exit=$SCAN_RC)"
    printf '%s\n' "$SCAN_OUT"
    exit 1
  fi
  case "$want" in
    0) allowed=$((allowed + 1)) ;;
    1) blocked=$((blocked + 1)) ;;
    2) notrun=$((notrun + 1)) ;;
  esac
  printf 'ok [%s] exit=%s\n' "$label" "$want"
}

plant() {
  local rel="$1" payload="$2"
  mkdir -p "$(dirname "$CASE_DIR/$rel")"
  printf '%s\n' "$payload" > "$CASE_DIR/$rel"
  git -C "$CASE_DIR" add "$rel"
}

FORBIDDEN_RE='^FAIL: portal constants outside contracts [1-9][0-9]*$'
WIRE_RE='^FAIL: ci/pre-push wiring broken [1-9][0-9]*$'

# ── 0) baseline: 보강 뒤에도 깨끗한 트리는 정확히 0 ───────────────────────────
init_case
expect_case "hardening baseline" 0 '^PASS: portal constants outside contracts 0$'

# ── D1) codex 미탐 8종 — 전부 정확히 exit 1 ──────────────────────────────────
init_case
plant "humansearch/src/humansearch/net_probe.py" 'REMOTE = "10.77.4.9:9444"'
expect_case "D1 IPv4 비루프백 host:port" 1 "$FORBIDDEN_RE"

init_case
plant "humansearch/tests/test_portal_host.py" 'PORTAL = "jobs-r9.vendor.ai"'
expect_case "D1 미등재 .ai 도메인" 1 "$FORBIDDEN_RE"

init_case
plant "humansearch/src/humansearch/css_desc_${RANDOM}.py" 'LOGIN = ".account-card input"'
expect_case "D1 CSS 자손 셀렉터" 1 "$FORBIDDEN_RE"

init_case
plant "humansearch/src/humansearch/css_attr.js" 'LOGIN = "[data-testid=sign-in]"'
expect_case "D1 CSS 속성 셀렉터" 1 "$FORBIDDEN_RE"

init_case
plant "humansearch/tests/xpath_ws_probe.py" "$XPATH_WS"
expect_case "D1 공백 XPath" 1 "$FORBIDDEN_RE"

init_case
plant "humansearch/src/humansearch/cdp_quoted.py" 'CDP_PORT = "9333"'
expect_case "D1 따옴표 CDP 포트" 1 "$FORBIDDEN_RE"

init_case
plant "humansearch/src/humansearch/cdp_map.yaml.py" 'CDP_PORT: 9333'
expect_case "D1 매핑형 CDP 포트" 1 "$FORBIDDEN_RE"

init_case
plant "humansearch/tests/ipv6_probe.py" 'REMOTE = "[::1]:9333"'
expect_case "D1 IPv6 루프백 host:port" 1 "$FORBIDDEN_RE"

# ── D2) CI run 블록 선행 종료·실패 중단 해제 — 배선 훼손으로 exit 1 ───────────
init_case
write_wf "$CASE_DIR" early_exit
git -C "$CASE_DIR" add .github/workflows/verify.yml
expect_case "D2 run 블록 선행 exit 0" 1 "$WIRE_RE"

init_case
write_wf "$CASE_DIR" set_e_off
git -C "$CASE_DIR" add .github/workflows/verify.yml
expect_case "D2 run 블록 실패 중단 해제" 1 "$WIRE_RE"

# ── D3) pre-push 건너뛰기 머리말 — 자기검사가 잡아야 한다 ─────────────────────
init_case
awk -v m="$MARKER" 'NR==2{print m} {print}' "$SCANNER" \
  > "$CASE_DIR/scripts/acceptance-hs-portal-constants.sh"
git -C "$CASE_DIR" add scripts/acceptance-hs-portal-constants.sh
expect_case "D3 검사기 머리말 표식" 1 "$WIRE_RE"

init_case
printf '#!/usr/bin/env bash\n%s\n' "$MARKER" \
  > "$CASE_DIR/scripts/acceptance-hs-portal-constants-mutations.sh"
git -C "$CASE_DIR" add scripts/acceptance-hs-portal-constants-mutations.sh
expect_case "D3 mutation 시험 머리말 표식" 1 "$WIRE_RE"

# ── D4) 임시 작업공간 생성 실패 — 정확히 exit 2 ──────────────────────────────
init_case
mkdir -p "$CASE_DIR/fakebin"
printf '#!/bin/sh\nexit 1\n' > "$CASE_DIR/fakebin/mktemp"
chmod +x "$CASE_DIR/fakebin/mktemp"
SCAN_RC=0
SCAN_OUT=$(cd "$CASE_DIR" && PATH="$CASE_DIR/fakebin:$PATH" \
  bash scripts/acceptance-hs-portal-constants.sh 2>&1) || SCAN_RC=$?
if [ "$SCAN_RC" -ne 2 ]; then
  echo "FAIL: hardening [D4 임시공간 생성 실패] exit=$SCAN_RC (기대: 정확히 2)"
  printf '%s\n' "$SCAN_OUT"
  exit 1
fi
if ! printf '%s\n' "$SCAN_OUT" | grep -q 'temp workspace unavailable'; then
  echo "FAIL: hardening [D4 임시공간 생성 실패] 이유가 다르다 (exit=$SCAN_RC)"
  printf '%s\n' "$SCAN_OUT"
  exit 1
fi
notrun=$((notrun + 1))
printf 'ok [%s] exit=%s\n' "D4 임시공간 생성 실패" 2

# ── D5) docs/ 은닉 — 문서 확장자·비실행만 면제 ────────────────────────────────
init_case
plant "docs/run_portal_probe.py" "$SEL_API"
expect_case "D5 docs 실행 코드 은닉" 1 "$FORBIDDEN_RE"

init_case
plant "docs/sot/failure-cases.md" "$BRAND_DOC"
expect_case "D5 정당한 문서 인용 — 오탐 금지" 0 '^PASS: portal constants outside contracts 0$'

init_case
plant "docs/tool-note.md" "$BRAND_DOC"
chmod +x "$CASE_DIR/docs/tool-note.md"
git -C "$CASE_DIR" add docs/tool-note.md
expect_case "D5 실행권한 달린 문서 위장" 1 "$FORBIDDEN_RE"

# ── 자기 배선: 이 보강 시험 자신도 CI 실행 줄에 있어야 한다 ───────────────────
total=$((total + 1))
WF_REAL=.github/workflows/verify.yml
if [ ! -f "$WF_REAL" ] || ! grep -v '^[[:space:]]*#' "$WF_REAL" | grep -qE \
  '^[[:space:]]*bash scripts/acceptance-hs-portal-constants-hardening\.sh[[:space:]]*$'; then
  echo "FAIL: hardening 자신이 CI($WF_REAL) 실행 줄에 없다 — 로컬에만 있는 검사는 없는 것으로 친다 (P15③)"
  exit 1
fi
blocked=$((blocked + 1))
printf 'ok [%s]\n' "hardening 자기 배선(CI 실행 줄)"

# ── 마무리: 원본 저장소 무변형 확인 ──────────────────────────────────────────
SNAP1=$(git status --porcelain)
if [ "$SNAP0" != "$SNAP1" ]; then
  echo "FAIL: hardening 시험이 원본 저장소를 변형했다 (검증기 오염 금지)"
  exit 1
fi

echo "PASS: portal-constants hardening blocked $blocked/$total (allowed $allowed, notrun $notrun)"
