#!/usr/bin/env bash
# acceptance-hs-kickoff.sh — HumanSearch 착수 정리(WU-0A)가 실제로 끝났는가.
#
# 무엇을 검사하나(CHECKED 12 = 처분 6 + CI 스텝 수 1 + 문서 3 + CI 배선 1 + 판정 1):
#   1~6  처분표의 대상 6건 각각에 `결론=(병합요청|재작성|폐기)` 와 `근거=` 가 있다.
#   7    docs/sot/verification-commands.md 의 CI 스텝 수·이름·순서 == verify.yml 의 `- name:` (1:1).
#   8~9  2026-08-17 레쥬메 설계서 2건이 docs/engineering/history/ 에 "v4 전제 역사 기록" 머리말과 함께 있다.
#   10   착수 프롬프트가 docs/engineering/goal-prompts/ 에 있다.
#   11   verify.yml 을 YAML 로 읽어, 이 스크립트와 자기 변이 스크립트가 스텝의 **실제
#        실행 명령**이고 그 스텝에 조건·오류무시 키가 없다(중복 키·미끼 문자열 배제).
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
  # 표를 열로 나눠 읽는다. 대상 문자열이 행의 어느 열에 있든 세면, 한 행에 대상 6개를
  # 몰아 적고 나머지를 지워도 여섯 판정이 모두 통과한다(Codex V2 5회차 지적).
  # 코드 펜스(백틱·물결표, 0~3칸 들여쓰기) 안쪽은 표가 아니다.
  # 출력: <대상열>\t<결론열>\t<근거열>
  disposition_cells() {
    awk '
      {
        line = $0
        sub(/^[ ]+/, "", line)
        indent = length($0) - length(line)
      }
      indent <= 3 && (substr(line, 1, 3) == "```" || substr(line, 1, 3) == "~~~") { fence = !fence; next }
      fence { next }
      substr(line, 1, 1) == "|" {
        n = split(line, c, "|")
        if (n != 7) next                      # | # | 대상 | 결론 | 근거 | 다음 행동 |
        for (k = 1; k <= n; k++) { gsub(/^[ \t]+|[ \t]+$/, "", c[k]) }
        if (c[3] == "" || c[4] == "") next
        print c[3] "\t" c[4] "\t" c[5]
      }
    ' "$DISPOSITION"
  }

  CELLS=$(disposition_cells)
  for t in "${targets[@]}"; do
    rows=$(printf '%s\n' "$CELLS" | awk -F'\t' -v t="$t" 'NF && index($1, t) > 0' | /usr/bin/grep -c .)
    row=$(printf '%s\n' "$CELLS" | awk -F'\t' -v t="$t" 'NF && index($1, t) > 0' | head -1)
    ev=$(printf '%s' "$row" | cut -f3 | sed 's/^근거=//')
    # 대상 열에 여러 대상을 몰아 적고 나머지 행을 지우면 여섯 판정이 모두 통과한다(Codex V2 5회차).
    others=0
    for u in "${targets[@]}"; do
      [ "$u" = "$t" ] && continue
      case "$t" in *"$u"*) continue;; esac
      if printf '%s' "$row" | cut -f1 | /usr/bin/grep -qF -- "$u"; then others=$((others+1)); fi
    done
    ev_alnum=$(printf '%s' "$ev" | tr -cd 'A-Za-z0-9' | wc -c | tr -d ' ')
    ev_solid=$(printf '%s' "$ev" | tr -d '[:space:]' | wc -c | tr -d ' ')
    # 근거는 "실행한 명령·경로·커밋"이어야 한다. 뜻 없는 영숫자(abcdefgh)를 막으려면
    # 길이만으로는 부족하다 — 코드 스팬(`...`) 한 쌍 이상을 요구한다(Codex V2 2회차 지적).
    ev_ticks=$(printf '%s' "$ev" | tr -cd '`' | wc -c | tr -d ' ')
    # 코드 스팬으로 감싸기만 하면 `abcdefgh` 도 통과한다(Codex V2 3회차 지적).
    # 근거의 형태 자체를 요구한다 — PR 번호(#12), 커밋(16진 7자 이상), 경로(a/b), 줄번호(:12).
    # 형태만 맞으면 `aaaa/bbbb.md:12` 같은 가짜도 통과한다(Codex V2 5회차 지적).
    # 근거에 적힌 커밋과 저장소 경로가 **실제로 있는지** 확인한다. 하나 이상 실증돼야 한다.
    ev_real=0
    ev_bad=""
    for tok in $(printf '%s' "$ev" | tr '`,;()[]' ' ' | tr ' ' '\n' \
                 | /usr/bin/grep -E '^[0-9a-f]{7,40}$' | /usr/bin/grep -E '[a-f]' | sort -u); do
      if git cat-file -e "${tok}^{commit}" 2>/dev/null; then ev_real=$((ev_real+1)); else ev_bad="$ev_bad $tok"; fi
    done
    for tok in $(printf '%s' "$ev" | tr '`,;()[]' ' ' | tr ' ' '\n' | sed 's/:[0-9]*$//' \
                 | /usr/bin/grep -E '^[A-Za-z0-9_.-]+(/[A-Za-z0-9_.-]+)+\.(md|py|sh|yml|yaml|ts|tsx|json)$' | sort -u); do
      if [ -e "$tok" ]; then
        ev_real=$((ev_real+1))
      elif [ "${t#task/}" != "$t" ] && git cat-file -e "$t:$tok" 2>/dev/null; then
        ev_real=$((ev_real+1))          # 대상이 브랜치면 그 브랜치에서 확인한다
      else
        ev_bad="$ev_bad $tok"
      fi
    done
    if [ "$rows" -eq 0 ]; then
      failc "처분표에 $t 행 없음"
    elif [ "$others" -gt 0 ]; then
      failc "$t 행의 대상 칸에 다른 대상 ${others}개가 함께 적혀 있다 — 대상마다 자기 행이 있어야 한다"
    elif [ "$rows" -ne 1 ]; then
      failc "$t 행이 ${rows}개 — 같은 대상에 처분이 둘 이상이면 결론이 무엇인지 정해지지 않는다"
    elif ! printf '%s' "$row" | cut -f2 | /usr/bin/grep -qE '^결론=(병합요청|재작성|폐기)$'; then
      failc "$t 행에 결론=(병합요청|재작성|폐기) 없음"
    elif [ "$ev_alnum" -lt 4 ] || [ "$ev_solid" -lt 8 ] || [ "$ev_ticks" -lt 2 ]; then
      failc "$t 행의 근거가 자리표시자 — 영숫자 ${ev_alnum}자(4 미만)·공백 제외 ${ev_solid}바이트(8 미만)·코드 스팬 표시 ${ev_ticks}개(2 미만) 중 하나"
    elif [ -n "$ev_bad" ]; then
      failc "$t 행의 근거에 실재하지 않는 것이 있다 —$ev_bad"
    elif [ "$ev_real" -eq 0 ]; then
      failc "$t 행의 근거에 실증 가능한 커밋·경로가 없다 (실존 확인 0건)"
    else
      pass "처분 $t → $(printf '%s' "$row" | cut -f2) (근거 실증 $ev_real 건)"
    fi
  done
