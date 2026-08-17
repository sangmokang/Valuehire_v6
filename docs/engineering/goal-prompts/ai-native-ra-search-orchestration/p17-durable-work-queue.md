# P17 — Supabase 지속 작업 큐

아래 내용을 새 Codex 작업의 첫 프롬프트로 그대로 사용한다.

## 목표

작업 제안을 개인정보 없는 지속 큐에 멱등하게 넣고 한 작업을 한 소비자만 가져가게 한다.

## 선행조건

P08·P15·P16 `CONTRACT_PASS`. `LIVE_PASS`에는 운영 제어 DB 변경 승인과 migration readback이 필요하다.

## 작업 소유 범위

`humansearch/src/humansearch/fleet/queue.py`, SQL migration 초안, 로컬 Postgres/Supabase fixture, 동시성시험.

경로가 현재 SOT와 충돌하면 임의로 다른 영역까지 고치지 말고 목표 문서에 충돌을 증거와 함께 기록해 이 프로젝트를 중단한다.

## 비범위

후보 원문 저장, 브라우저 서비스 키 노출, 오너 승인 없는 운영 migration 적용, 큐 외 다른 운영 스키마 변경.

## RED 먼저

두 소비자가 같은 작업을 동시에 가져가거나 같은 고유키가 두 행으로 들어가며, P16이 만든 적격성 증명이 없거나 만료·정지된 머신이 claim하는 실패 시험을 먼저 만든다.

## 구현 계약

고유키, 우선순위 입력 지문, 상태, visibility timeout, 전송 재시도 `delivery_attempt`와 `delivery_policy_version`, 모든 작업권 교체 세대 `queue_lease_epoch`, 자동 머신 장애 회수 횟수 `machine_recovery_attempts`와 `recovery_policy_version`, 최소 영수증만 저장한다. `delivery_attempt`는 개별 `work_id + delivery_policy_version`에서 일시 네트워크 오류와 서버가 명시한 지연 응답만 세며 기본 상한은 3회다. 상한 소진은 `EXHAUSTED`와 `exhaustion_reason=DELIVERY_RETRY_LIMIT`을 남긴다. 정책·인증·사람 개입은 이 카운터로 자동 재시도하지 않는다. `queue_lease_epoch`은 P18의 채널·계정 사용권 `account_fencing_token`과 다른 필드이고 자동 만료 회수와 사람 pause 모두에서 증가할 수 있다. `machine_recovery_attempts`는 `work_id + recovery_policy_version`별 0에서 시작해 P19의 자동 DB 만료 회수에서만 증가하며 사람 pause·명시적 재개·전송 재시도는 바꾸지 않는다. claim은 P16의 판정·원인·규칙 버전·머신 ID·상태 스냅샷 지문·신호 출처·관측시각·만료시각·P15에서 시작된 `local_reservation_epoch`을 담은 적격성 증명을 필수로 받고, 현재 등록값과 재검사한다. P17은 이 값을 새로 발급하거나 증가시키지 않는다. P16 판정은 `READY`이고 근거가 된 P15 사람 상태는 `IDLE_CONFIRMED`인 경우에만 claim한다. 증명이 없음·만료·지문 불일치이거나 P16 판정이 `STALE | HUMAN_ACTIVE | HUMAN_UNKNOWN | STOPPED | VERSION_BLOCKED`면 공유 상태 전이 없이 거부한다. 세 카운터는 서로의 상한을 소진하지 않으며 긴 거래 잠금은 금지한다.

## 가짜 합격을 깨는 시험

동시 claim, 재삽입, 소비자 사망, visibility 만료 회수, 회수 경합, 사람 pause에서 `queue_lease_epoch`만 증가하고 `machine_recovery_attempts`는 유지, 전송 `delivery_attempt` 3회 소진과 `DELIVERY_RETRY_LIMIT`, `Retry-After`, 정책·인증·사람 개입 자동 재시도 금지, 세 카운터 상호 불변, 적격성 증명 누락·만료·위조·재사용, `STALE | HUMAN_ACTIVE | HUMAN_UNKNOWN | STOPPED | VERSION_BLOCKED` claim 거부, RLS 거부, 후보 원문 필드 삽입을 시험한다.

## 검증

두 소비자 병렬시험에서 승자 1명, 만료 회수 1명, 중복 0, 오래된 결과 수락 0, 비적격 머신 claim 0, 전송 `delivery_attempt` 상한 3과 `DELIVERY_RETRY_LIMIT`, 세 카운터 상호 불변, 금지 필드 0, migration rollback, `bash verify.sh`.

## 원자적 인수 기준

후속 구현은 `bash scripts/acceptance-ai-ra-p17.sh` 한 명령으로 두 소비자 동시 실행에서 승자 1명·만료 회수 1명·중복/오래된 결과/후보 원문 필드 0건을 검사해야 한다. 전송 `delivery_attempt`는 같은 `work_id + delivery_policy_version`에서만 기본 상한 3을 세고 소진 시 `DELIVERY_RETRY_LIMIT`을 남기며, 정책·인증·사람 개입과 머신 장애 회수는 이 값을 바꾸지 않아야 한다. `machine_recovery_attempts`는 같은 `work_id + recovery_policy_version`에서 자동 만료 회수만 세고 사람 pause·명시적 재개·전송 재시도에는 변하지 않아야 하며, `queue_lease_epoch` 증가는 두 시도 상한을 소진하지 않아야 한다. 또한 P16 적격성 증명이 없거나 만료·불일치이고 `STALE | HUMAN_ACTIVE | HUMAN_UNKNOWN | STOPPED | VERSION_BLOCKED`인 머신의 claim은 0건이며, 적용한 큐 변경을 다시 읽고 되돌릴 수 있음을 검사해야 한다. 정상 실행은 `PASS AI_RA_P17 <실제 핵심 건수>`를 출력하되 실제 핵심 건수는 반드시 1 이상이고 종료값 0을 남겨야 하며, 핵심 차단을 한 줄 고장 낸 반대 시험은 0이 아닌 종료값이어야 한다. 이 프로젝트는 자기 인수 스크립트만 소유한다. P04가 소유한 `scripts/acceptance-ai-ra-all.sh`와 서버 workflow가 이름 규칙으로 자동 발견해야 하며, 이후 프로젝트는 공용 workflow를 직접 수정하지 않는다.

## 라이브 증거와 멈춤점

로컬/임시 DB 검증은 `CONTRACT_PASS`까지만 가능하다. 운영 migration 승인 없이는 `BLOCKED_OWNER`이며 `LIVE_PASS`가 아니다. 승인되면 운영 제어 DB에 후보 원문 없는 migration 한 건을 적용·다시 읽기·되돌리기까지 증명하고 멈춘다.

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
