#!/usr/bin/env bash
# acceptance-silent-failure-lint-mutations.sh — P3 린트(acceptance-silent-failure-lint.sh)의
# 뮤테이션 검증. 4개 금지 패턴을 각각 fixture에 주입해 실제로 FAIL을 내는지,
# 정상 fixture는 PASS인지, 대상 파일 0건은 NOT_RUN(exit 2)인지 확인한다.
set -uo pipefail

unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE GIT_OBJECT_DIRECTORY \
      GIT_ALTERNATE_OBJECT_DIRECTORIES GIT_COMMON_DIR GIT_PREFIX GIT_QUARANTINE_PATH

REPO=$(git rev-parse --show-toplevel 2>/dev/null) || {
  echo "NOT_RUN: git 저장소가 아니다"
  echo "CHECKED: 0"
  exit 2
}
SNAPSHOT=$(git -C "$REPO" status --porcelain)
LINT="$REPO/scripts/acceptance-silent-failure-lint.sh"
TMP=$(mktemp -d) || {
  echo "NOT_RUN: mktemp 실패"
  echo "CHECKED: 0"
  exit 2
}
trap 'rm -rf "$TMP"' EXIT

fail=0
checked=0

record() {
  local ok="$1" desc="$2" detail="$3"
  checked=$((checked + 1))
  if [ "$ok" -eq 0 ]; then
    printf 'PASS: %s — %s\n' "$desc" "$detail"
  else
    printf 'FAIL: %s — %s\n' "$desc" "$detail"
    fail=1
  fi
}

# 1) 정상 Python 파일 — 위반 없음 → exit 0
cat > "$TMP/clean.py" <<'EOF'
def load(path):
    try:
        return open(path).read()
    except FileNotFoundError:
        return None
EOF
rc=0
bash "$LINT" "$TMP/clean.py" >"$TMP/clean-first.log" 2>&1 || rc=$?
[ "$rc" -eq 0 ] && ok=0 || ok=1
record "$ok" "정상 Python 파일 — 위반 없음" "exit=$rc"

# 2) bare except — Python
cat > "$TMP/bare_except.py" <<'EOF'
def load(path):
    try:
        return open(path).read()
    except:
        return None
EOF
rc=0
out=$(bash "$LINT" "$TMP/bare_except.py" 2>&1) || rc=$?
if [ "$rc" -eq 1 ] && printf '%s' "$out" | grep -q "bare-except"; then ok=0; else ok=1; fi
record "$ok" "bare except 주입 — exit=1 + bare-except 마커" "exit=$rc"

# 3) bare/empty catch — JS
cat > "$TMP/bare_catch.js" <<'EOF'
function load(path) {
  try {
    return fs.readFileSync(path);
  } catch (e) {}
}
EOF
rc=0
out=$(bash "$LINT" "$TMP/bare_catch.js" 2>&1) || rc=$?
if [ "$rc" -eq 1 ] && printf '%s' "$out" | grep -q "bare-catch"; then ok=0; else ok=1; fi
record "$ok" "bare/empty catch 주입 — exit=1 + bare-catch 마커" "exit=$rc"

# 4) catch { return null }
cat > "$TMP/catch_null.ts" <<'EOF'
function load(path: string) {
  try {
    return fs.readFileSync(path);
  } catch (e) { return null }
}
EOF
rc=0
out=$(bash "$LINT" "$TMP/catch_null.ts" 2>&1) || rc=$?
if [ "$rc" -eq 1 ] && printf '%s' "$out" | grep -q "catch-return-null"; then ok=0; else ok=1; fi
record "$ok" "catch{return null} 주입 — exit=1 + catch-return-null 마커" "exit=$rc"

# 5) || [] fallback
cat > "$TMP/or_empty.js" <<'EOF'
function names(list) {
  return (list.items || []).map(x => x.name);
}
EOF
rc=0
out=$(bash "$LINT" "$TMP/or_empty.js" 2>&1) || rc=$?
if [ "$rc" -eq 1 ] && printf '%s' "$out" | grep -q "or-empty-array-fallback"; then ok=0; else ok=1; fi
record "$ok" "|| [] 주입 — exit=1 + or-empty-array-fallback 마커" "exit=$rc"

