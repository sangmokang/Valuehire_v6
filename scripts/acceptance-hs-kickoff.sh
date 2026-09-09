#!/usr/bin/env bash
# acceptance-hs-kickoff.sh — HumanSearch 착수 정리(WU-0A)가 실제로 끝났는가.
#
# 무엇을 검사하나(CHECKED 12 = 처분 6 + CI 스텝 수 1 + 문서 3 + CI 배선 1 + 판정 1):
#   1~6  처분표의 대상 6건 각각에 `결론=(병합요청|재작성|폐기)` 와 `근거=` 가 있다.
#   7    docs/sot/verification-commands.md 가 적은 CI 스텝 수 == verify.yml 의 `- name:` 수.
#   8~9  2026-08-17 레쥬메 설계서 2건이 docs/engineering/history/ 에 "v4 전제 역사 기록" 머리말과 함께 있다.
#   10   착수 프롬프트가 docs/engineering/goal-prompts/ 에 있다.
#   11   verify.yml 이 이 스크립트를 run-acceptance.sh 로 감싸 실행한다.
#   12   Codex V2 판정 문서가 docs/engineering/ 에 있고 첫 줄이 VERDICT: 다.
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
    row=$(/usr/bin/grep -F -- "$t" "$DISPOSITION" | /usr/bin/grep -E '^\|' | head -1)
    if [ -z "$row" ]; then
      failc "처분표에 $t 행 없음"
    elif ! printf '%s' "$row" | /usr/bin/grep -qE '결론=(병합요청|재작성|폐기)'; then
      failc "$t 행에 결론=(병합요청|재작성|폐기) 없음"
    elif ! printf '%s' "$row" | /usr/bin/grep -qE '근거=[^|]*[a-zA-Z0-9_./#-]'; then
      failc "$t 행에 근거= 없음"
    else
      pass "처분 $t → $(printf '%s' "$row" | /usr/bin/grep -oE '결론=(병합요청|재작성|폐기)' | head -1)"
    fi
  done
fi

# 7 CI 스텝 수
if [ -f "$VERIFY_YML" ] && [ -f "$VC_DOC" ]; then
  actual=$(/usr/bin/grep -cE '^[[:space:]]*- name:' "$VERIFY_YML")
  documented=$(/usr/bin/grep -oE '워크플로 스텝 [0-9]+개' "$VC_DOC" | head -1 | tr -cd '0-9')
  if [ -n "$documented" ] && [ "$documented" = "$actual" ]; then
    pass "CI 스텝 수 정본=$documented 실제=$actual"
  else
    failc "CI 스텝 수 불일치 정본=${documented:-없음} 실제=$actual"
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

# 11 CI 배선(자기 자신) — 래퍼 경유 실행 줄이 있어야 한다
if [ -f "$VERIFY_YML" ] && /usr/bin/grep -qE 'run: bash scripts/verify/run-acceptance\.sh scripts/acceptance-hs-kickoff\.sh' "$VERIFY_YML"; then
  pass "CI 배선 acceptance-hs-kickoff.sh"
else
  failc "verify.yml 에 acceptance-hs-kickoff.sh 배선 없음"
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
