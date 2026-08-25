#!/usr/bin/env bash
# acceptance-hs-portal-constants-hardening7.sh — 두 차례 독립 codex 검증이 확인한 G3 우회
# 4가지와, 2026-08-25 origin/main 병합 실측이 드러낸 오탐 1가지를 표본으로 고정한다.
#
# 계약: docs/engineering/humansearch-g3-hardening7-goal-2026-08-25.md §2
#   D1 태그명+순번 셀렉터        → 정확히 exit 1
#   D2 홑 클래스·태그.클래스 셀렉터 → 정확히 exit 1 (파일명은 오탐 0)
#   D3 제품 루트 계약 이탈        → 정확히 exit 2 (조용한 skip 금지)
#   D4 목록 밖 접미사             → 정확히 exit 1 (모르는 접미사는 거부 — fail-closed)
#   D5 예약 도메인·루프백         → 정확히 exit 0 (단, 포트가 붙으면 다시 exit 1)
#   차단 성공은 "0이 아님"이 아니라 정확한 exit code 와 FAIL 사유를 함께 확인한다.
#
# 자기 오염 방지: 공격 문자열은 조각 조립로 만들어 이 파일 자신이 전역 패턴에 걸리지 않게 한다.
# 원본 저장소는 절대 변형하지 않는다 — 모든 fixture 는 mktemp 샌드박스에만 쓴다.
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
NONOP_ADDRESSES_SOURCE=${G3_NONOP_ADDRESSES_SOURCE:-contracts/portal-constants-nonoperational-addresses.txt}
NONOP_SUFFIXES_SOURCE=${G3_NONOP_SUFFIXES_SOURCE:-contracts/portal-constants-nonoperational-suffixes.txt}

for required in "$SCANNER_SOURCE" "$GLOBAL_PATTERNS_SOURCE" "$PRODUCT_PATTERNS_SOURCE"; do
  if [ ! -f "$required" ]; then
    echo "FAIL: required G3 source missing: $required"
    exit 1
  fi
done
if ! command -v ruby >/dev/null 2>&1; then
  echo "FAIL: Ruby unavailable"
  exit 1
fi

SNAP0=$(git status --porcelain)
SANDBOX=$(mktemp -d)
cleanup() { rm -rf -- "$SANDBOX"; }
trap cleanup EXIT
trap 'cleanup; trap - EXIT; exit 143' TERM
trap 'cleanup; trap - EXIT; exit 130' INT
trap 'cleanup; trap - EXIT; exit 129' HUP

