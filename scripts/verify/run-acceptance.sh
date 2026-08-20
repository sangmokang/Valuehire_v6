#!/usr/bin/env bash
# run-acceptance.sh — 인수 검사가 "실행됐다"가 아니라 "실제로 무언가를 판정했다"를 강제한다.
#
# 왜 필요한가 (2026-08-21):
#   scripts/acceptance-hs-a4.sh 의 본문을 통째로 `exit 0` 으로 바꿔도 CI 는 초록이었다.
#   CI 는 스크립트를 부르고 종료값만 봤기 때문이다. 종료값 0 은 "검사가 통과했다"와
#   "검사가 아무것도 하지 않았다"를 구분하지 못한다.
#
# 계약: 대상 스크립트가 종료값 0 으로 끝났다면, 표준 출력에 자기가 무엇을 판정했는지
#       최소 한 줄(PASS 표식) 남겨야 한다. CHECKED 건수를 내는 스크립트는 그 값이
#       1 이상이어야 한다. 둘 중 하나라도 어기면 이 래퍼가 불합격시킨다.
#
# 막는 것 / 막지 못하는 것:
#   막는다   — 본문 삭제, `exit 0`, `true`, `: # no-op`, 검사 함수 제거, 조용한 조기 종료
#   막지 못함 — `echo "PASS: 검사했습니다"; exit 0` 같은 문구 위조. 그것은 P13 검사 약화
#              탐지(hooks/pre-commit)와 acceptance-0-6 의 몫이다. 여기서 다 막는다고
#              주장하지 않는다.
set -uo pipefail

target="${1:-}"
if [ -z "$target" ]; then
  echo "FAIL: 대상 인수 검사 경로가 없다 — 사용법: $0 <script.sh> [args...]"
  exit 2
fi
if [ ! -f "$target" ]; then
  echo "FAIL: 대상 인수 검사가 없다 — $target"
  exit 2
fi

out=$(mktemp) || {
  echo "FAIL: 임시 출력 파일 생성 실패 — 판정 근거를 모을 수 없다"
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

# 종료값 0 인데 판정 근거가 없다 — 이것이 exit 0 치환이 통과하던 구멍이다.
pass_lines=$(grep -c 'PASS' "$out")
if [ "$pass_lines" -lt 1 ]; then
  echo "FAIL(run-acceptance): $target 이 종료값 0 이지만 판정을 한 건도 내놓지 않았다."
  echo "  실행됐다는 사실은 검사했다는 증거가 아니다 — 본문이 비었거나 조기 종료했을 수 있다."
  exit 1
fi

# CHECKED 관례를 따르는 검사기는 건수 0 도 불합격이다(검사 대상 0개 금지).
if grep -q 'CHECKED:' "$out"; then
  checked=$(grep 'CHECKED:' "$out" | tail -1 | sed 's/.*CHECKED:[[:space:]]*//' | tr -cd '0-9')
  if [ -z "$checked" ] || [ "$checked" -lt 1 ]; then
    echo "FAIL(run-acceptance): $target 의 CHECKED 건수가 ${checked:-없음} — 검사 대상 0개는 합격이 아니다."
    exit 1
  fi
  echo "OK(run-acceptance): $target — 판정 ${pass_lines}건, CHECKED ${checked}"
  exit 0
fi

echo "OK(run-acceptance): $target — 판정 ${pass_lines}건"
