# goal — `make task-done`: 워크트리 폐기 전 무시된 산출물 회수 게이트

작성: 2026-08-26 · 등급 L3(SOT 수정 + 파괴적 동작 게이트) · 브랜치 `task/task-done-ignored-artifact-gate`
기준 SHA: `3094eef`

## 상위 목표 (1문장)

**워크트리를 지울 때 그 안에 남아 있던 적대검증 판정서·데이터가 경고 한 줄 없이 함께 삭제되는 일을 없앤다** —
성공 신호: `git worktree remove` 를 직접 부르지 않고 `make task-done` 을 쓰게 되며, 회수 대상이 있는 워크트리는
사람이 목록을 본 뒤에만 사라진다.

## 현재 상태 (실행으로 확인, 추측 아님)

| 사실 | 근거 |
|---|---|
| `Makefile` 이 저장소에 없다 | `git ls-files` 에 `Makefile`·`*.mk` 0건 |
| 게이트 6(종료)의 정본 명령은 수동 `git worktree remove` 다 | `docs/sot/verification-commands.md:16` 3열 |
| `make task-done` 은 "harness 가 가정하지만 이 저장소엔 없는 명령" 열에 있다 | 같은 파일 `:10` 헤더, `:16` 2열 |
| 문서가 Makefile 신설을 예정해 뒀다 | `docs/sot/verification-commands.md:90` — "명령이 바뀌면(예: `Makefile`이 나중에 생기면) 이 표를 그 시점에 다시 실행해서 갱신한다" |
| P12 가 `.gitignore` 된 산출물도 회수 범위로 규정한다 | `docs/sot/coding-principles.md:27` |
| `.harness/` 는 P12 본문에 있으나 `.gitignore` 에는 없다 | `.gitignore` 전문 대조, 0건 |
| CI 실제 스텝 수는 23인데 문서는 20이라 적혀 있다 | `grep -cE '^\s+- name:' .github/workflows/verify.yml` → `23` vs `verification-commands.md:20` |

### 실측 — `git worktree remove` 가 무엇을 막고 무엇을 안 막는가

격리 임시 저장소(`mktemp` 아래)에서 3조건 대조 실행:

| 워크트리에 남은 것 | 종료값 | 결과 |
|---|---|---|
| 추적 파일 수정 | `128` | `fatal: ... use --force` — 보호됨 |
| untracked 새 파일 | `128` | `fatal: ... use --force` — 보호됨 |
| **무시된 산출물만** | **`0`** | **메시지 0줄, 파일 삭제됨** |

→ git 이 안 막는 구멍은 **무시된 파일 하나뿐**이다. 이 게이트는 그 하나만 메운다(중복 아님 · P12).

### 실측 — 무시된 파일의 실제 구성

`git -C <wt> ls-files --others --ignored --exclude-standard` 를 등록 워크트리 전량에 적용.
(`git status --ignored` 는 디렉터리를 `!! dir/` 로 접어 개별 파일을 감춘다 — `ls-files` 를 쓴다.)

캐시·재생성 대상을 뺀 잔여의 최상위 경로별 구성:

```
.omx/state/     203   툴 세션 상태
.omx/logs/       60   툴 로그
.omx/artifacts/  15   ★ Codex·Claude 감사 판정서·프롬프트 원문 (회수 대상)
.omx/metrics.json 8
.omc/           136   툴 상태
.claude/private-reviews/ 29  ★ 적대검증 판정서 (회수 대상 · P12 명시)
.secret-patterns 13   로컬 전용 설정 (본체에 원본)
data/             1   ★ P21 데이터 (회수 대상)
humansearch/·bench/   하위 .omc/·.hypothesis/
```

**수치는 실시간으로 변한다.** 같은 HEAD 에서 40분 간격 두 번 측정에 `.omx/` 282→286,
등록 워크트리 51→52 로 드리프트했다(옆 세션이 작업 중이면 `.omx/` 가 계속 자란다).
→ **고정 수치를 계약에 박지 않는다. 실행 시점에 매번 열거한다.**

## 근본 원인

`git worktree remove` 의 안전 검사는 **git 이 아는 파일**(추적·untracked)만 본다.
무시된 파일은 정의상 git 의 관심 밖이므로 안전 검사 대상이 아니다.
그런데 이 저장소는 **판정서·데이터를 의도적으로 무시 처리**해서(P12·P21 · 유출 방지) 두고 있다.
즉 저장소 정책과 git 기본 동작이 정면으로 어긋나 있고, 그 사이에 사람이 맨손으로 서 있었다.

## 인수 기준 (AC-1, 1개)

