당신은 Qwen2.5:14b 독립 적대검증 엔진 V1입니다. 코드를 칭찬하거나 요약하면 실패입니다. 아래 T 계약을 깨뜨릴 수 있는 실제 bash 반례 명령을 단 하나 제안하세요. Codex 구현자의 결론은 받지 않습니다. 명령은 격리 mktemp clone만 다루고 원본 저장소는 읽기 전용이어야 합니다. git commit은 반드시 mktemp 임시 저장소에서만, GIT_* 환경변수 제거 후 scripts/install-hooks.sh로 훅을 설치하여 실행하세요. --no-verify 또는 core.hooksPath 우회는 계약을 깨는 반례가 아닙니다. 명령은 commit exit, stderr, before/after HEAD를 모두 출력해야 합니다. 기존 acceptance 그대로 재실행도 반례가 아닙니다.

T: main staged git commit은 exit!=0, stderr `BLOCKED: direct commit to main`, HEAD 불변(A). 별도 task/example worktree staged commit은 exit0·HEAD 전진. primary worktree의 task/* staged commit은 exit!=0, 다른 stderr `BLOCKED: development commit in primary worktree`, HEAD 불변(B). 0 fixture/case/target PASS 금지.

HOOK POLICY CODE:
REPO=$(git rev-parse --show-toplevel)
cd "$REPO"

fail=0
block() { printf 'BLOCKED: %s\n' "$1" >&2; fail=1; }

# 이슈 #84: 정확한 HEAD와 Git 관리 디렉터리로 커밋 위치를 먼저 판정한다.
# --git-dir == --git-common-dir인 checkout이 기본 worktree다. 연결된 worktree는
# 자체 git-dir이 공통 .git/worktrees/<id>에 있어 두 실제 경로가 다르다.
head_ref=""
if head_ref=$(git symbolic-ref -q HEAD); then
  : # unborn branch에도 refs/heads/<name>을 반환한다.
elif git rev-parse --verify HEAD >/dev/null 2>&1; then
  head_ref=detached-HEAD
else
  block "HEAD 참조 조회 실패 (fail-closed)"
  exit 1
fi
if [ "$head_ref" = refs/heads/main ]; then
  block "direct commit to main"
  exit 1
fi
if [[ "$head_ref" == refs/heads/task/* ]]; then
  git_dir=$(git rev-parse --git-dir) || { block "git-dir 조회 실패 (fail-closed)"; exit 1; }
  common_dir=$(git rev-parse --git-common-dir) || { block "git-common-dir 조회 실패 (fail-closed)"; exit 1; }
  git_dir_real=$(cd "$git_dir" && pwd -P) || { block "git-dir 정규화 실패 (fail-closed)"; exit 1; }
  common_dir_real=$(cd "$common_dir" && pwd -P) || { block "git-common-dir 정규화 실패 (fail-closed)"; exit 1; }
  if [ "$git_dir_real" = "$common_dir_real" ]; then
    block "development commit in primary worktree"
    exit 1
  fi
fi

# R(rename)을 넣지 않으면 `git mv notes.txt leak.db` 가 staged 목록에서 빠져
# 훅을 그대로 통과한다(2026-08-09 실측). 이름만 바꿔도 내용은 그대로다.
staged=$(git diff --cached --name-only --diff-filter=ACMR)
if [ -z "$staged" ]; then exit 0; fi

# scan <설명> <파일> <grep 인자...>
#   반환 0 = 매칭됨 / 1 = 매칭 없음 또는 실행오류(이 경우 block 이 이미 걸림)
scan() {
  local desc="$1" f="$2"; shift 2

ACCEPTANCE ACTUAL-COMMIT CHECK CODE:
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

ACTUAL COMMIT OUTPUT:
CASE: AC1-main-block
COMMAND: git -C /var/folders/4h/jphmynjn2jl54cqy8d_ddhkh0000gn/T/tmp.25tdiCcsU4/main-repo commit -m "acceptance: AC1-main-block"
TIME: 2026-09-16 00:06:24 KST
EXIT: 1
HEAD_BEFORE: 5a67dfb7c6298bd3467d9179a211f4f6cf730fc1
HEAD_AFTER: 5a67dfb7c6298bd3467d9179a211f4f6cf730fc1
STDOUT_BEGIN
STDOUT_END
STDERR_BEGIN
BLOCKED: direct commit to main
STDERR_END
PASS: AC1-main-block — blocked for expected reason, HEAD unchanged
CASE: AC1-main-hook-off-control
COMMAND: git -C /var/folders/4h/jphmynjn2jl54cqy8d_ddhkh0000gn/T/tmp.25tdiCcsU4/main-repo commit -m "acceptance: AC1-main-hook-off-control"
TIME: 2026-09-16 00:06:24 KST
EXIT: 0
HEAD_BEFORE: 5a67dfb7c6298bd3467d9179a211f4f6cf730fc1
HEAD_AFTER: 05b0c09274ef5e660bb579b3e0363e8a007f08c0
STDOUT_BEGIN
[main 05b0c09] acceptance: AC1-main-hook-off-control
 1 file changed, 1 insertion(+)
 create mode 100644 main-control.txt
STDOUT_END
STDERR_BEGIN
STDERR_END
PASS: AC1-main-hook-off-control — commit allowed, HEAD advanced
CASE: AC2-linked-task-allow
COMMAND: git -C /var/folders/4h/jphmynjn2jl54cqy8d_ddhkh0000gn/T/tmp.25tdiCcsU4/task-example commit -m "acceptance: AC2-linked-task-allow"
TIME: 2026-09-16 00:06:30 KST
EXIT: 0
HEAD_BEFORE: 5a67dfb7c6298bd3467d9179a211f4f6cf730fc1
HEAD_AFTER: 6b0b54ea94051b5d830811929c5fcc1f69251e9c
STDOUT_BEGIN
[task/example 6b0b54e] acceptance: AC2-linked-task-allow
 1 file changed, 1 insertion(+)
 create mode 100644 linked-probe.txt
STDOUT_END
STDERR_BEGIN
STDERR_END
PASS: AC2-linked-task-allow — commit allowed, HEAD advanced
CASE: AC3-primary-task-block
COMMAND: git -C /var/folders/4h/jphmynjn2jl54cqy8d_ddhkh0000gn/T/tmp.25tdiCcsU4/primary-repo commit -m "acceptance: AC3-primary-task-block"
TIME: 2026-09-16 00:06:32 KST
EXIT: 1
HEAD_BEFORE: 5a67dfb7c6298bd3467d9179a211f4f6cf730fc1
HEAD_AFTER: 5a67dfb7c6298bd3467d9179a211f4f6cf730fc1
STDOUT_BEGIN
STDOUT_END
STDERR_BEGIN
BLOCKED: development commit in primary worktree
STDERR_END
PASS: AC3-primary-task-block — blocked for expected reason, HEAD unchanged
CASE: AC3-primary-hook-off-control
COMMAND: git -C /var/folders/4h/jphmynjn2jl54cqy8d_ddhkh0000gn/T/tmp.25tdiCcsU4/primary-repo commit -m "acceptance: AC3-primary-hook-off-control"
TIME: 2026-09-16 00:06:32 KST
EXIT: 0
HEAD_BEFORE: 5a67dfb7c6298bd3467d9179a211f4f6cf730fc1
HEAD_AFTER: 2727acd9a1177bbbd31bb1ca661cef7160b4b0c9
STDOUT_BEGIN
[task/primary-example 2727acd] acceptance: AC3-primary-hook-off-control
 1 file changed, 1 insertion(+)
 create mode 100644 primary-control.txt
STDOUT_END
STDERR_BEGIN
STDERR_END
PASS: AC3-primary-hook-off-control — commit allowed, HEAD advanced
FIXTURES: 4
CASES: 5
CHECKED: 5
VERDICT: PASS
OK(run-acceptance): scripts/acceptance-commit-worktree-guards.sh — 판정 6건, CHECKED 5


마지막으로 요구합니다: 코드 요약 금지. 하나의 `bash` 코드 블록만 출력하세요. 명령은 T의 새 경계(예: unborn main, linked main, symbolic path, detached/non-task)를 실제로 공격해야 합니다. 코드 블록 바로 뒤에 2~3문장으로 예상 exit/stderr/HEAD와 무엇이 깨지면 결함인지 적으세요.