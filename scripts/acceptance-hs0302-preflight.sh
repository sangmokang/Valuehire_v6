#!/usr/bin/env bash
# acceptance-hs0302-preflight.sh — 마감 사전검사기가 실패 방향으로 닫혀 있는가 (HS-03.02 R6).
#
# 대상: scripts/verify/hs0302-closeout-preflight.sh (마감 프롬프트 0·2·5·7단계의 실행부).
# 차단 — 아래 반례 33종을 원본 밖 임시 사본에서 돌려 전부 거부돼야 한다. 기대값은 "통과 아님" 이 아니라 정확한 판정·종료값이다.
#   1 mktemp 실패 주입 → BLOCKED      2 git 조회 실패 주입 → BLOCKED (조회 실패는 대상 결함이 아니다)
#   3 빈 스크립트 → 거부               4 exit 0 만 → 거부
#   5 VERDICT: PASS 문구만 출력 → 거부  6 필수 검사 하나 삭제 → FAIL
#   7 자기 자신 재호출 → FAIL           8 V1 rc 파일 없음 → FAIL (증거 없는 주장은 채택하지 않는다)
#   9 V1 SHA 불일치 → FAIL
#   10~12 Codex V1(2026-09-17, e7a1a9a) 이 실제로 뚫은 경로의 회귀 봉인:
#   10 기준 조회 출력이 SHA 가 아님(rc 0 + NOT_A_SHA) → BLOCKED (e7a1a9a 는 이것을 PASS 로 접었다)
#   11 프롬프트 경로 미존재 → BLOCKED (e7a1a9a 는 FAIL 로 분류했다)
#   12 값 없는 옵션(--worktree 만) → FAIL 이되 CHECKED·VERDICT 꼬리가 있어야 한다 (e7a1a9a 는 꼬리 없이 죽었다)
#   13~15 Codex V1 2회차(f86d08b) 가 뚫은 경로의 회귀 봉인:
#   13 프롬프트 커밋 조회 출력이 SHA 가 아님 → BLOCKED   14 --check-v1 의 HEAD 조회 출력이 SHA 가 아님 → BLOCKED
#   15 V1 뒤 클론 venv 의 심볼릭 링크 대상만 바뀜 → --check-v1 FAIL (파일 전용 지문은 이것을 "동일" 로 봤다)
#   16 알 수 없는 인자(--bogus) → FAIL 이되 꼬리가 있어야 한다 (Codex V1 4회차: 이 분기의 꼬리를 지워도 시험이 초록이었다)
#   17 c 단계 도중 원본 venv 의 bin/python 링크 대상을 바꾸고 시각을 복원 → ac2.copy FAIL (codeaudit B1: 파일 전용 지문은 "불변" 으로 봤다)
#   18 d 단계 도중 SIGTERM → 표본기(ps 스냅샷)가 3초 안에 멈춰야 한다 (codeaudit B2: trap 이 없으면 고아가 워크트리 cwd 를 쥐고 영구 BLOCKED)
#   19 프롬프트 커밋 조회가 rc 0 + 빈 출력 → BLOCKED (Codex V1 5회차: 빈 값을 FAIL 로 보내던 별도 분기)
#   20~31 humanreview(c9dffa1) 변이 30종 중 생존 15종의 봉인 — "환경이 나쁠 때 잡는 검사" 마다 음성 대조군:
#   20 --check-v1 대상 SHA ≠ HEAD → FAIL   21 격리 클론의 객체가 원본과 하드링크(--no-local 부재) → 0 이어야
#   22 uv sync 로그에 새 설치 증거 없음 → FAIL   23 탐침이 OUTSIDE·1 failed → FAIL   24 src 에 symlink → FAIL(사본 링크 0 규칙)
#   25 복제가 하드링크로 이뤄짐 → FAIL   26 사본 모듈 realpath 가 사본 밖 → FAIL   27 존재하지 않는 --worktree → BLOCKED rc 2(die_blocked)
#   28 미커밋 변경 → FAIL(git.clean)   29 lsof 에 자기 셸 없음 → BLOCKED   30 공유메모리 30개 → BLOCKED   31 클론 venv 안에 원본 경로 → FAIL
#   32 --help 뒤에 다른 인자(--help --bogus) → FAIL 이되 꼬리가 있어야 한다 (Codex V1 8회차: 도움말이 뒤 인자를 검사하지 않고 rc 0 으로 끝났다)
#   33 값 자리에 다른 옵션(--worktree --help) → FAIL 이되 꼬리가 있어야 한다 (같은 회차: --help 를 경로 값으로 삼켜 BLOCKED 로 분류했다)
#   기록만(시험 없음): M04 신호 트랩 제거(EXIT 트랩만으로도 정지·PASS 부재 성립 — 부분 등가), M12 -newer 제거(지문이 mtime 포함 — 거의 등가),
#   M22 grep 자기검사, M25 클론에 .venv 사전 존재(합성 저장소에서 재현 불가).
# 통과 — 손대지 않은 사본은 고정 환경(합성 저장소 + 대역 명령)에서 PASS 여야 한다.
#   대역(uv·ps·lsof·ipcs)은 검사기의 판정 논리를 재기 위한 것이다. 실제 환경 실행은
#   마감 세션이 같은 검사기를 실제 워크트리에서 돌리는 것으로 증명한다(여기서 대신하지 않는다).
# 원본 저장소에는 아무것도 쓰지 않는다. 전후 `git status --porcelain` 을 대조한다.
set -uo pipefail
unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE GIT_OBJECT_DIRECTORY \
      GIT_ALTERNATE_OBJECT_DIRECTORIES GIT_COMMON_DIR GIT_PREFIX GIT_QUARANTINE_PATH
