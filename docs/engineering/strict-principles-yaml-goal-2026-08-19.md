# PR #31 principles.yaml 재작업 — goal (2026-08-19)

## 사장님 브리핑

**현재 결론:** PR #31의 로컬 구현은 보강할 수 있지만, push 금지 때문에 새 커밋에서 GitHub Actions가 새 검사를 실제 실행했는지는 이번 작업에서 증명할 수 없다. 최종 판정의 상한은 `로컬 CI-equivalent PASS 또는 PARTIAL / 실제 서버 실행 BLOCKED / 병합 불가`다. PR #32 브랜치는 읽기 전용으로만 감사하며, 이 브랜치에서는 정정 계획만 남긴다.

**판단 근거:** 현재 `principles.yaml`은 32개 원칙의 현황을 기록하지만 `acceptance-principles-check.sh`는 스키마·실제 경로·실행 배선을 엄격히 검사하지 않고, CI도 그 스크립트를 실행하지 않는다. P1은 “32개 원칙 전부가 기계 장치를 갖고 CI에서 실행되며, 하나라도 미충족이면 실패”라고 요구하므로 현황 기록이 있다는 사실만으로 P1을 완료 처리할 수 없다.

**틀리면 깨지는 것:** 미구현 원칙이나 죽은 경로가 초록으로 보이고, 필수 파일 두 개를 함께 삭제해도 훅과 CI가 통과하며, 기존 원격 초록을 새 로컬 변경의 증거로 오인하게 된다.

## 1. 작업 경계와 시작 기준선

| 작업공간 | 브랜치 | 시작 HEAD | 시작 `git status --porcelain` | 권한 |
|---|---|---|---|---|
| 저장소 루트 | `main` | `7bd3298695c93e0e60bdabd2500840da47c4db05` | 빈 출력 | 읽기 전용 |
| PR #31 worktree | `task/strict-principles-yaml` | `929247a27e4d36af28cdb5de8c95510689635068` | 빈 출력 | 이번 작업 수정 |
| PR #32 worktree | `task/codeaudit-wrap-2026-08-19` | `a3527a2836bf843a75fb494f00eefdff71385be7` | 빈 출력 | 읽기 전용 |

- root와 PR #32 worktree는 종료 시 시작 기준선과 같아야 한다.
- PR #31만 수정한다. PR #32 브랜치 checkout·merge·cherry-pick·파일 혼입은 금지한다.
- push·merge·배포와 전역 `~/.claude`, `~/.codex` 수정은 금지한다. 메일은 후속 사용자 지시로 모든 검증·기록이 끝난 뒤 `sangmokang`에게 실제 판정 그대로 완료 보고하는 1통만 허용한다.
- 임시 변조는 `mktemp` 격리 저장소에서만 수행하고 Git 환경변수를 먼저 해제한다.

## 2. SOT와 현재 재현

- `docs/sot/coding-principles.md`: P1은 32개 전체의 기계 장치와 CI 실행, 미충족 시 실패를 요구한다. P13은 5개, P14는 4개 요건 전체가 있어야 완전이다.
- `docs/sot/hook-contracts.md`: pre-commit은 stage 기준, pre-push는 깨끗한 worktree와 `acceptance-*.sh` 글로브를 계약으로 삼는다.
- `docs/sot/verification-commands.md`: 이 저장소는 Make/npm 저장소가 아니며 실제 게이트는 `scripts/session-status.sh`, `verify.sh`, workflow의 고정 스텝이다.
- `docs/sot/mechanism-registry.yaml`은 3개 장치만 다루므로 32개 원칙의 P1 판정을 대신하지 못한다.
- Ruby 2.6.10의 표준 YAML 엔진 Psych가 현재 환경에서 `Psych.safe_load`로 `principles.yaml` 32개를 읽는다. Python 표준 라이브러리에는 YAML 파서가 없으므로 Python 정규식/가짜 표준 YAML 주장은 폐기한다.
- 시작 시 `mechanism_found`는 `null` 또는 자유 문자열이다. 단일 경로, 여러 경로, `file:line`, 설명문, `~/.claude` 외부 경로가 한 필드에 섞여 있어 기계 판정 계약이 아니다.
- `git diff --check 7bd3298...929247a`는 D3 판정문의 후행 공백으로 종료값 2를 재현했다.
- PR #31/#32의 기존 `gh pr checks`는 기존 원격 HEAD의 두 `verify` 작업만 초록이다. 새 로컬 변경이나 새 principles 검사 실행 증거가 아니다.
- `docs/engineering/strict-principles-yaml-d3-3rd-verdict-2026-08-19.md`의 첫 줄은 `VERDICT: FAIL`이다. “Codex 3회 전부 PASS”로 요약하지 않는다.

## 3. 설계 결정 — B안

### 선택

`docs/sot/principles.yaml` 자체를 P1의 32개 강제 목록으로 정의한다.

- 파일은 현황을 정직하게 기록할 수 있다. 다만 `부분`, `없음`, `미확인`, CI 실행 경로 없음이 하나라도 있으면 P1 전체 판정은 실패한다.
- 정상 파일은 “YAML·스키마·기록된 경로 검증”에는 합격할 수 있지만, 현재 32개가 모두 충족되지 않으므로 기본 전체 실행은 의도적으로 `P1_UNMET`과 종료값 1을 낸다.
- CI와 pre-push는 진단용 스키마 모드가 아니라 기본 전체 실행만 사용한다.

### 버린 A안

현황표와 별도 registry를 나누는 A안은 선택하지 않는다. 보정 지시대로 별도 registry도 P1~P32 전체를 포함하고 미구현 항목에서 실패해야 하므로 합격 조건은 B안과 같다. 동일한 32개 ID·상태·경로를 두 파일에 중복하면 동기화 회귀 표면만 늘어난다. A안을 버린 것은 P1 의무를 완화하기 위해서가 아니다.

## 4. `mechanism_found` 계약

상위 항목은 정확히 다음 6개 키만 갖는다.

```yaml
- id: string
  principle: non-empty string
  mechanism_expected: non-empty string
  mechanism_found:
    - path: repository-relative file path
      check: repository-relative executable verifier path
      stages: [pre-commit, pre-push, session-start, acceptance, ci]
  status: 완전|부분|없음|해당없음|미확인
  evidence: non-empty string
```

세부 계약:

- `완전`·`부분`: `mechanism_found`는 비어 있지 않은 목록이며 각 원소는 정확히 `path`, `check`, `stages`만 가진다.
- `없음`·`해당없음`·`미확인`: `mechanism_found`는 `null`이다.
- `path`와 `check`는 절대경로, `..`, glob, `~`, `file:line`, 설명문을 허용하지 않는 저장소 상대경로다. 둘 다 일반 파일로 존재해야 하고 `check`는 실행 가능해야 한다.
- `path`는 구현 장치, `check`는 그 장치를 실행 검증하는 파일이다. 같은 파일을 자기 증거로 적는 것은 허용하지 않는다.
- `stages`는 호출 지점을 구조화해 기록한다. 파일 존재와 실행 배선은 별도 검증한다. `ci`가 있으면 workflow의 `run` 명령에서 `check`의 실제 실행을 찾아야 한다. 로컬 실행 결과와 서버 실행 결과도 분리해 보고한다.
- 설명은 `evidence`에만 둔다. 한 문자열을 임의로 잘라 경로로 해석하지 않는다.

## 5. 상태 재분류와 실제 집계

- 작업 시작 기준값: `완전 6 / 부분 12 / 없음 5 / 해당없음 4 / 미확인 5`.
- 과거 초안의 `완전 8 / 부분 10`은 폐기된 과거 수치다. V1/V2 원문에는 역사 기록 배너를 붙여 현재 수치가 아님을 명시했다.

| ID | 정정 전 | 정정 후 | 근거 |
|---|---|---|---|
| P11 | 부분 | 없음 | 기록한 검사 파일이 현재 브랜치에 없다. |
| P13 | 완전 | 부분 | SOT의 5개 요구 중 자기 포함·만료 억제·약화 탐지만 확인되고 권한 분리와 서버 보호는 없다. |
| P14 | 완전 | 부분 | 판정 수치의 코드 생성만 확인되고 나머지 3개 요구는 없다. |
| V-1 | 완전 | 미확인 | 전역 스킬은 이 저장소와 CI가 실행·검증할 수 없다. |
| V-2 | 완전 | 미확인 | 전역 스킬은 이 저장소와 CI가 실행·검증할 수 없다. |
| V-4 | 부분 | 없음 | 저장소 안 기계 장치가 없다. |
| V-5 | 완전 | 미확인 | 전역 스킬은 이 저장소와 CI가 실행·검증할 수 없다. |

Psych 재계산 최종값은 `완전 1 / 부분 12 / 없음 7 / 해당없음 4 / 미확인 8`이다. 완전은 5건 감소했고, 부분은 P11·V-4 감소와 P13·P14 증가가 상쇄돼 12건으로 같다. 없음은 2건, 미확인은 3건 늘었다.

## 6. Acceptance Criteria

### AC1 — 엄격한 YAML 스키마

- Psych가 읽은 구조를 정본으로 삼고 AST에서 중복 매핑 키를 별도 거부한다.
- ID는 정확히 32개이며 각 항목 상위 키는 정확히 6개다.
- unknown field, 중복 필드, 빈 `principle`·`evidence`, 계약 밖 status/type/value, 깨진 YAML은 실패한다.
- `principle`은 `coding-principles.md`의 원문 표제와 일치해야 한다.

### AC2 — 실제 mechanism 연결

- `완전`·`부분`의 `mechanism_found` 빈 값은 실패한다.
- 구조화된 `path`·`check`의 존재, `check` 실행권한, 호출 stage 배선을 검증한다.
- 경로 존재만으로 실행 완료라 부르지 않는다. 삭제 mutation은 탐지하고, 내용 약화의 일반 탐지는 이번 범위 밖이라고 명시한다.

### AC3 — CI 연결과 자기 삭제 방어

- workflow에 필수 파일 두 개의 고정 존재 확인과 `bash scripts/acceptance-principles-check.sh` 직접 실행 스텝을 둔다.
- pre-commit·pre-push도 글로브와 별개로 고정 필수 파일을 확인한다.
- 삭제·이름 변경은 차단하고 정상 추가/존재 대조군은 통과시킨다.
- 실제 새 서버 실행은 `BLOCKED — push 금지로 새 커밋에 대한 서버 실행 불가`다.

### AC4 — status 회귀와 첫 도입

- `origin/main`에 기준 파일이 있으면 status 하락을 실패시킨다.
- 없으면 `BASELINE_NOT_AVAILABLE`을 출력하고 회귀 PASS로 세지 않는다. 첫 도입 자체는 다른 검사 결과에 따라 진행할 수 있다.
- 첫 병합 뒤 `origin/main`에 파일이 생긴 다음 PR부터 기준선 검사가 활성화된다.
- 정당한 사실 정정은 전용 PR에서 실패 증거와 새 상태를 공개하고 오너가 실패 상태를 인지해 결정한다. 숨은 우회 플래그는 두지 않으며, 병합 뒤 새 main이 다음 기준선이 된다.

