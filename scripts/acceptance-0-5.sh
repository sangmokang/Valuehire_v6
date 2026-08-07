#!/usr/bin/env bash
# 0-5 인수 스크립트 — push + CI 연결.
# 실제 비밀 리터럴을 이 파일에 넣지 않는다. 로컬 전용 .secret-patterns에 의존하지도 않는다
# (CI에서도 그대로 돌아야 하므로). 검증 대상은 "CI가 비밀 스캔을 강제하는가"다.
set -euo pipefail
unset GIT_DIR GIT_INDEX_FILE GIT_OBJECT_DIRECTORY GIT_WORK_TREE GIT_COMMON_DIR GIT_ALTERNATE_OBJECT_DIRECTORIES
fail=0

WF=.github/workflows/verify.yml

# 1. 워크플로우 파일이 존재하고 추적되는가
if [ ! -f "$WF" ]; then echo "FAIL: $WF 없음"; fail=1
elif ! git ls-files --error-unmatch "$WF" >/dev/null 2>&1; then echo "FAIL: $WF 가 git 추적 대상이 아님"; fail=1; fi

# 2. 워크플로우가 실제 검증 명령을 호출하는가 (이름만 있는 껍데기 금지)
if [ -f "$WF" ]; then
  grep -q 'verify\.sh' "$WF" || { echo "FAIL: 워크플로우가 verify.sh를 호출하지 않음"; fail=1; }
  grep -q 'acceptance-0-6\.sh' "$WF" || { echo "FAIL: 워크플로우가 acceptance-0-6.sh를 호출하지 않음"; fail=1; }
  grep -qE 'on:|push:' "$WF" || { echo "FAIL: 워크플로우에 트리거 정의 없음"; fail=1; }
fi

# 3. 커밋되는 기본 패턴 파일이 존재하고, 그 자체엔 실제 비밀이 없어야 한다
DEF=.secret-patterns.default
if [ ! -s "$DEF" ]; then echo "FAIL: $DEF 없음/빈 파일 — CI가 패턴 없이 돌 수 없다"; fail=1
else
  git ls-files --error-unmatch "$DEF" >/dev/null 2>&1 || { echo "FAIL: $DEF 가 추적되지 않음(CI에서 안 보임)"; fail=1; }
  # 로컬 실제 패턴이 있으면, 기본 파일이 그 실제 리터럴을 품고 있지 않은지 확인
  if [ -s .secret-patterns ]; then
    while IFS= read -r lit; do
      [ -z "$lit" ] && continue
      if grep -qF "$lit" "$DEF"; then echo "FAIL: $DEF 에 실제 비밀 리터럴이 들어있음"; fail=1; fi
    done < .secret-patterns
  fi
fi

# 4. 로컬 전용 패턴 파일 없이도(=CI 환경 재현) verify.sh가 동작해야 한다
#    실저장소를 건드리지 않도록 격리 클론에서 검사한다.
sandbox=$(mktemp -d)
cleanup() { rm -rf -- "$sandbox"; }
trap 'cleanup' EXIT
trap 'cleanup; trap - EXIT; exit 143' TERM
trap 'cleanup; trap - EXIT; exit 130' INT
trap 'cleanup; trap - EXIT; exit 129' HUP
set +e
git clone -q --no-local . "$sandbox/repo" 2>/dev/null
clone_rc=$?
if [ "$clone_rc" -eq 0 ]; then
  if [ -e "$sandbox/repo/.secret-patterns" ]; then
    echo "FAIL: 클론에 로컬 전용 패턴 파일이 따라옴 — gitignore 되지 않았다"; fail=1
  fi
  ( cd "$sandbox/repo" && bash verify.sh >/dev/null 2>&1 )
  rc=$?
  if [ "$rc" -ne 0 ]; then
    echo "FAIL: 로컬 패턴 파일 없는 환경(CI 재현)에서 verify.sh exit=$rc (기대 0)"
    fail=1
  fi
  # 카나리: CI 환경에서도 검출력이 살아있는가 (기본 패턴이 잡아야 하는 형태를 심는다)
  ( cd "$sandbox/repo" \
      && printf 'CHATGPT_PASSWORD=hunter2example\n' > leak-canary.env.txt \
      && git add leak-canary.env.txt \
      && bash verify.sh >/dev/null 2>&1 )
  canary_rc=$?
  if [ "$canary_rc" -eq 0 ]; then
    echo "FAIL: 기본 패턴이 명백한 자격증명 대입문을 못 잡음 — CI 스캔이 무의미"
    fail=1
  fi
else
  echo "FAIL: 격리 클론 생성 실패(exit=$clone_rc) — 4번 검증 불가"; fail=1
fi
set -e
cleanup
trap - EXIT TERM INT HUP

# 5. 배송 — origin/main이 로컬 main과 같은 커밋을 가리켜야 한다(push 완료)
git fetch -q origin 2>/dev/null || true
local_main=$(git rev-parse main 2>/dev/null || echo none)
remote_main=$(git rev-parse origin/main 2>/dev/null || echo none)
if [ "$local_main" != "$remote_main" ]; then
  echo "FAIL: origin/main($remote_main) != main($local_main) — push 미완료"
  fail=1
fi

# 6. 원격에 비밀이 올라가지 않았는지 — 원격 브랜치 트리 전수 스캔(로컬 패턴 있을 때만)
if [ -s .secret-patterns ] && [ "$remote_main" != none ]; then
  if git grep -lIf .secret-patterns "$remote_main" -- 2>/dev/null | head -1 | grep -q .; then
    echo "FAIL: origin/main 트리에 비밀 패턴 매치 — 원격 유출"
    fail=1
  fi
fi

[ "$fail" -eq 0 ] && echo "PASS: 0-5 완료 — CI 비밀스캔 강제 + push 완료 + 원격 트리 비밀 0건" || exit 1
