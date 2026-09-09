#!/usr/bin/env bash
# acceptance-hs-kickoff.sh — HumanSearch 착수 정리(WU-0A)가 실제로 끝났는가.
#
# 무엇을 검사하나(CHECKED 12 = 처분 6 + CI 스텝 수 1 + 문서 3 + CI 배선 1 + 판정 1):
#   1~6  처분표의 대상 6건 각각에 `결론=(병합요청|재작성|폐기)` 와 `근거=` 가 있다.
#   7    docs/sot/verification-commands.md 의 CI 스텝 수·이름·순서 == verify.yml 의 `- name:` (1:1).
#   8~9  2026-08-17 레쥬메 설계서 2건이 docs/engineering/history/ 에 "v4 전제 역사 기록" 머리말과 함께 있다.
#   10   착수 프롬프트가 docs/engineering/goal-prompts/ 에 있다.
#   11   verify.yml 이 이 스크립트와 자기 변이 스크립트를 run-acceptance.sh 로 감싸
#        **주석이 아닌 실행 줄**로 돌리고, 그 스텝에 조건·오류무시가 없다.
#   12   Codex V2 판정 문서가 docs/engineering/ 에 있고 첫 줄이 VERDICT: 다.
#
# 강화 이력(Codex V2 2026-09-09 FAIL 판정): 처분 행 유일성·근거 자리표시자·정본 표의
# 빈 이름 행·실행 줄 주석 위장·오류무시 지시를 각각 잡는다. 음성 대조군은
# scripts/acceptance-hs-kickoff-mutations.sh 가 매번 돌려서 증명한다.
#
# 출력 규약: 판정마다 `PASS: ...` / `FAIL: ...` 한 줄, 마지막에 `CHECKED: <n>`.
# 종료값 0=PASS, 1=FAIL. 검사 대상 파일이 없으면 그 항목은 FAIL 이지 통과가 아니다.
# 이 스크립트는 저장소 안 파일만 읽는다. 네트워크·브라우저·외부 서비스 0.
set -u
cd "$(git rev-parse --show-toplevel)" || exit 1

DISPOSITION="docs/engineering/humansearch-branch-disposition-2026-09-07.md"
VERIFY_YML=".github/workflows/verify.yml"
VC_DOC="docs/sot/verification-commands.md"
HIST_DIR="docs/engineering/history"
PROMPT="docs/engineering/goal-prompts/humansearch-journey-kickoff-2026-09-07.md"
VERDICT_GLOB="docs/engineering/humansearch-kickoff-ledger-verdict-*.md"
EXPECTED=12

checked=0
fail=0
pass() { echo "PASS: $1"; checked=$((checked+1)); }
failc() { echo "FAIL: $1"; checked=$((checked+1)); fail=1; }

# 1~6 처분표
targets=(
  "PR #13"
  "PR #54"
  "PR #15"
  "task/hs-d1-permit"
  "task/hs-l1-malformed-url-fix"
  "task/hs-observe-url-crash"
)
if [ ! -f "$DISPOSITION" ]; then
  for t in "${targets[@]}"; do failc "처분표 없음 — $t 판정 불가 ($DISPOSITION)"; done
else
  for t in "${targets[@]}"; do
    rows=$(/usr/bin/grep -F -- "$t" "$DISPOSITION" | /usr/bin/grep -cE '^\|')
    row=$(/usr/bin/grep -F -- "$t" "$DISPOSITION" | /usr/bin/grep -E '^\|' | head -1)
    ev=$(printf '%s' "$row" | /usr/bin/grep -oE '근거=[^|]*' | head -1 | sed 's/^근거=//')
    ev_alnum=$(printf '%s' "$ev" | tr -cd 'A-Za-z0-9' | wc -c | tr -d ' ')
    ev_solid=$(printf '%s' "$ev" | tr -d '[:space:]' | wc -c | tr -d ' ')
    if [ "$rows" -eq 0 ]; then
      failc "처분표에 $t 행 없음"
    elif [ "$rows" -ne 1 ]; then
      failc "$t 행이 ${rows}개 — 같은 대상에 처분이 둘 이상이면 결론이 무엇인지 정해지지 않는다"
    elif ! printf '%s' "$row" | /usr/bin/grep -qE '결론=(병합요청|재작성|폐기)'; then
      failc "$t 행에 결론=(병합요청|재작성|폐기) 없음"
    elif [ "$ev_alnum" -lt 4 ] || [ "$ev_solid" -lt 8 ]; then
      failc "$t 행의 근거가 자리표시자 — 영숫자 ${ev_alnum}자(4 미만) 또는 공백 제외 ${ev_solid}바이트(8 미만)"
    else
      pass "처분 $t → $(printf '%s' "$row" | /usr/bin/grep -oE '결론=(병합요청|재작성|폐기)' | head -1)"
    fi
  done
fi

