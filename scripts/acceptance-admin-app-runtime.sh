#!/usr/bin/env bash
# acceptance-admin-app-runtime.sh — 관리자 화면을 고장 내면 반드시 빨개지는가 (AC10).
#
# 겨냥하는 결함: humansearch/tests/test_admin_shadow_server.py:70 은 app.js 를 빈 문자열로
# 써 놓고 MIME 타입만 본다. API 호출 경로를 바꾸거나 화면 그리는 코드를 통째로 지워도
# 어떤 시험도 빨개지지 않는다 — 파일이 "있다"와 "동작한다"는 다르다 (P16).
#
#   통과 — 손대지 않은 app.js + index.html 은 exit 0 과 양수 CHECKED
#   차단 — API 호출·화면 표시를 고장 낸 사본은 전부 불합격
#   무효 — 파일 없음·id 0개는 통과가 아니라 exit 2 (P20)
#
# 새 런타임 의존성을 들이지 않는다. node 는 개발기와 ubuntu-latest 러너 양쪽에 이미 있다.
set -uo pipefail

unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE GIT_OBJECT_DIRECTORY \
  GIT_ALTERNATE_OBJECT_DIRECTORIES GIT_COMMON_DIR GIT_PREFIX GIT_QUARANTINE_PATH

REPO=$(git rev-parse --show-toplevel 2>/dev/null) || {
  echo "NOT_RUN: git 저장소가 아니다"
  echo "CHECKED: 0"
  exit 2
}
cd "$REPO" || exit 2

HARNESS="$REPO/scripts/verify/admin-app-runtime.mjs"
APP="$REPO/apps/admin/app.js"
HTML="$REPO/apps/admin/index.html"

if ! command -v node > /dev/null 2>&1; then
  echo "NOT_RUN: node 를 찾을 수 없다 — 실행 기반 시험을 돌릴 수 없다 (재지 못한 것은 통과가 아니다)"
  echo "CHECKED: 0"
  exit 2
fi
for required in "$HARNESS" "$APP" "$HTML"; do
  if [ ! -f "$required" ]; then
    echo "FAIL: 필요한 파일이 없다 — $required (fail-closed)"
    echo "CHECKED: 0"
    exit 2
  fi
done

