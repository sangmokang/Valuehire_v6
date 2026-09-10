#!/usr/bin/env bash
# acceptance-hs-1300.sh — HS-13.00: 포지션 브리프·서치 패킷 스펙이 구현 지시서의 필수 구조를 갖췄는가
#
# 계약: docs/engineering/humansearch-hs13-position-brief-goal-2026-09-10.md §9 HS-13.00
#   출력 : 항목마다 PASS:/FAIL: 전부 출력, 마지막 줄 `CHECKED: <검사 수>`
#   exit : 0 = PASS | 1 = FAIL | 2 = NOT_RUN
#   불변식: CHECKED 는 정확히 EXPECTED_CHECKED 여야 한다 — 검사가 사라져도 초록이면 가짜다(P20)
#
# 무엇을 판정하나 (문서 WU 라서 "구조가 지시서 자격을 갖췄는가"만 본다 — 내용의 적합성은 보증하지 않는다):
#   1  문서 실존·비어있지 않음
#   2  §4 입력 영역 표의 catch-all 행("그 외 전부" + "명시적 거부")
#   3  §7 결정 목록 D1~D8 전부 존재 (8건 각각 1검사)
#   11 §8 예외 표의 catch-all 행("그 외 전부" + "명시적 중단")
#   12 §9 WU 카드 14건(HS-13.00~12 + 01b) 각각: 행 존재 + 5셀 전부 비어있지 않음 + 명령 셀이 실행 형식
#      (`cd humansearch && uv run --no-sync pytest|python -m humansearch.brief` 또는 `bash scripts/verify/run-acceptance.sh`) + 상태 셀이 허용값
#   26 §7 결정 D1~D9 각각 기본값 셀 10자 이상 (9건) — 위 3~10 의 "행 존재"와 별개 검사
#   35 §5 계약의 공개 타입 이름 12개가 코드 펜스 안에 존재 (각각 1검사)
#   47 "## 적대 검증 로그" 절 존재
#   48 §2 지시 9단계 검토 표에 9행
#   49 §9 WU 카드 수 == 14 (행 수 정확)
#   50 §7 D9 행 존재 (발송 멱등 — 2026-09-10 Codex V1 편입)
#   51~55 §4 입력 영역 표에 이미지·합본·언어·ClickUp 공백·시계 행 (5건)
#   56~63 §5 계약 함수 8개 펜스 안 존재 · 64 §6·§10 절 실존(record_intent) · 65~66 D10·D11 (Codeaudit 2026-09-10)
#   67 전 행 PLANNED 금지 · 68~70 D9 at-most-once 문구 3개 (Codex 2차 2026-09-10)
#   WU 행 검사(12~25)는 id↔명령 파일명 결합·행동 6자·양성/음성·비PLANNED 참조 파일 실존까지 본다 (Codex 2차)
#
# 2026-09-10 Codex V1: 이전 판은 ID·토큰 존재만 봐서 빈 셀 문서가 통과했다(높음). 위 12·26·35 가 그 반례를 막는다.
#
# HS_1300_DOC 는 자기 변이 검사(acceptance-hs-1300-mutations.sh)가 고장 사본을 먹일 때만 재지정한다.
set -uo pipefail

unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE GIT_OBJECT_DIRECTORY \
      GIT_ALTERNATE_OBJECT_DIRECTORIES GIT_COMMON_DIR GIT_PREFIX GIT_QUARANTINE_PATH

REPO=$(git rev-parse --show-toplevel 2>/dev/null) || { echo "NOT_RUN: git 저장소가 아니다"; echo "CHECKED: 0"; exit 2; }
cd "$REPO" || { echo "NOT_RUN: 저장소 루트로 이동 실패"; echo "CHECKED: 0"; exit 2; }

DOC="${HS_1300_DOC:-docs/engineering/humansearch-hs13-position-brief-goal-2026-09-10.md}"
EXPECTED_CHECKED=70

fail=0
checked=0

