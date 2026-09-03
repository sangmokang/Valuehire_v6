#!/usr/bin/env bash
# PUSH-PERFORMING
#   이 선언은 hooks/pre-push 가 읽는다. push 를 수행하는 스크립트를 pre-push 안에서
#   실행하면 무한 재귀가 되므로, pre-push 는 이 마커가 있는 스크립트를 건너뛰고
#   CI 가 대신 실행한다. 이름이 아니라 성질로 제외하기 위한 선언이다.
#
# 0-7 인수 스크립트 — 로컬 강제 장치(git hook)가 실제로 위반을 차단하는가.
#
# 계약: docs/sot/hook-contracts.md
#   출력  : exit 0 (6종 전부 BLOCKED) | exit 1 (하나라도 통과·위양성·셋업 실패)
#   불변식: 모든 시연은 mktemp -d 안의 clone 에서 수행한다. 원본 저장소를 건드리지 않는다.
#          검사를 실행하지 못한 경우도 실패로 판정한다(fail-closed).
#
# ── 판정 구조 (2026-08-07 V1 지적 반영) ─────────────────────────────────────
# 이전 판본은 "종료코드 ≠0 이면 BLOCKED" 로 셌다. 그래서 시연 1의 sed 가 BSD sed 에서
# 파싱 실패해 verify.sh 가 전혀 변조되지 않았는데도, `nothing to commit` 의 exit 1 을
# 차단으로 계수했다. P13④ 게이트는 한 번도 실행되지 않은 채 6/6 초록이 나왔다.
#
# 따라서 각 시연은 세 가지를 모두 만족해야 BLOCKED 로 센다:
#   ① 셋업이 성공한다        — 위반을 실제로 만들었는가 (만들지 못했으면 시연 무효)
#   ② 훅 ON 에서 exit ≠ 0   — 차단되는가
#   ③ 훅 OFF 에서 exit == 0 — 훅이 원인인가 (대조군. 없으면 위양성을 못 걸러낸다)
#
# 재진입 가드는 두지 않는다. 환경변수 하나로 전체 인수를 무력화하는 경로가 되기
# 때문이다(위반유형 E). 대신 hooks/pre-push 와 scripts/session-status.sh 가
# 이 스크립트를 실행 대상에서 제외하고, 그 사실을 화면에 출력한다.
set -euo pipefail

# 형제 스크립트(0-2·0-5)와 동일한 격리. 이 변수들이 환경에 남아 있으면 샌드박스의 git 이
# 실저장소를 가리켜 검증이 실저장소를 오염시키거나 위양성 PASS 를 낸다.
# 0-7 은 이 unset 이 없어서, 중첩 실행 시 git push 가 넘긴 GIT_DIR 때문에
# `git remote add` 가 실패해 우연히 재귀가 끊기고 있었다(V1 2026-08-07 규명).
# 우연에 기대지 않도록 형제와 같게 맞춘다.
unset GIT_DIR GIT_INDEX_FILE GIT_OBJECT_DIRECTORY GIT_WORK_TREE GIT_COMMON_DIR GIT_ALTERNATE_OBJECT_DIRECTORIES

# 재귀 방지 — 실패 방향에 주의한다.
# 이 변수가 있으면 SKIP(exit 0) 하면 안 된다. 그러면 외부에서 주입하는 것만으로 6종
# 시연 전체를 초록으로 건너뛸 수 있는 무력화 스위치가 된다(ACCEPTANCE_0_7_ACTIVE 가 그랬다).
# 그래서 **시연 불가 환경 = 실패**로 처리한다. 주입해도 통과가 아니라 빨간불이 된다.
if [ -n "${VH_PREPUSH_DEPTH:-}" ]; then
  echo "FAIL: pre-push 컨텍스트에서 0-7 이 호출됐다 (VH_PREPUSH_DEPTH=${VH_PREPUSH_DEPTH})."
  echo "      이 스크립트는 push 를 시연하므로 pre-push 안에서 돌면 재귀가 된다."
  echo "      pre-push 는 헤더의 '# PUSH-PERFORMING' 선언을 보고 이 파일을 건너뛰어야 한다."
  exit 1
fi

TOTAL=7
fail=0
step=0
allow_checked=0

REPO_ROOT=$(git rev-parse --show-toplevel) || { echo "FAIL: git 저장소가 아님"; exit 1; }

orig_state() { (cd "$REPO_ROOT" && git status --porcelain | LC_ALL=C sort | shasum | awk '{print $1}'); }
ORIG_BEFORE=$(orig_state)

sandbox=$(mktemp -d) || { echo "FAIL: 샌드박스 생성 실패"; exit 1; }
outdir=$(mktemp -d) || { echo "FAIL: 로그 디렉터리 생성 실패"; exit 1; }
cleanup() { rm -rf "$sandbox" "$outdir"; }
trap cleanup EXIT
trap 'cleanup; trap - EXIT; exit 143' TERM
trap 'cleanup; trap - EXIT; exit 130' INT
trap 'cleanup; trap - EXIT; exit 129' HUP

