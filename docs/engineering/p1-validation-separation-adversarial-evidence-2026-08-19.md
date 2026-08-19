# P1 검증 분리 적대 검증 증거 (2026-08-19)

## 결론

Claude 1차 적대 검증은 `VERDICT: PASS`를 반환했다. Codex 2차 재공격은 그 결론을 그대로 채택하지 않고, 원본 작업트리 밖의 임시 복제본에서 작업 이름·실행 모드·실패 무시 변조를 각각 주입했다. 세 변조는 모두 정적 배선 시험을 실패시켰다. 실제 workflow에서 추출한 진단 셸은 `rc=1`만 비차단하고 `rc=2`, `rc=127`은 원래 종료값으로 실패했다.

원격 GitHub Actions 결과는 아직 이 문서의 증거가 아니다. 이 문서는 push 전 로컬 적대 검증만 기록하며, 원격 원문은 push 뒤 별도 절에 추가한다.

## Claude 1차 실행 명령

실행 표면은 아래와 같다. 프롬프트에는 이 문서의 다음 원문에 나타난 14개 확인 항목과 출력 계약을 모두 전달했다.

```text
env -u ANTHROPIC_API_KEY claude -p '<PR #31 후속 변경 읽기 전용 적대 검증 프롬프트>'
```
→ API 키 환경변수를 제거한 로컬 Claude CLI에 읽기 전용 검증만 요청했다.

## Claude 1차 원문 보존 위치

CLI가 반환한 9,252자 전체 원문은
`docs/engineering/p1-validation-separation-claude-raw-2026-08-19.txt`에 바이트 순서대로 보존했다. 아래 블록은 검토 편의를 위해 같은 결론과 근거를 저장소 문맥에 맞춰 정리한 사본이며, 원문을 대체하지 않는다.

## Claude 1차 정리본

