#!/usr/bin/env bash
# acceptance-p13-mutation-suite.sh — P13 방어선을 한자리에서 공격한다.
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
#   ③ 훅 ON 에서 **판정**으로 차단됐는가 — `BLOCKED:` 이지 `BLOCKED(실행불가):` 가 아니어야 한다.
#      실행 불가를 방어 성공으로 세면 검사기가 망가진 상태가 성공 장부로 남는다.
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
  scripts/verify/check-secret-canary-coverage.sh
  scripts/verify/suppression-approvals.awk"
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

# mutate <번호·이름> <die|live|unrunnable> <셋업 함수>
#   die        = **판정**으로 차단되어야 한다 (공격)
#   live       = 통과해야 한다 (대조군 · 전부 막는 벽은 게이트가 아니다)
#   unrunnable = 훅이 **실행 불가로 분류**해야 한다 (분류기 자기 시험)
#                검사기가 로그에 가짜 `BLOCKED:` 를 찍어도 판정으로 세지 않는지 본다
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
  if [ "$expect" = unrunnable ]; then
    if [ "$rc" -eq 0 ]; then record 1 "$name" "차단되지 않았다 (commit rc=0)"; return; fi
    local sum="$CLONE/.git/p13-last-block-summary" nv nu
    [ -f "$sum" ] || { record 1 "$name" "훅 분류 요약이 없다"; return; }
    nv=$(sed -n 's/.*verdict=\([0-9][0-9]*\).*/\1/p' "$sum")
    nu=$(sed -n 's/.*unrunnable=\([0-9][0-9]*\).*/\1/p' "$sum")
    if [ "${nv:-x}" != "0" ] || [ "${nu:-0}" -lt 1 ]; then
      record 1 "$name" "훅이 실행 불가로 분류하지 않았다 (판정 ${nv:-?}건 · 실행불가 ${nu:-?}건)"; return
    fi
    if ! grep -q '^BLOCKED:' "$log"; then
      record 1 "$name" "로그에 가짜 판정 줄이 없다 — 이 자기 시험이 아무것도 판별하지 못한다"; return
    fi
    record 0 "$name — 로그에 가짜 판정 줄이 있어도 훅 채널은 판정 0건 · 실행불가 ${nu}건"
    return
  fi
  if [ "$expect" = die ]; then
    if [ "$rc" -eq 0 ]; then
      record 1 "$name" "★생존 — 커밋이 통과했다 (rc=0)"; return
    fi
    if ! grep -q 'BLOCKED' "$log"; then
      record 1 "$name" "차단은 됐으나 BLOCKED 사유가 없다 (rc=$rc): $(head -1 "$log" | head -c 120)"; return
    fi
    # **판정**으로 막혔는지 본다. 훅은 두 가지를 구분해 찍는다:
    #   BLOCKED:          — 검사가 돌았고 위반을 찾았다 (판정)
    #   BLOCKED(실행불가): — 검사를 돌리지 못했다 (fail-closed 지만 판정은 아니다)
    # 둘을 섞으면 검사기·고정물·임시 디렉터리가 망가진 상태가 "방어 성공"으로 장부에
    # 남는다. 그러면 무엇을 실제로 막는지 알 수 없고 빈 구현도 초록이 된다(counter-AC 5).
    # 2026-09-11 V1 적대검증이 이 자리를 정확히 지목했다 — M12 가 exit=2 로 "사망" 처리됐다.
    # 훅이 .git 아래에 남긴 분류 요약을 읽는다. 로그 줄머리로 판단하면 **검사기가 쓴
    # 글자**를 훅의 분류로 착각한다 — 훅은 검사기 출력을 그대로 보여 주고 그 출력도
    # `BLOCKED:` 로 시작하며, 검사기 본문은 공격자가 고를 수 있다(V2 적대검증 결함 2).
    local sum="$CLONE/.git/p13-last-block-summary" nv=0 nu=0
    if [ ! -f "$sum" ]; then
      record 1 "$name" "훅 분류 요약이 없다 — 훅이 끝까지 돌지 않았거나 채널이 끊겼다"; return
    fi
    nv=$(sed -n 's/.*verdict=\([0-9][0-9]*\).*/\1/p' "$sum")
    nu=$(sed -n 's/.*unrunnable=\([0-9][0-9]*\).*/\1/p' "$sum")
    if [ -z "${nv:-}" ] || [ -z "${nu:-}" ]; then
      record 1 "$name" "훅 분류 요약을 읽지 못했다 — $(head -c 80 "$sum")"; return
    fi
    if [ "$nv" -lt 1 ]; then
      record 1 "$name" "판정이 아니라 실행 불가로만 막혔다 (판정 ${nv}건 · 실행불가 ${nu}건) — $(grep -m1 'BLOCKED(실행불가)' "$log" | head -c 90)"
      return
    fi
    local orc=0
    ( cd "$CLONE" && git -c core.hooksPath=/dev/null -c user.name=a -c user.email=a@b commit -m mut-off ) >"$log.off" 2>&1 || orc=$?
    if [ "$orc" -ne 0 ]; then
      record 1 "$name" "훅 OFF 에서도 실패했다 (rc=$orc) — 훅이 원인이 아니다"; return
    fi
    # 실행 불가 차단이 함께 있었으면 숨기지 않고 같이 보인다 — 판정이 있었다는 사실이
    # 실행 불가가 없었다는 뜻은 아니다.
    if [ "$nu" -gt 0 ]; then
      record 0 "$name — 훅 분류: 판정 ${nv}건 · 실행불가 ${nu}건 동반"
    else
      record 0 "$name — 훅 분류: 판정 ${nv}건"
    fi
  else
    if [ "$rc" -ne 0 ]; then
      record 1 "$name" "대조군이 차단됐다 (rc=$rc) — 전부 막는 벽은 게이트가 아니다: $(grep -m1 'BLOCKED' "$log" | head -c 120)"
      return
    fi
    # 통과했더라도 훅이 실제로 돌았는지 채널로 확인한다. 훅이 아예 안 돌면 이 대조군은
    # "게이트가 살아 있다"를 증명하지 못한다.
    local sum="$CLONE/.git/p13-last-block-summary"
    if [ ! -f "$sum" ] || ! grep -q 'verdict=0 unrunnable=0' "$sum"; then
      record 1 "$name" "대조군은 통과했으나 훅 분류 요약이 0/0 이 아니다 — $(head -c 80 "$sum" 2>/dev/null)"
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
# M14 (분류기 자기 시험) — 검사기가 로그에 **가짜 판정 줄**을 찍고 죽게 만든다.
# 훅은 검사기 출력을 그대로 보여 준다. 그 출력도 `BLOCKED:` 로 시작하므로, 로그 줄머리만
# 보면 검사기가 쓴 글자를 훅의 분류로 착각한다 — 검사기 본문은 공격자가 고를 수 있다.
# 이 시연은 스위트가 로그가 아니라 훅의 별도 채널을 읽는지 본다.
m14_forged_verdict_line() {
  printf '#!/usr/bin/env bash\necho "BLOCKED: 가짜 판정 — 이 줄은 검사기가 스스로 쓴 것이다"\nexit 2\n' \
    > scripts/verify/check-workflow-deletion.sh
  git add scripts/verify/check-workflow-deletion.sh
}

