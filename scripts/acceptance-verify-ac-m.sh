#!/usr/bin/env bash
# acceptance-verify-ac-m.sh — mechanism 레지스트리 검사기가 계약대로 동작하는가 (AC-M)
#
# 계약: docs/engineering/verify-ac-m-goal-2026-08-12.md §③·⑩
#   정본: docs/engineering/verify-unification-goal-2026-08-10.md:78-81 (AC-M)
#   출력 : 항목마다 PASS:/FAIL: 전부 출력, 마지막 줄 `CHECKED: <검사 수>`
#   exit : 0 = PASS | 1 = FAIL | 2 = NOT_RUN
#   불변식: CHECKED 는 정확히 15 이어야 한다 — 검사가 몇 개 사라져도 초록이면 가짜다
#           (PR #6 결함 D3 의 교훈: checked==0 만 막으면 3개를 지워도 통과했다 · P20)
#
# 쓰기 규칙: 이 검사는 저장소에 어떤 파일도 만들지 않는다. 동적 fixture 는 전부
#   mktemp 디렉토리에만 쓴다(2026-08-09 검증기 오염 사고 · PR #6 결함 D4 의 교훈).
set -uo pipefail

# git 훅이 export 하는 환경으로 실제 저장소에 붙는 사고 방지 (hooks 상속 차단)
unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE GIT_OBJECT_DIRECTORY \
      GIT_ALTERNATE_OBJECT_DIRECTORIES GIT_COMMON_DIR GIT_PREFIX GIT_QUARANTINE_PATH

REPO=$(git rev-parse --show-toplevel 2>/dev/null) || { echo "NOT_RUN: git 저장소가 아니다"; echo "CHECKED: 0"; exit 2; }
cd "$REPO" || { echo "NOT_RUN: 저장소 루트로 이동 실패"; echo "CHECKED: 0"; exit 2; }

SNAP0=$(git status --porcelain)

CHECKER=scripts/verify/check-mechanism-registry.sh
FIXDIR=scripts/verify/fixtures/mechanism-registry
REGISTRY=docs/sot/mechanism-registry.yaml
EXPECTED_CHECKED=15

TMP=$(mktemp -d) || { echo "NOT_RUN: mktemp 실패"; echo "CHECKED: 0"; exit 2; }
trap 'rm -rf "$TMP"' EXIT

fail=0
checked=0

# 검사기를 지정 exit code 기대로 실행한다. 검사기가 없으면 bash 가 127 을 내고,
# 그것은 기대값과 달라 FAIL 이 된다 — "기대 동작이 없다"가 RED 의 올바른 이유다.
expect_rc() {
  local desc="$1" reg="$2" want="$3" rc=0
  checked=$((checked + 1))
  bash "$CHECKER" "$reg" >/dev/null 2>&1
  rc=$?
  if [ "$rc" -eq "$want" ]; then
    printf 'PASS: %s (exit=%s)\n' "$desc" "$rc"
  else
    printf 'FAIL: %s (기대 exit=%s, 실제 %s)\n' "$desc" "$want" "$rc"
    fail=1
  fi
}

# ── 1) 검사기 실존 + 실행권한 ────────────────────────────────────────────────
checked=$((checked + 1))
if [ -f "$CHECKER" ] && [ -x "$CHECKER" ]; then
  echo "PASS: 검사기 실존·실행가능 — $CHECKER"
else
  echo "FAIL: 검사기 없음/실행불가 — $CHECKER (기대 동작이 아직 없다)"
  fail=1
fi

# ── 2~4) 정본이 요구한 fixture 3종 (각각 다른 실패 경로) ─────────────────────
expect_rc "fixture 정상 명부 → 통과"            "$FIXDIR/normal.yaml"       0
expect_rc "fixture path 없는 항목 → 불합격"     "$FIXDIR/missing-path.yaml" 1
expect_rc "fixture 죽은 target → 불합격"        "$FIXDIR/dead-target.yaml"  1

# ── 5~10) 동적 fixture — fail-closed 경계 (전부 mktemp 에만 쓴다) ────────────
# id 중복
cat > "$TMP/dup-id.yaml" <<'EOF'
- id: "dup-mechanism"
  path: "hooks/pre-commit"
  target: "SECRET_PATTERNS_FILE= VERIFY_SCAN_SOURCE=index bash verify.sh"
  stage: "pre-commit"
  required: true
- id: "dup-mechanism"
  path: "hooks/pre-push"
  target: "-name 'verify.sh' -o -name 'acceptance-*.sh'"
  stage: "pre-push"
  required: true
EOF
expect_rc "id 중복 → 불합격" "$TMP/dup-id.yaml" 1

# 알 수 없는 stage 값 — 조용히 skip 하면 안 된다
cat > "$TMP/bad-stage.yaml" <<'EOF'
- id: "bad-stage-mechanism"
  path: "hooks/pre-commit"
  target: "SECRET_PATTERNS_FILE= VERIFY_SCAN_SOURCE=index bash verify.sh"
  stage: "sometimes-maybe"
  required: true
