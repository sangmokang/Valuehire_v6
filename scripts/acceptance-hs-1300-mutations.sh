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
#   변이 ⓖ catch-all 부정어 반전     → 검사가 exit 1  (2026-09-10 Codeaudit D-2)
#   변이 ⓗ 모든 WU 명령을 가짜 경로로 → 검사가 exit 1  (2026-09-10 Codex 2차)
#   변이 ⓘ D 기본값을 숫자 10자로     → 검사가 exit 1  (같은 지적)
#   변이 ⓙ 정상/반례 셀을 x 로       → 검사가 exit 1  (같은 지적)
#   대조군: 원본 문서            → 검사가 exit 0 (항상-거부 검사기를 잡는다)
#   변이 ⓚ id 접미 위장 파일명 · ⓛ '양성:없음 음성:없음' · ⓜ D값 '가123456789' · ⓝ IMPLEMENTED(x)+가짜 파일 → 각 exit 1 (Codex 3차)
#   변이 ⓞ .py.bak 경계 · ⓟ 가짜 브랜치 · ⓠ position_count 삭제 · ⓡ test_hs_1302b 참조 삭제 · ⓢ '통과통과…' 반복 · ⓣ D값 같은 단어 반복 (Codex 4차)
#   출력: PASS:/FAIL: + `CHECKED: 21`, exit 0/1/2
# 쓰기 규칙: 저장소에 아무 파일도 만들지 않는다. 고장 사본은 mktemp 디렉터리에만 쓴다.
set -uo pipefail

unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE GIT_OBJECT_DIRECTORY \
      GIT_ALTERNATE_OBJECT_DIRECTORIES GIT_COMMON_DIR GIT_PREFIX GIT_QUARANTINE_PATH

REPO=$(git rev-parse --show-toplevel 2>/dev/null) || { echo "NOT_RUN: git 저장소가 아니다"; echo "CHECKED: 0"; exit 2; }
cd "$REPO" || { echo "NOT_RUN: 저장소 루트로 이동 실패"; echo "CHECKED: 0"; exit 2; }

CHECKER=scripts/acceptance-hs-1300.sh
ORIG=docs/engineering/humansearch-hs13-position-brief-goal-2026-09-10.md
EXPECTED_CHECKED=21
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

# ⓖ §4 catch-all 행의 의미를 정반대로("명시적 거부 안 함")
sed -E 's/\*\*명시적 거부\(`BriefInputError`\)\*\*/전부 그대로 통과시킨다. 명시적 거부 안 함/' "$ORIG" > "$TMP/negated.md"
if ! $G -q '명시적 거부 안 함' "$TMP/negated.md"; then echo "NOT_RUN: 변이ⓖ 생성 실패"; echo "CHECKED: $checked"; exit 2; fi
expect_rc "변이ⓖ §4 catch-all 부정어 반전 → 불합격" "$TMP/negated.md" 1

# ⓗ 모든 WU 명령 셀을 형식만 맞는 가짜 경로로 (Codex 2차 반례 그대로)
awk -F'|' 'BEGIN{OFS="|"} /^\| *HS-13\./ { $4=" `bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-1399-fake.sh` (exit 0) " } { print }' "$ORIG" > "$TMP/fake-cmd.md"
if ! $G -q 'hs-1399-fake' "$TMP/fake-cmd.md"; then echo "NOT_RUN: 변이ⓗ 생성 실패"; echo "CHECKED: $checked"; exit 2; fi
expect_rc "변이ⓗ WU 명령 전부 가짜 경로 → 불합격" "$TMP/fake-cmd.md" 1

# ⓘ D 결정 기본값 셀을 숫자 10자로
awk -F'|' 'BEGIN{OFS="|"} /^\| *D[0-9]+ *\|/ { $4=" 1234567890 " } { print }' "$ORIG" > "$TMP/d-digits.md"
if ! $G -q '1234567890' "$TMP/d-digits.md"; then echo "NOT_RUN: 변이ⓘ 생성 실패"; echo "CHECKED: $checked"; exit 2; fi
expect_rc "변이ⓘ D 기본값 숫자 10자 → 불합격" "$TMP/d-digits.md" 1

# ⓙ 정상/반례 셀을 x 로
awk -F'|' 'BEGIN{OFS="|"} /^\| *HS-13\./ { $5=" x " } { print }' "$ORIG" > "$TMP/x-cell.md"
if $G -E '^\| *HS-13\.06' "$TMP/x-cell.md" | $G -q '양성'; then echo "NOT_RUN: 변이ⓙ 생성 실패"; echo "CHECKED: $checked"; exit 2; fi
expect_rc "변이ⓙ 정상/반례 셀 x → 불합격" "$TMP/x-cell.md" 1