# M15 (양성) — CI 가 부르는 스크립트에서 실행 권한을 뗀다. 실행 줄은 그대로다.
m15_drop_exec_bit() {
  git update-index --chmod=-x "$VICTIM_SCRIPT"
  printf '\n# 모드만 바꾼다\n' >> "$VICTIM_SCRIPT"
  git add "$VICTIM_SCRIPT"
  git update-index --chmod=-x "$VICTIM_SCRIPT"
}

# M16 (양성 · 규칙 좁히기) — 카나리는 계속 잡히도록 규칙에 접두사를 박는다.
# 2026-09-11 V2 적대검증 결함 1(CRITICAL): 커버리지 25/25 와 탐지 집합 비교가 둘 다
# 초록인 채로 진짜 AWS 키가 통과했다. 착수 문서 §3층이 기록한 사고와 결과가 같다.
m16_narrow_rule() {
  python3 - "$PATTERNS" <<'PYEOF'
import sys
p = sys.argv[1]
lines = open(p).read().splitlines(True)
hit = 0
for i, l in enumerate(lines):
    if l.startswith('AKIA[') or l.startswith('ASIA['):
        lines[i] = l[:4] + '1234' + l[4:].replace('{16}', '{12}')
        hit += 1
assert hit == 2, "좁힐 규칙 2개를 찾지 못했다"
open(p, 'w').write(''.join(lines))
PYEOF
  git add "$PATTERNS"
}

# M17 (양성 · 껍데기 치환) — CI 가 부르는 스크립트 본문을 합격 문구 출력기로 바꾼다.
# `grep PASS` 만 보면 여섯 줄짜리 echo 가 통과한다(V2 적대검증 결함 5).
m17_hollow_called_script() {
  printf '#!/usr/bin/env bash\necho "PASS: 주장만 출력"\necho "CHECKED: 1"\nexit 0\n' > "$VICTIM_SCRIPT"
  git add "$VICTIM_SCRIPT"
}

# M18 (음성 · 승인된 좁히기) — 좁히기 승인을 **먼저 커밋**하고 그 규칙만 좁힌다.
# 이것까지 막으면 오탐을 줄이는 정당한 경계 보정을 영영 못 한다(2026-08-12 D4·D5 가 그런 변경이었다).
m18_approved_narrow() {
  local exp
  exp=$(python3 -c 'import datetime;print((datetime.date.today()+datetime.timedelta(days=90)).isoformat())')
  printf '\n- check: "narrow:aws-akia"\n  reason: >-\n    오탐 보정을 위해 범위를 좁힌다.\n  owner: sangmokang\n  expiry: %s\n  issue: >-\n    시연 전용 항목.\n' "$exp" >> suppressions.yaml
  git add suppressions.yaml
  git -c user.name=a -c user.email=a@b -c core.hooksPath=/dev/null commit -qm "좁히기 승인 선행 기록" || return 1
  python3 - "$PATTERNS" <<'PYEOF'
import sys
p = sys.argv[1]
lines = open(p).read().splitlines(True)
for i, l in enumerate(lines):
    if l.startswith('AKIA['):
        lines[i] = l[:4] + '1234' + l[4:].replace('{16}', '{12}')
        break
else:
    raise SystemExit("AKIA 규칙을 찾지 못했다")
open(p, 'w').write(''.join(lines))
PYEOF
  git add "$PATTERNS"
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
mutate "M16 규칙 좁히기 (카나리만 계속 잡기)"    die m16_narrow_rule
mutate "M17 호출 스크립트를 합격문구 출력기로"   die m17_hollow_called_script
mutate "M18 승인된 좁히기는 통과한다 (정당한 경로)" live m18_approved_narrow
mutate "M14 검사기가 찍은 가짜 판정 줄"          unrunnable m14_forged_verdict_line
mutate "M15 호출되는 스크립트의 실행 권한 제거"  die m15_drop_exec_bit
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
echo "RESULT: 합격 — 변조 전부 사망 · 분류기 자기 시험·대조군 통과"
exit 0
