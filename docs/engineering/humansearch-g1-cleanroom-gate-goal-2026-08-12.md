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

| 시작 사실 | 직접 확인한 증거 |
|---|---|
| 시작 시 G1 검사기와 패턴 계약은 없었다. | 기준 커밋 `32ce698`에서 두 파일이 부재했다. |
| pre-push는 신규 `acceptance-*.sh`를 글로브로 실행한다. | `docs/sot/hook-contracts.md:18-26`; `hooks/pre-push`의 `find ... -name 'acceptance-*.sh'` 호출 |
| CI는 acceptance 명령을 명시적으로 열거하므로 G1을 새로 배선해야 한다. | `docs/sot/verification-commands.md:18-25`; `.github/workflows/verify.yml`에 G1 호출 0건 |
| 시작 게이트는 현재 통과한다. | `bash scripts/session-status.sh` → `HEAD: 32ce698 (synced)`, `ORIGIN: 32ce698`, `RED: 0/4` |
| 한 AC는 한 task worktree/branch/PR로 격리해야 한다. | `docs/sot/git-workflow.md:14-23` |

G1 핵심 구현 `6a9ae52`에는 fail-closed 스캐너 1개, deny-pattern 계약 1개, 고정 회귀 계약 5개가
있다. 최신 main `0459a37`을 merge한 배송 HEAD에서도 CI는 G1 스크립트 6개를 명시 실행하고
pre-push는 같은 6개를 글로브로 회수한다.

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
| 3 최소 구현 | PASS | 다섯 RED→GREEN 쌍을 분리했고 각 RED 파일은 대응 GREEN에서 byte diff 0이다. |
| 4 검증 | PASS_LOCAL_ADVERSARIAL | G1 6개, `verify.sh`, 0-2/0-5/0-6/0-7, 병합 후 pre-push 10개, `RED: 0/12`, Fable5 PASS, Codex V2 PASS를 확인했다. |
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
- [x] 다섯 RED `257eecd`, `602a131`, `e5197cf`, `f60d95c`, `8fb7a80`과 대응 GREEN을 별도 커밋으로 남겼다.
- [x] 최신 main 병합 후 pre-push 실행 10개 중 G1 6개가 포함됐고 `.github/workflows/verify.yml`에도 6개가 모두 명시됐다.
- [x] Fable5 1차 판정과 Codex 재현 결과를 아래 로그에 원문/명령과 함께 남겼다.

## 7. 비범위

- G2, G3, B1 및 모든 브라우저/extension/native-host 구현
- portal URL·port·selector 및 fresh capture provenance 검사
- v1~v5 제품 소스의 열람·복사·import·실행과 유사도 비교
- 실제 포털·후보자·세션·PII 접근
- main 직접 수정, 병합, 배포, 운영 push

## 적대 검증 로그

### 수정 이력

| 공격 | 판정 | 재현·조치 |
|---|---|---|
| 초기 Fable5의 `verification-commands.md` 선갱신 요구 | 당시 기각, 최신 SOT 병합 뒤 반영 | 구현 계약 357-358행 때문에 초기 main에서는 G2 전 선기재가 금지됐다. 이후 main `0459a37`의 최신 SOT가 새 acceptance PR의 실제 명령 동시 기재를 의무화해, 검증 완료된 G1 6개만 추가하고 G2 명령은 기재하지 않았다. |
| 초기 Fable5 PASS 뒤 Codex 재공격 | 1건 발견 | 임의 루트의 절대 worktree 경로가 통과했다. RED `602a131` → GREEN `3ed8f13`. |
| Fable5 문맥 재공격 | 7건 발견 | root-only, array, backtick, redirect, escaped space, brace, double-slash. RED `e5197cf` → GREEN `467fe5c`. |
| Fable5 콜론 재공격 | 4건 발견 | PATH 목록과 `host:/...` 문맥. RED `f60d95c` → GREEN `9cf5df2`. |
| Fable5 file URL 재공격 | 2건 발견 + 과차단 1건 | `file:///...`를 막고 `$(pwd)/...`를 허용했다. RED `8fb7a80` → GREEN `6a9ae52`. |
| 최종 Fable5 → Codex V2 | 모두 PASS | Fable5 차단 fuzz 43/43·허용 16/16, Codex 차단 31/31·허용 16/16, RED 역사 5/5. |

