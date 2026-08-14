#!/usr/bin/env bash
# acceptance-hs-portal-constants-mutations.sh — G3 검사기를 일부러 고장 낸 샌드박스에서
# 3상태(0=깨끗/1=위반/2=검사불능)가 정확히 지켜지는지 증명한다 (RED 정본).
#
# 계약: docs/engineering/humansearch-g3-portal-constants-goal-2026-08-12.md §1⑩
#   exit 0 = 전부 증명 | 1 = 하나라도 실패 (구현 부재 포함 — RED 의 올바른 실패 이유)
#
# 판정 규율 (사전감사 벡터 9·11): 차단 성공은 "0이 아님"이 아니라 **정확히 exit 1**만
# 센다. 검사기 충돌(2·127)은 차단이 아니라 검사불능이며 별도 기대값(정확히 2)으로 센다.
#
# 자기 오염 방지: 가짜 값·무력화 문자열은 전부 조각 조립로 만든다 — 이 파일 자신이
# G3 검사기(전역 패턴)와 pre-commit 약화 탐지에 원문 매칭되지 않게
# (scripts/acceptance-hs-cleanroom-mutations.sh:67-80 · .check-weakening-patterns 관례).
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

# ── 조각 조립 payload ─────────────────────────────────────────────────────────
SEL_API=$(printf 'document.query%s("#login-form")' 'Selector')
SEL_PY=$(printf 'driver.find_%s(By.CSS_%s, "#resume-list > li")' 'element' 'SELECTOR')
URL_P=$(printf 'LOGIN_URL = "https%s//career-portal.example/login"' ':')
DOM_P=$(printf 'session_host = "cdn.talent-hub.%s"' 'net')
HP_P=$(printf 'CDP_ADDR = "127.0.0.1%s"' ':9222')
FLAG_P=$(printf 'launch_arg = "--remote-%s=9224"' 'debugging-port')
BRAND_P=$(printf 'referrer = "https%s//www.sara%s/zf_user"' ':' 'min.co.kr')
XPATH_P=$(printf 'USER_FIELD = "%s%s"' '//input' '[@name="user-id"]')
CSSID_P=$(printf 'LOGIN_BTN = %s#loginBtn%s' '"' '"')
MARKER_JSON=$(printf '{"login_url": "https%s//www.sara%s/login", "login_btn": %s#loginBtn%s}' \
  ':' 'min.co.kr' '"' '"')
WK_OR=$(printf '%s%s true' '|' '|')
WK_COE=$(printf 'continue-on%s true' '-error:')
WK_IF=$(printf 'if: ${{ fal%s }}' 'se')

# ── 샌드박스 구성 ─────────────────────────────────────────────────────────────
write_wf() {
  local d="$1" v="$2"
  local self='bash scripts/acceptance-hs-portal-constants.sh'
  local sib='bash scripts/acceptance-hs-portal-constants-mutations.sh'
  {
    printf 'name: verify\non:\n  push:\n  pull_request:\njobs:\n  verify:\n    runs-on: ubuntu-latest\n    steps:\n'
    printf '      - name: g3\n'
    case "$v" in
      if_false) printf '        %s\n' "$WK_IF" ;;
      coe)      printf '        %s\n' "$WK_COE" ;;
    esac
    printf '        run: %s\n' '|'
    case "$v" in
      ok|if_false|coe) printf '          %s\n          %s\n' "$self" "$sib" ;;
      self_commented)  printf '          # %s\n          %s\n' "$self" "$sib" ;;
      self_missing)    printf '          %s\n' "$sib" ;;
      echo_prefixed)   printf '          echo %s\n          %s\n' "$self" "$sib" ;;
      suffixed)        printf '          %s %s\n          %s\n' "$self" "$WK_OR" "$sib" ;;
      sibling_missing) printf '          %s\n' "$self" ;;
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
    "$CASE_DIR/humansearch/tests" "$CASE_DIR/lib"
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
    echo "FAIL: mutation [$label] exit=$SCAN_RC (기대: 정확히 $want)"
    printf '%s\n' "$SCAN_OUT"
    exit 1
  fi
  if [ -n "$needle" ] && ! printf '%s\n' "$SCAN_OUT" | grep -qE "$needle"; then
    echo "FAIL: mutation [$label] 이유가 다르다 (exit=$SCAN_RC)"
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
ZONE_RE='^FAIL: contracts zone violations [1-9][0-9]*$'
WIRE_RE='^FAIL: ci/pre-push wiring broken [1-9][0-9]*$'