```text
VERDICT: PASS

# 결론

PR #31 후속 변경(95329e2..ebe9f6f)은 사용자가 지시한 14개 확인 항목 전부를 통과했습니다. principles.yaml의 "32개 중 31개 미충족"이라는 실제 상태는 조금도 숨겨지거나 완화되지 않았고, 그 미충족 판정이 P1 장부 구조 검사·P3 검사·기존 verify 회귀 검사의 실행을 더 이상 가로막지 않도록 GitHub Actions 워크플로가 4개의 독립 작업(job)으로 분리됐습니다. 저는 문서의 자기 주장을 그대로 믿지 않고, 실제 스크립트 실행·격리된 워크플로 변조 재현·GitHub API 실측으로 하나씩 다시 확인했으며, 이 과정에서 검증 대상 저장소 파일이나 git 상태는 전혀 바꾸지 않았습니다.

# 판단 근거

가장 중요한 갈림길은 "workflow YAML에 새 job 4개와 이름이 보인다는 사실을 그대로 배선 완료로 인정할 것인가, 아니면 그 job들이 실제로 서로 독립적이고 각 job의 명령이 진짜로 요구된 모드로 고정돼 있는지 별도로 재현할 것인가"였습니다. 저는 후자를 택했습니다. 이유는 이 정책 변경의 핵심이 "이름만 그럴듯하게 나눠놓고 실제로는 여전히 한 job에 묶여 있거나, 진단 job이 몰래 `--schema-only`로 격하돼 미충족을 숨기는" 종류의 위장이 가장 위험한 실패 모드이기 때문입니다. 그래서 저는 `.github/workflows/verify.yml`을 직접 읽어 4개 job에 `needs`가 전혀 없음을 확인했고(아래 §1), 거기서 멈추지 않고 job 이름·실행 모드·`continue-on-error`를 임의로 변조한 사본을 mktemp 격리 디렉터리에서 만들어 `acceptance-principles-mutations.sh`에 내장된 것과 동일한 Ruby 판정 로직을 독립적으로 재실행했습니다(아래 §3). 세 가지 변조(이름 변경, 모드 약화, `continue-on-error` 삽입) 전부 실제로 잡혔습니다.

두 번째 갈림길은 "진단 job의 rc≥2 처리를 workflow YAML 텍스트 검토만으로 충분하다고 볼 것인가, 실제로 그 bash `case` 문을 rc=0/1/2/127 네 가지로 실행해 봐야 하는가"였습니다. 텍스트만 봐서는 `set +e ... set -e ... case ... exit "$rc"` 조합이 GitHub Actions의 기본 `bash -e` 실행 환경에서 의도대로 동작하는지 확신할 수 없었으므로, 저는 그 스텝의 셸 로직을 그대로 떼어내 네 가지 rc로 직접 실행했습니다(아래 §2). rc=1은 스텝 자체가 exit 0으로 끝나(비차단) 다른 job을 막지 않고, rc=2·127은 스텝이 그 값 그대로 실패해 진단 job이 실패합니다 — 사용자가 요구한 "rc≥2는 성공으로 바꾸거나 숨기면 안 된다"는 조건과 정확히 일치합니다.

세 번째 갈림길은 "branch protection을 문서 주장(§11 '실측이 있을 때만 주장한다')만 읽고 넘어갈 것인가, 제가 직접 `gh api`로 재확인할 것인가"였습니다. 문서 스스로 "확인하지 않았다"고 명시했지만, 검증자가 그 명시를 재확인하지 않으면 "확인 안 했다고 써놓고 사실은 확인했으면서 숨겼을 가능성"을 배제할 수 없습니다. 직접 `gh api repos/sangmokang/Valuehire_v6/branches/main/protection`을 호출한 결과 403(GitHub 요금제 제한)이 나왔고, 이는 이전 세션에서 이미 기록된 한계와 일치합니다. 문서의 "확인하지 않았다"는 진술이 실제로 확인 불가능한 상황과 정확히 부합했습니다.

버린 해석은 "principles.yaml 상태가 이번 diff에 20줄 바뀐 것으로 나오니 뭔가 상태가 조작됐을 수 있다"는 의심이었습니다. 이는 `git diff --stat b3361f0..ebe9f6f`에서 나온 것인데, b3361f0에는 이 브랜치의 이전(선행) 조사 커밋 95329e2가 포함되지 않은 상태였기 때문입니다. 사용자가 지시한 정확한 기준점(95329e2 이후)으로 다시 `git diff`를 뜨자 principles.yaml은 완전히 무변화(빈 diff)였습니다. 잘못된 기준점으로 판단했다면 "상태 조작 의심"이라는 오판정을 내렸을 것입니다.

이 PASS 판정이 틀렸다면 무엇이 깨지는가: 만약 제가 놓친 조합 변조(예: job 이름과 모드를 동시에 손대면서 mutation 스크립트 자체도 같은 커밋에서 무력화하는 공격)가 실제로 존재한다면, 서버에서 "필수 검사 초록"을 32개 완료로 오인하는 사고가 재발할 수 있습니다. 다만 이 범주는 `hooks/pre-commit`의 "검사기 자기무력화 동시 변경 방어"(P3 mutation 로그의 "검사기 자체 무력화 공격 → BLOCKED" 항목)로 별도 방어되고 있으며, 이번 검증 범위(제가 재현한 3개 개별 변조)는 전부 잡혔습니다.

# 기술 상세

## 1. workflow job 분리·독립성 (요구사항 1)

`.github/workflows/verify.yml:15-70`에 4개 job이 정의돼 있습니다.

```yaml
jobs:
  principles-structure:      # :15  P1 원칙 장부 구조·배선 검증 (필수)
  p1-completion-diagnostic:  # :38  P1 원칙 32개 전체 완료 진단 (비차단)
  p3:                        # :70  P3 조용한 실패 문법 판정
  verify:                    # :81  비밀·HumanSearch·기록·훅 등 기존 회귀
```
→ 4개 job 모두 `needs:` 키가 없어 GitHub Actions는 이들을 병렬·독립 실행합니다. `principles-structure`는 `--schema-only`(:36)만, `p1-completion-diagnostic`은 인자 없는 기본 전체 명령(:47)만 실행해 두 의미가 명확히 나뉘어 있습니다.

`p1-completion-diagnostic` job(:38-68)의 핵심:

```yaml
run: |
  set +e
  bash scripts/acceptance-principles-check.sh
  rc=$?
  set -e
  echo "P1_COMPLETION_RAW_EXIT: $rc"
  case "$rc" in
    0) echo "P1_COMPLETION_RESULT: COMPLETE" ;;
    1) echo "P1_COMPLETION_RESULT: UNMET"; echo "::warning ..." ;;
    *) echo "P1_COMPLETION_RESULT: NOT_RUN"; exit "$rc" ;;
  esac
