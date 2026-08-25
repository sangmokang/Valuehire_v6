# WU0-A — CI 보호 step의 정확한 명령 계약

## Goal

`verify.yml`에 안전 명령의 경로 문자열이 존재하는지만 보는 검사를 폐기하고, 보호 대상의 job ID·고유 step name·ordered run lines·허용된 if·continue-on-error 부재가 정본과 정확히 같을 때만 통과시킨다.

이번 Work Unit은 WU0-A만 다룬다. acceptance script가 `PASS:`/`CHECKED:` 문구를 위조하면 상위 runner가 통과하는 문제는 WU0-B로 남긴다.

## 기준선과 경계

- 위험등급: L3
- 원격 기준: `origin/main` = `c59bad7b160c473cda5545e76e6fa6bcc711a7ea`
- 격리 worktree: `worktrees/wu0a-ci-command-contract`
- 격리 브랜치: `task/wu0a-ci-command-contract`
- 원본 local main: `3094eefa646b102074dfb6401777afe450223e6c`
- 제외: `3094eef`의 finding-runner 관련 6파일 전부
- 금지: 원본 dirty main 수정/reset/checkout/clean, push, PR 생성·수정, merge
- 세션 ID: `01a02502-d7fa-7793-9085-5c356ff94d4e`

## 계약

1. `docs/sot/ci-required-steps.json`이 보호 대상마다 job, name, ordered run lines, 허용 if, continue-on-error 금지를 선언한다.
2. 보호 step은 지정 job 안에서 정확히 1개여야 한다.
3. 줄 끝 공백과 CRLF/LF 차이만 무시하며, shell 문법·wrapper·주석을 의미상 정규화하지 않는다.
4. 파일 없음·파싱 불가·보호 대상 0개는 exit 2다.
5. 삭제·중복·이름·명령·조건·오류무시 위반은 exit 1이다.
6. 이 검사는 “워크플로가 승인된 명령을 선언했다”만 증명한다. 해당 SHA에서 GitHub runner가 실제 실행했다는 증거는 원격 check 귀속 단계가 별도로 맡는다.

## RED — 구현 전 재현

- 시각: UTC `2026-08-25T08:37:56Z`, KST `2026-08-25T17:37:56+0900`
- HEAD: `c59bad7b160c473cda5545e76e6fa6bcc711a7ea`
- 실행 위치: 격리 worktree
- driver exit: `0` (네 공격을 실행한 harness 자체의 종료값)

명령은 각 변조를 `mktemp -d` 아래 workflow 사본에 적용한 뒤 다음 원명령을 호출했다.

```text
bash scripts/verify/check-ci-step-integrity.sh <mktemp>/red-N.yml
```

전체 출력:

```text
===== RED 1 =====
MUTATION=echo scripts/verify/run-acceptance.sh scripts/acceptance-hs-gates.sh
ALLOWED: 인수 검사 0-5 (push · CI 연결) — if 허용 (origin/main==main 을 보는 검사라 main push 에서만 의미가 있다. PR 실행에서 요구하면 상시 실패한다.)
PASS: 조건부·오류무시 스텝 없음 (job·step 25개 검사)
CHECKED: 25
EXIT=0

===== RED 2 =====
MUTATION=printf "%s\\n" scripts/verify/run-acceptance.sh scripts/acceptance-hs-gates.sh
ALLOWED: 인수 검사 0-5 (push · CI 연결) — if 허용 (origin/main==main 을 보는 검사라 main push 에서만 의미가 있다. PR 실행에서 요구하면 상시 실패한다.)
PASS: 조건부·오류무시 스텝 없음 (job·step 25개 검사)
CHECKED: 25
EXIT=0

===== RED 3 =====
MUTATION=true # bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-gates.sh
ALLOWED: 인수 검사 0-5 (push · CI 연결) — if 허용 (origin/main==main 을 보는 검사라 main push 에서만 의미가 있다. PR 실행에서 요구하면 상시 실패한다.)
PASS: 조건부·오류무시 스텝 없음 (job·step 25개 검사)
CHECKED: 25
EXIT=0

===== RED 4 =====
MUTATION=: # bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-gates.sh
ALLOWED: 인수 검사 0-5 (push · CI 연결) — if 허용 (origin/main==main 을 보는 검사라 main push 에서만 의미가 있다. PR 실행에서 요구하면 상시 실패한다.)
PASS: 조건부·오류무시 스텝 없음 (job·step 25개 검사)
CHECKED: 25
EXIT=0
```

