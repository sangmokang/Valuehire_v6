#!/usr/bin/env bash
# LLM 위키 필드 복구·감사기 인수 검사.
# ① 두 단위시험 묶음 실행(네트워크 없음) ② 보호 조건 변조 2종이 각각 빨개지는지 확인 ③ SOT 문턱 표 파싱.
# 종료값 0 = PASS, 1 = FAIL. 처리한 시험 수를 출력하고 최소치 미만이면 FAIL(P20).
set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT" || { echo "VERDICT: FAIL (root 진입 실패)"; exit 1; }
fail=0
MIN_TESTS=14

run_tests() { python3 -m unittest scripts.llm_wiki.test_backfill_structured_profiles scripts.llm_wiki.test_field_audit 2>&1; }

out="$(run_tests)"; rc=$?
ran="$(printf '%s\n' "$out" | sed -nE 's/^Ran ([0-9]+) tests?.*/\1/p' | tail -1)"
if [ "$rc" -ne 0 ]; then echo "UNIT: FAIL rc=$rc"; printf '%s\n' "$out" | tail -20; fail=1; else echo "UNIT: PASS ran=${ran:-0}"; fi
if [ -z "${ran:-}" ] || [ "${ran:-0}" -lt "$MIN_TESTS" ]; then echo "UNIT_COUNT: FAIL ran=${ran:-0} < $MIN_TESTS"; fail=1; else echo "UNIT_COUNT: PASS ran=$ran"; fi

# 변조 시험: 보호 조건을 빼면 시험이 반드시 실패해야 한다. mktemp 사본에서만 수행.
mutate() { # $1 라벨, $2 파일, $3 sed 식
  local tmp; tmp="$(mktemp -d)"; cp -R "$ROOT/scripts" "$tmp/scripts"; cp -R "$ROOT/docs" "$tmp/docs"
  find "$tmp" -name __pycache__ -type d -prune -exec rm -rf {} +
  sed -i.bak -E "$3" "$tmp/scripts/llm_wiki/$2" && rm -f "$tmp/scripts/llm_wiki/$2.bak"
  if cmp -s "$tmp/scripts/llm_wiki/$2" "$ROOT/scripts/llm_wiki/$2"; then echo "MUTATION[$1]: FAIL (변조가 적용되지 않음)"; fail=1; rm -rf "$tmp"; return; fi
  if (cd "$tmp" && env -u GIT_DIR -u GIT_WORK_TREE python3 -m unittest scripts.llm_wiki.test_backfill_structured_profiles scripts.llm_wiki.test_field_audit >/dev/null 2>&1 </dev/null); then
    echo "MUTATION[$1]: FAIL (변조가 살아남음)"; fail=1
  else
    echo "MUTATION[$1]: PASS (변조 차단)"
  fi
  rm -rf "$tmp"
}
mutate is_null_guard backfill_structured_profiles.py 's/&structured_json=is.null//'
mutate zero_total_pass field_audit.py 's/if not stat.total:/if stat.total is None:/'

# SOT 문턱 표가 실제로 읽히는지(표 0행이면 FAIL)
if python3 - <<'PY' >/dev/null 2>&1
from pathlib import Path
from scripts.llm_wiki.field_audit import parse_thresholds
t = parse_thresholds(Path("docs/sot/llm-wiki.md").read_text(encoding="utf-8"))
assert len(t) >= 6, len(t)
PY
then echo "SOT_THRESHOLDS: PASS"; else echo "SOT_THRESHOLDS: FAIL"; fail=1; fi

if [ "$fail" -eq 0 ]; then echo "VERDICT: PASS"; exit 0; else echo "VERDICT: FAIL"; exit 1; fi