**EARS**: 워크트리 `worktrees/<NAME>/` 에 캐시가 아닌 무시된 산출물이 남아 있는 상태에서
`make task-done NAME=<NAME>` 이 호출되면, 시스템은 **워크트리를 삭제하지 않고** 종료값 비-0 으로 끝나며
남은 경로 목록을 표준출력에 낸다.

**검증 명령**: `bash scripts/verify/run-acceptance.sh scripts/acceptance-task-done.sh`

**counter-AC (이게 없으면 가짜 RED)**:
- C1 `clean` — 무시 파일이 전혀 없는 워크트리는 **삭제되어야 한다**(exit 0, 디렉터리·등록 모두 사라짐).
- C2 `cache-only` — `.ruff_cache/`·`.venv/` 만 있는 워크트리도 **삭제되어야 한다**(exit 0).
- C3 `artifact` — `artifacts/keep.txt` 가 있으면 **삭제되지 않고** 경로가 출력된다(exit 1).

> C1 이 없으면 `Makefile` 이 아예 없어 `make` 가 실패하는 것도 "차단 성공"으로 집계된다.
> 구현 0줄 상태에서 전체가 확실히 RED 가 되려면 **정상 삭제 대조군이 반드시 있어야 한다.**
> (Codex 1차 심사 Q8 지적 — 이 지적이 없었으면 가짜 RED 를 커밋할 뻔했다.)

## 계약 (입출력 모양 먼저 · SDD)

### `scripts/task-done.sh <NAME>`

3상태 fail-closed. **종료값 0 일 때만 워크트리를 지운다.**

| 상태 | 종료값 | 조건 | 동작 |
|---|---|---|---|
| `BLOCK` | 1 | 무시 파일 중 P12·P21 명시 회수 대상이 있다 | 삭제 안 함 + 목록 출력 |
| `REVIEW` | 2 | 회수 대상은 없으나 캐시·재생성 대상도 아닌 미분류 무시 파일이 있다 | 삭제 안 함 + 목록 + 무시 출처 출력 |
| `OK` | 0 | 남은 무시 파일이 최소 캐시·재생성 대상뿐이다 | `git worktree remove` 수행 |
| `REFUSED` | 2 | 인자 위반·미등록 대상·git 명령 실패 (판정 불능) | 삭제 안 함 + 사유 출력 |

우선순위 `REFUSED > BLOCK > REVIEW > OK`.

**모든 경로에서 `STATE: <상태>` 한 줄을 반드시 낸다.** 종료값만으로는 부족하다 —
2026-08-26 RED 실행에서 실증된 함정: `Makefile` 이 없을 때 `make` 자신이 exit 2 를 내므로,
"exit 2 면 REVIEW", "비-0 이면 거부됨" 같은 종료값 기반 단언은 **구현이 0줄이어도 통과한다.**
인수 검사는 종료값 + `STATE:` 문구 + 경로 출력을 함께 요구한다.

**회수 대상 패턴(BLOCK)** — 손으로 넓히는 목록이 아니라 SOT 에서 유도한다:

| 패턴 | 근거 |
|---|---|
| `(^\|/)private-reviews/` | P12 본문 명시 |
| `(^\|/)artifacts/` | P12 본문 명시 (`.omx/artifacts/` 도 이 패턴에 걸린다) |
| `(^\|/)\.harness/` | P12 본문 명시 |
| `(^\|/)data/` | P21 (`docs/sot/coding-principles.md:36`) |

**제외 목록(최소 · 근거를 스크립트 주석에 남긴다)**:

| 제외 | 성질 | 근거 |
|---|---|---|
| `.ruff_cache/` `.mypy_cache/` `.pytest_cache/` `__pycache__/` `*.pyc` `.hypothesis/` | 순수 캐시 | 도구 재실행으로 동일 재생성. `.gitignore:44` 주석이 "G2 게이트가 만드는 로컬 산출물"로 규정 |
| `.venv/` `node_modules/` | 재생성 가능 의존성 환경 | `humansearch/uv.lock` · `pyproject.toml` 로 결정적 복원 가능 |

이 둘 **외에는 아무것도 제외하지 않는다.** `dist/`·`build/`·`.next/`·`.omc/`·`.omx/state/`·`.secret-patterns`
는 전부 REVIEW 로 간다 — "캐시라고 부를 수 없는 것을 캐시 목록에 넣는" 방향으로는 넓히지 않는다.

**출력 형식** (한 워크트리에 무시 파일이 2,528개인 사례가 실재하므로 요약한다):

```
STATE: BLOCK
BLOCKERS: 17
  .claude/private-reviews/  14개
    .claude/private-reviews/pr13-verdict.md
    ... (최대 5줄 표시)
  .omx/artifacts/            3개
REVIEW: 0
CHECKED: 1
```

