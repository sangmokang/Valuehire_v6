#!/usr/bin/env bash
# check-mechanism-registry.sh — 검사 장치 명부가 실제 장치와 일치하는지 대조한다 (AC-M)
#
# 계약: docs/engineering/verify-ac-m-goal-2026-08-12.md §⑩
#   정본: docs/engineering/verify-unification-goal-2026-08-10.md:78-81
#   입력 : $1 = 명부 경로 (기본 docs/sot/mechanism-registry.yaml)
#          WORKFLOW_FILE = CI 워크플로 경로 (기본 .github/workflows/verify.yml)
#   출력 : 항목마다 PASS:/FAIL: (PASS 줄에 적용 규칙 표기), 마지막 줄 `CHECKED: <항목 수>`
#   exit : 0 = 전부 통과 | 1 = 위반(문법 오류 포함) | 2 = NOT_RUN(명부 없음·항목 0개)
#
# 파서 계약(이 밖의 형태는 전부 exit 1 — fail-closed · 2026-08-12 V1 D5·D6 반영):
#   항목은 `- id: 값`, 필드는 2칸 들여쓴 `key: 값`. 전체 줄 주석(#)과 빈 줄만 허용.
#   값은 "..." / '...' 로 정확히 감싸거나(닫힘 필수, 뒤에 아무것도 없어야), 영숫자·._- 만.
#   같은 항목에 같은 필드 2회 금지. 빈 값 = 누락. path 는 저장소 루트 기준 상대경로만
#   (절대경로·`..` 금지 — V1 D4). ci_mirror_job 은 stage:ci, manual_reason 은
#   stage:manual 에서만 허용(불일치 필드 = 위반). stage:ci 의 target 은 지정한
#   job 아래 step.run 에 있는 정확한 비주석 명령줄이어야 한다.
#
# ⚠️ bash 3.2 호환 — `${VAR^^}` 계열 금지(맥 기본 bash 실측 함정), 연관배열 금지.
set -uo pipefail

REGISTRY=${1:-docs/sot/mechanism-registry.yaml}
WORKFLOW_FILE=${WORKFLOW_FILE:-.github/workflows/verify.yml}

if [ ! -f "$REGISTRY" ]; then
  echo "NOT_RUN: 명부 없음 — $REGISTRY"
  echo "CHECKED: 0"
  exit 2
fi

fail=0
checked=0
syntax_fail=0
seen_ids=""

# 워크플로의 jobs: 키 목록 (규칙 4 대조용)
ci_jobs=""
if [ -f "$WORKFLOW_FILE" ]; then
  ci_jobs=$(awk '/^jobs:[[:space:]]*$/{f=1;next} f&&/^[^[:space:]]/{f=0} f&&/^  [A-Za-z0-9_-]+:[[:space:]]*$/{s=$1;sub(/:$/,"",s);print s}' "$WORKFLOW_FILE")
fi

