# 결론

검사 명령의 글자만 남겨 두고 실제 실행을 없애는 설정을 모두 거부하도록 고칩니다. 기존 실행 처리기 세 위치에 더해, 실행 시작 폴더 세 위치와 실행 전 개입 환경값 세 위치를 차단하고 실행할 기계의 값도 실제 이름을 담은 형태인지 확인합니다. 실패를 먼저 재현하고 최소 수정 뒤 전체 과거 시험을 다시 통과시킬 때까지만 완료로 보겠습니다.

# 판단 근거

현재 검사는 실행할 명령, 일부 건너뛰기 설정, 실행 처리기 세 위치, 실행 기계 키의 존재를 확인합니다. 그러나 같은 이름의 가짜 검사 폴더로 시작 위치를 바꾸는 설정, 검사 본문보다 먼저 셸을 끝내는 환경값, 실행 기계 키의 실제 값은 확인하지 않으므로 아무 검사도 하지 않거나 시작조차 할 수 없는 설정을 정상으로 인정할 수 있습니다.

갈림길은 실행 시작 폴더를 저장소 루트 값만 허용할지, 해당 키의 존재 자체를 거부할지입니다. 경로 표기와 식을 모두 안전하게 증명하는 허용 규칙은 복잡하고 새 우회를 만들 수 있으므로 버리고, G3 단계·작업 기본값·파일 기본값 중 한 곳에라도 키가 있으면 값과 관계없이 거부합니다. 환경값은 모든 값을 금지하면 정상 사용을 깨뜨리므로 셸 시작과 명령 탐색을 바꾸는 `BASH_ENV`·`ENV`·`SHELLOPTS`·`PATH` 네 키만 세 소유 위치에서 거부합니다. 실행 기계 값은 비어 있지 않은 문자열 또는 그런 문자열만 담은 비어 있지 않은 목록만 허용합니다.

이 판단이 틀리면 서버 설정 화면에는 여덟 검사 명령이 그대로 보이지만 실제로는 한 줄도 실행되지 않거나, 실행할 수 없는 작업을 정상 표본으로 검증하게 됩니다.

## 설계 결정 카드

- **무엇을** — 기존 `shell` 차단에 더해 G3 단계·작업·파일의 실행 시작 폴더 키는 값과 무관하게 거부하고, 세 위치의 환경값 중 `BASH_ENV`·`ENV`·`SHELLOPTS`·`PATH`를 거부하며, 실행 기계 값은 비어 있지 않은 문자열 또는 그런 문자열의 비어 있지 않은 목록만 허용합니다.
- **왜** — 시작 폴더와 네 환경값은 명령 글자를 보존한 채 다른 검사 파일을 실행하거나 진짜 검사 본문 전에 성공으로 끝낼 수 있고, 빈 실행 기계 값은 작업 대상을 지정하지 못하기 때문입니다.
- **버린 길** — 저장소 루트처럼 보이는 시작 폴더만 허용하는 방식과 모든 환경값을 금지하는 방식은 각각 경로 우회가 남고 무해한 설정까지 깨뜨리므로 버렸습니다.
- **대가** — 안전한 목적의 실행 시작 폴더도 G3 실행 경로에서는 쓸 수 없으며, `PATH`를 정상적으로 보강해야 하는 경우에도 별도 계약 변경이 필요합니다.
- **되돌리기** — 허용이 필요해지면 먼저 안전·위험 표본을 추가하고 검증 가능한 정확한 값 목록을 계약으로 승인한 뒤 존재 기반 차단을 좁혀야 합니다.

# 기술 상세·증거

## 현재 상태

- `scripts/acceptance-hs-portal-constants.sh:221-242` — G3 명령이 든 작업과 단계를 고르는 본체입니다. 세 `shell` 위치와 `runs-on` 키 존재는 읽지만 실행 시작 폴더, 세 소유 위치의 환경값, `runs-on` 값의 종류·내용은 읽지 않습니다.
- `scripts/acceptance-hs-portal-constants-hardening6.sh:64-121` — 정상·공격 워크플로 표본을 만드는 함수입니다. G6 갱신 전에는 G6-1~G6-3 표본이 없었습니다.
- `.github/workflows/verify.yml:14-60` — 실제 G3 실행 경로입니다. G3 작업에는 `runs-on: ubuntu-latest`가 있고, G3 단계와 작업·파일 기본값에는 `shell` 설정이 없습니다.
- `.claude/private-reviews/codex-g3-verdict6-2026-08-15.md:40-76` — 실행 시작 폴더 세 위치, `BASH_ENV` 세 위치, `runs-on`의 null·빈 목록·거짓값이 각각 현행 본체 종료값 0으로 재현된 최신 판정입니다.

