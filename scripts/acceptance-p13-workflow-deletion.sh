#!/usr/bin/env bash
# acceptance-p13-workflow-deletion — CI 워크플로의 스텝·검사 줄 삭제 탐지(suppressions.yaml p13-deletion-blindspot 해소)
#
# 범위: .github/workflows/* 만. 다른 경로의 삭제는 리팩터링 오탐 방지를 위해 탐지하지 않는다(오너 지시 2026-11-12).
#
# 계약: docs/engineering/suppressions-renew-goal-2026-11-12.md AC-2
#   출력  : exit 0 (기대 판정 전부 일치) | exit 1 (하나라도 불일치·셋업 실패)
#   판정  : 각 시연을 훅 ON/OFF 로 두 번 돌린다(acceptance-0-7 과 같은 대조군 구조).
#           block 기대 = 훅 ON 실패 + 훅 OFF 성공 / pass 기대 = 훅 ON·OFF 모두 성공
#   불변식: mktemp -d 안의 clone 에서만 시연한다. 원본 저장소를 건드리지 않는다.
#           push 는 하지 않는다(커밋만) — pre-push 글로브에서도 안전하게 돈다(hs-a4 와 같은 성질).
set -euo pipefail
unset GIT_DIR GIT_INDEX_FILE GIT_OBJECT_DIRECTORY GIT_WORK_TREE GIT_COMMON_DIR GIT_ALTERNATE_OBJECT_DIRECTORIES

REPO_ROOT=$(git rev-parse --show-toplevel) || { echo "FAIL: git 저장소가 아님"; exit 1; }
orig_state() { (cd "$REPO_ROOT" && git status --porcelain | LC_ALL=C sort | shasum | awk '{print $1}'); }
ORIG_BEFORE=$(orig_state)

sandbox=$(mktemp -d) || { echo "FAIL: 샌드박스 생성 실패"; exit 1; }
outdir=$(mktemp -d) || { echo "FAIL: 로그 디렉터리 생성 실패"; exit 1; }
cleanup() { rm -rf "$sandbox" "$outdir"; }
trap cleanup EXIT

git clone -q "$REPO_ROOT" "$sandbox/repo" || { echo "FAIL: clone 실패"; exit 1; }
cd "$sandbox/repo"
git config user.email "acceptance@local"
git config user.name "acceptance"
bash scripts/install-hooks.sh >/dev/null 2>&1 || { echo "FAIL: install-hooks.sh 실패"; exit 1; }
[ "$(git config --get core.hooksPath)" = "hooks" ] || { echo "FAIL: core.hooksPath 가 hooks 가 아니다"; exit 1; }
BASE=$(git rev-parse HEAD)

fail=0; checked=0
reset_tree() { git reset -q --hard "$BASE"; git clean -qfd; }

# demo <block|pass> <이름> <셋업> <행위>
demo() {
  local expect="$1" name="$2" setup="$3" action="$4" key="${5:-스텝·검사 줄 삭제}" sON sOFF aON aOFF
  checked=$((checked + 1))
  reset_tree; git config core.hooksPath hooks
  set +e; ( eval "$setup" ) >"$outdir/s.on" 2>&1; sON=$?; ( eval "$action" ) >"$outdir/a.on" 2>&1; aON=$?; set -e
  reset_tree; git config core.hooksPath /dev/null
  set +e; ( eval "$setup" ) >"$outdir/s.off" 2>&1; sOFF=$?; ( eval "$action" ) >"$outdir/a.off" 2>&1; aOFF=$?; set -e
  reset_tree; git config core.hooksPath hooks

  if [ "$sON" -ne 0 ] || [ "$sOFF" -ne 0 ]; then
    echo "FAIL: [$name] 셋업 실패(on=$sON off=$sOFF) — 위반을 만들지 못해 시연 무효"; fail=1; return
  fi
  if [ "$aOFF" -ne 0 ]; then
    echo "FAIL: [$name] 훅 OFF 에서도 실패(exit=$aOFF) — 대조군 무효"; awk 'NR<=3{print "    " $0}' "$outdir/a.off"; fail=1; return
  fi
  if [ "$expect" = block ]; then
    if [ "$aON" -ne 0 ] && grep -qF "$key" "$outdir/a.on"; then
      echo "PASS: [$name] 차단됨 (훅ON=$aON · 훅OFF=$aOFF)"
    else
      echo "FAIL: [$name] 차단되지 않음 (훅ON=$aON · 훅OFF=$aOFF)"; awk '/BLOCKED/{print "    " $0; if (++n == 3) exit}' "$outdir/a.on"; fail=1
    fi
  else
    if [ "$aON" -eq 0 ]; then
      echo "PASS: [$name] 오탐 없음 (훅ON=0 · 훅OFF=0)"
    else
      echo "FAIL: [$name] 오탐 — 정상 변경이 차단됨 (훅ON=$aON)"; awk '/BLOCKED/{print "    " $0; if (++n == 3) exit}' "$outdir/a.on"; fail=1
    fi
  fi
}

