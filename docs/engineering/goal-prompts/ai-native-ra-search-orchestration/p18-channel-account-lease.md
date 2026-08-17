# P18 — 채널·계정 사용권과 account fencing token

아래 내용을 새 Codex 작업의 첫 프롬프트로 그대로 사용한다.

## 목표

같은 채널·계정은 한 머신만 사용하고 만료된 실행자의 늦은 결과를 `account_fencing_token`으로 거부한다.

## 선행조건

P15~P17 `CONTRACT_PASS`. `LIVE_PASS`에는 P17 `LIVE_PASS`와 승인된 운영 제어 DB가 필요하다.

## 작업 소유 범위

`humansearch/src/humansearch/fleet/lease.py`, SQL 제약 초안, 가짜 시계·동시성시험.

경로가 현재 SOT와 충돌하면 임의로 다른 영역까지 고치지 말고 목표 문서에 충돌을 증거와 함께 기록해 이 프로젝트를 중단한다.

## 비범위

실제 로그인, 계정 회전, 차단 회피, 브라우저 실행.

## RED 먼저

두 머신이 같은 계정 사용권을 얻거나 이전 `account_fencing_token` 결과가 받아들여지는 실패 시험을 먼저 만든다.

## 구현 계약

lease key=채널+계정 지문, holder, expiry, 단조 증가 정수 `account_fencing_token`을 원자적으로 관리한다. 갱신·해제·만료 후 승계는 명시 상태전이며 `FREE | EXPIRED`에서 성공한 모든 획득/승계 때 토큰을 올린다. 직전 holder와 같은 머신이라도 명시적 해제 뒤 다시 획득하면 새 토큰이다. 이 토큰은 P17의 모든 작업권 교체 세대 `queue_lease_epoch`과 별도 필드이고 서로 대신할 수 없다.

## 가짜 합격을 깨는 시험

동시 획득, 시계 경계, 네트워크 분할, 늦은 갱신, 같은 holder의 명시적 해제→재획득 토큰 증가, 이전 토큰 결과, holder 위조를 시험한다.

## 검증

100회 동시 경합 승자 항상 1명, stale 결과 0건 수락, rollback, `bash verify.sh`.

## 원자적 인수 기준

후속 구현은 `bash scripts/acceptance-ai-ra-p18.sh` 한 명령으로 같은 계정 사용권은 한 실행자만 얻고 승계 뒤 `account_fencing_token`이 정확히 증가하며 이전 토큰의 결과가 거부되고 P17 `queue_lease_epoch`과 혼용되지 않음을 검사해야 한다. 정상 실행은 `PASS AI_RA_P18 <실제 핵심 건수>`를 출력하되 실제 핵심 건수는 반드시 1 이상이고 종료값 0을 남겨야 하며, 핵심 차단을 한 줄 고장 낸 반대 시험은 0이 아닌 종료값이어야 한다. 이 프로젝트는 자기 인수 스크립트만 소유한다. P04가 소유한 `scripts/acceptance-ai-ra-all.sh`와 서버 workflow가 이름 규칙으로 자동 발견해야 하며, 이후 프로젝트는 공용 workflow를 직접 수정하지 않는다.

## 라이브 증거와 멈춤점

합성 계정 지문과 임시 DB는 `CONTRACT_PASS` 증거다. `LIVE_PASS`는 운영 제어 DB에서 비밀이 아닌 시험용 계정 지문 하나를 두 실행자가 경합해 승자 1명·이전 `account_fencing_token` 거부를 증명해야 한다. 실제 운영 계정 로그인은 하지 않는다.

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
