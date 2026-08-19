# 검증 권한과 SHA 귀속 구현 goal — 2026-08-19

## 결론

지금 만드는 장치는 구현자가 자기 결과를 스스로 합격 처리하지 못하게 증거의 출처와 승인 권한을 나눕니다. 다만 이 변경 자체가 그 보호 장치를 함께 바꾸므로, 별도 사람 검토와 새 원격 실행 전에는 공식 합격으로 올리지 않습니다.

오너가 나중에 결정할 한 가지는 이 변경을 별도로 검토한 뒤 원격에 올려 새 자동 검사를 실행할지입니다. 올리기, 합치기, 배포, 원격 설정 변경은 하지 않습니다. 작업 보고 메일은 사용자의 최신 지시에 따라 최종 검증 뒤 sangmokang에게 보냅니다.

## 판단 근거

**무엇을** — 기존 PR #31·#32와 분리된 새 작업공간에서 검증 권한 정본, 실행 가능한 요구사항 계약, 고장 주입 시험, 대상 커밋 대조, 서버·업로드 직전 검사 연결을 한 묶음으로 만듭니다.

**왜** — 구현자와 같은 권한으로 쓴 문서나 로그만으로는 자기 승인을 막을 수 없습니다. 내부 장치는 변경을 찾아낼 수 있을 뿐이고, 최종 승인은 대상 커밋과 신뢰된 실행을 묶어 확인하는 바깥 정책에만 맡겨야 합니다.

**버린 길** — PR #31의 미병합 `principles.yaml`과 코드를 가져오는 길은 버렸습니다. 실패 중인 변경에 암묵적으로 기대면 원인과 책임이 다시 섞이기 때문입니다. 기존 원칙을 이번에 전부 계약으로 바꾸는 길도 범위가 지나치게 커 가짜 항목만 늘 위험 때문에 버렸습니다.

**대가** — 내부 검사들이 모두 성공해도 외부 보호 설정과 새 원격 실행이 없으면 공식 합격은 나오지 않습니다. 기존 원칙 중 새 계약에 들어오지 않은 항목은 `UNREGISTERED`로 집계합니다.

**되돌리기** — `task/verification-authority` 브랜치와 `worktrees/verification-authority` 작업공간을 폐기하면 됩니다. 기존 PR #31·#32와 루트 작업공간에는 변경을 남기지 않습니다.

## 작업 지시 원문

아래는 2026-08-19 사용자 지시를 이 문서에 보존한 것입니다. 이 문서의 요약보다 원문이 우선합니다.

<details>
<summary>원문 펼치기</summary>

