# Repository data protection 적대감사 후속 goal — 2026-08-26

## 1층 결론

현재 `1a3c384fb0d6f6715340a2deb8ec3d373c78e9b5`는 정상 CSV와 정상 SQL을 개인정보 적재로 잘못 차단하는 다섯 반례와, `PASS:`/`CHECKED:`를 출력만 하는 가짜 인수 검사를 통과시키는 반례가 재현돼 병합할 수 없다. 이 작업은 해당 오탐과 검사기 위조 통과를 RED→GREEN으로 고치되, 기존 부분 Git 실패·집계·경로 비노출 방어를 약화하지 않는다.

원격 push·PR·merge와 원본 dirty worktree 수정은 하지 않는다. Claude V1과 P23이 실행되지 않으면 로컬 구현 통과와 전체 배송 가능 여부를 분리한다.

## 2층 판단 근거

- `pii_word_count`가 컬럼 이름의 부분 문자열까지 개인정보 낱말로 센다. `username,mailer`는 개인정보 컬럼이 아니지만 `name`과 `mail` 두 종으로 계산된다.
- SQL 적재문 판정은 주석과 작은따옴표 문자열을 지운 사본을 만들지만, 개인정보 낱말 수는 원문 전체에서 세므로 주석·값 문자열의 `name email`이 별도 정상 적재문과 결합된다.
- `INSERT ... VALUES` 정규식이 세미콜론을 넘어가므로 서로 다른 SQL 문장의 단어가 한 적재문처럼 결합된다.
- `COPY ... FROM` 정규식은 `COPY (SELECT ... FROM ...) TO STDOUT` 내보내기도 적재로 판정한다.
- `run-acceptance.sh`는 종료값과 `PASS`/`CHECKED` 출력만 보므로 실제 판정 명령 없이 문구만 출력하는 가짜 검사도 통과한다.
- 출력 전용 사본 거부를 추가하자 `check-pre-push-runtime.sh`의 정상 sandbox stub도 출력 전용이라 원칙 검사가 `CHECKED: 0`으로 실패했다. fixture가 자기 파일 존재를 실제 판정하도록 바꿔 새 래퍼 계약과 맞춘다.
- 부분 Git 출력 실패, `all` 집계, 원문 경로 비노출, 정확한 대상 수집, CI 단일 배선은 기존 방어이며 이번 수정의 회귀 금지 대상이다.

## 위험 등급과 기준

- 등급: Strict L3 — 개인정보 판정기·SOT·검사기 변경.
- 구현 기준: `fdac401be104bc5d9454401edf0477fb478636dc..HEAD`.
- 이번 RED 기준 SHA: `1a3c384fb0d6f6715340a2deb8ec3d373c78e9b5`.
- 파일 hard limit: 600줄, 함수 hard limit: 100줄.
- 정본: `docs/sot/coding-principles.md`, `docs/sot/principles.yaml`, `docs/sot/features/engineering/repository-data-protection.yaml`, `docs/sot/verification-commands.md`.

## EARS 인수 기준

### AC-N1 — 정확한 개인정보 컬럼 낱말

When CSV·TSV·SQL의 식별자를 판정할 때, 시스템은 `name`, `email` 등 정본에 등록된 완전한 낱말만 세고 `username`, `mailer` 같은 부분 문자열은 세지 않아야 한다.

- counter-AC: `username,mailer`가 `name`+`mail`로 두 종 처리되어 정상 CSV가 실패한다.
- 검증: 전용 acceptance에서 현재 CSV 대조군이 exit 0, PASS 1, FAIL 0, CHECKED 1이어야 한다.

### AC-N2 — SQL 판정용 사본 일관성

When SQL 개인정보 적재 여부를 판정할 때, 시스템은 주석과 작은따옴표 문자열 내용을 제거한 같은 판정용 사본에서 개인정보 컬럼 낱말과 적재문을 모두 판정해야 한다.

- counter-AC: 주석 또는 값 문자열에만 `name email`이 있고 실제 적재 컬럼은 `id,status`인 SQL이 실패한다.
- 검증: 현재·삭제 history·all 대조군의 exit/PASS/FAIL/NOT_RUN/CHECKED를 정확히 검증한다.

