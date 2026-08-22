#!/usr/bin/env bash
# P3 린터의 금지 패턴, 의도적 Map 기본값, fail-closed를 격리 fixture로 검증한다.
set -uo pipefail

unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE GIT_OBJECT_DIRECTORY \
      GIT_ALTERNATE_OBJECT_DIRECTORIES GIT_COMMON_DIR GIT_PREFIX GIT_QUARANTINE_PATH

REPO=$(git rev-parse --show-toplevel 2>/dev/null) || {
  echo "NOT_RUN: git 저장소가 아니다"
  echo "CHECKED: 0"
  exit 2
}
LINT="$REPO/scripts/acceptance-silent-failure-lint.sh"
SNAPSHOT=$(git -C "$REPO" status --porcelain)
TMP=$(mktemp -d "${TMPDIR:-/tmp}/p3-lint.XXXXXX") || {
  echo "NOT_RUN: fixture 디렉터리를 만들 수 없다"
  echo "CHECKED: 0"
  exit 2
}
trap 'ruby -rfileutils -e "FileUtils.remove_entry(ARGV[0]) if File.exist?(ARGV[0])" "$TMP"' EXIT

fail=0
checked=0

record() {
  local ok="$1" description="$2" detail="$3"
  checked=$((checked + 1))
  if [ "$ok" -eq 0 ]; then
    printf 'PASS: %s — %s\n' "$description" "$detail"
  else
    printf 'FAIL: %s — %s\n' "$description" "$detail"
    fail=1
  fi
}

expect() {
  local description="$1" file="$2" expected_rc="$3" marker="$4"
  local rc=0 output=""
  output=$(bash "$LINT" "$file" 2>&1) || rc=$?
  if [ "$rc" -eq "$expected_rc" ] && { [ -z "$marker" ] || printf '%s\n' "$output" | grep -Fq "$marker"; }; then
    record 0 "$description" "exit=$rc${marker:+, marker=$marker}"
  else
    record 1 "$description" "expected=$expected_rc/$marker actual=$rc output=${output//$'\n'/ | }"
  fi
}

cat > "$TMP/clean.py" <<'EOF'
def load(path):
    try:
        return open(path).read()
    except FileNotFoundError:
        raise RuntimeError("input_missing")
EOF
expect "구체적 Python 예외 처리" "$TMP/clean.py" 0 "PASS:"

cat > "$TMP/bare.py" <<'EOF'
def load():
    try:
        return risky()
    except:
        return None
EOF
expect "Python bare except 차단" "$TMP/bare.py" 1 "bare-except"

cat > "$TMP/empty-catch.mjs" <<'EOF'
function load() {
  try { return risky(); } catch (error) { /* ignored */ }
}
EOF
expect "JavaScript 모듈 빈 catch 차단" "$TMP/empty-catch.mjs" 1 "bare-catch"

cat > "$TMP/catch-null.ts" <<'EOF'
function load() {
  try { return risky(); } catch (error) { return (null); }
}
EOF
expect "catch return null 차단" "$TMP/catch-null.ts" 1 "catch-return-null"

cat > "$TMP/catch-null-unreachable.js" <<'EOF'
function load() {
  try { return risky(); } catch (error) { return null; console.error(error); }
}
EOF
expect "return null 뒤 죽은 문장으로 우회 불가" "$TMP/catch-null-unreachable.js" 1 "catch-return-null"

cat > "$TMP/catch-null-after-log.js" <<'EOF'
function load() {
  try { return risky(); } catch (error) {
    console.error(error);
    return null;
  }
}
EOF
expect "로그 뒤 catch return null도 차단" "$TMP/catch-null-after-log.js" 1 "catch-return-null"

cat > "$TMP/catch-null-conditional.ts" <<'EOF'
function load(recoverable: boolean) {
  try { return risky(); } catch (error) {
    markFailed(error);
    if (recoverable) { return null; }
    throw error;
  }
}
EOF
expect "조건문 안 catch return null도 차단" "$TMP/catch-null-conditional.ts" 1 "catch-return-null"

cat > "$TMP/or-array.js" <<'EOF'
const items = response.items || [];
EOF
expect "일반 || [] 기본값 차단" "$TMP/or-array.js" 1 "or-empty-array-fallback"

cat > "$TMP/nullish.ts" <<'EOF'
const retries = response.retries ?? 3;
EOF
expect "일반 ?? 기본값 차단" "$TMP/nullish.ts" 1 "nullish-coalescing-fallback"

cat > "$TMP/assignments.ts" <<'EOF'
state.items ||= [];
config.retries ??= 3;
EOF
rc=0
output=$(bash "$LINT" "$TMP/assignments.ts" 2>&1) || rc=$?
if [ "$rc" -eq 1 ] \
   && [ "$(printf '%s\n' "$output" | grep -c 'or-empty-array-fallback')" -eq 1 ] \
   && [ "$(printf '%s\n' "$output" | grep -c 'nullish-coalescing-fallback')" -eq 1 ]; then
  record 0 "복합 대입 기본값 2종 차단" "exit=1, markers=2"