> 엄격 작업 지시 — 검증 권한 분리와 SHA 귀속 판정 구현
>
> 목표: “LLM의 자기 판정은 증거가 아니다”라는 상위 원칙을 저장소의 정본 문서, 검사 계약, 고장 주입 시험, GitHub Actions 배선에 구현한다. 문자열 금지가 목적이 아니라 구현 주체가 자신의 구현과 검증 장치를 함께 바꾼 뒤 스스로 합격을 선언할 수 없도록 판정 권한과 증거의 신뢰 경계를 분리한다.
>
> PR #31/#32는 병합 불가 상태이며 해당 브랜치·worktree·커밋을 수정하거나 재사용하지 않는다. main 직접 작업, 다른 셀 변경의 reset·restore·checkout·삭제, push·merge·배포·PR·GitHub 설정·메일 변경, 전역 설정·전역 SKILL.md 변경, `pull_request_target`에서 PR 코드 실행, 내부 해시만으로 외부 보호 주장, 로컬 결과의 공식 PASS 표현, 과거 초록의 현재 증거 재사용을 금지한다.
>
> 착수 시 `git status --porcelain`, 현재 브랜치, root와 PR #31/#32 작업공간 HEAD, `git worktree list --porcelain`, `git branch -vv`, 원격 PR HEAD와 check SHA, 기존 미커밋 변경을 기록한다. `origin/main`을 읽기 전용 확인한 뒤 깨끗한 `task/verification-authority` 작업공간을 만들고, PR #31 미병합 코드가 필요하면 복사하지 말고 `DEPENDENCY_BLOCKED`로 기록한다.
>
> 수정 전에 AGENTS.md, 존재하는 모든 CLAUDE.md, `docs/sot/coding-principles.md`, `docs/sot/git-workflow.md`, `docs/sot/hook-contracts.md`, 존재하면 `docs/sot/principles.yaml`, `.github/workflows/verify.yml`, `hooks/pre-commit`, `hooks/pre-push`, `scripts/acceptance-*.sh`, `scripts/verify*.sh`, `docs/engineering/*principles*`, `docs/engineering/*verification*`, 관련 git 이력과 gitignore 대상 과거 판정을 읽는다.
>
> 새 상위 정본은 `docs/sot/verification-authority.md`를 권장하며 인덱스에 연결한다. LLM은 코드·테스트·문서·반례를 제안할 수 있지만 LLM이 쓴 PASS·COMPLETE·MERGEABLE에는 공식 권한이 없다. 공식 판정은 신뢰된 GitHub Actions workflow, 지정 필수 check, 대상 commit SHA, PR 또는 merge candidate 관계, 보호 영역 변경 여부, 별도 승인 증거를 모두 가진 외부 정책만 발급한다.
>
> 보호 대상은 검증 workflow, 필수 검사 목록, 상태 변환 규칙, mutation fixture·runner, SHA 대조 검사, branch ruleset·CODEOWNERS·merge 정책 선언, 보호 목록 자체다. 같은 저장소·권한 아래 manifest와 checker가 함께 바뀔 수 있음을 수정 차단이라 부르지 않는다. 실제 외부 강제를 확인하지 못하면 `ENFORCED`, `DETECT_ONLY`, `UNAVAILABLE`, `BLOCKED`를 정직하게 구분한다.
>
> 이번 작업은 보호 파일을 직접 바꾸므로 기능 시험이 성공해도 `POLICY_REVIEW_REQUIRED`만 사용할 수 있다. 요구사항 계약은 `id`, `invariant`, `counterexamples`, `verifier`, `stage`, `authority`, `coverage_status`를 가지며 YAML은 Ruby Psych 또는 저장소 표준 파서를 쓴다. verifier 경로만 보지 않고 실제 실행하며 빈 값, 중복·계약 밖 필드, 미실행 단계는 실패한다. 기존 요구사항을 한꺼번에 바꾸지 않고 미등록 항목을 `UNREGISTERED`로 집계한다.
>
> 구현자 상태는 `LOCAL_CANDIDATE`, `FAIL`, `VERIFIER_FAIL`, `STALE`, `POLICY_REVIEW_REQUIRED`, `BLOCKED`, `UNVERIFIED`이며 외부 정책만 `VERIFIED(repository, workflow identity, required check, target SHA, run identity)`를 부여한다. SHA 없는 단독 PASS를 만들지 않고 merge queue의 PR HEAD와 merge-group SHA 관계를 구분한다.
>
> AC1~AC10은 상위 정본, 실행 가능한 계약, 검증 시스템 자기 실패, CI 직접 실행, SHA 귀속·stale, 보호 영역의 정직한 보장, rollback·recovery·unlock·cleanup 고장 주입, 파생 상태 자동 생성, LLM 판정 비권위성, merge 권한 분리를 요구한다. 전체 기존 요구사항의 억지 변환은 범위 밖이고, 외부 보호가 없는데 병합 차단을 구현했다고 쓰지 않는다.
>
> 모든 파괴적 시험은 `mktemp` 격리 저장소에서만 실행하고 `GIT_DIR`, `GIT_WORK_TREE`, `GIT_INDEX_FILE`, `GIT_COMMON_DIR`, `GIT_OBJECT_DIRECTORY`, `GIT_ALTERNATE_OBJECT_DIRECTORIES`를 unset한다. 최소 mutation은 verifier 조기 `exit 0`, CI `echo bash`, CI 주석화, checker 삭제, registry 이름 변경, case 삭제, 예상 개수 동반 하향, 빈 counterexample, 실행 배선 제거, manifest+checker 동시 약화, 과거 SHA, PR HEAD 변경, check 이름 변경, workflow identity 변경, 성공값 위조 fixture, rollback 권한 복구 실패, rollback 실패 후 상태 삭제 시도, 정상 대조군 18종이다. 각 항목은 고장 내용, 실행 명령, 실제 종료값, 기대 실패 이유, 생존 여부, 원본 무변경을 남긴다.
>
> RED→GREEN은 실패 mutation을 먼저 작성하고 수정 전 생존 RED를 보존한 뒤 최소 구현으로 막고 같은 mutation과 정상 대조군을 재실행한다. mutation 삭제·기대값 완화로 GREEN을 만들지 않고 수치를 기록한다.
>
> 최소 검증은 변경 셸 `bash -n`, 저장소 표준 YAML 파서와 Ruby Psych 파싱, 정상 대조군, 전체 mutation, SHA fixture, failure injection, pre-commit, pre-push, 실제 verify, `git diff --check`, base 대비 diff 검사, 최종 status, root와 PR #31/#32 작업공간 시작 상태 동일 확인이다. 종료값뿐 아니라 실패 수, mutation 수, STALE·BLOCKED·UNREGISTERED를 확인한다.
>
> 구현 뒤 `env -u ANTHROPIC_API_KEY claude -p`로 1차 적대검증을 하며 verifier `exit 0`, CI `echo bash`, checker+manifest 동시 변경, case+expected 동시 감소, 과거 SHA 재사용, workflow/check 위조, merge queue 관계, rollback 상태 삭제, LLM 보고만으로 VERIFIED, 외부 강제 과장, CI·pre-push 배선, 정상 변경 오탐을 공격한다. strict SKILL.md §8-7 출력 형식 블록을 그대로 붙이고 원문·명령·종료값을 `## 적대 검증 로그`에 보존한다.
>
> Codex 2차는 Claude의 모든 file:line과 명령을 재현하고 FAIL 과장과 PASS 누락을 양방향 공격하며 미시도 mutation 2개 이상을 추가한다. 일치·불일치·누락 표를 남기고 갈리면 추가 재현 전 결론내지 않는다.
>
> push가 금지되어 공식 원격 검증은 반드시 `BLOCKED: 새 commit SHA가 원격에 없으므로 신뢰된 GitHub Actions 결과 없음`으로 기록한다. 오너가 나중에 비병합 검증 push를 별도 승인하기 전에는 push하지 않는다.
>
> 중단 조건은 조기 exit·echo CI·case 삭제 생존, SHA 불일치 유효화, 복구 실패 후 상태 삭제, 외부 보호 과장, 보호 영역 자기 승인, 필수 검사 실패·미실행·차단, 새 원격 실행 없음, 원본 예상 밖 변경, Claude/Codex 미해결 불일치다. 올바른 종료 상태는 외부 정책 승인과 새 GitHub Actions가 없으면 최대 `POLICY_REVIEW_REQUIRED` 또는 `BLOCKED`다. 다 작업하고 sangmokang으로 보고한다.