### AC5 — guard의 정직한 범위와 복구

- `chmod 444`를 쓰기 원천 차단으로 부르지 않는다. 동일 UID 사용자는 chmod·내용·상태 파일을 바꿀 수 있다.
- 별도 소유자·외부 감독자·OS 불변 앵커가 이 작업 권한 안에 없으므로 guard는 우발적 변경 억제와 변조 탐지 장치로 한정한다.
- lock은 모든 대상 사전검사 뒤 적용하고 실패·신호 시 이미 바꾼 권한을 되돌린다. 비정상 종료 뒤 상태 파일로 복구할 경로를 둔다.
- 정상 unlock은 성공한 check 뒤만 허용한다. 무결성을 증명하지 못한 강제 복구는 별도 명령과 경고로 분리한다.
- guard 공격 시험은 복제본에서만 한다. 실제 전역 파일의 같은 해시는 적대자 방어 성공 증거가 아니다.

### AC6 — 문서 정합성과 공백

- P13/P14와 최종 집계, goal·SOT·검증표를 일치시킨다.
- D3 `VERDICT: FAIL`을 그대로 보존하고 기존 후행 공백을 제거한다.
- PR #32 roadmap/보고의 잘못된 완료·guard·검증 요약은 읽기 전용 감사 결과와 별도 정정 계획으로만 남긴다.
- `git diff --check` 종료값 0을 요구한다.

### AC7 — RED→GREEN 및 대조군

격리 mutation harness를 먼저 추가해 현 구현에서 실패(RED)를 확인한 뒤 최소 구현으로 다음을 판별한다.

1. unknown field → 실패
2. 빈 evidence 및 `완전`/`부분`의 빈 mechanism → 실패
3. 필수 파일 삭제 → pre-commit 실패
4. 필수 파일 삭제 → 로컬 CI-equivalent 실패
5. ID 변경 → 실패
6. 깨진 따옴표 → 실패
7. status 하락 + 기준선 존재 → 실패
8. 기준선 없음 → `BASELINE_NOT_AVAILABLE`
9. mechanism 파일 삭제 + YAML 유지 → 실패
10. 정상 표 → 스키마·경로 계약 합격, P1 전체 판정은 미충족 항목 때문에 실패

## 7. Harness 게이트와 검증 명령

- 게이트 0 `bash scripts/session-status.sh`: `RED: 2/23`, 종료값 0. `acceptance-0-2.sh`는 로컬 `.secret-patterns` 부재로 기존 RED이고, `acceptance-principles-check.sh`는 의도된 `P1_UNMET` RED다. 나머지 21개는 통과했다.
- 게이트 4: 변경 셸 `bash -n=0`, Psych 원칙 32개·워크플로 총 22개 스텝 parse=0, principles mutation `20/20=0`, guard mutation `8/8=0`, `verify.sh=0`, 두 `git diff --check=0`.
- 실제 `bash hooks/pre-push`: 21개를 실행해 principles 전체 검사 1개만 `exit=1`로 차단하고 나머지 20개는 통과, pre-push 종료값 1.
- CI-equivalent는 로컬 실행으로만 표기한다. GitHub Actions 서버 판정으로 승격하지 않는다.
- 새 커밋의 실제 서버 실행은 `BLOCKED — push 금지로 새 커밋에 대한 서버 실행 불가`다.

## 8. 위험과 중단 조건

- 기본 전체 principles 검사는 현재 의도적으로 빨갛다. 이는 32개 장치가 완성되지 않았다는 P1의 정직한 결과다.
- CI 배선이 없거나 필수 파일 삭제가 통과하거나 guard 범위를 정직하게 표현하지 못하면 로컬 구현도 FAIL이다.
- 새 서버 실행은 권한상 BLOCKED이므로 PR은 병합 불가다.
- mechanism 파일의 존재·호출 정적 배선과 선택된 mutation은 보지만, 임의 코드 약화 전체를 자동 판별하는 것은 이번 범위 밖이다.

## 9. PR #32 읽기 전용 정정 계획

`task/codeaudit-wrap-2026-08-19`는 시작 HEAD와 상태를 바꾸지 않았다. 다음은 별도 PR #32 worktree에서 고쳐야 할 정정안이며 이번 작업의 수정 완료로 세지 않는다.

| PR #32 위치 | 현재 주장 | 정정안 |
|---|---|---|
| roadmap:28-30 | D3 수정 PASS·Claude PASS·AC-P13Y 완료·병합만 대기 | D3 첫 줄은 `VERDICT: FAIL`; 새 로컬 구현은 P1 31/32 미충족이고 서버 검증 BLOCKED라 병합 불가로 정정 |
| roadmap:34 | chmod 444 guard를 검증자 쓰기 방지 장치로 요약 | 동일 UID 우회가 가능한 우발 변경 억제·변조 탐지 장치로 범위 축소 |
| roadmap:48 | 시작 집계 `완전 6/부분 12/없음 5/해당없음 4/미확인 5` | 역사 시작값으로 표시하고 최종 `1/12/7/4/8` 및 7개 변경표 연결 |
| roadmap:72 | principles 양쪽 검증 PASS | 현재 구현 정확성의 로컬 PASS와 P1 전체 FAIL·서버 BLOCKED를 분리 |
| overnight:13,18,22,55,99-104,124-125 | 기존 검사 PASS·guard 물리 차단·원격 CI 초록을 완료 근거로 사용 | 엄격 스키마·실행 배선·동일 UID 한계·새 HEAD 미검증으로 재작성 |

이 표는 `PR #32 정정안 준비`이며 PR #32 브랜치 파일은 수정하지 않았다.

## 적대 검증 로그

- Claude 첫 호출은 셸 인용 오류로 본체가 실행되지 않아 `NOT_RUN`이었다. guard lock을 유지한 채 같은 필수 명령을 바로 재실행했다.
- 실제 1차: `env -u ANTHROPIC_API_KEY claude -p <적대검증 프롬프트>`, 종료값 0.
- guard: lock 0 → Claude 0 → check 0 → unlock 0. 시작·종료 SHA-256은 각각 `d679be...d4f`, `907158...67f`로 같고 권한은 644로 복구됐다. 이것은 동일 UID 공격 방지 증거가 아니다.

### Claude 1차 원문

<!-- CLAUDE_RAW_START -->
> 저장 계약: 아래 읽기용 원문은 후행 공백만 제거했다. 바이트 단위 원문은 SHA-256 `ee4531241b1db759c031f460077695796dd6369151ee186c3e7a02709236fe41`와 Base64 블록이 정본이며 그대로 복원할 수 있다.

#### 읽기용 원문

~~~~text
# VERDICT: PASS

(PASS = 로컬 강제 구현과 그 정직한 보고가 명시된 인수 기준을 충족한다는 뜻이다. P1 완료나 PR 병합 가능을 뜻하지 않는다 — 실제로 32개 중 31개가 미충족이며 새 커밋의 서버 실행은 BLOCKED다.)

## 요약 (3층 브리핑)

**결론**: PR #31의 로컬 구현(commit `f3b5d0f`, worktree HEAD)은 goal 문서(§3 B안)와 SOT(P1)가 요구하는 "32개 전부 미충족 시 전체 실패" 설계를 실제로 구현했고, 10개 공격 시나리오 전부를 독립 재현으로 방어했다. 원격 PR #31의 헤드는 `929247a`(로컬보다 3커밋 뒤)이고 그 초록 `verify` 체크 2건은 이 3커밋의 실제 구현을 검증한 적이 없다 — push 금지로 새 실행은 BLOCKED다.

**판단 근거**: 아래 10개 공격을 mktemp 격리 저장소에서 직접 재현했고(스크립트의 자기선언을 신뢰하지 않고 별도 명령으로 재확인), 전부 설계대로 차단/보고됨을 확인했다.

**틀리면 깨지는 것**: 이 PASS는 "구현이 자기 목표를 달성했다"는 뜻이지 "병합해도 된다"는 뜻이 아니다. 32개 중 31개가 여전히 미충족이고, 이 사실이 로컬 실행에서 정확히 `P1_UNMET: 31/32`로 드러난다는 것이 바로 PASS 판정의 핵심 증거다.

---

## 1) `acceptance-principles-check.sh` ↔ `verify.yml` 직접 배선, 두 필수 파일 고정 목록

**검증**: `.github/workflows/verify.yml:22-26`(파일 존재 고정 검사) + `:34-35`(`bash scripts/acceptance-principles-check.sh` 직접 실행)
```
- name: P1 원칙 장부 필수 파일 존재 검사
  run: |
    test -f docs/sot/principles.yaml
    test -f scripts/acceptance-principles-check.sh
    test -x scripts/acceptance-principles-check.sh
- name: P1 원칙 32개 전체 강제 검사
  run: bash scripts/acceptance-principles-check.sh
```
**결과**: 통과. `docs/sot/verification-commands.md`(작업트리, 미커밋)의 표 1·4행과도 일치.

## 2) 필수 파일 삭제/rename — pre-commit·로컬 CI-equivalent 통과 가능 여부

독립 mktemp clone(`core.hooksPath hooks` 명시 설정 후 실제 `git commit` 실행):

```
### 삭제(두 파일 동시):
BLOCKED: P1 필수 파일이 인덱스에 없다 — docs/sot/principles.yaml
BLOCKED: P1 필수 파일이 인덱스에 없다 — scripts/acceptance-principles-check.sh
commit rc=1

### rename:
BLOCKED: P1 필수 파일이 인덱스에 없다 — docs/sot/principles.yaml (삭제·이름 변경 금지)
commit rc=1
```
정상 무관 커밋(README 수정)은 `rc=0`로 통과 — 차단과 통과가 한 쌍임을 확인.

**발견(INFO, 심각도 낮음, 이미 설계상 인지된 한계)**: `hooks/pre-commit` 자체를 필수 파일 2개와 **같은 커밋에서 함께 삭제**하면 git이 존재하지 않는 훅을 조용히 skip하여 `commit rc=0`으로 통과한다(재현: `scripts/acceptance-principles-check.sh`, `docs/sot/principles.yaml`, `hooks/pre-commit` 3개 동시 `git rm` → commit 성공). 그러나:
- `hooks/pre-push`는 별도 독립 검사를 가지고 있어(`hooks/pre-push:19-32`, pre-commit 존재에 의존하지 않음) 같은 mktemp에서 재현 시 `BLOCKED`(rc=1)로 push를 막았다.
- 로컬 CI-equivalent(`test -f hooks/pre-commit`, verify.yml:154-156 "강제 장치 존재 검사")도 독립적으로 `FAIL: hooks/pre-commit 없음`을 낸다.
방어선이 3중(pre-commit/pre-push/CI)이라 이 경로는 최종적으로 fail-closed다. 새 결함이 아니라 git 훅의 구조적 한계이며 CI 배선 주석(verify.yml:148-151)에 이미 명시돼 있다.

