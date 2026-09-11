#!/usr/bin/env bash
# acceptance-secret-canary-coverage.sh — 카나리가 대표하지 않는 비밀 규칙을 막는가.
#
# 왜 필요한가 (2026-09-11 Codex 적대검증 C2):
#   탐지 회귀 검사는 "기준에서 잡히던 값이 계속 잡히는가"만 본다. 어떤 카나리도
#   대표하지 않는 규칙은 통째로 사라져도 검출 집합이 안 변해 조용히 통과했다.
#   실측: 규칙 25개 중 카나리에 연결된 것은 4개뿐. ASIA 규칙을 지워도 전부 초록이었다.
#
# 계약: exit 0 (전 시연 합격) | exit 1 (하나라도 불합격) | exit 2 (셋업 실패 · fail-closed)
#   불변식: 모든 시연은 mktemp -d 안의 clone 에서 수행한다. 원본 저장소를 건드리지 않는다.
#
# 판정 구조는 acceptance-p13-deletion 과 같다. 각 시연은 셋 다 만족해야 합격이다:
#   ① 셋업이 실제로 위반을 만들었는가 ② 훅 ON 에서 **이 검사의 사유로** 차단되는가
#   ③ 훅 OFF 에서 통과하는가 (대조군 없이는 위양성을 못 걸러낸다)
# 생산 호출 형태로 시험한다 — 검사기에 인자를 주는 형태로만 시험하면 인자 없는
# 생산 경로(pre-commit 이 부르는 그 형태)를 꺼도 전부 초록이 된다(2026-09-06 실측 교훈).
set -uo pipefail

unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE GIT_OBJECT_DIRECTORY \
      GIT_ALTERNATE_OBJECT_DIRECTORIES GIT_COMMON_DIR GIT_PREFIX GIT_QUARANTINE_PATH

BLOCK_MARK='비밀 규칙 카나리 커버리지'
PATTERNS=.secret-patterns.default
FIX_DIR=scripts/verify/fixtures/secret-canaries
CANARY_POS="$FIX_DIR/positive.txt"
CANARY_NEG="$FIX_DIR/negative.txt"
MANIFEST="$FIX_DIR/manifest.txt"
COVER_SRC=scripts/verify/check-secret-canary-coverage.sh
REG_SRC=scripts/verify/check-secret-detection-regression.sh
WF=.github/workflows/verify.yml

REPO=$(git rev-parse --show-toplevel 2>/dev/null) || {
  echo "FAIL: git 저장소가 아니다 (fail-closed)"; echo "CHECKED: 0"; exit 2; }
cd "$REPO" || { echo "FAIL: 저장소 루트로 이동 실패"; echo "CHECKED: 0"; exit 2; }
for f in "$PATTERNS" hooks/pre-commit "$CANARY_POS" "$CANARY_NEG" "$MANIFEST"; do
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

# clone 은 HEAD 를 받는다. 지금 고치는 중인 검사기·고정물·규칙 파일을 작업트리 사본으로
# 덮고 **커밋까지** 한다 — 검사기가 인덱스와 HEAD 를 읽으므로 cp 만으로는 판정 입력이
# 바뀌지 않는다. 이 줄이 없으면 어긋난 조합을 시험하게 되고 변이가 전부 생존한다.
# 명부와 훅 파일도 함께 옮긴다. 순환 우회 시연은 "장치를 지우면 명부 검사가 막는가"를
# 묻는데, 격리 사본의 명부가 커밋된 옛 판본이면 새 항목이 없어 무엇을 지워도 통과한다
# (2026-09-11 실측: 시연 2건이 그 이유로 빨갰다). 검사기만 옮기고 그것이 대조하는
# 정본을 두고 오면 어긋난 조합을 시험하게 된다.
INSTALL="$COVER_SRC $REG_SRC $CANARY_POS $CANARY_NEG $MANIFEST $PATTERNS verify.sh hooks/pre-commit docs/sot/mechanism-registry.yaml"
# 커버리지 검사기의 **존재를 전제로 두지 않는다**. 전제로 두면 검사기가 없을 때 시연이
# 한 번도 돌지 않고 exit 2 로 끝나, "커버 공백이 차단되지 않는다"는 사실 자체가
# 관측되지 않는다(acceptance-p13-deletion 이 같은 이유로 같은 선택을 했다).
INSTALLED=""
for f in $INSTALL; do
  if [ ! -f "$f" ]; then
    if [ "$f" = "$COVER_SRC" ]; then continue; fi
    echo "FAIL: 설치 대상이 없다 — $f"; echo "CHECKED: 0"; exit 2
  fi
  mkdir -p "$CLONE/$(dirname "$f")" || { echo "FAIL: 디렉터리 생성 실패 — $f"; echo "CHECKED: 0"; exit 2; }
  cp -p "$f" "$CLONE/$f" || { echo "FAIL: 설치 실패 — $f"; echo "CHECKED: 0"; exit 2; }
  INSTALLED="$INSTALLED $f"
