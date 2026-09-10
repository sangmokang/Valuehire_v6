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

fail=0

# 금지 경로 판정 — 훅(hooks/pre-commit)과 **같은 목록**이어야 한다.
# 목록이 갈라지면 한쪽만 막는 비대칭이 생기고, 그 비대칭이 훅 우회 습관을 만든다.
# 확장자 비교는 대소문자를 무시한다(dump.DB 가 통과한 2026-08-09 실측).
# HS-13.09 추가: *.packet.json(서치 패킷)·*.sent.json(발송 장부)은 후보자 이름·프로필 URL·
# 이메일을 그대로 담는다(D7). .gitignore 도 같은 두 패턴을 덮는다.
is_forbidden_path() {
  local lf; lf=$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]')
  case "$lf" in
    artifacts/*|*/artifacts/*|data/*|*/data/*|private-reviews/*|*/private-reviews/*|\
    *.db|*.db-*|*.sqlite|*.sqlite-*|*.sqlite3|*.sqlite3-*|*.jsonl|*.ndjson|*.parquet|\
    *.packet.json|*.sent.json)
      return 0 ;;
  esac
  return 1
}

# ── tracked ──────────────────────────────────────────────────────────────────
scan_tracked() {
  local n=0 bad=0 f sz
  while IFS= read -r -d '' f; do
    n=$((n + 1))
    if is_forbidden_path "$f"; then
      echo "FAIL: 산출물·데이터 경로가 추적됨: $f (P21 · 후보자 PII)"; bad=1; continue
    fi
    sz=$(git cat-file -s ":$f" 2>/dev/null) || sz=""
    case "$sz" in
      ''|*[!0-9]*) echo "FAIL: blob 크기를 읽지 못함: $f (fail-closed)"; bad=1; continue ;;
    esac
    if [ "$sz" -gt "$MAX_BYTES" ]; then
      echo "FAIL: ${MAX_BYTES} 바이트 초과: $f (${sz} 바이트)"; bad=1
    fi
  done < <(git ls-files -z)
  if [ "$n" -eq 0 ]; then
    echo "FAIL: 추적 파일 0개 — 스캔 무효 (P20 · 대상을 못 찾은 것이지 깨끗한 것이 아니다)"
    return 2
  fi
  [ "$bad" -eq 0 ] && echo "PASS: 추적 파일 ${n}개 검사, 위반 0건"
  return "$bad"
}

# ── history (D1) ─────────────────────────────────────────────────────────────
# 기존 CI '히스토리 전량 스캔' 스텝이 이미 도달 가능한 blob 을 경로까지 열거한다.
# 새 순회를 만들지 않고 같은 열거를 재사용한다(P12 · 회수 우선).
scan_history() {
  local objs bad=0 blobs=0 sha sz path count
  objs=$(mktemp) || { echo "FAIL: mktemp 실패 (fail-closed)"; return 2; }
  # shellcheck disable=SC2064
  trap "rm -f '$objs'" RETURN
  if ! git rev-list --all --reflog --objects > "$objs" 2>/dev/null; then
    echo "FAIL: git rev-list 실패 — 기록을 읽지 못했다 (스캔 무효)"; return 2
  fi
  count=$(awk '{print $1}' "$objs" | sort -u | wc -l | tr -d ' ')
  if [ "$count" -lt 2 ]; then
    echo "FAIL: 도달 가능 객체가 ${count}개 — 저장소를 제대로 읽지 못했다 (스캔 무효)"; return 2
  fi
  while IFS= read -r sha; do
    [ -z "$sha" ] && continue
    [ "$(git cat-file -t "$sha" 2>/dev/null)" = blob ] || continue
    blobs=$((blobs + 1))
    path=$(awk -v s="$sha" '$1==s {print $2; exit}' "$objs")
    if [ -n "$path" ] && is_forbidden_path "$path"; then
      echo "FAIL: 기록에 산출물·데이터 경로가 남아 있음: $path ($sha)"; bad=1; continue
    fi
    sz=$(git cat-file -s "$sha" 2>/dev/null) || sz=""
    case "$sz" in ''|*[!0-9]*) continue ;; esac
    if [ "$sz" -gt "$MAX_BYTES" ]; then
      echo "FAIL: 기록에 ${MAX_BYTES} 바이트 초과 blob 이 남아 있음: ${path:-<경로없음>} (${sz} 바이트, $sha)"
      bad=1
    fi
  done < <(awk '{print $1}' "$objs" | sort -u)
  if [ "$blobs" -eq 0 ]; then
    echo "FAIL: blob 을 한 개도 읽지 못했다 (스캔 무효)"; return 2
  fi
  [ "$bad" -eq 0 ] && echo "PASS: 기록 전량 blob ${blobs}개 검사, 크기·경로 위반 0건"
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

# 검토 기준선. "이 파일을 사람이 전수 확인했고 후보자 개인정보가 없다"를 **내용 해시**와
# 함께 적는다. 경로 예외나 기한 유예가 아니다 — 파일이 한 글자라도 바뀌면 해시가 어긋나
# 다시 차단된다. 규칙 자체는 어디서도 약해지지 않는다.
#
# 왜 필요한가: 이 규칙은 컬럼 이름 조합을 본다. 그런데 저장 프로시저는 정상적으로
# `insert into ... (client_name, candidate_name ...) values (...)` 를 담는다. 값이 진짜
# 사람 이름인지 자리표시자인지는 정규식으로 판별할 수 없다. 규칙을 좁히면 미탐이 늘고
# 그대로 두면 정상 마이그레이션이 영구히 막힌다. 그래서 판별을 사람에게 넘기되,
# 그 판단에 유효기간 대신 **내용 고정**을 건다.
REVIEWED_FILE=.data-exposure-reviewed

blob_sha() {
  if command -v sha256sum >/dev/null 2>&1; then
    git cat-file blob ":$1" 2>/dev/null | sha256sum | cut -d' ' -f1
  else
    git cat-file blob ":$1" 2>/dev/null | shasum -a 256 | cut -d' ' -f1
  fi
}

reviewed_reason() {
  [ -f "$REVIEWED_FILE" ] || return 1
  awk -F'\t' -v p="$1" -v s="$2" \
    '$1==s && $2==p {print $3; found=1} END{exit found?0:1}' "$REVIEWED_FILE"
}

# 원장이 썩는 것을 막는다 — 지워진 파일이나 바뀐 내용을 가리키는 항목은 그 자체가 불합격.
check_reviewed_ledger() {
  local bad=0 sha path reason
  [ -f "$REVIEWED_FILE" ] || return 0
  while IFS=$'\t' read -r sha path reason; do
    case "$sha" in ''|'#'*) continue ;; esac
    if [ -z "${path:-}" ] || [ -z "${reason:-}" ]; then
      echo "FAIL: 검토 기준선 형식 오류 — sha·경로·사유 세 칸이 필요하다: $sha"; bad=1; continue
    fi
    if ! git ls-files --error-unmatch "$path" >/dev/null 2>&1; then
      echo "FAIL: 검토 기준선의 죽은 항목 — 추적되지 않는 경로: $path"; bad=1; continue
    fi
    if [ "$(blob_sha "$path")" != "$sha" ]; then
      echo "FAIL: 검토 기준선이 낡았다 — $path 내용이 검토 이후 바뀌었다(재검토 필요)"; bad=1
    fi
  done < "$REVIEWED_FILE"
  return "$bad"
}

pii_word_count() { printf '%s' "$1" | tr 'A-Z' 'a-z' | grep -oE "$PII_COLUMN_WORDS" | sort -u | wc -l | tr -d ' '; }

scan_pii() {
  local n=0 files=0 bad=0 f lf header rows hits body
  while IFS= read -r -d '' f; do
    n=$((n + 1))
    lf=$(printf '%s' "$f" | tr 'A-Z' 'a-z')
    case "$lf" in *.csv|*.tsv) ;; *.sql) ;; *) continue ;; esac
    files=$((files + 1))
    case "$lf" in
      *.csv|*.tsv)
        header=$(git cat-file blob ":$f" 2>/dev/null | head -1)
        rows=$(git cat-file blob ":$f" 2>/dev/null | tail -n +2 | grep -cE '[^[:space:],]')
        hits=$(pii_word_count "$header")
        if [ "$hits" -ge 2 ] && [ "$rows" -ge 1 ]; then
          if reason=$(reviewed_reason "$f" "$(blob_sha "$f")"); then
            echo "REVIEWED: $f — $reason"
          else
            echo "FAIL: 후보자 개인정보로 보이는 표 데이터: $f (개인정보 컬럼 ${hits}종 · 데이터 ${rows}행)"
            bad=1
          fi
        fi
        ;;
      *.sql)
        body=$(git cat-file blob ":$f" 2>/dev/null)
        hits=$(pii_word_count "$body")
        if [ "$hits" -ge 2 ] && printf '%s' "$body" | grep -qiE '\b(insert[[:space:]]+into|values[[:space:]]*\(|copy[[:space:]]+.*from)'; then
          if reason=$(reviewed_reason "$f" "$(blob_sha "$f")"); then
            echo "REVIEWED: $f — $reason"
          else
            echo "FAIL: 후보자 개인정보로 보이는 적재문: $f (개인정보 컬럼 ${hits}종 · INSERT/VALUES/COPY 포함)"
            bad=1
          fi
        fi
        ;;
    esac
  done < <(git ls-files -z)
  if [ "$n" -eq 0 ]; then
    echo "FAIL: 추적 파일 0개 — 스캔 무효 (P20)"; return 2
  fi
  check_reviewed_ledger || bad=1
  [ "$bad" -eq 0 ] && echo "PASS: csv/tsv/sql ${files}개 검사(추적 ${n}개 중), 개인정보 적재 0건"
  return "$bad"
}

run() {
  local rc=0
  case "$1" in
    tracked) scan_tracked || rc=$? ;;
    history) scan_history || rc=$? ;;
    pii)     scan_pii     || rc=$? ;;
  esac
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

exit "$fail"
