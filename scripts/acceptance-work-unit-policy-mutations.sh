#!/usr/bin/env bash
# 구조화된 Work Unit 정책의 값·순서·스키마·생성 문서 변조를 격리 사본에서 공격한다.
set -uo pipefail

unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE GIT_OBJECT_DIRECTORY \
  GIT_ALTERNATE_OBJECT_DIRECTORIES GIT_COMMON_DIR GIT_PREFIX GIT_QUARANTINE_PATH

REPO=$(git rev-parse --show-toplevel 2>/dev/null) || {
  echo "VERDICT: NOT_RUN"
  echo "REASON: not a git repository"
  echo "CHECKED: 0"
  exit 2
}
cd "$REPO" || exit 2

POLICY=docs/sot/work-unit-policy.yaml
DOCUMENT=docs/sot/work-unit-policy.md
CHECKER=scripts/verify/check-work-unit-policy.rb
for required in "$POLICY" "$DOCUMENT" "$CHECKER"; do
  if [ ! -f "$required" ] || [ -L "$required" ] || [ ! -s "$required" ]; then
    printf 'VERDICT: FAIL\nREQUIRED_FILE_INVALID: %s\nCHECKED: 0\n' "$required"
    exit 1
  fi
done

SNAPSHOT=$(git status --porcelain=v1)
TMP=$(mktemp -d "${TMPDIR:-/tmp}/work-unit-policy.XXXXXX") || exit 2
case "$(basename "$TMP")" in
  work-unit-policy.*) ;;
  *) echo "VERDICT: NOT_RUN"; echo "REASON: unsafe temp path $TMP"; exit 2 ;;
esac
trap 'rm -rf "$TMP"' EXIT HUP INT TERM

fail=0
checked=0

run_check() {
  local policy="$1" document="$2" wanted="$3" pattern="$4" label="$5"
  local rc=0 output=""
  checked=$((checked + 1))
  output=$(ruby "$CHECKER" "$policy" "$document" 2>&1) || rc=$?
  if [ "$rc" -eq "$wanted" ] && printf '%s\n' "$output" | grep -q "$pattern"; then
    printf 'PASS: %s — exit=%s\n' "$label" "$rc"
  else
    printf 'FAIL: %s — expected exit=%s pattern=%s actual=%s\n%s\n' \
      "$label" "$wanted" "$pattern" "$rc" "$output"
    fail=1
  fi
}

new_policy() {
  local name="$1"
  cp "$POLICY" "$TMP/$name.yaml"
  printf '%s' "$TMP/$name.yaml"
}

run_check "$POLICY" "$DOCUMENT" 0 '^VERDICT: PASS$' "정상 정책"

p=$(new_policy claims_two)
ruby -e 'p=ARGV[0]; s=File.read(p).sub("claims_per_unit: 1", "claims_per_unit: 2"); File.write(p,s)' "$p"
run_check "$p" "$DOCUMENT" 1 'POLICY_VALUE_INVALID: work_unit.claims_per_unit' "한 단위에 주장 두 개"

p=$(new_policy units_six)
ruby -e 'p=ARGV[0]; s=File.read(p).sub("max_units_per_pr: 5", "max_units_per_pr: 6"); File.write(p,s)' "$p"
run_check "$p" "$DOCUMENT" 1 'POLICY_VALUE_INVALID: work_unit.max_units_per_pr' "PR 상한 여섯 개"

p=$(new_policy hours_49)
ruby -e 'p=ARGV[0]; s=File.read(p).sub("max_branch_lifetime_hours: 48", "max_branch_lifetime_hours: 49"); File.write(p,s)' "$p"
run_check "$p" "$DOCUMENT" 1 'POLICY_VALUE_INVALID: work_unit.max_branch_lifetime_hours' "브랜치 수명 49시간"

p=$(new_policy gate_missing)
ruby -e 'p=ARGV[0]; s=File.read(p).sub(/^    - integrated_adversarial\n/, ""); File.write(p,s)' "$p"
run_check "$p" "$DOCUMENT" 1 'POLICY_VALUE_INVALID: pull_request.final_gates' "전체 적대검증 삭제"

p=$(new_policy gate_reordered)
ruby -e 'p=ARGV[0]; s=File.read(p).sub("    - strict\n    - codeaudit\n", "    - codeaudit\n    - strict\n"); File.write(p,s)' "$p"
run_check "$p" "$DOCUMENT" 1 'POLICY_VALUE_INVALID: pull_request.final_gates' "strict와 codeaudit 순서 반전"

p=$(new_policy document_review)
ruby -e 'p=ARGV[0]; s=File.read(p).sub("document_review_can_pass: false", "document_review_can_pass: true"); File.write(p,s)' "$p"
run_check "$p" "$DOCUMENT" 1 'POLICY_VALUE_INVALID: review.high_risk.document_review_can_pass' "문서 검토만으로 고위험 통과"

