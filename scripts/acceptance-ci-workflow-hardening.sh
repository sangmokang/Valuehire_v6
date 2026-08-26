#!/usr/bin/env bash
# acceptance-ci-workflow-hardening.sh — V1 적대 검증(2026-08-27)이 뚫은 반례를 회귀로 고정한다.
#
# V1 이 실제로 뚫은 것 (전부 사본에서 명령으로 재현하고 `bash -e` 로 삼킴을 실증함):
#   F1 [치명] 오류 삼킴 탐지가 "줄 끝 꼬리" 6종뿐이었다. `|| true; echo done` 처럼 꼬리를
#             줄 중간에 두거나 `set +e` · `trap 'exit 0' ERR` · `&` · `| cat` 로 실패 전파를
#             끊는 16개 변형이 전부 통과했다.
#   F2 [치명] `shell:` 과 `defaults.run.shell` 을 아무도 보지 않았다. GitHub 은 커스텀 shell 에
#             `-e` 를 붙이지 않으므로, 이 키 하나로 다줄 스텝 중간 줄의 실패가 전부 무시된다.
#   F3 [높음] 필수 명령 대조가 주석을 걷어내지 않는 substring 이었다. `echo "bash …"` ·
#             `printf` · `: bash …` · `# bash …` 가 전부 "명령이 있다"로 셌다.
#   F4 [높음] 트리거는 키 존재만 봤다. `push: branches: ["never-such-branch"]` 나
#             `paths-ignore: ["**"]` 로 워크플로를 영구히 실행되지 않게 만들어도 통과했다.
#
# 계약: 위 변형은 전부 scripts/verify/check-ci-required-manifest.sh 가 불합격시켜야 한다.
#       손대지 않은 워크플로는 그대로 통과해야 한다(과잉 차단이면 그것도 결함이다).
set -uo pipefail

unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE GIT_OBJECT_DIRECTORY \
  GIT_ALTERNATE_OBJECT_DIRECTORIES GIT_COMMON_DIR GIT_PREFIX GIT_QUARANTINE_PATH

REPO=$(git rev-parse --show-toplevel 2>/dev/null) || {
  echo "NOT_RUN: git 저장소가 아니다"
  echo "CHECKED: 0"
  exit 2
}
cd "$REPO" || exit 2

CHECKER="$REPO/scripts/verify/check-ci-required-manifest.sh"
MANIFEST="$REPO/docs/sot/ci-required-manifest.yaml"
WF="$REPO/.github/workflows/verify.yml"
HELPER="$REPO/scripts/verify/wf-mutate.rb"

for required in "$CHECKER" "$MANIFEST" "$WF" "$HELPER"; do
  if [ ! -f "$required" ]; then
    echo "FAIL: 필요한 파일이 없다 — $required (fail-closed)"
    echo "CHECKED: 0"
    exit 2
  fi
done