pass() { checked=$((checked + 1)); printf 'PASS: %s\n' "$1"; }
failed() { checked=$((checked + 1)); printf 'FAIL: %s\n' "$1"; fail=1; }

# grep 은 ugrep 으로 가려져 있을 수 있다 — 절대경로로 고정한다(2026-08-25 실측).
G=/usr/bin/grep

# 1) 문서 실존
if [ -s "$DOC" ]; then
  pass "문서 실존·비어있지 않음 — $DOC"
else
  failed "문서 없음/빈 파일 — $DOC (기대 동작이 아직 없다)"
  echo "CHECKED: $checked"
  exit 1
fi

# 절 단위로 자르는 도우미: 시작 헤더(정규식)부터 다음 '## ' 헤더 직전까지
section() {
  awk -v start="$1" '
    $0 ~ start { on=1; print; next }
    on && /^## / { exit }
    on { print }
  ' "$DOC"
}

# 2) §4 catch-all — 부정어 반전("명시적 거부 안 함"·"하지 않") 금지 (2026-09-10 Codeaudit D-2)
if section '^## 4\. 입력 영역 표' | $G -E '그 외 전부' | $G '명시적 거부' | $G -Evq '안 ?함|하지 ?않|않는다|금지 ?안'; then
  pass "§4 입력 영역 표 catch-all 행(그 외 전부 → 명시적 거부)"
else
  failed "§4 입력 영역 표에 catch-all 행이 없다"
fi

# 3~10) §7 결정 D1~D8
sec7=$(section '^## 7\. 결정 목록')
for d in D1 D2 D3 D4 D5 D6 D7 D8; do
  if printf '%s\n' "$sec7" | $G -Eq "^\| *$d *\|"; then
    pass "§7 결정 $d 행 존재"
  else
    failed "§7 결정 $d 행 없음"
  fi
done

# 11) §8 catch-all — 부정어 반전 금지
if section '^## 8\. 예외 표' | $G -E '그 외 전부' | $G '명시적 중단' | $G -Evq '안 ?함|하지 ?않|않는다|금지 ?안'; then
  pass "§8 예외 표 catch-all 행(그 외 전부 → 명시적 중단)"
else
  failed "§8 예외 표에 catch-all 행이 없다"
fi

