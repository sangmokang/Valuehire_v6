#!/usr/bin/env bash
# pr-review/run.sh — 열린 PR 을 한 건씩 Claude·Codex 가 herdr 옆 창에서 함께 전수 리뷰하고, 실제 문제는 고친다 (#133)
#
# 실행  : herdr 창 안에서만(HERDR_ENV=1). 주기 실행은 scripts/pr-review/loop.sh, 착수는 start.sh.
# 흐름  : PR 한 건마다 herdr 새 탭 → 왼쪽 Claude(읽기 전용, 결과 파일만 씀) → 오른쪽 Codex(Claude 발견을
#         재현·판정하고 확인된 문제를 고쳐 커밋) → 탭 닫기. 에이전트를 PR 마다 새로 띄우므로 문맥이 매번
#         비어 있다(= clear). 이전 PR 의 대화가 다음 PR 로 넘어가지 않는다.
# 상태  : $PR_REVIEW_STATE(기본 ~/.valuehire-pr-review) — 저장소 밖. ledger.jsonl · runs/ · repo/(전용 clone)
# 장부  : REVIEWED  그 SHA 는 다시 보지 않는다
#         FAILED    다음 회차에 재시도. 같은 SHA 3회면 GAVE_UP(사람 확인)
#         HOLD_PII  판정문에 개인정보 패턴 — 공개 저장소라 게시하지 않는다(사람 확인)
# 권한  : Claude 는 dontAsk + 읽기·git 조회·결과 폴더 쓰기만. Codex 는 workspace-write 샌드박스 + 결과 폴더.
#         push·댓글은 이 스크립트만 한다. push 는 fast-forward 만 — 그사이 브랜치가 바뀌었으면 덮어쓰지 않는다.
# 한도  : 회차당 PR_REVIEW_MAX_PER_RUN(기본 3)건. 사용량 한도 문구가 보이면 그 회차를 멈춘다.
set -uo pipefail

STATE=${PR_REVIEW_STATE:-$HOME/.valuehire-pr-review}
REPO=${PR_REVIEW_REPO:-sangmokang/Valuehire_v6}
REMOTE=${PR_REVIEW_REMOTE:-https://github.com/$REPO.git}
MAX=${PR_REVIEW_MAX_PER_RUN:-3}
WAIT_MS=${PR_REVIEW_AGENT_TIMEOUT_MS:-3600000}
HERE=$(cd "$(dirname "$0")" && pwd)
CLONE=$STATE/repo
LEDGER=$STATE/ledger.jsonl

log()    { printf '%s %s\n' "$(date '+%F %T')" "$*"; }
ledger() { printf '{"pr":%s,"sha":"%s","status":"%s","ts":"%s","note":"%s"}\n' \
             "$1" "$2" "$3" "$(date '+%FT%T%z')" "${4:-}" >> "$LEDGER"; }
seen()   { grep -qF "\"pr\":$1,\"sha\":\"$2\",\"status\":\"$3\"" "$LEDGER"; }

if [ "${HERDR_ENV:-}" != 1 ] || [ -z "${HERDR_WORKSPACE_ID:-}" ]; then
  log "FAIL: herdr 창 안에서 실행해야 한다(HERDR_ENV=1). scripts/pr-review/start.sh 로 착수하라"; exit 2
fi
mkdir -p "$STATE/runs" && touch "$LEDGER" || { log "FAIL: 상태 디렉터리 ${STATE}"; exit 2; }

# ── 잠금: 살아 있는 실행이 있으면 건너뛴다. 주인이 죽었으면(재부팅·강제종료) 넘겨받는다 ──
if ! mkdir "$STATE/lock" 2>/dev/null; then
  owner=""; [ -f "$STATE/lock/pid" ] && owner=$(cat "$STATE/lock/pid")
  if [ -n "$owner" ] && kill -0 "$owner" 2>/dev/null; then
    log "SKIP: 이전 실행(pid ${owner})이 아직 돈다"; exit 0
  fi
  log "죽은 잠금(pid ${owner:-없음})을 넘겨받는다"
fi
echo $$ > "$STATE/lock/pid"
trap 'rm -rf "$STATE/lock"' EXIT

# ── 전용 clone: 사람이 쓰는 작업트리·워크트리와 섞이지 않게 한다 ──────────────
if [ ! -d "$CLONE/.git" ]; then
  git clone -q "$REMOTE" "$CLONE" || { log "FAIL: clone ${REMOTE}"; exit 2; }
fi
git -C "$CLONE" fetch -q --prune origin || { log "FAIL: fetch"; exit 2; }

# start_agent <이름> <종류> <창> [에이전트 인자...] — 시작 확인 창 하나는 넘긴다
#   Claude 폴더 신뢰 확인: 전용 clone(우리 저장소)이므로 '신뢰'를 고른다
#   Codex 훅 신뢰 확인   : 훅을 신뢰하지 않고 닫는다(esc)
start_agent() {
  local name=$1 kind=$2 pane=$3 res i; shift 3
  # 새 창은 셸이 뜨기 전·앞 명령(unset)이 끝나기 전에는 agent_pane_busy 로 거절된다(2026-10-13 실측)
  for i in $(seq 1 60); do
    res=$(herdr agent start "$name" --kind "$kind" --pane "$pane" --timeout 60000 -- "$@")
    printf '%s' "$res" | grep -q '"agent_pane_busy"' || break
    sleep 1
  done
  printf '%s' "$res" | jq -e '.result.agent' >/dev/null && return 0
  if herdr agent read "$name" --source visible | grep -q 'trust this folder'; then
    herdr agent send-keys "$name" down > /dev/null; herdr agent send-keys "$name" enter > /dev/null
  else
    herdr agent send-keys "$name" esc > /dev/null
  fi
  herdr agent wait "$name" --until idle --timeout 30000 | jq -e '.result.agent' >/dev/null
}

# ask <이름> <지시 파일> — 지시 파일을 읽고 따르게 한 뒤 끝날 때까지 기다린다. 0 끝남 / 1 실패 / 3 사용량 한도·수용량 초과
#   (2026-10-13 실측: Codex 가 'Selected model is at capacity' 로 아무것도 안 하고 끝났다 — 같은 회차의 다음 PR 도 같으므로 멈춘다)
ask() {
  local name=$1 file=$2 st
  st=$(herdr agent prompt "$name" "Read $file and follow it exactly. 끝나면 지시 파일이 말한 결과 파일만 남기고 멈춰라." \
         --wait --timeout "$WAIT_MS" | jq -r '.result.agent.agent_status // .error.code')
  if herdr agent read "$name" --source recent-unwrapped --lines 80 | grep -qiE 'usage limit|rate limit|limit reached|at capacity'; then
    return 3
  fi
  case "$st" in idle|done) return 0 ;; *) return 1 ;; esac
}

