# HumanSearch G1 클린룸 게이트 goal

- 작성일: 2026-08-12
- 구현 계약: `worktrees/humansearch-clean-room-plan/docs/engineering/humansearch-v6-clean-room-rebuild-goal-2026-08-12.md`
- 작업 단위: Phase G의 G1 하나
- GitHub issue: `#7` (`G1: enforce HumanSearch clean-room runtime boundary`)
- 작업 브랜치/워크트리: `task/humansearch-g1-cleanroom-gate` / `worktrees/humansearch-g1-cleanroom-gate`
- 중단선: G1 PR과 CI 검증까지만 수행한다. G2, G3, B1 및 브라우저 구현은 시작하지 않는다.

## 1. 현재 상태

스캔 범위는 v6 현재 브랜치의 `scripts/`, `contracts/`, `hooks/`, `.github/`, `docs/sot/`와 오너가
제공한 클린룸 계약 문서로 제한했다. `Valuehire_v1`~`Valuehire_v5` 제품 소스는 열람·복사·import·실행하지
않았다.

| 사실 | 직접 확인한 증거 |
|---|---|
| G1 검사기와 패턴 계약은 아직 없다. | `test -e scripts/acceptance-hs-cleanroom.sh`, `test -e contracts/cleanroom-deny-patterns.txt`가 모두 부재를 확인했다. |
| pre-push는 신규 `acceptance-*.sh`를 글로브로 실행한다. | `docs/sot/hook-contracts.md:18-26`; `hooks/pre-push`의 `find ... -name 'acceptance-*.sh'` 호출 |
| CI는 acceptance 명령을 명시적으로 열거하므로 G1을 새로 배선해야 한다. | `docs/sot/verification-commands.md:18-25`; `.github/workflows/verify.yml`에 G1 호출 0건 |
| 시작 게이트는 현재 통과한다. | `bash scripts/session-status.sh` → `HEAD: 32ce698 (synced)`, `ORIGIN: 32ce698`, `RED: 0/4` |
| 한 AC는 한 task worktree/branch/PR로 격리해야 한다. | `docs/sot/git-workflow.md:14-23` |

## 2. 근본 원인

클린룸 경계가 문서에만 있고 추적 파일과 symlink를 판정하는 실행 장치가 없다. 일반 텍스트 grep만
추가하면 symlink가 저장소 밖 파일을 역참조하거나, 검사기/패턴 파일을 자기 면제로 빼거나, 처리 파일
0건으로도 성공할 수 있다. 또한 현 pre-push는 새 acceptance를 자동 회수하지만 CI는 그렇지 않아,
검사기 파일만 추가하면 로컬 전용 부분 배선이 된다.

## 3. Acceptance Criteria — G1 단언 1개

**비문서 추적 파일에 과거 v1~v5 경로·import·실행 참조가 있거나 추적 symlink가 저장소 밖을 가리키면,
동일한 G1 검사기가 로컬과 CI에서 exit 1로 거부한다. 깨끗한 실제 트리는 exit 0이고 검사 파일 수를
2개 이상 보고한다.**

기계 검증 명령과 기대 출력:

```text
bash scripts/acceptance-hs-cleanroom-mutations.sh
PASS: clean-room mutations blocked <N>/<N>

bash scripts/acceptance-hs-cleanroom.sh
PASS: forbidden runtime refs 0
PASS: escaping symlinks 0
CHECKED: <N>   # N >= 2
```

G1 검사기는 `docs/engineering/**`만 계약상 제외한다. 검사기 자체와
`contracts/cleanroom-deny-patterns.txt`는 검사 대상이다. 패턴 파일 누락·빈 패턴·grep 오류·Git 목록
실패·검사 수 2개 미만은 모두 fail-closed다.

## 4. Harness 게이트 진행

| Gate | 상태 | 증거/종료 조건 |
|---|---|---|
| 0 시작 자격 | PASS | `bash scripts/session-status.sh` → `RED: 0/4` |
| 1 스펙 | PASS | 이 문서와 GitHub issue `#7`에 G1 단언 1개만 두었다. |
| 2 격리/RED | PASS | 별도 worktree에서 `bash scripts/acceptance-hs-cleanroom-mutations.sh` → `FAIL: required G1 implementation missing: scripts/acceptance-hs-cleanroom.sh`, `RED_EXIT=1`. |
| 3 최소 구현 | PASS | RED `257eecd` 뒤 mutation 파일 diff 0을 유지하고 GREEN `d57f0b6`에 검사기·패턴·CI 배선만 추가했다. |
| 4 검증 | PASS_LOCAL | G1 두 명령, `bash verify.sh`, 기존 acceptance 전량, 실제 pre-push 호출, `RED: 0/6`을 확인했다. Claude/Codex 적대검증과 원격 CI는 아직 남았다. |
| 5 배송 | NOT_RUN | task 브랜치 push와 PR/CI까지만 수행한다. 병합은 하지 않는다. |
| 6 종료 | NOT_RUN | 오너 병합 전이므로 worktree를 제거하지 않는다. |