SNAPSHOT=$(git status --porcelain)
TMP=$(mktemp -d) || {
  echo "NOT_RUN: mktemp 실패"
  echo "CHECKED: 0"
  exit 2
}
case "$TMP" in
  /tmp/*|/private/tmp/*|/var/folders/*|/private/var/folders/*) ;;
  *) echo "NOT_RUN: 안전하지 않은 임시 경로 — $TMP"; echo "CHECKED: 0"; exit 2 ;;
esac
trap 'ruby -rfileutils -e "FileUtils.remove_entry(ARGV[0]) if File.exist?(ARGV[0])" "$TMP"' EXIT

TOTAL=21
checked=0
failed=0

record() {
  local ok="$1"
  local label="$2"
  local detail="$3"
  checked=$((checked + 1))
  if [ "$ok" -eq 0 ]; then
    printf 'PASS: %s — %s\n' "$label" "$detail"
  else
    printf 'FAIL: %s — %s\n' "$label" "$detail"
    failed=1
  fi
}

# expect <설명> <기대 종료값> <app 경로> <html 경로>
expect() {
  local label="$1"
  local wanted="$2"
  local app="$3"
  local html="$4"
  local rc=0
  local out=""
  if [ -z "$app" ] || [ -z "$html" ]; then
    record 1 "$label" "주입 실패 — 사본 경로가 비었다(공격이 실행되지 않았다)"
    return
  fi
  out=$(node "$HARNESS" --app "$app" --html "$html" 2>&1) || rc=$?
  if [ "$rc" -eq "$wanted" ]; then
    record 0 "$label" "exit=$rc"
  else
    record 1 "$label" "expected exit=$wanted actual=$rc / $(printf '%s' "$out" | grep '^FAIL:' | head -2 | tr '\n' ' ')"
  fi
}

# 사본에 ruby 로 주입한다. 반환값은 사본 경로.
break_app() {
  local name="$1"
  local code="$2"
  local path
  mkdir -p "$TMP/$name" || return 1
  path="$TMP/$name/$(basename "$APP")"
  cp "$APP" "$path" || return 1
  ruby -e "$code" "$path" || return 1
  # 주입이 실제로 파일을 바꿨는지 확인한다. 안 바뀌었다면 그것은 "막았다"가 아니라
  # "공격하지 않았다"이므로 사본 경로를 돌려주지 않는다.
  if cmp -s "$APP" "$path"; then
    return 1
  fi
  printf '%s' "$path"
}

break_html() {
  local name="$1"
  local code="$2"
  local path
  mkdir -p "$TMP/$name" || return 1
  path="$TMP/$name/$(basename "$HTML")"
  cp "$HTML" "$path" || return 1
  ruby -e "$code" "$path" || return 1
  if cmp -s "$HTML" "$path"; then
    return 1
  fi
  printf '%s' "$path"
}

# ── 통과 쪽: 손대지 않은 화면 ────────────────────────────────────────────────
expect "실제 app.js + index.html → 통과" 0 "$APP" "$HTML"

clean_out=$(node "$HARNESS" --app "$APP" --html "$HTML" 2>&1)
clean_checked=$(printf '%s\n' "$clean_out" | awk -F'CHECKED:' '/CHECKED:/ { gsub(/[^0-9]/, "", $2); v=$2 } END { print v + 0 }')
if [ "$clean_checked" -ge 1 ]; then
  record 0 "정상 실행의 CHECKED 양수" "CHECKED=$clean_checked"
else
  record 1 "정상 실행의 CHECKED 양수" "CHECKED=$clean_checked — 0건 단언은 합격이 아니다"
fi

# ── 차단 쪽: API 호출을 고장 낸다 ────────────────────────────────────────────
p=$(break_app api-path 'p=ARGV[0]; s=File.read(p).sub("\"/api/dashboard\"", "\"/api/wrong\""); File.write(p,s)')
expect "API 경로를 바꿈 → 불합격" 1 "$p" "$HTML"

p=$(break_app api-cache 'p=ARGV[0]; s=File.read(p).sub("cache: \"no-store\", ", ""); File.write(p,s)')
expect "캐시 금지 옵션 제거 → 불합격" 1 "$p" "$HTML"

p=$(break_app api-gone 'p=ARGV[0]; s=File.read(p).sub(/const response = await fetch\([^\n]*\);/, "const response = { ok: true, json: () => Promise.resolve({ weeks: [] }) };"); File.write(p,s)')
expect "API 호출 자체를 없앰 → 불합격" 1 "$p" "$HTML"

# ── 차단 쪽: 화면 표시를 고장 낸다 ───────────────────────────────────────────
p=$(break_app no-metrics 'p=ARGV[0]; s=File.read(p).sub("      renderMetrics(dashboard, snapshot);\n", ""); File.write(p,s)')
expect "지표를 그리지 않음 → 불합격" 1 "$p" "$HTML"

p=$(break_app no-provenance 'p=ARGV[0]; s=File.read(p).sub("      renderProvenance(dashboard, snapshot);\n", ""); File.write(p,s)')
expect "판정 근거를 그리지 않음 → 불합격" 1 "$p" "$HTML"

p=$(break_app no-heatmap 'p=ARGV[0]; s=File.read(p).sub("      renderHeatmap(dashboard);\n", ""); File.write(p,s)')
expect "히트맵을 그리지 않음 → 불합격" 1 "$p" "$HTML"

p=$(break_app no-click 'p=ARGV[0]; s=File.read(p).sub(/button\.addEventListener\("click", \(\) => \{\n.*\n      \}\);\n/, ""); File.write(p,s)')
expect "주차 클릭 반응 제거 → 불합격" 1 "$p" "$HTML"

p=$(break_app no-ready 'p=ARGV[0]; s=File.read(p).sub("      document.body.dataset.ready = \"true\";\n", ""); File.write(p,s)')
expect "완료 표식 제거 → 불합격" 1 "$p" "$HTML"

p=$(break_app value-faked 'p=ARGV[0]; s=File.read(p).sub("const value = result.value === null ? \"미집계\" : String(result.value);", "const value = String(result.value === null ? 0 : result.value);"); File.write(p,s)')
expect "미집계를 0 으로 지어냄 → 불합격" 1 "$p" "$HTML"

# ── 차단 쪽: 실패를 성공처럼 말한다 (P3) ─────────────────────────────────────
p=$(break_app failure-hidden 'p=ARGV[0]; s=File.read(p).sub("      state.dataset.status = \"FAIL\";", "      state.dataset.status = \"PASS\";"); File.write(p,s)')
expect "불러오기 실패를 PASS 로 말함 → 불합격" 1 "$p" "$HTML"

# ── 차단 쪽: 화면 쪽에서 id 를 지운다 ────────────────────────────────────────
# app.js 는 loadDashboard 를 try 로 감싸므로 없는 자리를 만나면 예외가 아니라 실패 경로로
# 빠진다. 그래서 판정은 "실행 불가(2)"가 아니라 "불합격(1)"이다 — 어느 쪽이든 빨개진다.
p=$(break_html no-provenance-id 'p=ARGV[0]; s=File.read(p).sub("<dl id=\"provenance\"></dl>", "<dl></dl>"); File.write(p,s)')
expect "화면에서 판정 근거 자리를 지움 → 불합격" 1 "$APP" "$p"

# ── V1 F6 (높음): 화면이 스크립트를 불러오는지 보지 않았다 ─────────────────
# 2026-08-27 실측: <script src> 를 지우거나 경로를 틀리게 하거나 type 을 바꿔도 시험이
# 초록이었다. 브라우저에서는 app.js 가 한 줄도 실행되지 않는데도 그랬다.
p=$(break_html no-script-tag 'p=ARGV[0]; s=File.read(p).sub(%q{<script src="/app.js" defer></script>}, ""); File.write(p,s)')
expect "화면에서 스크립트 태그 제거 → 불합격" 1 "$APP" "$p"

p=$(break_html wrong-script-src 'p=ARGV[0]; s=File.read(p).sub(%q{src="/app.js"}, %q{src="/wrong.js"}); File.write(p,s)')
expect "화면의 스크립트 경로 오기 → 불합격" 1 "$APP" "$p"

p=$(break_html template-script-type 'p=ARGV[0]; s=File.read(p).sub(%q{<script src="/app.js" defer>}, %q{<script src="/app.js" type="text/template" defer>}); File.write(p,s)')
expect "스크립트를 실행되지 않는 type 으로 → 불합격" 1 "$APP" "$p"

# 브라우저에 없는 node 전역을 참조하면 브라우저에서만 죽는다. 하네스가 그것을 통과시키면
# "여기서는 되는데 화면은 하얗다"가 된다.
p=$(break_app node-global 'p=ARGV[0]; s=File.read(p).sub("  async function loadDashboard() {", "  async function loadDashboard() {\n    void process.version;"); File.write(p,s)')
expect "브라우저에 없는 node 전역 참조 → 불합격" 1 "$p" "$HTML"

# 반대 방향 — 표준 DOM 메서드를 쓰는 **정상 코드**를 빨갛게 만들면 그것도 결함이다.
p=$(break_app standard-appendchild 'p=ARGV[0]; s=File.read(p).sub("      item.append(button);", "      item.appendChild(button);"); File.write(p,s)')
expect "표준 appendChild 로 바꾼 정상 코드 → 통과(오차단 없음)" 0 "$p" "$HTML"

# ── fail-closed ─────────────────────────────────────────────────────────────
expect "app.js 없음 → 실행 불가" 2 "$TMP/does-not-exist.js" "$HTML"

printf '<html><body></body></html>\n' > "$TMP/no-ids.html"
expect "id 가 하나도 없는 화면 → 실행 불가" 2 "$APP" "$TMP/no-ids.html"

# ── 원본 불변 ────────────────────────────────────────────────────────────────
current=$(git status --porcelain)
if [ "$current" = "$SNAPSHOT" ]; then
  record 0 "원본 저장소 상태 불변" "before/after 동일"
else
  record 1 "원본 저장소 상태 불변" "변경 발생"
fi

printf 'CHECKED: %d\n' "$checked"
if [ "$checked" -ne "$TOTAL" ]; then
  printf 'FAIL: 실행 사례 수 불일치 — expected=%d actual=%d\n' "$TOTAL" "$checked"
  failed=1
fi
if [ "$failed" -eq 0 ]; then
  echo "VERDICT: PASS"
else
  echo "VERDICT: FAIL"
fi
exit "$failed"
