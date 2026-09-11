#!/usr/bin/env bash
# check-secret-detection-regression.sh — 비밀 규칙의 **탐지력이 줄었는지**를 판정한다.
#
# 왜 필요한가 (2026-09-10 Codex 적대검증):
#   P13 약화 탐지는 diff 의 추가된 줄을 일반 약화 리터럴(`|| true` 등) 목록과 대조한다.
#   비밀 규칙 파일에는 그 방식이 원리적으로 통하지 않는다:
#     · 규칙 **삭제**는 추가된 줄이 없어 입력에 들어오지도 않는다
#     · 수량 하한을 {16} → {99} 로 올리는 **수정**은 어떤 약화 리터럴과도 일치하지 않는다
#   실측: `AKIA[0-9A-Z]{16}` 을 지운 커밋이 통과했고, **바로 다음 커밋에서 실제 AWS 키가
#   그대로 통과했다**. 규칙을 정하는 파일은 문법이 아니라 **무엇을 잡는가**로 지켜야 한다.
#
# 판정: 기준(HEAD)의 패턴과 커밋될(인덱스) 패턴으로 카나리를 각각 돌려 **검출 집합을 비교**한다.
#   · 기준에서 잡히던 양성이 인덱스에서 안 잡히면 → 탐지력 축소 → 차단
#   · 음성이 새로 잡히면 → 오탐 증가 → 차단 (게이트가 벽이 되는 것도 약화다)
#   삭제·수정·수량자·문자집합 축소가 형태와 무관하게 한꺼번에 걸린다.
#
# 정당한 축소: 카나리 fixture 에서 해당 양성 줄도 함께 지운다. 그 삭제는 diff 에 남아
#   리뷰에서 보인다 — 이 검사가 막는 것은 **조용한** 축소다.
#
# 계약: exit 0 (탐지력 유지) | exit 1 (축소·오탐 증가) | exit 2 (검사 불가 · fail-closed)
set -uo pipefail

PATTERNS_FILE=.secret-patterns.default
FIX=scripts/verify/fixtures/secret-canaries

die() { printf 'FAIL: %s (fail-closed)\n' "$1"; echo "CHECKED: 0"; exit 2; }

REPO=$(git rev-parse --show-toplevel 2>/dev/null) || die "git 저장소가 아니다"
cd "$REPO" || die "저장소 루트로 이동할 수 없다"

TMP=$(mktemp -d) || die "임시 디렉터리를 만들 수 없다"
trap 'rm -rf "$TMP"' EXIT
for f in base head pos neg pos.raw neg.raw err; do : > "$TMP/$f" || die "작업 파일을 열 수 없다 ($TMP/$f)"; done

# 패턴 정제 — verify.sh:40 과 **글자 그대로 같은 방식**이어야 한다.
# 인라인 주석을 자르면 안 된다. 패턴 자신이 '#' 를 포함하고(끝의 인라인 주석을 허용하는
# 규칙들), 그것을 자르면 문자 클래스가 깨져 grep 이 "brackets not balanced" 로 죽는다.
# 정제 방식이 갈리면 이 검사와 실제 스캔이 다른 규칙 집합을 보게 된다 —
# 판정기가 2벌이 되는 것이고, 이 저장소는 그것으로 이미 한 번 갈렸다(2026-08-07).
# grep 의 종료값 1 은 "남은 줄이 없음"이고, 주석뿐인 파일·빈 파일에서는 **정상 입력**이다.
# 2 이상만 실행 오류다. 둘을 섞으면 빈 규칙 파일이 "읽지 못했다"(exit 2 · 실행 불가)로
# 둔갑해, 규칙을 통째로 비우는 약화가 판정이 아니라 환경 사고로 보고된다(2026-09-11 실측).
clean() {
  local rc=0
  tr -d '\r' | grep -vE '^[[:space:]]*(#|$)' || rc=$?
  if [ "$rc" -gt 1 ]; then return "$rc"; fi
  return 0
}

# 기준: HEAD 의 패턴. 첫 커밋이면 빈 집합(그때는 비교할 기준이 없으므로 통과).
if git rev-parse --verify --quiet HEAD >/dev/null; then
  git show "HEAD:$PATTERNS_FILE" 2>/dev/null | clean > "$TMP/base" || : > "$TMP/base"
fi
# 커밋될 내용: 인덱스. 스테이징에 없으면 HEAD 와 같다.
if git ls-files --error-unmatch -- "$PATTERNS_FILE" >/dev/null 2>&1; then
  git show ":$PATTERNS_FILE" 2>/dev/null | clean > "$TMP/head" || die "인덱스의 패턴 파일을 읽지 못했다"
