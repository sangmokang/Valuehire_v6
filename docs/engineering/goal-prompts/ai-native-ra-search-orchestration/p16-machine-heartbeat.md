# P16 — 머신 생존·준비 상태 판정

아래 내용을 새 Codex 작업의 첫 프롬프트로 그대로 사용한다.

## 목표

생존 신호와 준비 점검을 분리해 오래됐거나 사람이 사용 중인 머신이 작업을 받지 못하게 한다.

## 선행조건

P15 `CONTRACT_PASS`.

## 작업 소유 범위

`humansearch/src/humansearch/fleet/heartbeat.py`, 시계 포트, 상태전이·단위시험.

경로가 현재 SOT와 충돌하면 임의로 다른 영역까지 고치지 말고 목표 문서에 충돌을 증거와 함께 기록해 이 프로젝트를 중단한다.

## 비범위

작업 큐 claim, 브라우저 명령, 원격 머신 재부팅.

## RED 먼저

만료된 heartbeat 또는 사람 사용 중 상태가 READY로 판정되는 실패 시험을 먼저 만든다.

## 구현 계약

P15의 사람 상태와 사람이 로컬에서 발급한 `local_reservation_epoch`을 입력으로 받아 `READY | STALE | HUMAN_ACTIVE | HUMAN_UNKNOWN | STOPPED | VERSION_BLOCKED`를 단조 시계 기준으로 계산하고 원인·규칙 버전·머신 ID·상태 스냅샷 지문·신호 출처·관측시각·만료시각·같은 `local_reservation_epoch`을 남긴다. P16은 이 값을 새로 발급하거나 증가시키지 않는다. `READY`는 heartbeat와 사람 신호가 모두 유효하고 P15 사람 상태가 `IDLE_CONFIRMED`이며 버전·중단 스위치·로컬 예약이 적격일 때만 반환한다. 사람 상태 신호가 없거나 오래됐으면 `HUMAN_UNKNOWN`이며 `READY`가 아니다.

## 가짜 합격을 깨는 시험

시계 역행, 중복 heartbeat, 네트워크 지연, 버전 변경, stop 이후 늦은 신호, 경계 밀리초를 시험한다.

## 검증

가짜 시계 상태전이, 100회 결정 동일성, heartbeat 누락 변조, `bash verify.sh`.

## 원자적 인수 기준

후속 구현은 `bash scripts/acceptance-ai-ra-p16.sh` 한 명령으로 생존·사람 사용 상태가 고정된 시계에서 재현되고, `IDLE_CONFIRMED`인 유효 신호만 `READY`로 바뀌며 P17이 소비할 적격성 증명 필드를 남김을 검사해야 한다. 오래된 생존/사람 신호, `HUMAN_ACTIVE | HUMAN_UNKNOWN`, 시계 역행은 `READY`로 세지 않아야 한다. 정상 실행은 `PASS AI_RA_P16 <실제 핵심 건수>`를 출력하되 실제 핵심 건수는 반드시 1 이상이고 종료값 0을 남겨야 하며, 핵심 차단을 한 줄 고장 낸 반대 시험은 0이 아닌 종료값이어야 한다. 이 프로젝트는 자기 인수 스크립트만 소유한다. P04가 소유한 `scripts/acceptance-ai-ra-all.sh`와 서버 workflow가 이름 규칙으로 자동 발견해야 하며, 이후 프로젝트는 공용 workflow를 직접 수정하지 않는다.

## 라이브 증거와 멈춤점

합성 신호만 사용한다. 실제 머신 모니터링 설치 없이 판정 함수에서 멈춘다.

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
