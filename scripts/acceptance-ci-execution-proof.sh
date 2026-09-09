#!/usr/bin/env bash
# acceptance-ci-execution-proof.sh — CI 가 인수 스크립트를 "실제로 실행했다"를 증명하는가.
#
# 왜 필요한가 (억제 ci-transfer-guarantee · 만료 2026-09-15):
#   hooks/pre-push 의 CI 이관 보증은 워크플로를 문자열로 파싱한다. 규칙을 하나 막을
#   때마다 우회가 하나씩 늘었고, V1 6차에서 다시 4종이 통과했다:
#     `bash ; echo <path>` · `bash /dev/null <path>` · `bash "" <path>` · `sh /dev/null <path>`
#   넷 다 스크립트를 한 줄도 실행하지 않는다. `if: ${{ false }}` 류 항상-거짓 조건도 남아 있다.
#
#   그래서 판정 근거를 문자열에서 **실행 흔적**으로 바꾼다. run-acceptance.sh 래퍼가
#   판정을 확인한 뒤에만 마커를 남기고, 검수기가 기대 목록 전량이 마커에 있는지 본다.
#   워크플로를 어떻게 편집하든 **실행하지 않으면** 마커가 없으므로 통과할 수 없다.
#
# 시연 방식: 격리 clone 에서 인수 스크립트를 가벼운 스텁으로 치환하고, 워크플로의 run:
#   블록만 뽑아 실행하는 미니 러너로 CI 한 판을 흉내낸다. 실제 인수 검사를 전량 돌리면
#   시연 1건에 10분이 넘어 아무도 돌리지 않게 된다 — 여기서 시험하는 것은 인수 검사의
#   내용이 아니라 **검수기의 판별력**이다.
#
# 계약: exit 0 (전 시연 합격) | exit 1 (하나라도 불합격) | exit 2 (셋업 실패 · fail-closed)
set -uo pipefail

unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE GIT_OBJECT_DIRECTORY \
      GIT_ALTERNATE_OBJECT_DIRECTORIES GIT_COMMON_DIR GIT_PREFIX GIT_QUARANTINE_PATH

REPO=$(git rev-parse --show-toplevel 2>/dev/null) || {
  echo "FAIL: git 저장소가 아니다 (fail-closed)"; echo "CHECKED: 0"; exit 2; }
cd "$REPO" || { echo "FAIL: 저장소 루트로 이동 실패"; echo "CHECKED: 0"; exit 2; }

WF=.github/workflows/verify.yml
WRAPPER=scripts/verify/run-acceptance.sh
AUDITOR=scripts/verify/check-acceptance-markers.sh
for f in "$WF" "$WRAPPER"; do
  [ -f "$f" ] || { echo "FAIL: $f 없음 (fail-closed)"; echo "CHECKED: 0"; exit 2; }
done
command -v ruby >/dev/null 2>&1 || { echo "FAIL: ruby 없음 — 워크플로를 YAML 로 읽을 수 없다"; echo "CHECKED: 0"; exit 2; }

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

# 작업트리 사본으로 덮는다. clone 은 HEAD 를 받으므로 이 줄이 없으면 지금 고치는 중인
# 래퍼·검수기가 아니라 커밋된 옛 버전을 시험하게 된다(2026-09-09 p13 작업에서 실측한 함정).
for f in "$WRAPPER" "$AUDITOR"; do
  [ -f "$f" ] || continue
  mkdir -p "$CLONE/$(dirname "$f")" && cp -p "$f" "$CLONE/$f" && chmod +x "$CLONE/$f" || {
    echo "FAIL: $f 설치 실패"; echo "CHECKED: 0"; exit 2; }
done

# 인수 스크립트를 스텁으로 치환한다. 래퍼 계약(PASS 한 줄 + CHECKED>=1)만 만족시킨다.
stub_count=0
while IFS= read -r s; do
  [ -z "$s" ] && continue
  printf '#!/usr/bin/env bash\necho "PASS: stub %s"\necho "CHECKED: 1"\nexit 0\n' "$s" > "$CLONE/$s"
  chmod +x "$CLONE/$s"; stub_count=$((stub_count + 1))
done < <(cd "$CLONE" && find . -maxdepth 2 -name 'acceptance-*.sh' -not -path './worktrees/*' | sed 's#^\./##' | LC_ALL=C sort)
[ "$stub_count" -ge 5 ] || { echo "FAIL: 스텁 대상이 ${stub_count}개뿐 — 시연 대상 부족 (fail-closed)"; echo "CHECKED: 0"; exit 2; }