else
  record 1 "복합 대입 기본값 2종 차단" "exit=$rc output=${output//$'\n'/ | }"
fi

cat > "$TMP/declared-map.js" <<'EOF'
const grouped = new Map();
const values = grouped.get("known-key") || [];
(grouped.get("empty-group") || []).forEach(render);
EOF
expect "선언된 Map.get 빈 컬렉션 모델링 허용" "$TMP/declared-map.js" 0 "PASS:"

cat > "$TMP/reassignable-map.js" <<'EOF'
let grouped = new Map();
const values = grouped.get("key") || [];
EOF
expect "재할당 가능한 Map 변수는 예외 아님" "$TMP/reassignable-map.js" 1 "or-empty-array-fallback"

cat > "$TMP/unknown-get.js" <<'EOF'
const values = api.get("items") || [];
EOF
expect "임의 get 호출의 || []는 예외 아님" "$TMP/unknown-get.js" 1 "or-empty-array-fallback"

cat > "$TMP/shadowed-map-parameter.js" <<'EOF'
const grouped = new Map();
function load(grouped) {
  return grouped.get("items") || [];
}
EOF
expect "Map 이름을 가린 함수 매개변수는 예외 아님" "$TMP/shadowed-map-parameter.js" 1 "or-empty-array-fallback"

cat > "$TMP/shadowed-map-local.js" <<'EOF'
const grouped = new Map();
function load() {
  const grouped = api;
  return grouped.get("items") || [];
}
EOF
expect "Map 이름을 가린 내부 선언은 예외 아님" "$TMP/shadowed-map-local.js" 1 "or-empty-array-fallback"

cat > "$TMP/enclosing-map.js" <<'EOF'
function load(keys) {
  const grouped = new Map();
  return keys.map((key) => grouped.get(key) || []);
}
EOF
expect "둘러싼 유효 범위의 const Map은 예외 유지" "$TMP/enclosing-map.js" 0 "PASS:"

cat > "$TMP/escaped-block-map.js" <<'EOF'
if (enabled) {
  const grouped = new Map();
}
const values = grouped.get("items") || [];
EOF
expect "다른 블록의 Map 이름은 예외로 새지 않음" "$TMP/escaped-block-map.js" 1 "or-empty-array-fallback"

cat > "$TMP/literals.jsx" <<'EOF'
const text = "catch (error) {} and value ?? fallback";
const pattern = /catch \(error\) \{\}|value\?\?/;
const view = <div>documentation ?? value || []</div>;
function handled() {
  try { return risky(); } catch (error) { console.error(error); throw error; }
}
EOF
expect "문자열·정규식·JSX 본문과 처리된 catch 허용" "$TMP/literals.jsx" 0 "PASS:"

cat > "$TMP/template.ts" <<'EOF'
const message = `literal ?? ${value ?? 3}`;
EOF
expect "템플릿 보간식 안 실행 ?? 차단" "$TMP/template.ts" 1 "nullish-coalescing-fallback"

# 인자 없는 전체 수집은 확장자 대소문자와 무관하게 모든 대상 파일을 찾아야 한다.
CASE_REPO="$TMP/case-repo"
git -C "$TMP" init --quiet case-repo
cat > "$CASE_REPO/bypass.JS" <<'EOF'
const items = response.items || [];
EOF
cat > "$CASE_REPO/bypass.PY" <<'EOF'
def load():
    try:
        return risky()
    except:
        return None
EOF
cat > "$CASE_REPO/bypass.TSX" <<'EOF'
const retries = response.retries ?? 3;
EOF
git -C "$CASE_REPO" add bypass.JS bypass.PY bypass.TSX
case_rc=0
case_output=$(cd "$CASE_REPO" && bash "$LINT" 2>&1) || case_rc=$?
case_checked=$(printf '%s\n' "$case_output" | sed -n 's/^CHECKED_FILES: //p' | tail -1)
if [ "$case_rc" -eq 1 ] \
   && [ "$case_checked" -eq 3 ] 2>/dev/null \
   && printf '%s\n' "$case_output" | grep -Fq "or-empty-array-fallback" \
   && printf '%s\n' "$case_output" | grep -Fq "bare-except" \
   && printf '%s\n' "$case_output" | grep -Fq "nullish-coalescing-fallback"; then
  record 0 "전체 수집은 대문자 확장자 3종 포함" "exit=1, checked=3"
else
  record 1 "전체 수집은 대문자 확장자 3종 포함" "exit=$case_rc checked=${case_checked:-없음} output=${case_output//$'\n'/ | }"
fi

