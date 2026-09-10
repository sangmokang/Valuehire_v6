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
#   12 §9 WU 카드 HS-13.00~HS-13.12 전부 존재 (13건 각각 1검사)
#   25 §5 계약의 공개 타입 이름 12개 존재 (각각 1검사)
#   37 "## 적대 검증 로그" 절 존재
#   38 §2 지시 9단계 검토 표에 9행
#
# HS_1300_DOC 는 자기 변이 검사(acceptance-hs-1300-mutations.sh)가 고장 사본을 먹일 때만 재지정한다.
set -uo pipefail

unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE GIT_OBJECT_DIRECTORY \
      GIT_ALTERNATE_OBJECT_DIRECTORIES GIT_COMMON_DIR GIT_PREFIX GIT_QUARANTINE_PATH

REPO=$(git rev-parse --show-toplevel 2>/dev/null) || { echo "NOT_RUN: git 저장소가 아니다"; echo "CHECKED: 0"; exit 2; }
cd "$REPO" || { echo "NOT_RUN: 저장소 루트로 이동 실패"; echo "CHECKED: 0"; exit 2; }

DOC="${HS_1300_DOC:-docs/engineering/humansearch-hs13-position-brief-goal-2026-09-10.md}"
EXPECTED_CHECKED=38

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

# 2) §4 catch-all
if section '^## 4\. 입력 영역 표' | $G -E '그 외 전부' | $G -q '명시적 거부'; then
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

# 11) §8 catch-all
if section '^## 8\. 예외 표' | $G -E '그 외 전부' | $G -q '명시적 중단'; then
  pass "§8 예외 표 catch-all 행(그 외 전부 → 명시적 중단)"
else
  failed "§8 예외 표에 catch-all 행이 없다"
fi

# 12~24) §9 WU 카드 13건
sec9=$(section '^## 9\. Issue HS-13')
for n in 00 01 02 03 04 05 06 07 08 09 10 11 12; do
  if printf '%s\n' "$sec9" | $G -Eq "^\| *HS-13\.$n *\|"; then
    pass "§9 WU 카드 HS-13.$n 존재"
  else
    failed "§9 WU 카드 HS-13.$n 없음"
  fi
done

# 25~36) §5 공개 타입 이름 12개
sec5=$(section '^## 5\. 계약')
for t in BriefInputError SourceRef Claim PositionSpec JdSource CompanyBrief \
         EmailContact CandidateEvidence ScoreBreakdown CandidateLead JdPacket SearchPacket; do
  if printf '%s\n' "$sec5" | $G -Eq "class $t\b"; then
    pass "§5 타입 $t 선언 존재"
  else
    failed "§5 타입 $t 선언 없음"
  fi
done

# 37) 적대 검증 로그 절
if $G -Eq '^## 적대 검증 로그' "$DOC"; then
  pass "'## 적대 검증 로그' 절 존재"
else
  failed "'## 적대 검증 로그' 절 없음"
fi

# 38) §2 지시 9단계 검토 표 = 9행 (표 헤더·구분선 제외, 첫 열이 1~9)
rows=$(section '^## 2\. 사장님 지시' | $G -Ec '^\| *[1-9] *\|')
if [ "$rows" -eq 9 ]; then
  pass "§2 지시 9단계 검토 표 9행"
else
  failed "§2 지시 검토 표 행 수 $rows (기대 9)"
fi

echo "CHECKED: $checked"
if [ "$checked" -ne "$EXPECTED_CHECKED" ]; then
  echo "FAIL: CHECKED $checked ≠ 기대 $EXPECTED_CHECKED — 검사가 사라지거나 늘었다"
  exit 1
fi
exit "$fail"
