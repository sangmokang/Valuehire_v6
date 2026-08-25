#!/usr/bin/env bash
# acceptance-task-done.sh — `make task-done` 이 워크트리 폐기 전에 무시된 산출물을 회수시키는가.
#
# 계약: docs/engineering/task-done-ignored-artifact-gate-goal-2026-08-26.md (AC-1)
#   출력  : PASS/FAIL 줄 + `CHECKED: N`. exit 0(전부 충족) | 1(위반) | 2(시험 자체 불능)
#   불변식: 조용한 통과 금지. 원본 저장소를 건드리지 않는다.
#
# 왜 "차단된다"만 재면 안 되는가 (2026-08-26 Codex 1차 심사 Q8):
#   차단 사례 하나만 두면 `Makefile` 이 없어 `make` 가 실패하는 것까지 "차단 성공"으로 집계된다.
#   구현이 0줄이어도 초록이 되는 가짜 RED 다. 그래서 **정상 삭제 대조군(C1·C2)** 을 함께 잰다.
#   차단과 통과를 한 쌍으로 재는 것은 이 저장소의 게이트 설계 원칙이다.
#
# 왜 원본이 아니라 임시 저장소인가:
#   실 워크트리에는 사장님의 판정서가 들어 있다. 인수 검사가 그것을 지우거나, 반대로 실 상태에
#   의존해 판정이 흔들리면 검사기 자신이 오염원이 된다. fixture 는 전부 mktemp 아래에서 만든다.
set -uo pipefail

unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE GIT_OBJECT_DIRECTORY \
      GIT_ALTERNATE_OBJECT_DIRECTORIES GIT_COMMON_DIR GIT_PREFIX GIT_QUARANTINE_PATH

REPO=$(git rev-parse --show-toplevel) || {
  echo "NOT_RUN: git 저장소가 아니다"
  echo "CHECKED: 0"
  exit 2
}
cd "$REPO" || exit 2

SNAPSHOT=$(git status --porcelain)

TMP=$(mktemp -d) || {
  echo "NOT_RUN: mktemp 실패 — 격리 없이는 시험하지 않는다"
  echo "CHECKED: 0"
  exit 2
}
trap 'chmod -R u+w "$TMP" >/dev/null 2>&1; rm -rf "$TMP"' EXIT

fail=0
checked=0

# ── fixture 이름·경로를 실행마다 바꾼다 ──────────────────────────────────────
#
# 왜 (2026-08-26 V1 자체 공격에서 실증):
#   워크트리 이름과 파일 경로를 고정해 두면, 검사를 전혀 하지 않고 그 이름만 보고
#   정답을 흉내내는 위조본이 통과한다. 실측: 아래 위조본이 16/16 PASS · exit 0.
#     case "$1" in
#       clean|cacheonly|directok) echo "STATE: OK"; git worktree remove ...; exit 0 ;;
#       artifact) echo "STATE: BLOCK"; echo "artifacts/keep.txt"; exit 1 ;;
#     esac
#   run-acceptance.sh 는 자기 주석에서 "문구 위조는 막지 못한다"고 자백한다.
#   그 구멍을 여기서 좁힌다 — 정답을 미리 알 수 없게 만들면 흉내낼 수가 없다.
RUNID="$$-${RANDOM}-${RANDOM}"
WT_CLEAN="clean-$RUNID"
WT_CACHE="cacheonly-$RUNID"
WT_RECOVER="recover-$RUNID"
WT_REVIEW="review-$RUNID"
WT_DIRECT="directok-$RUNID"

# 회수 대상 디렉터리도 P12·P21 이 명시한 넷 중에서 매번 고른다.
RECOVER_DIRS=(private-reviews artifacts data .harness)
RECOVER_DIR="${RECOVER_DIRS[$((RANDOM % 4))]}"
RECOVER_FILE="$RECOVER_DIR/keep-$RUNID.md"
REVIEW_FILE=".toolstate/session-$RUNID.json"

record() {
  local ok="$1" desc="$2" detail="$3"
  checked=$((checked + 1))
  if [ "$ok" -eq 0 ]; then
    printf 'PASS: %s — %s\n' "$desc" "$detail"
  else
    printf 'FAIL: %s — %s\n' "$desc" "$detail"
    fail=1
  fi
}