# ── 조각 조립 공격 표본 ───────────────────────────────────────────────────────
D1_NTH=$(printf 'ROW = "table tbody tr:nth-%s(5) td"' 'child')
D1_TYPE=$(printf 'CELL = "td:nth-of-%s(2)"' 'type')
D1_FIRST=$(printf 'HEAD = "thead tr th:first-%s"' 'child')
D1_TAGS=$(printf 'LIST = "table tbody %s"' 'tr')
D2_CLASS=$(printf 'BTN = ".login-%s"' 'button')
D2_TAGCLASS=$(printf 'BTN = "button.%s"' 'submit')
D2_CLEAN=$(printf 'ASSETS = ["app.js", "styles.css", "index.html", "private.txt"]')
# 2라벨로 둔다. 3라벨은 기존의 "따옴표 3라벨 호스트" 규칙이 이미 잡으므로 D4(고정 TLD
# 열거의 실패 방향)를 찌르지 못한다 — 실측으로 확인했다(변경 전/후 모두 flat 패턴 0건).
D4_UNKNOWN=$(printf 'HOST = "hire-%s.zzunknown"' 'portal')
D4_NEWTLD=$(printf 'HOST = "hire-%s.%s"' 'portal' 'jobs')
D4_REALTLD=$(printf 'HOST = "hire-%s.co.%s"' 'portal' 'kr')
D5_RESERVED=$(printf 'BASE = "https%s//portal.%s/login"' ':' 'invalid')
D5_LOOPBACK=$(printf 'SAFE_HOSTS = {"127.0.0.1", "%s"}' 'localhost')
D5_LOOPPORT=$(printf 'DIAG = "127.0.0.1%s"' ':9333')
VERSION_OK=$(printf 'REQUIRES_PYTHON = "3.12"')
# ── 2026-08-25 V1(codex) 판정 흡수 표본 ──────────────────────────────────────
V_NTHLAST=$(printf 'CELL = "td:nth-last-%s(2)"' 'child')
V_NTHLASTTYPE=$(printf 'CELL = "td:nth-last-of-%s(2)"' 'type')
V_LAST=$(printf 'CELL = "tr:last-%s"' 'child')
V_FIRSTTYPE=$(printf 'CELL = "tr:first-of-%s"' 'type')
V_LASTTYPE=$(printf 'CELL = "tr:last-of-%s"' 'type')
V_ONLY=$(printf 'CELL = "tr:only-%s"' 'child')
V_ONLYTYPE=$(printf 'CELL = "tr:only-of-%s"' 'type')
F2_UPPER=$(printf 'HOST = "HIRE-%s.ZZUNKNOWN"' 'PORTAL')
F2_CLASS=$(printf 'BTN = ".Login-%s"' 'Button')
F2_FULLWIDTH=$(printf 'HOST = "hire-portal．zzunknown"')
F3_UPPEREXT='export const NAME = "web";'
F4_MIXED=$(printf 'ENDPOINTS = "https%s//portal.invalid/,https%s//api.vendor.zzunknown".split(",")' ':' ':')
F5_TLDEXT=$(printf 'HOST = "hire-%s.zip"' 'portal')
F5_TLDEXT2=$(printf 'HOST = "hire-%s.%s"' 'portal' 'py')
F5_SCHEME=$(printf 'BASE = "https%s//hire-portal.zip/login"' ':')
F6_COMBINATOR=$(printf 'SEL = "dl > %s"' 'dd')
F7_PROSE=$(printf 'MESSAGE = "a table"')
F7_PROSE2=$(printf 'MESSAGE = "button label"')
F9_ANY=$(printf 'BIND = "0.0.0.0"')
F9_IPV6=$(printf 'DIAG = "[::1]%s"' ':9333')
F9_V6BARE=$(printf 'SAFE = "[::1]"')
# ── 2026-08-25 자체 적대 검증(A3·A4): 비운영 주소를 덧붙여 따옴표 모양을 깨뜨리는 마스킹.
# 중화를 "삭제"로 구현했을 때 닫는 따옴표가 사라져 셀렉터 규칙이 통째로 무력화됐다.
A3_MASK=$(printf 'SEL = ".login-%s portal.%s"' 'button' 'invalid')
A4_MASK=$(printf 'SEL = "#loginBtn %s"' 'localhost')
A4_MASK2=$(printf 'SEL = "#loginBtn input 127.0.0.1"')

G3_NAMES="acceptance-hs-portal-constants acceptance-hs-portal-constants-mutations acceptance-hs-portal-constants-hardening acceptance-hs-portal-constants-hardening2 acceptance-hs-portal-constants-hardening3 acceptance-hs-portal-constants-hardening4 acceptance-hs-portal-constants-hardening5 acceptance-hs-portal-constants-hardening6 acceptance-hs-portal-constants-hardening7"

write_wf_ok() {
  {
    printf 'name: verify\non:\n  push:\n  pull_request:\njobs:\n  verify:\n    runs-on: ubuntu-latest\n    steps:\n'
    printf '      - name: g3\n        run: |\n'
    for g in $G3_NAMES; do printf '          bash scripts/%s.sh\n' "$g"; done
  } > "$1/.github/workflows/verify.yml"
}

