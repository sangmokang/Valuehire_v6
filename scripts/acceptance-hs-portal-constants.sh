#!/usr/bin/env bash
# acceptance-hs-portal-constants.sh — G3: 운영 상수·portal locator(URL·포트·도메인·CSS
# selector·XPath)는 저장소 루트의 정확한 contracts/ 밖에 존재할 수 없다 (P22 · 웹 자동화 5조 1번).
#
# 계약: docs/engineering/humansearch-g3-portal-constants-goal-2026-08-12.md §1⑩
#   exit 0 = 깨끗한 트리 | 1 = 위반 발견(금지값·contracts 구역 위반·배선 훼손)
#   exit 2 = 검사 불능(패턴 계약 부재/깨짐, 열거·읽기 실패, 제품 루트 부재, 하한 미달)
#
# 경계 규칙 (사전감사 벡터 8):
#   허용 구역은 git ls-files 상대 경로의 정확한 `contracts/` 접두뿐이다. 부분 문자열
#   (a/contracts/, contracts-evil/) 은 전부 검사 대상이다. contracts/ 값에는 금지 패턴을
#   적용하지 않는 대신 구역 자체를 검사한다(정규 파일·비실행·허용 확장자만).
#   docs/ 디렉터리 전체를 면제하지 않는다. 그 안에서도 문서 확장자(md·yaml·yml·txt·html)이고
#   Git 추적 모드가 100644인 정규 비실행 파일만 면제하며 CHECKED 에 세지 않는다. 그 조건을
#   벗어난 docs 파일(실행 코드·실행 권한 문서)은 전역 검사 대상이다(V1 결함 D5·F3).
#   그 밖의 모든 추적 파일 — 이 검사기 자신·scripts/·hooks/·.github/ 포함 — 은 전역
#   패턴으로 검사한다. 자기면제 없음(P13④). 제품 루트는 전역 + 제품 전용 패턴 둘 다.
set -euo pipefail

unset GIT_DIR GIT_INDEX_FILE GIT_OBJECT_DIRECTORY GIT_WORK_TREE GIT_COMMON_DIR
unset GIT_ALTERNATE_OBJECT_DIRECTORIES

REPO=$(git rev-parse --show-toplevel) || {
  echo "FAIL: repository root unavailable"
  exit 2
}
cd "$REPO"

GLOBAL_PATTERNS=contracts/portal-constants-deny-patterns.txt
PRODUCT_PATTERNS=contracts/portal-constants-deny-patterns-product.txt
PRODUCT_ROOTS="humansearch/src humansearch/tests"
WF=.github/workflows/verify.yml
HOOK=hooks/pre-push

# 임시 작업공간 생성 실패는 위반(1)이 아니라 검사 불능(2)이다 — set -e 에 맡기면
# mktemp 의 1 이 그대로 새어 나가 규칙 위반과 환경 고장이 구분되지 않는다 (V1 결함 D4).
GCLEAN=$(mktemp) || { echo "FAIL: temp workspace unavailable"; exit 2; }
PCLEAN=$(mktemp) || { echo "FAIL: temp workspace unavailable"; exit 2; }
FILES=$(mktemp) || { echo "FAIL: temp workspace unavailable"; exit 2; }
ERRS=$(mktemp) || { echo "FAIL: temp workspace unavailable"; exit 2; }
cleanup() { rm -f -- "$GCLEAN" "$PCLEAN" "$FILES" "$ERRS"; }
trap cleanup EXIT
trap 'cleanup; trap - EXIT; exit 143' TERM
trap 'cleanup; trap - EXIT; exit 130' INT
trap 'cleanup; trap - EXIT; exit 129' HUP