WF=.github/workflows/verify.yml

demo block "스텝 통째 삭제(name+run)" \
  "perl -ni -e 'print unless /name: 인수 검사 hs-a4 |run: bash scripts\/verify\/run-acceptance\.sh scripts\/acceptance-hs-a4\.sh\$/' $WF && ! grep -q 'name: 인수 검사 hs-a4 ' $WF" \
  "git add $WF && git commit -qm 'ci: drop hs-a4 step'"

demo block "run 블록 안 검사 명령 1줄 삭제" \
  "perl -ni -e 'print unless /^ +bash scripts\/verify\/run-acceptance\.sh scripts\/acceptance-hs-cleanroom-mutations\.sh\$/' $WF && ! grep -q 'acceptance-hs-cleanroom-mutations.sh' $WF" \
  "git add $WF && git commit -qm 'ci: drop cleanroom mutations'"

demo block "스텝을 주석으로 위장 삭제" \
  "perl -pi -e 's/^(\s*)(- name: 인수 검사 0-6 |run: bash scripts\/verify\/run-acceptance\.sh scripts\/acceptance-0-6\.sh)/\$1# \$2/' $WF && grep -q '# - name: 인수 검사 0-6 ' $WF" \
  "git add $WF && git commit -qm 'ci: comment out 0-6'"

demo block "워크플로 파일 삭제" \
  "test -f $WF" \
  "git rm -q $WF && git commit -qm 'ci: remove workflow'"

demo block "워크플로를 밖으로 rename" \
  "test -f $WF" \
  "git mv $WF docs/verify.yml.bak && git commit -qm 'ci: move workflow out'"

demo pass "워크플로 주석 줄 삭제(counter)" \
  "perl -ni -e 'print unless /# 기본 상한은 360분/' $WF && ! grep -q '기본 상한은 360분' $WF" \
  "git add $WF && git commit -qm 'ci: trim comment'"

demo pass "워크플로 비검사 스칼라 변경(counter)" \
  "perl -pi -e 's/^(\s*)timeout-minutes: 30\$/\$1timeout-minutes: 31/' $WF && grep -q 'timeout-minutes: 31' $WF" \
  "git add $WF && git commit -qm 'ci: bump timeout'"

demo pass "워크플로 밖 경로의 줄 삭제(counter · 리팩터링 오탐 방지)" \
  "perl -ni -e 'print unless /echo \"OK: docs\/sot 재구성 AC 전부 충족\"/' scripts/check-docs-sot.sh && ! grep -q 'OK: docs/sot 재구성 AC 전부 충족' scripts/check-docs-sot.sh" \
  "git add scripts/check-docs-sot.sh && git commit -qm 'refactor: drop echo'"

