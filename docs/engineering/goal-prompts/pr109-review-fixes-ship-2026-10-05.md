# PR #109 리뷰 수정 배송 프롬프트 (2026-10-05 작성)

/strict

## 결론
PR #109(`task/jev-shadow-base-split`, HEAD 6ce1e6a) 위에 쌓인 리뷰 수정 브랜치 `task/pr109-review-fixes` 를 PR #109 로 배송한다. 코드 작업은 끝났고(V1 FAIL→수정→V2 PASS), 남은 일은 사장님 승인 후 push·원격 CI 확인뿐이다.

## 0단계 — 착수 전 실측 (불일치하면 멈추고 보고)
1. `git -C worktrees/pr109-review-fixes log --oneline 6ce1e6a..HEAD` 가 이 브랜치 커밋만 보여주는지, `git status --porcelain` 이 비었는지.
2. `gh pr view 109 --json headRefOid,state` 의 headRefOid 가 여전히 6ce1e6a 인지(다르면 다른 세션이 push 한 것 — rebase 판단을 사장님께 올린다).
3. `git diff --stat 6ce1e6a..HEAD` 가 7개 파일(goal 2개 문서 포함 시 8개)뿐이고 PR #123(llmcodereview 스킬) 파일이 섞이지 않았는지.
4. 실행 중인 codex/claude 세션이 같은 워크트리를 쓰지 않는지(`lsof -Fpcn` + awk 로 cwd 확인).

## 1단계 — 배송 (사장님 승인 필요)
- 권고안: `git push origin task/pr109-review-fixes:task/jev-shadow-base-split` (fast-forward). 강제 push 금지.
- 대안: `task/pr109-review-fixes` 를 별도 브랜치로 올려 base=`task/jev-shadow-base-split` 인 하위 PR 을 연다(리뷰 단위 분리, 대신 병합 2번).
- pre-push 훅이 verify.sh + acceptance 전량을 돈다. `--no-verify` 금지.

## 2단계 — 원격 확인
- `gh pr checks 109` 를 push 이벤트와 pull_request 이벤트로 나눠 본다.
- 알려진 빨간불: 9/15 만료 억제(suppressions.yaml) 스캔 — 이 PR 결함이 아니다. HumanSearch G2 단계(gates·mutations 6/6·antiforge 3/3)가 초록인지가 이 PR 판정 기준이다.
- PR 본문에 §8-8 형식으로 D1~D7 상태 표, V1/V2 판정 요약, 미룬 S3(D8 시험 잠금, D9 as_of 기본값, D10 순서 중복·문서 AC, argparse 오류 JSON 경계) 를 적고 `gh pr view 109 --json body` 로 다시 읽는다.

## 3단계 — 후속(별도 작업 단위)
- S3 묶음: D8(hash 출처·SDK 전달값 시험 잠금), argparse 오류를 JSON 경계로(사용자 동작 변경이므로 사장님 확인 후).
- close 실패 경고를 출력 ledger 필드로 올릴지(스키마 변경) 여부 — 운영에서 stderr 수집이 안 되면 검토.

## 근거 위치
- goal: docs/engineering/pr109-review-fixes-goal-2026-10-05.md (AC1~AC9, 적대 검증 로그)
- 판정 원문: private-reviews/pr109-review-fixes/V1-VERDICT.md, V2-VERDICT.md (gitignore)