## 5. 적대 검증 항목

- 검사기나 패턴 파일이 자기 자신을 제외하는가.
- 파일명 공백·개행·선행 하이픈 또는 binary 취급으로 스캔이 우회되는가.
- 패턴 파일 누락·빈 값·깨진 regex·`git ls-files` 실패가 성공으로 오인되는가.
- v1~v5 각 세대 경로, 과거 커밋 식별자, 과거 driver import, subprocess/쉘 실행 참조를 놓치는가.
- 절대/상대/dangling symlink가 저장소 밖을 가리킬 때 차단되는가.
- 외부 symlink 내용을 읽어 버려 클린룸 경계를 검사기가 스스로 깨는가.
- pre-push에서는 실행되지만 CI에는 빠진 부분 배선인가.
- `CHECKED`가 0 또는 1인데 PASS하는가.

## 6. SOT 체크리스트

- [x] `docs/sot/INDEX.md`를 읽고 SOT와 사건 기록의 경계를 확인했다.
- [x] `docs/sot/coding-principles.md`의 P1/P2/P3/P5/P13/P15/P20을 G1에 적용했다.
- [x] `docs/sot/hook-contracts.md`의 pre-push 글로브와 fail-closed 계약을 확인했다.
- [x] `docs/sot/verification-commands.md`의 실제 bash 검증 배관을 확인했다.
- [x] `docs/sot/git-workflow.md`의 한 AC = 한 branch/worktree/PR 규약을 적용했다.
- [x] RED `257eecd`와 GREEN `d57f0b6`을 별도 커밋으로 남겼다.
- [x] pre-push 글로브 실행 4개 중 G1 두 명령이 포함됐고, `.github/workflows/verify.yml:28-31`에도 둘 다 배선됐다.
- [ ] Claude 1차 판정과 Codex 재현 결과를 아래 로그에 원문/명령과 함께 남긴다.

## 7. 비범위

- G2, G3, B1 및 모든 브라우저/extension/native-host 구현
- portal URL·port·selector 및 fresh capture provenance 검사
- v1~v5 제품 소스의 열람·복사·import·실행과 유사도 비교
- 실제 포털·후보자·세션·PII 접근
- main 직접 수정, 병합, 배포, 운영 push

## 적대 검증 로그

NOT_RUN — G1 GREEN과 로컬 검증 뒤 `claude -p` 1차, Codex 2차 순서로 append한다.

## 로컬 검증 로그

```text
$ bash scripts/acceptance-hs-cleanroom-mutations.sh
PASS: clean-room mutations blocked 10/10

$ bash scripts/acceptance-hs-cleanroom.sh
PASS: forbidden runtime refs 0
PASS: escaping symlinks 0
CHECKED: 29

$ bash verify.sh
PASS: no secret-pattern match in any tracked file, .env not tracked

$ bash scripts/acceptance-0-2.sh
PASS: 0-2 — 히스토리·객체·reflog·docs 리터럴 0건, 스캐너 뮤테이션 검출 확인

$ bash scripts/acceptance-0-5.sh
PASS: 0-5 완료 — CI 비밀스캔 강제 + push 완료 + 원격 트리 비밀 0건

$ bash scripts/acceptance-0-6.sh
PASS: 병합 완료, 가짜 검증 스크립트 0건

$ bash scripts/acceptance-0-7.sh
PASS: 위반 6 종이 전부 차단됨 (각 건 훅 OFF 대조 통과)

$ hooks/pre-push
pre-push: 검사 4개 실행
  ok  ./scripts/acceptance-0-6.sh
  ok  ./scripts/acceptance-hs-cleanroom-mutations.sh
  ok  ./scripts/acceptance-hs-cleanroom.sh
  ok  ./verify.sh

$ bash scripts/session-status.sh
HEAD: d57f0b6 (ahead 2 / behind 0)
ORIGIN: 32ce698
RED: 0/6 (acceptance-0-7.sh 제외 — CI 담당)
```

task worktree에는 ignore된 `.secret-patterns`가 없어서 첫 `acceptance-0-2`가 exit 2였고, 환경변수를
전역 주입하면 `acceptance-0-5`의 격리 clone까지 오염됐다. v6 루트의 로컬 패턴 파일을 ignore된
`.secret-patterns` symlink로 연결한 뒤 각 스크립트의 기본 경로를 보존해 최종 `RED: 0/6`을 얻었다.