→ 무엇을 확인했나: 본체 판정부, 시험 표본 생성부, 실제 서버 설정, 최신 판정의 네 재현을 서로 대조했습니다. 실제 파일은 새 규칙의 정상 형태이고 시험 생성부와 본체만 보강이 필요합니다.

## 근본 원인

YAML(= 들여쓰기로 서버 자동 실행 구조를 적는 설정 형식)을 구조적으로 읽은 뒤에도 `run` 문자열과 일부 키 존재 중심으로만 정상 여부를 정합니다. 같은 명령의 실제 시작 위치와 시작 전 환경, 실행 기계 값의 유효성이 정상 조건에 포함되지 않은 것이 G6-1~G6-3의 공통 원인입니다.

## 인수 기준

1. 단계 `shell` 키가 있는 G3 표본은 본체가 정확히 종료값 1을 냅니다.
2. G3 작업의 `defaults.run.shell`이 있는 표본은 본체가 정확히 종료값 1을 냅니다.
3. 파일 전체의 `defaults.run.shell`이 있는 표본은 본체가 정확히 종료값 1을 냅니다.
4. G3 작업에 `runs-on`이 없는 표본은 본체가 정확히 종료값 1을 냅니다.
5. `hardening6` 정상 표본은 `runs-on: ubuntu-latest`를 가지며 본체 종료값 0입니다.
6. 실제 `.github/workflows/verify.yml`은 새 규칙에서 본체 종료값 0입니다.
7. 본체·mutations·hardening 1~6과 추적 셸 파일 전체 문법 검사가 모두 종료값 0입니다.
8. `shell` 방어 한 줄을 임시 무력화하면 `hardening6`이 종료값 1이고, 원복 뒤 다시 0입니다.
9. G3 단계의 `working-directory`, G3 작업의 `defaults.run.working-directory`, 파일 전체의 `defaults.run.working-directory` 중 하나라도 키가 있으면 값과 무관하게 본체가 정확히 종료값 1을 냅니다.
10. G3 단계·그 작업·파일 전체의 `env` 중 한 곳이라도 `BASH_ENV`·`ENV`·`SHELLOPTS`·`PATH` 키를 가지면 값과 무관하게 본체가 정확히 종료값 1을 냅니다.
11. `BASH_ENV`는 단계·작업·파일 세 소유 위치를 각각 독립 표본으로 고정하고, `ENV`·`SHELLOPTS`·`PATH`도 최소 한 소유 위치씩 독립 표본으로 고정합니다.
12. 세 소유 위치의 다른 무해한 환경값은 허용하며 본체가 종료값 0을 냅니다.
13. G3 작업의 `runs-on`은 공백이 아닌 문자열 또는 공백이 아닌 문자열만 담은 비어 있지 않은 목록일 때만 허용합니다.
14. `runs-on`의 null·빈 목록·불리언 거짓값 표본은 각각 본체가 정확히 종료값 1을 냅니다.
15. 실제 `.github/workflows/verify.yml`에 G3 실행 경로의 금지 환경값·실행 시작 폴더가 없고 `runs-on: ubuntu-latest`가 있으며, 본체 종료값 0을 유지합니다.
16. `working-directory` 방어 한 줄을 임시 무력화하면 `hardening6`이 종료값 1이고, 원복 뒤 다시 0입니다.

여기서 종료값(= 프로그램이 끝나며 남기는 성적)은 이 본체에서 0이 합격, 1이 규칙 위반, 2가 검사를 수행할 수 없음입니다.

## Harness 게이트 진행