# 6) ?? nullish-coalescing fallback
cat > "$TMP/nullish.ts" <<'EOF'
function limit(cfg: Config) {
  return cfg.maxRetries ?? 3;
}
EOF
rc=0
out=$(bash "$LINT" "$TMP/nullish.ts" 2>&1) || rc=$?
if [ "$rc" -eq 1 ] && printf '%s' "$out" | grep -q "nullish-coalescing-fallback"; then ok=0; else ok=1; fi
record "$ok" "?? 주입 — exit=1 + nullish-coalescing-fallback 마커" "exit=$rc"

# 7) 대상 파일 0건 — NOT_RUN(exit 2), 통과가 아니다(P20 fail-closed)
# collect_files 인자 없이 부르면 git ls-files 를 쓰므로, 존재하지 않는 파일 경로를
# 인자로 줘서 "지정은 됐지만 실존 대상 0건"을 재현한다.
rc=0
out=$(bash "$LINT" "$TMP/does-not-exist.py" 2>&1) || rc=$?
if [ "$rc" -eq 2 ] && printf '%s' "$out" | grep -q "NOT_RUN"; then ok=0; else ok=1; fi
record "$ok" "존재하지 않는 파일 지정 — 0건 스캔은 통과가 아니라 NOT_RUN(exit 2)" "exit=$rc"

# 8) 정상 fixture 재확인 — 다중 파일 동시 검사에서 clean은 섞여도 무해
rc=0
bash "$LINT" "$TMP/clean.py" >"$TMP/clean-second.log" 2>&1 || rc=$?
[ "$rc" -eq 0 ] && ok=0 || ok=1
record "$ok" "정상 fixture 재확인(회귀 없음)" "exit=$rc"

# 9)~19) codex V1이 실제로 뚫은 문법 변형과 오탐을 회귀 시험으로 고정한다.
# 한 파일에 모두 섞어 exit=1만 확인하면 첫 위반 하나가 나머지 누락을 가린다.
# 따라서 서로 다른 문법 변형은 독립 fixture로 실행한다.
cat > "$TMP/python_inline_except.py" <<'EOF'
def load():
    try:
        return 1
    except: return None
EOF
rc=0
out=$(bash "$LINT" "$TMP/python_inline_except.py" 2>&1) || rc=$?
if [ "$rc" -eq 1 ] && printf '%s' "$out" | grep -q "bare-except"; then ok=0; else ok=1; fi
record "$ok" "Python 한 줄 handler bare except → BLOCKED" "exit=$rc"

cat > "$TMP/python_continued_except.py" <<'EOF'
def load():
    try:
        return 1
    except \
    :
        return None
EOF
rc=0
out=$(bash "$LINT" "$TMP/python_continued_except.py" 2>&1) || rc=$?
if [ "$rc" -eq 1 ] && printf '%s' "$out" | grep -q "bare-except"; then ok=0; else ok=1; fi
record "$ok" "Python 줄연결 bare except → BLOCKED" "exit=$rc"

cat > "$TMP/python_docstring.py" <<'EOF'
def documentation():
    text = """
except:
"""
    return text
EOF
rc=0
bash "$LINT" "$TMP/python_docstring.py" >"$TMP/python_docstring.log" 2>&1 || rc=$?
[ "$rc" -eq 0 ] && ok=0 || ok=1
record "$ok" "Python 독스트링 안 except:는 실행 코드가 아니므로 통과" "exit=$rc"

cat > "$TMP/js_empty_multiline.js" <<'EOF'
function load() {
  try { return 1; } catch (e) {
  }
}
EOF
rc=0
out=$(bash "$LINT" "$TMP/js_empty_multiline.js" 2>&1) || rc=$?
if [ "$rc" -eq 1 ] && printf '%s' "$out" | grep -q "bare-catch"; then ok=0; else ok=1; fi
record "$ok" "JavaScript 여러 줄 빈 catch → BLOCKED" "exit=$rc"

cat > "$TMP/js_empty_comment.js" <<'EOF'
function load() {
  try { return 1; } catch /* reason */ (e) { /* deliberately empty */ }
}
EOF
rc=0
out=$(bash "$LINT" "$TMP/js_empty_comment.js" 2>&1) || rc=$?
if [ "$rc" -eq 1 ] && printf '%s' "$out" | grep -q "bare-catch"; then ok=0; else ok=1; fi
record "$ok" "JavaScript 주석만 든 catch → BLOCKED" "exit=$rc"