## 3) unknown field / 중복 키 / 빈 principle·evidence·mechanism / 잘못된 ID·status / 깨진 YAML

`acceptance-principles-mutations.sh` 20개 항목 전부 재실행 → 전부 PASS(rc=0). 자기선언을 믿지 않고 별도 mktemp에서 독립 재현:
```
UNKNOWN_FIELD: item[5] totally_new_field
SCHEMA_FAIL: 1 violation(s)   (rc=1)

DUPLICATE_KEY: $[0][0][0].id
SCHEMA_FAIL: 1 violation(s)   (rc=1)
```
(`scripts/acceptance-principles-check.sh:186-209`의 unknown/missing/empty/status 검사 로직과 일치)

## 4) mechanism_found가 없는/미실행 mechanism을 가리키는 경우, YAML status 유지한 채 mechanism 파일·검사기 배선 제거

기존 mutation 케이스(`missing_mechanism`→`MECHANISM_PATH_MISSING`, `disconnected_mechanism`→`MECHANISM_CHECK_DISCONNECTED`)를 실제 **P21(유일한 완전 항목)의 실제 mechanism 쌍**(`path: hooks/pre-commit`, `check: scripts/acceptance-hs-a4.sh`)에 대해 독립 재현:
```
### 가짜 ci-wired mechanism(check가 실제로 그 path를 참조하지 않음)
MECHANISM_CHECK_DISCONNECTED: P2.mechanism_found[0] path=... check=...
SCHEMA_FAIL: ... (rc=1)
```
또한 `scripts/acceptance-hs-a4.sh`를 직접 실행해 P21의 mechanism이 **문자열 단언이 아니라 실제 임시저장소 실행**으로 검증됨을 확인(`CHECKED: 30`, 전부 PASS, rc=0) — 1MB 초과·경로 규칙·rename 우회·인덱스 blob 측정까지 실제 hook 실행.

## 5) status 회귀와 BASELINE_NOT_AVAILABLE 구분

```
git cat-file -e origin/main:docs/sot/principles.yaml → "exists on disk, but not in 'origin/main'"
```
실제 `--full` 실행 출력:
```
BASELINE_NOT_AVAILABLE: origin/main:docs/sot/principles.yaml — first introduction; regression is not counted as PASS
P1_UNMET: 31/32 — ...
```
코드 확인(`acceptance-principles-check.sh:383-385`): `BASELINE_NOT_AVAILABLE` 분기는 `overall`을 건드리지 않는다 — PASS로 카운트되지도, 그 자체로 실패시키지도 않는다(AC4 요구와 일치). 최종 실패는 별도의 `P1_UNMET`에서 온다. 회귀 존재/부재 각각의 mutation 케이스도 독립적으로 마커 일치 확인함.

## 6) 동일 UID guard 우회 — 정직한 문서화 확인

`scripts/acceptance-guard-global-skill-files.sh`는 mktemp 복제본(`$dir/files/claude.md`, `codex.md`)만 조작 — 실제 `~/.claude/skills/strict/SKILL.md`(444, 원본 손상 없음 확인함)는 건드리지 않음. 실행 결과:
```
PASS: 동일 UID 내용+상태 위조 우회 재현 — check exit=0 (0이 문서화된 한계)
```
`guard-global-skill-files.sh:8-11` 주석과 goal 문서 AC5가 "동일 UID는 chmod·내용·상태 파일을 바꿀 수 있다"를 명시적으로 한계로 선언하며, 이 테스트는 그 한계가 **과장 없이 실제로 재현됨**(우회가 실제로 통과함, 그리고 그것이 문서화된 한계라고 정확히 라벨링됨)을 보여준다. 은폐가 아니라 정직한 노출.

**부수 관찰(정보성)**: 실제 `~/.claude/skills/strict/SKILL.md`, `~/.codex/skills/strict/SKILL.md`가 현재 mode 444(잠금 상태)이고 `~/.cache/valuehire-guard/strict-skill-files.state`가 오늘 09:14 타임스탬프로 남아있다 — 이번 검증 세션 시작 전 실제 lock이 걸리고 아직 unlock되지 않은 상태로 보인다(§10 "Claude 1차: lock → claude -p → check → unlock" 순서의 잔여물로 추정). PR 코드 결함이 아니며 나는 이 파일들에 손대지 않았다(읽기만 함, mode 변경 없음 확인).

## 7) P13/P14/P11/V 상태, 문서 정합성, 8/10·6/12 stale claim, D3 첫 줄

- 실행 결과: `STATUS_COUNTS: 완전=1 부분=12 없음=7 해당없음=4 미확인=8` (합계 32, ruby 재계산과 일치)
- `D3 3차 판정문` 첫 줄: `VERDICT: FAIL` (grep으로 직접 확인, `#`, `**PASS**` 요약으로 왜곡 없음)
- `git diff --check` (D3 판정문 파일, HEAD 기준): rc=0, trailing whitespace 0건 — commit `4263965`에서 정리됨 확인.
- "완전 8/부분 10", "6/12" 문구는 `strict-principles-yaml-v2round-verdict-2026-08-19.md`(날짜 박힌 과거 판정 기록)에만 남아있고, 그 문서 자체가 "이 숫자는 갱신 전 상태"라고 스스로 표시함 — 현재 판정으로 오인될 위험은 낮음. goal 문서(§5)는 최종 수치를 하드코딩하지 않고 "스크립트로 재계산" 원칙을 명시해 stale-count 재발을 구조적으로 막음.
- P13(`부분`)·P14(`부분`)·P11(`없음`) 각 evidence 필드를 SOT 원문(①~⑤/①~④ 요건)과 대조: P13은 ②③④만 구현·①⑤ 미구현("evidence" 문구가 정확히 이를 명시), P14는 ①만 구현·②③④ 미구현, P11은 "이전 판정(완전)은 과장이었음"으로 스스로 정정 — 과장 없이 보수적으로 분류됨.
- **경미한 미비(LOW)**: goal 문서 §5는 "완전→그외"로 재분류된 항목을 P13·P14·P11·V-4·V-1/2/5(7개)로 열거하지만, 시작 기준값(완전=6) 대비 실제 최종값(완전=1)의 하락폭(5개)과 정확히 1:1로 대응되는 근거표는 goal 문서 자체엔 없다(개별 evidence 필드에는 있음). 최종 판정 정확성 자체엔 영향 없음 — 정보 누락일 뿐, 실행 결과가 이미 원본 진실.

## 8) 새 pre-commit 필수파일 요구가 기존 fixture·정상 통제를 회귀시켰는가

```
bash scripts/session-status.sh → RED: 2/23 (acceptance-0-7.sh 제외 — CI 담당)
```
RED 2건 확인: `acceptance-0-2.sh`(rc=2, 로컬 `.secret-patterns` 부재 — PR과 무관, 최종 수정 커밋 `6a4f2f0`로 이 PR 이전부터 존재)와 `acceptance-principles-check.sh`(rc=1, 의도된 P1_UNMET). 나머지 21개 acceptance 스크립트 + `verify.sh`는 전부 GREEN. 정상 무관 커밋(README 수정)도 pre-commit 통과 확인(§2). 회귀 없음.

## 9) git diff --check 정합성

```
git diff --check origin/main HEAD   → rc=0
git diff --check (working tree 포함, 미커밋 문서수정 포함) → rc=0
git diff --check HEAD                → rc=0
```
전부 클린. (초기에 `git diff --check 7bd3298 929247a` 실행에서 trailing whitespace가 보였는데, 이는 이력상 중간 커밋 사이의 diff이며 이후 커밋 `4263965`에서 정리되어 현재 HEAD에는 남아있지 않음 — 별도 확인함)

## 10) P1 완전 실패 원칙과 범위 외 명시

```
P1_UNMET: 31/32 — P1,P2,...,V-5   (rc=1)
```
1개(P21)만 완전+CI배선 충족, 31개 미충족 시 정확히 실패(설계 로직 `acceptance-principles-check.sh:389-393`도 코드 검토로 재확인 — 완전 32개 중 1개만 조건 미달이어도 `unmet` non-empty). "임의 코드 약화 전체 자동판별은 범위 밖"이라는 명시는 goal 문서 §8, AC2에 이미 존재.

---

## 축 분리 최종 판정

| 축 | 판정 |
|---|---|
| 구현 정확성(스키마/mechanism/회귀/guard) | **PASS** — 10개 공격 전부 방어 확인(독립 재현) |
| 의도된 P1 실패(Design B) | **정직하게 재현됨** — `P1_UNMET: 31/32`, exit 1 |
| 로컬 CI-equivalent | **PASS**(파일 존재/실행 검사 통과) 단 전체 파이프라인 중 `acceptance-principles-check.sh` 자체는 P1_UNMET으로 RED |
| 실제 GitHub Actions 서버 실행 | **BLOCKED** — 원격 헤드는 `929247a`(로컬보다 3커밋 뒤), 초록 체크 2건은 새 3커밋을 검증한 적 없음 |
| 병합 가능성 | **아니오** — P1 미충족 + 서버 검증 불가로 병합 불가 (goal 문서 결론과 일치) |
~~~~

#### 바이트 단위 원문(Base64)