# 7 CI 스텝 수
if [ -f "$VERIFY_YML" ] && [ -f "$VC_DOC" ]; then
  actual=$(/usr/bin/grep -cE '^[[:space:]]*- name:' "$VERIFY_YML")
  documented=$(/usr/bin/grep -oE '워크플로 스텝 [0-9]+개' "$VC_DOC" | head -1 | tr -cd '0-9')
  # 수만 같아서는 안 된다 — 정본은 "이름·순서 그대로"를 주장하므로 이름을 1:1 대조한다(Codex V2 지적).
  doc_rows=$(/usr/bin/grep -cE '^\| [0-9]+ \|' "$VC_DOC")
  empty_names=$(/usr/bin/grep -E '^\| [0-9]+ \|' "$VC_DOC" | awk -F'|' '{gsub(/^ +| +$/,"",$3); if ($3 == "") c++} END {print c+0}')
  # 명령치환은 후행 빈 줄을 지운다 — 끝에 표식을 붙여 "이름이 빈 마지막 행"이 사라지지 않게 한다.
  yaml_names=$(/usr/bin/grep -E '^[[:space:]]*- name:' "$VERIFY_YML" | sed -E 's/^[[:space:]]*- name:[[:space:]]*//'; echo '<끝>')
  doc_names=$(/usr/bin/grep -E '^\| [0-9]+ \|' "$VC_DOC" | awk -F'|' '{gsub(/^ +| +$/,"",$3); print $3}'; echo '<끝>')
  if [ -n "$documented" ] && [ "$documented" = "$actual" ] && [ "$doc_rows" = "$actual" ] \
     && [ "$empty_names" -eq 0 ] && [ "$yaml_names" = "$doc_names" ]; then
    pass "CI 스텝 수·이름·순서 정본=$documented 실제=$actual 표 행=$doc_rows 빈 이름 0 이름 1:1"
  else
    mism=$(diff <(printf '%s\n' "$yaml_names") <(printf '%s\n' "$doc_names") | /usr/bin/grep -c '^[<>]')
    failc "CI 스텝 불일치 정본=${documented:-없음} 실제=$actual 표 행=$doc_rows 빈 이름=$empty_names 이름 불일치 줄=$mism"
  fi
else
  failc "verify.yml 또는 verification-commands.md 없음"
fi

# 8~9 역사 기록 문서
for f in resume-evidence-supabase-archive-goal-2026-08-17.md resume-evidence-supabase-implementation-prompt-2026-08-17.md; do
  p="$HIST_DIR/$f"
  if [ -f "$p" ] && head -5 "$p" | /usr/bin/grep -q 'v4 전제 역사 기록'; then
    pass "역사 기록 보존 $f"
  else
    failc "역사 기록 없음 또는 머리말 없음 $p"
  fi
done

# 10 착수 프롬프트
if [ -f "$PROMPT" ] && /usr/bin/grep -q '^# HumanSearch 여정 착수 프롬프트' "$PROMPT"; then
  pass "착수 프롬프트 커밋됨 $PROMPT"
else
  failc "착수 프롬프트 없음 $PROMPT"
fi

# 11 CI 배선(자기 자신 + 자기 변이) — 주석이 아닌 실행 줄이어야 하고, 조건·오류무시가 없어야 한다.
# 문자열 grep 만으로는 실행 줄을 주석으로 위장하고 다른 명령으로 바꿔치기해도 통과한다(Codex V2 지적).
# 그래서 스텝 블록을 잘라 그 안의 run: 줄과 약화 지시를 함께 본다.
wiring_verdict() {
  awk -v t="$1" '
    function flush() {
      if (blk != "" && blk ~ ("\n[ \t]*run: bash scripts/verify/run-acceptance\\.sh scripts/" t "[ \t]*\n")) {
        if (blk ~ /\n[ \t]*if:/ || blk ~ /\n[ \t]*continue-on-error:/) print "WEAK"; else print "OK"
      }
      blk = ""
    }
    /^[[:space:]]*- name:/ { flush() }
    { blk = blk "\n" $0 }
    END { blk = blk "\n"; flush() }
  ' "$VERIFY_YML" | head -1
}
if [ -f "$VERIFY_YML" ]; then
  w_self=$(wiring_verdict 'acceptance-hs-kickoff\\.sh')
  w_mut=$(wiring_verdict 'acceptance-hs-kickoff-mutations\\.sh')
  if [ "$w_self" = "OK" ] && [ "$w_mut" = "OK" ]; then
    pass "CI 배선 2건 — 본 검사·자기 변이 검사 모두 실행 줄이고 조건·오류무시 없음"
  else
    failc "CI 배선 불량 — 본 검사=${w_self:-없음} 자기 변이=${w_mut:-없음} (주석 위장·조건·오류무시·누락)"
  fi
else
  failc "verify.yml 없음"
fi

# 12 Codex V2 판정 문서
verdict=$(ls $VERDICT_GLOB 2>/dev/null | head -1)
if [ -n "$verdict" ] && [ -s "$verdict" ] && head -1 "$verdict" | /usr/bin/grep -qE '^VERDICT: (PASS|FAIL)'; then
  pass "판정 문서 $verdict ($(head -1 "$verdict"))"
else
  failc "판정 문서 없음/빈 파일/첫 줄 VERDICT 아님 ($VERDICT_GLOB)"
fi

echo "CHECKED: $checked"
if [ "$checked" -ne "$EXPECTED" ]; then
  echo "FAIL: 검사 건수 $checked ≠ 기대 $EXPECTED"
  exit 1
fi
exit "$fail"
