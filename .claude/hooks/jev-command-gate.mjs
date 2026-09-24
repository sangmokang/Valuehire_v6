#!/usr/bin/env node
// jev-command-gate — Bash 도구 PreToolUse 훅. 실행 직전의 셸 명령을 Jev(TypeSafe AI)에
// 물어 "기존 데이터를 복구 불가능하게 지우거나 덮어쓰는가" 확률을 받고, 기준선 이상이면 차단한다.
//
// 호출 경로: Vercel AI Gateway (Hobby 무료 티어에서도 Jev 제공). 의존성 0개, Node 20+ 내장 fetch.
//   AI_GATEWAY_API_KEY   vercel.com/ai-gateway 에서 발급한 vck_ 키 (필수)
//   JEV_GATE_THRESHOLD   차단 기준선. 기본 0.45
//   JEV_GATE_ACTION      deny(기본) | ask — 기준선 이상일 때 차단할지 사람에게 물을지
//   JEV_GATE_ON_ERROR    open(기본) | closed — 키 없음·호출 실패 시 통과시킬지 막을지
//   JEV_GATE_TIMEOUT_MS  호출 제한 시간. 기본 5000
//   JEV_GATE             off 이면 게이트를 끈다 (명시적 opt-out)
//   JEV_ENDPOINT         엔드포인트 교체 (테스트용 mock 서버)
//
// 계약: docs/sot/hook-contracts.md "`.claude/hooks/jev-command-gate.mjs`"
//   기준선 미만   → 출력 없음, exit 0. 일반 권한 흐름을 그대로 탄다 (allow 를 내지 않는다)
//   기준선 이상   → permissionDecision=deny(또는 ask) + 확률을 사유에 적는다
//   판정 불가     → 조용히 통과하지 않는다. systemMessage 로 "NOT_RUN: <사유>" 를 알린다 (P3)

import { existsSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

const DEFAULT_ENDPOINT = 'https://ai-gateway.vercel.sh/v4/ai/evaluation-model';
const ENDPOINT = process.env.JEV_ENDPOINT === undefined ? DEFAULT_ENDPOINT : process.env.JEV_ENDPOINT;
const ACTION = process.env.JEV_GATE_ACTION === 'ask' ? 'ask' : 'deny';
const FAIL_CLOSED = process.env.JEV_GATE_ON_ERROR === 'closed';
// 숫자 설정은 main() 안에서 읽는다. 여기서 던지면 아래 catch 를 거치지 않고 죽는다.
let THRESHOLD;
let TIMEOUT_MS;

const QUESTION = {
  type: 'boolean',
  instructions: [
    '이 셸 명령을 그대로 실행하면, 이미 존재하는 파일·디렉터리·데이터베이스·설정·git 이력이',
    '복구 불가능하게 삭제되거나, 비워지거나, 통째로 덮어써지는가?',
    '읽기 전용 명령(cat, sed -n, tail, grep, ls, git status/log/diff), 새 파일 생성,',
    '평소의 git add/commit/push, 패키지 설치, 테스트 실행은 해당하지 않는다.',
    '스크립트나 압축 해제처럼 파괴 동작이 안에 숨어 있을 수 있으면 그 가능성까지 따진다.',
  ].join(' '),
};

function parseRatio(raw, fallback, max = 1) {
  if (raw === undefined || raw.trim() === '') return fallback;
  const v = Number.parseFloat(raw);
  if (!Number.isFinite(v) || v < 0 || v > max) {
    throw new Error(`잘못된 설정값: ${raw}`);
  }
  return v;
}

function emit(obj) {
  process.stdout.write(JSON.stringify(obj) + '\n');
}

function decide(decision, reason) {
  emit({ hookSpecificOutput: { hookEventName: 'PreToolUse', permissionDecision: decision, permissionDecisionReason: reason } });
}

// 판정하지 못했다는 사실은 반드시 드러낸다. 다만 키가 없는 상태에서 Bash 호출마다
// 같은 경고를 내면 소음이므로, 같은 세션·같은 사유는 한 번만 알린다.
function notRun(reason, sessionId) {
  if (FAIL_CLOSED) {
    decide('deny', `jev 게이트 NOT_RUN (${reason}) — JEV_GATE_ON_ERROR=closed 이므로 차단합니다.`);
    return;
  }
  const marker = join(tmpdir(), `jev-gate-${(typeof sessionId === 'string' ? sessionId : 'nosession').replace(/[^\w-]/g, '_')}-${reason.replace(/[^\w가-힣-]/g, '_').slice(0, 60)}`);
  if (existsSync(marker)) return;
  try {
    writeFileSync(marker, '');
  } catch (e) {
    process.stderr.write(`jev 게이트: 경고 중복 억제 파일을 만들지 못했습니다 (${e.message}). 경고가 반복될 수 있습니다.\n`);
  }
  emit({ systemMessage: `jev 게이트 NOT_RUN: ${reason} — 파괴 명령 위험도 검사 없이 진행합니다.` });
}

async function readStdin() {
  let s = '';
  for await (const c of process.stdin) s += c;
  return s;
}

async function ask(command, key) {
  const ac = new AbortController();
  const timer = setTimeout(() => ac.abort(), TIMEOUT_MS);
  let res;
  try {
    res = await fetch(ENDPOINT, {
      method: 'POST',
      signal: ac.signal,
      headers: {
        authorization: `Bearer ${key}`,
        'content-type': 'application/json',
        'ai-evaluation-model-specification-version': '4',
        'ai-gateway-protocol-version': '0.0.1',
        'ai-model-id': 'typesafe-ai/jev',
      },
      body: JSON.stringify({ state: `셸 명령:\n${command}`, questions: { destructive: QUESTION }, providerOptions: {} }),
    });
  } catch (e) {
    throw new Error(ac.signal.aborted ? `${TIMEOUT_MS}ms 초과` : `연결 실패: ${e.message}`);
  } finally {
    clearTimeout(timer);
  }
  const text = await res.text();
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  let body;
  try {
    body = JSON.parse(text);
  } catch {
    throw new Error('응답이 JSON 이 아님');
  }
  const p = body?.answers?.destructive?.probability;
  if (typeof p !== 'number' || !Number.isFinite(p) || p < 0 || p > 1) {
    throw new Error('응답에 destructive 확률이 없음');
  }
  return p;
}

async function main() {
  THRESHOLD = parseRatio(process.env.JEV_GATE_THRESHOLD, 0.45);
  TIMEOUT_MS = Math.max(500, Math.trunc(parseRatio(process.env.JEV_GATE_TIMEOUT_MS, 5000, Infinity)));
  const input = JSON.parse(await readStdin());
  if (process.env.JEV_GATE === 'off') return;
  if (input.tool_name !== 'Bash') return;
  const command = input.tool_input?.command;
  if (typeof command !== 'string' || !command.trim()) return;

  const key = process.env.AI_GATEWAY_API_KEY?.trim();
  if (!key) {
    notRun('AI_GATEWAY_API_KEY 없음', input.session_id);
    return;
  }

  let p;
  try {
    p = await ask(command, key);
  } catch (e) {
    notRun(e.message, input.session_id);
    return;
  }

  if (p >= THRESHOLD) {
    decide(ACTION, `jev 위험도 ${p.toFixed(2)} ≥ 기준선 ${THRESHOLD} — 기존 데이터를 복구 불가능하게 지우거나 덮어쓸 수 있는 명령입니다. 백업·범위 축소·읽기 전용 대안을 먼저 검토하세요. (끄려면 JEV_GATE=off)`);
  }
}

main().catch((e) => {
  // 입력이나 설정이 깨진 경우. 조용히 통과하지 않고 stderr 로 알리되, 훅 오류(exit 1)는 도구 실행을 막지 않는다.
  process.stderr.write(`jev 게이트 오류: ${e.message}\n`);
  process.exit(FAIL_CLOSED ? 2 : 1);
});
