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

TMP=$(mktemp -d) || {
  echo "FAIL: temporary directory creation failed (exit 2)"
  exit 2
}
cleanup() { rm -rf "$TMP"; }
trap cleanup EXIT
trap 'cleanup; trap - EXIT; exit 143' TERM
trap 'cleanup; trap - EXIT; exit 130' INT
trap 'cleanup; trap - EXIT; exit 129' HUP

CLEAN=$TMP/patterns.clean
ERRS=$TMP/scanner.errors
FILES=$TMP/tracked-files
ALLOWLIST_RAW=$TMP/allowlist.raw
ALLOWLIST_ROWS=$TMP/allowlist.rows
ALLOWLIST_USED=$TMP/allowlist.used
: > "$ERRS"
: > "$ALLOWLIST_USED"

# CRLF 제거 + 주석(#)·공백뿐인 줄 제거 → 유효 패턴이 0개면 조용한 no-op 금지
cat "${SOURCES[@]}" | tr -d '\r' | /usr/bin/grep -vE '^[[:space:]]*(#|$)' > "$CLEAN" || true
if [ ! -s "$CLEAN" ]; then
  echo "FAIL: no effective secret patterns in: ${SOURCES[*]} (주석/빈 줄뿐, exit 2)"
  exit 2
fi

# 스캔 소스 (V1 2026-08-07 지적 반영):
#   worktree(기본) — 작업트리 파일 내용을 읽는다. CI·수동 검사용.
#   index          — 인덱스(스테이지)에 등록된 blob 내용을 읽는다. pre-commit 용.
#
# 왜 나눠야 하나: 목록만 인덱스에서 읽고 내용을 작업트리에서 읽으면 다음으로 우회된다.
#   git add <비밀파일> → 작업트리만 깨끗한 내용으로 덮어씀 → git commit → 통과
#   (실측: 커밋된 blob 에 AKIA… 가 들어갔는데 스캔은 PASS)
SCAN_SOURCE="${VERIFY_SCAN_SOURCE:-worktree}"
case "$SCAN_SOURCE" in
  worktree|index) ;;
  *) echo "FAIL: invalid VERIFY_SCAN_SOURCE '$SCAN_SOURCE' (exit 2)"; exit 2 ;;
esac

# 줄 허용 목록은 원문 대신 정확한 파일 경로와 줄 내용의 Git blob 지문을 저장한다.
# 같은 경로·지문 항목 하나는 매치 한 번만 소비한다. 파일 전체·디렉터리·글로브 면제는 없다.
ALLOWLIST_SOURCE="${SECRET_ALLOWLIST_FILE:-.secret-allowlist.yaml}"
if printf '%s' "$ALLOWLIST_SOURCE" | /usr/bin/grep -qE '(^/|//|/$|(^|/)\.{1,2}(/|$)|[*?\[])'; then
  echo "FAIL: secret allowlist path must be a literal repository-relative path (exit 2)"
  exit 2
fi
if ! git ls-files --error-unmatch -- ":(literal)$ALLOWLIST_SOURCE" >/dev/null 2>&1; then
  echo "FAIL: secret allowlist file is not tracked: $ALLOWLIST_SOURCE (exit 2)"
  exit 2
fi
allowlist_mode=$(git ls-files -s -- ":(literal)$ALLOWLIST_SOURCE" | awk 'NR==1{print $1}')
case "$allowlist_mode" in
  100644|100755) ;;
  *) echo "FAIL: secret allowlist must be a regular tracked file: $ALLOWLIST_SOURCE (exit 2)"; exit 2 ;;
esac
if [ "$SCAN_SOURCE" = index ]; then
  if ! git show ":$ALLOWLIST_SOURCE" > "$ALLOWLIST_RAW" 2>/dev/null; then
    echo "FAIL: secret allowlist missing/unreadable in index: $ALLOWLIST_SOURCE (exit 2)"
    exit 2
  fi
elif [ ! -f "$ALLOWLIST_SOURCE" ] || [ ! -r "$ALLOWLIST_SOURCE" ] || [ ! -s "$ALLOWLIST_SOURCE" ]; then
  echo "FAIL: secret allowlist missing/not-a-file/unreadable/empty: $ALLOWLIST_SOURCE (exit 2)"
  exit 2