fi

# 워크플로를 한 번만 읽는다. 읽지 못하면 항목 7·11 이 각각 실패를 세어 CHECKED 가 흔들린다.
STEPS=""
STEPS_ERR=""
if [ -f "$VERIFY_YML" ]; then
  STEPS=$(python3 scripts/verify/list-workflow-steps.py "$VERIFY_YML" 2>&1) || {
    STEPS_ERR="$STEPS"
    STEPS=""
  }
fi

# 7 CI 스텝 수·이름·순서
if [ -n "$STEPS_ERR" ]; then
  failc "워크플로를 정규 형식으로 읽지 못했다 — $STEPS_ERR"
elif [ -f "$VERIFY_YML" ] && [ -f "$VC_DOC" ]; then
  # `- name:` 을 문자열로 세면 이름 없는 스텝(uses 만 있는 checkout)이 통째로 빠지고,
  # 여러 줄 문자열 안의 가짜 머리글이 스텝으로 세어진다. YAML 로 읽는다.
  actual=$(printf '%s' "$STEPS" | /usr/bin/grep -c . )
  documented=$(/usr/bin/grep -oE '워크플로 스텝 [0-9]+개' "$VC_DOC" | head -1 | tr -cd '0-9')
  # 수만 같아서는 안 된다 — 정본은 "이름·순서 그대로"를 주장하므로 이름을 1:1 대조한다(Codex V2 지적).
  doc_rows=$(/usr/bin/grep -cE '^\| [0-9]+ \|' "$VC_DOC")
  empty_names=$(/usr/bin/grep -E '^\| [0-9]+ \|' "$VC_DOC" | awk -F'|' '{gsub(/^ +| +$/,"",$3); if ($3 == "") c++} END {print c+0}')
  # 행 번호가 1..N 으로 유일·연속이어야 한다. 번호를 중복시키면 행 수는 맞고 내용만 바뀐다.
  num_seq=$(/usr/bin/grep -E '^\| [0-9]+ \|' "$VC_DOC" | awk -F'|' '{gsub(/ /,"",$2); if ($2+0 != NR) bad=1} END {print bad+0}')
  # 명령치환은 후행 빈 줄을 지운다 — 끝에 표식을 붙여 "이름이 빈 마지막 행"이 사라지지 않게 한다.
  yaml_names=$(printf '%s\n' "$STEPS" | awk -F'\t' 'NF{print $2}'; echo '<끝>')
  doc_names=$(/usr/bin/grep -E '^\| [0-9]+ \|' "$VC_DOC" | awk -F'|' '{gsub(/^ +| +$/,"",$3); print $3}'; echo '<끝>')
  if [ -n "$documented" ] && [ "$documented" = "$actual" ] && [ "$doc_rows" = "$actual" ] \
     && [ "$empty_names" -eq 0 ] && [ "$num_seq" -eq 0 ] && [ "$yaml_names" = "$doc_names" ]; then
    pass "CI 스텝 수·이름·순서 정본=$documented 실제=$actual 표 행=$doc_rows 빈 이름 0 번호 1..$doc_rows 이름 1:1"
  else
    mism=$(diff <(printf '%s\n' "$yaml_names") <(printf '%s\n' "$doc_names") | /usr/bin/grep -c '^[<>]')
    failc "CI 스텝 불일치 정본=${documented:-없음} 실제=$actual 표 행=$doc_rows 빈 이름=$empty_names 번호 어긋남=$num_seq 이름 불일치 줄=$mism"
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

