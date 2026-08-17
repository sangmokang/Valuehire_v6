# P07 — 수량·구성별 서치 부족분 계산

아래 내용을 새 Codex 작업의 첫 프롬프트로 그대로 사용한다.

## 목표

이미 확보한 고유 적격 후보와 필수 구성의 빈칸을 분리해 다음 서치가 필요한 이유를 계산한다.

## 선행조건

P03·P13 `CONTRACT_PASS`.

## 작업 소유 범위

`humansearch/src/humansearch/search_gap/engine.py`, coverage 모델, 합성 fixture와 단위·속성시험.

경로가 현재 SOT와 충돌하면 임의로 다른 영역까지 고치지 말고 목표 문서에 충돌을 증거와 함께 기록해 이 프로젝트를 중단한다.

## 비범위

사이트 검색 실행, 후보 최종 평가, 작업 큐 삽입.

## RED 먼저

중복 후보를 여러 명으로 세거나 페이지 미완주 0건을 소진으로 판정하는 실패 시험을 먼저 만든다.

## 구현 계약

P03의 `target_eligible_candidate_count`에서 P12 공용 스키마를 통과한 P13 내부+규칙엔진+`ELIGIBLE` 영수증과 후속 P25 외부+사람+`ACCEPTED` 영수증을 `canonical_candidate_id`로 합집합한 `current_eligible_unique_candidate_count`를 빼 수량 부족을 계산하고, 경력·산업·기술·지역·연차·회사군·채널별 구성 부족을 따로 반환한다. P12 공용 함수를 그대로 호출해 얻은 `candidate_eligibility_receipt_set_hash`를 부족분 출력에 포함하고 자체 해시 구현은 만들지 않아 P06과 같은 후보 세대인지 P08이 검증하게 한다. P25 이전 최초 계산에서는 승인된 외부 영수증 집합이 빈 값이며, `REVIEW_REQUIRED | INELIGIBLE | REJECTED | HOLD`와 출처만 다른 중복 후보는 세지 않는다. `target_pre_interview_count`는 이 계산에 쓰지 않는다. 완주 영수증 없는 0건은 `UNKNOWN`; 연속 2회 신규 0명+완주일 때만 검색식 소진이다.

## 가짜 합격을 깨는 시험

동일 후보 다중 출처·별칭, P13 `REVIEW_REQUIRED` 혼입, P25 `REJECTED | HOLD` 혼입, P25 이전 빈 외부 집합, 일부 페이지, 필수 구성 누락, 목표 필드 교환, 목표 초과, 채널 차단, 마지막 신규 위치 누락을 시험한다.

## 검증

골든 coverage 표, 중복/미완주 변조 시험, 100회 지문 동일성, `bash verify.sh`.

## 원자적 인수 기준

후속 구현은 `bash scripts/acceptance-ai-ra-p07.sh` 한 명령으로 P12 공용 스키마의 내부 `ELIGIBLE`과 선택적으로 주입된 외부 `ACCEPTED`만 `canonical_candidate_id` 합집합으로 세어 `target_eligible_candidate_count - current_eligible_unique_candidate_count`와 채널·구성 부족을 분리 계산하고 `candidate_eligibility_receipt_set_hash`를 남겨야 한다. 미래 P25 구현 없이도 공용 스키마의 합성 외부 `ACCEPTED` fixture로 이 입력 포트를 검증한다. `REVIEW_REQUIRED | INELIGIBLE | REJECTED | HOLD`·불법 origin/source/state 조합·별칭 중복·목표 0·과잉 입력에서도 수량을 부풀리거나 음수 작업을 만들지 않고 `target_pre_interview_count` 교환 변조를 거부해야 한다. 정상 실행은 `PASS AI_RA_P07 <실제 핵심 건수>`를 출력하되 실제 핵심 건수는 반드시 1 이상이고 종료값 0을 남겨야 하며, 핵심 차단을 한 줄 고장 낸 반대 시험은 0이 아닌 종료값이어야 한다. 이 프로젝트는 자기 인수 스크립트만 소유한다. P04가 소유한 `scripts/acceptance-ai-ra-all.sh`와 서버 workflow가 이름 규칙으로 자동 발견해야 하며, 이후 프로젝트는 공용 workflow를 직접 수정하지 않는다.

## 라이브 증거와 멈춤점

합성 후보와 영수증만 사용한다. 외부 서치 작업을 만들지 않고 계산 결과에서 멈춘다.

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
