#!/usr/bin/env bash
# check-workflow-deletion.sh — CI 워크플로에서 검사 실행 줄을 잃는 약화를 잡는다.
#
# 왜 필요한가 (억제 p13-deletion-blindspot):
#   hooks/pre-commit 의 scan_added() 는 diff 의 추가된 줄(+)만 본다. 삭제로 인한 약화는
#   원리적으로 보이지 않았다. check-ci-step-integrity.sh 는 "스텝 삭제는 막지 못한다"고
#   자기 계약에 명시했고, hooks/pre-push 의 실행줄 검사는 DEFERRED 와 PUSH-PERFORMING
#   선언 스크립트만 대조한다. 그 사이에 나머지 인수 스크립트 전부가 무방비로 있었다.
#
# 왜 .github/workflows/* 로만 범위를 잡나:
#   삭제 diff 검사를 전면 도입하면 리팩터링마다 오탐이 난다. 워크플로 파일에서 스크립트
#   실행 줄의 소실은 거의 항상 약화라서, 이 범위는 오탐이 거의 없다(억제 원장 · V1 합의).
#
# 판정 — **파일 단위 diff 가 아니라 디렉터리 전체 집합**을 비교한다:
#   BEFORE = HEAD 의 .github/workflows/*.yml|yaml 에서 뽑은 스크립트 실행 경로 집합
#   AFTER  = 커밋될 인덱스의 같은 집합
#   BEFORE − AFTER 중 **저장소에 아직 존재하는** 스크립트가 하나라도 있으면 차단.
#
#   집합 비교라서 다음이 한꺼번에 닫힌다 — 줄 삭제 · 스텝 삭제 · 파일 삭제 ·
#   **파일 이름 변경**(git mv verify.yml verify.yml.bak) · 파일 이동 · 분할.
#   파일별 diff 로 짰던 첫 판은 rename 을 놓쳤다(2026-09-09 감사 실측: `git mv`
#   한 번으로 CI 전 스텝이 사라지는데 커밋이 통과했다). 이 저장소는 2026-08-09 에
#   `git mv notes.txt leak.db` 로 같은 함정을 이미 한 번 맞았고 hooks/pre-commit:23 이
#   그것을 경고하고 있었다 — 새 검사기에서 같은 실수를 반복하지 않도록 방식을 바꾼다.
#
#   · 스텝 이동·이름 변경·줄 재배치 → 경로가 AFTER 에 남으므로 통과
#   · 워크플로 파일 이름을 다른 .yml 로 바꾸는 정당한 정리 → 여전히 워크플로라 AFTER 에 남는다
#   · 스크립트 자체를 함께 지우는 은퇴 → **자동 면제하지 않는다**. suppressions.yaml 에
#     `retire:<경로>` 승인(owner·reason·expiry 필수)이 있어야 통과한다.
#
#     왜 자동 면제를 뺐나 (2026-09-10 Codex 적대검증): 스크립트와 그 워크플로 스텝을 한
#     커밋에 함께 지우면 공격과 정당한 은퇴가 구분되지 않았다. 실측으로 233줄짜리 검사가
#     흔적 없이 사라지는데 커밋이 통과했다. 최종 마커 검수도 **현재 트리**의 글로브로 기대
#     목록을 만들기 때문에 사라진 검사를 요구하지 않는다 — 두 방어선이 같은 맹점을 공유했다.
#     은퇴를 막지는 않는다. 기록을 남기게 할 뿐이다.
#
# 계약: exit 0 (약화 없음) | exit 1 (약화 발견) | exit 2 (검사 실행 불가 · fail-closed)
#
# fail-open 금지 규칙: 입출력 준비 실패를 명령의 "결과 없음"과 섞지 않는다.
#   bash 는 리다이렉션이 실패하면 명령을 실행하지 않고 종료값 1 을 주는데, 그 1 이 grep 의
#   "매치 없음"과 겹쳐 디스크 만재·임시 디렉터리 소실에서 조용한 초록이 난다
#   (2026-09-05 v6 에서 같은 모양이 3군데). 그래서 출력 파일을 먼저 확보하고 명령을 돌린다.
set -uo pipefail

BLOCK_MARK='워크플로 검사 실행 줄 삭제'
WF_DIR='.github/workflows'

die_setup() { printf 'FAIL: %s (fail-closed)\n' "$1"; echo "CHECKED: 0"; exit 2; }

command -v git >/dev/null 2>&1 || die_setup "git 을 찾을 수 없다"
REPO=$(git rev-parse --show-toplevel 2>/dev/null) || die_setup "git 저장소가 아니다"
cd "$REPO" || die_setup "저장소 루트로 이동할 수 없다"

TMP=$(mktemp -d) || die_setup "임시 디렉터리를 만들 수 없다 — 검사 결과를 모을 곳이 없다"
trap 'rm -rf "$TMP"' EXIT

for f in before after gone hits; do
  : > "$TMP/$f" || die_setup "작업 파일을 열 수 없다 ($TMP/$f)"
done

# 실행 줄에서 스크립트 경로를 뽑는다. 주석 줄(# 로 시작)은 제외한다 — 워크플로 주석에는
# 스크립트 이름이 설명으로 자주 등장하고, 주석을 지우는 것은 약화가 아니다.
extract_paths() {
  grep -v '^[[:space:]]*#' \
    | grep -oE '[A-Za-z0-9_][A-Za-z0-9_./-]*\.sh' \
    | LC_ALL=C sort -u
}