# 11 CI 배선 — 기대한 **이름의 스텝**이 기대한 명령을 돌려야 한다.
# 명령만 보면 이름이 다른 스텝으로 명령을 옮겨도 통과한다(Codex V2 5회차 지적).
WANT_PREFIX="bash scripts/verify/run-acceptance.sh scripts/"
wiring_verdict() {
  printf '%s\n' "$STEPS" | awk -F'\t' -v want="$WANT_PREFIX$1" -v nm="$2" '
    NF && index($2, nm) > 0 { hits++; run = $3; cnt = $4 + 0; weak = $5 }
    END {
      if (hits == 0) { print "없음"; exit }
      if (hits > 1)  { print "이름중복"; exit }
      if (run != want) { print "명령다름"; exit }
      if (cnt > 1) { print "키중복"; exit }
      if (weak != "") { print "약화"; exit }
      print "OK"
    }
  '
}
if [ -n "$STEPS_ERR" ]; then
  failc "CI 배선 불량 — 워크플로를 정규 형식으로 읽지 못했다"
elif [ -n "$STEPS" ]; then
  w_self=$(wiring_verdict 'acceptance-hs-kickoff.sh' 'hs-kickoff (')
  w_mut=$(wiring_verdict 'acceptance-hs-kickoff-mutations.sh' 'hs-kickoff-mutations')
  if [ "$w_self" = "OK" ] && [ "$w_mut" = "OK" ]; then
    pass "CI 배선 2건 — 이름과 명령이 같은 스텝에서 일치하고 조건·오류무시 없음"
  else
    failc "CI 배선 불량 — 본 검사=$w_self 자기 변이=$w_mut"
  fi
else
  failc "CI 배선 불량 — 워크플로 스텝이 비었다"
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