# ── fixture: 통제된 .gitignore 를 가진 독립 저장소 ────────────────────────────
# 원본의 .gitignore 를 복사하지 않는다. `.omx/` 처럼 .git/info/exclude(커밋 안 되는 로컬
# 파일)로 무시되는 항목이 있어 머신마다 결과가 달라지기 때문이다(2026-08-26 실측).
make_fixture() {
  local root="$1"
  mkdir -p "$root" || return 1
  git init -q "$root" || return 1
  git -C "$root" config user.email "acceptance@local" || return 1
  git -C "$root" config user.name "acceptance" || return 1
  git -C "$root" config commit.gpgsign false || return 1

  cat > "$root/.gitignore" <<'IGN'
artifacts/
private-reviews/
data/
.harness/
.ruff_cache/
.venv/
.toolstate/
IGN

  mkdir -p "$root/scripts"
  # 시험 대상 = 이 저장소의 실제 구현. 없으면 없는 채로 복사하지 않는다(그게 RED 다).
  if [ -f "$REPO/Makefile" ]; then
    cp "$REPO/Makefile" "$root/Makefile" || return 1
  fi
  if [ -f "$REPO/scripts/task-done.sh" ]; then
    cp "$REPO/scripts/task-done.sh" "$root/scripts/task-done.sh" || return 1
    chmod +x "$root/scripts/task-done.sh"
  fi

  echo "fixture" > "$root/README.md"
  git -C "$root" add -A || return 1
  git -C "$root" commit -qm "fixture init" || return 1
}

# 워크트리 1개를 만들고 그 안에 지정한 파일들을 심는다.
add_wt() {
  local root="$1" name="$2"; shift 2
  git -C "$root" worktree add -q "worktrees/$name" -b "task/$name" || return 1
  local rel
  for rel in "$@"; do
    mkdir -p "$root/worktrees/$name/$(dirname "$rel")" || return 1
    printf '지우면 안 되는 내용\n' > "$root/worktrees/$name/$rel" || return 1
  done
}

# make task-done 을 돌리고 (종료값, 워크트리 잔존여부, 출력) 을 돌려준다.
run_task_done() {
  local root="$1" name="$2"
  RTD_OUT=$(cd "$root" && make task-done NAME="$name" 2>&1)
  RTD_RC=$?
  if [ -e "$root/worktrees/$name" ]; then RTD_ALIVE=1; else RTD_ALIVE=0; fi
}

# 검사기를 직접 돌린다.
#
# 왜 두 표면을 따로 재는가 (2026-08-26 GREEN 시도에서 실증):
#   GNU make 는 레시피가 실패하면 레시피의 종료값과 무관하게 **자기 종료값 2** 를 낸다
#   (`make: *** [task-done] Error 1` → make 자체는 2). 그래서 make 를 통해서는
#   BLOCK(1) 과 REVIEW(2) 가 구분되지 않는다.
#   → 3상태 종료값은 scripts/task-done.sh 의 계약이고, make 는 0 vs 비-0 + STATE 문구를
#     보장한다. 둘 다 재지 않으면 종료값 계약이 아무 데서도 검증되지 않는다.
run_direct() {
  local root="$1" name="$2"
  RTD_OUT=$(cd "$root" && bash scripts/task-done.sh "$name" 2>&1)
  RTD_RC=$?
  if [ -e "$root/worktrees/$name" ]; then RTD_ALIVE=1; else RTD_ALIVE=0; fi
}

# ── 시나리오 3종: 통과 2 + 차단 1 ─────────────────────────────────────────────
FIX="$TMP/main"
if ! make_fixture "$FIX"; then
  echo "NOT_RUN: fixture 저장소를 만들지 못했다"
  echo "CHECKED: $checked"
  exit 2
fi

# C1 clean — 무시 파일이 하나도 없다. 반드시 삭제되어야 한다.
#   이 케이스가 없으면 구현 부재로 인한 make 실패가 "차단 성공"으로 집계된다.
if add_wt "$FIX" "$WT_CLEAN"; then
  run_task_done "$FIX" "$WT_CLEAN"
  if [ "$RTD_RC" -eq 0 ] && [ "$RTD_ALIVE" -eq 0 ]; then
    record 0 "C1 clean 워크트리는 폐기된다" "exit=$RTD_RC 잔존=$RTD_ALIVE"
  else
    record 1 "C1 clean 워크트리는 폐기된다" "exit=$RTD_RC 잔존=$RTD_ALIVE (기대 exit=0 잔존=0) :: ${RTD_OUT}"
  fi
