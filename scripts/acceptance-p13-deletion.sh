#!/usr/bin/env bash
# acceptance-p13-deletion.sh — CI 워크플로에서 검사 실행 줄을 지우면 커밋이 막히는가.
#
# 왜 필요한가 (억제 p13-deletion-blindspot · 만료 2026-09-15):
#   hooks/pre-commit 의 scan_added() 는 diff 의 추가된 줄(+)만 본다. 그래서 검사 줄을
#   **삭제**하는 약화는 원리적으로 탐지되지 않았다.
#   scripts/verify/check-ci-step-integrity.sh 도 자기 계약에 "스텝 자체를 삭제하는 것은
#   막지 못한다"고 적어 두었고, hooks/pre-push 의 실행줄 검사는 DEFERRED(0-5·0-7)와
#   PUSH-PERFORMING 선언 스크립트만 대조한다. 나머지 인수 스크립트는 로컬에서 전량
#   실행되므로, CI 스텝만 지우면 로컬 게이트가 전부 초록이었다.
#
# 계약: 출력 exit 0 (전 시연 합격) | exit 1 (하나라도 불합격) | exit 2 (셋업 실패 · fail-closed)
#   불변식: 모든 시연은 mktemp -d 안의 clone 에서 수행한다. 원본 저장소를 건드리지 않는다.
#
# 판정 구조는 acceptance-0-7 과 같다. 각 시연은 셋 다 만족해야 합격이다:
#   ① 셋업이 성공한다        — 위반을 실제로 만들었는가 (못 만들었으면 시연 무효)
#   ② 훅 ON 에서 차단된다    — 그리고 **이 검사가 낸 사유로** 차단됐는가 (다른 검사의
#                              차단을 계수하면 위양성이다. acceptance-0-7 이 겪은 실수다)
#   ③ 훅 OFF 에서 통과한다   — 훅이 원인인가 (대조군 없이는 위양성을 못 걸러낸다)
#
# 생산 호출 형태로 시험한다. 검사기에 인자를 주는 형태로만 시험하면 인자 없는 생산
# 경로(pre-commit 이 부르는 그 형태)를 꺼도 전부 초록이 된다(2026-09-06 실측 교훈).
set -uo pipefail

unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE GIT_OBJECT_DIRECTORY \
      GIT_ALTERNATE_OBJECT_DIRECTORIES GIT_COMMON_DIR GIT_PREFIX GIT_QUARANTINE_PATH

BLOCK_MARK='워크플로 검사 실행 줄 삭제'

REPO=$(git rev-parse --show-toplevel 2>/dev/null) || {
  echo "FAIL: git 저장소가 아니다 (fail-closed)"; echo "CHECKED: 0"; exit 2; }
cd "$REPO" || { echo "FAIL: 저장소 루트로 이동 실패"; echo "CHECKED: 0"; exit 2; }

WF=.github/workflows/verify.yml
# 검사기 존재를 전제로 두지 않는다. 두면 검사기가 없을 때 시연이 한 번도 돌지 않고
# exit 2 로 끝나, "삭제가 차단되지 않는다"는 사실이 관측되지 않는다. 부재는 시연 5 가 잡는다.
for f in "$WF" hooks/pre-commit; do
  [ -f "$f" ] || { echo "FAIL: $f 없음 — 검사를 실행할 수 없다 (fail-closed)"; echo "CHECKED: 0"; exit 2; }
done

SANDBOX=$(mktemp -d) || { echo "FAIL: 샌드박스 생성 실패"; echo "CHECKED: 0"; exit 2; }
cleanup() { chmod -R u+w "$SANDBOX" 2>/dev/null; rm -rf "$SANDBOX"; }
trap cleanup EXIT
trap 'cleanup; trap - EXIT; exit 143' TERM
trap 'cleanup; trap - EXIT; exit 130' INT