~~~~text
IyBWRVJESUNUOiBQQVNTCgooUEFTUyA9IOuhnOy7rCDqsJXsoJwg6rWs7ZiE6rO8IOq3uCDsoJXs
p4HtlZwg67O06rOg6rCAIOuqheyLnOuQnCDsnbjsiJgg6riw7KSA7J2EIOy2qeyhse2VnOuLpOuK
lCDrnLvsnbTri6QuIFAxIOyZhOujjOuCmCBQUiDrs5Htlakg6rCA64ql7J2EIOucu+2VmOyngCDs
lYrripTri6Qg4oCUIOyLpOygnOuhnCAzMuqwnCDspJEgMzHqsJzqsIAg66+47Lap7KGx7J2066mw
IOyDiCDsu6TrsIvsnZgg7ISc67KEIOyLpO2WieydgCBCTE9DS0VE64ukLikKCiMjIOyalOyVvSAo
M+y4tSDruIzrpqztlZEpCgoqKuqysOuhoCoqOiBQUiAjMzHsnZgg66Gc7LusIOq1rO2YhChjb21t
aXQgYGYzYjVkMGZgLCB3b3JrdHJlZSBIRUFEKeydgCBnb2FsIOusuOyEnCjCpzMgQuyViCnsmYAg
U09UKFAxKeqwgCDsmpTqtaztlZjripQgIjMy6rCcIOyghOu2gCDrr7jstqnsobEg7IucIOyghOyy
tCDsi6TtjKgiIOyEpOqzhOulvCDsi6TsoJzroZwg6rWs7ZiE7ZaI6rOgLCAxMOqwnCDqs7Xqsqkg
7Iuc64KY66as7JikIOyghOu2gOulvCDrj4Xrpr0g7J6s7ZiE7Jy866GcIOuwqeyWtO2WiOuLpC4g
7JuQ6rKpIFBSICMzMeydmCDtl6Trk5zripQgYDkyOTI0N2FgKOuhnOy7rOuztOuLpCAz7Luk67CL
IOuSpCnsnbTqs6Ag6re4IOy0iOuhnSBgdmVyaWZ5YCDssrTtgawgMuqxtOydgCDsnbQgM+y7pOuw
i+ydmCDsi6TsoJwg6rWs7ZiE7J2EIOqygOymne2VnCDsoIHsnbQg7JeG64ukIOKAlCBwdXNoIOq4
iOyngOuhnCDsg4gg7Iuk7ZaJ7J2AIEJMT0NLRUTri6QuCgoqKu2MkOuLqCDqt7zqsbAqKjog7JWE
656YIDEw6rCcIOqzteqyqeydhCBta3RlbXAg6rKp66asIOyggOyepeyGjOyXkOyEnCDsp4HsoJEg
7J6s7ZiE7ZaI6rOgKOyKpO2BrOumve2KuOydmCDsnpDquLDshKDslrjsnYQg7Iug66Kw7ZWY7KeA
IOyViuqzoCDrs4Trj4Qg66qF66C57Jy866GcIOyerO2ZleyduCksIOyghOu2gCDshKTqs4TrjIDr
oZwg7LCo64uoL+uztOqzoOuQqOydhCDtmZXsnbjtlojri6QuCgoqKu2LgOumrOuptCDquajsp4Dr
ipQg6rKDKio6IOydtCBQQVNT64qUICLqtaztmITsnbQg7J6Q6riwIOuqqe2RnOulvCDri6zshLHt
lojri6Qi64qUIOucu+ydtOyngCAi67OR7ZWp7ZW064+EIOuQnOuLpCLripQg65y77J20IOyVhOuL
iOuLpC4gMzLqsJwg7KSRIDMx6rCc6rCAIOyXrOyghO2eiCDrr7jstqnsobHsnbTqs6AsIOydtCDs
gqzsi6TsnbQg66Gc7LusIOyLpO2WieyXkOyEnCDsoJXtmZXtnoggYFAxX1VOTUVUOiAzMS8zMmDr
oZwg65Oc65+s64Kc64uk64qUIOqyg+ydtCDrsJTroZwgUEFTUyDtjJDsoJXsnZgg7ZW17IusIOym
neqxsOuLpC4KCi0tLQoKIyMgMSkgYGFjY2VwdGFuY2UtcHJpbmNpcGxlcy1jaGVjay5zaGAg4oaU
IGB2ZXJpZnkueW1sYCDsp4HsoJEg67Cw7ISgLCDrkZAg7ZWE7IiYIO2MjOydvCDqs6DsoJUg66qp
66GdCgoqKuqygOymnSoqOiBgLmdpdGh1Yi93b3JrZmxvd3MvdmVyaWZ5LnltbDoyMi0yNmAo7YyM
7J28IOyhtOyerCDqs6DsoJUg6rKA7IKsKSArIGA6MzQtMzVgKGBiYXNoIHNjcmlwdHMvYWNjZXB0
YW5jZS1wcmluY2lwbGVzLWNoZWNrLnNoYCDsp4HsoJEg7Iuk7ZaJKQpgYGAKLSBuYW1lOiBQMSDs
m5DsuZkg7J6l67aAIO2VhOyImCDtjIzsnbwg7KG07J6sIOqygOyCrAogIHJ1bjogfAogICAgdGVz
dCAtZiBkb2NzL3NvdC9wcmluY2lwbGVzLnlhbWwKICAgIHRlc3QgLWYgc2NyaXB0cy9hY2NlcHRh
bmNlLXByaW5jaXBsZXMtY2hlY2suc2gKICAgIHRlc3QgLXggc2NyaXB0cy9hY2NlcHRhbmNlLXBy
aW5jaXBsZXMtY2hlY2suc2gKLSBuYW1lOiBQMSDsm5DsuZkgMzLqsJwg7KCE7LK0IOqwleygnCDq
soDsgqwKICBydW46IGJhc2ggc2NyaXB0cy9hY2NlcHRhbmNlLXByaW5jaXBsZXMtY2hlY2suc2gK
YGBgCioq6rKw6rO8Kio6IO2GteqzvC4gYGRvY3Mvc290L3ZlcmlmaWNhdGlvbi1jb21tYW5kcy5t
ZGAo7J6R7JeF7Yq466asLCDrr7jsu6TrsIsp7J2YIO2RnCAxwrc07ZaJ6rO864+EIOydvOy5mC4K
CiMjIDIpIO2VhOyImCDtjIzsnbwg7IKt7KCcL3JlbmFtZSDigJQgcHJlLWNvbW1pdMK366Gc7Lus
IENJLWVxdWl2YWxlbnQg7Ya16rO8IOqwgOuKpSDsl6zrtoAKCuuPheumvSBta3RlbXAgY2xvbmUo
YGNvcmUuaG9va3NQYXRoIGhvb2tzYCDrqoXsi5wg7ISk7KCVIO2bhCDsi6TsoJwgYGdpdCBjb21t
aXRgIOyLpO2WiSk6CgpgYGAKIyMjIOyCreygnCjrkZAg7YyM7J28IOuPmeyLnCk6IApCTE9DS0VE
OiBQMSDtlYTsiJgg7YyM7J287J20IOyduOuNseyKpOyXkCDsl4bri6Qg4oCUIGRvY3Mvc290L3By
aW5jaXBsZXMueWFtbApCTE9DS0VEOiBQMSDtlYTsiJgg7YyM7J287J20IOyduOuNseyKpOyXkCDs
l4bri6Qg4oCUIHNjcmlwdHMvYWNjZXB0YW5jZS1wcmluY2lwbGVzLWNoZWNrLnNoCmNvbW1pdCBy
Yz0xCgojIyMgcmVuYW1lOgpCTE9DS0VEOiBQMSDtlYTsiJgg7YyM7J287J20IOyduOuNseyKpOyX
kCDsl4bri6Qg4oCUIGRvY3Mvc290L3ByaW5jaXBsZXMueWFtbCAo7IKt7KCcwrfsnbTrpoQg67OA
6rK9IOq4iOyngCkKY29tbWl0IHJjPTEKYGBgCuygleyDgSDrrLTqtIAg7Luk67CLKFJFQURNRSDs
iJjsoJUp7J2AIGByYz0wYOuhnCDthrXqs7wg4oCUIOywqOuLqOqzvCDthrXqs7zqsIAg7ZWcIOyM
jeyehOydhCDtmZXsnbguCgoqKuuwnOqyrChJTkZPLCDsi6zqsIHrj4Qg64Ku7J2MLCDsnbTrr7gg
7ISk6rOE7IOBIOyduOyngOuQnCDtlZzqs4QpKio6IGBob29rcy9wcmUtY29tbWl0YCDsnpDssrTr
pbwg7ZWE7IiYIO2MjOydvCAy6rCc7JmAICoq6rCZ7J2AIOy7pOuwi+yXkOyEnCDtlajqu5gg7IKt
7KCcKirtlZjrqbQgZ2l07J20IOyhtOyerO2VmOyngCDslYrripQg7ZuF7J2EIOyhsOyaqe2eiCBz
a2lw7ZWY7JesIGBjb21taXQgcmM9MGDsnLzroZwg7Ya16rO87ZWc64ukKOyerO2YhDogYHNjcmlw
dHMvYWNjZXB0YW5jZS1wcmluY2lwbGVzLWNoZWNrLnNoYCwgYGRvY3Mvc290L3ByaW5jaXBsZXMu
eWFtbGAsIGBob29rcy9wcmUtY29tbWl0YCAz6rCcIOuPmeyLnCBgZ2l0IHJtYCDihpIgY29tbWl0
IOyEseqztSkuIOq3uOufrOuCmDoKLSBgaG9va3MvcHJlLXB1c2hg64qUIOuzhOuPhCDrj4Xrpr0g
6rKA7IKs66W8IOqwgOyngOqzoCDsnojslrQoYGhvb2tzL3ByZS1wdXNoOjE5LTMyYCwgcHJlLWNv
bW1pdCDsobTsnqzsl5Ag7J2Y7KG07ZWY7KeAIOyViuydjCkg6rCZ7J2AIG1rdGVtcOyXkOyEnCDs
nqztmIQg7IucIGBCTE9DS0VEYChyYz0xKeuhnCBwdXNo66W8IOunieyVmOuLpC4KLSDroZzsu6wg
Q0ktZXF1aXZhbGVudChgdGVzdCAtZiBob29rcy9wcmUtY29tbWl0YCwgdmVyaWZ5LnltbDoxNTQt
MTU2ICLqsJXsoJwg7J6l7LmYIOyhtOyerCDqsoDsgqwiKeuPhCDrj4Xrpr3soIHsnLzroZwgYEZB
SUw6IGhvb2tzL3ByZS1jb21taXQg7JeG7J2MYOydhCDrgrjri6QuCuuwqeyWtOyEoOydtCAz7KSR
KHByZS1jb21taXQvcHJlLXB1c2gvQ0kp7J206528IOydtCDqsr3roZzripQg7LWc7KKF7KCB7Jy8
66GcIGZhaWwtY2xvc2Vk64ukLiDsg4gg6rKw7ZWo7J20IOyVhOuLiOudvCBnaXQg7ZuF7J2YIOq1
rOyhsOyggSDtlZzqs4TsnbTrqbAgQ0kg67Cw7ISgIOyjvOyEnSh2ZXJpZnkueW1sOjE0OC0xNTEp
7JeQIOydtOuvuCDrqoXsi5zrj7wg7J6I64ukLgoKIyMgMykgdW5rbm93biBmaWVsZCAvIOykkeuz
tSDtgqQgLyDruYggcHJpbmNpcGxlwrdldmlkZW5jZcK3bWVjaGFuaXNtIC8g7J6Y66q765CcIElE
wrdzdGF0dXMgLyDquajsp4QgWUFNTAoKYGFjY2VwdGFuY2UtcHJpbmNpcGxlcy1tdXRhdGlvbnMu
c2hgIDIw6rCcIO2VreuqqSDsoITrtoAg7J6s7Iuk7ZaJIOKGkiDsoITrtoAgUEFTUyhyYz0wKS4g
7J6Q6riw7ISg7Ja47J2EIOuvv+yngCDslYrqs6Ag67OE64+EIG1rdGVtcOyXkOyEnCDrj4Xrpr0g
7J6s7ZiEOgpgYGAKVU5LTk9XTl9GSUVMRDogaXRlbVs1XSB0b3RhbGx5X25ld19maWVsZApTQ0hF
TUFfRkFJTDogMSB2aW9sYXRpb24ocykgICAocmM9MSkKCkRVUExJQ0FURV9LRVk6ICRbMF1bMF1b
MF0uaWQKU0NIRU1BX0ZBSUw6IDEgdmlvbGF0aW9uKHMpICAgKHJjPTEpCmBgYAooYHNjcmlwdHMv
YWNjZXB0YW5jZS1wcmluY2lwbGVzLWNoZWNrLnNoOjE4Ni0yMDlg7J2YIHVua25vd24vbWlzc2lu
Zy9lbXB0eS9zdGF0dXMg6rKA7IKsIOuhnOyngeqzvCDsnbzsuZgpCgojIyA0KSBtZWNoYW5pc21f
Zm91bmTqsIAg7JeG64qUL+uvuOyLpO2WiSBtZWNoYW5pc23snYQg6rCA66as7YKk64qUIOqyveya
sCwgWUFNTCBzdGF0dXMg7Jyg7KeA7ZWcIOyxhCBtZWNoYW5pc20g7YyM7J28wrfqsoDsgqzquLAg
67Cw7ISgIOygnOqxsAoK6riw7KG0IG11dGF0aW9uIOy8gOydtOyKpChgbWlzc2luZ19tZWNoYW5p
c21g4oaSYE1FQ0hBTklTTV9QQVRIX01JU1NJTkdgLCBgZGlzY29ubmVjdGVkX21lY2hhbmlzbWDi
hpJgTUVDSEFOSVNNX0NIRUNLX0RJU0NPTk5FQ1RFRGAp66W8IOyLpOygnCAqKlAyMSjsnKDsnbzt
lZwg7JmE7KCEIO2VreuqqSnsnZgg7Iuk7KCcIG1lY2hhbmlzbSDsjI0qKihgcGF0aDogaG9va3Mv
cHJlLWNvbW1pdGAsIGBjaGVjazogc2NyaXB0cy9hY2NlcHRhbmNlLWhzLWE0LnNoYCnsl5Ag64yA
7ZW0IOuPheumvSDsnqztmIQ6CmBgYAojIyMg6rCA7KecIGNpLXdpcmVkIG1lY2hhbmlzbShjaGVj
a+qwgCDsi6TsoJzroZwg6re4IHBhdGjrpbwg7LC47KGw7ZWY7KeAIOyViuydjCkKTUVDSEFOSVNN
X0NIRUNLX0RJU0NPTk5FQ1RFRDogUDIubWVjaGFuaXNtX2ZvdW5kWzBdIHBhdGg9Li4uIGNoZWNr
PS4uLgpTQ0hFTUFfRkFJTDogLi4uIChyYz0xKQpgYGAK65iQ7ZWcIGBzY3JpcHRzL2FjY2VwdGFu
Y2UtaHMtYTQuc2hg66W8IOyngeygkSDsi6TtlontlbQgUDIx7J2YIG1lY2hhbmlzbeydtCAqKuus
uOyekOyXtCDri6jslrjsnbQg7JWE64uI6528IOyLpOygnCDsnoTsi5zsoIDsnqXshowg7Iuk7ZaJ
KirsnLzroZwg6rKA7Kad65Co7J2EIO2ZleyduChgQ0hFQ0tFRDogMzBgLCDsoITrtoAgUEFTUywg
cmM9MCkg4oCUIDFNQiDstIjqs7zCt+qyveuhnCDqt5zsuZnCt3JlbmFtZSDsmrDtmozCt+yduOuN
seyKpCBibG9iIOy4oeygleq5jOyngCDsi6TsoJwgaG9vayDsi6TtlokuCgojIyA1KSBzdGF0dXMg
7ZqM6reA7JmAIEJBU0VMSU5FX05PVF9BVkFJTEFCTEUg6rWs67aECgpgYGAKZ2l0IGNhdC1maWxl
IC1lIG9yaWdpbi9tYWluOmRvY3Mvc290L3ByaW5jaXBsZXMueWFtbCDihpIgImV4aXN0cyBvbiBk
aXNrLCBidXQgbm90IGluICdvcmlnaW4vbWFpbiciCmBgYArsi6TsoJwgYC0tZnVsbGAg7Iuk7ZaJ
IOy2nOugpToKYGBgCkJBU0VMSU5FX05PVF9BVkFJTEFCTEU6IG9yaWdpbi9tYWluOmRvY3Mvc290
L3ByaW5jaXBsZXMueWFtbCDigJQgZmlyc3QgaW50cm9kdWN0aW9uOyByZWdyZXNzaW9uIGlzIG5v
dCBjb3VudGVkIGFzIFBBU1MKUDFfVU5NRVQ6IDMxLzMyIOKAlCAuLi4KYGBgCuy9lOuTnCDtmZXs
nbgoYGFjY2VwdGFuY2UtcHJpbmNpcGxlcy1jaGVjay5zaDozODMtMzg1YCk6IGBCQVNFTElORV9O
T1RfQVZBSUxBQkxFYCDrtoTquLDripQgYG92ZXJhbGxg7J2EIOqxtOuTnOumrOyngCDslYrripTr
i6Qg4oCUIFBBU1ProZwg7Lm07Jq07Yq465CY7KeA64+ELCDqt7gg7J6Q7LK066GcIOyLpO2MqOyL
nO2CpOyngOuPhCDslYrripTri6QoQUM0IOyalOq1rOyZgCDsnbzsuZgpLiDstZzsooUg7Iuk7Yyo
64qUIOuzhOuPhOydmCBgUDFfVU5NRVRg7JeQ7IScIOyYqOuLpC4g7ZqM6reAIOyhtOyerC/rtoDs
nqwg6rCB6rCB7J2YIG11dGF0aW9uIOy8gOydtOyKpOuPhCDrj4Xrpr3soIHsnLzroZwg66eI7Luk
IOydvOy5mCDtmZXsnbjtlaguCgojIyA2KSDrj5nsnbwgVUlEIGd1YXJkIOyasO2ajCDigJQg7KCV
7KeB7ZWcIOusuOyEnO2ZlCDtmZXsnbgKCmBzY3JpcHRzL2FjY2VwdGFuY2UtZ3VhcmQtZ2xvYmFs
LXNraWxsLWZpbGVzLnNoYOuKlCBta3RlbXAg67O17KCc67O4KGAkZGlyL2ZpbGVzL2NsYXVkZS5t
ZGAsIGBjb2RleC5tZGAp66eMIOyhsOyekSDigJQg7Iuk7KCcIGB+Ly5jbGF1ZGUvc2tpbGxzL3N0
cmljdC9TS0lMTC5tZGAoNDQ0LCDsm5Drs7gg7IaQ7IOBIOyXhuydjCDtmZXsnbjtlagp64qUIOqx
tOuTnOumrOyngCDslYrsnYwuIOyLpO2WiSDqsrDqs7w6CmBgYApQQVNTOiDrj5nsnbwgVUlEIOuC
tOyaqSvsg4Htg5wg7JyE7KGwIOyasO2ajCDsnqztmIQg4oCUIGNoZWNrIGV4aXQ9MCAoMOydtCDr
rLjshJztmZTrkJwg7ZWc6rOEKQpgYGAKYGd1YXJkLWdsb2JhbC1za2lsbC1maWxlcy5zaDo4LTEx
YCDso7zshJ3qs7wgZ29hbCDrrLjshJwgQUM16rCAICLrj5nsnbwgVUlE64qUIGNobW9kwrfrgrTs
mqnCt+yDge2DnCDtjIzsnbzsnYQg67CU6r+AIOyImCDsnojri6Qi66W8IOuqheyLnOyggeycvOuh
nCDtlZzqs4TroZwg7ISg7Ja47ZWY66mwLCDsnbQg7YWM7Iqk7Yq464qUIOq3uCDtlZzqs4TqsIAg
Kirqs7zsnqUg7JeG7J20IOyLpOygnOuhnCDsnqztmITrkKgqKijsmrDtmozqsIAg7Iuk7KCc66Gc
IO2GteqzvO2VqCwg6re466as6rOgIOq3uOqyg+ydtCDrrLjshJztmZTrkJwg7ZWc6rOE65286rOg
IOygle2Zle2eiCDrnbzrsqjrp4HrkKgp7J2EIOuztOyXrOykgOuLpC4g7J2A7Y+Q6rCAIOyVhOuL
iOudvCDsoJXsp4HtlZwg64W47LacLgoKKirrtoDsiJgg6rSA7LCwKOygleuztOyEsSkqKjog7Iuk
7KCcIGB+Ly5jbGF1ZGUvc2tpbGxzL3N0cmljdC9TS0lMTC5tZGAsIGB+Ly5jb2RleC9za2lsbHMv
c3RyaWN0L1NLSUxMLm1kYOqwgCDtmITsnqwgbW9kZSA0NDQo7J6g6riIIOyDge2DnCnsnbTqs6Ag
YH4vLmNhY2hlL3ZhbHVlaGlyZS1ndWFyZC9zdHJpY3Qtc2tpbGwtZmlsZXMuc3RhdGVg6rCAIOyY
pOuKmCAwOToxNCDtg4DsnoTsiqTtg6ztlITroZwg64Ko7JWE7J6I64ukIOKAlCDsnbTrsogg6rKA
7KadIOyEuOyFmCDsi5zsnpEg7KCEIOyLpOygnCBsb2Nr7J20IOqxuOumrOqzoCDslYTsp4EgdW5s
b2Nr65CY7KeAIOyViuydgCDsg4Htg5zroZwg67O07J2464ukKMKnMTAgIkNsYXVkZSAx7LCoOiBs
b2NrIOKGkiBjbGF1ZGUgLXAg4oaSIGNoZWNrIOKGkiB1bmxvY2siIOyInOyEnOydmCDsnpTsl6zr
rLzroZwg7LaU7KCVKS4gUFIg7L2U65OcIOqysO2VqOydtCDslYTri4jrqbAg64KY64qUIOydtCDt
jIzsnbzrk6Tsl5Ag7IaQ64yA7KeAIOyViuyVmOuLpCjsnb3quLDrp4wg7ZWoLCBtb2RlIOuzgOqy
vSDsl4bsnYwg7ZmV7J24KS4KCiMjIDcpIFAxMy9QMTQvUDExL1Yg7IOB7YOcLCDrrLjshJwg7KCV
7ZWp7ISxLCA4LzEwwrc2LzEyIHN0YWxlIGNsYWltLCBEMyDssqsg7KSECgotIOyLpO2WiSDqsrDq
s7w6IGBTVEFUVVNfQ09VTlRTOiDsmYTsoIQ9MSDrtoDrtoQ9MTIg7JeG7J2MPTcg7ZW064u57JeG
7J2MPTQg66+47ZmV7J24PThgICjtlanqs4QgMzIsIHJ1Ynkg7J6s6rOE7IKw6rO8IOydvOy5mCkK
LSBgRDMgM+ywqCDtjJDsoJXrrLhgIOyyqyDspIQ6IGBWRVJESUNUOiBGQUlMYCAoZ3JlcOycvOuh
nCDsp4HsoJEg7ZmV7J24LCBgI2AsIGAqKlBBU1MqKmAg7JqU7JW97Jy866GcIOyZnOqzoSDsl4bs
nYwpCi0gYGdpdCBkaWZmIC0tY2hlY2tgIChEMyDtjJDsoJXrrLgg7YyM7J28LCBIRUFEIOq4sOyk
gCk6IHJjPTAsIHRyYWlsaW5nIHdoaXRlc3BhY2UgMOqxtCDigJQgY29tbWl0IGA0MjYzOTY1YOyX
kOyEnCDsoJXrpqzrkKgg7ZmV7J24LgotICLsmYTsoIQgOC/rtoDrtoQgMTAiLCAiNi8xMiIg66y4
6rWs64qUIGBzdHJpY3QtcHJpbmNpcGxlcy15YW1sLXYycm91bmQtdmVyZGljdC0yMDI2LTA4LTE5
Lm1kYCjrgqDsp5wg67CV7Z6MIOqzvOqxsCDtjJDsoJUg6riw66GdKeyXkOunjCDrgqjslYTsnojq
s6AsIOq3uCDrrLjshJwg7J6Q7LK06rCAICLsnbQg7Iir7J6Q64qUIOqwseyLoCDsoIQg7IOB7YOc
IuudvOqzoCDsiqTsiqTroZwg7ZGc7Iuc7ZWoIOKAlCDtmITsnqwg7YyQ7KCV7Jy866GcIOyYpOyd
uOuQoCDsnITtl5jsnYAg64Ku7J2MLiBnb2FsIOusuOyEnCjCpzUp64qUIOy1nOyihSDsiJjsuZjr
pbwg7ZWY65Oc7L2U65Sp7ZWY7KeAIOyViuqzoCAi7Iqk7YGs66a97Yq466GcIOyerOqzhOyCsCIg
7JuQ7LmZ7J2EIOuqheyLnO2VtCBzdGFsZS1jb3VudCDsnqzrsJzsnYQg6rWs7KGw7KCB7Jy866Gc
IOunieydjC4KLSBQMTMoYOu2gOu2hGApwrdQMTQoYOu2gOu2hGApwrdQMTEoYOyXhuydjGApIOqw
gSBldmlkZW5jZSDtlYTrk5zrpbwgU09UIOybkOusuCjikaB+4pGkL+KRoH7ikaMg7JqU6rG0Keqz
vCDrjIDsobA6IFAxM+ydgCDikaHikaLikaPrp4wg6rWs7ZiEwrfikaDikaQg66+46rWs7ZiEKCJl
dmlkZW5jZSIg66y46rWs6rCAIOygle2Zle2eiCDsnbTrpbwg66qF7IucKSwgUDE064qUIOKRoOun
jCDqtaztmITCt+KRoeKRouKRoyDrr7jqtaztmIQsIFAxMeydgCAi7J207KCEIO2MkOyglSjsmYTs
oIQp7J2AIOqzvOyepeydtOyXiOydjCLsnLzroZwg7Iqk7Iqk66GcIOygleyglSDigJQg6rO87J6l
IOyXhuydtCDrs7TsiJjsoIHsnLzroZwg67aE66WY65CoLgotICoq6rK966+47ZWcIOuvuOu5hChM
T1cpKio6IGdvYWwg66y47IScIMKnNeuKlCAi7JmE7KCE4oaS6re47Jm4IuuhnCDsnqzrtoTrpZjr
kJwg7ZWt66qp7J2EIFAxM8K3UDE0wrdQMTHCt1YtNMK3Vi0xLzIvNSg36rCcKeuhnCDsl7TqsbDt
lZjsp4Drp4wsIOyLnOyekSDquLDspIDqsJIo7JmE7KCEPTYpIOuMgOu5hCDsi6TsoJwg7LWc7KKF
6rCSKOyZhOyghD0xKeydmCDtlZjrnb3tj60oNeqwnCnqs7wg7KCV7ZmV7Z6IIDE6MeuhnCDrjIDs
nZHrkJjripQg6re86rGw7ZGc64qUIGdvYWwg66y47IScIOyekOyytOyXlCDsl4bri6Qo6rCc67OE
IGV2aWRlbmNlIO2VhOuTnOyXkOuKlCDsnojsnYwpLiDstZzsooUg7YyQ7KCVIOygle2ZleyEsSDs
npDssrTsl5Qg7JiB7ZalIOyXhuydjCDigJQg7KCV67O0IOuIhOudveydvCDrv5AsIOyLpO2WiSDq
srDqs7zqsIAg7J2066+4IOybkOuzuCDsp4Tsi6QuCgojIyA4KSDsg4ggcHJlLWNvbW1pdCDtlYTs
iJjtjIzsnbwg7JqU6rWs6rCAIOq4sOyhtCBmaXh0dXJlwrfsoJXsg4Eg7Ya17KCc66W8IO2ajOq3
gOyLnOy8sOuKlOqwgAoKYGBgCmJhc2ggc2NyaXB0cy9zZXNzaW9uLXN0YXR1cy5zaCDihpIgUkVE
OiAyLzIzIChhY2NlcHRhbmNlLTAtNy5zaCDsoJzsmbgg4oCUIENJIOuLtOuLuSkKYGBgClJFRCAy
6rG0IO2ZleyduDogYGFjY2VwdGFuY2UtMC0yLnNoYChyYz0yLCDroZzsu6wgYC5zZWNyZXQtcGF0
dGVybnNgIOu2gOyerCDigJQgUFLqs7wg66y06rSALCDstZzsooUg7IiY7KCVIOy7pOuwiyBgNmE0
ZjJmMGDroZwg7J20IFBSIOydtOyghOu2gO2EsCDsobTsnqwp7JmAIGBhY2NlcHRhbmNlLXByaW5j
aXBsZXMtY2hlY2suc2hgKHJjPTEsIOydmOuPhOuQnCBQMV9VTk1FVCkuIOuCmOuouOyngCAyMeqw
nCBhY2NlcHRhbmNlIOyKpO2BrOumve2KuCArIGB2ZXJpZnkuc2hg64qUIOyghOu2gCBHUkVFTi4g
7KCV7IOBIOustOq0gCDsu6TrsIsoUkVBRE1FIOyImOyglSnrj4QgcHJlLWNvbW1pdCDthrXqs7wg
7ZmV7J24KMKnMikuIO2ajOq3gCDsl4bsnYwuCgojIyA5KSBnaXQgZGlmZiAtLWNoZWNrIOygle2V
qeyEsQoKYGBgCmdpdCBkaWZmIC0tY2hlY2sgb3JpZ2luL21haW4gSEVBRCAgIOKGkiByYz0wCmdp
dCBkaWZmIC0tY2hlY2sgKHdvcmtpbmcgdHJlZSDtj6ztlagsIOuvuOy7pOuwiyDrrLjshJzsiJjs
oJUg7Y+s7ZWoKSDihpIgcmM9MApnaXQgZGlmZiAtLWNoZWNrIEhFQUQgICAgICAgICAgICAgICAg
4oaSIHJjPTAKYGBgCuyghOu2gCDtgbTrprAuICjstIjquLDsl5AgYGdpdCBkaWZmIC0tY2hlY2sg
N2JkMzI5OCA5MjkyNDdhYCDsi6Ttlonsl5DshJwgdHJhaWxpbmcgd2hpdGVzcGFjZeqwgCDrs7Ts
mIDripTrjbAsIOydtOuKlCDsnbTroKXsg4Eg7KSR6rCEIOy7pOuwiyDsgqzsnbTsnZggZGlmZuyd
tOupsCDsnbTtm4Qg7Luk67CLIGA0MjYzOTY1YOyXkOyEnCDsoJXrpqzrkJjslrQg7ZiE7J6sIEhF
QUTsl5DripQg64Ko7JWE7J6I7KeAIOyViuydjCDigJQg67OE64+EIO2ZleyduO2VqCkKCiMjIDEw
KSBQMSDsmYTsoIQg7Iuk7YyoIOybkOy5meqzvCDrspTsnIQg7Jm4IOuqheyLnAoKYGBgClAxX1VO
TUVUOiAzMS8zMiDigJQgUDEsUDIsLi4uLFYtNSAgIChyYz0xKQpgYGAKMeqwnChQMjEp66eMIOyZ
hOyghCtDSeuwsOyEoCDstqnsobEsIDMx6rCcIOuvuOy2qeyhsSDsi5wg7KCV7ZmV7Z6IIOyLpO2M
qCjshKTqs4Qg66Gc7KeBIGBhY2NlcHRhbmNlLXByaW5jaXBsZXMtY2hlY2suc2g6Mzg5LTM5M2Dr
j4Qg7L2U65OcIOqygO2GoOuhnCDsnqztmZXsnbgg4oCUIOyZhOyghCAzMuqwnCDspJEgMeqwnOun
jCDsobDqsbQg66+464us7J207Ja064+EIGB1bm1ldGAgbm9uLWVtcHR5KS4gIuyehOydmCDsvZTr
k5wg7JW97ZmUIOyghOyytCDsnpDrj5ntjJDrs4TsnYAg67KU7JyEIOuwliLsnbTrnbzripQg66qF
7Iuc64qUIGdvYWwg66y47IScIMKnOCwgQUMy7JeQIOydtOuvuCDsobTsnqwuCgotLS0KCiMjIOy2
lSDrtoTrpqwg7LWc7KKFIO2MkOyglQoKfCDstpUgfCDtjJDsoJUgfAp8LS0tfC0tLXwKfCDqtazt
mIQg7KCV7ZmV7ISxKOyKpO2CpOuniC9tZWNoYW5pc20v7ZqM6reAL2d1YXJkKSB8ICoqUEFTUyoq
IOKAlCAxMOqwnCDqs7Xqsqkg7KCE67aAIOuwqeyWtCDtmZXsnbgo64+F66a9IOyerO2YhCkgfAp8
IOydmOuPhOuQnCBQMSDsi6TtjKgoRGVzaWduIEIpIHwgKirsoJXsp4HtlZjqsowg7J6s7ZiE65Co
Kiog4oCUIGBQMV9VTk1FVDogMzEvMzJgLCBleGl0IDEgfAp8IOuhnOy7rCBDSS1lcXVpdmFsZW50
IHwgKipQQVNTKioo7YyM7J28IOyhtOyerC/si6Ttlokg6rKA7IKsIO2GteqzvCkg64uoIOyghOyy
tCDtjIzsnbTtlITrnbzsnbgg7KSRIGBhY2NlcHRhbmNlLXByaW5jaXBsZXMtY2hlY2suc2hgIOye
kOyytOuKlCBQMV9VTk1FVOycvOuhnCBSRUQgfAp8IOyLpOygnCBHaXRIdWIgQWN0aW9ucyDshJzr
soQg7Iuk7ZaJIHwgKipCTE9DS0VEKiog4oCUIOybkOqyqSDtl6Trk5zripQgYDkyOTI0N2FgKOuh
nOy7rOuztOuLpCAz7Luk67CLIOuSpCksIOy0iOuhnSDssrTtgawgMuqxtOydgCDsg4ggM+y7pOuw
i+ydhCDqsoDspp3tlZwg7KCBIOyXhuydjCB8Cnwg67OR7ZWpIOqwgOuKpeyEsSB8ICoq7JWE64uI
7JikKiog4oCUIFAxIOuvuOy2qeyhsSArIOyEnOuyhCDqsoDspp0g67aI6rCA66GcIOuzke2VqSDr
tojqsIAgKGdvYWwg66y47IScIOqysOuhoOqzvCDsnbzsuZgpIHwK
~~~~