else
  record 1 "C1 clean 워크트리는 폐기된다" "워크트리 생성 실패"
fi

# C2 cache-only — 캐시와 재생성 가능한 의존성 환경만 남았다. 역시 삭제되어야 한다.
#   이 케이스가 빨간 채로 두면 제외 목록이 좁아 정상 워크트리가 영구 폐기 불가가 된다.
if add_wt "$FIX" "$WT_CACHE" ".ruff_cache/CACHEDIR.TAG" ".venv/pyvenv.cfg"; then
  run_task_done "$FIX" "$WT_CACHE"
  if [ "$RTD_RC" -eq 0 ] && [ "$RTD_ALIVE" -eq 0 ]; then
    record 0 "C2 캐시·재생성 대상만 있으면 폐기된다" "exit=$RTD_RC 잔존=$RTD_ALIVE"
  else
    record 1 "C2 캐시·재생성 대상만 있으면 폐기된다" "exit=$RTD_RC 잔존=$RTD_ALIVE (기대 exit=0 잔존=0) :: ${RTD_OUT}"
  fi
else
  record 1 "C2 캐시·재생성 대상만 있으면 폐기된다" "워크트리 생성 실패"
fi

# C3 artifact — P12 회수 대상이 남았다. 차단 + 경로 출력.
if add_wt "$FIX" "$WT_RECOVER" "$RECOVER_FILE"; then
  run_task_done "$FIX" "$WT_RECOVER"
  if [ "$RTD_RC" -ne 0 ] && [ "$RTD_ALIVE" -eq 1 ] \
     && printf '%s' "$RTD_OUT" | grep -q 'STATE: BLOCK'; then
    record 0 "C3 회수 대상이 있으면 폐기가 차단된다(make)" "exit=$RTD_RC 잔존=$RTD_ALIVE STATE=BLOCK"
  else
    record 1 "C3 회수 대상이 있으면 폐기가 차단된다(make)" "exit=$RTD_RC 잔존=$RTD_ALIVE (기대 비-0 잔존=1 STATE:BLOCK) :: ${RTD_OUT}"
  fi
  # 종료값 1(BLOCK)은 make 가 2 로 뭉개므로 검사기를 직접 불러서 잰다.
  run_direct "$FIX" "$WT_RECOVER"
  if [ "$RTD_RC" -eq 1 ] && [ "$RTD_ALIVE" -eq 1 ]; then
    record 0 "C3 검사기 직접 호출은 BLOCK=1 을 낸다" "exit=$RTD_RC"
  else
    record 1 "C3 검사기 직접 호출은 BLOCK=1 을 낸다" "exit=$RTD_RC (기대 1) :: ${RTD_OUT}"
  fi
  # 목록 출력은 인수 기준 본문("그 목록을 출력한다")이다. 차단만 하고 침묵하면 불합격.
  if printf '%s' "$RTD_OUT" | grep -qF "$RECOVER_FILE"; then
    record 0 "C3 차단 시 남은 경로를 출력한다" "출력에 $RECOVER_FILE 포함"
  else
    record 1 "C3 차단 시 남은 경로를 출력한다" "출력에 경로가 없다 :: ${RTD_OUT}"
  fi
else
  record 1 "C3 회수 대상이 있으면 폐기가 차단된다" "워크트리 생성 실패"
  record 1 "C3 차단 시 남은 경로를 출력한다" "워크트리 생성 실패"
fi