### Fable5 최종 1차

실행 명령:

```bash
env -u ANTHROPIC_API_KEY claude --safe-mode --no-session-persistence --permission-mode bypassPermissions --tools Read,Grep,Bash --model claude-fable-5 --effort high -p "$(sed -n '1,$p' /tmp/humansearch-g1-fable5-final2-prompt.txt)"
```

`-p` 임시 파일에는 G1만 평가하고, 구버전 소스·fixture·package·worktree·process·Git blob의
열람/복사/import/실행을 금지하며, 공식 6개 검사·다섯 RED/GREEN·fail-closed·경로 fuzz·기존 결함군과
정상 기준선을 재공격하고 마지막에 `VERDICT` 하나를 출력하라는 프롬프트를 넣었다.

원문(ANSI 없음):

> # G1 최종 적대적 검증 결과 — HEAD `6a9ae52`
>
> ## 요약
>
> 현재 HEAD에서 G1 계약(비문서 추적 파일의 v1~v5 경로·import·실행·symlink 거부, fail-closed, 로컬/CI 동일 검사기)에 **중대한 결함을 찾지 못했습니다.** 요청된 6개 항목 전부를 신선한 증거로 재검증했고, 워크트리는 검증 종료 시점에도 clean입니다. 아래에 증거와 경미한 관찰 2건을 기록합니다.
>
> ## 1. 공식 스크립트·배선 — 전부 PASS
>
> - 스캐너 `scripts/acceptance-hs-cleanroom.sh` → `PASS: forbidden runtime refs 0`, `PASS: escaping symlinks 0`, `CHECKED: 33`, exit 0. **33은 정확히 추적 파일 57 − `docs/engineering/` 24와 일치**하며, 검사기 자신과 `contracts/cleanroom-deny-patterns.txt`도 검사 대상에 포함됩니다(제외는 `scripts/acceptance-hs-cleanroom.sh:109`의 `docs/engineering/*` 하나뿐).
> - 5개 인수 스크립트: mutations 10/10, absolute-paths 3/3, absolute-contexts 7/7, colon-paths 4/4, file-urls 2/2 — 모두 exit 0.
> - `verify.sh` PASS, `session-status.sh` → `RED: 0/10`.
> - pre-push 발견: `hooks/pre-push:112`의 글로브가 G1 스크립트 6개 전부를 자동 회수해 실행했고(검사 8개, exit 0), CI는 `.github/workflows/verify.yml:28-35`의 전용 스텝에서 동일 6개를 `bash scripts/...`로 명시 실행합니다. 로컬/CI 동등성 성립.
> - `docs/sot/`는 검증 당시 브랜치 전체에서 diff 0 — 당시 `verification-commands.md` 변경을 요구하지 않으며 계약대로 G2로 유보됨. 이후 main `0459a37` 병합으로 최신 SOT가 새 acceptance 명령의 동시 기재를 요구해 G1 6개만 후속 반영했다.
>
> ## 2. RED-before-GREEN 5쌍 — byte 불변 + 역사적 실패 재현
>
> 각 RED 테스트 파일의 blob 해시가 RED 커밋과 HEAD에서 동일하고(`git log`상 각 파일을 건드린 커밋은 자기 RED 하나뿐), 각 RED 커밋 트리를 임시 디렉터리에 추출해 실행하면 실제로 실패했으며, 각 GREEN 커밋에서 통과로 전환됩니다.
>
> | RED → GREEN | RED 시점 실패 증거 |
> |---|---|
> | `257eecd` → `d57f0b6` | `FAIL: required G1 implementation missing` exit 1 |
> | `602a131` → `3ed8f13` | 임의 루트 3건 미차단 (scanner exit 0) |
> | `e5197cf` → `467fe5c` | 절대경로 문맥 7건 미차단 |
> | `f60d95c` → `9cf5df2` | 콜론 구분 4건 미차단 |
> | `8fb7a80` → `6a9ae52` | file:// 미차단 **그리고** `$(pwd)` 과차단(양방향 결함)을 동시에 노출 |
>
> ## 3. 스캐너 fail-closed·적대 입력 — 전부 정상
>
> 샌드박스 실측: git 저장소 아님/패턴 파일 부재/빈 파일/주석만/깨진 regex/빈 매칭 regex(`.*`)/패턴 파일 읽기불가/CHECKED<2/추적 파일 읽기불가 → 9건 모두 exit 2 fail-closed. 공백·개행·선행 하이픈 파일명과 NUL 포함 바이너리 속 오염 4건 모두 검출, 저장소 내부 symlink는 허용, 절대·dangling 탈출 symlink는 mutations 스크립트가 차단 확인. 패턴 자기매칭은 `worktre[e]s`·`cce928[0]`·런타임 문자열 조립으로 회피되어 자기면제 없이 통과합니다.
>
> ## 4. 합성 fuzz — 차단 43종 / 허용 16종 전부 기대 일치
>
> 임시 디렉터리의 합성 문자열만 사용(구소스 미접촉, 종료 후 삭제 확인). 임의 루트, 파일시스템 루트 `/worktrees/x`, 이중 슬래시, 무末尾슬래시, 배열/백틱/리다이렉트/이스케이프 공백/브레이스/따옴표/Python 접두 문자열, 콜론 리스트(`$BASE:`, `PYTHONPATH`, `export P=$P:`, `host:`, `user@host:`), `file:` 슬래시 1~4개·대문자, `~/worktrees`, v1~v5 각 세대·`cce9280`·`cdp_driver` 대소문자 — 모두 차단. `https://`·`ssh://`·`git@host:상대경로`·`"$GCD"/`·`${GCD}/`·`$GCD/`·`$(pwd)/`·상대경로·`./`·`../`·`'./worktrees/*'` 글로브 — 모두 허용.
>
> **최신 수리의 필수 4건 정확 판정:** `file:///az/worktrees/x` 차단, `git clone file:///Users/me/project/worktrees/other-task` 차단, `https://example.com/worktrees/demo` 허용, `$(pwd)/worktrees/demo` 허용 — 패턴 직접 grep과 공식 `acceptance-hs-cleanroom-file-urls.sh`(전체 스캐너 경유) 양쪽에서 확인.
>
> ## 5. 경미한 관찰 (판정 비차단)
>
> - **[MINOR] 산문 속 비이스케이프 공백 경로 미차단** — `contracts/cleanroom-deny-patterns.txt:7`. 재현: `/My Drive/worktrees/x` → 허용. 따옴표판(`"/custom root/..."`)과 이스케이프판(`\ `)은 차단되므로, 남는 것은 셸/코드에서 단일 토큰이 될 수 없는 산문 표기뿐입니다. 계약 §3-4가 의도적 회피의 완전 증명을 주장하지 않으므로 중대 결함이 아닙니다. 교정하려면 `([^/[:space:]…]| )` 형태의 산문 전용 패턴을 추가하되 과차단 회귀 테스트가 선행돼야 합니다.
> - **[INFO] 줄 분할·인코딩 회피 가능** — grep은 줄 단위 바이트 매칭이라 `Valuehire_\n v5`나 UTF-16 표기는 통과합니다. 이는 의도적 회피 영역으로, G1의 우발적 오염 차단 계약 범위 밖입니다.
> - **[INFO] 안전 방향 과차단** — `/az/worktrees-backup/x`처럼 `worktrees-` 접두 이름도 차단됩니다(末尾 경계에 `-` 허용). 허용 기준선 6종과 충돌하지 않아 교정 불요.
>
> 검증 종료 상태: `git status` clean, HEAD `6a9ae52`, 임시 디렉터리 전부 삭제, v1~v5 소스·프로세스·blob 미접촉.
>
> VERDICT: PASS