cat > "$TMP/js_empty_split.js" <<'EOF'
function load() {
  try { return 1; }
  catch
  (e)
  {
  }
}
EOF
rc=0
out=$(bash "$LINT" "$TMP/js_empty_split.js" 2>&1) || rc=$?
if [ "$rc" -eq 1 ] && printf '%s' "$out" | grep -q "bare-catch"; then ok=0; else ok=1; fi
record "$ok" "JavaScript catch·매개변수·블록 줄분리 → BLOCKED" "exit=$rc"

cat > "$TMP/js_null_multiline.ts" <<'EOF'
function load(): number | null {
  try { return 1; } catch (e) {
    return null;
  }
}
EOF
rc=0
out=$(bash "$LINT" "$TMP/js_null_multiline.ts" 2>&1) || rc=$?
if [ "$rc" -eq 1 ] && printf '%s' "$out" | grep -q "catch-return-null"; then ok=0; else ok=1; fi
record "$ok" "TypeScript 여러 줄 catch return null → BLOCKED" "exit=$rc"

cat > "$TMP/js_null_parenthesized.js" <<'EOF'
function load() {
  try { return 1; } catch (e) { return (null); }
}
EOF
rc=0
out=$(bash "$LINT" "$TMP/js_null_parenthesized.js" 2>&1) || rc=$?
if [ "$rc" -eq 1 ] && printf '%s' "$out" | grep -q "catch-return-null"; then ok=0; else ok=1; fi
record "$ok" "JavaScript 괄호로 감싼 catch return null → BLOCKED" "exit=$rc"

cat > "$TMP/js_array_variants.js" <<'EOF'
function a(value) { return value ||
  []; }
function b(value) { return value || [ ]; }
function c(value) { return value || /* fallback */ []; }
EOF
rc=0
out=$(bash "$LINT" "$TMP/js_array_variants.js" 2>&1) || rc=$?
hits=$(printf '%s\n' "$out" | grep -c 'or-empty-array-fallback' || true)
if [ "$rc" -eq 1 ] && [ "$hits" -eq 3 ]; then ok=0; else ok=1; fi
record "$ok" "JavaScript 줄바꿈·내부공백·주석 || [] 3종 → 모두 BLOCKED" "exit=$rc, hits=$hits/3"

cat > "$TMP/js_literals.js" <<'EOF'
const stringText = "catch (e) {} and value ?? fallback";
const templateText = `documentation says value ?? fallback and catch (e) {}`;
// Example only: config ?? defaultValue || []
const regexText = /catch \(e\) \{\}|value\?\?/;
function handled() {
  try { return 1; } catch (e) { console.error(e); throw e; }
}
EOF
rc=0
bash "$LINT" "$TMP/js_literals.js" >"$TMP/js_literals.log" 2>&1 || rc=$?
[ "$rc" -eq 0 ] && ok=0 || ok=1
record "$ok" "JavaScript 문자열·템플릿·주석·정규식과 실제 처리 catch는 통과" "exit=$rc"

cat > "$TMP/js_template_expression.ts" <<'EOF'
const message = `literal ?? ${value ?? 3}`;
EOF
rc=0
out=$(bash "$LINT" "$TMP/js_template_expression.ts" 2>&1) || rc=$?
hits=$(printf '%s\n' "$out" | grep -c 'nullish-coalescing-fallback')
if [ "$rc" -eq 1 ] && [ "$hits" -eq 1 ]; then ok=0; else ok=1; fi
record "$ok" "템플릿 본문은 무시하고 보간식 안 ??만 BLOCKED" "exit=$rc, hits=$hits/1"

