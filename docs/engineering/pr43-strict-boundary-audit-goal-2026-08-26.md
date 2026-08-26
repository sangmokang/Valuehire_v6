# PR #43 Strict 파일 경계 감사·수정 goal (2026-08-26)

## 1층 결론

현재 PR #43은 병합하면 안 된다. 저장소는 직접 작성 파일을 600줄까지 허용하지만 실제 Strict 검사기는 501줄부터 거부하고, 변이 시험은 이 잘못된 기준을 합격으로 판정한다.

이 작업은 검사기가 현재 저장소 정본의 600줄 경계를 직접 읽도록 고치고, 600줄 통과·601줄 실패를 독립 표본으로 증명한 뒤 새 원격 커밋 검증에 넘긴다.

## 2층 판단 근거

- 정본인 `docs/sot/coding-principles.md`의 P11은 파일 hard 한도를 600 LOC로 정한다.
- 파생 장부인 `docs/sot/principles.yaml`도 `hard600`을 기록한다.
- `scripts/verify/check-strict-principles-skills.sh`는 500을 하드코딩해 501줄을 거부한다.
- `scripts/acceptance-principles-mutations.sh`와 `docs/sot/verification-commands.md`는 500/501을 올바른 경계로 설명해 거짓 정상 상태를 만든다.
- 이 불일치는 PR #43에서 처음 생기지 않았지만, PR #43이 해당 변이 시험을 수정하고 전체 원칙 검증 보존을 주장하므로 현재 후보의 병합 판정을 막는다.

## 모드와 범위

- 모드: code-change
- 위험등급: L3
- 근거: 검사기·변이 시험·검증 정본 문서를 함께 바꾸며 CI 판정 의미에 영향을 준다.
- 기준 HEAD: `b93b98b7454d833f067adc2cbe31073e1e2bd9d3`
- 기준 main: `c59bad7b160c473cda5545e76e6fa6bcc711a7ea`
- 대상:
  - `scripts/verify/check-strict-principles-skills.sh`
  - `scripts/acceptance-principles-mutations.sh`
  - `docs/sot/verification-commands.md`
- 비범위:
  - 히스토리 스캐너 동작 확대
  - Issue #22 reachable commit/tree/tag 확대
  - PR 병합, PR #29 종료, push, PR 본문 수정

## 현재 상태와 근본 원인

### 현재 상태

```text
docs/sot/coding-principles.md:26  P11 file hard 600 LOC
docs/sot/principles.yaml:108    file hard600
scripts/verify/check-strict-principles-skills.sh:74  lines > 500 이면 실패
scripts/acceptance-principles-mutations.sh:284-312  500 통과/501 실패를 합격으로 판정
```

→ 같은 저장소의 정본과 판정기가 서로 다른 경계를 사용한다. 현재 변이 시험의 초록불은 정본 준수를 증명하지 못한다.

### 근본 원인

검사기가 저장소 정본에서 hard 한도를 읽지 않고 Strict 기본 fallback 값 500을 고정값으로 사용했다. 변이 시험도 같은 잘못된 값을 기대해 구현과 시험이 함께 틀린 상관 결함이 됐다.

## 계약

### 입력

`check-strict-principles-skills.sh <codex-skill.md> <claude-skill.md>`는 두 스킬 파일을 입력으로 받고, 검사기 자신의 저장소에 있는 `docs/sot/coding-principles.md`를 경계 정본으로 읽는다.

### 처리

1. 검사기는 자신의 경로에서 저장소 루트를 고정한다.
2. P11의 파일 hard LOC 값이 정확히 하나 존재하는지 확인한다.
3. 두 스킬의 물리적 줄 수가 hard 값 이하인지 비교한다.
4. 공통 계약과 엔진 순서 검사는 기존과 동일하게 유지한다.

### 출력과 오류

- 모든 계약 충족: 종료값 0, `VERDICT: PASS`, 읽은 hard 한도와 두 파일 줄 수 출력.
- 스킬 내용·경계 위반: 종료값 1, `VERDICT: FAIL`, 구체 오류 출력.
- 정본 누락·빈 파일·P11 hard 값 파싱 불가: 종료값 2, `VERDICT: NOT_RUN`, 이유 출력.
- 검사 대상 0개는 존재할 수 없다. 두 스킬 경로는 필수이며 누락 시 종료값 2다.

### 경계

- 현재 정본 hard 값 600과 같은 600줄 정상 사본은 통과해야 한다.
- 601줄 고장 사본은 `LINE_LIMIT_EXCEEDED`로 실패해야 한다.
- 실제 두 스킬의 현재 줄 수는 600 이하여야 한다.

## EARS 인수 기준

### AC-1 정본 경계 사용