# ── 0) baseline: 깨끗한 트리는 정확히 0, 카운트는 독립 대조 ───────────────────
init_case
expect_case "clean baseline" 0 '^PASS: portal constants outside contracts 0$'
ind=$( (cd "$CASE_DIR" && find humansearch/src humansearch/tests -type f | wc -l | tr -d ' ') )
rep=$(printf '%s\n' "$SCAN_OUT" | awk '/^PRODUCT_FILES: /{print $2}')
if [ -z "$rep" ] || [ "$rep" != "$ind" ]; then
  echo "FAIL: PRODUCT_FILES 자기보고($rep)가 독립 열거($ind)와 다르다 — 카운트 위조 의심"
  printf '%s\n' "$SCAN_OUT"
  exit 1
fi
chk=$(printf '%s\n' "$SCAN_OUT" | awk '/^CHECKED: /{print $2}')
if [ -z "$chk" ] || [ "$chk" -lt 10 ]; then
  echo "FAIL: baseline 이 CHECKED >= 10 을 보고하지 않았다 ($chk)"
  printf '%s\n' "$SCAN_OUT"
  exit 1
fi

# ── 1) 제품 코드에 심은 가짜 값 — 파일명·확장자·경로·값 다양화 ────────────────
init_case
plant "humansearch/src/humansearch/portal_client.py" "$URL_P"
expect_case "product scheme URL (.py)" 1 "$FORBIDDEN_RE"

init_case
plant "humansearch/tests/test_login_probe.py" "$DOM_P"
expect_case "product bare domain (tests/.py)" 1 "$FORBIDDEN_RE"

init_case
plant "humansearch/src/humansearch/config_probe_${RANDOM}.py" "$HP_P"
expect_case "product host:port (무작위 파일명)" 1 "$FORBIDDEN_RE"

init_case
plant "humansearch/src/humansearch/dom_probe.js" "$SEL_API"
expect_case "product selector API (.js)" 1 "$FORBIDDEN_RE"

init_case
plant "humansearch/tests/locator_probe.py" "$XPATH_P"
expect_case "product XPath literal" 1 "$FORBIDDEN_RE"

init_case
plant "humansearch/src/humansearch/ui_ids.py" "$CSSID_P"
expect_case "product quoted CSS id" 1 "$FORBIDDEN_RE"

# ── 2) 제품 밖(전역 계층) — scripts/·hooks/·루트·검사기 자신까지 자기면제 없음 ─
init_case
plant "scripts/helper_probe.sh" "$SEL_PY"
expect_case "scripts/ selector API — scripts 면제 금지" 1 "$FORBIDDEN_RE"

init_case
printf '# probe: %s\n' "$SEL_API" >> "$CASE_DIR/scripts/acceptance-hs-portal-constants.sh"
expect_case "검사기 자신에 심은 selector — 자기면제 금지" 1 "$FORBIDDEN_RE"

init_case
plant "note-${RANDOM}.cfg" "$FLAG_P"
expect_case "루트 파일 CDP 플래그" 1 "$FORBIDDEN_RE"

init_case
plant "hooks/deploy_probe" "$BRAND_P"
expect_case "hooks/ 포털 브랜드 도메인" 1 "$FORBIDDEN_RE"

# ── 3) contracts 경계 — 정확한 루트만 허용, 유사 경로·실행물·확장자 위장 차단 ──
init_case
plant "contracts/portal-markers.json" "$MARKER_JSON"
expect_case "루트 contracts/ 정당 값 — 오탐 금지" 0 '^PASS: portal constants outside contracts 0$'

init_case
plant "contracts-evil/markers.txt" "$SEL_API"
expect_case "contracts-evil/ 유사 경로 위장" 1 "$FORBIDDEN_RE"

init_case
plant "humansearch/src/humansearch/contracts/markers.json" "$MARKER_JSON"
expect_case "중첩 가짜 contracts/ 경로" 1 "$FORBIDDEN_RE"

init_case
printf 'marker data\n' > "$CASE_DIR/contracts/tool-probe.txt"
chmod +x "$CASE_DIR/contracts/tool-probe.txt"
git -C "$CASE_DIR" add contracts/tool-probe.txt
expect_case "contracts/ 실행 권한 파일" 1 "$ZONE_RE"