# 미니 러너 — 워크플로를 YAML 로 읽어 조건 없는 스텝의 run: 만 실행한다.
# `if:` 가 붙은 스텝은 CI 에서 건너뛰어질 수 있으므로 실행하지 않는다. 그래야
# `if: ${{ false }}` 주입이 "실행 안 됨 → 마커 없음"으로 정직하게 관측된다.
# 러너는 **변조 대상과 관련된 스텝만** 실행한다. 워크플로 전체를 돌리면 히스토리 blob
# 전량 스캔·데이터 노출 스캔까지 매 시연마다 돌아 시연 1건에 수 분이 걸린다(실측: 11 시연
# 8분 넘게 진행 중이었다). 여기서 시험하는 것은 워크플로 전체가 아니라 **한 스텝을 실행하지
# 않게 만들었을 때 마커 검수가 그것을 잡는가**이므로, 그 스텝만 돌리는 것으로 충분하다.
# 조건(`if`)이 붙은 스텝은 실행하지 않는다 — CI 에서 건너뛰어질 수 있으므로, `if: ${{ false }}`
# 주입이 "실행 안 됨 → 마커 없음"으로 정직하게 관측되어야 한다.
cat > "$SANDBOX/runner.rb" <<'RUBY'
require 'psych'
require 'date'
doc = Psych.safe_load(File.read(ARGV[0]), aliases: true, permitted_classes: [Date, Time])
needle = ARGV[2]
cmds = []
(doc['jobs'] || {}).each_value do |job|
  next unless job.is_a?(Hash)
  next if job.key?('if')
  (job['steps'] || []).each do |st|
    next unless st.is_a?(Hash)
    next if st.key?('if')
    r = st['run']
    next unless r
    cmds << r if needle.nil? || needle.empty? || r.include?(needle)
  end
end
File.write(ARGV[1], cmds.join("\n"))
RUBY

run_ci() {  # 미니 러너 실행 → 마커 디렉터리를 채운다
  local dir="$1" needle="${2:-}"
  rm -rf "$dir"; mkdir -p "$dir" || return 2
  ( cd "$CLONE" && ruby "$SANDBOX/runner.rb" "$WF" "$SANDBOX/cmds.sh" "$needle" ) 2>"$SANDBOX/ruby.err" || return 2
  # stdin 을 반드시 막는다. 변조 중 `bash ; echo <path>` 는 **인자 없는 bash** 를 실행하고,
  # 그것은 stdin 에서 명령을 읽으려고 무한정 기다린다(실측: 시연이 7분 넘게 멈춰 있었다).
  # 우회 형태를 정직하게 실행해 보는 것이 이 시연의 목적이므로, 변조를 순화하는 대신
  # 입력을 끊는다.
  ( cd "$CLONE" && ACCEPTANCE_MARKER_DIR="$dir" bash "$SANDBOX/cmds.sh" ) </dev/null >/dev/null 2>&1
  return 0
}

# 검수기의 **실행 실패**(파일 없음 rc=127 · 권한 없음 126)를 판정 불합격과 구별한다.
# 구별하지 않으면 검수기가 아예 없는 상태에서 양성 시연이 전부 "잡았다"로 초록이 된다
# (실측: 구현 0줄인데 8건 PASS). 검사 실행 실패는 판정이 아니라 시연 무효다.
unrunnable() { [ "$1" -eq 127 ] || [ "$1" -eq 126 ]; }
audit() {  # 검수 실행 → 종료값. expect 파일을 주면 기대 목록을 그것으로 좁힌다.
  local dir="$1" expect="${2:-}" rc=0
  if [ -n "$expect" ]; then
    ( cd "$CLONE" && ACCEPTANCE_MARKER_DIR="$dir" ACCEPTANCE_EXPECT_LIST="$expect" bash "$AUDITOR" ) >"$SANDBOX/audit.out" 2>&1 || rc=$?
  else
    ( cd "$CLONE" && ACCEPTANCE_MARKER_DIR="$dir" bash "$AUDITOR" ) >"$SANDBOX/audit.out" 2>&1 || rc=$?
  fi
  echo "$rc"
}

BASE=$(cd "$CLONE" && git rev-parse HEAD)
reset_clone() {
  ( cd "$CLONE" && git checkout --quiet "$BASE" -- "$WF" ) 2>/dev/null
}