```
→ rc=1(미충족)만 비차단 처리하고, rc=0·rc≥2는 각각 성공/그대로 실패로 남습니다. 이 로직을 아래 §2에서 직접 재현했습니다.

## 2. rc별 진단 스텝 재현 (요구사항 2)

동일 `set +e/case/exit` 셸 로직을 4가지 인위적 rc로 직접 실행했습니다.

```text
--- rc=0 --- P1_COMPLETION_RESULT: COMPLETE, STEP_EXIT=0
--- rc=1 --- P1_COMPLETION_RESULT: UNMET,    STEP_EXIT=0
--- rc=2 --- P1_COMPLETION_RESULT: NOT_RUN,  STEP_EXIT=2
--- rc=127 --- P1_COMPLETION_RESULT: NOT_RUN, STEP_EXIT=127
```
→ rc=1만 스텝 자체가 exit 0으로 끝나 job이 계속되고, rc≥2는 스텝이 원래 값 그대로 실패합니다.

## 3. mutation 스크립트의 드리프트 탐지 (요구사항 3)

`scripts/acceptance-principles-mutations.sh:224-320`에 내장된 workflow 정적 배선 검사 로직을 mktemp 격리 사본에 3가지 변조를 가해 재현했습니다.

```text
=== job 이름만 변경 ===        → JOB_NAME_MISMATCH: principles-structure
=== --schema-only → --full === → STRUCTURE_COMMAND_MISSING: bash scripts/acceptance-principles-check.sh --schema-only
=== continue-on-error: true 삽입 === → REQUIRED_JOB_ALLOWS_FAILURE: principles-structure
```
→ 세 가지 변조 모두 별도 오류 코드로 잡혔습니다. `bash scripts/acceptance-principles-mutations.sh`도 21/21 PASS, exit 0으로 통과했습니다.

## 4~11. 지정 스크립트 실측 결과 (요구사항 4~11)

```text
scripts/acceptance-principles-mutations.sh          → CHECKED: 21, FAIL 0건, exit=0
scripts/acceptance-silent-failure-lint-mutations.sh → CHECKED: 35, FAIL 0건, exit=0
  (자기무력화 공격 → BLOCKED exit=1 / 무해한 자기개선 → 통과 exit=0)
scripts/acceptance-guard-global-skill-files.sh      → CHECKED: 8, FAIL 0건, exit=0
scripts/acceptance-hs-a4.sh                         → CHECKED: 30, FAIL 0건, exit=0
scripts/acceptance-principles-check.sh --pre-push   → P1_LOCAL_GATE, exit=0
scripts/acceptance-principles-check.sh              → P1_UNMET: 31/32, exit=1
verify.sh                                            → PASS, exit=0
scripts/session-status.sh                            → HEAD: ebe9f6f, RED: 2/25, exit=0
```
→ 전체 완료 명령의 종료값 1과 `P1_UNMET: 31/32`가 그대로 재현됐습니다. 상태 합계도 32개입니다.

## 12. principles.yaml 무변경 (요구사항 12)

```text
git diff 95329e2..ebe9f6f -- docs/sot/principles.yaml   → 빈 출력
```
→ 95329e2 이후 principles.yaml은 무변화입니다. b3361f0과의 차이는 선행 조사 커밋 95329e2에서 이미 생긴 변경입니다.

## 13. 문서의 정직성 (요구사항 13)

`docs/sot/verification-commands.md:20`은 저장소 정책의 “필수”와 GitHub branch protection의 required check를 구분합니다. Claude가 직접 API를 호출했을 때 다음 응답을 받았습니다.

```text
gh api repos/sangmokang/Valuehire_v6/branches/main/protection
→ 403 "Upgrade to GitHub Pro or make this repository public to enable this feature."
```
→ 보호 규칙의 실제 활성 여부를 확인할 수 없으므로 required check라고 주장하지 않는 문서와 일치합니다.

## 14. git 상태 무손상 (요구사항 14)

```text
검증 시작: On branch task/strict-principles-yaml, nothing to commit, working tree clean
검증 종료: branch.ab +6 -0, porcelain 변경 없음
```
→ 읽기 전용 검증 전후 원본 작업트리 변경은 없습니다.

# 용어 설명

- job은 GitHub Actions 안에서 독립 실행되는 작업 단위입니다.
- rc는 명령 종료값입니다. 이 계약은 1을 미충족, 2 이상을 검사 실행 오류로 구분합니다.
- required check는 GitHub branch protection이 서버에서 병합을 강제하는 설정입니다. 저장소 문서의 정책상 “필수”와 다릅니다.
- mutation 검사는 격리 사본에 위반을 일부러 넣어 검사기가 실제로 차단하는지 증명하는 방법입니다.

# 발견 사항

1. [INFO, 낮음] 이 증거 문서가 생기기 전 goal의 적대 검증 절은 비어 있었습니다. 사업 영향은 증거 보존 미완료였으며 이 문서로 보완됩니다.
2. [INFO, 낮음] 로컬 브랜치가 원격보다 6커밋 앞서 있어 새 workflow의 원격 실행 증거는 아직 없습니다. 사업 영향은 로컬 합격만으로 서버 실행을 주장할 수 없다는 것입니다.

# 5줄 설계 카드

문제 — P1 전체 미충족이 같은 job의 뒤 검사를 실행하지 못하게 했습니다.
목표 — 미충족을 보존하면서 구조·P3·회귀 검사를 독립 실행합니다.
핵심 제약 — 상태 상향, rc≥2 은폐, P3·회귀 약화가 금지됩니다.
선택 — 구조 필수, 전체 완료 진단, P3, verify를 네 독립 job으로 둡니다.
기각 — 전체 명령 삭제, 상태 상향, 같은 job의 실패 무시는 증거를 숨기므로 버립니다.

# 미확인 사항과 재시도

- push 전이므로 GitHub Actions 서버의 네 job과 원격 `P1_UNMET` 원문은 아직 확인하지 못했습니다.
- branch protection API는 403이라 실제 활성 여부를 확인하지 못했습니다.
- 로컬 명령은 모두 첫 실행에서 의도한 결과를 냈습니다.
```
→ 위 블록은 Claude CLI 1차 판정의 저장소 검토용 정리본이며, 전체 원문은 별도 `.txt` 파일이 기준이다.