# 값 검증 + 정제 — PV_VAL 에 결과. return 1 = 계약 밖 형태 (V1 D5: 미닫힘 따옴표·
# 인라인 주석·따옴표 섞임을 값에 흡수한 채 조용히 통과하던 것을 여기서 끊는다).
PV_VAL=""
parse_value() {
  local v="$1"
  PV_VAL=""
  if printf '%s' "$v" | grep -qE '^"[^"]*"$'; then
    PV_VAL=${v#\"}; PV_VAL=${PV_VAL%\"}; return 0
  fi
  if printf '%s' "$v" | grep -qE "^'[^']*'\$"; then
    PV_VAL=${v#\'}; PV_VAL=${PV_VAL%\'}; return 0
  fi
  if printf '%s' "$v" | grep -qE '^[A-Za-z0-9._-]+$'; then
    PV_VAL=$v; return 0
  fi
  return 1
}

# 현재 항목 상태
e_id="" e_path="" e_target="" e_stage="" e_required="" e_ci_job="" e_reason=""
e_keys="" in_entry=0

reset_entry() {
  e_id="" e_path="" e_target="" e_stage="" e_required="" e_ci_job="" e_reason=""
  e_keys=""
}

# 스키마 검증(규칙 1 + 필수 필드 + path 형태) — 위반 사유를 stdout 으로, return 1
validate_schema() {
  if [ -z "$e_id" ]; then echo "id 없음"; return 1; fi
  if printf '%s\n' "$seen_ids" | grep -qxF -- "$e_id"; then
    echo "id 중복 — $e_id"; return 1
  fi
  if [ -z "$e_path" ]; then echo "path 누락/빈 값"; return 1; fi
  if [ -z "$e_target" ]; then echo "target 누락/빈 값"; return 1; fi
  if [ -z "$e_stage" ]; then echo "stage 누락/빈 값"; return 1; fi
  if [ -z "$e_required" ]; then echo "required 누락/빈 값"; return 1; fi
  case "$e_required" in true|false) : ;; *) echo "required 값 오류 — $e_required"; return 1 ;; esac
  # V1 D4: 저장소 루트 기준 상대경로만 — 절대경로·상위 이동은 통제 범위 밖 파일을 가리킨다
  case "$e_path" in
    /*) echo "절대경로 금지 — $e_path (저장소 루트 기준 상대경로만)"; return 1 ;;
    ..*|*/..*|*/../*) echo "상위 이동(..) 금지 — $e_path"; return 1 ;;
  esac
  # V1 D5-d: stage 와 맞지 않는 필드는 오타·오해의 신호다 — 조용히 무시하지 않는다
  if [ -n "$e_ci_job" ] && [ "$e_stage" != "ci" ]; then
    echo "ci_mirror_job 은 stage:ci 전용 — stage:$e_stage 에 있음"; return 1
  fi
  if [ -n "$e_reason" ] && [ "$e_stage" != "manual" ]; then
    echo "manual_reason 은 stage:manual 전용 — stage:$e_stage 에 있음"; return 1
  fi
  # codeaudit 2026-08-12 AC-M-F3: 심볼릭 링크는 상대경로 검사(/*·..)를 우회해 저장소 밖
  # 실행파일을 가리킬 수 있다([ -x ]·[ -f ] 가 링크를 따라간다). 명부 항목은 저장소 안
  # 추적된 실제 파일이어야 하므로 링크 자체를 거부한다(재현성·통제 범위 유지).
  if [ -L "$e_path" ]; then echo "심볼릭 링크 금지 — $e_path (저장소 안 실제 파일만)"; return 1; fi
  if [ ! -f "$e_path" ]; then echo "path 실존하지 않음 — $e_path"; return 1; fi
  return 0
}

# stage 별 대조(규칙 3~5) — 위반 사유를 stdout 으로, return 1
ci_target_is_run_command() {
  local workflow="$1" job="$2" target="$3"
  case "$target" in
    'run: '*) target=${target#run: } ;;
  esac

  CI_JOB="$job" CI_TARGET="$target" ruby -ryaml -e '
    begin
      workflow = YAML.safe_load(
        File.read(ARGV.fetch(0)),
        permitted_classes: [],
        permitted_symbols: [],
        aliases: false
      )
      jobs = workflow.is_a?(Hash) ? workflow["jobs"] : nil
      selected = jobs.is_a?(Hash) ? jobs[ENV.fetch("CI_JOB")] : nil
      steps = selected.is_a?(Hash) ? selected["steps"] : nil
      exit 2 unless steps.is_a?(Array)

      target = ENV.fetch("CI_TARGET")
      found = steps.any? do |step|
        run = step.is_a?(Hash) ? step["run"] : nil
        next false unless run.is_a?(String)

        run.lines.any? do |line|
          command = line.strip
          !command.empty? && !command.start_with?("#") && command == target
        end
      end
      exit(found ? 0 : 1)
    rescue StandardError
      exit 2
    end
  ' "$workflow" 2>/dev/null
}

validate_stage() {
  case "$e_stage" in
    pre-commit|pre-push)
      if ! grep -qF -- "$e_target" "$e_path"; then
        echo "죽은 target — '$e_target' 이(가) $e_path 안에 없다"; return 1
      fi
      ;;
    ci)
      if [ -z "$e_ci_job" ]; then
        echo "stage:ci 인데 ci_mirror_job 누락"; return 1
      fi
      if ! printf '%s\n' "$ci_jobs" | grep -qxF -- "$e_ci_job"; then
        echo "ci_mirror_job '$e_ci_job' 이(가) $WORKFLOW_FILE 의 jobs: 키에 없다"; return 1
      fi
      # V1 D1 + codeaudit 2026-08-15 A2: 파일 전체 grep 은 target 이 주석에만 있어도
      # '실행 중'으로 오인했다. 지정 job 의 step.run 안에 있는 정확한 비주석 명령만 인정한다.
      if ! ci_target_is_run_command "$e_path" "$e_ci_job" "$e_target"; then
        echo "죽은 ci target — '$e_target' 이(가) $e_ci_job 작업의 실제 run 명령에 없다"; return 1
      fi
      ;;
    manual)
      if [ -z "$e_reason" ]; then
        echo "stage:manual 인데 manual_reason 누락 — 호출 검사 회피 금지"; return 1
      fi
      if [ ! -x "$e_path" ]; then
        echo "manual path 가 실행권한 없음 — $e_path"; return 1
      fi
      ;;
    *)
      echo "알 수 없는 stage — $e_stage"; return 1
      ;;
  esac
  return 0
}

rules_label() {
  case "$e_stage" in
    pre-commit|pre-push) printf '규칙 1·2·3' ;;
    ci)                  printf '규칙 1·2·4' ;;
    manual)              printf '규칙 1·2·5' ;;
  esac
}

flush_entry() {
  [ "$in_entry" -eq 1 ] || return 0
  checked=$((checked + 1))
  local bad=""
  bad=$(validate_schema)
  if [ -z "$bad" ]; then
    bad=$(validate_stage)
  fi
  seen_ids="$seen_ids
$e_id"
  if [ -z "$bad" ]; then
    printf 'PASS: %s (%s · %s)\n' "$e_id" "$e_stage" "$(rules_label)"
  else
    printf 'FAIL: %s — %s\n' "${e_id:-<id없음>}" "$bad"
    fail=1
  fi
  reset_entry
}

set_field() {
  local key="$1" val="$2"
  # V1 D5-a: 같은 필드 2회 = 마지막 값이 조용히 이기는 사고 — 중복 자체를 위반으로
  if printf '%s\n' "$e_keys" | grep -qxF -- "$key"; then
    echo "FAIL: 필드 중복 — ${e_id:-<id없음>} 의 $key"
    syntax_fail=1
    return
  fi
  e_keys="$e_keys
$key"
  case "$key" in
    path)          e_path="$val" ;;
    target)        e_target="$val" ;;
    stage)         e_stage="$val" ;;
    required)      e_required="$val" ;;
    ci_mirror_job) e_ci_job="$val" ;;
    manual_reason) e_reason="$val" ;;
    *) echo "FAIL: 알 수 없는 키 — $key"; syntax_fail=1 ;;
  esac
}

while IFS= read -r raw || [ -n "$raw" ]; do
  line=$(printf '%s' "$raw" | tr -d '\r')
  stripped=$(printf '%s' "$line" | sed 's/^[[:space:]]*//')
  case "$stripped" in ''|\#*) continue ;; esac
  case "$line" in
    '- id:'*)
      flush_entry
      in_entry=1
      rawval=$(printf '%s' "${line#- id:}" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
      if parse_value "$rawval"; then
        e_id="$PV_VAL"
        e_keys="id"
      else
        echo "FAIL: id 값이 계약 밖 형태 — $rawval"
        syntax_fail=1
      fi
      ;;
    '  '[a-z_]*:*)
      key=${stripped%%:*}
      rawval=$(printf '%s' "${stripped#*:}" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
      if parse_value "$rawval"; then
        set_field "$key" "$PV_VAL"
      else
        echo "FAIL: $key 값이 계약 밖 형태 — $rawval"
        syntax_fail=1
      fi
      ;;
    *)
      echo "FAIL: 파서 계약 밖의 줄 — $line"
      syntax_fail=1
      ;;
  esac
done < "$REGISTRY"
flush_entry
[ "$syntax_fail" -eq 1 ] && fail=1

# V1 D6: 문법 오류가 있으면 항목 0개여도 '검사 불능(2)'이 아니라 '위반(1)'이다 —
# 잘못 쓴 명부는 대응 주체가 다르다(작성자 수정 vs 환경 복구).
if [ "$checked" -eq 0 ]; then
  if [ "$syntax_fail" -eq 1 ]; then
    echo "CHECKED: 0"
    exit 1
  fi
  echo "NOT_RUN: 항목 0개 — 0건 대조로 통과는 금지한다 (P20)"
  echo "CHECKED: 0"
  exit 2
fi

printf 'CHECKED: %d\n' "$checked"
exit "$fail"
