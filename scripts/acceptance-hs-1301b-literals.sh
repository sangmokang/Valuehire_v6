#!/usr/bin/env bash
# acceptance-hs-1301b-literals.sh — 브리프 운영 상수가 코드에 다시 적혔는가 (P22)
#
# 계약: docs/engineering/humansearch-hs13-position-brief-goal-2026-09-10.md §5·§7 D3·D4
#       계약 파일: contracts/humansearch/brief-policy.json
#   출력 : 항목마다 PASS:/FAIL: 전부 출력, 마지막 줄 `CHECKED: <검사 수>`
#   exit : 0 = PASS | 1 = FAIL | 2 = NOT_RUN
#   불변식: CHECKED 는 정확히 EXPECTED_CHECKED 여야 한다 — 검사가 사라져도 초록이면 가짜다(P20)
#
# 무엇을 판정하나:
#   humansearch/src/humansearch/brief/*.py 에서 (policy.py 제외) 아래 리터럴이 각 0건인가.
#     1  1899 / 1900        — LinkedIn InMail 본문 상한과 그 경계 (한 검사로 묶는다)
#     2  valueconnect.kr    — 팀 메일 도메인
#     3  linkedin.com/in    — 공개 프로필 URL 접두
#     4  [포지션]           — 팀 메일 제목 접두
#     5  901814621569       — ClickUp 포지션 리스트 id
#
# 무엇을 판정하지 못하나 (과장 금지):
#   값이 계약 파일과 **같은지**는 보지 않는다. 그것은 humansearch/tests/test_hs_1301b.py 의
#   몫이다(계약값을 바꾸면 판정이 따라 바뀌는가). 여기서는 "코드에 두 번째 소유자가
#   생겼는가"만 본다. 두 검사가 한 쌍이어야 P22 가 실제로 강제된다.
#
# policy.py 를 제외하는 이유: 계약 파일의 키 이름과 검증 정규식이 사는 유일한 자리다.
#   단, policy.py 안에도 값 리터럴은 없어야 하므로 아래 6) 에서 따로 확인한다.
set -uo pipefail

unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE GIT_OBJECT_DIRECTORY \
      GIT_ALTERNATE_OBJECT_DIRECTORIES GIT_COMMON_DIR GIT_PREFIX GIT_QUARANTINE_PATH

REPO=$(git rev-parse --show-toplevel 2>/dev/null) || {
  echo "NOT_RUN: git 저장소가 아니다"; echo "CHECKED: 0"; exit 2
}
cd "$REPO" || { echo "NOT_RUN: 저장소 루트로 이동 실패"; echo "CHECKED: 0"; exit 2; }

# grep 은 ugrep 으로 가려져 있을 수 있다 — 절대경로로 고정한다(2026-08-25 실측).
G=/usr/bin/grep
[ -x "$G" ] || { echo "NOT_RUN: $G 가 없다"; echo "CHECKED: 0"; exit 2; }

BRIEF_DIR="${HS_1301B_BRIEF_DIR:-humansearch/src/humansearch/brief}"
POLICY="$BRIEF_DIR/policy.py"
EXPECTED_CHECKED=5

if [ ! -d "$BRIEF_DIR" ]; then
  echo "NOT_RUN: 브리프 패키지 디렉터리가 없다 — $BRIEF_DIR"
  echo "CHECKED: 0"
  exit 2
fi
if [ ! -f "$POLICY" ]; then
  echo "FAIL: 계약 로더가 없다 — $POLICY (리터럴을 옮겨 둘 자리가 없다)"
  echo "CHECKED: 0"
  exit 1
fi

# 대상 파일 목록: policy.py 를 뺀 브리프 모듈 전부. 0건이면 통과가 아니라 NOT_RUN(P20).
targets=()
while IFS= read -r f; do
  case "$f" in
    "$POLICY") continue ;;
  esac
  targets+=("$f")
done < <(find "$BRIEF_DIR" -maxdepth 1 -name '*.py' -type f | LC_ALL=C sort)

if [ "${#targets[@]}" -lt 1 ]; then
  echo "NOT_RUN: 검사 대상 .py 가 0개 — 빈 글로브는 '전부 통과'가 되므로 판정하지 않는다"
  echo "CHECKED: 0"
  exit 2
fi

fail=0
checked=0
pass() { checked=$((checked + 1)); printf 'PASS: %s\n' "$1"; }
failed() { checked=$((checked + 1)); printf 'FAIL: %s\n' "$1"; fail=1; }

# 리터럴 1종을 대상 전부에서 센다. 걸린 줄은 그대로 보여준다(어디를 고칠지 알아야 한다).
check_literal() {
  local label="$1" pattern="$2"
  local hits
  hits=$("$G" -nE "$pattern" "${targets[@]}" 2>/dev/null)
  if [ -z "$hits" ]; then
    pass "$label 리터럴 0건 (${#targets[@]}개 파일)"
  else
    failed "$label 리터럴이 코드에 남아 있다 — 계약 파일이 유일한 소유자여야 한다(P22)"
    printf '%s\n' "$hits" | sed 's/^/    /'
  fi
}

check_literal "1899/1900 (InMail 본문 상한·경계)" '1899|1900'
check_literal "valueconnect.kr (팀 메일 도메인)"   'valueconnect\.kr'
check_literal "linkedin.com/in (프로필 URL 접두)"  'linkedin\.com/in'
check_literal "[포지션] (메일 제목 접두)"          '\[포지션\]'
check_literal "901814621569 (ClickUp 리스트 id)"   '901814621569'

# 보조 진단 — policy.py 자신도 값을 들고 있으면 안 된다(폴백 기본값 금지). 계약 파일을
# 못 읽으면 거부해야지, 코드에 적어 둔 값으로 대신하면 안 된다.
# CHECKED 에는 넣지 않는다: 이 WU 카드가 `CHECKED: 5` 를 계약값으로 못박았기 때문이다.
# 대신 조용히 넘어가지 않도록 통과일 때도 한 줄을 남긴다(무출력 = 판정 없음).
policy_hits=$("$G" -nE '1899|1900|valueconnect\.kr|linkedin\.com/in|\[포지션\]|901814621569' \
  "$POLICY" 2>/dev/null)
if [ -z "$policy_hits" ]; then
  printf 'PASS: (보조·CHECKED 제외) %s 에 값 리터럴 0건 — 폴백 기본값 없음\n' "$POLICY"
else
  printf 'FAIL: (보조·CHECKED 제외) %s 안에도 값 리터럴이 있다 — 계약 파일에서만 읽어야 한다\n' "$POLICY"
  printf '%s\n' "$policy_hits" | sed 's/^/    /'
  fail=1
fi

echo "CHECKED: $checked"
if [ "$checked" -ne "$EXPECTED_CHECKED" ]; then
  echo "FAIL: CHECKED $checked ≠ 기대 $EXPECTED_CHECKED — 검사가 사라지거나 늘었다"
  exit 1
fi
exit "$fail"
