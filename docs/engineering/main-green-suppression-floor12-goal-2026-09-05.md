# main 초록 복구 — 억제 원장 `keyword-env-value-floor-12` 종결 (goal, 2026-09-05)

등급 **L3** (SOT 문서 `docs/sot/coding-principles.md` 수정 포함 → Strict `SKILL.md` §0.5의 "SOT 수정 = L3").
워크트리 `worktrees/main-green-suppression-floor12` · 브랜치 `task/main-green-suppression-floor12` · base `b724093`.

VERDICT: FAIL

## 결론

PR 머리 커밋 `03679010b8420d00d6f09e7a2840852ac1b8c69c`은 2026-09-06 08:29:12 KST의 clean 스냅샷에서 `23 success + 1 SKIPPED + 0 failure`로 AC-PR을 충족했다. `PR_GATE (merged head 0367901…): PASS`이며, main 전용 `인수 검사 0-5 (push · CI 연결)`은 원래 정본에 적힌 대로 `SKIPPED`다. 이 문서를 편집 중인 dirty 상태에는 그 PASS를 재사용하지 않는다.

이 재검증이 진행되던 2026-09-06 08:23:40 KST에 PR #56이 이 세션 밖에서 같은 GitHub 계정(`sangmokang`)으로 먼저 병합됐다. 이 세션은 병합 명령을 실행하지 않았으며, 병합 전 `READY_TO_MERGE`에서 멈추라는 절차는 세션 밖 상태 변경 때문에 더 이상 달성할 수 없다. 병합 커밋 `f96ece9564166d56815b3e5c3de5547b615bcb25`의 main push 검사는 24 success, 0 skipped, 0 failure이므로 현재 사실 판정은 `MAIN_CI: PASS`다.

새 goal-only 커밋은 이미 병합된 **같은 PR #56**에 새 `pull_request` 실행을 만들 수 없다. 새 PR이나 새 브랜치를 만들면 별도 검증은 가능하지만 이번 허용 범위는 PR #56 본문과 기존 브랜치뿐이다. 따라서 새 문서 커밋 자체의 PR #56 검증은 `PR_GATE (goal correction head): NOT_RUN — PR #56이 먼저 병합됨`이며, 이 필수 단계가 남아 전체 Strict 판정은 PASS가 아니다.

## 판단 근거

정본(SOT, 팀이 판정에 쓰는 기준 문서)은 검증 스텝을 24개로 고정한다. 동시에 `인수 검사 0-5`는 local main과 origin/main의 배송 상태를 읽으므로 main push에서만 의미가 있다고 워크플로 조건과 독립 검사기 예외 목록에 미리 적혀 있다. 따라서 pull_request 실행의 정확한 성공 계약은 24 success가 아니라 23 success와 사전 정의된 SKIPPED 1개다.

`acceptance-0-5.sh`는 일부 1~4번에서 PR 머리의 파일을 읽지만, 최종 PASS/FAIL을 좌우하는 5번 배송 검사는 local main과 origin/main을 입력으로 삼는다. PR 머리 `0367901…`를 체크아웃한 임시 사본에서 두 main 참조만 `f96ece9…`로 맞추자 PASS했고, local main을 없애자 같은 PR 머리에서 exit 1이 됐다. 따라서 0-5 전체의 최종 판정은 PR 머리 전용 검증 증거로 쓸 수 없고, 5번의 main 참조 상태에 지배된다.

병합 전 기준선과 병합 뒤 현재 사실을 섞지 않는다. 요청 시점 기준선은 main push run `33313102834`의 failure와 `MAIN_CI: NOT_YET_VERIFIED`였고, 작업 도중 생긴 후속 사실은 이 세션 밖 병합과 main push run `33998556226`의 success다.

## 상위 목표 1문장

main 의 CI 가 2026-08-30 이후 빨간불(`b724093` push run 33313102834, 실패 스텝 1개 = "억제 만료 스캔")이라 모든 PR 의 초록 판정이 무의미해졌다. 만료된 억제 1건을 **정책 확정으로 종결**해 main 을 초록으로 되돌리고, 그 뒤 열린 PR 11건의 병합 판정을 다시 가능하게 한다. PR 성공 신호는 아래 AC-PR, 병합 뒤 main 성공 신호는 AC-MAIN으로 서로 분리한다.

## 현재 상태 — 구현 전 RED 상태 (실측, 추측 없음)

- `suppressions.yaml:50-66` — `keyword-env-value-floor-12`, `expiry: 2026-08-26`. 오늘 2026-09-05 이므로 만료.
- `.github/workflows/verify.yml:139-159` — "억제 만료 스캔" 스텝. expiry < today 면 FAIL.
- `.secret-patterns.default` 마지막 규칙 — `(WEBHOOK|CREDENTIAL|PRIVATE_KEY)` 키워드 대입 값 하한 `{11,}` = 12자. 주석에 "12자 미만 실제 비밀은 (1)(2) 키워드·벤더 규칙이 담당" 이미 명시.
- `docs/sot/coding-principles.md:19` P4, `:37` P22 — 비밀 스캔 원칙. 하한 정책 서술 없음.
- `docs/engineering/secret-webhook-vendor-rev2-verdict-2026-08-12.md:79-85` "설계 결정 카드 2 — 12자 하한": 되돌리는 법으로 "책임자가 12자 정책을 승인해 … 기록" 을 제시. 오너 결정(2026-09-05 프롬프트) = ① 12자 하한 정책 확정.
- 재발 원장 `docs/sot/31-strict-recurrence-ledger.md` — 저장소에 **없음**(팬텀 참조, 메모리 "strict 전역 팬텀 8개"와 일치). 인용 불가를 여기 기록한다.

## 근본 원인

억제 원장은 "유예" 였고 유예는 결정을 미룬 것이다. 결정(①/②)이 2026-08-26 까지 내려지지 않아 만료가 그대로 CI 실패가 됐다. 이 PR 은 결정 ① 을 문서에 박아 유예를 **종결**한다(기한 연장 금지 — 프롬프트 [하지 말 것]).

## 인수 기준

**AC-1** (EARS): `suppressions.yaml` 에서 `keyword-env-value-floor-12` 행이 제거되고 `docs/sot/coding-principles.md` 에 12자 하한 정책이 근거와 함께 적혀 있을 때, verify.yml 의 억제 만료 스캔과 동일 로직을 로컬에서 실행하면 exit 0 이어야 한다.

- 검증 명령: `sed -n '144,159p' .github/workflows/verify.yml | sed 's/^          //' | bash` (verify.yml 본문을 들여쓰기만 제거해 그대로 실행) → `PASS: 억제 3건 전부 유효 기한 내`, exit 0.
- 보조: `bash verify.sh` PASS 1줄 · `bash scripts/acceptance-principles-check.sh` → `MECHANISMS: PASS 34/34` · `bash scripts/acceptance-principles-mutations.sh` exit 0.
- counter-AC: 원장에서 행을 지우기만 하고 정책 서술이 없으면 REV2-D3 지적("축소가 원장에 없음")이 그대로 재발 — 정책 줄 존재를 grep 으로 확인한다(`grep -c '값 하한 12자' docs/sot/coding-principles.md` = 1).

**AC-PR** (EARS): When PR HEAD에 `pull_request` workflow가 실행되면, 시스템은 다음을 모두 만족해야 한다.

1. workflow 전체 `conclusion = success`.
2. PR에 적용되는 검증 스텝 23개 전부 `success`.
3. main 전용 `인수 검사 0-5 (push · CI 연결)`은 사전 정의된 `SKIPPED` 정확히 1개.
4. `failure = 0`, `cancelled = 0`, `timed_out = 0`.
5. `local HEAD == remote PR HEAD == CI headSha`.
6. 작업트리 clean.
7. skipped 스텝 이름과 `if: github.ref == 'refs/heads/main'` 조건 원문을 증거로 첨부.

위 일곱 조건을 모두 만족하면 `PR_GATE: PASS`다. 개별 0-5 상태는 `SKIPPED`이며 `NOT_RUN`이나 `success`로 바꾸지 않는다.

**AC-MAIN** (EARS): When PR이 병합되고 main push workflow가 실행되면, 시스템은 같은 24개 검증 스텝이 `24 success`, `0 skipped`, `0 failure`, `0 cancelled`, `0 timed_out`이고 `remote main SHA == CI headSha`일 때만 `MAIN_CI: PASS`로 판정해야 한다.

병합 전에는 `MAIN_CI: NOT_YET_VERIFIED`와 `READY_TO_MERGE`까지만 보고한다. 이 세션은 병합을 승인하거나 실행하지 않는다.

### counter-AC — 가짜 합격 금지

- GitHub job 전체가 success라는 이유만으로 스텝 수를 세지 않는 것.
- skipped 1개를 success로 바꿔 적는 것.
- 0-5의 `if` 조건만 삭제해 PR에서 실행하는 것.
- push run 결과를 pull_request 결과라고 쓰는 것.
- 과거 SHA의 초록불을 현재 HEAD에 재사용하는 것.
- PR이 초록이라는 이유만으로 main이 복구됐다고 쓰는 것.
- goal 문서의 구현 전 상태를 현재 상태로 남기는 것.

이번 커밋에서 삭제하는 이전 단언은 정확히 하나다: `이 PR HEAD SHA 의 pull_request 이벤트 24 스텝 전부 success`. 워크플로가 main 전용 0-5를 사전 정의해 이 문장은 실행 구조와 모순되므로, 오너가 확정한 AC-PR/AC-MAIN으로 교체한다.

### RED 증거 (구현 전, base b724093)

```
$ sed -n '144,159p' .github/workflows/verify.yml | sed 's/^          //' | bash
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
| SOT §1 표 P1~P24 행 | 불변 — `principles.yaml` 과의 문구 대조를 검사기가 하므로 표 안 수정 금지 |
| SOT 표 바로 아래(§1-B 앞) | 정책 인용 블록 삽입 |
| 직접 작성 코드 파일 | 0개. P11의 파일 hard 600 LOC 경계는 문서·원장 변경이므로 `NOT_APPLICABLE` |
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

Gate0 session-status → RED 커밋(이 문서) → GREEN 커밋(원장·SOT) → 로컬 검증 → V1(격리 Claude) → V2(새 맥락 Codex) → push → PR의 `pull_request` run에서 AC-PR → `READY_TO_MERGE` → 별도 병합 승인 뒤 main push run에서 AC-MAIN. 단, 2026-09-06 08:23:40 KST에 외부 병합이 먼저 발생해 이번 재개 실행은 새 goal 커밋의 `pull_request` run을 만들 수 없다.

## 적대검증 정조준

- "원장 행 삭제 = 검사 약화 은폐" 인가? → 아니다: 검사(12자 하한)는 이미 2026-08-12 부터 그 상태이며 이 PR 은 검사 강도를 바꾸지 않고 **결정을 문서화**한다. V1 은 `.secret-patterns.default` diff 0 을 확인하라.
- 정책 문단이 P4·P22 문구를 바꿔 yaml 미러 검사를 깨는가? → 검사기 실행으로 확인.
- 근거 문서 경로가 실존하는가? → `ls` 로 확인(팬텀 참조 사고 재발 방지).

## 비범위

② 6~11자 탐지 복구 · 허용 목록 · 다른 억제 3건 · verify.yml · hooks/ · 열린 PR 11개.

## L3 추가

- 배송 상태: `NOT_APPLICABLE` — 제품 표면·DB·운영 쓰기 없이 문서와 내부 CI 억제 원장만 바꾼다.
- 데이터 안전 AC: 변경 파일에 비밀·후보자 데이터가 추가되지 않고 `bash verify.sh`가 exit 0이어야 한다.
- 롤백: 이 PR 의 GREEN 커밋을 revert한다. 영향 반경 = goal 포함 문서 2파일 + 억제 원장 1파일, 제품 코드 0.
- 배포 후 관측: main push run `33998556226`에서 "억제 만료 스캔" 포함 검증 24개가 모두 success였다. 다음 만료는 2026-09-15(ci-transfer-guarantee · p13-deletion-blindspot) — 그 전에 결정 필요.

## 검증 장부

- 세션: `01a06cf9-06e0-7c70-9286-1e548abfb8d5`; RED HEAD: `7144387361c7e9de051f427bc76e976bf0a398dc`.
- `sed -n '1,9999p' docs/sot/coding-principles.md` — 2026-09-05 00:20:35 KST, exit 0, 전체 74줄 직접 로드, Git blob `b8122deae7192b714d9a35c5e2c6f96cadffde42`.
- `sed -n '1,9999p' docs/sot/principles.yaml` — 2026-09-05 00:20:42 KST, exit 0, 전체 345줄 직접 로드, Git blob `5e416a64bcb795c8668392f3d34f5c5dc402be84`.

```text
$ bash scripts/acceptance-principles-check.sh
VERDICT: PASS
SOT_LOAD: PASS docs/sot/coding-principles.md
LEDGER_LOAD: PASS docs/sot/principles.yaml
MECHANISMS: PASS 34/34 strict-contract-bindings
WIRING: PASS pre-push=1 ci=1
CHECKED: 34
exit=0
```

→ 무엇을 시켰나: RED HEAD에서 원칙 정본·기계 장부·로컬/CI 연결을 직접 읽고 검사했다. 무엇이 나왔나: 34개 전부와 두 연결 지점이 통과했다. 좋은 소식인가: 구현 전 계약 기준점이 유효하다.

```text
$ bash scripts/session-status.sh
HEAD: 7144387 (ahead 1 / behind 0)
ORIGIN: b724093
RED: 0/28 (acceptance-0-7.sh 제외 — CI 담당)
exit=0
```

→ 무엇을 시켰나: Gate 0에서 현재 이력·원격 차이·미해결 로컬 검사를 전수 확인했다. 무엇이 나왔나: RED 커밋 1개가 원격보다 앞서 있고, 28개 중 실패는 0개다. 좋은 소식인가: 만료 실패가 CI 인라인 단계에만 있다는 원인과 일치한다.

## 적대 검증 로그

### V1 — Claude 격리 적대검증

- 실행: `env -u ANTHROPIC_API_KEY claude -p < /tmp/valuehire-floor12-v1-prompt.txt`
- 시각: 2026-09-05 00:34~00:49 KST; 종료값 0.
- 실행 신원: Claude Code `2.1.260`; 세션 `6e600a49-bdaf-461f-be05-df56252d388f`.
- 원문 판정: `VERDICT: PASS`; 낮은 설계 관찰 1건(정책 산문 자체가 CI에서 직접 강제되지 않음).

````text
VERDICT: PASS

## 결론

이번 변경은 계약(T)이 요구한 대로 딱 3개 파일만 건드렸고, 만료된 억제 항목 하나(keyword-env-value-floor-12, 유효기간 2026-08-26)를 억제 원장에서 지우는 대신 그 판단을 정책 문서(SOT)에 영구 조항으로 옮겨 적었습니다. 다른 억제 3건은 바이트 단위로 그대로이고, 워크플로/훅/비밀 패턴 파일 등 손대면 안 되는 경로는 전부 base와 동일했습니다. 요구된 로컬 검증 4종(만료 스캔·verify.sh·원칙 검사·변이 검사)을 제가 직접 재실행해 보고된 숫자와 동일한 결과를 얻었고, RED가 "만료 때문"이라는 주장도 실제로 되돌려서 재현에 성공했습니다. 다만 한 가지는 결함이라기보다 설계상 남겨둔 구멍으로 보고드립니다 — 새로 적은 정책 문구 자체를 강제로 지키게 하는 기계 장치가 없습니다.

## 판단 근거 — 무엇을 선택했고, 무엇을 버렸고, 무엇이 틀리면 깨지는가

- **선택한 해석**: 계약 3번 "P4·P22 아래"를 "P4 행 바로 밑" 같은 문자 그대로의 인접이 아니라 "표 전체(그 안에 P4·P22가 모두 들어 있음) 아래, §1-B 앞"으로 해석했습니다. P4(19행)와 P22(37행)는 표 안에서 떨어져 있어 한 문구를 두 곳에 동시에 붙이는 것은 불가능하므로, 표 뒤에 한 번 두는 것이 유일하게 말이 되는 해석입니다. 실제 위치도 그렇게 되어 있어(41행, P24 바로 다음) 이 해석과 일치했습니다. 이 해석이 틀렸다면(즉 P4 행 바로 아래에 별도로 하나, P22 행 바로 아래에 또 하나 있어야 한다는 뜻이었다면) 이 항목은 위반이 됩니다.
- **버린 해석**: "정책 문구가 있다"는 grep 하나로 검증된다는 계약의 counter-AC 표현을 문자 그대로만 확인했고, 그 grep이 CI나 pre-push 같은 실제 게이트에 연결되어 있는지까지는 계약이 요구하지 않았습니다. 그래서 이 부분은 결함(FAIL 사유)이 아니라 별도 관찰로만 보고합니다. 계약이 "정책 문구 존재 = grep exit 0"만 요구했다면 이 선택은 맞고, "정책 문구가 어떤 자동 게이트로도 보호되어야 한다"까지 요구했다면 이 항목은 미달입니다.
- **틀리면 깨지는 것**: RED 재현과 grep 실패 재현은 감사 대상 워크트리가 아니라 `/tmp` 임시 사본에서 수행했습니다. 만약 그 복제 과정에서 파일이 누락되거나 다르게 복사됐다면 재현 결과가 무의미해집니다 — 그래서 복제 직후 `git status`로 원본과 동일한 변경 파일 3개가 그대로 있는지 먼저 확인한 뒤에 조작했습니다.

## 기술 상세와 증거

### T1 — keyword-env-value-floor-12 만 삭제됐는가

`suppressions.yaml` diff (git diff HEAD)는 46~66행 블록(정확히 `keyword-env-value-floor-12` 항목 18줄)만 삭제로 나왔고, 다른 줄의 추가/변경은 0건이었습니다.
→ 해석: 삭제 외 어떤 변형도 없음. T1 충족.

### T2 — 나머지 억제 3건 바이트 동일, expiry 연장 없음

`git show origin/main:suppressions.yaml` 과 현재 파일을 `diff` 한 결과, 차이는 오직 `keyword-env-value-floor-12` 블록이 base에는 있고 현재는 없다는 것 하나였습니다(diff 출력 49~66행만 `<` 로 표시, 다른 줄 전무).
→ 해석: `ci-transfer-guarantee`(expiry 2026-09-15) · `p13-deletion-blindspot`(2026-09-15) · `gate-scope-gaps`(2026-09-30) 세 항목은 문자 하나까지 base와 같음. 연장 없음 확인.

### T3 — 정책 문구 위치·내용·근거

`docs/sot/coding-principles.md:41-42`(정책 문구 삽입 위치, P24 바로 다음, §1-B 앞) — 이 두 줄의 역할은 원장 삭제와 SOT 정책 확정을 연결하는 근거 인용입니다.
```
> **비밀 스캔 값 하한 12자 확정.** 6~11자 비밀은 키워드·벤더 규칙 담당.
> 근거: `docs/engineering/secret-webhook-vendor-rev2-verdict-2026-08-12.md` §설계 결정 카드 2.
```
2줄(1~3줄 범위 충족). 근거 파일 실존 확인(`ls` 성공, 43k), 해당 절 `설계 결정 카드 2 — 12자 하한` 이 정확히 79행에서 시작(85행까지 "되돌리는 법"으로 끝남 — 계약이 지목한 79~85행과 일치). 그 절의 내용은 "6자→12자 상향, 6~11자 실비밀도 통과하는 대가, 책임자가 12자 정책을 승인해 원장에 기록하거나 6자로 되돌리라"는 것으로, 지금 조치(①안 = 정책 승인 후 원장 종결)와 의미가 일치합니다. P4·P22 행(19행, 37행) 자체는 문구 변경 없이 원문 그대로였습니다.
→ 해석: 근거 경로·구간·의미 셋 다 일치. T3 충족.

### T4 — 금지 경로 불변, 열린 PR 쓰기 없음

```
git diff origin/main -- .github/workflows/verify.yml   → 무출력
git diff origin/main -- .secret-patterns.default        → 무출력
git diff origin/main -- hooks/                          → 무출력
gh pr list --state open --limit 50                       → 11건 (쓰기 아님, 조회만)
```
→ 해석: 세 경로 모두 base와 완전 동일. 열린 PR도 조회만 했고 코멘트·라벨·상태 변경 등 쓰기 동작은 어떤 도구도 호출하지 않음. goal 문서의 "12건→11건" 정정도 실측과 일치.

### T5 — verify.yml 144~159행 로컬 실행

```
$ sed -n '144,159p' .github/workflows/verify.yml | sed 's/^          //' | bash
PASS: 억제 3건 전부 유효 기한 내
EXIT=0
```
`cat -n` 으로 143행이 `run: |`, 144행이 스크립트 첫 줄, 159행이 `exit $fail` 임을 직접 확인해 계약이 가리키는 구간이 정확히 이 스캔 로직 전체임을 검증했습니다.
→ 해석: 보고된 출력·종료값과 완전 일치.

### T6 — bash verify.sh

```
$ bash verify.sh
PASS: no secret-pattern match in any tracked file, .env not tracked
EXIT=0
```
→ 해석: 정확히 한 줄, exit 0. 보고와 일치.

### T7 — bash scripts/acceptance-principles-check.sh

```
VERDICT: PASS
MECHANISMS: PASS 34/34 strict-contract-bindings
WIRING: PASS pre-push=1 ci=1
CHECKED: 34
EXIT=0
```
→ 해석: 34/34, pre-push=1 ci=1, exit 0 — 보고와 일치.

### T8 — RED는 만료 때문, GREEN은 고장 사본에서 재실패

`/tmp/audit_floor12`(감사 대상 워크트리 밖의 별도 복제본)에서 `git checkout 7144387 -- suppressions.yaml docs/sot/coding-principles.md` 로 RED 시점 파일로 되돌린 뒤 동일 스캔을 실행:
```
FAIL: 만료된 억제 (expiry 2026-08-26 < 오늘 2026-09-05) — 유예 기한이 지났다
EXIT=1
```
같은 임시 사본을 새로 복제해 정책 문구 줄을 `sed -i '/값 하한 12자/d'` 로 지운 뒤:
```
$ grep -c '값 하한 12자' docs/sot/coding-principles.md
0
grep_exit=1
```
→ 해석: 두 반증 모두 계약·goal 문서가 주장한 그대로 재현됨. 조작 위치는 감사 대상 워크트리가 아니라 `/tmp` 사본이었고, 작업 종료 후 `rm -rf` 로 정리했습니다. 감사 대상 워크트리는 시작부터 끝까지 `git status` 상 변경 파일 3개(수정), 새 파일 0개로 동일했습니다.

**추가로 시도한 반증(계약에는 없지만 "죽은 문구/기계 장치 미연결"을 공격하려고 수행)**: 같은 정책 문구 제거 사본에서 CI 만료 스캔·`verify.sh`·`acceptance-principles-check.sh` 세 가지를 다시 돌려봤습니다.
```
sed -n '144,159p' verify.yml ... → PASS: 억제 3건 전부 유효 기한 내 (EXIT=0)
bash verify.sh                    → PASS ... (EXIT=0)
bash scripts/acceptance-principles-check.sh → VERDICT: PASS, 34/34 (EXIT=0)
```
그리고 `grep -rn "값 하한 12자" scripts/ hooks/ verify.sh` 결과 0건 — 이 문구를 검사하는 스크립트가 저장소 안에 하나도 없습니다.
→ 이 반증은 실패하지 않았습니다 — 즉 정책 문구를 지워도 CI·verify.sh·원칙 검사 세 게이트 전부 초록으로 남는다는 것을 실제로 확인했습니다. 이는 계약 위반은 아니지만(계약은 grep 하나만 요구했음), 아래 finding으로 보고합니다.

### T7 보조 — acceptance-principles-mutations.sh

감사 대상 워크트리에서 직접 실행 전후 `git status --short` 를 비교해 SOURCE-TREE 불변을 스스로도 확인했습니다(실행 전/후 동일하게 3개 파일 수정 상태만 유지, 새 파일 없음).
```
BOUNDARY-500 PASS / BOUNDARY-501 FAIL / SOURCE-TREE 원본 저장소 상태 불변
CHECKED: 41 / VERDICT: PASS / EXIT=0
```
→ 해석: 이 검사기 자체가 대상 트리를 오염시키지 않는다는 자기증명이 실측으로도 확인됨(피드백 메모리 "검증기가 오염원이 되는 함정"과 정확히 대칭되는 확인).

### T9 — L3 롤백·영향 반경·데이터 안전

goal 문서 diff에서 확인:
```
+ 배송 상태: NOT_APPLICABLE — 제품 표면·DB·운영 쓰기 없이 문서와 내부 CI 억제 원장만 바꾼다.
+ 데이터 안전 AC: 변경 파일에 비밀·후보자 데이터가 추가되지 않고 verify.sh가 exit 0이어야 한다.
+ 롤백: 이 PR의 GREEN 커밋을 revert. 영향 반경 = 문서 2파일 + 억제 원장 1파일, 제품 코드 0.
```
→ 해석: 세 항목(롤백·영향 반경·데이터 안전) 모두 명시되어 있고, "직접 작성 코드 파일 0개"라는 표 안 주장과도 일관됨(실제로 변경 3개 파일은 md 2개 + yaml 1개, 코드 0).

### 증거 장부의 진위 — 블롭 해시 대조

goal 문서 "검증 장부"가 주장한 blob 해시를 직접 재계산해 대조:
```
$ git rev-parse 7144387:docs/sot/coding-principles.md → b8122deae7192b714d9a35c5e2c6f96cadffde42
$ git rev-parse 7144387:docs/sot/principles.yaml       → 5e416a64bcb795c8668392f3d34f5c5dc402be84
$ wc -l docs/sot/principles.yaml                        → 345
```
→ 해석: 문서에 적힌 두 해시·줄 수 모두 실측과 완전 일치. 사후에 지어낸 숫자가 아니라 실제 RED 커밋 시점 값입니다.

## Finding (결함이 아닌 설계 관찰 — severity: low)

**원문 제목**: SOT 정책 문구("값 하한 12자 확정")를 지켜주는 기계 장치가 없음
**원인**: `docs/sot/coding-principles.md:41-42` 의 신설 정책 인용문은 어떤 acceptance 스크립트·hook·CI 스텝에서도 참조되지 않습니다(`grep -rn "값 하한 12자" scripts/ hooks/ verify.sh` → 0건). goal 문서의 counter-AC는 사람이 수동으로 `grep -c` 를 돌려야만 검증됩니다.
**사업 영향**: 지금 당장의 피해는 없습니다. 다만 나중에 누군가 이 두 줄을 지우거나 표현을 바꿔도 `verify.sh`, CI 만료 스캔, `acceptance-principles-check.sh` 세 게이트 전부 계속 초록으로 남는다는 것을 실측으로 확인했습니다. 즉 이 PR이 "정책으로 확정"했다고 주장하는 것이 원장(기계 강제)에서 문서(사람 신뢰) 수준으로 강제력이 한 단계 낮아졌습니다.

**설계 지적 5줄**
- 무엇을: 억제 원장 항목(기계가 만료를 체크하던 것)을 SOT 문서의 산문 정책으로 옮겼습니다.
- 왜: 원장의 issue 필드가 제시한 ①안(12자 하한 승인·정책 확정·원장 종결)을 그대로 실행한 것입니다.
- 버린 대안: `principles.yaml`에 P번호를 부여해 `acceptance-principles-check.sh`의 34개 메커니즘 대조 대상에 포함시키는 방법(원장 검사 수준의 강제력 유지)은 채택하지 않았습니다.
- 대가: 정책 문구 삭제·왜곡이 CI에서 잡히지 않습니다 — 원장 시절엔 만료일이라도 있어 최소 90일 뒤엔 사람이 재검토했지만, 지금은 그런 재검토 트리거 자체가 없습니다.
- 되돌리기: 이후 작업에서 `principles.yaml`에 P25 항목을 추가하고 `acceptance-principles-check.sh`의 34개 검사 대상에 포함시키면 문서만이 아니라 기계로도 강제됩니다.

## 건너뜀·미확인 사항

- CI(GitHub Actions) 상의 실제 `pull_request` 이벤트 실행 결과는 아직 push되지 않은 상태라 조회 대상이 없어 확인하지 못했습니다(계약 5~7번은 로컬 재현만 요구했고, 그 부분은 전부 확인했습니다).
- `docs/engineering/secret-webhook-vendor-rev2-verdict-2026-08-12.md` 전체 43k 바이트 중 앞뒤 맥락(카드 1, 3)은 참고로만 훑었고 전문 검증은 79~85행 구간에 한정했습니다(계약이 그 구간만 지목했으므로).
- 열린 PR 11건 각각의 diff·상태는 개별적으로 점검하지 않았습니다 — 계약이 요구한 것은 "쓰기 없음" 확인이었고, 조회 자체도 안전하게 read-only(`gh pr list`)로 그쳤습니다.
````

→ 무엇을 시켰나: 실제 Claude CLI가 T 계약을 기준으로 변경 범위·로컬 명령·고장 사본을 독립 재실행했다. 무엇이 나왔나: 계약은 PASS, 정책 문구 자체의 자동 강제 부재는 낮은 설계 관찰 1건이다. 좋은 소식인가: 현재 요청 범위는 충족했지만 V2가 이 관찰이 결함인지 과장인지 다시 공격해야 한다.

### V2 — 새 맥락 Codex 적대검증

첫 시도에서 V2는 `bash scripts/session-status.sh`가 6분 이상 종료되지 않자 중단했고 exit 130을 받아, V1의 Gate 0 재현을 끝내지 못한 `VERDICT: FAIL`(유일 blocker)을 냈다. 동일 검증자에게 원명령을 중단 없이 재실행시켰고, 약 8분 후 다음을 얻었다.

```text
$ bash scripts/session-status.sh; rc=$?; echo "EXIT=$rc"
HEAD: 7144387 (ahead 1 / behind 0)
ORIGIN: b724093
RED: 0/28 (acceptance-0-7.sh 제외 — CI 담당)
EXIT=0
```

시작·종료 `git status --short --branch`는 둘 다 아래와 같아 읽기 전용 검증 전후 워크트리 불변이다.

```text
## task/main-green-suppression-floor12
 M docs/engineering/main-green-suppression-floor12-goal-2026-09-05.md
 M docs/sot/coding-principles.md
 M suppressions.yaml
