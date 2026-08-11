#!/usr/bin/env bash
# check-mechanism-registry.sh — 검사 장치 명부가 실제 장치와 일치하는지 대조한다 (AC-M)
#
# 계약: docs/engineering/verify-ac-m-goal-2026-08-12.md §⑩
#   정본: docs/engineering/verify-unification-goal-2026-08-10.md:78-81
#   입력 : $1 = 명부 경로 (기본 docs/sot/mechanism-registry.yaml)
#          WORKFLOW_FILE = CI 워크플로 경로 (기본 .github/workflows/verify.yml)
#   출력 : 항목마다 PASS:/FAIL:, 마지막 줄 `CHECKED: <항목 수>`
#   exit : 0 = 전부 통과 | 1 = 위반 | 2 = NOT_RUN(명부 없음·항목 0개)
#
# 파서 계약(이 밖의 형태는 전부 exit 1 — fail-closed):
#   항목은 `- id: 값` 으로 시작하고, 필드는 2칸 들여쓴 `key: 값`.
#   전체 줄 주석(#)과 빈 줄만 허용. 값의 앞뒤 따옴표는 벗겨 비교. 빈 값 = 누락.
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
seen_ids=""

# 워크플로의 jobs: 키 목록 (규칙 4 대조용)
ci_jobs=""
if [ -f "$WORKFLOW_FILE" ]; then
  ci_jobs=$(awk '/^jobs:[[:space:]]*$/{f=1;next} f&&/^[^[:space:]]/{f=0} f&&/^  [A-Za-z0-9_-]+:[[:space:]]*$/{s=$1;sub(/:$/,"",s);print s}' "$WORKFLOW_FILE")
fi

unquote() {
  local v="$1"
  case "$v" in
    \"*\") v=${v#\"}; v=${v%\"} ;;
    \'*\') v=${v#\'}; v=${v%\'} ;;
  esac
  printf '%s' "$v"
}

# 현재 항목 상태
e_id="" e_path="" e_target="" e_stage="" e_required="" e_ci_job="" e_reason=""
in_entry=0

reset_entry() { e_id="" e_path="" e_target="" e_stage="" e_required="" e_ci_job="" e_reason=""; }

flush_entry() {
  [ "$in_entry" -eq 1 ] || return 0
  checked=$((checked + 1))
  local bad=""

  # 규칙 1 — id 유일성 + 필수
  if [ -z "$e_id" ]; then
    bad="id 없음"
  elif printf '%s\n' "$seen_ids" | grep -qxF -- "$e_id"; then
    bad="id 중복 — $e_id"
  fi
  seen_ids="$seen_ids
$e_id"

  # 필수 필드 (빈 값 = 누락)
  if [ -z "$bad" ]; then
    if [ -z "$e_path" ]; then bad="path 누락/빈 값"
    elif [ -z "$e_target" ]; then bad="target 누락/빈 값"
    elif [ -z "$e_stage" ]; then bad="stage 누락/빈 값"
    elif [ -z "$e_required" ]; then bad="required 누락/빈 값"
    fi
  fi
  if [ -z "$bad" ]; then
    case "$e_required" in true|false) : ;; *) bad="required 값 오류 — $e_required" ;; esac
  fi

  # 규칙 2 — path 실존
  if [ -z "$bad" ] && [ ! -f "$e_path" ]; then
    bad="path 실존하지 않음 — $e_path"
  fi

  # 규칙 3~5 — stage 별 대조 (알 수 없는 stage 는 조용히 skip 하지 않는다)
  if [ -z "$bad" ]; then
    case "$e_stage" in
      pre-commit|pre-push)
        if ! grep -qF -- "$e_target" "$e_path"; then
          bad="죽은 target — '$e_target' 이(가) $e_path 안에 없다"
        fi
        ;;
      ci)
        if [ -z "$e_ci_job" ]; then
          bad="stage:ci 인데 ci_mirror_job 누락"
        elif ! printf '%s\n' "$ci_jobs" | grep -qxF -- "$e_ci_job"; then
          bad="ci_mirror_job '$e_ci_job' 이(가) $WORKFLOW_FILE 의 jobs: 키에 없다"
        fi
        ;;
      manual)
        if [ -z "$e_reason" ]; then
          bad="stage:manual 인데 manual_reason 누락 — 호출 검사 회피 금지"
        elif [ ! -x "$e_path" ]; then
          bad="manual path 가 실행권한 없음 — $e_path"
        fi
        ;;
      *)
        bad="알 수 없는 stage — $e_stage"
        ;;
    esac
  fi

  if [ -z "$bad" ]; then
    printf 'PASS: %s (%s)\n' "$e_id" "$e_stage"
  else
    printf 'FAIL: %s — %s\n' "${e_id:-<id없음>}" "$bad"
    fail=1
  fi
  reset_entry
}

syntax_fail=0
while IFS= read -r raw || [ -n "$raw" ]; do
  line=$(printf '%s' "$raw" | tr -d '\r')
  # 전체 줄 주석·빈 줄
  case "$line" in
    ''|\#*|[[:space:]]*\#*)
      stripped=$(printf '%s' "$line" | sed 's/^[[:space:]]*//')
      case "$stripped" in ''|\#*) continue ;; esac
      ;;
  esac
  stripped=$(printf '%s' "$line" | sed 's/^[[:space:]]*//')
  [ -z "$stripped" ] && continue
  case "$line" in
    '- id:'*)
      flush_entry
      in_entry=1
      e_id=$(unquote "$(printf '%s' "${line#- id:}" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')")
      ;;
    '  '[a-z_]*:*)
      key=${stripped%%:*}
      val=$(unquote "$(printf '%s' "${stripped#*:}" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')")
      case "$key" in
        path)          e_path="$val" ;;
        target)        e_target="$val" ;;
        stage)         e_stage="$val" ;;
        required)      e_required="$val" ;;
        ci_mirror_job) e_ci_job="$val" ;;
        manual_reason) e_reason="$val" ;;
        *) echo "FAIL: 알 수 없는 키 — $key"; syntax_fail=1 ;;
      esac
      ;;
    *)
      echo "FAIL: 파서 계약 밖의 줄 — $line"
      syntax_fail=1
      ;;
  esac
done < "$REGISTRY"
flush_entry
[ "$syntax_fail" -eq 1 ] && fail=1

if [ "$checked" -eq 0 ]; then
  echo "NOT_RUN: 항목 0개 — 0건 대조로 통과는 금지한다 (P20)"
  echo "CHECKED: 0"
  exit 2
fi

printf 'CHECKED: %d\n' "$checked"
exit "$fail"
