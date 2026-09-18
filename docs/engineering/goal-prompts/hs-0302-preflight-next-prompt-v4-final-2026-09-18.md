# HS-03.02 사전검사기 — 비용 효율화 최종 프롬프트 v4 (2026-09-18, v2·v3 대체, /clear 뒤 그대로 붙여넣기)

## 결론

이 검사기에 대한 반복 검증(변이·생존·매트릭스·다중 LLM 검토)은 여기서 끝낸다. 남은 일은 하나다 — 실제 사고를 막는 검사는 남기고, 중복이거나 가치가 낮은 검사와 "검증을 검증하는" 구조는 뺀다. 검사 수·줄수 목표는 두지 않는다. 사장님께 오는 질문은 최대 둘이다: 사고 방어인데 대체 장치가 없는 검사를 뺄지(DECISION 항목, 한 단어), 그리고 배송 전 기준 브랜치 51커밋 처리.

## 프롬프트 본문

```text
$strict
대상: 워크트리 worktrees/hs0302-preflight-followup-20260917(브랜치 task/hs0302-preflight-followup-20260917, 기준 A task/hs-0302-r6-survivor-defenses-20260916). 검사기 scripts/verify/hs0302-closeout-preflight.sh, 인수 시험 scripts/acceptance-hs0302-preflight.sh, 명부 docs/sot/verification-commands.md, CI .github/workflows/verify.yml 의 해당 스텝. 과거 기록은 private-reviews/hs-0302/claude-preflight-followup-e36770d-2026-09-17/README.md 만 참고한다.

목표는 이 검사기를 완벽하게 증명하는 것이 아니라, 비용 대비 필요한 최소 마감 안전장치로 단순화하는 것이다. 이번 작업 이후 이 검사기에 대한 mutation/survivor 검증과 다중 LLM 검토는 종료한다.

원칙: 새 checker·ledger·contract·acceptance 파일·CI 계층을 만들지 않는다. 58/84 생존을 다시 0 으로 만들지 않는다. mutation matrix 를 다시 만들지 않는다. 검사기를 검사하기 위한 범용 프레임워크를 만들지 않는다. 실제 사고 기록이 있는 검사를 "복잡하다" 는 이유만으로 삭제하지 않되, 사고가 있었다는 이유만으로 영구 유지하지도 않는다. 기존 pre-push·CI·다른 검사가 같은 사고를 충분히 막으면 중복 검사는 삭제한다. 성공 기준은 검증 강도가 아니라 코드와 테스트의 실질적 축소다. 검사 수·줄수 목표("5~6개") 를 두지 않는다 — 필요한 것이 8개면 8개, 4개면 4개.

0단계: `bash scripts/verify/hs0302-closeout-preflight.sh --branch task/hs0302-preflight-followup-20260917 --base task/hs-0302-r6-survivor-defenses-20260916` 마지막 두 줄이 `CHECKED: N`·`VERDICT: PASS` 가 아니면 그 판정을 보고하고 멈춘다.

1단계 — 검사 분류(코드 수정 없음): FULL 11개(git.worktree git.branch git.clean git.base-ancestor git.prompt-tail proc.codex proc.cwd shm.ledger ac2.copy ac3.clone shm.post)와 --check-v1 5개(v1.sha v1.head v1.rc v1.verdict v1.venv-same) 각각에 세 가지만 판단한다. ① 없으면 잘못된 코드 또는 잘못된 실행환경의 결과가 PASS 되어 push·마감될 수 있는가 ② 실제 사고 때문에 생긴 검사인가(검사기 머리글 주석·README 로그·마감 프롬프트에서 인용) ③ 다른 기존 게이트가 같은 위험을 막는가(file:line). 분류는 KEEP / REMOVE / DECISION(사고 방어인데 대체 장치가 없어 삭제에 위험수용 결정 필요). 근거는 저장소 파일만 쓰고 새 검증·적대 리뷰를 돌리지 않는다. 표를 docs/engineering/hs-0302-preflight-surface-2026-09-18.md 에 쓰고 커밋한다. DECISION 이 있으면 그 항목(검사 이름·사고 한 줄)만 보고하고 멈춘다 — 사장님이 "삭제" 또는 "유지" 로 답한다.

2단계 — 최소 구현(한 커밋): KEEP 과 "유지" 답을 받은 검사만 남긴다. REMOVE 는 검사기·REQUIRED 목록·명부·CI 스텝 주석·마감 프롬프트의 검사 수에서 함께 제거한다. 새 추상화 없음. 인수 시험은 남은 검사에 대해서만 유지한다 — 검사마다 정상 → PASS, 잘못된 상태 → 그 검사의 FAIL 또는 BLOCKED 를 확인할 수 있으면 충분하다. 여러 검사가 같은 실패 경로를 공유하면 억지로 중복하지 않되, 어느 검사가 막았는지 구분이 필요하면 검사 이름을 확인한다. 무력화 반례(빈 파일·exit 0·VERDICT 문구만·필수 검사 삭제·자기 재호출)는 기존 것을 유지한다. 재귀·프로세스 폭주처럼 기계를 위험하게 할 수 있는 시험은 무제한 실행하지 않는다 — 인수 시험 전체를 `perl -e 'alarm shift; exec @ARGV' 600` 한 줄로 감싸는 것으로 충분하며 그 이상의 실행 프레임워크를 만들지 않는다. 커밋 메시지에 삭제한 검사와 ①~③ 근거를 한 줄씩 적는다(P13 이 검사 삭제에 근거를 요구한다).

3단계 — 검증 후 종료: 다음만 실행한다. `bash scripts/verify/run-acceptance.sh scripts/acceptance-hs0302-preflight.sh`, `bash scripts/acceptance-ci-step-integrity.sh`, `bash scripts/acceptance-principles-check.sh`, 최종 코드에서 0단계 명령(실제 환경 1회). 모두 PASS 면 자동 검증 종료. 실패가 나오면 그 실패만 고치고 관련 시험만 재실행한다. Codex·Claude 다중 적대검토, survivor-zero, mutation 재생성은 하지 않는다.

배송: 기준 브랜치 task/hs-0302-candidate-identity-20260914 가 원격보다 51커밋 앞서 있으므로 사장님이 "기준 브랜치 먼저 push 승인" 또는 "origin 기준 재배치 승인" 을 주기 전에는 push·PR 하지 않는다. 주면 hs-0302-r6-ship-prompt-2026-09-17.md 를 따르되 PR 본문에는 KEEP/REMOVE 목록과 3단계 결과만 적는다.

보고(그 외는 쓰지 않는다): KEEP / REMOVE / DECISION 목록 · 검사기와 인수 시험의 규모 변화(검사 수·줄수 전후) · 실행한 시험과 PASS/FAIL · 남은 현실적 위험 최대 3개 · 이 작업을 여기서 종료해도 되는지. 추가 아키텍처 개선, 새 검증 체계, 후속 mutation 작업은 제안하지 않는다.
```

→ v2·v3 는 이 파일로 대체된다. 결정 줄은 필요할 때(DECISION 보고 뒤, 배송 전)만 한 줄로 붙인다.
