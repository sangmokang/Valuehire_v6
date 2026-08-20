# 원칙 복구 커밋 후보 V1 적대검증 요청 — 2026-08-20

## 결론

현재 저장소를 읽기 전용으로 감사해, index가 이번 원칙 게이트 복구만 포함하고 기존 사용자 자산과 이전 merge_group 작업을 배제했는지 판정하라.

## 제약

- 작업 위치: `/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/verification-authority`
- 기준 HEAD: `858b96d510cf9e4da393b85446871448b4c1dfa6`
- 파일 수정, stage 변경, reset, checkout, 삭제, commit, push, PR, merge, deploy, mail 금지.
- 작업공간에는 index와 무관한 사용자 변경 및 미추적 파일이 있으므로 보존하라.
- 주장보다 `git diff --cached`, 실제 파일, 명령 출력이 우선이다.

## 확인할 주장

1. cached diff에는 원칙 장부·검사기·mutation·배선·복구 문서와 공유 파일의 관련 hunk만 있다.
2. `.github/workflows/verify.yml`의 `VA_PR_HEAD_SHA` 변경, 이전 merge_group 제거 문서·코드, verification-authority 추적 수정 6개는 cached diff에 없다.
3. 현재 미추적 총 45개는 기존 사용자 자산 42개와 직전 merge_group 제거 작업 3개다. 기존 42개는 index에 없고 결합 SHA-256 `1e008fb0728c104acd241e884f43b78abaedc9e177b7c2cd87e6aecb91799ab7`로 보존된다. 뒤의 3개 경로는 goal의 명시적 제외 목록으로 별도 보존된다.
4. `scripts/acceptance-principles-mutations.sh`는 약화 카나리를 실행 시 조립하면서 실패 기대 반례 29개와 대조군 5개, 총 34개 검사를 계속 통과한다. 또한 이 파일이 staged 상태인 현재 index를 `bash hooks/pre-commit`으로 검사하면 exit 0이어야 한다.
5. 현재 혼합 작업공간의 pre-push는 P15에 따라 실패하는 것이 정상이다. 검증 주장은 HEAD+index만 물질화한 격리 복제본을 임시 검증 커밋으로 clean 상태로 만든 뒤 `bash hooks/pre-push`의 21개 검사가 통과했다는 뜻이며, 그 증거가 commit-prep 실행 장부에 있는지 확인한다.
6. 실제 대상 저장소에는 commit과 push가 없어야 한다.

## 판정 형식

첫 줄은 `V1_VERDICT: PASS` 또는 `V1_VERDICT: FAIL`로 쓴다. 이어서 치명·높음·중간·낮음 순으로 결함을 `file:line`과 재현 명령으로 적고, 증거가 없는 추정은 추정이라고 표시하라. 소비자나 재현 없이 운영 결함으로 과장하지 마라.