fail=0
checked=0
record() {  # record <ok:0|1> <설명> <상세>
  checked=$((checked + 1))
  if [ "$1" -eq 0 ]; then
    printf 'PASS: %s\n' "$2"
  else
    printf 'FAIL: %s — %s\n' "$2" "$3"; fail=1
  fi
}

# --- 격리 clone -------------------------------------------------------------
# --no-local 을 쓴다. 기본 로컬 clone 은 하드링크로 객체를 **공유**해서, 원본에서
# 폐기된 객체 때문에 허위 FAIL 이 나거나 반대로 샌드박스 변조가 원본에 비친다.
CLONE="$SANDBOX/clone"
if ! git clone --no-local --quiet --no-hardlinks "$REPO" "$CLONE" 2>"$SANDBOX/clone.err"; then
  echo "FAIL: 격리 clone 실패 — $(head -2 "$SANDBOX/clone.err" | tr '\n' ' ')"
  echo "CHECKED: 0"; exit 2
fi
cp -p hooks/pre-commit "$CLONE/.git/hooks/pre-commit" || {
  echo "FAIL: 훅 설치 실패"; echo "CHECKED: 0"; exit 2; }
chmod +x "$CLONE/.git/hooks/pre-commit"

# 삭제 대상으로 쓸 실행 줄을 실제 워크플로에서 고른다. 하드코딩하면 워크플로가 바뀐 뒤
# 이 시연이 조용히 무의미해진다(셋업 실패를 합격으로 세는 경로).
VICTIM=$(grep -n 'run-acceptance\.sh scripts/acceptance-' "$CLONE/$WF" | head -1 | cut -d: -f1)
if [ -z "$VICTIM" ]; then
  echo "FAIL: 워크플로에서 인수 스크립트 실행 줄을 찾지 못했다 — 시연 대상 0개는 합격이 아니다"
  echo "CHECKED: 0"; exit 2
fi
VICTIM_PATH=$(sed -n "${VICTIM}p" "$CLONE/$WF" | sed 's/.*run-acceptance\.sh[[:space:]]*//' | awk '{print $1}')

# try <설명> <훅ON기대: block|pass> <셋업 함수>
run_case() {
  local desc="$1" expect="$2" setup="$3"
  local log="$SANDBOX/log.$checked"
  ( cd "$CLONE" && git checkout --quiet -- . && git clean -qfd ) 2>/dev/null
  if ! ( cd "$CLONE" && $setup ) >"$SANDBOX/setup.err" 2>&1; then
    record 1 "$desc" "셋업 실패 — 위반을 만들지 못했다: $(head -1 "$SANDBOX/setup.err")"
    return
  fi
  # 셋업이 실제로 스테이징을 만들었는가 (빈 커밋은 훅 이전에 거부되어 위양성이 된다)
  if ( cd "$CLONE" && git diff --cached --quiet ); then
    record 1 "$desc" "셋업이 스테이징을 만들지 못했다 — 시연 무효"
    return
  fi
  local rc=0
  ( cd "$CLONE" && git -c user.name=a -c user.email=a@b commit -m "demo" ) >"$log" 2>&1 || rc=$?
  if [ "$expect" = block ]; then
    if [ "$rc" -eq 0 ]; then
      record 1 "$desc" "차단되지 않았다 (commit rc=0)"; return
    fi
    if ! grep -q "$BLOCK_MARK" "$log"; then
      record 1 "$desc" "차단은 됐으나 이 검사의 사유가 아니다 (rc=$rc) — 다른 검사의 차단을 계수하면 위양성이다: $(grep -m1 BLOCKED "$log" | head -c 120)"
      return
    fi
    # 대조군: 훅을 끄면 통과해야 한다. 안 그러면 훅이 원인이 아니다.
    local orc=0
    ( cd "$CLONE" && git -c core.hooksPath=/dev/null -c user.name=a -c user.email=a@b commit -m "demo-off" ) >"$log.off" 2>&1 || orc=$?
    if [ "$orc" -ne 0 ]; then
      record 1 "$desc" "훅 OFF 에서도 실패했다 (rc=$orc) — 훅이 원인이 아니다: $(head -1 "$log.off")"
      return
    fi
    record 0 "$desc"
  else
    if [ "$rc" -ne 0 ] && grep -q "$BLOCK_MARK" "$log"; then
      record 1 "$desc" "오탐 — 정당한 변경을 이 검사가 차단했다: $(grep -m1 "$BLOCK_MARK" "$log" | head -c 160)"
      return
    fi
    record 0 "$desc"
  fi
}

