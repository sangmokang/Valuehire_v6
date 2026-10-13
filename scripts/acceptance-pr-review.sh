#!/usr/bin/env bash
# acceptance-pr-review.sh — 열린 PR 자동 리뷰(scripts/pr-review/run.sh)가 약속대로 도는가 (#133)
#
# 가짜 gh·herdr 와 로컬 bare 원격으로 run.sh 를 실제 실행해 결과(호출 수·탭·댓글·원격 브랜치·장부)를 본다.
# 가짜 herdr 는 agent prompt 를 받으면 그 창의 에이전트(claude/codex) 역할을 흉내 낸다.
#   1. 새 SHA PR 만, PR 마다 herdr 새 탭에 Claude·Codex 를 새로 띄워(문맥 새로 시작) 1회씩 · 탭은 닫는다
#   2. Codex 지시문은 Claude 리뷰 파일을 가리킨다 · 댓글 1개 · 장부 REVIEWED
#   3. 수정 커밋은 PR 브랜치로 push 되고, 그 새 SHA 는 다시 리뷰하지 않는다 · 같은 SHA 는 건너뛴다
#   4. Claude 실패 → Codex 안 부름 · 댓글 없음 / Codex 실패 → 댓글 없음 · 다음 회차 재시도
#   5. 개인정보 패턴이 든 판정은 게시하지 않는다
#   6. 사용량 한도 → 그 회차 중단 / 1회 상한 / 실행 중 잠금 / herdr 밖 실행 거부
# 출력: PASS 한 줄 + CHECKED: <n> (run-acceptance.sh 계약) · 하나라도 어기면 exit 1
set -uo pipefail

ROOT=$(cd "$(dirname "$0")/.." && pwd)
RUN="$ROOT/scripts/pr-review/run.sh"
fail=0; checked=0
ok()  { checked=$((checked + 1)); echo "ok: $1"; }
bad() { checked=$((checked + 1)); echo "FAIL: $1"; fail=1; }
expect() { if [ "$2" = "$3" ]; then ok "$1 ($2)"; else bad "$1 — 기대 '$3' 실제 '$2'"; fi; }

[ -f "$RUN" ] || { echo "FAIL: $RUN 없음"; echo "CHECKED: 0"; exit 1; }

T=$(mktemp -d) || { echo "FAIL: 임시 디렉터리"; exit 1; }
trap 'rm -rf "$T"' EXIT
F=$T/fake; mkdir -p "$F/comments" "$F/h" "$T/bin"
export GIT_AUTHOR_NAME=t GIT_AUTHOR_EMAIL=t@local GIT_COMMITTER_NAME=t GIT_COMMITTER_EMAIL=t@local

# ── 원격: 브랜치 b1..b8 ───────────────────────────────────────────────────
git init -q --bare "$T/remote.git"
git init -q "$T/seed"; (
  cd "$T/seed" && echo base > base.txt && git add . && git commit -qm base
  for b in b1 b2 b3 b4 b5 b6 b7 b8; do
    git checkout -qb "$b" && echo "$b" > "$b.txt" && git add . && git commit -qm "$b" && git checkout -q -
  done
  git remote add origin "$T/remote.git" && git push -q origin --all
)
sha() { git --git-dir="$T/remote.git" rev-parse "refs/heads/$1"; }

# prs <번호:브랜치>... — 원격의 현재 SHA 로 PR 목록을 만든다
prs() {
  local out="[" sep="" n b
  for p in "$@"; do n=${p%%:*}; b=${p#*:}
    out="$out$sep{\"number\":$n,\"headRefName\":\"$b\",\"headRefOid\":\"$(sha "$b")\",\"title\":\"PR $n\"}"; sep=","
  done
  echo "$out]" > "$F/prs.json"
}

# ── 가짜 gh ───────────────────────────────────────────────────────────────
cat > "$T/bin/gh" <<'EOF'
#!/usr/bin/env bash
F=$FAKE
case "$1 $2" in
  "pr list")    cat "$F/prs.json" ;;
  "pr view")    echo '{"title":"t","body":"사업 목적 본문"}' ;;
  "pr diff")    echo "diff --git a/x b/x" ;;
  "pr checks")  echo "verify pass" ;;
  "pr comment") n=$3; shift 3
                while [ $# -gt 0 ]; do [ "$1" = --body-file ] && cp "$2" "$(mktemp "$F/comments/$n.XXXXXX")"; shift; done ;;
  *) echo "fake gh: unsupported $*" >&2; exit 1 ;;
