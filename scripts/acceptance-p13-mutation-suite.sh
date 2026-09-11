#!/usr/bin/env bash
# acceptance-p13-mutation-suite.sh — P13 방어선 13종을 한자리에서 공격한다.
#
# 왜 한자리에 모으나 (착수 문서 §필수 mutation 목록):
#   "하나를 막으면 다른 하나가 열린다"를 이 저장소는 이미 네 번 겪었다. 검사기마다
#   자기 인수 검사가 있지만, 그것들은 각자의 사유로만 판정한다. 공격자는 사유를 가리지
#   않는다 — 지우든, 이름을 바꾸든, 내용을 비우든, 승인을 위조하든 결과만 같으면 된다.
#   그래서 **결과 기준**으로 한 번 더 훑는다: 이 커밋이 통과하는가.
#
# 계약: exit 0 (전 변조 사망 + 대조군 통과) | exit 1 (생존) | exit 2 (셋업 실패 · fail-closed)
#   불변식: 모든 변조는 mktemp -d 안의 clone 에서 수행한다. 원본 저장소를 건드리지 않는다.
#
# 각 변조는 넷을 만족해야 "사망"으로 센다:
#   ① 셋업이 실제로 파일을 바꿨는가 — diff 로 확인한다. 변조가 안 걸린 채 "생존"으로
#      세는 사고가 2026-09-11 세션에만 두 번 났다.
#   ② 스테이징이 만들어졌는가 — 빈 커밋은 훅 이전에 거부되어 위양성이 된다.
#   ③ 훅 ON 에서 차단되고 BLOCKED 사유가 남았는가.
#   ④ 훅 OFF 에서는 통과하는가 — 대조군 없이는 "원래 안 되는 커밋"과 구분되지 않는다.
#
# 대조군(양성 통제): 아무 해도 없는 변경은 **통과해야** 한다. 전부 막는 벽은 게이트가
#   아니라 고장이다. 차단과 통과를 한 쌍으로 재지 않으면 그 구분을 못 한다.
set -uo pipefail

unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE GIT_OBJECT_DIRECTORY \
      GIT_ALTERNATE_OBJECT_DIRECTORIES GIT_COMMON_DIR GIT_PREFIX GIT_QUARANTINE_PATH

WF=.github/workflows/verify.yml
PATTERNS=.secret-patterns.default
FIX_DIR=scripts/verify/fixtures/secret-canaries
VICTIM_SCRIPT=scripts/acceptance-guard-global-skill-files.sh

REPO=$(git rev-parse --show-toplevel 2>/dev/null) || {
  echo "FAIL: git 저장소가 아니다 (fail-closed)"; echo "CHECKED: 0"; exit 2; }
cd "$REPO" || { echo "FAIL: 저장소 루트로 이동 실패"; echo "CHECKED: 0"; exit 2; }
for f in "$WF" hooks/pre-commit "$PATTERNS" "$VICTIM_SCRIPT"; do
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

# clone 은 HEAD 를 받는다. 지금 판본의 검사기·고정물·정본을 작업트리 사본으로 덮고
# **커밋까지** 한다 — 검사기들이 인덱스와 HEAD 를 읽으므로 cp 만으로는 판정 입력이
# 바뀌지 않는다. 이 줄이 없으면 어긋난 조합을 시험하게 되고 변이가 전부 생존한다.
INSTALL="hooks/pre-commit $PATTERNS $WF verify.sh suppressions.yaml
  docs/sot/mechanism-registry.yaml
  $FIX_DIR/positive.txt $FIX_DIR/negative.txt $FIX_DIR/manifest.txt
  scripts/verify/check-workflow-deletion.sh
  scripts/verify/check-secret-detection-regression.sh
  scripts/verify/check-secret-canary-coverage.sh"
INSTALLED=""
for f in $INSTALL; do
  [ -f "$f" ] || { echo "FAIL: 설치 대상이 없다 — $f"; echo "CHECKED: 0"; exit 2; }
  mkdir -p "$CLONE/$(dirname "$f")" || { echo "FAIL: 디렉터리 생성 실패 — $f"; echo "CHECKED: 0"; exit 2; }
  cp -p "$f" "$CLONE/$f" || { echo "FAIL: 설치 실패 — $f"; echo "CHECKED: 0"; exit 2; }
  chmod +x "$CLONE/$f" 2>/dev/null
  INSTALLED="$INSTALLED $f"
done
( cd "$CLONE" && git add -A -- $INSTALLED \
  && { git diff --cached --quiet \
       || git -c user.name=a -c user.email=a@b -c core.hooksPath=/dev/null \
            commit -qm "작업트리 사본 설치 (변조 기준점)"; } ) >"$SANDBOX/seed.err" 2>&1 || {
  echo "FAIL: 작업트리 사본 커밋 실패 — $(head -2 "$SANDBOX/seed.err" | tr '\n' ' ')"
  echo "CHECKED: 0"; exit 2; }
