#!/usr/bin/env bash
# hs0302-closeout-preflight.sh — HS-03.02 R6 스택 마감 사전검사 (마감 프롬프트 0·2·5·7단계의 실행부).
#
# 왜 있는가: 마감 프롬프트 v4.7 은 검증 명령이 산문 126줄에 박혀 있어 붙여넣는 사람마다 다르게
#   실행됐다. 명령을 이 파일 한 곳에 두고 프롬프트는 진입점 한 줄만 남긴다.
# 무엇을 하는가 (독립 함수, 순서 고정):
#   a. git 상태  — 브랜치·clean·기준 조상·"프롬프트 마지막 커밋 뒤 goal-prompts 밖 변경 0".
#                  git 조회는 종료값과 비어 있지 않은 SHA 를 먼저 확인한다(조회 실패를 0건으로 접지 않는다).
#   b. 동시 편집·공유메모리 — ps·lsof·ipcs 를 파일로 받아 rc 와 헤더를 확인하고 보고만 한다. 삭제 명령은 없다.
#   c. 변이 사본(AC-2) — pyproject·src·tests 를 mktemp 사본에 복제해 동일성·링크 0·원본 .venv 불변을 확인.
#   d. 격리 클론(AC-3) — --no-local 클론에 uv sync 로 새 venv 를 만들고 탐침 시험을 클론의 pytest 로 돌린다.
#   e. --check-v1 <sha> — 호출자가 남긴 v1-rc.txt(실제 셸 반환값)·판정 파일·대상 SHA·venv 지문을 검사한다.
#      V1(codex exec) 자체는 이 스크립트가 부르지 않는다.
# 출력 계약: 마지막 두 줄이 `CHECKED: N` 과 `VERDICT: PASS|FAIL|BLOCKED`. 종료값 0/1/2.
#   PASS 는 필수 검사 이름마다 `PASS: <이름>` 이 남아야만 난다(CHECKED 는 보고용 숫자일 뿐이다).
#   FAIL = 대상이 틀렸다. BLOCKED = 검증 환경을 못 만들었다(mktemp 실패·경로 미존재·조회 실패·동시 편집).
# 한계: 공유메모리 조회(ipcs)는 macOS 형식(`T ` 헤더·`m` 행) 전용이며 GNU util-linux 형식에서는 shm.ledger 가 BLOCKED 로 끝난다 —
#   리눅스에서 실제 마감 실행은 불가하고, CI 의 인수 시험은 macOS 모양 대역으로 판정 논리만 잰다(Codex 적대 리뷰 D3). stat/date 는 GNU 대체 형식. 검사기 자신의
#   문법·판정 논리는 scripts/acceptance-hs0302-preflight.sh 가 반례 33종으로 공격한다.
#   --check-v1 은 "클론 환경이 그대로인가" 를 증명하지 판정이 그 클론에서 나왔는지는 증명하지 못한다(자기 신고) — 2026-09-17 codeaudit B5.
set -euo pipefail

if [ "${HS0302_PREFLIGHT_DEPTH:-0}" -gt 0 ]; then
  echo "FAIL: 재귀 호출 — 이 검사기는 자기 자신을 다시 부르지 않는다 (depth=${HS0302_PREFLIGHT_DEPTH})"
  echo "CHECKED: 0"; echo "VERDICT: FAIL"; exit 1
fi
export HS0302_PREFLIGHT_DEPTH=1
unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE GIT_OBJECT_DIRECTORY \
      GIT_ALTERNATE_OBJECT_DIRECTORIES GIT_COMMON_DIR GIT_PREFIX GIT_QUARANTINE_PATH

GREP=/usr/bin/grep
BRANCH=task/hs-0302-r6-survivor-defenses-20260916
BASE=task/hs-0302-candidate-identity-20260914
PROMPT=docs/engineering/goal-prompts/hs-0302-r6-next-prompt-2026-09-16.md
W="$PWD"; MODE=full; V1_SHA=""; SESSION=""; EVIDENCE=""
usage() {
  cat <<'USAGE'
사용: hs0302-closeout-preflight.sh [--worktree DIR] [--branch NAME] [--base NAME] [--prompt PATH]
      hs0302-closeout-preflight.sh --check-v1 <SHA> --session <S> [--worktree DIR] [--evidence-dir DIR]
USAGE
}
need() { [ $# -ge 2 ] && case "$2" in --*) false ;; *) true ;; esac || { echo "FAIL: 인자 $1 의 값이 없다(다음 토큰: ${2:-<없음>})"; usage; echo "CHECKED: 0"; echo "VERDICT: FAIL"; exit 1; }; }   # 값 자리에 다른 --옵션이 오면 값 누락(Codex V1 8회차)
while [ $# -gt 0 ]; do
  case "$1" in
    --worktree) need "$@"; W="$2"; shift 2 ;;
    --branch) need "$@"; BRANCH="$2"; shift 2 ;;
    --base) need "$@"; BASE="$2"; shift 2 ;;
    --prompt) need "$@"; PROMPT="$2"; shift 2 ;;
    --check-v1) need "$@"; MODE=v1; V1_SHA="$2"; shift 2 ;;
    --session) need "$@"; SESSION="$2"; shift 2 ;;
    --evidence-dir) need "$@"; EVIDENCE="$2"; shift 2 ;;
    -h|--help) [ $# -eq 1 ] || { echo "FAIL: --help 는 단독으로만 쓴다(뒤에 붙은 인자: ${*:2})"; usage; echo "CHECKED: 0"; echo "VERDICT: FAIL"; exit 1; }; usage; exit 0 ;;   # Codex V1 8회차: --help 뒤 잘못된 인자가 rc 0·꼬리 없이 끝났다
    *) echo "FAIL: 알 수 없는 인자 $1"; usage; echo "CHECKED: 0"; echo "VERDICT: FAIL"; exit 1 ;;
  esac