esac
EOF
# ── 가짜 herdr: 탭·창·에이전트. agent prompt 에서 에이전트 역할을 흉내 낸다(mode.<kind>.<번호>) ──
cat > "$T/bin/herdr" <<'EOF'
#!/usr/bin/env bash
F=$FAKE; H=$F/h
newid() { local c; c=$(cat "$H/seq" 2>/dev/null); c=$((${c:-0} + 1)); echo "$c" > "$H/seq"; echo "$c"; }
opt() { local k=$1; shift; while [ $# -gt 0 ]; do [ "$1" = "$k" ] && { echo "$2"; return; }; shift; done; }
case "$1 $2" in
  "tab create")  i=$(newid); opt --cwd "$@" > "$H/pane.p$i.cwd"; echo open >> "$F/tabs.log"
                 echo "{\"result\":{\"tab\":{\"tab_id\":\"t$i\"},\"root_pane\":{\"pane_id\":\"p$i\"}}}" ;;
  "pane split")  i=$(newid); opt --cwd "$@" > "$H/pane.p$i.cwd"
                 echo "{\"result\":{\"pane\":{\"pane_id\":\"p$i\"}}}" ;;
  "pane run"|"pane read") : ;;
  "tab close")   echo close >> "$F/tabs.log"; echo '{"result":{"type":"ok"}}' ;;
  "agent start") name=$3; kind=$(opt --kind "$@"); pane=$(opt --pane "$@")
                 # 실제 herdr 실측(2026-10-13): 새 창의 셸이 준비되기 전에는 첫 시도가 거절된다
                 if [ ! -f "$H/ready.$pane" ]; then touch "$H/ready.$pane"
                   echo '{"error":{"code":"agent_pane_busy"}}'; exit 1; fi
                 echo "$kind $pane" > "$H/agent.$name"; echo "$kind $name" >> "$F/starts.log"
                 echo '{"result":{"agent":{"agent_status":"idle"}}}' ;;
  "agent prompt") name=$3; text=$4; read -r kind pane < "$H/agent.$name"; dir=$(cat "$H/pane.$pane.cwd")
                 file=${text#Read }; file=${file%% *}; out=$(dirname "$file")
                 n=$(sed -n 's/.*PR #\([0-9]*\).*/\1/p' "$file" | head -1)
                 echo "$n" >> "$F/$kind.calls"; cp "$file" "$F/last-$kind-prompt"
                 mode=ok; [ -f "$F/mode.$kind.$n" ] && mode=$(cat "$F/mode.$kind.$n")
                 case "$mode" in
                   fail)  ;;
                   usage) echo "ERROR: You've hit your usage limit." > "$H/usage.$name" ;;
                   capacity) echo "■ Selected model is at capacity. Please try a different model." > "$H/usage.$name" ;;
                   *) if [ "$kind" = claude ]; then
                        printf '## Claude 1차 리뷰 PR #%s\n- 발견: 없음\n' "$n" > "$out/claude.md"
                      else
                        [ "$mode" = fix ] && (cd "$dir" && echo fixed > fix.txt && git add fix.txt && git commit -qm fix)
                        if [ "$mode" = pii ]; then v="연락처 someone@example.com"; else v="발견 없음"; fi
                        printf '## 자동 리뷰 PR #%s\n- %s\n판정: 병합 가능\n' "$n" "$v" > "$out/verdict.md"
                      fi ;;
                 esac
                 echo '{"result":{"agent":{"agent_status":"done"}}}' ;;
  "agent read")  [ -f "$H/usage.$3" ] && cat "$H/usage.$3" ;;
  "agent send-keys"|"agent wait") echo '{"result":{"agent":{"agent_status":"idle"}}}' ;;
  *) echo "fake herdr: unsupported $*" >&2; exit 1 ;;
esac
exit 0
EOF
chmod +x "$T/bin/gh" "$T/bin/herdr"

export FAKE=$F PATH="$T/bin:$PATH" PR_REVIEW_STATE=$T/state PR_REVIEW_REMOTE=$T/remote.git PR_REVIEW_REPO=fake/repo
export HERDR_ENV=1 HERDR_WORKSPACE_ID=w9
cnt()      { if [ -f "$1" ]; then wc -l < "$1" | tr -d ' '; else echo 0; fi; }
calls()    { cnt "$F/${1:-codex}.calls"; }
comments() { ls "$F/comments" | grep -c "^$1\." ; }
led()      { grep -c "\"pr\":$1,\"sha\":\"$2\",\"status\":\"$3\"" "$T/state/ledger.jsonl" 2>/dev/null; }
run()      { PR_REVIEW_MAX_PER_RUN=${MAX:-3} bash "$RUN" > "$T/run.out" 2>&1; echo $?; }

# 0. herdr 밖에서는 거부
expect "herdr 밖 실행은 거부(exit 2)" "$(HERDR_ENV= bash "$RUN" > /dev/null 2>&1; echo $?)" 2

