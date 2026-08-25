#!/usr/bin/env bash
# acceptance-hs-portal-constants-hardening5.sh — G3의 YAML 구조 판별과 의미 기반 화면 찾기
# 방어를 독립 표본으로 증명한다. 기존 RED 원장 3벌은 동결 상태로 유지한다.
#
# 계약:
#   F1 실제 jobs.*.steps[*].run 밖의 환경 변수 문자열에만 G3 명령이 있으면 정확히 exit 1
#   F2 제품 코드의 Playwright 의미 기반 화면 찾기 4종은 각각 정확히 exit 1
#   차단 성공은 검사기의 정확한 exit 1과 해당 FAIL 사유를 함께 확인한다.
set -euo pipefail

unset GIT_DIR GIT_INDEX_FILE GIT_OBJECT_DIRECTORY GIT_WORK_TREE GIT_COMMON_DIR
unset GIT_ALTERNATE_OBJECT_DIRECTORIES

REPO=$(git rev-parse --show-toplevel) || {
  echo "FAIL: repository root unavailable"
  exit 1
}
cd "$REPO"

SCANNER_SOURCE=${G3_SCANNER_SOURCE:-scripts/acceptance-hs-portal-constants.sh}
GLOBAL_PATTERNS_SOURCE=${G3_GLOBAL_PATTERNS_SOURCE:-contracts/portal-constants-deny-patterns.txt}
PRODUCT_PATTERNS_SOURCE=${G3_PRODUCT_PATTERNS_SOURCE:-contracts/portal-constants-deny-patterns-product.txt}
MODE=${1:-all}

case "$MODE" in
  all|f1|f2) ;;
  *)
    echo "FAIL: usage: $0 [all|f1|f2]"
    exit 1
    ;;
esac

for required in "$SCANNER_SOURCE" "$GLOBAL_PATTERNS_SOURCE" "$PRODUCT_PATTERNS_SOURCE"; do
  if [ ! -f "$required" ]; then
    echo "FAIL: required G3 source missing: $required"
    exit 1
  fi
done
if ! command -v ruby >/dev/null 2>&1; then
  echo "FAIL: Ruby YAML parser unavailable"
  exit 1
fi

SNAP0=$(git status --porcelain)
SANDBOX=$(mktemp -d)
cleanup() { rm -rf -- "$SANDBOX"; }
trap cleanup EXIT
trap 'cleanup; trap - EXIT; exit 143' TERM
trap 'cleanup; trap - EXIT; exit 130' INT
trap 'cleanup; trap - EXIT; exit 129' HUP

# 검사기가 이 시험 파일 자체를 읽어도 금지 원문이 되지 않도록 API 이름은 조각으로 만든다.
GBR=$(printf 'BUTTON = page.get_by_%s("button", name="Sign in")' 'role')
GBL=$(printf 'EMAIL = page.get_by_%s("Email address")' 'label')
GBT=$(printf 'SUBMIT = page.get_by_%s("submit-login")' 'test_id')
GBX=$(printf 'LINK = page.get_by_%s("Log in")' 'text')

G3_NAMES="acceptance-hs-portal-constants acceptance-hs-portal-constants-mutations acceptance-hs-portal-constants-hardening acceptance-hs-portal-constants-hardening2 acceptance-hs-portal-constants-hardening3 acceptance-hs-portal-constants-hardening4 acceptance-hs-portal-constants-hardening5"

write_commands() {
  local indent="$1" g
  for g in $G3_NAMES; do
    printf '%sbash scripts/%s.sh\n' "$indent" "$g"
  done
}

write_wf_ok() {
  {
    printf 'name: verify\non:\n  push:\n  pull_request:\njobs:\n  verify:\n    runs-on: ubuntu-latest\n    steps:\n'
    printf '      - name: g3\n        run: |\n'
    write_commands '          '
  } > "$1/.github/workflows/verify.yml"
}

