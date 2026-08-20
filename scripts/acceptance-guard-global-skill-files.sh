#!/usr/bin/env bash
# acceptance-guard-global-skill-files.sh — guard 복제본의 복구와 동일 UID 한계를 격리 검증한다.
set -uo pipefail

unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE GIT_OBJECT_DIRECTORY \
      GIT_ALTERNATE_OBJECT_DIRECTORIES GIT_COMMON_DIR GIT_PREFIX GIT_QUARANTINE_PATH

REPO=$(git rev-parse --show-toplevel 2>/dev/null) || {
  echo "NOT_RUN: git 저장소가 아니다"
  echo "CHECKED: 0"
  exit 2
}
SNAPSHOT=$(git -C "$REPO" status --porcelain)
TMP=$(mktemp -d) || {
  echo "NOT_RUN: mktemp 실패"
  echo "CHECKED: 0"
  exit 2
}
trap 'ruby -rfileutils -e "FileUtils.remove_entry(ARGV[0]) if File.exist?(ARGV[0])" "$TMP"' EXIT

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

mode_of() {
  # GNU(리눅스 CI 러너)를 먼저 시도한다 — guard-global-skill-files.sh의 file_mode()와
  # 동일한 이유(2026-08-19): BSD -f와 GNU -f는 의미가 전혀 달라서, BSD 순서를 그대로
  # 쓰면 리눅스에서 -f가 디스크 정보를 권한 값처럼 반환한다.
  if stat -c '%a' "$1" 2>/dev/null; then
    return 0
  fi
  stat -f '%Lp' "$1" 2>/dev/null
}

make_guard() {
  local name="$1" dir
  dir="$TMP/$name"
  mkdir -p "$dir/files" "$dir/state"
  cp "$REPO/scripts/guard-global-skill-files.sh" "$dir/guard.sh"
  cp "$REPO/docs/sot/coding-principles.md" "$dir/files/claude.md"
  cp "$REPO/docs/sot/git-workflow.md" "$dir/files/codex.md"
  chmod 640 "$dir/files/claude.md"
  chmod 600 "$dir/files/codex.md"
  ruby - "$dir/guard.sh" "$dir" <<'RUBY'
path, dir = ARGV
raw = File.read(path)
raw = raw.gsub('$HOME/.claude/skills/strict/SKILL.md', "#{dir}/files/claude.md")
raw = raw.gsub('$HOME/.codex/skills/strict/SKILL.md', "#{dir}/files/codex.md")
raw = raw.gsub('$HOME/.cache/valuehire-guard', "#{dir}/state")
File.write(path, raw)
RUBY
  chmod +x "$dir/guard.sh"
}

make_guard normal
normal_rc=0
bash "$TMP/normal/guard.sh" lock >/dev/null || normal_rc=$?
if [ "$normal_rc" -eq 0 ] &&
   [ "$(mode_of "$TMP/normal/files/claude.md")" = 444 ] &&
   [ "$(mode_of "$TMP/normal/files/codex.md")" = 444 ]; then
  normal_ok=0
else
  normal_ok=1
fi
record "$normal_ok" "normal lock" "exit=$normal_rc, modes=444/444"

unlock_before_rc=0
bash "$TMP/normal/guard.sh" unlock >/dev/null 2>&1 || unlock_before_rc=$?
if [ "$unlock_before_rc" -ne 0 ]; then unlock_before_ok=0; else unlock_before_ok=1; fi
record "$unlock_before_ok" "check 전 unlock 거부" "exit=$unlock_before_rc"

check_rc=0
unlock_rc=0
bash "$TMP/normal/guard.sh" check >/dev/null || check_rc=$?
bash "$TMP/normal/guard.sh" unlock >/dev/null || unlock_rc=$?
if [ "$check_rc" -eq 0 ] && [ "$unlock_rc" -eq 0 ] &&
   [ "$(mode_of "$TMP/normal/files/claude.md")" = 640 ] &&
   [ "$(mode_of "$TMP/normal/files/codex.md")" = 600 ]; then
  normal_close_ok=0
