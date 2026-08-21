# Work Unit 중간 증명 경계 도입 — goal (2026-08-21)

## 1층 결론

Valuehire의 기존 `strict → codeaudit → 전체 적대검증 → CI`는 그대로 최종 관문으로 유지합니다. 그 앞에 작업을 하나의 주장씩 닫는 Work Unit을 넣어, 큰 구현이 끝난 뒤에야 결함을 찾는 현재의 빈틈을 줄입니다.

유료 GitHub 기능, 새 오케스트레이션 제품, Work Unit마다 새 Agent를 띄우는 방식은 필수 조건으로 채택하지 않습니다. 저장소의 기존 worktree, 실행 가능한 인수 기준, RED 시험, 반증 시험, Git 커밋만으로 기본 절차가 돌아가야 합니다.

## 2층 판단 근거

### 가져올 핵심

Work Unit은 파일 묶음이나 막연한 “CI 개선”이 아니라 **하나의 반증 가능한 주장**입니다. 각 Work Unit은 그 주장만 구현하고, 해당 기능 검사와 간단한 반증 1~3개를 통과한 뒤 커밋으로 닫습니다.

Work Unit 안에서 찾는 것은 “이 주장 하나가 참인가?”이고, PR 전체의 마지막 검증에서 찾는 것은 “각 주장은 참이어도 결합하면 깨지는가?”입니다. 두 검사는 대체 관계가 아니라 범위가 다른 두 겹의 검사입니다.

### Valuehire에 맞게 바꿀 부분

외부 제안의 “Work Unit 하나 = 커밋 하나”는 그대로 채택하지 않습니다. 현재 정본 P5는 기능이 없어서 실패하는 RED 시험을 먼저 커밋하고, GREEN 구현 커밋이 그 시험의 기대값을 바꾸지 못하게 합니다. 따라서 여러 Work Unit의 RED 계약을 먼저 잠근 뒤, 각 Work Unit을 닫는 GREEN 커밋을 하나씩 만드는 구조로 적용합니다.

`squash merge` 뒤에는 개별 Work Unit 커밋이 `main`에 남지 않습니다. Work Unit 커밋은 병합 전 검토·원인 격리 경계이고, 병합 뒤 롤백 경계는 PR 전체의 squash 커밋입니다. 특정 Work Unit만 되돌릴 때는 해당 변경을 역적용하는 새 커밋을 만듭니다.

### 결정 카드 — 중간 증명 경계

> **무엇을** — `ISSUE/요구사항 → Work Unit 분해 → WU별 구현·표적 검증·작은 공격·완료 커밋 → 전체 strict·codeaudit·결합 공격·CI` 순서를 저장소 규칙으로 고정합니다.
> **왜** — 큰 변경 뒤 한 번만 검사하면 실패 원인의 범위가 넓고, 구현자가 만든 맥락에 검증 판단까지 묶입니다.
> **버린 길** — 기존 최종 검사를 Work Unit 검사로 대체하는 길과 모든 Work Unit에 full codeaudit·외부 Agent를 강제하는 길은 각각 결합 결함 누락과 과도한 비용 때문에 버립니다.
> **대가** — RED 계약 커밋과 Work Unit 완료 커밋이 늘어나고, 구현 전에 분해 시간이 듭니다.
> **되돌리기** — 이 변경의 SOT 커밋을 되돌리면 기존 `작업 1개 = 인수 기준 1개` 절차로 복구됩니다.

## 현재 상태와 근본 원인

아래 `file:line`은 변경 전 기준 commit `dcc71dd022cba9656cb1a4b6a0f825d8d99655a5`의 역할을 기록한 것이다.

- `docs/sot/git-workflow.md:15` 역할: 현재는 작업·worktree·브랜치·인수 기준을 모두 1:1로 묶어 PR보다 작은 증명 경계를 표현하지 못합니다.
- `docs/sot/git-workflow.md:21` 역할: PR도 인수 기준 1개로 고정해 하나의 목표 안에서 서로 의존하는 여러 작은 주장을 순서대로 닫는 방법이 없습니다.
- `docs/sot/verification-commands.md:10-16` 역할: 저장소 전체 게이트 명령은 적혀 있지만 Work Unit 표적 검사와 PR 전체 통합 검사의 질문·시점이 분리되어 있지 않습니다.
- `docs/sot/coding-principles.md`의 P2·P5·P13·P15 역할: 실행 가능한 인수 기준, RED 이후 시험 불변, 검사 약화 공격, 최종 서버 검사를 이미 요구합니다. 새 방법론은 이 원칙들을 다시 만들지 않고 실행 순서와 경계만 연결합니다.