When 검사기가 정상 Strict 스킬 두 개를 검사하면, 시스템은 현재 저장소 P11에서 읽은 hard 600을 사용해야 한다.

- 검증: `bash scripts/acceptance-principles-mutations.sh`
- 기대: `BOUNDARY-600 ... PASS`, `BOUNDARY-601 ... FAIL`, 전체 종료값 0.
- counter-AC: 검사기와 시험이 모두 500/501을 기대해 함께 초록이 되는 상태.

### AC-2 실패 폐쇄

If 검사기 저장소의 P11 hard 한도를 읽을 수 없으면, 시스템은 기본값으로 조용히 통과하지 않고 NOT_RUN 종료값 2를 내야 한다.

- 검증: 변이 시험의 격리 사본에서 P11 경계 문구를 제거한 뒤 검사기 실행.
- 기대: `VERDICT: NOT_RUN`, 종료값 2.
- counter-AC: 파싱 실패를 500 또는 600 기본값으로 대체해 초록으로 만드는 상태.

### AC-3 기존 보호 보존

While 파일 경계 계약을 수정해도, 시스템은 공통 계약 불일치·엔진 순서 오류·누락 SOT·0건 배선·CI 실패 무시 반례를 계속 차단해야 한다.

- 검증: `bash scripts/acceptance-principles-check.sh`, `bash scripts/acceptance-principles-mutations.sh`, `bash scripts/acceptance-semantic-mutations.sh`, `bash verify.sh`.
- 기대: 각 원명령 종료값 0과 명시된 CHECKED 수.
- counter-AC: 600/601만 맞추고 기존 반례 하나를 삭제하거나 기대값을 약화하는 상태.

### AC-4 보고와 원격 SHA 정직성

When 로컬 수정으로 HEAD가 PR #43 원격 head와 달라지면, 시스템은 기존 원격 Actions를 새 코드의 합격 근거로 재사용하지 않고 다음 SHIP 작업을 REQUEST_CHANGES로 넘겨야 한다.

- 검증: `git rev-parse HEAD`, `git rev-parse origin/task/pr29-history-scan-final-20260825`, `gh pr view 43 --json headRefOid,statusCheckRollup`.
- 기대: push 전에는 원격 검증을 새 SHA의 PASS로 주장하지 않는다.
- counter-AC: 옛 `b93b98b...` Actions 초록을 새 로컬 커밋에 귀속하는 상태.

## Harness 게이트와 적대검증

- Gate 0: SOT 직접 로드, 원칙 검사, 현재 HEAD·main·원격 후보 고정.
- Gate 1: 위 AC와 입력·출력·오류·경계 계약 고정.
- Gate 2: 기존 501줄 표본이 잘못 실패하는 RED를 독립 재현.
- Gate 3: 변이 시험을 600/601 계약으로 먼저 바꿔 RED를 만든 뒤 검사기 최소 수정으로 GREEN.
- Gate 3.5: `verify.sh` → 원칙 변이 시험 → Strict 스킬 검사기의 실제 호출 경로 확인.
- Gate 4: 전체 관련 로컬 검증과 R2 고장 사본 통과.
- Gate 5: 로컬 CHECKPOINT만 만든다. push·PR 갱신·원격 CI는 다음 Strict 프롬프트 범위다.

V1은 Claude가 정본 추출 실패, 600/601, 검사기·시험 동시 약화, 저장소 밖 결합을 공격한다. V2는 새 Codex 맥락에서 V1의 모든 결함과 PASS 근거를 재현하고 과장·누락을 반대로 공격한다.

## 영향 반경·데이터 안전·롤백

- 영향 반경: Strict 스킬 대칭성 검사와 이를 부르는 원칙 변이 시험, 검증 명령 문서.
- 데이터 안전 AC: 제품 데이터·자격증명·외부 서비스에 읽기/쓰기를 하지 않는다. 모든 고장 표본은 `mktemp` 아래에서 실행한다.
- 롤백: 로컬 CHECKPOINT 커밋을 `git revert <sha>`로 되돌린다. 원격 push 전이므로 main과 PR 원격 코드에는 영향이 없다.

## 검증 장부

| 시각 | 세션 | HEAD | 명령 | 종료값 | 상태 | 핵심 출력 |
|---|---|---|---|---:|---|---|
| 2026-08-26T09:23:35+09:00 | strict-pr43-reaudit-20260826 | b93b98b7454d833f067adc2cbe31073e1e2bd9d3 | `bash scripts/acceptance-principles-check.sh` | 0 | PASS | `CHECKED: 34` |
| 2026-08-26T09:24:12+09:00 | strict-pr43-reaudit-20260826 | b93b98b7454d833f067adc2cbe31073e1e2bd9d3 | `bash scripts/acceptance-principles-mutations.sh` | 0 | FAIL(계약) | 잘못된 `BOUNDARY-500 PASS`·`BOUNDARY-501 FAIL`을 전체 PASS로 인정 |

