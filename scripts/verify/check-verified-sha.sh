#!/usr/bin/env bash
# check-verified-sha.sh — 초록불은 브랜치가 아니라 커밋 SHA 에 귀속된다.
#
# 왜 필요한가:
#   "CI 통과했습니다"는 어느 커밋에 대해 통과했는지를 말하지 않는다. PR 원격 HEAD 가
#   929247a 인데 초록불은 그 이전 커밋 것이고 로컬 HEAD 는 또 다른 26ad98c 인 상태에서
#   사람도 LLM 도 "통과"라고 말할 수 있었다. 세 SHA 가 다르면 그 초록불은 지금 머지하려는
#   코드에 대한 것이 아니다.
#
# 계약: 아래가 전부 참일 때만 VERIFIED 다.
#   로컬 HEAD == 원격 브랜치 HEAD == CI 가 실제로 검사한 SHA
#   그 SHA 에 대한 verify 결론이 success
#   작업트리에 커밋되지 않은 변경이 없다
# 하나라도 어긋나면 UNVERIFIED 이고, 조회 자체를 못 하면 NOT_RUN 이다(모르면 통과 아님).
#
# 이 스크립트는 완료를 선언하지 않는다. 상태를 계산해서 출력할 뿐이다.
set -uo pipefail

# ── 순수 판정부 ──────────────────────────────────────────────────────────────
# 조회 없이 다섯 값만으로 판정한다. 인수 검사가 이 경로로 진리표를 전량 시험한다.
evaluate() {
  local local_sha="$1" remote_sha="$2" ci_sha="$3" conclusion="$4" worktree="$5"
  local reasons=()

  for name in local_sha remote_sha ci_sha; do
    local v="${!name}"
    if [ -z "$v" ] || [ "$v" = "none" ]; then
      reasons+=("${name}=없음")
    fi
  done

  if [ "${#reasons[@]}" -eq 0 ]; then
    [ "$local_sha" = "$remote_sha" ] || reasons+=("로컬 HEAD != 원격 HEAD")
    [ "$remote_sha" = "$ci_sha" ] || reasons+=("원격 HEAD != CI 가 검사한 SHA")
  fi
  [ "$conclusion" = "success" ] || reasons+=("CI 결론=${conclusion:-없음}")
  [ "$worktree" = "clean" ] || reasons+=("작업트리=${worktree:-알수없음}")

  printf 'LOCAL_HEAD: %s\n' "${local_sha:-none}"
  printf 'REMOTE_HEAD: %s\n' "${remote_sha:-none}"
  printf 'CI_VERIFIED_SHA: %s\n' "${ci_sha:-none}"
  printf 'CI_CONCLUSION: %s\n' "${conclusion:-none}"
  printf 'WORKTREE: %s\n' "${worktree:-unknown}"
  if [ "${#reasons[@]}" -eq 0 ]; then
    echo "VERDICT: VERIFIED"
    return 0
  fi
  local r
  for r in "${reasons[@]}"; do
    printf 'UNVERIFIED_REASON: %s\n' "$r"
  done
  echo "VERDICT: UNVERIFIED"
  return 1
}

if [ "${1:-}" = "--evaluate" ]; then
  shift
  if [ "$#" -ne 5 ]; then
    echo "FAIL: --evaluate 는 인자 5개가 필요하다 (local remote ci conclusion worktree)"
    exit 2
  fi
  evaluate "$@"
  exit $?
fi

# ── 실제 조회부 ──────────────────────────────────────────────────────────────
branch="${1:-$(git rev-parse --abbrev-ref HEAD 2>/dev/null)}"
if [ -z "$branch" ] || [ "$branch" = "HEAD" ]; then
  echo "NOT_RUN: 브랜치를 확정하지 못했다 (detached HEAD?)"
  exit 2
fi

local_sha=$(git rev-parse HEAD 2>/dev/null)
if [ -z "$local_sha" ]; then
  echo "NOT_RUN: 로컬 HEAD 를 읽지 못했다"
  exit 2
fi

remote_sha=$(git ls-remote origin "refs/heads/$branch" 2>/dev/null | awk '{print $1}' | head -1)
if [ -z "$remote_sha" ]; then
  echo "NOT_RUN: 원격에 $branch 가 없다 — 아직 push 되지 않았다면 검증된 SHA 자체가 없다"
  exit 2
fi

if ! command -v gh > /dev/null 2>&1; then
  echo "NOT_RUN: gh CLI 가 없어 CI 결론을 조회할 수 없다"
  exit 2
fi

# 원격 HEAD SHA 에 붙은 check-run 만 본다. 브랜치나 PR 로 조회하면 옛 커밋의 초록불을
# 지금 코드의 것으로 착각하게 된다 — 이 스크립트가 존재하는 이유가 바로 그것이다.
runs=$(gh api "repos/{owner}/{repo}/commits/$remote_sha/check-runs" \
        --jq '.check_runs[] | select(.name=="verify") | "\(.conclusion)"' 2>/dev/null)
rc=$?
if [ "$rc" -ne 0 ]; then
  echo "NOT_RUN: check-runs 조회 실패 (gh exit=$rc) — 모르는 것을 통과로 세지 않는다"
  exit 2
fi

if [ -z "$runs" ]; then
  conclusion="none"
  ci_sha="none"
else
  conclusion=$(printf '%s\n' "$runs" | head -1)
  ci_sha="$remote_sha"
fi

if [ -z "$(git status --porcelain)" ]; then
  worktree="clean"
else
  worktree="dirty"
fi

evaluate "$local_sha" "$remote_sha" "$ci_sha" "$conclusion" "$worktree"
