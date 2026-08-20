#!/usr/bin/env bash
# acceptance-semantic-mutations.sh — 인수 검사를 무력화하면 반드시 빨개지는가.
#
# 이 검사가 겨냥하는 사건(2026-08-21 사장님 지적):
#   scripts/acceptance-hs-a4.sh 의 본문을 통째로 `exit 0` 으로 바꿔도 CI 가 초록이었다.
#   검사의 존재(existence)만 봤고 검사의 의미(semantics)를 보지 않았기 때문이다.
#
# 여기서는 차단과 통과를 한 쌍으로 잰다.
#   차단 — 무력화한 사본 5종은 scripts/verify/run-acceptance.sh 가 전부 불합격시켜야 한다.
#   통과 — 손대지 않은 실제 인수 검사는 그대로 합격해야 한다(과잉 차단이면 그것도 결함).
#
# 원본 저장소를 건드리지 않는다. 사본은 mktemp 아래에서만 만들고 끝나면 상태를 대조한다.
set -uo pipefail

unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE GIT_OBJECT_DIRECTORY \
      GIT_ALTERNATE_OBJECT_DIRECTORIES GIT_COMMON_DIR GIT_PREFIX GIT_QUARANTINE_PATH

REPO=$(git rev-parse --show-toplevel 2>/dev/null) || {
  echo "NOT_RUN: git 저장소가 아니다"
  echo "CHECKED: 0"
  exit 2
}
cd "$REPO" || exit 2
RUNNER="$REPO/scripts/verify/run-acceptance.sh"
if [ ! -f "$RUNNER" ]; then
  echo "FAIL: 래퍼 판정기가 없다 — $RUNNER (fail-closed)"
  echo "CHECKED: 0"
  exit 2
fi

SNAPSHOT=$(git status --porcelain)
TMP=$(mktemp -d) || {
  echo "NOT_RUN: mktemp 실패"
  echo "CHECKED: 0"
  exit 2
}
trap 'ruby -rfileutils -e "FileUtils.remove_entry(ARGV[0]) if File.exist?(ARGV[0])" "$TMP"' EXIT

fail=0
checked=0

record() {
  local ok="$1" desc="$2" detail="$3"
  checked=$((checked + 1))
  if [ "$ok" -eq 0 ]; then
    printf 'PASS: %s — %s\n' "$desc" "$detail"
  else
    printf 'FAIL: %s — %s\n' "$desc" "$detail"
    fail=1
  fi
}

# ── 대상 목록: 검사 대상 0개는 합격이 아니다 ─────────────────────────────────
targets=()
while IFS= read -r f; do
  targets+=("$f")
done < <(git ls-files 'scripts/acceptance-*.sh' | LC_ALL=C sort)

if [ "${#targets[@]}" -lt 5 ]; then
  echo "FAIL: 인수 검사 대상이 ${#targets[@]}개 — 글로브가 비면 '전부 통과'가 되므로 불합격이다"
  echo "CHECKED: $checked"
  exit 1
fi
record 0 "대상 수집" "인수 검사 ${#targets[@]}개 (하한 5)"

# ── 무력화 5종. 어느 것도 래퍼를 통과해서는 안 된다 ──────────────────────────
write_mutant() {
  local kind="$1" path="$2"
  case "$kind" in
    exit-zero)  printf '#!/usr/bin/env bash\nexit 0\n' > "$path" ;;
    true-only)  printf '#!/usr/bin/env bash\ntrue\n' > "$path" ;;
    noop)       printf '#!/usr/bin/env bash\n: # no-op\n' > "$path" ;;
    empty)      printf '#!/usr/bin/env bash\n' > "$path" ;;
    echo-only)  printf '#!/usr/bin/env bash\necho "검사했습니다"\n' > "$path" ;;
    *)          return 1 ;;
  esac
}

for kind in exit-zero true-only noop empty echo-only; do
  blocked=0
  survivors=""
  for t in "${targets[@]}"; do
    mutant="$TMP/$(basename "$t")"
    write_mutant "$kind" "$mutant" || continue
    rc=0
    bash "$RUNNER" "$mutant" >/dev/null 2>&1 || rc=$?
    if [ "$rc" -ne 0 ]; then
      blocked=$((blocked + 1))
    else
      survivors="$survivors $(basename "$t")"
    fi
  done
  if [ "$blocked" -eq "${#targets[@]}" ]; then
    record 0 "무력화 차단: $kind" "${blocked}/${#targets[@]} 전부 불합격 처리"
  else
    record 1 "무력화 차단: $kind" "살아남은 사본:${survivors:- 없음} (${blocked}/${#targets[@]})"
  fi
done

# ── 통과 쪽: 손대지 않은 실제 인수 검사는 그대로 합격해야 한다 ───────────────
# 전량 실행은 CI 몫이다(중복 실행 비용). 여기서는 외부 의존이 없는 것 하나로 확인한다.
sample="scripts/acceptance-guard-global-skill-files.sh"
if [ -f "$sample" ]; then
  sample_rc=0
  bash "$RUNNER" "$sample" >/dev/null 2>&1 || sample_rc=$?
  if [ "$sample_rc" -eq 0 ]; then
    record 0 "정상 인수 검사 통과" "$(basename "$sample") exit=0 (과잉 차단 없음)"
  else
    record 1 "정상 인수 검사 통과" "$(basename "$sample") exit=$sample_rc — 래퍼가 정상 검사를 막는다"
  fi
else
  record 1 "정상 인수 검사 통과" "표본 없음 — $sample"
fi

# ── 래퍼 자신의 fail-closed ──────────────────────────────────────────────────
noarg_rc=0
bash "$RUNNER" >/dev/null 2>&1 || noarg_rc=$?
if [ "$noarg_rc" -ne 0 ]; then
  record 0 "래퍼 인자 없음 거부" "exit=$noarg_rc"
else
  record 1 "래퍼 인자 없음 거부" "exit=0 — 인자 없이도 합격이면 배선을 비워도 통과한다"
fi

missing_rc=0
bash "$RUNNER" "$TMP/does-not-exist.sh" >/dev/null 2>&1 || missing_rc=$?
if [ "$missing_rc" -ne 0 ]; then
  record 0 "래퍼 대상 없음 거부" "exit=$missing_rc"
else
  record 1 "래퍼 대상 없음 거부" "exit=0 — 없는 검사도 합격이면 파일을 지우면 통과한다"
fi

current=$(git status --porcelain)
if [ "$current" = "$SNAPSHOT" ]; then
  record 0 "원본 저장소 상태 불변" "before/after 동일"
else
  record 1 "원본 저장소 상태 불변" "변경 발생"
fi

printf 'CHECKED: %d\n' "$checked"
if [ "$fail" -eq 0 ]; then
  echo "VERDICT: PASS"
else
  echo "VERDICT: FAIL"
fi
exit "$fail"
