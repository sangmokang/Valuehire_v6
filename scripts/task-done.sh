#!/usr/bin/env bash
# task-done.sh — 워크트리를 폐기하기 전에 무시된 산출물을 회수시킨다 (harness 게이트 6).
#
# 계약: docs/engineering/task-done-ignored-artifact-gate-goal-2026-08-26.md (AC-1)
# 인수 검사: scripts/acceptance-task-done.sh
#
# 왜 필요한가 (2026-08-26 격리 저장소 3조건 실측):
#   추적 파일 수정  → git worktree remove 가 exit 128 로 거부한다.
#   untracked 새 파일 → 역시 exit 128 로 거부한다.
#   **무시된 파일만**  → exit 0, 메시지 0줄, 그대로 삭제된다.
#   이 저장소는 적대검증 판정서(private-reviews/·.omx/artifacts/)와 데이터(data/)를
#   의도적으로 무시 처리해 둔다(P12·P21). 그래서 git 의 기본 안전검사와 저장소 정책이
#   정면으로 어긋나 있고, 그 틈으로 회수 대상이 경고 없이 사라진다.
#
# 3상태 fail-closed. **종료값 0 일 때만 워크트리를 지운다.**
#   REFUSED(2) 판정 불능 — 인자 위반·미등록 대상·git 실패. 모르는 것은 통과가 아니다(P3).
#   BLOCK  (1) P12·P21 이 명시한 회수 대상이 남아 있다.
#   REVIEW (2) 캐시도 재생성 대상도 아닌 미분류가 남아 있다. 사람이 보고 정리해야 한다.
#   OK     (0) 최소 캐시·재생성 대상만 남았다 → 삭제한다.
#
# REVIEW 가 왜 exit 0 이 아닌가: 출력만 하고 통과시키면 "소리 내는 fail-open" 일 뿐이고,
# 모르는 상태를 합격으로 세는 것이라 P3 위반이다. 막고 나서 사람이 판단한다.
set -uo pipefail

state_out() { printf 'STATE: %s\n' "$1"; }

refuse() {
  state_out REFUSED
  printf 'REASON: %s\n' "$1"
  exit 2
}

NAME="${1:-}"

