#!/usr/bin/env bash
# acceptance-hs-portal-constants-hardening4.sh — codeaudit(2026-08-13)가 찾은 배선 우회를
# 봉쇄했는지 증명한다 (5차 RED 정본 — 5차 GREEN 은 이 파일을 바꿀 수 없다).
#
# 계약: docs/engineering/humansearch-g3-portal-constants-goal-2026-08-12.md §1⑩ + 적대 검증 로그
#   봉쇄 대상 (codeaudit A2, V1 3차 F1 과 동형의 미봉쇄 잔여):
#   실제 G3 스텝을 지우고 임의 리터럴 스칼라 키(description:/note:/summary:/run-name: 등 `키: |`)
#   안에 가짜 G3 단계를 숨기면 배선 검사가 실행 0회를 정상으로 오인한다.
#   검사기는 `env:` 만 배제했으나 다른 모든 `키: |` 리터럴 블록도 실행 칸이 아니다.
#   판정 규율: 차단 성공은 정확히 exit 1 만 센다.
#
# 원본 저장소 무변형. 은닉 payload 는 워크플로 텍스트라 원문 표기 안전.
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

G3_NAMES="acceptance-hs-portal-constants acceptance-hs-portal-constants-mutations acceptance-hs-portal-constants-hardening acceptance-hs-portal-constants-hardening2 acceptance-hs-portal-constants-hardening3 acceptance-hs-portal-constants-hardening4"

write_wf_ok() {
  {
    printf 'name: verify\non:\n  push:\n  pull_request:\njobs:\n  verify:\n    runs-on: ubuntu-latest\n    steps:\n'
    printf '      - name: g3\n        run: |\n'
    local g
    for g in $G3_NAMES; do printf '          bash scripts/%s.sh\n' "$g"; done
  } > "$1/.github/workflows/verify.yml"
}

# 실제 G3 스텝을 지우고, 지정한 리터럴 스칼라 키 안에 가짜 단계를 숨긴 워크플로.
write_wf_hidden() {
  local d="$1" key="$2"
  {
    printf 'name: verify\non:\n  push:\n  pull_request:\njobs:\n  verify:\n    runs-on: ubuntu-latest\n    steps:\n'
    printf '      - name: decoy\n        %s: |\n' "$key"
    printf '          - name: fake g3\n            run: |\n'
    local g
    for g in $G3_NAMES; do printf '              bash scripts/%s.sh\n' "$g"; done
    printf '        run: echo "G3 removed; payload hidden in %s"\n' "$key"
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
  for f in mutations hardening hardening2 hardening3 hardening4; do
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
  write_wf_ok "$CASE_DIR"
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
    echo "FAIL: hardening4 [$label] exit=$SCAN_RC (기대: 정확히 $want)"
    printf '%s\n' "$SCAN_OUT"
    exit 1
  fi
  if [ -n "$needle" ] && ! printf '%s\n' "$SCAN_OUT" | grep -qE "$needle"; then
    echo "FAIL: hardening4 [$label] 이유가 다르다 (exit=$SCAN_RC)"
    printf '%s\n' "$SCAN_OUT"
    exit 1
  fi
  case "$want" in
    0) allowed=$((allowed + 1)) ;;
    1) blocked=$((blocked + 1)) ;;
  esac
  printf 'ok [%s] exit=%s\n' "$label" "$want"
}

WIRE_RE='^FAIL: ci/pre-push wiring broken [1-9][0-9]*$'

# ── 0) baseline: 정상 6줄 스텝은 정확히 0 ─────────────────────────────────────
init_case
expect_case "hardening4 baseline" 0 '^PASS: ci/pre-push wiring intact$'

# ── 리터럴 스칼라 키 은닉 — 이름 무관하게 전부 배선 훼손 exit 1 ────────────────
for key in description note summary run-name comment memo; do
  init_case
  write_wf_hidden "$CASE_DIR" "$key"
  git -C "$CASE_DIR" add .github/workflows/verify.yml
  expect_case "리터럴 스칼라 은닉: $key" 1 "$WIRE_RE"
done

# ── 자기 배선: 이 시험 자신도 CI 실행 줄에 있어야 한다 ────────────────────────
total=$((total + 1))
WF_REAL=.github/workflows/verify.yml
if [ ! -f "$WF_REAL" ] || ! grep -v '^[[:space:]]*#' "$WF_REAL" | grep -qE \
  '^[[:space:]]*bash scripts/acceptance-hs-portal-constants-hardening4\.sh[[:space:]]*$'; then
  echo "FAIL: hardening4 자신이 CI($WF_REAL) 실행 줄에 없다 — 로컬에만 있는 검사는 없는 것으로 친다 (P15③)"
  exit 1
fi
blocked=$((blocked + 1))
printf 'ok [%s]\n' "hardening4 자기 배선(CI 실행 줄)"

# ── 마무리: 원본 저장소 무변형 확인 ──────────────────────────────────────────
SNAP1=$(git status --porcelain)
if [ "$SNAP0" != "$SNAP1" ]; then
  echo "FAIL: hardening4 시험이 원본 저장소를 변형했다 (검증기 오염 금지)"
  exit 1
fi

echo "PASS: portal-constants hardening4 cases $total (blocked-mutations $((blocked - 1)), clean-baselines $allowed, wiring-present 1)"
