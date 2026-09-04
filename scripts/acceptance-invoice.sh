#!/usr/bin/env bash
# acceptance-invoice.sh — Invoice 스킬의 계산·입력·계약·플랫폼 동등성 회귀 검사.
set -uo pipefail

REPO=$(git rev-parse --show-toplevel)
cd "$REPO" || exit 2

fail=0
checked=0
record_pass() {
  checked=$((checked + 1))
  printf 'PASS: %s\n' "$1"
}
record_fail() {
  checked=$((checked + 1))
  fail=1
  printf 'FAIL: %s\n' "$1" >&2
}

required_files=(
  contracts/invoice/invoice-v1.json
  contracts/invoice/deduction-v1.json
  contracts/invoice/storage-v1.json
  docs/sot/invoice.md
  docs/sot/invoice-storage.md
  supabase/migrations/20260901090000_invoice_fee_agreements_and_storage.sql
  supabase/migrations/20260901100000_invoice_fee_agreement_immutability.sql
  supabase/migrations/20260901103000_invoice_fee_agreement_idempotent_upsert.sql
  supabase/migrations/20260902090000_invoice_runtime_integrity.sql
  tools/invoice/generate_invoice.py
  tools/invoice/generate_deduction.py
  tools/invoice/storage_common.py
  tools/invoice/storage_schema.py
  tools/invoice/storage_agreements.py
  tools/invoice/storage_remote.py
  tools/invoice/store_invoice_set.py
  tools/invoice/tests/test_generate_invoice.py
  tools/invoice/tests/test_generate_deduction.py
  tools/invoice/tests/test_store_invoice_set.py
  tools/invoice/tests/assert_contract_snapshot.py
  tools/invoice/tests/postgres_fixture.sql
  tools/invoice/tests/postgres_runtime_assertions.sql
  tools/invoice/tests/test_postgres_integrity.sh
  scripts/verify/check-invoice-gate.py
  .codex/skills/invoice/SKILL.md
  .codex/skills/invoice/agents/openai.yaml
  .claude/skills/invoice/SKILL.md
  .claude/skills/invoice/agents/openai.yaml
)
missing=()
for path in "${required_files[@]}"; do
  [ -f "$path" ] || missing+=("$path")
done
if [ "${#missing[@]}" -eq 0 ]; then
  record_pass "Invoice 정본·렌더러·Codex/Claude 스킬 필수 파일 ${#required_files[@]}개 존재"
else
  record_fail "Invoice 필수 파일 누락: ${missing[*]}"
fi

test_log=$(mktemp) || {
  echo "FAIL: 테스트 출력 임시 파일을 만들 수 없다"
  exit 2
}
trap 'rm -f "$test_log"' EXIT
python3 -m unittest discover -s tools/invoice/tests -v >"$test_log" 2>&1
test_rc=$?
cat "$test_log"
if [ "$test_rc" -eq 0 ] && grep -Eq '^Ran [1-9][0-9]* tests?' "$test_log" && grep -Eq '^OK$' "$test_log"; then
  record_pass "계산·기한·입력 거부·계약 변조·HTML 필수 필드 회귀 테스트"
else
  record_fail "Invoice 회귀 테스트 실패 또는 테스트 0건"
fi

postgres_rc=0
bash tools/invoice/tests/test_postgres_integrity.sh
postgres_rc=$?
if [ "$postgres_rc" -eq 0 ]; then
  record_pass "PostgreSQL 마이그레이션·동시성·저장 RPC·전달 영수증 실증"
else
  record_fail "PostgreSQL 런타임 무결성 검사 실패"
fi

gate_rc=0
python3 scripts/verify/check-invoice-gate.py || gate_rc=$?
if [ "$gate_rc" -eq 0 ]; then
  record_pass "Invoice 단위·PostgreSQL 검사의 독립 CI 배선"
else
  record_fail "Invoice 테스트 게이트 배선 누락 또는 위조 가능"
fi