echo "=== 대상: $WF / 희생 줄 ${VICTIM} ($VICTIM_PATH) ==="

# 시연 1 (양성) — 인수 스크립트 실행 줄을 지운다. 스크립트 파일은 그대로 남는다.
setup_delete_run_line() {
  sed -i.bak "${VICTIM}d" "$WF" && rm -f "$WF.bak" && git add "$WF"
}
run_case "실행 줄 삭제는 차단된다 ($VICTIM_PATH)" block setup_delete_run_line

# 시연 2 (양성) — 스텝 전체(name + run)를 지운다. 스텝 통째 삭제가 흔한 형태다.
setup_delete_step() {
  local s=$((VICTIM - 1))
  sed -i.bak "${s},${VICTIM}d" "$WF" && rm -f "$WF.bak" && git add "$WF"
}
run_case "스텝 통째 삭제는 차단된다" block setup_delete_step

# 시연 3 (음성 · 오탐 대조) — 같은 스크립트를 계속 실행하되 스텝 이름만 바꾼다.
# 줄은 삭제되지만 실행 경로는 새 본문에 그대로 있다. 차단하면 리팩터링마다 오탐이다.
setup_rename_step() {
  sed -i.bak "${VICTIM}s#run: #run: #" "$WF"
  local s=$((VICTIM - 1))
  sed -i.bak "${s}s/name: .*/name: 이름만 바꾼 스텝/" "$WF" && rm -f "$WF.bak" && git add "$WF"
}
run_case "스텝 이름 변경은 통과한다 (오탐 대조)" pass setup_rename_step

# 시연 4 (음성 · 범위 대조) — 워크플로 밖 파일에서 같은 모양의 줄을 지운다.
# 억제 원장이 합의한 범위는 .github/workflows/* 뿐이다. 그 밖까지 잡으면 오탐이 폭증한다.
setup_delete_outside() {
  printf 'bash scripts/verify/run-acceptance.sh %s\n' "$VICTIM_PATH" > docs/_p13_demo.txt
  git add docs/_p13_demo.txt
  git -c user.name=a -c user.email=a@b -c core.hooksPath=/dev/null commit -qm seed
  : > docs/_p13_demo.txt
  git add docs/_p13_demo.txt
}
run_case "워크플로 밖 파일의 같은 줄 삭제는 통과한다 (범위 대조)" pass setup_delete_outside

# 시연 5 (배선) — 검사기가 존재해도 훅이 부르지 않으면 무방비다.
# 몽키패치로 치워 둔 함수가 시험 0건이 되는 것을 막는다(2026-08-27 PR#54 교훈).
if grep -q 'check-workflow-deletion\.sh' hooks/pre-commit; then
  record 0 "hooks/pre-commit 이 검사기를 호출한다 (배선)"
else
  record 1 "hooks/pre-commit 이 검사기를 호출한다 (배선)" "훅에 호출이 없다 — 검사기가 있어도 커밋은 막히지 않는다"
fi

echo
echo "CHECKED: $checked"
if [ "$fail" -ne 0 ]; then
  echo "RESULT: 불합격 — 삭제 약화가 차단되지 않는다"
  exit 1
fi
echo "RESULT: 합격 — 워크플로 검사 실행 줄 삭제가 차단된다"
exit 0
