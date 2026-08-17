# P19 — 머신 스케줄러와 장애 승계

아래 내용을 새 Codex 작업의 첫 프롬프트로 그대로 사용한다.

## 목표

허용 채널·생존·사용권을 모두 만족한 머신만 작업을 받고 장애 뒤 새 `queue_lease_epoch`·`account_fencing_token`과 새 머신이 이미 로컬에서 발급한 `local_reservation_epoch`로 안전하게 이어받는다.

## 선행조건

P16~P18 `CONTRACT_PASS`. `LIVE_PASS`에는 P17·P18 `LIVE_PASS`와 등록된 시험 실행자 두 대가 필요하다.

## 작업 소유 범위

`humansearch/src/humansearch/fleet/scheduler.py`, 상태기계, 두 머신 통합fixture·시험.

경로가 현재 SOT와 충돌하면 임의로 다른 영역까지 고치지 말고 목표 문서에 충돌을 증거와 함께 기록해 이 프로젝트를 중단한다.

## 비범위

브라우저 조작, 운영 배포, 처리량을 위한 클릭 속도 증가.

## RED 먼저

머신 A 사망 뒤 A와 B가 모두 완료 결과를 확정하거나 차단 채널 머신이 배정되는 실패 시험을 먼저 만든다.

## 구현 계약

작업 우선순위, 머신 capability, heartbeat, 사람 상태 신호, 로컬 자동화 예약, lease를 순서대로 검증한다. 필드 계약은 P17의 작업권 세대 `queue_lease_epoch`, P18의 채널·계정 사용권 `account_fencing_token`, P15에서 사람의 로컬 제어 동작이 발급하고 P16→P17이 그대로 전달한 `local_reservation_epoch` 세 개로 고정하고 서로 대체하거나 한 카운터로 합치지 않는다. P19는 `local_reservation_epoch`을 발급·증가시키지 않고 배정에 결합한다. 자동 장애 회수는 데이터베이스 시각으로 만료된 `LEASED | RUNNING`만 조건부 갱신해 `QUEUED`로 되돌리고 `delivery_attempt`는 유지한 채 `queue_lease_epoch`과 P17의 `machine_recovery_attempts`를 함께 1씩 올린다. 사람 개입은 별도 명시 전이로 현재 세 값을 조건부 대조해 `RUNNING→PAUSED_FOR_HUMAN`, P18 계정 사용권 해제, `queue_lease_epoch` 증가를 한 영수증으로 남기되 `machine_recovery_attempts`는 바꾸지 않는다. 같은 머신 재개도 사람이 P15에서 새 `local_reservation_epoch`을 발급한 뒤 `PAUSED_FOR_HUMAN→QUEUED`로 보내고, P18 사용권을 다시 획득해 새 `account_fencing_token`을 받은 다음에만 배정한다. 개입 통지가 제어 장부에 닿지 않으면 재개하지 않고 P21 로컬 마감 폐기와 자동 만료 회수 경로를 따른다. 새 머신이 계정 사용권을 획득하면 P18이 새 `account_fencing_token`을 발급하고, 실제 배정은 새 머신의 현재 `local_reservation_epoch`을 결합한다. 완료 결과는 세 현재값이 모두 일치할 때만 확정한다. `machine_recovery_limit` 기본값은 개별 `work_id + recovery_policy_version`당 3회다. `machine_recovery_attempts < 3`일 때만 자동 회수와 증가를 허용하고 이미 3이면 다음 회수 요청은 카운터를 올리거나 재배정하지 않고 `EXHAUSTED`·`exhaustion_reason=MACHINE_RECOVERY_LIMIT`·사람 에스컬레이션 영수증을 남긴다. 다시 시도하려면 사람이 원인을 검토하고 새 정책 버전·새 작업 ID로 만들어야 한다. `QUEUED→LEASED→RUNNING`과 실패/만료/재개를 세 값과 장애 횟수가 포함된 영수증으로 남긴다.

## 가짜 합격을 깨는 시험

A 사망, B 승계, A 늦은 완료, 만료 회수 경합, 세 epoch/token 중 하나만 오래된 완료, lease 미만료 상태의 같은 머신 사람 개입→명시적 pause→해제→새 로컬 예약→재획득→재개, 자동 장애 2회+사람 pause 2회에서 `machine_recovery_attempts=2` 유지, 개입 통지 유실, 자동 장애 회수 3회 뒤 다음 회수 요청의 `EXHAUSTED` 전이와 재배정 0건, 사람 신호 없음/만료, 로컬 예약 불일치, 지휘자 재시작, 동일 점수, stop switch, 정책 만료를 시험한다.

