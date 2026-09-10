#!/usr/bin/env bash
# acceptance-hs-1300-mutations.sh — acceptance-hs-1300.sh 가 고장 난 스펙을 실제로 잡는가 (자기 변이 3종)
#
# 계약: docs/engineering/humansearch-hs13-position-brief-goal-2026-09-10.md §9 HS-13.00 · P13⑥
#   변이 ⓐ 문서 부재            → 검사가 exit 1
#   변이 ⓑ WU 카드 1행 삭제      → 검사가 exit 1
#   변이 ⓒ §4 catch-all 행 삭제  → 검사가 exit 1
#   변이 ⓓ WU 카드 셀 전부 비움     → 검사가 exit 1  (2026-09-10 Codex V1 높음 — 이전 검사기는 통과시켰다)
#   변이 ⓔ D 결정 기본값 셀 비움    → 검사가 exit 1  (같은 지적)
#   변이 ⓕ 제목·토큰만 남긴 최소 문서 → 검사가 exit 1  (같은 지적)
#   대조군: 원본 문서            → 검사가 exit 0 (항상-거부 검사기를 잡는다)
#   출력: PASS:/FAIL: + `CHECKED: 7`, exit 0/1/2
# 쓰기 규칙: 저장소에 아무 파일도 만들지 않는다. 고장 사본은 mktemp 디렉터리에만 쓴다.
set -uo pipefail

unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE GIT_OBJECT_DIRECTORY \
      GIT_ALTERNATE_OBJECT_DIRECTORIES GIT_COMMON_DIR GIT_PREFIX GIT_QUARANTINE_PATH

REPO=$(git rev-parse --show-toplevel 2>/dev/null) || { echo "NOT_RUN: git 저장소가 아니다"; echo "CHECKED: 0"; exit 2; }
cd "$REPO" || { echo "NOT_RUN: 저장소 루트로 이동 실패"; echo "CHECKED: 0"; exit 2; }

CHECKER=scripts/acceptance-hs-1300.sh
ORIG=docs/engineering/humansearch-hs13-position-brief-goal-2026-09-10.md
EXPECTED_CHECKED=7
G=/usr/bin/grep

[ -s "$ORIG" ] || { echo "NOT_RUN: 원본 문서 없음 — $ORIG"; echo "CHECKED: 0"; exit 2; }
TMP=$(mktemp -d) || { echo "NOT_RUN: mktemp 실패"; echo "CHECKED: 0"; exit 2; }
trap 'rm -rf "$TMP"' EXIT

fail=0
checked=0

expect_rc() {
  local desc="$1" doc="$2" want="$3" rc=0
  checked=$((checked + 1))
  HS_1300_DOC="$doc" bash "$CHECKER" >/dev/null 2>&1
  rc=$?
  if [ "$rc" -eq "$want" ]; then
    printf 'PASS: %s (exit=%s)\n' "$desc" "$rc"
  else
    printf 'FAIL: %s (기대 exit=%s, 실제 %s)\n' "$desc" "$want" "$rc"
    fail=1
  fi
}

# 대조군 — 원본은 통과해야 한다 (항상-거부 검사기 차단)
expect_rc "대조군: 원본 문서 → 통과" "$ORIG" 0

# ⓐ 문서 부재
expect_rc "변이ⓐ 문서 부재 → 불합격" "$TMP/absent.md" 1

# ⓑ WU 카드 1행(HS-13.06) 삭제
$G -v '^| HS-13.06 ' "$ORIG" > "$TMP/no-wu.md"
if $G -q '^| HS-13.06 ' "$TMP/no-wu.md"; then echo "NOT_RUN: 변이ⓑ 생성 실패"; echo "CHECKED: $checked"; exit 2; fi
expect_rc "변이ⓑ WU 카드 HS-13.06 삭제 → 불합격" "$TMP/no-wu.md" 1

# ⓒ §4 catch-all 행 삭제 (§8 의 '그 외 전부' 는 남긴다 — 검사기가 절을 구분하는지 본다)
awk '
  /^## 4\. 입력 영역 표/ { in4=1 }
  /^## 5\. / { in4=0 }
  in4 && /그 외 전부/ { next }
  { print }
' "$ORIG" > "$TMP/no-catchall.md"
if ! $G -q '그 외 전부' "$TMP/no-catchall.md"; then echo "NOT_RUN: 변이ⓒ 가 §8 까지 지웠다"; echo "CHECKED: $checked"; exit 2; fi
expect_rc "변이ⓒ §4 catch-all 행 삭제 → 불합격" "$TMP/no-catchall.md" 1

# ⓓ WU 카드 행의 ID 만 남기고 나머지 셀을 비운다
sed -E 's/^\| *(HS-13\.[0-9]{2}[a-z]?) *\|.*$/| \1 | | | | |/' "$ORIG" > "$TMP/wu-empty.md"
if ! $G -Eq '^\| HS-13\.06 \| \| \| \| \|$' "$TMP/wu-empty.md"; then echo "NOT_RUN: 변이ⓓ 생성 실패"; echo "CHECKED: $checked"; exit 2; fi
expect_rc "변이ⓓ WU 카드 셀 전부 비움 → 불합격" "$TMP/wu-empty.md" 1

# ⓔ D 결정 행의 기본값 셀을 비운다
sed -E 's/^\| *(D[0-9]) *\|([^|]*)\|[^|]*\|/| \1 |\2| |/' "$ORIG" > "$TMP/d-empty.md"
if $G -E '^\| *D2 *\|' "$TMP/d-empty.md" | $G -q 'sangmokang'; then echo "NOT_RUN: 변이ⓔ 생성 실패"; echo "CHECKED: $checked"; exit 2; fi
expect_rc "변이ⓔ D 결정 기본값 셀 비움 → 불합격" "$TMP/d-empty.md" 1

# ⓕ 절 제목·catch-all 문구·ID·타입 토큰만 남긴 최소 문서
{
  echo '## 2. 사장님 지시'; for i in 1 2 3 4 5 6 7 8 9; do echo "| $i | | | |"; done
  echo '## 4. 입력 영역 표'; echo '| 그 외 전부 | 명시적 거부 |'
  echo '## 5. 계약'; echo '```python'
  for t in BriefInputError SourceRef Claim PositionSpec JdSource CompanyBrief EmailContact CandidateEvidence ScoreBreakdown CandidateLead JdPacket SearchPacket; do echo "class $t: ..."; done
  echo '```'
  echo '## 7. 결정 목록'; for d in 1 2 3 4 5 6 7 8 9; do echo "| D$d | | | |"; done
  echo '## 8. 예외 표'; echo '| 그 외 전부 | 명시적 중단 |'
  echo '## 9. Issue HS-13'; for n in 00 01 01b 02 03 04 05 06 07 08 09 10 11 12; do echo "| HS-13.$n | | | | |"; done
  echo '## 적대 검증 로그'
} > "$TMP/minimal.md"
expect_rc "변이ⓕ 제목·토큰만 남긴 최소 문서 → 불합격" "$TMP/minimal.md" 1

echo "CHECKED: $checked"
if [ "$checked" -ne "$EXPECTED_CHECKED" ]; then
  echo "FAIL: CHECKED $checked ≠ 기대 $EXPECTED_CHECKED"
  exit 1
fi
exit "$fail"
