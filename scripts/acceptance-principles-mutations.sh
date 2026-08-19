#!/usr/bin/env bash
# acceptance-principles-mutations.sh — principles 강제기의 fail-closed 경계를 격리 검증한다.
set -uo pipefail

unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE GIT_OBJECT_DIRECTORY \
      GIT_ALTERNATE_OBJECT_DIRECTORIES GIT_COMMON_DIR GIT_PREFIX GIT_QUARANTINE_PATH

REPO=$(git rev-parse --show-toplevel 2>/dev/null) || {
  echo "NOT_RUN: git 저장소가 아니다"
  echo "CHECKED: 0"
  exit 2
}
SNAPSHOT=$(git -C "$REPO" status --porcelain)
TMP=$(mktemp -d) || {
  echo "NOT_RUN: mktemp 실패"
  echo "CHECKED: 0"
  exit 2
}
trap 'rm -rf "$TMP"' EXIT

fail=0
checked=0
NO_VERIFY=--no"-verify"

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

overlay_current() {
  local dst="$1" f
  for f in \
    docs/sot/principles.yaml \
    scripts/acceptance-principles-check.sh \
    scripts/acceptance-principles-mutations.sh \
    hooks/pre-commit \
    hooks/pre-push \
    .github/workflows/verify.yml; do
    mkdir -p "$dst/$(dirname "$f")"
    cp "$REPO/$f" "$dst/$f"
  done
}

git clone --quiet --no-hardlinks "$REPO" "$TMP/template" || {
  echo "NOT_RUN: 격리 template clone 실패"
  echo "CHECKED: 0"
  exit 2
}
overlay_current "$TMP/template"
git -C "$TMP/template" config user.name principles-mutation
git -C "$TMP/template" config user.email principles-mutation@example.invalid
git -C "$TMP/template" add docs/sot/principles.yaml \
  scripts/acceptance-principles-check.sh scripts/acceptance-principles-mutations.sh \
  hooks/pre-commit hooks/pre-push .github/workflows/verify.yml
# --allow-empty: template은 $REPO를 clone한 것이라 overlay_current가 복사하는 파일이
# 이미 마지막 커밋과 완전히 같을 수 있다(작업트리가 깨끗한 게 정상 상태다). 그럴 때
# "commit할 게 없다"는 git의 정상 동작(exit 1)을 오류로 착각하면 안 된다. 2026-08-19
# CI 실측: GitHub Actions는 run: 스텝을 bash -e로 실행해, 이 한 줄의 exit 1이 21개
# 시험 전부가 시작되기도 전에 스크립트 전체를 죽였다(로컬은 -e 없이 실행해 안 걸렸다).
git -C "$TMP/template" commit --quiet --allow-empty "$NO_VERIFY" -m fixture
git -C "$TMP/template" branch -M main

git init --quiet --bare "$TMP/with-baseline.git"
# init.defaultBranch가 실행 환경마다 다르다(로컬 macOS git은 main, GitHub Actions
# 러너는 master가 기본이었다 — 2026-08-19 CI 실측: 로컬 통과·서버 exit=127 재현).
# bare repo의 symbolic HEAD가 push하지 않은 기본 브랜치(예: master)를 계속 가리키면
# 그 뒤 clone이 "remote HEAD refers to nonexistent ref"로 조용히 빈 작업트리를 만든다.
# 환경변수에 기대지 않고 이 저장소들의 HEAD를 명시적으로 고정한다.
git -C "$TMP/with-baseline.git" symbolic-ref HEAD refs/heads/main
git -C "$TMP/template" remote set-url origin "$TMP/with-baseline.git"
git -C "$TMP/template" push --quiet -u origin main

cp -R "$TMP/template" "$TMP/no-baseline-source"
git -C "$TMP/no-baseline-source" rm --quiet docs/sot/principles.yaml
git -C "$TMP/no-baseline-source" commit --quiet "$NO_VERIFY" -m no-baseline
git init --quiet --bare "$TMP/no-baseline.git"
git -C "$TMP/no-baseline.git" symbolic-ref HEAD refs/heads/main
git -C "$TMP/no-baseline-source" remote set-url origin "$TMP/no-baseline.git"
git -C "$TMP/no-baseline-source" push --quiet -u origin main

new_case() {
  local name="$1" remote="${2:-$TMP/with-baseline.git}"
  git clone --quiet "$remote" "$TMP/$name"
  git -C "$TMP/$name" config user.name principles-mutation
  git -C "$TMP/$name" config user.email principles-mutation@example.invalid
}

