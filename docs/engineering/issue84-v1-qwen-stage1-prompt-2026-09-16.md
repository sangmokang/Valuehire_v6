독립 V1 적대검증의 1차 단계입니다. 당신은 Codex와 다른 Qwen2.5:14b 모델입니다. 작성자 결론은 전달하지 않습니다. 현재 로컬 작업 브랜치의 코드와 원문 실행 출력만 받습니다. 아래 계약을 깨뜨릴 수 있는 명령을 당신이 직접 고안하세요. 저희가 각 명령을 격리된 mktemp clone에서 실행해 전체 출력을 되돌려 드립니다. 원본 저장소의 commit/checkout/reset/stash/push/PR/병합 명령을 절대 제안하지 마세요. 실제 git commit 실증은 mktemp 아래 임시 저장소에서만 허용됩니다. 제안 명령에는 GIT_* 환경변수 제거와 scripts/install-hooks.sh 실제 실행을 포함해야 합니다. 파일 소스 문자열만 찾는 제안은 무효입니다. 명령은 bash에 붙여넣을 수 있는 정확한 코드 블록 2~3개로 작성하고, 예상 종료값/stderr/전후 HEAD 및 깨지는 계약을 적으세요. 동일 기존 acceptance를 단순 재실행하는 명령은 반례가 아닙니다.

