#!/usr/bin/env bash
# 추적 파일 전체에서 비밀 패턴을 스캔한다. 패턴은 이 파일에 하드코딩하지 않고
# gitignore된 .secret-patterns(한 줄당 ERE 1개, # 주석·빈 줄 허용)에서 읽는다.
# 스캐너 자신도 스캔 대상(자기 면제 없음).
# V2(2026-08-07) REFUTED 반영:
#  ① 파일명 공백/개행/선행하이픈 우회 차단 — ls-files -z + xargs -0 + `--`
#  ② fail-open 차단 — -f/-r 검사, CRLF 정규화, 유효 패턴 0개 시 exit 2, grep stderr를 실패로 취급
set -euo pipefail

# 패턴 소스 결정:
#  - SECRET_PATTERNS_FILE 지정 시 → 그 파일만 사용(테스트·CI 주입용, 기존 계약 유지)
#  - 미지정 시 → 커밋된 .secret-patterns.default + gitignore된 .secret-patterns 합집합.
#    전자는 "모양"(일반 자격증명 패턴), 후자는 이 프로젝트의 알려진 실제 리터럴.
#    CI에는 후자가 없으므로 전자만으로 동작한다 — 실제 비밀을 CI에 올리지 않기 위한 설계.
SOURCES=()
if [ -n "${SECRET_PATTERNS_FILE:-}" ]; then
  SOURCES=("$SECRET_PATTERNS_FILE")
else
  [ -e .secret-patterns.default ] && SOURCES+=(.secret-patterns.default)
  [ -e .secret-patterns ] && SOURCES+=(.secret-patterns)
fi

if [ ${#SOURCES[@]} -eq 0 ]; then
  echo "FAIL: no secret patterns file found (.secret-patterns.default / .secret-patterns) (exit 2)"
  echo "      조용한 스킵 금지 — 패턴 없이는 스캔 자체가 무효다."
  exit 2
fi
for p in "${SOURCES[@]}"; do
  if [ ! -f "$p" ] || [ ! -r "$p" ] || [ ! -s "$p" ]; then
    echo "FAIL: secret patterns file missing/not-a-file/unreadable/empty: $p (exit 2)"
    echo "      로컬: 저장소 루트에 .secret-patterns 배치 / CI: .secret-patterns.default 사용."
    exit 2
  fi
done

CLEAN=$(mktemp) ERRS=$(mktemp)
trap 'rm -f "$CLEAN" "$ERRS"' EXIT

# CRLF 제거 + 주석(#)·공백뿐인 줄 제거 → 유효 패턴이 0개면 조용한 no-op 금지
cat "${SOURCES[@]}" | tr -d '\r' | grep -vE '^[[:space:]]*(#|$)' > "$CLEAN" || true
if [ ! -s "$CLEAN" ]; then
  echo "FAIL: no effective secret patterns in: ${SOURCES[*]} (주석/빈 줄뿐, exit 2)"
  exit 2
fi

FAIL=0

# 스캔 소스 (V1 2026-08-07 지적 반영):
#   worktree(기본) — 작업트리 파일 내용을 읽는다. CI·수동 검사용.
#   index          — 인덱스(스테이지)에 등록된 blob 내용을 읽는다. pre-commit 용.
#
# 왜 나눠야 하나: 목록만 인덱스에서 읽고 내용을 작업트리에서 읽으면 다음으로 우회된다.
#   git add <비밀파일> → 작업트리만 깨끗한 내용으로 덮어씀 → git commit → 통과
#   (실측: 커밋된 blob 에 AKIA… 가 들어갔는데 스캔은 PASS)
SCAN_SOURCE="${VERIFY_SCAN_SOURCE:-worktree}"

set +e
# -i: 자격증명 키워드는 대소문자를 가리지 않는다(`password:` / `PASSWORD=` 둘 다 잡아야 함)
if [ "$SCAN_SOURCE" = "index" ]; then
  LEAKS=""
  while IFS= read -r -d '' f; do
    rc=0
    git show ":$f" 2>>"$ERRS" | grep -qEif "$CLEAN" || rc=$?
    if [ "$rc" -eq 0 ]; then
      LEAKS="${LEAKS}${f}"$'\n'
    elif [ "$rc" -gt 1 ]; then
      printf 'grep 실행 오류(rc=%s): %s\n' "$rc" "$f" >> "$ERRS"
    fi
  done < <(git ls-files -z)
  LEAKS="${LEAKS%$'\n'}"
else
  LEAKS=$(git ls-files -z | xargs -0 grep -lEif "$CLEAN" -- 2>"$ERRS")
fi
set -e
if [ -s "$ERRS" ]; then
  echo "FAIL: scanner error — fail-closed (grep/xargs stderr):"
  sed 's/^/  ! /' "$ERRS"
  FAIL=1
fi
if [ -n "$LEAKS" ]; then
  echo "FAIL: secret pattern matched in tracked files:"
  printf '%s\n' "$LEAKS" | sed 's/^/  - /'
  FAIL=1
fi

if git ls-files | grep -qx "\.env$"; then
  echo "FAIL: .env is tracked by git (should stay untracked/gitignored)"
  FAIL=1
fi

if [ "$FAIL" -eq 0 ]; then
  echo "PASS: no secret-pattern match in any tracked file, .env not tracked"
  exit 0
else
  exit 1
fi