</details>

## 현재 상태 — 착수 증거

### 저장소와 작업공간

| 대상 | 시작 브랜치 | 시작 HEAD | 미커밋 변경 |
|---|---|---|---|
| 루트 `/Users/kangsangmo/Desktop/Valuehire_v6` | `main` | `7bd3298695c93e0e60bdabd2500840da47c4db05` | 없음 |
| PR #31 로컬 작업공간 `worktrees/strict-principles-yaml` | `task/strict-principles-yaml` | `26ad98c70ac1eb9ae997b29c0f597cbfb4620b95` | 없음 |
| PR #32 로컬 작업공간 `worktrees/codeaudit-wrap` | `task/codeaudit-wrap-2026-08-19` | `a3527a2836bf843a75fb494f00eefdff71385be7` | 없음 |
| 이번 작업 `worktrees/verification-authority` | `task/verification-authority` | `7bd3298695c93e0e60bdabd2500840da47c4db05` | 이 문서만 새로 작성 |

→ 루트와 두 기존 PR 작업공간은 깨끗했습니다. PR #31의 로컬 작업공간은 원격 PR HEAD보다 뒤에 있지만, 동기화하거나 수정하지 않습니다.

### 원격 기준과 과거 검사

| 대상 | 원격 HEAD | 과거 check SHA | 과거 결과 | 이번 작업 증거로 사용 |
|---|---|---|---|---|
| `origin/main` | `7bd3298695c93e0e60bdabd2500840da47c4db05` | 해당 없음 | 해당 없음 | 새 브랜치 기준으로만 사용 |
| PR #31 | `929247a27e4d36af28cdb5de8c95510689635068` | 동일 | `verify` 성공, workflow run 32172717612·32172711744 | 사용 안 함 |
| PR #32 | `a3527a2836bf843a75fb494f00eefdff71385be7` | 동일 | `verify` 성공, workflow run 32173067674·32173025324 | 사용 안 함 |