# --- 전제 0: 훅 인프라가 존재하는가 -------------------------------------------
echo "=== 전제 검사: 훅 인프라 ==="
for f in hooks/pre-commit hooks/pre-push scripts/install-hooks.sh scripts/session-status.sh; do
  if [ ! -f "$REPO_ROOT/$f" ]; then
    echo "FAIL: $f 없음 — 로컬 강제 장치가 설치되지 않았다"; fail=1
  elif [ ! -x "$REPO_ROOT/$f" ]; then
    echo "FAIL: $f 실행 권한 없음 — 훅은 존재해도 조용히 통과한다"; fail=1
  fi
done
if [ ! -f "$REPO_ROOT/.claude/settings.json" ]; then
  echo "FAIL: .claude/settings.json 없음 — SessionStart hook 미등록 (AC-5)"; fail=1
fi
if [ "$fail" -ne 0 ]; then
  echo; echo "RESULT: 전제 미충족 — 시연을 진행할 수 없다. exit 1"; exit 1
fi
echo "OK: 훅 파일 4종 + settings.json 존재"
echo

# --- 샌드박스 clone + 훅 설치 -------------------------------------------------
git clone -q "$REPO_ROOT" "$sandbox/repo" || { echo "FAIL: clone 실패"; exit 1; }
git init -q --bare "$sandbox/remote.git" || { echo "FAIL: bare 원격 생성 실패"; exit 1; }
cd "$sandbox/repo"
git remote add sandbox "$sandbox/remote.git"
git config user.email "acceptance@local"
git config user.name "acceptance"
bash scripts/install-hooks.sh >/dev/null 2>&1 || { echo "FAIL: install-hooks.sh 실패"; exit 1; }

hp=$(git config --get core.hooksPath) || hp=""
[ "$hp" = "hooks" ] || { echo "FAIL: core.hooksPath='$hp' (기대 'hooks')"; exit 1; }
[ -x hooks/pre-commit ] || { echo "FAIL: clone 에서 pre-commit 실행 권한 없음"; exit 1; }

BASE=$(git rev-parse HEAD)
echo "=== 시연 (샌드박스: $sandbox/repo · 각 시연마다 훅 ON/OFF 대조) ==="

reset_tree() {
  git reset -q --hard "$BASE"
  git clean -qfd
}

# demo <이름> <셋업코드> <행위코드> [기대사유]
#
# [기대사유] (2026-09-03 추가): 훅 ON 출력에 이 문구가 있어야 BLOCKED 로 센다.
# 왜 필요한가 — pre-commit 은 검사 8종을 끝까지 순차 실행하고 **어느 하나만 걸려도**
# 종료값이 1이다. 종료값만 보면 "겨냥한 게이트가 막았다"와 "다른 게이트가 먼저
# 막았다"가 구분되지 않는다(위 15-17행 사고와 같은 유형). 특히 `.secret-patterns.default`
# 를 겨냥한 시연은 §1 비밀 스캔이 함께 반응한다 — 심는 약화 리터럴이 곧 스캔 패턴이
# 되어 저장소 문서를 매칭하기 때문이다(2026-09-03 실측: 약화 패턴 9종 전부 그렇다).
# 사유 대조가 없으면 훅을 한 줄도 고치지 않아도 이 시연이 초록으로 난다.
demo() {
  local name="$1" setup="$2" action="$3" want="${4:-}"
  step=$((step + 1))
  local sON sOFF aON aOFF

  # 훅 ON
  reset_tree; git config core.hooksPath hooks
  set +e
  ( eval "$setup" )  >"$outdir/setup.on.$step" 2>&1; sON=$?
  ( eval "$action" ) >"$outdir/act.on.$step"   2>&1; aON=$?
  set -e

  # 훅 OFF (대조군) — 같은 셋업·행위가 훅 없이는 성공해야 훅이 원인임이 증명된다
  reset_tree; git config core.hooksPath /dev/null
  set +e
  ( eval "$setup" )  >"$outdir/setup.off.$step" 2>&1; sOFF=$?
  ( eval "$action" ) >"$outdir/act.off.$step"   2>&1; aOFF=$?
  set -e

  reset_tree; git config core.hooksPath hooks

  if [ "$sON" -ne 0 ] || [ "$sOFF" -ne 0 ]; then
    printf '[%d/%d] %s → SETUP FAILED (on=%d off=%d) ← 위반을 만들지 못했다. 시연 무효\n' \
      "$step" "$TOTAL" "$name" "$sON" "$sOFF"
    sed 's/^/         /' "$outdir/setup.on.$step" | head -3
    fail=1
  elif [ "$aON" -ne 0 ] && [ "$aOFF" -eq 0 ] && [ -n "$want" ] \
       && ! grep -qF "$want" "$outdir/act.on.$step"; then
    printf '[%d/%d] %s → 사유 불일치 ← 차단은 됐지만 겨냥한 게이트가 아니다 (기대 사유: %s)\n' \
      "$step" "$TOTAL" "$name" "$want"
    awk '/BLOCKED/{print "         실제: " $0}' "$outdir/act.on.$step" | head -3
    fail=1
  elif [ "$aON" -ne 0 ] && [ "$aOFF" -eq 0 ]; then
    printf '[%d/%d] %s → BLOCKED (훅ON=%d · 훅OFF=%d) ✓ 훅이 원인\n' \
      "$step" "$TOTAL" "$name" "$aON" "$aOFF"
    if [ -n "$want" ]; then
      awk -v w="$want" 'index($0,w){print "         " $0; exit}' "$outdir/act.on.$step"
    else
      awk '/BLOCKED/{print "         " $0; exit}' "$outdir/act.on.$step"
    fi
  elif [ "$aON" -ne 0 ] && [ "$aOFF" -ne 0 ]; then
    printf '[%d/%d] %s → 위양성 ← 훅 없이도 실패한다 (훅ON=%d · 훅OFF=%d)\n' \
      "$step" "$TOTAL" "$name" "$aON" "$aOFF"
    sed 's/^/         /' "$outdir/act.off.$step" | head -3
    fail=1
  else
    printf '[%d/%d] %s → PASSED ← 결함, 차단되지 않음 (훅ON=%d · 훅OFF=%d)\n' \
      "$step" "$TOTAL" "$name" "$aON" "$aOFF"
    fail=1
  fi
}