근본 원인은 검사 종류의 부족이 아니라 **큰 구현과 최종 검사 사이에 닫힌 증명 경계가 없는 것**입니다.

## 범위와 위험등급

- 위험등급: **L3** — SOT 두 파일의 개발·검증 흐름을 바꿉니다.
- 변경 범위: `docs/sot/git-workflow.md`, `docs/sot/verification-commands.md`, 구조화된 Work Unit 정책·생성 문서·검사기·반례, 기존 `scripts/acceptance-principles-*.sh`, 이 goal 문서.
- 비범위: GitHub Pro 결제, branch protection, CODEOWNERS, 새 Agent 런타임, 새 CI 실행 줄·새 외부 의존성 추가, 기존 P0 결함 구현.
- 영향 반경: 이후 모든 코드·제품 작업의 분해, 커밋, 검증 순서. 제품 런타임과 후보자 데이터에는 직접 영향이 없습니다.

## 입출력·오류·경계 계약

### 입력

- 하나의 ISSUE 또는 요구사항 문서.
- 실행 가능한 인수 기준과 가짜 합격 시나리오.
- 저장소의 현재 위험등급·SOT·실제 검증 명령.

### 출력

- Work Unit 1~5개. 각 항목은 ID, 주장 1개, 선행 관계, 위험등급, 정확한 검증 명령·기대값, 반증 1~3개, 변경 범위, 완료 커밋을 가집니다.
- 각 Work Unit은 `PASS / FAIL / NOT_RUN / BLOCKED` 중 하나로 기록합니다.
- 모든 Work Unit이 PASS여도 PR 전체 strict·codeaudit·결합 적대검증·CI가 별도로 남습니다.

### 오류

- 주장이 둘 이상이거나 `CI 개선`, `검증 시스템 완성`처럼 반증할 수 없으면 분해 실패입니다.
- 표적 검증 명령이 없거나 검사 대상이 0개면 `NOT_RUN`이며 완료할 수 없습니다.
- 반증이 실패하거나 독립 검토가 필요한 고위험 경로에서 검토가 없으면 `FAIL` 또는 `NOT_RUN`입니다.

### 경계

- 파일 수·줄 수로 Work Unit을 나누지 않습니다.
- 고위험 경로의 유일한 정본 목록은 `docs/sot/verification-commands.md`의 “위험도에 따른 Work Unit 검사 강도” 절입니다. 이 goal은 목록을 복제하지 않습니다.
- 일반 Work Unit은 표적 검사와 반증 1~3개로 닫고, 고위험 Work Unit은 독립 검토를 추가합니다.
- Agent 교체는 선택입니다. 같은 세션에서도 구현 맥락과 검증 질문을 분리할 수 있어야 합니다.

## 인수 기준과 counter-AC

### AC-1 — Work Unit 경계

**When** 하나의 목표가 여러 독립 주장을 포함하면, 시스템은 목표를 Work Unit 1~5개로 나누고 각 Work Unit을 하나의 주장과 완료 커밋 경계로 기록해야 합니다.

- 검증 명령: `bash scripts/acceptance-work-unit-policy.sh`
- 기대값: 종료값 0, `POLICY_CHECKED: 19`, `DOCUMENT_SYNC: PASS`. 하나의 주장, 완료 커밋, PR 상한, 브랜치 수명, 검토 보정, squash 경계가 구조화된 정책으로 직접 검사됩니다.
- counter-AC: Work Unit을 파일 단위로 정의, 여러 Work Unit을 한 완료 커밋에 혼합, squash 뒤 개별 커밋 revert 가능하다고 기록.

### AC-2 — 두 층의 검증

**When** Work Unit 구현이 끝나면, 시스템은 해당 AC와 작은 반증을 먼저 실행하고, 모든 Work Unit 뒤에는 strict·codeaudit·전체 적대검증·CI를 별도로 실행해야 합니다.

