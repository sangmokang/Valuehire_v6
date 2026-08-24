#!/usr/bin/env bash
# scan-data-exposure.sh — 후보자 데이터가 git 으로 새는 세 경로를 한 판정기로 막는다
#
# 계약:
#   사용법 : bash scripts/scan-data-exposure.sh <tracked|history|pii|all>
#   출력   : 항목마다 PASS:/FAIL: 를 stdout 에 전부 출력
#   종료   : 0 = PASS | 1 = FAIL(위반 발견) | 2 = NOT_RUN(스캔 자체가 성립하지 않음)
#   불변식 : 검사 대상 0건은 통과가 아니다 (P20 · fail-closed)
#
# 왜 하나로 모았나(2026-08-12 V1 적대검증 D4):
#   같은 규칙을 CI 워크플로 본문과 인수 스크립트에 두 벌로 적었더니, CI 스텝에
#   `if: ${{ false }}` 를 넣어 영구히 꺼도 인수검사·pre-commit·pre-push 가 전부 초록이었다.
#   판정기가 두 벌이면 반드시 갈라진다. 판정을 여기 한 곳에 두고 CI 도 인수검사도
#   **같은 파일을 실행**한다. 그러면 인수검사가 문자열 대조가 아니라 실행 검증이 된다(P16).
#
# 세 모드가 막는 것:
#   tracked — 지금 추적 중인 파일의 크기·금지 경로 (기존 CI 인라인 본문을 여기로 옮김)
#   history — **도달 가능한 모든 blob** 의 크기·금지 경로 (D1)
#             커밋했다가 다음 커밋에서 지운 큰 파일은 현재 목록에 없지만 기록에는 남는다.
#             2026-08-12 실측: 1,228,800 바이트가 도달 가능한 채로 tracked 스캔을 통과했다.
#   pii     — 크기·확장자로는 안 잡히는 **후보자 개인정보 내용** (D2)
#             *.csv·*.sql 은 정상 마이그레이션·픽스처와 구분이 안 되어 경로 차단에서
#             의도적으로 제외돼 있다. 그 자리를 이 검사가 메운다.
#             2026-08-12 실측: 220 바이트 CSV 와 125 바이트 SQL 이 훅·CI·비밀스캔을 전부 통과했다.
set -uo pipefail

MODE="${1:-all}"
MAX_BYTES=1048576

case "$MODE" in
  tracked|history|pii|all) ;;
  *) echo "NOT_RUN: 알 수 없는 모드 '$MODE' (tracked|history|pii|all)"; exit 2 ;;
esac

git rev-parse --git-dir >/dev/null 2>&1 || { echo "NOT_RUN: git 저장소가 아니다"; exit 2; }

TMP_ROOT=$(mktemp -d) || { echo "NOT_RUN: 임시 검사 공간을 만들지 못했다"; echo "CHECKED: 0"; exit 2; }
trap 'rm -rf -- "$TMP_ROOT"' EXIT

fail=0
checked_total=0
last_checked=0