# 유효한 YAML의 여러 줄 큰따옴표 값 안에 run 모양과 G3 명령을 넣는다. 구조상 실제
# 실행 칸은 echo 한 줄뿐이며, G3 명령은 env.NOTE 문자열에만 존재한다.
write_wf_env_only() {
  {
    printf 'name: verify\non:\n  push:\n  pull_request:\njobs:\n  verify:\n    runs-on: ubuntu-latest\n    steps:\n'
    printf '      - name: harmless carrier\n'
    printf '        run: echo "G3 disabled; payload only in env"\n'
    printf '        env:\n'
    printf '          NOTE: "fake G3\n'
    printf '            run: |\n'
    write_commands '              '
    printf '            "\n'
  } > "$1/.github/workflows/verify.yml"
}

assert_env_only_shape() {
  local wf="$1" shape
  shape=$(ruby -ryaml -e '
    data = YAML.safe_load(File.read(ARGV.fetch(0)), permitted_classes: [], permitted_symbols: [], aliases: false)
    steps = data.fetch("jobs").values.flat_map { |job| job.fetch("steps", []) }
    needle = "bash scripts/acceptance-hs-portal-constants.sh"
    runs = steps.count { |step| step.is_a?(Hash) && step["run"].to_s.include?(needle) }
    envs = steps.count do |step|
      step.is_a?(Hash) && step.fetch("env", {}).values.any? { |value| value.to_s.include?(needle) }
    end
    puts "RUN_FIELDS_WITH_G3=#{runs}"
    puts "ENV_VALUES_WITH_G3=#{envs}"
  ' "$wf") || {
    echo "FAIL: F1 fixture is not valid YAML"
    exit 1
  }
  if [ "$shape" != $'RUN_FIELDS_WITH_G3=0\nENV_VALUES_WITH_G3=1' ]; then
    echo "FAIL: F1 fixture has the wrong YAML ownership"
    printf '%s\n' "$shape"
    exit 1
  fi
  printf '%s\n' "$shape"
}

total=0
blocked=0
allowed=0
wiring=0
CASE_DIR=""

init_case() {
  total=$((total + 1))
  CASE_DIR="$SANDBOX/case-$total"
  mkdir -p "$CASE_DIR/scripts" "$CASE_DIR/contracts" "$CASE_DIR/hooks" \
    "$CASE_DIR/.github/workflows" "$CASE_DIR/humansearch/src/humansearch" \
    "$CASE_DIR/humansearch/tests" "$CASE_DIR/lib"
  git -C "$CASE_DIR" init -q
  cp "$SCANNER_SOURCE" "$CASE_DIR/scripts/acceptance-hs-portal-constants.sh"
  local f
  for f in mutations hardening hardening2 hardening3 hardening4 hardening5; do
    printf '#!/usr/bin/env bash\n# wiring probe placeholder\n' \
      > "$CASE_DIR/scripts/acceptance-hs-portal-constants-$f.sh"
  done
  cp "$GLOBAL_PATTERNS_SOURCE" "$CASE_DIR/contracts/portal-constants-deny-patterns.txt"
  cp "$PRODUCT_PATTERNS_SOURCE" "$CASE_DIR/contracts/portal-constants-deny-patterns-product.txt"
  # 2026-08-25 동결 예외(hardening7): 검사기가 요구하는 계약이 3벌 늘었다. 공격 내용과
  # 기대 종료코드는 그대로 두고 입력만 맞춘다 — 2026-08-13 runs-on 표본 조정과 같은 처리.
  # 루트 계약만은 표본 자신의 구조를 적는다. 표본 저장소에는 apps/admin 이 없고,
  # "등재했는데 실재하지 않는 루트 = exit 2" 규칙이 그 불일치를 정확히 잡기 때문이다.
  printf 'humansearch/src\nhumansearch/tests\n' \
    > "$CASE_DIR/contracts/portal-constants-product-roots.txt"
  cp contracts/portal-constants-nonoperational-addresses.txt "$CASE_DIR/contracts/portal-constants-nonoperational-addresses.txt"
  cp contracts/portal-constants-nonoperational-suffixes.txt "$CASE_DIR/contracts/portal-constants-nonoperational-suffixes.txt"
  cp contracts/portal-constants-nonproduct-paths.txt "$CASE_DIR/contracts/portal-constants-nonproduct-paths.txt"
  cp contracts/portal-constants-ambiguous-suffixes.txt "$CASE_DIR/contracts/portal-constants-ambiguous-suffixes.txt"
  cp hooks/pre-push "$CASE_DIR/hooks/pre-push"
  chmod +x "$CASE_DIR/hooks/pre-push"
  write_wf_ok "$CASE_DIR"
  printf 'PACKAGE_NAME = "humansearch"\n' > "$CASE_DIR/humansearch/src/humansearch/__init__.py"
  printf 'def test_boundary():\n    assert True\n' > "$CASE_DIR/humansearch/tests/test_boundary.py"
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
    echo "FAIL: hardening5 [$label] exit=$SCAN_RC (기대: 정확히 $want)"
    printf '%s\n' "$SCAN_OUT"
    exit 1
  fi
  if ! printf '%s\n' "$SCAN_OUT" | grep -qE "$needle"; then
    echo "FAIL: hardening5 [$label] 이유가 다르다 (exit=$SCAN_RC)"
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
  printf '%s\n' "$payload" > "$CASE_DIR/$rel"
  git -C "$CASE_DIR" add "$rel"
}