p=$(new_policy paid_review)
ruby -e 'p=ARGV[0]; s=File.read(p).sub("paid_external_review_required: false", "paid_external_review_required: true"); File.write(p,s)' "$p"
run_check "$p" "$DOCUMENT" 1 'POLICY_VALUE_INVALID: review.high_risk.paid_external_review_required' "유료 외부 검토 필수화"

p=$(new_policy high_risk_path)
ruby -e 'p=ARGV[0]; s=File.read(p).sub(/^      - "hooks\/\*\*"\n/, ""); File.write(p,s)' "$p"
run_check "$p" "$DOCUMENT" 1 'POLICY_VALUE_INVALID: review.high_risk.paths' "고위험 hooks 경로 삭제"

p=$(new_policy completion_missing)
ruby -e 'p=ARGV[0]; s=File.read(p).sub(/^    - completion_commit\n/, ""); File.write(p,s)' "$p"
run_check "$p" "$DOCUMENT" 1 'POLICY_VALUE_INVALID: work_unit.completion_requires' "완료 커밋 삭제"

p=$(new_policy rollback_unit)
ruby -e 'p=ARGV[0]; s=File.read(p).sub("squash_rollback_boundary: pull_request", "squash_rollback_boundary: work_unit"); File.write(p,s)' "$p"
run_check "$p" "$DOCUMENT" 1 'POLICY_VALUE_INVALID: pull_request.squash_rollback_boundary' "squash 롤백 경계 과장"

p=$(new_policy missing_key)
ruby -e 'p=ARGV[0]; s=File.read(p).sub(/^  claims_per_unit: 1\n/, ""); File.write(p,s)' "$p"
run_check "$p" "$DOCUMENT" 1 'POLICY_SCHEMA_INVALID: work_unit' "필수 키 삭제"

p=$(new_policy duplicate_key)
ruby -e 'p=ARGV[0]; s=File.read(p).sub("  claims_per_unit: 1\n", "  claims_per_unit: 1\n  claims_per_unit: 1\n"); File.write(p,s)' "$p"
run_check "$p" "$DOCUMENT" 1 'POLICY_DUPLICATE_KEY:' "중복 키 추가"

p=$(new_policy unknown_key)
ruby -e 'p=ARGV[0]; s=File.read(p).sub("version: 1\n", "version: 1\nunknown_escape: true\n"); File.write(p,s)' "$p"
run_check "$p" "$DOCUMENT" 1 'POLICY_SCHEMA_INVALID: root' "알 수 없는 키 추가"

p=$(new_policy syntax_error)
ruby -e 'p=ARGV[0]; File.write(p, File.read(p) + "broken: [\n")' "$p"
run_check "$p" "$DOCUMENT" 1 'POLICY_YAML_INVALID:' "YAML 문법 오류"

cp "$DOCUMENT" "$TMP/document-exception.md"
ruby -e 'p=ARGV[0]; File.write(p, File.read(p) + "\n긴급할 때는 전체 적대검증을 건너뛰어도 된다.\n")' "$TMP/document-exception.md"
run_check "$POLICY" "$TMP/document-exception.md" 1 'DOCUMENT_OUT_OF_SYNC:' "생성 문서에 동의어 예외 추가"

cp "$DOCUMENT" "$TMP/document-review.md"
ruby -e 'p=ARGV[0]; File.write(p, File.read(p) + "\n고위험 작업은 문서 REVIEW만으로 완료 처리할 수 있다.\n")' "$TMP/document-review.md"
run_check "$POLICY" "$TMP/document-review.md" 1 'DOCUMENT_OUT_OF_SYNC:' "생성 문서에 문서 검토 예외 추가"

cp "$DOCUMENT" "$TMP/document-claims.md"
ruby -e 'p=ARGV[0]; File.write(p, File.read(p) + "\n문서 전용 Work Unit은 두 주장을 포함해도 된다.\n")' "$TMP/document-claims.md"
run_check "$POLICY" "$TMP/document-claims.md" 1 'DOCUMENT_OUT_OF_SYNC:' "생성 문서에 다중 주장 예외 추가"

after=$(git status --porcelain=v1)
checked=$((checked + 1))
if [ "$after" = "$SNAPSHOT" ]; then
  echo "PASS: SOURCE-TREE 원본 저장소 상태 불변"
else
  echo "FAIL: SOURCE-TREE 원본 저장소 상태 변경"
  fail=1
fi

printf 'CHECKED: %d\n' "$checked"
if [ "$fail" -eq 0 ]; then
  echo "VERDICT: PASS"
else
  echo "VERDICT: FAIL"
fi
exit "$fail"