### Codex 2차 재현·재공격

실행 명령: `bash -n /tmp/humansearch-g1-codex-v2.sh && bash /tmp/humansearch-g1-codex-v2.sh`

원문:

```text
PASS: Codex reproduced byte-stable RED->GREEN history 5/5
PASS: Codex blocked static-path/string fuzz 31/31
PASS: Codex preserved dynamic/relative/remote baselines 16/16
INFO: unquoted prose path with a raw space remains outside executable-token coverage
PASS: Codex reproduced fail-closed pattern/count guards 4/4
PASS: Codex V2 adversarial verification; official G1 6/6; worktree clean
```

| Fable5 주장 | Codex 재현 | 최종 판정 |
|---|---|---|
| RED→GREEN 5쌍이 byte 불변이고 RED에서 실제 실패 | 5/5 재현 | 일치 |
| 공식 G1 6개와 clean scan 통과 | 6/6 재현 | 일치 |
| 정적 경로/문자열 공격 전량 차단 | 독립 31/31 | 일치 |
| 동적·상대·원격 URL 정상 기준선 통과 | 독립 16/16 | 일치 |
| fail-closed | 독립 4/4 | 일치 |
| 비인용 raw-space 산문은 남지만 실행 토큰이 아님 | 동일 재현 | 알려진 비차단 한계, G1 material defect 아님 |