# case <설명> <expect: fail|pass> <워크플로 변조 함수>
run_case() {
  local desc="$1" expect="$2" mutate="$3"
  reset_clone
  if [ -n "$mutate" ]; then
    if ! ( cd "$CLONE" && $mutate ) >"$SANDBOX/mut.err" 2>&1; then
      record 1 "$desc" "변조 주입 실패 — 시연 무효: $(head -1 "$SANDBOX/mut.err")"; return
    fi
    if ( cd "$CLONE" && git diff --quiet -- "$WF" ); then
      record 1 "$desc" "변조가 워크플로를 바꾸지 못했다 — 시연 무효"; return
    fi
  fi
  local dir="$SANDBOX/markers"
  if ! run_ci "$dir" "$VPATH"; then
    record 1 "$desc" "미니 러너 실행 실패: $(head -1 "$SANDBOX/ruby.err")"; return
  fi
  printf '%s\n' "$VPATH" > "$SANDBOX/expect.one" || { record 1 "$desc" "기대 목록 파일 생성 실패"; return; }
  local rc; rc=$(audit "$dir" "$SANDBOX/expect.one")
  if unrunnable "$rc"; then
    record 1 "$desc" "검수기를 실행할 수 없다 (rc=$rc · $AUDITOR) — 시연 무효. 실행 실패를 '잡았다'로 세면 구현 0줄에서도 초록이 난다"
    return
  fi
  if [ "$expect" = fail ]; then
    if [ "$rc" -eq 0 ]; then
      record 1 "$desc" "검수가 통과시켰다 (rc=0) — 실행되지 않은 검사를 실행됐다고 판정한다"
    else
      record 0 "$desc"
    fi
  else
    if [ "$rc" -ne 0 ]; then
      record 1 "$desc" "오탐 — 정상 워크플로를 불합격시켰다 (rc=$rc): $(grep -m1 -E 'FAIL|MISSING' "$SANDBOX/audit.out" | head -c 160)"
    else
      record 0 "$desc"
    fi
  fi
}

# 변조 대상 줄을 실제 워크플로에서 고른다 (하드코딩하면 워크플로가 바뀐 뒤 조용히 무의미해진다)
VLINE=$(grep -n "run-acceptance\.sh scripts/acceptance-" "$CLONE/$WF" | head -1 | cut -d: -f1)
[ -n "$VLINE" ] || { echo "FAIL: 변조할 실행 줄을 찾지 못했다"; echo "CHECKED: 0"; exit 2; }
VPATH=$(sed -n "${VLINE}p" "$CLONE/$WF" | sed 's/.*run-acceptance\.sh[[:space:]]*//' | awk '{print $1}')
echo "=== 변조 대상: ${WF}:${VLINE} → $VPATH (스텁 ${stub_count}개) ==="

m_comment()   { sed -i.bak "${VLINE}s#run: #\# run: #" "$WF" && rm -f "$WF.bak"; }
m_echo()      { sed -i.bak "${VLINE}s#run: .*#run: echo $VPATH#" "$WF" && rm -f "$WF.bak"; }
m_devnull()   { sed -i.bak "${VLINE}s#run: .*#run: bash /dev/null $VPATH#" "$WF" && rm -f "$WF.bak"; }
m_emptyarg()  { sed -i.bak "${VLINE}s#run: .*#run: bash \"\" $VPATH#" "$WF" && rm -f "$WF.bak"; }
m_shdevnull() { sed -i.bak "${VLINE}s#run: .*#run: sh /dev/null $VPATH#" "$WF" && rm -f "$WF.bak"; }
m_semicolon() { sed -i.bak "${VLINE}s#run: .*#run: bash ; echo $VPATH#" "$WF" && rm -f "$WF.bak"; }
m_delete()    { sed -i.bak "${VLINE}d" "$WF" && rm -f "$WF.bak"; }
m_falseif()   {
  local ind; ind=$(sed -n "${VLINE}p" "$WF" | sed 's/[^ ].*//')
  sed -i.bak "${VLINE}i\\
${ind}if: \${{ false }}
" "$WF" && rm -f "$WF.bak"
}
m_rename()    { local s=$((VLINE - 1)); sed -i.bak "${s}s/name: .*/name: 이름만 바꾼 스텝/" "$WF" && rm -f "$WF.bak"; }

run_case "손대지 않은 워크플로는 통과한다 (대조군)"        pass ""
run_case "run: 주석 처리를 잡는다"                         fail m_comment
run_case "echo 대체를 잡는다"                              fail m_echo
run_case "bash /dev/null <path> 를 잡는다"                 fail m_devnull
run_case "bash \"\" <path> 를 잡는다"                      fail m_emptyarg
run_case "sh /dev/null <path> 를 잡는다"                   fail m_shdevnull
run_case "bash ; echo <path> 를 잡는다"                    fail m_semicolon
run_case "스텝 본문 삭제를 잡는다"                         fail m_delete
run_case "if: \${{ false }} 를 잡는다"                     fail m_falseif
run_case "스텝 이름 변경은 통과한다 (오탐 대조)"           pass m_rename