- 게이트 0: `Makefile`과 `package.json`이 없고 `make -n red-ledger`는 2였습니다. 이 저장소 정본에 따라 `bash scripts/session-status.sh`를 실행해 시작 HEAD `201baa5`와 원격 기준을 확인했습니다.
- 게이트 1: 위 인수 기준 열여섯 개로 작업 계약을 고정했습니다.
- 게이트 2: 사용자가 지정한 격리 워크트리와 `task/humansearch-g3-portal-constants` 브랜치를 사용합니다.
- 게이트 3: `hardening6`에 네 실패 표본을 먼저 추가해 기존 본체의 잘못된 0을 기록한 뒤 본체를 수정합니다.
- 게이트 4: 사용자 지정 전량 회귀와 `bash verify.sh`를 실행하고 종료값 원문을 보고서에 보존합니다.
- 게이트 5: 로컬 커밋까지만 허용합니다. `git push`, 합치기, 배포는 하지 않습니다.
- 게이트 6: 이 작업에서는 워크트리를 제거하지 않습니다.
- G6 갱신: `hardening6`에 실행 시작 폴더 3개, `BASH_ENV` 소유 위치 3개, `ENV`·`SHELLOPTS`·`PATH` 각 1개, 실행 기계 무효값 3개, 무해한 환경값 1개를 먼저 추가합니다. 현행 본체가 위험 표본을 잘못 0으로 승인하는 RED를 각 표본에서 관측한 뒤에만 본체를 수정합니다.

## 적대 검증 항목

- 세 `shell` 설정 중 하나를 놓치거나 G3 명령이 없는 다른 작업의 설정 때문에 오탐하지 않는지 확인합니다.
- `runs-on`이 다른 작업에만 있고 G3 작업에는 없는 경우를 정상으로 오인하지 않는지 확인합니다.
- 새 방어 한 줄을 무력화했을 때 새 시험이 실제로 실패하는지 확인합니다.
- 실행 시작 폴더가 단계·작업·파일 어느 위치에 있어도 안전한 중복 단계나 작업으로 숨길 수 없는지 확인합니다.
- 금지 환경값 키 비교가 대소문자 계약을 정확히 따르며, 다른 무해한 키까지 과잉 차단하지 않는지 확인합니다.
- `runs-on` 문자열의 공백값과 목록 원소의 빈 문자열까지 잘못 허용하지 않는지 확인합니다.
- Claude에게 변경 파일과 전체 회귀 증거를 읽기 전용으로 공격하게 하고, 그 판정의 모든 근거를 Codex가 다시 실행해 양방향으로 검토합니다.

## SOT 체크리스트

- `docs/sot/INDEX.md` — 사건 기록은 날짜를 붙여 `docs/engineering/`에 남긴다는 경계를 읽었습니다.
- `docs/sot/coding-principles.md` — P5의 실패 시험 선행, P13의 검사 약화 금지, P15의 서버·로컬 이중 배선, P16의 실행 동작 검증, P20의 0건 통과 금지, P22의 포털 상수 경계를 읽었습니다.
- `docs/sot/verification-commands.md` — 이 저장소가 make/npm 기반이 아니며 실제 검증 진입점은 `bash verify.sh`, G3 전량 명령, 셸 문법 검사임을 읽었습니다.
- `docs/sot/git-workflow.md` — 격리 워크트리·작업 브랜치와 로컬 커밋 경계를 확인했습니다.

## 비범위

- 포털 상수·화면 위치 탐지 정규식 자체는 바꾸지 않습니다.
- 자동 실행 사건을 `push`와 `pull_request` 모두로 강화하는 별도 설계는 다루지 않습니다.
- 새 의존성, 무관한 정리, 원격 전송, 합치기, 배포는 하지 않습니다.

## 적대 검증 로그

### 다른 엔진 1차 검증

실행 명령 전문:

```bash
env -u ANTHROPIC_API_KEY TMPDIR="$PWD/.g3-fix3-tmp" omx ask claude "Read the current git diff in /Users/kangsangmo/Desktop/Valuehire_v6/worktrees/humansearch-g3-portal-constants and adversarially verify that any shell key on a G3 step, its job defaults.run.shell, or workflow defaults.run.shell is rejected regardless of value; that a G3 job missing runs-on is rejected; that duplicate safe steps or jobs cannot hide an unsafe one in either order; and that the actual verify.yml still passes. Read-only only. Return VERDICT PASS or FAIL with file:line evidence and commands run."
```

→ 무엇을 시켰나: 현재 변경 전체를 다른 엔진이 읽고 실행 방식 세 위치, 실행 기계 누락, 중복 순서 우회, 실제 파일을 적대적으로 검토하도록 요청했습니다.