SNAPSHOT=$(git status --porcelain)
TMP=$(mktemp -d) || {
  echo "NOT_RUN: mktemp 실패"
  echo "CHECKED: 0"
  exit 2
}
case "$TMP" in
  /tmp/*|/private/tmp/*|/var/folders/*|/private/var/folders/*) ;;
  *) echo "NOT_RUN: 안전하지 않은 임시 경로 — $TMP"; echo "CHECKED: 0"; exit 2 ;;
esac
trap 'ruby -rfileutils -e "FileUtils.remove_entry(ARGV[0]) if File.exist?(ARGV[0])" "$TMP"' EXIT

TOTAL=38
checked=0
failed=0

record() {
  local ok="$1"
  local label="$2"
  local detail="$3"
  checked=$((checked + 1))
  if [ "$ok" -eq 0 ]; then
    printf 'PASS: %s — %s\n' "$label" "$detail"
  else
    printf 'FAIL: %s — %s\n' "$label" "$detail"
    failed=1
  fi
}

# attack <설명> <기대 종료값> <변형 이름> <변형 인자...>
# 변형은 scripts/verify/wf-mutate.rb 가 수행한다. 주입이 실패하면 그 스크립트가 exit 1 로
# 알리고, 여기서는 "공격하지 않은 채 통과"를 합격으로 세지 않는다.
attack() {
  local label="$1"
  local wanted="$2"
  shift 2
  local out="$TMP/wf-$checked.yml"
  cp "$WF" "$out" || { record 1 "$label" "사본 생성 실패"; return; }
  if ! ruby "$HELPER" "$out" "$@" > /dev/null 2>&1; then
    record 1 "$label" "주입 실패 — 공격이 실행되지 않았다 (mutate: $*)"
    return
  fi
  local rc=0
  local text=""
  text=$(WORKFLOW_FILE="$out" bash "$CHECKER" "$MANIFEST" 2>&1) || rc=$?
  if [ "$rc" -eq "$wanted" ]; then
    record 0 "$label" "exit=$rc"
  else
    record 1 "$label" "expected exit=$wanted actual=$rc / $(printf '%s' "$text" | grep '^FAIL:' | head -1)"
  fi
}

# ── 통과 쪽: 손대지 않은 워크플로 ───────────────────────────────────────────
clean_rc=0
clean_out=$(WORKFLOW_FILE="$WF" bash "$CHECKER" "$MANIFEST" 2>&1) || clean_rc=$?
if [ "$clean_rc" -eq 0 ]; then
  record 0 "손대지 않은 워크플로 → 통과" "exit=0 (과잉 차단 없음)"
else
  record 1 "손대지 않은 워크플로 → 통과" "exit=$clean_rc / $(printf '%s' "$clean_out" | grep '^FAIL:' | head -1)"
fi

# ── F1: 필수 명령 뒤에 실패를 삼키는 것을 붙인다 ────────────────────────────
OR='|'
OR="$OR|"
attack "F1-1 꼬리를 줄 중간에 둠 ($OR true; echo done)"      1 append-run "$OR true; echo done"
attack "F1-2 꼬리 뒤 주석 ($OR true  # keep going)"           1 append-run "$OR true  # keep going"
attack "F1-3 실패를 경고 출력으로 바꿈 ($OR echo warn)"        1 append-run "$OR echo warn"
attack "F1-4 절대경로 true ($OR /bin/true)"                   1 append-run "$OR /bin/true"
attack "F1-5 실패를 성공 종료로 ($OR exit 0 # done)"           1 append-run "$OR exit 0 # done"
attack "F1-6 세미콜론으로 이어 붙임 (; echo done)"             1 append-run "; echo done"
attack "F1-7 백그라운드로 던짐 (&)"                            1 append-run " &"
attack "F1-8 파이프로 종료값 가림 (| cat)"                     1 append-run " | cat"
attack "F1-9 tee 로 종료값 가림"                               1 append-run " 2>&1 | tee /dev/null"
attack "F1-10 오류 전파 끄기 (set +e)"                         1 prepend-run "set +e"
attack "F1-11 오류 전파 끄기 (set +o errexit)"                 1 prepend-run "set +o errexit"
attack "F1-12 ERR 트랩으로 성공 종료"                          1 prepend-run "trap 'exit 0' ERR"

# ── F2: shell 을 바꿔 -e 를 떼어낸다 ────────────────────────────────────────
attack "F2-1 스텝에 shell 지정"           1 step-shell hs-cleanroom "bash {0}"
attack "F2-2 워크플로 defaults 에 shell"  1 workflow-shell "bash {0}"
attack "F2-3 job defaults 에 shell"       1 job-shell verify "bash {0}"

# ── F3: 실행처럼 보이지만 실행하지 않는 형태 ───────────────────────────────
attack "F3-1 인용 echo 로 위장"     1 wrap-run 'echo "CMD"'
attack "F3-2 printf 로 위장"        1 wrap-run "printf '%s\\n' \"CMD\""
attack "F3-3 no-op 콜론으로 위장"   1 wrap-run ': CMD'
attack "F3-4 명령 자체를 주석 처리" 1 wrap-run '# CMD'

# ── F4: 트리거를 남기고 필터로 영구 비활성화한다 ───────────────────────────
attack "F4-1 도달 불가 branches 필터" 1 trigger-filter push branches never-such-branch
attack "F4-2 모든 경로 무시 필터"     1 trigger-filter push paths-ignore '**'
attack "F4-3 도달 불가 태그 필터"     1 trigger-filter push tags never-such-tag

# ── V2 G1 (치명): 단독 줄이어도 그 줄이 실행되지 않을 수 있다 ──────────────
# 2026-08-27 V2 실측: 명령을 단독 줄로 두면서도 도달하지 못하게 만드는 다섯 형태가
# 전부 통과했다. "그 줄에 혼자 있는가"만 보고 "그 줄에 닿는가"를 보지 않았기 때문이다.
attack "G1-1 앞에 exit 0 을 두어 죽은 코드로"     1 wrap-run 'exit 0
CMD'
attack "G1-2 거짓 분기 안으로 옮김"                1 wrap-run 'if false; then
  CMD
fi'
attack "G1-3 호출되지 않는 함수 안으로 옮김"       1 wrap-run 'never_called() {
  CMD
}'
attack "G1-4 command 접두로 set +e 우회"           1 wrap-run 'command set +e
CMD
true'
attack "G1-5 숫자 heredoc 마커로 위장"             1 wrap-run 'cat <<'"'"'123'"'"'
CMD
123'

# ── V2 G2 (높음): must_run_contains 자리는 여전히 echo 위장을 허용했다 ─────
# 인라인 본문 스텝 다섯 곳은 조각 대조라, 본문을 조각을 인용한 echo 한 줄로 바꿔도
# "조각이 있다"로 셌다.
attack "G2-1 history-scan 본문을 echo 한 줄로"        1 contains-echo history-scan "git cat-file blob"
attack "G2-2 suppressions-expiry 본문을 echo 한 줄로" 1 contains-echo suppressions-expiry "suppressions.yaml"
attack "G2-3 hooks-present 본문을 echo 한 줄로"       1 contains-echo hooks-present "hooks/pre-commit hooks/pre-push"
attack "G2-4 shell-syntax 본문을 echo 한 줄로"        1 contains-echo shell-syntax "bash -n"
attack "G2-5 pattern-file-selfcheck 본문을 echo 로"   1 contains-echo pattern-file-selfcheck ".secret-patterns.default"

# ── V2 G4 (높음): YAML 1.1 에서 on 과 true 가 같은 키로 합쳐진다 ───────────
# 원문의 `on:` 은 그대로 두고 최상위 `true:` 블록을 덧붙이면, 검사기는 GitHub 이
# 트리거로 보는 노드가 아니라 합쳐진 다른 노드를 읽고 초록을 낸다.
attack "G4-1 최상위 true: 키를 덧붙여 트리거를 흐림" 1 true-key

# ── V2 3차 H1~H3: 줄 연속과 블록 경계를 제대로 못 봤다 ─────────────────────
# 2026-08-27 V2 실측 3건. 하나는 미탐, 둘은 정상 구성을 막는 오탐이다.
#
# H1 미탐 — 백슬래시로 줄을 이으면 뒷줄이 앞줄의 조건에 매달린다. 그런데 별개 줄로 봐서
#          "단독 줄에 있다"로 셌다.
attack "H1 백슬래시 줄 연속으로 조건에 매닮 → 불합격" 1 wrap-run 'false && \
CMD'

# H2 오탐 — 조건부 중괄호 그룹 안의 exit 을 전역 종료로 오인해, 그 뒤의 정상 명령을
#          죽은 코드로 잘못 판정했다. 그룹은 조건이 거짓이면 아예 실행되지 않는다.
attack "H2 조건부 그룹 안 exit 뒤의 정상 명령 → 통과(오차단 없음)" 0 wrap-run 'false && {
  exit 0
}
CMD'

# H3 오탐 — 한 줄에서 열고 닫는 블록(`if …; then …; fi`)은 깊이를 되돌려야 하는데,
#          닫기를 먼저 세고 열기를 나중에 세는 순서 탓에 다음 줄이 블록 안으로 보였다.
attack "H3 한 줄 완결 블록 뒤의 정상 명령 → 통과(오차단 없음)" 0 wrap-run 'if true; then :; fi
CMD'

# ── 원본 불변 ───────────────────────────────────────────────────────────────
current=$(git status --porcelain)
if [ "$current" = "$SNAPSHOT" ]; then
  record 0 "원본 저장소 상태 불변" "before/after 동일"
else
  record 1 "원본 저장소 상태 불변" "변경 발생"
fi

printf 'CHECKED: %d\n' "$checked"
if [ "$checked" -ne "$TOTAL" ]; then
  printf 'FAIL: 실행 사례 수 불일치 — expected=%d actual=%d\n' "$TOTAL" "$checked"
  failed=1
fi
if [ "$failed" -eq 0 ]; then
  echo "VERDICT: PASS"
else
  echo "VERDICT: FAIL"
fi
exit "$failed"