total=0
blocked=0
allowed=0
notrun=0
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
  for f in mutations hardening hardening2 hardening3 hardening4 hardening5 hardening6 hardening7; do
    printf '#!/usr/bin/env bash\n# wiring probe placeholder\n' \
      > "$CASE_DIR/scripts/acceptance-hs-portal-constants-$f.sh"
  done
  cp "$GLOBAL_PATTERNS_SOURCE" "$CASE_DIR/contracts/portal-constants-deny-patterns.txt"
  cp "$PRODUCT_PATTERNS_SOURCE" "$CASE_DIR/contracts/portal-constants-deny-patterns-product.txt"
  # 루트 계약은 표본 자신의 구조를 적는다 (표본 저장소엔 apps/admin 이 없다).
  printf 'humansearch/src\nhumansearch/tests\n' \
    > "$CASE_DIR/contracts/portal-constants-product-roots.txt"
  if [ -f "$NONOP_ADDRESSES_SOURCE" ]; then
    cp "$NONOP_ADDRESSES_SOURCE" "$CASE_DIR/contracts/portal-constants-nonoperational-addresses.txt"
  fi
  if [ -f "$NONOP_SUFFIXES_SOURCE" ]; then
    cp "$NONOP_SUFFIXES_SOURCE" "$CASE_DIR/contracts/portal-constants-nonoperational-suffixes.txt"
  fi
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
    echo "FAIL: hardening7 [$label] exit=$SCAN_RC (기대: 정확히 $want)"
    printf '%s\n' "$SCAN_OUT"
    exit 1
  fi
  if [ -n "$needle" ] && ! printf '%s\n' "$SCAN_OUT" | grep -qE "$needle"; then
    echo "FAIL: hardening7 [$label] 이유가 다르다 (exit=$SCAN_RC)"
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
CLEAN_RE='^PASS: portal constants outside contracts 0$'

init_case
expect_case "baseline 깨끗한 트리" 0 "$CLEAN_RE"

# ── D1 태그명 + 순번 셀렉터 ──────────────────────────────────────────────────
init_case; plant "humansearch/src/humansearch/row_probe.py" "$D1_NTH"
expect_case "D1 순번 셀렉터 nth-child" 1 "$FORBIDDEN_RE"
init_case; plant "humansearch/tests/type_probe.py" "$D1_TYPE"
expect_case "D1 순번 셀렉터 nth-of-type" 1 "$FORBIDDEN_RE"
init_case; plant "humansearch/src/humansearch/first_probe.py" "$D1_FIRST"
expect_case "D1 구조 의사클래스 first-child" 1 "$FORBIDDEN_RE"
init_case; plant "humansearch/tests/tagchain_probe.py" "$D1_TAGS"
expect_case "D1 태그명만으로 이어진 자손 셀렉터" 1 "$FORBIDDEN_RE"

# ── D2 홑 클래스 셀렉터 ──────────────────────────────────────────────────────
init_case; plant "humansearch/src/humansearch/class_probe.py" "$D2_CLASS"
expect_case "D2 홑 클래스 셀렉터" 1 "$FORBIDDEN_RE"
init_case; plant "humansearch/tests/tagclass_probe.py" "$D2_TAGCLASS"
expect_case "D2 태그.클래스 셀렉터" 1 "$FORBIDDEN_RE"
init_case; plant "humansearch/src/humansearch/assets_probe.py" "$D2_CLEAN"
expect_case "D2 파일명·확장자는 오탐 금지" 0 "$CLEAN_RE"
init_case; plant "humansearch/tests/version_probe.py" "$VERSION_OK"
expect_case "D2 판 번호 문자열은 오탐 금지" 0 "$CLEAN_RE"

# ── V1 F10: 의사클래스 변종 전체 (CA-1 "변종 전체" 요구) ────────────────────
init_case; plant "humansearch/src/humansearch/v1.py" "$V_NTHLAST"
expect_case "V1 nth-last-child" 1 "$FORBIDDEN_RE"
init_case; plant "humansearch/src/humansearch/v2.py" "$V_NTHLASTTYPE"
expect_case "V1 nth-last-of-type" 1 "$FORBIDDEN_RE"
init_case; plant "humansearch/src/humansearch/v3.py" "$V_LAST"
expect_case "V1 last-child" 1 "$FORBIDDEN_RE"
init_case; plant "humansearch/src/humansearch/v4.py" "$V_FIRSTTYPE"
expect_case "V1 first-of-type" 1 "$FORBIDDEN_RE"
init_case; plant "humansearch/src/humansearch/v5.py" "$V_LASTTYPE"
expect_case "V1 last-of-type" 1 "$FORBIDDEN_RE"
init_case; plant "humansearch/src/humansearch/v6.py" "$V_ONLY"
expect_case "V1 only-child" 1 "$FORBIDDEN_RE"
init_case; plant "humansearch/src/humansearch/v7.py" "$V_ONLYTYPE"
expect_case "V1 only-of-type" 1 "$FORBIDDEN_RE"