T 계약: HEAD=refs/heads/main에서 staged change를 일반 git commit하면 비0, stderr `BLOCKED: direct commit to main`, HEAD 불변(A, 이슈 원문). 별도 task/example worktree staged commit은 0과 새 HEAD. primary worktree task/* staged commit은 비0, stderr `BLOCKED: development commit in primary worktree`, HEAD 불변(B, 이번 요청 추가). fixture/검사 대상/실행 사례가 0이면 PASS 금지. 기존 secret/workflow 정상·차단 유지. 새 acceptance는 실제 pre-push, 고정 CI, verification 명령 및 무결성 계약에 연결. 우회 변수/설정 추가 금지. Git 표준 훅은 --no-verify 등으로 우회 가능한 로컬 가드레일이며 CI는 개발자의 primary 위치를 관찰하지 못함. 원격 branch protection 설정은 미확인.


## hooks/pre-commit 첫 정책: hooks/pre-commit
```text
#!/usr/bin/env bash
# pre-commit — 커밋 시점 로컬 강제 장치 (P4·P13·P14·P22)
#
# 계약: docs/sot/hook-contracts.md
#   출력  : exit 0 (통과) | exit 1 (차단)
#   차단 시 stderr: "BLOCKED: <사유> — <파일경로>"
#   ※ 매칭된 실제 비밀 값은 절대 출력하지 않는다 (패턴 이름과 경로만)
#   불변식: 검사를 실행하지 못하면 exit 1 (fail-closed)
#   제외  : 없음. 이 훅 자신도 검사 대상이다 (P13 ④)
#
# fail-open 방지 규칙 (2026-08-07 실측으로 추가):
#   grep 은 매칭 없음이 exit 1, 실행 오류가 exit >=2 다. 이 둘을 구분하지 않으면
#   패턴이 깨져 검사가 돌지 않은 경우까지 "위반 없음"으로 통과한다. 실제로 발생했다.
#   따라서 모든 스캔은 scan() 을 통하며, exit >=2 는 차단으로 처리한다.
set -euo pipefail

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
  local rc=0
  git show ":$f" | grep -q "$@" || rc=$?
  if [ "$rc" -gt 1 ]; then
    block "검사 실행 실패 — $desc / $f (grep exit=$rc · fail-closed)"
    return 1
  fi
  return "$rc"
```


## 새 실제 git commit acceptance: scripts/acceptance-commit-worktree-guards.sh
```text
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

```


## 실제 최종 AC 원문: docs/engineering/issue84-final-ac-after-fixture-repair-output-2026-09-16.txt
```text
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

```


## 무건 검사 원문: docs/engineering/issue84-zero-cases-output-2026-09-15.txt
```text
CHECKED: 0
VERDICT: FAIL
REASON: fixture=0 target=0 case=0
FAIL(run-acceptance): scripts/acceptance-commit-worktree-guards.sh 종료값 1

```


## 실제 pre-push 원문: docs/engineering/issue84-prepush-final-output-2026-09-16.txt
```text
COMMAND: git -C /var/folders/4h/jphmynjn2jl54cqy8d_ddhkh0000gn/T/tmp.FMmOV4UNBr/repo push --dry-run /var/folders/4h/jphmynjn2jl54cqy8d_ddhkh0000gn/T/tmp.FMmOV4UNBr/remote.git HEAD:refs/heads/task/issue84-commit-guards-20260915
TIME: 2026-09-16 00:06:46 KST
VERDICT: PASS
SOT_LOAD: PASS docs/sot/coding-principles.md
LEDGER_LOAD: PASS docs/sot/principles.yaml
MECHANISMS: PASS 34/34 strict-contract-bindings
WIRING: PASS pre-push=1 ci=1
CHECKED: 34
  skip ./scripts/acceptance-0-2.sh (DEFERRED · CI 담당)
  skip ./scripts/acceptance-0-5.sh (DEFERRED · CI 담당)
  skip ./scripts/acceptance-0-7.sh (PUSH-PERFORMING · CI 담당)
pre-push: 검사 28개 실행
  ok  ./scripts/acceptance-0-2-unreachable-content.sh
  ok  ./scripts/acceptance-0-6.sh
  ok  ./scripts/acceptance-ci-step-integrity.sh
  ok  ./scripts/acceptance-commit-worktree-guards.sh
  ok  ./scripts/acceptance-guard-global-skill-files.sh
  ok  ./scripts/acceptance-hs-a3.sh
  ok  ./scripts/acceptance-hs-a4.sh
  ok  ./scripts/acceptance-hs-cleanroom-absolute-contexts.sh
  ok  ./scripts/acceptance-hs-cleanroom-absolute-paths.sh
  ok  ./scripts/acceptance-hs-cleanroom-colon-paths.sh
  ok  ./scripts/acceptance-hs-cleanroom-file-urls.sh
  ok  ./scripts/acceptance-hs-cleanroom-hook-env-mutations.sh
  ok  ./scripts/acceptance-hs-cleanroom-hook-env.sh
  ok  ./scripts/acceptance-hs-cleanroom-mutations.sh
  ok  ./scripts/acceptance-hs-cleanroom.sh
  ok  ./scripts/acceptance-hs-gates-antiforge.sh
  ok  ./scripts/acceptance-hs-gates-mutations.sh
  ok  ./scripts/acceptance-hs-gates.sh
  ok  ./scripts/acceptance-invoice.sh
  ok  ./scripts/acceptance-principles-check.sh
  ok  ./scripts/acceptance-principles-mutations.sh
  ok  ./scripts/acceptance-secret-webhook-vendor.sh
  ok  ./scripts/acceptance-semantic-mutations.sh
  ok  ./scripts/acceptance-silent-failure-lint-mutations.sh
  ok  ./scripts/acceptance-silent-failure-lint.sh
  ok  ./scripts/acceptance-verified-sha.sh
  ok  ./scripts/acceptance-verify-ac-m.sh
  ok  ./verify.sh
To /var/folders/4h/jphmynjn2jl54cqy8d_ddhkh0000gn/T/tmp.FMmOV4UNBr/remote.git
 * [new branch]      HEAD -> task/issue84-commit-guards-20260915
EXIT: 0

```


## git-workflow 정본: docs/sot/git-workflow.md
```text
# Valuehire v6 — Git/브랜치 전략 (SOT)

최종 갱신: 2026-08-08
근거: `docs/engineering/v6-coding-principles-goal-2026-08-06.md` §4

## 현재 규칙

### 결론: Trunk-based + 수명 짧은 worktree 브랜치 + 태그 릴리스

**GitFlow REJECT.** develop/release/hotfix 분기는 여러 팀의 병렬 릴리스 트레인을 조율하는 장치다.
1인에게는 조율 대상이 없어 순수 오버헤드이며, 더 나쁜 것은 **장수 브랜치 + LLM 생성 코드 = 대형 충돌**이고
**LLM은 충돌을 "코드를 새로 지어내서" 해결한다. v4의 자동로그인 6벌이 그 산물이다.**

**worktree는 브랜치 전략이 아니라 작업 공간 격리 메커니즘**이며 trunk-based와 결합된다.
작업 1개 = worktree 1개 = 브랜치 1개 = 인수 기준 1개.

### 규약

- `main` 보호. 직접 push 금지. **오너 본인도 예외 없음**
- 작업 브랜치 `task/<name>`, 위치 `worktrees/<name>/`, **수명 24~48시간 상한**. 초과 = 인수 기준이 너무 크다는 신호(v4: 워크트리 77개·미병합 브랜치 113개가 방치된 실측 사례)
- 로컬 커밋 위치 정책: HEAD가 `refs/heads/main`이면 모든 checkout에서 직접 커밋을
  거부한다(이슈 #84의 A). 기본 worktree의 HEAD가 `refs/heads/task/*`이면 개발
  커밋을 별도 위치 사유로 거부한다(이번 요청의 B). 정상 허용 범위는 분리된
  `worktrees/<name>/`의 `task/<name>` 브랜치이며 기존 비밀·약화 훅도 통과해야 한다.
  기본 worktree는 Git의 `--git-dir`과 `--git-common-dir` 실제 경로가 같은 checkout이다.
  이 로컬 위치 정책은 다른 브랜치·detached HEAD의 일반 커밋에 대한 보호를
  주장하지 않는다. 표준 훅은 `git commit --no-verify`로 건너뛸 수 있다.
- PR = 인수 기준 1개. **squash merge**, 머지 후 브랜치 삭제
- 릴리스 = `main` 의 어노테이트 태그 `v6.YYYY.MM.DD-N` → CI가 artifact 빌드 → digest 산출 → `releases/<digest>/` 설치
- **자동 병합 금지.** 오너가 diff를 실제로 읽는 것이 P11(코드 예산)의 존재 이유

## 시행 지점

- 워크트리 생성: `git worktree add worktrees/<name> -b task/<name>` (이 저장소엔 아직 `make task`가 없다 — `docs/sot/verification-commands.md` 참고)
- `main` 보호(직접 push 금지)는 아직 GitHub 브랜치 보호 규칙으로 기계 강제되어 있는지 실행으로 재확인 필요 — 이 문서 갱신 시점 기준 미확인.
- 로컬 `hooks/pre-commit`은 빠른 커밋 시점 가드레일이다. CI는 개발자의 기본
  worktree 위치를 관찰할 수 없다. 최종 main 보호는 GitHub branch protection,
  PR 및 최종 SHA의 CI 검증이 담당한다. 실제 원격 보호 설정은 이 작업에서 미확인.

## 비범위 / 한계

- CI가 각 원칙(P1~P22)을 어떻게 강제하는지의 전체 매핑표는 여기 옮기지 않았다 — 원본 goal 문서 §4 "CI가 강제할 것"에 있다.
- `main` 브랜치 보호 규칙의 실제 GitHub 설정 여부는 이 문서 작성 시점에 실행 확인하지 않았다(범위 밖) — 필요 시 `gh api repos/:owner/:repo/branches/main/protection`로 확인한다.

```


## hook-contracts 정본: docs/sot/hook-contracts.md
```text
# Valuehire v6 — 로컬 강제 장치(git hook) 계약 (SOT)

최종 갱신: 2026-08-22
근거(도입 배경·적대검증·6종 위반 시연): `docs/engineering/hook-enforcement-goal-2026-08-07.md`

## 현재 규칙 — 입출력 계약

### `hooks/pre-commit`
```
입력  : stdin 없음. `git symbolic-ref -q HEAD`의 현재 브랜치 참조
        (첫 커밋 전 unborn branch도 참조로 읽음), Git의 git-dir/common-dir,
        스테이징된 파일 목록(git diff --cached --name-only --diff-filter=ACMR)
        ※ R(rename) 포함. 빼면 `git mv notes.txt leak.db` 가 목록에서 사라져 그대로 통과한다
출력  : exit 0 (통과) | exit 1 (차단)
        위치 정책 차단 시 stderr: "BLOCKED: direct commit to main" 또는
        "BLOCKED: development commit in primary worktree".
        기존 staged 검사 차단 시 stderr: "BLOCKED: <검사이름> — <파일경로> (패턴: <패턴이름>)"
        ※ 매칭된 실제 값은 절대 출력하지 않는다
검사  : ⓪ HEAD=refs/heads/main의 직접 커밋 차단(모든 worktree);
        HEAD=refs/heads/task/*이고 git-dir과 git-common-dir의 실제 경로가 같은
        기본 worktree의 개발 커밋 차단. 분리 worktree의 task/*는 아래 기존 staged
        검사 결과에 따라 허용. Git 경로 조회·정규화 오류는 차단한다.
        ① 비밀 스캔(verify.sh 위임, VERIFY_SCAN_SOURCE=index) ② 검사기 자기 제외
        ③ 검사 약화 패턴 ④ 만료 없는/지난 억제 ⑤ LLM 출력→판정 수치 ⑥ 외부효과 모듈 네트워크 0건
        ⑦ 대용량 파일(1,048,576 바이트 초과) · 산출물 경로(artifacts/·data/·private-reviews/·
          *.db·*.sqlite·*.sqlite3) 차단 — P21. gitignore 가 `git add -f` 로 우회되므로
          차단 지점을 훅에도 둔다. 크기는 작업트리가 아니라 **인덱스 blob**에서 잰다
          (작업트리를 재면 add 후 덮어쓰기로 우회된다 — ①과 같은 이유).
          경로/확장자 비교는 **소문자로 정규화**한 뒤 수행한다(dump.DB 가 통과했다).
          디렉터리 규칙은 하위 경로까지 덮고, `.gitignore` 는 최상위로 앵커한다 —
          앵커가 없으면 src/data/schema.json 같은 정상 소스가 조용히 사라진다(P3).
          CI 등가물: `.github/workflows/verify.yml` 의 "대용량 파일 · 산출물 경로 스캔"
          (훅은 이번 커밋의 스테이지분만, CI 는 추적 파일 전체를 본다)
        ⑧ P3 조용한 실패 문법. 동일 block scope의 `const Map`만 제한적으로 예외 처리하고,
          확장자를 소문자로 정규화해 스테이지된 Python/JavaScript
          계열 blob을 같은 커밋의
          `scripts/acceptance-silent-failure-lint.sh`로 검사한다. 작업트리 사본은 판정에
          사용하지 않는다. CI는 같은 린터와 mutation 회귀를 전체 추적 파일에 실행한다
불변식: set -euo pipefail. 검사를 실행하지 못하면 exit 1 (fail-closed).
        위치 정책은 staged 파일이 0개여도 먼저 판정하며, 차단 시 HEAD를 바꾸지 않는다.
        detached HEAD는 유효한 커밋인지 확인하고 두 위치 정책의 범위 밖으로 둔다.
제외  : 없음. 자기 자신(hooks/)도 검사 대상이다
한계  : 표준 Git 로컬 훅은 git commit --no-verify 등으로 우회할 수 있다.
        CI는 개발자 로컬의 기본 worktree 위치를 볼 수 없고 GitHub branch
        protection·PR·CI가 최종 main 보호를 맡는다. 현재 원격 보호 설정은 미확인.
```

### `hooks/pre-push`
```
입력  : stdin 으로 <local ref> <local sha> <remote ref> <remote sha> (git 표준)
출력  : exit 0 | exit 1
        실행: verify.sh, scripts/acceptance-*.sh 전량 (glob — 새 스크립트 추가 시 자동 포함)
        차단 시 stderr: "BLOCKED: <스크립트경로> exit=<code>"
불변식: 스크립트가 0개 발견되면 exit 1 (fail-closed — "검사할 게 없어서 통과"를 금지)
        미추적 파일(??) 존재 시 exit 1 (P15)
한계  : git push --no-verify 로 우회 가능. CI 가 최종 방어선 (문서에 명시)
```

### `scripts/session-status.sh`
```
입력  : 없음
출력  : stdout 3줄 + exit 0
        HEAD: <sha> (<origin 대비: synced|ahead N|behind N>)
        ORIGIN: <sha>
        RED: <실패한 acceptance 스크립트 수>/<전체 수>
불변식: git 조회 실패 시 해당 줄에 "UNKNOWN" 을 출력하고 exit 1 (조용한 성공 금지)
```

### `scripts/acceptance-0-7.sh`
```
입력  : 없음
출력  : exit 0 (6종 전부 BLOCKED) | exit 1 (하나라도 통과)
        각 시연: "[N/6] <위반이름> → BLOCKED (exit=<code>)" 또는 "→ PASSED ← 결함"
불변식: 모든 시연은 mktemp -d 안의 clone 에서 수행.
        종료 시 원본 저장소의 git status 가 시연 전과 동일함을 확인하고, 다르면 exit 1
        판정은 종료 코드로만 한다. 문자열 비교 단독 판정 금지
```

### `scripts/install-hooks.sh`
```
입력  : 없음
동작  : git config core.hooksPath hooks && chmod +x hooks/*
출력  : exit 0 + 설치된 훅 목록
불변식: 실행 후 core.hooksPath 를 재조회해 실제로 설정됐는지 확인(readback). 불일치 시 exit 1
```

## 시행 지점

이 5개 파일 자체가 시행 지점이다. 각 파일 상단 주석의 `# 계약: docs/sot/hook-contracts.md`가 이 문서를 가리킨다 — 파일을 직접 읽으면 항상 최신 계약과 실제 구현이 같은지 대조할 수 있다.

## 비범위 / 한계

- 6종 위반 시연의 실제 실행 결과·적대검증 판정(V1 조건부 REJECT→승인까지 5차 판정)은 `docs/engineering/hook-enforcement-goal-2026-08-07.md` 실행 결과·적대 검증 로그 절에 있다. 이 문서는 재현하지 않는다.
- `git push --no-verify` 우회는 구조적으로 탐지 불가(2026-08-07 확정) — CI가 최종 방어선이라는 전제가 깨지면 이 문서 전체가 무효하다.

```