else
  : > "$TMP/head"
fi

[ -s "$TMP/base" ] || { echo "PASS: 기준 패턴이 없어 비교 대상이 없다 (첫 도입)"; echo "CHECKED: 0"; exit 0; }
if [ ! -s "$TMP/head" ]; then
  printf 'BLOCKED: 비밀 규칙 파일이 통째로 비었거나 사라졌다 — %s\n' "$PATTERNS_FILE"
  printf '         기준에는 규칙 %d개가 있었다.\n' "$(awk 'NF{c++} END{print c+0}' "$TMP/base")"
  echo "CHECKED: 0"; exit 1
fi

# 카나리 조립 — fixture 는 <설명>\t<앞>\t<뒤> 로 쪼개 두었다(파일 자신이 스캔에 걸리지 않게)
#
# 고정물은 **인덱스(커밋될 내용)** 에서 읽는다. 작업트리 파일을 직접 읽으면 다음으로 우회된다:
#   git rm --cached 로 카나리 삭제를 stage → 작업트리 파일은 원래대로 복원 → commit
#   (2026-09-11 실측: staged 유효줄 2 / worktree 유효줄 4 인 상태에서 rc=0 으로 통과했고
#    하한 3건도 함께 무력화됐다. 판정기가 커밋될 내용이 아니라 화면에 열린 파일을 봤다.)
# 패턴 쪽은 이미 `git show :<path>` 로 읽고 있었다 — 고정물만 작업트리를 봤다.
read_indexed() {  # <경로> <출력>
  git ls-files --error-unmatch -- "$1" >/dev/null 2>&1 \
    || die "카나리 고정물이 인덱스에 없다 — $1 (작업트리 직접 읽기는 금지다)"
  # 오류 메시지를 버리지 않는다 — 무엇 때문에 못 읽었는지가 복구의 출발점이다.
  if ! git show ":$1" > "$2" 2>"$TMP/err"; then
    die "인덱스에서 고정물을 읽지 못했다 — $1: $(head -1 "$TMP/err")"
  fi
}
assemble() {  # <고정물 내용 파일> <출력>
  local src="$1" out="$2"
  [ -f "$src" ] || die "카나리 고정물 내용을 읽을 수 없다 — $src"
  : > "$out" || die "작업 파일을 열 수 없다 ($out)"
  local desc a b
  while IFS=$'\t' read -r desc a b; do
    case "${desc:-}" in ''|\#*) continue ;; esac
    [ -n "${a:-}" ] || continue
    printf '%s\t%s%s\n' "$desc" "$a" "${b:-}" >> "$out" || die "카나리 조립 실패"
  done < "$src"
  [ -s "$out" ] || die "카나리가 0건이다 — 검사 대상 0개는 합격이 아니다 ($src)"
}