cat > "$TMP/jsx_text_and_expression.tsx" <<'EOF'
const view = <div>documentation ?? value || [] catch (e) {} {value ?? 3}</div>;
EOF
rc=0
out=$(bash "$LINT" "$TMP/jsx_text_and_expression.tsx" 2>&1) || rc=$?
nullish_hits=$(printf '%s\n' "$out" | grep -c 'nullish-coalescing-fallback')
other_hits=$(printf '%s\n' "$out" | grep -Ec 'bare-catch|catch-return-null|or-empty-array-fallback')
if [ "$rc" -eq 1 ] && [ "$nullish_hits" -eq 1 ] && [ "$other_hits" -eq 0 ]; then ok=0; else ok=1; fi
record "$ok" "JSX 본문은 무시하고 중괄호 실행식 안 ??만 BLOCKED" "exit=$rc, nullish=$nullish_hits/1, other=$other_hits/0"

cat > "$TMP/js_nested_handled.ts" <<'EOF'
function load(value: number) {
  try { return value; } catch (error) {
    if (error) { console.error(error); }
    throw error;
  }
}
EOF
rc=0
bash "$LINT" "$TMP/js_nested_handled.ts" >"$TMP/js_nested_handled.log" 2>&1 || rc=$?
[ "$rc" -eq 0 ] && ok=0 || ok=1
record "$ok" "중첩 블록에서 실제 처리하는 catch는 통과" "exit=$rc"

cat > "$TMP/js_nested_violations_in_handled_catch.ts" <<'EOF'
function wrapper(cfg: Config, list: ItemList) {
  try { setup(); } catch (wrapError) {
    log(wrapError);
    function hiddenNull() {
      try { return risky(); } catch (error) { return null; }
    }
    function hiddenEmpty() {
      try { risky(); } catch (error) {}
    }
    const hiddenArray = list.items || [];
    const hiddenNullish = cfg.retries ?? 3;
    return { hiddenNull, hiddenEmpty, hiddenArray, hiddenNullish };
  }
}
EOF
rc=0
out=$(bash "$LINT" "$TMP/js_nested_violations_in_handled_catch.ts" 2>&1) || rc=$?
catch_null_hits=$(printf '%s\n' "$out" | grep -c 'catch-return-null' || true)
bare_catch_hits=$(printf '%s\n' "$out" | grep -c 'bare-catch' || true)
array_hits=$(printf '%s\n' "$out" | grep -c 'or-empty-array-fallback' || true)
nullish_hits=$(printf '%s\n' "$out" | grep -c 'nullish-coalescing-fallback' || true)
if [ "$rc" -eq 1 ] \
   && [ "$catch_null_hits" -eq 1 ] \
   && [ "$bare_catch_hits" -eq 1 ] \
   && [ "$array_hits" -eq 1 ] \
   && [ "$nullish_hits" -eq 1 ]; then
  ok=0
else
  ok=1
fi
record "$ok" "처리 중인 바깥 catch 안의 네 위반도 모두 BLOCKED" \
  "exit=$rc, catch-null=$catch_null_hits/1, bare-catch=$bare_catch_hits/1, array=$array_hits/1, nullish=$nullish_hits/1"