done

# ── 장부 ─────────────────────────────────────────────────────────────────────
checked=0; fails=0; blocks=0; passed=" "
REQUIRED_FULL="git.worktree git.branch git.clean git.base-ancestor git.prompt-tail proc.codex proc.cwd shm.ledger ac2.copy ac3.clone shm.post"
REQUIRED_V1="v1.sha v1.head v1.rc v1.verdict v1.venv-same"
note() { printf '  %s\n' "$*"; }
pass() { checked=$((checked + 1)); passed="$passed$1 "; printf 'PASS: %s — %s\n' "$1" "$2"; }
fail() { checked=$((checked + 1)); fails=$((fails + 1)); printf 'FAIL: %s — %s\n' "$1" "$2"; }
blocked() { checked=$((checked + 1)); blocks=$((blocks + 1)); printf 'BLOCKED: %s — %s\n' "$1" "$2"; }
SNAP_PID=""
stop_sampler() { # kill 이 아니라 정지 표식으로 끝낸다 — 죽인 표본기의 sleep 자식이 워크트리 cwd 를 쥔 고아로 남는다(2026-09-17 실측)
  if [ -n "$SNAP_PID" ]; then : > "$S/sampler.stop"; wait "$SNAP_PID" 2>>"$S/sampler.err" || :; SNAP_PID=""; fi; }
finish() {
  stop_sampler
  local required="$REQUIRED_FULL" n
  [ "$MODE" = v1 ] && required="$REQUIRED_V1"
  if [ "$fails" -eq 0 ] && [ "$blocks" -eq 0 ]; then
    for n in $required; do
      case "$passed" in *" $n "*) ;; *) printf 'MISSING: %s — 필수 검사가 PASS 를 남기지 않았다\n' "$n"; fails=$((fails + 1)) ;; esac
    done
  fi
  printf 'CHECKED: %d\n' "$checked"
  if [ "$fails" -gt 0 ]; then echo "VERDICT: FAIL"; exit 1; fi
  if [ "$blocks" -gt 0 ]; then echo "VERDICT: BLOCKED"; exit 2; fi
  echo "VERDICT: PASS"; exit 0
}
die_blocked() { blocked "$1" "$2"; stop_sampler; printf 'CHECKED: %d\n' "$checked"; echo "VERDICT: BLOCKED"; exit 2; }
run_required() { "$2"; }   # 이름은 장부 대조용(finish 가 필수 이름별 PASS 를 요구한다)
physdir() { (cd -- "$1" 2>/dev/null && pwd -P); }
# stat 형식: BSD(macOS) 우선, 아니면 GNU. 지문 = inode 크기 mtime 권한 링크수 경로
if stat -f '%i' / >/dev/null 2>&1; then STAT_FP=(stat -f '%i %z %m %p %l %N'); STAT_PERM=(stat -f '%Lp %N')
else STAT_FP=(stat -c '%i %s %Y %a %h %n'); STAT_PERM=(stat -c '%a %n'); fi
fp_stat() { find "$1" -type f -exec "${STAT_FP[@]}" {} + | sort | shasum -a 256; }
# 전체 지문 = 일반 파일(stat·내용 해시) + 심볼릭 링크의 대상. 링크 대상을 빼면 bin/python 이 다른 인터프리터를 가리켜도 "동일" 로 나온다(Codex V1 2026-09-17 실증).
fp_full() { { find "$1" -type f -exec "${STAT_FP[@]}" {} + | sort; find "$1" -type f -exec shasum -a 256 {} + | sort -k2; find "$1" -type l -exec sh -c 'for l; do printf "L %s -> %s\n" "$l" "$(readlink "$l")"; done' _ {} + | sort; } | shasum -a 256; }
perm_list() { (cd -- "$1" && find src tests -type f -not -path '*/__pycache__/*' -exec "${STAT_PERM[@]}" {} + | sort); }
gitq() { # gitq <outvar> <args...> : 종료값 0 이 아니면 1 을 돌려준다(호출자가 BLOCKED 로 적는다)
  local __v="$1"; shift; local out rc=0
  out=$(git -C "$W" "$@" 2>"$S/git.err") || rc=$?
  printf -v "$__v" '%s' "$out"; return "$rc"
}
is_sha() { printf '%s' "$1" | "$GREP" -qE '^[0-9a-f]{40}$'; }

if [ ! -x "$GREP" ] || ! printf 'alpha\n' | "$GREP" -q 'alpha' || printf 'alpha\n' | "$GREP" -q 'beta'; then
  echo "BLOCKED: grep.self — $GREP 자기검사 실패(PATH 의 grep 은 ugrep 으로 가려질 수 있어 절대경로만 쓴다)"
  echo "CHECKED: 0"; echo "VERDICT: BLOCKED"; exit 2