mutate_yaml() {
  local dir="$1" ruby_body="$2"
  (
    cd "$dir" || exit 1
    ruby -rpsych -e '
      path = "docs/sot/principles.yaml"
      data = Psych.safe_load(File.read(path), permitted_classes: [], permitted_symbols: [], aliases: false)
      '"$ruby_body"'
      File.write(path, Psych.dump(data))
    '
  )
}

expect_checker() {
  local desc="$1" dir="$2" mode="$3" want_rc="$4" pattern="$5"
  local output rc=0 ok=0
  output=$(cd "$dir" && bash scripts/acceptance-principles-check.sh "$mode" 2>&1) || rc=$?
  if [ "$rc" -ne "$want_rc" ]; then
    ok=1
  elif [ -n "$pattern" ] && ! printf '%s\n' "$output" | grep -qF -- "$pattern"; then
    ok=1
  fi
  record "$ok" "$desc" "exit=$rc, expected=$want_rc, marker=${pattern:-<none>}"
  # 실패 원인을 잘라내지 않는다 — record는 요약만 찍어서, 로컬에서 재현되는데 CI에서만
  # 다르게 실패하는 상황을 진단할 방법이 없었다(2026-08-19 실측). 검사기 원본 출력을
  # 실패에만 들여쓰기로 첨부한다.
  if [ "$ok" -ne 0 ]; then
    printf '%s\n' "$output" | sed 's/^/    | /'
  fi
}

# 정상 구조 대조군. 전체 P1 판정과 달리 schema-only는 기록 구조만 판정한다.
new_case normal
expect_checker "정상 원칙표 schema-only" "$TMP/normal" --schema-only 0 "SCHEMA_OK"

new_case unknown
mutate_yaml "$TMP/unknown" 'data[0]["unexpected_field"] = "must fail"'
expect_checker "unknown field 추가" "$TMP/unknown" --schema-only 1 "UNKNOWN_FIELD"

new_case duplicate_field
perl -0pi -e 's/(  principle: "[^"]*"\n)/$1  principle: "duplicate"\n/' \
  "$TMP/duplicate_field/docs/sot/principles.yaml"
expect_checker "중복 필드" "$TMP/duplicate_field" --schema-only 1 "DUPLICATE_KEY"

new_case empty_principle
mutate_yaml "$TMP/empty_principle" 'data[0]["principle"] = ""'
expect_checker "빈 principle" "$TMP/empty_principle" --schema-only 1 "EMPTY_FIELD"

new_case empty_evidence
mutate_yaml "$TMP/empty_evidence" 'data[0]["evidence"] = ""'
expect_checker "빈 evidence" "$TMP/empty_evidence" --schema-only 1 "EMPTY_FIELD"

new_case empty_mechanism
mutate_yaml "$TMP/empty_mechanism" 'data[0]["mechanism_found"] = nil'
expect_checker "부분 상태의 빈 mechanism_found" "$TMP/empty_mechanism" --schema-only 1 "MECHANISM_REQUIRED"

new_case changed_id
mutate_yaml "$TMP/changed_id" 'data[0]["id"] = "P99"'
expect_checker "ID 변경" "$TMP/changed_id" --schema-only 1 "ID_SET_MISMATCH"

new_case bad_status
mutate_yaml "$TMP/bad_status" 'data[0]["status"] = "거의완전"'
expect_checker "계약 밖 status" "$TMP/bad_status" --schema-only 1 "STATUS_INVALID"

new_case broken_yaml
perl -0pi -e 's/principle: "[^"]*"/principle: "broken/' "$TMP/broken_yaml/docs/sot/principles.yaml"
expect_checker "깨진 따옴표" "$TMP/broken_yaml" --schema-only 1 "YAML_PARSE_ERROR"

new_case missing_mechanism
rm "$TMP/missing_mechanism/hooks/pre-commit"
expect_checker "mechanism 파일 삭제 + status 유지" "$TMP/missing_mechanism" --schema-only 1 "MECHANISM_PATH_MISSING"

new_case disconnected_mechanism
perl -0pi -e 's#hooks/pre-commit#hooks/pre_commit#g' \
  "$TMP/disconnected_mechanism/scripts/acceptance-hs-a4.sh"
expect_checker "verifier에서 mechanism 연결 제거" "$TMP/disconnected_mechanism" --schema-only 1 "MECHANISM_CHECK_DISCONNECTED"

new_case regression
mutate_yaml "$TMP/regression" 'data.find { |x| x["id"] == "P21" }["status"] = "부분"'
expect_checker "기준선 존재 + status 하락" "$TMP/regression" --full 1 "STATUS_REGRESSION"

