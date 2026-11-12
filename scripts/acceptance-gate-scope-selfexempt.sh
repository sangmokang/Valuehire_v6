#!/usr/bin/env bash
# acceptance-gate-scope-selfexempt — 자기제외 탐지 범위(suppressions.yaml gate-scope-gaps (1) 해소)
#
# 계약: docs/engineering/suppressions-renew-goal-2026-11-12.md AC-1
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
  local expect="$1" name="$2" setup="$3" action="$4" sON sOFF aON aOFF
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
    if [ "$aON" -ne 0 ] && grep -q '자기 제외' "$outdir/a.on"; then
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
LC=.claude/skills/verify/local-checks.sh

demo block "워크플로 자기제외" \
  "test -f $WF && printf '      - name: probe\n        run: git ls-files | grep -v verify.yml\n' >> $WF && grep -q 'grep -v verify.yml' $WF" \
  "git add $WF && git commit -qm 'weaken: workflow self-exempt'"

demo block "스킬 local-checks 자기제외" \
  "test -f $LC && printf '\nkeep=\$(git ls-files | grep -v local-checks.sh)\n' >> $LC && grep -q 'grep -v local-checks.sh' $LC" \
  "git add $LC && git commit -qm 'weaken: local-checks self-exempt'"

demo block "기존 범위 scripts/*.sh 자기제외(회귀)" \
  "printf '\nkeep=\$(git ls-files | grep -v acceptance-0-6.sh)\n' >> scripts/acceptance-0-6.sh && grep -q 'grep -v acceptance-0-6.sh' scripts/acceptance-0-6.sh" \
  "git add scripts/acceptance-0-6.sh && git commit -qm 'weaken: script self-exempt'"

demo pass "워크플로 정상 스텝 추가(counter)" \
  "printf '      - name: probe\n        run: echo probe\n' >> $WF && grep -q 'run: echo probe' $WF" \
  "git add $WF && git commit -qm 'ci: add probe step'"

demo pass "스킬 local-checks 정상 추가(counter)" \
  "printf '\necho probe\n' >> $LC && tail -1 $LC | grep -q probe" \
  "git add $LC && git commit -qm 'skill: add probe'"

# ── V1(Codex 2026-11-12) 반례 — 파일명 점을 이스케이프·문자클래스로 쓴 자기제외 ──
demo block "V1-4a 이스케이프한 점(local-checks\\.sh)" \
  "printf '%s\n' '' 'keep=\$(git ls-files | grep -v '\''local-checks\\.sh'\'')' >> $LC && grep -qF 'local-checks\\.sh' $LC" \
  "git add $LC && git commit -qm 'weaken: escaped self-exempt'"

demo block "V1-4b 문자클래스 점(verify[.]yml)" \
  "printf '      - name: probe\n        run: git ls-files | grep -v \"verify[.]yml\"\n' >> $WF && grep -qF 'verify[.]yml' $WF" \
  "git add $WF && git commit -qm 'weaken: bracket self-exempt'"

# ── V1 3차 반례 — 더 긴 다른 파일명(archived-verify.yml)을 빼는 것은 자기제외가 아니다 ──
demo pass "V1c-2 다른 파일 archived-verify.yml 제외(counter)" \
  "printf '      - name: probe\n        run: git ls-files | grep -v archived-verify.yml\n' >> $WF && grep -q 'grep -v archived-verify.yml' $WF" \
  "git add $WF && git commit -qm 'ci: skip archived'"

demo block "V1c-3 경로째 쓴 자기제외(workflows/verify.yml\$)" \
  "printf '      - name: probe\n        run: git ls-files | grep -v \"workflows/verify.yml\$\"\n' >> $WF && grep -q 'workflows/verify.yml' $WF" \
  "git add $WF && git commit -qm 'weaken: path self-exempt'"

if [ "$(orig_state)" != "$ORIG_BEFORE" ]; then
  echo "FAIL: 시연이 원본 저장소를 변경했다"; fail=1
fi

echo "CHECKED: $checked"
if [ "$fail" -eq 0 ]; then
  echo "PASS: 자기제외 탐지 범위 시연 ${checked}건 전부 기대 판정과 일치"
  exit 0
fi
echo "RESULT: 기대와 다른 판정이 있다. exit 1"
exit 1
