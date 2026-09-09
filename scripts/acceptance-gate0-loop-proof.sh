#!/usr/bin/env bash
# acceptance-gate0-loop-proof.sh — 게이트 0 이 "검사를 실제로 돌렸다"를 증명하는가.
#
# 왜 필요한가:
#   scripts/session-status.sh 는 find 로 검사기 N 개를 찾고(total), while 루프로 하나씩
#   돌린 뒤 `RED: <red>/<total>` 을 출력한다. 그런데 루프 입력(here-string)이 만들어지지
#   않으면 bash 는 루프를 **실행하지 않고** 종료값 1 을 준다. total 은 이미 N 이라
#   fail-closed(`total -eq 0`) 검사를 통과하고, red 는 초기값 0 그대로다.
#   결과: 검사기 N 개를 찾아 놓고 한 개도 실행하지 않은 채 `RED: 0/N` + exit 0.
#   트리거는 디스크 만재·임시 디렉터리 소실·읽기 전용 샌드박스이며, codex 샌드박스에서
#   실제로 발동해 `RED: 0/28` 거짓 초록이 났다.
#
#   이 출력은 harness 게이트 0(시작 자격)의 판정이다. 거짓 초록이면 "미해결 RED 없음"
#   이라는 전제 위에서 새 작업이 시작된다.
#
# 무엇을 요구하는가: 입력 방식이 무엇이든 **실행 횟수가 total 과 다르면 수치를 내지 않고
#   exit 1**. here-string 을 다른 방식으로 바꾸는 것으로는 부족하다 — 파이프도 실패할 수
#   있고 그때도 같은 모양으로 접힌다. 자기 실행 횟수를 세는 것만이 방식에 무관하다.
#
# 계약: exit 0 (전 시연 합격) | exit 1 (하나라도 불합격) | exit 2 (셋업 실패 · fail-closed)
set -uo pipefail

unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE GIT_OBJECT_DIRECTORY \
      GIT_ALTERNATE_OBJECT_DIRECTORIES GIT_COMMON_DIR GIT_PREFIX GIT_QUARANTINE_PATH

REPO=$(git rev-parse --show-toplevel 2>/dev/null) || {
  echo "FAIL: git 저장소가 아니다 (fail-closed)"; echo "CHECKED: 0"; exit 2; }
cd "$REPO" || { echo "FAIL: 저장소 루트로 이동 실패"; echo "CHECKED: 0"; exit 2; }

TARGET=scripts/session-status.sh
[ -f "$TARGET" ] || { echo "FAIL: $TARGET 없음 (fail-closed)"; echo "CHECKED: 0"; exit 2; }

SANDBOX=$(mktemp -d) || { echo "FAIL: 샌드박스 생성 실패"; echo "CHECKED: 0"; exit 2; }
cleanup() { chmod -R u+w "$SANDBOX" 2>/dev/null; rm -rf "$SANDBOX"; }
trap cleanup EXIT
trap 'cleanup; trap - EXIT; exit 143' TERM
trap 'cleanup; trap - EXIT; exit 130' INT

fail=0; checked=0
record() {
  checked=$((checked + 1))
  if [ "$1" -eq 0 ]; then printf 'PASS: %s\n' "$2"
  else printf 'FAIL: %s — %s\n' "$2" "$3"; fail=1; fi
}

CLONE="$SANDBOX/clone"
git clone --no-local --quiet --no-hardlinks "$REPO" "$CLONE" 2>"$SANDBOX/clone.err" || {
  echo "FAIL: 격리 clone 실패 — $(head -2 "$SANDBOX/clone.err" | tr '\n' ' ')"
  echo "CHECKED: 0"; exit 2; }

# 시연 저장소에 origin/main 참조를 만들어 준다. session-status.sh 는 HEAD 와 origin/main 을
# 대조해 동기 상태를 보고하는데, 그 참조가 없으면 sync=UNKNOWN 이 되어 rc=1 로 끝난다.
# 로컬 워크트리에는 origin/main 이 있어서 통과했지만 CI 러너의 체크아웃에는 없어서
# 대조군이 빨개졌다(실측: PR #75 CI — "HEAD: feedcee (UNKNOWN)").
# 시연 환경을 갖추는 것이지 판정을 무르는 것이 아니다 — 종료값 0 요구는 그대로다.
if ! ( cd "$CLONE" && git update-ref refs/remotes/origin/main HEAD ) 2>"$SANDBOX/ref.err"; then
  echo "FAIL: 시연 저장소에 origin/main 참조를 만들지 못했다 — $(head -1 "$SANDBOX/ref.err")"
  echo "CHECKED: 0"; exit 2
