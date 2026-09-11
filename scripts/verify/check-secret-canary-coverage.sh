#!/usr/bin/env bash
# check-secret-canary-coverage.sh — 비밀 규칙 하나하나가 **양성 카나리로 실제 덮이는가**.
#
# 왜 필요한가 (2026-09-11 Codex 적대검증 C2):
#   탐지 회귀 검사(check-secret-detection-regression.sh)는 "기준에서 잡히던 값이 계속
#   잡히는가"만 본다. 그래서 **어떤 카나리도 대표하지 않는 규칙**은 통째로 사라져도
#   검출 집합이 변하지 않아 조용히 통과한다. 실측: 규칙 25개 중 카나리에 연결된 것은
#   4개뿐이었고, 나머지 21개는 삭제해도 회귀 검사가 초록이었다(ASIA 규칙 실증).
#
# 판정: manifest(capability → 카나리 → 그 카나리가 잡아야 하는 규칙 id)를 정본으로 두고
#   ① 규칙마다 id 가 선언되어 있는가        (id 없는 규칙은 manifest 에 올릴 수 없다)
#   ② 모든 규칙 id 가 manifest 에 적혀 있는가 (새 규칙 + 카나리 없음 → 차단)
#   ③ manifest 가 가리키는 규칙 id·카나리가 실제로 존재하는가 (규칙 삭제 → 차단)
#   ④ **적힌 대로 실제로 잡히는가**를 실행으로 확인한다 (match-never 로 바꾸면 차단)
#   ④ 가 핵심이다. ①~③ 만이면 manifest 에 "덮는다"고 적어 두기만 해도 통과한다.
#
# 입력은 **커밋될 내용(인덱스)** 이다. 작업트리를 직접 읽지 않는다 —
#   지운 것을 스테이징하고 화면 파일만 되돌리면 통과하는 우회가 열린다(C3 와 같은 함정).
#
# 계약: exit 0 (전 규칙 커버) | exit 1 (커버 공백·manifest 불일치) | exit 2 (검사 불가 · fail-closed)
#
# --oracle-selftest: 같은 입력을 **생산 스캐너 verify.sh** 로도 판정해 두 경로를 대조한다.
#   한계: 두 경로 모두 같은 정규식 엔진(grep -Ei)과 같은 규칙 파일을 쓴다. 규칙 자체가
#   틀렸거나 엔진이 같은 방식으로 틀리면 이 대조는 그것을 보지 못한다. 이 검사가 드러내는
#   것은 **적재·정제·배관의 차이**(주석 절단, CRLF, 파일 합치기 순서)로 생기는 공통모드다.
set -uo pipefail

PATTERNS_FILE=.secret-patterns.default
FIX_DIR=scripts/verify/fixtures/secret-canaries
POS_FILE="$FIX_DIR/positive.txt"
NEG_FILE="$FIX_DIR/negative.txt"
MANIFEST="$FIX_DIR/manifest.txt"
SCANNER=verify.sh

die() { printf 'FAIL: %s (fail-closed)\n' "$1"; echo "CHECKED: 0"; exit 2; }
block() { printf 'BLOCKED: %s\n' "$1"; }

MODE=cover
case "${1:-}" in
  '') ;;
  --oracle-selftest) MODE=oracle ;;
  *) die "알 수 없는 인자: $1 (사용법: check-secret-canary-coverage.sh [--oracle-selftest])" ;;
esac

command -v git >/dev/null 2>&1 || die "git 을 찾을 수 없다"
REPO=$(git rev-parse --show-toplevel 2>/dev/null) || die "git 저장소가 아니다"
cd "$REPO" || die "저장소 루트로 이동할 수 없다"

TMP=$(mktemp -d) || die "임시 디렉터리를 만들 수 없다"
trap 'rm -rf "$TMP"' EXIT
for f in rules claimed one err; do
  : > "$TMP/$f" || die "작업 파일을 열 수 없다 ($TMP/$f)"
done