# demo_allow <이름> <셋업코드> <행위코드>
#   차단 시연의 **짝**. 같은 파일에 대한 정상 변경이 훅 ON 에서 그대로 통과해야 한다.
#   차단만 시험하면 "전부 막는 훅"도 만점을 받는다 — 그런 훅은 우회 습관을 만든다.
demo_allow() {
  local name="$1" setup="$2" action="$3"
  local s a
  allow_checked=$((allow_checked + 1))
  reset_tree; git config core.hooksPath hooks
  set +e
  ( eval "$setup" )  >"$outdir/setup.allow.$allow_checked" 2>&1; s=$?
  ( eval "$action" ) >"$outdir/act.allow.$allow_checked"   2>&1; a=$?
  set -e
  reset_tree; git config core.hooksPath hooks

  if [ "$s" -ne 0 ]; then
    printf '[통과쌍 %d] %s → SETUP FAILED (%d) ← 정상 변경을 만들지 못했다. 시연 무효\n' \
      "$allow_checked" "$name" "$s"
    sed 's/^/         /' "$outdir/setup.allow.$allow_checked" | head -3
    fail=1
  elif [ "$a" -eq 0 ]; then
    printf '[통과쌍 %d] %s → PASSED ✓ 훅 ON 에서도 정상 변경은 막지 않는다\n' \
      "$allow_checked" "$name"
  else
    printf '[통과쌍 %d] %s → 오탐 ← 정상 변경이 막혔다 (훅ON=%d). 오탐 1건이 곧 우회 습관이다\n' \
      "$allow_checked" "$name" "$a"
    sed 's/^/         /' "$outdir/act.allow.$allow_checked" | head -5
    fail=1
  fi
}

# 1. 검사기가 자기 자신을 검사 대상에서 제외 (§0 E1 재현)
#
#    대상은 verify.sh 가 아니라 acceptance-0-6.sh 다. verify.sh 를 변조하면 그 파일이
#    스스로 오작동해 pre-commit 의 "비밀 스캔" 단계에서 먼저 걸리고, 정작 검증하려는
#    P13④(자기 제외 탐지) 게이트는 실행되지 않는다. 다른 검사 스크립트에 자기 제외만
#    삽입해야 P13④ 를 정조준할 수 있다.
demo "검사기 자기 제외" \
  'printf "\nkeep=\$(git ls-files | grep -v acceptance-0-6.sh)\n" >> scripts/acceptance-0-6.sh
   grep -q "grep -v acceptance-0-6.sh" scripts/acceptance-0-6.sh' \
  'git add scripts/acceptance-0-6.sh && git commit -m "weaken: self-exempt"'

# 2. 검사를 skip / 실패 무시로 완화 (48143a7 · 129f61d 재현)
#
#    심는 문자열을 조립해서 만든다. 리터럴로 두면 이 스크립트 자신이
#    .check-weakening-patterns 에 걸려 커밋할 수 없다(실측: pre-commit 이 차단).
#    acceptance-0-5.sh 가 카나리에서 쓰는 것과 같은 자기 매칭 방지 기법이다.
demo "검사 약화(실패 무시)" \
  'w=$(printf "%s%s" "||" " true")
   printf "\nbash verify.sh %s\n" "$w" >> scripts/acceptance-0-2.sh
   grep -qF "$w" scripts/acceptance-0-2.sh' \
  'git add scripts/acceptance-0-2.sh && git commit -m "weaken: swallow failure"'