new_case no_baseline "$TMP/no-baseline.git"
cp "$REPO/docs/sot/principles.yaml" "$TMP/no_baseline/docs/sot/principles.yaml"
git -C "$TMP/no_baseline" add docs/sot/principles.yaml
expect_checker "기준선 없음 명시" "$TMP/no_baseline" --full 1 "BASELINE_NOT_AVAILABLE"

expect_checker "정상 표의 P1 전체 미충족" "$TMP/normal" --full 1 "P1_UNMET"
expect_checker "정상 표의 pre-push 로컬 게이트" "$TMP/normal" --pre-push 0 "P1_LOCAL_GATE"

# pre-commit 고정 필수 파일: 삭제·rename 차단, 첫 도입 add 허용.
new_case precommit_delete
git -C "$TMP/precommit_delete" rm --quiet docs/sot/principles.yaml
pc_rc=0
(cd "$TMP/precommit_delete" && bash hooks/pre-commit >/dev/null 2>&1) || pc_rc=$?
if [ "$pc_rc" -ne 0 ]; then pc_ok=0; else pc_ok=1; fi
record "$pc_ok" "필수 파일 삭제 → pre-commit 차단" "exit=$pc_rc"

new_case precommit_rename
git -C "$TMP/precommit_rename" mv docs/sot/principles.yaml docs/sot/principles-renamed.yaml
pc_rc=0
(cd "$TMP/precommit_rename" && bash hooks/pre-commit >/dev/null 2>&1) || pc_rc=$?
if [ "$pc_rc" -ne 0 ]; then pc_ok=0; else pc_ok=1; fi
record "$pc_ok" "필수 파일 이름 변경 → pre-commit 차단" "exit=$pc_rc"

new_case precommit_add
cp "$TMP/precommit_add/docs/sot/principles.yaml" "$TMP/first-intro-principles.yaml"
cp "$TMP/precommit_add/scripts/acceptance-principles-check.sh" "$TMP/first-intro-check.sh"
git -C "$TMP/precommit_add" rm --quiet docs/sot/principles.yaml scripts/acceptance-principles-check.sh
git -C "$TMP/precommit_add" commit --quiet "$NO_VERIFY" -m before-first-intro
mkdir -p "$TMP/precommit_add/docs/sot" "$TMP/precommit_add/scripts"
cp "$TMP/first-intro-principles.yaml" "$TMP/precommit_add/docs/sot/principles.yaml"
cp "$TMP/first-intro-check.sh" "$TMP/precommit_add/scripts/acceptance-principles-check.sh"
chmod +x "$TMP/precommit_add/scripts/acceptance-principles-check.sh"
git -C "$TMP/precommit_add" add docs/sot/principles.yaml scripts/acceptance-principles-check.sh
pc_rc=0
(cd "$TMP/precommit_add" && bash hooks/pre-commit >/dev/null 2>&1) || pc_rc=$?
if [ "$pc_rc" -eq 0 ]; then pc_ok=0; else pc_ok=1; fi
record "$pc_ok" "필수 파일 첫 도입 add 대조군" "exit=$pc_rc"

# workflow 고정 배선과 같은 존재 검사를 로컬에서 실행한다.
wiring_ok=0
if ! grep -qF 'test -f docs/sot/principles.yaml' "$REPO/.github/workflows/verify.yml" || \
   ! grep -qF 'test -f scripts/acceptance-principles-check.sh' "$REPO/.github/workflows/verify.yml" || \
   ! grep -qF 'bash scripts/acceptance-principles-check.sh' "$REPO/.github/workflows/verify.yml"; then
  wiring_ok=1
fi
record "$wiring_ok" "CI 고정 파일 목록 + 직접 실행 배선" "workflow literal 확인"

new_case ci_delete
rm "$TMP/ci_delete/docs/sot/principles.yaml"
ci_rc=0
(
  cd "$TMP/ci_delete" || exit 1
  test -f docs/sot/principles.yaml &&
  test -f scripts/acceptance-principles-check.sh
) >/dev/null 2>&1 || ci_rc=$?
if [ "$ci_rc" -ne 0 ]; then ci_ok=0; else ci_ok=1; fi
record "$ci_ok" "필수 파일 삭제 → 로컬 CI-equivalent 차단" "exit=$ci_rc"

current=$(git -C "$REPO" status --porcelain)
if [ "$current" = "$SNAPSHOT" ]; then status_ok=0; else status_ok=1; fi
record "$status_ok" "원본 worktree 상태 기준선 보존" "before/after 동일"

printf 'CHECKED: %d\n' "$checked"
exit "$fail"
