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
bash "$LINT" "$TMP/clean.py" >/tmp/.p3out 2>&1 || rc=$?
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
bash "$LINT" "$TMP/clean.py" >/tmp/.p3out2 2>&1 || rc=$?
[ "$rc" -eq 0 ] && ok=0 || ok=1
record "$ok" "정상 fixture 재확인(회귀 없음)" "exit=$rc"

# 9) hooks/pre-commit 실제 배선 — 격리 임시 git 저장소에서 진짜 훅을 실행해 확인한다.
# (acceptance-hs-a4.sh와 같은 방식: 판정을 다시 구현하지 않고 실제 hooks/pre-commit을 그대로 돈다.)
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
  chmod +x hooks/pre-commit scripts/acceptance-silent-failure-lint.sh &&
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

# 원본 저장소 무변경 확인
AFTER=$(git -C "$REPO" status --porcelain)
[ "$SNAPSHOT" = "$AFTER" ] && ok=0 || ok=1
record "$ok" "원본 worktree 상태 기준선 보존" "before/after 동일 여부=$ok"

echo "CHECKED: $checked"
exit "$fail"