fi

# 작업트리 사본으로 덮는다. clone 은 HEAD 를 받으므로 이 줄이 없으면 지금 고치는 중인
# 판본이 아니라 커밋된 옛 판본을 시험하게 된다.
cp -p "$TARGET" "$CLONE/$TARGET" && chmod +x "$CLONE/$TARGET" || {
  echo "FAIL: 대상 설치 실패"; echo "CHECKED: 0"; exit 2; }

# 인수 스크립트를 스텁으로 치환한다. 실제로 전량 돌리면 시연 1건에 10분이 넘어 아무도
# 돌리지 않게 된다 — 여기서 시험하는 것은 인수 검사의 내용이 아니라 게이트 0 의 자기검증이다.
stub_count=0
while IFS= read -r s; do
  [ -z "$s" ] && continue
  printf '#!/usr/bin/env bash\nexit 0\n' > "$CLONE/$s"
  chmod +x "$CLONE/$s"; stub_count=$((stub_count + 1))
done < <(cd "$CLONE" && find . -maxdepth 2 \( -name 'verify.sh' -o -name 'acceptance-*.sh' \) \
         -not -path './worktrees/*' -not -path './.git/*' | sed 's#^\./##' | LC_ALL=C sort)
[ "$stub_count" -ge 5 ] || {
  echo "FAIL: 스텁 대상이 ${stub_count}개뿐 — 시연 대상 부족 (fail-closed)"; echo "CHECKED: 0"; exit 2; }

run_target() {  # stdout+stderr → $SANDBOX/out, 종료값 반환
  local rc=0
  ( cd "$CLONE" && bash "$TARGET" ) >"$SANDBOX/out" 2>&1 || rc=$?
  echo "$rc"
}

restore() { cp -p "$TARGET" "$CLONE/$TARGET" && chmod +x "$CLONE/$TARGET"; }

# --- 시연 1 (음성 · 대조군) 정상 실행 -----------------------------------------
restore
rc=$(run_target)
line=$(grep '^RED:' "$SANDBOX/out" | head -1)
if [ "$rc" -ne 0 ]; then
  record 1 "정상 실행은 RED 수치를 내고 통과한다 (대조군)" "종료값 $rc — $(head -1 "$SANDBOX/out")"
elif ! printf '%s' "$line" | grep -qE '^RED: [0-9]+/[0-9]+'; then
  record 1 "정상 실행은 RED 수치를 내고 통과한다 (대조군)" "RED 수치 줄이 없다: ${line:-<없음>}"
else
  record 0 "정상 실행은 RED 수치를 내고 통과한다 (대조군) — $line"
fi
EXPECT_TOTAL=$(printf '%s' "$line" | sed -n 's#^RED: [0-9]*/\([0-9]*\).*#\1#p')

# --- 시연 2 (양성) 루프가 0회 도는 경우 ---------------------------------------
# here-string 생성 실패와 관측적으로 같은 상태를 만든다. bash 가 루프를 실행하지 않는
# 그 상황을 macOS 에서 직접 재현할 수는 없으므로(3.2 는 /tmp 로 물러선다), 결함의 본질인
# "찾기는 N 개인데 실행은 0회"를 생산 호출 형태 그대로 만든다.
restore
if ! sed -i.bak 's#^done <<< "\$checks"$#done <<< ""#' "$CLONE/$TARGET"; then
  record 1 "루프 0회는 수치를 내지 않고 실패한다" "변조 주입 실패 — 시연 무효"
else
  rm -f "$CLONE/$TARGET.bak"
  if ! grep -q 'done <<< ""' "$CLONE/$TARGET"; then
    record 1 "루프 0회는 수치를 내지 않고 실패한다" "변조가 반영되지 않았다 — 시연 무효"
  else
    rc=$(run_target)
    if [ "$rc" -eq 0 ]; then
      record 1 "루프 0회는 수치를 내지 않고 실패한다" "종료값 0 — 검사 0회 실행하고 통과했다: $(grep '^RED:' "$SANDBOX/out" | head -1)"
    elif grep -qE '^RED: [0-9]+/[0-9]+' "$SANDBOX/out"; then
      record 1 "루프 0회는 수치를 내지 않고 실패한다" "종료값은 $rc 이지만 RED 수치를 여전히 출력한다: $(grep '^RED:' "$SANDBOX/out" | head -1) — 읽는 사람은 이것을 판정으로 받아들인다"
    else
      record 0 "루프 0회는 수치를 내지 않고 실패한다"
    fi
  fi