# C4 review — 캐시도 회수 대상도 아닌 미분류. 삭제 금지(exit 2), BLOCK 과 구분된다.
#
# 종료값만 재면 안 된다(2026-08-26 RED 실행에서 실증): `Makefile` 이 없을 때 make 자신이
# exit 2 를 내므로, 구현이 0줄이어도 "exit 2 면 REVIEW" 라는 단언은 통과해 버린다.
# 그래서 판정 문구(`STATE: REVIEW`)와 경로 출력까지 함께 요구한다.
if add_wt "$FIX" "$WT_REVIEW" "$REVIEW_FILE"; then
  run_task_done "$FIX" "$WT_REVIEW"
  if [ "$RTD_RC" -eq 2 ] && [ "$RTD_ALIVE" -eq 1 ] \
     && printf '%s' "$RTD_OUT" | grep -q 'STATE: REVIEW' \
     && printf '%s' "$RTD_OUT" | grep -qF "$REVIEW_FILE"; then
    record 0 "C4 미분류 무시 파일은 폐기를 막는다(REVIEW)" "exit=$RTD_RC 잔존=$RTD_ALIVE STATE=REVIEW"
  else
    record 1 "C4 미분류 무시 파일은 폐기를 막는다(REVIEW)" "exit=$RTD_RC 잔존=$RTD_ALIVE (기대 exit=2 잔존=1 STATE:REVIEW + 경로) :: ${RTD_OUT}"
  fi
  # BLOCK 과 REVIEW 가 서로 다른 종료값이어야 한다 — 직접 호출로 확인한다.
  run_direct "$FIX" "$WT_REVIEW"
  if [ "$RTD_RC" -eq 2 ] && [ "$RTD_ALIVE" -eq 1 ]; then
    record 0 "C4 검사기 직접 호출은 REVIEW=2 를 낸다" "exit=$RTD_RC (BLOCK=1 과 구분됨)"
  else
    record 1 "C4 검사기 직접 호출은 REVIEW=2 를 낸다" "exit=$RTD_RC (기대 2) :: ${RTD_OUT}"
  fi
else
  record 1 "C4 미분류 무시 파일은 폐기를 막는다(REVIEW)" "워크트리 생성 실패"
  record 1 "C4 검사기 직접 호출은 REVIEW=2 를 낸다" "워크트리 생성 실패"
fi

# C5 direct-OK — 검사기 직접 호출도 정상 폐기 경로를 돈다(make 만 되는 게 아니다).
if add_wt "$FIX" "$WT_DIRECT"; then
  run_direct "$FIX" "$WT_DIRECT"
  if [ "$RTD_RC" -eq 0 ] && [ "$RTD_ALIVE" -eq 0 ]; then
    record 0 "C5 검사기 직접 호출도 clean 을 폐기한다" "exit=$RTD_RC 잔존=$RTD_ALIVE"
  else
    record 1 "C5 검사기 직접 호출도 clean 을 폐기한다" "exit=$RTD_RC 잔존=$RTD_ALIVE (기대 exit=0 잔존=0) :: ${RTD_OUT}"
  fi
else
  record 1 "C5 검사기 직접 호출도 clean 을 폐기한다" "워크트리 생성 실패"
fi

# ── 인자 위반: 전부 삭제 금지 방향으로 거부되어야 한다 ────────────────────────
# 여기서도 "비-0" 만 재면 구현 부재의 make 실패가 그대로 합격이 된다(같은 함정).
# 검사기가 스스로 낸 거부 판정(`STATE: REFUSED`)을 요구한다.
for bad in "" "../escape" "/tmp/absolute" "does-not-exist"; do
  RTD_OUT=$(cd "$FIX" && make task-done NAME="$bad" 2>&1)
  RTD_RC=$?
  if [ "$RTD_RC" -ne 0 ] && printf '%s' "$RTD_OUT" | grep -q 'STATE: REFUSED'; then
    record 0 "인자 거부: '${bad:-<빈값>}'" "exit=$RTD_RC STATE=REFUSED"
  else
    record 1 "인자 거부: '${bad:-<빈값>}'" "exit=$RTD_RC — 검사기 자신의 거부 판정이 없다 :: ${RTD_OUT}"
  fi
done