BASE=$(cd "$CLONE" && git rev-parse HEAD) || {
  echo "FAIL: 기준 커밋을 읽지 못했다"; echo "CHECKED: 0"; exit 2; }
( cd "$CLONE" && git diff --quiet "$BASE" -- $INSTALLED ) || {
  echo "FAIL: 설치본이 기준 커밋에 반영되지 않았다 — 변조 전체가 무효다"
  echo "CHECKED: 0"; exit 2; }

# mutate <번호·이름> <die|live> <셋업 함수>
#   die  = 차단되어야 한다 (공격)
#   live = 통과해야 한다 (대조군)
mutate() {
  local name="$1" expect="$2" setup="$3" log="$SANDBOX/log.$checked"
  ( cd "$CLONE" && git reset --hard --quiet "$BASE" && git clean -qfdx ) 2>/dev/null
  if ! ( cd "$CLONE" && $setup ) >"$SANDBOX/setup.err" 2>&1; then
    record 1 "$name" "셋업 실패 — 변조를 만들지 못했다: $(head -1 "$SANDBOX/setup.err")"; return
  fi
  # ① 변조가 실제로 파일에 적용됐는가. 안 걸린 채 "생존"으로 세는 것이 이 저장소의 상습 사고다.
  if ( cd "$CLONE" && git diff --quiet "$BASE" ) && ( cd "$CLONE" && git diff --cached --quiet "$BASE" ); then
    record 1 "$name" "변조가 파일에 적용되지 않았다 — 이 항목은 무효다"; return
  fi
  # ② 스테이징이 만들어졌는가.
  if ( cd "$CLONE" && git diff --cached --quiet ); then
    record 1 "$name" "스테이징이 비었다 — 훅 이전에 거부되어 위양성이 된다"; return
  fi
  local rc=0
  ( cd "$CLONE" && git -c user.name=a -c user.email=a@b commit -m mut ) >"$log" 2>&1 || rc=$?
  if [ "$expect" = die ]; then
    if [ "$rc" -eq 0 ]; then
      record 1 "$name" "★생존 — 커밋이 통과했다 (rc=0)"; return
    fi
    if ! grep -q 'BLOCKED:' "$log"; then
      record 1 "$name" "차단은 됐으나 BLOCKED 사유가 없다 (rc=$rc): $(head -1 "$log" | head -c 120)"; return
    fi
    local orc=0
    ( cd "$CLONE" && git -c core.hooksPath=/dev/null -c user.name=a -c user.email=a@b commit -m mut-off ) >"$log.off" 2>&1 || orc=$?
    if [ "$orc" -ne 0 ]; then
      record 1 "$name" "훅 OFF 에서도 실패했다 (rc=$orc) — 훅이 원인이 아니다"; return
    fi
    record 0 "$name — 사유: $(grep -m1 'BLOCKED:' "$log" | sed 's/^BLOCKED: //' | head -c 70)"
  else
    if [ "$rc" -ne 0 ]; then
      record 1 "$name" "대조군이 차단됐다 (rc=$rc) — 전부 막는 벽은 게이트가 아니다: $(grep -m1 'BLOCKED:' "$log" | head -c 120)"
      return
    fi
    record 0 "$name"
  fi
}

# 워크플로에서 지울 실행 줄을 실제 파일에서 고른다. 하드코딩하면 워크플로가 바뀐 뒤
# 이 항목이 조용히 무의미해진다(셋업 실패를 합격으로 세는 경로).
pick_run_line() {  # <스크립트 경로 조각> → 줄 번호
  grep -n "run-acceptance\.sh $1" "$CLONE/$WF" | head -1 | cut -d: -f1
}

