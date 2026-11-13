#!/usr/bin/env bash
# 인수 검사: 로컬 산출물 폴더(/audit_work/, /.playwright-mcp/)는 git 이 무시한다.
# 근거: docs/engineering/ignore-local-scratch-goal-2026-11-14.md (P21 — 후보자 PII 데이터는 git 에 넣지 않는다)
# counter-AC: 최상위 앵커만 무시해야 한다 — 하위 경로의 같은 이름 폴더(정상 소스)는 무시되면 안 된다.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
fail=0

# AC: 최상위 산출물 경로는 무시된다
for p in audit_work/candidates_raw.csv audit_work/progress.json .playwright-mcp/page-x.yml .playwright-mcp/console-x.log; do
  if ! git check-ignore -q --no-index "$p"; then
    echo "FAIL: $p 가 무시되지 않음 (PII/도구 산출물 커밋 위험)"; fail=1
  fi
done

# counter-AC: 하위 경로의 같은 이름은 무시되면 안 된다 (조용한 소스 누락 방지, P3)
for p in docs/audit_work/note.md humansearch/.playwright-mcp/fixture.yml; do
  if git check-ignore -q --no-index "$p"; then
    echo "FAIL: $p 가 무시됨 (앵커 누락 — 정상 소스가 조용히 사라짐)"; fail=1
  fi
done

[ "$fail" -eq 0 ] && echo "PASS: acceptance-ignore-local-scratch"
exit "$fail"
