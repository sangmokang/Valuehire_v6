#!/usr/bin/env bash
# pr-review/run.sh — 열린 PR 을 한 건씩 새 Codex 프로세스로 전수 리뷰하고, 실제 문제는 그 PR 브랜치에서 고친다 (#133)
#
# 실행  : launchd 가 매시간(scripts/pr-review/install.sh). 수동은 bash scripts/pr-review/run.sh
# 문맥  : PR 한 건 = codex exec 새 프로세스 1개. 앞 PR 의 대화가 다음 PR 로 넘어가지 않는다(매번 clear).
# 상태  : $PR_REVIEW_STATE(기본 ~/.valuehire-pr-review) — 저장소 밖. ledger.jsonl · runs/ · repo/(전용 clone)
# 장부  : REVIEWED  그 SHA 는 다시 보지 않는다
#         FAILED    다음 회차에 재시도. 같은 SHA 3회면 GAVE_UP(사람 확인)
#         HOLD_PII  판정문에 개인정보 패턴 — 공개 저장소라 게시하지 않는다(사람 확인)
# 권한  : Codex 는 workspace-write 샌드박스라 push·댓글을 못 한다. 둘 다 이 스크립트가 한다.
#         push 는 fast-forward 만 한다. 그사이 누가 브랜치를 밀었으면 실패로 남기고 덮어쓰지 않는다.
# 한도  : 회차당 PR_REVIEW_MAX_PER_RUN(기본 3)건. Codex 사용량 한도 오류가 나면 그 회차를 멈춘다.
set -uo pipefail

STATE=${PR_REVIEW_STATE:-$HOME/.valuehire-pr-review}
REPO=${PR_REVIEW_REPO:-sangmokang/Valuehire_v6}
REMOTE=${PR_REVIEW_REMOTE:-https://github.com/$REPO.git}
MAX=${PR_REVIEW_MAX_PER_RUN:-3}
HERE=$(cd "$(dirname "$0")" && pwd)
CLONE=$STATE/repo
LEDGER=$STATE/ledger.jsonl

log()    { printf '%s %s\n' "$(date '+%F %T')" "$*"; }
ledger() { printf '{"pr":%s,"sha":"%s","status":"%s","ts":"%s","note":"%s"}\n' \
             "$1" "$2" "$3" "$(date '+%FT%T%z')" "${4:-}" >> "$LEDGER"; }
seen()   { grep -qF "\"pr\":$1,\"sha\":\"$2\",\"status\":\"$3\"" "$LEDGER"; }

mkdir -p "$STATE/runs" && touch "$LEDGER" || { log "FAIL: 상태 디렉터리 $STATE"; exit 2; }

# ── 잠금: 살아 있는 실행이 있으면 건너뛴다. 주인이 죽었으면(재부팅·강제종료) 넘겨받는다 ──
if ! mkdir "$STATE/lock" 2>/dev/null; then
  owner=""; [ -f "$STATE/lock/pid" ] && owner=$(cat "$STATE/lock/pid")
  if [ -n "$owner" ] && kill -0 "$owner" 2>/dev/null; then
    log "SKIP: 이전 실행(pid $owner)이 아직 돈다"; exit 0
  fi
  log "죽은 잠금(pid ${owner:-없음})을 넘겨받는다"
fi
echo $$ > "$STATE/lock/pid"
trap 'rm -rf "$STATE/lock"' EXIT

# ── 전용 clone: 사람이 쓰는 작업트리·워크트리와 섞이지 않게 한다 ──────────────
if [ ! -d "$CLONE/.git" ]; then
  git clone -q "$REMOTE" "$CLONE" || { log "FAIL: clone $REMOTE"; exit 2; }
fi
git -C "$CLONE" fetch -q --prune origin || { log "FAIL: fetch"; exit 2; }

# review_one <번호> <브랜치> <SHA>  →  0 처리 끝 / 1 실패(재시도) / 3 사용량 한도(회차 중단)
review_one() {
  local n=$1 branch=$2 sha=$3 out rc new pushed="" note=""
  out=$STATE/runs/pr-$n-$(date +%Y%m%d-%H%M%S)
  mkdir -p "$out"

  git -C "$CLONE" fetch -q origin "$branch" &&
    git -C "$CLONE" checkout -q -f -B "review/pr-$n" "$sha" &&
    git -C "$CLONE" clean -qfdx ||
    { ledger "$n" "$sha" FAILED "체크아웃 실패"; return 1; }
  if [ -f "$CLONE/scripts/install-hooks.sh" ]; then
    (cd "$CLONE" && bash scripts/install-hooks.sh) > "$out/hooks.log" 2>&1
  fi

  # Codex 샌드박스는 네트워크가 막혀 있다. PR 자료는 여기서 미리 받아 둔다.
  gh pr view "$n" --repo "$REPO" --json title,body,closingIssuesReferences,labels > "$out/pr.json" &&
    gh pr diff "$n" --repo "$REPO" > "$out/pr.diff" ||
    { ledger "$n" "$sha" FAILED "PR 자료 조회 실패"; return 1; }
  gh pr checks "$n" --repo "$REPO" > "$out/checks.txt" 2>&1   # 대기·실패 중이어도 자료로만 쓴다

  sed -e "s|{{N}}|$n|g" -e "s|{{OUT}}|$out|g" -e "s|{{BRANCH}}|$branch|g" "$HERE/prompt.md" > "$out/prompt.md"
  mkdir -p "$CLONE/.git/review-tmp"   # 샌드박스 안에서 쓸 수 있고 작업트리를 더럽히지 않는 임시 경로
  TMPDIR="$CLONE/.git/review-tmp" codex exec -C "$CLONE" -s workspace-write --skip-git-repo-check \
    -o "$out/verdict.md" "$(cat "$out/prompt.md")" < /dev/null > "$out/codex.log" 2>&1
  rc=$?
  if [ "$rc" -ne 0 ] || ! grep -q '^판정:' "$out/verdict.md"; then
    if grep -qiE 'usage limit|rate limit' "$out/codex.log"; then
      ledger "$n" "$sha" FAILED "codex 사용량 한도"; return 3
    fi
    ledger "$n" "$sha" FAILED "codex rc=$rc 또는 판정 줄 없음"; return 1
  fi

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
    printf '\n_자동 리뷰(매시간 · Codex · PR 한 건마다 새 세션 · 같은 SHA 는 다시 보지 않음)_\n'
  } > "$out/comment.md"
  gh pr comment "$n" --repo "$REPO" --body-file "$out/comment.md" > "$out/comment.log" 2>&1 ||
    { ledger "$n" "$sha" FAILED "댓글 게시 실패"; return 1; }

  ledger "$n" "$sha" REVIEWED
  [ -n "$pushed" ] && ledger "$n" "$pushed" REVIEWED "자동 수정 커밋"
  log "PR #$n 리뷰 완료${pushed:+ · 수정 push $pushed}"
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
  [ "$count" -ge "$MAX" ] && { log "회차 상한 $MAX건 — 나머지는 다음 회차"; break; }
  count=$((count + 1))
  log "PR #$n ($branch @ ${sha:0:7}) 리뷰 시작"
  review_one "$n" "$branch" "$sha" < /dev/null
  rc=$?
  [ "$rc" -eq 3 ] && { log "STOP: Codex 사용량 한도 — 이번 회차 중단"; break; }
done < <(printf '%s' "$prs" | jq -r 'sort_by(.number)[] | [.number, .headRefName, .headRefOid] | @tsv')

log "회차 종료: 리뷰 시도 ${count}건"
exit 0
