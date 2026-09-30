#!/usr/bin/env bash
# archive-stale-branches.sh — PR 없는 오래된 원격 브랜치를 archive/ 태그로 박제한 뒤 삭제한다.
#
# 근거: docs/engineering/pr-branch-triage-2026-09-28.md §1 (오너 승인 2026-09-30)
# 사용: bash scripts/archive-stale-branches.sh            # 미리보기만 (기본)
#       bash scripts/archive-stale-branches.sh --apply    # 박제 → 원격 확인 → 삭제
# 종료값: 0=PASS  1=FAIL(일부라도 박제·삭제 실패)  2=NOT_RUN(입력을 신뢰할 수 없어 아무것도 안 함)
#
# 유실 0 불변식:
#   - 삭제 대상은 원격 archive/<이름> 태그가 브랜치 끝 SHA와 같다고 ls-remote 로 확인된 것뿐이다.
#   - 삭제는 --force-with-lease 로 확인 시점 SHA에 묶는다. 그 사이 누가 push 했으면 삭제되지 않는다.
# 제외: main · 열린 PR의 head · 최근 MIN_AGE_DAYS 안에 커밋된 브랜치(다른 세션이 작업 중일 수 있음).
# bash 3.2(macOS 기본) 호환 — mapfile·연관배열을 쓰지 않는다.
set -euo pipefail

MIN_AGE_DAYS=${MIN_AGE_DAYS:-7}
APPLY=0
if [ "${1:-}" = "--apply" ]; then APPLY=1
elif [ -n "${1:-}" ]; then echo "사용법: $0 [--apply]" >&2; exit 2
fi

REPO=$(git rev-parse --show-toplevel)
cd "$REPO"
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT

if ! git fetch --prune --quiet origin; then
  echo "NOT_RUN: git fetch 실패 — 원격 상태를 모르면 아무것도 지우지 않는다" >&2; exit 2
fi

# 열린 PR head 목록은 gh 로만 얻는다. 실패하면 PR 이 있는 브랜치를 지울 수 있으므로 중단한다.
if ! gh pr list --state open --limit 500 --json headRefName -q '.[].headRefName' > "$WORK/pr-heads"; then
  echo "NOT_RUN: gh pr list 실패 — 열린 PR 목록 없이는 진행하지 않는다" >&2; exit 2
fi
if [ ! -s "$WORK/pr-heads" ]; then
  echo "NOT_RUN: 열린 PR 0건으로 읽혔다 — 조회 오류로 보고 중단한다" >&2; exit 2
fi

now=$(date +%s)
cutoff=$(( now - MIN_AGE_DAYS * 86400 ))
: > "$WORK/targets"
skipped_recent=0; skipped_pr=0
git for-each-ref --format='%(refname:strip=3)' refs/remotes/origin > "$WORK/all"
while IFS= read -r br; do
  case "$br" in HEAD|main) continue ;; esac
  if grep -qxF "$br" "$WORK/pr-heads"; then skipped_pr=$((skipped_pr+1)); continue; fi
  ts=$(git log -1 --format=%ct "refs/remotes/origin/$br")
  if [ "$ts" -gt "$cutoff" ]; then skipped_recent=$((skipped_recent+1)); continue; fi
  printf '%s %s\n' "$br" "$(git rev-parse "refs/remotes/origin/$br")" >> "$WORK/targets"
done < "$WORK/all"

total=$(wc -l < "$WORK/targets" | tr -d ' ')
echo "대상 ${total}개 · 제외: 열린 PR head ${skipped_pr}개, 최근 ${MIN_AGE_DAYS}일 내 커밋 ${skipped_recent}개"
if [ "$total" -eq 0 ]; then echo "NOT_RUN: 대상 0개"; exit 2; fi
sed 's/^/  /' "$WORK/targets"
if [ "$APPLY" -eq 0 ]; then echo "미리보기 끝. 실행하려면 --apply"; exit 0; fi

# 1) 로컬 태그 생성. 같은 이름 태그가 다른 SHA를 가리키면 그 브랜치는 건너뛴다.
fail=0
: > "$WORK/tagged"
while read -r br sha; do
  tag="archive/$br"
  if existing=$(git rev-parse -q --verify "refs/tags/$tag^{commit}"); then
    if [ "$existing" != "$sha" ]; then
      echo "FAIL: $tag 가 이미 다른 커밋($existing)을 가리킨다 — $br 건너뜀" >&2; fail=1; continue
    fi
  else
    git tag "$tag" "$sha"
  fi
  printf '%s %s\n' "$br" "$sha" >> "$WORK/tagged"
done < "$WORK/targets"

# 2) 태그를 한 번에 push (pre-push 훅이 1회 돈다).
refspecs=$(awk '{print "refs/tags/archive/"$1}' "$WORK/tagged")
# shellcheck disable=SC2086
if ! git push origin $refspecs; then
  echo "FAIL: 태그 push 실패 — 아무 브랜치도 지우지 않았다" >&2; exit 1
fi

# 3) 원격에서 태그 SHA를 다시 읽어, 일치하는 브랜치만 삭제 목록에 넣는다.
git ls-remote --tags origin 'refs/tags/archive/*' > "$WORK/remote-tags"
: > "$WORK/deletable"
while read -r br sha; do
  if grep -qxF "$sha	refs/tags/archive/$br" "$WORK/remote-tags"; then
    printf '%s %s\n' "$br" "$sha" >> "$WORK/deletable"
  else
    echo "FAIL: 원격 archive/$br 확인 실패 — 브랜치 유지" >&2; fail=1
  fi
done < "$WORK/tagged"

ndel=$(wc -l < "$WORK/deletable" | tr -d ' ')
if [ "$ndel" -eq 0 ]; then echo "FAIL: 삭제 가능한 브랜치 0개" >&2; exit 1; fi

# 4) 확인 시점 SHA에 묶어 한 번에 삭제 (pre-push 훅이 1회 돈다).
leases=$(awk '{print "--force-with-lease=refs/heads/"$1":"$2}' "$WORK/deletable")
dels=$(awk '{print ":refs/heads/"$1}' "$WORK/deletable")
# shellcheck disable=SC2086
if ! git push origin $leases $dels; then
  echo "FAIL: 브랜치 삭제 push 실패 — 태그는 남아 있으니 유실은 없다" >&2; exit 1
fi

echo "박제·삭제 ${ndel}개 / 대상 ${total}개. 되살리기: git push origin archive/<이름>:refs/heads/<이름>"
[ "$fail" -eq 0 ] && echo "PASS" || echo "FAIL: 일부 건너뜀(위 로그)"
exit "$fail"