- 검증 명령: `bash scripts/acceptance-work-unit-policy.sh`
- 기대값: 종료값 0, `POLICY_CHECKED: 19`, `DOCUMENT_SYNC: PASS`. Work Unit과 PR 전체 검사의 순서, 고위험 검토 등급·비용·롤백 경계가 구조화된 정책으로 직접 검사됩니다.
- counter-AC: Work Unit마다 full codeaudit 강제, 최종 통합 검사를 삭제, CI 초록을 로컬 PASS로 대체.

### AC-3 — 구조화 정책과 생성 문서 변조 차단

**When** Work Unit 정책의 값·순서·스키마를 바꾸거나 생성 문서에 예외 문장을 덧붙이면, 정책 mutation 게이트는 해당 사본을 실패시켜야 합니다.

- 검증 명령: `bash scripts/acceptance-work-unit-policy-mutations.sh`
- 기대값: 종료값 0, `CHECKED: 19`, `VERDICT: PASS`. 정상 정책은 통과하고 값·순서·스키마·생성 문서 반례 17개는 모두 기대한 `FAIL`을 관측하며 원본 저장소는 불변입니다.
- counter-AC: `전체 적대검증 생략`, pre-push로 최종 관문 대체, 고위험 경로 삭제, 문서 REVIEW만으로 고위험 WU PASS, WU·브랜치 상한 완화.

## Work Unit 장부

| ID | 하나의 주장 | 선행 | 위험 | 완료 경계 | 상태 | 상태 근거 |
|---|---|---|---|---|---|---|
| WU-01 | 목표·Work Unit·커밋·PR의 관계가 하나의 주장 단위 검토를 보존합니다. | 계약 RED | L3(SOT) | `4dd2e97`, `87b526a`, `cbe3d6b` | PASS | Codex 실행 REVIEW·codeaudit 승인 |
| WU-02 | Work Unit 표적 검사와 PR 전체 통합 검사가 서로 다른 질문과 시점으로 분리됩니다. | WU-01 | L3(SOT) | `9a3c862`, `87b526a`, `cbe3d6b` | PASS | Codex 실행 REVIEW·codeaudit 승인 |
| WU-03 | Work Unit 계약의 삭제·완화·의미 반전을 기존 원칙 게이트가 실패시킵니다. | WU-01, WU-02 | L3(검증 장치) | `2c05ab2`, `659e709`(RED), `58043bb`, `8b7a44b`(GREEN), `cbe3d6b` | PASS | 28/28·53/53·pre-push 승인 |
| WU-04 | Work Unit의 기계 계약은 자연어가 아니라 구조화된 정책 한 벌에서 판정됩니다. | WU-03 | L3(SOT·검증 장치) | `dc2dad9`(RED), `28155fc`(GREEN) | PASS | 정책 19건·생성 문서 byte-exact 일치 |
| WU-05 | 정책값·순서·스키마·생성 문서의 우회가 고장 사본에서 전부 실패합니다. | WU-04 | L3(검증 장치) | `dc2dad9`(RED), `28155fc`(GREEN) | PASS | 정상 1건·고장 사본 17건·원본 불변 1건 |

### 구조화 정책 보정 — RED→GREEN

RED 커밋 `dc2dad9`은 구조화 정책·생성 문서·검사기가 없는 상태와 값·순서·스키마·동의어 우회 반례를 먼저 고정했습니다. GREEN 커밋 `28155fc`은 `docs/sot/work-unit-policy.yaml`을 유일한 정책 입력으로 삼고, 사람용 문서를 결정적으로 생성하며, 기존 원칙 검사에서 Work Unit 자연어 문장·금지 정규식을 제거했습니다.

```text
bash scripts/acceptance-work-unit-policy.sh: CHECKED 5, VERDICT PASS
ruby scripts/verify/check-work-unit-policy.rb: POLICY_CHECKED 19, DOCUMENT_SYNC PASS
bash scripts/acceptance-work-unit-policy-mutations.sh: CHECKED 19, VERDICT PASS
bash scripts/acceptance-semantic-mutations.sh: CHECKED 10, VERDICT PASS
bash scripts/verify/check-mechanism-registry.sh: CHECKED 16
bash scripts/acceptance-verify-ac-m.sh: CHECKED 31
workflow/SOT step names: 25/25, diff 없음
```

