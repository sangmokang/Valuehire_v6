#!/usr/bin/env bash
# acceptance-0-2의 복구 가능 객체 판정을 합성 저장소에서 검증한다.
set -euo pipefail

# 합성 fixture가 호출자 셸의 실제 패턴 경로를 물려받으면 같은 시험이 환경마다 달라진다.
# 자동 훅뿐 아니라 직접 실행도 반드시 아래 fixture의 .secret-patterns만 사용한다.
unset SECRET_PATTERNS_FILE
# pre-push가 넘기는 저장소 위치를 물려받으면 합성 git 명령이 실제 저장소를 바꾼다.
unset GIT_DIR GIT_INDEX_FILE GIT_OBJECT_DIRECTORY GIT_WORK_TREE GIT_COMMON_DIR GIT_ALTERNATE_OBJECT_DIRECTORIES

ROOT=$(git rev-parse --show-toplevel)
TMP_ROOT=$(mktemp -d)

cleanup() {
  case "$TMP_ROOT" in
    "${TMPDIR:-/tmp}"/*|/tmp/*|/private/tmp/*|/var/folders/*) rm -rf -- "$TMP_ROOT" ;;
    *) printf 'BLOCKED: 임시 경로 정리 거부: %s\n' "$TMP_ROOT" >&2 ;;
  esac
}
trap cleanup EXIT
trap 'cleanup; trap - EXIT; exit 143' TERM
trap 'cleanup; trap - EXIT; exit 130' INT
trap 'cleanup; trap - EXIT; exit 129' HUP

REPO="$TMP_ROOT/repo"
git init -q "$REPO"
cp "$ROOT/verify.sh" "$REPO/verify.sh"
mkdir -p "$REPO/scripts"
cp "$ROOT/scripts/acceptance-0-2.sh" "$REPO/scripts/acceptance-0-2.sh"

SYNTHETIC_LITERAL='LOCAL-GATE-SYNTHETIC-LITERAL-42'
printf '%s\n' "$SYNTHETIC_LITERAL" > "$REPO/.secret-patterns"
printf '%s\n' '.secret-patterns' > "$REPO/.gitignore"

git -C "$REPO" add verify.sh scripts/acceptance-0-2.sh .gitignore
git -C "$REPO" -c user.email=fixture@example.invalid -c user.name=fixture \
  commit -qm 'fixture'

fail=0
checked=0

run_case() {
  local name=$1
  local expected_rc=$2
  local expected_pattern=$3
  shift 3

  local output
  local rc=0
  output="$(cd "$REPO" && "$@" 2>&1)" || rc=$?
  checked=$((checked + 1))
  printf '[%s] exit=%s expected=%s\n%s\n' "$name" "$rc" "$expected_rc" "$output"

  if [ "$rc" -ne "$expected_rc" ]; then
    printf 'FAIL: %s 종료 성적 불일치\n' "$name"
    fail=1
  fi
  if [ -n "$expected_pattern" ] && ! printf '%s\n' "$output" | grep -Fq "$expected_pattern"; then
    printf 'FAIL: %s 필수 판정 문구 누락: %s\n' "$name" "$expected_pattern"
    fail=1
  fi
}

run_case no-unreachable 0 '' bash scripts/acceptance-0-2.sh

printf '%s\n' 'harmless recovery object' | git -C "$REPO" hash-object -w --stdin >/dev/null
run_case harmless-unreachable 0 '' bash scripts/acceptance-0-2.sh

run_case endstate-requires-zero 1 'unreachable 객체 1건 잔존' \
  env ACCEPTANCE_ENDSTATE=1 bash scripts/acceptance-0-2.sh

printf '%s\n' "$SYNTHETIC_LITERAL" | git -C "$REPO" hash-object -w --stdin >/dev/null
run_case secret-unreachable 1 '복구 가능 blob에 리터럴 잔존' \
  bash scripts/acceptance-0-2.sh

printf 'CHECKED: %s\n' "$checked"
if [ "$fail" -ne 0 ]; then
  exit 1
fi
printf '%s\n' 'PASS: 무해한 복구 객체 허용·비밀 객체 차단·최종 정리 0개 조건 보존'