cat > "$TMP/invalid.py" <<'EOF'
def broken(:
    pass
EOF
rc=0
out=$(bash "$LINT" "$TMP/invalid.py" 2>&1) || rc=$?
if [ "$rc" -eq 2 ] && printf '%s' "$out" | grep -q 'NOT_RUN'; then ok=0; else ok=1; fi
record "$ok" "깨진 Python 문법은 합격이 아니라 NOT_RUN" "exit=$rc"

cat > "$TMP/invalid.ts" <<'EOF'
function broken() {
  return 1;
EOF
rc=0
out=$(bash "$LINT" "$TMP/invalid.ts" 2>&1) || rc=$?
if [ "$rc" -eq 2 ] && printf '%s' "$out" | grep -q 'NOT_RUN'; then ok=0; else ok=1; fi
record "$ok" "닫히지 않은 TypeScript 블록은 합격이 아니라 NOT_RUN" "exit=$rc"

if [ -z "${P3_SKIP_HOOK_SUBTESTS:-}" ]; then
  p3_job=$(awk '
    /^  p3:/ { inside=1 }
    inside && seen && /^  [A-Za-z0-9_-]+:/ { exit }
    inside { print; seen=1 }
  ' "$REPO/.github/workflows/verify.yml")
  if printf '%s\n' "$p3_job" | grep -Fq 'uses: actions/checkout@v4' \
     && printf '%s\n' "$p3_job" | grep -Fq 'bash scripts/acceptance-silent-failure-lint.sh' \
     && printf '%s\n' "$p3_job" | grep -Fq 'bash scripts/acceptance-silent-failure-lint-mutations.sh' \
     && ! printf '%s\n' "$p3_job" | grep -q '^[[:space:]]*needs:'; then
    ok=0
  else
    ok=1
  fi
  record "$ok" "CI P3 독립 작업은 P1 성적과 무관하게 본체+회귀시험을 실행" "독립 job+두 명령 정적 배선"
fi

# 20)+21) hooks/pre-commit 실제 배선 — 격리 임시 git 저장소에서 진짜 훅을 실행해 확인한다.
# (acceptance-hs-a4.sh와 같은 방식: 판정을 다시 구현하지 않고 실제 hooks/pre-commit을 그대로 돈다.)
#
# ⚠️ P3_SKIP_HOOK_SUBTESTS 가드(2026-08-19): hooks/pre-commit §9(자기보호)는 자신이
# 커밋될 버전으로 **이 스크립트 자체**를 재실행해 검사기가 여전히 위반을 잡는지
# 확인한다. 그런데 이 스크립트가 실제 hooks/pre-commit을 다시 부르는 이 섹션까지
# 함께 재실행되면, 그 안에서 또 hooks/pre-commit → §9 → 이 스크립트 → hooks/pre-commit
# → ... 로 무한 재귀에 빠진다(2026-08-19 실측: 15초 넘게 응답 없음, 강제 종료).
# hooks/pre-commit §9는 검사기의 "패턴 탐지 능력"만 재확인하면 충분하므로(1~8번),
# 자기 자신을 재귀 호출하는 이 섹션(9~10번)은 그 컨텍스트에서 건너뛴다.
if [ -z "${P3_SKIP_HOOK_SUBTESTS:-}" ]; then
HOOKREPO="$TMP/hookrepo"
mkdir -p "$HOOKREPO"
setup_rc=0
(
  cd "$HOOKREPO" &&
  git init --quiet &&
  git symbolic-ref HEAD refs/heads/main &&
  git config user.email "t@example.invalid" && git config user.name "t" &&
  mkdir -p hooks scripts &&
  cp "$REPO/hooks/pre-commit" hooks/pre-commit &&
  cp "$REPO/scripts/acceptance-silent-failure-lint.sh" scripts/acceptance-silent-failure-lint.sh &&
  cp "$REPO/scripts/acceptance-silent-failure-lint-mutations.sh" scripts/acceptance-silent-failure-lint-mutations.sh &&
  chmod +x hooks/pre-commit scripts/acceptance-silent-failure-lint.sh scripts/acceptance-silent-failure-lint-mutations.sh &&
  cp "$REPO/verify.sh" verify.sh 2>/dev/null &&
  cp "$REPO/.secret-patterns.default" .secret-patterns.default 2>/dev/null &&
  cp "$REPO/.check-weakening-patterns" .check-weakening-patterns 2>/dev/null &&
  printf 'id: []\n' > suppressions.yaml &&
  mkdir -p docs/sot &&
  printf 'placeholder\n' > docs/sot/principles.yaml &&
  cp "$REPO/scripts/acceptance-principles-check.sh" scripts/acceptance-principles-check.sh 2>/dev/null &&
  chmod +x scripts/acceptance-principles-check.sh 2>/dev/null &&
  git add -A >/dev/null && git commit --quiet -m init
) >/dev/null 2>&1 || setup_rc=$?

HOOK_BAD_LOG="$TMP/hook_bad.log"
HOOK_GOOD_LOG="$TMP/hook_good.log"

rc=0
if [ -d "$HOOKREPO/.git" ]; then
  (
    cd "$HOOKREPO" &&
    printf 'def f():\n    try:\n        return 1\n    except:\n        return None\n' > scripts/bad.py &&
    git add scripts/bad.py >/dev/null &&
    bash hooks/pre-commit
  ) >"$HOOK_BAD_LOG" 2>&1 || rc=$?
else
  rc=99
fi
if [ "$rc" -eq 1 ] && grep -q "조용한 실패 패턴 발견 (P3)" "$HOOK_BAD_LOG" 2>/dev/null; then ok=0; else ok=1; fi
record "$ok" "실제 hooks/pre-commit 배선(위반 스테이지 → BLOCKED)" "exit=$rc"

rc=0
if [ -d "$HOOKREPO/.git" ]; then
  (
    cd "$HOOKREPO" &&
    git reset --quiet scripts/bad.py 2>/dev/null
    rm -f scripts/bad.py
    printf 'def f():\n    return 1\n' > scripts/good.py &&
    git add scripts/good.py >/dev/null &&
    bash hooks/pre-commit
  ) >"$HOOK_GOOD_LOG" 2>&1 || rc=$?
else
  rc=99
fi
[ "$rc" -eq 0 ] && ok=0 || ok=1
record "$ok" "실제 hooks/pre-commit 배선(정상 파일 → 통과)" "exit=$rc"

# 22) 검사기 자체 무력화 공격 — 2026-08-19 codex V1 적대검증이 실제로 뚫었던 경로.
# Python AST bare-except 판정을 반대로 바꾸면서 위반 파일을
# **같은 커밋**으로 스테이지하면, hooks/pre-commit §8만 있던 시절엔 exit 0으로
# 통과했다(무력화된 확정본으로 자기 자신을 검사했으므로). §9(자기보호: 뮤테이션
# 시험을 확정본으로 재실행)가 이걸 막아야 한다.
HOOK_SELFWEAKEN_LOG="$TMP/hook_selfweaken.log"
HOOK_BENIGN_LOG="$TMP/hook_benign.log"
rc=0
if [ -d "$HOOKREPO/.git" ]; then
  (
    cd "$HOOKREPO" &&
    git reset --quiet >/dev/null 2>&1
    git checkout -q -- scripts/acceptance-silent-failure-lint.sh 2>/dev/null
    rm -f scripts/good.py &&
    perl -pi -e 's/node\.type is None/node.type is not None/' scripts/acceptance-silent-failure-lint.sh &&
    printf 'def f():\n    try:\n        return 1\n    except:\n        return None\n' > scripts/attack.py &&
    git add scripts/acceptance-silent-failure-lint.sh scripts/attack.py >/dev/null &&
    bash hooks/pre-commit
  ) >"$HOOK_SELFWEAKEN_LOG" 2>&1 || rc=$?
else
  rc=99
fi
if [ "$rc" -eq 1 ] && grep -q "P3 검사기 자체가 같은 커밋에서 무력화됨" "$HOOK_SELFWEAKEN_LOG" 2>/dev/null; then ok=0; else ok=1; fi
record "$ok" "검사기 자체 무력화 공격(같은 커밋에서 정규식 무력화+위반) → BLOCKED" "exit=$rc"

# 대조군 — 검사기에 무해한 주석만 더한 정상 개선 커밋은 막히면 안 된다(벽 아닌 게이트).
rc=0
if [ -d "$HOOKREPO/.git" ]; then
  (
    cd "$HOOKREPO" &&
    git reset --quiet >/dev/null 2>&1
    git checkout -q -- scripts/acceptance-silent-failure-lint.sh 2>/dev/null
    rm -f scripts/attack.py &&
    printf '\n# benign comment\n' >> scripts/acceptance-silent-failure-lint.sh &&
    printf '\n# benign comment\n' >> scripts/acceptance-silent-failure-lint-mutations.sh &&
    git add scripts/acceptance-silent-failure-lint.sh scripts/acceptance-silent-failure-lint-mutations.sh >/dev/null &&
    bash hooks/pre-commit
  ) >"$HOOK_BENIGN_LOG" 2>&1 || rc=$?
else
  rc=99
fi
[ "$rc" -eq 0 ] && ok=0 || ok=1
record "$ok" "검사기 무해한 자기개선 커밋은 통과(벽이 아니라 게이트)" "exit=$rc"
fi

# 원본 저장소 무변경 확인
AFTER=$(git -C "$REPO" status --porcelain)
[ "$SNAPSHOT" = "$AFTER" ] && ok=0 || ok=1
record "$ok" "원본 worktree 상태 기준선 보존" "before/after 동일 여부=$ok"

echo "CHECKED: $checked"
exit "$fail"
