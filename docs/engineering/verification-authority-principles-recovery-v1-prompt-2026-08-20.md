# V1 독립 적대검증 요청 — 원칙 게이트 복구

## 결론

누락됐던 원칙 검증 묶음이 실제 실행 경로까지 온전히 복구됐는지, 구현자 설명을 믿지 말고 현재 파일과 직접 실행으로 반박하라.

대상 저장소는 현재 디렉터리다. 읽기 전용으로 감사하고 파일을 수정하지 마라.

## 주장

`docs/sot/principles.yaml`과 `scripts/acceptance-principles-check.sh`는 삭제된 것이 아니라 별도 작업 브랜치에서 만들어진 뒤 이 브랜치에 병합되지 않았다. 최신 보강본의 최소 완결 묶음을 이 작업트리에 복구했고 기존 일반 PR verification-authority 동작과 사용자 미추적 자산을 보존했다.

## 반드시 검증할 것

1. `git diff`와 `git status --short`를 읽고 복구가 문서만 복사한 것이 아니라 SOT·checker·mutation·fixture/helper·pre-push·CI·mechanism registry에 완결되게 배선됐는지 확인하라.
2. `docs/engineering/verification-authority-principles-recovery-goal-2026-08-20.md`의 AC와 counter-AC를 코드에 대조하라.
3. 다음 명령을 직접 실행하고 종료값과 핵심 출력을 기록하라.
   - `bash scripts/acceptance-principles-check.sh`
   - `bash scripts/acceptance-principles-mutations.sh`
   - `bash scripts/verify/check-mechanism-registry.sh`
   - `bash scripts/acceptance-verify-ac-m.sh`
   - `bash scripts/acceptance-verification-authority.sh`
   - `bash verify.sh`
   - `git diff --check`
4. `relations`/`merge_group` 제거 후 일반 PR 전용 verification-authority 변경을 이번 복구가 되돌리거나 오염했는지 확인하라.
5. 오래된 `task/strict-principles-yaml` 초안을 무비판적으로 복사한 흔적, 실패 삼키기, 0건 PASS, 자기검사 제외, 잘못된 스텝 수 문서를 공격하라.
6. 사용자 기존 미추적 파일을 이번 복구가 삭제·변조했다는 증거가 있는지 확인하라. 증명할 수 없으면 미확인으로 적어라.

## 출력 계약

- 첫 줄: `V1_VERDICT: PASS|FAIL|NOT_RUN`
- 결함은 심각도, file:line, 재현 명령, 기대/실제를 포함한다.
- 실행하지 못한 명령은 PASS가 아니라 NOT_RUN으로 적는다.
- 구현자 설명을 근거로 세지 말고 현재 파일과 직접 실행만 근거로 삼는다.
- 소비자·재현 없이 미래 위험을 현재 운영 결함으로 과장하지 마라.
