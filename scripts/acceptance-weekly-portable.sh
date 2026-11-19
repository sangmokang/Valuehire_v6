#!/usr/bin/env bash
set -euo pipefail

ROOT=$(git rev-parse --show-toplevel)
CODEX="$ROOT/.codex/skills/weekly/SKILL.md"
CLAUDE="$ROOT/.claude/skills/weekly/SKILL.md"
PROMPT="$ROOT/docs/engineering/weekly-portable-validation-prompt-2026-11-09-v2.2.md"
fail=0

for path in "$CODEX" "$CLAUDE" "$PROMPT"; do
  if [ ! -s "$path" ]; then
    echo "FAIL: 공용 Weekly 파일이 없거나 비어 있음: ${path#"$ROOT"/}"
    fail=1
  fi
done
[ "$fail" -eq 0 ] || exit 1

if ! cmp -s "$CODEX" "$CLAUDE"; then
  echo "FAIL: Codex와 Claude Weekly 스킬이 서로 다름"
  fail=1
fi

for url in \
  'https://app.notion.com/p/valueconnect/FY26W45-406345c17dca81a8951cc7f778b91c48' \
  'https://app.notion.com/p/valueconnect/FY26W46-40d345c17dca8194995ccd15dd9c1210' \
  'https://admin.valuehire.cc'; do
  if ! grep -Fq "$url" "$PROMPT"; then
    echo "FAIL: 공용 프롬프트에 검증 기준 URL이 없음: $url"
    fail=1
  fi
done

for phrase in '같은 기간' 'cutoff' '공통 ID' '미검증' 'W45는 원형' 'live 형식 사례'; do
  if ! grep -Fq "$phrase" "$PROMPT"; then
    echo "FAIL: 공용 프롬프트에 대사/역할 조건이 없음: $phrase"
    fail=1
  fi
done

[ "$fail" -eq 0 ] || exit 1
echo 'PASS: Weekly prompt source, Codex/Claude parity, sample references, and admin reconciliation contract'
