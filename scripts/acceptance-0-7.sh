#!/usr/bin/env bash
# 0-7 인수 스크립트 — 로컬 강제 장치(git hook)가 실제로 위반을 차단하는가.
#
# 계약: docs/engineering/hook-enforcement-goal-2026-08-07.md ⑩
#   출력  : exit 0 (6종 전부 BLOCKED) | exit 1 (하나라도 통과 = 결함)
#   불변식: 모든 시연은 mktemp -d 안의 clone 에서 수행한다. 원본 저장소를 건드리지 않는다.
#          판정은 종료 코드로만 한다. 문자열 비교 단독 판정 금지.
#          검사를 실행하지 못한 경우도 실패로 판정한다(fail-closed).
#
# 이 스크립트는 자기 자신을 검사 대상에서 제외하지 않는다(P13).
set -euo pipefail

TOTAL=6
fail=0
step=0

REPO_ROOT=$(git rev-parse --show-toplevel) || { echo "FAIL: git 저장소가 아님"; exit 1; }

# --- 원본 오염 감시: 시연 전 상태를 해시로 고정 -------------------------------
orig_state() { (cd "$REPO_ROOT" && git status --porcelain | LC_ALL=C sort | shasum | awk '{print $1}'); }
ORIG_BEFORE=$(orig_state)

sandbox=$(mktemp -d) || { echo "FAIL: 샌드박스 생성 실패"; exit 1; }
cleanup() { rm -rf "$sandbox"; }
trap cleanup EXIT
trap 'cleanup; trap - EXIT; exit 143' TERM
trap 'cleanup; trap - EXIT; exit 130' INT
trap 'cleanup; trap - EXIT; exit 129' HUP

# --- 전제 0: 훅 인프라가 존재하는가 (없으면 나머지 시연은 무의미) --------------
echo "=== 전제 검사: 훅 인프라 ==="
for f in hooks/pre-commit hooks/pre-push scripts/install-hooks.sh scripts/session-status.sh; do
  if [ ! -f "$REPO_ROOT/$f" ]; then
    echo "FAIL: $f 없음 — 로컬 강제 장치가 설치되지 않았다"
    fail=1
  elif [ ! -x "$REPO_ROOT/$f" ]; then
    echo "FAIL: $f 실행 권한 없음 — 훅은 존재해도 조용히 통과한다"
    fail=1
  fi
done
if [ ! -f "$REPO_ROOT/.claude/settings.json" ]; then
  echo "FAIL: .claude/settings.json 없음 — SessionStart hook 미등록 (AC-5)"
  fail=1
fi
if [ "$fail" -ne 0 ]; then
  echo
  echo "RESULT: 전제 미충족 — 시연을 진행할 수 없다. exit 1"
  exit 1
fi
echo "OK: 훅 파일 4종 + settings.json 존재"
echo

# --- 샌드박스 clone + 훅 설치 -------------------------------------------------
git clone -q "$REPO_ROOT" "$sandbox/repo" || { echo "FAIL: clone 실패"; exit 1; }
cd "$sandbox/repo"
git config user.email "acceptance@local"
git config user.name "acceptance"

bash scripts/install-hooks.sh >/dev/null 2>&1 || { echo "FAIL: install-hooks.sh 실패"; exit 1; }

# readback: 설치가 실제로 됐는지 (install 스크립트의 자기 보고를 믿지 않는다)
hp=$(git config --get core.hooksPath || true)
[ "$hp" = "hooks" ] || { echo "FAIL: core.hooksPath='$hp' (기대 'hooks') — 훅이 연결되지 않음"; exit 1; }
[ -x hooks/pre-commit ] || { echo "FAIL: clone 에서 pre-commit 실행 권한 없음"; exit 1; }
echo "=== 시연 (샌드박스: $sandbox/repo) ==="

# --- 시연 도구 ----------------------------------------------------------------
# demo <이름> — stdin 으로 받은 셸 코드를 실행하고, 그것이 실패(=차단)해야 통과.
demo() {
  local name="$1"
  step=$((step + 1))
  local body; body=$(cat)
  set +e
  ( eval "$body" ) >"$sandbox/out.$step" 2>&1
  local rc=$?
  set -e
  if [ "$rc" -ne 0 ]; then
    echo "[$step/$TOTAL] $name → BLOCKED (exit=$rc)"
    sed 's/^/         /' "$sandbox/out.$step" | grep -m1 'BLOCKED' || true
  else
    echo "[$step/$TOTAL] $name → PASSED ← 결함 (차단되지 않음)"
    fail=1
  fi
  # 다음 시연을 위해 작업트리 원복
  git reset -q --hard HEAD && git clean -qfd
}

# 1. 검사기가 자기 자신을 검사 대상에서 제외 (§0 E1 재현)
demo "검사기 자기 제외" <<'BODY'
  sed -i.bak "s|^LEAKS=.*|LEAKS=\$(git ls-files | grep -v '^verify\\.sh\$' | xargs grep -l x)|" verify.sh
  rm -f verify.sh.bak
  git add verify.sh && git commit -m "weaken: self-exempt"
BODY

# 2. 검사를 skip / || true 로 완화 (48143a7 · 129f61d 재현)
demo "검사 약화(|| true)" <<'BODY'
  printf '\nbash verify.sh || true\n' >> scripts/acceptance-0-2.sh
  git add scripts/acceptance-0-2.sh && git commit -m "weaken: swallow failure"
BODY

# 3. 만료일 없는 억제 (98d923f — 35일 방치 재현)
demo "만료일 없는 억제" <<'BODY'
  printf -- '- check: hard_exclude_freelancer\n  reason: "later"\n  owner: someone\n' > suppressions.yaml
  git add suppressions.yaml && git commit -m "suppress: no expiry"
BODY

# 4. LLM 출력 숫자를 판정 필드에 기록 (v4 QA-094 재현)
demo "LLM 출력→판정 필드" <<'BODY'
  mkdir -p src
  printf 'const r = await llm.chat(p);\nscore = parseFloat(r.text);\ndb.insert({ fit_score: score });\n' > src/scoring.js
  git add src/scoring.js && git commit -m "feat: scoring"
BODY

# 5. 커밋 안 된 변경을 둔 채 push (78f3631 ② 재현)
demo "미커밋 상태로 push" <<'BODY'
  echo "dirty" > uncommitted.txt
  git push --dry-run origin HEAD:refs/heads/probe-0-7
BODY

# 6. 외부 효과 코드에 네트워크 호출이 0건 (§0 E5 gptreview.js 재현)
demo "가짜 외부효과 모듈" <<'BODY'
  mkdir -p src
  printf 'async function fetchProfile() {\n  console.log("fetching...");\n  return { ok: true };\n}\n' > src/portal-login.js
  git add src/portal-login.js && git commit -m "feat: portal login"
BODY

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
if [ "$fail" -eq 0 ]; then
  echo "PASS: 위반 $TOTAL 종이 전부 차단됨"
  exit 0
fi
echo "RESULT: 차단되지 않은 위반이 있다. exit 1"
exit 1