if python3 -m py_compile \
  tools/invoice/generate_invoice.py tools/invoice/generate_deduction.py \
  tools/invoice/storage_common.py tools/invoice/storage_schema.py \
  tools/invoice/storage_agreements.py tools/invoice/storage_remote.py \
  tools/invoice/store_invoice_set.py scripts/verify/check-invoice-gate.py \
  tools/invoice/tests/test_generate_invoice.py tools/invoice/tests/test_generate_deduction.py \
  tools/invoice/tests/test_store_invoice_set.py \
  tools/invoice/tests/assert_contract_snapshot.py; then
  record_pass "Invoice Python 문법 검사"
else
  record_fail "Invoice Python 문법 검사 실패"
fi

if cmp -s .codex/skills/invoice/SKILL.md .claude/skills/invoice/SKILL.md \
  && cmp -s .codex/skills/invoice/agents/openai.yaml .claude/skills/invoice/agents/openai.yaml; then
  record_pass "Codex와 Claude Invoice 스킬·UI 메타데이터 바이트 동등"
else
  record_fail "Codex와 Claude Invoice 스킬이 서로 다름"
fi

size_log=$(python3 - <<'PY'
import ast
from pathlib import Path

files = (
    Path("tools/invoice/generate_invoice.py"),
    Path("tools/invoice/generate_deduction.py"),
    Path("tools/invoice/store_invoice_set.py"),
    Path("tools/invoice/storage_common.py"),
    Path("tools/invoice/storage_schema.py"),
    Path("tools/invoice/storage_agreements.py"),
    Path("tools/invoice/storage_remote.py"),
    Path("tools/invoice/tests/test_generate_invoice.py"),
    Path("tools/invoice/tests/test_generate_deduction.py"),
    Path("tools/invoice/tests/test_store_invoice_set.py"),
    Path("tools/invoice/tests/assert_contract_snapshot.py"),
    Path("scripts/verify/check-invoice-gate.py"),
    Path(".codex/skills/invoice/SKILL.md"),
    Path(".claude/skills/invoice/SKILL.md"),
)
violations = []
for path in files:
    lines = len(path.read_text(encoding="utf-8").splitlines())
    print(f"SIZE: {path} {lines}/600")
    if lines > 600:
        violations.append(f"{path}: {lines} lines")

for path in (item for item in files if item.suffix == ".py"):
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            length = (node.end_lineno or node.lineno) - node.lineno + 1
            if length > 100:
                violations.append(f"{path}:{node.lineno} {node.name}: {length} lines")

if violations:
    print("\n".join(f"LIMIT_FAIL: {item}" for item in violations))
    raise SystemExit(1)
print("LIMIT_PASS: direct files <=600 lines and Python functions <=100 lines")
PY
)
size_rc=$?
printf '%s\n' "$size_log"
if [ "$size_rc" -eq 0 ] && grep -q '^LIMIT_PASS:' <<<"$size_log"; then
  record_pass "P11 파일·함수 크기 상한"
else
  record_fail "P11 파일·함수 크기 상한 위반"
fi

if ! command -v rg >/dev/null 2>&1; then
  record_fail "미완성 표식 검사기 rg를 실행할 수 없음"
else
  rg -n 'TODO|FIXME|NotImplementedError' \
    contracts/invoice docs/sot/invoice.md docs/sot/invoice-storage.md \
    supabase/migrations \
    tools/invoice .codex/skills/invoice .claude/skills/invoice
  marker_rc=$?
  if [ "$marker_rc" -eq 0 ]; then
    record_fail "Invoice 범위에 미완성 표식 존재"
  elif [ "$marker_rc" -eq 1 ]; then
    record_pass "Invoice 범위에 TODO·FIXME·미구현 표식 없음"
  else
    record_fail "미완성 표식 검사가 종료값 $marker_rc 로 실패"
  fi
fi

if [ "$fail" -ne 0 ]; then
  echo "VERDICT: FAIL"
  echo "CHECKED: $checked"
  exit 1
fi

echo "VERDICT: PASS"
echo "CHECKED: $checked"