fi

# --- 시연 3 (양성) 루프가 도중에 끊긴 경우 ------------------------------------
# 전부 아니면 0 만 잡으면 부분 실행이 통과한다. 1개만 돌고 나머지가 누락돼도
# `RED: 0/N` 이 나오는 것은 같은 거짓 초록이다.
restore
if ! sed -i.bak 's#^done <<< "\$checks"$#done <<< "$(printf "%s\\\\n" "$checks" | head -1)"#' "$CLONE/$TARGET"; then
  record 1 "부분 실행도 수치를 내지 않고 실패한다" "변조 주입 실패 — 시연 무효"
else
  rm -f "$CLONE/$TARGET.bak"
  rc=$(run_target)
  if [ "$rc" -eq 0 ]; then
    record 1 "부분 실행도 수치를 내지 않고 실패한다" "종료값 0 — 1개만 돌고 통과했다: $(grep '^RED:' "$SANDBOX/out" | head -1)"
  elif grep -qE '^RED: [0-9]+/[0-9]+' "$SANDBOX/out"; then
    record 1 "부분 실행도 수치를 내지 않고 실패한다" "RED 수치를 여전히 출력한다: $(grep '^RED:' "$SANDBOX/out" | head -1)"
  else
    record 0 "부분 실행도 수치를 내지 않고 실패한다"
  fi
fi

# --- 시연 4 (음성 · 오탐 대조) 실패하는 검사기가 있어도 수치는 나온다 ----------
# 실행 횟수 대조를 "종료값이 0 이 아니면 실패"로 잘못 만들면, RED 가 실제로 있는
# 정상 상황까지 UNKNOWN 이 된다. 그러면 게이트 0 이 영원히 빨간불이라 아무도 안 쓴다.
restore
victim=$(cd "$CLONE" && find . -maxdepth 2 -name 'acceptance-*.sh' -not -path './worktrees/*' | LC_ALL=C sort | head -1)
if [ -z "$victim" ]; then
  record 1 "실패하는 검사기가 있어도 수치는 나온다 (오탐 대조)" "희생 대상 없음 — 시연 무효"
else
  printf '#!/usr/bin/env bash\nexit 1\n' > "$CLONE/$victim"; chmod +x "$CLONE/$victim"
  rc=$(run_target)
  line=$(grep '^RED:' "$SANDBOX/out" | head -1)
  red_n=$(printf '%s' "$line" | sed -n 's#^RED: \([0-9]*\)/.*#\1#p')
  if [ "$rc" -ne 0 ]; then
    record 1 "실패하는 검사기가 있어도 수치는 나온다 (오탐 대조)" "종료값 $rc — RED 가 있는 정상 상황을 실행 실패로 뭉갠다"
  elif [ "${red_n:-0}" -lt 1 ]; then
    record 1 "실패하는 검사기가 있어도 수치는 나온다 (오탐 대조)" "RED 를 1건 심었는데 수치가 ${red_n:-없음}: $line"
  else
    record 0 "실패하는 검사기가 있어도 수치는 나온다 (오탐 대조) — $line"
  fi
  printf '#!/usr/bin/env bash\nexit 0\n' > "$CLONE/$victim"; chmod +x "$CLONE/$victim"
fi

# --- 시연 5 (배선) 실행 횟수를 세는 코드가 실제로 있는가 -----------------------
restore
if grep -qE 'ran[+=]|ran=\$\(\(' "$CLONE/$TARGET" && grep -q 'total' "$CLONE/$TARGET"; then
  record 0 "session-status.sh 가 실행 횟수를 세어 total 과 대조한다 (배선)"
else
  record 1 "session-status.sh 가 실행 횟수를 세어 total 과 대조한다 (배선)" "실행 횟수를 세는 코드가 없다 — 입력 방식만 바꾸면 같은 fail-open 이 다시 난다"
fi

echo
echo "총 검사기 ${EXPECT_TOTAL:-?}개 · 스텁 ${stub_count}개"
echo "CHECKED: $checked"
[ "$fail" -ne 0 ] && { echo "RESULT: 불합격 — 게이트 0 이 실행하지 않고도 초록을 낸다"; exit 1; }
echo "RESULT: 합격 — 실행 횟수가 total 과 다르면 수치를 내지 않는다"
exit 0