→ 자연어 표현은 생성 출력일 뿐 판정 입력이 아니다. 정책값·키·순서가 달라지거나 생성 문서에 예외 동의어를 덧붙이면 격리 사본 검사가 실패한다.

### RED 계약

- 같은 명령으로 AC-1·AC-2의 필수 문구 부재를 먼저 확인하고, AC-3은 별도 mutation RED 커밋으로 잠급니다.
- RED는 문법 오류나 파일 누락이 아니라 아직 Work Unit 절차가 정본에 없어서 실패해야 합니다.
- WU 완료 커밋은 이 AC의 기대값을 바꾸지 않습니다.

V1은 최초 goal에 고정했던 `rg "A|B|C"` 형태가 하나만 찾아도 종료값 0을 내는 OR 검사라서 아래 AND 방식 RED 출력과 원명령이 일치하지 않는다고 판정했습니다. 그 지적은 맞습니다. 최초 명령은 무효로 폐기했고, AC-1·AC-2의 검증 명령을 실제 RED 하니스와 같은 전건 AND 방식으로 교정했습니다. 아래 최초 출력은 삭제하지 않되 원명령 PASS 증거로 세지 않습니다. 교정 명령의 기준 commit RED와 현재 GREEN은 후속 로그에 새로 기록합니다.

실행 시각: `2026-08-21T02:44:04+0900` 이후, 기준 commit `dcc71dd022cba9656cb1a4b6a0f825d8d99655a5`, goal 세션 `01a02041-4ea2-7470-a7aa-96e993cc0eef`.

```text
MISSING: Work Unit
MISSING: 하나의 주장
MISSING: 완료 커밋
PRESENT: squash
AC-1_RED_EXIT=1
MISSING: LOCAL VALIDATE
MISSING: 작은 적대검증
MISSING: 전체 strict
MISSING: 전체 codeaudit
MISSING: 전체 적대검증
MISSING: GitHub verify CI
AC-2_RED_EXIT=1
```

→ 정본 파일은 읽혔지만 Work Unit 중간층과 두 검증 층이 아직 없어서 올바른 이유로 실패했습니다. 문법 오류·작업 폴더 오류·검사 대상 0건이 아닌 유효한 RED입니다.

### 롤백과 데이터 안전

- WU-01 또는 WU-02가 잘못되면 해당 완료 커밋을 먼저 되돌립니다.
- squash merge 뒤에는 PR 전체를 되돌리거나 잘못된 WU 변경만 새 커밋으로 역적용합니다.
- 코드·DB·후보자 데이터·자격증명을 바꾸지 않으므로 데이터 마이그레이션과 운영 복구는 없습니다.

## Harness·검증 계획

1. Gate 0: 현재 SOT·과거 goal·필수 strict 원칙 직접 로드와 시작 상태를 기록합니다.
2. Gate 2: 격리 worktree `worktrees/work-unit-methodology`에서 작업합니다.
3. RED: AC-1·AC-2의 필수 문구 검색이 현재 정본에서 실패함을 확인합니다.
4. GREEN: WU-01, WU-02를 서로 다른 완료 커밋으로 닫고, WU-03은 기존 원칙 게이트 안에서 RED 반례를 통과시킵니다.
5. R2: 임시 고장 사본에서 “최종 검사를 삭제”, “파일 단위 WU”, “모든 WU full audit”을 주입해 AC 위반임을 확인합니다.
6. R4: `docs/sot/INDEX.md → git-workflow.md / verification-commands.md` 참조 경로와 실제 사용 명령을 확인합니다.
7. 통합: `bash scripts/check-docs-sot.sh`, `bash scripts/acceptance-principles-check.sh`, 관련 전체 검증을 실행합니다.
8. V1: Claude가 외부 의존 과잉, 기존 P5 충돌, squash 롤백 과장, 고위험 경로 누락을 공격합니다.
9. V2: 새 Codex 맥락이 V1의 파일·명령·판정을 재현하고 반대 방향으로 재공격합니다.

## 적대 검증 로그

### 교정된 RED→GREEN

실행 시각 `2026-08-21T03:11:40+0900`, 실행 기준 HEAD `9a3c8623c3bb481e679c79763f131eb303214a03`. 기준 commit 파일은 반복 검색이 가능한 `mktemp` 일반 파일로 고정했습니다. 프로세스 치환 스트림은 첫 검색이 입력을 소비해 뒤 검색이 모두 실패하는 환경 함정을 확인해 폐기했습니다.