unset HS0302_PREFLIGHT_DEPTH

GREP=/usr/bin/grep
if [ ! -x "$GREP" ] || ! printf 'alpha\n' | "$GREP" -q 'alpha' || printf 'alpha\n' | "$GREP" -q 'beta'; then
  echo "NOT_RUN: $GREP 자기검사 실패 — 판정기를 신뢰할 수 없다"; echo "CHECKED: 0"; exit 2
fi
REPO=$(git rev-parse --show-toplevel 2>/dev/null) || {
  echo "NOT_RUN: git 저장소가 아니다"; echo "CHECKED: 0"; exit 2
}
cd "$REPO" || { echo "NOT_RUN: 저장소 이동 실패"; echo "CHECKED: 0"; exit 2; }

SCRIPT=scripts/verify/hs0302-closeout-preflight.sh
BRANCH=task/hs-0302-r6-survivor-defenses-20260916
BASE=task/hs-0302-candidate-identity-20260914
PROMPT=docs/engineering/goal-prompts/hs-0302-r6-next-prompt-2026-09-16.md
# 필수 검사 이름 — 검사기가 이 이름마다 `PASS: <이름>` 줄을 남겨야 PASS 로 인정한다.
REQ_FULL="git.worktree git.branch git.clean git.base-ancestor git.prompt-tail proc.codex proc.cwd shm.ledger ac2.copy ac3.clone shm.post"
REQ_V1="v1.sha v1.head v1.rc v1.verdict v1.venv-same"
SNAP0=$(git status --porcelain)
TMP=$(mktemp -d) || { echo "NOT_RUN: mktemp 실패"; echo "CHECKED: 0"; exit 2; }
# 검사기는 증거 보존을 위해 자기 세션 폴더(mktemp)를 지우지 않는다. 여기서는 사본 실행이 만든 세션 폴더를 모아 지운다.
SESSIONS="$TMP/sessions.txt"; : > "$SESSIONS"
cleanup() { while IFS= read -r d; do [ -n "$d" ] && [ -d "$d" ] && rm -rf "$d"; done < "$SESSIONS"; rm -rf "$TMP"; }
trap cleanup EXIT

fail=0
checked=0
record() {
  local ok="$1" desc="$2" detail="$3"
  checked=$((checked + 1))
  if [ "$ok" -eq 0 ]; then printf 'PASS: %s — %s\n' "$desc" "$detail"
  else printf 'FAIL: %s — %s\n' "$desc" "$detail"; fail=1; fi
}
finish() {
  local now
  now=$(git status --porcelain)
  if [ "$now" = "$SNAP0" ]; then record 0 "원본 저장소 상태 불변" "before/after 동일"
  else record 1 "원본 저장소 상태 불변" "변경 발생"; fi
  printf 'CHECKED: %d\n' "$checked"
  if [ "$fail" -eq 0 ]; then echo "VERDICT: PASS"; exit 0; fi
  echo "VERDICT: FAIL"; exit 1
}

if [ ! -f "$SCRIPT" ]; then
  record 1 "검사기 존재" "$SCRIPT 가 없다 — 마감 명령이 아직 프롬프트 산문에만 있다(RED)"
  finish
fi
record 0 "검사기 존재" "$SCRIPT"
if bash -n "$SCRIPT" 2>"$TMP/syntax.err"; then record 0 "검사기 bash -n" "구문 오류 없음"
else record 1 "검사기 bash -n" "$(head -1 "$TMP/syntax.err")"; fi

# ── 고정 환경: 합성 저장소 + 대역 명령 ─────────────────────────────────────────
WT="$TMP/wt"
build_fixture() {
  git init -q "$WT" && git -C "$WT" checkout -q -b "$BASE" || return 1
  git -C "$WT" config user.email acceptance@example.invalid
  git -C "$WT" config user.name acceptance
  git -C "$WT" config commit.gpgsign false
  mkdir -p "$WT/humansearch/src/humansearch" "$WT/humansearch/tests" "$WT/$(dirname "$PROMPT")" || return 1
  printf '[project]\nname = "humansearch"\n' > "$WT/humansearch/pyproject.toml"
  printf '[[package]]\nname = "a"\n\n[[package]]\nname = "b"\n' > "$WT/humansearch/uv.lock"
  printf 'X = 1\n' > "$WT/humansearch/src/humansearch/__init__.py"
  printf 'Y = 2\n' > "$WT/humansearch/src/humansearch/candidate_identity.py"
  printf 'def test_ok():\n    assert True\n' > "$WT/humansearch/tests/test_fixture.py"
  printf '.venv/\nprivate-reviews/\n' > "$WT/.gitignore"
  printf '# prompt v1\n' > "$WT/$PROMPT"
  git -C "$WT" add -A && git -C "$WT" commit -q -m base || return 1
  git -C "$WT" checkout -q -b "$BRANCH" || return 1
  printf '# prompt v2\n' >> "$WT/$PROMPT"
  git -C "$WT" commit -q -am prompt || return 1
  # 원본 워크트리의 .venv 대역(git 이 무시하는 경로) — AC-2 의 불변 확인 대상
  mkdir -p "$WT/humansearch/.venv/bin" "$WT/humansearch/.venv/lib/python3.14/site-packages" || return 1
  ln -s ../lib/python3.14 "$WT/humansearch/.venv/bin/python"
  printf '#!/bin/sh\nexec python "$@"\n' > "$WT/humansearch/.venv/bin/pytest"
  printf '%s/humansearch/src\n' "$WT" > "$WT/humansearch/.venv/lib/python3.14/site-packages/humansearch.pth"
  printf 'import _virtualenv\n' > "$WT/humansearch/.venv/lib/python3.14/site-packages/_virtualenv.pth"
}