# 패턴 계약 검증 (G1 acceptance-hs-cleanroom.sh:14-43 방어 재사용):
# 부재/빈 파일/유효 패턴 0개/깨진 표현식/빈 문자열 매치 전부 exit 2 — "검사가 안 돌았는데
# 위반 없음"을 원리적으로 금지한다.
load_patterns() {
  local src="$1" dst="$2" rc=0
  if [ ! -f "$src" ] || [ ! -r "$src" ] || [ ! -s "$src" ]; then
    echo "FAIL: portal pattern contract missing, unreadable, or empty: $src"
    exit 2
  fi
  sed -e 's/\r$//' -e '/^[[:space:]]*#/d' -e '/^[[:space:]]*$/d' "$src" > "$dst"
  if [ ! -s "$dst" ]; then
    echo "FAIL: portal pattern contract has zero effective patterns: $src"
    exit 2
  fi
  printf '\n' | LC_ALL=C grep -aEiqf "$dst" > /dev/null 2> "$ERRS" || rc=$?
  if [ "$rc" -gt 1 ]; then
    echo "FAIL: portal pattern contract contains an invalid expression: $src"
    exit 2
  fi
  if [ "$rc" -eq 0 ]; then
    echo "FAIL: portal pattern contract contains an empty-matching expression: $src"
    exit 2
  fi
}

load_patterns "$GLOBAL_PATTERNS" "$GCLEAN"
load_patterns "$PRODUCT_PATTERNS" "$PCLEAN"

# 제품 루트가 없으면 조용한 skip 이 아니라 검사 불능이다 (사전감사 벡터 5).
for root in $PRODUCT_ROOTS; do
  if [ ! -d "$root" ]; then
    echo "FAIL: product root missing: $root"
    exit 2
  fi
done

if ! git ls-files -z > "$FILES"; then
  echo "FAIL: tracked-file enumeration failed"
  exit 2
fi

checked=0
product_files=0
contract_files=0
forbidden=0
zone_violations=0
errors=0

scan_with() {
  local path="$1" pats="$2" tier="$3" rc=0
  LC_ALL=C grep -aEiqf "$pats" -- "./$path" 2>> "$ERRS" || rc=$?
  if [ "$rc" -eq 0 ]; then
    forbidden=$((forbidden + 1))
    printf '  forbidden(%s): %q\n' "$tier" "$path"
  elif [ "$rc" -gt 1 ]; then
    errors=$((errors + 1))
    printf '  unreadable: %q\n' "$path"
  fi
}

