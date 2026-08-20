# 원칙 게이트 복구 커밋 준비 goal — 2026-08-20

## 결론

이번 원칙 검증 복구에 속한 변경만 커밋 후보로 선별한다. 과거 연구 자료와 이전 기능 변경은 작업공간에 그대로 보존하고, 실제 커밋이나 원격 전송은 하지 않는다.

## 판단 근거

작업 시작 시 인덱스는 비어 있었다. 복구 파일 대부분은 전용 파일이지만 CI 구성과 검증 명령 문서에는 이전 일반 변경 요청 작업이 함께 들어 있어 파일 전체를 선별하면 사용자 범위를 넘는다. 두 공유 파일은 복구 부분만 선별해야 한다.

## 결정 카드

- 무엇을: 복구 전용 파일은 전체, 공유 파일은 복구 부분만 인덱스에 넣는다.
- 왜: 커밋 후보가 이번 복구만 담아야 하기 때문이다.
- 버린 길: 현재 변경 파일 전체를 한 번에 올리는 방식은 이전 작업과 기존 사용자 자산을 섞으므로 기각한다.
- 대가: 공유 파일은 인덱스와 작업공간 내용이 달라져 별도 스냅샷 검증이 필요하다.
- 되돌리기: 아래 선별 경로만 인덱스에서 내리면 작업공간 파일은 그대로 남는다.

## 범위

### 전용 수정 파일

- `docs/sot/coding-principles.md`
- `docs/sot/mechanism-registry.yaml`
- `hooks/pre-push`
- `scripts/verify/check-mechanism-registry.sh`

### 공유 파일의 복구 부분만

- `.github/workflows/verify.yml`: 원칙 검사와 mutation 두 단계만
- `docs/sot/verification-commands.md`: 위 두 단계, 단계 수·번호·각주·복구 근거만

### 복구 신규 파일

- `docs/sot/principles.yaml`
- `scripts/acceptance-principles-check.sh`
- `scripts/acceptance-principles-mutations.sh`
- `scripts/verify/check-strict-principles-skills.sh`
- `scripts/verify/check-strict-verdict-ledger.sh`
- `scripts/verify/fixtures/strict-principles/` 아래 4개
- `docs/engineering/verification-authority-principles-recovery-*` 6개
- 이 goal 문서

### 명시적 제외

- 기존 미추적 사용자 자산 42개 전부
- 이전 merge_group 제거 작업의 신규 3개와 추적 수정 6개
- 공유 파일 안의 `VA_PR_HEAD_SHA` 배선과 일반 PR 설명 변경
- commit, push, PR, merge, deploy, mail

## T 계약

### 입력

- HEAD `858b96d510cf9e4da393b85446871448b4c1dfa6`
- 현재 작업공간
- 비어 있는 시작 인덱스

### 출력

- 인덱스에는 위 복구 경로와 복구 부분만 존재한다.
- 작업공간의 기존 파일 본문은 스테이징 전후 같아야 한다.
- 기존 미추적 42개 결합 SHA-256은 `1e008fb0728c104acd241e884f43b78abaedc9e177b7c2cd87e6aecb91799ab7`이어야 한다.
- 현재 미추적 총 45개는 위 기존 42개와 직전 merge_group 제거 작업 3개로 분리하며, 후자도 보존하되 이번 index에는 넣지 않는다.
- commit과 push 수는 0이어야 한다.

### 오류와 경계

- 선택 대상 0개는 FAIL이다.
- 제외 경로가 인덱스에 하나라도 들어가면 FAIL이다.
- 공유 파일 전체가 들어가 이전 변경이 섞이면 FAIL이다.
- 새 셸 파일의 실행권한이 인덱스에서 빠지면 FAIL이다.
- 인덱스 스냅샷 검사가 아닌 현재 혼합 작업공간 검사만으로 합격시키면 FAIL이다.

## EARS 인수 기준

### AC-1 선별 범위

When 커밋 후보를 만들면 시스템은 복구 전용 경로와 공유 파일의 복구 부분만 인덱스에 넣어야 한다.

검증: `git diff --cached --name-status`와 `git diff --cached`.

counter-AC: 공유 파일 전체를 올려 이전 일반 PR 변경까지 섞는다.

### AC-2 사용자 자산 보존

When 선별 전후 기존 42개 미추적 파일을 비교하면 시스템은 경로와 SHA-256을 모두 보존해야 한다.

검증: 42개 경로별 `shasum -a 256` 결합 지문 대조.

counter-AC: 과거 merge_group fixture를 삭제하거나 우연히 인덱스에 넣는다.

현재 관찰값: 미추적 총 45개 = 기존 사용자 자산 42개 + 직전 merge_group 제거 작업 3개다. “기존 42개”는 전체 미추적 수가 아니라 시작 시 고정한 사용자 자산 집합을 뜻한다.

### AC-3 이전 작업 분리

When 인덱스 경로를 검사하면 시스템은 이전 merge_group 제거 작업의 전용 파일과 추적 수정 파일을 포함하지 않아야 한다.

counter-AC: 현재 `git status`의 모든 변경을 일괄 선별한다.

### AC-4 정확한 스냅샷 검증

When 전체 검증을 실행하면 시스템은 HEAD와 인덱스 차이만 반영한 격리 사본에서 원칙 검사·mutation·mechanism·AC-M·verification-authority·기본 검사를 실행해야 한다.

counter-AC: 인덱스에 없는 작업공간 변경 덕분에 통과한 결과를 커밋 후보 합격으로 사용한다.

### AC-5 외부 변경 금지

When 작업을 종료하면 시스템은 commit, push, PR, merge, deploy, mail을 한 건도 만들지 않아야 한다.

## Harness 게이트

- G0: 시작 HEAD, 빈 인덱스, 전체 상태와 42개 지문을 고정한다.
- G1: 이 문서로 선별·제외·오류 계약을 고정한다.
- G2: 공유 파일 전체 스테이징이 범위 위반임을 cached diff로 공격한다.
- G3: 최소 선별로 인덱스를 구성한다.
- G3.5: CI와 pre-push에서 원칙 검사 호출 경로를 확인한다.
- G4: 격리된 인덱스 스냅샷에서 전체 검증을 실행한다.
- G5: Claude V1과 새 맥락 Codex V2가 인덱스 범위와 증거를 재공격한다.
- G6: 최종 지문·인덱스 목록·commit/push 0건을 기록한다.

## 롤백

선별된 경로만 `git restore --staged -- <경로>`로 인덱스에서 내린다. 이 작업은 작업공간 본문을 바꾸지 않는다. 실행은 사용자가 요청할 때만 한다.
