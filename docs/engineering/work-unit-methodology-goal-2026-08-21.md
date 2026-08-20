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

- `docs/sot/git-workflow.md:15` 역할: 현재는 작업·worktree·브랜치·인수 기준을 모두 1:1로 묶어 PR보다 작은 증명 경계를 표현하지 못합니다.
- `docs/sot/git-workflow.md:21` 역할: PR도 인수 기준 1개로 고정해 하나의 목표 안에서 서로 의존하는 여러 작은 주장을 순서대로 닫는 방법이 없습니다.
- `docs/sot/verification-commands.md:10-16` 역할: 저장소 전체 게이트 명령은 적혀 있지만 Work Unit 표적 검사와 PR 전체 통합 검사의 질문·시점이 분리되어 있지 않습니다.
- `docs/sot/coding-principles.md`의 P2·P5·P13·P15 역할: 실행 가능한 인수 기준, RED 이후 시험 불변, 검사 약화 공격, 최종 서버 검사를 이미 요구합니다. 새 방법론은 이 원칙들을 다시 만들지 않고 실행 순서와 경계만 연결합니다.

근본 원인은 검사 종류의 부족이 아니라 **큰 구현과 최종 검사 사이에 닫힌 증명 경계가 없는 것**입니다.

## 범위와 위험등급

- 위험등급: **L3** — SOT 두 파일의 개발·검증 흐름을 바꿉니다.
- 변경 범위: `docs/sot/git-workflow.md`, `docs/sot/verification-commands.md`, 이 goal 문서.
- 비범위: GitHub Pro 결제, branch protection, CODEOWNERS, 새 Agent 런타임, CI·훅·검사 스크립트 변경, 기존 P0 결함 구현.
- 영향 반경: 이후 모든 코드·제품 작업의 분해, 커밋, 검증 순서. 제품 런타임과 후보자 데이터에는 직접 영향이 없습니다.

## 입출력·오류·경계 계약

### 입력

- 하나의 ISSUE 또는 요구사항 문서.
- 실행 가능한 인수 기준과 가짜 합격 시나리오.
- 저장소의 현재 위험등급·SOT·실제 검증 명령.

### 출력

- Work Unit 1~N개. 각 항목은 ID, 주장 1개, 선행 관계, 위험등급, 정확한 검증 명령·기대값, 반증 1~3개, 변경 범위, 완료 커밋을 가집니다.
- 각 Work Unit은 `PASS / FAIL / NOT_RUN / BLOCKED` 중 하나로 기록합니다.
- 모든 Work Unit이 PASS여도 PR 전체 strict·codeaudit·결합 적대검증·CI가 별도로 남습니다.

### 오류

- 주장이 둘 이상이거나 `CI 개선`, `검증 시스템 완성`처럼 반증할 수 없으면 분해 실패입니다.
- 표적 검증 명령이 없거나 검사 대상이 0개면 `NOT_RUN`이며 완료할 수 없습니다.
- 반증이 실패하거나 독립 검토가 필요한 고위험 경로에서 검토가 없으면 `FAIL` 또는 `NOT_RUN`입니다.

### 경계

- 파일 수·줄 수로 Work Unit을 나누지 않습니다.
- `.github/workflows/**`, `hooks/**`, `scripts/acceptance-*`, `verify*`, `mechanism-registry`, 비밀·개인정보, 배포, 인증·로그인은 고위험 Work Unit입니다.
- 일반 Work Unit은 표적 검사와 반증 1~3개로 닫고, 고위험 Work Unit은 독립 검토를 추가합니다.
- Agent 교체는 선택입니다. 같은 세션에서도 구현 맥락과 검증 질문을 분리할 수 있어야 합니다.

## 인수 기준과 counter-AC

### AC-1 — Work Unit 경계

**When** 하나의 목표가 여러 독립 주장을 포함하면, 시스템은 목표를 Work Unit 1~N개로 나누고 각 Work Unit을 하나의 주장과 완료 커밋 경계로 기록해야 합니다.

- 검증 명령: `rg -n "Work Unit|하나의 주장|완료 커밋|squash" docs/sot/git-workflow.md`
- 기대값: 종료값 0이며 네 개념이 모두 현재 규칙에 설명됩니다.
- counter-AC: Work Unit을 파일 단위로 정의, 여러 Work Unit을 한 완료 커밋에 혼합, squash 뒤 개별 커밋 revert 가능하다고 기록.

### AC-2 — 두 층의 검증

**When** Work Unit 구현이 끝나면, 시스템은 해당 AC와 작은 반증을 먼저 실행하고, 모든 Work Unit 뒤에는 strict·codeaudit·전체 적대검증·CI를 별도로 실행해야 합니다.

- 검증 명령: `rg -n "LOCAL VALIDATE|작은 적대검증|전체 strict|전체 codeaudit|전체 적대검증|GitHub verify CI" docs/sot/verification-commands.md`
- 기대값: 종료값 0이며 Work Unit과 PR 전체 검사의 질문·시점이 분리됩니다.
- counter-AC: Work Unit마다 full codeaudit 강제, 최종 통합 검사를 삭제, CI 초록을 로컬 PASS로 대체.

## Work Unit 장부

| ID | 하나의 주장 | 선행 | 위험 | 완료 경계 | 상태 |
|---|---|---|---|---|---|
| WU-01 | 목표·Work Unit·커밋·PR의 관계가 하나의 주장 단위 검토를 보존합니다. | 계약 RED | L3(SOT) | `docs/sot/git-workflow.md` 단독 완료 커밋 | OPEN |
| WU-02 | Work Unit 표적 검사와 PR 전체 통합 검사가 서로 다른 질문과 시점으로 분리됩니다. | WU-01 | L3(SOT) | `docs/sot/verification-commands.md` 단독 완료 커밋 | OPEN |

### RED 계약

- 같은 명령으로 AC-1·AC-2의 필수 문구 부재를 먼저 확인합니다.
- RED는 문법 오류나 파일 누락이 아니라 아직 Work Unit 절차가 정본에 없어서 실패해야 합니다.
- WU 완료 커밋은 이 AC의 기대값을 바꾸지 않습니다.

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
4. GREEN: WU-01, WU-02를 서로 다른 완료 커밋으로 닫습니다.
5. R2: 임시 고장 사본에서 “최종 검사를 삭제”, “파일 단위 WU”, “모든 WU full audit”을 주입해 AC 위반임을 확인합니다.
6. R4: `docs/sot/INDEX.md → git-workflow.md / verification-commands.md` 참조 경로와 실제 사용 명령을 확인합니다.
7. 통합: `bash scripts/check-docs-sot.sh`, `bash scripts/acceptance-principles-check.sh`, 관련 전체 검증을 실행합니다.
8. V1: Claude가 외부 의존 과잉, 기존 P5 충돌, squash 롤백 과장, 고위험 경로 누락을 공격합니다.
9. V2: 새 Codex 맥락이 V1의 파일·명령·판정을 재현하고 반대 방향으로 재공격합니다.

## 적대 검증 로그

아직 실행 전입니다. 실행 신원·명령·시각·종료값·전체 출력·해시는 구현 뒤 여기에 추가합니다.