FORBIDDEN_RE='^FAIL: portal constants outside contracts [1-9][0-9]*$'
WIRE_RE='^FAIL: ci/pre-push wiring broken [1-9][0-9]*$'

init_case
expect_case "hardening5 baseline" 0 '^PASS: ci/pre-push wiring intact$'

if [ "$MODE" = all ] || [ "$MODE" = f1 ]; then
  init_case
  write_wf_env_only "$CASE_DIR"
  git -C "$CASE_DIR" add .github/workflows/verify.yml
  assert_env_only_shape "$CASE_DIR/.github/workflows/verify.yml"
  expect_case "F1 quoted env value is not a run field" 1 "$WIRE_RE"
fi

if [ "$MODE" = all ] || [ "$MODE" = f2 ]; then
  init_case
  plant "humansearch/src/humansearch/login_role.py" "$GBR"
  expect_case "F2 semantic role finder" 1 "$FORBIDDEN_RE"

  init_case
  plant "humansearch/tests/login_label.py" "$GBL"
  expect_case "F2 semantic label finder" 1 "$FORBIDDEN_RE"

  init_case
  plant "humansearch/src/humansearch/login_test_id.py" "$GBT"
  expect_case "F2 semantic test-id finder" 1 "$FORBIDDEN_RE"

  init_case
  plant "humansearch/tests/login_text.py" "$GBX"
  expect_case "F2 semantic text finder" 1 "$FORBIDDEN_RE"
fi

if [ "$MODE" = all ]; then
  total=$((total + 1))
  if ! grep -v '^[[:space:]]*#' .github/workflows/verify.yml | grep -qE \
    '^[[:space:]]*bash scripts/acceptance-hs-portal-constants-hardening5\.sh[[:space:]]*$'; then
    echo "FAIL: hardening5 자신이 CI 실행 줄에 없다"
    exit 1
  fi
  blocked=$((blocked + 1))
  wiring=1
  printf 'ok [%s]\n' "hardening5 자기 배선(CI 실행 줄)"
fi

SNAP1=$(git status --porcelain)
if [ "$SNAP0" != "$SNAP1" ]; then
  echo "FAIL: hardening5 시험이 원본 저장소를 변형했다"
  exit 1
fi

echo "PASS: portal-constants hardening5 cases $total (blocked-mutations $((blocked - wiring)), clean-baselines $allowed, wiring-present $wiring)"