# ── 인자 검증: 전부 삭제 금지 방향으로 거부한다 ──────────────────────────────
[ -n "$NAME" ] || refuse "NAME 이 비었다 — 사용법: make task-done NAME=<worktree-name>"
case "$NAME" in
  -*)     refuse "NAME 이 '-' 로 시작한다 — 옵션으로 해석될 수 있다: $NAME" ;;
  */*)    refuse "NAME 에 '/' 가 있다 — worktrees/ 아래 이름 하나만 받는다: $NAME" ;;
  .|..)   refuse "NAME 이 '$NAME' 이다" ;;
  *..*)   refuse "NAME 에 '..' 가 있다 — 상위 경로 이동은 허용하지 않는다: $NAME" ;;
esac

REPO=$(git rev-parse --show-toplevel) || refuse "git 저장소가 아니다"
WT="$REPO/worktrees/$NAME"

[ ! -L "$WT" ] || refuse "$WT 가 심볼릭 링크다 — 링크 대상까지 지울 위험이 있다"
[ -d "$WT" ]   || refuse "$WT 가 없다"

# 등록된 워크트리인가. 일반 디렉터리를 지우지 않기 위해 반드시 확인한다.
# 경로 비교는 pwd -P 로 심볼릭 링크를 푼 뒤에 한다(macOS 의 /tmp → /private/tmp 때문).
wt_real=$(cd "$WT" && pwd -P) || refuse "$WT 로 이동할 수 없다"
registered=0
while IFS= read -r line; do
  case "$line" in
    "worktree "*)
      p=${line#worktree }
      if [ -d "$p" ]; then
        p_real=$(cd "$p" && pwd -P) || continue
      else
        p_real=$p
      fi
      if [ "$p_real" = "$wt_real" ]; then registered=1; fi
      ;;
  esac
done < <(git worktree list --porcelain)
[ "$registered" -eq 1 ] || refuse "$WT 는 등록된 워크트리가 아니다 (git worktree list 에 없다)"

# ── 분류 패턴 ────────────────────────────────────────────────────────────────
#
# 제외(EXCLUDE)는 최소로 둔다. 넓히면 검사가 그만큼 무력해진다.
#   · .ruff_cache/ .mypy_cache/ .pytest_cache/ __pycache__/ .hypothesis/ *.pyc
#     → 순수 캐시. 도구를 다시 돌리면 동일하게 재생성된다.
#       (.gitignore 의 "G2 게이트가 humansearch/ 에서 만드는 로컬 산출물" 주석 참조)
#   · .venv/ node_modules/
#     → 캐시는 아니지만 humansearch/uv.lock · pyproject.toml 로 결정적 복원이 된다.
#       이것까지 잡으면 정상 워크트리가 상시 폐기 불가가 되어 사람이 우회를 습관화한다.
#
# 이 둘 외에는 아무것도 제외하지 않는다. dist/ build/ .next/ 와 도구 상태(.omc/ .omx/state/)
# 는 REVIEW 로 보낸다 — "캐시라고 부를 수 없는 것"을 캐시 목록에 넣는 방향으로는 넓히지 않는다.
EXCLUDE='(^|/)(\.ruff_cache|\.mypy_cache|\.pytest_cache|__pycache__|\.hypothesis|\.venv|node_modules)/|\.pyc$'

# 회수 대상(RECOVER)은 손으로 늘리는 목록이 아니라 SOT 에서 유도한다.
#   private-reviews/ · artifacts/ · .harness/  → P12 (docs/sot/coding-principles.md)
#   data/                                      → P21 (같은 문서)
# `(^|/)artifacts/` 이므로 .omx/artifacts/ 도 걸린다(2026-08-26 실측: 그 안에 Codex·Claude
# 감사 판정서 15건이 실제로 들어 있었다. 도구 디렉터리라고 통째로 넘기면 안 되는 이유다).
RECOVER='(^|/)(private-reviews|artifacts|\.harness|data)/'

# ── 무시된 파일 열거 ─────────────────────────────────────────────────────────
#
# git status --ignored 는 디렉터리를 `!! dir/` 로 접어 개별 파일을 감춘다. ls-files 를 쓴다.
# -z 로 공백·개행이 든 파일명까지 안전하게 받는다.
# 실패를 빈 목록으로 강등하지 않는다 — 그게 fail-open 이 완성되는 지점이다.
#
# 결과를 명령 치환($(...))으로 받지 않는다. bash 는 명령 치환에서 NUL 바이트를 버리므로
# -z 로 구분한 파일명이 한 덩어리로 뭉쳐 분류가 통째로 깨진다. 임시 파일을 경유한다.
SCRATCH=$(mktemp) || refuse "임시 파일을 만들지 못했다 — 목록을 모을 수 없다"
trap 'rm -f "$SCRATCH"' EXIT

enumerate() {
  git -C "$WT" ls-files --others --ignored --exclude-standard -z -- . > "$SCRATCH"
}

classify() {
  n_block=0; n_review=0
  block_list=""; review_list=""
  local f
  while IFS= read -r -d '' f; do
    if printf '%s' "$f" | grep -qE "$EXCLUDE"; then
      continue
    fi
    if printf '%s' "$f" | grep -qE "$RECOVER"; then
      n_block=$((n_block + 1))
      block_list="${block_list}${f}"$'\n'
    else
      n_review=$((n_review + 1))
      review_list="${review_list}${f}"$'\n'
    fi
  done
}

enumerate || refuse "git ls-files 가 실패했다 — 무엇이 남았는지 모르는 채로 지우지 않는다"
classify < "$SCRATCH"

# 최대 5줄까지만 보인다. 한 워크트리에 무시 파일이 2,528개인 사례가 실재한다(2026-08-26 실측).
show() {
  local title="$1" count="$2" body="$3"
  printf '%s: %s\n' "$title" "$count"
  if [ "$count" -gt 0 ]; then
    printf '%s' "$body" | grep -v '^$' | head -5 | sed 's/^/    /'
    if [ "$count" -gt 5 ]; then printf '    ... 외 %s개\n' "$((count - 5))"; fi
  fi
}

if [ "$n_block" -gt 0 ]; then
  state_out BLOCK
  show BLOCKERS "$n_block" "$block_list"
  show REVIEW   "$n_review" "$review_list"
  printf 'HINT: 위 경로를 회수한 뒤 다시 실행하십시오 (P12 · P21).\n'
  exit 1
fi

if [ "$n_review" -gt 0 ]; then
  state_out REVIEW
  printf 'BLOCKERS: 0\n'
  show REVIEW "$n_review" "$review_list"
  printf 'HINT: 캐시도 회수 대상도 아닌 파일입니다. 확인 후 직접 지우고 다시 실행하십시오.\n'
  exit 2
fi

# ── OK: 삭제 직전 재검사 후 폐기 ────────────────────────────────────────────
# 판정과 삭제 사이에 다른 세션이 파일을 만들 수 있다. 창을 좁힐 뿐 없애지는 못한다.
enumerate || refuse "삭제 직전 재검사에서 git ls-files 가 실패했다"
classify < "$SCRATCH"
if [ "$n_block" -gt 0 ] || [ "$n_review" -gt 0 ]; then
  state_out REFUSED
  printf 'REASON: 판정 직후 새 파일이 생겼다 (BLOCK=%s REVIEW=%s) — 다시 실행하십시오\n' \
    "$n_block" "$n_review"
  exit 2
fi

if ! remove_out=$(git worktree remove "$WT" 2>&1); then
  state_out REFUSED
  printf 'REASON: git worktree remove 가 거부했다 — %s\n' "$remove_out"
  exit 2
fi

state_out OK
printf 'REMOVED: worktrees/%s\n' "$NAME"
exit 0
