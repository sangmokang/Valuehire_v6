#!/usr/bin/env bash
# 0-2 인수 스크립트 — 비밀번호 리터럴은 이 파일에 절대 넣지 않는다(.secret-patterns에서 런타임에 읽음).
# 근거: 2026-08-06 acceptance-0-6.sh 자기 매칭 사고 재발 방지.
# V1(codex 2026-08-07) 판정 반영: ③ trap 기반 원복(신호에도 심은 리터럴 잔존 금지),
# ④ 객체 수준 검증(cat-file/fsck) — "git log --all 0건"만으로 완료 판정 금지.
set -euo pipefail
# V2 3차 판정 잔여지적 ⑴: 이 변수들이 환경에 있으면 격리 sandbox의 git이 실저장소를 가리켜
# 검증이 실저장소를 오염시키거나 위양성 PASS를 낸다. CI/훅 도입(0-5) 전에 반드시 닫아둔다.
unset GIT_DIR GIT_INDEX_FILE GIT_OBJECT_DIRECTORY GIT_WORK_TREE GIT_COMMON_DIR GIT_ALTERNATE_OBJECT_DIRECTORIES
fail=0

PATTERNS="${SECRET_PATTERNS_FILE:-.secret-patterns}"
if [ ! -s "$PATTERNS" ]; then echo "FAIL: $PATTERNS 없음/빈 파일 — AC 판정 불가"; exit 2; fi
LIT=$(head -1 "$PATTERNS")

# 1. 히스토리 전체(모든 refs, -S)에서 리터럴 커밋 0건
hits=$(git log --all -S"$LIT" --oneline | wc -l | tr -d ' ')
if [ "$hits" -ne 0 ]; then
  echo "FAIL: 히스토리에 리터럴 커밋 ${hits}건 잔존"
  git log --all -S"$LIT" --oneline
  fail=1
fi

# 2. verify.sh — 리터럴 하드코딩·자기 면제(grep -v 제외 일체) 없이 통과
if grep -qF "$LIT" verify.sh; then echo "FAIL: verify.sh에 리터럴 하드코딩 잔존"; fail=1; fi
# 자기 면제 = 스캔 대상(ls-files) 파이프라인에서의 경로 제외. 패턴 파일 전처리의 grep -v(주석 제거)는 무관.
if grep -E 'ls-files' verify.sh | grep -q 'grep -v'; then
  echo "FAIL: verify.sh 스캔 파이프라인에 자기 면제/경로 제외(grep -v) 잔존"; fail=1
fi
bash verify.sh || { echo "FAIL: verify.sh exit != 0"; fail=1; }

# 3. 뮤테이션 — 스캐너가 조용히 무력화되지 않았는지 실증한다.
#    ⚠️ V2 재판정(2026-08-07) 반영: 이 검사를 **이 저장소 안에서** 하면 안 된다.
#    실제 리터럴을 git add하면 blob이 object DB에 영구히 써지고(= 0-2 목적 자체를 파괴),
#    그 unreachable blob을 check5의 fsck가 세어 어떤 상태에서도 PASS가 불가능해진다.
#    → 격리된 임시 저장소 + 합성 토큰으로 검증한다. 실제 리터럴·실제 object DB 무접촉.
sandbox=$(mktemp -d)
cleanup_sandbox() { rm -rf -- "$sandbox"; }
trap 'cleanup_sandbox' EXIT
trap 'cleanup_sandbox; trap - EXIT; exit 143' TERM
trap 'cleanup_sandbox; trap - EXIT; exit 130' INT
trap 'cleanup_sandbox; trap - EXIT; exit 129' HUP
CANARY="ACCEPTANCE-MUTATION-CANARY-42"
(
  cd "$sandbox"
  git init -q .
  cp "$OLDPWD/verify.sh" .
  printf '%s\n' "$CANARY" > .secret-patterns
  printf '.secret-patterns\n' > .gitignore
  git add verify.sh .gitignore
  git -c user.email=a@a -c user.name=a commit -qm init
  printf '%s\n' "$CANARY" > planted.txt
  git add planted.txt
)
# 신호 원복 적대 테스트 전용 훅(운영 경로 무영향): 원복 창을 결정적으로 늘린다
[ -n "${ACCEPTANCE_TEST_SLEEP:-}" ] && sleep "$ACCEPTANCE_TEST_SLEEP"
if ( cd "$sandbox" && bash verify.sh >/dev/null 2>&1 ); then
  echo "FAIL: 심은 카나리를 verify.sh가 못 잡음 — 스캐너가 조용히 무력화됨"
  fail=1
fi
# 패턴 파일이 실제로 유효한 패턴을 갖는지(주석·빈줄뿐이 아닌지)는 verify.sh가 exit 2로 보증하지만,
# 실제 .secret-patterns가 이 저장소 스캔에 쓰이고 있음을 여기서 한 번 더 확인한다.
if ! grep -qvE '^[[:space:]]*(#|$)' "$PATTERNS"; then
  echo "FAIL: $PATTERNS 에 유효 패턴 0개"; fail=1