```text
=== AC-1 CORRECTED RED regular-file ===
MISSING: Work Unit
MISSING: 하나의 주장
MISSING: 완료 커밋
PRESENT: squash
EXIT=1
=== AC-1 CORRECTED GREEN ===
PRESENT: Work Unit
PRESENT: 하나의 주장
PRESENT: 완료 커밋
PRESENT: squash
EXIT=0
=== AC-2 CORRECTED RED regular-file ===
MISSING: LOCAL VALIDATE
MISSING: 작은 적대검증
MISSING: 전체 strict
MISSING: 전체 codeaudit
MISSING: 전체 적대검증
MISSING: GitHub verify CI
EXIT=1
=== AC-2 CORRECTED GREEN ===
PRESENT: LOCAL VALIDATE
PRESENT: 작은 적대검증
PRESENT: 전체 strict
PRESENT: 전체 codeaudit
PRESENT: 전체 적대검증
PRESENT: GitHub verify CI
EXIT=0
```

→ 교정한 전건 AND 명령은 변경 전 정본을 두 AC 모두 RED로, 현재 정본을 두 AC 모두 GREEN으로 판정했습니다. AC-1에서는 기존 `squash` 하나만 있어도 전체 합격하지 않았으므로 V1의 OR 우회가 닫혔습니다.

### R2 고장 사본

첫 “최종 적대검증 삭제” 고장 사본은 문구 뒤에 `생략`을 붙였고, 당시 문자열 존재 검사에는 필수 문자열이 남아 통과했습니다. 이는 공격이 무효인 것이 아니라 의미 반전을 탐지하지 못한 실제 fail-open 결함입니다. 문구 완전 삭제 재시도만 실패한 것으로는 이 결함이 닫히지 않았고, 후속 WU-03의 정확한 줄 계약과 mutation 회귀시험으로 보정했습니다.

```text
PASS: 원본 WU/PR 경계
PASS: 원본 두 층 검증·push 관계
PASS: 다중 주장 변조 차단
PASS: WU 6개 이상 변조 차단
FAIL: 최종 적대검증 삭제 변조가 통과
PASS: pre-push 대체 과장 변조 차단
PASS: 일반 WU 과잉검증 변조 차단
CHECKED: 7

--- 재시도: 필수 문구 완전 삭제 ---
PASS: 최종 적대검증 완전 삭제 변조 차단
CHECKED: 1
```

→ 원본과 완전 삭제 반례만으로는 의미 반전 우회를 막지 못했습니다. 이 로그의 `FAIL: 최종 적대검증 삭제 변조가 통과`가 WU-03의 유효한 RED 근거입니다.

### WU-03 RED→GREEN — 정본 의미 반전 차단

RED 커밋 `2c05ab2`에서 기존 mutation fixture에 두 SOT를 넣고 신규 반례 9개를 먼저 추가했습니다. 구현 전 실행은 각 반례가 실제로 `VERDICT: PASS`를 내서 전체 종료값 1이었습니다.

```text
C2-WORKFLOW-MISSING부터 C2-FINAL-ADVERSARIAL-SKIP까지 신규 9개: expected FAIL, actual PASS
CHECKED: 49
VERDICT: FAIL
```

GREEN 커밋 `58043bb`은 새 CI 줄을 만들지 않고 이미 pre-push·CI에 직접 배선된 `scripts/acceptance-principles-check.sh`가 두 Work Unit SOT를 읽도록 확장했습니다.

```text
bash scripts/acceptance-principles-check.sh: exit 0
WORK_UNIT_METHOD: PASS 25/25

bash scripts/acceptance-principles-mutations.sh: exit 0
신규 9개 반례: 모두 기대한 FAIL 관측
CHECKED: 49
VERDICT: PASS
```

→ 문서 존재만 확인하던 임시 AC를 기존 상시 게이트의 계약과 격리 mutation으로 교체했습니다. 새 acceptance 파일·새 CI 실행 줄·외부 서비스는 추가하지 않았습니다.

### codeaudit 2차 RED→GREEN — 덧붙이기 우회와 검토 신뢰 경계

