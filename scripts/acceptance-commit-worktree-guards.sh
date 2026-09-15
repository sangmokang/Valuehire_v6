#!/usr/bin/env bash
# 이슈 #84: 실제 Git 커밋으로 main(A), 기본 worktree의 task/*(B), 분리 task/* 허용을 검증한다.
# 계약: docs/engineering/issue84-commit-guards-goal-2026-09-15.md
set -uo pipefail

# Git 훅/CI가 물려 준 Git 경로 변수는 임시 저장소 실증에 새어 들어오면 안 된다.
while IFS= read -r name; do unset "$name"; done < <(env | awk -F= '/^GIT_[A-Za-z0-9_]*=/{print $1}')

repo=$(git rev-parse --show-toplevel 2>/dev/null) || {
  printf 'VERDICT: FAIL\nREASON: source repository unavailable\nCHECKED: 0\n'
  exit 2
}
cd "$repo" || exit 2
if [ ! -f hooks/pre-commit ] || [ ! -f scripts/install-hooks.sh ]; then
  printf 'VERDICT: FAIL\nREASON: hook fixture unavailable\nCHECKED: 0\n'
  exit 2
fi

source_status=$(git status --porcelain)
tmp=$(mktemp -d) || {
  printf 'VERDICT: FAIL\nREASON: mktemp failed\nCHECKED: 0\n'
  exit 2
}
trap 'ruby -rfileutils -e "FileUtils.remove_entry(ARGV[0]) if File.exist?(ARGV[0])" "$tmp"' EXIT

fail=0
checked=0
fixtures=0
cases=0
record() {
  local label="$1" ok="$2" detail="$3"
  checked=$((checked + 1))
  if [ "$ok" -eq 0 ]; then printf 'PASS: %s — %s\n' "$label" "$detail"
  else printf 'FAIL: %s — %s\n' "$label" "$detail"; fail=1; fi
}

prepare() {
  local dir="$1"
  git clone -q "$repo" "$dir" || return 1
  git -C "$dir" config user.name acceptance
  git -C "$dir" config user.email acceptance@local.invalid
  (cd "$dir" && bash scripts/install-hooks.sh) > "$tmp/install.$fixtures" 2>&1 || return 1
  if [ "$(git -C "$dir" config --get core.hooksPath)" != hooks ] || [ ! -x "$dir/hooks/pre-commit" ]; then
    return 1
  fi
  fixtures=$((fixtures + 1))
}

stage_probe() {
  local dir="$1" name="$2"
  printf 'policy probe %s\n' "$name" > "$dir/$name"
  git -C "$dir" add -- "$name"
  [ "$(git -C "$dir" diff --cached --name-only)" = "$name" ]
}

# commit_case <label> <worktree> <file> <want:block|allow> <expected-stderr>
commit_case() {
  local label="$1" dir="$2" file="$3" wanted="$4" reason="$5"
  local before after rc=0 stdout="$tmp/out.$cases" stderr="$tmp/err.$cases"
  cases=$((cases + 1))
  if ! stage_probe "$dir" "$file"; then
    record "$label" 1 'staged fixture creation failed'
    return
  fi
  before=$(git -C "$dir" rev-parse HEAD) || { record "$label" 1 'before HEAD unreadable'; return; }
  git -C "$dir" commit -m "acceptance: $label" > "$stdout" 2> "$stderr" || rc=$?
  after=$(git -C "$dir" rev-parse HEAD) || { record "$label" 1 'after HEAD unreadable'; return; }
  printf 'CASE: %s\nCOMMAND: git -C %s commit -m "acceptance: %s"\nTIME: %s\nEXIT: %s\nHEAD_BEFORE: %s\nHEAD_AFTER: %s\n' \
    "$label" "$dir" "$label" "$(date '+%Y-%m-%d %H:%M:%S %Z')" "$rc" "$before" "$after"
  printf 'STDOUT_BEGIN\n'; cat "$stdout"; printf 'STDOUT_END\n'
  printf 'STDERR_BEGIN\n'; cat "$stderr"; printf 'STDERR_END\n'
  if [ "$wanted" = block ]; then
    if [ "$rc" -ne 0 ] && [ "$before" = "$after" ] && grep -qF "$reason" "$stderr"; then
      record "$label" 0 "blocked for expected reason, HEAD unchanged"
    else
      record "$label" 1 "expected blocked reason=$reason and unchanged HEAD; actual exit=$rc"
    fi
  elif [ "$rc" -eq 0 ] && [ "$before" != "$after" ]; then
    record "$label" 0 'commit allowed, HEAD advanced'
  else
    record "$label" 1 "expected allowed commit and new HEAD; actual exit=$rc"
  fi
}

