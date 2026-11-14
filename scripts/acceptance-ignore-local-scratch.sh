#!/usr/bin/env bash
# 인수 검사: 로컬 산출물 폴더(/audit_work/, /.playwright-mcp/)는 git 에 들어가지 못한다.
# 근거: docs/engineering/ignore-local-scratch-goal-2026-11-14.md (P21 — 후보자 PII 데이터는 git 에 넣지 않는다)
# 1) gitignore 가 최상위 경로를 무시한다
# 2) counter-AC: 새 규칙은 하위 동명 폴더를 무시하지 않는다(앵커, P3 조용한 실패 방지)
# 3) git add -f 로 강제 추가해도 pre-commit 훅이 막는다(실행 검증)
# 4) 공용 판정기(CI 가 실행하는 scan-data-exposure.sh tracked)도 추적된 경우를 막는다(실행 검증)
# 5) 현재 저장소에 두 경로가 추적되어 있지 않다
# 6) CI 고정 목록에 이 검사가 등록되어 있다
set -euo pipefail
# pre-push 훅은 GIT_DIR·GIT_INDEX_FILE 등을 넘긴다. 지우지 않으면 임시 저장소의 git add 가
# 실제 저장소 인덱스를 오염시킨다(2026-11-14 push 차단 실측). 다른 인수검사와 같은 방식.
unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE GIT_OBJECT_DIRECTORY \
      GIT_ALTERNATE_OBJECT_DIRECTORIES GIT_COMMON_DIR GIT_PREFIX GIT_QUARANTINE_PATH
cd "$(git rev-parse --show-toplevel)"
fail=0
ROOT=$PWD
SNAPSHOT=$(git status --porcelain)

# 1)
for p in audit_work/candidates_raw.csv audit_work/progress.json .playwright-mcp/page-x.yml .playwright-mcp/console-x.log; do
  if ! git check-ignore -q --no-index "$p"; then
    echo "FAIL: $p 가 무시되지 않음 (PII/도구 산출물 커밋 위험)"; fail=1
  fi
done

# 2) .log 는 기존 *.log 규칙 대상이라 제외하고, 새 디렉터리 규칙만 본다
for p in docs/audit_work/note.md humansearch/.playwright-mcp/fixture.yml; do
  if git check-ignore -q --no-index "$p"; then
    echo "FAIL: $p 가 무시됨 (앵커 누락 — 정상 소스가 조용히 사라짐)"; fail=1
  fi
done

# 3) 강제 추가 → 훅 차단 (임시 저장소에서 실제 실행)
for p in audit_work/progress.json .playwright-mcp/page-x.yml; do
  tmp=$(mktemp -d) || { echo "FAIL: 임시 저장소 생성 실패 (fail-closed)"; fail=1; continue; }
  mkdir -p "$tmp/hooks"
  cp "$ROOT/hooks/pre-commit" "$tmp/hooks/"
  cp "$ROOT/verify.sh" "$ROOT/.secret-patterns.default" "$ROOT/.check-weakening-patterns" "$ROOT/.gitignore" "$tmp/"
  [ -f "$ROOT/suppressions.yaml" ] && cp "$ROOT/suppressions.yaml" "$tmp/"
  rc=0
  out=$(
    cd "$tmp" || exit 9
    git init -q .
    git config user.email a@b.c; git config user.name t
    mkdir -p "$(dirname "$p")"
    printf '{"candidate_id":"0"}\n' > "$p"
    git add -f "$p" >/dev/null 2>&1
    bash hooks/pre-commit 2>&1
  ) || rc=$?
  rm -rf "$tmp"
  if [ "$rc" -eq 0 ] || ! printf '%s\n' "$out" | grep -q '산출물·데이터 경로'; then
    echo "FAIL: git add -f $p 가 pre-commit 훅을 통과함 (rc=$rc)"; fail=1
  fi
done

# 4) 추적된 경우 → 공용 판정기 차단, 하위 동명 경로는 통과(대조군)
judge() {  # judge <경로> <기대: block|pass>
  local p="$1" want="$2" tmp rc=0
  tmp=$(mktemp -d) || { echo "FAIL: 임시 저장소 생성 실패 (fail-closed)"; fail=1; return; }
  cp "$ROOT/scripts/scan-data-exposure.sh" "$tmp/judge.sh"
  (
    cd "$tmp" || exit 9
    git init -q .
    git config user.email a@b.c; git config user.name t
    mkdir -p "$(dirname "$p")"
    printf 'x\n' > "$p"
    git add -f "$p" >/dev/null 2>&1
    bash judge.sh tracked
  ) >/dev/null 2>&1 || rc=$?
  rm -rf "$tmp"
  if [ "$want" = block ] && [ "$rc" -eq 0 ]; then
    echo "FAIL: 판정기가 추적된 $p 를 통과시킴"; fail=1
  elif [ "$want" = pass ] && [ "$rc" -ne 0 ]; then
    echo "FAIL: 판정기가 정상 경로 $p 를 막음 (rc=$rc)"; fail=1
  fi
}
judge audit_work/progress.json block
judge .playwright-mcp/page-x.yml block
judge docs/audit_work/note.md pass

# 5)
if [ -n "$(git ls-files -- audit_work .playwright-mcp)" ]; then
  echo "FAIL: audit_work/ 또는 .playwright-mcp/ 가 이미 추적되고 있음"; fail=1
fi

# 6) CI 고정 목록에 이 검사가 등록되어 있다 (P15③ — 로컬에만 있는 검사는 없는 것으로 친다)
if ! grep -qE '^[[:space:]]+run: bash scripts/verify/run-acceptance\.sh scripts/acceptance-ignore-local-scratch\.sh[[:space:]]*$' .github/workflows/verify.yml; then
  echo "FAIL: .github/workflows/verify.yml 에 acceptance-ignore-local-scratch.sh 스텝이 없음 (로컬 전용 검사)"; fail=1
fi

# 7) 이 검사 자체가 실제 저장소를 오염시키지 않았다
if [ "$(git status --porcelain)" != "$SNAPSHOT" ]; then
  echo "FAIL: 검사 실행 후 git status 가 바뀜 — 임시 저장소 조작이 실제 저장소로 샜다"; fail=1
fi

[ "$fail" -eq 0 ] && echo "PASS: acceptance-ignore-local-scratch"
exit "$fail"
