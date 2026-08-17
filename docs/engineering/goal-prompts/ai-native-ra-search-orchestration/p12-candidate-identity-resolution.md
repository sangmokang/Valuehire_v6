# P12 — 후보 동일인 연결과 사람 검토

아래 내용을 새 Codex 작업의 첫 프롬프트로 그대로 사용한다.

## 목표

강한 동일인 근거만 자동 연결하고 이름·회사·직함 유사도는 검토 대기로 남긴다.

## 선행조건

P09~P11 `CONTRACT_PASS`.

## 작업 소유 범위

`humansearch/src/humansearch/candidates/identity.py`, `humansearch/src/humansearch/candidates/eligibility_receipts.py`, `contracts/candidate_eligibility_receipt.schema.json`, 연결 근거와 공용 적격 영수증·집합 지문 모델, 단위·속성시험.

경로가 현재 SOT와 충돌하면 임의로 다른 영역까지 고치지 말고 목표 문서에 충돌을 증거와 함께 기록해 이 프로젝트를 중단한다.

## 비범위

원천 행 병합·삭제, 이름만으로 자동 병합, 언어모델 최종 판정.

## RED 먼저

동명이인 또는 이름+회사 일치만으로 자동 병합되거나 연결 해제를 기록 삭제로 처리하는 실패 시험을 먼저 만든다.

## 구현 계약

검증된 이메일, 승인된 프로필 URL, 동일 이력서 내용 지문, 출처의 자기 링크만 강한 근거다. 동일인 클러스터에는 원천 ID와 분리된 불변 `canonical_candidate_id`를 부여하고, 결과는 `AUTO_LINK | NEEDS_REVIEW | DISTINCT`와 이 ID·근거·정책버전·별칭 폐쇄(alias closure)를 반환한다. P09~P11 내부 목록뿐 아니라 후속 P22~P24 staged evidence도 같은 입력 포트로 받을 수 있게 하되, 이름·회사·직함만으로 연결하지 않는다. 새 연결은 가장 오래된 기존 정식 ID를 유지하고 다른 ID를 별칭으로 남기며, 어느 ID로 조회해도 같은 현재 ID와 이력에 도달해야 한다. 연결과 해제는 각각 대상·근거 종류·사유·출처·검토자·시각·앞 사건 지문을 가진 사건으로 뒤에 추가하고, 연결 해제도 과거 연결 사건을 삭제하거나 ID를 재사용하지 않는다. 해제 시 기준 구성요소는 기존 ID를 유지하고 분리된 구성요소는 새 ID를 받으며, 분리 전 `DO_NOT_CONTACT` 보호는 양쪽에 보수적으로 승계하고 명시적 사람 검토 사건 없이는 해제하지 않는다.

공용 `candidate_eligibility_receipt`는 `receipt_version`, `canonical_candidate_id`, 별칭 폐쇄 지문, `origin_kind=INTERNAL_INVENTORY | EXTERNAL_STAGED_EVIDENCE`, `decision_source=RULE_ENGINE | HUMAN`, `decision_state`, 근거 지문, 정책 버전, 결정 사건 지문·시각만 담고 후보 원문을 금지한다. 허용 조합은 내부+규칙엔진+`ELIGIBLE | REVIEW_REQUIRED | INELIGIBLE`, 외부+사람+`ACCEPTED | REJECTED | HOLD`뿐이다. P12는 스키마와 조합 검증만 소유하고, P13은 내부 결정 생성, P25는 외부 사람 결정 생성, P07은 계수 규칙을 각각 소유한다.

P12의 `eligibility_receipts.py`는 `candidate_eligibility_receipt_set_hash` 생성의 유일한 구현을 소유한다. 먼저 별칭 폐쇄를 현재 정식 ID로 해석하고 append-only 사건 사슬이 유효한 영수증 중 `(canonical_candidate_id, origin_kind)`별 현재 유효 결정 1개만 선택하며, 같은 사건 세대의 현재 결정이 둘이면 거부한다. 각 영수증에서 `receipt_version`, 현재 `canonical_candidate_id`, 별칭 폐쇄 지문, `origin_kind`, `decision_source`, `decision_state`, 근거 지문, 정책 버전, 결정 사건 지문을 고정 키로 추출한다. 모든 식별자·버전·지문은 스키마가 허용한 ASCII 값만 받고, 위 레코드를 `(canonical_candidate_id, origin_kind, decision_source, decision_state, policy_version, decision_event_hash)` UTF-8 바이트 오름차순으로 정렬한다. 키 이름 오름차순·공백 없음·배열 순서 보존의 정규 JSON UTF-8에 SHA-256을 적용해 소문자 64자리 hex 앞에 `sha256:`을 붙인다. `decided_at`은 결정 사건 지문이 이미 포함하므로 집합 직렬화에는 다시 넣지 않는다. P06·P07은 이 함수를 불러 쓰고 복제 구현하거나 필드를 빼지 못한다.

## 가짜 합격을 깨는 시험

공용 이메일, URL 정규화 충돌, 이름 변경, 동일 회사 동명이인, 오래된 이력서, 상충하는 강한 키, 후속 staged evidence 입력, 두 클러스터 연결 뒤 별칭 조회, 연결 해제 뒤 ID 비재사용과 양쪽 접촉금지 승계, 적격 영수증 필수값 누락·후보 원문·origin/source/state 불법 조합을 시험한다. 집합 지문은 입력 순열 100개에서 1종이고 상태·정책·사건 지문 하나를 바꾸면 달라지며, 같은 후보·origin의 현재 결정 중복과 ASCII 밖 식별자는 거부해야 한다.

## 검증

골든 쌍/삼중 후보 집합, 순서 불변성, 같은 입력의 정식 ID 안정성, 잘못된 연결 해제 가능성, 해제 뒤 별칭·보호 이력 보존, `bash verify.sh`.

## 원자적 인수 기준

후속 구현은 `bash scripts/acceptance-ai-ra-p12.sh` 한 명령으로 강한 식별자만 자동 연결하고 이름·회사·직함만 같은 사례와 충돌 식별자는 사람 검토로 남음을 검사해야 한다. 동일 입력·순서 변경에도 `canonical_candidate_id`가 안정적이고, 연결 뒤 과거 별칭이 현재 ID로 해석되며, 해제 뒤 ID를 재사용하지 않고 분리된 양쪽에 기존 `DO_NOT_CONTACT` 보호가 남아야 한다. 공용 적격 영수증 스키마는 내부 규칙 결정과 외부 사람 결정의 허용 조합만 받고 후보 원문·누락 ID·불법 조합을 거부해야 한다. 집합 지문 함수는 순열 100개에 같은 `sha256:<64hex>` 1종을 반환하고 상태·정책·사건 지문 변조에는 다른 값, 현재 결정 중복·비ASCII 식별자에는 거부를 반환해야 한다. 정상 실행은 `PASS AI_RA_P12 <실제 핵심 건수>`를 출력하되 실제 핵심 건수는 반드시 1 이상이고 종료값 0을 남겨야 하며, 핵심 차단을 한 줄 고장 낸 반대 시험은 0이 아닌 종료값이어야 한다. 이 프로젝트는 자기 인수 스크립트만 소유한다. P04가 소유한 `scripts/acceptance-ai-ra-all.sh`와 서버 workflow가 이름 규칙으로 자동 발견해야 하며, 이후 프로젝트는 공용 workflow를 직접 수정하지 않는다.

## 라이브 증거와 멈춤점

합성 식별자만 사용한다. 실제 후보 연결 행을 쓰지 않고 판정 계약에서 멈춘다.

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
