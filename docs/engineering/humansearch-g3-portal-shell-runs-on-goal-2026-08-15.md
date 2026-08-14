# 결론

검사 명령의 글자만 남겨 두고 실제 실행을 없애는 세 가지 설정과, 실행할 기계를 지정하지 않은 설정을 모두 거부하도록 고칩니다. 실패를 먼저 재현하고 최소 수정 뒤 전체 과거 시험을 다시 통과시킬 때까지만 완료로 보겠습니다.

# 판단 근거

현재 검사는 실행할 명령이 적혀 있는지와 일부 건너뛰기 설정만 확인합니다. 그러나 명령을 어떻게 처리할지 바꾸는 세 위치와 실행 기계 지정은 확인하지 않으므로, 아무 검사도 하지 않는 설정을 정상으로 인정할 수 있습니다.

갈림길은 낯선 실행 처리기 값만 골라 금지할지, 해당 설정의 존재 자체를 거부할지입니다. 값 목록 방식은 새 무력화 문자열을 다시 놓칠 수 있으므로 버리고, 사용자 요구대로 세 위치 중 한 곳에라도 설정이 있으면 값과 관계없이 거부합니다. 실행 기계도 값의 종류를 심사하지 않고 키가 없으면 거부합니다.

이 판단이 틀리면 서버 설정 화면에는 여덟 검사 명령이 그대로 보이지만 실제로는 한 줄도 실행되지 않거나, 실행할 수 없는 작업을 정상 표본으로 검증하게 됩니다.

## 설계 결정 카드

- **무엇을** — G3 명령을 담은 단계의 `shell`, 그 작업의 `defaults.run.shell`, 파일 전체의 `defaults.run.shell`이 하나라도 있으면 불합격시키고, 그 작업의 `runs-on`이 없을 때도 불합격시킵니다.
- **왜** — 세 설정은 명령 글자를 보존한 채 실행 방식만 바꿀 수 있고, `runs-on`은 실제 작업 실행에 필요한 소유 정보이기 때문입니다.
- **버린 길** — `echo {0}` 같은 알려진 값만 금지하는 목록 방식은 다른 실행 무력화 값을 놓치므로 버렸습니다.
- **대가** — 안전한 사용자 지정 실행 처리기를 쓰는 G3 단계도 허용하지 않는 보수적 제한이 생깁니다.
- **되돌리기** — 안전한 처리기 허용이 필요해지면 별도 실패 표본과 명시적 허용 목록을 먼저 승인받아 이 존재 기반 차단을 좁혀야 합니다.

# 기술 상세·증거

## 현재 상태

- `scripts/acceptance-hs-portal-constants.sh:222-236` — G3 명령이 든 작업과 단계를 고르는 본체입니다. 작업 조건·선행 작업·실패 무시와 단계 조건·실패 무시·명령 문자열만 보고, 세 `shell` 위치와 `runs-on`은 읽지 않습니다.
- `scripts/acceptance-hs-portal-constants-hardening6.sh:62-85` — 정상·공격 워크플로 표본을 만드는 함수입니다. 현재 정상 표본에도 `runs-on`이 없습니다.
- `.github/workflows/verify.yml:14-60` — 실제 G3 실행 경로입니다. G3 작업에는 `runs-on: ubuntu-latest`가 있고, G3 단계와 작업·파일 기본값에는 `shell` 설정이 없습니다.
- `.claude/private-reviews/codex-g3-verdict5-2026-08-15.md` — 단계·작업 기본값·파일 기본값의 실행 처리기 무력화와 실행 기계 누락이 각각 기존 본체 종료값 0으로 재현된 최신 판정입니다.

→ 무엇을 확인했나: 본체 판정부, 시험 표본 생성부, 실제 서버 설정, 최신 판정의 네 재현을 서로 대조했습니다. 실제 파일은 새 규칙의 정상 형태이고 시험 생성부와 본체만 보강이 필요합니다.

## 근본 원인

YAML(= 들여쓰기로 서버 자동 실행 구조를 적는 설정 형식)을 구조적으로 읽은 뒤에도 `run` 문자열 중심으로만 정상 여부를 정합니다. 실행 처리기를 바꾸는 소유 위치와 실행 기계 지정이 정상 조건에 포함되지 않은 것이 공통 원인입니다.

## 인수 기준

1. 단계 `shell` 키가 있는 G3 표본은 본체가 정확히 종료값 1을 냅니다.
2. G3 작업의 `defaults.run.shell`이 있는 표본은 본체가 정확히 종료값 1을 냅니다.
3. 파일 전체의 `defaults.run.shell`이 있는 표본은 본체가 정확히 종료값 1을 냅니다.
4. G3 작업에 `runs-on`이 없는 표본은 본체가 정확히 종료값 1을 냅니다.
5. `hardening6` 정상 표본은 `runs-on: ubuntu-latest`를 가지며 본체 종료값 0입니다.
6. 실제 `.github/workflows/verify.yml`은 새 규칙에서 본체 종료값 0입니다.
7. 본체·mutations·hardening 1~6과 추적 셸 파일 전체 문법 검사가 모두 종료값 0입니다.
8. `shell` 방어 한 줄을 임시 무력화하면 `hardening6`이 종료값 1이고, 원복 뒤 다시 0입니다.

여기서 종료값(= 프로그램이 끝나며 남기는 성적)은 이 본체에서 0이 합격, 1이 규칙 위반, 2가 검사를 수행할 수 없음입니다.

## Harness 게이트 진행

- 게이트 0: `Makefile`과 `package.json`이 없고 `make -n red-ledger`는 2였습니다. 이 저장소 정본에 따라 `bash scripts/session-status.sh`를 실행해 시작 HEAD `201baa5`와 원격 기준을 확인했습니다.
- 게이트 1: 위 인수 기준 여덟 개로 작업 계약을 고정했습니다.
- 게이트 2: 사용자가 지정한 격리 워크트리와 `task/humansearch-g3-portal-constants` 브랜치를 사용합니다.
- 게이트 3: `hardening6`에 네 실패 표본을 먼저 추가해 기존 본체의 잘못된 0을 기록한 뒤 본체를 수정합니다.
- 게이트 4: 사용자 지정 전량 회귀와 `bash verify.sh`를 실행하고 종료값 원문을 보고서에 보존합니다.
- 게이트 5: 로컬 커밋까지만 허용합니다. `git push`, 합치기, 배포는 하지 않습니다.
- 게이트 6: 이 작업에서는 워크트리를 제거하지 않습니다.

## 적대 검증 항목

- 세 `shell` 설정 중 하나를 놓치거나 G3 명령이 없는 다른 작업의 설정 때문에 오탐하지 않는지 확인합니다.
- `runs-on`이 다른 작업에만 있고 G3 작업에는 없는 경우를 정상으로 오인하지 않는지 확인합니다.
- 새 방어 한 줄을 무력화했을 때 새 시험이 실제로 실패하는지 확인합니다.
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
