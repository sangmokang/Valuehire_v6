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
CHECKER_SRC=scripts/verify/check-workflow-deletion.sh
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

# 검사기도 **작업트리 사본**으로 덮는다. clone 은 HEAD 를 받으므로, 이 줄이 없으면
# 훅은 지금 상태를 쓰는데 검사기는 커밋된 옛 버전을 쓰는 어긋난 조합을 시험하게 된다.
# 실측(2026-09-09): 그 상태에서는 검사기를 어떻게 망가뜨려도 5/5 초록이 나왔다 —
# 변이 4종(차단 끄기·범위 필터 제거·집합 비교 뒤집기·주석 제외 제거)이 전부 생존했다.
# 생존은 "도달 불가"가 아니라 "시험이 대상을 안 본다"는 뜻이었다.
if [ -f "$CHECKER_SRC" ]; then
  mkdir -p "$CLONE/$(dirname "$CHECKER_SRC")" || {
    echo "FAIL: 검사기 디렉터리 생성 실패"; echo "CHECKED: 0"; exit 2; }
  cp -p "$CHECKER_SRC" "$CLONE/$CHECKER_SRC" || {
    echo "FAIL: 검사기 설치 실패"; echo "CHECKED: 0"; exit 2; }
  chmod +x "$CLONE/$CHECKER_SRC"
fi

# 시연마다 여기로 되돌린다. 시연 4 는 seed 커밋을 만들어 HEAD 를 옮기므로 SHA 로 고정한다.
BASE=$(cd "$CLONE" && git rev-parse HEAD) || {
  echo "FAIL: 기준 커밋을 읽지 못했다"; echo "CHECKED: 0"; exit 2; }

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
  # 인덱스까지 되돌린다. checkout -- . 은 작업트리만 복원하므로 앞 시연의 스테이징이
  # 남아, 다음 시연의 셋업이 엉뚱한 줄을 지우고 "차단되지 않았다"는 거짓 신호를 낸다.
  ( cd "$CLONE" && git reset --hard --quiet "$BASE" && git clean -qfdx ) 2>/dev/null
  # reset/clean 이 작업트리 사본을 되돌리므로 매 시연 직전에 다시 덮는다.
  if [ -f "$CHECKER_SRC" ]; then
    mkdir -p "$CLONE/$(dirname "$CHECKER_SRC")" 2>/dev/null
    cp -p "$CHECKER_SRC" "$CLONE/$CHECKER_SRC" 2>/dev/null && chmod +x "$CLONE/$CHECKER_SRC"
  fi
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

# 시연 5 (음성 · 주석 대조) — 워크플로 주석에서 스크립트 이름이 든 줄을 지운다.
# 워크플로 주석에는 "acceptance-0-2 는 여기서 돌리지 않는다" 같은 설명이 흔하다.
# 주석 삭제는 검사를 끄지 않으므로 통과해야 한다. 이 시연이 없으면 검사기에서 주석
# 제외를 빼도 전부 초록이었다(2026-09-09 변이 M4 생존 실측).
# 아무 주석이나 고르면 안 된다. 그 주석이 언급한 스크립트가 실행 줄에도 남아 있으면
# D-A 가 비어 어떤 구현이든 통과해, 시연이 아무것도 판별하지 못한다(M4 생존 실측).
# 조건: ① 주석에만 등장하고 ② 저장소에 실존하는 경로. 그래야 주석 제외를 빼는 순간 빨개진다.
setup_delete_comment() {
  local active cl p found=""
  active=$(grep -v '^[[:space:]]*#' "$WF" | grep -oE '[A-Za-z0-9_][A-Za-z0-9_./-]*\.sh' | LC_ALL=C sort -u)
  while IFS=: read -r cl rest; do
    [ -n "$cl" ] || continue
    for p in $(printf '%s' "$rest" | grep -oE '[A-Za-z0-9_][A-Za-z0-9_./-]*\.sh'); do
      printf '%s\n' "$active" | grep -qx "$p" && continue
      git ls-files --error-unmatch -- "$p" >/dev/null 2>&1 || continue
      found="$cl"; break
    done
    [ -n "$found" ] && break
  done < <(grep -nE '^[[:space:]]*#.*[A-Za-z0-9_./-]+\.sh' "$WF")
  [ -n "$found" ] || return 1
  sed -i.bak "${found}d" "$WF" && rm -f "$WF.bak" && git add "$WF"
}
run_case "워크플로 주석 줄 삭제는 통과한다 (주석 대조)" pass setup_delete_comment

