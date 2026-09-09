#!/usr/bin/env bash
# check-acceptance-markers.sh — CI 가 인수 스크립트를 **실제로 실행했는가**를 마커로 대조한다.
#
# 왜 필요한가 (억제 ci-transfer-guarantee · 만료 2026-09-15):
#   hooks/pre-push 의 CI 이관 보증은 워크플로를 문자열로 파싱한다. 규칙을 하나 막을 때마다
#   우회가 하나씩 늘었고, V1 6차에서 다시 4종이 통과했다:
#     `bash ; echo <path>` · `bash /dev/null <path>` · `bash "" <path>` · `sh /dev/null <path>`
#   넷 다 스크립트를 한 줄도 실행하지 않는다. `if: ${{ false }}` 류 항상-거짓 조건도 남아 있었다.
#
#   그래서 판정 근거를 문자열에서 **실행 흔적**으로 바꾼다. scripts/verify/run-acceptance.sh 가
#   대상의 판정을 확인한 뒤에만 마커를 남기고, 여기서 기대 목록 전량이 마커에 있는지 본다.
#   워크플로를 어떻게 편집하든 래퍼를 거쳐 실행되지 않으면 마커가 없다.
#
# 왜 pre-push 가 아니라 CI 안에서 보나:
#   pre-push 시점에는 이번 커밋의 CI 가 아직 돌지 않았다. 최근 성공 run 을 조회하면 **직전**
#   run 을 보게 되고, 방금 워크플로를 망가뜨린 push 는 직전 run 이 초록이라 통과한다(N-1 지연).
#   같은 run 안에서 검수하면 그 지연이 없다.
#
# 막지 못하는 것: 워크플로를 편집할 수 있는 주체는 마커 생성 줄을 직접 추가해 위조할 수 있다.
#   그 편집은 워크플로 diff 에 남고, check-workflow-deletion.sh(삭제)와 pre-commit 의 P13
#   추가 탐지가 그 쪽을 맡는다. 실행 증명은 위조를 불가능하게 만드는 것이 아니라,
#   **워크플로를 편집하지 않고는 우회할 수 없게** 만드는 것이다. 여기서 다 막는다고 하지 않는다.
#
# 계약: exit 0 (기대 목록 전량 실행됨) | exit 1 (누락·해시 불일치) | exit 2 (검수 불가 · fail-closed)
#   기대 목록: ACCEPTANCE_EXPECT_LIST 파일이 있으면 그것, 없으면 저장소 글로브 − 아래 면제 목록.
set -uo pipefail

die() { printf 'FAIL: %s (fail-closed)\n' "$1"; echo "CHECKED: 0"; exit 2; }

REPO=$(git rev-parse --show-toplevel 2>/dev/null) || die "git 저장소가 아니다"
cd "$REPO" || die "저장소 루트로 이동할 수 없다"

DIR="${ACCEPTANCE_MARKER_DIR:-}"
[ -n "$DIR" ] || die "ACCEPTANCE_MARKER_DIR 이 비어 있다 — 무엇을 대조할지 알 수 없다"
MARKERS="$DIR/markers.tsv"

TMP=$(mktemp -d) || die "임시 디렉터리를 만들 수 없다"
trap 'rm -rf "$TMP"' EXIT
# 출력 파일을 먼저 확보한다. 여기서 실패하면 검수 실패지 "누락 없음"이 아니다.
: > "$TMP/expect" || die "작업 파일을 열 수 없다 ($TMP/expect)"
: > "$TMP/miss"   || die "작업 파일을 열 수 없다 ($TMP/miss)"

# CI 실행 면제 — 이름이 아니라 이유와 함께 적는다. 이유 없이 늘리지 않는다.
#   scripts/acceptance-0-2.sh : 로컬 전용 .secret-patterns 의 실제 리터럴을 기준으로 하는데
#     CI 에는 그 파일이 없고, 기본 패턴으로 대체하면 패턴 파일 자신이 매칭돼 상시 실패한다
#     (실측: CI run 31176518944). CI 에서의 등가물은 히스토리 전량 스캔 스텝이다.
EXEMPT="scripts/acceptance-0-2.sh"

