#!/usr/bin/env bash
# acceptance-secret-detection-regression.sh — 비밀 규칙의 탐지력을 줄이면 커밋이 막히는가.
#
# 왜 필요한가 (2026-09-10 Codex 적대검증):
#   P13 약화 탐지는 추가된 줄을 일반 약화 리터럴 목록과 대조한다. 비밀 규칙 파일에는
#   그 방식이 원리적으로 통하지 않는다 — **삭제**는 추가 줄이 없어 입력에 안 들어오고,
#   수량 하한을 {16} → {99} 로 올리는 **수정**은 어떤 약화 리터럴과도 일치하지 않는다.
#   실측: AKIA 규칙을 지운 커밋이 통과했고 **바로 다음 커밋에서 실제 AWS 키가 통과했다**.
#
# 계약: exit 0 (전 시연 합격) | exit 1 (하나라도 불합격) | exit 2 (셋업 실패 · fail-closed)
set -uo pipefail

unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE GIT_OBJECT_DIRECTORY \
      GIT_ALTERNATE_OBJECT_DIRECTORIES GIT_COMMON_DIR GIT_PREFIX GIT_QUARANTINE_PATH

BLOCK_MARK='비밀 탐지력'
PATTERNS=.secret-patterns.default
CANARY_POS=scripts/verify/fixtures/secret-canaries/positive.txt
CHECKER_SRC=scripts/verify/check-secret-detection-regression.sh

REPO=$(git rev-parse --show-toplevel 2>/dev/null) || {
  echo "FAIL: git 저장소가 아니다 (fail-closed)"; echo "CHECKED: 0"; exit 2; }
cd "$REPO" || { echo "FAIL: 저장소 루트로 이동 실패"; echo "CHECKED: 0"; exit 2; }
for f in "$PATTERNS" hooks/pre-commit "$CANARY_POS"; do
  [ -f "$f" ] || { echo "FAIL: $f 없음 (fail-closed)"; echo "CHECKED: 0"; exit 2; }
done

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
cp -p hooks/pre-commit "$CLONE/.git/hooks/pre-commit" || {
  echo "FAIL: 훅 설치 실패"; echo "CHECKED: 0"; exit 2; }
chmod +x "$CLONE/.git/hooks/pre-commit"
# 검사기도 작업트리 사본으로 덮는다 — clone 은 HEAD 를 받으므로 이 줄이 없으면
# 지금 고치는 중인 판본이 아니라 커밋된 옛 판본을 시험하게 된다.
# 검사기와 **카나리 고정물**을 함께 옮긴다. 고정물이 빠지면 검사기가 fail-closed 로
# exit 2 를 내고, 음성 시연이 전부 "오탐"으로 빨개진다(2026-09-11 실측). 검사기만 옮기고
# 그것이 읽는 데이터를 두고 오면 어긋난 조합을 시험하게 된다.
install_from_worktree() {
  local f
  for f in "$@"; do
    [ -f "$f" ] || continue
    mkdir -p "$CLONE/$(dirname "$f")" || return 1
    cp -p "$f" "$CLONE/$f" || return 1
  done
  [ -f "$CLONE/$CHECKER_SRC" ] && chmod +x "$CLONE/$CHECKER_SRC"
  return 0
}
FIXTURES="scripts/verify/fixtures/secret-canaries/positive.txt scripts/verify/fixtures/secret-canaries/negative.txt"
install_from_worktree "$CHECKER_SRC" $FIXTURES || {
  echo "FAIL: 검사기·고정물 설치 실패"; echo "CHECKED: 0"; exit 2; }