# ── V1 F2: 대소문자·전각점 ───────────────────────────────────────────────────
init_case; plant "humansearch/src/humansearch/upper_probe.py" "$F2_UPPER"
expect_case "V1 F2 대문자 호스트" 1 "$FORBIDDEN_RE"
init_case; plant "humansearch/tests/upperclass_probe.py" "$F2_CLASS"
expect_case "V1 F2 대문자 CSS 클래스" 1 "$FORBIDDEN_RE"
init_case; plant "humansearch/src/humansearch/fullwidth_probe.py" "$F2_FULLWIDTH"
expect_case "V1 F2 전각 마침표 호스트" 1 "$FORBIDDEN_RE"

# ── V1 F3: 대문자 확장자가 제품 루트 탐지를 피하지 못한다 ────────────────────
init_case; plant "apps/web/main.PY" "$F3_UPPEREXT"
expect_case "V1 F3 대문자 확장자 미등재 폴더" 2 'product code outside the product-root contract'
init_case; plant "apps/web/main.Js" "$F3_UPPEREXT"
expect_case "V1 F3 혼합 대소문자 확장자" 2 'product code outside the product-root contract'

# ── V1 F4: 예약 URL 제거가 같은 줄의 실제 URL 을 지우지 않는다 ───────────────
init_case; plant "humansearch/src/humansearch/mixed_probe.py" "$F4_MIXED"
expect_case "V1 F4 예약 URL 뒤의 실제 URL" 1 "$FORBIDDEN_RE"

# ── V1 F5: 실 TLD 와 겹치는 확장자를 면제하지 않는다 ─────────────────────────
init_case; plant "humansearch/src/humansearch/zip_probe.py" "$F5_TLDEXT"
expect_case "V1 F5 .zip 은 파일 확장자이자 실 TLD" 1 "$FORBIDDEN_RE"
init_case; plant "humansearch/tests/py_probe.py" "$F5_TLDEXT2"
expect_case "V1 F5 .py 는 파일 확장자이자 실 TLD" 1 "$FORBIDDEN_RE"
init_case; plant "humansearch/src/humansearch/zipurl_probe.py" "$F5_SCHEME"
expect_case "V1 F5 scheme 이 붙으면 어느 접미사든 잡힌다" 1 "$FORBIDDEN_RE"

# ── V1 F6·F7: 태그 셀렉터의 두 방향 ─────────────────────────────────────────
init_case; plant "humansearch/src/humansearch/comb_probe.py" "$F6_COMBINATOR"
expect_case "V1 F6 결합자가 있으면 어휘 밖 태그도 잡는다" 1 "$FORBIDDEN_RE"
init_case; plant "humansearch/tests/prose_probe.py" "$F7_PROSE"
expect_case "V1 F7 평범한 영어 문구는 오탐 금지" 0 "$CLEAN_RE"
init_case; plant "humansearch/tests/prose2_probe.py" "$F7_PROSE2"
expect_case "V1 F7 태그 2개 영어 문구도 오탐 금지" 0 "$CLEAN_RE"

# ── V1 F9: 0.0.0.0 과 IPv6 루프백의 경계 ────────────────────────────────────
init_case; plant "humansearch/src/humansearch/any_probe.py" "$F9_ANY"
expect_case "V1 F9 0.0.0.0 은 면제 대상이 아니다" 1 "$FORBIDDEN_RE"
init_case; plant "humansearch/src/humansearch/v6port_probe.py" "$F9_IPV6"
expect_case "V1 F9 포트 붙은 IPv6 루프백은 위반" 1 "$FORBIDDEN_RE"
init_case; plant "humansearch/src/humansearch/v6bare_probe.py" "$F9_V6BARE"
expect_case "V1 F9 포트 없는 IPv6 루프백은 위반 아님" 0 "$CLEAN_RE"

# ── D3 제품 루트 계약 ────────────────────────────────────────────────────────
init_case; plant "apps/web/main.js" 'export const NAME = "web";'
expect_case "D3 미등재 제품 폴더 — 조용한 skip 금지" 2 'product code outside the product-root contract'
init_case
git -C "$CASE_DIR" rm -q -f contracts/portal-constants-product-roots.txt > /dev/null
rm -f "$CASE_DIR/contracts/portal-constants-product-roots.txt"
expect_case "D3 루트 계약 부재" 2 'product root contract missing'
init_case
printf '# 주석만 남긴다\n\n' > "$CASE_DIR/contracts/portal-constants-product-roots.txt"
expect_case "D3 루트 계약 유효 항목 0개" 2 'zero effective roots'
init_case
printf 'humansearch/src\nhumansearch/tests\nhumansearch/absent\n' \
  > "$CASE_DIR/contracts/portal-constants-product-roots.txt"