while IFS= read -r -d '' path; do
  case "$path" in
    contracts/*)
      contract_files=$((contract_files + 1))
      mode=$(git ls-files -s -- "$path" | awk '{print $1}')
      case "$mode" in
        100644) ;;
        *)
          zone_violations=$((zone_violations + 1))
          printf '  contracts-zone: %q (mode %s — 데이터 구역엔 정규 비실행 파일만)\n' "$path" "${mode:-?}"
          ;;
      esac
      lower=$(printf '%s' "$path" | tr '[:upper:]' '[:lower:]')
      case "$lower" in
        *.txt|*.json|*.yaml|*.yml|*.md) ;;
        *)
          zone_violations=$((zone_violations + 1))
          printf '  contracts-zone: %q (허용 확장자 밖)\n' "$path"
          ;;
      esac
      continue
      ;;
    docs/*)
      # 문서 면제는 디렉터리 전체가 아니라 "문서 확장자 + 정규 비실행 파일"에만 준다.
      # 통 면제는 docs/run-portal.py 같은 실행 코드의 은닉 경로가 된다 (V1 결함 D5).
      lower=$(printf '%s' "$path" | tr '[:upper:]' '[:lower:]')
      mode=$(git ls-files -s -- "$path" | awk '{print $1}')
      case "$lower" in
        *.md|*.yaml|*.yml|*.txt|*.html)
          if [ "$mode" = "100644" ]; then continue; fi
          ;;
      esac
      # 문서 형식이 아니거나 실행 가능한 docs 파일 → 전역 검사로 계속 진행
      ;;
  esac
  checked=$((checked + 1))
  case "$path" in
    humansearch/src/*|humansearch/tests/*)
      product_files=$((product_files + 1))
      scan_with "$path" "$GCLEAN" global
      scan_with "$path" "$PCLEAN" product
      ;;
    *)
      scan_with "$path" "$GCLEAN" global
      ;;
  esac
done < "$FILES"

# ── 배선 자기 검사 (사전감사 벡터 1·2, V1 결함 D2·D3, V1 2차 결함 N2·N3) ──────
# CI 는 수동 열거(verify.yml)라 여기 등록되지 않으면 "로컬에만 있는 검사"가 되고,
# P15③ 은 그것을 없는 것으로 친다. 이 검사기 자신이 양쪽 배선을 확인한다.
wiring_fail=0
wire_bad() { wiring_fail=$((wiring_fail + 1)); printf '  wiring: %s\n' "$1"; }

# 존재하는 G3 검사 파일 전부가 각자 CI 실행 줄을 가져야 한다. 요구 목록을 파일
# 존재에서 만들므로 새 G3 검사를 추가하면 CI 줄도 자동으로 요구된다 (V1 2차 N3).
# 잔여 한계: 검사 파일 자체를 지우면 요구도 사라진다 — 그 삭제는 diff·P13 라벨·
# RED 원장 분모 감소로 드러난다 (goal 문서 한계 절).
G3_FILES=$(find . -maxdepth 2 -name 'acceptance-hs-portal-constants*.sh' \
  -not -path './worktrees/*' -not -path './.git/*' | sed 's|^\./||' | LC_ALL=C sort)
# awk -v 는 개행을 못 받으므로(BSD awk) 세미콜론으로 잇는다 — 경로에 ; 는 없다.
ALLOWED_CMDS=""
while IFS= read -r g3f; do
  if [ -z "$g3f" ]; then continue; fi
  ALLOWED_CMDS="${ALLOWED_CMDS}bash ${g3f};"
done <<G3EOF
$G3_FILES
G3EOF

# 워크플로를 YAML 구조로 읽고 jobs.*.steps[*].run 문자열만 실행 칸으로 인정한다. 파일
# 어딘가에 명령 글자가 있다는 이유만으로 통과시키면 env.NOTE 같은 실행되지 않는 값 안의
# 가짜 단계도 배선으로 오인한다(V1 3차 F1). Ruby 표준 YAML 해석기를 쓰므로 새 의존성은 없다.
#
# target 명령이 있는 run 문자열은 주석·빈 줄·현재 G3 실행 줄만 담아야 하고, 그 스텝에 if 또는
# continue-on-error 키가 있으면 인정하지 않는다. 이로써 기존 셸 감싸기·오류 무시 방어도 유지한다.
ci_line_ok() {
  local tgt="$1"
  ruby -ryaml -e '
    workflow_path, target, allowed_text = ARGV
    begin
      workflow = YAML.safe_load(
        File.read(workflow_path),
        permitted_classes: [],
        permitted_symbols: [],
        aliases: true
      )
    rescue Psych::Exception, SystemCallError
      exit 2
    end

    jobs = workflow.is_a?(Hash) ? workflow["jobs"] : nil
    exit 2 unless jobs.is_a?(Hash)
    allowed = allowed_text.split(";").reject(&:empty?).each_with_object({}) do |command, set|
      set[command] = true
    end

    good = jobs.values.any? do |job|
      next false unless job.is_a?(Hash) && job["steps"].is_a?(Array)
      job["steps"].any? do |step|
        next false unless step.is_a?(Hash)
        next false if step.key?("if") || step.key?("continue-on-error")
        run = step["run"]
        next false unless run.is_a?(String)

        lines = run.each_line.map(&:strip).reject { |line| line.empty? || line.start_with?("#") }
        lines.include?(target) && lines.all? { |line| allowed.key?(line) }
      end
    end
    exit(good ? 0 : 1)
  ' "$WF" "$tgt" "$ALLOWED_CMDS"
}

if [ ! -f "$WF" ]; then
  wire_bad "CI 워크플로($WF) 부재 — 판정 권한이 있는 쪽이 비어 있다"
elif ! command -v ruby >/dev/null 2>&1; then
  echo "FAIL: YAML parser unavailable: ruby"
  exit 2
else
  while IFS= read -r g3f; do
    if [ -z "$g3f" ]; then continue; fi
    ci_rc=0
    ci_line_ok "bash $g3f" || ci_rc=$?
    case "$ci_rc" in
      0) ;;
      1) wire_bad "CI 실행 줄이 없거나 블록이 오염됨: bash $g3f" ;;
      *)
        errors=$((errors + 1))
        printf 'CI workflow YAML parse failed: %s\n' "$WF" >> "$ERRS"
        break
        ;;
    esac
  done <<G3EOF2
$G3_FILES
G3EOF2
fi

if [ ! -f "$HOOK" ] || [ ! -x "$HOOK" ]; then
  wire_bad "pre-push 훅 부재 또는 실행 불가 — 로컬 1차 차단이 없다"
else
  if ! grep -qF -- "-o -name 'acceptance-*.sh'" "$HOOK"; then
    wire_bad "pre-push 의 acceptance 글로브 수집식이 사라졌다"
  fi
  # 훅 상단의 무조건 exit 0 은 수집 이전에 훅 전체를 무력화한다 (V1 2차 N3 절반).
  # 순정 pre-push 에는 순수 `exit 0` 줄이 없다(실측: exit 1 두 곳과 exit "$fail" 뿐).
  if sed -e 's/[[:space:]]*#.*//' "$HOOK" | grep -qE '^[[:space:]]*exit[[:space:]]+0[[:space:]]*$'; then
    wire_bad "pre-push 에 무조건 exit 0 줄이 있다 — 훅이 검사 전에 통과한다"
  fi
  found_self=$(printf '%s\n' "$G3_FILES" | grep -cF 'acceptance-hs-portal-constants')
  if [ "$found_self" -lt 2 ]; then
    wire_bad "글로브 수집 재현에서 검사기·mutation 이 다 잡히지 않는다 (found=$found_self)"
  fi
  # pre-push 는 파일 첫 20줄의 건너뛰기 표식을 보고 검사를 CI 로 넘긴다. G3 파일에 그
  # 표식이 붙으면 로컬 절반이 조용히 사라지므로 여기서 차단한다 (V1 결함 D3).
  G3_MARK=$(printf '# PUSH-%s' 'PERFORMING')
  while IFS= read -r g3f; do
    if [ -z "$g3f" ]; then continue; fi
    if head -20 "$g3f" | grep -qF "$G3_MARK"; then
      wire_bad "G3 검사 파일이 pre-push 건너뛰기 표식을 달고 있다: $g3f"
    fi
  done <<G3EOF3
