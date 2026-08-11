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

G1 핵심 구현 `4256e3f`에는 fail-closed 스캐너 1개, deny-pattern 계약 1개, 고정 회귀 계약 7개가
있다. 최신 main `0459a37`을 merge한 배송 HEAD에서 CI는 G1 스크립트 8개를 명시 실행하고
pre-push는 같은 8개를 글로브로 회수한다.

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
| 3 최소 구현 | PASS | 일곱 RED→GREEN 쌍을 분리했고 각 RED 파일은 대응 GREEN에서 byte diff 0이다. |
| 4 검증 | PASS_LOCAL_ADVERSARIAL | G1 8개, `verify.sh`, 0-2/0-5/0-6/0-7, pre-push 12개, Fable5 PASS, Codex V2 PASS를 확인했다. |
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
- [x] 일곱 RED `257eecd`, `602a131`, `e5197cf`, `f60d95c`, `8fb7a80`, `177ec14`, `9596e63`과 대응 GREEN을 별도 커밋으로 남겼다.
- [x] 최신 main 병합 후 pre-push 실행 12개 중 G1 8개가 포함됐고 `.github/workflows/verify.yml`에도 8개가 모두 명시됐다.
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
| 실제 `git push` pre-push | hook 환경 결함 발견 | 다섯 샌드박스가 호출자 index를 덮었다. index-only 복원 뒤 RED `177ec14` → GREEN `e9f8d03`. 원격 변경 0건. |
| Fable5 hook 재공격 | 회귀 게이트 1건 발견 | 실제 `GIT_DIR` 단일 회귀를 기존 테스트가 놓쳤다. RED `9596e63` → GREEN `4256e3f`. |
| 최종 Fable5 → Codex V2 | 모두 PASS | unset 변이 6/6, routing 5/5, 주석 우회 1/1, G1/CI/SOT 8/8. |

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

### 실제 hook 결함 교정 뒤 최종 재공격

Fable5 명령:

```bash
env -u ANTHROPIC_API_KEY claude --safe-mode --no-session-persistence --permission-mode bypassPermissions --tools Read,Grep,Bash --model claude-fable-5 --effort high -p "$(sed -n '1,$p' /tmp/humansearch-g1-fable5-routing-final-prompt.txt)"
```

원문(ANSI 없음):

> ## 검증 결과 요약
>
> HEAD `4256e3f`에서 G1 게이트에 대한 최종 적대적 검증을 완료했습니다. **차단(BLOCKING)·중대(MATERIAL) 결함은 발견하지 못했습니다.** 워크트리는 읽기 전용으로 유지했고, 모든 변이 실험은 `/tmp`의 합성 임시 저장소에서 수행 후 삭제했으며, push는 하지 않았습니다.
>
> ### 1. 이전 MATERIAL 발견에 대한 재공격 — 해소 확인
>
> - **RED 파일 바이트 동일성**: `scripts/acceptance-hs-cleanroom-hook-env-mutations.sh`의 SHA-256이 RED `9596e63`, GREEN `4256e3f`, 작업트리 모두 `0fd58917…`로 동일합니다.
> - **RED 재현**: 임시 클론에서 `9596e63`을 체크아웃해 실행하니 여섯 변이 전부 `exit=0`으로 탈출하고 `FAIL: … blocked 0/6`(exit 1)이었습니다. 구버전 hook-env가 넘겨준 mutant suite root를 무시했다는 진단 그대로입니다.
> - **GREEN 수리 내용**: `scripts/acceptance-hs-cleanroom-hook-env.sh:17-25`가 suite root 인자를 실제로 소비하고(2개 이상 인자·부재 디렉터리는 exit 2), `:88-94`에서 여섯 Git 변수를 전부 scratch 저장소로 주입하며, `:99-102`에서 scratch의 index/objects/refs 전후 해시를, `:62,111-115`에서 라이브 index를 비교합니다.
>
> ### 2. 독립 변이 재검증 (변이 스크립트를 신뢰하지 않고 직접 수행)
>
> - **변수별 6종 변이**: mutation 스크립트는 첫 번째 스위트만 변이하므로, 저는 여섯 변수를 다섯 스위트에 **순환 배치**해 각각 다른 스위트에서 unset을 제거하고 실제 게이트를 호출했습니다. 6/6 전부 `rc=1`, `FAIL: hook Git environment isolated 4/5`로 빨간불이 됩니다. 즉 하니스는 첫 스위트만이 아니라 다섯 스위트 전부를 검사합니다.
> - **grep 우회형 행동 변이**: `unset` 줄에서 GIT_DIR을 빼고 말미 주석(`# GIT_DIR`)으로 정적 grep을 통과시키는 적대적 변이를 만들어도, 행동 검사(scratch 주입 실행)가 스위트 실패(exit=128)를 잡아 게이트가 `rc=1`로 떨어집니다. 정적 검사와 행동 검사가 서로의 사각을 메우는 것을 실측했습니다.
> - **linked-worktree 유사 구성의 GIT_DIR**: 합성 메인 저장소 + `git worktree add`로 만든 연결 워크트리에서 (a) `git rev-parse --git-path index`가 워크트리 전용 index(`.git/worktrees/linked/index`)를 올바르게 가리키고, (b) 훅 방식으로 GIT_DIR을 상속시킨 baseline이 5/5 PASS, (c) GIT_DIR unset 제거 변이와 행동 누출 변이 모두 `rc=1`, (d) 호출자(연결 워크트리) index가 변조되지 않음을 확인했습니다. 커밋 메시지가 주장한 "linked-worktree가 GIT_DIR로 라우팅되는" 시나리오가 실제로 커버됩니다.
>
> ### 3. G1 8개 스크립트·배선·기존 커버리지
>
> - **8/8 실행**: 워크트리에서 8개 스크립트 전부 `rc=0` — 스캐너 `PASS: forbidden runtime refs 0 / escaping symlinks 0 / CHECKED: 38`, 변이 스위트 `10/10`, 절대경로 `3/3`, 문맥 `7/7`, 콜론 `4/4`, file URL `2/2`(https·`$(pwd)` 동적 경로는 과차단하지 않음), hook-env `5/5`, unset 변이 `6/6`.
> - **CI 명시 8/8**: `.github/workflows/verify.yml`의 "HumanSearch G1 클린룸 경계" 스텝에 8개 전부 개별 `bash` 실행 줄로 존재합니다.
> - **pre-push 발견 8/8**: `hooks/pre-push`의 글로브·필터 로직을 그대로 시뮬레이션한 결과 실행 집합에 cleanroom 스크립트 8개가 모두 포함되고, 어느 것도 `PUSH-PERFORMING` 마커나 DEFERRED 제외에 걸리지 않습니다.
> - **SOT 8/8**: `docs/sot/verification-commands.md:28-35`에 8개 전부 등재.
> - **fail-closed**: 패턴 계약 부재·유효 패턴 0건 모두 `rc=2` 실측. 스캐너는 `docs/engineering/*`만 제외하고 자기 자신과 패턴 파일도 스캔하며, 패턴은 자기매칭 회피형으로 작성돼 있습니다.
> - **억제·약화 없음**: `suppressions.yaml`의 4건은 전부 G1 이전부터 있던 무관 항목(0-2 이관, CI 파싱 보증 한계 등)이고 만료 기한이 모두 미래입니다. cleanroom 스크립트에 `|| true`/`exit 0`류 약화 없음. `verify.sh` PASS, 작업트리 clean, 임시 디렉터리 전부 삭제 확인.
>
> ### 관찰 사항 (결함 아님, 조치 불요)
>
> - unset 변이 검출의 1차 경로는 정적 grep이고 일부 변수(예: `GIT_ALTERNATE_OBJECT_DIRECTORIES`)는 행동 검사만으로는 무해할 수 있으나, 요구사항인 "각 변이에서 게이트가 빨간불"은 두 경로의 합으로 6/6 충족되며, grep을 우회하는 누출도 행동 검사가 잡는 것을 실측했습니다.
>
> VERDICT: PASS

