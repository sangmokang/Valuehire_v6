# P13 — 근거 분리형 내부 후보 매칭

아래 내용을 새 Codex 작업의 첫 프롬프트로 그대로 사용한다.

## 목표

적합도·연락 순서·근거 완전성·절대 차단을 분리해 같은 입력에서 같은 내부 후보 순서를 만든다.

## 선행조건

P03·P12 `CONTRACT_PASS`.

## 작업 소유 범위

`humansearch/src/humansearch/matching/internal_match.py`, 규칙 버전, 골든 fixture·단위/속성시험.

경로가 현재 SOT와 충돌하면 임의로 다른 영역까지 고치지 말고 목표 문서에 충돌을 증거와 함께 기록해 이 프로젝트를 중단한다.

## 비범위

언어모델의 최종 점수, 후보 자동 연락·탈락, 원문 없는 사실 생성.

## RED 먼저

원문 근거가 없거나 hard gate가 있는데 높은 단일 점수로 통과하는 실패 시험을 먼저 만든다.

## 구현 계약

P12의 `canonical_candidate_id`와 별칭 폐쇄를 적용해 동일 후보를 한 번만 계산한다. `fit_score`, `contact_priority`, `evidence_completeness`, `hard_gate`를 별도로 반환하고, 버전된 임계값으로 `gap_eligibility=ELIGIBLE | REVIEW_REQUIRED | INELIGIBLE`을 정한다. 이 결정은 P12 공용 스키마의 내부+규칙엔진 영수증으로만 출력한다. `ELIGIBLE`은 hard gate가 없고 승인된 필수조건과 근거 완전성 임계값을 모두 통과한 경우뿐이며, `REVIEW_REQUIRED`·`INELIGIBLE`·강한 동일인 근거가 없는 후보는 P07의 `current_eligible_unique_candidate_count`에 포함할 수 없다. LLM은 근거 구간 초안만 제공하고 코드가 승인된 구조값을 계산한다.

## 가짜 합격을 깨는 시험

누락 근거, 상충 이력, 필수 자격 부재, 점수 동점, 시간 변화, 프롬프트 문구 변화, 과거 규칙 버전, 같은 후보의 원천·별칭 중복, `REVIEW_REQUIRED`를 적격 수에 넣는 변조를 시험한다.

## 검증

골든 후보 순위, 100회 출력 지문 1종, hard gate 변조 시험, `bash verify.sh`.

## 원자적 인수 기준

후속 구현은 `bash scripts/acceptance-ai-ra-p13.sh` 한 명령으로 필수조건·적합도·연락 가능성·근거 충분성을 분리하고 같은 입력 100회에서 결과 지문이 1종임을 검사해야 한다. P12 별칭을 닫은 `canonical_candidate_id`마다 P12 공용 스키마를 통과한 내부 `ELIGIBLE` 영수증은 최대 1개이고, hard gate·근거 미달·`REVIEW_REQUIRED` 후보의 적격 영수증은 0개이며 이 값들이 P07 입력 지문에 보존돼야 한다. 정상 실행은 `PASS AI_RA_P13 <실제 핵심 건수>`를 출력하되 실제 핵심 건수는 반드시 1 이상이고 종료값 0을 남겨야 하며, 핵심 차단을 한 줄 고장 낸 반대 시험은 0이 아닌 종료값이어야 한다. 이 프로젝트는 자기 인수 스크립트만 소유한다. P04가 소유한 `scripts/acceptance-ai-ra-all.sh`와 서버 workflow가 이름 규칙으로 자동 발견해야 하며, 이후 프로젝트는 공용 workflow를 직접 수정하지 않는다.

## 라이브 증거와 멈춤점

익명 합성 이력만 쓴다. 실제 후보 평가·연락 없이 순수 계산에서 멈춘다.

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
