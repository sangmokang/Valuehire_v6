# ValueHire v6 strict delivery chain — Pull Request 초안

## 원격 경계

- PR: `NOT_RUN`
- CI: `NOT_RUN`
- Merge: `NOT_RUN`
- Deploy: `NOT_RUN`
- Live Verify: `NOT_RUN`
- checkpoint readiness: `NOT_RUN`
- overall T: `NOT_RUN`

push, PR 생성·수정, merge, deploy는 사용자 승인 전 실행 금지다. 로컬 GREEN은 GitHub CI GREEN을 대신하지 않는다.

## Base 사전 조건

2026-08-27 로컬 refs 기준으로 이 브랜치는 `origin/main`보다 6커밋 뒤이고 18커밋 앞이다. 기반인 `rescue/main-mixed-20260825T200952`의 5커밋도 `origin/main`에 없다. 따라서 base 이력을 먼저 정리하거나 승인된 PR 대상을 확정하기 전에는 아래 원격 명령을 실행하지 않는다.

- PR 생성 명령: `BLOCKED`
- 예상 base 후보: `main`
- head: `task/wu3b-delivery-chain-20260827`
- 예상 결과: 승인된 base 이력 위에 이 브랜치 변경만 포함하는 OPEN PR과 실제 GitHub check rollup 생성

승인과 base 확정 뒤 준비된 명령:

```bash
git push -u origin task/wu3b-delivery-chain-20260827
gh pr create --base main --head task/wu3b-delivery-chain-20260827 --title "검증 결과를 변경 후보와 끝까지 묶는다" --body-file docs/engineering/valuehire-delivery-chain-pr-draft-2026-08-27.md
gh pr view <실제-PR-번호> --json title,body,url,statusCheckRollup
```

## Pull Request 본문

### 왜 필요한가

작업 폴더에서 run ledger나 secret pattern을 완화해 거짓 합격을 만들 수 있었고, Issue부터 WU 커밋·검증·PR/CI·merge 이후 운영 증거까지 같은 후보에 묶는 검증 가능한 사슬이 없었다.

### 변경 요약

- checkpoint scope는 명시적 run/WU ID가 가리키는 Git index ledger 한 개만 사용한다.
- secret pattern은 index blob 또는 승인 SHA가 일치하는 입력만 사용한다.
- Issue, branch/worktree, RED/GREEN commit, 명령·시간·종료값·전체 출력 hash를 pinned evidence commit으로 검증한다.
- G/V1/V2와 candidate SHA를 하나의 T 계약에 묶고 stale·무출력·부분 출력·누락 공격을 차단한다.
- PR/CI/merge/deploy/live verify 상태를 분리하고 merge 전 readiness와 overall T를 `NOT_RUN`으로 고정한다.
- pre-push와 GitHub workflow에 새 acceptance를 배선하되 실제 원격 CI 결과는 PR 생성 뒤에만 기록한다.

### 검증 계획

- 요청된 원명령 7개와 checkpoint delivery acceptance를 최종 candidate SHA에서 재실행한다.
- hard 600/601, 대문자 `.JS/.TSX`, no-op mutation 5종, ledger/secret decoy, trace 변조 반례를 확인한다.
- Claude V1과 새 맥락 Codex V2가 같은 candidate와 T를 독립 검증한다.
- 실제 PR 번호가 생긴 뒤에만 `gh pr view ... statusCheckRollup`을 실행하고 GitHub CI 판정을 갱신한다.

### 롤백

병합 전에는 브랜치와 worktree를 폐기한다. 병합 뒤에는 WU GREEN 커밋을 역순으로 revert하고 동일 acceptance를 재실행한다. 실패 evidence는 삭제하지 않고 새 rollback record로 남긴다.

### 현재 판정

원격 PR·CI와 사용자 merge가 없으므로 `REQUEST_CHANGES`다. Deploy와 Live Verify는 merge 이후 별도 증거가 생기기 전까지 `NOT_RUN`이다.