fi
S=$(mktemp -d 2>/dev/null) || { echo "BLOCKED: session.mktemp — 임시 폴더를 만들지 못했다(검증 환경 부재)"; echo "CHECKED: 0"; echo "VERDICT: BLOCKED"; exit 2; }
[ -d "$W" ] || die_blocked "worktree.path" "경로가 없다: $W"
W=$(physdir "$W") || die_blocked "worktree.path" "실경로를 얻지 못했다: $W"
cd -- "$W" || die_blocked "worktree.path" "이동 실패: $W"
# 강제 종료(메모리 부족·kill)에도 표본기를 남기지 않고, 신호로 끊긴 실행은 PASS 를 찍지 못한다(codeaudit B2 + 반례 18 실측: 트랩이 정지만 하면 실행이 이어져 PASS 까지 찍혔다)
on_signal() { stop_sampler; printf 'CHECKED: %d\n' "$checked"; echo "VERDICT: BLOCKED"; exit 2; }
trap on_signal INT TERM; trap stop_sampler EXIT
printf 'SESSION_DIR=%s\nWORKTREE=%s\nMODE=%s\n' "$S" "$W" "$MODE"

# ── a. git 상태 ──────────────────────────────────────────────────────────────
check_git_worktree() {
  local top
  gitq top rev-parse --show-toplevel || { blocked git.worktree "git 조회 실패 rc≠0: $(head -1 "$S/git.err")"; return; }
  [ "$(physdir "$top")" = "$W" ] && pass git.worktree "$W" || fail git.worktree "저장소 최상위 $top ≠ $W"
}
check_git_branch() {
  local br
  gitq br branch --show-current || { blocked git.branch "git 조회 실패: $(head -1 "$S/git.err")"; return; }
  [ -n "$br" ] || { fail git.branch "브랜치 이름이 비었다(detached HEAD)"; return; }
  [ "$br" = "$BRANCH" ] && pass git.branch "$br" || fail git.branch "$br ≠ $BRANCH"
}
check_git_clean() {
  local st
  gitq st status --porcelain || { blocked git.clean "git status 실패: $(head -1 "$S/git.err")"; return; }
  [ -z "$st" ] && pass git.clean "git status --porcelain 빈 출력" || fail git.clean "미커밋 변경: $(printf '%s' "$st" | head -3 | tr '\n' ';')"
}
check_git_base_ancestor() {
  local x rc=0
  gitq x rev-parse --verify "$BASE^{commit}" || { blocked git.base-ancestor "기준 브랜치 조회 실패 $BASE: $(head -1 "$S/git.err")"; return; }
  is_sha "$x" || { blocked git.base-ancestor "기준 조회 출력이 SHA 가 아니다: '$x' (조회 계층 오염)"; return; }
  git -C "$W" merge-base --is-ancestor "$BASE" HEAD 2>"$S/git.err" || rc=$?
  case "$rc" in
    0) pass git.base-ancestor "$BASE($x) 은 HEAD 의 조상" ;;
    1) fail git.base-ancestor "$BASE 이 HEAD 의 조상이 아니다" ;;
    *) blocked git.base-ancestor "merge-base 조회 실패 rc=$rc" ;;
  esac
}
check_git_prompt_tail() {
  local p head diff out rc=0
  gitq head rev-parse HEAD || { blocked git.prompt-tail "HEAD 조회 실패"; return; }
  is_sha "$head" || { blocked git.prompt-tail "HEAD 가 SHA 가 아니다: '$head'"; return; }
  HEAD_SHA="$head"
  [ -f "$W/$PROMPT" ] || { blocked git.prompt-tail "프롬프트 경로가 없다(검증 입력 부재): $PROMPT"; return; }
  gitq p log -1 --format=%H -- "$PROMPT" || { blocked git.prompt-tail "프롬프트 커밋 조회 실패: $(head -1 "$S/git.err")"; return; }
  # 빈 출력도 SHA 가 아니다 — 추적되지 않은 파일인지 조회 이상인지 여기서 구분할 수 없으므로 계약대로 BLOCKED(Codex V1 5회차)
  is_sha "$p" || { blocked git.prompt-tail "프롬프트 커밋 조회 출력이 SHA 가 아니다: '${p:-<빈 출력>}' (추적되지 않은 파일이거나 조회 계층 이상)"; return; }
  gitq diff diff --name-only "$p..HEAD" || { blocked git.prompt-tail "diff 조회 실패: $(head -1 "$S/git.err")"; return; }
  out=$(printf '%s\n' "$diff" | "$GREP" -v -e '^$' -e '^docs/engineering/goal-prompts/') || rc=$?
  [ "$rc" -le 1 ] || { blocked git.prompt-tail "grep 실행 오류 rc=$rc"; return; }
  [ -z "$out" ] && pass git.prompt-tail "P=$p 뒤 goal-prompts 밖 변경 0 (HEAD=$head)" || fail git.prompt-tail "P=$p 뒤 goal-prompts 밖 변경: $(printf '%s' "$out" | tr '\n' ' ')"
}