init_case
plant "contracts/run-probe.sh" 'echo marker'
expect_case "contracts/ 허용 확장자 밖" 1 "$ZONE_RE"

# ── 4) CI 배선 무력화 — 주석·삭제·echo·후미 무력화·조건·오류무시 ──────────────
for variant in self_commented self_missing echo_prefixed suffixed if_false coe sibling_missing; do
  init_case
  write_wf "$CASE_DIR" "$variant"
  git -C "$CASE_DIR" add .github/workflows/verify.yml
  expect_case "CI 무력화: $variant" 1 "$WIRE_RE"
done

# ── 5) pre-push 배선 훼손 ─────────────────────────────────────────────────────
init_case
git -C "$CASE_DIR" rm -q -f hooks/pre-push
expect_case "pre-push 부재" 1 "$WIRE_RE"

init_case
chmod -x "$CASE_DIR/hooks/pre-push"
expect_case "pre-push 실행권한 제거" 1 "$WIRE_RE"

init_case
printf '#!/usr/bin/env bash\nexit 0\n' > "$CASE_DIR/hooks/pre-push"
chmod +x "$CASE_DIR/hooks/pre-push"
git -C "$CASE_DIR" add hooks/pre-push
expect_case "pre-push 글로브 수집식 제거" 1 "$WIRE_RE"

# ── 6) 검사 불능 — 정확히 2 (차단 성공으로 세지 않는다) ───────────────────────
init_case
git -C "$CASE_DIR" rm -q -f contracts/portal-constants-deny-patterns.txt
expect_case "전역 패턴 계약 부재" 2 'pattern contract missing'

init_case
: > "$CASE_DIR/contracts/portal-constants-deny-patterns.txt"
expect_case "전역 패턴 계약 빈 파일" 2 'pattern contract missing, unreadable, or empty'

init_case
printf '(\n' >> "$CASE_DIR/contracts/portal-constants-deny-patterns.txt"
expect_case "깨진 정규식" 2 'invalid expression'

init_case
printf 'x*\n' >> "$CASE_DIR/contracts/portal-constants-deny-patterns.txt"
expect_case "빈 문자열 매치 정규식" 2 'empty-matching expression'

init_case
printf '(\n' >> "$CASE_DIR/contracts/portal-constants-deny-patterns-product.txt"
expect_case "제품 패턴 계약 깨짐" 2 'invalid expression'

init_case
git -C "$CASE_DIR" rm -q -r -f humansearch/tests > /dev/null
rm -rf "$CASE_DIR/humansearch/tests"
expect_case "제품 루트 부재 — 조용한 skip 금지" 2 'product root missing'

init_case
git -C "$CASE_DIR" rm -q -f humansearch/src/humansearch/__init__.py \
  humansearch/tests/test_boundary.py > /dev/null
mkdir -p "$CASE_DIR/humansearch/src/humansearch" "$CASE_DIR/humansearch/tests"
expect_case "제품 파일 0건 — 0건 통과 금지" 2 'product files 0'

# ── 7) 위반과 검사불능이 겹치면 검사불능이 이긴다 (일부 스캔의 위반 수는 무효) ──
init_case
plant "humansearch/src/humansearch/portal_probe.py" "$URL_P"
printf '(\n' >> "$CASE_DIR/contracts/portal-constants-deny-patterns.txt"
expect_case "위반+깨진 패턴 동시 — 2 우선" 2 'invalid expression'

# ── 8) 카운트: 제품 파일 5개면 정확히 5를 보고 ────────────────────────────────
init_case
plant "humansearch/src/humansearch/models.py" 'MODEL_VERSION = 1'
plant "humansearch/src/humansearch/scoring.py" 'BASE_SCORE = 0'
plant "humansearch/tests/test_scoring.py" 'EXPECTED = 0'
expect_case "제품 5파일 깨끗" 0 '^PRODUCT_FILES: 5$'

# ── 마무리: 원본 저장소 무변형 확인 ──────────────────────────────────────────
SNAP1=$(git status --porcelain)
if [ "$SNAP0" != "$SNAP1" ]; then
  echo "FAIL: mutation 시험이 원본 저장소를 변형했다 (검증기 오염 금지)"
  exit 1
fi

echo "PASS: portal-constants mutations blocked $blocked/$total (allowed $allowed, notrun $notrun)"
