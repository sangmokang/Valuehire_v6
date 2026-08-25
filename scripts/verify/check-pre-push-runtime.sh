#!/usr/bin/env bash
# 후보 pre-push가 acceptance 글로브로 probe를 실제 발견·실행하는지 격리 증명한다.
set -uo pipefail

unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE GIT_OBJECT_DIRECTORY \
  GIT_ALTERNATE_OBJECT_DIRECTORIES GIT_COMMON_DIR GIT_PREFIX GIT_QUARANTINE_PATH
unset VH_PREPUSH_DEPTH

REPO=$(git rev-parse --show-toplevel 2>/dev/null) || {
  echo "NOT_RUN: git 저장소가 아니다"
  exit 2
}
cd "$REPO" || exit 2

HOOK=${1:-hooks/pre-push}
case "$HOOK" in
  /*|..*|*/..*|*/../*) echo "FAIL: 안전하지 않은 hook 경로 — $HOOK"; exit 1 ;;
esac
if [ ! -f "$HOOK" ] || [ -L "$HOOK" ]; then
  echo "FAIL: hook 파일 없음 또는 심볼릭 링크 — $HOOK"
  exit 1
fi

TMP_ROOT=$(cd "${TMPDIR:-/tmp}" 2>/dev/null && pwd -P) || {
  echo "NOT_RUN: 임시 루트 확인 실패"
  exit 2
}
TMP=$(mktemp -d "$TMP_ROOT/XXXXXXXXXXXX") || exit 2
if [ ! -d "$TMP" ] || [ -L "$TMP" ] || [ "$(dirname "$TMP")" != "$TMP_ROOT" ]; then
  echo "NOT_RUN: 안전하지 않은 임시 경로 — $TMP"
  exit 2
fi
trap 'rm -rf "$TMP"' EXIT HUP INT TERM

SANDBOX="$TMP/repo"
NONCE=$(od -An -N8 -tx1 /dev/urandom 2>/dev/null | tr -d '[:space:]')
if ! printf '%s\n' "$NONCE" | grep -qE '^[0-9a-f]{16}$'; then
  NONCE="$(date +%s)-$$"
fi
BYTE_HEX=$(printf '%s' "$NONCE" | tr -cd '0-9a-f' | cut -c1-2)
[ -n "$BYTE_HEX" ] || BYTE_HEX=2a
PROBE_EXIT=$((40 + 16#$BYTE_HEX % 80))
PROBE_REL="scripts/acceptance-${NONCE}.sh"
MARKER="$SANDBOX/.runtime-marker-${NONCE}"
MARKER_PROOF="executed-${NONCE}"
mkdir -p "$SANDBOX/hooks" "$SANDBOX/scripts/verify" "$SANDBOX/.github/workflows"
cp "$HOOK" "$SANDBOX/hooks/pre-push"
# pre-push 는 인수 검사를 실행 래퍼로 돌린다. 샌드박스에 래퍼가 없으면 probe 가
# "발견·실행됐는가"가 아니라 "래퍼가 없다"로 실패해 검사의 뜻이 달라진다.
cp scripts/verify/run-acceptance.sh "$SANDBOX/scripts/verify/run-acceptance.sh"
cp .github/workflows/verify.yml "$SANDBOX/.github/workflows/verify.yml"

cat > "$SANDBOX/scripts/acceptance-principles-check.sh" <<'EOF'
#!/usr/bin/env bash
echo "PASS: sandbox stub"
exit 0
EOF
cat > "$SANDBOX/$PROBE_REL" <<EOF
#!/usr/bin/env bash
printf '%s\n' '$MARKER_PROOF' > '$MARKER'
exit $PROBE_EXIT
EOF
cat > "$SANDBOX/verify.sh" <<'EOF'
#!/usr/bin/env bash
echo "PASS: sandbox stub"
exit 0
EOF
chmod +x "$SANDBOX/hooks/pre-push" "$SANDBOX/scripts/verify/run-acceptance.sh" \
  "$SANDBOX/scripts/acceptance-principles-check.sh" \
  "$SANDBOX/$PROBE_REL" "$SANDBOX/verify.sh"

git -C "$SANDBOX" init -q || exit 2
git -C "$SANDBOX" config user.name "Runtime $NONCE"
git -C "$SANDBOX" config user.email "$NONCE@example.invalid"
git -C "$SANDBOX" add -A || exit 2
git -C "$SANDBOX" commit -qm "verify $NONCE" || exit 2

output=$(cd "$SANDBOX" && bash hooks/pre-push 2>&1)
rc=$?
if [ "$rc" -eq 1 ] && [ -f "$MARKER" ] && grep -qxF "$MARKER_PROOF" "$MARKER" && \
   grep -qF "BLOCKED: ./$PROBE_REL exit=$PROBE_EXIT" <<< "$output"; then
  echo "PASS: pre-push runtime probe discovered and executed"
else
  echo "FAIL: pre-push runtime probe 미실행 또는 실패 전파 누락 — exit=$rc"
  printf '%s\n' "$output"
  exit 1
fi

# 스캐너 호출을 없앴도 훅 소스에 문자열이 남는지가 아니라, 실제 pre-push가
# 변조된 워크플로를 차단하는지를 증명한다.
cat > "$SANDBOX/$PROBE_REL" <<'EOF'
#!/usr/bin/env bash
echo "PASS: sandbox runtime probe"
exit 0
EOF
rm -f -- "$MARKER"
ruby -e 'p=ARGV[0]; s=File.read(p); old="run: bash scripts/scan-history-secrets.sh"; abort "scanner line missing" unless s.include?(old); File.write(p, s.sub(old, "run: bash verify.sh"))' \
  "$SANDBOX/.github/workflows/verify.yml"
git -C "$SANDBOX" add "$PROBE_REL" .github/workflows/verify.yml || exit 2
git -C "$SANDBOX" commit -qm "mutate scanner wiring $NONCE" || exit 2

mutated_output=$(cd "$SANDBOX" && bash hooks/pre-push 2>&1)
mutated_rc=$?
if [ "$mutated_rc" -eq 1 ] \
   && grep -qF "CI 의 '히스토리 전량 스캔' 정본 실행이 사라졌다" <<< "$mutated_output"; then
  echo "PASS: pre-push scanner wiring mutation blocked"
  exit 0
fi

echo "FAIL: pre-push scanner wiring mutation 차단 누락 — exit=$mutated_rc"
printf '%s\n' "$mutated_output"
exit 1
