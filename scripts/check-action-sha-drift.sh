#!/usr/bin/env bash
# 서드파티 GitHub Action 참조가 가변 태그(예: @v4)로 되돌아갔는지 검사한다.
# owner/repo@<40자 SHA(대소문자 무관)> 형태만 통과시킨다. 로컬 액션(./path)·
# Docker 액션(docker://...)은 버전 고정 개념이 다르므로 대상에서 제외한다.
# 주석 처리되어 실행되지 않는 `# uses: ...` 줄도 대상에서 제외한다(2026-09-07
# V1 적대검증에서 주석 줄을 실제 참조로 오판하는 반례가 나와 편입).
#
# 대상 디렉터리는 첫 인자로 받는다(기본값: 현재 저장소의 .github/workflows).
# fixture 격리 시험(scripts/check-action-sha-drift.sh <tmpdir>)을 지원하기 위함이다 —
# 실제 저장소를 mutate하지 않고 반례를 재현하려면 별도 디렉터리가 필요하다.
set -u

target="${1:-.github/workflows}"

if [ ! -d "$target" ]; then
  echo "FAIL: 대상 디렉터리 없음: $target"
  exit 2
fi

fail=0
n=0
while IFS= read -r line; do
  n=$((n+1))
  if ! printf '%s' "$line" | grep -qE '@[0-9a-fA-F]{40}$'; then
    echo "FAIL: 가변 참조로 고정되지 않은 액션: $line"
    fail=1
  fi
done < <(
  find "$target" -type f \( -name '*.yml' -o -name '*.yaml' \) -print0 2>/dev/null |
  xargs -0 awk '
    {
      line = $0
      trimmed = line
      sub(/^[[:space:]]+/, "", trimmed)
      if (trimmed ~ /^#/) next
      if (match(line, /uses:[[:space:]]*[^.\/#[:space:]][^[:space:]]*\/[^[:space:]]+@[^[:space:]#]+/)) {
        m = substr(line, RSTART, RLENGTH)
        sub(/^uses:[[:space:]]*/, "", m)
        print m
      }
    }
  '
)

if [ "$n" -eq 0 ]; then
  echo "FAIL: 검사 대상 액션 참조 0건 — 검사 무효(대상 0건은 통과가 아니다)"
  exit 2
fi

[ "$fail" -eq 0 ] && echo "PASS: 액션 참조 ${n}건 전부 SHA로 고정됨"
exit $fail