실행 출력 전문:

```text
/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/humansearch-g3-portal-constants/.omx/artifacts/claude-read-the-current-git-diff-in-users-kangsangmo-desktop-valueh-2026-08-14T22-52-12-753Z.md
OMX_ASK_CLAUDE_RECOVERY_RC=1
```

→ 무엇이 나왔나: Claude CLI가 로그인되지 않아 판정은 생성되지 않았습니다. 원문 산출물에는 `Not logged in · Please run /login`과 종료값 1이 보존됐으므로, 다른 엔진 검증은 건너뛴 것으로 처리합니다.

### Codex 재공격

Claude 판정이 없으므로 그 판정을 재현하는 2차 검증은 수행할 수 없었습니다. 대신 구현자가 계약의 “하나라도”와 순서 독립성을 직접 공격해 최초 GREEN에서 여섯 추가 우회를 찾았습니다.

| 공격 | 최초 GREEN 본체 | 보강 뒤 본체 | 최종 hardening6 |
|---|---:|---:|---:|
| 나쁜 step 뒤 안전한 step 복제 | 0 | 1 | 0 |
| 나쁜 job defaults 뒤 안전한 job 복제 | 0 | 1 | 0 |
| runs-on 없는 job 뒤 안전한 job 복제 | 0 | 1 | 0 |
| 안전한 step 뒤 나쁜 step | 0 | 1 | 0 |
| 안전한 job 뒤 나쁜 job defaults | 0 | 1 | 0 |
| 안전한 job 뒤 runs-on 없는 job | 0 | 1 | 0 |

→ 무엇을 확인했나: 나쁜 위치가 앞·뒤 어느 쪽에 있어도 최초 GREEN은 안전한 복제만 골라 0을 냈고, 전체 위치를 끝까지 읽도록 바꾼 뒤 각 본체는 1, 18건을 묶은 hardening6은 0이었습니다. 최초 구현을 그대로 제출하지 않게 막은 좋은 소식이지만, 다른 엔진 교차검증이 없다는 한계는 남습니다.

### G6-1~G6-3 fix4 RED·GREEN 기록

RED 명령과 핵심 출력:

```text
bash scripts/acceptance-hs-portal-constants-hardening6.sh step_working_directory
FAIL: hardening6 [N6 step-level working-directory key] exit=0 (기대: 정확히 1)
RED_SUITE_EXIT[step_working_directory]=1
bash scripts/acceptance-hs-portal-constants-hardening6.sh job_default_working_directory
FAIL: hardening6 [N6 job defaults.run.working-directory key] exit=0 (기대: 정확히 1)
RED_SUITE_EXIT[job_default_working_directory]=1
bash scripts/acceptance-hs-portal-constants-hardening6.sh workflow_default_working_directory
FAIL: hardening6 [N6 workflow defaults.run.working-directory key] exit=0 (기대: 정확히 1)
RED_SUITE_EXIT[workflow_default_working_directory]=1
bash scripts/acceptance-hs-portal-constants-hardening6.sh step_bash_env
FAIL: hardening6 [N7 step env BASH_ENV key] exit=0 (기대: 정확히 1)
RED_SUITE_EXIT[step_bash_env]=1
bash scripts/acceptance-hs-portal-constants-hardening6.sh job_bash_env
FAIL: hardening6 [N7 job env BASH_ENV key] exit=0 (기대: 정확히 1)
RED_SUITE_EXIT[job_bash_env]=1
bash scripts/acceptance-hs-portal-constants-hardening6.sh workflow_bash_env
FAIL: hardening6 [N7 workflow env BASH_ENV key] exit=0 (기대: 정확히 1)
RED_SUITE_EXIT[workflow_bash_env]=1
bash scripts/acceptance-hs-portal-constants-hardening6.sh runs_on_null
FAIL: hardening6 [N8 runs-on null] exit=0 (기대: 정확히 1)
RED_SUITE_EXIT[runs_on_null]=1
bash scripts/acceptance-hs-portal-constants-hardening6.sh runs_on_empty_list
FAIL: hardening6 [N8 runs-on empty list] exit=0 (기대: 정확히 1)
RED_SUITE_EXIT[runs_on_empty_list]=1
bash scripts/acceptance-hs-portal-constants-hardening6.sh runs_on_false
FAIL: hardening6 [N8 runs-on false] exit=0 (기대: 정확히 1)
RED_SUITE_EXIT[runs_on_false]=1
```