# 금지 경로 판정 — 훅(hooks/pre-commit)과 **같은 목록**이어야 한다.
# 목록이 갈라지면 한쪽만 막는 비대칭이 생기고, 그 비대칭이 훅 우회 습관을 만든다.
# 확장자 비교는 대소문자를 무시한다(dump.DB 가 통과한 2026-08-09 실측).
is_forbidden_path() {
  local lf; lf=$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]')
  case "$lf" in
    artifacts/*|*/artifacts/*|data/*|*/data/*|private-reviews/*|*/private-reviews/*|\
    *.db|*.db-*|*.sqlite|*.sqlite-*|*.sqlite3|*.sqlite3-*|*.jsonl|*.ndjson|*.parquet)
      return 0 ;;
  esac
  return 1
}

safe_display_path() {
  # 제어문자가 줄 구조를 깨거나 로그를 위조하지 않도록 shell-escaped 경로만 출력한다.
  printf '%q' "$1"
}

# ── tracked ──────────────────────────────────────────────────────────────────
scan_tracked() {
  local n=0 inspected=0 bad=0 invalid=0 f sz
  while IFS= read -r -d '' f; do
    n=$((n + 1))
    if is_forbidden_path "$f"; then
      echo "FAIL: 산출물·데이터 경로가 추적됨: $f (P21 · 후보자 PII)"; bad=1
    fi
    sz=$(git cat-file -s ":$f" 2>/dev/null) || sz=""
    case "$sz" in
      ''|*[!0-9]*) echo "NOT_RUN: blob 크기를 읽지 못함: $f"; invalid=1; continue ;;
    esac
    inspected=$((inspected + 1))
    if [ "$sz" -gt "$MAX_BYTES" ]; then
      echo "FAIL: ${MAX_BYTES} 바이트 초과: $f (${sz} 바이트)"; bad=1
    fi
  done < <(git ls-files -z)
  last_checked=$inspected
  if [ "$n" -eq 0 ]; then
    echo "NOT_RUN: 추적 파일 0개 — 스캔 무효 (P20 · 대상을 못 찾은 것이지 깨끗한 것이 아니다)"
    return 2
  fi
  [ "$invalid" -eq 0 ] || return 2
  [ "$bad" -eq 0 ] && echo "PASS: 추적 파일 ${n}개 검사, 위반 0건"
  return "$bad"
}

# ── history (D1) ─────────────────────────────────────────────────────────────
# rev-list --objects 는 동일 blob에 대표 경로 하나만 붙인다. 경로별 정책을 적용하려면
# 모든 도달 가능 commit tree를 별도로 열거해야 안전 확장자 alias가 PII 경로를 숨기지 못한다.
append_commit_tree_pairs() {
  # append_commit_tree_pairs <commit> <destination>
  local rev="$1" destination="$2" tree="$TMP_ROOT/history-tree"
  local record meta type sha raw_path lower kind forbidden display
  if ! git ls-tree -rz --full-tree "$rev" > "$tree" 2>/dev/null; then
    echo "NOT_RUN: 도달 가능 commit tree를 완전히 읽지 못했다: $rev"; return 2
  fi
  while IFS= read -r -d '' record; do
    meta=${record%%$'\t'*}; raw_path=${record#*$'\t'}
    if [ "$meta" = "$record" ] || ! IFS=' ' read -r _ type sha <<< "$meta" \
       || [ "$type" != blob ] || [ -z "$sha" ]; then
      echo "NOT_RUN: commit tree의 blob-경로 항목이 불완전하다: $rev"; return 2
    fi
    forbidden=0; is_forbidden_path "$raw_path" && forbidden=1
    lower=$(printf '%s' "$raw_path" | tr '[:upper:]' '[:lower:]'); kind=other
    case "$lower" in *.csv) kind=csv ;; *.tsv) kind=tsv ;; *.sql) kind=sql ;; esac
    display=$(safe_display_path "$raw_path") || {
      echo "NOT_RUN: history 경로를 안전하게 표시하지 못했다: $sha"; return 2;
    }
    printf '%s\t%s\t%s\t%s\n' "$sha" "$forbidden" "$kind" "$display" >> "$destination" \
      || { echo "NOT_RUN: history blob-경로를 기록하지 못했다"; return 2; }
  done < "$tree"
}

collect_history_inventory() {
  # collect_history_inventory <object-ids> <blob-path-pairs>
  local ids="$1" pairs="$2" objects="$TMP_ROOT/history-objects"
  local revisions="$TMP_ROOT/history-revisions" raw="$TMP_ROOT/history-pairs-raw" rev
  if ! git rev-list --all --reflog --objects > "$objects" 2>/dev/null \
     || ! git rev-list --all --reflog > "$revisions" 2>/dev/null; then
    echo "NOT_RUN: git rev-list 실패 — 기록을 읽지 못했다 (스캔 무효)"; return 2
  fi
  if ! awk '{ print $1 }' "$objects" | LC_ALL=C sort -u > "$ids"; then
    echo "NOT_RUN: 도달 가능 객체 목록을 정규화하지 못했다"; return 2
  fi
  : > "$raw" || { echo "NOT_RUN: history 경로 목록을 만들지 못했다"; return 2; }
  while IFS= read -r rev; do
    [ -n "$rev" ] || continue
    append_commit_tree_pairs "$rev" "$raw" || return 2
  done < "$revisions"
  if ! LC_ALL=C sort -u "$raw" > "$pairs"; then
    echo "NOT_RUN: history blob-경로 목록을 정규화하지 못했다"; return 2
  fi
}

scan_history() {
  local ids="$TMP_ROOT/history-ids" pairs="$TMP_ROOT/history-pairs"
  local info="$TMP_ROOT/history-info" paths="$TMP_ROOT/history-paths"
  local pii_paths="$TMP_ROOT/history-pii-paths" content="$TMP_ROOT/history-blob"
  local bad=0 invalid=0 blobs=0 inspected=0 sha info_sha type sz path candidate
  local pii_rc csv_seen tsv_seen sql_seen forbidden kind
  collect_history_inventory "$ids" "$pairs" || return 2
  if ! git cat-file --batch-check='%(objectname) %(objecttype) %(objectsize)' \
       < "$ids" > "$info" 2>/dev/null; then
    echo "NOT_RUN: 도달 가능 Git 객체 메타데이터 배치 읽기에 실패했다"; return 2
  fi
  exec 3< "$info"
  while IFS= read -r sha; do
    [ -n "$sha" ] || continue
    if ! IFS=' ' read -r info_sha type sz <&3 \
       || [ "$info_sha" != "$sha" ] || [ -z "$type" ] || [ -z "$sz" ]; then
      echo "NOT_RUN: 도달 가능 Git 객체 메타데이터가 불완전하다: $sha"; invalid=1; continue
    fi
    [ "$type" = blob ] || continue
    blobs=$((blobs + 1)); path=""; csv_seen=0; tsv_seen=0; sql_seen=0
    : > "$pii_paths"
    awk -F '\t' -v want="$sha" '$1 == want { print $2 "\t" $3 "\t" $4 }' \
      "$pairs" > "$paths" || { invalid=1; continue; }
    while IFS=$'\t' read -r forbidden kind candidate; do
      [ -n "$path" ] || path="$candidate"
      if [ "$forbidden" -eq 1 ]; then
        echo "FAIL: 기록에 산출물·데이터 경로가 남아 있음: $candidate ($sha)"; bad=1
      fi
      case "$kind" in
        csv) [ "$csv_seen" -eq 1 ] || { printf '%s\t%s\n' "$kind" "$candidate" >> "$pii_paths"; csv_seen=1; } ;;
        tsv) [ "$tsv_seen" -eq 1 ] || { printf '%s\t%s\n' "$kind" "$candidate" >> "$pii_paths"; tsv_seen=1; } ;;
        sql) [ "$sql_seen" -eq 1 ] || { printf '%s\t%s\n' "$kind" "$candidate" >> "$pii_paths"; sql_seen=1; } ;;
      esac
    done < "$paths"
    case "$sz" in
      ''|*[!0-9]*) echo "NOT_RUN: 기록 blob 크기를 읽지 못했다: $sha"; invalid=1; continue ;;
    esac
    if [ "$sz" -gt "$MAX_BYTES" ]; then
      echo "FAIL: 기록에 ${MAX_BYTES} 바이트 초과 blob 이 남아 있음: ${path:-<경로없음>} (${sz} 바이트, $sha)"; bad=1
    elif [ -s "$pii_paths" ]; then
      if ! git cat-file blob "$sha" > "$content" 2>/dev/null; then
        echo "NOT_RUN: 개인정보 후보 history blob을 읽지 못했다: $sha"; invalid=1; continue
      fi
      while IFS=$'\t' read -r kind candidate; do
        pii_rc=0; scan_pii_content "$candidate" "$content" "$sha" "$kind" || pii_rc=$?
        [ "$pii_rc" -eq 1 ] && bad=1
        [ "$pii_rc" -eq 2 ] && invalid=1
      done < "$pii_paths"
    fi
    inspected=$((inspected + 1))
  done < "$ids"
  if IFS= read -r _ <&3; then echo "NOT_RUN: Git 객체 메타데이터가 객체 목록보다 많다"; invalid=1; fi
  exec 3<&-; last_checked=$inspected
  if [ "$blobs" -eq 0 ]; then echo "NOT_RUN: blob 을 한 개도 읽지 못했다 (스캔 무효)"; return 2; fi
  if [ "$invalid" -ne 0 ] || [ "$inspected" -ne "$blobs" ]; then return 2; fi
  [ "$bad" -eq 0 ] && echo "PASS: 기록 전량 blob ${blobs}개 검사, 크기·경로·개인정보 위반 0건"
  return "$bad"
}

# ── pii (D2) ─────────────────────────────────────────────────────────────────
# 후보자 개인정보 '컬럼 이름 조합' 으로 판정한다. 값 모양이 아니라 스키마를 본다 —
# 이름·전화번호는 형식이 자유로워 값 모양으로는 오탐이 폭증한다.
#
# 오탐을 막는 두 조건(둘 다 만족해야 차단):
#   ① 개인정보 컬럼 낱말이 **2종 이상**
#   ② 실제 **데이터를 담은** 형태다 — CSV 는 헤더 밑에 데이터 행이 1줄 이상,
#      SQL 은 INSERT/VALUES/COPY 같은 데이터 적재문이 있다.
# 그래서 `CREATE TABLE candidates(name, email)` 같은 **스키마 정의는 통과**한다.
# 스키마는 정상 마이그레이션이고, 그것까지 막으면 정상 개발이 멈춘다.
# ⚠️ 변수 이름에 TOKEN 을 쓰면 안 된다 — 기존 자격증명 패턴(.secret-patterns.default:9)이
# 그 이름만 보고 이 줄을 비밀로 잡는다(2026-08-12 실측: pre-commit 이 이 커밋을 막았다).
# 검사를 약화시키는 대신 이름을 고친다.
PII_COLUMN_WORDS='name|email|e_mail|mail|phone|mobile|tel|school|univ|university|profile_url|linkedin|resume|birth|이름|이메일|전화|휴대폰|학교|생년|프로필'

pii_word_count() {
  tr '[:upper:]' '[:lower:]' | grep -oE "$PII_COLUMN_WORDS" | sort -u | awk 'END { print NR + 0 }'
}

is_pii_path() {
  local lf; lf=$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]')
  case "$lf" in *.csv|*.tsv|*.sql) return 0 ;; *) return 1 ;; esac
}

scan_pii_content() {
  # scan_pii_content <path> <content-file> [history-blob-fingerprint] [known-format]
  # 현재 파일과 history가 이 한 함수를 공유한다. 실제 값은 어느 출력에도 쓰지 않는다.
  local path="$1" content="$2" fingerprint="${3:-}" format="${4:-}"
  local lf display header rows hits shape meta
  if [ -z "$format" ]; then
    lf=$(printf '%s' "$path" | tr '[:upper:]' '[:lower:]')
    case "$lf" in *.csv) format=csv ;; *.tsv) format=tsv ;; *.sql) format=sql ;; *) return 0 ;; esac
    display=$(safe_display_path "$path") || return 2
  else
    display="$path"
  fi
  case "$format" in
    csv|tsv)
      header=$(sed -n '1p' "$content")
      hits=$(printf '%s' "$header" | pii_word_count)
      rows=$(awk 'NR > 1 && $0 ~ /[^[:space:],]/ { n++ } END { print n + 0 }' "$content")
      [ "$hits" -ge 2 ] && [ "$rows" -ge 1 ] || return 0
      shape="표 데이터 ${rows}행"
      ;;
    sql)
      hits=$(pii_word_count < "$content")
      if [ "$hits" -lt 2 ] \
         || ! grep -qiE '\b(insert[[:space:]]+into|values[[:space:]]*\(|copy[[:space:]]+.*from)' "$content"; then
        return 0
      fi
      shape="INSERT/VALUES/COPY 적재문"
      ;;
    *) return 2 ;;
  esac
  if [ -n "$fingerprint" ]; then meta=" · blob $fingerprint"; else meta=""; fi
  printf 'FAIL: 후보자 개인정보 내용: %s%s · 개인정보 컬럼 %s종 · %s\n' \
    "$display" "$meta" "$hits" "$shape"
  return 1
}

scan_pii() {
  local n=0 inspected=0 files=0 bad=0 invalid=0 f content="$TMP_ROOT/current-blob" pii_rc
  while IFS= read -r -d '' f; do
    n=$((n + 1))
    if ! is_pii_path "$f"; then inspected=$((inspected + 1)); continue; fi
    files=$((files + 1))
    if ! git cat-file blob ":$f" > "$content" 2>/dev/null; then
      echo "NOT_RUN: 추적 개인정보 후보 blob을 읽지 못했다: $f"; invalid=1; continue
    fi
    pii_rc=0
    scan_pii_content "$f" "$content" || pii_rc=$?
    [ "$pii_rc" -eq 1 ] && bad=1
    [ "$pii_rc" -eq 2 ] && invalid=1
    inspected=$((inspected + 1))
  done < <(git ls-files -z)
  last_checked=$inspected
  if [ "$n" -eq 0 ]; then
    echo "NOT_RUN: 추적 파일 0개 — 스캔 무효 (P20)"; return 2
  fi
  if [ "$invalid" -ne 0 ] || [ "$inspected" -ne "$n" ]; then return 2; fi
  [ "$bad" -eq 0 ] && echo "PASS: csv/tsv/sql ${files}개 검사(추적 ${n}개 중), 개인정보 적재 0건"
  return "$bad"
}

run() {
  local rc=0
  last_checked=0
  case "$1" in
    tracked) scan_tracked || rc=$? ;;
    history) scan_history || rc=$? ;;
    pii)     scan_pii     || rc=$? ;;
  esac
  checked_total=$((checked_total + last_checked))
  # NOT_RUN(2)은 FAIL(1)보다 강하게 전파한다 — 스캔이 성립하지 않은 것을 통과로 접지 않는다.
  if [ "$rc" -eq 2 ]; then fail=2
  elif [ "$rc" -ne 0 ] && [ "$fail" -ne 2 ]; then fail=1
  fi
}

if [ "$MODE" = all ]; then
  run tracked; run history; run pii
else
  run "$MODE"
fi

printf 'CHECKED: %d\n' "$checked_total"
exit "$fail"