# ── b. 동시 편집·공유메모리 (보고만, 삭제 없음) ──────────────────────────────
check_proc_codex() {
  local rc=0 hits
  ps -axo pid,ppid,command > "$S/ps-all.txt" 2>"$S/ps.err" || rc=$?
  [ "$rc" -eq 0 ] && [ "$(wc -l < "$S/ps-all.txt")" -ge 2 ] && head -1 "$S/ps-all.txt" | "$GREP" -q 'PID' \
    || { blocked proc.codex "ps 조회 실패 rc=$rc 또는 헤더 없음"; return; }
  hits=$(awk -v me="$$" -v pp="$PPID" 'NR>1 && $1!=me && $1!=pp && $2!=me && /[c]odex (app-server|exec)/' "$S/ps-all.txt")
  [ -z "$hits" ] && pass proc.codex "codex app-server/exec 0건(자기 pid·ppid 제외)" \
    || blocked proc.codex "다른 codex 프로세스가 떠 있다(동시 편집 위험): $(printf '%s' "$hits" | head -3 | cut -c1-90 | tr '\n' ';')"
}
check_proc_cwd() {
  local rc=0 rel self=0 other=0 others="" pid cmd path lsof_pid
  lsof -d cwd -Fpcn > "$S/lsof-cwd.txt" 2>"$S/lsof.err" & lsof_pid=$!   # lsof 는 ps 스냅샷 뒤에 태어나므로 pid 를 직접 받아 제외한다
  wait "$lsof_pid" || rc=$?
  [ "$rc" -eq 0 ] && "$GREP" -q '^p' "$S/lsof-cwd.txt" || { blocked proc.cwd "lsof 조회 실패 rc=$rc 또는 p 줄 0"; return; }
  # 자기 셸·조상·자손(파이프라인 자식)은 제외한다. 계통은 ps 스냅샷으로 재구성한다.
  rel=$(awk -v me="$$" 'NR>1{pp[$1]=$2} END{r[me]=1; p=me; for(i=0;i<64&&(p in pp)&&pp[p]>1;i++){p=pp[p]; r[p]=1}
        c=1; while(c){c=0; for(k in pp) if(!(k in r) && (pp[k] in r)){r[k]=1; c=1}} for(k in r) print k}' "$S/ps-all.txt")
  while IFS=$'\t' read -r pid cmd path; do
    [ -n "$pid" ] || continue
    case "$path" in "$W"|"$W"/*) ;; *) continue ;; esac
    if [ "$pid" = "$$" ]; then self=1
    elif [ "$pid" = "$lsof_pid" ] || printf '%s\n' "$rel" | "$GREP" -qx "$pid"; then :
    else other=$((other + 1)); others="$others $pid($cmd)"; fi
  done < <(awk '/^p/{pid=substr($0,2)} /^c/{cmd=substr($0,2)} /^n/{print pid "\t" cmd "\t" substr($0,2)}' "$S/lsof-cwd.txt")
  [ "$self" -eq 1 ] || { blocked proc.cwd "자기 셸(pid $$)이 lsof 에 안 보인다 — 검사가 살아 있지 않다"; return; }
  [ "$other" -eq 0 ] && pass proc.cwd "이 워크트리를 cwd 로 가진 다른 프로세스 0 (SELF 확인)" \
    || blocked proc.cwd "다른 프로세스 ${other}개가 이 워크트리에 있다:$others"
}
shm_ledger() { # shm_ledger <raw> <ledger> : ipcs -mp 를 파일로 받고 헤더 확인 뒤 ID OWNER CPID 만 남긴다
  local rc=0
  ipcs -mp > "$1" 2>"$S/ipcs.err" || rc=$?
  [ "$rc" -eq 0 ] && "$GREP" -q '^T ' "$1" || return 1
  awk '$1=="m"{print $2, $5, $7}' "$1" | sort > "$2"
}
check_shm_ledger() {
  local n rc=0
  shm_ledger "$S/shm-pre-raw.txt" "$S/shm-pre.txt" || { blocked shm.ledger "ipcs -mp 조회 실패(rc 또는 헤더 T 없음) — 세그먼트 0건이 아니다"; return; }
  ipcs -ma > "$S/shm-pre-nattch.txt" 2>"$S/ipcs.err" || rc=$?
  [ "$rc" -eq 0 ] && "$GREP" -q '^T ' "$S/shm-pre-nattch.txt" || { blocked shm.ledger "ipcs -ma 조회 실패 rc=$rc"; return; }
  n=$(wc -l < "$S/shm-pre.txt" | tr -d ' ')
  awk '{print "  shm 사전 장부:", $0}' "$S/shm-pre.txt"
  if [ "$n" -ge 30 ]; then blocked shm.ledger "공유메모리 세그먼트 ${n}개 ≥ 30 — invoice 게이트가 shmget ENOSPC 로 죽는다. 정리는 사람 결정"
  else pass shm.ledger "사전 장부 ${n}개(ID OWNER CPID), 한도 30 미만"; fi
  ( while [ ! -e "$S/sampler.stop" ]; do printf 'T %s\n' "$(date +%s)"; LC_ALL=C ps -axo pid=,ppid=,lstart=; sleep 1; done >> "$S/ps-snap.txt" ) 2>>"$S/sampler.err" &
  SNAP_PID=$!
  : > "$S/sweep-pids.txt"
}
to_epoch() { # to_epoch <lstart 문자열|hh:mm:ss(오늘)> — 실패면 빈 문자열
  local v="$1" e=""
  case "$v" in
    [0-9][0-9]:[0-9][0-9]:[0-9][0-9]) e=$(LC_ALL=C date -j -f '%Y-%m-%d %H:%M:%S' "$(date +%Y-%m-%d) $v" +%s 2>/dev/null) || e=$(date -d "$(date +%Y-%m-%d) $v" +%s 2>/dev/null) || e="" ;;
    *) e=$(LC_ALL=C date -j -f '%a %b %d %H:%M:%S %Y' "$v" +%s 2>/dev/null) || e=$(LC_ALL=C date -d "$v" +%s 2>/dev/null) || e="" ;;
  esac
  printf '%s' "$e"
}
judge_new_shm() { # 소유권 6조건. 전부 성립해야 0. 삭제는 하지 않는다.
  local id="$1" owner cpid ctime ct lst ls lin alive born alivepid nattch ok=1
  owner=$(awk -v id="$id" '$1==id{print $2}' "$S/shm-post.txt"); cpid=$(awk -v id="$id" '$1==id{print $3}' "$S/shm-post.txt")
  ctime=$(awk -v id="$id" '$1=="m" && $2==id {print $15}' "$S/shm-post-nattch.txt"); nattch=$(awk -v id="$id" '$1=="m" && $2==id {print $9}' "$S/shm-post-nattch.txt")
  ct=$(to_epoch "$ctime"); lst=$(awk -v c="$cpid" '$1==c {print $3, $4, $5, $6, $7; exit}' "$S/ps-snap.txt"); ls=$(to_epoch "$lst")
  lin=$(awk -v c="$cpid" 'NR==FNR{top[$1]=1; next} $1=="T"{next} {if (!($1 in pp)) pp[$1]=$2} END{p=c; for(i=0; i<64 && (p in pp); i++){if(p in top){print "LINEAGE_OK"; exit} p=pp[p]} print "LINEAGE_NO"}' "$S/sweep-pids.txt" "$S/ps-snap.txt")
  alive=$(awk -v c="$cpid" -v ct="${ct:-999999999999}" '$1=="T"{t=$2; next} $1==c && t>=ct {print "ALIVE_AFTER_CREATE"; exit}' "$S/ps-snap.txt")
  case "$ls:$ct" in :*|*:|*[!0-9:]*) born="BLOCKED(시각 변환 실패)" ;; *) [ "$ls" -lt "$ct" ] && born=BORN_BEFORE_CREATE || born="NOT_BORN_BEFORE" ;; esac
  alivepid=$(ps -p "$cpid" -o pid= 2>/dev/null | wc -l | tr -d ' ')
  note "shm 신규 ID $id: OWNER=$owner(me=$(id -un)) CPID=$cpid CTIME=$ctime nattch=$nattch $lin ${alive:-NOT_ALIVE_AFTER_CREATE} $born ps-p=$alivepid"
  [ "$owner" = "$(id -un)" ] && [ "$lin" = LINEAGE_OK ] && [ "$alive" = ALIVE_AFTER_CREATE ] && [ "$born" = BORN_BEFORE_CREATE ] \
    && [ "$alivepid" = 0 ] && [ "$nattch" = 0 ] && ok=0
  return "$ok"
}
check_shm_post() {
  local new reuse id bad=0 rc=0
  stop_sampler
  shm_ledger "$S/shm-post-raw.txt" "$S/shm-post.txt" || { blocked shm.post "사후 ipcs -mp 조회 실패"; return; }
  ipcs -ma > "$S/shm-post-nattch.txt" 2>"$S/ipcs.err" || rc=$?
  [ "$rc" -eq 0 ] && "$GREP" -q '^T ' "$S/shm-post-nattch.txt" || { blocked shm.post "사후 ipcs -ma 조회 실패 rc=$rc"; return; }
  new=$(comm -13 "$S/shm-pre.txt" "$S/shm-post.txt" | awk '{print $1}')
  [ -n "$new" ] || { pass shm.post "이 실행이 만든 신규 세그먼트 0"; return; }
  reuse=$(awk '$1=="T"{next} {ls=$3" "$4" "$5" "$6" "$7; if (($1 in st) && st[$1] != ls) s[$1] = 1; st[$1] = ls} END{for (p in s) print "REUSE-SUSPECT", p}' "$S/ps-snap.txt")
  [ -z "$reuse" ] || { blocked shm.post "pid 재사용 의심 — 신규 ID 전부 판정 보류: $(printf '%s' "$reuse" | tr '\n' ';')"; return; }
  for id in $new; do judge_new_shm "$id" || bad=$((bad + 1)); done
  [ "$bad" -eq 0 ] && pass shm.post "신규 세그먼트 $(printf '%s\n' "$new" | wc -l | tr -d ' ')개 전부 소유권 6조건 증명 — 삭제는 사람이 ipcrm 으로" \
    || blocked shm.post "소유권을 증명 못 한 신규 세그먼트 ${bad}개 — 삭제하지 않는다(nattch 0 은 소유 증거가 아니다)"
}
sweep() { # sweep <dir> <log> <cmd...> : dir 에서 최상위 pid 를 남기며 직렬 실행. 종료값을 돌려준다.
  local dir="$1" log="$2" pid rc=0; shift 2
  ( cd -- "$dir" && exec "$@" ) > "$log" 2>&1 & pid=$!
  echo "$pid" >> "$S/sweep-pids.txt"
  wait "$pid" || rc=$?
  return "$rc"
}

# ── c. 변이 사본(AC-2) — 원본 작업트리에는 아무것도 쓰지 않는다 ─────────────
check_ac2_copy() {
  local cd0 st0 st1 venv0 venv1 loaded rc=0 n
  [ -d "$W/humansearch/.venv" ] || { blocked ac2.copy "원본 $W/humansearch/.venv 가 없다(3단계 pytest 를 먼저 돌려야 한다)"; return; }
  gitq st0 status --porcelain || { blocked ac2.copy "git status 실패"; return; }
  venv0=$(fp_full "$W/humansearch/.venv")   # 원본 venv 도 링크 대상까지 — 파일 전용 지문은 bin/python 링크 교체를 못 본다(codeaudit B1)
  cd0=$(mktemp -d "$S/ac2-copy.XXXXXX" 2>/dev/null) || { blocked ac2.copy "사본 mktemp 실패"; return; }
  printf 'AC2_COPY=%s\n' "$cd0"
  cp "$W/humansearch/pyproject.toml" "$cd0/" && cp -R "$W/humansearch/src" "$W/humansearch/tests" "$cd0/" || { blocked ac2.copy "복제 실패"; return; }
  find "$cd0" \( -name __pycache__ -o -name .pytest_cache \) -type d -prune -exec rm -rf {} +
  n=$(find "$cd0" -name '*.pyc' | wc -l | tr -d ' '); [ "$n" = 0 ] || { fail ac2.copy "사본에 .pyc ${n}개 잔존"; return; }
  cmp "$W/humansearch/pyproject.toml" "$cd0/pyproject.toml" > "$S/ac2-diff.txt" 2>&1 \
    && diff -qr -x __pycache__ -x .pytest_cache "$W/humansearch/src" "$cd0/src" >> "$S/ac2-diff.txt" 2>&1 \
    && diff -qr -x __pycache__ -x .pytest_cache "$W/humansearch/tests" "$cd0/tests" >> "$S/ac2-diff.txt" 2>&1 \
    && diff <(perm_list "$W/humansearch") <(perm_list "$cd0") >> "$S/ac2-diff.txt" 2>&1 || rc=$?
  [ "$rc" -eq 0 ] && [ ! -s "$S/ac2-diff.txt" ] || { fail ac2.copy "사본이 원본과 다르다(내용·권한): $(head -2 "$S/ac2-diff.txt" | tr '\n' ';')"; return; }
  n=$(find "$cd0" -type l | wc -l | tr -d ' '); [ "$n" = 0 ] || { fail ac2.copy "사본 안 symlink ${n}개"; return; }
  n=$(find "$cd0" -type f -links +1 | wc -l | tr -d ' '); [ "$n" = 0 ] || { fail ac2.copy "사본 안 hardlink ${n}개"; return; }
  rc=0
  sweep "$cd0" "$S/ac2-load.log" env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$cd0/src" \
    uv run --frozen --no-sync --project "$W/humansearch" python -c 'import os, humansearch.candidate_identity as m; print(os.path.realpath(m.__file__))' || rc=$?
  loaded=$(tail -n 1 "$S/ac2-load.log")
  [ "$rc" -eq 0 ] || { blocked ac2.copy "사본 모듈 로드 실행 실패 rc=$rc: $(head -1 "$S/ac2-load.log")"; return; }
  case "$loaded" in "$(physdir "$cd0")"/*) ;; *) fail ac2.copy "사본이 아니라 다른 경로의 모듈이 실행됐다: $loaded"; return ;; esac
  n=$(find "$W/humansearch/.venv" -newer "$cd0/pyproject.toml" | wc -l | tr -d ' ')
  venv1=$(fp_full "$W/humansearch/.venv"); gitq st1 status --porcelain || { blocked ac2.copy "git status 실패(사후)"; return; }
  [ "$n" = 0 ] && [ "$venv0" = "$venv1" ] || { fail ac2.copy "원본 .venv 가 바뀌었다(newer ${n}개, 지문 전후 $([ "$venv0" = "$venv1" ] && echo 동일 || echo 상이))"; return; }
  [ "$st0" = "$st1" ] && pass ac2.copy "사본 $cd0 동일·링크 0·모듈 realpath 사본 안·원본 .venv 지문 불변·git status 불변" || fail ac2.copy "git status 가 전후 다르다"
}

# ── d. 격리 클론(AC-3) — 클론과 venv 지문은 세션 폴더에 남긴다(V1 은 호출자가 그 클론에서 돌린다) ──
write_probe() { mkdir -p "$S/probe"; cat > "$S/probe/test_v1_clone_paths.py" <<'PY'
import glob, json, os, re, subprocess, sys, sysconfig, pytest, humansearch.candidate_identity as m
def test_v1_clone_paths_are_inside_clone():
    c = os.environ["C"]; root = os.path.realpath(c) + os.sep
    def inside(k, v):
        if not v or not os.path.isabs(v):
            return False
        real = os.path.realpath(os.path.dirname(v)) + os.sep + os.path.basename(v) if k in ("sys.executable", "pytest-shebang") else os.path.realpath(v)
        return real.startswith(root)
    items = {"sys.prefix": sys.prefix, "sys.executable": sys.executable, "module": m.__file__, "pytest": pytest.__file__}
    shared = []
    for r, ds, fs in os.walk(c):
        ds[:] = [d for d in ds if d not in (".git", ".venv")]
        shared += [os.path.join(r, x) for x in fs if os.stat(os.path.join(r, x)).st_nlink > 1]
    assert not shared, "hard-linked files in clone (shared with another checkout): " + ", ".join(shared[:5])
    with open(os.path.join(c, "humansearch/.venv/bin/pytest"), encoding="utf-8") as f:
        first, second = f.readline().strip(), f.readline()
    hit = re.search(r"'([^']*/bin/python[^']*)'", second) if first == "#!/bin/sh" else None
    items["pytest-shebang"] = hit.group(1) if hit else first.removeprefix("#!")
    allowed = {"_virtualenv.pth": ["import _virtualenv"], "humansearch.pth": None}
    for p in sorted(glob.glob(os.path.join(sysconfig.get_paths()["purelib"], "*.pth"))):
        name = os.path.basename(p); lines = [ln.rstrip("\n") for ln in open(p, encoding="utf-8") if ln.strip() and not ln.startswith("#")]
        if name not in allowed or (allowed[name] is not None and lines != allowed[name]) or (allowed[name] is None and (len(lines) != 1 or lines[0].startswith("import "))):
            items[".pth-unexpected:" + name] = "/UNEXPECTED_PTH/" + name + "#" + " | ".join(lines)[:100]
        elif allowed[name] is None:
            items[".pth:" + name] = lines[0]
    own = os.path.realpath(os.path.dirname(__file__)) + os.sep
    stdlib = {os.path.realpath(x) for x in json.loads(subprocess.check_output([sys.executable, "-S", "-c", "import sys, json; print(json.dumps(sys.path))"]).decode()) if x}
    for k, entry in enumerate(sys.path):
        e = os.path.realpath(entry or os.getcwd())
        if not ((e + os.sep).startswith(root) or (e + os.sep).startswith(own) or e in stdlib):
            items["sys.path#" + str(k)] = entry
    bad = [k for k, v in items.items() if not inside(k, v)]
    for k, v in items.items():
        print(("OUTSIDE " if k in bad else "OK ") + k + " = " + str(v))
    assert not bad, "clone outside: " + ", ".join(bad)
PY
}
run_probe() { # run_probe <clone> <log> : 클론의 uv run pytest 로 탐침 실행. 0 = 1 passed·이름별 OK 6·OUTSIDE 0
  local c="$1" log="$2" rc=0 named=0 nm outside
  sweep "$c/humansearch" "$log" env C="$c" PYTHONDONTWRITEBYTECODE=1 \
    uv run --frozen pytest -c pyproject.toml -p no:cacheprovider -q -s "$S/probe/test_v1_clone_paths.py" || rc=$?
  for nm in sys.prefix sys.executable module pytest pytest-shebang .pth:humansearch.pth; do
    "$GREP" -q "^OK $nm = " "$log" && named=$((named + 1))
  done
  outside=$("$GREP" -c '^OUTSIDE ' "$log") || :
  PROBE_DETAIL="rc=$rc named=$named/6 OUTSIDE=$outside $("$GREP" -o '[0-9]* passed' "$log" | head -1)"
  [ "$rc" -eq 0 ] && [ "$named" -eq 6 ] && [ "$outside" = 0 ] && "$GREP" -q '1 passed' "$log"
}
check_ac3_clone() {
  local c="$S/v1-clone" plus lock rc=0 pos ext
  git clone -q --no-local "$W" "$c" 2>"$S/clone.err" && git -C "$c" checkout -q "$HEAD_SHA" 2>>"$S/clone.err" \
    || { blocked ac3.clone "클론 실패: $(head -1 "$S/clone.err")"; return; }
  [ ! -e "$c/humansearch/.venv" ] || { fail ac3.clone "클론 직후 .venv 가 이미 있다(추적된 venv?)"; return; }
  (cd "$c/humansearch" && uv sync --frozen) > "$S/v1-sync.log" 2>&1 || rc=$?
  [ "$rc" -eq 0 ] || { blocked ac3.clone "uv sync --frozen 실패 rc=$rc: $(tail -1 "$S/v1-sync.log")"; return; }
  plus=$("$GREP" -c '^ + ' "$S/v1-sync.log") || :; lock=$("$GREP" -c '^\[\[package\]\]' "$c/humansearch/uv.lock") || :
  [ "$lock" -gt 1 ] && [ "$plus" -ge $((lock - 1)) ] && "$GREP" -q '^Installed ' "$S/v1-sync.log" \
    || { fail ac3.clone "새 설치 증거 부족: 설치 줄 $plus < uv.lock 패키지 $lock − 1 또는 Installed 줄 없음(복사 venv 의심)"; return; }
  write_probe
  run_probe "$c" "$S/v1-probe.log" || { fail ac3.clone "탐침 실패($PROBE_DETAIL) — 클론 밖 경로가 실행된다"; return; }
  printf '%s\n' "$W" > "$S/probe/positive.txt"; pos=$("$GREP" -rlF -- "$W" "$S/probe/positive.txt" | wc -l | tr -d ' ')
  [ "$pos" = 1 ] || { blocked ac3.clone "grep 양성 대조군 $pos ≠ 1 — 검사기가 살아 있지 않다"; return; }
  rc=0; ext=$("$GREP" -rlF -- "$W" "$c/humansearch/.venv" 2>"$S/grep.err") || rc=$?
  case "$rc" in
    1) ;; 0) fail ac3.clone "클론 venv 안에 원본 경로 문자열: $(printf '%s' "$ext" | head -2 | tr '\n' ';')"; return ;;
    *) blocked ac3.clone "grep 읽기 오류 rc=$rc"; return ;;
  esac
  find "$c/humansearch/.venv" -name __pycache__ -type d -prune -exec rm -rf {} +
  fp_full "$c/humansearch/.venv" > "$S/v1-venv-id.txt"
  printf 'V1_CLONE=%s\nV1_VENV_ID=%s\n' "$c" "$(cut -d' ' -f1 "$S/v1-venv-id.txt")"
  pass ac3.clone "--no-local 클론, 새 venv(설치 $plus/lock $lock), 탐침 $PROBE_DETAIL, 원본 경로 grep 0, 지문 기록"
}