STUB="$TMP/bin"
REAL_GIT=$(command -v git)
build_stubs() {
  mkdir -p "$STUB" "$TMP/bin-badmktemp" "$TMP/bin-badgit" || return 1
  cat > "$STUB/uv" <<'UV'
#!/usr/bin/env bash
# 대역 uv — sync: 클론 안에 .venv 를 만들고 설치 로그를 낸다 / run: 탐침·모듈 경로를 흉내 낸다
case "${1:-}" in
  sync)
    mkdir -p .venv/bin .venv/lib/python3.14/site-packages
    ln -s ../lib/python3.14 .venv/bin/python
    printf '#!/bin/sh\nexec python "$@"\n' > .venv/bin/pytest
    printf '%s/src\n' "$(pwd -P)" > .venv/lib/python3.14/site-packages/humansearch.pth
    printf 'import _virtualenv\n' > .venv/lib/python3.14/site-packages/_virtualenv.pth
    printf 'Resolved 2 packages\n + a==1.0\n + b==1.0\nInstalled 2 packages in 1ms\n'
    ;;
  run)
    case " $* " in
      *" pytest "*)
        c="${C:?C 미정의}"
        for k in sys.prefix sys.executable module pytest pytest-shebang .pth:humansearch.pth; do
          printf 'OK %s = %s/humansearch/.venv/x\n' "$k" "$c"
        done
        printf '1 passed in 0.01s\n'
        ;;
      *" python "*)
        printf '%s/candidate_identity.py\n' "$(cd "${PYTHONPATH:?}/humansearch" && pwd -P)"
        ;;
      *) echo "stub uv: unknown run form: $*" >&2; exit 9 ;;
    esac
    ;;
  *) echo "stub uv: unknown subcommand: $*" >&2; exit 9 ;;
esac
UV
  cat > "$STUB/ps" <<'PS'
#!/usr/bin/env bash
# 대역 ps — 호출한 검사기(부모)를 자기 셸로 보이게 하고, codex 프로세스는 없다
case "$*" in
  "-axo pid,ppid,command") printf '  PID  PPID COMMAND\n    1     0 /sbin/launchd\n%5d %5d bash\n' "$PPID" 1 ;;
  *) printf '    1     0 Wed Sep 17 03:00:00 2026\n%5d %5d Wed Sep 17 03:00:01 2026\n' "$PPID" 1 ;;
esac
PS
  cat > "$STUB/lsof" <<'LSOF'
#!/usr/bin/env bash
# 대역 lsof -d cwd -Fpcn — 호출한 검사기(부모)의 cwd 한 건 + 무관 프로세스 한 건
printf 'p%s\ncbash\nf cwd\nn%s\np1\nclaunchd\nf cwd\nn/\n' "$PPID" "$PWD"
LSOF
  cat > "$STUB/ipcs" <<'IPCS'
