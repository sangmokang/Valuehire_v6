# main 초록 복구 — 억제 원장 `keyword-env-value-floor-12` 종결 (goal, 2026-09-05)

등급 **L3** (SOT 문서 `docs/sot/coding-principles.md` 수정 포함 → Strict `SKILL.md` §0.5의 "SOT 수정 = L3").
워크트리 `worktrees/main-green-suppression-floor12` · 브랜치 `task/main-green-suppression-floor12` · base `b724093`.

## 상위 목표 1문장

main 의 CI 가 2026-08-30 이후 빨간불(`b724093` push run 33313102834, 실패 스텝 1개 = "억제 만료 스캔")이라 모든 PR 의 초록 판정이 무의미해졌다. 만료된 억제 1건을 **정책 확정으로 종결**해 main 을 초록으로 되돌리고, 그 뒤 열린 PR 11건의 병합 판정을 다시 가능하게 한다. 성공 신호 = 이 PR HEAD SHA 의 pull_request 이벤트 24 스텝 전부 success.

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

- 검증 명령: `sed -n '144,159p' .github/workflows/verify.yml | sed 's/^          //' | bash` (verify.yml 본문을 들여쓰기만 제거해 그대로 실행) → `PASS: 억제 3건 전부 유효 기한 내`, exit 0.
- 보조: `bash verify.sh` PASS 1줄 · `bash scripts/acceptance-principles-check.sh` → `MECHANISMS: PASS 34/34` · `bash scripts/acceptance-principles-mutations.sh` exit 0.
- counter-AC: 원장에서 행을 지우기만 하고 정책 서술이 없으면 REV2-D3 지적("축소가 원장에 없음")이 그대로 재발 — 정책 줄 존재를 grep 으로 확인한다(`grep -c '값 하한 12자' docs/sot/coding-principles.md` = 1).

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

Gate0 session-status → RED 커밋(이 문서) → GREEN 커밋(원장·SOT) → 로컬 검증 4종 → V1(격리 Claude) → V2(새 맥락 Codex) → push → PR → CI(pull_request, PR HEAD SHA) → READY TO MERGE(merge 는 사용자).

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
- 배포 후 관측: main 의 다음 push run 에서 "억제 만료 스캔" 스텝 success 여부. 다음 만료는 2026-09-15(ci-transfer-guarantee · p13-deletion-blindspot) — 그 전에 결정 필요.

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