# ── e. V1 증거(--check-v1) — 호출자가 남긴 파일만 검사한다 ─────────────────────
check_v1_sha() { is_sha "$V1_SHA" && pass v1.sha "$V1_SHA" || fail v1.sha "대상 SHA 형식이 아니다: '$V1_SHA'"; }
check_v1_head() {
  local h; gitq h rev-parse HEAD || { blocked v1.head "HEAD 조회 실패"; return; }
  is_sha "$h" || { blocked v1.head "HEAD 조회 출력이 SHA 가 아니다: '$h' (조회 계층 오염)"; return; }
  [ "$h" = "$V1_SHA" ] && pass v1.head "HEAD = 대상 SHA" || fail v1.head "HEAD $h ≠ 대상 $V1_SHA (다른 트리의 판정이다)"
}
check_v1_rc() {
  local f="$EVIDENCE/v1-rc.txt" v
  [ -f "$f" ] || { fail v1.rc "$f 없음 — codex exec 의 실제 반환값 기록이 없으면 판정은 채택되지 않는다"; return; }
  v=$(tr -d '[:space:]' < "$f")
  [ "$v" = 0 ] && pass v1.rc "v1-rc.txt = 0" || fail v1.rc "v1-rc.txt = '$v' (0 이어야)"
}
check_v1_verdict() {
  local f="$EVIDENCE/codex-v1-${V1_SHA:0:7}.md" first
  [ -f "$f" ] || { fail v1.verdict "$f 없음"; return; }
  first=$(head -n 1 "$f")
  [ "$first" = "VERDICT: PASS" ] || { fail v1.verdict "첫 줄 '$first' ≠ 'VERDICT: PASS'"; return; }
  tail -n +2 "$f" | "$GREP" -qF -- "$V1_SHA" && pass v1.verdict "$f 첫 줄 PASS, 본문에 대상 SHA" \
    || fail v1.verdict "본문에 대상 SHA 전체가 없다 — 다른 SHA 의 판정이거나 SHA 미기재"
}
check_v1_venv_same() {
  local c="$SESSION/v1-clone" now
  [ -f "$SESSION/v1-venv-id.txt" ] && [ -d "$c/humansearch/.venv" ] || { fail v1.venv-same "세션 폴더에 v1-venv-id.txt 또는 v1-clone/.venv 가 없다(사전검사 미완)"; return; }
  now=$(fp_full "$c/humansearch/.venv")
  [ "$now" = "$(cat "$SESSION/v1-venv-id.txt")" ] || { fail v1.venv-same "V1 실행 뒤 클론 venv 지문이 달라졌다 — 판정의 출처가 다르다"; return; }
  [ -f "$S/probe/test_v1_clone_paths.py" ] || write_probe
  run_probe "$c" "$S/v1-probe-after.log" && pass v1.venv-same "VENV_SAME + 탐침 재실행 $PROBE_DETAIL" \
    || fail v1.venv-same "VENV_SAME 이지만 탐침 재실행 실패($PROBE_DETAIL)"
}