RED acceptance 실행:

- 시각: UTC `2026-08-25T08:48:44Z`, KST `2026-08-25T17:48:44+0900`
- 명령: `bash scripts/acceptance-ci-step-integrity.sh`
- HEAD: `c59bad7b160c473cda5545e76e6fa6bcc711a7ea`
- 세션: `01a02502-d7fa-7793-9085-5c356ff94d4e`
- exit: `1`

```text
PASS: 현재 정상 workflow — exit=0 CHECKED=25
PASS: 설명용 echo가 있는 비보호 setup step — exit=0
PASS: 안전 명령과 무관한 workflow metadata 변경 — exit=0
PASS: 이유가 기록된 0-5 조건부 step — 정확한 if 허용
FAIL: counter-01 echo 정확 경로 — expected exit=1 actual=0
FAIL: counter-02 printf 정확 경로 — expected exit=1 actual=0
FAIL: counter-03a true 뒤 주석 — expected exit=1 actual=0
FAIL: counter-03b colon 뒤 주석 — expected exit=1 actual=0
FAIL: counter-04 step 이름 유지·run 변경 — expected exit=1 actual=0
FAIL: counter-05 동일 이름 step 중복 — expected exit=1 actual=0
FAIL: counter-06 다른 job 정상·원래 step 무력화 — expected exit=1 actual=0
FAIL: counter-07 multi-line 뒤 exit 0 — expected exit=1 actual=0
FAIL: counter-08 workflow·계약 동시 약화 — expected exit=1 actual=0
PASS: counter-09 checker 전체 exit 0 — runner exit=1
PASS: bash -n wrapper — exit=1
FAIL: 보호 step 삭제 — expected exit=1 actual=0
FAIL: 보호 step 이름 변경 — expected exit=1 actual=0
PASS: 허용되지 않은 step if — exit=1
PASS: continue-on-error 키 존재 — exit=1
PASS: 보호 job if — exit=1
PASS: workflow 파일 없음 — exit=2
FAIL: 계약 파일 없음 — expected exit=2 actual=0
PASS: workflow 파싱 불가 — exit=2
FAIL: 계약 파싱 불가 — expected exit=2 actual=0
FAIL: counter-10 보호 대상 0개 — expected exit=2 actual=0
PASS: 원본 저장소 상태 불변 — before/after 동일
CHECKED: 26
VERDICT: FAIL
```

## 정본 로드 증거

- `docs/sot/coding-principles.md`, `docs/sot/principles.yaml`, `docs/sot/mechanism-registry.yaml`, `docs/sot/verification-commands.md`, workflow와 네 검사기를 직접 읽었다.
- `bash scripts/acceptance-principles-check.sh` exit `0`: `VERDICT: PASS`, `MECHANISMS: PASS 34/34`, `WIRING: PASS pre-push=1 ci=1`, `CHECKED: 34`.
- 지정된 `docs/engineering/work-unit-process-adoption-2026-08-21.md`는 원격 기준선에 없다. 원본 dirty main의 미추적 사본은 읽기 전용으로 확인했으며 WU0 diff에 반입하지 않는다.

## 결정 카드

> 무엇을 — WU0-A에서 보호 step의 정확한 명령 계약만 먼저 고칩니다.
> 왜 — 현재는 경로 문자열만 남겨도 다섯 방어선이 모두 합격합니다.
> 버린 길 — echo|printf|true 정규식을 계속 추가하는 방식은 새 표현마다 다시 뚫려 기각했습니다.
> 대가 — workflow 명령을 정당하게 바꿀 때 계약도 함께 갱신해야 합니다. 가짜 합격 출력 문제는 남습니다.
> 되돌리기 — 독립 브랜치의 RED/GREEN commit만 폐기하면 원격 main과 dirty 원본에는 영향이 없습니다.

## 미해결 finding

- `HIGH / REPRODUCED / WU0-B`: acceptance script가 필요한 `PASS:`/`CHECKED:` 문자열만 위조하면 `run-acceptance`, `acceptance-semantic-mutations`, pre-commit이 통과할 수 있다. WU0-A는 이를 해결했다고 주장하지 않는다.
- 원격 보호 규칙과 현재 SHA의 실제 GitHub check 귀속은 이 로컬 Work Unit의 증명 범위가 아니다.