# (옛 시연 제거) "실행 줄과 스크립트를 함께 지우면 통과한다"는 **자동 면제**를 시험하던
# 것이다. 2026-09-10 Codex 적대검증에서 그 면제가 공격과 정당한 은퇴를 구분하지 못한다는
# 것이 드러나(233줄 검사가 흔적 없이 사라지는데 통과) 정책을 바꿨다. 이제 은퇴는 막지
# 않되 suppressions.yaml 승인을 요구한다 — 아래 "승인 없는 은퇴"·"승인된 은퇴" 두 시연이
# 그 자리를 대신하며, 검사기의 존재 확인 분기도 그 쌍이 잡는다(옛 M5 변이의 대체).

# 시연 7 (양성 · 파일 통째) — 워크플로 파일 자체를 지운다. 가장 거친 약화이고,
# 줄 단위 diff 만 보면 놓친다(스테이징 목록에서 D 를 빼면 이 시연이 생존했다 · M6).
setup_delete_workflow() {
  git rm -q "$WF"
}
run_case "워크플로 파일 통째 삭제는 차단된다" block setup_delete_workflow

# 시연 8 (양성 · 이름 변경) — 워크플로 파일을 GitHub 이 안 읽는 확장자로 바꾼다.
# `git mv verify.yml verify.yml.bak` 한 번으로 CI 전 스텝이 사라진다. 첫 판은 파일별
# diff 로 짜서 이것을 놓쳤다(2026-09-09 감사 실측: rc=0 으로 통과). 이 저장소는
# 2026-08-09 에 `git mv notes.txt leak.db` 로 같은 함정을 이미 한 번 맞았다.
setup_rename_workflow() {
  git mv "$WF" "${WF}.bak"
}
run_case "워크플로 파일 이름 변경(.yml→.bak)은 차단된다" block setup_rename_workflow

# 시연 9 (음성 · 정당한 이름 변경) — 여전히 워크플로인 다른 .yml 로 옮긴다.
# 이것까지 막으면 워크플로를 영원히 정리하지 못한다.
setup_rename_to_yml() {
  git mv "$WF" ".github/workflows/renamed-verify.yml"
}
run_case "다른 .yml 로 이름을 바꾸면 통과한다 (정당한 정리)" pass setup_rename_to_yml

# 시연 10 (양성 · 흔적 없는 은퇴) — 인수 스크립트와 그 CI 스텝을 **한 커밋에 함께** 지운다.
# 이전 판은 "스크립트가 저장소에서 사라졌으면 정당한 제거"로 자동 면제했다. 그래서 공격과
# 정당한 은퇴를 구분하지 못했다(2026-09-10 Codex 적대검증 실측: 233줄짜리 검사가 흔적 없이
# 사라지는데 커밋이 통과했다). 최종 마커 검수도 현재 트리 글로브로 기대 목록을 만들기 때문에
# 사라진 검사를 요구하지 않는다 — 두 방어선이 같은 맹점을 공유한다.
# 은퇴는 막지 않되 **기록을 남기게** 한다: suppressions.yaml 의 승인 없이는 차단.
setup_retire_without_approval() {
  local v="scripts/acceptance-guard-global-skill-files.sh"
  [ -f "$v" ] || return 1
  python3 - "$v" <<'PYEOF'
import re, sys
v = sys.argv[1]
p = '.github/workflows/verify.yml'
s = open(p).read()
n = re.sub(r'\n      - name: [^\n]*\n(?:        [^\n]*\n)*?        run: bash scripts/verify/run-acceptance\.sh ' + re.escape(v) + r'\n', '\n', s, count=1)
assert n != s, "워크플로 스텝 삭제 실패"
open(p, 'w').write(n)
PYEOF
  git rm -q "$v" && git add .github/workflows/verify.yml
}
run_case "승인 없는 은퇴(스크립트+스텝 동시 삭제)는 차단된다" block setup_retire_without_approval

# 시연 11 (양성 · 자기 승인) — 같은 삭제를 **같은 커밋에 쓴 승인**과 함께 한다.
# 2026-09-11 Codex 적대검증 C1 실측: 이 형태로 233줄짜리 검사가 rc=0 으로 사라졌다.
# 승인을 인덱스(커밋될 내용)에서 읽으면 지우는 사람이 스스로를 승인할 수 있다 —
# 자물쇠 옆에 열쇠를 걸어 둔 것과 같다. 승인은 **기준 브랜치에 이미 있던 것**만 센다.
setup_retire_self_approved() {
  local v="scripts/acceptance-guard-global-skill-files.sh"
  [ -f "$v" ] || return 1
  python3 - "$v" <<'PYEOF'
import re, sys, datetime
v = sys.argv[1]
p = '.github/workflows/verify.yml'
s = open(p).read()
n = re.sub(r'\n      - name: [^\n]*\n(?:        [^\n]*\n)*?        run: bash scripts/verify/run-acceptance\.sh ' + re.escape(v) + r'\n', '\n', s, count=1)
assert n != s, "워크플로 스텝 삭제 실패"
open(p, 'w').write(n)
exp = (datetime.date.today() + datetime.timedelta(days=30)).isoformat()
with open('suppressions.yaml', 'a') as f:
    f.write('\n- check: "retire:%s"\n  reason: >-\n    시연용 승인 — 이 검사를 은퇴시킨다.\n  owner: attacker\n  expiry: %s\n  issue: >-\n    시연 전용 항목.\n' % (v, exp))
PYEOF
  git rm -q "$v" && git add .github/workflows/verify.yml suppressions.yaml
}
run_case "같은 커밋에 쓴 자기 승인은 차단된다 (선재성)" block setup_retire_self_approved

