#!/usr/bin/env bash
# session-status.sh — 세션 시작 시 저장소의 현재 상태를 보고한다 (P12 회수).
#
# 왜 필요한가: 긴 세션 중 다른 세션이 커밋을 쌓으면, 세션 시작 시점의 HEAD 를 계속
# 믿고 작업하다가 이미 끝난 일을 다시 하게 된다(2026-08-07 실제 발생).
#
# 계약: docs/engineering/hook-enforcement-goal-2026-08-07.md ⑩
#   출력  : stdout 3줄 + exit 0
#   불변식: git 조회 실패 시 해당 줄에 UNKNOWN 을 출력하고 exit 1 (조용한 성공 금지)
set -uo pipefail

rc=0

head_sha=$(git rev-parse --short HEAD 2>/dev/null) || { head_sha="UNKNOWN"; rc=1; }
origin_sha=$(git rev-parse --short origin/main 2>/dev/null) || { origin_sha="UNKNOWN"; rc=1; }

sync="UNKNOWN"
if [ "$head_sha" != "UNKNOWN" ] && [ "$origin_sha" != "UNKNOWN" ]; then
  ahead=$(git rev-list --count origin/main..HEAD 2>/dev/null) || ahead=""
  behind=$(git rev-list --count HEAD..origin/main 2>/dev/null) || behind=""
  if [ -z "$ahead" ] || [ -z "$behind" ]; then
    sync="UNKNOWN"; rc=1
  elif [ "$ahead" = "0" ] && [ "$behind" = "0" ]; then
    sync="synced"
  else
    sync="ahead ${ahead} / behind ${behind}"
  fi
fi

printf 'HEAD: %s (%s)\n' "$head_sha" "$sync"
printf 'ORIGIN: %s\n' "$origin_sha"

# 미해결 RED — 인수 스크립트 중 실패하는 것의 수
root=$(git rev-parse --show-toplevel 2>/dev/null) || root=""
if [ -z "$root" ]; then
  printf 'RED: UNKNOWN\n'
  exit 1
fi
# 상대 경로로 찾는다 — 절대 경로로 하면 워크트리(.../worktrees/<name>/)에서
# 자기 자신이 제외 패턴에 걸려 검사 0개가 되고, 그것이 "RED 0/0"으로 조용히 통과한다.
cd "$root"
# acceptance-0-7 은 제외한다. clone 6회 + 훅 ON/OFF 대조 12회를 돌아 세션 시작마다
# 실행하기엔 무겁고, 자신이 push 를 시연하므로 훅과 얽힌다. CI 가 매 push 마다 돌린다.
# 조용히 빼지 않고 출력에 명시한다 — 소리 없는 제외는 위반유형 E(검사 skip 전환)다.
EXCLUDED=acceptance-0-7.sh
checks=$(find . -maxdepth 2 \( -name 'verify.sh' -o -name 'acceptance-*.sh' \) \
         -not -name "$EXCLUDED" \
         -not -path './worktrees/*' -not -path './.git/*' | LC_ALL=C sort)
total=$(printf '%s\n' "$checks" | awk 'NF{c++} END{print c+0}')

# 0건은 "깨끗함"이 아니라 "검사기를 못 찾음"이다 (P20 · fail-closed)
if [ "$total" -eq 0 ]; then
  printf 'RED: UNKNOWN (검사 스크립트 0개 — 탐색 실패)\n'
  exit 1
fi

red=0
while IFS= read -r c; do
  if [ -z "$c" ]; then continue; fi
  bash "$c" >/dev/null 2>&1 || red=$((red + 1))
done <<< "$checks"

printf 'RED: %d/%d (%s 제외 — CI 담당)\n' "$red" "$total" "$EXCLUDED"
exit "$rc"