fi
cleanup_sandbox
trap - EXIT TERM INT HUP

# 4. docs/ 실파일(비추적 포함)에 리터럴 0건
if [ -d docs ]; then
  if grep -rlF "$LIT" docs/ 2>/dev/null; then echo "FAIL: docs/ 실파일에 리터럴 잔존"; fail=1; fi
else
  echo "NOTE: docs/ 없음(워크트리에서 실행 중) — 최종 판정은 main에서 재실행 필수"
fi

# 5-a. 객체 수준 — 알려진 오염 객체가 저장소(object db)에서 실제로 소멸했는가
#      (V1-④ + V2-④d 반영)
#    "log --all 0건"은 live-ref 음성일 뿐이다. 비밀의 실체는 blob이므로 커밋 SHA만으론 증명 불가 —
#    2026-08-07 사전 전수 열거한 오염 blob 6개 + -S 히트 커밋 6개의 객체 부재를 직접 검사한다.
CONTAMINATED_COMMITS="4d53eac48c957e70ece5d04a600b2e53527f384a
c32d5fd091748f17259e16236e76098ef325479e
e951c59c7dede7762bfcf17aeb9a026c4894609f
ce814451f3d83a0f9b6360ec6ab9218a15a03c2c
2f45b7b6dda007976ee493b6cca9b0a4bece25be
965f084fed098db8daeae376ca05f3e21b814d41"
CONTAMINATED_BLOBS="2efa8a62dcb79de0836886a96ccebd32f0388446
450f4ace2a410e17c9b3945104dff135fcbb3ddf
5cc108c1159d963e07213add8f6fe0360e4f1bdf
bd3eb3eebab7618895b99509e44f26b7347e0420
e3a42af9f052964012832e996cc7eec2b9b8509c
f9f12ed9a352eb5e4cc881239f39ee5568d80478"
for sha in $CONTAMINATED_COMMITS; do
  if git cat-file -e "$sha" 2>/dev/null; then
    echo "FAIL: 오염 커밋 객체 잔존(복구 가능): $sha"; fail=1
  fi
done
for sha in $CONTAMINATED_BLOBS; do
  if git cat-file -e "$sha" 2>/dev/null; then
    echo "FAIL: 오염 blob 객체 잔존(cat-file -p로 평문 복원 가능): $sha"; fail=1
  fi
done
# 5-b. 미래의 미도달 객체 내용 검사 — 상시 회귀 조건.
#      실패한 commit/reset만으로도 unrelated unreachable 객체는 정상 개발 중 생긴다. 개수 0을
#      상시 요구하면 Gate 0을 영구 차단하므로, 일반 실행에서는 객체 내용을 실제 리터럴과 대조한다.
#      commit message·tree path·tag에도 값이 들어갈 수 있어 blob만이 아니라 모든 객체형을 연다.
#      --no-reflogs 필수: reflog가 가리키는 객체는 아래 5-c에서 별도로 전수 검사한다.
fsck_rc=0
fsck_output=$(git fsck --full --no-reflogs --unreachable 2>&1) || fsck_rc=$?
if [ "$fsck_rc" -ne 0 ]; then
  echo "FAIL: git fsck 실행 실패 (exit=$fsck_rc) — 미도달 객체 검사 무효"
  fail=1
fi
unreachable_objects=$(printf '%s\n' "$fsck_output" |
  awk '$1 == "unreachable" { print $2, $3 }')
while read -r object_type sha; do
  [ -z "${object_type:-}" ] && continue
  if git cat-file "$object_type" "$sha" 2>/dev/null |
     LC_ALL=C grep -aF "$LIT" >/dev/null; then
    object_scan_status=("${PIPESTATUS[@]}")
  else
    object_scan_status=("${PIPESTATUS[@]}")
  fi
  cat_file_rc=${object_scan_status[0]:-1}
  grep_rc=${object_scan_status[1]:-2}
  if [ "$cat_file_rc" -ne 0 ]; then
    echo "FAIL: unreachable ${object_type} 읽기 실패: $sha (exit=$cat_file_rc)"
    fail=1
  elif [ "$grep_rc" -eq 0 ]; then
    echo "FAIL: unreachable ${object_type}에 리터럴 잔존: $sha"
    fail=1
  elif [ "$grep_rc" -ne 1 ]; then
    echo "FAIL: unreachable ${object_type} 내용 대조 실패: $sha (exit=$grep_rc)"
    fail=1
  fi
done <<< "$unreachable_objects"