m01_delete_protected_script() { git rm -q "$VICTIM_SCRIPT"; }
m02_rename_protected_script() { git mv "$VICTIM_SCRIPT" "${VICTIM_SCRIPT}.bak"; }
m03_delete_workflow_call() {
  local n; n=$(pick_run_line "$VICTIM_SCRIPT"); [ -n "$n" ] || return 1
  sed -i.bak "${n}d" "$WF" && rm -f "$WF.bak" && git add "$WF"
}
m04_stub_protected_script() {
  printf '#!/usr/bin/env bash\nexit 0\n' > "$VICTIM_SCRIPT" && git add "$VICTIM_SCRIPT"
}
m05_delete_patterns_file() { git rm -q "$PATTERNS"; }
m06_delete_one_pattern() {
  python3 - "$PATTERNS" <<'PYEOF'
import sys
p = sys.argv[1]
lines = open(p).read().splitlines(True)
out, skip = [], False
for l in lines:
    if l.strip() == '# @id: aws-akia':
        skip = True; continue
    if skip:
        skip = False
        if l.startswith('AKIA'):
            continue
    out.append(l)
assert len(out) < len(lines), "삭제 대상 없음"
open(p, 'w').write(''.join(out))
PYEOF
  git add "$PATTERNS"
}
m07_pattern_match_never() {
  python3 - "$PATTERNS" <<'PYEOF'
import sys
p = sys.argv[1]
lines = open(p).read().splitlines(True)
never = 'THIS_WILL_NEVER' + '_MATCH_ANY_VALUE'
for i, l in enumerate(lines):
    if l.startswith('ASIA['):
        lines[i] = never + '\n'
        break
else:
    raise SystemExit("ASIA 규칙을 찾지 못했다")
open(p, 'w').write(''.join(lines))
PYEOF
  git add "$PATTERNS"
}
append_suppression() {  # <owner> <expiry> — 나머지 필드는 고정
  printf '\n- check: "retire:%s"\n  reason: >-\n    변조용 항목.\n  owner: %s\n  expiry: %s\n  issue: >-\n    변조용 항목.\n' \
    "$VICTIM_SCRIPT" "$1" "$2" >> suppressions.yaml
}
m08_self_approved_retire() {
  local n exp; n=$(pick_run_line "$VICTIM_SCRIPT"); [ -n "$n" ] || return 1
  exp=$(python3 -c 'import datetime;print((datetime.date.today()+datetime.timedelta(days=365)).isoformat())')
  sed -i.bak "${n}d" "$WF" && rm -f "$WF.bak"
  append_suppression attacker "$exp"
  git rm -q "$VICTIM_SCRIPT" && git add "$WF" suppressions.yaml
}
m09_suppression_without_expiry() {
  printf '\n- check: no-expiry-demo\n  reason: >-\n    변조용 항목.\n  owner: attacker\n  issue: >-\n    변조용 항목.\n' >> suppressions.yaml
  git add suppressions.yaml
}
m10_suppression_past_expiry() { append_suppression attacker 2020-01-01; git add suppressions.yaml; }
m11_suppression_blank_owner() {
  local exp; exp=$(python3 -c 'import datetime;print((datetime.date.today()+datetime.timedelta(days=365)).isoformat())')
  append_suppression "" "$exp"; git add suppressions.yaml
}
m12_delete_canary_fixture() { git rm -q "$FIX_DIR/positive.txt"; }
m13_delete_regression_ci_step() {
  local n; n=$(pick_run_line "scripts/acceptance-secret-detection-regression.sh"); [ -n "$n" ] || return 1
  sed -i.bak "${n}d" "$WF" && rm -f "$WF.bak" && git add "$WF"
}
control_benign_change() {
  printf '\n변조 스위트 대조군 — 해가 없는 문서 한 줄.\n' >> "$FIX_DIR/README.md"
  git add "$FIX_DIR/README.md"
}

mutate "M01 보호 스크립트 삭제"                 die m01_delete_protected_script
mutate "M02 보호 스크립트 이름 변경"             die m02_rename_protected_script
mutate "M03 워크플로 호출 줄만 삭제"             die m03_delete_workflow_call
mutate "M04 스크립트를 exit 0 껍데기로 치환"     die m04_stub_protected_script
mutate "M05 비밀 규칙 파일 통째 삭제"            die m05_delete_patterns_file
mutate "M06 규칙 한 개 삭제"                     die m06_delete_one_pattern
mutate "M07 규칙을 match-never 로 변경"          die m07_pattern_match_never
mutate "M08 자기 승인 은퇴(같은 커밋 승인)"      die m08_self_approved_retire
mutate "M09 expiry 없는 억제 추가"               die m09_suppression_without_expiry
mutate "M10 expiry 과거 날짜"                    die m10_suppression_past_expiry
mutate "M11 owner 공백"                          die m11_suppression_blank_owner
mutate "M12 카나리 고정물 삭제"                  die m12_delete_canary_fixture
mutate "M13 회귀 검사 CI 스텝 제거"              die m13_delete_regression_ci_step
mutate "대조군 — 해 없는 문서 변경은 통과한다"   live control_benign_change

# 배선 — 이 스위트가 CI 에서 돌지 않으면, 로컬을 건너뛴 push 에는 아무 소용이 없다.
if grep -q 'acceptance-p13-mutation-suite\.sh' "$WF"; then
  record 0 "CI 워크플로가 이 변조 스위트를 실행한다 (배선)"
else
  record 1 "CI 워크플로가 이 변조 스위트를 실행한다 (배선)" "$WF 에 실행 줄이 없다"
fi

echo
echo "CHECKED: $checked"
[ "$fail" -ne 0 ] && { echo "RESULT: 불합격 — 생존한 변조가 있다"; exit 1; }
echo "RESULT: 합격 — 변조 13종 전부 사망 · 대조군 통과"
exit 0