→ 과거 초록은 각 과거 SHA에만 귀속됩니다. 이번 로컬 변경은 아직 원격 SHA도 원격 실행도 없습니다.

### 외부 보호 읽기 전용 확인

```text
$ gh api repos/sangmokang/Valuehire_v6/branches/main/protection
gh: Upgrade to GitHub Pro or make this repository public to enable this feature. (HTTP 403)

$ gh api repos/sangmokang/Valuehire_v6/rulesets
gh: Upgrade to GitHub Pro or make this repository public to enable this feature. (HTTP 403)
```

→ 두 조회 모두 권한 문제가 아니라 현재 비공개 저장소 요금제에서 기능을 쓸 수 없다는 원격 응답입니다. 따라서 branch protection과 ruleset은 `UNAVAILABLE`이며 `ENFORCED`라고 쓰지 않습니다.

### 정본·과거 이력 조사

- 저장소 루트에 `AGENTS.md`와 `CLAUDE.md`는 존재하지 않았습니다. 이번 세션에 사용자 메시지로 제공된 AGENTS.md 계약과 `/Users/kangsangmo/.codex/skills/strict/SKILL.md` 전문을 적용합니다.
- `docs/sot/principles.yaml`은 `origin/main`에 없습니다. PR #31의 미병합 사본을 가져오지 않으며 기존 P1~P22는 이번 계약에서 `UNREGISTERED`로 집계합니다.
- 읽은 정본: `docs/sot/INDEX.md`, `coding-principles.md`, `git-workflow.md`, `hook-contracts.md`, `verification-commands.md`, `mechanism-registry.yaml`.
- 읽은 실행 경로: `.github/workflows/verify.yml`, `verify.sh`, `hooks/pre-commit`, `hooks/pre-push`, `scripts/acceptance-*.sh`, `scripts/verify/check-mechanism-registry.sh`.
- 읽은 기록: `docs/engineering/*principles*`, `docs/engineering/*verification*`, 관련 `git log --all -- <파일>` 및 `.claude/private-reviews`, `.omx/artifacts`의 관련 판정.
- 조사 중 ignored artifacts 전체를 대상으로 한 검색이 지나치게 넓어 대용량 브라우저 캡처까지 출력했습니다. 파일은 수정하지 않았고, 이후 검색은 판정 문서 경로와 필요한 낱말로 제한합니다.

## 근본 원인

1. `coding-principles.md`의 P17과 V-4는 만든 자가 증거를 쓸 수 없고 외부 모델 의견이 합격증이 아니라고 선언하지만, 현재 서버 검사는 같은 PR에서 workflow와 checker를 함께 바꿀 수 있습니다.
2. 기존 mechanism registry 검사는 경로와 target 문자열 중심이며, `run: echo bash ...`처럼 실행하지 않는 배선을 명령 구조로 판별하지 못합니다.
3. 현재 저장소에는 PR HEAD·merge-group SHA·check SHA·workflow identity·run identity를 한 튜플로 대조하는 판정기가 없습니다.
4. mutation harness가 존재하지만 이번 검증 권한 장치 자체의 case 삭제, 기대 수 하향, 조기 성공 종료를 독립 목록과 출력 계약으로 교차 확인하는 계약은 없습니다.
5. 외부 보호 조회가 403으로 거부되므로 내부 manifest는 변경 탐지만 할 수 있습니다. 이를 차단이라고 부르면 사실과 다릅니다.