### `Makefile`

```make
task-done:
	@bash scripts/task-done.sh "$(NAME)"
```

얇은 위임만 한다. 로직은 전부 `scripts/task-done.sh` 에 둔다
(Makefile 은 tab 문법·셸 이스케이프가 까다로워 검사 로직을 담기에 부적합하고, 인수 검사가 직접 호출하기도 어렵다).

**표면이 둘이고 종료값 계약이 다르다** (2026-08-26 GREEN 시도에서 실측 발견):

| 표면 | 종료값 보장 |
|---|---|
| `bash scripts/task-done.sh <NAME>` | `0` OK · `1` BLOCK · `2` REVIEW/REFUSED (3상태 정본) |
| `make task-done NAME=<NAME>` | `0` OK · **비-0** 그 외 |

GNU make 는 레시피가 실패하면 레시피의 종료값과 무관하게 **자기 종료값 2** 를 낸다
(`make: *** [task-done] Error 1` 이 떠도 `make` 자체는 2). 따라서 make 를 통해서는
BLOCK(1)과 REVIEW(2)가 구분되지 않는다. `STATE:` 문구가 두 표면 공통의 판정 표식이다.

이 사실을 몰랐다면 "make 로만 재는" 인수 검사가 종료값 계약을 아무 데서도 검증하지 않은 채
초록이 됐을 것이다. 인수 검사는 두 표면을 모두 잰다(C3·C4 는 make + 직접 호출 쌍, C5 는 직접 호출 OK).

## 결정성 규율 — 입력 영역 표 (§3 ①)

명시 입력: `NAME`. 암묵 입력: 저장소 HEAD, `.gitignore`, `.git/info/exclude`(**커밋 안 됨 — 머신마다 다름**),
등록 워크트리 목록, 파일시스템 상태, 동시 실행 중인 다른 세션.

| # | 입력 | 처리 |
|---|---|---|
| 1 | 정상 `NAME`, 등록된 `worktrees/<NAME>` | 3상태 판정 |
| 2 | `NAME` 빈 값·미지정 | 명시적 거부 exit 2 |
| 3 | `NAME` 에 `/`·`..`·절대경로 | 명시적 거부 exit 2 (경로 탈출 차단) |
| 4 | `worktrees/<NAME>` 없음 | 명시적 거부 exit 2 |
| 5 | 존재하나 등록된 워크트리가 아님(일반 디렉터리) | 명시적 거부 exit 2 |
| 6 | `worktrees/<NAME>` 가 심볼릭 링크 | 명시적 거부 exit 2 |
| 7 | `git ls-files` 가 비-0 으로 실패 | 명시적 거부 exit 2 (**빈 목록으로 강등 금지**) |
| 8 | 무시 파일 0개 | `OK` exit 0 → 삭제 |
| 9 | 캐시·재생성 대상만 | `OK` exit 0 → 삭제 |
| 10 | 회수 대상 포함 | `BLOCK` exit 1 |
| 11 | 미분류만 | `REVIEW` exit 2 |
| 12 | 판정 후 삭제 직전 새 파일 생김(경쟁) | 삭제 직전 재검사. 잔여 위험은 §비범위에 명시 |
| 13 | **그 외 전부** | **명시적 거부 exit 2** (catch-all) |

### 결정 목록 (오너 확정 완료)

| 결정 | 확정값 | 확정자 |
|---|---|---|
| 캐시/산출물 경계 | E안 3상태 | 사장님 (2026-08-26 선택) |
| `.venv`·`node_modules` | 제외(재생성 가능) | Codex Q3 → 사장님 승인 |
| `.omx/artifacts/` | BLOCK(회수 대상) | Codex V5 실측 발견 |
| REVIEW 의 종료값 | **2 (삭제 금지)** | Codex V3 — exit 0 은 "소리 내는 fail-open" 이라 P3 위반 |
| `.harness/` 를 `.gitignore` 에 추가할지 | **이번 범위 밖** | 아래 비범위 참조 |

## 작업 분해 (R1)

| WU | 내용 | 검증 |
|---|---|---|
| WU1 | RED — `scripts/acceptance-task-done.sh` (C1·C2·C3 + 인자 위반 + 무력화) | 실행 시 FAIL |
| WU2 | 구현 — `Makefile` + `scripts/task-done.sh` | WU1 GREEN |
| WU3 | 배선 — CI 스텝 + `mechanism-registry.yaml` 등록 | pre-push·CI 통과 |
| WU4 | 문서 — `verification-commands.md` 8·16행 + 스텝 수 20→24 | `check-docs-sot.sh` 통과 |

## 예외 케이스 표 (R1 ③)

