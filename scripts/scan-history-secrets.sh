#!/usr/bin/env bash
# 도달 가능한 모든 히스토리 blob을 기본 비밀 패턴으로 검사한다.
# 종료값: 0=위반 없음, 1=위반 발견, 2=검사기 오류 또는 스캔 무효.
set -u

TMP_DIR=
CLEAN=
OBJS=
SHAS=
BLOB=

cleanup() {
  local cleanup_failed=0
  if [ -n "$BLOB" ] && ! rm -f -- "$BLOB"; then cleanup_failed=1; fi
  if [ -n "$SHAS" ] && ! rm -f -- "$SHAS"; then cleanup_failed=1; fi
  if [ -n "$OBJS" ] && ! rm -f -- "$OBJS"; then cleanup_failed=1; fi
  if [ -n "$CLEAN" ] && ! rm -f -- "$CLEAN"; then cleanup_failed=1; fi
  if [ -n "$TMP_DIR" ] && ! rmdir -- "$TMP_DIR" 2>/dev/null; then cleanup_failed=1; fi
  return "$cleanup_failed"
}

TMP_DIR=$(mktemp -d)
mktemp_rc=$?
if [ "$mktemp_rc" -ne 0 ] || [ -z "$TMP_DIR" ] || [ ! -d "$TMP_DIR" ]; then
  echo "FAIL: mktemp 실패 — 임시 파일을 만들지 못했다(스캔 무효)"
  exit 2
fi

CLEAN="$TMP_DIR/patterns"
OBJS="$TMP_DIR/objects"
SHAS="$TMP_DIR/shas"
BLOB="$TMP_DIR/blob"
trap cleanup EXIT
trap 'exit 2' HUP INT TERM

if ! awk '
  {
    gsub(/\r/, "")
    if ($0 !~ /^[[:space:]]*(#|$)/) print
  }
' .secret-patterns.default > "$CLEAN"; then
  echo "FAIL: 기본 패턴 파일을 읽지 못했다(스캔 무효)"
  exit 2
fi
if [ ! -s "$CLEAN" ]; then
  echo "FAIL: 유효 패턴 0개"
  exit 2
fi

if ! git rev-list --all --reflog --objects > "$OBJS"; then
  echo "FAIL: git rev-list 실패 — 히스토리를 읽지 못했다(스캔 무효)"
  exit 2
fi
if ! awk 'NF && !seen[$1]++ { print $1 }' "$OBJS" > "$SHAS"; then
  echo "FAIL: 도달 가능 객체 목록을 정리하지 못했다(스캔 무효)"
  exit 2
fi

count=$(awk 'END { print NR + 0 }' "$SHAS")
count_rc=$?
if [ "$count_rc" -ne 0 ]; then
  echo "FAIL: 도달 가능 객체 수를 세지 못했다(스캔 무효)"
  exit 2
fi
case "$count" in
  ''|*[!0-9]*)
    echo "FAIL: 도달 가능 객체 수가 올바르지 않다(스캔 무효)"
    exit 2
    ;;
esac
if [ "$count" -lt 2 ]; then
  echo "FAIL: 도달 가능 객체가 ${count}개 — 저장소를 제대로 읽지 못했다(스캔 무효)"
  exit 2
fi
echo "스캔 대상 객체: ${count}개"

hit=0
blobs=0
while IFS= read -r sha; do
  object_type=$(git cat-file -t "$sha" 2>/dev/null)
  type_rc=$?
  if [ "$type_rc" -ne 0 ]; then
    echo "FAIL: 객체형 읽기 실패: $sha (git cat-file exit=$type_rc · 스캔 무효)"
    exit 2
  fi

  if [ "$object_type" = blob ]; then
    blobs=$((blobs + 1))
    if ! git cat-file blob "$sha" > "$BLOB"; then
      echo "FAIL: blob 읽기 실패: $sha (스캔 무효)"
      exit 2
    fi

    grep -a -E -i -f "$CLEAN" "$BLOB" >/dev/null
    grep_rc=$?
    case "$grep_rc" in
      0)
        echo "FAIL: 히스토리 blob에 자격증명 패턴 매치: $sha"
        if ! awk -v s="$sha" '
          $1 == s {
            path = $0
            sub(/^[^[:space:]]+[[:space:]]*/, "", path)
            if (path == "") path = "(rev-list 경로 없음)"
            print "  경로: " path
            found = 1
          }
          END {
            if (!found) print "  경로: (rev-list 기록 없음)"
          }
        ' "$OBJS"; then
          echo "FAIL: 과거 경로를 읽지 못했다(스캔 무효)"
          exit 2
        fi
        hit=1
        ;;
      1)
        ;;
      *)
        echo "FAIL: grep 검사기 오류: $sha (grep exit=$grep_rc · 스캔 무효)"
        exit 2
        ;;
    esac
  fi
done < "$SHAS"

if [ "$blobs" -eq 0 ]; then
  echo "FAIL: blob을 한 개도 읽지 못했다(스캔 무효)"
  exit 2
fi
if [ "$hit" -eq 0 ]; then
  echo "PASS: 히스토리 전량 blob 스캔 0건 (blob ${blobs}개 검사)"
fi
result=$hit
if ! cleanup; then
  echo "FAIL: 임시 파일 정리 실패 — 민감 내용이 남았을 수 있다(스캔 무효)"
  result=2
fi
trap - EXIT HUP INT TERM
exit "$result"
