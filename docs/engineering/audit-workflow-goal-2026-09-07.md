# 시간-부패 검사 전용 워크플로 audit.yml 신설 — goal (2026-09-07)

## 상위 목표

`verify.yml`은 push/PR이 있을 때만 돈다. 그런데 "억제(suppressions.yaml) 만료일이 지났는가"처럼 **아무도 커밋을 안 해도 시간이 지나면 저절로 문제가 되는 검사**는 push/PR 트리거만으로는 아무도 안 볼 수 있다 — 만료일이 지나도 다음 커밋이 올라올 때까지 아무도 모른다. 매일 새벽 혼자 도는 `audit.yml`을 추가해 이 빈틈을 막는다. **성공 신호**: (1) 억제 만료 스캔이 push/PR과 무관하게 매일 자동으로 돈다, (2) 서드파티 GitHub Action이 가변 태그로 되돌아가면(SHA 고정이 풀리면) 자동으로 잡힌다, (3) 실패 시 사람이 알 수 있다(GitHub 기본 이메일 알림 — 사장님 선택).

## 배경 — 이 작업이 나온 경위

사장님이 checkout SHA 고정 작업(PR #67, `docs/engineering/checkout-v7-sha-pin-goal-2026-09-07.md`) 완료 보고를 받은 뒤, 외부에서 받은 피드백(`.github/workflows/`를 `verify.yml`/`audit.yml`/`lint-pr.yml` 3개로 역할 분리하자는 제안)을 전달했다. 검토 결과 `audit.yml`·`lint-pr.yml` 분리는 채택 추천, `push`+`pull_request` 중복 실행 제거는 이 저장소에 브랜치 보호가 없다는 사정과 충돌해 별도 결정 보류로 사장님께 보고했다. 사장님이 `audit.yml` 내용을 먼저 요청했고, 실패 알림 방식으로 "이메일"(GitHub 기본 동작, 별도 스텝 불필요)을 선택해 이번 WU를 시작한다. `lint-pr.yml`은 이번 WU 범위 밖이다(비범위 참고).

## 현재 상태 (file:line)

- `.github/workflows/verify.yml:139-159` — "억제 만료 스캔" 스텝이 **인라인 셸 스크립트**로 존재. push/pull_request/workflow_dispatch에서만 실행.
- `hooks/pre-commit:115-134` — **같은 판정 로직**(형식 검사+만료 비교)이 커밋 시점 `staged` 콘텐츠 대상으로 별도 구현되어 있다. 이 두 곳은 "커밋 시점 staged"와 "현재 워킹트리"라는 서로 다른 입력을 보므로 **이번 WU에서 통합하지 않는다**(아래 결정 목록 2).
- `.github/workflows/` 디렉터리에는 현재 `verify.yml` 1개만 존재.
- `.github/dependabot.yml` 없음(이전 WU에서 확인한 그대로, 변화 없음).
- 이 브랜치는 `main`(01495b3)에서 분기했다 — PR #67(checkout SHA 고정)은 아직 병합 전이라 이 브랜치의 `verify.yml:18`은 여전히 `actions/checkout@v4`(가변 태그)다.

## 읽은 SOT

- `docs/sot/verification-commands.md` — CI(`verify.yml`)가 실제로 도는 26개 스텝의 표. 새 워크플로 파일을 추가하면 이 문서도 함께 갱신해야 "표를 실행해서 확인한 결과"라는 이 문서 자신의 원칙이 유지된다.
- `docs/sot/coding-principles.md` P13 — 검사 파일(CI 워크플로 포함) diff는 원칙상 `weakens-check` 라벨 대상. 이번 변경은 검사를 **추가**하는 것이라 약화가 아니다(라벨 미부착, 이전 WU와 동일 근거).
- `docs/sot/git-workflow.md` — 워크트리 생성 명령 확인, `worktrees/audit-workflow-20260907` 생성.
- SOT에 "같은 판정 로직을 두 곳에 적으면 반드시 갈라진다"는 원칙이 `scan-data-exposure.sh`("CI 도 인수검사도 같은 파일을 실행") 등 여러 곳에 반복 등장 — 이번 WU가 `verify.yml`의 인라인 로직을 스크립트로 뽑아 `audit.yml`과 공유하는 이유.

## 결정 목록

1. **`lint-pr.yml`은 이번 WU에 포함하지 않는다.** 사장님이 `audit.yml` 내용만 먼저 요청했다. 별도 WU로 남긴다(비범위).
2. **`hooks/pre-commit`의 만료 검사 로직은 건드리지 않는다.** `verify.yml`(워킹트리 파일 대상)과 `pre-commit`(staged 콘텐츠 대상)은 입력 소스가 다르다 — 억지로 한 스크립트로 합치면 "staged vs. 워킹트리"라는 실제 차이를 스크립트 인자로 숨기게 되어 오히려 더 헷갈린다. 이번엔 `verify.yml`↔`audit.yml`처럼 **입력이 완전히 같은 두 곳**만 스크립트 공유 대상으로 삼는다.
3. **액션 SHA 드리프트 검사의 실시간 실측 결과**: 이 브랜치는 아직 PR #67을 포함하지 않아 `verify.yml`의 checkout이 여전히 `@v4`다. 그래서 이 스크립트를 지금 저장소에 대고 실행하면 **정상적으로 FAIL이 나온다**(실측 예정, 아래 게이트 계획). 이건 스크립트 결함이 아니라 PR #67 병합 대기 상태를 정확히 반영하는 것이다 — PR #67이 먼저 병합되면 자동으로 PASS로 바뀐다. 이 사실을 숨기거나 억지로 맞추려고 이 브랜치에서 `verify.yml`의 checkout 줄까지 같이 고치지 않는다(그러면 PR #67과 내용이 겹쳐 병합 순서에 따라 불필요한 혼선이 생긴다).
4. **`audit.yml`은 CI(`verify.yml`)가 아니므로 병합 게이트가 아니다.** 이 PR의 병합 가능 여부는 여전히 `verify.yml`의 초록불로만 판단한다(로컬에서 `audit.yml`을 검증하는 방법은 아래 게이트 계획 참고).

## 인수 기준 (EARS)

- **AC-1**: `scripts/check-suppression-expiry.sh`가 `verify.yml`의 기존 인라인 로직과 **동일한 입출력**(같은 저장소 상태에서 같은 종료값·같은 PASS/FAIL 문구)을 낸다.
  검증: 추출 전/후 각각 `bash scripts/check-suppression-expiry.sh`(추출 후) vs 추출 전 인라인 스크립트를 같은 `suppressions.yaml`에 대해 실행해 출력 대조.
- **AC-2**: `.github/workflows/audit.yml`이 `schedule`(매일 새벽 KST)과 `workflow_dispatch`로 트리거되고, 억제 만료 스캔(스크립트 공유)과 액션 SHA 드리프트 검사 2개를 실행한다.
  검증: `actionlint` 없으므로 `ruby -ryaml -e 'YAML.safe_load(...)'`로 구문 검증 + `acceptance-ci-step-integrity.sh`가 이 새 워크플로도 구조적으로 무결한지 확인(그 스크립트가 다중 워크플로 파일을 지원하는지 먼저 실측).
- **AC-3**: `scripts/check-action-sha-drift.sh`가 격리된 fixture(실제 저장소를 건드리지 않는 임시 사본)에서 (a) SHA로 고정된 참조는 PASS, (b) 가변 태그로 된 참조는 FAIL로 정확히 판정한다.
  검증: 임시 디렉터리에 합성 workflow yml 2개(정상/반례)를 만들어 스크립트 실행, 종료값 대조.
- **counter-AC**: `check-action-sha-drift.sh`를 이 저장소(PR #67 병합 전 상태)에 대고 그대로 실행하면 `verify.yml:18`의 `@v4`를 잡아 FAIL이 나와야 한다(스크립트가 진짜로 동작한다는 반증).

## 계약 (입출력 모양)

- `scripts/check-suppression-expiry.sh`: 입력 없음(현재 디렉터리의 `suppressions.yaml` 읽음), 출력은 stdout PASS/FAIL 문구 + 종료값(0=PASS/1=FAIL).
- `scripts/check-action-sha-drift.sh`: 입력 없음(현재 디렉터리 기준 `git grep`으로 `.github/workflows/*.yml`/`*.yaml` 스캔), 출력은 stdout PASS/FAIL 문구 + 종료값(0=PASS/1=FAIL/2=검사대상 0건 NOT_RUN 취급).
- `.github/workflows/audit.yml`: 트리거 `schedule`+`workflow_dispatch`, 산출물은 워크플로 실행 로그(성공/실패)뿐 — 저장소에 파일을 쓰지 않는다.

## 게이트 계획

- RED/GREEN 유닛테스트 대상은 있다(스크립트 2개는 순수 셸 로직이라 fixture 기반 시험 가능) — AC-1/AC-3는 fresh 실행 증거로, AC-2는 YAML 구문 검사 + 구조 무결성 검사로 확인한다.
- `audit.yml`은 `verify.yml`이 아니므로 이 PR의 CI 초록불(push/PR)에는 안 걸린다. 대신 push 후 `gh workflow run audit.yml --ref <branch>`로 수동 실행해 라이브 1건을 남긴다(가능하면 — GitHub이 비-기본 브랜치의 신규 workflow_dispatch를 막을 수 있어, 안 되면 그 사실과 이유를 기록하고 로컬 fixture 증거로 갈음한다).
- `docs/sot/verification-commands.md`에 `audit.yml` 섹션을 추가해 문서-실제 상태 일치를 유지한다.

## 비범위

- `lint-pr.yml`(PR 전용 규칙 검사) — 별도 WU.
- `hooks/pre-commit`의 만료 검사 로직 통합 — 이번 WU에서 하지 않음(결정 목록 2).
- `push`+`pull_request` 중복 실행 제거 — 별도 결정 필요, 이 WU와 무관.
- `.github/dependabot.yml` — 별도 WU(이전 WU에서 이미 비범위로 기록).
- `verify.yml:18`의 checkout SHA 고정 — PR #67이 담당, 이 WU에서 손대지 않는다(결정 목록 3).

## 적대 검증 로그

### 배선 증명 (CI 라이브 로그, 2026-09-07)

PR #68 push 이벤트 CI 실행(run 34074547386)의 "억제 만료 스캔 (suppressions.yaml)" 스텝 실제 stdout: `##[group]Run bash scripts/check-suppression-expiry.sh` → `PASS: 억제 3건 전부 유효 기한 내`. 인라인 로직이 아니라 새 스크립트가 실제로 CI에서 호출·실행됨을 확인.

### V1 (fresh 서브에이전트, `humanreview` 스킬 기반, 2026-09-07)

**최초 판정: REQUEST_CHANGES.** 전문은 `docs/engineering/audit-workflow-v1-verdict-2026-09-07.md`.

확인된 것: AC-1(추출 전/후 로직 동일, 경계값 6종), counter-AC(현재 저장소에 대고 실행 시 `verify.yml`의 `@v4`를 정확히 잡음), PR #68 head SHA 일치·push/pull_request 두 이벤트 CI 성공, verify.yml diff에 검사 약화 은닉 없음.

**M-1 (유효 반례, 채택)**: `check-action-sha-drift.sh`가 **주석 처리되어 실행되지 않는** `# uses: actions/checkout@v4` 같은 줄도 실제 참조로 오판(당시 저장소에 이 패턴이 없어 즉시 오탐은 아니었으나 잠재 결함). → 매칭 전에 각 줄을 trim해 `#`로 시작하면 건너뛰도록 수정, fixture로 재확인(PASS).

**M-2 (유효 반례, 채택)**: 같은 스크립트가 유효한 **대문자 40자 SHA**를 가변 참조로 오판(`[0-9a-f]`가 소문자만 허용, git SHA는 대소문자 무관). → `[0-9a-fA-F]`로 수정, fixture로 재확인(PASS).

**M-3 (유효 반례, 채택)**: goal 문서가 "`acceptance-ci-step-integrity.sh`가 다중 워크플로를 지원하는지 먼저 실측"하라고 지시했는데 실측 기록이 비어 있었다. 실측 결과 그 스크립트가 `verify.yml`에 하드코딩되어 있어 **`audit.yml`은 구조 무결성 검사(무력화 저항)의 보호를 전혀 못 받는 상태**였다 — 누군가 `audit.yml`에 `continue-on-error: true`를 몰래 넣어도 이 저장소 어떤 자동 검사도 못 잡는 회귀 방어선 공백. → `scripts/acceptance-ci-step-integrity.sh`를 `run_battery()` 함수로 일반화해 `verify.yml`·`audit.yml` 양쪽에 동일한 무력화 8종 배터리를 돌리도록 확장(검사기 1벌 `scripts/verify/check-ci-step-integrity.sh`는 이미 워크플로 경로를 인자로 받아 그대로 재사용). 로컬 재실행: `CHECKED: 23`(기존 14 → 23), `VERDICT: PASS`.

**R9(발견 반례 영구 편입)**: M-1·M-2는 스크립트 수정 자체가 회귀 방어(같은 반례를 fixture로 재확인해 PASS 전환 확인 완료). M-3는 CI에 이미 등록된 기존 인수 검사(`acceptance-ci-step-integrity.sh`, `verify.yml` 22번 스텝)의 커버리지를 넓히는 것으로 편입했다 — 새 스크립트를 만들지 않고 기존 검사기를 일반화해 "검사기 1벌" 원칙을 유지했다.

**정정 후 상태**: 위 3건 모두 이 PR 안에서 코드로 반영·재검증 완료. `.github/workflows/audit.yml`/`verify.yml`의 트리거·나머지 스텝은 이번 정정에서 변경 없음.
