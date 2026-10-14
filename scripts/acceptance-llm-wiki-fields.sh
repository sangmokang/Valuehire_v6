#!/usr/bin/env bash
# LLM 위키 필드 복구·감사기 인수 검사.
# ① 단위시험(네트워크 없음) — 건너뜀(skip) 0건·최소 건수 ② 보호 조건 변조가 "기대한 시험의 단언 실패"로 빨개지는지
#   (문법·import 오류 종료는 차단 증거로 세지 않음, 전체 출력 보존) ③ SOT 문턱 표의 필수 필드 집합.
# 종료값 0 = PASS, 1 = FAIL. V1 2026-10-14 결함 2·6 반영.
set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT" || { echo "VERDICT: FAIL (root 진입 실패)"; exit 1; }
fail=0
MIN_TESTS=25
LOGDIR="$(mktemp -d)"

run_tests() { env -u GIT_DIR -u GIT_WORK_TREE python3 -m unittest scripts.llm_wiki.test_backfill_structured_profiles scripts.llm_wiki.test_field_audit 2>&1 </dev/null; }

out="$(run_tests)"; rc=$?
ran="$(printf '%s\n' "$out" | sed -nE 's/^Ran ([0-9]+) tests?.*/\1/p' | tail -1)"
skipped="$(printf '%s\n' "$out" | sed -nE 's/.*skipped=([0-9]+).*/\1/p' | tail -1)"
if [ "$rc" -ne 0 ]; then echo "UNIT: FAIL rc=$rc"; printf '%s\n' "$out" | tail -20; fail=1; else echo "UNIT: PASS ran=${ran:-0}"; fi
if [ -z "${ran:-}" ] || [ "${ran:-0}" -lt "$MIN_TESTS" ]; then echo "UNIT_COUNT: FAIL ran=${ran:-0} < $MIN_TESTS"; fail=1; else echo "UNIT_COUNT: PASS ran=$ran"; fi
if [ -n "${skipped:-}" ] && [ "${skipped:-0}" -gt 0 ]; then echo "UNIT_SKIP: FAIL skipped=$skipped (건너뛴 시험은 실행이 아니다)"; fail=1; else echo "UNIT_SKIP: PASS skipped=0"; fi

# 변조: 보호 조건을 빼면 '기대한 시험'이 단언 실패로 빨개져야 한다. mktemp 사본에서만 수행.
mutate() { # $1 라벨, $2 파일, $3 sed 식, $4 기대 실패 시험 이름
  local tmp log; tmp="$(mktemp -d)"; log="$LOGDIR/$1.log"
  cp -R "$ROOT/scripts" "$tmp/scripts"; cp -R "$ROOT/docs" "$tmp/docs"
  find "$tmp" -name __pycache__ -type d -prune -exec rm -rf {} +
  sed -i.bak -E "$3" "$tmp/scripts/llm_wiki/$2" && rm -f "$tmp/scripts/llm_wiki/$2.bak"
  if cmp -s "$tmp/scripts/llm_wiki/$2" "$ROOT/scripts/llm_wiki/$2"; then echo "MUTATION[$1]: FAIL (변조가 적용되지 않음)"; fail=1; rm -rf "$tmp"; return; fi
  (cd "$tmp" && env -u GIT_DIR -u GIT_WORK_TREE python3 -m unittest scripts.llm_wiki.test_backfill_structured_profiles scripts.llm_wiki.test_field_audit </dev/null) > "$log" 2>&1
  local mrc=$?
  if [ "$mrc" -eq 0 ]; then echo "MUTATION[$1]: FAIL (변조가 살아남음)"; fail=1
  elif /usr/bin/grep -qE "SyntaxError|ImportError|ModuleNotFoundError|IndentationError" "$log"; then echo "MUTATION[$1]: FAIL (실행 오류로 종료 — 차단 증거 아님)"; tail -5 "$log"; fail=1
  elif ! /usr/bin/grep -qE "^(FAIL|ERROR): $4 " "$log"; then echo "MUTATION[$1]: FAIL (기대한 시험 $4 이 빨개지지 않음)"; /usr/bin/grep -E "^(FAIL|ERROR):" "$log" | head -5; fail=1
  else echo "MUTATION[$1]: PASS ($4 실패로 차단, log=$log)"
  fi
  rm -rf "$tmp"
}
mutate is_null_guard backfill_structured_profiles.py 's/&structured_json=is.null//' test_apply_guards_every_write_with_is_null_and_writes_ledger
mutate absent_row_fill backfill_structured_profiles.py 's/elif row.local_id not in remote_state:/elif False:/' test_selects_only_present_and_empty_remote_rows
mutate zero_total_pass field_audit.py 's/if not stat.total:/if stat.total is None:/' test_zero_total_is_fail_not_pass
mutate swallow_http_error backfill_structured_profiles.py 's/^([[:space:]]+)raise$/\1matched = 0/' test_intent_is_written_before_patch_and_error_is_recorded
mutate drop_hash_check backfill_structured_profiles.py 's/for key in \("source", "input_hash"\):/for key in ("source",):/' test_non_string_or_empty_hash_is_invalid
mutate duplicate_threshold field_audit.py 's/if key in found:/if False:/' test_duplicate_field_row_is_rejected

# SOT 문턱 표: 필수 필드 집합이 그대로 있어야 한다(개수만 세지 않음)
if python3 - <<'PY' </dev/null
from pathlib import Path
from scripts.llm_wiki.field_audit import parse_thresholds
t = parse_thresholds(Path("docs/sot/llm-wiki.md").read_text(encoding="utf-8"))
required = {("profile_archives", "structured_json"), ("pipeline_candidates", "ai_assessment"), ("pipeline_candidates", "resume_data"),
            ("pipeline_candidates", "email"), ("sourcing_results", "fit_reason"), ("gmail_derived_events", "candidate_id")}
missing = required - set(t)
assert not missing, f"필수 필드 누락: {sorted(missing)}"
PY
then echo "SOT_THRESHOLDS: PASS"; else echo "SOT_THRESHOLDS: FAIL"; fail=1; fi

if [ "$fail" -eq 0 ]; then echo "VERDICT: PASS"; rm -rf "$LOGDIR"; exit 0; else echo "VERDICT: FAIL (logs: $LOGDIR)"; exit 1; fi