cat > "$TMP/invalid.py" <<'EOF'
def broken(:
    pass
EOF
expect "깨진 Python은 합격 대신 NOT_RUN" "$TMP/invalid.py" 2 "NOT_RUN:"

expect "존재하지 않는 입력은 NOT_RUN" "$TMP/missing.py" 2 "NOT_RUN:"

mixed_rc=0
mixed_output=$(bash "$LINT" "$TMP/clean.py" "$TMP/missing.py" 2>&1) || mixed_rc=$?
if [ "$mixed_rc" -eq 2 ] && printf '%s\n' "$mixed_output" | grep -Fq "NOT_RUN:"; then
  record 0 "정상 파일에 누락 입력을 섞어도 fail-closed" "exit=2"
else
  record 1 "정상 파일에 누락 입력을 섞어도 fail-closed" "exit=$mixed_rc output=${mixed_output//$'\n'/ | }"
fi

# 실제 pre-commit은 작업트리가 아니라 스테이지된 blob을 검사해야 한다.
HOOK_REPO="$TMP/hook-repo"
git clone --quiet --shared "$REPO" "$HOOK_REPO" 2>/dev/null
hook_setup=$?
if [ "$hook_setup" -eq 0 ]; then
  cp "$REPO/hooks/pre-commit" "$HOOK_REPO/hooks/pre-commit"
  cp "$LINT" "$HOOK_REPO/scripts/acceptance-silent-failure-lint.sh"
  chmod +x "$HOOK_REPO/hooks/pre-commit" "$HOOK_REPO/scripts/acceptance-silent-failure-lint.sh"
  git -C "$HOOK_REPO" config user.email "p3@example.invalid"
  git -C "$HOOK_REPO" config user.name "P3 fixture"
  printf 'function bad() { try { risky(); } catch (error) {} }\n' > "$HOOK_REPO/p3-bad.js"
  git -C "$HOOK_REPO" add hooks/pre-commit scripts/acceptance-silent-failure-lint.sh p3-bad.js
  hook_rc=0
  hook_output=$(cd "$HOOK_REPO" && bash hooks/pre-commit 2>&1) || hook_rc=$?
  if [ "$hook_rc" -eq 1 ] && printf '%s\n' "$hook_output" | grep -Fq "조용한 실패 패턴 발견 (P3)"; then
    record 0 "pre-commit 위반 blob 차단" "exit=1"
  else
    record 1 "pre-commit 위반 blob 차단" "exit=$hook_rc output=${hook_output//$'\n'/ | }"
  fi

  printf 'function good() { return 1; }\n' > "$HOOK_REPO/p3-bad.js"
  git -C "$HOOK_REPO" add p3-bad.js
  printf 'function bad() { try { risky(); } catch (error) {} }\n' > "$HOOK_REPO/p3-bad.js"
  hook_rc=0
  hook_output=$(cd "$HOOK_REPO" && bash hooks/pre-commit 2>&1) || hook_rc=$?
  if [ "$hook_rc" -eq 0 ]; then
    record 0 "pre-commit은 작업트리 미끼 대신 정상 index blob 판정" "exit=0"
  else
    record 1 "pre-commit은 작업트리 미끼 대신 정상 index blob 판정" "exit=$hook_rc output=${hook_output//$'\n'/ | }"
  fi

  printf 'const items = response.items || [];\n' > "$HOOK_REPO/p3-uppercase-bad.JS"
  git -C "$HOOK_REPO" add p3-uppercase-bad.JS
  hook_rc=0
  hook_output=$(cd "$HOOK_REPO" && bash hooks/pre-commit 2>&1) || hook_rc=$?
  if [ "$hook_rc" -eq 1 ] && printf '%s\n' "$hook_output" | grep -Fq "조용한 실패 패턴 발견 (P3)"; then
    record 0 "pre-commit은 대문자 확장자 index blob 차단" "exit=1"
  else
    record 1 "pre-commit은 대문자 확장자 index blob 차단" "exit=$hook_rc output=${hook_output//$'\n'/ | }"
  fi
else
  record 1 "pre-commit fixture 준비" "git clone exit=$hook_setup"
fi

repo_rc=0
repo_output=$(cd "$REPO" && bash "$LINT" 2>&1) || repo_rc=$?
repo_checked=$(printf '%s\n' "$repo_output" | sed -n 's/^CHECKED_FILES: //p' | tail -1)
if [ "$repo_rc" -eq 0 ] && [ "${repo_checked:-0}" -gt 0 ] 2>/dev/null; then
  record 0 "현재 main 소스 전체 회귀" "exit=0, checked=$repo_checked"
else
  record 1 "현재 main 소스 전체 회귀" "exit=$repo_rc output=${repo_output//$'\n'/ | }"
fi

AFTER=$(git -C "$REPO" status --porcelain)
if [ "$SNAPSHOT" = "$AFTER" ]; then
  record 0 "원본 worktree 기준선 보존" "before=after"
else
  record 1 "원본 worktree 기준선 보존" "검사가 저장소를 변경했다"
fi

echo "CHECKED: $checked"
exit "$fail"