expect_case "D3 등재했으나 실재하지 않는 루트" 2 'product root missing'

# ── D4 접미사 fail-closed ────────────────────────────────────────────────────
init_case; plant "humansearch/src/humansearch/tld_probe.py" "$D4_UNKNOWN"
expect_case "D4 목록에 없는 접미사 — 모르는 값은 거부" 1 "$FORBIDDEN_RE"
init_case; plant "humansearch/tests/newtld_probe.py" "$D4_NEWTLD"
expect_case "D4 신설 TLD (.jobs)" 1 "$FORBIDDEN_RE"
init_case
printf 'kr\nco\ncom\n' >> "$CASE_DIR/contracts/portal-constants-nonoperational-suffixes.txt"
plant "humansearch/src/humansearch/realtld_probe.py" "$D4_REALTLD"
expect_case "D4 실 TLD 를 예외에 넣어도 통과하지 않는다 (다층 방어)" 1 "$FORBIDDEN_RE"
init_case
git -C "$CASE_DIR" rm -q -f contracts/portal-constants-nonoperational-suffixes.txt > /dev/null
rm -f "$CASE_DIR/contracts/portal-constants-nonoperational-suffixes.txt"
expect_case "D4 접미사 계약 부재" 2 'portal judgment contract missing'

# ── D5 예약 도메인·루프백 정밀화 ─────────────────────────────────────────────
init_case; plant "humansearch/tests/reserved_probe.py" "$D5_RESERVED"
expect_case "D5 RFC 2606 예약 도메인 URL 은 위반이 아니다" 0 "$CLEAN_RE"
init_case; plant "humansearch/src/humansearch/loopback_probe.py" "$D5_LOOPBACK"
expect_case "D5 루프백 고정은 안전장치다" 0 "$CLEAN_RE"
init_case; plant "humansearch/src/humansearch/diag_probe.py" "$D5_LOOPPORT"
expect_case "D5 포트가 붙은 루프백은 여전히 위반" 1 "$FORBIDDEN_RE"
init_case
git -C "$CASE_DIR" rm -q -f contracts/portal-constants-nonoperational-addresses.txt > /dev/null
rm -f "$CASE_DIR/contracts/portal-constants-nonoperational-addresses.txt"
expect_case "D5 비운영 주소 계약 부재" 2 'portal judgment contract missing'

# ── 자체 적대 검증 A3·A4: 비운영 주소 마스킹으로 셀렉터 규칙을 깨뜨릴 수 없다 ────
init_case; plant "humansearch/src/humansearch/mask_class_probe.py" "$A3_MASK"
expect_case "A3 예약 도메인으로 클래스 규칙 마스킹" 1 "$FORBIDDEN_RE"
init_case; plant "humansearch/tests/mask_id_probe.py" "$A4_MASK"
expect_case "A4 루프백으로 id 규칙 마스킹" 1 "$FORBIDDEN_RE"
init_case; plant "humansearch/src/humansearch/mask_id2_probe.py" "$A4_MASK2"
expect_case "A4 루프백 IP 로 id 규칙 마스킹" 1 "$FORBIDDEN_RE"

# ── 자기 배선 ────────────────────────────────────────────────────────────────
total=$((total + 1))
if ! grep -v '^[[:space:]]*#' .github/workflows/verify.yml | grep -qE \
  '^[[:space:]]*bash scripts/acceptance-hs-portal-constants-hardening7\.sh[[:space:]]*$'; then
  echo "FAIL: hardening7 자신이 CI 실행 줄에 없다"
  exit 1
fi
wiring=1
printf 'ok [%s]\n' "hardening7 자기 배선(CI 실행 줄)"

SNAP1=$(git status --porcelain)
if [ "$SNAP0" != "$SNAP1" ]; then
  echo "FAIL: hardening7 시험이 원본 저장소를 변형했다"
  exit 1
fi

echo "PASS: portal-constants hardening7 blocked $blocked (allowed $allowed, notrun $notrun, wiring $wiring)"
echo "CHECKED: $total"