## 설계 결정

1. 새 정본 `docs/sot/verification-authority.md`를 인덱스에 연결합니다.
2. `docs/sot/verification-requirements.yaml`은 이번 원칙과 장치만 완전 계약으로 등록하고 P1~P22는 `legacy_unregistered`에 둡니다.
3. Ruby Psych의 구문 트리를 사용해 중복 키를 먼저 찾고, 안전 파싱 뒤 계약 밖 필드·빈 값·잘못된 단계·실행되지 않는 명령을 거부합니다.
4. `.github/workflows/verify.yml`은 명령의 단순 포함이 아니라 YAML의 실제 `run` 단계에서 첫 실행 명령이 검사 스크립트인지 확인합니다.
5. SHA 판정기는 성공 fixture를 공식 합격으로 올리지 않고 `LOCAL_CANDIDATE` 또는 보호 파일 변경 시 `POLICY_REVIEW_REQUIRED`까지만 생성합니다. 공식 `VERIFIED(...)` 발급 구현은 저장소 밖 정책의 책임으로 남깁니다.
6. 보호 목록과 내부 checker는 `DETECT_ONLY`입니다. 둘을 함께 약화하는 지정 mutation은 별도 독립 필수 목록이 잡지만, 같은 권한이 저장소의 모든 독립 목록까지 함께 바꿀 수 있다는 구조적 한계는 남습니다.
7. CI 결과는 대상 SHA를 포함한 파생 JSON을 만들고 artifact로 올리도록 배선합니다. 이 workflow 자체가 이번 변경에 포함되므로 외부 승인 전 권위는 없습니다.

## 버린 대안

- 기존 모든 원칙을 이번 PR에서 한꺼번에 변환: 범위가 지나치게 커지고 가짜 계약을 수량만 채울 위험이 큽니다.
- PR #31의 `principles.yaml` 재사용: 미병합 브랜치 의존성과 책임 혼합 때문에 버렸습니다.
- PASS·COMPLETE 같은 낱말 금지: 권한과 SHA 귀속 문제를 해결하지 못해 버렸습니다.
- 저장소 내부 checksum만으로 보호 선언: 동일 권한이 재계산할 수 있어 `ENFORCED`가 아니므로 버렸습니다.
- `pull_request_target`에서 PR 코드 실행: 신뢰된 토큰과 비신뢰 코드를 섞으므로 금지합니다.

## Acceptance Criteria

- AC1~AC10은 사용자 원문을 그대로 적용합니다.
- 기계 판정의 추가 불변식: 모든 필수 verifier 명령은 실제로 실행되고 출력 계약까지 만족해야 합니다.
- 차단 대조군: 사용자 지정 17종과 Codex·Claude 재공격에서 추가한 5종, 합계 22종을 모두 잡아야 합니다.
- 통과 대조군: 정상 사본 1종과 정상 SHA·recovery fixture가 통과해야 합니다.
- 내부 검사 성공 뒤 상태는 `POLICY_REVIEW_REQUIRED`; 원격 새 실행은 push 금지 때문에 `BLOCKED`입니다.

## Harness 게이트 진행

- 게이트 0: `make -n red-ledger`는 종료값 2와 `No rule to make target`을 냈습니다. 정본에 따라 `bash scripts/session-status.sh`를 사용합니다.
- 게이트 1: 이 문서와 AC1~AC10이 작업 계약입니다.
- 게이트 2: `task/verification-authority` / `worktrees/verification-authority`를 `origin/main`에서 생성했습니다.
- 게이트 3: 먼저 mutation harness와 RED 생존 증거를 만들고 최소 구현으로 막습니다.
- 게이트 4: 정본의 실제 verify 명령과 사용자 필수 검증을 모두 실행합니다.
- 게이트 5: push·PR 생성이 명시적으로 금지되어 `BLOCKED`입니다.
- 게이트 6: 오너 승인 전 작업공간을 삭제하지 않습니다.

## 게이트 설계 3원칙