$G3_FILES
G3EOF3
fi

# ── 판정 ─────────────────────────────────────────────────────────────────────
if [ "$forbidden" -eq 0 ]; then
  echo "PASS: portal constants outside contracts 0"
else
  echo "FAIL: portal constants outside contracts $forbidden"
fi
if [ "$zone_violations" -eq 0 ]; then
  echo "PASS: contracts zone violations 0"
else
  echo "FAIL: contracts zone violations $zone_violations"
fi
if [ "$wiring_fail" -eq 0 ]; then
  echo "PASS: ci/pre-push wiring intact"
else
  echo "FAIL: ci/pre-push wiring broken $wiring_fail"
fi
echo "PRODUCT_FILES: $product_files"
echo "CHECKED: $checked"
echo "CONTRACT_FILES: $contract_files"

# 검사 불능(2)이 위반(1)보다 우선한다 — 일부만 읽은 스캔의 "위반 n건"은 믿을 수 없다.
if [ "$errors" -ne 0 ] || [ -s "$ERRS" ]; then
  echo "FAIL: scanner errors $errors"
  exit 2
fi
if [ "$product_files" -lt 2 ]; then
  echo "FAIL: product files $product_files (<2) — 검사 대상이 없어서 통과는 금지 (P20)"
  exit 2
fi
if [ "$checked" -lt 10 ]; then
  echo "FAIL: checked files $checked (<10)"
  exit 2
fi
if [ "$contract_files" -lt 2 ]; then
  echo "FAIL: contract files $contract_files (<2) — 패턴 계약 2벌이 추적되고 있지 않다"
  exit 2
fi
if [ "$forbidden" -ne 0 ] || [ "$zone_violations" -ne 0 ] || [ "$wiring_fail" -ne 0 ]; then
  exit 1
fi