### AC-N3 — INSERT 문장 경계

When `INSERT INTO ... VALUES`를 판정할 때, 시스템은 하나의 세미콜론 경계 안에서 세 키워드가 순서대로 존재할 때만 적재문으로 인정해야 한다.

- counter-AC: 첫 문장의 `INSERT INTO ... SELECT`와 다음 schema 문장의 `values(name,email)`가 결합된다.
- 검증: 서로 다른 문장 대조군은 exit 0이어야 하고 기존 여러 줄 실제 INSERT 적재문은 exit 1이어야 한다.

### AC-N4 — COPY 방향 구분

When PostgreSQL COPY를 판정할 때, 시스템은 테이블 대상 뒤의 `FROM` 적재만 차단하고 `COPY (SELECT ... FROM ...) TO` 내보내기는 차단하지 않아야 한다.

- counter-AC: 쿼리 내부 `FROM`을 COPY 적재 방향으로 오인한다.
- 검증: COPY query export 대조군은 exit 0이고, 기존 현재·history·all `COPY table ... FROM`은 exit 1이어야 한다.

### AC-N5 — 기존 안전 계약 보존

While 위 SQL·컬럼 판정을 고칠 때, 시스템은 부분 `git ls-files` 실패를 `NOT_RUN/CHECKED: 0/exit 2`로 처리하고, `all`의 FAIL·NOT_RUN·CHECKED 집계와 모든 경로 가명 출력을 그대로 보존해야 한다.

- counter-AC: 오탐 수정이 실제 PII 적재를 허용하거나 부분 목록을 PASS로 접는다.
- 검증: repository acceptance, hs-a4, semantic mutations, CI integrity, 공격 mutation을 모두 재실행한다.

### AC-N6 — 출력 전용 인수 검사 위조 차단

When `run-acceptance.sh`가 인수 검사를 실행할 때, 시스템은 `PASS:`/`CHECKED:`/`VERDICT:` 문구만 출력하고 실제 판정 명령이 없는 스크립트를 검사 실행으로 인정하지 않아야 한다.

- counter-AC: `echo "PASS: fake"; echo "CHECKED: 1"; echo "VERDICT: PASS"`만 있는 사본이 exit 0으로 통과한다.
- 검증: `acceptance-semantic-mutations.sh`가 `fake-pass-output` 무력화를 전 대상에 주입해 모두 불합격 처리해야 한다.

## 입출력·오류·경계 계약

- 입력: Git blob인 `csv|tsv|sql`, mode `tracked|history|pii|all`.
- 출력: 원문 경로·개인정보 값을 제외한 `PASS:`, `FAIL:`, `NOT_RUN:`, 마지막 `CHECKED: N`.
- 종료값: `0=PASS`, `1=위반`, `2=검사 불성립`.
- SQL 문장 경계: 세미콜론. 실제 multiline 공백은 허용한다.
- COPY 적재: `COPY <table-or-qualified-identifier> [(columns)] FROM ...`; `COPY (<query containing FROM>) TO ...`는 적재가 아니다.
- 개인정보 낱말: 정본 목록과 식별자 경계가 일치하는 고유 낱말 수.
- 현재와 history는 `scan_pii_content` 하나를 계속 공유한다.

## RED 원장

`1a3c384f...`의 임시 저장소 fresh 실행에서 다음 정상 입력이 모두 `exit 1`로 잘못 차단됐다.

1. CSV `username,mailer` + 데이터 1행.
2. 주석에만 `name email`, 실제 `INSERT INTO audit(id,status) VALUES ...`.
3. 값 문자열에만 `name email`, 실제 `INSERT INTO audit(message,status) VALUES ...`.
4. 첫 문장 `INSERT INTO ... SELECT`, 다음 문장 `CREATE TABLE values(name,email)`.
5. `COPY (SELECT name,email FROM candidates) TO STDOUT`.

또한 `run-acceptance.sh`에 `PASS: fake`, `CHECKED: 1`, `VERDICT: PASS`만 출력하는 임시 사본을 주입하면 exit 0으로 통과했다.

