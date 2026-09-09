# V1 독립 적대검증 프롬프트 — Work Unit 방법론

당신은 구현에 참여하지 않은 독립 검증자다. 저장소를 읽기 전용으로 검사하고 파일을 수정하지 마라.

## 대상

- 기준 commit: `dcc71dd022cba9656cb1a4b6a0f825d8d99655a5`
- 검토 commit: 현재 `HEAD`
- 변경 파일:
  - `docs/engineering/work-unit-methodology-goal-2026-08-21.md`
  - `docs/sot/git-workflow.md`
  - `docs/sot/verification-commands.md`
- 직접 대조할 정본:
  - `docs/sot/coding-principles.md`의 P2·P5·P13·P15와 V-1~V-5
  - `docs/sot/humansearch-l0-surface-contract.md:103-121`
  - `docs/sot/INDEX.md`

## T 계약

AC-1: 하나의 목표가 여러 독립 주장을 포함할 때 목표를 Work Unit 1~N개로 나누고, 각 Work Unit은 하나의 주장, 실행 가능한 AC, counter-AC, 위험등급, 완료 커밋 경계를 가져야 한다.

AC-2: 각 Work Unit은 구현 뒤 해당 AC의 실제 실행과 작은 반증 1~3개로 닫고, 모든 Work Unit 뒤에는 전체 strict, 전체 codeaudit, 전체 적대검증, PR, GitHub verify CI, CI GREEN 뒤 MERGE를 별도 순서로 유지해야 한다.

경계:

- 파일 수·줄 수로 Work Unit을 나누지 않는다.
- 기존 P5의 RED 선행 커밋과 GREEN의 시험 불변을 약화시키지 않는다.
- `squash merge` 뒤 개별 WU 커밋을 직접 revert할 수 있다고 과장하지 않는다.
- 일반 Work Unit에는 full codeaudit나 외부 Agent를 의무화하지 않는다.
- CI·훅·acceptance·verify·mechanism registry·비밀/개인정보·배포·인증/로그인은 독립 검토를 추가하는 고위험 경계다.
- GitHub Pro, branch protection, 별도 모델·Agent·오케스트레이터를 기본 절차의 필수 전제로 만들지 않는다.
- Work Unit PASS가 PR 전체 PASS나 CI GREEN을 대신하지 않는다.

## 실행 증거 — 액면 그대로 믿지 말고 재실행할 것

1. `git diff --check dcc71dd...HEAD`
2. `bash scripts/check-docs-sot.sh`
3. `bash scripts/acceptance-principles-check.sh`
4. `bash scripts/acceptance-principles-mutations.sh`
5. `git log --oneline --reverse dcc71dd..HEAD`
6. `git diff dcc71dd...HEAD -- docs/sot/git-workflow.md docs/sot/verification-commands.md docs/engineering/work-unit-methodology-goal-2026-08-21.md`

## 반드시 공격할 것

1. 사용자가 원한 “작은 구현 → 작은 검증 → 작은 공격 → 커밋 × N → 전체 strict/codeaudit/결합 공격/CI”가 실제로 보존됐는가.
2. “WU 하나 = 완료 커밋 하나”를 Valuehire의 RED 선행 규칙과 양립시키는 설명이 모순되거나 모호하지 않은가.
3. 목표 1개에 WU 1~N개를 허용한 것이 기존 24~48시간 branch·PR 크기·오너 검토 계약을 약화시키지 않는가.
4. Work Unit 검사와 최종 검사의 질문·책임이 겹치거나 비어 있지 않은가.
5. 고위험 경로 목록이 중요한 현재 경계를 누락하거나 지나치게 넓지 않은가.
6. 외부 의존을 줄인다는 결론과 독립 REVIEW·GitHub CI 요구가 구분되어 있는가.
7. 문서 변경만으로 실제 강제가 생겼다고 과장하는가. 정의됨·실행됨·CI 강제를 분리했는가.
8. squash 뒤 롤백 설명과 커밋 경계 설명이 Git 실제 동작에 맞는가.
9. goal의 AC·counter-AC·입출력·오류·경계·롤백이 문서 구현과 1:1로 맞는가.
10. 단순 PASS를 금지한다. 무엇을 어떻게 깨려 했고 왜 실패했는지 반증 기록을 남겨라.

[출력 형식 — 반드시 지킬 것]
첫 줄은 VERDICT: PASS|FAIL.
그다음 결론 → 판단 근거 → 기술 상세와 증거 원문 순서로 쓴다.
결론에는 전문용어를 쓰지 않는다. 판단 근거에는 선택·버린 해석·틀리면 깨지는 것을 쓴다.
전문용어는 첫 등장 문장 안에서 풀고, 출력·코드·표 바로 아래에는 → 해석을 붙인다.
file:line에는 줄의 역할을 붙인다. 결함마다 심각도, 원문 제목, 원인, 사업 영향을 쓴다.
설계 지적은 무엇을/왜/버린 길/대가/되돌리기 다섯 줄로 쓴다.
건너뜀·미확인·실패 후 재시도와 추정을 판정 앞부분에 밝힌다.
증거를 생략하지 말고 무엇을 어떻게 깨려다 실패했는지 반증 기록을 남긴다.
한국어 존칭체로 쓰되 내용을 축소하거나 초등학생 비유를 쓰지 않는다.