# ── V1(Codex 2026-11-12 thread 01a1cffa) 반례 — 텍스트 판정기를 YAML 구조 판정으로 바꾼 근거 ──
PW=.github/workflows/probe.yml
seed_probe() { # 시드 워크플로를 먼저 커밋한다(추가만이므로 훅 ON/OFF 모두 통과해야 한다)
  printf '%s\n' "$1" > $PW && git add $PW && git commit -qm 'seed probe workflow'
}

demo block "V1-1 삭제한 스텝 문구를 env 문자열에 미끼로 남김" \
  "perl -ni -e 'print unless /name: 인수 검사 hs-a4 |run: bash scripts\/verify\/run-acceptance\.sh scripts\/acceptance-hs-a4\.sh\$/' $WF && printf 'env:\n  DECOY: |\n    - name: 인수 검사 hs-a4 (대용량·산출물 차단이 실제로 도는가)\n    run: bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-a4.sh\n' >> $WF && ! grep -q '^      - name: 인수 검사 hs-a4 ' $WF" \
  "git add $WF && git commit -qm 'ci: hide hs-a4 in env'"

ANCHOR_WF='on: push
jobs:
  probe:
    runs-on: ubuntu-latest
    steps:
      - name: gate
        run: &checks |
          bash scripts/acceptance-0-6.sh
          bash scripts/acceptance-hs-a4.sh'
demo block "V1-2a 앵커 run 블록 안 명령 1줄 삭제" \
  "seed_probe \"\$ANCHOR_WF\" && perl -ni -e 'print unless /bash scripts\/acceptance-hs-a4\.sh/' $PW && ! grep -q hs-a4 $PW" \
  "git add $PW && git commit -qm 'ci: drop anchored line'"

FLOW_WF='on: push
jobs:
  probe:
    runs-on: ubuntu-latest
    steps:
      - {name: keep, run: echo keep}
      - {name: gate, run: bash scripts/acceptance-0-6.sh}'
demo block "V1-2b flow 형식 스텝 삭제" \
  "seed_probe \"\$FLOW_WF\" && perl -ni -e 'print unless /name: gate/' $PW && ! grep -q 'name: gate' $PW" \
  "git add $PW && git commit -qm 'ci: drop flow step'"

RUNFIRST_WF='on: push
jobs:
  probe:
    runs-on: ubuntu-latest
    steps:
      - run: |
          bash scripts/acceptance-0-6.sh
        env:
          LABEL: old'
demo pass "V1-3 run 이 첫 키인 스텝의 형제 env 값 변경(counter)" \
  "seed_probe \"\$RUNFIRST_WF\" && perl -pi -e 's/LABEL: old/LABEL: new/' $PW && grep -q 'LABEL: new' $PW" \
  "git add $PW && git commit -qm 'ci: relabel'"

demo pass "스텝 순서 이동(counter)" \
  "seed_probe \"\$FLOW_WF\" && printf '%s\n' 'on: push' 'jobs:' '  probe:' '    runs-on: ubuntu-latest' '    steps:' '      - {name: gate, run: bash scripts/acceptance-0-6.sh}' '      - {name: keep, run: echo keep}' > $PW" \
  "git add $PW && git commit -qm 'ci: reorder'"

# fail-closed: 판정기가 판정하지 못하면(YAML 파싱 실패) 통과가 아니라 차단이다(mutant F 회귀).
demo block "YAML 파싱 불가 워크플로 커밋(fail-closed)" \
  "printf 'jobs: [\\n' >> $WF && tail -1 $WF | grep -qF 'jobs: ['" \
  "git add $WF && git commit -qm 'ci: broken yaml'" "워크플로 삭제 판정 실패"

if [ "$(orig_state)" != "$ORIG_BEFORE" ]; then
  echo "FAIL: 시연이 원본 저장소를 변경했다"; fail=1
fi

echo "CHECKED: $checked"
if [ "$fail" -eq 0 ]; then
  echo "PASS: 워크플로 삭제 탐지 시연 ${checked}건 전부 기대 판정과 일치"
  exit 0
fi
echo "RESULT: 기대와 다른 판정이 있다. exit 1"
exit 1