# 작업트리 사본을 clone 에 **커밋**한다. 검사기가 인덱스와 HEAD 를 읽으므로 cp 만으로는
# 판정 입력이 바뀌지 않는다 — clone 의 HEAD·인덱스에는 커밋된 옛 판본이 그대로 남아,
# 지금 고치는 중인 판본이 아니라 옛 조합을 시험하게 된다(2026-09-09 에 변이 4종이 전부
# 생존한 원인이 이 어긋남이었다). 훅은 끄고 커밋한다 — 설치 자체는 시연이 아니다.
# 작업트리와 clone 의 HEAD 가 이미 같으면 커밋할 것이 없다 — 그것은 정상이다.
# `nothing to commit` 종료값을 설치 실패로 세면 손대지 않은 상태에서 시연이 0건이 된다.
( cd "$CLONE" && git add -A -- "$CHECKER_SRC" $FIXTURES \
  && { git diff --cached --quiet \
       || git -c user.name=a -c user.email=a@b -c core.hooksPath=/dev/null \
            commit -qm "작업트리 사본 설치 (시연 기준점)"; } ) >"$SANDBOX/seed.err" 2>&1 || {
  echo "FAIL: 작업트리 사본 커밋 실패 — $(head -2 "$SANDBOX/seed.err" | tr '\n' ' ')"
  echo "CHECKED: 0"; exit 2; }
BASE=$(cd "$CLONE" && git rev-parse HEAD) || {
  echo "FAIL: 기준 커밋을 읽지 못했다"; echo "CHECKED: 0"; exit 2; }
# 설치본이 기준 커밋에 들어갔는지 확인한다. 안 들어갔으면 모든 시연이 옛 판본을 본다.
( cd "$CLONE" && git diff --quiet "$BASE" -- "$CHECKER_SRC" $FIXTURES ) || {
  echo "FAIL: 설치본이 기준 커밋에 반영되지 않았다 — 시연 전체가 무효다"
  echo "CHECKED: 0"; exit 2; }

run_case() {  # <설명> <block|pass> <셋업 함수명> [기대 종료값 — block 일 때만, 기본 1]
  local desc="$1" expect="$2" setup="$3" want_rc="${4:-1}" log="$SANDBOX/log.$checked"
  # BASE 에 설치본이 커밋돼 있으므로 reset --hard 하나로 작업트리·인덱스·HEAD 가 모두
  # 지금 판본으로 돌아온다. 따로 다시 덮지 않는다.
  ( cd "$CLONE" && git reset --hard --quiet "$BASE" && git clean -qfdx ) 2>/dev/null
  if ! ( cd "$CLONE" && $setup ) >"$SANDBOX/setup.err" 2>&1; then
    record 1 "$desc" "셋업 실패 — $(head -1 "$SANDBOX/setup.err")"; return
  fi
  if ( cd "$CLONE" && git diff --cached --quiet ); then
    record 1 "$desc" "셋업이 스테이징을 만들지 못했다 — 시연 무효"; return
  fi
  local rc=0
  ( cd "$CLONE" && git -c user.name=a -c user.email=a@b commit -m demo ) >"$log" 2>&1 || rc=$?
  if [ "$expect" = block ]; then
    if [ "$rc" -eq 0 ]; then record 1 "$desc" "차단되지 않았다 (commit rc=0)"; return; fi
    if ! grep -q "$BLOCK_MARK" "$log"; then
      record 1 "$desc" "차단은 됐으나 이 검사의 사유가 아니다 (rc=$rc): $(grep -m1 BLOCKED "$log" | head -c 120)"
      return
    fi
    # 실행 불가(exit 2)와 판정 실패(exit 1)를 가른다. 둘을 같은 신호로 세면
    # mktemp 거부·고정물 부재 같은 환경 사고가 "차단됨"으로 계수되고,
    # 구현이 0줄이어도 전부 초록이 난다(counter-AC 5).
    if ! grep -q "exit=$want_rc" "$log"; then
      record 1 "$desc" "차단 사유의 종료값이 다르다 (기대 exit=$want_rc): $(grep -m1 -o 'exit=[0-9]*' "$log")"
      return
    fi
    local orc=0
    ( cd "$CLONE" && git -c core.hooksPath=/dev/null -c user.name=a -c user.email=a@b commit -m demo-off ) >"$log.off" 2>&1 || orc=$?
    if [ "$orc" -ne 0 ]; then
      record 1 "$desc" "훅 OFF 에서도 실패했다 (rc=$orc) — 훅이 원인이 아니다"; return
    fi
    record 0 "$desc"
  else
    if [ "$rc" -ne 0 ] && grep -q "$BLOCK_MARK" "$log"; then
      record 1 "$desc" "오탐 — 정당한 변경을 차단했다: $(grep -m1 "$BLOCK_MARK" "$log" | head -c 140)"
      return
    fi
    record 0 "$desc"
  fi
}