else
  normal_close_ok=1
fi
record "$normal_close_ok" "check 뒤 unlock + 원래 권한 복구" "check=$check_rc unlock=$unlock_rc"

make_guard missing
ruby -rfileutils -e 'FileUtils.rm(ARGV[0])' "$TMP/missing/files/codex.md"
missing_rc=0
bash "$TMP/missing/guard.sh" lock >/dev/null 2>&1 || missing_rc=$?
if [ "$missing_rc" -ne 0 ] &&
   [ "$(mode_of "$TMP/missing/files/claude.md")" = 640 ] &&
   [ ! -e "$TMP/missing/state/strict-skill-files.state" ]; then
  missing_ok=0
else
  missing_ok=1
fi
record "$missing_ok" "두 번째 파일 누락 preflight" "exit=$missing_rc, first-mode=$(mode_of "$TMP/missing/files/claude.md")"

make_guard interrupted
ruby - "$TMP/interrupted/guard.sh" <<'RUBY'
path = ARGV[0]
raw = File.read(path)
needle = <<'TEXT'
    if ! chmod 444 "$file"; then
      echo "FAIL: lock 권한 적용 실패 — $file"
      return 1
    fi
TEXT
replacement = needle + "    kill -TERM $$\n"
abort "fixture injection failed" unless raw.sub!(needle, replacement)
File.write(path, raw)
RUBY
if [ "$?" -ne 0 ]; then
  echo "NOT_RUN: 중간 종료 fixture 주입 실패"
  echo "CHECKED: $checked"
  exit 2
fi
interrupted_rc=0
bash "$TMP/interrupted/guard.sh" lock >/dev/null 2>&1 || interrupted_rc=$?
if [ "$interrupted_rc" -ne 0 ] &&
   [ "$(mode_of "$TMP/interrupted/files/claude.md")" = 640 ] &&
   [ "$(mode_of "$TMP/interrupted/files/codex.md")" = 600 ] &&
   [ ! -e "$TMP/interrupted/state/strict-skill-files.state" ]; then
  interrupted_ok=0
else
  interrupted_ok=1
fi
record "$interrupted_ok" "첫 chmod 뒤 중간 종료 rollback" "exit=$interrupted_rc"

make_guard recover
bash "$TMP/recover/guard.sh" lock >/dev/null
recover_rc=0
recover_output=$(bash "$TMP/recover/guard.sh" recover 2>&1) || recover_rc=$?
if [ "$recover_rc" -eq 0 ] &&
   printf '%s\n' "$recover_output" | grep -qF "RECOVERED_WITHOUT_INTEGRITY_PROOF" &&
   [ "$(mode_of "$TMP/recover/files/claude.md")" = 640 ] &&
   [ "$(mode_of "$TMP/recover/files/codex.md")" = 600 ]; then
  recover_ok=0
else
  recover_ok=1
fi
record "$recover_ok" "비정상 종료 뒤 recover" "exit=$recover_rc, PASS로 세지 않는 표식"

# ── 복구 실패 주입 (Inv1·Inv2·Inv3·Inv4) ─────────────────────────────────────
# 기존 "중간 종료 rollback" 케이스는 되돌리기가 성공하는 경로만 본다. 실제로 위험한
# 것은 되돌리기 자체가 실패했을 때다: 파일1은 잠긴 채 남는데 복구 장부를 지워버리면
# 다시 되돌릴 방법이 영영 사라진다. chmod 를 2회차부터 실패시켜 그 상황을 만든다.
make_guard recovery_fail
mkdir -p "$TMP/recovery_fail/bin"
cat > "$TMP/recovery_fail/bin/chmod" <<'STUB'
#!/usr/bin/env bash
if [ -f "$CHMOD_COUNTER" ]; then n=$(cat "$CHMOD_COUNTER"); else n=0; fi
n=$((n + 1))
printf '%s\n' "$n" > "$CHMOD_COUNTER"
if [ "$n" -ge 2 ]; then
  printf 'chmod: injected failure (call #%s)\n' "$n" >&2
  exit 1