Fable5가 최종 PASS 전에 놓쳤고 Codex가 먼저 찾은 material 결함은 임의 루트 1개 클래스였다. 이후
Fable5가 문맥 7개, 콜론 4개, file URL 2개를 추가로 찾았다. 최종 교정 뒤 양쪽의 material 불일치는 0개다.

## 로컬 검증 로그

```text
$ bash scripts/acceptance-hs-cleanroom-file-urls.sh
PASS: local file URLs blocked without URL/dynamic overreach 2/2

$ bash scripts/acceptance-hs-cleanroom-colon-paths.sh
PASS: colon-delimited absolute worktree paths blocked 4/4

$ bash scripts/acceptance-hs-cleanroom-absolute-contexts.sh
PASS: absolute worktree path contexts blocked 7/7

$ bash scripts/acceptance-hs-cleanroom-absolute-paths.sh
PASS: arbitrary absolute worktree paths blocked 3/3

$ bash scripts/acceptance-hs-cleanroom-mutations.sh
PASS: clean-room mutations blocked 10/10

$ bash scripts/acceptance-hs-cleanroom.sh
PASS: forbidden runtime refs 0
PASS: escaping symlinks 0
CHECKED: 36

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
pre-push: 검사 10개 실행
  ok  ./scripts/acceptance-0-6.sh
  ok  ./scripts/acceptance-hs-a3.sh
  ok  ./scripts/acceptance-hs-a4.sh
  ok  ./scripts/acceptance-hs-cleanroom-absolute-contexts.sh
  ok  ./scripts/acceptance-hs-cleanroom-absolute-paths.sh
  ok  ./scripts/acceptance-hs-cleanroom-colon-paths.sh
  ok  ./scripts/acceptance-hs-cleanroom-file-urls.sh
  ok  ./scripts/acceptance-hs-cleanroom-mutations.sh
  ok  ./scripts/acceptance-hs-cleanroom.sh
  ok  ./verify.sh

$ bash scripts/session-status.sh
HEAD: da01771 (ahead 14 / behind 0)
ORIGIN: 0459a37
RED: 0/12 (acceptance-0-7.sh 제외 — CI 담당)
```

task worktree에는 ignore된 `.secret-patterns`가 없어서 첫 `acceptance-0-2`가 exit 2였고, 환경변수를
전역 주입하면 `acceptance-0-5`의 격리 clone까지 오염됐다. v6 루트의 로컬 패턴 파일을 ignore된
`.secret-patterns` symlink로 연결한 뒤 각 스크립트의 기본 경로를 보존해 최신 main 병합 후 최종
`RED: 0/12`를 얻었다.