#!/usr/bin/env bash
# 대역 ipcs — 헤더는 있고 세그먼트는 0건
printf 'IPC status from <running system> as of now\nT     ID     KEY        MODE       OWNER    GROUP  CPID  LPID\nShared Memory:\n\n'
IPCS
  printf '#!/usr/bin/env bash\necho "mktemp: injected failure" >&2\nexit 1\n' > "$TMP/bin-badmktemp/mktemp"
  printf '#!/usr/bin/env bash\necho "fatal: injected git failure" >&2\nexit 128\n' > "$TMP/bin-badgit/git"
  # 반례 10: 기준 조회(rev-parse --verify <ref>^{commit})만 rc 0 으로 SHA 아닌 값을 내고 나머지는 실제 git 에 위임
  mkdir -p "$TMP/bin-notsha" "$TMP/bin-notsha-log" "$TMP/bin-notsha-head" || return 1
  printf '#!/usr/bin/env bash\ncase "$*" in *"rev-parse --verify "*"^{commit}"*) echo NOT_A_SHA; exit 0 ;; esac\nexec %s "$@"\n' "$REAL_GIT" > "$TMP/bin-notsha/git"
  # 반례 13·14: 프롬프트 커밋 조회(log -1 --format=%H) / HEAD 조회(rev-parse HEAD)만 rc 0 + NOT_A_SHA
  printf '#!/usr/bin/env bash\ncase "$*" in *"log -1 --format=%%H"*) echo NOT_A_SHA; exit 0 ;; esac\nexec %s "$@"\n' "$REAL_GIT" > "$TMP/bin-notsha-log/git"
  printf '#!/usr/bin/env bash\ncase "$*" in *"rev-parse HEAD"*) echo NOT_A_SHA; exit 0 ;; esac\nexec %s "$@"\n' "$REAL_GIT" > "$TMP/bin-notsha-head/git"
  mkdir -p "$TMP/bin-emptylog" && printf '#!/usr/bin/env bash\ncase "$*" in *"log -1 --format=%%H"*) exit 0 ;; esac\nexec %s "$@"\n' "$REAL_GIT" > "$TMP/bin-emptylog/git"
  # 반례 22·23·26·31: uv 대역 변형 — 하나의 동작만 나쁘게 하고 나머지는 기본 대역에 위임
  mkdir -p "$TMP/bin-copyvenv" "$TMP/bin-badprobe" "$TMP/bin-outsidemod" "$TMP/bin-leakpath" "$TMP/bin-noself" "$TMP/bin-shm30" "$TMP/bin-hardcp" || return 1
  printf '#!/usr/bin/env bash\ncase "${1:-}" in sync) "$(dirname "$0")/../bin/uv" "$@" >/dev/null; printf "Installed 1 package in 1ms\\n" ;; *) exec "$(dirname "$0")/../bin/uv" "$@" ;; esac\n' > "$TMP/bin-copyvenv/uv"
  printf '#!/usr/bin/env bash\ncase " $* " in *" pytest "*) printf "OUTSIDE sys.prefix = /elsewhere\\n1 failed in 0.01s\\n"; exit 1 ;; *) exec "$(dirname "$0")/../bin/uv" "$@" ;; esac\n' > "$TMP/bin-badprobe/uv"
  printf '#!/usr/bin/env bash\ncase " $* " in *" python "*) echo /elsewhere/humansearch/candidate_identity.py ;; *) exec "$(dirname "$0")/../bin/uv" "$@" ;; esac\n' > "$TMP/bin-outsidemod/uv"
  printf '#!/usr/bin/env bash\ncase "${1:-}" in sync) "$(dirname "$0")/../bin/uv" "$@"; git config --get remote.origin.url > .venv/leak.txt ;; *) exec "$(dirname "$0")/../bin/uv" "$@" ;; esac\n' > "$TMP/bin-leakpath/uv"
  # 반례 29: lsof 에 자기 셸이 없다(조회가 죽어 있음) / 반례 30: 공유메모리 세그먼트 30개
  printf '#!/usr/bin/env bash\nprintf "p1\\nclaunchd\\nf cwd\\nn/\\n"\n' > "$TMP/bin-noself/lsof"
  printf '#!/usr/bin/env bash\nprintf "IPC status\\nT     ID     KEY        MODE       OWNER    GROUP  CPID  LPID\\nShared Memory:\\n"; for i in $(seq 1 30); do printf "m %%d 0x0 --rw------- u g %%d 1 0 0 0 0 0 0 00:00:00 00:00:00 00:00:00\\n" "$((65536+i))" "$((1000+i))"; done\n' > "$TMP/bin-shm30/ipcs"
  # 반례 25: 복제가 하드링크로 이뤄진다(실제 cp 뒤 사본 파일을 원본의 하드링크로 교체)
  cat > "$TMP/bin-hardcp/cp" <<'HCP'
#!/usr/bin/env bash
/bin/cp "$@" || exit $?
args=(); for a in "$@"; do case "$a" in -*) ;; *) args+=("$a") ;; esac; done
n=${#args[@]}; [ "$n" -ge 2 ] || exit 0; dest="${args[$((n-1))]}"
for ((i=0; i<n-1; i++)); do src="${args[$i]}"
  if [ -f "$src" ]; then ln -f "$src" "$dest/$(basename "$src")"
  elif [ -d "$src" ]; then (cd "$src" && find . -type f) | while IFS= read -r rel; do ln -f "$src/$rel" "$dest/$(basename "$src")/$rel"; done; fi
done
HCP
  # 반례 17: c 단계의 uv run(모듈 로드) 사이에 원본 venv 링크 대상을 바꾸고 링크·부모 폴더 시각을 복원(-newer 검사를 피하는 공격 형태)
  mkdir -p "$TMP/bin-venvswap" && cat > "$TMP/bin-venvswap/uv" <<'SWAP'
#!/usr/bin/env bash
w=""; prev=""; for a in "$@"; do [ "$prev" = "--project" ] && w="$a"; prev="$a"; done
case " $* " in *" python "*) if [ -n "$w" ] && [ -L "$w/.venv/bin/python" ]; then
  ln -sfn ../lib "$w/.venv/bin/python"; touch -h -r "$w/pyproject.toml" "$w/.venv/bin/python"; touch -r "$w/pyproject.toml" "$w/.venv/bin"; fi ;; esac