fi
exec /bin/chmod "$@"
STUB
chmod +x "$TMP/recovery_fail/bin/chmod"
rf_state="$TMP/recovery_fail/state/strict-skill-files.state"
rf_rc=0
rf_output=$(CHMOD_COUNTER="$TMP/recovery_fail/counter" \
  PATH="$TMP/recovery_fail/bin:$PATH" \
  bash "$TMP/recovery_fail/guard.sh" lock 2>&1) || rf_rc=$?

# Inv1 — 복구가 100% 성공하기 전에는 복구 장부를 지우지 않는다.
if [ -f "$rf_state" ]; then rf_state_ok=0; else rf_state_ok=1; fi
record "$rf_state_ok" "Inv1 복구 실패 시 recovery state 보존" \
  "lock exit=$rf_rc, state=$([ -f "$rf_state" ] && echo 존재 || echo 삭제됨)"

# Inv2 — 복구 실패를 삼키지 않는다.
if printf '%s\n' "$rf_output" | grep -qF "RECOVERY_FAILED"; then rf_loud_ok=0; else rf_loud_ok=1; fi
record "$rf_loud_ok" "Inv2 복구 실패를 출력으로 알린다" "RECOVERY_FAILED 표식"

# Inv3 — 부분 적용이면 재복구가 필요한 상태임을 표식으로 남긴다.
if printf '%s\n' "$rf_output" | grep -qF "RECOVERY_REQUIRED"; then rf_mark_ok=0; else rf_mark_ok=1; fi
record "$rf_mark_ok" "Inv3 부분 적용은 RECOVERY_REQUIRED 로 남는다" "표식 출력"

# Inv4 — 실패 뒤에도 다시 복구할 수 있다(주입 없이 recover 재실행).
rf_recover_rc=0
bash "$TMP/recovery_fail/guard.sh" recover >/dev/null 2>&1 || rf_recover_rc=$?
rf_m1=$(mode_of "$TMP/recovery_fail/files/claude.md")
rf_m2=$(mode_of "$TMP/recovery_fail/files/codex.md")
if [ "$rf_recover_rc" -eq 0 ] && [ "$rf_m1" = 640 ] && [ "$rf_m2" = 600 ]; then
  rf_again_ok=0
else
  rf_again_ok=1
fi
record "$rf_again_ok" "Inv4 실패 뒤 recover 재실행 가능" \
  "recover exit=$rf_recover_rc, modes=$rf_m1/$rf_m2 (기대 640/600)"

make_guard same_uid
bash "$TMP/same_uid/guard.sh" lock >/dev/null
chmod 644 "$TMP/same_uid/files/claude.md"
printf '\nforged-by-same-uid\n' >> "$TMP/same_uid/files/claude.md"
forged_hash=$(shasum -a 256 "$TMP/same_uid/files/claude.md" | awk '{print $1}')
state="$TMP/same_uid/state/strict-skill-files.state"
ruby - "$state" "$TMP/same_uid/files/claude.md" "$forged_hash" <<'RUBY'
path, target, hash = ARGV
lines = File.readlines(path).map do |line|
  fields = line.chomp.split("\t", -1)
  fields[2] = hash if fields[0] == target
  fields.join("\t") + "\n"
end
File.write(path, lines.join)
RUBY
chmod 444 "$TMP/same_uid/files/claude.md"
forgery_rc=0
bash "$TMP/same_uid/guard.sh" check >/dev/null || forgery_rc=$?
if [ "$forgery_rc" -eq 0 ]; then forgery_ok=0; else forgery_ok=1; fi
record "$forgery_ok" "동일 UID 내용+상태 위조 우회 재현" "check exit=$forgery_rc (0이 문서화된 한계)"
bash "$TMP/same_uid/guard.sh" unlock >/dev/null

current=$(git -C "$REPO" status --porcelain)
if [ "$current" = "$SNAPSHOT" ]; then status_ok=0; else status_ok=1; fi
record "$status_ok" "원본 worktree 상태 기준선 보존" "before/after 동일"

printf 'CHECKED: %d\n' "$checked"
exit "$fail"

