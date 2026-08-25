#!/usr/bin/env bash
# 로컬 운영자가 scan-data-exposure.sh의 12자리 path 지문을 현재·삭제 history 경로로 역조회한다.
# 이 명령은 원문 경로를 의도적으로 출력하므로 CI/goal/판정서에서 실행하지 않는다.
set -uo pipefail

unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE GIT_OBJECT_DIRECTORY \
      GIT_ALTERNATE_OBJECT_DIRECTORIES GIT_COMMON_DIR GIT_PREFIX GIT_QUARANTINE_PATH

WANTED=$(printf '%s' "${1:-}" | tr '[:upper:]' '[:lower:]')
case "$WANTED" in
  [0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]) ;;
  *) echo "NOT_RUN: 12자리 16진수 path 지문이 필요하다"; echo "MATCHES: 0"; exit 2 ;;
esac

git rev-parse --git-dir >/dev/null 2>&1 || {
  echo "NOT_RUN: git 저장소가 아니다"; echo "MATCHES: 0"; exit 2;
}
TMP_ROOT=$(mktemp -d) || { echo "NOT_RUN: 임시 역조회 공간을 만들지 못했다"; echo "MATCHES: 0"; exit 2; }
trap 'ruby -rfileutils -e "FileUtils.remove_entry(ARGV[0]) if File.exist?(ARGV[0])" "$TMP_ROOT"' EXIT

fingerprint_path() {
  local digest
  digest=$(printf '%s' "$1" | shasum -a 256 2>/dev/null) || return 2
  digest=${digest%%[[:space:]]*}
  digest=$(printf '%s' "$digest" | tr '[:upper:]' '[:lower:]')
  case "$digest" in *[!0-9a-f]*|'') return 2 ;; esac
  [ "${#digest}" -ge 12 ] || return 2
  printf '%.12s' "$digest"
}

record_match() {
  local path="$1" actual escaped
  actual=$(fingerprint_path "$path") || return 2
  [ "$actual" = "$WANTED" ] || return 0
  printf -v escaped '%q' "$path"
  printf '%s\n' "$escaped" >> "$TMP_ROOT/matches"
}

collect_current() {
  local path
  if ! git ls-files -z > "$TMP_ROOT/current" 2>/dev/null; then return 2; fi
  while IFS= read -r -d '' path; do record_match "$path" || return 2; done < "$TMP_ROOT/current"
}

collect_history() {
  local rev record meta type path
  if ! git rev-list --all --reflog > "$TMP_ROOT/revisions" 2>/dev/null; then return 2; fi
  while IFS= read -r rev; do
    [ -n "$rev" ] || continue
    if ! git ls-tree -rz --full-tree "$rev" > "$TMP_ROOT/tree" 2>/dev/null; then return 2; fi
    while IFS= read -r -d '' record; do
      meta=${record%%$'\t'*}; path=${record#*$'\t'}
      if [ "$meta" = "$record" ] || ! IFS=' ' read -r _ type _ <<< "$meta" || [ "$type" != blob ]; then
        return 2
      fi
      record_match "$path" || return 2
    done < "$TMP_ROOT/tree"
  done < "$TMP_ROOT/revisions"
}

: > "$TMP_ROOT/matches"
if ! collect_current || ! collect_history; then
  echo "NOT_RUN: Git 경로 목록을 완전히 읽지 못했다"
  echo "MATCHES: 0"
  exit 2
fi
if ! LC_ALL=C sort -u "$TMP_ROOT/matches" > "$TMP_ROOT/unique"; then
  echo "NOT_RUN: 역조회 후보를 정규화하지 못했다"; echo "MATCHES: 0"; exit 2
fi

count=$(awk 'END { print NR + 0 }' "$TMP_ROOT/unique")
while IFS= read -r path; do [ -z "$path" ] || printf 'MATCH: %s\n' "$path"; done < "$TMP_ROOT/unique"
printf 'MATCHES: %d\n' "$count"
if [ "$count" -eq 0 ]; then exit 1; fi
if [ "$count" -gt 1 ]; then printf 'COLLISION: %d candidates\n' "$count"; exit 1; fi
exit 0