done
# 실제로 복사한 것만 스테이징한다. 없는 경로가 하나라도 섞이면 git add 가 통째로 실패해
# "설치 실패"로 보이고, 검사기 부재라는 **관측하려던 사실**이 시연 0건으로 덮인다.
[ -n "$INSTALLED" ] || { echo "FAIL: 설치된 파일이 0개다"; echo "CHECKED: 0"; exit 2; }
[ -f "$CLONE/$COVER_SRC" ] && chmod +x "$CLONE/$COVER_SRC"
chmod +x "$CLONE/$REG_SRC"
# 작업트리와 clone 의 HEAD 가 이미 같으면 커밋할 것이 없다 — 그것은 정상이다.
( cd "$CLONE" && git add -A -- $INSTALLED \
  && { git diff --cached --quiet \
       || git -c user.name=a -c user.email=a@b -c core.hooksPath=/dev/null \
            commit -qm "작업트리 사본 설치 (시연 기준점)"; } ) >"$SANDBOX/seed.err" 2>&1 || {
  echo "FAIL: 작업트리 사본 커밋 실패 — $(head -2 "$SANDBOX/seed.err" | tr '\n' ' ')"
  echo "CHECKED: 0"; exit 2; }
BASE=$(cd "$CLONE" && git rev-parse HEAD) || {
  echo "FAIL: 기준 커밋을 읽지 못했다"; echo "CHECKED: 0"; exit 2; }
( cd "$CLONE" && git diff --quiet "$BASE" -- $INSTALLED ) || {
  echo "FAIL: 설치본이 기준 커밋에 반영되지 않았다 — 시연 전체가 무효다"
  echo "CHECKED: 0"; exit 2; }

run_case() {  # <설명> <block|pass> <셋업 함수> [기대 종료값 — block 일 때만, 기본 1]
  local desc="$1" expect="$2" setup="$3" want_rc="${4:-1}" log="$SANDBOX/log.$checked"
  ( cd "$CLONE" && git reset --hard --quiet "$BASE" && git clean -qfdx ) 2>/dev/null
  if ! ( cd "$CLONE" && $setup ) >"$SANDBOX/setup.err" 2>&1; then
    record 1 "$desc" "셋업 실패 — 위반을 만들지 못했다: $(head -1 "$SANDBOX/setup.err")"; return
  fi
  if ( cd "$CLONE" && git diff --cached --quiet ); then
    record 1 "$desc" "셋업이 스테이징을 만들지 못했다 — 시연 무효"; return
  fi
  local rc=0
  ( cd "$CLONE" && git -c user.name=a -c user.email=a@b commit -m demo ) >"$log" 2>&1 || rc=$?
  if [ "$expect" = block ]; then
    if [ "$rc" -eq 0 ]; then record 1 "$desc" "차단되지 않았다 (commit rc=0)"; return; fi
    if ! grep -q "$BLOCK_MARK" "$log"; then
      record 1 "$desc" "차단은 됐으나 이 검사의 사유가 아니다 (rc=$rc): $(grep -m1 BLOCKED "$log" | head -c 140)"
      return
    fi
    # 실행 불가(exit 2)와 판정 실패(exit 1)를 가른다. 둘을 같은 신호로 세면 환경 사고가
    # "차단됨"으로 계수되고 구현이 0줄이어도 전부 초록이 난다(counter-AC 5).
    if ! grep -q "check-secret-canary-coverage exit=$want_rc" "$log"; then
      record 1 "$desc" "차단 사유의 종료값이 다르다 (기대 exit=$want_rc): $(grep -m1 -o 'check-secret-canary-coverage exit=[0-9]*' "$log")"
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
      record 1 "$desc" "오탐 — 정당한 변경을 이 검사가 차단했다: $(grep -m1 "$BLOCK_MARK" "$log" | head -c 160)"
      return
    fi
    record 0 "$desc"
  fi
}

# 시연 1 (양성) — 규칙을 추가하면서 카나리·manifest 는 안 만든다.
# 아무것도 매칭하지 않는 모양을 쓴다 — 음성 카나리를 건드리면 오탐 증가로 다른 검사가
# 먼저 걸려 이 시연이 무엇을 판별했는지 알 수 없게 된다.
setup_add_rule_without_canary() {
  printf '\n# @id: demo-uncovered\nDEMOCOVERONLY[0-9A-Z]{20}\n' >> "$PATTERNS"
  git add "$PATTERNS"
}
run_case "카나리 없는 규칙 추가는 차단된다" block setup_add_rule_without_canary