# review_one <번호> <브랜치> <SHA>  →  0 처리 끝 / 1 실패(재시도) / 3 사용량 한도(회차 중단)
review_one() {
  local n=$1 branch=$2 sha=$3 out tab pc px rc new pushed="" note=""
  out=$STATE/runs/pr-$n-$(date +%Y%m%d-%H%M%S)
  mkdir -p "$out"

  git -C "$CLONE" fetch -q origin "$branch" &&
    git -C "$CLONE" checkout -q -f -B "review/pr-$n" "$sha" &&
    git -C "$CLONE" clean -qfdx ||
    { ledger "$n" "$sha" FAILED "체크아웃 실패"; return 1; }
  if [ -f "$CLONE/scripts/install-hooks.sh" ]; then
    (cd "$CLONE" && bash scripts/install-hooks.sh) > "$out/hooks.log" 2>&1
  fi

  gh pr view "$n" --repo "$REPO" --json title,body,closingIssuesReferences,labels > "$out/pr.json" &&
    gh pr diff "$n" --repo "$REPO" > "$out/pr.diff" ||
    { ledger "$n" "$sha" FAILED "PR 자료 조회 실패"; return 1; }
  gh pr checks "$n" --repo "$REPO" > "$out/checks.txt" 2>&1   # 대기·실패 중이어도 자료로만 쓴다

  for p in claude codex; do
    sed -e "s|{{N}}|$n|g" -e "s|{{OUT}}|$out|g" -e "s|{{BRANCH}}|$branch|g" "$HERE/prompt-$p.md" > "$out/prompt-$p.md"
  done

  # PR 하나 = herdr 새 탭 하나. 왼쪽 Claude, 오른쪽 Codex. 끝나면 탭째 닫아 두 에이전트를 함께 끝낸다.
  tab=$(herdr tab create --workspace "$HERDR_WORKSPACE_ID" --cwd "$CLONE" --label "pr-$n" --no-focus) ||
    { ledger "$n" "$sha" FAILED "herdr 탭 생성 실패"; return 1; }
  pc=$(printf '%s' "$tab" | jq -r '.result.root_pane.pane_id'); tab=$(printf '%s' "$tab" | jq -r '.result.tab.tab_id')
  mkdir -p "$CLONE/.git/review-tmp"   # Codex 샌드박스 안에서 쓸 수 있고 작업트리를 더럽히지 않는 임시 경로
  px=$(herdr pane split "$pc" --direction right --cwd "$CLONE" --env "TMPDIR=$CLONE/.git/review-tmp" --no-focus |
         jq -r '.result.pane.pane_id')
  herdr pane run "$pc" "unset ANTHROPIC_API_KEY" > /dev/null   # API 키가 로그인보다 우선해 잔액 부족으로 죽는다

  rc=0
  if ! start_agent "rvc-$n" claude "$pc" --permission-mode dontAsk --allowedTools Read Grep Glob \
         "Bash(git diff:*)" "Bash(git log:*)" "Bash(git show:*)" "Edit(/$out/**)"; then
    rc=1; note="Claude 시작 실패"
  else
    ask "rvc-$n" "$out/prompt-claude.md"; rc=$?
    [ "$rc" -eq 0 ] && [ ! -s "$out/claude.md" ] && { rc=1; note="Claude 리뷰 파일 없음"; }
  fi
  if [ "$rc" -eq 0 ]; then
    if ! start_agent "rvx-$n" codex "$px" -s workspace-write -a never --add-dir "$out"; then
      rc=1; note="Codex 시작 실패"
    else
      ask "rvx-$n" "$out/prompt-codex.md"; rc=$?
      [ "$rc" -eq 0 ] && ! grep -q '^판정:' "$out/verdict.md" && { rc=1; note="판정 줄 없음"; }
    fi
  fi
  herdr pane read "$pc" --source recent-unwrapped --lines 400 > "$out/claude-pane.log"
  herdr pane read "$px" --source recent-unwrapped --lines 400 > "$out/codex-pane.log"
  herdr tab close "$tab" > /dev/null
  if [ "$rc" -eq 3 ]; then ledger "$n" "$sha" FAILED "사용량 한도"; return 3; fi
  if [ "$rc" -ne 0 ]; then ledger "$n" "$sha" FAILED "${note:-에이전트 실패}"; return 1; fi
  note=""

  new=$(git -C "$CLONE" rev-parse HEAD)
  if [ "$new" != "$sha" ]; then
    if git -C "$CLONE" merge-base --is-ancestor "$sha" "$new" &&
       git -C "$CLONE" push -q origin "HEAD:refs/heads/$branch" > "$out/push.log" 2>&1; then
      pushed=$new
    else
      note="수정 커밋을 push 하지 못했다(브랜치가 그사이 바뀌었거나 pre-push 차단). 수정은 반영되지 않았다."
    fi
  fi

  # 공개 저장소다. 이메일·전화번호·프로필 URL 이 판정문에 있으면 게시하지 않는다.
  if grep -qE '[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}|01[016789][- ]?[0-9]{3,4}[- ]?[0-9]{4}|linkedin\.com/in/' "$out/verdict.md"; then
    ledger "$n" "$sha" HOLD_PII "판정문 개인정보 패턴"
    [ -n "$pushed" ] && ledger "$n" "$pushed" HOLD_PII "자동 수정 커밋"
    return 0
  fi

  {
    echo "<!-- pr-review:auto sha=$sha -->"
    cat "$out/verdict.md"
    [ -n "$note" ] && printf '\n> %s\n' "$note"
    printf '\n_자동 리뷰(매시간 · Claude 읽기 리뷰 → Codex 대조·수정 · PR 마다 새 세션 · 같은 SHA 는 다시 보지 않음)_\n'
  } > "$out/comment.md"
  gh pr comment "$n" --repo "$REPO" --body-file "$out/comment.md" > "$out/comment.log" 2>&1 ||
    { ledger "$n" "$sha" FAILED "댓글 게시 실패"; return 1; }

  ledger "$n" "$sha" REVIEWED
  [ -n "$pushed" ] && ledger "$n" "$pushed" REVIEWED "자동 수정 커밋"
  log "PR #${n} 리뷰 완료${pushed:+ · 수정 push ${pushed}}"
  return 0
}

