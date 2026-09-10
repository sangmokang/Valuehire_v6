# HS-00.04 구현 커밋 후 readback

## 결론

`PASS`. GREEN 구현 커밋 `95bb942b0ecda4b4b03e3e49dcc93d91b30bac48`의 대상 Git blob과 작업 파일 9개가 모두 같은 SHA-256이었다. 커밋된 상태에서 canonical 105건, 실제 verify workflow 32개 job·step, Strict 원칙 34개를 다시 실행해 모두 통과했다.

이 기록은 로컬 checkpoint다. 원격 push·draft PR·PR·merge·원격 CI·운영 쓰기는 실행하지 않았다.

## 커밋과 누적 범위

- 선행 완료: `c28270c1ea6153d4ea0aae83a8562981b2564269`.
- RED 최종 커밋: `c7c6332bc6debab5b83090ae0230f1de74b7f724`.
- GREEN 구현/증거 커밋: `95bb942b0ecda4b4b03e3e49dcc93d91b30bac48`.
- GREEN 커밋 자체: 8 files, 530 insertions, 18 deletions.
- HS-00.04 누적: 9 files, 893 insertions, 20 deletions. hard 3,000 미만이다.
- 직접 작성 코드: checker 280줄, acceptance 299줄. 각각 hard 600 미만이다.

## Git blob과 작업 파일 대조

```text
MATCH docs/engineering/humansearch-hs0004-goal-2026-09-10.md blob=94cfeee01d01a23825f9706d9f1fb145252e37257e8fd774f2f28e49e6871750 file=94cfeee01d01a23825f9706d9f1fb145252e37257e8fd774f2f28e49e6871750
MATCH docs/sot/verification-commands.md blob=9ba301fd782df45d3a4af6f85b5a85de861f2e9650a0747b6f39a1ae45852877 file=9ba301fd782df45d3a4af6f85b5a85de861f2e9650a0747b6f39a1ae45852877
MATCH scripts/acceptance-ci-step-integrity.sh blob=a179b235ace39c21a5ab08f5092207383edb0fc32a929dc9d083fc82a39dc906 file=a179b235ace39c21a5ab08f5092207383edb0fc32a929dc9d083fc82a39dc906
MATCH scripts/verify/check-ci-step-integrity.sh blob=2f48e44fb67def7832505b80d037c4a7217b946aea10b0fcf9df860eb8bba2fd file=2f48e44fb67def7832505b80d037c4a7217b946aea10b0fcf9df860eb8bba2fd
MATCH docs/engineering/evidence/hs0004-20260910/claude-v1-final-prompt.md blob=ee2a37446c5d81c76944ce9f9a2406d3ee03a951cbfb979c55e4e21556696040 file=ee2a37446c5d81c76944ce9f9a2406d3ee03a951cbfb979c55e4e21556696040
MATCH docs/engineering/evidence/hs0004-20260910/claude-v1-final-verdict.md blob=64ad2f305a78bacad362696f0958add56267eb580b9bda9312e1ae97eb7c21c9 file=64ad2f305a78bacad362696f0958add56267eb580b9bda9312e1ae97eb7c21c9
MATCH docs/engineering/evidence/hs0004-20260910/codeaudit-final-verdict.md blob=4217b02282fa7653b2bd8312c05f7c19bde96435264e6f7c937a0b475cb39a1c file=4217b02282fa7653b2bd8312c05f7c19bde96435264e6f7c937a0b475cb39a1c
MATCH docs/engineering/evidence/hs0004-20260910/codex-v2-final-verdict.md blob=4b87648c5ce377eaa92689ca446b6e2e3ad4526707db136a26d113e5769b7512 file=4b87648c5ce377eaa92689ca446b6e2e3ad4526707db136a26d113e5769b7512
MATCH docs/engineering/evidence/hs0004-20260910/verification-ledger.md blob=a08439d8bc4d300d48e9f3b5f25ddf275a3d75068bda133957d396b96e563e46 file=a08439d8bc4d300d48e9f3b5f25ddf275a3d75068bda133957d396b96e563e46
```

→ `git show HEAD:<path>`로 읽은 커밋 내용과 파일시스템의 현재 내용을 각각 SHA-256으로 계산했다. 9개 모두 `MATCH`여서 검증 뒤 바이트가 바뀌지 않았다.

## 커밋된 상태 재실행

```text
bash scripts/verify/run-acceptance.sh scripts/acceptance-ci-step-integrity.sh
CHECKED: 105
VERDICT: PASS
OK(run-acceptance): scripts/acceptance-ci-step-integrity.sh — 판정 106건, CHECKED 105

bash scripts/verify/check-ci-step-integrity.sh .github/workflows/verify.yml
PASS: TRIGGER_CONTRACT: push·pull_request·workflow_dispatch 시작 범위 유지
PASS: 조건부·오류무시 스텝 없음 (job·step 32개 검사)
CHECKED: 32

bash scripts/acceptance-principles-check.sh
VERDICT: PASS
MECHANISMS: PASS 34/34 strict-contract-bindings
WIRING: PASS pre-push=1 ci=1
CHECKED: 34
```

→ 구현 커밋에서 필수 trigger 삭제·축소·YAML 의미 충돌 반례 105개와 실제 workflow, 원칙 배선이 다시 통과했다. 종료값은 모두 0이었다.

## 참조와 작업공간 상태

```text
task HEAD  = 95bb942b0ecda4b4b03e3e49dcc93d91b30bac48
root main  = f12ea335a0fd323bb3eec3ca0e300ae1ca9b0717
origin/main = fc6beedc78019862bc2f1b3bf4c4ad3bbd8e845b
task vs main left/right = 13/47
task vs origin/main left/right = 12/47
git status --short = empty
```

→ 시작 시 root main과 origin/main은 모두 `fc6beedc...`였다. 작업 중 다른 로컬 작업으로 root main만 `f12ea335...`로 이동했으며, 이 WU는 recovery worktree와 전용 branch에서만 커밋했다. 원격 ref는 변하지 않았다.

## NOT_RUN과 남은 위험

- 원격 push·draft PR·PR·merge·원격 CI·운영 쓰기: `NOT_RUN` — 승인 범위 밖이다.
- Actions 활성화, branch protection, required checks, fork approval, commit-message skip: `NOT_RUN`/WU 제외다.
- inherited RED `6/31`, CI 담당 제외 `acceptance-0-7.sh`, `LC_ALL=C` Ruby inline Unicode, `%YAML 1.2`, 정확한 branches 형식, `ALLOWED_STEP_IF` 이름 재사용, Ruby 3.4 bundled `base64` 가용성은 후속 위험이다.
- 오염된 최초 lane `task/hs-0004-20260910`은 증거 보존만 하며 이 readback과 구현에 쓰지 않았다.
