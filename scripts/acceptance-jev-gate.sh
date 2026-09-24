#!/usr/bin/env bash
# acceptance-jev-gate.sh — .claude/hooks/jev-command-gate.mjs 계약 회귀 검사.
#   계약: docs/sot/hook-contracts.md "`.claude/hooks/jev-command-gate.mjs`"
#   실제 Vercel AI Gateway 대신 로컬 mock 서버(JEV_ENDPOINT)로 요청 모양과 판정 분기를 검사한다.
#   종료: 0 = 전부 통과 | 1 = 하나라도 실패 | 3 = 환경 부재(node 없음 · mock 기동 실패)
set -uo pipefail

REPO=$(git rev-parse --show-toplevel)
cd "$REPO" || exit 2
HOOK=.claude/hooks/jev-command-gate.mjs

if ! command -v node >/dev/null 2>&1; then
  echo "BLOCKED: node 없음 — 훅을 실행할 수 없다" >&2
  exit 3
fi

fail=0
checked=0
pass() { checked=$((checked + 1)); printf 'PASS: %s\n' "$1"; }
bad()  { checked=$((checked + 1)); fail=1; printf 'FAIL: %s\n' "$1" >&2; }

work=$(mktemp -d) || { echo "BLOCKED: 임시 경로 생성 실패" >&2; exit 3; }
trap 'kill "$mock_pid" 2>/dev/null; rm -rf "$work"' EXIT

# mock: 명령 문자열에 따라 확률을 돌려주고, 요청 헤더·본문 모양이 틀리면 400 을 낸다.
cat > "$work/mock.mjs" <<'JS'
import { createServer } from 'node:http';
import { writeFileSync } from 'node:fs';
const srv = createServer(async (req, res) => {
  let s = '';
  for await (const c of req) s += c;
  const body = JSON.parse(s);
  const okShape = req.headers['ai-model-id'] === 'typesafe-ai/jev'
    && req.headers.authorization === 'Bearer vck_test'
    && body.questions?.destructive?.type === 'boolean'
    && typeof body.state === 'string';
  if (!okShape) { res.writeHead(400); res.end('bad shape'); return; }
  if (body.state.includes('explode')) { res.writeHead(500); res.end('boom'); return; }
  const p = body.state.includes('truncate') ? 0.78 : body.state.includes('garbage') ? 'x' : 0.04;
  res.writeHead(200, { 'content-type': 'application/json' });
  res.end(JSON.stringify({ answers: { destructive: { type: 'boolean', probability: p } } }));
});
srv.listen(0, '127.0.0.1', () => writeFileSync(process.argv[2], String(srv.address().port)));
JS
node "$work/mock.mjs" "$work/port" &
mock_pid=$!
for _ in $(seq 1 50); do [ -s "$work/port" ] && break; sleep 0.1; done
if [ ! -s "$work/port" ]; then echo "BLOCKED: mock 서버 기동 실패" >&2; exit 3; fi
URL="http://127.0.0.1:$(cat "$work/port")/"

# run <env...> -- <command>  → stdout 을 $out, 종료값을 $rc 에
run() {
  local envs=()
  while [ "$1" != "--" ]; do envs+=("$1"); shift; done
  shift
  local payload
  payload=$(node -e 'process.stdout.write(JSON.stringify({session_id:process.argv[2]+Math.random(),tool_name:"Bash",tool_input:{command:process.argv[1]}}))' "$1" "s")
  out=$(printf '%s' "$payload" | env -u AI_GATEWAY_API_KEY TMPDIR="$work" JEV_ENDPOINT="$URL" "${envs[@]}" node "$HOOK" 2>"$work/err")
  rc=$?
}

run AI_GATEWAY_API_KEY=vck_test -- 'truncate -s 0 app.db'
if [ "$rc" -eq 0 ] && printf '%s' "$out" | grep -q '"permissionDecision":"deny"' && printf '%s' "$out" | grep -q '0.78'; then
  pass "위험도 0.78 ≥ 0.45 → deny, 사유에 확률 기재"
else bad "파괴 명령이 차단되지 않음 (rc=$rc out=$out)"; fi

run AI_GATEWAY_API_KEY=vck_test JEV_GATE_ACTION=ask -- 'truncate -s 0 app.db'
if printf '%s' "$out" | grep -q '"permissionDecision":"ask"'; then pass "JEV_GATE_ACTION=ask → ask"
else bad "ask 모드 미적용 (out=$out)"; fi

run AI_GATEWAY_API_KEY=vck_test -- 'sed -n 1,20p README.md'
if [ "$rc" -eq 0 ] && [ -z "$out" ]; then pass "위험도 0.04 → 출력 없음(allow 를 내지 않고 일반 권한 흐름 유지)"
else bad "안전 명령에 결정이 출력됨 (rc=$rc out=$out)"; fi

run AI_GATEWAY_API_KEY=vck_test JEV_GATE_THRESHOLD=0.9 -- 'truncate -s 0 app.db'
if [ -z "$out" ]; then pass "JEV_GATE_THRESHOLD=0.9 → 0.78 통과"
else bad "기준선 설정 미적용 (out=$out)"; fi

run -- 'truncate -s 0 app.db'
if [ "$rc" -eq 0 ] && printf '%s' "$out" | grep -q 'NOT_RUN: AI_GATEWAY_API_KEY 없음'; then pass "키 없음 → systemMessage NOT_RUN (조용한 통과 아님)"
else bad "키 없음이 드러나지 않음 (rc=$rc out=$out)"; fi

run JEV_GATE_ON_ERROR=closed -- 'ls'
if printf '%s' "$out" | grep -q '"permissionDecision":"deny"'; then pass "키 없음 + ON_ERROR=closed → deny"
else bad "fail-closed 미적용 (out=$out)"; fi

run AI_GATEWAY_API_KEY=vck_test -- 'explode'
if printf '%s' "$out" | grep -q 'NOT_RUN: HTTP 500'; then pass "게이트웨이 500 → NOT_RUN 알림"
else bad "HTTP 오류가 드러나지 않음 (out=$out)"; fi

run AI_GATEWAY_API_KEY=vck_test -- 'garbage'
if printf '%s' "$out" | grep -q 'NOT_RUN: 응답에 destructive 확률이 없음'; then pass "확률 필드 이상 → NOT_RUN 알림"
else bad "잘못된 응답이 통과로 처리됨 (out=$out)"; fi

run AI_GATEWAY_API_KEY=vck_wrong -- 'truncate -s 0 app.db'
if printf '%s' "$out" | grep -q 'NOT_RUN: HTTP 400'; then pass "요청 모양·키 불일치 → mock 거부가 드러남"
else bad "요청 모양 검사 실패 (out=$out)"; fi

run AI_GATEWAY_API_KEY=vck_test JEV_GATE=off -- 'truncate -s 0 app.db'
if [ -z "$out" ]; then pass "JEV_GATE=off → 게이트 비활성"
else bad "opt-out 미적용 (out=$out)"; fi

run AI_GATEWAY_API_KEY=vck_test JEV_GATE_THRESHOLD=abc -- 'ls'
if [ "$rc" -ne 0 ] && grep -q '잘못된 설정값' "$work/err"; then pass "잘못된 기준선 → 오류 종료(stderr)"
else bad "잘못된 설정이 조용히 기본값으로 대체됨 (rc=$rc)"; fi

if ! grep -q 'jev-command-gate.mjs' .claude/settings.json; then bad ".claude/settings.json 에 훅 미등록"
else pass ".claude/settings.json 에 PreToolUse 훅 등록"; fi

echo "CHECKED: $checked"
exit "$fail"
