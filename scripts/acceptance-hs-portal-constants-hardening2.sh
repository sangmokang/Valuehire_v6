#!/usr/bin/env bash
# acceptance-hs-portal-constants-hardening2.sh — V1(codex) 2차 적대검증의 신규 결함 3축을
# 봉쇄했는지 증명한다 (3차 RED 정본 — 3차 GREEN 은 이 파일을 바꿀 수 없다).
#
# 계약: docs/engineering/humansearch-g3-portal-constants-goal-2026-08-12.md §1⑩ + 적대 검증 로그
#   봉쇄 대상 (codex 2차 verdict, .claude/private-reviews/codex-g3-verdict2-2026-08-12.md):
#   N1 새 직접 표현 10종 미탐 (TLD·단일라벨 호스트·한자리 포트·포트 키·camelCase 포트·
#      따옴표 값 CSS 속성·id 자손·백틱 CSS·절대 XPath·함수형 XPath)
#   N2 CI run 블록을 셸 제어문(if false; then)으로 감싸 실행 0회 [치명]
#   N3 hardening CI 줄 삭제를 아무도 못 잡음 / pre-push 선행 exit 0
#   판정 규율: 차단 성공은 정확히 exit 1 만 센다.
#
# 자기 오염 방지: 이 파일은 scripts/ 에 있어 제품 전용 계층이 적용되지 않으므로 제품 전용
# payload 는 원문 표기가 안전하다(전역 계층 매치 여부는 payload 마다 확인 완료). 전역 계층에
# 걸릴 수 있는 문자열은 조각 조립한다. 원본 저장소는 절대 변형하지 않는다.
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

write_wf() {
  local d="$1" v="$2"
  local self='bash scripts/acceptance-hs-portal-constants.sh'
  local sib='bash scripts/acceptance-hs-portal-constants-mutations.sh'
  local hard='bash scripts/acceptance-hs-portal-constants-hardening.sh'
  {
    printf 'name: verify\njobs:\n  verify:\n    steps:\n'
    printf '      - name: g3\n'
    printf '        run: %s\n' '|'
    printf '          # G3 boundary step\n'
    case "$v" in
      shell_if) printf '          if false; then\n' ;;
    esac
    case "$v" in
      no_hardening) printf '          %s\n          %s\n' "$self" "$sib" ;;
      *)            printf '          %s\n          %s\n          %s\n' "$self" "$sib" "$hard" ;;
    esac
    case "$v" in
      shell_if)   printf '          fi\n' ;;
      stray_true) printf '          true\n' ;;
    esac
  } > "$d/.github/workflows/verify.yml"
}

total=0
blocked=0
allowed=0
CASE_DIR=""

init_case() {
  total=$((total + 1))
  CASE_DIR="$SANDBOX/case-$total"
  mkdir -p "$CASE_DIR/scripts" "$CASE_DIR/contracts" "$CASE_DIR/hooks" \
    "$CASE_DIR/.github/workflows" "$CASE_DIR/humansearch/src/humansearch" \
    "$CASE_DIR/humansearch/tests" "$CASE_DIR/lib"
  git -C "$CASE_DIR" init -q
  cp "$SCANNER" "$CASE_DIR/scripts/acceptance-hs-portal-constants.sh"
  printf '#!/usr/bin/env bash\n# wiring probe placeholder\n' \
    > "$CASE_DIR/scripts/acceptance-hs-portal-constants-mutations.sh"
  printf '#!/usr/bin/env bash\n# wiring probe placeholder\n' \
    > "$CASE_DIR/scripts/acceptance-hs-portal-constants-hardening.sh"
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
    echo "FAIL: hardening2 [$label] exit=$SCAN_RC (기대: 정확히 $want)"
    printf '%s\n' "$SCAN_OUT"
    exit 1
  fi
  if [ -n "$needle" ] && ! printf '%s\n' "$SCAN_OUT" | grep -qE "$needle"; then
    echo "FAIL: hardening2 [$label] 이유가 다르다 (exit=$SCAN_RC)"
    printf '%s\n' "$SCAN_OUT"
    exit 1
  fi
  case "$want" in
    0) allowed=$((allowed + 1)) ;;
    1) blocked=$((blocked + 1)) ;;
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

# ── 0) baseline: 3파일 + 3줄 + 블록 내 주석은 정확히 0 ────────────────────────
init_case
expect_case "hardening2 baseline" 0 '^PASS: portal constants outside contracts 0$'