# 시연 12 (음성 · 선재 승인) — 승인을 **먼저 커밋**하고 다음 커밋에서 삭제한다.
# 이 경로까지 막으면 검사를 영원히 은퇴시키지 못하는 벽이 된다. 은퇴를 막는 것이
# 목적이 아니라, 승인이 삭제보다 **먼저** 기록되게 하는 것이 목적이다.
setup_retire_preapproved() {
  local v="scripts/acceptance-guard-global-skill-files.sh"
  [ -f "$v" ] || return 1
  python3 - "$v" <<'PYEOF'
import sys, datetime
v = sys.argv[1]
exp = (datetime.date.today() + datetime.timedelta(days=30)).isoformat()
with open('suppressions.yaml', 'a') as f:
    f.write('\n- check: "retire:%s"\n  reason: >-\n    시연용 승인 — 이 검사를 은퇴시킨다.\n  owner: sangmokang\n  expiry: %s\n  issue: >-\n    시연 전용 항목.\n' % (v, exp))
PYEOF
  git add suppressions.yaml
  git -c user.name=a -c user.email=a@b -c core.hooksPath=/dev/null commit -qm "승인 선행 기록" || return 1
  python3 - "$v" <<'PYEOF'
import re, sys
v = sys.argv[1]
p = '.github/workflows/verify.yml'
s = open(p).read()
n = re.sub(r'\n      - name: [^\n]*\n(?:        [^\n]*\n)*?        run: bash scripts/verify/run-acceptance\.sh ' + re.escape(v) + r'\n', '\n', s, count=1)
assert n != s, "워크플로 스텝 삭제 실패"
open(p, 'w').write(n)
PYEOF
  git rm -q "$v" && git add .github/workflows/verify.yml
}
run_case "선재 승인 뒤 다음 커밋의 은퇴는 통과한다 (정당한 경로)" pass setup_retire_preapproved

# 시연 13 (양성 · 항목 스키마) — 승인은 HEAD 에 선재하지만 owner 가 비어 있다.
# 필드를 파일 전체에서 **개수로만** 세면 앞 항목의 owner 를 빌려 쓰는 조합이 통과한다.
# hooks/pre-commit 의 총량 검사가 그 형태이고, 게다가 이 커밋은 suppressions.yaml 을
# 스테이징하지 않으므로 그 검사가 아예 돌지 않는다 — 항목 경계를 세는 쪽이 필요하다.
setup_retire_preapproved_bad_schema() {
  local v="scripts/acceptance-guard-global-skill-files.sh"
  [ -f "$v" ] || return 1
  python3 - "$v" <<'PYEOF'
import sys, datetime
v = sys.argv[1]
exp = (datetime.date.today() + datetime.timedelta(days=30)).isoformat()
with open('suppressions.yaml', 'a') as f:
    f.write('\n- check: "retire:%s"\n  reason: >-\n    시연용 승인 — owner 가 비었다.\n  owner:\n  expiry: %s\n  issue: >-\n    시연 전용 항목.\n' % (v, exp))
PYEOF
  git add suppressions.yaml
  git -c user.name=a -c user.email=a@b -c core.hooksPath=/dev/null commit -qm "스키마 위반 승인 선행 기록" || return 1
  python3 - "$v" <<'PYEOF'
import re, sys
v = sys.argv[1]
p = '.github/workflows/verify.yml'
s = open(p).read()
n = re.sub(r'\n      - name: [^\n]*\n(?:        [^\n]*\n)*?        run: bash scripts/verify/run-acceptance\.sh ' + re.escape(v) + r'\n', '\n', s, count=1)
assert n != s, "워크플로 스텝 삭제 실패"
open(p, 'w').write(n)
PYEOF
  git rm -q "$v" && git add .github/workflows/verify.yml
}
run_case "owner 가 빈 선재 승인은 차단된다 (항목 단위 스키마)" block setup_retire_preapproved_bad_schema

# 시연 12 (배선) — 검사기가 존재해도 훅이 부르지 않으면 무방비다.
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
