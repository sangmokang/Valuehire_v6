#!/usr/bin/env bash
# acceptance-verify-ac-m.sh — mechanism 레지스트리 검사기가 계약대로 동작하는가 (AC-M)
#
# 계약: docs/engineering/verify-ac-m-goal-2026-08-12.md §③·⑩
#   정본: docs/engineering/verify-unification-goal-2026-08-10.md:78-81 (AC-M)
#   출력 : 항목마다 PASS:/FAIL: 전부 출력, 마지막 줄 `CHECKED: <검사 수>`
#   exit : 0 = PASS | 1 = FAIL | 2 = NOT_RUN
#   불변식: CHECKED 는 정확히 34 이어야 한다 — 검사가 몇 개 사라져도 초록이면 가짜다
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
EXPECTED_CHECKED=34

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

# 이 인수 검사 자신의 CI 배선을 확인한다. 두 번째 인수의 워크플로를 받는 이유는
# 주석만 남은 가짜 배선을 임시 fixture 로 재현해 이 검사 자체도 시험하기 위해서다.
own_ci_wiring_is_unconditional() {
  local wf="$1"
  ruby -ryaml -e '
    begin
      workflow = YAML.safe_load(
        File.read(ARGV.fetch(0)),
        permitted_classes: [],
        permitted_symbols: [],
        aliases: false
      )
      jobs = workflow.is_a?(Hash) ? workflow["jobs"] : nil
      selected = jobs.is_a?(Hash) ? jobs["verify"] : nil
      steps = selected.is_a?(Hash) ? selected["steps"] : nil
      exit 2 unless steps.is_a?(Array)

      targets = [
        "bash scripts/acceptance-verify-ac-m.sh",
        "bash scripts/verify/run-acceptance.sh scripts/acceptance-verify-ac-m.sh"
      ]
      matches = steps.count do |step|
        next false unless step.is_a?(Hash)
        next false if step.key?("if") || step.key?("continue-on-error")
        run = step["run"]
        next false unless run.is_a?(String)

        run.lines.any? do |line|
          command = line.strip
          !command.empty? && !command.start_with?("#") && targets.include?(command)
        end
      end
      exit(matches == 1 ? 0 : 1)
    rescue StandardError
      exit 2
    end
  ' "$wf" 2>/dev/null
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

cat > "$TMP/comment-only-target.yaml" <<'EOF'
- id: "comment-only-target"
  path: "scripts/verify/fixtures/mechanism-registry/comment-only-hook.sh"
  target: "-name 'verify.sh' -o -name 'acceptance-*.sh'"
  stage: "pre-push"
  required: true
EOF
expect_rc "주석에만 있는 target → 불합격" "$TMP/comment-only-target.yaml" 1

cat > "$TMP/echo-only-target.yaml" <<'EOF'
- id: "echo-only-target"
  path: "scripts/verify/fixtures/mechanism-registry/echo-only-hook.sh"
  target: "-name 'verify.sh' -o -name 'acceptance-*.sh'"
  stage: "pre-push"
  required: true
EOF
expect_rc "echo에만 있는 target → 불합격" "$TMP/echo-only-target.yaml" 1

cat > "$TMP/dead-code-target.yaml" <<'EOF'
- id: "dead-code-target"
  path: "scripts/verify/fixtures/mechanism-registry/dead-code-hook.sh"
  target: "-name 'verify.sh' -o -name 'acceptance-*.sh'"
  stage: "pre-push"
  required: true
EOF
expect_rc "최상위 exit 뒤 target → 불합격" "$TMP/dead-code-target.yaml" 1

cat > "$TMP/if-false-target.yaml" <<'EOF'
- id: "if-false-target"
  path: "scripts/verify/fixtures/mechanism-registry/if-false-hook.sh"
  target: "-name 'verify.sh' -o -name 'acceptance-*.sh'"
  stage: "pre-push"
  required: true
EOF
expect_rc "if false 분기 안 target → 불합격" "$TMP/if-false-target.yaml" 1

cat > "$TMP/fingerprint-target.yaml" <<'EOF'
- id: "fingerprint-target"
  path: "scripts/verify/fixtures/mechanism-registry/fingerprint-hook.sh"
  target: "-name 'verify.sh' -o -name 'acceptance-*.sh'"
  stage: "pre-push"
  required: true
EOF
expect_rc "고정 sandbox 지문에서만 실행되는 target → 불합격" "$TMP/fingerprint-target.yaml" 1

cat > "$TMP/path-fingerprint-target.yaml" <<'EOF'
- id: "path-fingerprint-target"
  path: "scripts/verify/fixtures/mechanism-registry/path-fingerprint-hook.sh"
  target: "-name 'verify.sh' -o -name 'acceptance-*.sh'"
  stage: "pre-push"
  required: true
EOF
expect_rc "고정 임시경로 접두사에서만 실행되는 target → 불합격" "$TMP/path-fingerprint-target.yaml" 1

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
# ⚠️ path 는 저장소 안 상대경로여야 한다 — 절대경로는 계약 위반으로 거부된다(V1 D4).
cat > "$TMP/manual-ok.yaml" <<'EOF'
- id: "manual-ok"
  path: "scripts/session-status.sh"
  target: "scripts/session-status.sh"
  stage: "manual"
  manual_reason: "goal 작성 시점에 사람이 실행하는 검사 (fixture)"
  required: true
EOF
expect_rc "manual 정상(사유+실행권한) → 통과" "$TMP/manual-ok.yaml" 0

# ── V1 적대검증(2026-08-12, FAIL 9건)이 뚫은 경계 — 반례를 고정한다 ─────────
# V1 D2: 존재하지만 실행권한이 없는 manual path — 규칙 5의 유일한 판별 반례.
# (사유 없음·정상 파일만으로는 -x 검사 한 줄을 지워도 전체가 초록이었다 — 실측)
# 절대경로 거부(D4)와 분리해 시험하기 위해 저장소 안 상대경로가 필요하다.
# 저장소를 오염시키지 않도록, 이미 커밋돼 있는 비실행(644) 파일을 가리킨다.
cat > "$TMP/manual-not-exec.yaml" <<'EOF'
- id: "manual-not-exec"
  path: "scripts/verify/fixtures/mechanism-registry/normal.yaml"
  target: "x"
  stage: "manual"
  manual_reason: "실행권한 없는 파일을 가리키는 반례 (fixture)"
  required: true
EOF
expect_rc "manual 인데 실행권한 없음 → 불합격" "$TMP/manual-not-exec.yaml" 1

# V1 D1: ci 항목의 target 이 워크플로 파일에 없는 거짓 명령 — 규칙 4가 작업 이름만
# 보면 존재하지 않는 명령을 '실행 중'이라고 명부에 적어도 통과한다(실측 CHECKED:15 rc=0).
cat > "$TMP/ci-fake-target.yaml" <<'EOF'
- id: "ci-fake-target"
  path: ".github/workflows/verify.yml"
  target: "run: bash scripts/fake-never-called.sh"
  stage: "ci"
  ci_mirror_job: "verify"
  required: true
EOF
expect_rc "ci 인데 거짓 target → 불합격" "$TMP/ci-fake-target.yaml" 1

# codeaudit(2026-08-15) 후속 A2: ci target 문자열이 실제 run 명령에는 없고 주석에만
# 있어도 파일 전체 grep은 통과했다. 명부는 "실제로 실행되는 장치"의 명부이므로,
# 작업의 run 값 안에 있는 정확한 명령줄만 근거로 인정해야 한다.
mkdir -p "$TMP/comment-only/.github/workflows"
cat > "$TMP/comment-only/.github/workflows/verify.yml" <<'EOF'
name: verify
on: push
jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - name: 목표 명령을 주석에만 둔 가짜 배선
        # bash scripts/acceptance-hs-portal-constants.sh
        run: echo clean
EOF
cat > "$TMP/comment-only/registry.yaml" <<'EOF'
- id: "ci-comment-only-target"
  path: ".github/workflows/verify.yml"
  target: "bash scripts/acceptance-hs-portal-constants.sh"
  stage: "ci"
  ci_mirror_job: "verify"
  required: true
EOF
comment_only_rc=$(cd "$TMP/comment-only" && bash "$REPO/$CHECKER" registry.yaml >/dev/null 2>&1; echo $?)
checked=$((checked + 1))
if [ "$comment_only_rc" -eq 1 ]; then
  echo "PASS: ci target 이 주석에만 있음 → 불합격 (exit=1)"
else
  echo "FAIL: ci target 이 주석에만 있음 → 불합격 (기대 exit=1, 실제 $comment_only_rc)"
  fail=1
fi

# codeaudit 2026-08-15 D4: 명령은 run 안에 있지만 step 자체가 if:false 로 꺼진 경우.
mkdir -p "$TMP/if-false/.github/workflows"
cat > "$TMP/if-false/.github/workflows/verify.yml" <<'EOF'
name: verify
on: push
jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - name: 꺼진 목표 명령
        if: false
        run: bash scripts/acceptance-hs-portal-constants.sh
EOF
cat > "$TMP/if-false/registry.yaml" <<'EOF'
- id: "ci-if-false-target"
  path: ".github/workflows/verify.yml"
  target: "bash scripts/acceptance-hs-portal-constants.sh"
  stage: "ci"
  ci_mirror_job: "verify"
  required: true
EOF
if_false_rc=$(cd "$TMP/if-false" && bash "$REPO/$CHECKER" registry.yaml >/dev/null 2>&1; echo $?)
checked=$((checked + 1))
if [ "$if_false_rc" -eq 1 ]; then
  echo "PASS: ci target step 이 if:false 로 꺼짐 → 불합격 (exit=1)"
else
  echo "FAIL: ci target step 이 if:false 로 꺼짐 → 불합격 (기대 exit=1, 실제 $if_false_rc)"
  fail=1
fi

# V1 D4: 저장소 밖 절대경로 — 계약(⑩)은 저장소 루트 기준 상대경로다.
cat > "$TMP/abs-path.yaml" <<'EOF'
- id: "abs-path"
  path: "/bin/sh"
  target: "/bin/sh"
  stage: "manual"
  manual_reason: "절대경로 반례 (fixture)"
  required: true
EOF
expect_rc "절대경로 path → 불합격" "$TMP/abs-path.yaml" 1

# codeaudit(2026-08-12) AC-M-F3: 상대경로 심볼릭 링크가 저장소 밖 실행파일을 가리키면
# 절대경로 검사(/*)를 우회하고 [ -x ] 가 심링크를 따라가 통과했다. "저장소 안 상대경로만"
# 경계가 심링크로 뚫린 것 — 저장소 안 추적 파일이 아니라 각 실행 기계의 임의 파일을 가리킬 수 있다.
# ⚠️ 저장소를 오염시키지 않으려고 심링크를 $TMP 안에 만들고, 검사기를 $TMP 를 cwd 로
# 실행해 상대경로 "sl" 이 그 심링크로 풀리게 한다(검사기는 cwd 기준 상대경로를 본다).
ln -s /bin/sh "$TMP/sl" 2>/dev/null
cat > "$TMP/symlink-rel.yaml" <<'EOF'
- id: "symlink-rel"
  path: "sl"
  target: "y"
  stage: "manual"
  manual_reason: "저장소 안 상대경로 심링크 → 밖 실행파일 (fixture)"
  required: true
EOF
symrc=$( cd "$TMP" && bash "$REPO/$CHECKER" symlink-rel.yaml >/dev/null 2>&1; echo $? )
checked=$((checked + 1))
if [ "$symrc" -eq 1 ]; then
  echo "PASS: 상대경로 심볼릭 링크 → 불합격 (exit=1)"
else
  echo "FAIL: 상대경로 심볼릭 링크 → 불합격 (기대 exit=1, 실제 $symrc)"
  fail=1
fi

# V1 D5-a: 같은 항목에 같은 필드 2회 — 마지막 값이 조용히 이긴다.
# ⚠️ 마지막 값이 모든 규칙을 통과하는 형태여야 판별력이 있다 — 마지막 값이 어차피
# 다른 규칙에 걸리면 중복 감지가 없어도 빨개져서 이 반례가 아무것도 증명 못 한다.
cat > "$TMP/dup-field.yaml" <<'EOF'
- id: "dup-field"
  path: "hooks/pre-push"
  path: "hooks/pre-commit"
  target: "SECRET_PATTERNS_FILE= VERIFY_SCAN_SOURCE=index bash verify.sh"
  stage: "pre-commit"
  required: true
EOF
expect_rc "필드 중복(path 2회, 마지막 값 유효) → 불합격" "$TMP/dup-field.yaml" 1

# V1 D5-b: 값 뒤 인라인 주석 — id·사유 같은 자유 문자열 필드에서는 주석·따옴표가
# 값에 통째로 흡수된 채 조용히 통과한다(enum 필드는 값 오류로 자기방어되므로 제외).
cat > "$TMP/inline-comment.yaml" <<'EOF'
- id: "inline-comment" # 주석이 id 에 흡수된다
  path: "hooks/pre-commit"
  target: "SECRET_PATTERNS_FILE= VERIFY_SCAN_SOURCE=index bash verify.sh"
  stage: "pre-commit"
  required: true
EOF
expect_rc "id 뒤 인라인 주석 → 불합격" "$TMP/inline-comment.yaml" 1

# V1 D5-c: 닫히지 않은 따옴표 — 따옴표 문자가 id 에 섞인 채 통과했다.
cat > "$TMP/unmatched-quote.yaml" <<'EOF'
- id: "unmatched
  path: "hooks/pre-commit"
  target: "SECRET_PATTERNS_FILE= VERIFY_SCAN_SOURCE=index bash verify.sh"
  stage: "pre-commit"
  required: true
EOF
expect_rc "닫히지 않은 따옴표 → 불합격" "$TMP/unmatched-quote.yaml" 1

# V1 D5-d: stage 와 맞지 않는 필드 — pre-commit 항목의 ci_mirror_job.
cat > "$TMP/stage-mismatch.yaml" <<'EOF'
- id: "stage-mismatch"
  path: "hooks/pre-commit"
  target: "SECRET_PATTERNS_FILE= VERIFY_SCAN_SOURCE=index bash verify.sh"
  stage: "pre-commit"
  ci_mirror_job: "verify"
  required: true
EOF
expect_rc "stage 불일치 필드(ci_mirror_job) → 불합격" "$TMP/stage-mismatch.yaml" 1

# V1 D6: 문법 오류만 있고 인식 항목 0개 — '검사 불능(2)'이 아니라 '위반(1)'이어야 한다.
cat > "$TMP/syntax-only.yaml" <<'EOF'
  - id: "misindented"
EOF
expect_rc "문법 오류·항목 0개 → 위반(1)" "$TMP/syntax-only.yaml" 1

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

# ── codeaudit 2026-08-15 D1: 주석만 남은 자기배선 반례 ───────────────────────
mkdir -p "$TMP/self-comment/.github/workflows"
cat > "$TMP/self-comment/.github/workflows/verify.yml" <<'EOF'
name: verify
on: push
jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - name: 인수 검사 verify-ac-m
        run: |
          # run: bash scripts/acceptance-verify-ac-m.sh
          echo skipped
EOF
checked=$((checked + 1))
if own_ci_wiring_is_unconditional "$TMP/self-comment/.github/workflows/verify.yml"; then
  echo "FAIL: CI 자기배선 target 이 셸 주석에만 있는데 합격했다"
  fail=1
else
  echo "PASS: CI 자기배선 target 이 셸 주석에만 있음 → 불합격"
fi

# ── V1 D3: CI 배선 자기검사 ──────────────────────────────────────────────────
# 이 인수 검사의 실행 줄이 서버 자동검사(verify.yml)에 조건 없이 정확히 1회 있는가.
# CI 스텝을 if 로 끄거나 지워도 로컬 검사가 전부 초록이었다(V1 실측 · P15③).
checked=$((checked + 1))
WF=.github/workflows/verify.yml
# 2026-08-21 부터 CI 는 scripts/verify/run-acceptance.sh 래퍼를 거쳐 실행한다. 판정은
# 문자열 grep 이 아니라 YAML 구조로 한다(주석 위장·조건부 스텝을 grep 은 못 막는다 —
# 이 파일의 self-comment fixture 가 그 반례다). 래퍼 없는 직접 실행도 계속 인정한다.
if own_ci_wiring_is_unconditional "$WF"; then
  echo "PASS: CI 배선 — verify.yml 에 무조건 실행 스텝 정확히 1회"
else
  echo 'FAIL: CI 배선 — 정확한 비주석 실행 줄 1회가 아니거나 조건부/오류무시 스텝 (로컬에만 있는 검사는 없는 것으로 친다 · P15③)'
  fail=1
fi

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