→ 새 아홉 시험은 각각 1로 실패했고, 실패 문장은 현행 본체가 위험 표본을 잘못 0으로 승인했음을 그대로 보존합니다. 본체 수정 전에 관측한 RED입니다.

추가 환경값과 정상 환경값 RED 출력:

```text
FAIL: hardening6 [N7 step env ENV key] exit=0 (기대: 정확히 1)
RED_SUITE_EXIT[step_env]=1
FAIL: hardening6 [N7 job env SHELLOPTS key] exit=0 (기대: 정확히 1)
RED_SUITE_EXIT[job_shellopts_env]=1
FAIL: hardening6 [N7 workflow env PATH key] exit=0 (기대: 정확히 1)
RED_SUITE_EXIT[workflow_path_env]=1
ok [harmless env keys remain allowed] exit=0
RED_SUITE_EXIT[safe_env]=0
```

→ 네 금지 키 전부가 최소 한 소유 위치에 고정됐고 `BASH_ENV`는 세 위치 모두 고정됐습니다. 무해한 환경값은 원래도 0이었고 보강 뒤에도 유지해야 하는 정상 기준입니다.

GREEN 전체 출력의 최종 판정:

```text
PASS: portal-constants hardening6 cases 31 (blocked-mutations 28, clean-baselines 2, wiring-present 1)
GREEN_HARDENING6_FILTERED_EXIT=0
REGRESSION_BUNDLE_EXIT=0
BASH_N_FILE_COUNT=34
BASH_N_ALL_EXIT=0
VERIFY_SH_EXIT=0
CURRENT_VERIFY_YML_SHAPE_EXIT=0
```

→ 새 표본과 과거 표본 31개, G3 회귀 전량, 추적 셸 34개 문법, 비밀정보 검사, 현행 서버 설정 구조가 모두 0입니다.

방어 무력화 시험:

```text
FAIL: hardening6 [N6 step-level working-directory key] exit=0 (기대: 정확히 1)
MUTATION_WORKING_DIRECTORY_DISABLED_H6_EXIT=1
PASS: portal-constants hardening6 cases 31 (blocked-mutations 28, clean-baselines 2, wiring-present 1)
MUTATION_RESTORED_RETRY_HARDENING6_EXIT=0
```

→ 단계 시작 폴더 방어 한 줄을 잠시 끄자 시험이 1로 실패했고, 원복 뒤 다시 0이었습니다. 첫 원복 실행은 모든 기능 표본 통과 뒤 원본 상태가 실행 중 달라졌다는 자체 점검으로 1이어서 근거에서 제외하고 같은 명령을 다시 실행했습니다.

### G6 fix4 다른 엔진 1차 검증

실행 명령 전문:

```bash
env -u ANTHROPIC_API_KEY TMPDIR="$PWD/.g3-fix4-claude-tmp" claude -p '현재 저장소의 git diff와 다음 파일을 읽기 전용으로 적대 검증해 주세요: scripts/acceptance-hs-portal-constants.sh, scripts/acceptance-hs-portal-constants-hardening6.sh, docs/engineering/humansearch-g3-portal-shell-runs-on-goal-2026-08-15.md, .github/workflows/verify.yml. 목표는 G3 명령이 있는 단계·그 작업의 defaults.run·워크플로 최상위 defaults.run 중 working-directory 키가 하나라도 있으면 값과 무관하게 거부하는지, 같은 단계·작업·워크플로 env에서 BASH_ENV·ENV·SHELLOPTS·PATH 키를 거부하면서 다른 env 키는 허용하는지, G3 작업의 runs-on이 비어 있지 않은 문자열 또는 비어 있지 않은 문자열 목록일 때만 허용하는지 확인하는 것입니다. null·빈 목록·false를 포함한 hardening6 표본이 실제 구현을 검사하는지, 안전한 중복 단계나 작업이 위험 설정을 숨길 수 있는지, 현재 verify.yml이 계속 통과하는지도 직접 명령으로 확인하세요. 변경하거나 커밋하지 마세요. 가짜 완료, 고아, 과장, 빠진 소유 위치, 타입 우회를 정조준하세요.

[출력 형식 — 반드시 지킬 것]
읽는 사람은 기술 배경이 없는 사업 책임자다. 판정 내용은 절대 축소하지 말고, 표현만 풀어 써라.
1) 문서 맨 앞에 결론. 결정할 사항 1개당 1~2문장, 전체 분량 상한 없음. 전문용어는 풀어 쓰더라도 결론에서는 쓰지 마라.
2) 그다음 판단 근거: 왜 그렇게 봤는지, 갈림길에서 왜 이 해석을 골랐는지, 버린 해석은 왜 버렸는지, 이 판정이 틀리면 무엇이 깨지는지.
3) 그다음부터 기술 상세·명령·출력·file:line 전문. 증거는 하나도 생략하지 마라.
- 전문용어는 첫 등장 문장 안에서 괄호로 풀어 써라. 뒤에 몰아 쓴 용어집은 무효다.
- 터미널 출력·코드 블록·표를 붙였으면 바로 아래에 → 뭘 시켰나 / 뭐가 나왔나 / 좋은 소식인가 나쁜 소식인가 1~3줄을 달아라.
- 첫 줄에 VERDICT: PASS|FAIL 한 줄을 두어라. 그 한 줄은 결론의 일부가 아니라 기계가 읽는 표식이므로 결론 제목 앞에 온다.
- file:line 을 인용하면 그 줄이 무슨 일을 하는 줄인지 한 마디 덧붙여라.
- 결함마다 심각도 라벨을 붙이고, 그 옆에 그대로 두면 사업/운영에 무슨 일이 생기는지 한 문장으로 덧붙여라.
- 설계 결정을 지적할 때는 무엇을 / 왜 / 버린 대안 / 대가 / 되돌리는 법 5줄로 적어라.
- 이번에 건너뛴 것·확인하지 못한 것·중간에 실패해서 다시 한 것을 판정 앞부분에 명시해라.
- 추정과 확인된 사실을 구분 표시해라. 확인 못 한 것은 ※.
- 한국어 존칭체. 초등학생용 비유는 쓰지 마라 — 성인 의사결정자 수준으로 써라.'
```

→ 실행한 명령과 프롬프트 전문입니다. 네 대상 파일, 세 계약, 중복 우회, 현행 `verify.yml`, 사업 책임자용 출력 형식을 모두 전달했습니다.

실행 출력 전문:

```text
Not logged in · Please run /login
SessionEnd hook [node "${CLAUDE_PLUGIN_ROOT}/scripts/session-lifecycle-hook.mjs" SessionEnd] failed: EPERM: operation not permitted, unlink '/Users/kangsangmo/.claude/plugins/data/codex-openai-codex/state/humansearch-g3-portal-constants-39cbd6bf44ef0c67/broker.json'

CLAUDE_ADVERSARIAL_EXIT=1
CLAUDE_TEMP_CLEANUP_EXIT=0
```

→ Claude CLI가 로그인되지 않아 판정 본문을 만들지 못했습니다. 따라서 다른 엔진 1차 검증은 미실행으로 처리하며, 임시 폴더는 0으로 정리했습니다.

### G6 fix4 Codex 재공격

별도 검증 역할의 최초 판정은 `PARTIAL`이었으나, 재질문 결과 두 지적은 사용자 명시 최소 표본 미충족이 아니라 추가 권고라고 정정했습니다. 사용자 명시 표본인 `BASH_ENV` 세 소유 위치, `ENV` 추가 표본, `runs-on` null·빈 목록·거짓값은 모두 존재하고 0 회귀를 확인했습니다. `ENV`·`SHELLOPTS`·`PATH`의 모든 소유 위치 조합과 새 규칙별 안전 중복 조합은 이번 명시 범위를 넓히는 후속 권고입니다.

검증 역할이 사용자 경계를 어기고 `/tmp/g3-extra.QQbcK2`에 독립 복제본을 만들고 남겼습니다. 그 복제 결과는 판정 근거에서 전부 제외했고, 다음 명령으로 정확한 폴더를 제거했습니다.

```text
OUT_OF_SCOPE_TMP_REMOVAL_EXIT=0
```

→ 작업 폴더 밖 임시 쓰기는 절차 위반이었습니다. 잔여물은 0으로 제거했으며, 완료 근거는 작업 폴더 안의 `hardening6`, 전체 회귀, 무력화·원복 시험만 사용합니다.