# ── N1) codex 2차 미탐 10종 — 전부 정확히 exit 1 ─────────────────────────────
init_case
plant "humansearch/src/deep/net/tld_probe.py" 'PORTAL = "jobs.vendor.biz"'
expect_case "N1-1 미등재 .biz 도메인" 1 "$FORBIDDEN_RE"

init_case
plant "humansearch/tests/deep/net/host_probe.cfg" 'REMOTE = "portal:9444"'
expect_case "N1-2 단일 라벨 호스트:포트" 1 "$FORBIDDEN_RE"

init_case
plant "humansearch/src/deep/net/port1_probe.toml" 'REMOTE = "10.77.4.9:8"'
expect_case "N1-3 한 자리 포트" 1 "$FORBIDDEN_RE"

init_case
plant "humansearch/tests/deep/net/json_probe.json" '{"port": 9333}'
expect_case "N1-4 JSON 따옴표 포트 키" 1 "$FORBIDDEN_RE"

init_case
plant "humansearch/src/deep/net/camel_probe.js" 'cdpPort = 9333'
expect_case "N1-5 camelCase 포트 변수" 1 "$FORBIDDEN_RE"

init_case
plant "humansearch/tests/deep/ui/attrq_probe.js" 'LOGIN = '"'"'[data-testid="sign-in"]'"'"''
expect_case "N1-6 따옴표 값 CSS 속성" 1 "$FORBIDDEN_RE"

init_case
plant "humansearch/src/deep/ui/iddesc_probe.py" 'LOGIN = "#login input"'
expect_case "N1-7 CSS id 자손" 1 "$FORBIDDEN_RE"

init_case
plant "humansearch/src/deep/ui/backtick_probe.js" 'LOGIN = `#login`'
expect_case "N1-8 백틱 CSS id" 1 "$FORBIDDEN_RE"

init_case
plant "humansearch/tests/deep/ui/absxpath_probe.py" 'LOGIN = "/html/body/input"'
expect_case "N1-9 절대 XPath" 1 "$FORBIDDEN_RE"

init_case
plant "humansearch/src/deep/ui/funcxpath_probe.py" 'LOGIN = '"'"'//input[contains(@name, "email")]'"'"''
expect_case "N1-10 함수형 XPath" 1 "$FORBIDDEN_RE"

# ── N2) CI run 블록을 셸 제어문으로 감싸기 — 실행 0회 우회 [치명] ─────────────
init_case
write_wf "$CASE_DIR" shell_if
git -C "$CASE_DIR" add .github/workflows/verify.yml
expect_case "N2 셸 if-false 감싸기" 1 "$WIRE_RE"

init_case
write_wf "$CASE_DIR" stray_true
git -C "$CASE_DIR" add .github/workflows/verify.yml
expect_case "N2 블록 내 이물질 줄(true)" 1 "$WIRE_RE"

# ── N3) hardening CI 줄 삭제 + pre-push 선행 종료 ─────────────────────────────
init_case
write_wf "$CASE_DIR" no_hardening
git -C "$CASE_DIR" add .github/workflows/verify.yml
expect_case "N3 hardening 실행 줄 삭제" 1 "$WIRE_RE"

init_case
awk 'NR==2{print "exit 0"} {print}' hooks/pre-push > "$CASE_DIR/hooks/pre-push"
chmod +x "$CASE_DIR/hooks/pre-push"
git -C "$CASE_DIR" add hooks/pre-push
expect_case "N3 pre-push 선행 exit 0" 1 "$WIRE_RE"

# ── 자기 배선: 이 시험 자신도 CI 실행 줄에 있어야 한다 ────────────────────────
total=$((total + 1))
WF_REAL=.github/workflows/verify.yml
if [ ! -f "$WF_REAL" ] || ! grep -v '^[[:space:]]*#' "$WF_REAL" | grep -qE \
  '^[[:space:]]*bash scripts/acceptance-hs-portal-constants-hardening2\.sh[[:space:]]*$'; then
  echo "FAIL: hardening2 자신이 CI($WF_REAL) 실행 줄에 없다 — 로컬에만 있는 검사는 없는 것으로 친다 (P15③)"
  exit 1
fi
blocked=$((blocked + 1))
printf 'ok [%s]\n' "hardening2 자기 배선(CI 실행 줄)"

# ── 마무리: 원본 저장소 무변형 확인 ──────────────────────────────────────────
SNAP1=$(git status --porcelain)
if [ "$SNAP0" != "$SNAP1" ]; then
  echo "FAIL: hardening2 시험이 원본 저장소를 변형했다 (검증기 오염 금지)"
  exit 1
fi

echo "PASS: portal-constants hardening2 cases $total (blocked-mutations $((blocked - 1)), clean-baselines $allowed, wiring-present 1)"