Codex 명령: `bash -n /tmp/humansearch-g1-codex-hook-final.sh && bash /tmp/humansearch-g1-codex-hook-final.sh`

원문:

```text
PASS: Codex reproduced hook mutation RED->GREEN history 1/1
PASS: Codex reproduced six-variable routing and mutations 5/5 + 6/6
PASS: Codex blocked static-check comment bypass behaviorally 1/1
PASS: Codex verified G1 execution and CI/SOT wiring 8/8
PASS: Codex final adversarial verification; worktree and live index unchanged
```

최종 Fable5와 Codex 사이 material 불일치는 0개다.

## 로컬 검증 로그

```text
$ bash scripts/acceptance-hs-cleanroom-hook-env-mutations.sh
PASS: hook environment unset mutations blocked 6/6

$ bash scripts/acceptance-hs-cleanroom-hook-env.sh
PASS: hook Git environment isolated 5/5

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
CHECKED: 38

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
pre-push: 검사 12개 실행
  ok  ./scripts/acceptance-0-6.sh
  ok  ./scripts/acceptance-hs-a3.sh
  ok  ./scripts/acceptance-hs-a4.sh
  ok  ./scripts/acceptance-hs-cleanroom-absolute-contexts.sh
  ok  ./scripts/acceptance-hs-cleanroom-absolute-paths.sh
  ok  ./scripts/acceptance-hs-cleanroom-colon-paths.sh
  ok  ./scripts/acceptance-hs-cleanroom-file-urls.sh
  ok  ./scripts/acceptance-hs-cleanroom-hook-env-mutations.sh
  ok  ./scripts/acceptance-hs-cleanroom-hook-env.sh
  ok  ./scripts/acceptance-hs-cleanroom-mutations.sh
  ok  ./scripts/acceptance-hs-cleanroom.sh
  ok  ./verify.sh

$ bash scripts/session-status.sh
HEAD: 4256e3f (ahead 19 / behind 0)
ORIGIN: 0459a37
RED: 0/14 (acceptance-0-7.sh 제외 — CI 담당)
```

task worktree에는 ignore된 `.secret-patterns`가 없어서 첫 `acceptance-0-2`가 exit 2였고, 환경변수를
전역 주입하면 `acceptance-0-5`의 격리 clone까지 오염됐다. v6 루트의 로컬 패턴 파일을 ignore된
`.secret-patterns` symlink로 연결한 뒤 각 스크립트의 기본 경로를 보존해 최신 main 병합 후 최종
`RED: 0/14`를 얻었다. 공유 객체 DB의 다른 active worktree staged index가 만든 tree는 현재 G1 변경과
무관하므로 보존했고, 최종 0-2는 현재 G1 브랜치의 no-local clean clone에서 PASS를 재확인했다.
