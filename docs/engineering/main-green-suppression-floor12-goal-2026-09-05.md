# main 초록 복구 — 억제 원장 `keyword-env-value-floor-12` 종결 (goal, 2026-09-05)

등급 **L3** (SOT 문서 `docs/sot/coding-principles.md` 수정 포함 → SOT-30 §1 표 "SOT 수정 = L3"). 모드 `mixed`.
워크트리 `worktrees/main-green-suppression-floor12` · 브랜치 `task/main-green-suppression-floor12` · base `b724093`.

## 상위 목표 1문장

main 의 CI 가 2026-08-30 이후 빨간불(`b724093` push run 33313102834, 실패 스텝 1개 = "억제 만료 스캔")이라 모든 PR 의 초록 판정이 무의미해졌다. 만료된 억제 1건을 **정책 확정으로 종결**해 main 을 초록으로 되돌리고, 그 뒤 열린 PR 12건의 병합 판정을 다시 가능하게 한다. 성공 신호 = 이 PR HEAD SHA 의 pull_request 이벤트 24 스텝 전부 success.

## 현재 상태 (실측, 추측 없음)

- `suppressions.yaml:50-66` — `keyword-env-value-floor-12`, `expiry: 2026-08-26`. 오늘 2026-09-05 이므로 만료.
- `.github/workflows/verify.yml:139-159` — "억제 만료 스캔" 스텝. expiry < today 면 FAIL.
- `.secret-patterns.default` 마지막 규칙 — `(WEBHOOK|CREDENTIAL|PRIVATE_KEY)` 키워드 대입 값 하한 `{11,}` = 12자. 주석에 "12자 미만 실제 비밀은 (1)(2) 키워드·벤더 규칙이 담당" 이미 명시.
- `docs/sot/coding-principles.md:19` P4, `:37` P22 — 비밀 스캔 원칙. 하한 정책 서술 없음.
- `docs/engineering/secret-webhook-vendor-rev2-verdict-2026-08-12.md:79-85` "설계 결정 카드 2 — 12자 하한": 되돌리는 법으로 "책임자가 12자 정책을 승인해 … 기록" 을 제시. 오너 결정(2026-09-05 프롬프트) = ① 12자 하한 정책 확정.
- 재발 원장 `docs/sot/31-strict-recurrence-ledger.md` — 저장소에 **없음**(팬텀 참조, 메모리 "strict 전역 팬텀 8개"와 일치). 인용 불가를 여기 기록한다.

## 근본 원인

억제 원장은 "유예" 였고 유예는 결정을 미룬 것이다. 결정(①/②)이 2026-08-26 까지 내려지지 않아 만료가 그대로 CI 실패가 됐다. 이 PR 은 결정 ① 을 문서에 박아 유예를 **종결**한다(기한 연장 금지 — 프롬프트 [하지 말 것]).

## 인수 기준 (AC 1개)

**AC-1** (EARS): `suppressions.yaml` 에서 `keyword-env-value-floor-12` 행이 제거되고 `docs/sot/coding-principles.md` 에 12자 하한 정책이 근거와 함께 적혀 있을 때, verify.yml 의 억제 만료 스캔과 동일 로직을 로컬에서 실행하면 exit 0 이어야 한다.

- 검증 명령: `bash <scratch>/ci-expiry-scan.sh <worktree>` (본문은 verify.yml:144-159 와 `diff` 로 동일 확인, 들여쓰기만 제거) → `PASS: 억제 3건 전부 유효 기한 내`, exit 0.
- 보조: `bash verify.sh` PASS 1줄 · `bash scripts/acceptance-principles-check.sh` → `MECHANISMS: PASS 34/34` · `bash scripts/acceptance-principles-mutations.sh` exit 0.
- counter-AC: 원장에서 행을 지우기만 하고 정책 서술이 없으면 REV2-D3 지적("축소가 원장에 없음")이 그대로 재발 — 정책 줄 존재를 grep 으로 확인한다(`grep -c '값 하한 12자' docs/sot/coding-principles.md` = 1).

### RED 증거 (구현 전, base b724093)

```
$ bash ci-expiry-scan.sh worktrees/main-green-suppression-floor12
FAIL: 만료된 억제 (expiry 2026-08-26 < 오늘 2026-09-05) — 유예 기한이 지났다
exit=1
$ grep -c '값 하한 12자' docs/sot/coding-principles.md
0
```
올바른 이유로 실패한다(만료 판정). 다른 스텝은 base 에서 이미 PASS(`principles-check` 34/34, `verify.sh` PASS).