# 시연 1 (양성) — 규칙 삭제. 추가된 줄이 없어 기존 P13 은 원리적으로 못 본다.
setup_delete_rule() {
  python3 - "$PATTERNS" <<'PY'
import sys
p = sys.argv[1]
lines = open(p).read().splitlines(True)
out = [l for l in lines if not l.startswith('AKIA')]
assert len(out) < len(lines), "삭제 대상 없음"
open(p, 'w').write(''.join(out))
PY
  git add "$PATTERNS"
}
run_case "비밀 규칙 삭제는 차단된다" block setup_delete_rule

# 시연 2 (양성) — 수량 하한 상향. Codex 가 지목한 형태. 문법은 멀쩡하고 탐지력만 사라진다.
setup_raise_quantifier() {
  sed -i.bak 's/AKIA\[0-9A-Z\]{16}/AKIA[0-9A-Z]{99}/' "$PATTERNS" && rm -f "$PATTERNS.bak"
  grep -q 'AKIA\[0-9A-Z\]{99}' "$PATTERNS" || return 1
  git add "$PATTERNS"
}
run_case "수량 하한 상향({16}→{99})은 차단된다" block setup_raise_quantifier

# 시연 3 (양성) — 파일을 통째로 비운다.
setup_empty_file() { : > "$PATTERNS" && git add "$PATTERNS"; }
run_case "규칙 파일을 비우면 차단된다" block setup_empty_file

# 시연 4 (음성 · 정당한 축소) — 규칙과 카나리를 **함께** 지운다. 삭제가 diff 에 남는다.
setup_shrink_with_canary() {
  python3 - "$PATTERNS" "$CANARY_POS" <<'PY'
import sys
p, c = sys.argv[1], sys.argv[2]
lines = open(p).read().splitlines(True)
open(p, 'w').write(''.join([l for l in lines if not l.startswith('AKIA')]))
cl = open(c).read().splitlines(True)
open(c, 'w').write(''.join([l for l in cl if 'AWS 액세스' not in l]))
PY
  git add "$PATTERNS" "$CANARY_POS"
}
run_case "카나리를 함께 고친 축소는 통과한다 (정당한 경로)" pass setup_shrink_with_canary

# 시연 5 (음성 · 오탐 대조) — 규칙을 **추가**한다. 탐지력이 늘어나는 변경은 막으면 안 된다.
setup_add_rule() {
  printf '\n# 시연용 추가 규칙\nDEMOSECRET[0-9A-Z]{20}\n' >> "$PATTERNS"
  git add "$PATTERNS"
}
run_case "규칙 추가는 통과한다 (탐지력 증가)" pass setup_add_rule

# 시연 6 (양성 · 카나리 자체 축소) — 카나리를 하한 미만으로 줄인다.
# 카나리가 조용히 줄면 다음 축소를 감시할 수 없다 — 서서히 무장해제된다. 실측으로
# 겪었다: 시험 중 고정물을 복원하지 못해 양성이 4 → 3건이 되었고, **그 상태에서 수량자
# 상향이 "탐지력 유지"로 통과했다**. 검사기가 자기 입력이 줄어든 것을 못 보면 판정
# 전체가 조용히 무의미해진다. 이 시연이 없으면 하한을 0 으로 바꿔도 전부 초록이다(S3 생존).
setup_shrink_canary() {
  python3 - "$CANARY_POS" <<'PYEOF'
import sys
p = sys.argv[1]
lines = open(p).read().splitlines(True)
head = [l for l in lines if l.startswith('#')]
body = [l for l in lines if not l.startswith('#') and l.strip()]
assert len(body) > 2, "줄일 대상이 부족하다"
open(p, 'w').write(''.join(head + body[:2]))
PYEOF
  git add "$CANARY_POS"
}
run_case "카나리를 하한 미만으로 줄이면 차단된다" block setup_shrink_canary