<!-- CLAUDE_RAW_END -->

## Codex 2차 재공격

| Claude 주장 | Codex 재현 | 판정 |
|---|---|---|
| CI 고정 파일·직접 실행 배선 | `verify.yml:22-35` 직접 대조 | 일치 |
| 스키마·20개 mutation | harness 20/20 및 checker 186-215행 재현 | 일치 |
| mechanism 삭제·배선 제거 탐지 | `MECHANISM_PATH_MISSING`, `MECHANISM_CHECK_DISCONNECTED` 재현 | 일치 |
| 기준선 없음은 PASS가 아님 | checker 383-385행과 실제 출력 대조 | 일치 |
| 동일 UID guard 우회 | 격리 guard 8/8 중 위조 후 check 0 재현 | 일치; 보장 범위 축소 유지 |
| 기존 A4 fixture 무회귀 | 시작 HEAD A4=0, 중간 회귀=1, fixture 보정 뒤 30/30=0 | 일치; 이번 작업에서 추가 수리 |
| pre-commit까지 동시 삭제하면 commit 가능 | 격리 clone에서 3파일 동시 삭제 commit=0, pre-push=1, CI 고정 존재검사=1 | 일치; Git 훅 구조 한계이며 후단 차단 존재 |
| 현재 집계 1/12/7/4/8 | Psych 재계산과 7개 변경 대조 | 일치 |
| 과거 수치는 V2 기록에만 존재 | `rg` 결과 V1에도 8개 문구 존재 | 불일치; V1/V2 둘 다 역사 기록 배너 추가 |
| goal에 정정 전후 1:1 표가 부족 | 7개 변경을 이전/이후/근거 표로 재계산 | 일치; 이 문서에서 보완 |
| 공백 오류 없음 | worktree와 `origin/main...HEAD` 모두 0 | 일치 |
| P1 31/32 미충족 | 전체 검사 exit=1, pre-push exit=1 | 일치 |

