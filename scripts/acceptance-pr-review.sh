#!/usr/bin/env bash
# acceptance-pr-review.sh — 열린 PR 자동 리뷰(scripts/pr-review/run.sh)가 약속대로 도는가 (#133)
#
# 가짜 gh·codex 와 로컬 bare 원격으로 run.sh 를 실제 실행해 결과(호출 수·댓글·원격 브랜치·장부)를 본다.
#   1. 새 SHA PR 만 PR 당 codex 1회 · 댓글 1개 · 장부 REVIEWED
#   2. 수정 커밋은 PR 브랜치로 push 되고, 그 새 SHA 는 다시 리뷰하지 않는다
#   3. 같은 SHA 는 건너뛴다
#   4. codex 실패 → 댓글 없음 · 다음 회차에 재시도
#   5. 개인정보 패턴이 든 판정은 게시하지 않는다
#   6. 사용량 한도 → 그 회차 중단 / 1회 상한 / 실행 중 잠금이면 아무것도 안 한다
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
F=$T/fake; mkdir -p "$F/comments" "$T/bin"
export GIT_AUTHOR_NAME=t GIT_AUTHOR_EMAIL=t@local GIT_COMMITTER_NAME=t GIT_COMMITTER_EMAIL=t@local

# ── 원격: 브랜치 b1..b7 ───────────────────────────────────────────────────
git init -q --bare "$T/remote.git"
git init -q "$T/seed"; (
  cd "$T/seed" && echo base > base.txt && git add . && git commit -qm base
  for b in b1 b2 b3 b4 b5 b6 b7; do
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
# ── 가짜 codex: 프롬프트의 'PR #N' 으로 동작을 고른다 (mode.N) ───────────────
cat > "$T/bin/codex" <<'EOF'
#!/usr/bin/env bash
F=$FAKE; out=""; dir=""; last=""
while [ $# -gt 0 ]; do
  case "$1" in -o) out=$2; shift ;; -C) dir=$2; shift ;; esac; last=$1; shift
done
n=$(printf '%s' "$last" | sed -n 's/.*PR #\([0-9]*\).*/\1/p' | head -1)
echo "$n" >> "$F/codex.calls"
mode=ok; [ -f "$F/mode.$n" ] && mode=$(cat "$F/mode.$n")
case "$mode" in
  fail)  echo "boom" >&2; exit 1 ;;
  usage) echo "ERROR: You've hit your usage limit." >&2; exit 1 ;;
  fix)   (cd "$dir" && echo fixed > fix.txt && git add fix.txt && git commit -qm "fix") ;;
esac
if [ "$mode" = pii ]; then v="연락처 someone@example.com"; else v="발견 없음"; fi
printf '## 자동 리뷰 PR #%s\n- %s\n판정: 병합 가능\n' "$n" "$v" > "$out"
EOF
chmod +x "$T/bin/gh" "$T/bin/codex"

export FAKE=$F PATH="$T/bin:$PATH" PR_REVIEW_STATE=$T/state PR_REVIEW_REMOTE=$T/remote.git PR_REVIEW_REPO=fake/repo
calls()    { wc -l < "$F/codex.calls" 2>/dev/null | tr -d ' ' || echo 0; }
comments() { ls "$F/comments" | grep -c "^$1\." ; }
led()      { grep -c "\"pr\":$1,\"sha\":\"$2\",\"status\":\"$3\"" "$T/state/ledger.jsonl" 2>/dev/null; }
run()      { PR_REVIEW_MAX_PER_RUN=${MAX:-3} bash "$RUN" > "$T/run.out" 2>&1; echo $?; }
: > "$F/codex.calls"

# 1·2. 새 PR 2건: #1 그대로, #2 수정 커밋
echo fix > "$F/mode.2"; A1=$(sha b1); B2=$(sha b2)
prs 1:b1 2:b2
expect "1회차 종료값" "$(run)" 0
expect "PR 당 codex 1회" "$(calls)" 2
expect "#1 댓글 1개" "$(comments 1)" 1
expect "#2 댓글 1개" "$(comments 2)" 1
expect "#1 장부 REVIEWED" "$(led 1 "$A1" REVIEWED)" 1
NB2=$(sha b2)
if [ "$NB2" != "$B2" ] && git --git-dir="$T/remote.git" cat-file -e "$NB2:fix.txt" 2>/dev/null; then
  ok "#2 수정 커밋이 PR 브랜치로 push 됨"; else bad "#2 수정 커밋이 원격 b2 에 없다"; fi
expect "#2 수정 후 SHA 도 장부 REVIEWED" "$(led 2 "$NB2" REVIEWED)" 1

# 3. 같은 SHA 재실행 → codex 호출 없음
prs 1:b1 2:b2
run >/dev/null
expect "같은 SHA 는 건너뜀(호출 수 불변)" "$(calls)" 2
expect "같은 SHA 댓글 추가 없음" "$(comments 2)" 1

# 4. 실패 → 댓글 없음, 다음 회차 재시도
echo fail > "$F/mode.3"; prs 3:b3
run >/dev/null
expect "실패한 PR 댓글 없음" "$(comments 3)" 0
expect "실패 장부 FAILED" "$(led 3 "$(sha b3)" FAILED)" 1
echo ok > "$F/mode.3"; run >/dev/null
expect "실패한 PR 은 다음 회차에 재시도되어 REVIEWED" "$(led 3 "$(sha b3)" REVIEWED)" 1

# 5. 개인정보 패턴 → 게시 보류
echo pii > "$F/mode.4"; prs 4:b4
run >/dev/null
expect "개인정보 판정 댓글 게시 안 함" "$(comments 4)" 0
expect "개인정보 판정 장부 HOLD_PII" "$(led 4 "$(sha b4)" HOLD_PII)" 1

# 6a. 사용량 한도 → 그 회차 중단(#6 호출 안 됨)
echo usage > "$F/mode.5"; prs 5:b5 6:b6
before=$(calls); run >/dev/null
expect "사용량 한도 뒤 같은 회차 중단" "$(( $(calls) - before ))" 1
expect "#6 은 이번 회차에 리뷰 안 됨" "$(comments 6)" 0

# 6b. 1회 상한
rm -f "$F/mode.5"; prs 5:b5 6:b6 7:b7
before=$(calls); MAX=1 run >/dev/null
expect "1회 상한 1건" "$(( $(calls) - before ))" 1

# 6c. 다른 실행이 살아 있으면 아무것도 안 함
sleep 300 & holder=$!
mkdir -p "$T/state/lock" && echo "$holder" > "$T/state/lock/pid"
before=$(calls); run >/dev/null
expect "잠금 중 codex 호출 없음" "$(( $(calls) - before ))" 0
kill "$holder" 2>/dev/null; wait "$holder" 2>/dev/null
# 잠금 주인이 죽었으면 넘겨받는다(재부팅·강제종료 뒤 영구 정지 방지)
run >/dev/null
if [ "$(calls)" -gt "$before" ]; then ok "죽은 잠금은 넘겨받음"; else bad "죽은 잠금 때문에 영구 정지"; fi

echo "CHECKED: $checked"
if [ "$fail" -eq 0 ]; then echo "PASS: PR 자동 리뷰 약속 ${checked}건 전부 충족"; exit 0; fi
echo "RESULT: 어긴 약속이 있다. exit 1"; exit 1