# 5-c. 도달 가능한 모든 지점(refs + reflog 포함)의 blob 전수 스캔 — 상시 회귀 조건.
#      SHA 화이트리스트는 "과거의 알려진 오염"만 잡는다. 미래에 새로 유입되는 비밀은
#      내용 기반으로만 잡을 수 있으므로, --reflog 포함 전 객체를 실제로 열어 확인한다.
while IFS= read -r sha; do
  [ -z "$sha" ] && continue
  reachable_type_rc=0
  reachable_type=$(git cat-file -t "$sha" 2>/dev/null) || reachable_type_rc=$?
  if [ "$reachable_type_rc" -ne 0 ]; then
    echo "FAIL: 도달 가능 객체형 읽기 실패: $sha (exit=$reachable_type_rc)"
    fail=1
    continue
  fi
  [ "$reachable_type" = blob ] || continue

  if git cat-file blob "$sha" 2>/dev/null |
     LC_ALL=C grep -aF "$LIT" >/dev/null; then
    reachable_scan_status=("${PIPESTATUS[@]}")
  else
    reachable_scan_status=("${PIPESTATUS[@]}")
  fi
  reachable_cat_file_rc=${reachable_scan_status[0]:-1}
  reachable_grep_rc=${reachable_scan_status[1]:-2}
  if [ "$reachable_cat_file_rc" -ne 0 ]; then
    echo "FAIL: 도달 가능 blob 읽기 실패: $sha (exit=$reachable_cat_file_rc)"
    fail=1
  elif [ "$reachable_grep_rc" -eq 0 ]; then
    echo "FAIL: 도달 가능 blob에 리터럴 잔존: $sha"
    fail=1
  elif [ "$reachable_grep_rc" -ne 1 ]; then
    echo "FAIL: 도달 가능 blob 내용 대조 실패: $sha (exit=$reachable_grep_rc)"
    fail=1
  fi
done < <(git rev-list --all --reflog --objects 2>/dev/null | awk '{print $1}' | sort -u)

# 6~9. 종료상태(end-state) 전용 검사 — 청소 **직후**에만 참인 조건이다.
#      unreachable 객체 0개·ref 화이트리스트·pseudoref 부재·워크트리 0개는 이후 정상적인
#      개발(commit/reset, worktree 생성, fetch)에서 당연히 깨진다. 일반 실행은 위 5-b에서
#      unreachable 객체의 실제 내용을 검사한다. 청소 절차 검증 시 ACCEPTANCE_ENDSTATE=1 로 켠다.
if [ -n "${ACCEPTANCE_ENDSTATE:-}" ]; then
# 6. unreachable 객체 0개 — 비밀 이력 청소를 끝낸 바로 그 시점의 완결성
unreach=$(printf '%s\n' "$unreachable_objects" | awk 'NF{c++} END{print c+0}')
if [ "$unreach" -ne 0 ]; then
  echo "FAIL: unreachable 객체 ${unreach}건 잔존 (reflog expire/gc --prune=now 미완)"
  fail=1
fi

# 7. ref 화이트리스트 — main·origin/main 외 ref(브랜치/태그/스태시/notes/replace 등) 잔존 금지
extra=$(git for-each-ref --format='%(refname)' | grep -vE '^refs/(heads/main|remotes/origin/main)$' || true)
if [ -n "$extra" ]; then
  echo "FAIL: 허용 외 ref 잔존(오염 조상 복구 경로일 수 있음):"
  echo "$extra" | sed 's/^/  - /'
  fail=1
fi

# 8. pseudoref — common dir + 워크트리별 ORIG_HEAD/FETCH_HEAD 잔존 금지 (V1-④ + V2-④c)
GCD=$(git rev-parse --git-common-dir)
for p in ORIG_HEAD FETCH_HEAD; do
  if [ -e "$GCD/$p" ]; then echo "FAIL: $p 잔존 ($GCD/$p)"; fail=1; fi
  for wp in "$GCD"/worktrees/*/"$p"; do
    [ -e "$wp" ] && { echo "FAIL: per-worktree $p 잔존 ($wp)"; fail=1; }
  done
done

# 9. 워크트리 admin dir — stale admin dir는 gc --prune=now를 무력화하는 gc root (V2-④b)
#    최종 상태에선 등록 워크트리 0개 + prunable 0개 + admin dir 잔존 0개여야 한다.
prunable=$(git worktree list --porcelain | grep -c '^prunable' || true)
if [ "$prunable" -ne 0 ]; then
  echo "FAIL: prunable 워크트리 ${prunable}개 — stale admin dir가 오염 객체를 gc에서 살려둘 수 있음"
  git worktree list
  fail=1
fi
if [ -d "$GCD/worktrees" ] && [ -n "$(/bin/ls -A "$GCD/worktrees" 2>/dev/null)" ]; then
  echo "FAIL: 워크트리 admin dir 잔존: $GCD/worktrees/ 아래 $(/bin/ls -A "$GCD/worktrees" | tr '\n' ' ')"
  fail=1
fi
fi  # ACCEPTANCE_ENDSTATE

[ "$fail" -eq 0 ] && echo "PASS: 0-2 — 히스토리·객체·reflog·docs 리터럴 0건, 스캐너 뮤테이션 검출 확인${ACCEPTANCE_ENDSTATE:+ (+종료상태 검사)}" || exit 1