# 1·2·3. 새 PR 2건: #1 그대로, #2 수정 커밋
echo fix > "$F/mode.codex.2"; A1=$(sha b1); B2=$(sha b2)
prs 1:b1 2:b2
expect "1회차 종료값" "$(run)" 0
expect "PR 당 Claude 1회" "$(calls claude)" 2
expect "PR 당 Codex 1회" "$(calls codex)" 2
expect "PR 마다 에이전트를 새로 띄움(2 PR × 2)" "$(cnt "$F/starts.log")" 4
expect "에이전트 이름이 PR 마다 다름" "$(cut -d' ' -f2 "$F/starts.log" | sort -u | wc -l | tr -d ' ')" 4
expect "열린 탭은 전부 닫힘" "$(grep -c close "$F/tabs.log")" "$(grep -c open "$F/tabs.log")"
if grep -q 'claude.md' "$F/last-codex-prompt"; then ok "Codex 지시문이 Claude 리뷰 파일을 가리킴"
else bad "Codex 지시문에 Claude 리뷰 파일이 없다"; fi
expect "#1 댓글 1개" "$(comments 1)" 1
expect "#2 댓글 1개" "$(comments 2)" 1
expect "#1 장부 REVIEWED" "$(led 1 "$A1" REVIEWED)" 1
NB2=$(sha b2)
if [ "$NB2" != "$B2" ] && git --git-dir="$T/remote.git" cat-file -e "$NB2:fix.txt" 2>/dev/null; then
  ok "#2 수정 커밋이 PR 브랜치로 push 됨"; else bad "#2 수정 커밋이 원격 b2 에 없다"; fi
expect "#2 수정 후 SHA 도 장부 REVIEWED" "$(led 2 "$NB2" REVIEWED)" 1

prs 1:b1 2:b2
run >/dev/null
expect "같은 SHA 는 건너뜀(Codex 호출 수 불변)" "$(calls)" 2
expect "같은 SHA 댓글 추가 없음" "$(comments 2)" 1

# 4a. Claude 실패 → Codex 안 부름 · 댓글 없음
echo fail > "$F/mode.claude.8"; prs 8:b8
before=$(calls)
run >/dev/null
expect "Claude 실패 시 Codex 호출 없음" "$(( $(calls) - before ))" 0
expect "Claude 실패 PR 댓글 없음" "$(comments 8)" 0
expect "Claude 실패 장부 FAILED" "$(led 8 "$(sha b8)" FAILED)" 1
expect "실패해도 탭은 닫힘" "$(grep -c close "$F/tabs.log")" "$(grep -c open "$F/tabs.log")"

# 4b. Codex 실패 → 댓글 없음, 다음 회차 재시도
echo fail > "$F/mode.codex.3"; prs 3:b3
run >/dev/null
expect "Codex 실패 PR 댓글 없음" "$(comments 3)" 0
expect "Codex 실패 장부 FAILED" "$(led 3 "$(sha b3)" FAILED)" 1
echo ok > "$F/mode.codex.3"; run >/dev/null
expect "실패한 PR 은 다음 회차에 재시도되어 REVIEWED" "$(led 3 "$(sha b3)" REVIEWED)" 1

# 5. 개인정보 패턴 → 게시 보류
echo pii > "$F/mode.codex.4"; prs 4:b4
run >/dev/null
expect "개인정보 판정 댓글 게시 안 함" "$(comments 4)" 0
expect "개인정보 판정 장부 HOLD_PII" "$(led 4 "$(sha b4)" HOLD_PII)" 1

# 6a. 사용량 한도 → 그 회차 중단(#6 호출 안 됨)
echo usage > "$F/mode.codex.5"; prs 5:b5 6:b6
before=$(calls); run >/dev/null
expect "사용량 한도 뒤 같은 회차 중단" "$(( $(calls) - before ))" 1
expect "#6 은 이번 회차에 리뷰 안 됨" "$(comments 6)" 0

# 6a'. 모델 수용량 초과도 같은 회차를 멈춘다(실측 문구)
echo capacity > "$F/mode.codex.5"; prs 5:b5 6:b6
before=$(calls); run >/dev/null
expect "수용량 초과 뒤 같은 회차 중단" "$(( $(calls) - before ))" 1

# 6b. 1회 상한 — 상한에 걸려도 회차는 정상 종료한다
rm -f "$F/mode.codex.5"; prs 5:b5 6:b6 7:b7
before=$(calls)
expect "1회 상한 회차 종료값" "$(MAX=1 run)" 0
expect "1회 상한 1건" "$(( $(calls) - before ))" 1

# 6c. 다른 실행이 살아 있으면 아무것도 안 함
sleep 300 & holder=$!
mkdir -p "$T/state/lock" && echo "$holder" > "$T/state/lock/pid"
before=$(calls); run >/dev/null
expect "잠금 중 Codex 호출 없음" "$(( $(calls) - before ))" 0
kill "$holder" 2>/dev/null; wait "$holder" 2>/dev/null
# 잠금 주인이 죽었으면 넘겨받는다(재부팅·강제종료 뒤 영구 정지 방지)
run >/dev/null
if [ "$(calls)" -gt "$before" ]; then ok "죽은 잠금은 넘겨받음"; else bad "죽은 잠금 때문에 영구 정지"; fi

echo "CHECKED: $checked"
if [ "$fail" -eq 0 ]; then echo "PASS: PR 자동 리뷰 약속 ${checked}건 전부 충족"; exit 0; fi
echo "RESULT: 어긴 약속이 있다. exit 1"; exit 1
