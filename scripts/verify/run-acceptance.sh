#!/usr/bin/env bash
# run-acceptance.sh — 승인된 acceptance identity만 실행한 뒤 종료값을 보존한다.
#
# 왜 필요한가 (2026-08-21):
#   scripts/acceptance-hs-a4.sh 의 본문을 통째로 `exit 0` 으로 바꿔도 CI 는 초록이었다.
#   CI 는 스크립트를 부르고 종료값만 봤기 때문이다. 종료값 0 은 "검사가 통과했다"와
#   "검사가 아무것도 하지 않았다"를 구분하지 못한다.
#
# 계약: 대상 스크립트를 실행하기 전에 repo-relative path와 현재 bytes를 독립 JSON
#       contract에 대조한다. PASS/CHECKED/VERDICT 출력은 표시 자료일 뿐 성공 권한이
#       아니다.
#
# 막는 것 / 막지 못하는 것:
#   막는다   — 본문 삭제, `exit 0`, `true`, `: # no-op`, 출력 위조, 정상 출력 replay,
#              repo 밖/미추적/symlink/hardlink target, contract 0건/감소/중복/모호성
#   막지 못함 — runner·validator·contract·workflow를 함께 약화하는 공격(WU0-D).
set -uo pipefail

target="${1:-}"
if [ -z "$target" ]; then
  echo "FAIL: 대상 인수 검사 경로가 없다 — 사용법: $0 <script.sh> [args...]"
  echo "CHECKED: 0"
  exit 2
fi

integrity_rc=0
ruby scripts/verify/check-acceptance-integrity.rb "$target" || integrity_rc=$?
if [ "$integrity_rc" -ne 0 ]; then
  exit "$integrity_rc"
fi

out=$(mktemp) || {
  echo "FAIL: 임시 출력 파일 생성 실패 — 판정 근거를 모을 수 없다"
  echo "CHECKED: 0"
  exit 2
}
trap 'rm -f "$out"' EXIT

shift
bash "$target" "$@" 2>&1 | tee "$out"
rc=${PIPESTATUS[0]}

if [ "$rc" -ne 0 ]; then
  # 원래 실패는 원래 종료값 그대로 넘긴다. 래퍼가 실패 이유를 바꾸지 않는다.
  echo "FAIL(run-acceptance): $target 종료값 $rc"
  exit "$rc"
fi

echo "OK(run-acceptance): $target — 승인된 identity 실행"