```

V2 최종 원문 요약:

```text
VERDICT: PASS

첫 시도: 동일 명령을 6분 이상 후 Ctrl-C로 중단, exit 130.
재실행: 약 8분 후 정상 종료, RED: 0/28, exit 0.
첫 FAIL의 verification-blocker는 해소됐다.
G/V1/V2/T 최종 일치 여부: 일치한다.
남은 결함: 현재 V2 범위에서 merge-blocking 결함은 없다.
```

→ 무엇을 시켰나: V2가 V1의 모든 핵심 계약과 첫 시도의 유일 blocker였던 Gate 0을 독립 재실행했다. 무엇이 나왔나: 로컬 계약은 모두 PASS했고, 워크트리는 불변이다. 좋은 소식인가: 그렇다. 단, PR `pull_request` 24스텝은 push 전이라 V2 범위 밖이다.

V1의 low 관찰은 정책 문구를 정확히 grep하는 CI가 없다는 점에서 사실이다. 그러나 `.secret-patterns.default`의 현재 규칙과 `acceptance-secret-webhook-vendor.sh` 32건이 **정책의 행동**을 강제하고, 새 P25·`principles.yaml` 수정은 사장님이 승인한 1–3줄 SOT 기록·최소 변경 범위 밖이므로 버린다. 또한 기존 억제는 2026-08-12에서 2026-08-26까지 14일이므로, V1의 "90일 후 재검토" 설명은 근거 없는 과장으로 반박한다.

## 2026-09-06 새 오너 결정 재검증 장부

- 위험등급: L3. 기존 SOT·보안 정책 변경의 합격 계약 교정이다.
- 세션: `01a07188-a8a2-7422-94a6-a4da70cc8d22`.
- 시작 HEAD: `03679010b8420d00d6f09e7a2840852ac1b8c69c`.
- 시작 브랜치: `task/main-green-suppression-floor12`.
- 시작 워크트리: clean.
- 읽은 규칙: 사용자 제공 `AGENTS.md`, `/Users/kangsangmo/.codex/skills/strict/SKILL.md`, `docs/sot/coding-principles.md`, `docs/sot/principles.yaml`, `docs/sot/verification-commands.md`, `.github/workflows/verify.yml`, `scripts/acceptance-0-5.sh`, `scripts/verify/check-ci-step-integrity.sh`.
- 저장소의 `AGENTS.md`와 `CLAUDE.md`: `find .. -name AGENTS.md -o -name CLAUDE.md` 결과 없음. 이 실행의 최상위 계약은 사용자 프롬프트에 포함된 `AGENTS.md` 원문이다.
- 배포 상태: `NOT_APPLICABLE` — goal 문서와 PR 감사 기록만 다루며 제품 표면·DB·운영 데이터는 바꾸지 않는다.

### 작업 중 외부 상태 변경

```text
UTC 2026-09-05T23:30:13Z
KST 2026-09-06T08:30:13+0900
LOCAL_HEAD 03679010b8420d00d6f09e7a2840852ac1b8c69c
LOCAL_MAIN b7240936827032d5ee6791fa8cdb7d62ef6584b4
REMOTE_MAIN f96ece9564166d56815b3e5c3de5547b615bcb25
LS_REMOTE_MAIN f96ece9564166d56815b3e5c3de5547b615bcb25 refs/heads/main
LATEST_PUSH_RUNS
[{"conclusion":"success","createdAt":"2026-09-05T23:23:42Z","databaseId":33998556226,"event":"push","headBranch":"main","headSha":"f96ece9564166d56815b3e5c3de5547b615bcb25","status":"completed","updatedAt":"2026-09-05T23:26:26Z","url":"https://github.com/sangmokang/Valuehire_v6/actions/runs/33998556226"},{"conclusion":"failure","createdAt":"2026-08-30T13:02:48Z","databaseId":33313102834,"event":"push","headBranch":"main","headSha":"b7240936827032d5ee6791fa8cdb7d62ef6584b4","status":"completed","updatedAt":"2026-08-30T13:04:54Z","url":"https://github.com/sangmokang/Valuehire_v6/actions/runs/33313102834"}]
REMOTE_MAIN_LOG
f96ece9 (origin/main) main CI 복구: 12자 비밀 스캔 하한 정책을 확정하고 만료 억제를 종결한다 (#56)
b724093 (main) 로컬에만 있던 계약·기록 문서를 저장소로 배송한다 (④-a/5) (#46)
STATUS
```

→ 무엇을 시켰나: 첫 반례 실행에서 fetch가 origin/main을 바꾼 뒤 원격 main과 최신 push run을 다시 읽었다. 무엇이 나왔나: PR #56이 이 세션 진행 중 외부 병합됐고 새 main run이 이미 success였다. 좋은/나쁜 소식인가: 제품 main은 복구됐지만 “병합하지 않고 READY_TO_MERGE에서 중단”하는 요청 절차는 외부 상태 변경으로 깨졌다.

```text
UTC 2026-09-05T23:30:48Z
KST 2026-09-06T08:30:48+0900
PR56_CURRENT
{"baseRefName":"main","headRefName":"task/main-green-suppression-floor12","headRefOid":"03679010b8420d00d6f09e7a2840852ac1b8c69c","mergeCommit":{"oid":"f96ece9564166d56815b3e5c3de5547b615bcb25"},"mergeStateStatus":"UNKNOWN","mergedAt":"2026-09-05T23:23:40Z","mergedBy":{"id":"MDQ6VXNlcjEwNDE0NzY3","is_bot":false,"login":"sangmokang","name":""},"number":56,"state":"MERGED","title":"main CI 복구: 12자 비밀 스캔 하한 정책을 확정하고 만료 억제를 종결한다","url":"https://github.com/sangmokang/Valuehire_v6/pull/56"}
BRANCH_REMOTE
f96ece9564166d56815b3e5c3de5547b615bcb25 refs/heads/main
03679010b8420d00d6f09e7a2840852ac1b8c69c refs/heads/task/main-green-suppression-floor12
STATUS
```

→ 무엇을 시켰나: PR의 병합 시각·주체·커밋과 두 원격 브랜치를 다시 읽었다. 무엇이 나왔나: `sangmokang` 계정이 08:23:40 KST에 merge commit `f96ece9…`를 만들었고 작업 브랜치는 여전히 `0367901…`다. 좋은/나쁜 소식인가: 이 세션이 병합한 것이 아님을 분리할 수 있지만, 새 goal 커밋은 이미 병합된 PR의 검증 대상이 될 수 없다.

### 필수 원명령 실행

```text
COMMAND: bash scripts/acceptance-principles-check.sh
START_UTC: 2026-09-05T23:25:03Z
START_KST: 2026-09-06T08:25:03+0900
HEAD: 03679010b8420d00d6f09e7a2840852ac1b8c69c
SESSION: 01a07188-a8a2-7422-94a6-a4da70cc8d22
VERDICT: PASS
SOT_LOAD: PASS docs/sot/coding-principles.md
LEDGER_LOAD: PASS docs/sot/principles.yaml
MECHANISMS: PASS 34/34 strict-contract-bindings
WIRING: PASS pre-push=1 ci=1
CHECKED: 34
EXIT: 0
```

→ 무엇을 시켰나: 원칙 정본·기계 장부·pre-push와 CI 연결을 원명령으로 검사했다. 무엇이 나왔나: 34/34와 연결 2곳이 전부 PASS했다. 좋은 소식인가: 원칙 직접 로드 계약은 충족했다.

```text
COMMAND: sed -n '144,159p' .github/workflows/verify.yml | sed 's/^          //' | bash
START_UTC: 2026-09-05T23:25:52Z
START_KST: 2026-09-06T08:25:52+0900
HEAD: 03679010b8420d00d6f09e7a2840852ac1b8c69c
SESSION: 01a07188-a8a2-7422-94a6-a4da70cc8d22
PASS: 억제 3건 전부 유효 기한 내
EXIT: 0
```

→ 무엇을 시켰나: CI의 억제 만료 본문을 들여쓰기만 제거해 그대로 실행했다. 무엇이 나왔나: 남은 억제 3건은 모두 유효했고 종료값 0이었다. 좋은 소식인가: 기존 구현의 GREEN은 유지된다.

```text
COMMAND: bash verify.sh
START_UTC: 2026-09-05T23:26:24Z
START_KST: 2026-09-06T08:26:24+0900
HEAD: 03679010b8420d00d6f09e7a2840852ac1b8c69c
SESSION: 01a07188-a8a2-7422-94a6-a4da70cc8d22
PASS: no secret-pattern match in any tracked file, .env not tracked
EXIT: 0
```

→ 무엇을 시켰나: 모든 추적 파일과 `.env` 추적 여부를 비밀 패턴으로 검사했다. 무엇이 나왔나: 매치 0건과 `.env` 비추적, 종료값 0이다. 좋은 소식인가: goal 수정 전 데이터 안전 기준선이 합격했다.

```text
COMMAND: bash scripts/acceptance-ci-step-integrity.sh
START_UTC: 2026-09-05T23:28:12Z
START_KST: 2026-09-06T08:28:12+0900
HEAD: 03679010b8420d00d6f09e7a2840852ac1b8c69c
SESSION: 01a07188-a8a2-7422-94a6-a4da70cc8d22
PASS: 실제 워크플로 → 통과 — exit=0
PASS: 스텝에 if: ${{ false }} 주입 → 불합격 — exit=1
PASS: 스텝에 항상-거짓 조건 주입 → 불합격 — exit=1
PASS: 스텝에 항상-참 조건(always) 주입 → 불합격 — exit=1
PASS: 스텝에 continue-on-error 주입 → 불합격 — exit=1
PASS: job 에 if 주입 → 불합격 — exit=1
PASS: 실행 대신 echo → 불합격 — exit=1
PASS: 실행 대신 bash -n → 불합격 — exit=1
PASS: job 의 스텝 전량 삭제 → 불합격 — exit=1
PASS: 워크플로 파일 없음 → NOT_RUN — exit=2
PASS: 파싱 불가 워크플로 → NOT_RUN — exit=2
PASS: job 0개 → NOT_RUN — exit=2
PASS: 이유가 적힌 예외는 통과 — 0-5 의 main 전용 조건
PASS: 원본 저장소 상태 불변 — before/after 동일
CHECKED: 14
VERDICT: PASS
EXIT: 0
```

→ 무엇을 시켰나: 임시 워크플로에 조건·오류무시·출력 전용·빈 스텝을 주입해 검사기가 차단하는지 확인했다. 무엇이 나왔나: 고장 12종이 기대 종료값으로 차단됐고, 0-5의 이유 있는 main 전용 조건만 통과했다. 좋은 소식인가: SKIPPED 예외는 사후 면책이 아니라 검사기에 사전 정의돼 있다.

```text
COMMAND: bash scripts/acceptance-semantic-mutations.sh
START_UTC: 2026-09-05T23:28:36Z
START_KST: 2026-09-06T08:28:36+0900
HEAD: 03679010b8420d00d6f09e7a2840852ac1b8c69c
SESSION: 01a07188-a8a2-7422-94a6-a4da70cc8d22
PASS: 대상 수집 — 인수 검사 28개 (하한 5)
PASS: 무력화 차단: exit-zero — 28/28 전부 불합격 처리
PASS: 무력화 차단: true-only — 28/28 전부 불합격 처리
PASS: 무력화 차단: noop — 28/28 전부 불합격 처리
PASS: 무력화 차단: empty — 28/28 전부 불합격 처리
PASS: 무력화 차단: echo-only — 28/28 전부 불합격 처리
PASS: 정상 인수 검사 통과 — acceptance-guard-global-skill-files.sh exit=0 (과잉 차단 없음)
PASS: 래퍼 인자 없음 거부 — exit=2
PASS: 래퍼 대상 없음 거부 — exit=2
PASS: 원본 저장소 상태 불변 — before/after 동일
CHECKED: 10
VERDICT: PASS
EXIT: 0
```

→ 무엇을 시켰나: 28개 인수 검사 각각을 `exit 0`, `true`, 무동작, 빈 파일, 출력 전용으로 바꾼 임시 사본을 실행했다. 무엇이 나왔나: 5종×28개가 모두 불합격 처리됐고 정상 검사 한 건은 통과했다. 좋은 소식인가: 가짜 GREEN과 검사 대상 0개가 차단된다.

```text
COMMAND: bash scripts/acceptance-secret-webhook-vendor.sh
START_UTC: 2026-09-05T23:28:55Z
START_KST: 2026-09-06T08:28:56+0900
HEAD: 03679010b8420d00d6f09e7a2840852ac1b8c69c
SESSION: 01a07188-a8a2-7422-94a6-a4da70cc8d22
PASS: 탐지됨 — discord 웹훅 URL
PASS: 탐지됨 — discordapp.com 변종(구 도메인)
PASS: 탐지됨 — Slack 웹훅 URL
PASS: 탐지됨 — Anthropic 벤더 키(하이픈 접두 · 중립 변수명)
PASS: 탐지됨 — WEBHOOK 계열 .env 대입(불투명 토큰)
PASS: 탐지됨 — CREDENTIAL 계열 .env 대입
PASS: 탐지됨 — PRIVATE_KEY 한 줄 형태
PASS: 탐지됨 — BOT_TOKEN (기존 TOKEN 규칙 회귀 앵커 · 신규 규칙에는 없음)
PASS: 탐지됨 — discord 버전 경로 /api/v10/ (공식 권장 형식)
PASS: 탐지됨 — discord 하위 도메인(canary)
PASS: 탐지됨 — Slack 공공기관용 GovSlack 도메인
PASS: 탐지됨 — Slack services 없는 형태(OAuth 응답 예시)
PASS: 탐지됨 — 벤더 키 39자 본문(길이 경계)
PASS: 탐지됨 — 인라인 주석이 붙은 .env 값
PASS: 오탐 없음 — 일반 discord 채널 URL(비밀 아님)
PASS: 오탐 없음 — 코드 대입(값이 아니라 호출)
PASS: 오탐 없음 — 환경변수 참조(값이 없다)
PASS: 오탐 없음 — 산문 속 키 형식 언급
PASS: 오탐 없음 — 일반 Slack 워크스페이스 URL
PASS: 오탐 없음 — .env.example 의 예시 주소
PASS: 오탐 없음 — 숫자만 있는 설정값(재시도 간격)
PASS: 오탐 없음 — 접미사 위장 도메인(notdiscord.com)
PASS: 오탐 없음 — 접미사 위장 도메인(not-hooks.slack.com)
PASS: 오탐 없음 — CREDENTIAL 저장 방식 이름(글자 설정값)
PASS: 오탐 없음 — PRIVATE_KEY 형식 이름(짧은 글자+숫자 설정값)
PASS: 오탐 없음 — sk-ant 조각을 품은 평범한 식별자(왼쪽 경계)
PASS: 오탐 없음 — 밑줄 접두 위장 discord 도메인
PASS: 오탐 없음 — 밑줄 접두 위장 slack 도메인
PASS: 스캐너 종단 — 벤더 키 파일을 verify.sh 가 차단 (verify.sh exit=1)
PASS: 스캐너 종단 — 대문자 표기 웹훅도 차단(-i 손실 감지) (verify.sh exit=1)
PASS: 스캐너 종단 — 정상 파일은 verify.sh 가 통과 (verify.sh exit=0)
PASS: 3축 종료 상태 동일 (파일 상태[무시 포함] · HEAD · 객체 수 — 중간에 바꿨다 되돌린 변경·같은 개수 객체 교체는 못 본다, REV2-D1)
CHECKED: 32
EXIT: 0
```

→ 무엇을 시켰나: 12자 정책의 탐지·오탐 경계와 실제 `verify.sh` 종단 연결을 실행했다. 무엇이 나왔나: 탐지·비탐지·종단·상태 불변 32건이 전부 PASS했다. 좋은 소식인가: 정책의 실제 행동은 회귀 없이 유지된다.

```text
COMMAND: bash scripts/verify/check-verified-sha.sh task/main-green-suppression-floor12
START_UTC: 2026-09-05T23:29:12Z
START_KST: 2026-09-06T08:29:12+0900
HEAD: 03679010b8420d00d6f09e7a2840852ac1b8c69c
SESSION: 01a07188-a8a2-7422-94a6-a4da70cc8d22
LOCAL_HEAD: 03679010b8420d00d6f09e7a2840852ac1b8c69c
REMOTE_HEAD: 03679010b8420d00d6f09e7a2840852ac1b8c69c
CI_VERIFIED_SHA: 03679010b8420d00d6f09e7a2840852ac1b8c69c
CI_CONCLUSION: success
WORKTREE: clean
VERDICT: VERIFIED
EXIT: 0
```

→ 무엇을 시켰나: 수정 전 PR 머리의 로컬·원격·CI SHA와 작업트리를 판정기로 비교했다. 무엇이 나왔나: 세 SHA가 같고 CI success, 워크트리 clean이었다. 좋은 소식인가: run `33895262180`은 과거 커밋이 아니라 당시 현재 PR 머리에 정확히 귀속된다.

### `acceptance-0-5.sh` 반례

첫 원본 워크트리 실행은 시작 때 저장된 origin/main과 local main이 같았지만 스크립트 내부 fetch가 새 외부 병합을 받아 origin/main만 전진시켜 exit 1이 됐다. 필수 반례를 끝내기 위해 원본 밖의 임시 clone으로 입력을 통제해 다시 실행했다.

```text
COMMAND: git rev-parse HEAD main origin/main; bash scripts/acceptance-0-5.sh
START_UTC: 2026-09-05T23:29:37Z
START_KST: 2026-09-06T08:29:37+0900
HEAD: 03679010b8420d00d6f09e7a2840852ac1b8c69c
LOCAL_MAIN: b7240936827032d5ee6791fa8cdb7d62ef6584b4
ORIGIN_MAIN: b7240936827032d5ee6791fa8cdb7d62ef6584b4
SESSION: 01a07188-a8a2-7422-94a6-a4da70cc8d22
STATUS_BEFORE_START
STATUS_BEFORE_END
FAIL: origin/main(f96ece9564166d56815b3e5c3de5547b615bcb25) != main(b7240936827032d5ee6791fa8cdb7d62ef6584b4) — push 미완료
STATUS_AFTER_START
STATUS_AFTER_END
EXIT: 1
```

→ 무엇을 시켰나: 원본 작업 브랜치에서 0-5를 직접 실행했다. 무엇이 나왔나: 검사 내부 fetch 뒤 origin/main만 외부 병합 커밋으로 전진해 실패했다. 좋은/나쁜 소식인가: 워크트리는 불변이지만 이 검사 결과가 PR HEAD가 아니라 main 참조에 좌우된다는 첫 증거다.

```text
COMMAND: temp clone; checkout task/main-green-suppression-floor12; bash scripts/acceptance-0-5.sh
START_UTC: 2026-09-05T23:31:48Z
START_KST: 2026-09-06T08:31:48+0900
ORIGINAL_HEAD: 03679010b8420d00d6f09e7a2840852ac1b8c69c
ORIGINAL_STATUS_BEFORE_START
ORIGINAL_STATUS_BEFORE_END
TEMP_PATH: /var/folders/4h/jphmynjn2jl54cqy8d_ddhkh0000gn/T/tmp.tJyVgPFs1H/repo
TEMP_HEAD: 03679010b8420d00d6f09e7a2840852ac1b8c69c
TEMP_LOCAL_MAIN: f96ece9564166d56815b3e5c3de5547b615bcb25
TEMP_ORIGIN_MAIN: f96ece9564166d56815b3e5c3de5547b615bcb25
PASS: 0-5 완료 — CI 비밀스캔 강제 + push 완료 + 원격 트리 비밀 0건
TEMP_EXIT: 0
TEMP_STATUS_START
TEMP_STATUS_END
TEMP_RECOVERY_LOCATION: /Users/kangsangmo/.Trash/tmp.tJyVgPFs1H
ORIGINAL_STATUS_AFTER_START
ORIGINAL_STATUS_AFTER_END
EXIT: 0
```

→ 무엇을 시켰나: 동일 PR 머리를 체크아웃한 임시 clone에서 local main과 origin/main만 새 main 커밋으로 맞추고 0-5를 실행했다. 무엇이 나왔나: PR 머리와 main이 서로 다른데도 PASS했다. 좋은/나쁜 소식인가: 0-5 PASS는 PR HEAD 검증 증거가 아니라 main 배송 참조 검사라는 반례가 재현됐다. 임시 사본은 휴지통으로 이동해 복구 가능하고 원본 상태는 불변이다.

```text
COMMAND: temp PR-like clone without local main; bash scripts/acceptance-0-5.sh
START_UTC: 2026-09-05T23:32:32Z
START_KST: 2026-09-06T08:32:32+0900
ORIGINAL_HEAD: 03679010b8420d00d6f09e7a2840852ac1b8c69c
ORIGINAL_STATUS_BEFORE_START
ORIGINAL_STATUS_BEFORE_END
Deleted branch main (was f96ece9).
TEMP_PATH: /var/folders/4h/jphmynjn2jl54cqy8d_ddhkh0000gn/T/tmp.AQRx4G5rci/repo
TEMP_HEAD: 03679010b8420d00d6f09e7a2840852ac1b8c69c
TEMP_LOCAL_MAIN: main
none
TEMP_ORIGIN_MAIN: f96ece9564166d56815b3e5c3de5547b615bcb25
FAIL: origin/main(f96ece9564166d56815b3e5c3de5547b615bcb25) != main(main
none) — push 미완료
TEMP_EXIT: 1
TEMP_STATUS_START
TEMP_STATUS_END
TEMP_RECOVERY_LOCATION: /Users/kangsangmo/.Trash/tmp.AQRx4G5rci
ORIGINAL_STATUS_AFTER_START
ORIGINAL_STATUS_AFTER_END
EXPECTED_EXIT_CONFIRMED: 1
```

→ 무엇을 시켰나: 동일 PR 머리의 임시 clone에서 local main만 지워 PR 러너형 입력을 만들었다. 무엇이 나왔나: 기대대로 exit 1이었고, 실패 문자열에는 `git rev-parse main`이 표준출력에 남긴 `main`과 fallback `none`이 함께 보였다. 좋은/나쁜 소식인가: PR에서 조건만 제거하면 무관한 실패가 생긴다는 반례가 재현됐다. 임시 사본은 휴지통으로 이동했고 원본 상태는 불변이다.

첫 임시 사본 명령은 삭제 명령을 포함했다는 실행기 안전 정책 때문에 셸 시작 전 거부돼 `NOT_RUN`이었다. 같은 검증을 복구 가능한 휴지통 이동으로 바꿔 위 두 원명령을 끝까지 실행했다.

### AC-PR 원문과 집계

```text
QUERY_LABEL: gh run view 33895262180 AC-PR aggregate
START_UTC: 2026-09-05T23:35:24Z
START_KST: 2026-09-06T08:35:24+0900
HEAD: 03679010b8420d00d6f09e7a2840852ac1b8c69c
SESSION: 01a07188-a8a2-7422-94a6-a4da70cc8d22
PR_EVENT_HEAD_CONCLUSION
{"conclusion":"success","event":"pull_request","headSha":"03679010b8420d00d6f09e7a2840852ac1b8c69c","status":"completed","url":"https://github.com/sangmokang/Valuehire_v6/actions/runs/33895262180"}
PR_STEP_AGGREGATE
{"cancelled":0,"defined":24,"failure":0,"skipped":1,"skipped_names":["인수 검사 0-5 (push · CI 연결)"],"success":23,"timed_out":0}
PR_SHA_VALUES
LOCAL_HEAD=03679010b8420d00d6f09e7a2840852ac1b8c69c
REMOTE_BRANCH=03679010b8420d00d6f09e7a2840852ac1b8c69c
PR_HEAD=03679010b8420d00d6f09e7a2840852ac1b8c69c
CI_HEAD=03679010b8420d00d6f09e7a2840852ac1b8c69c
WORKTREE_STATUS_START
 M docs/engineering/main-green-suppression-floor12-goal-2026-09-05.md
WORKTREE_STATUS_END
EXIT: 0
```

→ 무엇을 시켰나: PR run의 이벤트·머리 SHA·전체 결론과 24개 정의의 각 결론을 세고 SHA를 대조했다. 무엇이 나왔나: workflow success, 23 success, 1 skipped, failure/cancelled/timed_out 각 0, 네 SHA가 `0367901…`로 일치했던 08:29:12 KST 스냅샷은 clean이었다. 위 재조회 시점의 워크트리 변경 1건은 그 뒤 작성한 이 goal 문서다. 좋은 소식인가: `PR_GATE: PASS`는 병합된 PR 머리 `0367901…`의 clean 스냅샷에만 귀속되며 현재 dirty 문서 상태에 재사용하지 않는다.

```text
COMMAND: nl -ba .github/workflows/verify.yml | sed -n '132,142p'
START_UTC: 2026-09-05T23:37:04Z
START_KST: 2026-09-06T08:37:04+0900
HEAD: 03679010b8420d00d6f09e7a2840852ac1b8c69c
SESSION: 01a07188-a8a2-7422-94a6-a4da70cc8d22
   132        run: bash scripts/verify/run-acceptance.sh scripts/acceptance-0-7.sh
   133
   134      - name: 인수 검사 0-5 (push · CI 연결)
   135        # origin/main==main 을 검사하므로 main 참조가 유효한 경우에만 의미가 있다.
   136        if: github.ref == 'refs/heads/main'
   137        run: bash scripts/verify/run-acceptance.sh scripts/acceptance-0-5.sh
   138
   139      - name: 억제 만료 스캔 (suppressions.yaml)
   140        # pre-commit 의 expiry 검사는 suppressions.yaml 이 '스테이징된 커밋'에서만 돈다.
   141        # 이미 커밋된 억제가 시간이 지나 썩는 것은 아무도 보지 않는다 — 이 게이트가
   142        # 막겠다고 인용한 98d923f(35일 방치) 시나리오 그 자체다. 그래서 매 push 마다 훑는다.
EXIT: 0
```

→ 무엇을 시켰나: skipped 스텝의 이름·이유·조건·실행줄을 원문 줄번호로 읽었다. 무엇이 나왔나: `.github/workflows/verify.yml:134`는 이름, `:135`는 main 참조 이유, `:136`은 `refs/heads/main` 조건, `:137`은 실제 0-5 실행이다. 좋은 소식인가: skipped 1개는 실행 뒤 재분류한 것이 아니라 실행 전부터 SOT와 검사기에 정의된 예외다.

### 병합 전 기준선과 AC-MAIN 현재 원문

```text
QUERY_LABEL: gh run view 33313102834 baseline aggregate
START_UTC: 2026-09-05T23:37:33Z
START_KST: 2026-09-06T08:37:33+0900
HEAD: 03679010b8420d00d6f09e7a2840852ac1b8c69c
SESSION: 01a07188-a8a2-7422-94a6-a4da70cc8d22
{"conclusion":"failure","event":"push","headSha":"b7240936827032d5ee6791fa8cdb7d62ef6584b4","status":"completed","url":"https://github.com/sangmokang/Valuehire_v6/actions/runs/33313102834"}
{"cancelled":0,"defined":24,"failure":1,"failure_names":["억제 만료 스캔 (suppressions.yaml)"],"skipped":11,"success":12,"timed_out":0}
EXIT: 0
```

→ 무엇을 시켰나: 요청이 고정한 병합 전 최신 main push run을 다시 집계했다. 무엇이 나왔나: event push, SHA `b724093…`, workflow failure, 24개 중 12 success·11 skipped·1 failure이며 실패 이름은 억제 만료 스캔이다. 좋은/나쁜 소식인가: 병합 전 판정은 정확히 `MAIN_CI: NOT_YET_VERIFIED`였고 복구가 필요했다.

```text
QUERY_LABEL: gh run view 33998556226 AC-MAIN aggregate
START_UTC: 2026-09-05T23:35:24Z
START_KST: 2026-09-06T08:35:24+0900
HEAD: 03679010b8420d00d6f09e7a2840852ac1b8c69c
SESSION: 01a07188-a8a2-7422-94a6-a4da70cc8d22
MAIN_EVENT_HEAD_CONCLUSION
{"conclusion":"success","event":"push","headSha":"f96ece9564166d56815b3e5c3de5547b615bcb25","status":"completed","url":"https://github.com/sangmokang/Valuehire_v6/actions/runs/33998556226"}
MAIN_STEP_AGGREGATE
{"cancelled":0,"defined":24,"failure":0,"skipped":0,"success":24,"timed_out":0}
MAIN_SHA_VALUES
REMOTE_MAIN=f96ece9564166d56815b3e5c3de5547b615bcb25
CI_HEAD=f96ece9564166d56815b3e5c3de5547b615bcb25
EXIT: 0
```

→ 무엇을 시켰나: 외부 병합으로 새로 생긴 main push run을 같은 24개 정의로 집계하고 원격 main SHA와 비교했다. 무엇이 나왔나: event push, workflow success, 24 success, skipped/failure/cancelled/timed_out 각 0, 두 SHA 일치다. 좋은 소식인가: 현재 사실은 `MAIN_CI: PASS`지만 이 세션의 병합 승인·실행 증거는 아니며 외부 병합 절차 위반을 지우지 않는다.

### 직접 읽기 원문 1/6 — 코딩 원칙 정본

````text
COMMAND: sed -n '1,9999p' docs/sot/coding-principles.md
START_UTC: 2026-09-05T23:41:25Z
START_KST: 2026-09-06T08:41:26+0900
HEAD: 03679010b8420d00d6f09e7a2840852ac1b8c69c
SESSION: 01a07188-a8a2-7422-94a6-a4da70cc8d22
# Valuehire v6 — 코딩 원칙 (SOT)

최종 갱신: 2026-08-21
근거(전체 논증·적대검증): `docs/engineering/v6-coding-principles-goal-2026-08-06.md` §0~§0-E, §8

## 현재 규칙

## §1. 확정 원칙 — 오너 27개 + 추가 6개 + Claude/Codex 자체제안 23개(A~O) + v4 전수조사 자체제안 12개를 **P1~P24**로 통합

**압축 기준(P1의 자기 적용)**: 통과하는 기계 장치를 가질 수 없는 항목은 남기지 않는다.
번호는 오너의 원본 27개 번호가 아니라 v6 정본 번호다. 대응 관계는 §2 판정표에 있다.
**P1~P15는 초판(§0~§0-C 근거)에서 확정, P16~P22는 §0-D~§0-E 병합에서 신설·흡수**했다. **P23~P24 는 2026-08-21 적대 검토(검사의 존재 vs 의미)에서 신설**했다.

| ID | 원칙 | 기계 장치 (이것이 없으면 원칙도 없다) |
|---|---|---|
| **P1** | **기계 장치 없는 원칙은 삭제한다** (키스톤) | `principles.yaml` 의 모든 항목이 `mechanism` 을 갖고 그 검사가 CI에서 실제 실행됐음을 확인. 미충족 항목 존재 시 CI 실패 |
| **P2** | **인수 기준은 실행 가능한 명령이다** | PR 본문에 검증 명령 + 기대 출력이 없으면 CI 실패. 산문 단언만 있으면 실패. "완료"의 정의는 PR 템플릿 체크박스가 아니라 **CI job**으로 만든다(사람이 체크하는 상자는 위장 가능) |
| **P3** | **조용한 실패 금지** | ① 판정은 `PASS / FAIL / NOT_RUN` **3상태**. `NOT_RUN` 이 하나라도 있으면 전체 판정은 PASS 불가 ② bare `except`/`catch` 금지 lint, `?? 기본값`·`catch { return null }`·`\|\| []` 패턴도 린트로 금지하고 명시적 `assertX()` 관문으로 대체. 단 **동일 block scope**에서 `const`로 `new Map()`을 선언한 컬렉션의 `.get(...) \|\| []`만 “키 없음”을 빈 컬렉션으로 모델링한 것으로 허용하며, 부모 scope에서 capture한 Map은 자동 예외가 아니다 ③ 모든 핸들러가 status와 함께 DB 기록 |
| **P4** | **가짜 구현 금지** | 외부 효과 모듈은 **네트워크 차단 CI 레인에서 반드시 실패**해야 한다. 네트워크 없이 초록이면 시뮬레이션이라는 증명이므로 CI 실패 |
| **P5** | **테스트 통과용 코드 금지** | ① RED 커밋 이후 **테스트 파일 불변** — 구현 PR의 테스트 파일 diff 검사 ② 순수 판정·채점 함수는 **속성 기반 테스트**(Hypothesis / fast-check) 필수 ③ 표본 뮤테이션 테스트 |
| **P6** | **실행 환경은 제품의 일부** | 소스 트리와 실행물 분리. launchd plist가 저장소·워크트리·Desktop 경로를 참조하면 CI 실패. `doctor / install / reconcile / status / uninstall` 을 코드로 제공 |
| **P7** | **되돌릴 수 있어야 배포다** | 이전 digest로 **한 명령 롤백**. N-1 릴리스가 현재 DB 스키마를 읽을 수 있음을 마이그레이션 검사로 보장 |
| **P8** | **단일 좌석은 lease로만 접근한다** | 3사 계정 = 사이트당 1석. TTL 있는 DB lease + fencing token. 획득 실패 시 크래시가 아니라 정상 종료. 오너 Chrome 점유 감지 |
| **P9** | **외부 효과는 멱등키 + readback** | ① `(position, candidate, channel)` 에 **DB unique 제약**. 실행 **전** intent 기록(write-ahead), 실행 **후** 화면 재확인(readback). "눌렀다"는 의도이지 결과가 아니다 ② **DB 접근 정책(RLS)도 같은 원칙**: `USING (true)` + `TO authenticated/anon` 조합으로 정책을 생성하면 P13의 "만료 없는 억제"와 동일 취급 — 정책 생성 PR에 회수계획 또는 정당화 주석 필수, 없으면 CI 경고(v4에서 이 조합 6개가 회수 없이 방치돼 후보자 경력데이터 5테이블 전체 노출, §0-D D-3) |
| **P10** | **사업 결과를 매일 박스 밖으로** | "오늘 포털별 실제 접촉 후보자 수"를 시스템이 스스로 외부 감시자에게 전송. 24시간 연속 0이면 알림. 감시자는 감시 대상과 **다른 실패 영역**에 있어야 한다(구매, 자체 구축 금지) |
| **P11** | **코드 예산 — 파일 크기와 PR 크기는 다른 규칙이다** | ① **파일**: soft 300 / hard 600 LOC(v5 모듈 126개 결함밀도 실측, 0.44→1.52건/100줄로 단조증가, 하한은 두지 않는다) ② **PR diff는 균일한 크기로 규제하지 않는다** — v4 머지 PR 313개(권위 데이터)에서 크기-결함률 곡선이 존재하지 않음을 확인(최초 "100~300줄 최적" 결론은 Codex REFUTE로 폐기, §0-D D-3). 대신 **외부 의존 경로**를 건드리는 PR은 크기 무관 라이브 스모크 1건 필수(P19), **내부 로직**은 크기 상한 없음(500줄+가 오히려 최저 결함률 34.8%) ③ 단 **3,000줄 초과 PR은 절대 금지**(60일 결함률 100%, n=4 — 두 달 뒤 원인 추적 불가) ④ 함수 soft 60 / hard 100 LOC. 생성 파일·마이그레이션·픽스처 면제. 예외 대장에 owner·reason·**expiry** 필수, expiry 경과 시 CI 실패 |
| **P12** | **회수 — 만들기 전에 이미 있는지 기계가 확인한다** | 코드에서 자동 생성되는 `capabilities.yaml`. 중복 id 추가 시 CI 실패. 정적 미참조 export 스캔(호출자 0인 모듈은 크기 무관 머지 차단). **`.gitignore` 된 산출물 디렉터리**(`private-reviews/`, `artifacts/`, `.harness/`)도 회수 범위에 포함. **화면(라우트·컴포넌트) 삭제 PR은 그 화면이 유일한 호출자였던 하위 모듈 목록을 자동 출력**하고 함께 처리하거나 사유를 남긴다(v4: 화면 4개 삭제 후 라이브러리 미삭제로 14,622줄 고아, §0-D D-3 인접 사례). **긴 세션 중에는 시작 시점의 HEAD 를 신뢰하지 않는다 — 보고·판단 직전에 HEAD 재확인**을 한다. 기계 장치: `.claude/settings.json` 의 SessionStart hook → `scripts/session-status.sh` 가 HEAD·origin 동기 상태·미해결 RED 를 자동 출력(2026-08-07 실측: 한 세션이 대화 중 옆 세션의 커밋 6개를 못 보고 이미 끝난 Phase 0 을 다시 브리핑함) |
| **P13** | **검사는 약화될 수 없다** 🆕 (사례 A·B·C③·E·G, §0-D D-3 첨부율 붕괴) | ① 검사 파일·계약 파일(`contracts/`, `*.spec`, CI 워크플로, plist 템플릿)의 diff는 **PR 라벨 `weakens-check` 없이 머지 불가** ② 검사 강도를 낮추는 패턴(`skip`, `xfail`, `allow_failure`, `continue-on-error`, `\|\| true`, 조건을 `if exists` 로 완화)은 CI가 탐지 ③ **모든 억제에 만료일 필수** — `suppressions.yaml` 에 `owner·reason·expiry·issue` 를 적고 **expiry 경과 시 CI 실패** ④ 검사기는 자기 자신을 검사 대상에서 제외할 수 없다 ⑤ **적대검증 판정서 첨부는 PR 필수 필드**로 CI가 파일 경로 존재를 확인한다(PR 템플릿 체크박스가 아니라 기계 검사) — v4에서 요구조항 명문화 후에도 첨부율이 41.7%→14.5%로 떨어진 것에 대한 직접 대응 ⑥ **안전장치는 존재가 아니라 무력화 저항으로 검증한다** — 인수 검사 본문을 `exit 0`·`true`·no-op·빈 파일·출력만으로 바꾸거나, CI 스텝에 `if: ${{ false }}`·항상-거짓 조건·`continue-on-error`·`echo` 대체를 넣었을 때 **반드시 빨개져야 한다**. 살아남은 무력화가 하나라도 있으면 그 검사가 아니라 **검증 체계 자체가 FAIL** 이다. 검사 대상이 0개인 것도 합격이 아니다(P20 과 결합). 기계 장치: `scripts/verify/run-acceptance.sh`(종료값 0 인데 판정 출력이 없으면 불합격) + `acceptance-semantic-mutations.sh`(무력화 5종 × 인수 검사 전량) + `scripts/verify/check-ci-step-integrity.sh`(워크플로를 실제 YAML 로 파싱해 조건부·오류무시 스텝 차단) + `acceptance-ci-step-integrity.sh`. 2026-08-21 실측: `acceptance-hs-a4.sh` 본문을 `exit 0` 으로 바꿔도, `run: bash x.sh` 를 `run: echo bash x.sh` 로 바꿔도 CI 는 초록이었다 |
| **P14** | **판정 수치는 코드가 만든다. LLM도 사람도 쓰지 않는다** 🆕 (사례 D) | ① 점수·확률·적합도·평점은 **순수 함수의 반환값만** DB에 기록. LLM 출력에서 숫자를 파싱해 판정 필드에 넣는 경로 금지(lint) ② 판정 행은 **입력 해시 + 계산 함수 버전**을 함께 저장해 재계산으로 검증 가능해야 함 ③ 판정 함수는 **속성 기반 테스트 필수**(P5와 결합) ④ 산출물에 실행하지 않은 도구·모델 이름을 기록 금지 |
| **P15** | **검증을 우회할 수 없다** 🆕 (사례 C②) | ① `make ship` 은 **작업트리가 커밋 상태와 일치할 때만** 진행(uncommitted diff·untracked 존재 시 거부) ② RED 커밋 이후 테스트 파일 diff 금지(P5)를 **되돌림 커밋에도 적용** — revert가 테스트·검사 파일을 건드리면 CI 실패 ③ **로컬 훅은 우회 가능하다는 것을 전제로 설계한다** — `git push --no-verify` 는 훅을 아예 실행하지 않으므로 "훅이 돌았는지"를 사후에 알 방법이 없다(2026-08-07 검토 결과 탐지 불가로 확정). 따라서 로컬 훅은 **빠른 1차 차단**이고 **판정 권한은 CI에 있다**. 같은 검사가 양쪽에 있어야 하며, 로컬에만 있는 검사는 없는 것으로 친다 ④ **구현 커밋은 자기 테스트의 기대값을 바꿀 수 없다** — 기대값(expect) 변경은 **단독 커밋**이어야 하고, 그 커밋의 PR 본문에 **삭제된 단언 목록을 자동 노출**한다(구 Desktop 원칙안 M을 흡수) | v5 단언 삭제 **6배**(추가 2.4배·삭제 14배, §0-D D-1). `ed570ab`가 SQL과 그 테스트 기대값을 한 커밋에서 뒤집고 같은 날 취소, `c73be71`이 행위 단언 17개를 커밋 메시지에 언급도 없이 삭제 |
| **P16** | **테스트는 소스 텍스트가 아니라 런타임 동작을 검사한다** 🆕 | ① `readFileSync`+`toContain`류 텍스트 단언 테스트는 파일명에 `.contract.test.*` 접미사를 강제하고, 그 밖의 파일에서 이 패턴이 발견되면 CI 실패 ② 신규 테스트는 대상 모듈을 **반드시 런타임 import** ③ 테스트/구현 비율과 결함률의 상관계수를 CI가 주기 계산해 **양의 상관**이면 경고 | v4 단언의 **29%**(3,037/10,450)가 소스 문자열만 검사. Codex 변조실증 — 731줄 컴포넌트를 17줄 스텁으로 바꿔도 3,706개 중 **2개만 실패**(그 2개도 텍스트 단언). 테스트-결함 상관계수 **r=+0.764**(정상은 음수) |
| **P17** | **증거는 만든 자가 쓸 수 없다** 🆕 | 판정서·영수증 쓰기 경로는 **러너 전용 권한**으로 분리한다. 에이전트에게 그 경로의 쓰기 권한 자체를 주지 않는다(위조 가능 경로를 하나씩 열거해서 막는 방식은 채택하지 않는다 — 열거는 항상 새는 곳이 생긴다) | v4 위조 차단 가드(`4bed913`)가 **7가지 쓰기 경로**(`>`·`tee`·`cp/mv/ln/rsync`·`sed -i`·`python -c`·`Write/Edit/MultiEdit`·MCP)를 하나씩 나열해서 막아야 했다 |
| **P18** | **위험한 동작은 금지하지 않고 능력을 없앤다** 🆕 | 사고 재발 시 가드(사후 검사) 추가 대신, 그 동작이 구조적으로 불가능하도록 권한·참조·토큰을 회수한다. P8(좌석 lease)의 일반화 | v4 가드 **20개**(11+9)가 전부 사후 대응. 가드 스스로 자백: *"훅은 로드 실패 시 통과라 최종 방어선이 아니다"* |
| **P19** | **외부 의존 경계는 크기와 무관하게 라이브 스모크가 배송 조건이다** 🆕 | 파일 경로 기준 자동 분류(`tools/gmail-*`, `*login*`, `src/lib/resumeIntake`, 채용사이트 스크래핑 등). 이 경로를 건드리는 PR은 CI가 **라이브 스모크 1건**을 요구한다. 내부 로직·화면은 크기 제한 없음 | v4 PR 313개 실측: 외부 의존 포함 PR은 크기를 줄여도 14일 결함률 62.5%가 바닥. 내부 로직은 500줄+에서도 34.8%(전 구간 최저). 기능별 1천줄당 fix도 외부(9.1~23.2) vs 내부(1.6~4.4) — **5~14배 차이**(§0-D D-3) |
| **P20** | **CI 검사는 "0건 처리로 통과"를 스스로 의심한다** 🆕 | typecheck·test 실행 스텝은 처리한 파일·케이스 수를 로그로 남기고, 사전에 정한 최소치 미만이면 **그 자체로 FAIL**(P3의 3상태 원칙을 CI 파이프라인 자체의 신뢰성에도 적용) | v4: `next typegen` 단독은 타입파일 3개만 만들어 `tsc`가 검사할 대상이 없는 채로 exit 0. 실제 `next build`는 184개를 만들어야 검사가 성립한다. **"CI에 `npm run check` 추가"라는 최초 P0 권고 자체가 이 함정에 걸려 영구 초록불이 될 뻔했다**(Codex가 잡음, §0-D D-3) |
| **P21** | **데이터는 git에 넣지 않는다** 🆕 | 1MB 초과 데이터 파일(JSON 덤프 등)은 pre-commit에서 차단하고 Supabase Storage/S3로 이관 | v4에 JSON **95.68MB**가 커밋돼 있다. 최대 단일 파일 31.4MB — 클론·CI 체크아웃이 무거워진다 |
| **P22** | **하드코딩 금지 + 자격증명은 소스에도 화면에도 없다** | 운영 상수·URL·포트·셀렉터는 `contracts/*.json` 한 곳. 코드 리터럴 재정의 검출 테스트. `secrets` 가드가 **소스 텍스트뿐 아니라 JSX 렌더 대상까지** 검사(값이 화면에 그대로 출력되는 경우 차단) | v4: `saramin.co.kr` 18파일·`9222` 9파일·셀렉터 10파일 54곳. **데모 계정 비밀번호가 공개 로그인 화면(`login-client.tsx:321`)에 렌더돼 노출**, 원본 27번 목록에서 이 갭이 명시적 P번호 없이 방치돼 있던 것을 오늘 병합에서 메움 |
| **P23** | **초록불은 커밋 SHA 에 귀속된다. 브랜치나 PR 에 귀속되지 않는다** 🆕 | `로컬 HEAD == 원격 브랜치 HEAD == CI 가 실제로 검사한 SHA` 세 값이 모두 같고, 그 SHA 에 대한 verify 결론이 success 이고, 작업트리가 깨끗할 때만 **VERIFIED** 다. 하나라도 어긋나면 **UNVERIFIED**, 조회 자체를 못 하면 **NOT_RUN** 이다(모르는 것은 통과가 아니다 · P3). 기계 장치: `scripts/verify/check-verified-sha.sh` 가 SHA 에 붙은 check-run 만 조회해 상태를 계산하고, `acceptance-verified-sha.sh` 가 진리표 9종 + 사유 출력 + 인자 부족 fail-closed 를 검증한다. **이 스크립트는 완료를 선언하지 않는다 — 상태를 계산해 출력할 뿐이다**(P14 의 일반화: 판정 수치뿐 아니라 판정 자체를 사람·LLM 의 문장에서 뗀다). | PR #31 원격 HEAD 는 929247a, 로컬 HEAD 는 26ad98c, 초록불은 또 다른 옛 커밋 것이었는데 그 상태로 "CI 통과"라고 말할 수 있었다 |
| **P24** | **복구·롤백 계열은 성공 경로가 아니라 불변조건으로 규정한다** 🆕 | 요구사항을 "되돌린다"로 적으면 되돌리기가 **실패했을 때**의 상태가 정의되지 않는다. 대신 절대 발생하면 안 되는 상태를 적는다. **Inv1** 복구가 100% 성공하기 전에는 recovery state 를 삭제하지 않는다 **Inv2** 복구 실패를 삼키지 않고 출력한다(P3) **Inv3** 부분 적용은 `RECOVERY_REQUIRED` 표식으로 남는다 **Inv4** 실패 뒤에도 재복구가 가능하다. 검증은 정상 경로가 아니라 **실패 주입**으로 한다 — 성공하는 rollback 만 시험하면 이 결함군을 원리적으로 잡을 수 없다. 기계 장치: `acceptance-guard-global-skill-files.sh` 의 Inv1~4(chmod 실패 주입). | 2026-08-21 실측: guard lock 이 되돌리기에 실패하고도 복구 장부를 지워, 파일이 444 로 잠긴 채 `recover` 조차 "복구할 lock 상태 없음"으로 영구 실패했다. 기존 8개 케이스는 되돌리기가 **성공하는** 경로만 봐서 이것을 잡지 못했다 |

> **비밀 스캔 값 하한 12자 확정.** 6~11자 비밀은 키워드·벤더 규칙 담당.
> 근거: `docs/engineering/secret-webhook-vendor-rev2-verdict-2026-08-12.md` §설계 결정 카드 2.

### §1-B. 웹 자동화(사이트에 붙어 조회·수집·입력)에만 적용되는 5조

가장 많이 실패한 영역이라 따로 둔다. Claude/Codex 자체제안 원칙안(구 Desktop 문서) §5에서 흡수.

| # | 조항 |
|---|---|
| 1 | **셀렉터는 코드가 아니라 데이터다** — `contracts/*/markers.json` 한 곳. 드리프트 대응 = 데이터 수정 |
| 2 | **판정기는 하나다** — 자동로그인 판정과 증거캡처 판정이 같은 함수를 쓴다 |
| 3 | **브라우저 계층은 한 벌이다** — 두 벌이 생기면 셀렉터 출처가 4곳으로 갈라진다(v4 실측) |
| 4 | **테스트는 실캡처 스냅샷으로만** — 시나리오 전체를 가짜 브라우저로 흉내내는 테스트를 만들지 않는다. 판정 / 배선 / 동작 3갈래로 나눠 검사한다 |
| 5 | **개입 감지는 규율이 아니라 구조로** — 드라이버 포트를 감싸 개입 신호 이후 호출이 **타입상 불가능**하게(손으로 검사 호출을 뿌린 v5에서 같은 결함 8회 재발) |

### 검증 체제 (P1~P22에 얹히는 절차)

| ID | 규칙 | 강제 |
|---|---|---|
| **V-1** | **검증자는 실행 산출물을 제출한다.** 코드를 읽고 낸 판단만으로는 PASS 불가. 실행할 것이 없으면 "실행 불가"라고 적고 그 자체를 결함으로 보고 | `/strict` §5 개정 |
| **V-2** | **V1은 다른 모델 계열, V2는 재현 전담.** V2는 새 의견을 내지 않고 V1의 증거를 직접 돌린다 | `/strict` §6 개정 |
| **V-3** | **V3 = 라이브 1건.** 기계 영수증 없이 완료 없음 | `make ship` 이 거부 |
| **V-4** | **외부 모델 의견은 가설이지 합격증이 아니다.** `private-reviews/` 의 지적은 로컬에서 `file:line` 으로 재현되기 전까지 결함으로 세지 않는다 | 문서 규약 + PR 템플릿 |
| **V-5** | **G·V1·V2가 계약 기준에서 갈리면 결론을 내지 않는다** | `/strict` 기존 규칙 유지 |

## 시행 지점

- Strict는 시작할 때 이 파일과 `docs/sot/principles.yaml`을 현재 저장소에서 직접 읽고 `bash scripts/acceptance-principles-check.sh`를 실행한다. 메모리·과거 대화·이전 보고서는 보조 정보이며 두 파일의 직접 로드를 대신하지 않는다.
- `docs/sot/principles.yaml`은 이 문서의 32개 원칙 문구와 Strict·pre-push·CI 검증 배선을 기계가 읽도록 옮긴 파생 장부다. 원칙 문구가 갈리면 이 문서가 맞고 검사기는 불일치를 실패시킨다.
- 각 원칙의 "기계 장치" 열이 실제 강제 지점이다. 이미 CI에 있는 것도 있고(예: 비밀 스캔 → P4·P22, `verify.sh` + `.github/workflows/verify.yml`), 아직 표에만 있고 CI에 없는 것도 있다 — "정본화됐다"가 "이미 강제된다"를 뜻하지 않는다.
- 오너 원본 27개 번호 ↔ v6 P번호 대응표는 원본 goal 문서 §2에 있다.
- 실제 강제 여부는 항상 실행으로 재확인한다(가정 금지) — `docs/sot/verification-commands.md` 참고.

## 비범위 / 한계

- 이 문서는 "확정된 규칙"만 담는다. 왜 이 번호가 나왔는지의 논증·v4/v5 실측·적대검증 과정은 원본 goal 문서(§0~§0-E, §8, 총 595줄)에 있으며 이 문서는 그것을 대체하지 않는다.
- "§4 GitHub 전략(CI가 강제할 것 — 원칙별 게이트 매핑)"은 이 문서에 옮기지 않았다. P번호별 "기계 장치" 열과 중복이라 원본 goal 문서 §4에만 둔다.
EXIT: 0
````

→ 무엇을 시켰나: 현재 작업 브랜치의 코딩 원칙 정본을 첫 줄부터 끝까지 직접 읽었다. 무엇이 나왔나: P11 hard 600줄, P13 검사 약화 차단, P23 SHA 귀속, P24 복구 불변조건과 12자 하한 정책이 들어 있다. 좋은 소식인가: 이번 AC 교정·고장 주입·SHA 대조의 상위 계약을 현재 HEAD에서 직접 확정했다.

### 직접 읽기 원문 2/6 — 원칙 기계 장부

````text
COMMAND: sed -n '1,9999p' docs/sot/principles.yaml
START_UTC: 2026-09-05T23:42:02Z
START_KST: 2026-09-06T08:42:03+0900
HEAD: 03679010b8420d00d6f09e7a2840852ac1b8c69c
SESSION: 01a07188-a8a2-7422-94a6-a4da70cc8d22
# coding-principles.md의 32개 원칙을 Strict 직접 로드와 로컬/CI 검사에 연결하는 기계 장부.
# mechanism_found와 status는 개별 제품 기능의 완성도가 아니라 이 원칙 계약의 직접 로드·검증 배선만 나타낸다.
# mechanism_expected에 적힌 제품 장치의 실제 구현 여부는 이 장부의 PASS 범위가 아니다.
# 원칙 문구의 유일한 정본은 docs/sot/coding-principles.md이며 이 파일은 파생 장부다.

- id: "P1"
  principle: "기계 장치 없는 원칙은 삭제한다"
  mechanism_expected: "principles.yaml 전 항목이 mechanism을 갖고 CI가 확인"
  mechanism_found:
    - path: "docs/sot/coding-principles.md"
      check: "scripts/acceptance-principles-check.sh"
      stages: ["strict", "pre-push", "ci"]
  status: "PASS"
  evidence: "Strict 계약 편입 장치의 실존·직접 실행만 PASS다. mechanism_expected에 적힌 제품 장치의 구현 완료를 주장하지 않는다."

- id: "P2"
  principle: "인수 기준은 실행 가능한 명령이다"
  mechanism_expected: "PR 본문에 검증 명령+기대 출력 없으면 CI 실패"
  mechanism_found:
    - path: "docs/sot/coding-principles.md"
      check: "scripts/acceptance-principles-check.sh"
      stages: ["strict", "pre-push", "ci"]
  status: "PASS"
  evidence: "Strict 계약 편입 장치의 실존·직접 실행만 PASS다. mechanism_expected에 적힌 제품 장치의 구현 완료를 주장하지 않는다."

- id: "P3"
  principle: "조용한 실패 금지"
  mechanism_expected: "3상태 판정 + bare except/catch 금지 lint + 핸들러 DB 기록"
  mechanism_found:
    - path: "docs/sot/coding-principles.md"
      check: "scripts/acceptance-principles-check.sh"
      stages: ["strict", "pre-push", "ci"]
  status: "PASS"
  evidence: "Strict 계약 편입 장치의 실존·직접 실행만 PASS다. mechanism_expected에 적힌 제품 장치의 구현 완료를 주장하지 않는다."

- id: "P4"
  principle: "가짜 구현 금지"
  mechanism_expected: "외부 효과 모듈이 네트워크 차단 레인에서 반드시 실패"
  mechanism_found:
    - path: "docs/sot/coding-principles.md"
      check: "scripts/acceptance-principles-check.sh"
      stages: ["strict", "pre-push", "ci"]
  status: "PASS"
  evidence: "Strict 계약 편입 장치의 실존·직접 실행만 PASS다. mechanism_expected에 적힌 제품 장치의 구현 완료를 주장하지 않는다."

- id: "P5"
  principle: "테스트 통과용 코드 금지"
  mechanism_expected: "RED 이후 테스트파일 불변 검사 + 속성기반 테스트 + 뮤테이션 표본"
  mechanism_found:
    - path: "docs/sot/coding-principles.md"
      check: "scripts/acceptance-principles-check.sh"
      stages: ["strict", "pre-push", "ci"]
  status: "PASS"
  evidence: "Strict 계약 편입 장치의 실존·직접 실행만 PASS다. mechanism_expected에 적힌 제품 장치의 구현 완료를 주장하지 않는다."

- id: "P6"
  principle: "실행 환경은 제품의 일부"
  mechanism_expected: "launchd plist가 저장소 경로 참조시 CI 실패 + doctor/install/reconcile/status/uninstall"
  mechanism_found:
    - path: "docs/sot/coding-principles.md"
      check: "scripts/acceptance-principles-check.sh"
      stages: ["strict", "pre-push", "ci"]
  status: "PASS"
  evidence: "Strict 계약 편입 장치의 실존·직접 실행만 PASS다. mechanism_expected에 적힌 제품 장치의 구현 완료를 주장하지 않는다."

- id: "P7"
  principle: "되돌릴 수 있어야 배포다"
  mechanism_expected: "이전 digest로 한 명령 롤백 + N-1 마이그레이션 호환 검사"
  mechanism_found:
    - path: "docs/sot/coding-principles.md"
      check: "scripts/acceptance-principles-check.sh"
      stages: ["strict", "pre-push", "ci"]
  status: "PASS"
  evidence: "Strict 계약 편입 장치의 실존·직접 실행만 PASS다. mechanism_expected에 적힌 제품 장치의 구현 완료를 주장하지 않는다."

- id: "P8"
  principle: "단일 좌석은 lease로만 접근한다"
  mechanism_expected: "TTL DB lease + fencing token, 오너 Chrome 점유 감지"
  mechanism_found:
    - path: "docs/sot/coding-principles.md"
      check: "scripts/acceptance-principles-check.sh"
      stages: ["strict", "pre-push", "ci"]
  status: "PASS"
  evidence: "Strict 계약 편입 장치의 실존·직접 실행만 PASS다. mechanism_expected에 적힌 제품 장치의 구현 완료를 주장하지 않는다."

- id: "P9"
  principle: "외부 효과는 멱등키 + readback"
  mechanism_expected: "(position,candidate,channel) DB unique 제약 + write-ahead + readback"
  mechanism_found:
    - path: "docs/sot/coding-principles.md"
      check: "scripts/acceptance-principles-check.sh"
      stages: ["strict", "pre-push", "ci"]
  status: "PASS"
  evidence: "Strict 계약 편입 장치의 실존·직접 실행만 PASS다. mechanism_expected에 적힌 제품 장치의 구현 완료를 주장하지 않는다."

- id: "P10"
  principle: "사업 결과를 매일 박스 밖으로"
  mechanism_expected: "일일 접촉 후보자 수 외부 감시자 전송, 24h 0건시 알림"
  mechanism_found:
    - path: "docs/sot/coding-principles.md"
      check: "scripts/acceptance-principles-check.sh"
      stages: ["strict", "pre-push", "ci"]
  status: "PASS"
  evidence: "Strict 계약 편입 장치의 실존·직접 실행만 PASS다. mechanism_expected에 적힌 제품 장치의 구현 완료를 주장하지 않는다."

- id: "P11"
  principle: "코드 예산 — 파일 크기와 PR 크기는 다른 규칙이다"
  mechanism_expected: "파일 soft300/hard600, 함수 soft60/hard100, 3000줄 초과 PR 절대금지"
  mechanism_found:
    - path: "docs/sot/coding-principles.md"
      check: "scripts/acceptance-principles-check.sh"
      stages: ["strict", "pre-push", "ci"]
  status: "PASS"
  evidence: "Strict 계약 편입 장치의 실존·직접 실행만 PASS다. mechanism_expected에 적힌 제품 장치의 구현 완료를 주장하지 않는다."

- id: "P12"
  principle: "회수 — 만들기 전에 이미 있는지 기계가 확인한다"
  mechanism_expected: "capabilities.yaml 자동생성 + 미참조 export 스캔 + gitignore 산출물 포함 + session-status.sh HEAD 재확인"
  mechanism_found:
    - path: "docs/sot/coding-principles.md"
      check: "scripts/acceptance-principles-check.sh"
      stages: ["strict", "pre-push", "ci"]
  status: "PASS"
  evidence: "Strict 계약 편입 장치의 실존·직접 실행만 PASS다. mechanism_expected에 적힌 제품 장치의 구현 완료를 주장하지 않는다."

- id: "P13"
  principle: "검사는 약화될 수 없다"
  mechanism_expected: "weakens-check 라벨 강제 + 억제패턴 탐지 + suppressions.yaml expiry 강제 + 자기제외 금지 + 적대검증 첨부 CI 확인"
  mechanism_found:
    - path: "docs/sot/coding-principles.md"
      check: "scripts/acceptance-principles-check.sh"
      stages: ["strict", "pre-push", "ci"]
  status: "PASS"
  evidence: "Strict 계약 편입 장치의 실존·직접 실행만 PASS다. mechanism_expected에 적힌 제품 장치의 구현 완료를 주장하지 않는다."

- id: "P14"
  principle: "판정 수치는 코드가 만든다. LLM도 사람도 쓰지 않는다"
  mechanism_expected: "LLM 출력→판정 필드 변환 금지 lint + 입력해시+계산함수버전 저장"
  mechanism_found:
    - path: "docs/sot/coding-principles.md"
      check: "scripts/acceptance-principles-check.sh"
      stages: ["strict", "pre-push", "ci"]
  status: "PASS"
  evidence: "Strict 계약 편입 장치의 실존·직접 실행만 PASS다. mechanism_expected에 적힌 제품 장치의 구현 완료를 주장하지 않는다."

- id: "P15"
  principle: "검증을 우회할 수 없다"
  mechanism_expected: "작업트리 청결 확인 + revert의 테스트/검사파일 변경 차단 + expect값 변경 단독커밋 강제"
  mechanism_found:
    - path: "docs/sot/coding-principles.md"
      check: "scripts/acceptance-principles-check.sh"
      stages: ["strict", "pre-push", "ci"]
  status: "PASS"
  evidence: "Strict 계약 편입 장치의 실존·직접 실행만 PASS다. mechanism_expected에 적힌 제품 장치의 구현 완료를 주장하지 않는다."

- id: "P16"
  principle: "테스트는 소스 텍스트가 아니라 런타임 동작을 검사한다"
  mechanism_expected: ".contract.test.* 접미사 강제 + 런타임 import 필수 + 테스트/결함 상관계수 CI 계산"
  mechanism_found:
    - path: "docs/sot/coding-principles.md"
      check: "scripts/acceptance-principles-check.sh"
      stages: ["strict", "pre-push", "ci"]
  status: "PASS"
  evidence: "Strict 계약 편입 장치의 실존·직접 실행만 PASS다. mechanism_expected에 적힌 제품 장치의 구현 완료를 주장하지 않는다."

- id: "P17"
  principle: "증거는 만든 자가 쓸 수 없다"
  mechanism_expected: "판정서 쓰기 경로는 러너 전용 권한, 에이전트 쓰기 권한 자체 없음"
  mechanism_found:
    - path: "docs/sot/coding-principles.md"
      check: "scripts/acceptance-principles-check.sh"
      stages: ["strict", "pre-push", "ci"]
  status: "PASS"
  evidence: "Strict 계약 편입 장치의 실존·직접 실행만 PASS다. mechanism_expected에 적힌 제품 장치의 구현 완료를 주장하지 않는다."

- id: "P18"
  principle: "위험한 동작은 금지하지 않고 능력을 없앤다"
  mechanism_expected: "사후 가드 대신 구조적으로 불가능하게 권한·참조·토큰 회수"
  mechanism_found:
    - path: "docs/sot/coding-principles.md"
      check: "scripts/acceptance-principles-check.sh"
      stages: ["strict", "pre-push", "ci"]
  status: "PASS"
  evidence: "Strict 계약 편입 장치의 실존·직접 실행만 PASS다. mechanism_expected에 적힌 제품 장치의 구현 완료를 주장하지 않는다."

- id: "P19"
  principle: "외부 의존 경계는 크기와 무관하게 라이브 스모크가 배송 조건이다"
  mechanism_expected: "파일경로 자동분류 → 해당 PR은 라이브 스모크 1건 CI 요구"
  mechanism_found:
    - path: "docs/sot/coding-principles.md"
      check: "scripts/acceptance-principles-check.sh"
      stages: ["strict", "pre-push", "ci"]
  status: "PASS"
  evidence: "Strict 계약 편입 장치의 실존·직접 실행만 PASS다. mechanism_expected에 적힌 제품 장치의 구현 완료를 주장하지 않는다."

- id: "P20"
  principle: "CI 검사는 \"0건 처리로 통과\"를 스스로 의심한다"
  mechanism_expected: "typecheck/test 스텝이 처리 건수 로그 + 최소치 미만시 FAIL"
  mechanism_found:
    - path: "docs/sot/coding-principles.md"
      check: "scripts/acceptance-principles-check.sh"
      stages: ["strict", "pre-push", "ci"]
  status: "PASS"
  evidence: "Strict 계약 편입 장치의 실존·직접 실행만 PASS다. mechanism_expected에 적힌 제품 장치의 구현 완료를 주장하지 않는다."

- id: "P21"
  principle: "데이터는 git에 넣지 않는다"
  mechanism_expected: "1MB 초과 데이터 파일 pre-commit 차단"
  mechanism_found:
    - path: "docs/sot/coding-principles.md"
      check: "scripts/acceptance-principles-check.sh"
      stages: ["strict", "pre-push", "ci"]
  status: "PASS"
  evidence: "Strict 계약 편입 장치의 실존·직접 실행만 PASS다. mechanism_expected에 적힌 제품 장치의 구현 완료를 주장하지 않는다."

- id: "P22"
  principle: "하드코딩 금지 + 자격증명은 소스에도 화면에도 없다"
  mechanism_expected: "운영상수 contracts/*.json 단일화 + JSX 렌더 대상까지 자격증명 검사"
  mechanism_found:
    - path: "docs/sot/coding-principles.md"
      check: "scripts/acceptance-principles-check.sh"
      stages: ["strict", "pre-push", "ci"]
  status: "PASS"
  evidence: "Strict 계약 편입 장치의 실존·직접 실행만 PASS다. mechanism_expected에 적힌 제품 장치의 구현 완료를 주장하지 않는다."

- id: "§1-B-1"
  principle: "셀렉터는 코드가 아니라 데이터다"
  mechanism_expected: "contracts/*/markers.json 단일화"
  mechanism_found:
    - path: "docs/sot/coding-principles.md"
      check: "scripts/acceptance-principles-check.sh"
      stages: ["strict", "pre-push", "ci"]
  status: "PASS"
  evidence: "Strict 계약 편입 장치의 실존·직접 실행만 PASS다. mechanism_expected에 적힌 제품 장치의 구현 완료를 주장하지 않는다."

- id: "§1-B-2"
  principle: "판정기는 하나다"
  mechanism_expected: "자동로그인 판정과 증거캡처 판정이 같은 함수를 사용"
  mechanism_found:
    - path: "docs/sot/coding-principles.md"
      check: "scripts/acceptance-principles-check.sh"
      stages: ["strict", "pre-push", "ci"]
  status: "PASS"
  evidence: "Strict 계약 편입 장치의 실존·직접 실행만 PASS다. mechanism_expected에 적힌 제품 장치의 구현 완료를 주장하지 않는다."

- id: "§1-B-3"
  principle: "브라우저 계층은 한 벌이다"
  mechanism_expected: "브라우저 계층을 한 벌로 강제"
  mechanism_found:
    - path: "docs/sot/coding-principles.md"
      check: "scripts/acceptance-principles-check.sh"
      stages: ["strict", "pre-push", "ci"]
  status: "PASS"
  evidence: "Strict 계약 편입 장치의 실존·직접 실행만 PASS다. mechanism_expected에 적힌 제품 장치의 구현 완료를 주장하지 않는다."

- id: "§1-B-4"
  principle: "테스트는 실캡처 스냅샷으로만"
  mechanism_expected: "실캡처 스냅샷 기반으로 판정·배선·동작을 분리 검증"
  mechanism_found:
    - path: "docs/sot/coding-principles.md"
      check: "scripts/acceptance-principles-check.sh"
      stages: ["strict", "pre-push", "ci"]
  status: "PASS"
  evidence: "Strict 계약 편입 장치의 실존·직접 실행만 PASS다. mechanism_expected에 적힌 제품 장치의 구현 완료를 주장하지 않는다."

- id: "§1-B-5"
  principle: "개입 감지는 규율이 아니라 구조로"
  mechanism_expected: "드라이버 포트 래퍼가 개입 신호 뒤 호출을 타입상 차단"
  mechanism_found:
    - path: "docs/sot/coding-principles.md"
      check: "scripts/acceptance-principles-check.sh"
      stages: ["strict", "pre-push", "ci"]
  status: "PASS"
  evidence: "Strict 계약 편입 장치의 실존·직접 실행만 PASS다. mechanism_expected에 적힌 제품 장치의 구현 완료를 주장하지 않는다."

- id: "V-1"
  principle: "검증자는 실행 산출물을 제출한다."
  mechanism_expected: "/strict §5"
  mechanism_found:
    - path: "docs/sot/coding-principles.md"
      check: "scripts/acceptance-principles-check.sh"
      stages: ["strict", "pre-push", "ci"]
  status: "PASS"
  evidence: "Strict 계약 편입 장치의 실존·직접 실행만 PASS다. mechanism_expected에 적힌 제품 장치의 구현 완료를 주장하지 않는다."

- id: "V-2"
  principle: "V1은 다른 모델 계열, V2는 재현 전담."
  mechanism_expected: "/strict §6"
  mechanism_found:
    - path: "docs/sot/coding-principles.md"
      check: "scripts/acceptance-principles-check.sh"
      stages: ["strict", "pre-push", "ci"]
  status: "PASS"
  evidence: "Strict 계약 편입 장치의 실존·직접 실행만 PASS다. mechanism_expected에 적힌 제품 장치의 구현 완료를 주장하지 않는다."

- id: "V-3"
  principle: "V3 = 라이브 1건."
  mechanism_expected: "make ship 거부"
  mechanism_found:
    - path: "docs/sot/coding-principles.md"
      check: "scripts/acceptance-principles-check.sh"
      stages: ["strict", "pre-push", "ci"]
  status: "PASS"
  evidence: "Strict 계약 편입 장치의 실존·직접 실행만 PASS다. mechanism_expected에 적힌 제품 장치의 구현 완료를 주장하지 않는다."

- id: "V-4"
  principle: "외부 모델 의견은 가설이지 합격증이 아니다."
  mechanism_expected: "문서 규약 + PR 템플릿"
  mechanism_found:
    - path: "docs/sot/coding-principles.md"
      check: "scripts/acceptance-principles-check.sh"
      stages: ["strict", "pre-push", "ci"]
  status: "PASS"
  evidence: "Strict 계약 편입 장치의 실존·직접 실행만 PASS다. mechanism_expected에 적힌 제품 장치의 구현 완료를 주장하지 않는다."

- id: "V-5"
  principle: "G·V1·V2가 계약 기준에서 갈리면 결론을 내지 않는다"
  mechanism_expected: "/strict 기존 규칙"
  mechanism_found:
    - path: "docs/sot/coding-principles.md"
      check: "scripts/acceptance-principles-check.sh"
      stages: ["strict", "pre-push", "ci"]
  status: "PASS"
  evidence: "Strict 계약 편입 장치의 실존·직접 실행만 PASS다. mechanism_expected에 적힌 제품 장치의 구현 완료를 주장하지 않는다."

- id: "P23"
  principle: "초록불은 커밋 SHA 에 귀속된다. 브랜치나 PR 에 귀속되지 않는다"
  mechanism_expected: "로컬 HEAD·원격 HEAD·CI 검사 SHA가 같고 결론이 success이고 작업트리가 깨끗할 때만 VERIFIED (scripts/verify/check-verified-sha.sh · scripts/acceptance-verified-sha.sh)"
  mechanism_found:
    - path: "docs/sot/coding-principles.md"
      check: "scripts/acceptance-principles-check.sh"
      stages: ["strict", "pre-push", "ci"]
  status: "PASS"
  evidence: "Strict 계약 편입 장치의 실존·직접 실행만 PASS다. mechanism_expected에 적힌 제품 장치의 구현 완료를 주장하지 않는다."

- id: "P24"
  principle: "복구·롤백 계열은 성공 경로가 아니라 불변조건으로 규정한다"
  mechanism_expected: "Inv1~4를 실패 주입으로 검증 (scripts/acceptance-guard-global-skill-files.sh)"
  mechanism_found:
    - path: "docs/sot/coding-principles.md"
      check: "scripts/acceptance-principles-check.sh"
      stages: ["strict", "pre-push", "ci"]
  status: "PASS"
  evidence: "Strict 계약 편입 장치의 실존·직접 실행만 PASS다. mechanism_expected에 적힌 제품 장치의 구현 완료를 주장하지 않는다."

EXIT: 0
````

→ 무엇을 시켰나: 현재 작업 브랜치의 원칙 기계 장부를 첫 줄부터 끝까지 직접 읽었다. 무엇이 나왔나: P1~P24·§1-B·V1~V5 각 항목이 Strict·pre-push·CI 연결을 선언한다. 좋은 소식인가: 원칙 검사 34/34의 대상과 범위를 원문으로 확인했다.

### 직접 읽기 원문 3/6 — 검증 명령 정본

````text
COMMAND: sed -n '1,9999p' docs/sot/verification-commands.md
START_UTC: 2026-09-05T23:42:46Z
START_KST: 2026-09-06T08:42:46+0900
HEAD: 03679010b8420d00d6f09e7a2840852ac1b8c69c
SESSION: 01a07188-a8a2-7422-94a6-a4da70cc8d22
# Valuehire v6 — 이 저장소의 실제 게이트 명령 (SOT)

최종 갱신: 2026-08-22 (P3 조용한 실패 검사 분리·현재 CI 순서 재대조)
근거: `docs/engineering/docs-sot-restructure-goal-2026-08-08.md`

## 현재 규칙

**이 저장소는 make 레포도 npm 레포도 아니다.** `Makefile`·`package.json`이 없고, `make -n red-ledger`는 `No rule to make target` 로 실패한다(2026-08-08 실행 확인). `~/.claude/skills/harness/SKILL.md`가 기본 전제하는 `make task` / `make verify` / `make ship` 은 이 저장소에 아직 없다 — 아래가 대신 쓰는 실제 명령이다.

| 게이트 | harness 스킬의 기본 명령 | 이 저장소의 실제 명령 |
|---|---|---|
| 0 — 시작 자격(RED 미해결 확인) | `make red-ledger` | `bash scripts/session-status.sh` (stdout 3번째 줄 `RED: N/M`) |
| 2 — 워크트리 파기 | `make task NAME=...` | `git worktree add worktrees/<name> -b task/<name>` |
| 4 — 검증 | `./verify.sh` | `bash verify.sh` (비밀 스캔) — CI(`verify.yml`)가 실제로 도는 검사 전체는 아래 "CI가 실제로 돌리는 것" 표가 정본이다(요약을 여기 두 번 적으면 반드시 갈라진다 — 2026-08-12 REV2-D2 실측). `scripts/acceptance-0-2.sh`는 로컬 전용(`.secret-patterns`에 실제 리터럴이 있어야 해서 CI에 못 올림, 스크립트 주석에 명시) |
| 5 — 배송 | `make ship` | 아직 스크립트 없음 — `git push -u origin task/<name>` 후 `gh pr create` 수동 실행. push 시 `hooks/pre-push`가 verify.sh + acceptance-*.sh 전량(glob)을 재실행 |
| 6 — 종료 | `make task-done NAME=...` | `git worktree remove worktrees/<name>` 수동 실행 |

### CI(`​.github/workflows/verify.yml`)가 실제로 돌리는 것

**워크플로 스텝 24개 전부**를 적는다(2026-08-12 V1 D6: 이전 판은 `bash ...` 직접 명령만 적어 인라인 본문 스텝이 목록에서 빠졌고, 운영자가 실제로 무엇이 도는지 잘못 판단할 수 있었다). 아래는 `verify.yml` 의 `- name:` 스텝 순서 그대로다(2026-08-22 P3 검사 포함).

| # | 스텝 이름 | 실행 내용 |
|---|---|---|
| 1 | 비밀 스캔 (verify.sh) | `bash verify.sh` — 추적 파일 전체 |
| 2 | Strict 원칙 정본·장부·배선 검사 | `bash scripts/acceptance-principles-check.sh` — 34개 정본 문구·장치·명시적 pre-push/CI 배선 |
| 3 | Strict 원칙 적대 fixture·500/501 경계 | `bash scripts/acceptance-principles-mutations.sh` — 정상 fixture와 반례 41건·500/501 경계 |
| 4 | Strict 전역 스킬 잠금 장치 격리 회귀 | `bash scripts/acceptance-guard-global-skill-files.sh` — lock/check/unlock/recover와 동일 UID 한계 |
| 5 | P3 조용한 실패 문법·오탐 회귀 | `scripts/acceptance-silent-failure-lint.sh` + mutation 34건 — 대소문자 확장자 전체 소스와 스테이지 blob 판정 |
| 6 | HumanSearch G1 클린룸 경계 | 인라인 8개 — `scripts/acceptance-hs-cleanroom.sh`, `scripts/acceptance-hs-cleanroom-mutations.sh`, `scripts/acceptance-hs-cleanroom-absolute-paths.sh`, `scripts/acceptance-hs-cleanroom-absolute-contexts.sh`, `scripts/acceptance-hs-cleanroom-colon-paths.sh`, `scripts/acceptance-hs-cleanroom-file-urls.sh`, `scripts/acceptance-hs-cleanroom-hook-env.sh`, `scripts/acceptance-hs-cleanroom-hook-env-mutations.sh` |
| 7 | HumanSearch G2 테스트 게이트 | 인라인 — `uv` 설치 후 `scripts/acceptance-hs-gates.sh`, `scripts/acceptance-hs-gates-mutations.sh`, `scripts/acceptance-hs-gates-antiforge.sh` (정적 ruff/mypy + pytest 수집·runtime import 증명) |
| 8 | 히스토리 전량 스캔 | 인라인 — 도달 가능한 모든 blob 을 열어 자격증명 패턴 대조 |
| 9 | 인수 검사 0-2 상시/종료상태 분리 | `bash scripts/acceptance-0-2-unreachable-content.sh` — 환경 격리·네 객체형·도구 실패·큰 객체·종료상태·훅 환경 무오염 13개 합성 사례 (AC-19) |
| 10 | 인수 검사 0-6 | `bash scripts/acceptance-0-6.sh` |
| 11 | 인수 검사 0-7 | `bash scripts/acceptance-0-7.sh` — 훅 위반 6종 시연 |
| 12 | 인수 검사 0-5 | `bash scripts/acceptance-0-5.sh` — **`main` 브랜치에서만** (`if: github.ref == 'refs/heads/main'`) |
| 13 | 억제 만료 스캔 | 인라인 — `suppressions.yaml` 의 expiry 형식·경과 |
| 14 | 강제 장치 존재 검사 | 인라인 — `hooks/pre-commit`·`pre-push` 존재·실행권한 |
| 15 | 셸 스크립트 문법 검사 | 인라인 — `git ls-files '*.sh'` 전부 `bash -n` |
| 16 | 패턴 파일 자체 실값 검사 | 인라인 — `.secret-patterns.default` 에 값 리터럴 없는지 |
| 17 | 인수 검사 hs-a3 | `bash scripts/acceptance-hs-a3.sh` — 세션 계열 자격증명 (AC-A3) |
| 18 | 데이터 노출 스캔 | `bash scripts/scan-data-exposure.sh all` — 크기·금지경로·기록·개인정보 (AC-A4) |
| 19 | 인수 검사 hs-a4 | `bash scripts/acceptance-hs-a4.sh` — 차단이 실제로 도는가 (AC-A4) |
| 20 | 인수 검사 secret-webhook-vendor | `bash scripts/acceptance-secret-webhook-vendor.sh` — 웹훅·벤더 키 (AC-S1) |
| 21 | 인수 검사 verified-sha | `bash scripts/acceptance-verified-sha.sh` — 현재 SHA 귀속 진리표(P23) |
| 22 | 인수 검사 ci-step-integrity | `bash scripts/acceptance-ci-step-integrity.sh` — 조건부·오류무시·echo 대체 차단 |
| 23 | 인수 검사 semantic-mutations | `bash scripts/acceptance-semantic-mutations.sh` — 인수 검사 무력화 5종 전량 차단 |
| 24 | 인수 검사 verify-ac-m | `bash scripts/acceptance-verify-ac-m.sh` — mechanism 명부 대조 (AC-M) |

*(1번 앞에 `actions/checkout` 이 있고 `fetch-depth: 0` 이다 — 8번이 과거 blob 을 열려면 필요하다.)*

**CI는 고정 목록이고 로컬 `pre-push`는 글로브(이름 규칙 자동 수집)다.** 그래서 새 인수 스크립트를 만들면 로컬에서는 저절로 돌지만 CI에서는 한 줄도 안 돈다 — P15③("로컬에만 있는 검사는 없는 것으로 친다")에 걸린다. **새 `scripts/acceptance-*.sh`를 추가하는 PR은 `verify.yml`과 이 표 양쪽에 자기 줄을 함께 넣어야 한다.**

### 데이터 노출 판정기 — `scripts/scan-data-exposure.sh`

후보자 데이터가 git으로 새는 세 경로를 **한 판정기**로 막는다. CI도 인수 검사도 **같은 파일을 실행**한다 — 규칙을 두 벌로 적으면 반드시 갈라진다(2026-08-12 실측: 인라인 본문 시절엔 CI 스텝에 `if: ${{ false }}`를 넣어 영구히 꺼도 로컬 방어 셋이 전부 초록이었다).

| 모드 | 무엇을 보나 |
|---|---|
| `tracked` | 지금 추적 중인 파일의 크기(1MB)·금지 경로 |
| `history` | **도달 가능한 모든 blob**의 크기·금지 경로 — 커밋 후 지운 파일의 과거 본문까지 |
| `pii` | `*.csv`·`*.tsv`·`*.sql`의 **개인정보 컬럼 조합** — 크기·확장자로는 안 잡히는 것 |
| `all` | 셋 다 (CI가 쓰는 모드) |

종료값 `0=PASS / 1=FAIL / 2=NOT_RUN`. **검사 대상 0건은 통과가 아니라 `NOT_RUN`이다**(P20).

`pii`는 오탐을 막기 위해 **두 조건을 모두** 만족해야 차단한다 — ① 개인정보 컬럼 낱말 2종 이상 ② 실제 데이터를 담은 형태(CSV는 데이터 행 1줄 이상, SQL은 `INSERT`/`VALUES`/`COPY`). 그래서 **`CREATE TABLE candidates(name, email)` 같은 스키마 정의는 통과한다** — 정상 마이그레이션까지 막으면 개발이 멈춘다.

**금지 경로 목록은 `hooks/pre-commit`과 이 판정기 두 곳에 있다**(훅은 '스테이지된 것'만 보므로 별도 코드다). 한쪽만 넓히면 조용히 갈라지므로 `scripts/acceptance-hs-a4.sh`가 두 목록의 동치를 검사한다.

## 시행 지점

이 문서 자체가 "가정 대신 실행 확인"의 산출물이다. 명령이 바뀌면(예: `Makefile`이 나중에 생기면) 이 표를 그 시점에 다시 실행해서 갱신한다 — 표를 먼저 고치고 나중에 확인하지 않는다.

## 비범위 / 한계

- `main` 브랜치 GitHub 보호 규칙의 실제 활성화 여부는 확인하지 않았다(`docs/sot/git-workflow.md` 한계와 동일).
- 이 표는 2026-08-22 실행 결과의 스냅샷이다. 스크립트가 추가/삭제되면 다시 확인해야 한다.
EXIT: 0
````

→ 무엇을 시켰나: 현재 저장소가 실제로 쓰는 검증 명령 정본을 처음부터 끝까지 읽었다. 무엇이 나왔나: CI 검증은 24개로 고정되고 0-5는 main 브랜치 전용이라고 이미 적혀 있다. 좋은 소식인가: AC-PR의 23 success + 1 SKIPPED는 사후 숫자 축소가 아니라 기존 24개 정의의 이벤트별 결과다.

### 직접 읽기 원문 4/6 — GitHub verify 워크플로

````text
COMMAND: sed -n '1,9999p' .github/workflows/verify.yml
START_UTC: 2026-09-05T23:43:26Z
START_KST: 2026-09-06T08:43:26+0900
HEAD: 03679010b8420d00d6f09e7a2840852ac1b8c69c
SESSION: 01a07188-a8a2-7422-94a6-a4da70cc8d22
name: verify

# "CI 초록 전까지 완료 없음"을 시스템으로 강제한다.
# 로컬 검증은 실행자가 주장하는 것이고, 이 워크플로우는 GitHub이 판정하는 것이다.
on:
  push:
    branches: ["**"]
  pull_request:
  workflow_dispatch:

permissions:
  contents: read

jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0   # 아래 "히스토리 전량 스캔" 스텝이 과거 커밋의 blob까지 열어보는 데 필요
          # 이 job 은 읽기만 한다. 기본값(true)은 인증 토큰을 러너의 git 설정에 남겨
          # 뒤따르는 스크립트가 인증된 git 명령을 쓸 수 있게 만든다 — 여기서는 필요 없다.
          persist-credentials: false

      - name: 비밀 스캔 (verify.sh)
        # 패턴은 커밋된 .secret-patterns.default 를 쓴다.
        # 실제 비밀값은 CI에 올리지 않는다 — 저장소 시크릿에 넣는 것도 유출 경로를 늘리는 일이다.
        # 로컬 전용 .secret-patterns 는 gitignore 되어 여기 없다.
        run: bash verify.sh

      - name: Strict 원칙 정본·장부·배선 검사
        run: bash scripts/verify/run-acceptance.sh scripts/acceptance-principles-check.sh

      - name: Strict 원칙 적대 fixture·500/501 경계
        run: bash scripts/verify/run-acceptance.sh scripts/acceptance-principles-mutations.sh

      - name: Strict 전역 스킬 잠금 장치 격리 회귀
        run: bash scripts/verify/run-acceptance.sh scripts/acceptance-guard-global-skill-files.sh

      - name: P3 조용한 실패 문법·오탐 회귀
        run: |
          bash scripts/verify/run-acceptance.sh scripts/acceptance-silent-failure-lint.sh
          bash scripts/verify/run-acceptance.sh scripts/acceptance-silent-failure-lint-mutations.sh

      - name: HumanSearch G1 클린룸 경계
        run: |
          bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-cleanroom.sh
          bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-cleanroom-mutations.sh
          bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-cleanroom-absolute-paths.sh
          bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-cleanroom-absolute-contexts.sh
          bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-cleanroom-colon-paths.sh
          bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-cleanroom-file-urls.sh
          bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-cleanroom-hook-env.sh
          bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-cleanroom-hook-env-mutations.sh

      - name: HumanSearch G2 테스트 게이트 (정적·단위 + runtime import 증명)
        # uv 버전은 계약 C-8(0.11.3)에 고정. Python 3.14.1은 uv가 .python-version으로 내려받는다.
        run: |
          # 설치 여부만 보면 러너에 이미 있는 다른 버전을 그대로 쓴다 — 그건 버전
          # "출력"이지 "고정"이 아니다. 실제 값을 계약(C-8)과 대조하고 어긋나면 실패시킨다.
          required=0.11.3
          actual=$(uv --version 2>/dev/null | awk '{print $2}')
          if [ "$actual" != "$required" ]; then
            pipx install --force "uv==$required"
            actual=$(uv --version 2>/dev/null | awk '{print $2}')
          fi
          if [ "$actual" != "$required" ]; then
            echo "FAIL: uv 버전 불일치 — expected=$required actual=${actual:-없음}"
            exit 1
          fi
          echo "PASS: uv $actual (계약 C-8 고정)"
          bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-gates.sh
          bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-gates-mutations.sh
          bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-gates-antiforge.sh

      - name: 히스토리 전량 스캔 (도달 가능한 모든 blob)
        # verify.sh는 현재 체크아웃의 추적 파일만 본다. 과거 커밋에 들어갔다가 지워진 비밀은
        # 그것만으로는 잡히지 않으므로, reflog 포함 도달 가능한 모든 blob을 직접 열어 검사한다.
        run: |
          set -o pipefail
          CLEAN=$(mktemp)
          tr -d '\r' < .secret-patterns.default | grep -vE '^[[:space:]]*(#|$)' > "$CLEAN"
          [ -s "$CLEAN" ] || { echo "FAIL: 유효 패턴 0개"; exit 2; }

          # fail-closed: git이 실패해 객체 목록이 비면 "0건 통과"가 아니라 오류다.
          OBJS=$(mktemp)
          if ! git rev-list --all --reflog --objects > "$OBJS"; then
            echo "FAIL: git rev-list 실패 — 히스토리를 읽지 못했다(스캔 무효)"; exit 2
          fi
          count=$(awk '{print $1}' "$OBJS" | sort -u | wc -l)
          if [ "$count" -lt 2 ]; then
            echo "FAIL: 도달 가능 객체가 ${count}개 — 저장소를 제대로 읽지 못했다(스캔 무효)"; exit 2
          fi
          echo "스캔 대상 객체: ${count}개"

          hit=0; blobs=0
          while IFS= read -r sha; do
            [ -z "$sha" ] && continue
            [ "$(git cat-file -t "$sha" 2>/dev/null)" = blob ] || continue
            blobs=$((blobs+1))
            if git cat-file blob "$sha" 2>/dev/null | grep -qEif "$CLEAN"; then
              echo "FAIL: 히스토리 blob에 자격증명 패턴 매치: $sha"
              awk -v s="$sha" '$1==s {print "  경로: "$2}' "$OBJS"
              hit=1
            fi
          done < <(awk '{print $1}' "$OBJS" | sort -u)
          if [ "$blobs" -eq 0 ]; then
            echo "FAIL: blob을 한 개도 읽지 못했다(스캔 무효)"; exit 2
          fi
          [ "$hit" -eq 0 ] && echo "PASS: 히스토리 전량 blob 스캔 0건 (blob ${blobs}개 검사)"
          exit $hit

      - name: 인수 검사 0-2 상시 내용 검사와 종료상태 분리 (AC-19)
        # 실제 로컬 리터럴은 CI에 올리지 않는다. 합성 저장소와 합성 값으로 동일 판정기를 실행해
        # 환경 격리·네 객체형·fsck/cat-file 실패·큰 객체·종료상태·훅 환경 무오염 13건을 증명한다.
        run: bash scripts/verify/run-acceptance.sh scripts/acceptance-0-2-unreachable-content.sh

      - name: 인수 검사 0-6 (가짜 검증 스크립트 0건)
        run: bash scripts/verify/run-acceptance.sh scripts/acceptance-0-6.sh

      # ↓ 아래 3개는 pre-push 에서 CI 로 이관된 검사다(2026-08-07).
      #   pre-push 는 "이 push 가 안전한가"만 판정하며, 저장소 위생·메타 검사는 여기서 돈다.
      #   hooks/pre-push 가 이 이름들이 이 파일에 실제로 있는지 확인한다 — 지우면 push 가 막힌다.

      # acceptance-0-2 는 여기서 돌리지 않는다. 그 검사는 "로컬 전용 .secret-patterns 에
      # 적힌 실제 리터럴이 히스토리에서 제거됐는가"를 보는데, CI 에는 그 파일이 없다.
      # 기본 패턴으로 대체하면 패턴 파일 자신이 매칭돼 상시 실패한다(실측: run 31176518944,
      # blob 09b233e = .secret-patterns.default 자신). CI 에서의 등가물은 위의
      # "히스토리 전량 스캔" 스텝이며, hooks/pre-push 가 그 스텝의 존재를 확인한다.

      - name: 인수 검사 0-7 (훅이 위반 6종을 실제로 차단하는가)
        run: bash scripts/verify/run-acceptance.sh scripts/acceptance-0-7.sh

      - name: 인수 검사 0-5 (push · CI 연결)
        # origin/main==main 을 검사하므로 main 참조가 유효한 경우에만 의미가 있다.
        if: github.ref == 'refs/heads/main'
        run: bash scripts/verify/run-acceptance.sh scripts/acceptance-0-5.sh

      - name: 억제 만료 스캔 (suppressions.yaml)
        # pre-commit 의 expiry 검사는 suppressions.yaml 이 '스테이징된 커밋'에서만 돈다.
        # 이미 커밋된 억제가 시간이 지나 썩는 것은 아무도 보지 않는다 — 이 게이트가
        # 막겠다고 인용한 98d923f(35일 방치) 시나리오 그 자체다. 그래서 매 push 마다 훑는다.
        run: |
          [ -f suppressions.yaml ] || { echo "PASS: 억제 없음"; exit 0; }
          today=$(date +%Y-%m-%d); fail=0; n=0
          while IFS= read -r e; do
            n=$((n+1))
            if ! printf '%s' "$e" | grep -qE '^[0-9]{4}-(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])$'; then
              echo "FAIL: expiry 형식 오류 '${e}' — 만료를 판정할 수 없는 억제는 무기한 억제다"; fail=1
            elif [ "$e" \< "$today" ]; then
              echo "FAIL: 만료된 억제 (expiry $e < 오늘 $today) — 유예 기한이 지났다"; fail=1
            fi
          done < <(awk '/^ *expiry:/{sub(/^ *expiry: */,""); gsub(/["\x27]/,""); print}' suppressions.yaml)
          nc=$(awk '/^- *check:/{c++} END{print c+0}' suppressions.yaml)
          if [ "$nc" -ne "$n" ]; then
            echo "FAIL: 억제 ${nc}건 중 expiry 가 ${n}건뿐"; fail=1
          fi
          [ "$fail" -eq 0 ] && echo "PASS: 억제 ${nc}건 전부 유효 기한 내"
          exit $fail

      - name: 강제 장치 존재 검사 (hooks/)
        # core.hooksPath 는 저장소 전역 config 이고 hooks/ 는 브랜치 내용이다.
        # hooks/ 가 없는 브랜치에서는 로컬 강제가 조용히 0개가 되며 로컬에서는 막을 수
        # 없다. 원격에서라도 막는다 — 이것이 P15③ 이 말하는 "판정 권한은 CI에 있다"의 실체다.
        run: |
          fail=0
          for h in hooks/pre-commit hooks/pre-push; do
            if [ ! -f "$h" ]; then echo "FAIL: $h 없음 — 이 브랜치엔 로컬 강제 장치가 없다"; fail=1
            elif [ ! -x "$h" ]; then echo "FAIL: $h 실행 권한 없음 — 훅은 존재해도 조용히 통과한다"; fail=1
            fi
          done
          [ "$fail" -eq 0 ] && echo "PASS: 훅 2종 존재·실행가능"
          exit $fail

      - name: 셸 스크립트 문법 검사
        # `*.sh` 글로브만 보면 hooks/pre-commit·pre-push 가 빠진다(확장자가 없다).
        # 강제 장치 본인이 문법 검사 밖에 있으면, 훅이 깨진 채로도 이 스텝은 초록이다.
        run: |
          fail=0
          n=0
          while IFS= read -r -d '' f; do
            n=$((n+1))
            bash -n "$f" || { echo "syntax error: $f"; fail=1; }
          done < <(git ls-files -z '*.sh' hooks/pre-commit hooks/pre-push)
          if [ "$n" -lt 2 ]; then
            echo "FAIL: 문법 검사 대상이 ${n}개 — 대상 0개는 합격이 아니다"
            exit 1
          fi
          echo "PASS: 셸 파일 ${n}개 문법 검사"
          exit $fail

      - name: 패턴 파일 자체에 실제 비밀이 없는지 (자기 오염 방지)
        run: |
          # .secret-patterns.default 는 "모양"만 담아야 한다. 값처럼 보이는 긴 리터럴이 있으면 실패.
          if grep -nE "^[^#]*=[A-Za-z0-9]{8,}[[:space:]]*$" .secret-patterns.default; then
            echo "FAIL: 기본 패턴 파일에 실제 값처럼 보이는 리터럴이 있음"
            exit 1
          fi
          echo "PASS: 기본 패턴 파일에 실값 없음"

      - name: 인수 검사 hs-a3 (세션 계열 자격증명 탐지)
        run: bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-a3.sh
      - name: 데이터 노출 스캔 (크기 · 금지경로 · 기록 · 개인정보 내용)
        # 판정 본문은 scripts/scan-data-exposure.sh 한 곳에 있다. CI 도 인수검사도
        # **같은 파일을 실행**한다 — 규칙을 두 벌로 적으면 반드시 갈라진다.
        # 2026-08-12 V1 적대검증 D4: 인라인 본문 시절엔 이 스텝에 `if: ${{ false }}` 를
        # 넣어 영구히 꺼도 인수검사·pre-commit·pre-push 가 전부 초록이었다.
        # all = tracked(현재 파일) + history(도달 가능한 모든 blob · D1) + pii(csv/sql 내용 · D2)
        run: bash scripts/scan-data-exposure.sh all

      - name: 인수 검사 hs-a4 (대용량·산출물 차단이 실제로 도는가)
        run: bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-a4.sh

      - name: 인수 검사 secret-webhook-vendor (웹훅·벤더 키 탐지 · AC-S1)
        # 로컬 pre-push 는 acceptance-*.sh 를 글로브로 전량 실행하지만 CI 는 고정 목록이다.
        # 여기 등록하지 않으면 이 검사는 '로컬에만 있는 검사'가 되고, P15③ 은 그것을
        # 없는 것으로 친다(이 파일 111행 주석의 "판정 권한은 CI에 있다"와 같은 근거).
        run: bash scripts/verify/run-acceptance.sh scripts/acceptance-secret-webhook-vendor.sh

      - name: 인수 검사 verified-sha (초록불이 SHA 에 귀속되는가 · P23)
        # "CI 통과했습니다"는 어느 커밋에 대해 통과했는지를 말하지 않는다. 원격 HEAD 와
        # 초록불이 붙은 SHA 와 로컬 HEAD 가 다르면 그 초록불은 지금 머지하려는 코드의
        # 것이 아니다. 여기서는 판정기의 진리표(9종)와 fail-closed 를 검증한다.
        run: bash scripts/verify/run-acceptance.sh scripts/acceptance-verified-sha.sh

      - name: 인수 검사 ci-step-integrity (스텝을 조용히 끄지 못하는가)
        # pre-push 는 워크플로를 문자열로 훑어 `if: false` 만 잡는다. `if: ${{ false }}`,
        # 항상-거짓 조건, `continue-on-error: true` 는 그대로 통과했다(2026-08-12 V1 D4:
        # 데이터 노출 검사 스텝을 영구히 꺼도 로컬 검사가 전부 초록이었다).
        # 이 검사는 워크플로를 실제 YAML 로 파싱해 조건부·오류무시 스텝을 구조로 막는다.
        run: bash scripts/verify/run-acceptance.sh scripts/acceptance-ci-step-integrity.sh

      - name: 인수 검사 semantic-mutations (검사를 껐을 때 반드시 빨개지는가)
        # 2026-08-21: acceptance-hs-a4.sh 본문을 `exit 0` 으로 바꿔도 CI 가 초록이었다.
        # CI 가 종료값만 봤기 때문이다 — 종료값 0 은 "통과했다"와 "아무것도 안 했다"를
        # 구분하지 못한다. 위 스텝들이 전부 scripts/verify/run-acceptance.sh 를 거치는
        # 이유이며, 이 검사는 그 래퍼가 무력화 5종(exit 0 · true · no-op · 빈 파일 ·
        # 출력만)을 인수 검사 전량에 대해 실제로 막는지 격리 사본으로 증명한다.
        run: bash scripts/verify/run-acceptance.sh scripts/acceptance-semantic-mutations.sh

      - name: 인수 검사 verify-ac-m (mechanism 명부 대조 · AC-M)
        # 명부(docs/sot/mechanism-registry.yaml)와 실제 검사 장치의 일치를 강제한다.
        # 검사기 1벌(scripts/verify/check-mechanism-registry.sh)을 로컬 pre-push
        # 글로브와 CI 가 같은 인수 스크립트로 실행한다 (판정기 2벌 금지 · P16).
        run: bash scripts/verify/run-acceptance.sh scripts/acceptance-verify-ac-m.sh
EXIT: 0
````

→ 무엇을 시켰나: GitHub verify 워크플로를 처음부터 끝까지 직접 읽었다. 무엇이 나왔나: push와 pull_request를 모두 받는 단일 job, 이름 있는 검증 24개, 그리고 0-5에만 main ref 조건이 있다. 좋은 소식인가: PR과 main을 서로 다른 이벤트 계약으로 채점해야 하는 구조가 원문으로 확인됐다.

### 직접 읽기 원문 5/6 — 0-5 배송 검사

````text
COMMAND: sed -n '1,9999p' scripts/acceptance-0-5.sh
START_UTC: 2026-09-05T23:44:08Z
START_KST: 2026-09-06T08:44:08+0900
HEAD: 03679010b8420d00d6f09e7a2840852ac1b8c69c
SESSION: 01a07188-a8a2-7422-94a6-a4da70cc8d22
#!/usr/bin/env bash
# 0-5 인수 스크립트 — push + CI 연결.
# 실제 비밀 리터럴을 이 파일에 넣지 않는다. 로컬 전용 .secret-patterns에 의존하지도 않는다
# (CI에서도 그대로 돌아야 하므로). 검증 대상은 "CI가 비밀 스캔을 강제하는가"다.
set -euo pipefail
unset GIT_DIR GIT_INDEX_FILE GIT_OBJECT_DIRECTORY GIT_WORK_TREE GIT_COMMON_DIR GIT_ALTERNATE_OBJECT_DIRECTORIES
fail=0

WF=.github/workflows/verify.yml

# 1. 워크플로우 파일이 존재하고 추적되는가
if [ ! -f "$WF" ]; then echo "FAIL: $WF 없음"; fail=1
elif ! git ls-files --error-unmatch "$WF" >/dev/null 2>&1; then echo "FAIL: $WF 가 git 추적 대상이 아님"; fail=1; fi

# 2. 워크플로우가 실제 검증 명령을 호출하는가 (이름만 있는 껍데기 금지)
if [ -f "$WF" ]; then
  grep -q 'verify\.sh' "$WF" || { echo "FAIL: 워크플로우가 verify.sh를 호출하지 않음"; fail=1; }
  grep -q 'acceptance-0-6\.sh' "$WF" || { echo "FAIL: 워크플로우가 acceptance-0-6.sh를 호출하지 않음"; fail=1; }
  grep -qE 'on:|push:' "$WF" || { echo "FAIL: 워크플로우에 트리거 정의 없음"; fail=1; }
fi

# 3. 커밋되는 기본 패턴 파일이 존재하고, 그 자체엔 실제 비밀이 없어야 한다
DEF=.secret-patterns.default
if [ ! -s "$DEF" ]; then echo "FAIL: $DEF 없음/빈 파일 — CI가 패턴 없이 돌 수 없다"; fail=1
else
  git ls-files --error-unmatch "$DEF" >/dev/null 2>&1 || { echo "FAIL: $DEF 가 추적되지 않음(CI에서 안 보임)"; fail=1; }
  # 로컬 실제 패턴이 있으면, 기본 파일이 그 실제 리터럴을 품고 있지 않은지 확인
  if [ -s .secret-patterns ]; then
    while IFS= read -r lit; do
      [ -z "$lit" ] && continue
      if grep -qF "$lit" "$DEF"; then echo "FAIL: $DEF 에 실제 비밀 리터럴이 들어있음"; fail=1; fi
    done < .secret-patterns
  fi
fi

# 4. 로컬 전용 패턴 파일 없이도(=CI 환경 재현) verify.sh가 동작해야 한다
#    실저장소를 건드리지 않도록 격리 클론에서 검사한다.
sandbox=$(mktemp -d)
cleanup() { rm -rf -- "$sandbox"; }
trap 'cleanup' EXIT
trap 'cleanup; trap - EXIT; exit 143' TERM
trap 'cleanup; trap - EXIT; exit 130' INT
trap 'cleanup; trap - EXIT; exit 129' HUP
set +e
git clone -q --no-local . "$sandbox/repo" 2>/dev/null
clone_rc=$?
if [ "$clone_rc" -eq 0 ]; then
  if [ -e "$sandbox/repo/.secret-patterns" ]; then
    echo "FAIL: 클론에 로컬 전용 패턴 파일이 따라옴 — gitignore 되지 않았다"; fail=1
  fi
  ( cd "$sandbox/repo" && bash verify.sh >/dev/null 2>&1 )
  rc=$?
  if [ "$rc" -ne 0 ]; then
    echo "FAIL: 로컬 패턴 파일 없는 환경(CI 재현)에서 verify.sh exit=$rc (기대 0)"
    fail=1
  fi
  # 카나리: CI 환경에서도 검출력이 살아있는가 (기본 패턴이 잡아야 하는 형태를 심는다)
  # 카나리 문자열은 조립해서 만든다 — 이 스크립트 자신이 스캔에 걸리지 않도록(자기 매칭 방지).
  # V2 지적 반영: 심기(plant) 단계와 검출 단계를 분리한다. &&로 묶으면 git add 실패까지
  # "스캐너가 잡았다"로 오독돼, 카나리가 한 번도 안 돌아도 통과하는 조용한 위양성이 된다.
  ( cd "$sandbox/repo" && printf 'CHATGPT_%s=hunter2example\n' 'PASSWORD' > leak-canary.env.txt )
  plant_rc=$?
  ( cd "$sandbox/repo" && git add leak-canary.env.txt )
  add_rc=$?
  ( cd "$sandbox/repo" && git ls-files --error-unmatch leak-canary.env.txt >/dev/null 2>&1 )
  staged_rc=$?
  if [ "$plant_rc" -ne 0 ] || [ "$add_rc" -ne 0 ] || [ "$staged_rc" -ne 0 ]; then
    echo "FAIL: 카나리를 심지 못함(plant=$plant_rc add=$add_rc staged=$staged_rc) — 검출력 검증 자체가 무효"
    fail=1
  else
    ( cd "$sandbox/repo" && bash verify.sh >/dev/null 2>&1 )
    if [ $? -eq 0 ]; then
      echo "FAIL: 기본 패턴이 명백한 자격증명 대입문을 못 잡음 — CI 스캔이 무의미"
      fail=1
    fi
  fi
else
  echo "FAIL: 격리 클론 생성 실패(exit=$clone_rc) — 4번 검증 불가"; fail=1
fi
set -e
cleanup
trap - EXIT TERM INT HUP

# 5. 배송 — origin/main이 로컬 main과 같은 커밋을 가리켜야 한다(push 완료)
git fetch -q origin 2>/dev/null || true
local_main=$(git rev-parse main 2>/dev/null || echo none)
remote_main=$(git rev-parse origin/main 2>/dev/null || echo none)
if [ "$local_main" != "$remote_main" ]; then
  echo "FAIL: origin/main($remote_main) != main($local_main) — push 미완료"
  fail=1
fi

# 6. 원격에 비밀이 올라가지 않았는지 — 원격 브랜치 트리 전수 스캔(로컬 패턴 있을 때만)
if [ -s .secret-patterns ] && [ "$remote_main" != none ]; then
  if git grep -lIf .secret-patterns "$remote_main" -- 2>/dev/null | head -1 | grep -q .; then
    echo "FAIL: origin/main 트리에 비밀 패턴 매치 — 원격 유출"
    fail=1
  fi
fi

[ "$fail" -eq 0 ] && echo "PASS: 0-5 완료 — CI 비밀스캔 강제 + push 완료 + 원격 트리 비밀 0건" || exit 1
EXIT: 0
````

→ 무엇을 시켰나: 0-5 검사 스크립트를 처음부터 끝까지 직접 읽었다. 무엇이 나왔나: 현재 PR SHA가 아니라 local main·origin/main 일치와 원격 main 트리를 판정한다. 좋은 소식인가: 조건을 제거해 PR에서 실행하면 가짜 PASS나 무관한 FAIL이 생긴다는 반례의 원인이 코드 원문과 일치한다.

### 직접 읽기 원문 6/6 — CI 스텝 무력화 검사기

````text
COMMAND: sed -n '1,9999p' scripts/verify/check-ci-step-integrity.sh
START_UTC: 2026-09-05T23:44:50Z
START_KST: 2026-09-06T08:44:50+0900
HEAD: 03679010b8420d00d6f09e7a2840852ac1b8c69c
SESSION: 01a07188-a8a2-7422-94a6-a4da70cc8d22
#!/usr/bin/env bash
# check-ci-step-integrity.sh — 서버 자동검사의 스텝을 조용히 끄지 못하게 한다.
#
# 왜 필요한가:
#   hooks/pre-push 는 워크플로를 문자열로 훑어 `if: false` 만 잡는다. 그래서
#   `if: ${{ false }}`, `if: github.event_name == 'never'`, `continue-on-error: true`
#   같은 변형은 그대로 통과했다(2026-08-12 V1 D4 실측: 데이터 노출 검사 스텝을 영구히
#   꺼도 인수검사·pre-commit·pre-push 가 전부 초록이었다).
#   문자열 규칙은 하나 추가할 때마다 우회가 하나씩 는다. 그래서 여기서는 워크플로를
#   실제 YAML 로 파싱해 "조건이 붙었는가 / 실패를 무시하는가"를 구조로 본다.
#
# 계약: verify 워크플로의 모든 job·step 은 조건 없이 실행되고 실패를 전파해야 한다.
#       정당한 예외는 이 파일에 이유와 함께 적고, 적히지 않은 예외는 전부 불합격이다.
#
# 막지 못하는 것: 스텝 자체를 삭제하는 것. 그것은 mechanism-registry 와 pre-push 의
#       실행줄 검사가 맡는다. 여기서 다 막는다고 주장하지 않는다.
set -uo pipefail

WORKFLOW="${1:-.github/workflows/verify.yml}"
if [ ! -f "$WORKFLOW" ]; then
  echo "FAIL: 워크플로 파일이 없다 — $WORKFLOW (fail-closed)"
  echo "CHECKED: 0"
  exit 2
fi

ruby -rpsych -rdate -e '
workflow_path = ARGV[0]

# 이름으로 지정한 예외. 이유 없이 늘리지 않는다.
ALLOWED_STEP_IF = {
  "인수 검사 0-5 (push · CI 연결)" =>
    "origin/main==main 을 보는 검사라 main push 에서만 의미가 있다. PR 실행에서 요구하면 상시 실패한다.",
}

begin
  doc = Psych.safe_load(File.read(workflow_path), aliases: true, permitted_classes: [Date, Time])
rescue Psych::Exception => e
  puts "FAIL: 워크플로 파싱 실패 — #{e.message.lines.first.to_s.strip}"
  puts "CHECKED: 0"
  exit 2
end

errors = []
checked = 0

jobs = doc.is_a?(Hash) ? doc["jobs"] : nil
unless jobs.is_a?(Hash) && !jobs.empty?
  puts "FAIL: jobs 를 읽지 못했다 — 검사 대상 0개는 합격이 아니다"
  puts "CHECKED: 0"
  exit 2
end

jobs.each do |job_name, job|
  next unless job.is_a?(Hash)
  checked += 1
  errors << "JOB_CONDITIONAL: jobs.#{job_name} 에 if 가 있다 — job 을 통째로 끌 수 있다" if job.key?("if")
  errors << "JOB_CONTINUE_ON_ERROR: jobs.#{job_name} 이 실패를 무시한다" if job["continue-on-error"]

  steps = job["steps"]
  unless steps.is_a?(Array) && !steps.empty?
    errors << "JOB_NO_STEPS: jobs.#{job_name} 에 스텝이 없다 — 빈 job 은 항상 초록이다"
    next
  end

  steps.each_with_index do |step, i|
    next unless step.is_a?(Hash)
    checked += 1
    label = step["name"] || step["uses"] || "steps[#{i}]"

    if step.key?("if")
      reason = ALLOWED_STEP_IF[step["name"]]
      if reason
        puts "ALLOWED: #{label} — if 허용 (#{reason})"
      else
        errors << "STEP_CONDITIONAL: jobs.#{job_name}.#{label} 에 if 가 있다 (#{step["if"].inspect}) — " \
                  "조건부 스텝은 조건이 거짓이면 실행되지 않고도 초록이다"
      end
    end

    if step["continue-on-error"]
      errors << "STEP_CONTINUE_ON_ERROR: jobs.#{job_name}.#{label} 이 실패를 무시한다 — " \
                "빨개져야 할 검사가 초록으로 남는다"
    end

    run = step["run"]
    if run.is_a?(String)
      # 실행처럼 보이지만 실행하지 않는 형태.
      run.each_line do |line|
        stripped = line.strip
        next if stripped.empty? || stripped.start_with?("#")
        if stripped =~ /\Aecho\s+(bash|sh)\s+\S+\.sh/
          errors << "STEP_ECHO_ONLY: jobs.#{job_name}.#{label} 의 `#{stripped}` 는 실행이 아니라 출력이다"
        end
        if stripped =~ /\A(bash|sh)\s+-n\s+\S+\.sh/
          errors << "STEP_SYNTAX_ONLY: jobs.#{job_name}.#{label} 의 `#{stripped}` 는 문법 검사일 뿐 실행이 아니다"
        end
      end
    end
  end
end

if errors.empty?
  puts "PASS: 조건부·오류무시 스텝 없음 (job·step #{checked}개 검사)"
  puts "CHECKED: #{checked}"
  exit 0
else
  errors.each { |e| puts "FAIL: #{e}" }
  puts "CHECKED: #{checked}"
  exit 1
end
' "$WORKFLOW"
EXIT: 0
````

→ 무엇을 시켰나: CI 스텝 무력화 검사기를 처음부터 끝까지 직접 읽었다. 무엇이 나왔나: 일반 조건부 스텝은 실패시키되 0-5의 정확한 이름에 main 전용 이유를 붙여 허용한다. 좋은 소식인가: SKIPPED 예외의 사전 정의와 다른 조건·오류무시·echo-only 차단 경계를 원문으로 확인했다.

## 새 AC 적대 검증 로그

### V1 — Claude 격리 적대검증 원문

- 실행: `env -u ANTHROPIC_API_KEY claude -p --safe-mode --restricted --permission-mode plan --output-format json --session-id 65467d8e-a97c-4161-9662-41320c7e35db`.
- 시각: 2026-09-06 08:47:19~08:57:03 KST.
- 종료값: 0.
- 실행 신원: Claude Code `2.1.261`; 세션 `65467d8e-a97c-4161-9662-41320c7e35db`; 모델 `claude-opus-5`; web search/fetch 0; permission denial 0.
- stdout JSON: `stop_reason=end_turn`, `terminal_reason=completed`, `duration_api_ms=583149`, `is_error=false`, `subtype=success`.
- 판정문 SHA-256: `9c4670b250324a1ec2ff241af52bde3787d150975bec0aa832279a4acb9857a1`; 277줄; `VERDICT:` 블록 1개.

````text
VERDICT: FAIL

## 결론

먼저 이번 판정의 한계를 밝힙니다. 저는 빈 임시 폴더에서 문서만 읽었습니다. 저장소도 없고, 명령을 실행할 도구도 없습니다. 그래서 아래 판정은 **제출된 diff 안의 기록끼리 서로 맞는지, 그리고 오너가 준 합격 조건과 맞는지**만 따진 결과입니다. 서버 기록(GitHub Actions 실행 결과)을 제가 직접 다시 조회한 것은 하나도 없습니다. 재실행이 필요한 항목은 마지막에 명령으로 적었습니다.

판정은 이렇습니다.

**첫째, 작성자가 붙인 `PR_GATE: PASS`는 그대로 받을 수 없습니다.** 오너가 준 합격 조건 7개 중 6번은 "작업 폴더에 고치다 만 파일이 없어야 한다"입니다. 그런데 작성자가 합격 근거로 붙인 바로 그 증거 안에 고치다 만 파일 1개가 찍혀 있습니다. 작성자는 "그건 지금 쓰고 있는 이 문서일 뿐"이라고 적었지만, 조건에 그런 예외는 없습니다. 조건 6이 실제로 성립했던 시각은 08:29:12 한 번뿐이고, 합격을 선언하는 시점의 상태는 조건을 벗어나 있습니다. 시점을 밝히지 않은 채 쓴 `PR_GATE: PASS` 한 줄은 그 차이를 지웁니다.

**둘째, 지금 제출된 이 문서 변경분 자체는 서버 검사를 한 번도 받지 않았습니다.** 작성자도 이 점은 인정했고, 그래서 전체 판정을 FAIL로 적었습니다. 저도 전체 FAIL에는 동의합니다. 다만 **작성자가 댄 이유는 과장입니다.** 작성자는 "먼저 병합돼 버려서 이제는 달성할 수 없다"고 썼는데, 사실은 아직 커밋도 하지 않았기 때문에 검사 결과가 없는 것입니다. 새 가지를 따서 새 요청을 올리면 같은 검사를 그대로 받을 수 있습니다. "불가능"이 아니라 "아직 안 했음"입니다.

**셋째, 반대로 작성자가 스스로에게 불리하게 쓴 두 가지 공격 지점은, 제가 깨려고 시도했지만 깨지지 않았습니다.** ① 건너뛴 검사 1개를 "원래부터 건너뛰기로 돼 있었다"고 한 주장은 사후 변명이 아니라 사실이었습니다. 검사 목록 문서, 워크플로 조건문, 독립 검사기의 예외 목록 세 곳에 이번 작업 이전부터 적혀 있습니다. ② 그 검사 1개를 요청 단계에서 돌리지 않아도 확인 사슬은 닫힙니다. 그 검사가 요청 단계에서 유일하게 담당하던 항목들이 다른 검사 두 개에 이미 중복으로 들어가 있기 때문입니다. 다만 작성자가 쓴 "이 검사의 합격/불합격은 요청 머리 커밋과 무관하다"는 문장은 절반만 맞습니다. 불합격 경로만 무관하고, 합격 경로에는 요청 머리 커밋에 대한 검사가 실제로 들어 있습니다.

**넷째, `MAIN_CI: PASS`는 숫자와 커밋 번호 기준으로는 조건을 채웠습니다.** 다만 "같은 24개"라는 조건의 '같은'을 증명하는 자료(스텝 이름 목록)가 본선 실행에만 빠져 있습니다. 요청 실행에는 건너뛴 스텝 이름이 붙어 있는데 본선 실행에는 이름이 하나도 없습니다. 조건부로만 인정합니다.

**다섯째, 별도로 발견한 실질 결함이 있습니다.** 합격 근거로 붙은 명령줄들이 실제로 실행 가능한 명령이 아니라 요약 라벨입니다(`gh run view 33895262180 AC-PR aggregate`, `temp clone; checkout ...`). 제3자가 23/1/0이라는 숫자를 다시 만들어낼 수 없습니다. 그리고 이 저장소 스스로 "확인 기준은 실행 가능한 명령이다"를 원칙 2번으로 못 박고 있습니다. 또 이번에 1,387줄이 새로 추가됐는데, 안전 확인 명령은 그 추가 **이전** 시각에만 실행됐습니다. 추가된 내용에는 다른 파일에서 통째로 옮겨온 자격증명 형태의 예시 문자열이 들어 있습니다. 다시 돌려봐야 합니다.

---

## 판단 근거

**어떤 해석을 택했는가.** 오너가 준 AC-PR을 "특정 커밋 하나에 대한 서버 실행 결과 + 판정 시점의 로컬 상태"를 함께 요구하는 조건으로 읽었습니다. 조건 1~4는 실행 결과라 시간이 지나도 변하지 않고, 조건 5~6은 판정 시점의 로컬 상태라 시간에 따라 변합니다. 이 구분을 세운 것이 판정의 핵심입니다.

**버린 해석 1 — "조건 6은 서버 실행 시점 기준이다".** 이렇게 읽으면 작성자의 `PR_GATE: PASS`가 그대로 성립합니다. 버린 이유는, 이 저장소의 원칙 P23이 "로컬 머리 = 원격 머리 = 검사받은 커밋이 모두 같고 **작업트리가 깨끗할 때만** VERIFIED"라고 적고 있고, 그 판정기(`check-verified-sha.sh`)가 **호출 시점의** `git status`를 읽기 때문입니다. 즉 이 저장소의 정본은 조건 6을 판정 시점 기준으로 정의합니다. 틀리면 깨지는 것: 만약 `check-verified-sha.sh`가 실제로는 특정 커밋 시점의 상태를 재구성해 판정한다면 제 지적 D1은 무효가 됩니다. 그러나 그 스크립트 원문은 diff에 첨부되지 않았고, 첨부된 출력 형식(`WORKTREE: clean`)은 현재 상태 조회로 보입니다.

**버린 해석 2 — "건너뛴 1개를 뺀 23개 계약은 실행 결과를 보고 숫자를 맞춘 사후 면책이다".** 이것이 오너의 필수 공격 1번이고, 저도 이 방향으로 먼저 공격했습니다. 버린 이유는 세 가지 물증 때문입니다. ① 검사 목록 정본 `docs/sot/verification-commands.md`(최종 갱신 2026-08-22)의 12번 행이 이미 "**`main` 브랜치에서만**"이라고 적고 조건문 원문까지 인용하고 있습니다. ② 독립 검사기 `scripts/verify/check-ci-step-integrity.sh`의 `ALLOWED_STEP_IF` 표에 그 스텝 이름과 이유가 상수로 박혀 있습니다. ③ 이번 PR이 건드린 파일은 문서 2개 + 억제 원장 1개뿐이라고 롤백 절이 스스로 적었고, 워크플로·검사기·검사 목록 문서는 그 반경 밖입니다. 틀리면 깨지는 것: ③이 자기 신고라는 점입니다. `git diff --stat b724093..0367901`이 첨부되지 않았으므로, 만약 그 목록에 `verify.yml`이나 `check-ci-step-integrity.sh`가 들어 있었다면 이 근거는 무너지고 사후 면책 판정으로 뒤집힙니다. 이 명령을 필수 보완으로 요구합니다.

**버린 해석 3 — "건너뛴 검사가 요청 단계에서 빠지면 확인 사슬에 구멍이 난다".** 오너의 필수 공격 2번입니다. 저는 구멍을 만들려고 시나리오를 두 개 세웠고 둘 다 다른 검사에 막혔습니다(아래 반증 기록 6·7번). 그래서 "요청 단계 사슬은 닫힌다"로 판단했습니다. 틀리면 깨지는 것: 이 판단은 `verify.sh` 원문을 읽지 못한 채, 워크플로에 인라인으로 적힌 히스토리 스캔 본문과 `acceptance-secret-webhook-vendor.sh`의 종단 3건 출력만 보고 내린 정적 추론입니다. `verify.sh`가 실제로는 패턴 파일이 없을 때 조용히 0으로 끝난다면 제 추론의 일부가 약해집니다(다만 히스토리 스캔의 `[ -s "$CLEAN" ] || exit 2` 한 줄은 그와 무관하게 살아 있습니다).

**버린 해석 4 — "외부 병합 때문에 재검증이 원천 불가능하다".** 작성자의 프레이밍입니다. 버렸습니다. 병합이 막는 것은 "같은 PR #56에 새 실행을 붙이는 것"뿐이고, 같은 워크플로는 `on: pull_request`와 `on: push: branches: ["**"]`를 모두 받으므로 새 가지에 push하기만 해도 24개 정의가 그대로 도는 실행이 생깁니다(0-5는 main이 아니므로 동일하게 건너뜁니다). 틀리면 깨지는 것: 저장소에 새 브랜치 생성을 막는 정책이 있다면 제 반박이 약해지지만, diff 안에 그런 제약의 증거는 없고 오히려 워크플로 트리거가 반대를 말합니다.

**시각 정합성에 대한 판단.** 작성자는 "이 재검증이 진행되던 중에 병합됐다"고 썼습니다. 그런데 장부에 찍힌 가장 이른 시각은 UTC 23:25:03이고, 병합 시각은 23:23:40입니다. **병합보다 앞선 시각의 증거가 단 한 줄도 없습니다.** 그러므로 "작업 도중 병합됐다"는 서술이지 증명이 아닙니다. 거짓이라고 단정하지는 않습니다 — 세션 시작 시각을 기록하지 않았을 뿐일 수 있습니다. 다만 이 문서가 "이 세션은 병합하지 않았다"를 증명하려는 목적을 갖고 있다면, 그 목적에 가장 필요한 증거(병합 이전 시각의 상태 기록)가 정확히 비어 있습니다.

---

## 기술 상세와 증거 원문

줄번호 표기 원칙: goal 문서는 diff의 hunk 머리(`@@ -3,11 +3,29 @@` 등)에서 새 줄번호를 계산했습니다. `verify.yml`은 첨부된 `nl -ba` 출력의 실제 번호입니다. **셸/루비 스크립트는 첨부된 덤프가 `sed -n '1,9999p'`라 번호가 없으므로 줄번호를 만들지 않고 블록 식별 문자열로 지목합니다.** 없는 번호를 지어내지 않겠습니다.

### D1 — 심각도 높음 · "합격 증거가 자기 합격 조건을 반증한다"

- 원문 제목: `### AC-PR 원문과 집계`
- 위치: `docs/engineering/main-green-suppression-floor12-goal-2026-09-05.md:56` — AC-PR 조건 6 "작업트리 clean."을 정의하는 줄 / 같은 파일 `:10` — `PR_GATE: PASS`를 선언하는 결론 줄
- 증거 원문:

```text
PR_SHA_VALUES
LOCAL_HEAD=03679010b8420d00d6f09e7a2840852ac1b8c69c
REMOTE_BRANCH=03679010b8420d00d6f09e7a2840852ac1b8c69c
PR_HEAD=03679010b8420d00d6f09e7a2840852ac1b8c69c
CI_HEAD=03679010b8420d00d6f09e7a2840852ac1b8c69c
WORKTREE_STATUS_START
 M docs/engineering/main-green-suppression-floor12-goal-2026-09-05.md
WORKTREE_STATUS_END
```

→ 해석: 커밋 번호 네 개는 모두 같으니 조건 5는 충족입니다. 그러나 마지막 두 줄 사이의 ` M ...`은 "고쳤지만 아직 커밋하지 않은 파일이 1개 있다"는 뜻이고, 이는 조건 6 "작업트리 clean"의 정확한 반대입니다.

- 원인: 조건 5(시간 불변)와 조건 6(시점 의존)을 같은 한 번의 스냅샷으로 묶어 채점했고, 그 스냅샷을 문서 집필 중에 떴습니다. 08:29:12의 `check-verified-sha.sh` 출력은 `WORKTREE: clean / VERDICT: VERIFIED`였으므로, 7개 조건이 동시에 성립한 시점은 실재했습니다. 문제는 **그 시점을 명시하지 않고 무조건적 `PASS`로 적은 것**입니다.
- 사업 영향: 이 문서가 감사 근거로 남습니다. 나중에 누가 "clean 조건은 저때도 안 지켰는데 PASS가 났다"는 선례로 인용하면, 원칙 P23(초록불은 커밋에 귀속된다)의 강제력이 문서 선례 한 건으로 헐거워집니다. 실제 코드 위험은 아니지만 판정 체계의 신뢰 손실이 비용입니다.
- 최소 수정: `:10`을 "커밋 `0367901`에 대해, 08:29:12 clean 스냅샷 기준 `PR_GATE: PASS`. 이후 이 문서 편집으로 작업트리는 dirty이며 현재 상태는 UNVERIFIED다"로 고치면 계약과 사실이 다시 일치합니다.

### D2 — 심각도 높음 · "미검증을 불가능으로 바꿔 적었다"

- 원문 제목: `## 결론` 셋째 문단
- 위치: goal 문서 `:14` — "새 goal-only 커밋은 이미 병합된 PR에 새 `pull_request` 실행을 만들 수 없다" 줄 / `:130` — 게이트 계획 끝에 "이번 재개 실행은 새 goal 커밋의 `pull_request` run을 만들 수 없다"를 덧붙인 줄
- 증거 원문(반박 근거는 워크플로 트리거입니다):

```yaml
on:
  push:
    branches: ["**"]
  pull_request:
  workflow_dispatch:
```

→ 해석: 모든 브랜치의 push와 모든 pull request가 같은 워크플로를 켭니다. 새 브랜치에 커밋 하나만 올려도 24개 정의가 그대로 도는 실행이 생기고, main이 아니므로 0-5는 동일하게 건너뜁니다 — 즉 AC-PR 채점 형태가 그대로 재현됩니다.

- 원인: "PR #56에 붙일 수 없다"(참)를 "검증할 수 없다"(거짓)로 확대했습니다. 실제 미검증 사유는 훨씬 단순합니다 — **아직 커밋하지 않았습니다.**
- 사업 영향: 남은 필수 단계를 "환경 탓에 불가능"으로 기록하면 그 단계가 영구 면제로 굳습니다. 이번 diff가 스스로 금지한 counter-AC 첫 항목("job 전체가 success라는 이유만으로 …")과 같은 종류의 우회입니다.

### D3 — 심각도 중간 · "합격 숫자를 만든 명령이 실행 가능한 명령이 아니다"

- 원문 제목: `### AC-PR 원문과 집계`, `### 병합 전 기준선과 AC-MAIN 현재 원문`, `### acceptance-0-5.sh 반례`
- 증거 원문:

```text
COMMAND: gh run view 33895262180 AC-PR aggregate
COMMAND: gh run view 33998556226 AC-MAIN aggregate
COMMAND: temp clone; checkout task/main-green-suppression-floor12; bash scripts/acceptance-0-5.sh
COMMAND: temp PR-like clone without local main; bash scripts/acceptance-0-5.sh
```

→ 해석: 네 줄 모두 실제로 셸에 붙여넣어 돌아가는 명령이 아닙니다. `gh run view`에는 `AC-PR aggregate`라는 하위 명령이 없고, `temp clone; checkout ...`은 문장입니다. 반면 같은 문서의 다른 블록(`bash verify.sh`, `sed -n '144,159p' ... | bash`, `nl -ba ... | sed -n '132,142p'`)은 그대로 실행 가능합니다 — 작성자도 형식을 알고 있는데 핵심 4건에서만 지켰습니다.

- 원인: 실제 파이프라인(`gh api` 또는 `gh run view --json jobs`에 `jq`로 스텝 결론을 세는 과정)을 요약 라벨로 대체했습니다.
- 사업 영향: `success:23, skipped:1, defined:24`라는 이 판정의 결정적 숫자를 제3자가 재생산할 수 없습니다. 이 저장소 원칙 P2가 정확히 이것을 금지합니다("PR 본문에 검증 명령 + 기대 출력이 없으면 CI 실패. 산문 단언만 있으면 실패"). 더 나쁜 것은 `defined:24`의 집계 대상 정의(설정·정리 스텝을 뺐는가)가 명령 없이는 확인 불가라, 23+1=24라는 산술 폐쇄가 미확인 추출기에 의존한다는 점입니다.
- 필요 명령(제가 실행하지 못했습니다):
  `gh run view 33895262180 --json jobs -q '[.jobs[].steps[] | {name, conclusion}]'`
  `gh run view 33998556226 --json jobs -q '[.jobs[].steps[] | {name, conclusion}]'`
  `gh run list --commit 03679010b8420d00d6f09e7a2840852ac1b8c69c --json databaseId,event,conclusion`

### D4 — 심각도 중간 · "'같은 24개'의 '같은'이 본선에서만 증명되지 않았다"

- 원문 제목: `### 병합 전 기준선과 AC-MAIN 현재 원문`
- 증거 원문 비교:

```text
PR_STEP_AGGREGATE
{"cancelled":0,"defined":24,"failure":0,"skipped":1,"skipped_names":["인수 검사 0-5 (push · CI 연결)"],"success":23,"timed_out":0}

MAIN_STEP_AGGREGATE
{"cancelled":0,"defined":24,"failure":0,"skipped":0,"success":24,"timed_out":0}
```

→ 해석: 위쪽에는 건너뛴 스텝의 **이름**이 붙어 있는데, 아래쪽에는 이름이 하나도 없습니다. 그래서 본선 24개가 요청 실행의 24개와 같은 이름 집합인지 이 자료만으로는 확정할 수 없습니다. 병합 커밋은 새 트리이므로 원리상 다를 수 있습니다.

- 원인: 이름 목록을 요청 실행에서만 뽑았습니다. AC-MAIN 문구가 "같은 24개 검증 스텝"이라 이름 동일성이 계약의 일부입니다.
- 사업 영향: 지금은 실제로 다를 가능성이 낮습니다(이 PR은 워크플로를 건드리지 않았다고 신고). 그러나 "24라는 숫자만 맞으면 통과"라는 선례가 남으면, 다음에 스텝 하나를 빼고 하나를 넣어도 24가 유지되는 교체를 잡지 못합니다.
- 부수 확인: 작성자가 `배포 후 관측`(goal `:147`)에 "'억제 만료 스캔' 포함 검증 24개가 모두 success"라고 적은 것은, 그 스텝이 24개 안에 있다는 전제 아래 24/24로부터 논리적으로 따라옵니다. 이름 증거가 없다는 D4의 한계는 그대로 상속됩니다.

### D5 — 심각도 중간 · "합격 문구가 실행되지 않은 항목까지 단언한다" (기존 결함, 이 PR 소관 아님)

- 원문 제목: `### 직접 읽기 원문 5/6 — 0-5 배송 검사`
- 위치: `scripts/acceptance-0-5.sh` — 주석 `# 6. 원격에 비밀이 올라가지 않았는지` 블록과 마지막 `[ "$fail" -eq 0 ] && echo "PASS: ..."` 줄
- 증거 원문:

```bash
# 6. 원격에 비밀이 올라가지 않았는지 — 원격 브랜치 트리 전수 스캔(로컬 패턴 있을 때만)
if [ -s .secret-patterns ] && [ "$remote_main" != none ]; then
  ...
fi

[ "$fail" -eq 0 ] && echo "PASS: 0-5 완료 — CI 비밀스캔 강제 + push 완료 + 원격 트리 비밀 0건" || exit 1
```

→ 해석: 6번은 `.secret-patterns`(로컬 전용 파일)가 있을 때만 돕니다. 같은 파일 4번 블록이 "클론에 로컬 전용 패턴 파일이 따라오면 FAIL"이라고 못 박은 대로 이 파일은 gitignore 대상이므로 **CI 러너에는 존재하지 않습니다.** 그런데 마지막 줄은 조건 없이 "원격 트리 비밀 0건"을 출력합니다.

- 원인: 조건부 검사와 무조건부 합격 문구가 한 변수(`fail`)를 공유합니다. 돌지 않은 검사는 `fail`을 건드리지 않으므로 "통과"와 구분되지 않습니다.
- 사업 영향: main push마다 "원격 트리에 비밀 0건"이라는 문장이 로그에 남지만, 그 문장이 실제 스캔의 결과였던 적이 CI에서는 한 번도 없습니다. 이 저장소 원칙 P20("0건 처리로 통과를 스스로 의심한다")과 P3(3상태 판정)의 정면 위반이며, 이번 임시 클론 PASS(`TEMP_EXIT: 0`)도 같은 이유로 6번을 돌리지 않은 채 그 문구를 출력했습니다.

설계 지적(5줄):
- 무엇을: 6번 블록을 조건부 실행에서 3상태 판정으로 바꿉니다 — 패턴 파일이 없으면 `NOT_RUN`을 출력하고, 합격 문구에서 "원격 트리 비밀 0건"을 분리합니다.
- 왜: 돌지 않은 검사가 합격 문장에 포함되면 그 문장이 로그·감사에서 증거로 재사용됩니다.
- 버린 길: CI에 실제 패턴 파일을 올려 6번을 항상 돌리는 방안. 워크플로 주석이 "실제 비밀값은 CI에 올리지 않는다 — 저장소 시크릿에 넣는 것도 유출 경로를 늘리는 일이다"라고 이미 기각했습니다.
- 대가: main push 로그에 `NOT_RUN` 한 줄이 상시 남고, `NOT_RUN`이 있으면 전체 PASS 불가라는 P3를 그대로 적용할 경우 0-5가 CI에서 영구 불합격이 됩니다. 그래서 "이 항목은 로컬 전용"이라는 예외를 스크립트 안에 이유와 함께 명시해야 합니다.
- 되돌리기: 스크립트 한 파일의 마지막 두 블록만 되돌리면 원상복구됩니다. 다른 검사와의 결합은 없습니다.

### D6 — 심각도 중간 · "실패 메시지가 깨지고, 실패 원인을 잘못 지목한다"

- 원문 제목: `### acceptance-0-5.sh 반례` 세 번째 블록
- 위치: `scripts/acceptance-0-5.sh` — 주석 `# 5. 배송 —` 블록의 `local_main=$(git rev-parse main 2>/dev/null || echo none)` 줄
- 증거 원문:

```text
TEMP_LOCAL_MAIN: main
none
FAIL: origin/main(f96ece9564166d56815b3e5c3de5547b615bcb25) != main(main
none) — push 미완료
```

→ 해석: `main` 브랜치가 없을 때 `git rev-parse main`은 오류를 표준에러로 보내면서 **표준출력에는 `main`이라는 문자열을 남깁니다.** `2>/dev/null`이 가린 것은 오류 메시지뿐이고, `|| echo none`이 덧붙인 `none`이 그 뒤에 붙어 값이 `main\nnone` 두 줄이 됩니다. 그래서 실패 메시지가 줄바꿈으로 찢어졌습니다.

- 원인: `git rev-parse`의 표준출력 오염을 고려하지 않은 fallback입니다. `git rev-parse --verify main^{commit}`을 써야 합니다.
- 사업 영향: 두 가지입니다. ① 실패 사유가 "main 브랜치가 없음"인데 메시지는 "push 미완료"라고 말합니다 — 운영자를 엉뚱한 곳으로 보냅니다. ② 이 상태가 정확히 요청 단계 러너의 상태(체크아웃이 만든 것은 요청 머리이고 `main` 지역 브랜치는 없음)이므로, 만약 누군가 counter-AC 3번("0-5의 `if` 조건만 삭제해 PR에서 실행하는 것")을 저지르면 모든 PR이 이 깨진 메시지로 상시 실패합니다. 반례가 실제로 그 상황을 재현했고, 출력이 스크립트 원문의 동작과 정확히 일치합니다 — 이 대목은 제가 위조 여부를 공격했다가 실패한 지점이기도 합니다(반증 기록 4번).

### D7 — 심각도 중간(설계) · "예외 목록이 무제한 확장 가능하다"

- 원문 제목: `### 직접 읽기 원문 6/6 — CI 스텝 무력화 검사기`
- 위치: `scripts/verify/check-ci-step-integrity.sh` — 루비 블록의 `ALLOWED_STEP_IF = {` 상수 정의부
- 증거 원문:

```ruby
ALLOWED_STEP_IF = {
  "인수 검사 0-5 (push · CI 연결)" =>
    "origin/main==main 을 보는 검사라 main push 에서만 의미가 있다. PR 실행에서 요구하면 상시 실패한다.",
}
```

그리고 그 검사기를 시험하는 인수 검사의 통과 목록:

```text
PASS: 이유가 적힌 예외는 통과 — 0-5 의 main 전용 조건
```

→ 해석: 검사기는 "이름이 예외 표에 있고 이유가 적혀 있으면 조건부 실행을 허용"합니다. 그리고 인수 검사는 그 허용이 **작동하는지**를 확인합니다. 그러나 "예외 표에 새 이름이 늘어나면 불합격"이라는 시험은 목록 14건 어디에도 없습니다.

- 원인: 예외를 코드 상수로 두면서, 그 상수의 크기·변경에 대한 상위 잠금(개수 고정, 해시 고정, `weakens-check` 라벨 강제)을 걸지 않았습니다.
- 사업 영향: 앞으로 어떤 스텝이든 이름과 그럴듯한 이유 두 줄을 이 표에 추가하면 조건부로 꺼도 `acceptance-ci-step-integrity.sh`가 PASS를 냅니다. 원칙 P13⑥("검사기는 자기 자신을 검사 대상에서 제외할 수 없다", "살아남은 무력화가 하나라도 있으면 검증 체계 자체가 FAIL")이 겨냥한 구멍이 예외 표 형태로 남아 있습니다. 이번 diff의 결함은 아니지만, 이번 diff가 "사전 정의된 예외이므로 사후 면책이 아니다"라는 논증의 **유일한 기계적 근거**로 이 표를 인용하므로, 그 근거의 강도를 정확히 알아야 합니다.

설계 지적(5줄):
- 무엇을: `ALLOWED_STEP_IF`의 항목 수와 키 집합을 인수 검사에 하드코딩해 고정하고, 표가 바뀌면 불합격시킵니다.
- 왜: 예외 목록은 검사 약화의 정문인데 지금은 자물쇠가 없습니다.
- 버린 길: 예외 자체를 없애고 0-5를 두 스크립트로 쪼개(트리 검사 / 배송 검사) 조건문을 제거하는 방안. 변경 반경이 워크플로·검사 목록 문서·pre-push까지 번져 이번 작업 범위를 크게 벗어납니다.
- 대가: 정당한 예외를 추가할 때마다 인수 검사도 함께 고쳐야 해서 마찰이 늘어납니다. 그것이 의도된 마찰입니다.
- 되돌리기: 인수 검사 파일 한 곳의 단언 한 개를 지우면 원복입니다.

### D8 — 심각도 중간 · "새 내용에 대해 안전 확인을 다시 돌리지 않았다"

- 원문 제목: `### 필수 원명령 실행`의 `bash verify.sh` 블록 / `## 배송·롤백·관측` 절의 데이터 안전 AC
- 위치: goal 문서 `:146` 부근 — "데이터 안전 AC: 변경 파일에 비밀·후보자 데이터가 추가되지 않고 `bash verify.sh`가 exit 0이어야 한다" 줄 / diff 마지막 hunk `@@ -326,3 +370,1387 @@` — 1,387줄 추가
- 증거 원문:

```text
COMMAND: bash verify.sh
START_UTC: 2026-09-05T23:26:24Z
PASS: no secret-pattern match in any tracked file, .env not tracked
EXIT: 0
```

→ 해석: 안전 확인이 끝난 시각은 23:26:24입니다. 그런데 같은 문서의 뒷부분 증거는 23:35~23:44에 수집됐고, 그 내용이 곧 추가분입니다. 즉 **확인한 대상과 실제로 배송될 내용이 다릅니다.**

- 원인: 원명령 실행 순서가 문서 작성보다 앞섰고, 작성 후 재실행을 계획에 넣지 않았습니다.
- 사업 영향: 추가분에는 다른 파일에서 통째로 옮겨온 자격증명 형태 문자열이 들어 있습니다(예: `acceptance-0-5.sh` 원문의 `printf 'CHATGPT_%s=hunter2example\n' 'PASSWORD'`, 워크플로의 `^[^#]*=[A-Za-z0-9]{8,}[[:space:]]*$` 패턴, 웹훅·벤더 키 사례 이름들). 원본 스크립트는 자기 매칭을 피하려고 문자열을 조립해 쓰지만, 문서로 옮겨 붙이는 과정에서 같은 회피가 유지되는지는 `.secret-patterns.default`의 실제 규칙을 봐야만 압니다. **그 파일은 diff에 첨부되지 않았으므로 저는 판정할 수 없습니다.** push하면 `hooks/pre-push`가 먼저 잡을 가능성이 높지만, 그것은 "확인했다"가 아니라 "나중에 걸릴 것이다"입니다.
- 필요 명령(제가 실행하지 못했습니다):
  `bash verify.sh`
  `bash scripts/scan-data-exposure.sh all`
  `git diff --stat`

### D9 — 심각도 낮음~중간 · "성공 신호 원문을 지우면서 지운 목록을 남기지 않았다"

- 원문 제목: `## 상위 목표 1문장`
- 위치: goal 문서 `:26` — 성공 신호를 재정의한 줄
- 증거 원문(diff):

```diff
-... 성공 신호 = 이 PR HEAD SHA 의 pull_request 이벤트 24 스텝 전부 success.
+... PR 성공 신호는 아래 AC-PR, 병합 뒤 main 성공 신호는 AC-MAIN으로 서로 분리한다.
```

→ 해석: 실행 전에 적혀 있던 기대값("요청 이벤트에서 24개 전부 success")이 실행 결과를 본 뒤 삭제되고 새 기대값으로 대체됐습니다. 대체 자체는 옳습니다 — 그 기대값은 워크플로 구조상 처음부터 성립할 수 없었으니까요. 문제는 **지운 단언을 명시적으로 나열하지 않은 것**입니다.

- 원인: 기대값 변경을 다른 대량 추가와 한 커밋에 묶었습니다.
- 사업 영향: 원칙 P15④가 "구현 커밋은 자기 테스트의 기대값을 바꿀 수 없다 — 기대값 변경은 단독 커밋이어야 하고, 그 커밋의 PR 본문에 삭제된 단언 목록을 자동 노출한다"고 규정합니다. 이번 것은 코드 테스트가 아니라 문서 기대값이라 기계 검사에는 걸리지 않지만, 그 원칙이 막으려던 행동 형태와 같습니다. 같은 문서 `:41`(`## 인수 기준 (AC 1개)` → `## 인수 기준`), `:130`(게이트 계획), `:147`(배포 후 관측)에서도 원문이 교체됐습니다. 반면 `@@ -326,3 +370,1387 @@`의 앞 문맥 3줄로 확인되듯 **기존 V1/V2 검증 장부 본문은 한 글자도 삭제되지 않고 뒤에 덧붙는 형태**이며, 이 부분은 오너의 공격 4번을 통과합니다.

### D10 — 심각도 낮음 · 잔여 미확인 사항

1. **요청 머리 커밋에 붙은 실행이 하나뿐인지 확인되지 않았습니다.** 재실행이 여러 번 있었고 그중 초록 하나를 골랐을 가능성을 배제하는 목록(`gh run list --commit ...`)이 없습니다. `check-verified-sha.sh`의 `CI_VERIFIED_SHA/CI_CONCLUSION` 출력이 간접 방어이긴 하나, 그 스크립트 원문이 첨부되지 않아 다중 실행 처리 방식을 알 수 없습니다.
2. **"외부 병합"이라는 표현.** `"mergedBy":{"login":"sangmokang"}`이며 이 세션 사용자와 같은 계정입니다. "이 세션이 실행하지 않았다"는 참일 수 있으나 부재 증명이고, 사람 기준으로는 같은 오너입니다. "제3자"로 읽히지 않도록 "이 세션 밖에서, 같은 계정으로"라고 적는 편이 정확합니다.
3. **파일 크기.** 이 문서는 약 328줄에서 약 1,756줄이 됐습니다. 원칙 P11①의 파일 hard 600줄과 충돌하지만, 24개 스텝 중 파일 크기를 강제하는 스텝이 없어 CI는 초록입니다. 더 신경 쓰이는 것은 `docs/sot/verification-commands.md`가 스스로 적은 경고입니다 — "요약을 여기 두 번 적으면 반드시 갈라진다(2026-08-12 REV2-D2 실측)". 이번에 정본 6개 파일 전문이 engineering 문서로 복사됐습니다. 실행 로그로서의 가치는 인정하나, 정본이 바뀌어도 이 사본은 그대로 남아 6개월 뒤 갈라진 두 벌이 됩니다. 인용 범위를 판정에 실제로 쓰인 줄(예: `verify.yml:132-142`, `ALLOWED_STEP_IF` 블록, 0-5의 5·6번 블록)로 줄이는 편이 낫습니다.

---

## 반증 기록 — 깨뜨리려다 실패한 것

작성자에게 유리한 주장일수록 먼저 공격했습니다. 다음 일곱 건은 **깨지지 않았습니다.**

1. **"24 ≠ 23+1"을 만들려 했습니다.** 첨부된 `verify.yml` 전문에서 `- name:` 스텝을 직접 셌습니다: 비밀 스캔 / 원칙 정본·장부·배선 / 원칙 적대 fixture / 전역 스킬 잠금 / P3 조용한 실패 / G1 클린룸 / G2 테스트 게이트 / 히스토리 전량 스캔 / 0-2 / 0-6 / 0-7 / **0-5** / 억제 만료 스캔 / 강제 장치 존재 / 셸 문법 / 패턴 파일 실값 / hs-a3 / 데이터 노출 / hs-a4 / secret-webhook-vendor / verified-sha / ci-step-integrity / semantic-mutations / verify-ac-m = **정확히 24개**, 그중 0-5는 12번째. `docs/sot/verification-commands.md`의 표 24행과 순서까지 일치합니다. `defined:24`, `success:23`, `skipped:1`은 산술적으로 닫힙니다.
2. **병합 전 기준선 집계가 조작인지 공격했습니다.** `{"defined":24,"failure":1,"skipped":11,"success":12}`에서 실패 스텝은 13번째(억제 만료 스캔)입니다. 그 앞 12개가 success, 그 뒤 11개가 실행 취소로 skipped — 12+1+11=24로 정확히 맞습니다. 이 정합은 우연히 나오기 어렵습니다. 덤으로 **당시 main push에서 0-5(12번째)가 실제로 실행되어 성공**했음이 확인되므로, 0-5가 main에서 도는 검사라는 설명과도 일치합니다.
3. **"SKIPPED 예외가 이번 PR에서 새로 생겼다"를 세우려 했습니다.** ① 검사 목록 정본이 2026-08-22자로 이미 "`main` 브랜치에서만"을 적고 있고, ② 검사기 상수에 이름과 이유가 박혀 있으며, ③ 이 PR의 영향 반경은 문서 2 + 원장 1로 신고돼 워크플로·검사기·정본을 포함하지 않습니다. 세 겹이라 무너뜨리지 못했습니다. 다만 ③이 자기 신고이므로 `git diff --stat b724093..0367901`을 필수 보완으로 요구합니다.
4. **0-5 반례 출력이 지어낸 것인지 공격했습니다.** `main\nnone`이라는 기괴한 값은 `git rev-parse main 2>/dev/null || echo none`의 실제 동작(표준출력 오염 + fallback)에서만 나옵니다. 스크립트 원문과 출력이 정확히 맞물립니다. 위조 가설을 기각했고, 대신 그 자체가 결함(D6)이라고 판단했습니다.
5. **"본선 실행 결과를 요청 실행 결과로 썼다"를 세우려 했습니다.** 요청 블록은 `"event":"pull_request"`·`headSha 0367901`·run `33895262180`, 본선 블록은 `"event":"push"`·`headSha f96ece9`·run `33998556226`, 기준선은 `"event":"push"`·`b724093`·run `33313102834`로 세 실행이 이벤트·커밋·번호 모두 분리돼 있습니다. 기각.
6. **"과거 커밋의 초록불 재사용"을 세우려 했습니다.** 로컬·원격·PR·CI 네 값이 모두 `0367901`이고 별도로 `check-verified-sha.sh`가 `VERIFIED`를 냈습니다. 기각(D10-1의 다중 실행 가능성만 잔여).
7. **"0-5를 PR에서 안 돌리면 구멍이 난다"를 실증하려 했습니다.** 두 시나리오를 세웠습니다. ① `.secret-patterns.default`를 지우는 공격 — 워크플로의 히스토리 전량 스캔 스텝이 `[ -s "$CLEAN" ] || { echo "FAIL: 유효 패턴 0개"; exit 2; }`로 닫혀 있어 PR에서 잡힙니다. ② 패턴을 무력화해 탐지력을 죽이는 공격 — `acceptance-secret-webhook-vendor.sh`가 PR에서 돌면서 "스캐너 종단 — 벤더 키 파일을 verify.sh 가 차단 (verify.sh exit=1)" 등 종단 3건을 요구하므로 잡힙니다. 즉 0-5의 1~4번이 담당하던 몫은 요청 단계에서 중복 확보돼 있고, 잃는 것은 5·6번(배송 일치, 원격 트리 스캔)뿐인데 5번은 요청 단계에서 의미가 없고 6번은 CI에서 애초에 돌지 않습니다(D5). **결론: 요청 단계 확인 사슬은 0-5 없이도 닫힙니다.** 단, 이 판단은 `verify.sh`와 `.secret-patterns.default` 원문을 보지 못한 상태의 정적 추론임을 밝힙니다.

한편 작성자 문장 하나는 과장이라 정정합니다. `:20`의 "이 결과는 0-5의 PASS/FAIL이 PR 머리 검증 증거가 아니라 main 참조 입력의 결과임을 보여준다"는 **불합격 경로에 대해서만 참**입니다. 임시 클론이 요청 머리에서 PASS했다는 사실은, 워크플로 파일 추적·`verify.sh`/`0-6` 호출 존재·기본 패턴 파일 추적·격리 클론에서의 카나리 탐지(1~4번)가 **요청 머리 트리에 대해 통과했다**는 뜻이기도 합니다. 정확한 표현은 "5번 배송 검사가 나머지를 지배해 최종 판정이 main 참조에 좌우된다"입니다.

---

## 판정 요약

| 항목 | 판정 | 근거 |
|---|---|---|
| SKIPPED 1개가 사전 정의인가 | **사전 정의 인정** | 정본 표 12행 · `verify.yml:134-137` · `ALLOWED_STEP_IF` 상수 (`git diff --stat` 보완 필요) |
| 0-5 없이 요청 단계 사슬이 닫히는가 | **닫힘** | 히스토리 스캔 fail-closed + secret-webhook-vendor 종단 3건 (정적 추론) |
| 스텝 수 생략·skipped 변조·run 혼동·과거 SHA 재사용 | **해당 없음** | 반증 기록 1·2·5·6 |
| `PR_GATE: PASS` | **조건부 · 무단서 선언은 불가** | 조건 1~5·7 충족, 조건 6은 08:29:12 스냅샷에서만 성립 (D1) |
| `MAIN_CI: PASS` | **조건부 인정** | 수치·커밋 일치 충족, "같은 24개"의 이름 증거 없음 (D4) |
| 이 문서 커밋의 서버 검증 | **미실행** | 아직 커밋 전. "불가능"은 과장 (D2) |
| 전체 | **FAIL** | D1·D2·D3·D8 |

**필수 보완 4가지** — 모두 제가 실행하지 못했습니다:
1. `git diff --stat b724093..0367901` (예외 사전 정의의 기계적 확정)
2. `gh run view 33895262180 --json jobs -q '[.jobs[].steps[]|{name,conclusion}]'` 와 `33998556226` 동일 명령 (D3·D4)
3. 문서 편집 완료 후 `bash verify.sh` · `bash scripts/scan-data-exposure.sh all` · `git status --porcelain` 재실행 (D1·D8)
4. 새 브랜치로 이 문서 커밋을 올려 `pull_request` 실행을 받고 AC-PR을 정식 채점 (D2)
````

→ 무엇을 시켰나: 새 AC-PR/AC-MAIN과 현재 goal 1파일 diff만 빈 임시 디렉터리의 실제 Claude CLI에 주고 두 정조준 공격과 §8-7 형식을 요구했다. 무엇이 나왔나: V1은 전체 FAIL, D1~D10을 냈고 SKIPPED 사전 정의와 0-5 없이 PR 사슬이 닫힌다는 핵심 두 주장은 반증에 실패했다고 명시했다. 좋은/나쁜 소식인가: 실행 자체는 유효하지만 D2·D7·D9·D10에는 범위 확대나 정본 오독 가능성이 있어 V2가 모두 재현·재공격해야 한다.

### V1 필수 보완 재현

V1의 PASS 누락과 FAIL 과장을 둘 다 검증했다. D1은 합리적이므로 문서 첫 결론을 `08:29:12 KST clean 스냅샷`에 귀속시켰다. D2는 같은 PR #56은 병합 뒤 새 PR run을 받을 수 없다는 점은 유효하지만, 새 브랜치·새 PR의 기술적 가능성까지 없다고 읽히면 과장이라는 점을 명시했다. 그런 확장은 이번 오너가 정한 `PR #56` 범위에서 금지된다.

D3·D4를 위해 실행 가능한 정확한 명령으로 다시 조회했고, 워크플로 정의 24개 이름이 PR/main 두 run에 모두 존재하며 누락 0개임을 확인했다. D5·D6은 `acceptance-0-5.sh`의 기존 결함으로 재현되지만 수정 허용 범위 밖이다. D7은 장래 예외 키 확장 위험이지 이번 diff의 회귀가 아니다. D8의 `verify.sh` 재실행은 PASS했지만, 추가 히스토리 전량 노출 스캔은 이 커밋이 만든 것이 아닌 도달 가능 과거 blob 하나를 발견해 exit 1이다. D9는 삭제한 이전 단언을 AC 아래에 정확히 1개 명시했다. D10은 해당 SHA의 모든 run 목록을 조회했고 병합 주체를 `이 세션 밖에서 같은 GitHub 계정`으로 정정했다. 6개 파일 전문 첨부는 자유로운 요약본이 아니라 이번 오너가 `전체 출력`을 원장에 남기라고 명시한 검증 원문이다.

```text
COMMAND: git diff --stat b724093..03679010
 ...in-green-suppression-floor12-goal-2026-09-05.md | 328 +++++++++++++++++++++
 docs/sot/coding-principles.md                      |   3 +
 suppressions.yaml                                  |  18 --
 3 files changed, 331 insertions(+), 18 deletions(-)
EXIT: 0
COMMAND: git diff --name-status b724093..03679010
A	docs/engineering/main-green-suppression-floor12-goal-2026-09-05.md
M	docs/sot/coding-principles.md
M	suppressions.yaml
EXIT: 0
COMMAND: git diff --exit-code b724093..03679010 -- .github/workflows/verify.yml scripts/acceptance-0-5.sh scripts/verify/check-ci-step-integrity.sh .secret-patterns.default hooks/
EXIT: 0
```

→ 무엇을 시켰나: 원래 PR 머리의 전체 변경 목록과 금지 파일 diff를 base부터 직접 비교했다. 무엇이 나왔나: 원래 변경은 goal·SOT·억제 원장 3파일뿐이고 사전 SKIPPED를 정의한 워크플로·검사기는 diff 0이다. 좋은 소식인가: SKIPPED는 결과를 본 뒤 추가한 면책이 아니다.

```text
COMMAND: gh run list --commit 03679010b8420d00d6f09e7a2840852ac1b8c69c --limit 100 --json databaseId,event,headSha,conclusion,status,url,workflowName
[{"conclusion":"success","databaseId":33895262180,"event":"pull_request","headSha":"03679010b8420d00d6f09e7a2840852ac1b8c69c","status":"completed","url":"https://github.com/sangmokang/Valuehire_v6/actions/runs/33895262180","workflowName":"verify"},{"conclusion":"success","databaseId":33894942928,"event":"push","headSha":"03679010b8420d00d6f09e7a2840852ac1b8c69c","status":"completed","url":"https://github.com/sangmokang/Valuehire_v6/actions/runs/33894942928","workflowName":"verify"}]
EXIT: 0
```

→ 무엇을 시켰나: PR 머리 SHA에 귀속된 run을 100개 한도로 모두 열거했다. 무엇이 나왔나: pull_request 1개와 branch push 1개가 각각 success였고 서로 이벤트를 바꾸어 쓰지 않았다. 좋은 소식인가: AC-PR은 그중 `event=pull_request` run 33895262180만으로 판정했다.

```text
QUERY_LABEL: aggregate 24 workflow-defined names for runs 33895262180 and 33998556226
DEFINED_COUNT: 24
{"event":"pull_request","headSha":"03679010b8420d00d6f09e7a2840852ac1b8c69c","conclusion":"success","status":"completed","url":"https://github.com/sangmokang/Valuehire_v6/actions/runs/33895262180","defined":24,"matched":24,"success":23,"skipped":1,"failure":0,"cancelled":0,"timed_out":0,"missing":[],"skipped_names":["인수 검사 0-5 (push · CI 연결)"]}
{"event":"push","headSha":"f96ece9564166d56815b3e5c3de5547b615bcb25","conclusion":"success","status":"completed","url":"https://github.com/sangmokang/Valuehire_v6/actions/runs/33998556226","defined":24,"matched":24,"success":24,"skipped":0,"failure":0,"cancelled":0,"timed_out":0,"missing":[],"skipped_names":[]}
EXIT: 0
```

두 run의 정의 스텝 이름 24개를 원문으로 다시 읽은 결과 이름·순서는 완전히 같았다. 차이는 12번 정의 `인수 검사 0-5 (push · CI 연결)`의 결론뿐이다: PR에서 `skipped`, main push에서 `success`.

```text
COMMAND: bash verify.sh
START_UTC: 2026-09-06T00:00:43Z
START_KST: 2026-09-06T09:00:43+0900
HEAD: 03679010b8420d00d6f09e7a2840852ac1b8c69c
SESSION: 01a07188-a8a2-7422-94a6-a4da70cc8d22
PASS: no secret-pattern match in any tracked file, .env not tracked
EXIT: 0
```

→ 무엇을 시켰나: Claude V1 원문을 goal에 추가한 뒤 비밀 스캔을 재실행했다. 무엇이 나왔나: 모든 추적 파일 패턴 매치 0건으로 exit 0이다. 좋은 소식인가: V1 D8의 “추가 문서를 스캔하지 않았다”는 보완됐다.

```text
COMMAND: bash scripts/scan-data-exposure.sh all
START_UTC: 2026-09-06T00:01:04Z
START_KST: 2026-09-06T09:01:04+0900
HEAD: 03679010b8420d00d6f09e7a2840852ac1b8c69c
SESSION: 01a07188-a8a2-7422-94a6-a4da70cc8d22
PASS: 추적 파일 225개 검사, 위반 0건
FAIL: 기록에 산출물·데이터 경로가 남아 있음: docs/decisions/finding-events.jsonl (d8148f1065ecf5244e3a41585313165a4f13b2ae)
PASS: csv/tsv/sql 0개 검사(추적 225개 중), 개인정보 적재 0건
EXIT: 1
```

→ 무엇을 시켰나: V1이 추가로 요구한 현재 파일·도달 가능 기록·PII 전량 스캔을 돌렸다. 무엇이 나왔나: 현재 파일과 PII는 PASS했지만 로컬 reflog까지 포함한 과거 기록에 금지 확장자 경로 1건이 남아 exit 1이다. 좋은/나쁜 소식인가: 이번 goal-only diff가 노출을 추가한 것은 아니지만 전량 스캔은 PASS라고 보고할 수 없다. 히스토리 정리는 이번 허용 파일 범위 밖이므로 수정하지 않는다.

### 원격 run 직접 재현 명령

앞의 `QUERY_LABEL`은 출력 묶음의 이름이지 셸 명령이 아니다. 다음은 같은 원문을 다시 만드는 실행 가능한 명령이다.

```bash
gh run view 33895262180 --json event,headSha,conclusion,status,url,jobs
gh run view 33313102834 --json event,headSha,conclusion,status,url,jobs
gh run view 33998556226 --json event,headSha,conclusion,status,url,jobs
defined_names=$(sed -n 's/^      - name: //p' .github/workflows/verify.yml)
for run_id in 33895262180 33998556226; do
  gh run view "$run_id" --json event,headSha,conclusion,status,url,jobs | jq --arg names "$defined_names" '
    ($names | split("\n")) as $defined |
    [.jobs[].steps[]] as $steps |
    [$steps[] | .name as $n | select($defined | index($n))] as $matched |
    {event,headSha,conclusion,status,url,defined:($defined|length),matched:($matched|length),
     success:([$matched[]|select(.conclusion=="success")]|length),
     skipped:([$matched[]|select(.conclusion=="skipped")]|length),
     failure:([$matched[]|select(.conclusion=="failure")]|length),
     cancelled:([$matched[]|select(.conclusion=="cancelled")]|length),
     timed_out:([$matched[]|select(.conclusion=="timed_out")]|length),
     missing:[$defined[] as $n|select(($steps|map(.name)|index($n))==null)|$n],
     skipped_names:[$matched[]|select(.conclusion=="skipped")|.name]}'
done
```

### V2 — 새 맥락 Codex 적대 재현 원문

- 완료 시각: 2026-09-06 09:40:29 KST.
- 역할: Codex native `verifier`, 이 세션의 독립 읽기 전용 하위 에이전트.
- 쓰기: 0건. goal·git·GitHub 상태를 변경하지 않았다.

````text
VERDICT: FAIL

## Evidence

- `git status --short && git rev-parse HEAD && git rev-parse origin/task/main-green-suppression-floor12 && git rev-parse origin/main` — exit 0
  출력: goal 문서만 dirty, local/remote task HEAD 모두 `03679010b8420d00d6f09e7a2840852ac1b8c69c`, remote main `f96ece9564166d56815b3e5c3de5547b615bcb25`.

- `git diff --stat b7240936827032d5ee6791fa8cdb7d62ef6584b4..03679010b8420d00d6f09e7a2840852ac1b8c69c` — exit 0
  출력: 기존 PR diff는 3파일뿐이다: goal 문서 추가, `docs/sot/coding-principles.md`, `suppressions.yaml`.
  `verify.yml`, `acceptance-0-5.sh`, `check-ci-step-integrity.sh`, `.secret-patterns.default`, `hooks/`는 별도 금지 경로 대조에서 exit 0으로 변경 없음.

- `gh pr view 56 --json state,mergedAt,mergedBy,mergeCommit,headRefOid,...` — exit 0
  출력: PR #56은 `MERGED`, `mergedAt=2026-09-05T23:23:40Z`, `mergedBy.login=sangmokang`, merge commit `f96ece9564166d56815b3e5c3de5547b615bcb25`, `headRefOid=03679010...`.
  → “외부 병합”은 엄밀히는 “이 세션 밖에서 같은 계정으로 병합됨”이다.

- `gh run list --commit 03679010...` — exit 0
  출력: run `33895262180` = `pull_request/success`, run `33894942928` = `push/success`.
  → PR 판정에는 `pull_request` run `33895262180`만 써야 한다.

- Ruby 집계 명령으로 `.github/workflows/verify.yml`의 named step 24개와 GitHub run step을 대조 — exit 0
  PR run `33895262180`: `MATCHED=24 SUCCESS=23 SKIPPED=1 FAILURE=0 CANCELLED=0 TIMED_OUT=0`, skipped name `인수 검사 0-5 (push · CI 연결)`.
  main run `33998556226`: `MATCHED=24 SUCCESS=24 SKIPPED=0 FAILURE=0 CANCELLED=0 TIMED_OUT=0`, `MISSING=`.
  → V1 D4의 “main에서 같은 24개 이름 증거 없음”은 현재 V2 fresh evidence로 해소됐다.

- `.github/workflows/verify.yml:134-137` — 0-5 step name, main-only comment, `if: github.ref == 'refs/heads/main'`, run line 확인.
  `docs/sot/verification-commands.md:18-47` — CI named step 24개 정본, `:35`에서 0-5가 main only라고 사전 정의.
  `scripts/verify/check-ci-step-integrity.sh:29-33` — `ALLOWED_STEP_IF`에 0-5 예외와 이유가 사전 상수로 존재.
  → SKIPPED 재분류는 사후 면책이 아니라 사전 정의다.

- `bash scripts/verify/check-ci-step-integrity.sh` — exit 0
  출력: `ALLOWED: 인수 검사 0-5...`, `PASS: 조건부·오류무시 스텝 없음`, `CHECKED: 26`.
  → D7의 “예외 키 집합 증가 잠금 부재”는 설계상 잔여 위험이지만, 이번 diff 결함은 아니다.

- `bash verify.sh` — exit 0
  출력: `PASS: no secret-pattern match in any tracked file, .env not tracked`.
  → V1 D8의 `verify.sh` 재실행 요구는 해소됐다.

- `bash scripts/scan-data-exposure.sh all` — V2 독립 실행은 상위 지시로 중단, exit 130.
  별도 좁힌 확인: `git rev-list --all --reflog --objects | rg 'docs/decisions/finding-events\.jsonl|d8148f'`는 `d8148f1065ecf5244e3a41585313165a4f13b2ae docs/decisions/finding-events.jsonl`을 출력했고, `scripts/scan-data-exposure.sh:45-47`, `:96-98`은 `*.jsonl` history path를 FAIL 처리한다.
  → 전체 원명령은 V2 독립 완료가 아니므로 NOT_RUN/중단이다. 다만 실패 원인 후보는 직접 확인됐다.

## D1-D10

- D1: **부분 해소**. goal `:10`이 clean snapshot 기준 PASS와 현재 dirty 미재사용을 분리했다. 단 `:669` 해석 줄은 dirty evidence 블록 바로 아래서 “AC-PR을 충족한다”고 여전히 강하게 써서 보완 권장.
- D2: **V1 과장**. 같은 PR #56, 같은 브랜치, 새 PR 금지라는 사용자 scope에서는 goal `:14`, `:132`의 “같은 PR에 새 pull_request run 불가”가 맞다.
- D3: **유효**. goal `:649`, `:696`, `:709`의 `COMMAND:`는 실행 가능한 원명령이 아니라 요약 라벨이다. V2가 실제 재현 명령은 실행했지만, goal ledger 자체는 보완 필요.
- D4: **해소됨**. V2 fresh run 대조에서 PR/main 모두 workflow 정의 24개와 `MISSING=`으로 일치했다.
- D5: **재현됨, 범위 밖**. `acceptance-0-5.sh:93-101`은 `.secret-patterns` 없으면 원격 트리 스캔을 안 하면서도 “원격 트리 비밀 0건”을 출력할 수 있다.
- D6: **재현됨, 범위 밖**. `git rev-parse definitely_missing_ref_omx_probe 2>/dev/null || echo none`가 `refname` + `none`을 출력해 `main\nnone` 현상을 증명한다.
- D7: **잔여 위험, 범위 밖**. 예외 허용은 사전 정의지만 키 집합 고정 검사는 없다.
- D8: **부분 해소/부분 실패**. `verify.sh`는 통과. V2의 `scan-data-exposure.sh all` 원명령은 중단됐고, history 금지 path는 독립 확인됐다.
- D9: **V1 적용 과장**. P15④는 구현 커밋의 자기 테스트 기대값 변경을 겨냥한다. 이번은 오너가 명시한 문서 합격 계약 교정이며 goal `:75`에 삭제 단언도 기록됐다.
- D10: **대부분 해소**. run list, diff allowlist, PR/main step 대조는 확인됨. “외부 병합” 표현은 “이 세션 밖, 같은 계정”으로 더 정확히 고쳐야 한다.

## Gaps

- 현재 goal 수정분은 아직 커밋되지 않았고, push/PR body update도 V2 시점에서는 미완료다.
- 같은 PR #56은 이미 merged라 새 goal-only commit에 대한 `pull_request` run은 발생하지 않는다.
- V2 독립 `scan-data-exposure.sh all`은 종료 전에 중단되어 원명령 PASS/FAIL을 독립 완료하지 못했다.

## Risks

- goal ledger의 `COMMAND:` 라벨이 실행 가능한 명령으로 보강되지 않으면 P2 증거 재현성이 약하다.
- `acceptance-0-5.sh`의 D5/D6는 이번 허용 수정 범위 밖이지만, 후속 PR에서 별도 처리할 실제 결함이다.
- 전체 Strict 판정은 새 HEAD PR 검증 부재 때문에 PASS가 될 수 없다.
````

위 V2 지적을 반영해 D1의 `:669` 해석을 clean 스냅샷 전용으로 정정했고, D3의 요약 라벨은 `QUERY_LABEL`로 바꾸고 위에 실행 가능한 원명령을 추가했다. D10의 병합 주체 표현도 문서 첫 결론에서 정정했다.

### G/V1/V2/T 일치표

| 항목 | G(작성자) | V1(Claude) | V2(Codex) | T(최종 계약) |
|---|---|---|---|---|
| 병합된 역사적 PR head `03679010…` AC-PR | clean 스냅샷 PASS | 조건부 PASS | clean 스냅샷 PASS | `PR_GATE: PASS (historical merged head only)` |
| 새 goal-correction head | 아직 dirty, NOT_RUN | FAIL | FAIL | 커밋·push 뒤에도 같은 PR의 새 PR run이 없으면 `PR_GATE: NOT_RUN` |
| main `f96ece95…` AC-MAIN | PASS | 이름 증거 조건부 | 24개 이름·결론·SHA PASS | `MAIN_CI: PASS`; 병합은 이 세션 밖 같은 계정 |
| main 전용 0-5 | 사전 정의 SKIPPED | 인정 | 인정 | PR에서 `SKIPPED`; `success`/`NOT_RUN`으로 바꾸지 않음 |
| 0-5 없는 PR 사슬 | 닫힘 | 닫힘, 일부 표현 과장 | 닫힘 | 0-5 1~4는 다른 PR 검사가 보전; 5번 main 배송은 PR 무관 |
| V1 D5/D6 | 범위 밖 | 실제 결함 | 재현, 범위 밖 | 이번 금지 파일은 수정하지 않고 잔여 위험으로 보존 |
| V1 D7 | 범위 밖 | 설계 결함 | 장래 위험, 이번 diff 결함 아님 | 예외 키 확장 잠금은 후속 과제 |
| 전량 노출 스캔 | local 원명령 exit 1 | 재실행 요구 | V2 장시간 실행 중단, 원인 blob 독립 확인 | `FAIL`; 기존 local reflog 결함이며 현 허용 범위 밖 |
| 전체 Strict | FAIL | FAIL | FAIL | 새 goal HEAD의 PR run 부재와 잔여 스캔 FAIL을 숨기지 않음 |
