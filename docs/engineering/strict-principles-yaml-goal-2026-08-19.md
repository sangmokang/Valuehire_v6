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
- push·merge·배포·메일 발송과 전역 `~/.claude`, `~/.codex` 수정은 금지한다.
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

## 5. 상태 재분류와 집계 규칙

- 작업 시작 기준값은 `완전 6 / 부분 12 / 없음 5 / 해당없음 4 / 미확인 5`다.
- 과거 초안의 `완전 8 / 부분 10`은 폐기된 과거 수치이며 현재 판정으로 사용하지 않는다.
- P13과 P14는 SOT 전체 요구를 충족하지 않으므로 `완전 → 부분`으로 낮춘다.
- 현재 브랜치에 파일이 없는 P11, 기계 장치가 없는 V-4, 저장소·CI가 확인할 수 없는 전역 스킬 기반 V-1/V-2/V-5도 계약에 맞게 다시 판정한다.
- 최종 집계는 YAML을 Psych로 읽어 다시 계산하며 기존 숫자에 맞추지 않는다. 변경 전 값, 변경 항목, 변경 후 값을 분리해 보고한다.

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

- 게이트 0 실제 명령: `bash scripts/session-status.sh`. 첫 시도는 HEAD/ORIGIN 두 줄 뒤 최종 RED 줄을 확보하지 못해 아직 `NOT_RUN`이며 개별 acceptance의 지연·종료 경로를 진단해 재실행한다.
- 게이트 4: 변경 셸 `bash -n`, Psych parse, mutation harness, `bash verify.sh`, 저장소 실제 CI 명령, `git diff --check`.
- CI-equivalent는 로컬 실행으로만 표기한다. GitHub Actions 서버 판정으로 승격하지 않는다.
- 필수 실패·NOT_RUN·BLOCKED를 PASS로 바꾸지 않는다.

## 8. 위험과 중단 조건

- 기본 전체 principles 검사는 현재 의도적으로 빨갛다. 이는 32개 장치가 완성되지 않았다는 P1의 정직한 결과다.
- CI 배선이 없거나 필수 파일 삭제가 통과하거나 guard 범위를 정직하게 표현하지 못하면 로컬 구현도 FAIL이다.
- 새 서버 실행은 권한상 BLOCKED이므로 PR은 병합 불가다.
- mechanism 파일의 존재·호출 정적 배선과 선택된 mutation은 보지만, 임의 코드 약화 전체를 자동 판별하는 것은 이번 범위 밖이다.

## 9. PR #32 읽기 전용 정정 계획

`task/codeaudit-wrap-2026-08-19`의 roadmap/보고에는 PR #31 완료, 서버 검증, guard의 쓰기 방지 범위, D3 판정을 현재 근거에 맞게 다시 써야 한다. 이 작업에서는 파일을 수정하지 않고 최종 보고에 `PR #32 정정안 준비`로만 기록한다.

## 10. 적대 검증 로그

Claude 1차는 guard `lock → claude -p → check → unlock` 순서로 실행한다. 원문을 이 절에 그대로 보존한다. Codex 2차는 Claude의 모든 `file:line`과 명령을 재현하고 PASS와 FAIL을 모두 공격해 일치·불일치·새 누락을 표로 남긴다.

현재 상태: `IN_PROGRESS`
