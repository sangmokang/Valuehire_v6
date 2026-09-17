# HS-03.02 사전검사기 — 다음 실행 프롬프트 v1 (2026-09-17, /clear 뒤 그대로 붙여넣기)

## 결론

사전검사기 작업은 로컬 검증과 독립 검증(Codex 여덟 회, 감사 세 종류)을 거쳐 코드 결함 0, 회귀 반례 33종으로 봉인된 상태다. 아직 하지 않은 것은 셋이다: 원격에 올리기(사람 승인), 두 번째 독립 검증(새 맥락 변이 생성), 리눅스 서버에서 새 검사가 실제로 도는지 보기. 이 프롬프트는 그 셋을 순서대로 닫는다. 사장님이 결정할 것은 두 개다 — 묶음 두 개를 그대로 올릴지 합칠지, 원격 올리기를 승인할지.

## 프롬프트 본문

```text
$strict
대상: 묶음 A `task/hs-0302-r6-survivor-defenses-20260916`(6df142c, 워크트리 worktrees/hs-0302-r6-survivor-defenses-20260916)와 묶음 B `task/hs0302-preflight-followup-20260917`(워크트리 worktrees/hs0302-preflight-followup-20260917, 기준 A). 제품 코드·인수 스크립트·정본은 바꾸지 않는다. 검증 증거 장부는 묶음 B 의 private-reviews/hs-0302/claude-preflight-followup-*/README.md (gitignored) — 그 적대 검증 로그 표를 먼저 읽고, 그 표에 없는 결과를 지어내지 않는다.
0단계(착수 자격): 두 워크트리에서 각각 `bash scripts/verify/hs0302-closeout-preflight.sh`(묶음 B 는 `--branch task/hs0302-preflight-followup-20260917 --base task/hs-0302-r6-survivor-defenses-20260916`). 마지막 두 줄이 `CHECKED: N`·`VERDICT: PASS` 가 아니면 마지막 줄의 판정을 그대로(FAIL 이면 대상 수정, BLOCKED 면 환경 복구) 보고하고 멈춘다. proc.codex 가 BLOCKED 면 `ps -axo pid,ppid,command | grep -E '[c]odex (app-server|exec)'` 로 부모가 launchd(1)이고 broker.sock 클라이언트가 0 인 고아 Codex 플러그인 트리인지 확인하고, 맞을 때만 사람이 정리한 뒤 재실행한다(검사기가 죽이지 않는다).
1단계(V2 — 새 맥락 에이전트, 판정은 파일로): 묶음 B 의 검사기(scripts/verify/hs0302-closeout-preflight.sh)와 인수 시험(scripts/acceptance-hs0302-preflight.sh)을 대상으로, 인수 시험의 반례 33종은 대조군으로만 쓰고 검사기의 방어 지점(분류 분기·지문·트랩·필수 이름 장부·꼬리·재귀 방지·클론/사본 검사)마다 목록에 없는 새 변이를 만들어 원본 밖 클론에서 `bash scripts/verify/run-acceptance.sh scripts/acceptance-hs0302-preflight.sh`(기대 CHECKED 41) 가 각각 FAIL 하는지 본다. 결과는 `private-reviews/hs-0302/v2-mutations-<SHA 앞 7자>.tsv`(변이 ID·파일:줄·diff 요약·rc·잡은 반례 번호·등가 여부). 생존 1건이라도 있으면 그것을 반례로 봉인하는 커밋 뒤 V1 재판정 — 생존 0 이 될 때까지. 무거운 실행은 하나씩만(이 기계는 메모리가 부족해 스윕과 codex 를 동시에 돌리면 시스템이 죽인다).
2단계(배송): 배송 프롬프트 docs/engineering/goal-prompts/hs-0302-r6-ship-prompt-2026-09-17.md(v3, 묶음 B 판)를 그대로 따른다 — 결정 ①(그대로/합쳐서) ②(push 승인) 없이는 0단계까지만. push 는 사람이 직접, PR 두 개는 Draft, 본문 "확인하지 못한 부분" 에 V2 결과·리눅스 CI 결과·억제 만료·--check-v1 출처 한계(자기 신고, V2 로 보완)를 적는다.
3단계(리눅스 실측): 두 PR 의 `gh pr checks` 에서 새 스텝 "인수 검사 hs0302-preflight" 의 결과를 따로 읽는다. 빨강이면 러너 로그의 FAIL 줄을 그대로 옮기고 고치지 않는다(GNU stat/ipcs 형식 차이면 검사기 머리글의 한계 조항과 대조).
4단계(마감 진입): 두 PR 이 사람 검토·병합된 뒤 새 세션에서 마감 프롬프트 docs/engineering/goal-prompts/hs-0302-r6-next-prompt-2026-09-16.md(v5.8)를 붙여넣는다. 그 전에는 마감 검증을 시작하지 않는다.
보고: 1 0단계 두 결과 2 V2 변이 수·생존·봉인 커밋 3 결정 ①② 실행 여부와 두 최종 SHA(로컬=원격) 4 PR 번호·본문 readback 5 CI 상태(이벤트별, 새 스텝 따로) 6 남은 위험 7 다음 행동. "push 가능" 은 승인이 아니며 사람 지시를 기다린다.
```

→ 위 블록이 붙여넣을 프롬프트 전체다. 결정 ①② 는 프롬프트 뒤에 "합쳐서 push 승인" 또는 "그대로 push 승인" 한 줄로 붙인다. 없으면 V2(1단계)까지만 하고 멈춘다.