# 한 쪽(트리 또는 인덱스)의 워크플로 전체에서 경로 집합을 만든다.
# $1 = "HEAD" 또는 "" (빈 값이면 인덱스)
collect() {
  local rev="$1" out="$2" listing p
  : > "$out" || die_setup "작업 파일을 열 수 없다 ($out)"
  if [ -n "$rev" ]; then
    git rev-parse --verify --quiet "$rev" >/dev/null || return 0   # 첫 커밋: BEFORE 는 빈 집합
    listing=$(git ls-tree -r --name-only "$rev" -- "$WF_DIR" 2>"$TMP/err") \
      || die_setup "워크플로 목록을 읽지 못했다 ($rev) — $(head -1 "$TMP/err")"
  else
    listing=$(git ls-files --cached -- "$WF_DIR" 2>"$TMP/err") \
      || die_setup "인덱스의 워크플로 목록을 읽지 못했다 — $(head -1 "$TMP/err")"
  fi
  while IFS= read -r p; do
    [ -z "$p" ] && continue
    # GitHub Actions 는 .yml/.yaml 만 워크플로로 읽는다. 그 밖 확장자는 실행되지 않으므로
    # 집합에 넣지 않는다 — 이것이 rename 우회(.yml.bak)를 자동으로 잡는 지점이다.
    case "$p" in
      "$WF_DIR"/*.yml|"$WF_DIR"/*.yaml) ;;
      *) continue ;;
    esac
    if [ -n "$rev" ]; then
      git show "$rev:$p" 2>/dev/null | extract_paths >> "$out"
    else
      git show ":$p" 2>/dev/null | extract_paths >> "$out"
    fi
  done <<EOF
$listing
EOF
  LC_ALL=C sort -u -o "$out" "$out" || die_setup "집합 정렬 실패 ($out)"
  return 0
}

collect HEAD "$TMP/before"
collect ""   "$TMP/after"

comm -23 "$TMP/before" "$TMP/after" > "$TMP/gone" || die_setup "집합 비교 실패"

# 은퇴 승인 목록 — suppressions.yaml 의 `check: "retire:<경로>"` 항목.
# 커밋될 내용(인덱스)에서 읽는다. 작업트리에서 읽으면 승인을 스테이징하지 않고도 통과한다.
collect_retire_approvals() {
  : > "$1" || die_setup "작업 파일을 열 수 없다 ($1)"
  git ls-files --error-unmatch -- suppressions.yaml >/dev/null 2>&1 || return 0
  git show :suppressions.yaml 2>/dev/null \
    | sed -n 's/^-[[:space:]]*check:[[:space:]]*["'"'"']\{0,1\}retire:\([^"'"'"']*\)["'"'"']\{0,1\}[[:space:]]*$/\1/p' \
    | LC_ALL=C sort -u > "$1" || die_setup "은퇴 승인 목록을 읽지 못했다"
}
collect_retire_approvals "$TMP/approved"
if false; then
  :
fi

checked=$(awk 'NF{c++} END{print c+0}' "$TMP/before")
violation=0
while IFS= read -r p; do
  [ -z "$p" ] && continue
  if git ls-files --error-unmatch -- "$p" >/dev/null 2>&1; then
    # 스크립트는 남아 있는데 CI 가 더 이상 부르지 않는다 — 언제나 약화다.
    printf '%s\t%s\n' "$p" "still-present" >> "$TMP/hits" || die_setup "결과 기록 실패"
    violation=1
  elif ! grep -qxF "$p" "$TMP/approved"; then
    # 스크립트도 함께 사라졌다 — 은퇴일 수 있으나 승인이 없으면 흔적 없는 제거다.
    printf '%s\t%s\n' "$p" "retired-unapproved" >> "$TMP/hits" || die_setup "결과 기록 실패"
    violation=1
  fi
done < "$TMP/gone"

if [ "$violation" -ne 0 ]; then
  while IFS=$'\t' read -r p why; do
    printf 'BLOCKED: %s — %s 의 실행 줄에서 %s 가 사라졌다.\n' "$BLOCK_MARK" "$WF_DIR" "$p"
    if [ "$why" = "still-present" ]; then
      printf '         스크립트는 저장소에 그대로 있는데 CI 가 더 이상 부르지 않는다.\n'
      printf '         (줄 삭제·스텝 삭제·파일 삭제·워크플로 파일 이름 변경 전부 여기서 걸린다)\n'
    else
      printf '         스크립트도 같은 커밋에서 함께 삭제됐다 — 은퇴라면 기록을 남겨야 한다.\n'
      printf '         자동 면제하지 않는다: 그러면 공격과 정당한 은퇴가 구분되지 않는다.\n'
    fi
    printf '         은퇴하려면 suppressions.yaml 에 다음을 owner·reason·expiry 와 함께 등록하라:\n'
    printf '           - check: "retire:%s"\n' "$p"
  done < "$TMP/hits"
  echo "CHECKED: $checked"
  exit 1
fi

printf 'PASS: 워크플로 실행 줄 소실 없음\n'
echo "CHECKED: $checked"
exit 0