# 커밋될 내용만 읽는다. 작업트리 직접 읽기는 금지다 — 지운 것을 스테이징하고 화면
# 파일만 되돌리면 통과하는 우회가 열린다.
read_indexed() {  # <경로> <출력>
  if ! git ls-files --error-unmatch -- "$1" >/dev/null 2>&1; then
    if git rev-parse --verify --quiet HEAD >/dev/null && git cat-file -e "HEAD:$1" 2>/dev/null; then
      block "$1 이 인덱스에서 사라졌다 — 커버리지 판정의 입력이 없다."
      echo "CHECKED: 0"; exit 1
    fi
    die "$1 이 추적되지 않는다"
  fi
  # 오류 메시지를 버리지 않는다 — 무엇 때문에 못 읽었는지가 복구의 출발점이다.
  if ! git show ":$1" > "$2" 2>"$TMP/err"; then
    die "인덱스에서 $1 을 읽지 못했다: $(head -1 "$TMP/err")"
  fi
}

# 고정물은 <설명>\t<앞>\t<뒤> 로 쪼개 두었다(파일 자신이 비밀 스캔에 걸리지 않게).
assemble() {  # <원본> <출력>
  : > "$2" || die "작업 파일을 열 수 없다 ($2)"
  local desc a b
  while IFS=$'\t' read -r desc a b; do
    case "${desc:-}" in ''|\#*) continue ;; esac
    [ -n "${a:-}" ] || continue
    printf '%s\t%s%s\n' "$desc" "$a" "${b:-}" >> "$2" || die "카나리 조립 실패"
  done < "$1"
  [ -s "$2" ] || die "카나리가 0건이다 — 검사 대상 0개는 합격이 아니다 ($1)"
}

read_indexed "$PATTERNS_FILE" "$TMP/patterns.raw"
read_indexed "$POS_FILE"      "$TMP/pos.raw"
assemble "$TMP/pos.raw" "$TMP/pos"

