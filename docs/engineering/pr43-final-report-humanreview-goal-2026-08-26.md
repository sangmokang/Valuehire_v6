# PR #43 최종 보고·SHIP 판정기 humanreview goal (2026-08-26)

## 1층 — 결론

직전 보고의 “지금은 병합하면 안 된다”는 결론은 맞지만, 다음 단계에서 사용할 두 검사 경로에 실패를 잘못 분류하거나 일부 검사만 보고 합격시키는 문제가 남아 있다.

이 작업은 읽기 실패를 모르는 상태로 정직하게 분류하고, 같은 후보에 붙은 검사가 모두 끝나 성공했을 때만 원격 검증 완료로 인정하도록 고친다. 원격 전달과 병합은 하지 않는다.

## 2층 — 판단 근거

- 정본 경계 검사기는 정본을 읽지 못하거나 P11 줄의 인코딩이 깨지면 `VERDICT: NOT_RUN`, 종료값 2를 내야 하지만 현재는 Ruby 예외와 종료값 1을 낸다.
- 원격 SHA 검사기는 한 커밋에 이름이 같은 `verify` 실행이 여러 개 있어도 첫 결론만 사용한다. 첫 실행이 성공이고 다른 실행이 진행 중이거나 실패면 `VERDICT: VERIFIED`를 잘못 낸다.
- PR #43의 현재 원격 head에는 실제로 `verify` check-run이 2개 있으므로 두 번째 문제는 가상 조건만이 아니다.
- 직전 보고의 로컬 SHA, 원격 SHA, 기존 Actions, 산출물 해시는 다시 확인해 모두 일치했다. 뒤집히는 것은 최종 `REQUEST_CHANGES`가 아니라 “다음 SHIP 프롬프트에 추가 수정이 필요 없다”는 전제다.

## 모드와 범위

- 모드: code-change
- 위험등급: L3
- 기준 HEAD: `d10ce987658a4d7ef24ea1a5265f2e2f697a1252`
- 기준 main: `c59bad7b160c473cda5545e76e6fa6bcc711a7ea`
- 대상:
  - `scripts/verify/check-strict-principles-skills.sh`
  - `scripts/acceptance-principles-mutations.sh`
  - `scripts/verify/check-verified-sha.sh`
  - `scripts/acceptance-verified-sha.sh`
  - 관련 CI·검증 문서와 다음 Strict 프롬프트
- 비범위: history scanner 기능 확대, Issue #22, push, PR 수정·생성·병합, PR #29 종료

## RED 원장

### F1 — 정본 읽기·인코딩 실패가 구조화되지 않음

- 상태: REPRODUCED
- 입력: 격리 사본에서 `coding-principles.md` 권한 000 또는 P11 줄에 잘못된 UTF-8 바이트 삽입
- 실제: Ruby stack trace, exit 1, `VERDICT: NOT_RUN` 없음
- 영향: 사용자는 계약 위반 FAIL과 검사 자체를 수행하지 못한 NOT_RUN을 구분할 수 없다.

### F2 — 여러 원격 실행 중 첫 성공만 보고 거짓 VERIFIED

- 상태: REPRODUCED
- 입력: 같은 SHA의 결론 목록 `success + null`, `success + failure`
- 실제: 첫 줄 `success`만 판정부에 전달돼 두 경우 모두 `VERDICT: VERIFIED`, exit 0
- 영향: PR용 검사 하나가 진행 중이거나 실패했는데도 push용 검사 하나만 성공하면 병합 준비 완료로 오인할 수 있다.

## EARS 인수 기준

### AC-1 정본 조회 실패 폐쇄

If 정본 파일을 읽을 수 없거나 정본 텍스트를 유효한 UTF-8로 해석할 수 없으면, 시스템은 `VERDICT: NOT_RUN`과 종료값 2를 출력해야 한다.

- 검증: 원칙 변이 시험의 unreadable·invalid-encoding 격리 표본
- counter-AC: Ruby stack trace와 exit 1만 남겨 원인과 상태를 잃는 경우

### AC-2 다중 원격 실행 전량 성공

When 같은 원격 SHA에 이름이 `verify`인 check-run이 둘 이상 있으면, 시스템은 모든 실행이 completed/success일 때만 VERIFIED를 허용해야 한다.

- 검증: `success+success` 통과, `success+pending`, `success+failure`, 빈 목록 차단
- counter-AC: API 반환 첫 줄이 success라는 이유만으로 나머지를 버리는 경우

### AC-3 기존 SHA·작업트리 계약 보존

While 다중 실행 집계를 추가해도, 시스템은 로컬 HEAD·원격 HEAD·CI SHA 일치와 clean worktree를 계속 요구해야 한다.

