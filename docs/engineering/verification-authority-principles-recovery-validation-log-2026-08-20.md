# 원칙 게이트 복구 실행 장부 — 2026-08-20

## 결론

누락된 원칙 검증 묶음은 현재 작업공간에 복구됐고 로컬 구현 검사는 모두 통과했다. 독립 검증 한 단계가 비용 잔액 부족으로 실행되지 않아 전체 엄격 판정만 실패로 닫혔다.

이 문서는 복구 직후 혼합 작업공간의 역사적 실행 장부다. 커밋 선별 중 mutation 카나리를 실행 시 조립하도록 후속 수정했으므로, 최종 커밋 후보의 범위·지문·재검증은 별도 commit-prep 장부를 권위 근거로 삼는다.

## 기준과 보존

- HEAD: `858b96d510cf9e4da393b85446871448b4c1dfa6`
- branch: `task/verification-authority`
- 최종 전체 status SHA-256: `6e0361bad67059add13ff33af625cae9b44fddb42e6f994de955514cf8f3d47a`
- 기존 미추적 사용자 자산: 42개
- 기존 42개 결합 SHA-256: `1e008fb0728c104acd241e884f43b78abaedc9e177b7c2cd87e6aecb91799ab7`
- commit, push, PR, merge, deploy, mail: 0건

## 실행 결과

```text
acceptance-principles-check        exit 0  CHECKED 32
acceptance-principles-mutations    exit 0  CHECKED 34
check-mechanism-registry           exit 0  CHECKED 6
acceptance-verify-ac-m              exit 0  CHECKED 25
acceptance-verification-authority  exit 0  mutations 32/31/0/1, SHA 9, recovery 8
verify.sh                           exit 0
hooks/pre-commit                    exit 0
git diff --check                    exit 0
brief-lint --strict                 exit 0  violations 0
Claude V1                           NOT_RUN  HTTP 400, tokens 0/0
fresh Codex V2                      local PASS, overall Strict FAIL
verdict-ledger check                exit 1  expected fail-closed
```

→ 제품 코드와 로컬 게이트는 모두 GREEN이다. 장부 검사 exit 1은 V1 미실행을 PASS로 위조하지 않고 전체 FAIL로 닫은 기대 결과다.

## 복구 파일 SHA-256

```text
253ee8e6fb2688d0e317127fc86e052b3152d5224e5d06b02a8d4ef24a78be51  .github/workflows/verify.yml
073d4bf646b069fae376ec268bf97ea835c5019386908535adc8b6ee71ffdc7a  docs/sot/coding-principles.md
4daaa38351365bfd91283af67561bdfc4c1c649826a4655366b4b620fde151d6  docs/sot/mechanism-registry.yaml
9651292eb8157806f88c38cbd308a0debb75a6d6d66ae71f17c308176c86e56b  docs/sot/verification-commands.md
5eb238585362ff380d41402e1e9e784abd80c4ca2677d48b84dae0b1b7684410  hooks/pre-push
9765943b25e737c3da89dbbfd82bc24ca3d5420f8ac7898b08bac88226df38bf  scripts/verify/check-mechanism-registry.sh
b7734fae038d9e3d856a6d805861c390a29754450c1c564f2769bd6819657260  docs/sot/principles.yaml
d87d589303409df2b4ed2c7c31483ecd7a20a7bb73e3537179bb99fa12830912  scripts/acceptance-principles-check.sh
575a6dc527e0cc4280f72c1dc750c73318951681b067df77da7994a23d4f25c7  scripts/acceptance-principles-mutations.sh
8d70fc3da2ee633b855aab61b82f2db225c29f71cedc7ac2f83621b6a0eccae3  scripts/verify/check-strict-principles-skills.sh
d8033e157b0707a6e684d9fd1f01529e77a9911c2efa73ddc168a8399c73ea1e  scripts/verify/check-strict-verdict-ledger.sh
514446d246dd0c105bb4d41610fb8590dfe49bc7fe8b5f55b77683fa45b88454  scripts/verify/fixtures/strict-principles/artifact.txt
f555115e340d567c9f236d2c4d4af5eab0c7a015673f407772c98f6be4ddcbd1  scripts/verify/fixtures/strict-principles/v1-fail-false-pass.yaml
e6c9f9ebd87b147c218e7ccd4e6e3644f5a530aa655d8c14b8b8323ded93b398  scripts/verify/fixtures/strict-principles/v1-fail-v2-not-run.yaml
7b98c2a7cc2b9b722f4546e59ea649147d286b4bb59934f77a54d0d152fe7615  scripts/verify/fixtures/strict-principles/valid-verdict.yaml
6f2ee75cbde2df05877a156232e16b21896e767479530108fcfc77db96c19353  docs/engineering/verification-authority-principles-recovery-goal-2026-08-20.md
fedd3f421ceaeed237821333fd94d2998aaec0b371ebbe00dec3916c6fb6783a  docs/engineering/verification-authority-principles-recovery-v1-prompt-2026-08-20.md
797d311e9f9513f12b30a778544d6099518fd5f3e3ab5a46942b1a3e25bcef6c  docs/engineering/verification-authority-principles-recovery-v1-verdict-2026-08-20.md
ad6ba80e2294f9c037701729a9acc6392b2e571492ecd3542a3ef3a509c930ed  docs/engineering/verification-authority-principles-recovery-v2-verdict-2026-08-20.md
7b157873446f4fe05be4629ad2cdad28ba3c11eeb8932cdf524d72f3be919e0f  docs/engineering/verification-authority-principles-recovery-verdict-2026-08-20.yaml
```

→ 위 값은 복구 직후 실행 코드·SOT·배선·fixture·G/V1/V2 장부 20개의 당시 내용 지문이다. 기존 verification-authority 변경이 함께 들어 있는 공유 파일도 당시 혼합 내용의 지문이며, 최종 선별 index의 지문이 아니다.

## 외부 작업공간 관찰

루트 워크트리의 이번 원칙 복구 관련 상태는 시작 지문과 같았다. 실행 중 별도 작업의 `admin-dashboard-inherit-goal-2026-08-20.md`가 새로 나타났지만, 이를 제외한 루트 상태 지문은 시작값 `3b80cd123313943762ea7e65bb5904d382de84dbb8f1810bcc13f2c15f65e1cb`와 동일하다. 그 파일은 수정하거나 삭제하지 않았다.
