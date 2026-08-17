# P06 — 재현 가능한 포지션 우선순위

아래 내용을 새 Codex 작업의 첫 프롬프트로 그대로 사용한다.

## 목표

승인된 입력만으로 포지션 처리 순서와 항목별 이유를 동일하게 재계산한다.

## 선행조건

P03·P05·P13 `CONTRACT_PASS`.

## 작업 소유 범위

`humansearch/src/humansearch/prioritization/position_priority.py`, 정책 버전 fixture, 단위·속성시험.

경로가 현재 SOT와 충돌하면 임의로 다른 영역까지 고치지 말고 목표 문서에 충돌을 증거와 함께 기록해 이 프로젝트를 중단한다.

## 비범위

언어모델의 숫자 확정, ClickUp 쓰기, 후보 매칭.

## RED 먼저

같은 입력의 필드 순서를 바꾸거나 100회 반복할 때 순서·지문이 달라지는 실패 시험을 먼저 만든다.

## 구현 계약

P05의 완주된 열린 포지션 스냅샷과 P03 `READY` 명세를 정식 고객사·포지션 ID와 ClickUp 스냅샷 지문으로 결합하고, 미완주·`NOT_RUN`·닫힌 상태·ID/지문 불일치는 계산하지 않고 `NEEDS_DECISION`으로 반환한다. 그 입력에서 긴급도 25, 가치 20, 부족률 25, 경과 15, 채널 빠짐 10, 내부 즉시검토 5의 버전된 순수 함수를 구현한다. 부족률은 P12 공용 스키마를 통과한 P13 내부+규칙엔진+`ELIGIBLE`과 선택적으로 주입된 외부+사람+`ACCEPTED`를 `canonical_candidate_id` 합집합으로 센다. P25 이전 최초 계산에서 외부 집합은 비어 있고, 내부 즉시검토 5점은 P13 내부 `ELIGIBLE`이 있을 때만 준다. `REVIEW_REQUIRED | INELIGIBLE | REJECTED | HOLD`는 세지 않는다. 부족률의 목표값은 P03의 `target_eligible_candidate_count`만 쓰고 `target_pre_interview_count`를 대신 쓰지 않는다. 각 구간과 배율은 통합 기획서의 `position_priority_v1`을 그대로 따르고, 위험은 감점이 아니라 실행 대상 제외다. 동점은 마감·생성·ID 순이다. P12 공용 함수를 그대로 호출해 `candidate_eligibility_receipt_set_hash`를 얻고 자체 해시 구현은 만들지 않는다. 출력은 이 집합 지문, P03·P05·P13 입력 지문, 점수·이유·정렬 결과, 정책 버전을 묶은 `position_priority_decision_hash`를 포함해 P08이 같은 입력 세대만 결합하게 한다.

## 가짜 합격을 깨는 시험

P05 미완주·`NOT_RUN`·닫힌 스냅샷, P03/P05 정식 ID·지문 불일치, P13 영수증 누락·중복 별칭·`REVIEW_REQUIRED` 혼입, 외부 `ACCEPTED` 합산과 내부/외부 동일 ID 중복, `REJECTED | HOLD` 혼입, 영수증 집합 지문 변조, `target_eligible_candidate_count` 0, 목표 필드 교환, 승인 채널 0개, 미래 날짜, 범위 밖 가치등급, NaN, 정책 위험 절대 차단, 동점, 입력 순서 변경, 시간 고정을 시험한다.

## 검증

골든 벡터, 경계·속성시험, 결정 지문 100회 1종, `bash verify.sh`.

## 원자적 인수 기준

후속 구현은 `bash scripts/acceptance-ai-ra-p06.sh` 한 명령으로 P05의 완주된 열린 포지션 스냅샷이 P03 `READY` 명세와 정식 ID·지문이 일치하고 P12 공용 스키마의 내부 `ELIGIBLE`·선택적 외부 `ACCEPTED` 영수증 집합이 유효할 때만 계산되며, 미완주·`NOT_RUN`·닫힘·불일치·영수증 누락은 점수 0건임을 검사해야 한다. 미래 P25 구현 없이 합성 외부 영수증 fixture로 재계산을 검증한다. 동일 입력 100회에서 `candidate_eligibility_receipt_set_hash`, 순서·점수·이유와 `position_priority_decision_hash`가 1종이고 동점·경계값 규칙이 고정돼야 하며, 같은 정식 후보의 내부/외부 중복과 `REVIEW_REQUIRED | INELIGIBLE | REJECTED | HOLD` 혼입을 거부해야 한다. P03 출력의 `target_eligible_candidate_count`만 부족률 목표로 소비하고 `target_pre_interview_count`로 교환한 변조도 거부해야 한다. 정상 실행은 `PASS AI_RA_P06 <실제 핵심 건수>`를 출력하되 실제 핵심 건수는 반드시 1 이상이고 종료값 0을 남겨야 하며, 핵심 차단을 한 줄 고장 낸 반대 시험은 0이 아닌 종료값이어야 한다. 이 프로젝트는 자기 인수 스크립트만 소유한다. P04가 소유한 `scripts/acceptance-ai-ra-all.sh`와 서버 workflow가 이름 규칙으로 자동 발견해야 하며, 이후 프로젝트는 공용 workflow를 직접 수정하지 않는다.

## 라이브 증거와 멈춤점

합성 입력만 사용한다. 실제 포지션 선정이나 ClickUp 변경 없이 함수 계약에서 멈춘다.

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