# 시연 7 (양성 · stage/worktree 미끼) — 삭제를 stage 하고 **작업트리만 되돌린다**.
# 2026-09-11 Codex 적대검증 C3 실측: staged 유효줄 2 / worktree 유효줄 4 인 상태에서
# 커밋이 rc=0 으로 통과했다. 판정기가 커밋될 내용이 아니라 화면에 열린 파일을 봤다.
# 이 시연이 없으면 검사기를 작업트리 읽기로 되돌려도 전부 초록이다.
setup_stage_delete_restore_worktree() {
  python3 - "$CANARY_POS" <<'PYEOF'
import sys
p = sys.argv[1]
lines = open(p).read().splitlines(True)
head = [l for l in lines if l.startswith('#')]
body = [l for l in lines if not l.startswith('#') and l.strip()]
assert len(body) > 2, "줄일 대상이 부족하다"
open(p, 'w').write(''.join(head + body[:2]))
PYEOF
  git add "$CANARY_POS"
  # 화면(작업트리)만 원래대로 되돌린다 — 커밋될 내용은 줄어든 채로 남는다.
  git show "HEAD:$CANARY_POS" > "$CANARY_POS" || return 1
  git diff --quiet -- "$CANARY_POS" && return 1   # 작업트리가 HEAD 와 같아야 미끼가 성립한다
  return 0
}
run_case "삭제를 stage 하고 작업트리만 복원해도 차단된다 (인덱스 판정)" block setup_stage_delete_restore_worktree

# 시연 8 (양성 · 하한 위 감소) — 카나리를 하한 위에서 한 건만 줄인다(규칙은 그대로).
# 하한만 두면 하한 위에서의 감소가 자유롭다. 실측으로 4 → 3 이 통과했고, 그 상태에서
# 수량자 상향이 "탐지력 유지"로 넘어갔다 — 감시 대상이 줄어든 것을 판정기가 못 봤다.
setup_shrink_canary_above_floor() {
  python3 - "$CANARY_POS" <<'PYEOF'
import sys
p = sys.argv[1]
lines = open(p).read().splitlines(True)
head = [l for l in lines if l.startswith('#')]
body = [l for l in lines if not l.startswith('#') and l.strip()]
assert len(body) >= 4, "하한 위에서 줄이려면 최소 4건이 필요하다"
open(p, 'w').write(''.join(head + body[:-1]))
PYEOF
  git add "$CANARY_POS"
}
run_case "규칙은 그대로 둔 채 카나리만 한 건 줄이면 차단된다 (하한 위)" block setup_shrink_canary_above_floor

# 시연 9 (구분 · 실행 불가) — 고정물을 인덱스에서 통째로 없앤다.
# fail-closed 로 차단되기는 하지만 그것은 **판정**이 아니라 **실행 불가**다(exit 2).
# 둘을 같은 신호로 세면 mktemp 거부·고정물 부재 같은 환경 사고가 "차단됨"으로 계수되고,
# 구현이 0줄이어도 전부 초록이 난다. 이 시연은 두 신호가 실제로 갈라지는지를 본다.
setup_remove_fixture_from_index() {
  git rm -q --cached "$CANARY_POS"
}
run_case "고정물이 인덱스에 없으면 실행 불가로 끊긴다 (exit 2 · 판정 실패와 구분)" block setup_remove_fixture_from_index 2

# 시연 7 (배선) — 검사기가 있어도 훅이 부르지 않으면 무방비다.
if grep -q 'check-secret-detection-regression\.sh' hooks/pre-commit; then
  record 0 "hooks/pre-commit 이 탐지 회귀 검사기를 호출한다 (배선)"
else
  record 1 "hooks/pre-commit 이 탐지 회귀 검사기를 호출한다 (배선)" "훅에 호출이 없다"
fi

echo
echo "CHECKED: $checked"
[ "$fail" -ne 0 ] && { echo "RESULT: 불합격 — 비밀 탐지력 축소가 차단되지 않는다"; exit 1; }
echo "RESULT: 합격 — 조용한 탐지력 축소는 커밋되지 않는다"
exit 0