# 카나리 자체가 조용히 줄면 다음 축소를 감시할 수 없다 — 서서히 무장해제된다.
# 기준(HEAD)의 카나리 건수와 대조하고, 하한도 둔다. 2026-09-11 실측: 시험 중 고정물을
# 복원하지 못해 양성이 4건 → 3건이 되었고, 그 상태에서 수량자 상향이 "탐지력 유지"로
# 통과했다. 검사기가 자기 입력이 줄어든 것을 못 보면 판정 전체가 조용히 무의미해진다.
CANARY_MIN=3
# 하한 위반과 기준 대비 감소는 **판정 실패(exit 1)** 다. 실행 불가(exit 2)와 섞지 않는다 —
# 섞으면 "임시 디렉터리를 못 만들었다"와 "카나리를 지웠다"가 같은 신호가 되고,
# 실행 불가를 차단으로 계수하는 순간 구현 0줄에서도 초록이 난다(counter-AC 5).
shrink_block() {  # <메시지>
  printf 'BLOCKED: 비밀 탐지 카나리가 줄었다 — %s\n' "$1"
  printf '         카나리가 조용히 줄면 다음 축소를 감시할 수 없다. 서서히 무장해제된다.\n'
  printf '         정당한 축소라면 규칙과 카나리를 **함께** 줄여라. 그 삭제는 diff 에 남는다.\n'
  echo "CHECKED: 0"
  exit 1
}
guard_canary_shrink() {  # <fixture 경로> <현재 조립본> <허용 감소분>
  local src="$1" now="$2" allow="$3" base_n now_n drop
  now_n=$(awk 'NF{c++} END{print c+0}' "$now")
  [ "$now_n" -ge "$CANARY_MIN" ] \
    || shrink_block "$src 가 ${now_n}건뿐이다 (하한 ${CANARY_MIN})"
  # 하한만 두면 하한 위에서의 감소가 자유롭다 — 4 → 3 이 실제로 통과했고, 그 상태에서
  # 수량자 상향이 "탐지력 유지"로 넘어갔다. 그래서 기준(HEAD)과도 대조한다.
  # 다만 **규칙을 함께 줄이는 정당한 축소**는 막지 않는다. 허용 감소분은 규칙이 줄어든
  # 수만큼이고(양성), 음성 카나리는 대응하는 규칙이 없으므로 0 이다.
  # 첫 커밋이거나 기준에 고정물이 없는 상태는 **정상**이다. 비교할 기준이 없을 뿐이고,
  # 오류를 삼키는 것이 아니다 — 그 의도가 제어 흐름에 드러나게 쓴다.
  if ! git rev-parse --verify --quiet HEAD >/dev/null; then
    return 0
  fi
  if ! git cat-file -e "HEAD:$src" 2>/dev/null; then
    return 0
  fi
  base_n=$(git show "HEAD:$src" 2>/dev/null | awk 'NF && $0 !~ /^#/ {c++} END{print c+0}')
  drop=$((base_n - now_n))
  if [ "$drop" -gt "$allow" ]; then
    shrink_block "$src 가 기준보다 ${drop}건 줄었다 (${base_n} → ${now_n}) · 규칙 축소로 정당화되는 감소는 ${allow}건뿐이다"
  fi
}
read_indexed "$FIX/positive.txt" "$TMP/pos.raw"
read_indexed "$FIX/negative.txt" "$TMP/neg.raw"
assemble "$TMP/pos.raw" "$TMP/pos"
assemble "$TMP/neg.raw" "$TMP/neg"
# 규칙이 줄어든 만큼은 양성 카나리도 함께 줄일 수 있다(정당한 축소 경로).
rule_drop=$(( $(awk 'NF{c++} END{print c+0}' "$TMP/base") - $(awk 'NF{c++} END{print c+0}' "$TMP/head") ))
[ "$rule_drop" -lt 0 ] && rule_drop=0
guard_canary_shrink "$FIX/positive.txt" "$TMP/pos" "$rule_drop"
guard_canary_shrink "$FIX/negative.txt" "$TMP/neg" 0

# hit <패턴파일> <값> → 0 = 잡힘 / 1 = 안 잡힘 / 2 = 실행오류
hit() {
  local pf="$1" val="$2" rc=0
  printf '%s\n' "$val" | grep -qEi -f "$pf" || rc=$?
  [ "$rc" -gt 1 ] && die "패턴 실행 오류 (grep exit=$rc) — 정규식이 깨졌을 수 있다"
  return "$rc"
}

checked=0; fail=0
lost=""; added=""

while IFS=$'\t' read -r desc val; do
  [ -z "${val:-}" ] && continue
  checked=$((checked + 1))
  if hit "$TMP/base" "$val"; then
    if ! hit "$TMP/head" "$val"; then
      lost="${lost}${desc}"$'\n'; fail=1
    fi
  fi
done < "$TMP/pos"

while IFS=$'\t' read -r desc val; do
  [ -z "${val:-}" ] && continue
  checked=$((checked + 1))
  if ! hit "$TMP/base" "$val"; then
    if hit "$TMP/head" "$val"; then
      added="${added}${desc}"$'\n'; fail=1
    fi
  fi
done < "$TMP/neg"

if [ "$fail" -ne 0 ]; then
  if [ -n "$lost" ]; then
    printf 'BLOCKED: 비밀 탐지력이 줄었다 — 기준에서 잡히던 값이 더 이상 안 잡힌다.\n'
    printf '%s' "$lost" | while IFS= read -r d; do [ -n "$d" ] && printf '         잃음: %s\n' "$d"; done
  fi
  if [ -n "$added" ]; then
    printf 'BLOCKED: 오탐이 늘었다 — 기준에서 안 잡히던 정상 값이 잡힌다.\n'
    printf '%s' "$added" | while IFS= read -r d; do [ -n "$d" ] && printf '         새 오탐: %s\n' "$d"; done
  fi
  printf '         정당한 변경이면 %s/positive.txt 의 해당 줄도 함께 고쳐라.\n' "$FIX"
  printf '         그 삭제는 diff 에 남아 리뷰에서 보인다 — 막는 것은 조용한 축소다.\n'
  echo "CHECKED: $checked"
  exit 1
fi

printf 'PASS: 비밀 탐지 집합 유지 (양성 %s건 · 음성 %s건)\n' \
  "$(awk 'NF{c++} END{print c+0}' "$TMP/pos")" "$(awk 'NF{c++} END{print c+0}' "$TMP/neg")"
echo "CHECKED: $checked"
exit 0
