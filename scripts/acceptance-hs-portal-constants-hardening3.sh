#!/usr/bin/env bash
# acceptance-hs-portal-constants-hardening3.sh — V1(codex) 3차 적대검증의 신규 결함을
# 봉쇄했는지 증명한다 (4차 RED 정본 — 4차 GREEN 은 이 파일을 바꿀 수 없다).
#
# 계약: docs/engineering/humansearch-g3-portal-constants-goal-2026-08-12.md §1⑩ + 적대 검증 로그
#   봉쇄 대상 (codex 3차 verdict, .claude/private-reviews/codex-g3-verdict3-2026-08-12.md):
#   F1(치명) CI 스텝의 env 값 문자열 안에 가짜 G3 단계를 넣으면 실행 0회인데 배선 통과
#   F2(높음) 의미 기반 화면 찾기 API 계열(Playwright get-by-* 4종) + element[attr] CSS 미탐
#     — 이 파일의 라벨·주석은 그 API 이름을 조각으로만 적는다(전역 계층 자기 매칭 회피).
#   판정 규율: 차단 성공은 정확히 exit 1 만 센다.
#
# 자기 오염 방지: get_by_* 는 전역 계층이므로 이 파일에 원문으로 두면 자기 매칭된다 → 조각 조립.
# env 우회 YAML 은 검사 대상 언어가 아니라 워크플로라 원문 표기 안전. 원본 저장소 무변형.
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

# ── 조각 조립 payload (전역 계층 회피) ────────────────────────────────────────
GBR=$(printf 'BTN = page.get_by_%s("button", name="Sign in")' 'role')
GBL=$(printf 'EMAIL = page.get_by_%s("Email address")' 'label')
GBT=$(printf 'SUBMIT = page.get_by_%s("submit-login")' 'test_id')
GBX=$(printf 'LINK = page.get_by_%s("Log in")' 'text')
ELA=$(printf 'BTN = %sbutton[type="submit"]%s' "'" "'")

G3_STEP='      - name: HumanSearch G3 포털 상수·locator 경계'

write_wf() {
  local d="$1" v="$2"
  local self='bash scripts/acceptance-hs-portal-constants.sh'
  local sib='bash scripts/acceptance-hs-portal-constants-mutations.sh'
  local hard='bash scripts/acceptance-hs-portal-constants-hardening.sh'
  local hard2='bash scripts/acceptance-hs-portal-constants-hardening2.sh'
  local hard3='bash scripts/acceptance-hs-portal-constants-hardening3.sh'
  {
    printf 'name: verify\non:\n  push:\n  pull_request:\njobs:\n  verify:\n    runs-on: ubuntu-latest\n    steps:\n'
    case "$v" in
      env_carrier)
        # 실제 G3 스텝은 삭제, 실행 명령은 echo. 정확한 5줄은 env 값 문자열 안에만 존재.
        printf '      - name: harmless note carrier\n'
        printf '        run: echo "G3 disabled; payload only in env"\n'
        printf '        env:\n'
        printf '          NOTE: |\n'
        printf '            - name: fake G3\n'
        printf '              run: |\n'
        printf '                %s\n                %s\n                %s\n                %s\n                %s\n' \
          "$self" "$sib" "$hard" "$hard2" "$hard3"
        ;;
      *)
        printf '%s\n' "$G3_STEP"
        printf '        run: %s\n' '|'
        printf '          %s\n          %s\n          %s\n          %s\n          %s\n' \
          "$self" "$sib" "$hard" "$hard2" "$hard3"
        ;;
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
  local f
  for f in mutations hardening hardening2 hardening3; do
    printf '#!/usr/bin/env bash\n# wiring probe placeholder\n' \
      > "$CASE_DIR/scripts/acceptance-hs-portal-constants-$f.sh"
  done
  cp "$GPAT" "$CASE_DIR/contracts/portal-constants-deny-patterns.txt"
  cp "$PPAT" "$CASE_DIR/contracts/portal-constants-deny-patterns-product.txt"
  # 2026-08-25 동결 예외(hardening7): 검사기가 요구하는 계약이 3벌 늘었다. 공격 내용과
  # 기대 종료코드는 그대로 두고 입력만 맞춘다 — 2026-08-13 runs-on 표본 조정과 같은 처리.
  # 루트 계약만은 표본 자신의 구조를 적는다. 표본 저장소에는 apps/admin 이 없고,
  # "등재했는데 실재하지 않는 루트 = exit 2" 규칙이 그 불일치를 정확히 잡기 때문이다.
  printf 'humansearch/src\nhumansearch/tests\n' \
    > "$CASE_DIR/contracts/portal-constants-product-roots.txt"
  cp contracts/portal-constants-nonoperational-addresses.txt "$CASE_DIR/contracts/portal-constants-nonoperational-addresses.txt"
  cp contracts/portal-constants-nonoperational-suffixes.txt "$CASE_DIR/contracts/portal-constants-nonoperational-suffixes.txt"
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
    echo "FAIL: hardening3 [$label] exit=$SCAN_RC (기대: 정확히 $want)"
    printf '%s\n' "$SCAN_OUT"
    exit 1
  fi
  if [ -n "$needle" ] && ! printf '%s\n' "$SCAN_OUT" | grep -qE "$needle"; then
    echo "FAIL: hardening3 [$label] 이유가 다르다 (exit=$SCAN_RC)"
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

