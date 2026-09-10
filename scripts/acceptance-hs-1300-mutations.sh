#!/usr/bin/env bash
# acceptance-hs-1300-mutations.sh — acceptance-hs-1300.sh 가 고장 난 스펙을 실제로 잡는가 (자기 변이 3종)
#
# 계약: docs/engineering/humansearch-hs13-position-brief-goal-2026-09-10.md §9 HS-13.00 · P13⑥
#   변이 ⓐ 문서 부재            → 검사가 exit 1
#   변이 ⓑ WU 카드 1행 삭제      → 검사가 exit 1
#   변이 ⓒ §4 catch-all 행 삭제  → 검사가 exit 1
#   대조군: 원본 문서            → 검사가 exit 0 (항상-거부 검사기를 잡는다)
#   출력: PASS:/FAIL: + `CHECKED: 4`, exit 0/1/2
# 쓰기 규칙: 저장소에 아무 파일도 만들지 않는다. 고장 사본은 mktemp 디렉터리에만 쓴다.
set -uo pipefail

unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE GIT_OBJECT_DIRECTORY \
      GIT_ALTERNATE_OBJECT_DIRECTORIES GIT_COMMON_DIR GIT_PREFIX GIT_QUARANTINE_PATH

REPO=$(git rev-parse --show-toplevel 2>/dev/null) || { echo "NOT_RUN: git 저장소가 아니다"; echo "CHECKED: 0"; exit 2; }
cd "$REPO" || { echo "NOT_RUN: 저장소 루트로 이동 실패"; echo "CHECKED: 0"; exit 2; }

CHECKER=scripts/acceptance-hs-1300.sh
ORIG=docs/engineering/humansearch-hs13-position-brief-goal-2026-09-10.md
EXPECTED_CHECKED=4
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

echo "CHECKED: $checked"
if [ "$checked" -ne "$EXPECTED_CHECKED" ]; then
  echo "FAIL: CHECKED $checked ≠ 기대 $EXPECTED_CHECKED"
  exit 1
fi
exit "$fail"