control_case() {
  local label="$1" dir="$2" base="$3" file="$4"
  git -C "$dir" reset -q --hard "$base" || { record "$label" 1 'reset in temporary fixture failed'; return; }
  git -C "$dir" config core.hooksPath /dev/null
  commit_case "$label" "$dir" "$file" allow ''
  git -C "$dir" config core.hooksPath hooks
}

if [ "${1:-}" = --self-test-empty ]; then
  printf 'CHECKED: 0\nVERDICT: FAIL\nREASON: fixture=0 target=0 case=0\n'
  exit 1
fi
if [ "$#" -ne 0 ]; then
  printf 'CHECKED: 0\nVERDICT: FAIL\nREASON: unexpected argument\n'
  exit 2
fi

# A: 어떤 작업 위치든 HEAD=main이면 거부. 훅 OFF 대조군은 같은 입력으로 성공.
main_repo="$tmp/main-repo"
if prepare "$main_repo" && git -C "$main_repo" switch -q -c main; then
  main_base=$(git -C "$main_repo" rev-parse HEAD)
  commit_case 'AC1-main-block' "$main_repo" main-probe.txt block 'BLOCKED: direct commit to main'
  control_case 'AC1-main-hook-off-control' "$main_repo" "$main_base" main-control.txt
else
  record AC1-main-fixture 1 'clone, checkout, or hook installation failed'
fi

# 허용: task/example을 실제 분리 worktree로 checkout하고 설치된 훅으로 커밋.
linked_repo="$tmp/linked-repo"
if prepare "$linked_repo"; then
  linked_base=$(git -C "$linked_repo" rev-parse HEAD)
  linked_dir="$tmp/task-example"
  if git -C "$linked_repo" worktree add -q -b task/example "$linked_dir" "$linked_base" &&
     (cd "$linked_dir" && bash scripts/install-hooks.sh) > "$tmp/install-linked" 2>&1 &&
     [ "$(git -C "$linked_dir" config --get core.hooksPath)" = hooks ] &&
     [ -x "$linked_dir/hooks/pre-commit" ]; then
    fixtures=$((fixtures + 1))
    commit_case 'AC2-linked-task-allow' "$linked_dir" linked-probe.txt allow ''
  else
    record AC2-linked-fixture 1 'linked task worktree or hook installation failed'
  fi
else
  record AC2-linked-fixture 1 'clone or hook installation failed'
fi

# B: 같은 task/*가 기본 worktree에 있으면 main 사유와 구별해 거부.
primary_repo="$tmp/primary-repo"
if prepare "$primary_repo" && git -C "$primary_repo" switch -q -c task/primary-example; then
  primary_base=$(git -C "$primary_repo" rev-parse HEAD)
  commit_case 'AC3-primary-task-block' "$primary_repo" primary-probe.txt block 'BLOCKED: development commit in primary worktree'
  control_case 'AC3-primary-hook-off-control' "$primary_repo" "$primary_base" primary-control.txt
else
  record AC3-primary-fixture 1 'clone, checkout, or hook installation failed'
fi

if [ "$fixtures" -lt 3 ] || [ "$cases" -lt 5 ] || [ "$checked" -lt 5 ]; then
  printf 'FAIL: nonempty contract violated — fixtures=%s cases=%s checked=%s\n' "$fixtures" "$cases" "$checked"
  fail=1
fi
if [ "$(git status --porcelain)" != "$source_status" ]; then
  printf 'FAIL: source status changed during temporary commit demonstrations\n'
  fail=1
fi

printf 'FIXTURES: %s\nCASES: %s\nCHECKED: %s\n' "$fixtures" "$cases" "$checked"
if [ "$fail" -eq 0 ]; then printf 'VERDICT: PASS\n'; else printf 'VERDICT: FAIL\n'; fi
exit "$fail"