## 검증

두 실행자 장애 시나리오에서 최종 완료 1건·stale 거부 1건, 결정 지문, `bash verify.sh`.

## 원자적 인수 기준

후속 구현은 `bash scripts/acceptance-ai-ra-p19.sh` 한 명령으로 두 실행자의 중복 작업 0건, 사망 실행자 작업의 안전한 재배정 1건, `queue_lease_epoch`·`account_fencing_token`·`local_reservation_epoch` 중 하나라도 오래된 결과 수락 0건이 증명됨을 검사해야 한다. lease 미만료 상태의 같은 머신 사람 개입은 `PAUSED_FOR_HUMAN`·계정 해제·`queue_lease_epoch` 증가 뒤, 새 로컬 예약·계정 토큰 없이는 재개 0건이고 세 값이 모두 새로 결합된 뒤에만 재개 1건이어야 한다. 개별 `work_id + recovery_policy_version`에서 자동 장애 2회+사람 pause 2회는 `machine_recovery_attempts=2`이고, 자동 장애 회수 3회 뒤 다음 회수 요청은 재배정 0건·`EXHAUSTED` 1건·`MACHINE_RECOVERY_LIMIT` 1건·사람 에스컬레이션 1건이어야 하며 새 정책 버전·새 작업 ID 없이는 재개되지 않아야 한다. 정상 실행은 `PASS AI_RA_P19 <실제 핵심 건수>`를 출력하되 실제 핵심 건수는 반드시 1 이상이고 종료값 0을 남겨야 하며, 핵심 차단을 한 줄 고장 낸 반대 시험은 0이 아닌 종료값이어야 한다. 이 프로젝트는 자기 인수 스크립트만 소유한다. P04가 소유한 `scripts/acceptance-ai-ra-all.sh`와 서버 workflow가 이름 규칙으로 자동 발견해야 하며, 이후 프로젝트는 공용 workflow를 직접 수정하지 않는다.

## 라이브 증거와 멈춤점

가짜 실행자 시험은 `CONTRACT_PASS`까지만 가능하다. `LIVE_PASS`는 외부 사이트를 열지 않은 두 실제 실행자에서 A 중단→B 승계→A 늦은 완료 거부 영수증을 요구한다. 실제 머신이 없으면 `BLOCKED_AUTH`이며 완료가 아니다.

## 공통 strict 실행 지시

1. 기본 작업공간을 수정하지 말고 최신 기준 커밋에서 이 프로젝트 전용 worktree와 `task/` 브랜치를 만든다.
2. 코드보다 먼저 이 프로젝트 목표 문서를 작성하고 원자적 인수 기준 1개, 반대 시험, 비범위, 실제 검증 명령을 적는다.
3. `docs/sot/INDEX.md`, `coding-principles.md`, `git-workflow.md`, `hook-contracts.md`, `verification-commands.md`와 P00B 이후 새 정본을 전문으로 읽고 체크리스트를 목표 문서에 남긴다.
4. v4/v5 코드는 행동·실패 사례와 테스트 오라클만 참고한다. import, 복사, subprocess 호출, 런타임 의존성은 금지한다.
5. RED를 실제 런타임 시험으로 먼저 만들고 실패 출력을 목표 문서에 남긴다. 소스 문자열 검색만으로 기능을 증명하거나 테스트 0건을 PASS로 세지 않는다.
6. 최소 구현 뒤 대상 시험→자기 번호 인수 검사→P04 공용 `scripts/acceptance-ai-ra-all.sh`→`bash verify.sh` 순으로 실행한다. P04 전 프로젝트는 자기 스크립트만 만들고 P04가 공용 배관을 연결하며, P04 이후 프로젝트는 이름 규칙 자동 발견을 증명하고 `.github/workflows/verify.yml`을 직접 수정하지 않는다.
7. 비밀·후보 원문·인증정보를 터미널, fixture, 문서, 커밋에 남기지 않는다. 외부 쓰기·발송·운영 DB 변경·배포는 이 프롬프트가 명시적으로 허용하지 않으면 하지 않는다.
8. `claude -p` 1차 적대검토를 실행하고 각 지적을 Codex가 직접 명령으로 재현한다. 한 항목이라도 동의하면 수정 후 1차부터 다시 반복한다.
9. 완료 보고는 변경 파일, 실제 처리 건수, 테스트/인수 검사 종료 코드, `git diff --check`, 남은 `NOT_RUN`과 위험을 구분한다. 검사가 하나라도 빨갛거나 증거가 없으면 완료라고 하지 않는다.