EOF
expect_rc "알 수 없는 stage → 불합격" "$TMP/bad-stage.yaml" 1

# manual 인데 manual_reason 없음 (counter-AC: manual 로 호출 검사 회피 금지)
cat > "$TMP/manual-no-reason.yaml" <<'EOF'
- id: "manual-no-reason"
  path: "verify.sh"
  stage: "manual"
  target: "verify.sh"
  required: true
EOF
expect_rc "manual 인데 사유 없음 → 불합격" "$TMP/manual-no-reason.yaml" 1

# manual + 사유 + 실행권한 path → 통과 (규칙 5 의 정상 경로)
printf '#!/bin/sh\nexit 0\n' > "$TMP/runnable.sh" && chmod +x "$TMP/runnable.sh"
cat > "$TMP/manual-ok.yaml" <<EOF
- id: "manual-ok"
  path: "$TMP/runnable.sh"
  target: "$TMP/runnable.sh"
  stage: "manual"
  manual_reason: "goal 작성 시점에 사람이 실행하는 검사 (fixture)"
  required: true
EOF
expect_rc "manual 정상(사유+실행권한) → 통과" "$TMP/manual-ok.yaml" 0

# 항목 0개(주석뿐) → NOT_RUN (0건 통과 금지 · P20)
cat > "$TMP/empty.yaml" <<'EOF'
# 주석만 있는 명부 — 항목 0개
EOF
expect_rc "항목 0개 명부 → NOT_RUN" "$TMP/empty.yaml" 2

# ci 인데 ci_mirror_job 이 실제 jobs: 키에 없음
cat > "$TMP/bad-ci-job.yaml" <<'EOF'
- id: "bad-ci-job"
  path: ".github/workflows/verify.yml"
  target: "run: bash verify.sh"
  stage: "ci"
  ci_mirror_job: "no-such-job-key"
  required: true
EOF
expect_rc "ci_mirror_job 불일치 → 불합격" "$TMP/bad-ci-job.yaml" 1

# 필수 필드 누락 (stage 없음) — 조용히 skip 하면 안 된다
cat > "$TMP/missing-field.yaml" <<'EOF'
- id: "missing-stage-mechanism"
  path: "hooks/pre-commit"
  target: "SECRET_PATTERNS_FILE= VERIFY_SCAN_SOURCE=index bash verify.sh"
  required: true
EOF
expect_rc "필수 필드(stage) 누락 → 불합격" "$TMP/missing-field.yaml" 1

# 빈 문자열 값 — 계약(goal ⑩): 빈 값 = 누락으로 취급
cat > "$TMP/empty-value.yaml" <<'EOF'
- id: "empty-path-mechanism"
  path: ""
  target: "SECRET_PATTERNS_FILE= VERIFY_SCAN_SOURCE=index bash verify.sh"
  stage: "pre-commit"
  required: true
EOF
expect_rc "빈 문자열 path → 불합격" "$TMP/empty-value.yaml" 1

# ── 13) 실제 명부가 검사기를 통과하는가 ──────────────────────────────────────
expect_rc "실제 명부(docs/sot/mechanism-registry.yaml) → 통과" "$REGISTRY" 0

# ── 14) 실제 명부의 항목 수 = 검사기 CHECKED 보고 수 (누락·부풀림 방지) ──────
checked=$((checked + 1))
if [ -f "$REGISTRY" ]; then
  entries=$(grep -c '^- id:' "$REGISTRY")
else
  entries=0
fi
reported=$(bash "$CHECKER" "$REGISTRY" 2>/dev/null | sed -n 's/^CHECKED: //p')
if [ -n "$reported" ] && [ "$entries" -ge 3 ] && [ "$entries" = "$reported" ]; then
  printf 'PASS: 명부 항목 %s개 = 검사기 보고 %s개 (하한 3)\n' "$entries" "$reported"
else
  printf 'FAIL: 명부 항목(%s) vs 검사기 보고(%s) 불일치 또는 하한(3) 미달\n' "$entries" "${reported:-없음}"
  fail=1
fi

# ── 15) 무오염 ───────────────────────────────────────────────────────────────
SNAP1=$(git status --porcelain)
checked=$((checked + 1))
if [ "$SNAP0" != "$SNAP1" ]; then
  echo "FAIL: 이 검사가 저장소를 오염시켰다 — 시작/종료 상태가 다르다 (판정 무효)"
  printf '%s\n' "$SNAP1" | sed 's/^/       /'
  fail=1
else
  echo "PASS: 저장소 무오염 (시작/종료 상태 동일)"
fi

# CHECKED 정확값 강제 — 검사 몇 개가 사라져도 초록이면 가짜 (D3 재발 방지 · P20)
if [ "$checked" -ne "$EXPECTED_CHECKED" ]; then
  printf 'FAIL: 검사 수 %d ≠ 계약값 %d — 검사가 사라졌거나 무단 추가됐다\n' "$checked" "$EXPECTED_CHECKED"
  fail=1
fi

printf 'CHECKED: %d\n' "$checked"
exit "$fail"