- [x] 자기 선언을 누가 확인하는지 각 상태 전환에 명시한다.
- [x] 장치가 있으면 통과하는 킬 스위치가 아니라, 장치가 약화되면 고장 주입이 실패하는지 확인한다.
- [x] 막아야 할 22종과 통과해야 할 정상 대조군 1종을 한 쌍으로 기록한다.

## RED → GREEN 기록

### RED — 약한 첫 판에서 두 mutation 생존

```text
$ bash scripts/acceptance-verification-authority-mutations.sh
SURVIVED: ci_echo — CI command changed to echo only (exit=0)
SURVIVED: empty_counterexample — counterexample list emptied (exit=0)
MUTATIONS: total=2 blocked=0 survived=2 controls=0
RED_EXIT=1
```

→ 실행 경로를 `echo`로 바꿔 실제 검사를 하지 않은 경우와 반례 목록을 비운 경우가 모두 종료값 0으로 살아남았습니다. mutation runner는 생존 2건 때문에 RED 종료값 1을 냈습니다.

RED 당시 원본 작업공간 상태는 새 파일 5개만 미추적이었고, mutation은 `mktemp` 복사본 안에서만 실행됐습니다. 이 증거를 남긴 뒤 약한 첫 판은 최종 구현으로 교체합니다.

## 검증 명령·출력

최종 명령 전문과 전체 출력은 같은 저장소의 `docs/engineering/verification-authority-validation-log-2026-08-19.md`에 보존합니다. 이 goal 문서는 결과를 판단하는 색인이고, 로그 파일은 잘라내지 않은 3층 증거입니다.

현재 재현 수치는 다음과 같습니다.

```text
CONTRACT: requirements=8 executed=8 unregistered=22
MUTATIONS: total=23 blocked=22 survived=0 controls=1
SHA_FIXTURES: total=11 states=FAIL,LOCAL_CANDIDATE,POLICY_REVIEW_REQUIRED,STALE,UNVERIFIED
RECOVERY_FIXTURES: total=8
STRUCTURAL_LIMIT: three_way_survived=true enforcement=DETECT_ONLY original_unchanged=true
AUTHORITY_RESULT: POLICY_REVIEW_REQUIRED
MUTATION_SURVIVED: 0
```

→ 8개 신규 계약의 명령이 실제로 실행됐고, 파괴 사례 22건은 모두 잡혔으며 정상 대조군 1건은 유지됐습니다. 세 목록을 함께 바꾸는 공격은 예상대로 살아남았고, 이를 보호 성공이 아니라 내부 탐지만 가능한 구조적 한계로 분류했습니다. 기존 P1~P22는 전환하지 않아 22건 모두 미등록으로 남습니다.

중간 실패도 숨기지 않습니다.

- Psych의 `safe_load_file`이 이 Ruby 버전에 없어 종료값 1: `Psych.safe_load(File.read(...))`로 같은 파서를 호출해 재실행했습니다.
- 존재하지 않는 `contract-check` 모드를 잘못 호출해 종료값 1: 실제 모드 `contract-execute`로 바로잡아 재실행했습니다.
- 첫 전체 mutation은 격리 사본에 `.git`이 없어 7건이 생존: 사본 안에서 `git init`과 baseline commit을 만든 뒤 재실행했습니다.
- workflow artifact 단계에 `if: always()`를 넣은 첫 판은 pre-commit이 약화 패턴으로 차단: 조건을 제거했습니다.
- Claude 원문 파일의 마지막 빈 줄 때문에 `git diff --check`가 종료값 2: 원문 내용은 유지하고 끝의 빈 줄만 제거한 뒤 재실행했습니다.

## 적대 검증 로그

실행 프롬프트 전문은 `docs/engineering/verification-authority-claude-prompt-2026-08-19.md`에 보존했습니다. Claude 판정 원문·실행 명령·종료값은 다음 두 파일에 한 글자도 요약하지 않고 보존했습니다.

- `docs/engineering/verification-authority-claude-review-1-2026-08-19.md`
- `docs/engineering/verification-authority-claude-review-2-2026-08-19.md`