# 12~25) §9 WU 카드 14건 — 행 존재 + 5셀 내용 + 명령 형식 + 상태값
sec9=$(section '^## 9\. Issue HS-13')
# 표의 한 행을 셀 배열로 쪼갠다(선행·후행 '|' 제거). 백틱 안의 '|' 는 표에 쓰지 않는다는 전제.
wu_row_ok() {
  local row="$1" cells n cmd state
  row="${row#|}"; row="${row%|}"
  IFS='|' read -r -a cells <<< "$row"
  n=${#cells[@]}
  [ "$n" -eq 5 ] || return 1
  for c in "${cells[@]}"; do
    [ -n "$(printf '%s' "$c" | tr -d '[:space:]')" ] || return 1
  done
  cmd="${cells[2]}"
  printf '%s' "$cmd" | $G -Eq 'cd humansearch && uv run --no-sync (pytest|python -m humansearch\.brief)|bash scripts/verify/run-acceptance\.sh scripts/acceptance-hs-13[0-9]{2}[a-z]?[-a-z]*\.sh' || return 1
  # 명령이 이 WU 의 id 와 결합돼 있어야 한다 (Codex 2차: 가짜 경로 scripts/acceptance-hs-1399-fake.sh 가 통과했다)
  local id="${cells[0]//[[:space:]]/}"; id="${id#HS-13.}"
  printf '%s' "$cmd" | $G -Eq "tests/test_hs_13${id}(_[a-z]+)?\.py|scripts/acceptance-hs-13${id}(-[a-z]+)*\.sh|python -m humansearch\.brief" || return 1
  # 행동 셀 최소 6자, 정상/반례 셀에 양성·음성 둘 다
  [ "$(printf '%s' "${cells[1]}" | tr -d '[:space:]' | wc -m | tr -d ' ')" -ge 6 ] || return 1
  printf '%s' "${cells[3]}" | $G -q '양성' || return 1
  printf '%s' "${cells[3]}" | $G -q '음성' || return 1
  state="$(printf '%s' "${cells[4]}" | tr -d '[:space:]')"
  printf '%s' "$state" | $G -Eq '^(PLANNED|RED|IMPLEMENTED|AUDITED|LOCAL_COMMITTED|PR_OPEN|VERIFIED|MERGED)(\(.+\))?$|^BLOCKED\(.+\)$' || return 1
  # PLANNED/BLOCKED 가 아니고 다른 브랜치 표기(괄호)도 없으면 참조 파일이 이 저장소에 실존해야 한다
  case "$state" in
    PLANNED|BLOCKED*|*\(*) ;;
    *)
      for f in $(printf '%s' "$cmd" | $G -Eo 'tests/test_hs_13[0-9a-z_]+\.py|scripts/acceptance-hs-13[0-9a-z-]+\.sh'); do
        case "$f" in tests/*) [ -f "humansearch/$f" ] || return 1 ;; *) [ -f "$f" ] || return 1 ;; esac
      done ;;
  esac
  return 0
}
for n in 00 01 01b 02 03 04 05 06 07 08 09 10 11 12; do
  row=$(printf '%s\n' "$sec9" | $G -E "^\| *HS-13\.$n *\|" | head -1)
  if [ -n "$row" ] && wu_row_ok "$row"; then
    pass "§9 WU 카드 HS-13.$n 존재·5셀 내용·명령 형식·상태값"
  else
    failed "§9 WU 카드 HS-13.$n 없음 또는 셀 비어있음/명령 형식·상태값 위반"
  fi
done

# 26~34) §7 D1~D9 기본값 셀 내용(10자 이상)
for d in D1 D2 D3 D4 D5 D6 D7 D8 D9; do
  row=$(printf '%s\n' "$sec7" | $G -E "^\| *$d *\|" | head -1)
  row="${row#|}"; row="${row%|}"
  IFS='|' read -r -a cells <<< "$row"
  val="$(printf '%s' "${cells[2]:-}" | tr -d '[:space:]')"
  distinct=$(printf '%s' "$val" | $G -o . | LC_ALL=C sort -u | wc -l | tr -d ' ')
  if [ "${#val}" -ge 10 ] && [ "$distinct" -ge 3 ] && printf '%s' "$val" | $G -q '[가-힣]'; then
    pass "§7 결정 $d 기본값 셀 내용 있음(${#val}자·문자 ${distinct}종·한글 포함)"
  else
    failed "§7 결정 $d 기본값 셀이 비었거나 10자 미만이거나 무의미(문자 ${distinct}종·한글 없음)"
  fi
done

# 35~46) §5 공개 타입 이름 12개 — 코드 펜스 안에서만 센다
sec5_fenced=$(section '^## 5\. 계약' | awk '/^```/{f=!f; next} f{print}')
for t in BriefInputError SourceRef Claim PositionSpec JdSource CompanyBrief \
         EmailContact CandidateEvidence ScoreBreakdown CandidateLead JdPacket SearchPacket; do
  if printf '%s\n' "$sec5_fenced" | $G -Eq "class $t\b"; then
    pass "§5 타입 $t 선언이 코드 펜스 안에 존재"
  else
    failed "§5 타입 $t 선언이 코드 펜스 안에 없음"
  fi
done

# 47) 적대 검증 로그 절
if $G -Eq '^## 적대 검증 로그' "$DOC"; then
  pass "'## 적대 검증 로그' 절 존재"
else
  failed "'## 적대 검증 로그' 절 없음"
fi

# 48) §2 지시 9단계 검토 표 = 9행 (표 헤더·구분선 제외, 첫 열이 1~9)
rows=$(section '^## 2\. 사장님 지시' | $G -Ec '^\| *[1-9] *\|')
if [ "$rows" -eq 9 ]; then
  pass "§2 지시 9단계 검토 표 9행"
else
  failed "§2 지시 검토 표 행 수 $rows (기대 9)"
fi

# 49) §9 WU 카드 수 정확히 14
wu_rows=$(printf '%s\n' "$sec9" | $G -Ec '^\| *HS-13\.[0-9]{2}[a-z]? *\|')
if [ "$wu_rows" -eq 14 ]; then
  pass "§9 WU 카드 수 14"
else
  failed "§9 WU 카드 수 $wu_rows (기대 14)"
fi

# 67) 전 행 PLANNED 금지 — 착수된 WU 가 최소 1개
if printf '%s\n' "$sec9" | $G -E '^\| *HS-13\.' | $G -Evq '\| *PLANNED *\|$'; then
  pass "§9 PLANNED 가 아닌 WU 카드 1개 이상"
else
  failed "§9 모든 WU 가 PLANNED — 착수 상태를 표시하지 않는 문서"
fi
# 68~70) D9 at-most-once 핵심 문구 3개 (Codex 2차 상충 지적)
sec5_all=$(section '^## 5\. 계약')
for k in 'O_CREAT\|O_EXCL' 'intent 파일이 없을 때만 True' 'def reconcile'; do
  if printf '%s\n' "$sec5_all" | $G -q "$k"; then pass "§5 D9 at-most-once 문구 '$k'"; else failed "§5 D9 문구 '$k' 없음"; fi
done

# 50) D9 발송 멱등 결정 존재
if printf '%s\n' "$sec7" | $G -E '^\| *D9 *\|' | $G -q '멱등'; then
  pass "§7 D9 발송 멱등 결정 존재"
else
  failed "§7 D9 발송 멱등 결정 없음"
fi

# 56~63) §5 계약 함수 8개 + CLI 계약 (Codeaudit 최소 보강 ②)
for f in verify_fidelity check_linkedin split_two_field compose_brief_mail load_recipients score_candidate build_boolean_queries build_inmail; do
  if printf '%s\n' "$sec5_fenced" | $G -Eq "def $f\("; then
    pass "§5 함수 $f 계약 존재"
  else
    failed "§5 함수 $f 계약 없음"
  fi
done
# 64) §6 출력 계약·§10 러너 절차 절 실존 (껍데기 문서 차단)
if $G -Eq '^### 6\. 출력 계약' "$DOC" && $G -Eq '^## 10\. HS-13\.10 러너 절차' "$DOC" && section '^## 10\. HS-13\.10 러너 절차' | $G -q 'record_intent'; then
  pass "§6 출력 계약·§10 러너 절차(D9 record_intent 포함) 실존"
else
  failed "§6 출력 계약 또는 §10 러너 절차(record_intent) 없음"
fi
# 65~66) D10 매력도·D11 어미 축약 결정 (Codeaudit D-3)
for d in D10 D11; do
  if printf '%s\n' "$sec7" | $G -Eq "^\| *$d *\|"; then pass "§7 결정 $d 존재"; else failed "§7 결정 $d 없음"; fi
done

# 51~55) §4 현실 입력 행 5종
sec4=$(section '^## 4\. 입력 영역 표')
for k in '이미지' '합본' '언어' 'ClickUp description' '시계'; do
  if printf '%s\n' "$sec4" | $G -Eq "^\| *[^|]*$k"; then
    pass "§4 입력 행 '$k' 존재"
  else
    failed "§4 입력 행 '$k' 없음"
  fi
done

echo "CHECKED: $checked"
if [ "$checked" -ne "$EXPECTED_CHECKED" ]; then
  echo "FAIL: CHECKED $checked ≠ 기대 $EXPECTED_CHECKED — 검사가 사라지거나 늘었다"
  exit 1
fi
exit "$fail"
