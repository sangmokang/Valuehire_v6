# Claude V1-L — 혼합 Markdown fence 최종 재검증

V1-K가 찾은 혼합 fence 결함을 교정했습니다. 현재 공유 작업 트리를 읽기 전용으로 확인하십시오.
`scripts/check-docs-sot.sh`는 여는 fence 문자와 길이를 기억하고 같은 문자·같은 길이 이상에서만
닫아야 합니다.

반드시 정상 구조 검사, checker 500줄 경계, `git diff --check`를 확인하고 격리 사본에서 아래를
재현하십시오.

1. 실제 `docs/engineering/humansearch-l0-auth-surface-goal-2026-08-18.md`의 `~~~text` 블록 내부
   가짜 `## task/...` 앵커 참조는 FAIL.
2. 같은 혼합 블록이 닫힌 뒤 실제 `### Claude V1 — 증거 결함 보완 명령과 프롬프트` 앵커 참조는 PASS.
3. V1-J의 underscore·연속 하이픈 4종과 존재하지 않는 앵커 실패가 유지됨.

새 결함이 없으면 PASS, 있으면 FAIL입니다. 첫 줄 `VERDICT: PASS|FAIL`, 한국어 300단어 이내로
결론·증거·잔여 위험을 작성하십시오.