## 계약 (SDD)

- 입력: `suppressions.yaml`(YAML 리스트, 필드 check/reason/owner/expiry/issue) · `docs/sot/coding-principles.md`(§1 표 + 산문).
- 출력: 원장 3건(ci-transfer-guarantee · p13-deletion-blindspot · gate-scope-gaps, 원문 불변) · SOT 에 정책 문단 1개(표 밖, `> ` 인용 블록, 1~3줄).

### ① 입력 영역 표

| 입력 | 처리 |
|---|---|
| 원장에 floor-12 행 존재 (현재) | 행 삭제 |
| 원장에 다른 3건 | 불변 (diff 로 0줄 변경 확인) |
| SOT §1 표 P1~P26 행 | 불변 — `principles.yaml` 과의 문구 대조를 검사기가 하므로 표 안 수정 금지 |
| SOT 표 바로 아래(§1-B 앞) | 정책 인용 블록 삽입 |
| 파일 500줄 게이트 | 76→~80줄, 해당 없음 |
| 그 외 전부(verify.yml · hooks/ · .secret-patterns.default · 열린 PR · 다른 억제) | 명시적 거부 — 수정 0건 |

### ② 결정 목록 (오너 확정)

- 12자 하한 = 정책 (① 선택). 근거 문서 = `secret-webhook-vendor-rev2-verdict-2026-08-12.md`.
- 기록 위치 = P4·P22 "아래" → 표 안이 아니라 표 직후 인용 블록(표 안은 yaml 미러 검사기가 깨진다).
- 등급 L3 로 상향(SOT 수정).

### ③ 표↔테스트

| 행 | 검사 |
|---|---|
| 행 삭제 | ci-expiry-scan exit 0 + `grep -c 'keyword-env-value-floor-12' suppressions.yaml` = 0 |
| 다른 3건 불변 | `git diff -U0 suppressions.yaml` 이 삭제만(+줄 0) |
| SOT 표 불변 | `acceptance-principles-check.sh` 34/34 |
| 정책 존재 | `grep -c '값 하한 12자'` = 1 |
| 그 외 거부 | `git diff --name-only` 가 정확히 3파일(goal·suppressions·coding-principles) |

### R1 예외 케이스 표

| 상황 | 처리 |
|---|---|
| pre-commit 이 suppressions.yaml 변경을 P13 약화로 차단 | 중단·사유 보고(억제는 만료일 있는 원장에만 — 삭제는 약화가 아니라 종결이므로 통과 예상, 실측으로 확인) |
| pre-push 가 acceptance 전량 재실행에서 다른 스텝 FAIL | 이 PR 범위 밖 → NOT_RUN 기록, 손대지 않음 |
| CI 24 스텝 중 이 PR 과 무관한 스텝 FAIL | 위와 같음, "완료" 미선언 |
| gh 조회 불능 | UNVERIFIED 보고 |
| 그 외 전부 | 명시적 중단 + 표 갱신 |

## 게이트 계획

Gate0 session-status → RED 커밋(이 문서) → GREEN 커밋(원장·SOT) → 로컬 검증 4종 → V1(codex fresh read-only, 파일 판정) → V2(리셋 Claude) → push → PR → CI(pull_request, PR HEAD SHA) → READY TO MERGE(merge 는 사용자).

## 적대검증 정조준

- "원장 행 삭제 = 검사 약화 은폐" 인가? → 아니다: 검사(12자 하한)는 이미 2026-08-12 부터 그 상태이며 이 PR 은 검사 강도를 바꾸지 않고 **결정을 문서화**한다. V1 은 `.secret-patterns.default` diff 0 을 확인하라.
- 정책 문단이 P4·P22 문구를 바꿔 yaml 미러 검사를 깨는가? → 검사기 실행으로 확인.
- 근거 문서 경로가 실존하는가? → `ls` 로 확인(팬텀 참조 사고 재발 방지).

## 비범위

② 6~11자 탐지 복구 · 허용 목록 · 다른 억제 3건 · verify.yml · hooks/ · 열린 PR 11개.

## L3 추가

- 롤백: 이 PR 의 revert 1커밋. 영향 반경 = 문서 2파일, 코드 0.
- 배포 후 관측: main 의 다음 push run 에서 "억제 만료 스캔" 스텝 success 여부. 다음 만료는 2026-09-15(ci-transfer-guarantee · p13-deletion-blindspot) — 그 전에 결정 필요.

## 적대 검증 로그

(후기록)