새로 발견한 문서 누락은 workflow를 이름 있는 21개로만 적어 총 스텝을 21개처럼 보이게 한 문구였다. `checkout 1 + 검증 21 = 총 22`로 정정했다.

### Claude 문서 재확인과 수리

두 번째 `env -u ANTHROPIC_API_KEY claude -p`는 `VERDICT: FAIL`이었다. 코드 결함이 아니라 첫 원문 자체의 `### 삭제(두 파일 동시): ` 후행 공백을 그대로 넣어 `git diff --check=2`가 된 것이 유일한 실패였다. 두 번째 출력도 같은 예시 끝에 공백을 다시 생성했으므로, 읽기용 원문은 줄 끝 공백만 제거하고 바이트 원문은 SHA-256+Base64로 이 문서에 보존하는 저장 계약으로 바꿨다. Base64 decode와 `/tmp/pr31-claude-adversarial.txt`는 byte-for-byte 동일했고, 수정 직후 `git diff --check=0`을 재현했다.

깨끗한 `0275da5`에서 세 번째 폐쇄 검증을 같은 guard 절차로 실행했다. Claude는 `VERDICT: PASS`를 반환했고 `git status` 빈 출력, 두 diff check 0, Base64 해시 일치, schema exit 0, 의도된 `P1_UNMET 31/32` exit 1, 실제 서버 실행 BLOCKED, 병합 불가를 재확인했다. guard check와 unlock도 각각 0이었고 시작 SHA-256과 종료 SHA-256은 같았다.