prs=$(gh pr list --repo "$REPO" --state open --limit 200 --json number,headRefName,headRefOid,title) ||
  { log "FAIL: PR 목록 조회"; exit 2; }

count=0
while IFS=$'\t' read -r n branch sha; do
  [ -n "$n" ] || continue
  seen "$n" "$sha" REVIEWED && continue
  seen "$n" "$sha" HOLD_PII && continue
  seen "$n" "$sha" GAVE_UP && continue
  if [ "$(grep -cF "\"pr\":$n,\"sha\":\"$sha\",\"status\":\"FAILED\"" "$LEDGER")" -ge 3 ]; then
    ledger "$n" "$sha" GAVE_UP "같은 SHA 3회 실패"; continue
  fi
  [ "$count" -ge "$MAX" ] && { log "회차 상한 ${MAX}건 — 나머지는 다음 회차"; break; }
  count=$((count + 1))
  log "PR #${n} (${branch} @ ${sha:0:7}) 리뷰 시작"
  review_one "$n" "$branch" "$sha" < /dev/null
  rc=$?
  [ "$rc" -eq 3 ] && { log "STOP: 사용량 한도 — 이번 회차 중단"; break; }
done < <(printf '%s' "$prs" | jq -r 'sort_by(.number)[] | [.number, .headRefName, .headRefOid] | @tsv')

log "회차 종료: 리뷰 시도 ${count}건"
exit 0