exec "$(dirname "$0")/../bin/uv" "$@"
SWAP
  # 반례 18: d 단계의 uv run pytest 를 6초 늦춰 SIGTERM 을 보낼 창을 만든다
  mkdir -p "$TMP/bin-slow" && printf '#!/usr/bin/env bash\ncase " $* " in *" pytest "*) sleep 6 ;; esac\nexec "$(dirname "$0")/../bin/uv" "$@"\n' > "$TMP/bin-slow/uv"
  chmod +x "$STUB"/* "$TMP/bin-badmktemp/mktemp" "$TMP/bin-badgit/git" "$TMP/bin-notsha/git" "$TMP/bin-notsha-log/git" "$TMP/bin-notsha-head/git" "$TMP/bin-emptylog/git" "$TMP/bin-venvswap/uv" "$TMP/bin-slow/uv" "$TMP"/bin-copyvenv/uv "$TMP"/bin-badprobe/uv "$TMP"/bin-outsidemod/uv "$TMP"/bin-leakpath/uv "$TMP"/bin-noself/lsof "$TMP"/bin-shm30/ipcs "$TMP"/bin-hardcp/cp
}

if build_fixture && build_stubs; then record 0 "고정 환경 준비" "합성 저장소 $WT, 대역 uv·ps·lsof·ipcs"
else record 1 "고정 환경 준비" "합성 저장소 또는 대역 생성 실패"; finish; fi
STUB_PATH="$STUB:$PATH"

# ── 판정: 사본을 돌리고 출력 꼬리(CHECKED·VERDICT)와 필수 PASS 줄로 판정한다 ────
# accepted(사본) = rc 0 이고 마지막 두 줄이 CHECKED: N(N≥1)·VERDICT: PASS 이며 필수 이름마다 PASS 줄이 있다.
case_no=0; CASE_OUT=""
run_case() {
  local name="$1" expect="$2" copy="$3" req="$4" path="$5"; shift 5
  local out rc=0 last prev n verdict=NONE accepted=0 missing=""
  case_no=$((case_no + 1)); out="$TMP/out-$case_no.txt"; CASE_OUT="$out"
  (cd "$TMP" && PATH="$path" bash "$copy" "$@") > "$out" 2>&1 || rc=$?
  sed -n 's/^SESSION_DIR=//p' "$out" >> "$SESSIONS"
  last=$(tail -n 1 "$out"); prev=$(tail -n 2 "$out" | head -n 1)
  case "$last" in "VERDICT: "*) verdict=${last#VERDICT: } ;; esac
  n=$(printf '%s' "$prev" | sed -n 's/^CHECKED: \([0-9][0-9]*\)$/\1/p')
  for r in $req; do
    "$GREP" -qE "^PASS: $(printf '%s' "$r" | sed 's/\./\\./g')( |$)" "$out" || missing="$missing $r"
  done
  if [ "$rc" -eq 0 ] && [ "$verdict" = PASS ] && [ -n "$n" ] && [ "$n" -ge 1 ] && [ -z "$missing" ]; then accepted=1; fi
  case "$expect" in
    PASS)    [ "$accepted" -eq 1 ] ;;
    REJECT)  [ "$accepted" -eq 0 ] ;;
    FAIL)    [ "$rc" -eq 1 ] && [ "$verdict" = FAIL ] && [ -n "$n" ] ;;
    BLOCKED) [ "$rc" -eq 2 ] && [ "$verdict" = BLOCKED ] && [ -n "$n" ] ;;
    FAIL_OR_BLOCKED) { [ "$rc" -eq 1 ] && [ "$verdict" = FAIL ]; } || { [ "$rc" -eq 2 ] && [ "$verdict" = BLOCKED ]; } ;;
    *) false ;;
  esac
  local ok=$?
  record "$ok" "$name" "기대 $expect / 관측 rc=$rc VERDICT=$verdict CHECKED=${n:-없음}${missing:+ 누락:$missing}"
  return "$ok"
}

# 사본 생성: 정확히 1곳이 바뀌었는지 확인하고, 아니면 사본을 만들지 않는다(변이 실패를 통과로 접지 않는다)
mutate() {
  local name="$1" mode="$2" needle="$3" copy hits
  copy="$TMP/mut-$name.sh"
  case "$mode" in
    delete-line)
      hits=$("$GREP" -c -- "$needle" "$SCRIPT")
      [ "$hits" -eq 1 ] || { echo "MUTATE_FAIL $name: 대상 줄이 ${hits}개 (1이어야)"; return 1; }
      "$GREP" -v -- "$needle" "$SCRIPT" > "$copy" ;;
    insert-after)
      hits=$("$GREP" -c -- "$needle" "$SCRIPT")
      [ "$hits" -eq 1 ] || { echo "MUTATE_FAIL $name: 기준 줄이 ${hits}개 (1이어야)"; return 1; }
      awk -v pat="$needle" -v ins="$4" '{print} index($0, pat)==1 {print ins}' "$SCRIPT" > "$copy" ;;
    *) return 1 ;;
  esac
  printf '%s\n' "$copy"
}

FULL_ARGS=(--worktree "$WT" --branch "$BRANCH" --base "$BASE" --prompt "$PROMPT")
cp "$SCRIPT" "$TMP/pristine.sh"

# 통과 쪽 — 정상 사본은 고정 환경에서 PASS 여야 한다(이 결과의 세션 폴더를 V1 검사에 재사용한다)
run_case "정상 사본 PASS(전체)" PASS "$TMP/pristine.sh" "$REQ_FULL" "$STUB_PATH" "${FULL_ARGS[@]}"
SESSION=$(sed -n 's/^SESSION_DIR=//p' "$CASE_OUT" | tail -1)
if [ -n "$SESSION" ] && [ -d "$SESSION" ] && [ -f "$SESSION/v1-venv-id.txt" ]; then
  record 0 "세션 폴더·venv 지문 산출" "$SESSION"
else
  record 1 "세션 폴더·venv 지문 산출" "SESSION_DIR 줄 또는 v1-venv-id.txt 없음"
fi

# 1 mktemp 실패 주입 → BLOCKED (검증 환경을 못 만든 것이지 대상이 틀린 게 아니다)
run_case "반례1 mktemp 실패 → BLOCKED" BLOCKED "$TMP/pristine.sh" "" "$TMP/bin-badmktemp:$STUB_PATH" "${FULL_ARGS[@]}"
# 2 git 조회 실패 주입 → BLOCKED (조회 실패를 '변경 0건' 으로 접지 않고, 대상 결함으로도 분류하지 않는다)
run_case "반례2 git 조회 실패 → BLOCKED" BLOCKED "$TMP/pristine.sh" "" "$TMP/bin-badgit:$STUB_PATH" "${FULL_ARGS[@]}"
# 3 빈 스크립트 → 거부
printf '#!/usr/bin/env bash\n' > "$TMP/mut-empty.sh"
run_case "반례3 빈 스크립트 → 거부" REJECT "$TMP/mut-empty.sh" "$REQ_FULL" "$STUB_PATH" "${FULL_ARGS[@]}"
# 4 exit 0 만 → 거부
printf '#!/usr/bin/env bash\nexit 0\n' > "$TMP/mut-exit0.sh"
run_case "반례4 exit 0 만 → 거부" REJECT "$TMP/mut-exit0.sh" "$REQ_FULL" "$STUB_PATH" "${FULL_ARGS[@]}"
# 5 VERDICT: PASS 문구만 → 거부 (필수 이름별 PASS 줄이 없다)
printf '#!/usr/bin/env bash\necho "CHECKED: 11"\necho "VERDICT: PASS"\nexit 0\n' > "$TMP/mut-verdict-only.sh"
run_case "반례5 VERDICT 문구만 → 거부" REJECT "$TMP/mut-verdict-only.sh" "$REQ_FULL" "$STUB_PATH" "${FULL_ARGS[@]}"
# 6 필수 검사 하나 삭제 → FAIL (검사기 자신의 장부가 누락을 잡아야 한다)
if copy=$(mutate required-deleted delete-line 'run_required git.clean check_git_clean'); then
  run_case "반례6 필수 검사 삭제 → FAIL" FAIL "$copy" "" "$STUB_PATH" "${FULL_ARGS[@]}"
else record 1 "반례6 필수 검사 삭제 → FAIL" "$copy"; fi
# 7 자기 자신 재호출 → FAIL (깊이 표식이 있으면 통과가 아니라 실패)
if copy=$(mutate self-reinvoke insert-after 'export HS0302_PREFLIGHT_DEPTH' 'bash "$0" "$@"; exit $?'); then
  run_case "반례7 자기 재호출 → FAIL" FAIL "$copy" "" "$STUB_PATH" "${FULL_ARGS[@]}"
else record 1 "반례7 자기 재호출 → FAIL" "$copy"; fi

# 10 기준 조회 출력이 SHA 가 아님 → BLOCKED (조회 계층 오염을 PASS 로 접지 않는다)
run_case "반례10 기준 조회 출력 비SHA → BLOCKED" BLOCKED "$TMP/pristine.sh" "" "$TMP/bin-notsha:$STUB_PATH" "${FULL_ARGS[@]}"
# 11 프롬프트 경로 미존재 → BLOCKED (검증 입력 부재는 대상 결함이 아니다)
run_case "반례11 프롬프트 경로 미존재 → BLOCKED" BLOCKED "$TMP/pristine.sh" "" "$STUB_PATH" --worktree "$WT" --branch "$BRANCH" --base "$BASE" --prompt docs/engineering/goal-prompts/does-not-exist.md
# 12 값 없는 옵션 → FAIL 이되 꼬리(CHECKED·VERDICT)가 있어야 한다
run_case "반례12 옵션 값 누락 → FAIL(꼬리 있음)" FAIL "$TMP/pristine.sh" "" "$STUB_PATH" --worktree
# 16 알 수 없는 인자 → FAIL 이되 꼬리(CHECKED·VERDICT)가 있어야 한다
run_case "반례16 알 수 없는 인자 → FAIL(꼬리 있음)" FAIL "$TMP/pristine.sh" "" "$STUB_PATH" --bogus
# 32 --help 뒤 다른 인자 → FAIL(꼬리 있음). 단독 --help 는 도움말(rc 0)이 맞다.
run_case "반례32 --help 뒤 인자 → FAIL(꼬리 있음)" FAIL "$TMP/pristine.sh" "" "$STUB_PATH" --help --bogus
# 33 값 자리에 다른 옵션 → FAIL(값 누락, 꼬리 있음)
run_case "반례33 값 자리에 다른 옵션 → FAIL(꼬리 있음)" FAIL "$TMP/pristine.sh" "" "$STUB_PATH" --worktree --help
# 19 프롬프트 커밋 조회 rc 0 + 빈 출력 → BLOCKED
run_case "반례19 프롬프트 커밋 조회 빈 출력 → BLOCKED" BLOCKED "$TMP/pristine.sh" "" "$TMP/bin-emptylog:$STUB_PATH" "${FULL_ARGS[@]}"
# 21 격리 클론의 git 객체가 원본과 하드링크면 --no-local 이 빠진 것이다(정상 세션 폴더로 확인)
hl=$(find "${SESSION:-$TMP/no-session}/v1-clone/.git/objects" -type f -links +1 2>>"$TMP/hl.err" | wc -l | tr -d ' ')
if [ -d "${SESSION:-}/v1-clone/.git/objects" ] && [ "$hl" = 0 ]; then record 0 "반례21 클론 객체 하드링크 0(--no-local)" "links+1 = $hl"
else record 1 "반례21 클론 객체 하드링크 0(--no-local)" "links+1 = ${hl:-없음} (0 이어야; 0 이 아니면 원본 저장소와 객체를 공유한다)"; fi
# 22 새 설치 증거 없음(Installed 1 package 만) → FAIL / 23 탐침 OUTSIDE·1 failed → FAIL / 26 사본 모듈 realpath 사본 밖 → FAIL / 31 클론 venv 안 원본 경로 → FAIL
run_case "반례22 새 venv 설치 증거 없음 → FAIL" FAIL "$TMP/pristine.sh" "" "$TMP/bin-copyvenv:$STUB_PATH" "${FULL_ARGS[@]}"
run_case "반례23 탐침 OUTSIDE·1 failed → FAIL" FAIL "$TMP/pristine.sh" "" "$TMP/bin-badprobe:$STUB_PATH" "${FULL_ARGS[@]}"
run_case "반례26 사본 모듈 realpath 사본 밖 → FAIL" FAIL "$TMP/pristine.sh" "" "$TMP/bin-outsidemod:$STUB_PATH" "${FULL_ARGS[@]}"
run_case "반례31 클론 venv 안 원본 경로 → FAIL" FAIL "$TMP/pristine.sh" "" "$TMP/bin-leakpath:$STUB_PATH" "${FULL_ARGS[@]}"
# 24 src 안 symlink(git 이 무시하는 이름) → 사본 링크 0 규칙으로 FAIL
printf '*.local\n' >> "$WT/.git/info/exclude"; ln -s __init__.py "$WT/humansearch/src/humansearch/x.local"   # 커밋하지 않는다(커밋하면 git.prompt-tail 이 먼저 FAIL 한다)
run_case "반례24 src 안 symlink → FAIL" FAIL "$TMP/pristine.sh" "" "$STUB_PATH" "${FULL_ARGS[@]}"
rm -f "$WT/humansearch/src/humansearch/x.local"
# 25 복제가 하드링크로 이뤄짐 → FAIL(사본 hardlink 0 규칙)
run_case "반례25 복제가 하드링크 → FAIL" FAIL "$TMP/pristine.sh" "" "$TMP/bin-hardcp:$STUB_PATH" "${FULL_ARGS[@]}"
# 27 존재하지 않는 --worktree → BLOCKED rc 2 (die_blocked 계약) / 29 lsof 에 자기 셸 없음 → BLOCKED / 30 공유메모리 30개 → BLOCKED
run_case "반례27 존재하지 않는 워크트리 → BLOCKED" BLOCKED "$TMP/pristine.sh" "" "$STUB_PATH" --worktree "$TMP/does-not-exist"
run_case "반례29 lsof 자기 셸 없음 → BLOCKED" BLOCKED "$TMP/pristine.sh" "" "$TMP/bin-noself:$STUB_PATH" "${FULL_ARGS[@]}"
run_case "반례30 공유메모리 30개 → BLOCKED" BLOCKED "$TMP/pristine.sh" "" "$TMP/bin-shm30:$STUB_PATH" "${FULL_ARGS[@]}"
# 28 미커밋 변경 → FAIL(git.clean)
printf 'dirty\n' > "$WT/dirty.txt"; run_case "반례28 미커밋 변경 → FAIL" FAIL "$TMP/pristine.sh" "" "$STUB_PATH" "${FULL_ARGS[@]}"; rm -f "$WT/dirty.txt"
# 17 c 단계 도중 원본 venv 링크 교체(시각 복원) → FAIL
run_case "반례17 원본 venv 링크 교체 → FAIL" FAIL "$TMP/pristine.sh" "" "$TMP/bin-venvswap:$STUB_PATH" "${FULL_ARGS[@]}"
if [ "$(readlink "$WT/humansearch/.venv/bin/python")" = "../lib" ]; then ln -sfn ../lib/python3.14 "$WT/humansearch/.venv/bin/python"; fi
# 18 d 단계 도중 SIGTERM → 표본기가 멈춰야 한다(고아가 남으면 다음 실행이 영구 BLOCKED)
sig_out="$TMP/out-sigterm.txt"; (cd "$TMP" && PATH="$TMP/bin-slow:$STUB_PATH" exec bash "$TMP/pristine.sh" "${FULL_ARGS[@]}") > "$sig_out" 2>&1 & sig_pid=$!
for _ in $(seq 1 100); do "$GREP" -q '^PASS: ac2.copy' "$sig_out" 2>/dev/null && break; sleep 0.1; done
sig_s=$(sed -n 's/^SESSION_DIR=//p' "$sig_out" | tail -1); printf '%s\n' "$sig_s" >> "$SESSIONS"
kill_rc=0; kill -TERM "$sig_pid" 2>>"$TMP/sig.err" || kill_rc=$?; sig_rc=0; wait "$sig_pid" 2>>"$TMP/sig.err" || sig_rc=$?; sleep 3
size1=$(wc -c < "$sig_s/ps-snap.txt" 2>>"$TMP/sig.err" | tr -d ' '); sleep 2.5; size2=$(wc -c < "$sig_s/ps-snap.txt" 2>>"$TMP/sig.err" | tr -d ' ')
sig_last=$(tail -n 1 "$sig_out"); sig_prev=$(tail -n 2 "$sig_out" | head -n 1)
# 정리(표본기 정지)만이 아니라 결과 계약도 요구한다: kill 성공, 종료값 2, 마지막 두 줄 CHECKED·VERDICT: BLOCKED (Codex 적대 리뷰 D1: 꼬리 없는 종료·FAIL 종료가 살아남았다)
if [ -n "$sig_s" ] && [ -f "$sig_s/ps-snap.txt" ] && [ "$size1" = "$size2" ] && [ "$kill_rc" -eq 0 ] && [ "$sig_rc" -eq 2 ] \
   && [ "$sig_last" = "VERDICT: BLOCKED" ] && printf '%s' "$sig_prev" | "$GREP" -qE '^CHECKED: [0-9]+$'; then
  record 0 "반례18 SIGTERM 뒤 표본기 정지·BLOCKED 꼬리" "ps-snap ${size1}B 로 정지(2.5초 불변), rc=$sig_rc, 꼬리 '$sig_prev' / '$sig_last'"
else
  record 1 "반례18 SIGTERM 뒤 표본기 정지·BLOCKED 꼬리" "ps-snap ${size1:-없음}→${size2:-없음}B, kill_rc=$kill_rc rc=$sig_rc 꼬리 '${sig_prev}' / '${sig_last}', 세션 ${sig_s:-없음}"
  lsof -t "$sig_s/ps-snap.txt" 2>>"$TMP/sig.err" | xargs kill 2>>"$TMP/sig.err"
fi
# 13 프롬프트 커밋 조회 출력이 SHA 가 아님 → BLOCKED (기준 조회만 막고 다른 조회를 두면 같은 오염이 FAIL 로 갈린다)
run_case "반례13 프롬프트 커밋 조회 비SHA → BLOCKED" BLOCKED "$TMP/pristine.sh" "" "$TMP/bin-notsha-log:$STUB_PATH" "${FULL_ARGS[@]}"

# ── V1 증거 검사(--check-v1): 정상 → PASS, rc 파일 없음 → FAIL/BLOCKED, SHA 불일치 → FAIL ──
SHA=$(git -C "$WT" rev-parse HEAD)
EV="$WT/private-reviews/hs-0302"
V1_ARGS=(--worktree "$WT" --session "${SESSION:-$TMP/no-session}" --evidence-dir "$EV")
write_v1_evidence() {
  local sha_in_body="$1"
  rm -rf "$EV" && mkdir -p "$EV" || return 1
  printf 'VERDICT: PASS\n\n## 결론\n대상 SHA %s 에 대한 판정이다.\n' "$sha_in_body" > "$EV/codex-v1-${SHA:0:7}.md"
  printf '0\n' > "$EV/v1-rc.txt"
}
if write_v1_evidence "$SHA"; then
  run_case "정상 V1 증거 PASS(--check-v1)" PASS "$TMP/pristine.sh" "$REQ_V1" "$STUB_PATH" --check-v1 "$SHA" "${V1_ARGS[@]}"
  # 14 --check-v1 의 HEAD 조회 출력이 SHA 가 아님 → BLOCKED
  run_case "반례14 V1 HEAD 조회 비SHA → BLOCKED" BLOCKED "$TMP/pristine.sh" "" "$TMP/bin-notsha-head:$STUB_PATH" --check-v1 "$SHA" "${V1_ARGS[@]}"
  # 8 V1 rc 파일 없음
  rm -f "$EV/v1-rc.txt"
  run_case "반례8 V1 rc 파일 없음 → FAIL" FAIL "$TMP/pristine.sh" "" "$STUB_PATH" --check-v1 "$SHA" "${V1_ARGS[@]}"
else record 1 "정상 V1 증거 PASS(--check-v1)" "증거 파일 생성 실패"; fi
# 20 --check-v1 대상 SHA 가 HEAD 가 아니다(다른 커밋의 완전한 증거) → FAIL(v1.head)
BASE_SHA=$(git -C "$WT" rev-parse "$BASE")
if [ -n "$BASE_SHA" ] && mkdir -p "$EV" && printf 'VERDICT: PASS\n\n대상 SHA %s\n' "$BASE_SHA" > "$EV/codex-v1-${BASE_SHA:0:7}.md" && printf '0\n' > "$EV/v1-rc.txt"; then
  run_case "반례20 V1 대상 SHA ≠ HEAD → FAIL" FAIL "$TMP/pristine.sh" "" "$STUB_PATH" --check-v1 "$BASE_SHA" "${V1_ARGS[@]}"
else record 1 "반례20 V1 대상 SHA ≠ HEAD → FAIL" "증거 준비 실패"; fi
# 9 V1 SHA 불일치 → FAIL (판정 본문의 SHA 가 대상과 다르다)
OTHER_SHA=$(printf '%s' "$SHA" | tr '0123456789abcdef' '123456789abcdef0')
if write_v1_evidence "$OTHER_SHA"; then
  run_case "반례9 V1 SHA 불일치 → FAIL" FAIL "$TMP/pristine.sh" "" "$STUB_PATH" --check-v1 "$SHA" "${V1_ARGS[@]}"
else record 1 "반례9 V1 SHA 불일치 → FAIL" "증거 파일 생성 실패"; fi
# 15 V1 뒤 클론 venv 의 심볼릭 링크 대상만 바뀜 → FAIL (파일은 그대로, 실행기 링크만 다른 곳을 가리킨다)
LINK="${SESSION:-$TMP/no-session}/v1-clone/humansearch/.venv/bin/python"
if write_v1_evidence "$SHA" && [ -L "$LINK" ] && ln -sfn ../lib "$LINK"; then
  run_case "반례15 V1 뒤 venv 링크 대상 변경 → FAIL" FAIL "$TMP/pristine.sh" "" "$STUB_PATH" --check-v1 "$SHA" "${V1_ARGS[@]}"
else record 1 "반례15 V1 뒤 venv 링크 대상 변경 → FAIL" "링크 $LINK 준비 실패"; fi

# 검사기 자체 크기(P11① hard 600) — 한도 안이어야 한다
lines=$(wc -l < "$SCRIPT" | tr -d ' ')
if [ "$lines" -le 600 ]; then record 0 "검사기 줄수 ≤ 600" "$lines 줄"
else record 1 "검사기 줄수 ≤ 600" "$lines 줄"; fi

finish