- 검증: 기존 `acceptance-verified-sha.sh` 진리표 전체와 새 집계 반례
- counter-AC: 여러 실행 확인을 추가하면서 SHA 비교나 dirty 차단을 제거하는 경우

### AC-4 기존 Strict·CI 배선 보존

While 두 검사기를 수정해도, 시스템은 원칙 34개, 경계 hard/hard+1, 의미론적 변이, CI step integrity와 history scan 게이트를 그대로 통과해야 한다.

- 검증: 관련 전체 원명령 재실행
- counter-AC: 새 반례만 맞추고 기존 CHECKED 수나 CI 호출을 약화하는 경우

## 입출력·오류·경계 계약

### Strict 경계 검사기

- 입력: 서로 다른 두 Strict skill 파일 경로와 검사기 저장소의 정본 파일
- 출력: PASS 0, 계약 위반 FAIL 1, 읽기·파싱 불능 NOT_RUN 2
- 경계: hard와 hard+1, SOT missing/empty/unreadable/invalid UTF-8/duplicate hard

### SHA 검사기

- 입력: 로컬 HEAD, 원격 브랜치 HEAD, 같은 원격 SHA의 모든 `verify` check-run 상태·결론, 작업트리 상태
- 출력: 전부 일치·모든 run completed/success·clean이면 VERIFIED 0; 알려진 불일치면 UNVERIFIED 1; 조회 자체 실패면 NOT_RUN 2
- 경계: 0개, 1개, 2개 이상, pending/null, failure, cancelled, SHA 불일치, dirty

## Harness 게이트

- Gate 0: SOT·과거 goal·직전 보고·현재 HEAD/remote 재고정
- Gate 1: AC/counter-AC와 위 입출력·오류·경계 계약
- Gate 2: F1·F2 격리 RED 보존
- Gate 3: 검사기 최소 수정과 새 반례 GREEN
- Gate 3.5: CI/다음 프롬프트가 실제 검사기를 호출하는 경로 재확인
- Gate 4: 18/23/33/34/원칙 변이/verified SHA/CI integrity/semantic mutation/verify/history scan
- Gate 5: 로컬 CHECKPOINT와 다음 Strict 프롬프트만 생성

## 영향 반경·데이터 안전·롤백

- 영향 반경: Strict skill 경계 판정, 정확한 원격 SHA 판정, 두 인수 검사, CI와 SHIP 지침
- 데이터 안전: 모든 고장 입력은 자동 삭제되는 임시 디렉터리 또는 순수 판정부 입력으로만 실행한다. 자격증명·제품 데이터·외부 쓰기는 없다.
- 롤백: 새 로컬 커밋을 `git revert <sha>`로 되돌린다. push 전이므로 원격에는 영향이 없다.

## 결정 카드

> **무엇을** — 읽기 실패를 구조화하고 같은 SHA의 검사 실행을 전량 집계한다.
> **왜** — 모르는 상태와 일부 성공을 완료로 접으면 원격 SHA 정직성 계약이 무너진다.
> **버린 길** — 다음 프롬프트에 수동 확인 문장만 추가하는 방법은 판정기 자체의 거짓 초록을 남기므로 기각한다.
> **대가** — 일부 중복 실행이 실패한 뒤 다른 실행만 재성공한 경우 보수적으로 UNVERIFIED가 될 수 있다.
> **되돌리기** — 로컬 checkpoint를 revert하고 이전 판정기로 돌아간다.

## 검증 장부