# ── 0) baseline: 5줄 실제 스텝은 정확히 0 ─────────────────────────────────────
init_case
expect_case "hardening3 baseline" 0 '^PASS: portal constants outside contracts 0$'

# ── F1) env 값 문자열 안 가짜 G3 단계 — 실행 0회, 배선 훼손 exit 1 [치명] ──────
init_case
write_wf "$CASE_DIR" env_carrier
git -C "$CASE_DIR" add .github/workflows/verify.yml
expect_case "F1 env 값 속 가짜 G3 단계" 1 "$WIRE_RE"

# ── F2) 의미 기반 화면 찾기 API + element[attr] CSS — forbidden exit 1 ────────
init_case
plant "humansearch/src/humansearch/login_role.py" "$GBR"
expect_case "F2 semantic role finder" 1 "$FORBIDDEN_RE"

init_case
plant "humansearch/tests/login_label.py" "$GBL"
expect_case "F2 semantic label finder" 1 "$FORBIDDEN_RE"

init_case
plant "humansearch/src/humansearch/login_tid.py" "$GBT"
expect_case "F2 semantic testid finder" 1 "$FORBIDDEN_RE"

init_case
plant "humansearch/tests/login_text.py" "$GBX"
expect_case "F2 semantic text finder" 1 "$FORBIDDEN_RE"

init_case
plant "humansearch/src/humansearch/login_css.js" "$ELA"
expect_case "F2 element[attr] CSS 셀렉터" 1 "$FORBIDDEN_RE"

# ── 자기 배선: 이 시험 자신도 CI 실행 줄에 있어야 한다 ────────────────────────
total=$((total + 1))
WF_REAL=.github/workflows/verify.yml
if [ ! -f "$WF_REAL" ] || ! grep -v '^[[:space:]]*#' "$WF_REAL" | grep -qE \
  '^[[:space:]]*bash scripts/acceptance-hs-portal-constants-hardening3\.sh[[:space:]]*$'; then
  echo "FAIL: hardening3 자신이 CI($WF_REAL) 실행 줄에 없다 — 로컬에만 있는 검사는 없는 것으로 친다 (P15③)"
  exit 1
fi
blocked=$((blocked + 1))
printf 'ok [%s]\n' "hardening3 자기 배선(CI 실행 줄)"

# ── 마무리: 원본 저장소 무변형 확인 ──────────────────────────────────────────
SNAP1=$(git status --porcelain)
if [ "$SNAP0" != "$SNAP1" ]; then
  echo "FAIL: hardening3 시험이 원본 저장소를 변형했다 (검증기 오염 금지)"
  exit 1
fi

echo "PASS: portal-constants hardening3 cases $total (blocked-mutations $((blocked - 1)), clean-baselines $allowed, wiring-present 1)"