# ⓚ~ⓝ Codex 3차 반례 그대로
awk -F'|' 'BEGIN{OFS="|"} /^\| *HS-13\.05 /{ $4=" `cd humansearch && uv run --no-sync pytest -q tests/test_hs_1305_zzz.py` " } { print }' "$ORIG" > "$TMP/zzz.md"
$G -q 'test_hs_1305_zzz' "$TMP/zzz.md" || { echo "NOT_RUN: 변이ⓚ 생성 실패"; echo "CHECKED: $checked"; exit 2; }
expect_rc "변이ⓚ id 접미 위장 파일명 → 불합격" "$TMP/zzz.md" 1
awk -F'|' 'BEGIN{OFS="|"} /^\| *HS-13\.05 /{ $5=" 양성:없음 음성:없음 " } { print }' "$ORIG" > "$TMP/none.md"
$G -q '양성:없음' "$TMP/none.md" || { echo "NOT_RUN: 변이ⓛ 생성 실패"; echo "CHECKED: $checked"; exit 2; }
expect_rc "변이ⓛ '양성:없음 음성:없음' → 불합격" "$TMP/none.md" 1
awk -F'|' 'BEGIN{OFS="|"} /^\| *D[0-9]+ *\|/{ $4=" 가123456789 " } { print }' "$ORIG" > "$TMP/d-ga.md"
$G -q '가123456789' "$TMP/d-ga.md" || { echo "NOT_RUN: 변이ⓜ 생성 실패"; echo "CHECKED: $checked"; exit 2; }
expect_rc "변이ⓜ D값 '가123456789' → 불합격" "$TMP/d-ga.md" 1
awk -F'|' 'BEGIN{OFS="|"} /^\| *HS-13\.05 /{ $4=" `cd humansearch && uv run --no-sync pytest -q tests/test_hs_1305.py` "; $6=" IMPLEMENTED(x) " } { print }' "$ORIG" > "$TMP/impl-x.md"
$G -q 'IMPLEMENTED(x)' "$TMP/impl-x.md" || { echo "NOT_RUN: 변이ⓝ 생성 실패"; echo "CHECKED: $checked"; exit 2; }
expect_rc "변이ⓝ IMPLEMENTED(x) 괄호 회피 + 미실존 파일 → 불합격" "$TMP/impl-x.md" 1

# ⓞ~ⓣ Codex 4차 반례
awk -F'|' 'BEGIN{OFS="|"} /^\| *HS-13\.05 /{ $4=" `cd humansearch && uv run --no-sync pytest -q tests/test_hs_1305.py.bak` " } { print }' "$ORIG" > "$TMP/bak.md"
$G -q 'test_hs_1305.py.bak' "$TMP/bak.md" || { echo "NOT_RUN: 변이ⓞ 생성 실패"; echo "CHECKED: $checked"; exit 2; }
expect_rc "변이ⓞ tests/test_hs_1305.py.bak 경계 위장 → 불합격" "$TMP/bak.md" 1
awk -F'|' 'BEGIN{OFS="|"} /^\| *HS-13\.05 /{ $6=" LOCAL_COMMITTED(task/fake-branch-does-not-exist) " } { print }' "$ORIG" > "$TMP/fake-branch.md"
$G -q 'fake-branch-does-not-exist' "$TMP/fake-branch.md" || { echo "NOT_RUN: 변이ⓟ 생성 실패"; echo "CHECKED: $checked"; exit 2; }
expect_rc "변이ⓟ LOCAL_COMMITTED(가짜 브랜치) → 불합격" "$TMP/fake-branch.md" 1
$G -v 'position_count: int' "$ORIG" > "$TMP/no-poscount.md"
expect_rc "변이ⓠ position_count 계약 삭제 → 불합격" "$TMP/no-poscount.md" 1
sed -E '/^\| *HS-13\.02 /s# tests/test_hs_1302b\.py##' "$ORIG" > "$TMP/no-1302b.md"
if $G -E '^\| *HS-13\.02 ' "$TMP/no-1302b.md" | $G -q 'tests/test_hs_1302b.py'; then echo "NOT_RUN: 변이ⓡ 생성 실패"; echo "CHECKED: $checked"; exit 2; fi
expect_rc "변이ⓡ 13.02 행의 test_hs_1302b 참조 삭제 → 불합격" "$TMP/no-1302b.md" 1
awk -F'|' 'BEGIN{OFS="|"} /^\| *HS-13\.05 /{ $5=" 양성:통과통과통과통과통과 음성:실패실패실패실패실패 " } { print }' "$ORIG" > "$TMP/repeat.md"
$G -q '통과통과통과' "$TMP/repeat.md" || { echo "NOT_RUN: 변이ⓢ 생성 실패"; echo "CHECKED: $checked"; exit 2; }
expect_rc "변이ⓢ 양성/음성 무의미 반복 → 불합격" "$TMP/repeat.md" 1
awk -F'|' 'BEGIN{OFS="|"} /^\| *D1 *\|/{ $4=" 무관단어반복 무관단어반복 " } { print }' "$ORIG" > "$TMP/d-repeat.md"
$G -q '무관단어반복 무관단어반복' "$TMP/d-repeat.md" || { echo "NOT_RUN: 변이ⓣ 생성 실패"; echo "CHECKED: $checked"; exit 2; }
expect_rc "변이ⓣ D값 같은 단어 반복 → 불합격" "$TMP/d-repeat.md" 1

echo "CHECKED: $checked"
if [ "$checked" -ne "$EXPECTED_CHECKED" ]; then
  echo "FAIL: CHECKED $checked ≠ 기대 $EXPECTED_CHECKED"
  exit 1
fi
exit "$fail"