# ── AC-4 독립 oracle — 같은 입력을 생산 스캐너로도 판정해 대조한다 ────────────
# 왜: 이 검사기와 verify.sh 가 규칙 파일을 각자 정제한다. 정제가 갈리면 두 판정기가
#     서로 다른 규칙 집합을 보게 되고, 이 저장소는 2026-08-07 에 그것으로 이미 한 번 갈렸다.
# 대조 대상: "이 값이 비밀로 잡히는가"를 ① 이 검사기의 적재 경로 ② verify.sh 의 적재·
#     스캔 경로로 각각 구해 일치를 요구한다. 어긋나면 둘 중 하나가 규칙을 잘못 읽고 있다.
run_oracle() {
  read_indexed "$NEG_FILE" "$TMP/neg.raw"
  read_indexed "$SCANNER"  "$TMP/scanner.sh"
  assemble "$TMP/neg.raw" "$TMP/neg"

  tr -d '\r' < "$TMP/patterns.raw" | grep -vE '^[[:space:]]*(#|$)' > "$TMP/clean" \
    || die "패턴 정제 실패"
  [ -s "$TMP/clean" ] || die "유효 규칙이 0개다 — 검사 대상 0개는 합격이 아니다"

  ORA="$TMP/oracle"
  mkdir -p "$ORA" || die "oracle 작업 디렉터리를 만들 수 없다"
  cp "$TMP/scanner.sh" "$ORA/verify.sh" || die "스캐너 사본 설치 실패"
  (
    cd "$ORA" || exit 3
    unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE GIT_OBJECT_DIRECTORY \
          GIT_ALTERNATE_OBJECT_DIRECTORIES GIT_COMMON_DIR GIT_PREFIX GIT_QUARANTINE_PATH
    git init -q . >/dev/null 2>&1
  ) || die "oracle 저장소 초기화 실패"

  # B 경로: 생산 스캐너를 그대로 돌린다. exit 1 = 잡힘 · exit 0 = 안 잡힘 · 그 밖 = 실행 불가.
  # 실행 불가(2)를 "안 잡힘"으로 접으면 구현 0줄에서도 초록이 난다 — die 로 끊는다.
  scan_by_production() {  # <값> → 0 잡힘 / 1 안 잡힘
    printf '%s\n' "$1" > "$ORA/canary.txt" || die "oracle 입력 파일을 쓸 수 없다"
    local rc=0
    (
      cd "$ORA" || exit 3
      unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE GIT_OBJECT_DIRECTORY \
            GIT_ALTERNATE_OBJECT_DIRECTORIES GIT_COMMON_DIR GIT_PREFIX GIT_QUARANTINE_PATH
      git add canary.txt >/dev/null 2>&1 || exit 3
      SECRET_PATTERNS_FILE="$TMP/patterns.raw" bash verify.sh >/dev/null 2>&1
    ) || rc=$?
    case "$rc" in
      0) return 1 ;;
      1) return 0 ;;
      *) die "생산 스캐너를 실행하지 못했다 (verify.sh exit=$rc) — 실행 불가를 판정으로 세지 않는다" ;;
    esac
  }
  scan_by_self() {  # <값> → 0 잡힘 / 1 안 잡힘
    local rc=0
    printf '%s\n' "$1" | grep -qEi -f "$TMP/clean" || rc=$?
    [ "$rc" -gt 1 ] && die "패턴 실행 오류 (grep exit=$rc) — 정규식이 깨졌을 수 있다"
    return "$rc"
  }

  local n=0 agree=0 bad=0 desc val a b expect side
  for side in pos neg; do
    if [ "$side" = pos ]; then expect=0; else expect=1; fi
    while IFS=$'\t' read -r desc val; do
      [ -n "${val:-}" ] || continue
      n=$((n + 1))
      a=0; scan_by_self "$val" || a=$?
      b=0; scan_by_production "$val" || b=$?
      if [ "$a" -eq "$b" ]; then
        agree=$((agree + 1))
        if [ "$a" -ne "$expect" ]; then
          block "두 경로가 일치하지만 기대와 다르다: '$desc' (양성은 잡혀야 하고 음성은 안 잡혀야 한다)"
          bad=1
        fi
      else
        block "판정이 갈렸다: '$desc' — 이 검사기=$a · 생산 스캐너=$b (0=잡힘 · 1=안 잡힘)"
        bad=1
      fi
    done < "$TMP/$side"
  done
  [ "$n" -gt 0 ] || die "대조 대상이 0건이다 — 검사 대상 0개는 합격이 아니다"
  if [ "$bad" -ne 0 ]; then
    printf '         두 경로가 같은 규칙 파일을 다르게 읽고 있다. 정제 방식을 맞춰라.\n'
    printf 'CHECKED: %d\n' "$n"
    exit 1
  fi
  printf 'PASS: 독립 oracle 일치 %d/%d\n' "$agree" "$n"
  printf 'CHECKED: %d\n' "$n"
  exit 0
}

if [ "$MODE" = oracle ]; then
  run_oracle
fi

# 명부(mechanism-registry)가 이 배선을 이름으로 지목한다. 이름을 지우면 명부 검사가
# 빨개진다 — manifest 를 안 읽는 판본으로 조용히 되돌리는 길을 막는다.
read_manifest() { read_indexed "$MANIFEST" "$TMP/manifest.raw"; }
read_manifest

