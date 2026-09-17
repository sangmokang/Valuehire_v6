#!/usr/bin/env bash
# acceptance-hs0302-preflight.sh — 마감 사전검사기가 실패 방향으로 닫혀 있는가 (HS-03.02 R6).
#
# 대상: scripts/verify/hs0302-closeout-preflight.sh (마감 프롬프트 0·2·5·7단계의 실행부).
# 차단 — 아래 반례 9종을 원본 밖 임시 사본에서 돌려 전부 거부돼야 한다.
#   1 mktemp 실패 주입 → BLOCKED      2 git 조회 실패 주입 → FAIL 또는 BLOCKED
#   3 빈 스크립트 → 거부               4 exit 0 만 → 거부
#   5 VERDICT: PASS 문구만 출력 → 거부  6 필수 검사 하나 삭제 → FAIL
#   7 자기 자신 재호출 → FAIL           8 V1 rc 파일 없음 → FAIL 또는 BLOCKED
#   9 V1 SHA 불일치 → FAIL
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
trap 'rm -rf "$TMP"' EXIT

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
  printf '#!/bin/sh\nexec python "$@"\n' > "$WT/humansearch/.venv/bin/pytest"
  printf '%s/humansearch/src\n' "$WT" > "$WT/humansearch/.venv/lib/python3.14/site-packages/humansearch.pth"
  printf 'import _virtualenv\n' > "$WT/humansearch/.venv/lib/python3.14/site-packages/_virtualenv.pth"
}

STUB="$TMP/bin"
build_stubs() {
  mkdir -p "$STUB" "$TMP/bin-badmktemp" "$TMP/bin-badgit" || return 1
  cat > "$STUB/uv" <<'UV'
#!/usr/bin/env bash
# 대역 uv — sync: 클론 안에 .venv 를 만들고 설치 로그를 낸다 / run: 탐침·모듈 경로를 흉내 낸다
case "${1:-}" in
  sync)
    mkdir -p .venv/bin .venv/lib/python3.14/site-packages
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
  chmod +x "$STUB"/* "$TMP/bin-badmktemp/mktemp" "$TMP/bin-badgit/git"
}

if build_fixture && build_stubs; then record 0 "고정 환경 준비" "합성 저장소 $WT, 대역 uv·ps·lsof·ipcs"
else record 1 "고정 환경 준비" "합성 저장소 또는 대역 생성 실패"; finish; fi
STUB_PATH="$STUB:$PATH"

# ── 판정: 사본을 돌리고 출력 꼬리(CHECKED·VERDICT)와 필수 PASS 줄로 판정한다 ────
# accepted(사본) = rc 0 이고 마지막 두 줄이 CHECKED: N(N≥1)·VERDICT: PASS 이며 필수 이름마다 PASS 줄이 있다.
run_case() {
  local name="$1" expect="$2" copy="$3" req="$4" path="$5"; shift 5
  local out="$TMP/out-$name.txt" rc=0 last prev n verdict=NONE accepted=0 missing=""
  (cd "$TMP" && PATH="$path" bash "$copy" "$@") > "$out" 2>&1 || rc=$?
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
  local name="$1" mode="$2" needle="$3" copy="$TMP/mut-$name.sh" hits
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
SESSION=$(sed -n 's/^SESSION_DIR=//p' "$TMP/out-정상 사본 PASS(전체).txt" | tail -1)
if [ -n "$SESSION" ] && [ -d "$SESSION" ] && [ -f "$SESSION/v1-venv-id.txt" ]; then
  record 0 "세션 폴더·venv 지문 산출" "$SESSION"
else
  record 1 "세션 폴더·venv 지문 산출" "SESSION_DIR 줄 또는 v1-venv-id.txt 없음"
fi

# 1 mktemp 실패 주입 → BLOCKED (검증 환경을 못 만든 것이지 대상이 틀린 게 아니다)
run_case "반례1 mktemp 실패 → BLOCKED" BLOCKED "$TMP/pristine.sh" "" "$TMP/bin-badmktemp:$STUB_PATH" "${FULL_ARGS[@]}"
# 2 git 조회 실패 주입 → FAIL/BLOCKED (조회 실패를 '변경 0건' 으로 접지 않는다)
run_case "반례2 git 조회 실패 → FAIL/BLOCKED" FAIL_OR_BLOCKED "$TMP/pristine.sh" "" "$TMP/bin-badgit:$STUB_PATH" "${FULL_ARGS[@]}"
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
  # 8 V1 rc 파일 없음
  rm -f "$EV/v1-rc.txt"
  run_case "반례8 V1 rc 파일 없음 → FAIL/BLOCKED" FAIL_OR_BLOCKED "$TMP/pristine.sh" "" "$STUB_PATH" --check-v1 "$SHA" "${V1_ARGS[@]}"
else record 1 "정상 V1 증거 PASS(--check-v1)" "증거 파일 생성 실패"; fi
# 9 V1 SHA 불일치 → FAIL (판정 본문의 SHA 가 대상과 다르다)
OTHER_SHA=$(printf '%s' "$SHA" | tr '0123456789abcdef' '123456789abcdef0')
if write_v1_evidence "$OTHER_SHA"; then
  run_case "반례9 V1 SHA 불일치 → FAIL" FAIL "$TMP/pristine.sh" "" "$STUB_PATH" --check-v1 "$SHA" "${V1_ARGS[@]}"
else record 1 "반례9 V1 SHA 불일치 → FAIL" "증거 파일 생성 실패"; fi

# 검사기 자체 크기(P11① hard 600) — 한도 안이어야 한다
lines=$(wc -l < "$SCRIPT" | tr -d ' ')
if [ "$lines" -le 600 ]; then record 0 "검사기 줄수 ≤ 600" "$lines 줄"
else record 1 "검사기 줄수 ≤ 600" "$lines 줄"; fi

finish