# 시연 2 (양성) — id 없이 규칙만 추가한다. id 가 없으면 manifest 에 올릴 수도 없다.
setup_add_rule_without_id() {
  printf '\nDEMONOID[0-9A-Z]{20}\n' >> "$PATTERNS"
  git add "$PATTERNS"
}
run_case "id 없는 규칙 추가는 차단된다" block setup_add_rule_without_id

# 시연 3 (양성) — 기존 규칙을 아무것도 잡지 않는 모양으로 바꾼다(match-never).
# manifest 는 그대로라 서류상으로는 덮여 있다. 실행으로 확인하지 않으면 통과한다.
setup_rule_match_never() {
  python3 - "$PATTERNS" <<'PYEOF'
import sys
p = sys.argv[1]
lines = open(p).read().splitlines(True)
# 토큰을 런타임에 조립한다. 소스에 리터럴로 두면 그것이 **추적 파일 안의 값**이 되어,
# 이 규칙을 넣는 순간 비밀 스캔이 이 인수 스크립트 자신을 잡는다(2026-09-11 실측).
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
run_case "규칙을 match-never 로 바꾸면 차단된다 (서류가 아니라 실행으로 확인)" block setup_rule_match_never

# 시연 4 (양성) — 규칙 한 개를 id 주석까지 통째로 지운다. manifest 가 없는 id 를 가리키게 된다.
setup_delete_rule() {
  python3 - "$PATTERNS" <<'PYEOF'
import sys
p = sys.argv[1]
lines = open(p).read().splitlines(True)
out, skip = [], False
for l in lines:
    if l.strip() == '# @id: aws-asia':
        skip = True; continue
    if skip:
        skip = False
        if l.startswith('ASIA['):
            continue
    out.append(l)
assert len(out) < len(lines), "삭제 대상 없음"
open(p, 'w').write(''.join(out))
PYEOF
  git add "$PATTERNS"
}
run_case "규칙 삭제는 차단된다 (manifest 가 빈 id 를 가리킨다)" block setup_delete_rule

# 시연 5 (양성) — manifest 에서 매핑 한 줄을 지운다. 규칙과 카나리는 그대로다.
# 이 줄이 사라지면 그 규칙은 다시 "아무도 대표하지 않는" 상태가 된다.
setup_drop_manifest_row() {
  python3 - "$MANIFEST" <<'PYEOF'
import sys
p = sys.argv[1]
lines = open(p).read().splitlines(True)
out = [l for l in lines if not (not l.startswith('#') and '\taws-asia\t' in l)]
assert len(out) < len(lines), "삭제 대상 없음"
open(p, 'w').write(''.join(out))
PYEOF
  git add "$MANIFEST"
}
run_case "manifest 매핑 줄 삭제는 차단된다" block setup_drop_manifest_row

# 시연 6 (음성 · 정당한 정리) — 규칙·id·카나리·manifest 를 **함께** 줄인다.
# 이것까지 막으면 규칙을 영원히 못 고친다. 삭제가 diff 에 남아 리뷰에서 보인다.
setup_shrink_together() {
  python3 - "$PATTERNS" "$CANARY_POS" "$MANIFEST" <<'PYEOF'
import sys
pat, can, man = sys.argv[1], sys.argv[2], sys.argv[3]
lines = open(pat).read().splitlines(True)
out, skip = [], False
for l in lines:
    if l.strip() == '# @id: aws-asia':
        skip = True; continue
    if skip:
        skip = False
        if l.startswith('ASIA['):
            continue
    out.append(l)
assert len(out) < len(lines), "규칙 삭제 실패"
open(pat, 'w').write(''.join(out))
cl = open(can).read().splitlines(True)
co = [l for l in cl if not l.startswith('AWS 임시 키 ID\t')]
assert len(co) < len(cl), "카나리 삭제 실패"
open(can, 'w').write(''.join(co))
ml = open(man).read().splitlines(True)
mo = [l for l in ml if not (not l.startswith('#') and '\taws-asia\t' in l)]
assert len(mo) < len(ml), "manifest 삭제 실패"
open(man, 'w').write(''.join(mo))
PYEOF
  git add "$PATTERNS" "$CANARY_POS" "$MANIFEST"
}
run_case "규칙·카나리·manifest 를 함께 줄이면 통과한다 (정당한 경로)" pass setup_shrink_together

# 시연 7 (음성 · 오탐 대조) — 카나리만 추가한다. manifest 에 없는 카나리는 여분일 뿐이다.
setup_add_canary_only() {
  printf '시연용 추가 카나리\tDEMOEXTRA\tVALUE123456\n' >> "$CANARY_POS"
  git add "$CANARY_POS"
}
run_case "카나리 추가만 하면 통과한다 (커버리지 증가)" pass setup_add_canary_only

# 시연 8 (배선) — 검사기가 있어도 훅이 부르지 않으면 무방비다.
if grep -q 'check-secret-canary-coverage\.sh' hooks/pre-commit; then
  record 0 "hooks/pre-commit 이 커버리지 검사기를 호출한다 (배선)"
else
  record 1 "hooks/pre-commit 이 커버리지 검사기를 호출한다 (배선)" "훅에 호출이 없다"
fi

# 시연 9 (배선) — CI 가 이 인수 검사를 돌리지 않으면 로컬을 우회한 push 가 무방비다.
if [ -f "$WF" ] && grep -q 'acceptance-secret-canary-coverage\.sh' "$WF"; then
  record 0 "CI 워크플로가 이 인수 검사를 실행한다 (배선)"
else
  record 1 "CI 워크플로가 이 인수 검사를 실행한다 (배선)" "$WF 에 실행 줄이 없다"
fi

# 시연 10 (AC-4 독립 oracle) — 같은 입력을 생산 스캐너로도 판정해 대조한다.
ORACLE_LOG="$SANDBOX/oracle.log"
orc=0
( cd "$CLONE" && git reset --hard --quiet "$BASE" && git clean -qfdx \
  && bash "$COVER_SRC" --oracle-selftest ) >"$ORACLE_LOG" 2>&1 || orc=$?
if [ "$orc" -eq 0 ] && grep -q 'PASS: 독립 oracle 일치' "$ORACLE_LOG"; then
  record 0 "독립 oracle 대조 — $(grep -m1 'PASS: 독립 oracle' "$ORACLE_LOG")"
else
  record 1 "독립 oracle 대조" "rc=$orc · $(head -2 "$ORACLE_LOG" | tr '\n' ' ' | head -c 160)"
fi

# 시연 11 (커버리지 원명령) — 손대지 않은 상태에서 전 규칙이 덮이는가.
COVER_LOG="$SANDBOX/cover.log"
crc=0
( cd "$CLONE" && bash "$COVER_SRC" ) >"$COVER_LOG" 2>&1 || crc=$?
if [ "$crc" -eq 0 ] && grep -q '전부 카나리로 덮임' "$COVER_LOG"; then
  record 0 "현재 규칙 전부가 카나리로 덮인다 — $(grep -m1 PASS "$COVER_LOG")"
else
  record 1 "현재 규칙 전부가 카나리로 덮인다" "rc=$crc · $(head -3 "$COVER_LOG" | tr '\n' ' ' | head -c 200)"
fi

# 시연 12·13 (순환 우회) — 검사기 자신과 그 호출부를 빼면 무엇이 막는가.
# counter-AC 4: "검사기는 고치되 그 검사기의 fixture·manifest·호출부를 보호 대상에서
# 뺀다". 훅 트리거는 규칙·고정물이 스테이징될 때만 돈다 — 검사기만 지우는 커밋은
# 트리거를 안 건드린다. 그 구멍은 **장치 명부**가 막는다: 명부가 경로와 배선 문구를
# 실제 파일과 대조하므로, 검사기를 지우거나 호출 줄을 빼면 명부 검사가 빨개진다.
circular_case() {  # <설명> <파괴 명령>
  local desc="$1" breaker="$2" log="$SANDBOX/circ.$checked" rc=0
  ( cd "$CLONE" && git reset --hard --quiet "$BASE" && git clean -qfdx ) 2>/dev/null
  if ! ( cd "$CLONE" && eval "$breaker" ); then
    record 1 "$desc" "파괴 셋업 실패 — 시연 무효"; return
  fi
  ( cd "$CLONE" && bash scripts/verify/check-mechanism-registry.sh ) >"$log" 2>&1 || rc=$?
  if [ "$rc" -eq 0 ]; then
    record 1 "$desc" "명부 검사가 통과했다 — 순환 우회가 열려 있다"
  else
    record 0 "$desc (명부 검사 rc=$rc)"
  fi
}
circular_case "커버리지 검사기를 지우면 명부 검사가 막는다" "rm -f '$COVER_SRC'"
circular_case "훅의 커버리지 호출 줄을 빼면 명부 검사가 막는다" \
  "sed -i.bak '/COVER_CHECKER=scripts\/verify\/check-secret-canary-coverage.sh/d' hooks/pre-commit && rm -f hooks/pre-commit.bak"

echo
echo "CHECKED: $checked"
[ "$fail" -ne 0 ] && { echo "RESULT: 불합격 — 카나리가 대표하지 않는 규칙이 통과한다"; exit 1; }
echo "RESULT: 합격 — 모든 비밀 규칙이 카나리로 덮인다"
exit 0