else
  cat -- "$ALLOWLIST_SOURCE" > "$ALLOWLIST_RAW"
fi

# YAML 전체가 아니라 아래 고정된 단일행 subset만 허용한다. 모르는 문법을 조용히
# 받아들이는 범용 흉내 파서보다, 인식하지 못한 모든 줄을 exit 2로 닫는 계약이다.
if ! awk '
  function reject(label) {
    printf "FAIL: secret allowlist syntax error at line %d (expected %s)\n", NR, label > "/dev/stderr"
    bad=1
  }
  function value(prefix, label, raw, v) {
    if (substr(raw, 1, length(prefix)) != prefix) { reject(label); return "" }
    v=substr(raw, length(prefix) + 1)
    if (length(v) < 3 || substr(v, 1, 1) != "\"" || substr(v, length(v), 1) != "\"") {
      reject(label); return ""
    }
    v=substr(v, 2, length(v) - 2)
    if (v == "" || index(v, "\"") || index(v, "\\") || v ~ /[[:cntrl:]]/) {
      reject(label); return ""
    }
    return v
  }
  BEGIN { state=0; count=0; bad=0 }
  state == 0 && ($0 ~ /^[[:space:]]*$/ || $0 ~ /^[[:space:]]*#/) { next }
  state == 0 { path=value("- path: ", "path", $0); state=1; next }
  state == 1 { hash=value("  line_hash: ", "line_hash", $0); state=2; next }
  state == 2 { reason=value("  reason: ", "reason", $0); state=3; next }
  state == 3 { owner=value("  owner: ", "owner", $0); state=4; next }
  state == 4 {
    expiry=value("  expiry: ", "expiry", $0)
    print path "\t" hash "\t" expiry
    count++
    state=0
    next
  }
  END {
    if (state != 0) {
      printf "FAIL: secret allowlist ended inside an entry\n" > "/dev/stderr"
      bad=1
    }
    if (count == 0) {
      printf "FAIL: secret allowlist has zero entries\n" > "/dev/stderr"
      bad=1
    }
    if (bad) exit 2
  }
' "$ALLOWLIST_RAW" > "$ALLOWLIST_ROWS"; then
  echo "FAIL: invalid secret allowlist: $ALLOWLIST_SOURCE (exit 2)"
  exit 2
fi

valid_date() {
  local value="$1" year month day max
  printf '%s' "$value" | /usr/bin/grep -qE '^[0-9]{4}-(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])$' || return 1
  year=${value%%-*}
  month=${value#*-}; month=${month%%-*}
  day=${value##*-}
  case "$month" in
    01|03|05|07|08|10|12) max=31 ;;
    04|06|09|11) max=30 ;;
    02)
      max=28
      if [ $((10#$year % 400)) -eq 0 ] || { [ $((10#$year % 4)) -eq 0 ] && [ $((10#$year % 100)) -ne 0 ]; }; then
        max=29
      fi
      ;;
    *) return 1 ;;
  esac
  [ $((10#$day)) -le "$max" ]
}

today=$(date +%Y-%m-%d)
ALLOW_TOTAL=0
while IFS=$'\t' read -r path hash expiry; do
  ALLOW_TOTAL=$((ALLOW_TOTAL + 1))
  if [ "$path" = "$ALLOWLIST_SOURCE" ]; then
    echo "FAIL: secret allowlist cannot suppress its own file in entry $ALLOW_TOTAL (exit 2)"
    exit 2
  fi
  if printf '%s' "$path" | /usr/bin/grep -qE '(^/|//|/$|(^|/)\.{1,2}(/|$)|[*?\[])'; then
    echo "FAIL: invalid literal path in secret allowlist entry $ALLOW_TOTAL (exit 2)"
    exit 2
  fi
  if ! printf '%s' "$hash" | /usr/bin/grep -qE '^[0-9a-f]{40}$'; then
    echo "FAIL: invalid line_hash in secret allowlist entry $ALLOW_TOTAL (exit 2)"
    exit 2
  fi
  if ! valid_date "$expiry"; then
    echo "FAIL: invalid expiry in secret allowlist entry $ALLOW_TOTAL (exit 2)"
    exit 2
  fi
  if [ "$expiry" \< "$today" ]; then
    echo "FAIL: expired secret allowlist entry $ALLOW_TOTAL (expiry $expiry < today $today, exit 2)"
    exit 2
  fi
done < "$ALLOWLIST_ROWS"

hash_line() { printf '%s' "$1" | git hash-object --stdin; }

consume_allowance() {
  local path="$1" line="$2" hash available used
  hash=$(hash_line "$line") || return 2
  available=$(awk -F '\t' -v p="$path" -v h="$hash" '$1 == p && $2 == h { c++ } END { print c+0 }' "$ALLOWLIST_ROWS")
  used=$(awk -F '\t' -v p="$path" -v h="$hash" '$1 == p && $2 == h { c++ } END { print c+0 }' "$ALLOWLIST_USED")
  if [ "$used" -lt "$available" ]; then
    printf '%s\t%s\n' "$path" "$hash" >> "$ALLOWLIST_USED"
    return 0
  fi
  return 1
}

write_tracked_content() {
  local path="$1"
  if [ "$SCAN_SOURCE" = index ]; then
    git show ":$path"
  elif [ -L "$path" ]; then
    readlink "./$path"
  elif [ -f "$path" ]; then
    cat -- "$path"
  else
    return 2
  fi
}

FAIL=0
ALLOWED_MATCHES=0
UNALLOWED_MATCHES=0

scan_tracked_file() {
  local path="$1" content=$TMP/content matches=$TMP/matches rc=0 line consume_rc
  if ! write_tracked_content "$path" > "$content" 2>>"$ERRS"; then
    printf 'tracked content read error: %q\n' "$path" >> "$ERRS"
    return
  fi
  LC_ALL=C /usr/bin/grep -aEif "$CLEAN" "$content" > "$matches" 2>>"$ERRS" || rc=$?
  if [ "$rc" -eq 1 ]; then return; fi
  if [ "$rc" -gt 1 ]; then
    printf 'grep execution error(rc=%s): %q\n' "$rc" "$path" >> "$ERRS"
    return
  fi
  while IFS= read -r line || [ -n "$line" ]; do
    consume_rc=0
    consume_allowance "$path" "$line" || consume_rc=$?
    if [ "$consume_rc" -eq 0 ]; then
      ALLOWED_MATCHES=$((ALLOWED_MATCHES + 1))
    elif [ "$consume_rc" -eq 1 ]; then
      if [ "$UNALLOWED_MATCHES" -eq 0 ]; then
        echo "FAIL: secret pattern matched in tracked files:"
      fi
      printf '  - %q\n' "$path"
      UNALLOWED_MATCHES=$((UNALLOWED_MATCHES + 1))
      FAIL=1
    else
      printf 'allowlist digest error: %q\n' "$path" >> "$ERRS"
    fi
  done < "$matches"
}

if ! git ls-files -z > "$FILES" 2>>"$ERRS"; then
  echo "FAIL: tracked file enumeration failed"
  FAIL=1
fi
while IFS= read -r -d '' f; do
  scan_tracked_file "$f"
done < "$FILES"

if [ -s "$ERRS" ]; then
  echo "FAIL: scanner error — fail-closed:"
  sed 's/^/  ! /' "$ERRS"
  FAIL=1
fi

if git ls-files | /usr/bin/grep -qx "\.env$"; then
  echo "FAIL: .env is tracked by git (should stay untracked/gitignored)"
  FAIL=1
fi

printf 'ALLOWED_LINES_COUNT=%d\n' "$ALLOW_TOTAL"
printf 'ALLOWED_MATCHES_CONSUMED=%d\n' "$ALLOWED_MATCHES"

if [ "$FAIL" -eq 0 ]; then
  echo "PASS: no secret-pattern match in any tracked file, .env not tracked"
  exit 0
else
  exit 1
fi