# ── 무력화 저항 (P13 ⑥) ──────────────────────────────────────────────────────
# 기존 acceptance-semantic-mutations.sh 는 `scripts/acceptance-*.sh` 만 변이시킨다.
# 검사기 **본체**(scripts/task-done.sh)를 껐을 때 빨개지는지는 여기서만 잴 수 있다.
if [ -f "$REPO/scripts/task-done.sh" ]; then
  for kind in exit-zero true-only noop; do
    MUT="$TMP/mut-$kind"
    if ! make_fixture "$MUT"; then
      record 1 "무력화($kind) 탐지" "fixture 생성 실패"
      continue
    fi
    case "$kind" in
      exit-zero) printf '#!/usr/bin/env bash\nexit 0\n' > "$MUT/scripts/task-done.sh" ;;
      true-only) printf '#!/usr/bin/env bash\ntrue\n'   > "$MUT/scripts/task-done.sh" ;;
      noop)      printf '#!/usr/bin/env bash\n: # no-op\n' > "$MUT/scripts/task-done.sh" ;;
    esac
    chmod +x "$MUT/scripts/task-done.sh"
    git -C "$MUT" add -A && git -C "$MUT" commit -qm "mutant $kind"

    # 무력화본에서는 C1(정상 폐기)이 깨져야 한다 — 지워야 할 것을 안 지운다.
    detected=1
    if add_wt "$MUT" clean; then
      run_task_done "$MUT" clean
      if [ "$RTD_RC" -ne 0 ] || [ "$RTD_ALIVE" -ne 0 ]; then detected=0; fi
    fi
    # 그리고 C3(차단)도 깨져야 한다 — 종료값이 1 이 아니게 된다.
    if [ "$detected" -ne 0 ] && add_wt "$MUT" artifact "artifacts/keep.txt"; then
      run_task_done "$MUT" artifact
      if [ "$RTD_RC" -ne 1 ]; then detected=0; fi
    fi

    if [ "$detected" -eq 0 ]; then
      record 0 "무력화($kind) 탐지" "검사기를 껐더니 인수 기준이 깨졌다 — 정상"
    else
      record 1 "무력화($kind) 탐지" "검사기를 껐는데도 인수 기준이 통과했다 — 검증 체계 FAIL"
    fi
  done
else
  record 1 "무력화 저항 시험" "scripts/task-done.sh 가 없어 변이 대상이 없다"
fi

# ── 명부 target 이 실재하는가 ────────────────────────────────────────────────
#
# scripts/verify/check-mechanism-registry.sh 는 stage:pre-push(128행)와 stage:ci(148행)
# 에서만 target 문자열의 실재를 대조하고 **stage:manual 에서는 대조하지 않는다**(152~159행).
# 그래서 manual 항목의 target 은 장식이 될 수 있다 — 2026-08-26 실측: task-done.sh 에서
# target 문자열을 지워도 명부 검사는 PASS 였다.
#
# 공유 검사기를 고치면 기존 manual 항목 4개가 함께 깨질 수 있어 이번 범위 밖이다(부채).
# 대신 task-done-checker 항목의 구멍만 여기서 막는다.
REG="$REPO/docs/sot/mechanism-registry.yaml"
CHK="$REPO/scripts/task-done.sh"
if [ -f "$REG" ] && [ -f "$CHK" ]; then
  reg_target=$(awk '
    /^- id: "task-done-checker"/ { inblk = 1; next }
    inblk && /^- id:/ { exit }
    inblk && /^  target:/ {
      line = $0
      sub(/^  target:[[:space:]]*"/, "", line)
      sub(/"[[:space:]]*$/, "", line)
      print line
      exit
    }
  ' "$REG")
  if [ -z "$reg_target" ]; then
    record 1 "명부 target 실재" "mechanism-registry.yaml 에서 task-done-checker 의 target 을 읽지 못했다"
  elif grep -qF -- "$reg_target" "$CHK"; then
    record 0 "명부 target 실재" "'$reg_target' 가 scripts/task-done.sh 안에 있다"
  else
    record 1 "명부 target 실재" "'$reg_target' 가 scripts/task-done.sh 안에 없다 — 명부가 거짓을 말한다"
  fi
else
  record 1 "명부 target 실재" "명부 또는 검사기 파일이 없다"
fi

# ── 원본 무오염 ───────────────────────────────────────────────────────────────
if [ "$(git -C "$REPO" status --porcelain)" = "$SNAPSHOT" ]; then
  record 0 "원본 저장소 무오염" "시작·종료 상태 동일"
else
  record 1 "원본 저장소 무오염" "인수 검사가 원본을 변경했다"
fi

echo "CHECKED: $checked"
[ "$fail" -eq 0 ] && exit 0
exit 1