현재 상태: `LOCAL_IMPLEMENTATION_VERIFIED / P1_FAIL / SERVER_BLOCKED / MERGE_NOT_ALLOWED`

## 9) 새 결함 재현과 pre-push/CI 권한 분리

### RED

기존 pre-push는 인자 없이 `acceptance-principles-check.sh`를 실행했다. 현재 현황표는
`완전 1 / 부분 12 / 없음 7 / 해당없음 4 / 미확인 8`이므로, 로컬 push도 `P1_UNMET:
31/32`에서 실패했다. P1 미충족 사실은 정확하지만, 아직 해당되지 않는 원칙을
현황표에 기록하는 동안 모든 unrelated push를 막는 결함이었다.

### 설계 판단

`해당없음`을 P1 전체 판정에서 조용히 제외하지 않는다. `principles.yaml`은 32개
원칙의 현황표로 남고, CI의 기본 `--full` 실행은 SOT P1대로 미충족 항목이 있으면
계속 실패한다. 대신 `hooks/pre-push`는 명시적 `--pre-push` 모드로 스키마·mechanism
경로/정적 배선·기준선 회귀만 검사한다. 이 모드는 P1 완성을 의미하지 않으며,
완전성 판정 권한은 workflow의 인자 없는 full 실행에 있다. A안/B안 어느 것도
미구현 원칙을 합격시키는 근거로 사용하지 않았다.

### GREEN 증거

- `scripts/acceptance-principles-check.sh --full`: `P1_UNMET: 31/32`, exit `1`.
- `scripts/acceptance-principles-check.sh --pre-push`: `P1_LOCAL_GATE: ...`, exit `0`.
- mutation harness: 정상 표 full 실패와 pre-push 성공을 각각 검증; 전체 `CHECKED: 21`.
- 실제 pre-push는 이번 변경이 미커밋인 상태에서 P15 청결성 검사로 exit `1`을 냈다. 이는 새 P1 완성 판정이 아니라 작업트리 오염 차단이며, clean fixture에서 pre-push 모드 checker가 0이 되는 것을 harness가 검증한다.

이 변경은 P1을 완성시키지 않는다. 로컬 push의 영구 차단만 제거하고, 새 커밋에 대한
실제 GitHub Actions 실행은 push 금지로 계속 `BLOCKED`다.

## 10) "원칙에 안 맞는 걸 최대한 고치자" — 사장님 지시 이행 (2026-08-19 후속)

### 사장님 브리핑

**결론:** push 금지가 풀린 뒤 실제 CI를 6차례 돌리며 매번 다른 진짜 환경 차이 버그(macOS/Linux 차이, `bash -e` 실행모드 차이, Ruby 라이브러리 버전 차이)를 고쳤지만, 마지막에 CI가 멈추는 지점은 버그가 아니라 이 PR 자신이 설계해 넣은 "32개 원칙 중 하나라도 안 채워지면 무조건 실패"라는 안전장치였다. 이 사실을 보고드리자 "원칙에 안 맞는 건 뭔지 확인하고, 수정할 수 있는 건 최대한 수정하자"는 지시를 받았다. 32개를 전부 채우는 건 이번에 불가능하다 — 4개(P7·P8·P9·P10)는 아직 존재하지 않는 사업 기능(배포 파이프라인·3사 동시접속 소싱·발송 DB·매일 사업 요약 전송)에 대한 원칙이라 "해당 없음"이고, 나머지 다수는 이 저장소 하나로 끝낼 수 없는 별도의 큰 설계 작업이다. 이번에 실제로 채운 건 P3(조용한 실패 금지)의 절반이다 — 이 저장소에 아직 위반 코드가 0건인 지금 시점에 bare except/catch·`??`·`||[]` 4가지 패턴을 막는 검사기를 새로 만들어 커밋 시점과 서버 검사 양쪽에 심었다. 이 검사기를 만들고 검증하는 과정에서 진짜 버그 2개를 추가로 찾아 고쳤다 — 하나는 이번에 내가 만든 코드에 있었고, 하나는 이번 작업과 무관하게 예전부터 있던 것이다.

**판단 근거:** 32개 중 "지금 당장 고칠 수 있는가"를 기준으로 골랐다. P3는 ⑴ 이 저장소가 아직 작아서(파이썬 5개 파일, JS/TS 0개) 위반이 0건인 깨끗한 상태고 ⑵ SOT에 검사 방법이 정확히 적혀 있고(`docs/sot/coding-principles.md:18`) ⑶ 새 사업 기능을 만들 필요 없이 순수 검사 로직만 추가하면 되는 조건을 모두 만족했다. 다른 원칙들(예: P17 "증거는 만든 자가 쓸 수 없다"는 권한 분리 시스템 전체 설계가 필요, P19 "라이브 스모크"는 저장소 전체 경로 자동분류가 필요)은 이번 세션 하나로 안전하게 끝낼 수 있는 규모가 아니라고 판단해 손대지 않았다. 버린 대안: 4개의 "해당 없음" 원칙을 principles.yaml에서 삭제하는 것도 검토했으나(P1 자신의 "기계 장치 없는 원칙은 삭제한다"는 문구 근거), 원칙 삭제는 SOT의 근본적인 축소이자 사업 범위 판단이라 제가 혼자 결정할 사안이 아니라고 보고 보류했다.

**틀리면 깨지는 것:** 만약 P3 검사기의 정규식이 실제 위반을 놓친다면(예: 여러 줄에 걸친 catch, 문자열 안의 `??`), "검사기가 있으니 안전하다"는 잘못된 안도감만 주고 실제로는 조용한 실패가 계속 스며든다 — 그래서 아래에 codex 적대검증을 별도로 요청했다.

### AC (이번 증분)

- **AC-P3-1**: `docs/sot/coding-principles.md:18`의 4패턴(bare except/catch, `??`, `catch{return null}`, `||[]`)이 py/js/ts 파일 전체에서 검사되고, 위반 시 exit 1을 낸다.
  검증: `bash scripts/acceptance-silent-failure-lint.sh`
  counter-AC: 정규식이 문법 변형(공백·여러 줄)에 우회되면 가짜.
