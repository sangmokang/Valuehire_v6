#!/usr/bin/env bash
# check-workflow-deletion.sh — CI 워크플로에서 검사 실행 줄을 지우는 약화를 잡는다.
#
# 왜 필요한가 (억제 p13-deletion-blindspot):
#   hooks/pre-commit 의 scan_added() 는 diff 의 추가된 줄(+)만 본다. 삭제로 인한 약화는
#   원리적으로 보이지 않았다. check-ci-step-integrity.sh 는 "스텝 삭제는 막지 못한다"고
#   자기 계약에 명시했고, hooks/pre-push 의 실행줄 검사는 DEFERRED 와 PUSH-PERFORMING
#   선언 스크립트만 대조한다. 그 사이에 나머지 인수 스크립트 전부가 무방비로 있었다.
#
# 왜 .github/workflows/* 로만 범위를 잡나:
#   삭제 diff 검사를 전면 도입하면 리팩터링마다 오탐이 난다. 워크플로 파일에서
#   스크립트 실행 줄의 삭제는 거의 항상 약화라서, 이 범위는 오탐이 거의 없다.
#   (억제 원장 issue 필드 · V1 합의)
#
# 판정: 삭제된 실행 줄에서 스크립트 경로를 뽑아(D), 커밋 후 워크플로 본문의 실행 줄에서
#       같은 경로를 뽑아(A) 비교한다. D - A 중 **저장소에 아직 존재하는** 스크립트가
#       하나라도 있으면 차단이다.
#       · 스텝 이동·이름 변경·줄 재배치는 경로가 A 에 그대로 남으므로 통과한다.
#       · 스크립트 자체를 지우는 정당한 제거는 파일이 없으므로 통과한다.
#
# 계약: exit 0 (약화 없음) | exit 1 (약화 발견) | exit 2 (검사 실행 불가 · fail-closed)
#       출력은 경로와 사유만 낸다.
#
# fail-open 금지 규칙: 입출력 준비 실패를 명령의 "결과 없음"과 섞지 않는다.
#   bash 는 리다이렉션이 실패하면 명령을 실행하지 않고 종료값 1 을 준다. 그런데 grep 의 1 은
#   "매치 없음"이라 두 의미가 겹쳐, 디스크 만재·임시 디렉터리 소실에서 조용한 초록이 난다
#   (2026-09-05 v6 에서 같은 모양이 3군데). 그래서 출력 파일을 먼저 확보하고 명령을 돌린다.
set -uo pipefail

BLOCK_MARK='워크플로 검사 실행 줄 삭제'
WF_PREFIX='.github/workflows/'

die_setup() { printf 'FAIL: %s (fail-closed)\n' "$1"; echo "CHECKED: 0"; exit 2; }

command -v git >/dev/null 2>&1 || die_setup "git 을 찾을 수 없다"
REPO=$(git rev-parse --show-toplevel 2>/dev/null) || die_setup "git 저장소가 아니다"
cd "$REPO" || die_setup "저장소 루트로 이동할 수 없다"

TMP=$(mktemp -d) || die_setup "임시 디렉터리를 만들 수 없다 — 검사 결과를 모을 곳이 없다"
trap 'rm -rf "$TMP"' EXIT

# 출력 파일을 먼저 확보한다. 여기서 실패하면 검사 실패지 "약화 없음"이 아니다.
: > "$TMP/files"  || die_setup "작업 파일을 열 수 없다 ($TMP/files)"
: > "$TMP/del"    || die_setup "작업 파일을 열 수 없다 ($TMP/del)"
: > "$TMP/keep"   || die_setup "작업 파일을 열 수 없다 ($TMP/keep)"
: > "$TMP/hits"   || die_setup "작업 파일을 열 수 없다 ($TMP/hits)"

# 스테이징된 워크플로 파일 (수정·삭제 모두. 삭제는 D 로 잡힌다)
if ! git diff --cached --name-only --diff-filter=MD -z > "$TMP/files.z" 2>"$TMP/err"; then
  die_setup "스테이징 목록을 읽지 못했다 — $(head -1 "$TMP/err")"
fi
tr '\0' '\n' < "$TMP/files.z" | grep "^${WF_PREFIX}" > "$TMP/files"
grc=$?
if [ "$grc" -gt 1 ]; then
  die_setup "스테이징 목록 필터 실행 오류 (grep exit=$grc)"
fi

checked=0
violation=0

# 실행 줄에서 스크립트 경로를 뽑는다. 주석 줄(# 로 시작)은 제외한다 —
# 워크플로 주석에는 스크립트 이름이 설명으로 자주 등장하고, 주석을 지우는 것은 약화가 아니다.
extract_paths() {  # stdin: 워크플로 줄들 → stdout: 스크립트 경로 (정렬·중복제거)
  sed -e 's/^[+-]//' \
    | grep -v '^[[:space:]]*#' \
    | grep -oE '[A-Za-z0-9_][A-Za-z0-9_./-]*\.sh' \
    | LC_ALL=C sort -u
}

while IFS= read -r wf; do
  [ -z "$wf" ] && continue
  checked=$((checked + 1))

  # 삭제된 줄(-) 에서 뽑은 경로
  if ! git diff --cached -U0 -- "$wf" > "$TMP/diff" 2>"$TMP/err"; then
    die_setup "diff 를 읽지 못했다 ($wf) — $(head -1 "$TMP/err")"
  fi
  grep '^-' "$TMP/diff" | grep -v '^---' | extract_paths > "$TMP/del"

  # 커밋될 본문(인덱스) 의 실행 줄에서 뽑은 경로. 파일이 통째로 삭제되면 빈 집합이다.
  if git ls-files --error-unmatch -- "$wf" >/dev/null 2>&1; then
    git show ":$wf" 2>/dev/null | extract_paths > "$TMP/keep"
  else
    : > "$TMP/keep"
  fi

  # D - A
  comm -23 "$TMP/del" "$TMP/keep" > "$TMP/gone" || die_setup "집합 비교 실패 ($wf)"

  while IFS= read -r p; do
    [ -z "$p" ] && continue
    # 스크립트 자체가 저장소에서 사라졌으면 정당한 제거다 (같은 커밋의 삭제 포함).
    if git ls-files --error-unmatch -- "$p" >/dev/null 2>&1; then
      printf '%s\t%s\n' "$wf" "$p" >> "$TMP/hits" || die_setup "결과 기록 실패"
      violation=1
    fi
  done < "$TMP/gone"
done < "$TMP/files"

if [ "$violation" -ne 0 ]; then
  while IFS=$'\t' read -r wf p; do
    printf 'BLOCKED: %s — %s 의 실행 줄에서 %s 가 사라졌다.\n' "$BLOCK_MARK" "$wf" "$p"
    printf '         스크립트는 저장소에 그대로 있는데 CI 가 더 이상 부르지 않는다.\n'
    printf '         정당하면 스크립트도 함께 지우거나 suppressions.yaml 에 expiry 와 함께 등록하라.\n'
  done < "$TMP/hits"
  echo "CHECKED: $checked"
  exit 1
fi

printf 'PASS: 워크플로 검사 실행 줄 삭제 없음\n'
echo "CHECKED: $checked"
exit 0