새 Codex codeaudit는 정상 9번 단계를 보존한 채 `단, 일정이 급하면 전체 적대검증은 생략할 수 있다`를 덧붙이면 당시 25/25 게이트가 합격하는 우회를 재현했습니다. 또한 동일 쓰기 권한에서 독립 검토자 신원을 기계 보증하는 영수증을 만들면 자기발급 문제가 반복된다고 지적했습니다.

RED 커밋 `659e709`은 다음 네 반례를 먼저 추가했고, 구현 전 모두 actual PASS여서 전체 종료값 1을 확인했습니다.

```text
C2-FINAL-ADVERSARIAL-ADDITIVE: actual PASS
C2-DOCUMENT-REVIEW-ADDITIVE: actual PASS
C2-PAID-REVIEW-REQUIRED: actual PASS
C2-REVIEW-ENFORCEMENT-CLAIM: actual PASS
CHECKED: 53
VERDICT: FAIL
```

GREEN 커밋 `8b7a44b`은 허용형 예외 문장을 거부하고, 비용 없는 새 로컬 맥락을 독립 검토의 기본값으로 고정했습니다. 같은 권한 안에서 검토자 신원을 기계 보증하지 못한다는 한계와 goal 장부·최종 codeaudit의 책임도 함께 기록했습니다.

```text
bash scripts/acceptance-principles-check.sh: exit 0
WORK_UNIT_METHOD: PASS 28/28
bash scripts/acceptance-principles-mutations.sh: exit 0
CHECKED: 53
VERDICT: PASS
```

→ 자기발급 독립성 영수증은 만들지 않았습니다. 원칙 게이트는 정본 정의와 예외 문구를 차단하고, 실제 독립 실행은 새 맥락의 명령·출력과 codeaudit 판정으로 증명합니다.

### R4 정본 진입 경로

```text
7:- [git-workflow.md](git-workflow.md) — trunk-based + worktree + 태그 릴리스 규약
8:- [verification-commands.md](verification-commands.md) — 이 저장소의 실제 게이트 명령(make 레포 아님, 실행 확인됨)
R4_PROCESS_ENTRYPOINT=PASS
```

→ `docs/sot/INDEX.md`가 두 변경 정본을 다음 세션의 진입점으로 연결합니다. 제품 런타임 코드는 바꾸지 않았으므로 동적 호출 경로와 라이브 제품 1건은 비범위입니다.

### V1 Claude 1차 판정

- 실행 신원: `claude 2.1.237`, 모든 실행에서 `env -u ANTHROPIC_API_KEY` 적용.
- 1차 원명령: 저장소 읽기 도구를 허용한 `claude -p`. 210초 무출력 뒤 `Client.listTools() called but server does not advertise tools capability`와 `Execution error`; `NOT_RUN`.
- 2차 복구: `--safe-mode --tools 'Bash,Read,Grep,Glob'`. 180초 무출력 뒤 `Execution error`; `NOT_RUN`.
- 환경 분해: `--safe-mode --tools '' -p 'Reply exactly: CLAUDE_OK'`는 4초 안에 `CLAUDE_OK`, 종료값 0. 인증 자체가 아니라 저장소 도구 연결 경로 결함으로 좁혔습니다.
- 3차 복구: 변경 diff·관련 정본·실행 증거를 입력에 직접 포함하고 도구 없는 독립 검토를 실행. 종료값 0, `VERDICT: FAIL`.
- 프롬프트 해시: `56ec38c75ce8aab1d09ee53b29cdc533ef2ac20fd213455162920fa85d2e7b95`.
- 판정문 해시: `cc4c1337d7ace85342dc709d44d9286e2f1e0485663916f56d27cd93af752a78`.
- 판정 원문: `docs/engineering/work-unit-methodology-v1-verdict-2026-08-21.md`.

V1이 잡은 결함은 C1/M1의 OR 검사, C2의 미갱신 장부·로그, M2의 push/pre-push 위치, M3의 비측정 PR 상한, 문체 혼용, 고위험 목록 이중 정의, 변경 전 줄 기준 미표시입니다. 모두 채택했으며 V1 재검토 전까지 WU 상태는 PASS가 아닙니다.

### V1 실행 재검토 — 비용 제약으로 NOT_RUN