if [ -n "${ACCEPTANCE_EXPECT_LIST:-}" ]; then
  [ -f "$ACCEPTANCE_EXPECT_LIST" ] || die "기대 목록 파일이 없다 — $ACCEPTANCE_EXPECT_LIST"
  sed 's#^\./##' "$ACCEPTANCE_EXPECT_LIST" | grep -v '^[[:space:]]*$' | LC_ALL=C sort -u > "$TMP/expect" \
    || die "기대 목록을 읽지 못했다"
else
  # 생산 경로 — 고정 목록이 아니라 글로브다. 고정 목록이면 새로 추가된 인수 스크립트가
  # 조용히 누락된다(2026-08-07 실측: acceptance-9-9.sh 를 추가해도 "검사 2개 실행"으로 통과).
  find . -maxdepth 2 -name 'acceptance-*.sh' -not -path './worktrees/*' -not -path './.git/*' \
    | sed 's#^\./##' | LC_ALL=C sort -u > "$TMP/found" || die "인수 스크립트를 찾지 못했다"
  if [ ! -s "$TMP/found" ]; then
    die "인수 스크립트가 0개 — 검사 대상 0개는 합격이 아니다"
  fi
  grep -vxF "$EXEMPT" "$TMP/found" > "$TMP/expect"
  grc=$?
  [ "$grc" -gt 1 ] && die "면제 목록 적용 실행 오류 (grep exit=$grc)"
fi

total=$(awk 'NF{c++} END{print c+0}' "$TMP/expect")
[ "$total" -ge 1 ] || die "기대 목록이 비었다 — 대조할 것이 없으면 합격이 아니다"

if [ ! -f "$MARKERS" ]; then
  printf 'FAIL: 실행 마커가 하나도 없다 — %s\n' "$MARKERS"
  printf '      인수 스크립트가 scripts/verify/run-acceptance.sh 를 거쳐 실행되지 않았다.\n'
  printf 'CHECKED: %d\n' "$total"
  exit 1
fi

checked=0
while IFS= read -r want; do
  [ -z "$want" ] && continue
  checked=$((checked + 1))
  if [ ! -f "$want" ]; then
    printf '%s\t저장소에 없음\n' "$want" >> "$TMP/miss" || die "결과 기록 실패"
    continue
  fi
  cur=$(shasum -a 256 "$want" 2>/dev/null | awk '{print $1}')
  [ -n "$cur" ] || die "해시를 계산할 수 없다 — $want"
  # 같은 경로가 여러 sha 로 기록될 수 있다(하위 인수 검사가 자기 샌드박스 사본을 래퍼로
  # 돌리는 경우). 그중 하나라도 **지금 저장소 파일의 해시**와 같으면 실제로 실행된 것이다.
  if awk -F'\t' -v p="$want" -v h="$cur" '$1==p && $2==h {found=1} END{exit found?0:1}' "$MARKERS"; then
    continue
  fi
  if awk -F'\t' -v p="$want" '$1==p {found=1} END{exit found?0:1}' "$MARKERS"; then
    printf '%s\t마커의 해시가 현재 파일과 다르다 (CI 가 다른 내용을 돌렸다)\n' "$want" >> "$TMP/miss" || die "결과 기록 실패"
  else
    printf '%s\t마커 없음 (실행되지 않았다)\n' "$want" >> "$TMP/miss" || die "결과 기록 실패"
  fi
done < "$TMP/expect"

if [ -s "$TMP/miss" ]; then
  while IFS=$'\t' read -r p why; do
    printf 'MISSING: %s — %s\n' "$p" "$why"
  done < "$TMP/miss"
  n=$(awk 'NF{c++} END{print c+0}' "$TMP/miss")
  printf 'FAIL: 기대 %d개 중 %d개가 실행 증명 없이 남았다.\n' "$total" "$n"
  printf '      주석 처리·echo 대체·bash /dev/null·if 조건·본문 삭제 어느 쪽이든,\n'
  printf '      래퍼를 거쳐 실행되지 않으면 마커가 생기지 않는다.\n'
  printf 'CHECKED: %d\n' "$checked"
  exit 1
fi

printf 'PASS: 기대 %d개 전부 실행 증명 있음\n' "$total"
printf 'CHECKED: %d\n' "$checked"
exit 0
