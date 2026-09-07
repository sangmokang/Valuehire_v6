#!/usr/bin/env bash
# 억제(suppressions.yaml) 만료일 검사.
# verify.yml(push/PR)과 audit.yml(매일 새벽)이 이 스크립트 하나를 함께 부른다 —
# 판정 로직을 두 곳에 따로 적으면 반드시 갈라진다(scan-data-exposure.sh와 같은 원칙).
# hooks/pre-commit 의 동명 검사는 'staged' 콘텐츠를 보는 별도 구현이라 여기서 합치지 않는다.
set -u

[ -f suppressions.yaml ] || { echo "PASS: 억제 없음"; exit 0; }

today=$(date +%Y-%m-%d); fail=0; n=0
while IFS= read -r e; do
  n=$((n+1))
  if ! printf '%s' "$e" | grep -qE '^[0-9]{4}-(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])$'; then
    echo "FAIL: expiry 형식 오류 '${e}' — 만료를 판정할 수 없는 억제는 무기한 억제다"; fail=1
  elif [ "$e" \< "$today" ]; then
    echo "FAIL: 만료된 억제 (expiry $e < 오늘 $today) — 유예 기한이 지났다"; fail=1
  fi
done < <(awk '/^ *expiry:/{sub(/^ *expiry: */,""); gsub(/["\x27]/,""); print}' suppressions.yaml)

nc=$(awk '/^- *check:/{c++} END{print c+0}' suppressions.yaml)
if [ "$nc" -ne "$n" ]; then
  echo "FAIL: 억제 ${nc}건 중 expiry 가 ${n}건뿐"; fail=1
fi

[ "$fail" -eq 0 ] && echo "PASS: 억제 ${nc}건 전부 유효 기한 내"
exit $fail