## Codex 2차 재공격

| 공격 또는 대조군 | 기대 | 실제 | 판정 |
| --- | --- | --- | --- |
| 구조 job 표시 이름 변경 | 정적 시험 실패 | `JOB_NAME_MISMATCH`, exit 1 | 차단 |
| 구조 명령 `--schema-only`를 `--full`로 변경 | 정적 시험 실패 | `STRUCTURE_COMMAND_MISSING`, exit 1 | 차단 |
| 구조 job에 `continue-on-error: true` 삽입 | 정적 시험 실패 | `REQUIRED_JOB_ALLOWS_FAILURE`, exit 1 | 차단 |
| 실제 진단 셸에 fixture rc 0 | step 0, COMPLETE | step 0, COMPLETE | 통과 |
| 실제 진단 셸에 fixture rc 1 | step 0, UNMET | step 0, UNMET | 통과 |
| 실제 진단 셸에 fixture rc 2 | step 2, NOT_RUN | step 2, NOT_RUN | 차단 |
| 실제 진단 셸에 fixture rc 127 | step 127, NOT_RUN | step 127, NOT_RUN | 차단 |
| 전체 P1 명령 | exit 1, 31/32 | exit 1, `P1_UNMET: 31/32` | 보존 |
| `95329e2..HEAD` 원칙 장부 | 무변경 | 빈 diff | 보존 |
| 기존 비-P1 verify 단계 | 17개 순서 보존 | 17개 동일 | 보존 |
| P3 검사기·뮤테이션·pre-commit | 무변경 | 빈 diff | 보존 |

→ Claude의 PASS를 독립 반례로 공격했고, 각 실패 방향과 정상 대조군이 예상 종료값을 냈다.

### 재공격 중 발견하고 기각한 오경보

첫 비교는 과거 P1 단계 이름을 잘못 적어 `EXPECTED=21 ACTUAL=17`을 출력했다. 실제 과거 workflow의 앞 네 단계가 P1 관련 단계임을 이름별로 다시 대조한 뒤 정확한 경계로 재실행했다.

```text
MOVED_P1_STEPS=4
VERIFY_NON_P1_STEPS_PRESERVED=true
EXPECTED=17 ACTUAL=17
JOBS_WITH_NEEDS=
P3_GUARD_FILES_UNCHANGED=1
```
→ 초기 불일치는 구현 누락이 아니라 검증용 비교 코드의 분류 오류였으며, 수정된 대조는 기존 회귀 17개와 P3 방어 파일의 보존을 증명한다.

## 현재 한계

- `/tmp/p1-codex-reattack.RFmSTT`와 `/tmp/p1-rc-matrix.sMPrlL`은 격리 시험 산출물이며 원본 작업트리에 포함되지 않는다.
- 원격 Actions 로그와 최종 PR 본문은 아직 검증하지 않았다.
- branch protection API의 403은 “보호 없음”의 증거가 아니라 실제 설정을 확인하지 못했다는 증거다.