각 출력은 원문 경로·값 없이 fingerprint만 포함했으므로 비노출 계약 자체는 유지됐다.

## Harness와 mutation

1. 전용 acceptance에 위 정상 대조군을 먼저 추가해 RED를 고정한다.
2. 실제 PII 적재 현재/history/all 사례는 그대로 RED여야 한다.
3. 컬럼 부분 문자열 허용, SQL raw-word-count 복귀, 세미콜론 횡단, COPY query export 오인, 가짜 PASS 출력 허용의 mutation을 각각 주입하고 acceptance가 죽이는지 확인한다.
4. 600/601·100/101, zero-target, 부분 Git 출력, 원문 경로 비노출, CI 호출 삭제 mutation을 재실행한다.

## 롤백·영향 반경·데이터 안전

- 영향 반경: `scripts/scan-data-exposure.sh`, 전용 acceptance, 기능·검증 SOT, 관련 mutation 증거.
- 롤백: 후속 로컬 커밋 하나를 되돌리되 이전 `1a3c384f...` 증거 커밋은 보존한다.
- 데이터 안전: 합성 `.invalid` 값만 사용하고 실제 후보자 데이터·원문 경로를 열지 않는다.
- 원본 worktree: 읽기 전용 상태 비교만 하며 변경·복구·재기준화하지 않는다.

## 완료 금지 조건

- 새 대조군 또는 기존 실제 적재 사례 하나라도 실패.
- mutation 하나라도 생존.
- 원문 개인정보·원문 경로 출력 발견.
- Claude V1, Codex V2, humanreview 중 필수 판정 미실행.
- P23 원격 검증이 `NOT_RUN`인 상태에서 전체 배송 가능하다고 주장.

## GREEN 및 공격 증거

- 전용 acceptance: exit 0, `CHECKED: 42`, `VERDICT: PASS`. 신규 9개 정상 대조군과 기존 실제 적재·부분 Git·집계·경로 비노출 계약이 함께 통과했다.
- semantic mutations: exit 0, `CHECKED: 11`, `VERDICT: PASS`. Git 대상 27개를 정확히 수집해 기존 5종과 `fake-pass-output` 1종을 전량 차단했다.
- 공격 mutation harness: 첫 실행에서 세미콜론 분할만 제거한 불충분한 변이가 생산 정규식의 `[^;]*` 이중 방어 때문에 살아남았다. harness를 문장 분할과 정규식 경계를 함께 복귀시키는 실제 회귀로 교정한 뒤 full 재실행은 exit 0, `MUTATIONS_CHECKED: 12`, `VERDICT: PASS`였다.
- 정적 검증: 변경 shell의 `bash -n`, `shellcheck -S warning`, `git diff --check` 모두 exit 0. 변경 직접 작성 파일은 103~512줄로 600줄 hard limit 안이다.
- 통합 RED: 강화된 runner가 `check-pre-push-runtime.sh`의 출력 전용 정상 stub 두 개를 거부해 principles가 exit 1, `CHECKED: 0`이었다. 두 stub에 자기 파일 존재 판정을 추가한 뒤 principles를 다시 실행한다.
- 커밋 후 통합 RED: runner가 판정 줄을 `^PASS:`로만 제한해 `VERDICT: PASS` + `CHECKED: 34` 형식의 정상 principles를 exit 1로 오차단했다. 정확한 `PASS:` 또는 정확한 `VERDICT: PASS`만 허용하고 semantic 정상 표본에 두 출력 형식을 모두 추가한다.
- 다음 독립 실행 프롬프트: `docs/engineering/repository-data-protection-strict-l3-next-delta-prompt-2026-08-26.md`. 기존 Strict L3 문서의 대체본이 아니라 마지막에 붙이는 추가 델타다.

위 수치는 커밋 전 targeted 증거다. Git index blob을 읽는 scanner의 authoritative 현재/history/all과 전체 로컬 게이트는 최종 로컬 커밋 SHA에서 다시 실행하며, 그 전에는 완료 근거로 승격하지 않는다.