| 상황 | 처리 |
|---|---|
| `mktemp` 사용 불가 | 명시적 중단(`NOT_RUN` + exit 2). 조용한 skip 금지 |
| 인수 시험 중 원본 저장소 오염 | 시작·종료 `git status --porcelain` 대조, 불일치 시 FAIL |
| 옆 세션이 동시에 워크트리 조작 | 삭제 직전 재검사. 잔여 위험 문서화 |
| `.git/info/exclude` 차이로 머신 간 결과 상이 | 인수 시험은 격리 저장소에서 자체 `.gitignore` 만 사용 |
| **그 외 전부** | **명시적 중단 + 이 표 갱신 후 재개** |

## 게이트 계획

0 시작자격(완료 · `RED 1/26`, HEAD `3094eef`) → 1 스펙(이 문서) → 2 RED 커밋 → 3 구현 →
4 검증(`run-acceptance.sh` + pre-push 전량) → 5 PR(**병합 금지**) → 6 종료

## 적대검증 정조준 (V1/V2 가 여기부터 때려라)

1. **가짜 RED** — 구현 0줄에서 C1 이 정말 실패하는가? `make` 부재 실패와 "차단 성공"이 구분되는가?
2. **fail-open** — 7·12·13행이 정말 삭제를 막는가? `ls-files` 실패를 빈 목록으로 강등하는 경로가 있는가?
3. **영구 차단** — C2 가 정말 통과하는가? 제외 목록이 좁아 정상 워크트리를 못 지우게 되지 않는가?
4. **경로 탈출** — `NAME=../../etc` · `NAME=/tmp/x` · 심볼릭 링크로 대상 밖을 지울 수 있는가?
5. **무력화 저항(P13⑥)** — `scripts/task-done.sh` 본문을 `exit 0`·`true`·no-op 으로 바꾸면 인수 검사가 빨개지는가?
   (기존 `acceptance-semantic-mutations.sh` 는 `scripts/acceptance-*.sh` 만 변이시키므로 **검사기 본체는 안 덮는다** —
   이 시험은 새 인수 스크립트가 직접 해야 한다.)
6. **자기 제외(P13④)** — 제외 패턴이 자기 자신을 검사 대상에서 빼지 않는가?
7. **0건 통과(P20)** — 검사 대상 0개가 합격으로 세어지는가?

## 비범위 / 한계

- **`.harness/` 를 `.gitignore` 에 추가하지 않는다.** P12 본문과 `.gitignore` 가 어긋나 있는 것은 사실이나,
  그건 이 AC 와 별개의 정본 정책 결정이다(`.harness` 는 현재 저장소에 존재조차 하지 않는다).
  BLOCK 패턴에는 `.harness/` 를 넣어 두어, 나중에 생기면 즉시 잡히게만 해 둔다. 부채로 남긴다.
- **`worktrees/` 밖 워크트리는 보호 범위 밖이다.** 등록 워크트리 56개 중 정규 경로는 45개,
  나머지 10개(`.claude/worktrees/`·`/private/tmp/`·`Valuehire_v6-wt-*`)는 이 명령이 다루지 않는다.
  `git-workflow.md:20` 이 정규 위치를 `worktrees/<name>/` 로 한정하므로 계약상 허용되지만,
  "전체 워크트리를 보호한다"고 주장하지 않는다.
- **판정과 삭제 사이의 경쟁 조건은 완전히 제거하지 못한다.** 삭제 직전 재검사로 창을 좁힐 뿐이다.
- 기존 `git worktree remove` 직접 호출을 금지하는 장치는 만들지 않는다(P18 의 "능력 회수"까지는 이번 범위 밖).

## 롤백 · 영향 반경 · 배포 후 관측 (L3)

- **롤백**: `Makefile`·`scripts/task-done.sh`·`scripts/acceptance-task-done.sh` 삭제 + CI 스텝·명부 항목 되돌림.
  기존 동작(수동 `git worktree remove`)은 그대로 살아 있으므로 롤백해도 기능 손실 0.
- **영향 반경**: 새 인수 스크립트가 `hooks/pre-push` glob 에 자동 편입되어 **모든 push 가 이 검사를 돈다.**
  이 검사가 느리거나 불안정하면 전 저장소 push 가 막힌다 → 인수 시험은 격리 저장소에서만 돌고 실 워크트리를 건드리지 않는다.
- **배포 후 관측**: `hooks/pre-push` 출력의 `ok scripts/acceptance-task-done.sh` 줄. 이 줄이 사라지면 검사가 빠진 것이다.

## 적대 검증 로그

(후기록 — V1·V2 판정 본문을 여기에 그대로 append 한다)
