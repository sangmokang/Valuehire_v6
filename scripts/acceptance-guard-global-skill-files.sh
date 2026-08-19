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
  if stat -f '%Lp' "$1" 2>/dev/null; then
    return 0
  fi
  stat -c '%a' "$1" 2>/dev/null
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