if [ "$MODE" = v1 ]; then
  [ -n "$SESSION" ] && [ -d "$SESSION" ] || die_blocked v1.session "--session 폴더가 없다: '$SESSION'"
  [ -n "$EVIDENCE" ] || EVIDENCE="$W/private-reviews/hs-0302"
  run_required v1.sha check_v1_sha
  run_required v1.head check_v1_head
  run_required v1.rc check_v1_rc
  run_required v1.verdict check_v1_verdict
  run_required v1.venv-same check_v1_venv_same
  finish
fi
HEAD_SHA=""
run_required git.worktree check_git_worktree
[ "$fails" -eq 0 ] && [ "$blocks" -eq 0 ] || finish
run_required git.branch check_git_branch
run_required git.clean check_git_clean
run_required git.base-ancestor check_git_base_ancestor
run_required git.prompt-tail check_git_prompt_tail
[ "$fails" -eq 0 ] && [ "$blocks" -eq 0 ] || finish
run_required proc.codex check_proc_codex
run_required proc.cwd check_proc_cwd
run_required shm.ledger check_shm_ledger
[ "$fails" -eq 0 ] && [ "$blocks" -eq 0 ] || finish
run_required ac2.copy check_ac2_copy
run_required ac3.clone check_ac3_clone
run_required shm.post check_shm_post
finish