- **AC-P3-2**: 위 검사가 hooks/pre-commit과 CI(.github/workflows/verify.yml) 양쪽에 실제로 배선된다.
  검증: `bash hooks/pre-commit`(스테이지 후) + `bash scripts/acceptance-principles-check.sh`의 SCHEMA_OK 확인
  counter-AC: 배선 문구만 있고 실제 호출이 없으면 가짜(§3.5 배선 증명 요구).

### 구현 요약

커밋 `228b384`(P3 린트 신설) + `f7f0a6b`(hooks/pre-commit 과요구 완화 + `scripts/acceptance-hs-a4.sh`의 선행 `bash -e` 잠복 버그 수정). 상세 근거·검증 로그는 각 커밋 메시지에 전문 보존.

발견한 버그 2건:
1. **이번 작업에서 만든 버그**: `hooks/pre-commit`의 새 §8이 `set -e` 아래서 "위반 없음" 케이스에 `grep '^FAIL:' | head -1`(매치 없음=exit 1)로 파이프 전체를 죽여 **정상 커밋이 원인 불명으로 실패**하는 잠재 결함. 격리 임시 저장소에서 실제 훅을 정상 파일로 돌려보고 발견.
2. **이번 작업과 무관한 기존 버그**: `scripts/acceptance-hs-a4.sh`가 `HEAD~2` 시점부터 동일하게, `out=$(...)` 를 독립 문장으로 두어 기대한 실패(exit 1)가 `set -e` 아래서 스크립트 전체를 조기 종료시키는 결함을 갖고 있었다. CI에서 이제까지 드러나지 않은 이유는 이 스텝보다 앞선 "P1 원칙 32개 전체 강제 검사"가 설계상 항상 실패해 뒤 스텝이 실행된 적이 없었기 때문이다 — 로컬 pre-push(글롭으로 전량 실행)에서 처음 걸렸다.

### 검증 결과 (로컬, 전부 `bash -e`)

- `acceptance-silent-failure-lint.sh`: CHECKED_FILES=5, PASS, exit=0
- `acceptance-silent-failure-lint-mutations.sh`: 11/11 PASS(4패턴 주입 각각 + 정상 fixture + 0건 NOT_RUN + 실제 hooks/pre-commit end-to-end 위반/정상 2건 + 원본 무변경)
- `acceptance-principles-mutations.sh`: 21/21 PASS(회귀 없음, fixture 조립 목록에 신규 파일 2개 반영 후)
- `acceptance-guard-global-skill-files.sh`: 8/8 PASS(회귀 없음)
- `acceptance-hs-a4.sh`: 30/30 PASS, exit=0(수정 전: 6번째 PASS 직후 즉사)
- `acceptance-principles-check.sh`: SCHEMA_OK 32/32, STATUS_COUNTS 완전=1 부분=12 없음=7 해당없음=4 미확인=8(변화 없음), P1_UNMET 31/32(변화 없음)
- push 후 실제 CI(`runs/32229657428` 등): "P1 원칙 32개 전체 강제 검사" 스텝에서 SCHEMA_OK 32/32 확인 후 설계된 P1_UNMET으로 실패 — 새 오류 없음, 이 스텝 이후 스텝(P3 검사 포함)은 job이 fail-fast라 실행되지 않음(로컬 pre-push만 전량 실행하는 구조라 그쪽에서 이미 검증됨)

### 적대 검증 로그

**codex(V1) 판정: `VERDICT: FAIL`.** 전문은 `private-reviews/p3-silent-failure-verdict-2026-08-19.md`에 원문 그대로 보존(격리 재현, `/tmp/p3-audit.DIyfQs`에서 공격 파일 작성 후 실제 검사기·훅에 통과시켜 확인).

**핵심 발견 (요구사항 R1~R6 중 R1·R2-b·R2-c 실패, 나머지는 합격):**
1. **R1 실패 — 정규식이 문법 변형에 우회된다.** 여러 줄 `catch (e) {\n}`, `catch\n(e)\n{\n}`, 주석만 있는 catch, 역슬래시 줄바꿈 `except \` 등 유효한 정상 문법이 6개 중 6개 놓쳤다. 반대로 독스트링·문자열·주석 안의 리터럴 텍스트(`"catch (e) {}"`, `` `... ?? ...` ``)는 3개 잘못 잡았다.
2. **R2-b/R2-c 실패 — 같은 커밋에서 검사기 자체를 무력화할 수 있었다.** `except` 탐지 정규식을 `NEVER-EXCEPT`로 바꾸면서 bare except 위반 파일을 같은 커밋에 스테이지하면, hooks/pre-commit이 무력화된 확정본으로 자기 자신을 검사해 exit 0(통과)을 냈다. `.github/workflows/verify.yml`에서 P3 검사 스텝은 그보다 앞선 "P1 원칙 32개 전체 강제 검사"가 설계상 항상 실패해 실제로 도달한 적이 없다는 것도 재확인됨 — "서버가 로컬 우회를 보완한다"는 기대는 현재 순서에서 성립하지 않는다.
3. **R2-a·R3·R4·R5·R6은 합격.** 스테이지된 인덱스 내용을 실제로 검사한다는 주장(작업트리 덮어쓰기 우회 불가), 뮤테이션 시험이 tautology가 아니라는 것(탐지 줄 5개를 하나씩 지우자 매번 FAIL), P3 상태 "부분" 표기의 정직성, `acceptance-hs-a4.sh`의 5곳 `bash -e` 수정이 실제로 유효하고 이번 작업과 무관한 기존 결함이었다는 것(HEAD~2에도 동일 결함 확인), 다른 31개 원칙 상태가 실수로 바뀌지 않았다는 것(STATUS_COUNTS 완전=1/부분=12/없음=7/해당없음=4/미확인=8 그대로) — 전부 codex가 직접 재현해 확인.

**Claude(V2) 재공격 — codex 판정의 격리 재현:**

codex가 제시한 "같은 커밋에서 검사기 무력화" 공격(R2-b/R2-c)을 별도의 격리 임시 git 저장소에서 직접 재현했다. `perl -pi -e` 로 `except` 탐지 정규식을 `NEVER-EXCEPT` 로 바꾸고 bare-except 위반 python 파일을 같은 커밋으로 `git add` 한 뒤 실제 `hooks/pre-commit`(수정 전 버전)을 그대로 실행:

```text
pre-commit exit=0
```
→ 뭘 시켰나: codex가 보고한 정확히 같은 공격을 재현. / 뭐가 나왔나: 위반 코드가 통과했다. / 좋은 소식인가 나쁜 소식인가: codex 판정과 100% 일치 — 실제 결함으로 확인.

**수정(커밋 예정): `hooks/pre-commit` §9 신설.** 검사기 자신(`scripts/acceptance-silent-failure-lint.sh`) 또는 그 뮤테이션 시험이 이번 커밋에 포함되면, **커밋될 확정본**으로 뮤테이션 시험(`scripts/acceptance-silent-failure-lint-mutations.sh`)을 재실행해 알려진 위반 패턴을 여전히 잡아내는지 확인한다. 뮤테이션 시험은 자체 fixture로 위반을 주입하므로 공격자가 무엇을 스테이지했는지와 무관하게 항상 같은 결론을 낸다. 같은 재현 절차로 수정 후 버전을 재시험:

```text
[1] 공격(weaken+violation 같은 커밋) exit=1 — BLOCKED: P3 검사기 자체가 같은 커밋에서 무력화됨
[2] 정상 커밋(README만) exit=0
[3] 검사기 무해한 자기개선(주석만 추가) exit=0
```
→ 뭘 시켰나: 공격·정상 커밋·무해한 자기개선 3가지를 수정 후 훅으로 재현. / 뭐가 나왔나: 공격만 막히고 나머지 둘은 정상 통과(벽이 아니라 게이트). / 좋은 소식인가 나쁜 소식인가: 좋은 소식 — 가장 심각했던 결함이 닫혔다.

**부작용 발견 및 수정: 무한 재귀.** §9가 뮤테이션 시험 전체를 재호출하는데, 그 시험 안에 이번에 새로 추가한 "실제 hooks/pre-commit 배선" 테스트(§9~10, HOOKREPO 기반)가 다시 `bash hooks/pre-commit`을 부르면서 `pre-commit → 뮤테이션시험 → pre-commit → ...`로 재귀에 빠졌다(2026-08-19 실측: 15초 이상 무응답, 강제 종료). `P3_SKIP_HOOK_SUBTESTS` 환경변수 가드를 추가해, §9에서 뮤테이션 시험을 재호출할 때는 패턴 탐지 능력만 재확인(1~8번)하고 자기 자신을 재귀 호출하는 구간(9~10번)은 건너뛰도록 고쳤다.

**R1(정규식 우회)은 이번 범위에서 고치지 않는다.** codex의 권고(언어별 구문 분석기로 교체)는 Python은 `ast` 모듈, JS/TS는 별도 파서/린터가 필요한 훨씬 큰 작업이라 이번 증분 세션 하나로 안전하게 끝낼 수 있는 규모가 아니라고 판단했다. `docs/sot/principles.yaml`의 P3 evidence에 이 한계를 정직하게 기록하고 "부분" 상태를 유지한다 — codex가 잡은 과장(R1을 "완전"으로 암시하지 않았는지) 재점검 결과, 원래 커밋 메시지가 "실질적인 안전장치"라고 쓴 것은 R2-b/R2-c 결함을 몰랐던 시점의 과장이었음을 인정하고 이 로그에 정정을 남긴다.

**갈리거나 뒤집힌 판정:** 없음. codex의 6개 요구사항별 판정(R1·R2-a·R2-b·R2-c·R3·R4·R5·R6) 전부를 Claude가 최소 1개 이상 재현해 일치를 확인했다(R2-b/R2-c는 공격 재현, 나머지는 codex 증거 원문과 로컬 재실행 대조). G(구현)·V1(codex)·V2(Claude)가 "R1·R2-b/c는 미해결 잔여 한계, 그 외는 실제 구현"이라는 결론에서 수렴했다.

**최종 검증 (수정 반영 후, 전부 bash -e):**
- `acceptance-silent-failure-lint-mutations.sh`: 13/13 PASS(자기 무력화 공격 BLOCKED + 무해한 자기개선 통과 2건 추가, 재귀 없음 확인)
- `acceptance-principles-mutations.sh`: 21/21 PASS(회귀 없음)
- `acceptance-guard-global-skill-files.sh`: 8/8 PASS(회귀 없음)
- `acceptance-hs-a4.sh`: 30/30 PASS(회귀 없음)
- `acceptance-principles-check.sh`: SCHEMA_OK 32/32, STATUS_COUNTS 완전=1 부분=12 없음=7 해당없음=4 미확인=8(변화 없음)
- 실제 `hooks/pre-commit`으로 이 커밋 자체(hooks/pre-commit + acceptance-silent-failure-lint-mutations.sh 동시 수정)를 스테이지해 exit 0 확인
- guard-global-skill-files lock/check/unlock 정상 수행, 시작·종료 SHA-256 일치