# ── 규칙 id 추출 ─────────────────────────────────────────────────────────────
# 형식: 유효 규칙 줄 바로 앞 주석에 `# @id: <슬러그>` 가 있어야 한다.
# id 가 없으면 manifest 에 올릴 수 없고, 따라서 카나리 없는 규칙이 조용히 들어오지 못한다.
awk '
  /^[[:space:]]*#[[:space:]]*@id:[[:space:]]*/ {
    id = $0; sub(/^[[:space:]]*#[[:space:]]*@id:[[:space:]]*/, "", id)
    sub(/[[:space:]]+$/, "", id); pending = id; next
  }
  /^[[:space:]]*(#|$)/ { next }
  {
    line = $0; sub(/\r$/, "", line)
    printf "%s\t%s\n", (pending == "" ? "<NO-ID>" : pending), line
    pending = ""
  }
' "$TMP/patterns.raw" > "$TMP/rules" || die "규칙 id 추출 실패"

rule_total=$(awk 'NF{c++} END{print c+0}' "$TMP/rules")
[ "$rule_total" -gt 0 ] || die "유효 규칙이 0개다 — 검사 대상 0개는 합격이 아니다"

fail=0; checked=0

if awk -F'\t' '$1 == "<NO-ID>"' "$TMP/rules" | grep -q .; then
  block "id 가 선언되지 않은 규칙이 있다 — 규칙 줄 바로 앞에 '# @id: <슬러그>' 를 달아라."
  awk -F'\t' '$1 == "<NO-ID>" {printf "         id 없음: %.70s\n", $2}' "$TMP/rules"
  fail=1
fi
dup=$(cut -f1 "$TMP/rules" | LC_ALL=C sort | uniq -d)
if [ -n "$dup" ]; then
  block "규칙 id 가 중복됐다 — 하나가 다른 하나의 커버리지를 가린다."
  printf '         중복 id: %s\n' "$dup"
  fail=1
fi

canary_value() {  # <설명> → 조립된 값
  awk -F'\t' -v d="$1" '$1 == d {print $2; found=1; exit} END{if(!found) exit 1}' "$TMP/pos"
}
rule_pattern() {  # <id> → 규칙 본문
  awk -F'\t' -v i="$1" '$1 == i {print $2; found=1; exit} END{if(!found) exit 1}' "$TMP/rules"
}

# ── manifest 대조 ────────────────────────────────────────────────────────────
# 형식: <capability>\t<카나리 설명>\t<규칙 id 쉼표목록>\t<묶은 근거>
while IFS=$'\t' read -r cap desc ids why; do
  case "${cap:-}" in ''|\#*) continue ;; esac
  rows=$(( ${rows:-0} + 1 ))
  if [ -z "${desc:-}" ] || [ -z "${ids:-}" ] || [ -z "${why:-}" ]; then
    block "manifest 항목에 빈 칸이 있다 (capability=$cap) — 네 칸(capability·카나리·규칙 id·근거) 전부 필요하다."
    fail=1; continue
  fi
  if ! val=$(canary_value "$desc"); then
    block "manifest 가 가리키는 카나리가 고정물에 없다: '$desc' (capability=$cap)"
    fail=1; continue
  fi
  ids_sp=$(printf '%s' "$ids" | tr ',' ' ')
  for id in $ids_sp; do
    checked=$((checked + 1))
    printf '%s\n' "$id" >> "$TMP/claimed" || die "결과 기록 실패"
    if ! pat=$(rule_pattern "$id"); then
      block "manifest 가 없는 규칙 id 를 가리킨다: '$id' (capability=$cap) — 규칙이 지워졌는가?"
      fail=1; continue
    fi
    printf '%s\n' "$pat" > "$TMP/one" || die "작업 파일을 열 수 없다"
    rc=0
    printf '%s\n' "$val" | grep -qEi -f "$TMP/one" || rc=$?
    if [ "$rc" -gt 1 ]; then
      die "패턴 실행 오류 (grep exit=$rc · 규칙 id=$id) — 정규식이 깨졌을 수 있다"
    elif [ "$rc" -ne 0 ]; then
      block "manifest 는 덮는다고 적었는데 실제로는 안 잡힌다: 규칙 '$id' ← 카나리 '$desc'"
      fail=1
    fi
  done
done < "$TMP/manifest.raw"

[ "${rows:-0}" -gt 0 ] || die "manifest 항목이 0건이다 — 검사 대상 0개는 합격이 아니다"

LC_ALL=C sort -u -o "$TMP/claimed" "$TMP/claimed" || die "집합 정렬 실패"
while IFS=$'\t' read -r id pat; do
  [ -n "$id" ] || continue
  [ "$id" = "<NO-ID>" ] && continue
  if ! grep -qxF "$id" "$TMP/claimed"; then
    block "규칙 '$id' 를 덮는 카나리가 manifest 에 없다 — 이 규칙은 사라져도 아무도 모른다."
    fail=1
  fi
done < "$TMP/rules"

if [ "$fail" -ne 0 ]; then
  printf '         정본: %s · 고정물: %s\n' "$MANIFEST" "$POS_FILE"
  echo "CHECKED: $checked"
  exit 1
fi

printf 'PASS: 규칙 %d개 전부 카나리로 덮임 (N=%d)\n' "$rule_total" "$rule_total"
echo "CHECKED: $checked"
exit 0
