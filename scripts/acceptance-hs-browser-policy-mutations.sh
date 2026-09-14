#!/usr/bin/env bash
# acceptance-hs-browser-policy-mutations.sh — browser-policy 검사가 주석·중복키·타입 변조를 실제로 잡는가.
set -uo pipefail

unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE GIT_OBJECT_DIRECTORY \
  GIT_ALTERNATE_OBJECT_DIRECTORIES GIT_COMMON_DIR GIT_PREFIX GIT_QUARANTINE_PATH

REPO=$(git rev-parse --show-toplevel 2>/dev/null) || {
  echo "VERDICT: NOT_RUN"
  echo "CHECKED: 0"
  exit 2
}
cd "$REPO" || exit 2

SNAPSHOT=$(git status --porcelain)
TMP=$(mktemp -d) || {
  echo "VERDICT: NOT_RUN"
  echo "CHECKED: 0"
  exit 2
}
trap 'rm -rf "$TMP"' EXIT HUP INT TERM

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

make_case() {
  local name="$1"
  local dest="$TMP/$name"
  mkdir -p "$dest/scripts" "$dest/contracts/humansearch" "$dest/docs/sot" "$dest/docs/engineering"
  cp scripts/acceptance-hs-browser-policy.sh "$dest/scripts/"
  cp contracts/humansearch/browser-policy.yaml "$dest/contracts/humansearch/"
  cp docs/sot/humansearch-browser-contract.md "$dest/docs/sot/"
  cp docs/engineering/humansearch-aside-browser-policy-goal-2026-09-14.md "$dest/docs/engineering/"
  git -C "$dest" init -q
  printf '%s\n' "$dest"
}

run_case() {
  local dir="$1" rc=0
  (cd "$dir" && bash scripts/acceptance-hs-browser-policy.sh >/dev/null 2>&1) || rc=$?
  printf '%s\n' "$rc"
}

normal=$(make_case normal)
normal_rc=$(run_case "$normal")
if [ "$normal_rc" -eq 0 ]; then
  record 0 "정상 browser-policy 계약" "exit=0"
else
  record 1 "정상 browser-policy 계약" "exit=$normal_rc"
fi

comment_override=$(make_case comment-override)
ruby -e '
  path = ARGV[0]
  text = File.read(path)
  text = text.sub(/^automation_app: Aside$/, "# automation_app: Aside\nautomation_app: Chrome")
  File.write(path, text)
' "$comment_override/contracts/humansearch/browser-policy.yaml"
rc=$(run_case "$comment_override")
if [ "$rc" -ne 0 ]; then
  record 0 "주석 속 automation_app 위장 차단" "exit=$rc"
else
  record 1 "주석 속 automation_app 위장 차단" "실제 값 Chrome 인데 통과"
fi

duplicate_key=$(make_case duplicate-key)
ruby -e '
  path = ARGV[0]
  text = File.read(path)
  text = text.sub(/^forbidden_app: Chrome$/, "forbidden_app: Chrome\nforbidden_app: Aside")
  File.write(path, text)
' "$duplicate_key/contracts/humansearch/browser-policy.yaml"
rc=$(run_case "$duplicate_key")
if [ "$rc" -ne 0 ]; then
  record 0 "중복키로 마지막 값 뒤집기 차단" "exit=$rc"
else
  record 1 "중복키로 마지막 값 뒤집기 차단" "forbidden_app 중복키가 통과"
fi

typed_bool=$(make_case typed-bool)
ruby -e '
  path = ARGV[0]
  text = File.read(path)
  text = text.sub(/^explicit_stop_requires_user_clear: true$/, "# explicit_stop_requires_user_clear: true\nexplicit_stop_requires_user_clear: \"true\"")
  File.write(path, text)
' "$typed_bool/contracts/humansearch/browser-policy.yaml"
rc=$(run_case "$typed_bool")
if [ "$rc" -ne 0 ]; then
  record 0 "불리언 문자열 위장 차단" "exit=$rc"
else
  record 1 "불리언 문자열 위장 차단" "문자열 true 가 통과"
fi

comment_only=$(make_case comment-only)
cat > "$comment_only/contracts/humansearch/browser-policy.yaml" <<'EOF'
# automation_app: Aside
# forbidden_app: Chrome
# jobkorea: aside_dedicated_profile
# saramin: aside_dedicated_profile
# linkedin_rps: aside_owner_real_profile
# input_attribution: target_app_profile_tab
# resume_requires: fresh_observation_and_fresh_lease
# explicit_stop_requires_user_clear: true
# live_authority_verified: false
version: "2026-09-14.aside-policy"
EOF
rc=$(run_case "$comment_only")
if [ "$rc" -ne 0 ]; then
  record 0 "주석만 남긴 no-op 계약 차단" "exit=$rc"
else
  record 1 "주석만 남긴 no-op 계약 차단" "실제 값 없는 계약이 통과"
fi

SNAP1=$(git status --porcelain)
if [ "$SNAPSHOT" = "$SNAP1" ]; then
  record 0 "원본 저장소 상태 불변" "before/after 동일"
else
  record 1 "원본 저장소 상태 불변" "상태 변경 발생"
fi

if [ "$checked" -lt 6 ]; then
  echo "VERDICT: NOT_RUN"
  echo "CHECKED: $checked"
  exit 2
fi

if [ "$fail" -eq 0 ]; then
  echo "VERDICT: PASS"
else
  echo "VERDICT: FAIL"
fi
echo "CHECKED: $checked"
exit "$fail"