첫 일반 실행은 확장 서버 초기화에서 10분 이상 본문 없이 멈춰 중단했고, 출력 없음·종료값 0이라 검증으로 세지 않았습니다. `--bare` 재시도는 로그인 정보가 없어 종료값 1이었습니다. 이후 사용자 지정 `env -u ANTHROPIC_API_KEY claude -p`를 유지하고 빈 MCP 설정만 지정한 두 유효 회차는 각각 종료값 0과 본문 `VERDICT: FAIL`을 남겼습니다.

### Codex 2차 재공격 비교

| Claude 주장 | Codex 재현 | 수정 후 결과 | 일치 |
|---|---|---|---|
| core 두 번째 줄 `exit 0`이 실제 acceptance·pre-push에서 살아남음 | 같은 격리 공격에서 종료값 0 재현 | 바깥 acceptance가 필수 표식을 확인해 종료값 1 | 일치, 수정됨 |
| `--no-mutations --output`이 가짜 실측 수치를 생성 | 결과 파일에 18/17/0/1 하드코딩 재현 | 증거 출력 조합 자체를 종료값 1로 거부 | 일치, 수정됨 |
| 암묵적 `VERIFIED` 반환이 자기검사를 우회 | `return` 없는 조건 반환으로 재현 | 정식 mutation `authority_implicit_verified_backdoor`가 종료값 1 | 일치, 수정됨 |
| mutation runner가 요약만 출력하고 조기 성공 | 전체 acceptance 종료값 0 재현 | 상위 실행기가 23개 case별 결과·격리 증거를 대조해 종료값 1 | 일치, 수정됨 |
| 출력 경로 고정 + SHA 주석이 배선 검사를 우회 | `wiring-check` 종료값 0 재현 | 정확한 4개 명령 인자를 비교해 종료값 1 | 일치, 수정됨 |
| manifest·checker·contract 세 목록 동시 약화는 생존 | `paths=11`, 종료값 0 재현 | 계속 생존하며 `STRUCTURAL_LIMIT ... DETECT_ONLY`로 자동 기록 | 일치, 공개 한계 |
| 과거 SHA, 이름 위조, merge-group 오귀속, rollback 상태 삭제는 차단 | 지정 fixture와 명령을 모두 재실행 | 기대 상태와 동일 | 일치 |
| 외부 강제를 `ENFORCED`로 과장하지 않음 | GitHub API 403·CODEOWNERS 부재 재확인 | `UNAVAILABLE`/`DETECT_ONLY` 유지 | 일치 |

→ Claude의 결함 5건은 모두 Codex가 독립 재현했고 과장으로 뒤집힌 항목은 0건입니다. 공개된 3중 약화 한계는 고치지 않고 자동 재현하도록 바꿨습니다. Codex가 Claude 1차 전에 추가한 `ci_dead_code_before_command`, `artifact_sha_unbound` 2건과 Claude 재공격 3건을 합쳐 전체 mutation은 18건에서 23건으로 늘었습니다.

## SOT 체크리스트

- [x] `docs/sot/INDEX.md` 읽음
- [x] `docs/sot/coding-principles.md` 읽음
- [x] `docs/sot/git-workflow.md` 읽음
- [x] `docs/sot/hook-contracts.md` 읽음
- [x] `docs/sot/verification-commands.md` 읽음
- [x] `docs/sot/mechanism-registry.yaml` 읽음
- [x] `docs/sot/principles.yaml` 부재 확인, PR #31에서 가져오지 않음
- [x] 새 정본을 인덱스와 실제 실행 경로에 연결
- [x] 로컬 성공을 공식 합격으로 표현하지 않음
- [x] 외부 보호 부재를 `UNAVAILABLE`, 내부 변경 탐지를 `DETECT_ONLY`로 기록

## 비범위

- 기존 P1~P22 전부의 계약 변환
- GitHub branch protection·ruleset·required check·CODEOWNERS 설정 변경
- push, PR 생성·수정, merge, 배포. 메일은 사용자의 최신 추가 지시에 따라 최종 보고만 수행
- PR #31·#32 코드·브랜치·worktree·커밋 수정 또는 재사용
- 저장소 밖 검증 서비스와 서명 인프라 구축