| 시각 | 세션 | HEAD | 명령 | 종료값 | 상태 | 핵심 출력 |
|---|---|---|---|---:|---|---|
| 2026-08-26 | pr43-final-report-humanreview | d10ce987658a4d7ef24ea1a5265f2e2f697a1252 | `bash scripts/acceptance-principles-check.sh` | 0 | PASS | `CHECKED: 34` |
| 2026-08-26 | pr43-final-report-humanreview | d10ce987658a4d7ef24ea1a5265f2e2f697a1252 | unreadable SOT 격리 probe | 1 | FAIL(계약) | Ruby `Errno::EACCES`, NOT_RUN 없음 |
| 2026-08-26 | pr43-final-report-humanreview | d10ce987658a4d7ef24ea1a5265f2e2f697a1252 | invalid UTF-8 P11 격리 probe | 1 | FAIL(계약) | Ruby `ArgumentError`, NOT_RUN 없음 |
| 2026-08-26 | pr43-final-report-humanreview | d10ce987658a4d7ef24ea1a5265f2e2f697a1252 | 다중 check-run 첫 줄 집계 probe | 0 | FAIL(계약) | `success+null`, `success+failure` 모두 `VERDICT: VERIFIED` |
| 2026-08-26 | pr43-final-report-humanreview | d10ce987658a4d7ef24ea1a5265f2e2f697a1252+dirty | `run-acceptance acceptance-principles-mutations` | 0 | PASS | 판정 49건, `CHECKED: 48`; 읽기·UTF-8 반례 포함 |
| 2026-08-26 | pr43-final-report-humanreview | d10ce987658a4d7ef24ea1a5265f2e2f697a1252+dirty | `run-acceptance acceptance-verified-sha` | 0 | PASS | 판정 19건, `CHECKED: 18`; 다중 run·빈 목록·오형식 포함 |
| 2026-08-26 | pr43-final-report-humanreview | d10ce987658a4d7ef24ea1a5265f2e2f697a1252+dirty | `acceptance-ci-step-integrity` | 0 | PASS | `CHECKED: 14` |
| 2026-08-26 | pr43-final-report-humanreview | d10ce987658a4d7ef24ea1a5265f2e2f697a1252+dirty | `bash -n` + `shellcheck -S warning` + `git diff --check` | 0 | PASS | 수정한 4개 셸 파일과 전체 diff |

### 전체 G 회귀

- `acceptance-history-scan-failclosed`: PASS, `CHECKED: 18`
- `acceptance-0-2-unreachable-content`: PASS, `CHECKED: 23`
- `acceptance-verify-ac-m`: PASS, `CHECKED: 33`
- `acceptance-principles-check`: PASS, `CHECKED: 34`
- `acceptance-principles-mutations`: PASS, `CHECKED: 48`
- `acceptance-verified-sha`: PASS, `CHECKED: 18`
- `acceptance-ci-step-integrity`: PASS, `CHECKED: 14`
- `acceptance-semantic-mutations`: PASS, `CHECKED: 10` (검사기 27개 × 변이 5종)
- `bash verify.sh`: PASS
- `bash scripts/scan-history-secrets.sh`: PASS, blob 1380개

첫 원칙 변이 병렬 실행 한 번은 읽기 전용으로 위임한 에이전트가 지시를 어기고 같은 파일을 수정해 `SOURCE-TREE` 불변 검사가 실패했다. 해당 에이전트를 중단하고 변경을 직접 대조·통합한 뒤 격리된 순차 재실행에서 `CHECKED: 48`, exit 0을 확인했다. 제품 결함으로 세지 않되 재현성 장부에는 남긴다.

## V1/V2 독립 검증

- Claude V1 최초 호출: NOT_RUN — `Error: No messages returned from query`; artifact `.omx/artifacts/claude-pr43-final-report-humanreview-v1-no-messages-2026-08-26.md`; SHA256 `812a6629aaac58799da6c0cdc469b8c713c2831387df125c6f27facad43ddf57`
- Claude V1 고유 재시도: NOT_RUN — 축소 프롬프트도 판정 본문 없음; artifact `.omx/artifacts/claude-pr43-final-report-humanreview-v1-retry-no-messages-2026-08-26.md`; SHA256 `bf833a6e6490455c2683557ac87eaeff2394d95c664d118ea778088138a348f2`
- 같은 실패 경로를 세 번째 반복하지 않는다. V1 NOT_RUN이므로 Strict 최종 PASS/READY를 선언하지 않는다.
- Codex V2: 최종 diff 읽기 전용 재검증은 로컬 checkpoint 뒤 ignored artifact와 최종 응답에 고정한다. tracked goal을 V2 뒤에 다시 커밋하면 V2가 검토한 SHA가 바뀌므로, checkpoint 이후의 V2 원문은 `.omx/artifacts/`에 둔다.

## quiet-failure 주입 범위

이 변경은 Bash/Ruby 기반 판정기이며 JavaScript/Python의 `catch`, `Map.get`, `extensions` 분기와 관계가 없어 그 세 필수 사례는 해당 없음이다. 대신 동일 위험군인 파일 읽기 실패, 잘못된 UTF-8, 빈 check-run 목록, pending/failure 혼합, 오형식 상태 레코드를 mutation으로 주입했다.

## 현재 판정

로컬 결함 수정은 GREEN이지만 Claude V1이 두 번 모두 NOT_RUN이고, 수정 커밋은 아직 원격 PR #43에 push되지 않아 정확한 새 SHA의 Actions도 NOT_RUN이다. 최종 상태는 `REQUEST_CHANGES`다. 이 tracked 문서는 checkpoint 전 장부이며, checkpoint 뒤 V2 산출물은 SHA를 바꾸지 않기 위해 ignored artifact로만 남긴다.
