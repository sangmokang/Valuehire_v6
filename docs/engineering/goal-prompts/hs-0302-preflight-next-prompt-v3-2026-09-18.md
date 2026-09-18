# HS-03.02 사전검사기 — 다음 실행 프롬프트 v3 (2026-09-18, 비용 우선판, /clear 뒤 그대로 붙여넣기)

## 결론

v2 를 대체한다. 검증 루프(변이 생성·매트릭스·3중 검토)는 여기서 멈춘다. 할 일은 둘뿐이다 — 검사기를 마감 판정에 실제로 필요한 항목만 남기고, 그 항목마다 반례 하나씩만 둔다. 사고 기록이 있는 검사는 "다른 게이트가 대신 막는다" 는 근거가 없으면 지우지 않는다(지우는 것은 그 사고 재발을 승인하는 결정이므로 사장님 몫). 독립 검증은 마지막에 Codex 한 번이다.

## 프롬프트 본문

```text
$strict
대상: 묶음 B `task/hs0302-preflight-followup-20260917`(워크트리 worktrees/hs0302-preflight-followup-20260917, 기준 A 6df142c). 검사기 scripts/verify/hs0302-closeout-preflight.sh(408줄), 인수 시험 scripts/acceptance-hs0302-preflight.sh(402줄). 증거 장부 private-reviews/hs-0302/claude-preflight-followup-e36770d-2026-09-17/README.md 의 표만 참고하고 새 검토를 만들지 않는다. 금지: 새 checker·ledger·contract 계층, 새 CI 스텝, 새 acceptance 파일, 변이 생성·매트릭스·에이전트 다중 검토. 무거운 실행은 하나씩. grep 은 /usr/bin/grep, timeout 은 perl -e 'alarm shift; exec @ARGV' N.

0단계(10분): `bash scripts/verify/hs0302-closeout-preflight.sh --branch task/hs0302-preflight-followup-20260917 --base task/hs-0302-r6-survivor-defenses-20260916` 마지막 두 줄 `CHECKED: N`·`VERDICT: PASS` 아니면 그 판정 그대로 보고하고 멈춘다. `bash scripts/verify/run-acceptance.sh scripts/acceptance-hs0302-preflight.sh` rc 0·CHECKED 44 를 기준선으로 적는다.

1단계(설계 표 1개, 코드 수정 없음): 필수 검사 11개(git.worktree git.branch git.clean git.base-ancestor git.prompt-tail proc.codex proc.cwd shm.ledger ac2.copy ac3.clone shm.post)와 --check-v1 5개(v1.sha v1.head v1.rc v1.verdict v1.venv-same)를 한 표로 만든다. 열은 넷 — ① 없으면 잘못된 코드가 마감·push 되는가(예/아니오, 한 줄 근거) ② 이 검사를 넣게 한 사고(README 적대 검증 로그·검사기 머리글 주석·마감 프롬프트에서 인용, 없으면 "없음") ③ 대신 막는 기존 게이트(pre-push·CI·다른 acceptance, file:line; 없으면 "없음") ④ 처분: 유지 / 삭제 / 사장님 결정. 규칙: ①예 → 유지. ①아니오이고 ②없음 → 삭제. ①아니오인데 ②있음이고 ③없음 → "사장님 결정"(삭제 = 그 사고 재발 승인). 표를 docs/engineering/hs-0302-preflight-surface-goal-2026-09-18.md 에 쓰고 커밋한 뒤, "사장님 결정" 행이 하나라도 있으면 그 행만 보고하고 멈춘다. 없으면 2단계로.

2단계(축소 구현, 한 커밋): 삭제 처분 검사를 검사기에서 지우고 REQUIRED_FULL·REQUIRED_V1·정본 명부(docs/sot/verification-commands.md 해당 행)·CI 스텝 주석·마감 프롬프트의 검사 수를 같은 커밋에서 맞춘다. 인수 시험은 다시 쓴다 — 남은 검사마다 정확히 두 줄: 대상이 틀린 반례 1(기대 FAIL:<이름>), 조회가 죽은 반례 1(기대 BLOCKED:<이름>; 조회가 없는 검사는 생략). run_case 는 기대 "판정:이름" 을 받아 그 줄이 출력에 있어야 통과(엉뚱한 이유로 잡힘 방지). 정상 사본 PASS 1, 무력화 반례(빈 파일·exit 0·VERDICT 문구만·필수 검사 삭제·자기 재호출) 5 는 유지. 전체 제한시간 하나(perl alarm 600 → 초과 시 `FAIL: TIMEOUT` 줄·rc 1). 그 밖의 반례는 지운다. 커밋 메시지에 삭제한 검사와 ①~③ 근거를 한 줄씩 적는다(P13 검사 약화 근거).
AC(전부 명령·기대값): (a) 새 인수 시험 rc 0, CHECKED = 남은 검사 수×2 − 조회 없는 검사 수 + 7(정상 1·무력화 5·TIMEOUT 1) 로 계산해 그 숫자를 적는다. (b) 남은 검사마다 그 검사의 분류 줄을 fail→pass 로 바꾼 사본이 인수 시험 FAIL 이 되는지 한 번씩(N번, 각 30초, 직렬). (c) 두 파일 각각 ≤ 600줄이고 이전보다 짧다. (d) `bash scripts/acceptance-ci-step-integrity.sh`·`bash scripts/acceptance-principles-check.sh` PASS. (e) 실제 환경 1회: 워크트리 B 에서 0단계 명령 전부 PASS.

3단계(독립 검증 1회): 격리 --no-local 클론에서 `codex exec -s workspace-write` + stdin </dev/null 로 V1 한 번. 판정은 private-reviews/hs-0302/codex-v1-<SHA 7자>.md 첫 줄. FAIL 이면 결함을 고치고 한 번만 재판정, 그래도 FAIL 이면 결함 목록만 보고하고 멈춘다. V2 는 하지 않는다.

배송: 기준 브랜치 task/hs-0302-candidate-identity-20260914 가 원격보다 51커밋 앞서 있다. 사장님이 "기준 브랜치 먼저 push 승인" 또는 "origin 기준 재배치 승인" 을 주기 전에는 push·PR 하지 않는다. 주면 hs-0302-r6-ship-prompt-2026-09-17.md v3 를 따르되 PR 본문 "확인하지 못한 부분" 에 삭제한 검사 목록과 V1 결과만 적는다.

보고(세 줄): 1 유지/삭제/결정 검사 수와 두 파일 줄수 2 AC (a)~(e) 결과와 V1 첫 줄 3 사장님 결정 필요 항목(있으면 1~2개).
```

→ 결정 줄은 블록 뒤에 붙인다. 1단계에서 "사장님 결정" 행이 나오면 검사 이름과 사고 한 줄만 보고하고 멈추니, 그때 "삭제" 또는 "유지" 한 단어로 답하면 된다. 배송 결정 ③(기준 브랜치)은 별도.