- 표준 `omx ask claude` 실행은 종료값 1과 `Credit balance is too low`를 반환해 저장소 명령을 시작하지 못했습니다.
- 환경 API 키를 제거한 로그인 경로는 무출력 대기 중 사용자의 “Claude는 돈 쓰면 안 된다” 지시에 따라 즉시 중단했습니다.
- 이후 Claude 유료 실행은 시도하지 않습니다. 도구 없는 문서 검토를 실행 REVIEW PASS로 승격하지도 않습니다.
- 실행 프롬프트: `docs/engineering/work-unit-methodology-v1-recheck-prompt-2026-08-21.md`.
- 판정 기록: `docs/engineering/work-unit-methodology-v1-recheck-verdict-2026-08-21.md`.

→ Claude V1 실행 REVIEW는 `NOT_RUN`입니다. 새 Codex 맥락의 독립 실행 검증은 구현 증거를 보강하지만, 현재 strict 계약에서 Claude V1을 실행한 것으로 대체하지 않습니다. 따라서 전체 strict 최종 판정은 PASS가 아닙니다.

### 비용 없는 독립 실행 REVIEW·codeaudit — PASS

깨끗한 HEAD `cbe3d6b`에서 새 Codex verifier와 codeaudit를 서로 다른 맥락으로 실행했습니다.

```text
verifier: PASS
pwd: /Users/kangsangmo/Desktop/Valuehire_v6/worktrees/work-unit-methodology
branch: task/work-unit-methodology
HEAD: cbe3d6b
principles: WORK_UNIT_METHOD 28/28
mutations: CHECKED 53, VERDICT PASS, SOURCE-TREE 불변
docs SOT / bash -n / diff check: exit 0

codeaudit: APPROVE
additive weakening 격리 재현:
  전체 적대검증은 생략할 수 있다
  → WORK_UNIT_CONTRACT_WEAKENED: FINAL_ADVERSARIAL_OPTIONAL
유료 외부 검토 비필수·동일 권한 신원 보증 한계: 수용
```

첫 verifier 실행은 검증 도중 goal·SOT를 동시에 편집해 `SOURCE-TREE` 불변 검사가 실패했습니다. 파일을 커밋해 안정된 트리로 만든 뒤 같은 verifier가 재실행해 PASS했으므로, 첫 실패는 검사 결함이 아니라 동시 편집 운영 결함으로 분류합니다.

### 전체 pre-push — PASS

깨끗한 HEAD `cbe3d6b`에서 `hooks/pre-push`를 직접 실행했습니다.

```text
WORK_UNIT_METHOD: PASS 28/28
pre-push: 검사 21개 실행
21개 모두 ok
종료값: 0
```

로컬에서 논리적으로 실행할 수 없는 세 검사는 기존 계약대로 명시적으로 분리됐습니다: `acceptance-0-2.sh`, `acceptance-0-5.sh`는 CI 담당으로 DEFERRED, `acceptance-0-7.sh`는 push 수행 검사라 CI 담당입니다. 이 분리는 이번 변경에서 새로 만든 skip이 아닙니다.

→ WU-01~03의 로컬 구현·반증·독립 실행 REVIEW·codeaudit는 PASS입니다. 원격 PR·GitHub CI·merge는 실행하지 않았고, Claude V1도 비용 제약으로 `NOT_RUN`이므로 이를 전체 strict 또는 배송 완료 PASS로 확대하지 않습니다.

### 통합 검사 — V1 보정 중간점

실행 시각 `2026-08-21T03:12:55+0900`, 기준 HEAD `9a3c8623c3bb481e679c79763f131eb303214a03`, 미커밋 diff 해시 `9e2c584781b969328cfedca317e257fba7dec97b9000c597a95429121e2d5c3f`.

```text
git diff --check: exit 0
bash scripts/check-docs-sot.sh: exit 0
bash scripts/acceptance-principles-check.sh: exit 0
VERDICT: PASS
SOT_LOAD: PASS docs/sot/coding-principles.md
LEDGER_LOAD: PASS docs/sot/principles.yaml
MECHANISMS: PASS 32/32 strict-contract-bindings
WIRING: PASS pre-push=1 ci=1
CHECKED: 32
```

→ 문서 형식·SOT 크기·원칙 직접 로드와 배선은 통과했습니다. 그러나 마지막 독립 판정은 아직 FAIL이므로 이 출력만으로 전체 PASS가 아닙니다.