# --- 생산 경로 시연 ------------------------------------------------------------
# 위 시연들은 기대 목록을 한 개로 좁혀 돈다(빠르게 하기 위해). 좁힌 목록으로만 시험하면
# **인자 없는 생산 경로**(검수기가 스스로 글로브로 기대 목록을 만드는 그 경로)가 한 번도
# 시험되지 않는다 — 2026-09-06 에 같은 함정으로 전량 초록이 난 적이 있다.
# 그래서 글로브 기대 목록을 쓰는 시연 두 건을 러너 없이 직접 돌린다.
fill_all_markers() {  # 모든 스텁을 래퍼로 실행해 마커를 채운다. <제외할 경로>
  local dir="$1" skip="${2:-}"
  rm -rf "$dir"; mkdir -p "$dir" || return 1
  local s
  while IFS= read -r s; do
    [ -z "$s" ] && continue
    [ -n "$skip" ] && [ "$s" = "$skip" ] && continue
    ( cd "$CLONE" && ACCEPTANCE_MARKER_DIR="$dir" bash "$WRAPPER" "$s" ) </dev/null >/dev/null 2>&1
  done < <(cd "$CLONE" && find . -maxdepth 2 -name 'acceptance-*.sh' -not -path './worktrees/*' | sed 's#^\./##' | LC_ALL=C sort)
  return 0
}

reset_clone
DIRALL="$SANDBOX/markers-all"
if ! fill_all_markers "$DIRALL"; then
  record 1 "글로브 기대 목록: 전량 실행하면 통과한다 (생산 경로 대조군)" "마커 채우기 실패"
else
  rc=$(audit "$DIRALL")
  if [ "$rc" -ne 0 ]; then
    record 1 "글로브 기대 목록: 전량 실행하면 통과한다 (생산 경로 대조군)" "오탐 (rc=$rc): $(grep -m1 -E 'FAIL|MISSING' "$SANDBOX/audit.out" | head -c 200)"
  else
    record 0 "글로브 기대 목록: 전량 실행하면 통과한다 (생산 경로 대조군)"
  fi
fi

SKIP=$(cd "$CLONE" && find . -maxdepth 2 -name 'acceptance-*.sh' -not -path './worktrees/*' | sed 's#^\./##' | LC_ALL=C sort | head -1)
if [ -z "$SKIP" ]; then
  record 1 "글로브 기대 목록: 한 개만 빠져도 불합격한다 (생산 경로)" "제외 대상 없음 — 시연 무효"
else
  if ! fill_all_markers "$SANDBOX/markers-skip" "$SKIP"; then
    record 1 "글로브 기대 목록: 한 개만 빠져도 불합격한다 (생산 경로)" "마커 채우기 실패"
  else
    rc=$(audit "$SANDBOX/markers-skip")
    if unrunnable "$rc"; then
      record 1 "글로브 기대 목록: 한 개만 빠져도 불합격한다 (생산 경로)" "검수기를 실행할 수 없다 (rc=$rc) — 시연 무효"
    elif [ "$rc" -eq 0 ]; then
      record 1 "글로브 기대 목록: 한 개만 빠져도 불합격한다 (생산 경로)" "$SKIP 를 빼도 통과했다 (rc=0) — 신규 인수 스크립트의 CI 등록 누락이 안 잡힌다"
    else
      record 0 "글로브 기대 목록: 한 개만 빠져도 불합격한다 (생산 경로) — 누락: $SKIP"
    fi
  fi
fi

# --- 마커 디렉터리 자체가 없을 때 (fail-closed) --------------------------------
rc=$(audit "$SANDBOX/markers-absent-$$")
if unrunnable "$rc"; then
  record 1 "마커 디렉터리가 없으면 불합격한다 (fail-closed)" "검수기를 실행할 수 없다 (rc=$rc) — 시연 무효"
elif [ "$rc" -eq 0 ]; then
  record 1 "마커 디렉터리가 없으면 불합격한다 (fail-closed)" "마커가 하나도 없는데 통과했다 — 검수 자체가 안 돈 것과 구별되지 않는다"
else
  record 0 "마커 디렉터리가 없으면 불합격한다 (fail-closed)"
fi

# 배선 — 검수기가 CI 에서 실제로 돌지 않으면 위 전부가 장식이다.
if grep -q 'check-acceptance-markers\.sh' "$WF"; then
  record 0 "워크플로가 마커 검수기를 실행한다 (배선)"
else
  record 1 "워크플로가 마커 검수기를 실행한다 (배선)" "CI 에 검수 스텝이 없다 — 마커를 아무도 대조하지 않는다"
fi

echo
echo "CHECKED: $checked"
[ "$fail" -ne 0 ] && { echo "RESULT: 불합격 — 실행 증명이 성립하지 않는다"; exit 1; }
echo "RESULT: 합격 — 실행하지 않은 검사는 CI 를 통과하지 못한다"
exit 0