## 결정 카드

> **무엇을** — 검사기가 저장소 정본의 P11 hard 값을 직접 읽게 한다.
> **왜** — 숫자를 두 곳에 복제하면 정본 변경 뒤 검사와 시험이 함께 낡아도 초록이 될 수 있다.
> **버린 길** — 하드코딩 500을 600으로만 바꾸는 방법은 다음 정본 변경에서 같은 결함이 재발하므로 기각한다.
> **대가** — 정본이 누락되거나 형식이 깨지면 스킬 검사도 NOT_RUN으로 멈춘다.
> **되돌리기** — CHECKPOINT 커밋 하나를 revert하면 원래 동작으로 돌아간다.

## 적대 검증 로그

### Codex local verification

| 시각 | 세션 | HEAD | 명령 | 종료값 | 상태 | 핵심 출력 |
|---|---|---|---|---:|---|---|
| 2026-08-26T09:36:14+09:00 | strict-pr43-reaudit-20260826 | b93b98b7454d833f067adc2cbe31073e1e2bd9d3+local | `bash scripts/verify/run-acceptance.sh scripts/acceptance-principles-mutations.sh` | 0 | PASS | `BOUNDARY-600 ... PASS`, `BOUNDARY-601 ... FAIL`, `C16 ... NOT_RUN`, `CHECKED: 43` |
| 2026-08-26T09:36:14+09:00 | strict-pr43-reaudit-20260826 | b93b98b7454d833f067adc2cbe31073e1e2bd9d3+local | `bash scripts/acceptance-ci-step-integrity.sh` | 0 | PASS | `CHECKED: 14` |
| 2026-08-26T09:36:14+09:00 | strict-pr43-reaudit-20260826 | b93b98b7454d833f067adc2cbe31073e1e2bd9d3+local | `bash scripts/verify/run-acceptance.sh scripts/acceptance-history-scan-failclosed.sh` | 0 | PASS | `CHECKED: 18` |
| 2026-08-26T09:36:14+09:00 | strict-pr43-reaudit-20260826 | b93b98b7454d833f067adc2cbe31073e1e2bd9d3+local | `bash scripts/verify/run-acceptance.sh scripts/acceptance-0-2-unreachable-content.sh` | 0 | PASS | `CHECKED: 23` |
| 2026-08-26T09:36:14+09:00 | strict-pr43-reaudit-20260826 | b93b98b7454d833f067adc2cbe31073e1e2bd9d3+local | `bash scripts/verify/run-acceptance.sh scripts/acceptance-verify-ac-m.sh` | 0 | PASS | `CHECKED: 33` |
| 2026-08-26T09:36:14+09:00 | strict-pr43-reaudit-20260826 | b93b98b7454d833f067adc2cbe31073e1e2bd9d3+local | `bash scripts/verify/run-acceptance.sh scripts/acceptance-principles-check.sh` | 0 | PASS | `CHECKED: 34` |
| 2026-08-26T09:36:14+09:00 | strict-pr43-reaudit-20260826 | b93b98b7454d833f067adc2cbe31073e1e2bd9d3+local | `bash scripts/acceptance-semantic-mutations.sh` | 0 | PASS | `CHECKED: 10` |
| 2026-08-26T09:36:14+09:00 | strict-pr43-reaudit-20260826 | b93b98b7454d833f067adc2cbe31073e1e2bd9d3+local | `bash verify.sh` | 0 | PASS | `PASS: no secret-pattern match in any tracked file, .env not tracked` |
| 2026-08-26T09:36:14+09:00 | strict-pr43-reaudit-20260826 | b93b98b7454d833f067adc2cbe31073e1e2bd9d3+local | `bash scripts/scan-history-secrets.sh` | 0 | PASS | `PASS: 히스토리 전량 blob 스캔 0건 (blob 1364개 검사)` |
| 2026-08-26T09:36:14+09:00 | strict-pr43-reaudit-20260826 | b93b98b7454d833f067adc2cbe31073e1e2bd9d3+local | `shellcheck -S warning scripts/verify/check-strict-principles-skills.sh scripts/acceptance-principles-mutations.sh` | 0 | PASS | warning 이상 0건 |

V1·V2와 원격 Actions는 아직 새 로컬 변경에 대해 실행하지 않았다. 다음 Strict SHIP 프롬프트에서 새 커밋 SHA를 push하고 그 SHA에 귀속된 원격 검사와 Claude/Codex 적대검증을 다시 실행한다.