# 3. 만료일 없는 억제 (98d923f — 35일 방치 재현)
demo "만료일 없는 억제" \
  'printf -- "- check: hard_exclude_freelancer\n  reason: later\n  owner: someone\n" > suppressions.yaml
   test -s suppressions.yaml' \
  'git add suppressions.yaml && git commit -m "suppress: no expiry"'

# 4. LLM 출력 숫자를 판정 필드에 기록 (v4 QA-094 재현)
demo "LLM 출력→판정 필드" \
  'mkdir -p src
   printf "const r = await llm.chat(p);\nscore = parseFloat(r.text);\ndb.insert({ fit_score: score });\n" > src/scoring.js
   test -s src/scoring.js' \
  'git add src/scoring.js && git commit -m "feat: scoring"'

# 5. 커밋 안 된 변경을 둔 채 push (78f3631 ② 재현)
demo "미커밋 상태로 push" \
  'echo dirty > uncommitted.txt
   test -s uncommitted.txt' \
  'git push --dry-run sandbox HEAD:refs/heads/probe-0-7'

# 6. 외부 효과 코드에 네트워크 호출이 0건 (§0 E5 gptreview.js 재현)
demo "가짜 외부효과 모듈" \
  'mkdir -p src
   printf "async function fetchProfile() {\n  console.log(\"fetching...\");\n  return { ok: true };\n}\n" > src/portal-login.js
   test -s src/portal-login.js' \
  'git add src/portal-login.js && git commit -m "feat: portal login"'

# 7. 비밀 스캔 규칙 파일(.secret-patterns.default)을 약화 (2026-09-03 추가)
#
#    이 저장소의 비밀 정책 **전체**가 이 파일 한 장에 있는데, P13 §3 검사 약화 감시는
#    `*.sh|*.yml|*.yaml|hooks/*` 만 봐서 이 파일이 범위 밖이었다. 규칙을 정하는 파일이
#    규칙 약화 감시 밖에 있으면, 검사기를 고칠 필요도 없이 검사 기준만 손대면 된다.
#
#    심는 문자열은 조립해서 만든다(시연 2와 같은 이유 — 리터럴로 두면 이 스크립트 자신이
#    .check-weakening-patterns 에 걸려 커밋할 수 없다).
#    사유 대조가 필수인 이유는 demo() 주석 참조 — §1 비밀 스캔이 함께 반응하므로
#    종료값만 보면 훅을 고치지 않아도 초록이 난다.
demo "비밀 패턴 파일 약화" \
  'w=$(printf "%s%s" "skip" ":")
   printf "\n%s\n" "$w" >> .secret-patterns.default
   grep -qx "$w" .secret-patterns.default' \
  'git add .secret-patterns.default && git commit -m "weaken: secret patterns"' \
  "검사 약화 패턴 추가 — .secret-patterns.default"

# 7의 짝 — 같은 파일에 대한 **정상** 규칙 추가는 통과해야 한다.
# 이 저장소 어디에도 없는 벤더 키 모양을 하나 더한다(2026-09-03 실측: 추적 파일 매치 0건).
demo_allow "비밀 패턴 파일 정상 추가" \
  'printf "\n%s\n" "zzk-[A-Za-z0-9]{32,}" >> .secret-patterns.default
   grep -qF "zzk-" .secret-patterns.default' \
  'git add .secret-patterns.default && git commit -m "feat: add vendor key shape"'

# --- 원본 오염 검사 -----------------------------------------------------------
echo
ORIG_AFTER=$(orig_state)
if [ "$ORIG_BEFORE" != "$ORIG_AFTER" ]; then
  echo "FAIL: 시연이 원본 저장소를 변경했다 (before=$ORIG_BEFORE after=$ORIG_AFTER)"
  fail=1
else
  echo "OK: 원본 저장소 무변경 확인 ($ORIG_AFTER)"
fi

echo
if [ "$allow_checked" -lt 1 ]; then
  echo "FAIL: 통과쌍 시연이 0건 — 차단만 시험하면 '전부 막는 훅'도 만점을 받는다"
  fail=1
fi

if [ "$fail" -eq 0 ]; then
  echo "PASS: 위반 $TOTAL 종이 전부 차단됨 (각 건 훅 OFF 대조 통과) + 정상 변경 통과쌍 ${allow_checked}건"
  exit 0
fi
echo "RESULT: 차단되지 않았거나 시연이 무효인 항목이 있다. exit 1"
exit 1
