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
#   그 SHA 에 대한 모든 verify 실행이 completed/success
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

evaluate_runs() {
  local local_sha="$1" remote_sha="$2" worktree="$3"
  shift 3
  local record status conclusion aggregate="success"

  printf 'CI_RUN_COUNT: %d\n' "$#"
  if [ "$#" -eq 0 ]; then
    evaluate "$local_sha" "$remote_sha" none none "$worktree"
    return $?
  fi

  for record in "$@"; do
    case "$record" in
      *:*:*)
        echo "NOT_RUN: check-run 레코드 구분자 초과 — $record"
        exit 2
        ;;
      *:*) ;;
      *)
        echo "NOT_RUN: check-run 레코드 형식 오류 — $record"
        exit 2
        ;;
    esac
    status=${record%%:*}
    conclusion=${record#*:}
    if [ -z "$status" ] || [ -z "$conclusion" ]; then
      echo "NOT_RUN: check-run 레코드 값 누락 — $record"
      exit 2
    fi
    case "$status" in
      completed|queued|in_progress|waiting|requested|pending) ;;
      *)
        echo "NOT_RUN: 알 수 없는 check-run 상태 — $status"
        exit 2
        ;;
    esac
  done

  # 모든 레코드의 구조를 먼저 검증한다. 집계 중 일찍 멈추면 뒤쪽의 오형식이나
  # 알 수 없는 상태를 UNVERIFIED 로 낮춰 조회 자체가 깨진 사실을 숨기게 된다.
  for record in "$@"; do
    status=${record%%:*}
    conclusion=${record#*:}
    if [ "$status" != "completed" ]; then
      aggregate="pending"
      break
    fi
    if [ "$conclusion" != "success" ]; then
      aggregate="$conclusion"
      break
    fi
  done

  evaluate "$local_sha" "$remote_sha" "$remote_sha" "$aggregate" "$worktree"
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

if [ "${1:-}" = "--evaluate-runs" ]; then
  shift
  if [ "$#" -lt 3 ]; then
    echo "FAIL: --evaluate-runs 는 최소 인자 3개가 필요하다 (local remote worktree [status:conclusion...])"
    exit 2
  fi
  local_sha="$1"
  remote_sha="$2"
  worktree="$3"
  shift 3
  evaluate_runs "$local_sha" "$remote_sha" "$worktree" "$@"
  exit $?
fi

# ── 실제 조회부 ──────────────────────────────────────────────────────────────
if [ "$#" -gt 0 ]; then
  branch="$1"
else
  branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)
  branch_rc=$?
  if [ "$branch_rc" -ne 0 ]; then
    echo "NOT_RUN: 현재 브랜치 조회 실패 (git rev-parse exit=$branch_rc) — 부분 출력을 증거로 쓰지 않는다"
    exit 2
  fi
fi
if [ -z "$branch" ] || [ "$branch" = "HEAD" ]; then
  echo "NOT_RUN: 브랜치를 확정하지 못했다 (detached HEAD?)"
  exit 2
fi

local_sha=$(git rev-parse HEAD 2>/dev/null)
local_sha_rc=$?
if [ "$local_sha_rc" -ne 0 ]; then
  echo "NOT_RUN: 로컬 HEAD 조회 실패 (git rev-parse exit=$local_sha_rc) — 부분 출력을 증거로 쓰지 않는다"
  exit 2
fi
if [ -z "$local_sha" ]; then
  echo "NOT_RUN: 로컬 HEAD 를 읽지 못했다"
  exit 2
fi

remote_sha=$(git ls-remote origin "refs/heads/$branch" 2>/dev/null | awk '{print $1}' | head -1)
remote_sha_rc=$?
if [ "$remote_sha_rc" -ne 0 ]; then
  echo "NOT_RUN: 원격 HEAD 조회 실패 (git ls-remote exit=$remote_sha_rc) — 부분 출력을 증거로 쓰지 않는다"
  exit 2
fi
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
# GitHub REST 기본값은 최신 check run 만 돌려주므로 모든 실행 집계를 위해 filter=all 을 명시한다.
encoded_runs=$(
  gh api --paginate "repos/{owner}/{repo}/commits/$remote_sha/check-runs?filter=all" \
    --jq '.check_runs[] | select(.name=="verify") | "\(.status):\(.conclusion // "none")"' 2>/dev/null |
    awk '{ printf "R%s\n", $0 }'
  pipeline_status=("${PIPESTATUS[@]}")
  printf 'X%s:%s\n' "${pipeline_status[0]}" "${pipeline_status[1]}"
)

records=()
gh_rc=2
filter_rc=2
trailer_count=0
while IFS= read -r encoded; do
  case "$encoded" in
    R*) records+=("${encoded#R}") ;;
    X*:*)
      trailer_count=$((trailer_count + 1))
      gh_rc=${encoded#X}
      filter_rc=${gh_rc#*:}
      gh_rc=${gh_rc%%:*}
      case "$gh_rc:$filter_rc" in
        *[!0-9:]*|*:*:*) trailer_count=2 ;;
      esac
      ;;
    *) trailer_count=2 ;;
  esac
done <<< "$encoded_runs"

if [ "$trailer_count" -ne 1 ]; then
  echo "NOT_RUN: check-runs 내부 전달 형식 오류 — 모르는 것을 통과로 세지 않는다"
  exit 2
fi
if [ "$gh_rc" -ne 0 ] || [ "$filter_rc" -ne 0 ]; then
  echo "NOT_RUN: check-runs 조회 실패 (gh exit=$gh_rc, filter exit=$filter_rc) — 모르는 것을 통과로 세지 않는다"
  exit 2
fi

status_output=$(git status --porcelain 2>/dev/null)
status_rc=$?
if [ "$status_rc" -ne 0 ]; then
  echo "NOT_RUN: 작업트리 상태 조회 실패 (git status exit=$status_rc) — 모르는 것을 clean으로 세지 않는다"
  exit 2
fi
if [ -z "$status_output" ]; then
  worktree="clean"
else
  worktree="dirty"
fi

# Bash 3.2는 `set -u`에서 빈 배열의 "${records[@]}" 확장을 unbound variable로
# 종료한다. 조회 결과 0건도 정상적인 UNVERIFIED 입력이므로 빈 배열은 명시적으로 분기한다.
if [ "${#records[@]}" -eq 0 ]; then
  evaluate_runs "$local_sha" "$remote_sha" "$worktree"
else
  evaluate_runs "$local_sha" "$remote_sha" "$worktree" "${records[@]}"
fi
