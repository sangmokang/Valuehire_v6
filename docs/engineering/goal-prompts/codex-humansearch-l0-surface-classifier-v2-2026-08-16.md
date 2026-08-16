# CODEX 자율 실행 프롬프트 v2 — HumanSearch L0 인증 화면 분류기

## 1층 — 결론

이 문서를 새 작업 창에 통째로 넣으면, 실행자는 먼저 필요한 앞 작업 세 개가 실제로 합쳐졌는지
확인합니다. 하나라도 준비되지 않았으면 코드를 전혀 바꾸지 않고 이유와 다음 행동만 남깁니다.

준비가 끝났으면 한 가지 작은 기능만 만듭니다. 실패하는 시험을 먼저 남기고, 그 시험을 통과시키는
최소 코드만 작성한 뒤, 일부러 코드를 한 번 망가뜨려 시험이 정말 잡는지 확인합니다. 서로 다른 두
검증자가 같은 증거에 동의하고 서버 검사까지 모두 끝나야 완료입니다.

실제 채용 사이트, 로그인, 화면 저장, 후보자 정보, 다음 라이브 단계는 절대 건드리지 않습니다.
작업 결과는 검토할 요청까지만 올리고 합치지는 않습니다.

## 2층 — 판단 근거

기존 프롬프트는 화면을 읽은 결과와 로그인 이후의 전체 실행 흐름을 한 덩어리로 섞었습니다. 그래서
다섯 개여야 할 첫 기능의 상태를 일곱 개로 늘리고, 계획에 없는 입력 이름과 우선순위까지 만들었습니다.
그대로 실행하면 틀린 설계를 정교하게 구현합니다.

이번 판은 첫 기능을 “지금 화면이 어떤 인증 표면인가”만 답하는 순수 분류기로 좁힙니다. 입력은 계약에
실제로 적힌 세 역할뿐이고, 가능한 조합을 모두 시험할 수 있습니다. 화면 역할이 서로 충돌하면 한쪽을
임의로 고르지 않고 구조 변경으로 멈춥니다.

버린 길은 세 가지입니다. 후속 실행 상태까지 한꺼번에 만드는 길은 범위가 커져 버렸고, 빈 화면 결과를
두 가지 중 골라도 된다고 두는 길은 시험의 정답을 없애 버렸으며, 앞 작업을 자동으로 합치는 길은 오너가
변경 내용을 직접 읽어야 한다는 저장소 규칙을 어깁니다.

이 선택의 대가는 첫 결과물이 실제 후보자를 찾지 않는다는 점입니다. 대신 실제 사이트에 닿기 전 가장
위험한 오인증 경로를 작고 되돌리기 쉬운 한 작업으로 봉쇄합니다. 틀렸다면 이 한 작업 요청을 합치지
않으면 끝이며, 기존 운영이나 후보자 자료에는 영향이 없습니다.

## 3층 — 실행 계약

### 0. 실행자·목표·권한

대상 실행자: 오너가 지정한 Codex `gpt-5.6-sol`, reasoning effort `xhigh`. 이것은 child agent
override가 아니라 이 자율 실행 세션 자체의 지정이다. active runtime이 이 모델과 effort를 지원하지
않으면 조용히 낮은 모델로 바꾸지 말고 변경 0으로 `BLOCKED` 보고한다.

너는 이 작업의 단일 구현 책임자다. 독립 구현 subagent에게 코드를 나누지 않는다. 이 작업은 한 인수
기준이고 RED와 GREEN의 순서를 한 실행자가 보존해야 하기 때문이다. 다른 엔진 검증은 이 문서의
Claude V1 단계에서만 수행한다.

목표는 다음 한 문장이다.

> `docs/sot/humansearch-l0-surface-contract.md`를 그대로 구현하는 순수 인증 화면 분류기를 한
> worktree, 한 branch, 한 PR로 만들고, 선행 병합·RED/GREEN·로컬 게이트·변조 시험·Claude V1·
> Codex V2·원격 CI를 모두 증명한 뒤 merge와 live 전에 멈춘다.

권한 안에 있는 작업:

- 저장소와 GitHub의 읽기 전용 상태 확인
- `task/humansearch-l0-surface-classifier` branch와 같은 이름의 worktree 생성 또는 안전한 재개
- 해당 worktree 안의 goal, test, dependency lock, 최소 product code, 다음 owner-gated prompt 변경
- task branch 일반 push와 PR 생성·갱신
- PR 검사 결과 조회

권한 밖인 작업:

- `main` 직접 수정·직접 push·merge·auto-merge·배포
- PR #13, #14, #15를 대신 merge하거나 내용을 고치는 일
- 실제 채용 포털 접속, browser/MCP 접속, 로그인, 세션, 자격증명, DOM/ARIA 캡처
- 후보자 개인정보, raw fixture, screenshot, 검색, 등록, 발송
- L2/L3/runner/C1 구현
- `--no-verify`, 검사 skip/xfail, 기대값 완화, SOT 우회

### 1. 전역 불변식

아래 열두 조건은 모든 단계에서 참이어야 한다.

1. 저장소의 추적 파일과 fresh 명령 출력만 사실로 센다. 대화 기억과 다른 worktree의 미추적 파일은
   근거가 아니다.
2. `docs/sot/`와 저장소 지시가 이 문서보다 우선한다. 충돌하면 제품 변경 0으로 중단한다.
3. 한 AC = 한 worktree = 한 branch = 한 PR이다.
4. 테스트를 구현에 맞춰 약화하지 않는다. 구현을 계약에 맞춘다.
5. RED 뒤 GREEN에서 test 파일, dependency 선언, lockfile을 바꾸지 않는다.
6. 잘못된 입력과 모순 관측은 조용히 인증 성공으로 흐르지 않는다.
7. 실행하지 못한 검사는 `NOT_RUN`이다. PASS로 바꾸지 않는다.
8. Claude의 말은 가설이다. Codex가 같은 파일과 명령으로 재현해야만 결함 또는 합격 근거다.
9. local HEAD, remote branch HEAD, PR head SHA, CI 대상 SHA가 같아야 한다.
10. 중단 뒤 재개할 때 branch/worktree/PR을 중복 생성하지 않는다.
11. 수정 가능한 범위를 벗어난 실패는 우회하지 않고 증거를 남기고 중단한다.
12. 완료 뒤에도 merge와 live를 하지 않는다.

### 2. 실행 상태기계

| 상태 | 진입 조건 | 성공 시 다음 | 실패 시 |
|---|---|---|---|
| `PREFLIGHT` | 프롬프트 시작 | `CONTRACT` | `BLOCKED` |
| `CONTRACT` | 선행 PR 세 개가 main에 병합됨 | `PLAN` | `BLOCKED` |
| `PLAN` | 정본과 worktree가 안전함 | `RED` | `BLOCKED` |
| `RED` | goal commit 완료 | `GREEN` | `BLOCKED` |
| `GREEN` | 유효한 RED commit 완료 | `LOCAL_VERIFY` | `BLOCKED` |
| `LOCAL_VERIFY` | GREEN commit 완료 | `MUTATION` | `FIX_RED` 또는 `BLOCKED` |
| `MUTATION` | targeted 검증 통과 | `CLAUDE_V1` | `FIX_RED` |
| `FIX_RED` | 실제 계약 결함 발견 | `FIX_GREEN` | `BLOCKED` |
| `FIX_GREEN` | 새 RED commit 완료 | `LOCAL_VERIFY` | `BLOCKED` |
| `CLAUDE_V1` | 모든 로컬 검증 통과 | `CODEX_V2` | `FIX_RED` 또는 `BLOCKED` |
| `CODEX_V2` | Claude 본문 확보 | `REVIEW_CHECKPOINT` | `CLAUDE_V1` 또는 `BLOCKED` |
| `REVIEW_CHECKPOINT` | V1/V2 재현 완료 | `SHIP` 또는 `FIX_RED` | `BLOCKED` |
| `SHIP` | V1/V2 합의·clean tree | `CI_WAIT` | `BLOCKED` |
| `CI_WAIT` | PR head 일치 | `HANDOFF` | `FIX_RED` 또는 `BLOCKED` |
| `HANDOFF` | 현재 PR head를 검사한 관측 CI가 모두 success | `DONE` | `BLOCKED` |

→ 이 표는 자율 실행의 프로그램 카운터다. 성공 조건 없이 다음 상태로 건너뛰지 말고, 실패 시 허용된
복구 상태만 사용한다. `BLOCKED`와 `DONE`은 둘 다 실행 종료 상태다.

최대 수정 루프는 세 번이다. 네 번째 결함이 나오면 범위가 작지 않다는 증거이므로 `BLOCKED`로 끝낸다.

### 3. `PREFLIGHT` — 변경 0인 시작 검사

처음에는 파일을 쓰지 않는다. 현재 위치가 어느 worktree인지 추측하지 말고 Git 공용 저장소와
사용 가능한 worktree를 읽는다.

다음을 순서대로 실행하고 명령과 전체 출력을 세션에 보존한다.

```bash
git rev-parse --show-toplevel
git rev-parse --git-common-dir
git worktree list --porcelain
git status --short --branch
git remote -v
git fetch origin --prune
git rev-parse origin/main
gh auth status
```

→ 저장소 위치, 기존 작업 공간, 현재 변경, 원격 갱신, GitHub 읽기 권한을 확인한다. 이 단계는 어떤
파일도 바꾸지 않는다.

중단 조건:

- Git 저장소가 아니거나 `origin`이 없다.
- fetch 또는 GitHub 조회에 필요한 권한이 없다.
- 기존 target worktree/branch가 서로 다른 commit을 가리켜 안전하게 재개할 수 없다.
- `main` worktree의 미추적 파일은 건드리지 않는다. target worktree만 clean하면 된다.

### 4. `CONTRACT` — 세 선행 PR의 실제 병합 증명

선행 PR은 #13, #14, #15다. `CLOSED`, branch 이름 존재, CI green만으로 병합을 추정하지 않는다.
각 PR에 대해 GitHub가 주는 merge commit을 읽고, 그 commit이 fresh `origin/main`의 조상인지 확인한다.
이 저장소는 squash merge를 쓰므로 원래 head commit의 ancestry를 요구하면 안 된다.

다음 읽기 전용 script로 세 번호를 모두 검사한다.

```bash
set -euo pipefail
blocked=0
for pr_number in 13 14 15; do
  pr_json="$(gh pr view "$pr_number" \
    --json number,state,baseRefName,headRefName,headRefOid,mergedAt,mergeCommit,url)"
  printf '%s\n' "$pr_json"
  pr_state="$(jq -r '.state' <<<"$pr_json")"
  base_ref="$(jq -r '.baseRefName' <<<"$pr_json")"
  merge_oid="$(jq -r '.mergeCommit.oid // empty' <<<"$pr_json")"
  if [ "$pr_state" != "MERGED" ] || [ "$base_ref" != "main" ] || [ -z "$merge_oid" ]; then
    printf 'pr=%s prerequisite=FAIL state=%s base=%s merge_oid=%s\n' \
      "$pr_number" "$pr_state" "$base_ref" "${merge_oid:-NONE}"
    blocked=1
    continue
  fi
  object_rc=0
  ancestry_rc=0
  git cat-file -e "$merge_oid^{commit}" || object_rc=$?
  git merge-base --is-ancestor "$merge_oid" origin/main || ancestry_rc=$?
  printf 'pr=%s object_rc=%s ancestry_rc=%s merge_oid=%s\n' \
    "$pr_number" "$object_rc" "$ancestry_rc" "$merge_oid"
  if [ "$object_rc" -ne 0 ] || [ "$ancestry_rc" -ne 0 ]; then
    blocked=1
  fi
done
if [ "$blocked" -ne 0 ]; then
  exit 20
fi
```

→ 세 PR의 상태·base·merge commit을 모두 출력하고, 각 merge commit이 로컬에 존재하며 현재 main에
포함됐는지 검사한다. 모두 합격이면 0, 하나라도 준비되지 않으면 이 script에서 20을 남긴다.

하나라도 `MERGED`가 아니거나 ancestry가 0이 아니면:

1. branch/worktree/product file을 만들지 않는다.
2. `## BLOCKED — 선행 병합 대기` 브리핑에 PR별 state, URL, mergeCommit, ancestry 종료값을 적는다.
3. “PR을 직접 merge하지 않았다”를 명시한다.
4. 실행을 종료한다. polling하거나 auto-merge하지 않는다.

세 개가 모두 통과하면 `origin/main`에서 아래 추적 파일을 읽는다.

```bash
git show origin/main:docs/sot/INDEX.md
git show origin/main:docs/sot/git-workflow.md
git show origin/main:docs/sot/verification-commands.md
git show origin/main:docs/sot/coding-principles.md
git show origin/main:docs/sot/hook-contracts.md
git show origin/main:docs/sot/humansearch-l0-surface-contract.md
git show origin/main:docs/engineering/humansearch-v6-clean-room-rebuild-goal-2026-08-12.md
```

→ 정본과 배경 계획이 다른 개인 작업 폴더가 아니라 현재 main에 추적됐는지 증명한다. 파일 하나라도
없으면 구현하지 않고 `BLOCKED`다.

저장소 루트와 상위 디렉터리에서 `AGENTS.md`와 `CLAUDE.md`를 찾고 적용 범위를 읽는다. 없는 파일을
있다고 가정하지 않는다. `rg --files -g 'AGENTS.md' -g 'CLAUDE.md'`의 스캔 범위를 기록한다.

### 5. 정본 계약의 기계 확인

다음 의미가 모두 존재하는지 읽기 전용 검색으로 확인한다.

- input role 정확히 세 개: `authenticated_surface`, `human_auth_surface`, `challenge_surface`
- output state 정확히 다섯 개: `UNKNOWN`, `HUMAN_AUTH`, `AUTHENTICATED`, `CHALLENGE`, `DRIFTED`
- 입력: `SurfaceObservation(matched_roles, contract_valid)`
- 공개 함수: `classify_auth_surface`
- 16개 정상 조합 전수
- `transition`, `RECHECK`, `AUTH_CONFLICT`, `RUNNING`, `STOP`은 L0 밖

다음 해석을 바꾸지 않는다.

| `contract_valid` | role 개수/종류 | 결과 |
|---|---|---|
| `False` | 어떤 부분집합이든 | `DRIFTED` |
| `True` | 0개 | `UNKNOWN` |
| `True` | 인증 role 한 개 | `AUTHENTICATED` |
| `True` | 사람 로그인 role 한 개 | `HUMAN_AUTH` |
| `True` | 확인 과제 role 한 개 | `CHALLENGE` |
| `True` | 서로 다른 role 2개 이상 | `DRIFTED` |

→ role 우선순위는 없다. 모순 관측을 한쪽 정상 상태로 축소하지 않는다. 이 표와 SOT가 다르면
중간안을 만들지 않고 `BLOCKED`다.

### 6. target worktree를 만들거나 재개

고정 이름:

- branch: `task/humansearch-l0-surface-classifier`
- worktree: 저장소 공용 루트 아래 `worktrees/humansearch-l0-surface-classifier`
- base: preflight에서 fetch한 `origin/main`

다음 분기를 지킨다.

1. worktree와 branch 둘 다 없으면 아래처럼 primary worktree의 절대 경로를 먼저 구한 뒤 만든다.

   ```bash
   PRIMARY_ROOT="$(git worktree list --porcelain | sed -n '1s/^worktree //p')"
   test -n "$PRIMARY_ROOT"
   git -C "$PRIMARY_ROOT" worktree add \
     "$PRIMARY_ROOT/worktrees/humansearch-l0-surface-classifier" \
     -b task/humansearch-l0-surface-classifier origin/main
   ```

   → 어느 worktree에서 프롬프트를 시작해도 하위 worktree 안에 다시 중첩 생성하지 않는다. primary
   root를 못 찾으면 추측 경로를 만들지 않고 `BLOCKED`다.
2. 둘 다 있으면 `git worktree list --porcelain`로 해당 branch가 해당 path에 정확히 묶였는지 확인하고
   그 worktree에서 재개한다.
3. branch만 있고 worktree가 없으면 `git log --format=fuller --decorate`와 commit별
   `git diff-tree --no-commit-id --name-only -r <SHA>`를 읽는다. 아래 §7의 phase/attempt 순서와 파일
   범위를 모든 commit이 만족하고 branch가 `origin/main`에서 갈라졌음을 증명한 경우에만 그 branch를
   worktree에 연결한다. “예상한 commit”을 사람이 추측하거나 제목만 보고 통과시키지 않는다.
4. worktree만 있거나 path/branch가 다르거나 예상 밖 commit이 있으면 자동 삭제·reset하지 않고
   `BLOCKED`다.

target worktree 진입 후 다음을 실행한다.

```bash
git status --short --branch
git rev-parse HEAD
git rev-parse origin/main
session_status_rc=0
session_status_out="$(bash scripts/session-status.sh 2>&1)" || session_status_rc=$?
printf '%s\n' "$session_status_out"
red_line="$(printf '%s\n' "$session_status_out" | sed -n '/^RED: /p')"
red_line_count="$(printf '%s\n' "$red_line" | sed '/^$/d' | wc -l | tr -d ' ')"
if [ "$session_status_rc" -ne 0 ] || [ "$red_line_count" -ne 1 ] ||
   ! printf '%s\n' "$red_line" |
     grep -Eq '^RED: 0/[1-9][0-9]* \(acceptance-0-7\.sh 제외 — CI 담당\)$'; then
  printf 'BLOCKED: Gate 0 failed rc=%s red=%s\n' \
    "$session_status_rc" "${red_line:-MISSING}"
  exit 23
fi
```

→ 새 작업이면 HEAD와 `origin/main`이 같고 변경 0이어야 한다. 시작 검사도 끝까지 실행해 실패가 정확히
0건인지 읽는다. 실행 불가, 출력 누락, 실패 1건 이상은 모두 23으로 중단한다. `.secret-patterns`를 다른
worktree에서 복사하거나 회수 가능한 Git 객체를 자동 삭제해 이 관문을 억지로 통과시키지 않는다.
재개라면 아래 checkpoint 규칙으로 이미 끝난 단계와 변경의 소유권을 증명해야 한다.

### 7. 재개와 checkpoint 규칙

진행 상태는 임시 파일이 아니라 Git commit과 구현 goal 문서로 판단한다.

- `git log --format=fuller --decorate origin/main..HEAD`를 읽는다.
- open PR은 `gh pr list --head task/humansearch-l0-surface-classifier --state open`으로 찾는다.
- 아래 phase trailer가 있는 commit만 공식 checkpoint다:
  `Phase: PLAN|RED|GREEN|REVIEW|EVIDENCE`.
- 순서는 PLAN 한 개 → attempt별 RED/GREEN/REVIEW → 그 attempt의 EVIDENCE다. PLAN을 뺀 각 attempt
  phase commit에는
  `Attempt: N`이 있고 N은 1부터 빈틈없이 증가한다. 한 attempt는 RED→GREEN→REVIEW이며 REVIEW가
  실제 결함을 확정하면 EVIDENCE 없이 다음 attempt의 RED로 간다.
- REVIEW가 통과한 attempt만 EVIDENCE를 한 개 만들 수 있다. 원격 CI에서 code 결함이 뒤늦게 발견되면
  그 EVIDENCE는 지우거나 고치지 않고 다음 attempt의 RED/GREEN/REVIEW/EVIDENCE를 새로 만든다. 최종
  HEAD의 공식 완료점은 가장 큰 attempt 번호의 EVIDENCE다.
- 초기 구현은 `Attempt: 1`, `Fix-for: INITIAL_CONTRACT`다. 후속 attempt는 `Fix-for:`에 Claude/Codex
  finding ID 또는 local 검증 ID를 넣는다. 같은 attempt/phase가 둘 이상이거나 순서가 깨지면
  `BLOCKED`다.
- working tree가 dirty면 diff가 현재 공식 phase의 예상 파일에만 있는지 확인한다. 소유권을 증명하지
  못하면 덮어쓰거나 버리지 않고 `BLOCKED`다.
- 이미 open PR이 있으면 새 PR을 만들지 않고 그 번호를 재사용한다.
- remote branch가 있으면 force push하지 않는다. fast-forward 일반 push만 허용한다.

phase별 허용 파일 범위도 checkpoint 계약의 일부다.

| Phase | 허용 파일 |
|---|---|
| `PLAN` | 날짜가 확정된 구현 goal 한 파일 |
| `RED` | `humansearch/tests/test_auth_surface.py`, `humansearch/pyproject.toml`, `humansearch/uv.lock` 중 현재 attempt에 필요한 파일만 |
| `GREEN` | `humansearch/src/humansearch/auth_surface.py`, `humansearch/src/humansearch/__init__.py` 중 현재 finding에 필요한 파일만 |
| `REVIEW` | 구현 goal 한 파일 |
| `EVIDENCE` | 구현 goal 한 파일과 고정 경로의 owner-gated next prompt 한 파일 |

→ branch만 남은 재개에서도 commit 순서뿐 아니라 실제 파일 범위를 대조한다. 범위 밖 파일, 알 수 없는
phase, 빠진 `Attempt:`/`Fix-for:`, 같은 phase 중복이 하나라도 있으면 연결하지 않고 `BLOCKED`다.

PLAN commit 뒤부터 EVIDENCE commit 직전까지의 허용된 미커밋 변경은 **공식 evidence buffer**다.
RED 실행, GREEN 검증, mutation, Claude V1, Codex V2의 명령과 출력을 구현 goal에 순서대로 append한다.
활성 RED/GREEN 편집이 없을 때 REVIEW commit 전에는 goal 정확히 한 파일만 dirty여야 한다. RED 중에는
goal과 현재 attempt의 RED 허용 파일만, GREEN 중에는 goal과 현재 attempt의 GREEN 허용 파일만 dirty일
수 있다. 구현 goal에는 편집 전에 `Attempt:`와 `Fix-for:`가 있는 open phase 표식을 먼저 append한다.
표식 없이 부분 파일이 dirty거나, RED와 GREEN 범위가 섞이거나, 표식의 attempt·phase와 다른 파일이
dirty면 `BLOCKED`다. REVIEW commit 뒤에는 goal과 §17의 고정 경로 owner-gated next prompt, 정확히 두
파일까지만 dirty일 수 있다.

- 재개 시 buffer를 버리거나 되돌리지 않는다.
- 마지막으로 닫힌 제목, 명령 블록, 출력 블록, `→` 해석까지 읽어 다음 미실행 단계만 이어간다.
- 닫히지 않은 block, 명령만 있고 출력이 없는 항목, 서로 다른 attempt 로그 혼합이 있으면 추측해서
  완성하지 않고 `BLOCKED`다.
- 각 checkpoint commit 뒤에 새로 append한 buffer는 해당 worktree에만 있으므로 다음 checkpoint 전에는
  원격 보존됐다고 주장하지 않는다.
- buffer가 사라졌으면 실행하지 않은 출력을 재구성하지 않는다. 마지막 commit checkpoint부터 fresh
  명령을 다시 실행해 새 증거를 만든다.

### 8. `PLAN` — 코드보다 goal 문서를 먼저 고정

날짜는 실행일의 서울 날짜를 사용하고 다음 파일을 먼저 만든다.

`docs/engineering/humansearch-l0-surface-classifier-goal-<YYYY-MM-DD>.md`

반드시 포함할 내용:

1. 1층 결론, 2층 판단 근거, 3층 증거
2. current HEAD, `origin/main`, 선행 PR 세 개의 merge 증거
3. 기존 구현 검색 범위와 결과
4. 근본 원인: 화면 분류와 run lifecycle 혼합
5. AC-L0-1~5와 counter-AC
6. Harness Gate 0~6
7. 정조준 적대검증 항목
8. 실제로 읽은 SOT 경로
9. 비범위와 live `NOT_RUN` 사유
10. RED/GREEN/변조/V1/V2/CI 전체 로그를 append할 빈 절

기존 구현을 먼저 찾는다.

```bash
rg -n "AuthSurfaceState|SurfaceObservation|classify_auth_surface|authenticated_surface|HUMAN_AUTH" \
  humansearch docs scripts .github
git log --all --oneline -- humansearch/src/humansearch humansearch/tests
```

→ 이미 있는 기능과 단순 문서 언급을 구분한다. 제품 구현이 없다는 결론도 검색 범위와 전체 출력이
있어야 한다.

goal 파일만 stage하고 diff를 확인한 뒤 PLAN commit을 만든다. 커밋 메시지는 Lore 형식을 따른다.

```text
L0 구현의 판정 경계를 코드보다 먼저 고정한다

Constraint: 인증 화면 분류만 허용하고 run lifecycle과 live portal은 범위 밖이다
Rejected: 7-state 통합 상태기계 | L0와 L2/L3 책임을 다시 섞는다
Confidence: high
Scope-risk: narrow
Directive: RED 이전에 이 goal과 HumanSearch L0 SOT의 불일치를 해결하라
Tested: 선행 PR merge commit ancestry와 SOT 추적 여부를 확인했다
Not-tested: 제품 동작은 아직 RED 전이라 NOT_RUN이다
Phase: PLAN
```

→ 이 commit은 구현 전에 계약과 증거 저장소를 고정한다. intent line은 “무엇을 추가했다”가 아니라
“왜 이 경계를 먼저 고정하는가”를 말한다.

### 9. `RED` — 시험과 시험 의존성만 먼저 commit

먼저 현재 package와 gate가 실제로 존재하는지 읽는다.

```bash
sed -n '1,220p' humansearch/pyproject.toml
sed -n '1,240p' scripts/acceptance-hs-gates.sh
sed -n '1,240p' scripts/acceptance-hs-portal-constants.sh
find humansearch/src humansearch/tests -maxdepth 5 -type f -print | sort
```

→ test runner, lint, typecheck, package 경계, 금지 상수 검사가 새 파일을 실제로 덮는지 확인한다.

`humansearch/pyproject.toml`의 dev dependency에 Hypothesis를 추가하고 `uv lock --project humansearch`로
lockfile을 갱신한다. 기존 dependency를 삭제하거나 버전을 낮추지 않는다.

`humansearch/tests/test_auth_surface.py` 하나를 만들고 제품 모듈을 runtime import한다. RED에서 제품
모듈을 파일 최상단에서 import하면 수집 자체가 중단되므로 금지한다. 대신 각 test 본문이 호출하는
`load_subject()` helper 안에서 `humansearch.auth_surface`를 import한다. 매개변수와 Hypothesis 전략은
제품 enum을 import하기 전에도 만들 수 있는 role member-name 문자열을 쓰고, test 실행 중
`load_subject()` 뒤 enum으로 바꾼다. 따라서 collect-only는 정확히 25개를 정상 수집하고 실제 test
실행은 각 test의 `load_subject()`에서 제품 모듈 부재로 실패해야 한다. 정확한 test shape:

- 결정표 16개를 매개변수화한 test 16개
- invalid input 매개변수 4개
  - observation 객체가 아님
  - `matched_roles`가 `frozenset`이 아님
  - `contract_valid`가 실제 bool이 아님
  - enum이 아닌 raw string role
- Hypothesis property test 5개
  - 모든 정상 입력은 다섯 enum 중 하나
  - invalid contract는 항상 `DRIFTED`
  - valid+empty는 항상 `UNKNOWN`
  - valid+role 2개 이상은 항상 `DRIFTED`
  - 같은 관측 두 번은 같은 결과

target file 하나를 수집하면 정확히 25개 test가 보여야 한다. 숫자가 다르면 이유를 설명하고 계약과
동일한 보장인지 확인하기 전에는 진행하지 않는다.

RED에서 기대하는 실패는 `humansearch.auth_surface` 기능이 아직 없기 때문이어야 한다. test syntax,
wrong cwd, dependency install, test collection 0, import path 오염 때문에 실패하면 RED가 아니라 환경
결함이다.

실행 순서:

```bash
uv sync --project humansearch
(cd humansearch && uv run pytest --collect-only -q tests/test_auth_surface.py)
(cd humansearch && uv run pytest -q tests/test_auth_surface.py)
```

→ 첫 명령은 Hypothesis를 실제 환경에 설치한다. 둘째는 25개 수집을 증명한다. 셋째는 기능 부재라는
올바른 이유로 0이 아닌 종료 성적을 내야 한다.

전체 stdout/stderr와 종료값을 goal의 RED 로그에 넣고 바로 아래 `→` 해석을 붙인다. 테스트,
`pyproject.toml`, `uv.lock`만 stage한다. 제품 source와 `__init__.py`는 stage에 있으면 안 된다.

RED commit 메시지:

```text
L0 계약을 구현 전에 실패하는 시험으로 잠근다

Constraint: 세 role과 contract validity의 16개 정상 조합을 전수 고정한다
Rejected: 구현과 시험 동시 commit | GREEN이 기대값을 바꿔도 숨길 수 있다
Confidence: high
Scope-risk: narrow
Directive: GREEN commit에서 test_auth_surface.py와 dependency lock을 바꾸지 마라
Tested: 25 tests collected; targeted test failed because auth_surface implementation is absent
Not-tested: 제품 구현은 의도적으로 아직 존재하지 않는다
Phase: RED
Attempt: 1
Fix-for: INITIAL_CONTRACT
```

→ RED commit은 실패를 보존하는 정상 checkpoint다. 실패 원인이 문법이나 환경이면 이 commit을 만들지
않는다.

### 10. `GREEN` — 최소 구현과 export만 commit

구현 파일은 `humansearch/src/humansearch/auth_surface.py` 하나다. 다음 구조를 벗어나지 않는다.

- `SurfaceRole(str, Enum)`: 정확히 세 값
- `AuthSurfaceState(str, Enum)`: 정확히 다섯 값
- `@dataclass(frozen=True, slots=True) SurfaceObservation`
- `InvalidObservation(ValueError)`
- single-role mapping 한 개
- `_validate_observation` 한 개
- `classify_auth_surface` 한 개

분류 알고리즘은 다음 순서다.

1. observation 객체와 각 필드의 runtime type을 검증한다.
2. `contract_valid is False`면 `DRIFTED`.
3. role 0개면 `UNKNOWN`.
4. role 2개 이상이면 `DRIFTED`.
5. role 1개면 mapping으로 세 정상 상태 중 하나를 반환한다.

금지:

- `transition`, `current state`, `decide_role`, `is_terminal`, priority list
- `RECHECK`, `AUTH_CONFLICT`, `RUNNING`, `STOP`, `structure_drift`, `human_login_done`
- portal명, URL, CSS, XPath, DOM API, 화면 문구
- file/network/env/time/random I/O
- catch 후 기본값, unknown input을 `UNKNOWN`으로 삼키기
- 새 acceptance script 또는 CI workflow 변경

`humansearch/src/humansearch/__init__.py`에서는 기존 `PACKAGE_NAME`을 보존하고 공개 API 다섯 이름만
export한다. test, dependency, lockfile은 수정하지 않는다.

다음을 실행한다.

```bash
git diff -- humansearch/tests humansearch/pyproject.toml humansearch/uv.lock
(cd humansearch && uv run pytest -q tests/test_auth_surface.py)
(cd humansearch && uv run ruff check src tests)
(cd humansearch && uv run mypy --strict src tests)
```

→ 첫 출력은 RED 이후 시험과 dependency가 불변인지 증명해야 하므로 비어 있어야 한다. 나머지는
targeted behavior, lint, strict typecheck를 순서대로 확인한다.

GREEN commit은 source module과 `__init__.py`만 포함한다.

```text
모순된 인증 화면을 성공으로 오인하지 않게 한다

Constraint: L0는 화면 분류만 소유하고 temporal transition은 후속 계층이 소유한다
Rejected: 위험 role 우선순위 | 상충 관측을 정상 상태 하나로 축소한다
Confidence: high
Scope-risk: narrow
Directive: RECHECK/RUNNING/STOP/AUTH_CONFLICT를 이 enum에 추가하지 마라
Tested: targeted 25 tests, ruff, mypy passed without changing RED expectations
Not-tested: live portal and runner wiring are intentionally out of scope
Phase: GREEN
Attempt: 1
Fix-for: INITIAL_CONTRACT
```

→ GREEN은 RED의 정답을 건드리지 않고 최소 code만 통과시킨 checkpoint다.

### 11. `LOCAL_VERIFY` — 작은 검사부터 저장소 게이트까지

각 명령은 앞 명령이 0일 때만 다음으로 간다. 출력과 case/file 수를 goal에 전부 기록한다.

```bash
(cd humansearch && uv run pytest -q tests/test_auth_surface.py)
(cd humansearch && uv run pytest -q tests)
(cd humansearch && uv run ruff check src tests)
(cd humansearch && uv run mypy --strict src tests)
bash scripts/acceptance-hs-gates.sh
bash scripts/acceptance-hs-gates-mutations.sh
bash scripts/acceptance-hs-gates-antiforge.sh
g3_scripts="$(find scripts -maxdepth 1 -type f \
  -name 'acceptance-hs-portal-constants*.sh' -print | sort)"
printf '%s\n' "$g3_scripts"
g3_count="$(printf '%s\n' "$g3_scripts" | sed '/^$/d' | wc -l | tr -d ' ')"
if [ "$g3_count" -lt 2 ]; then
  exit 21
fi
while IFS= read -r g3_script; do
  test -n "$g3_script" || continue
  bash "$g3_script"
done <<<"$g3_scripts"
bash verify.sh
git diff --check origin/main...HEAD
CURRENT_ATTEMPT="$(
  git log --format='%(trailers:key=Attempt,valueonly)' origin/main..HEAD |
    sed '/^$/d' | sort -n | tail -1
)"
test -n "$CURRENT_ATTEMPT"
RED_SHA="$(
  git rev-list --reverse origin/main..HEAD | while IFS= read -r sha; do
    phase="$(git show -s --format='%(trailers:key=Phase,valueonly)' "$sha")"
    attempt="$(git show -s --format='%(trailers:key=Attempt,valueonly)' "$sha")"
    if [ "$phase" = RED ] && [ "$attempt" = "$CURRENT_ATTEMPT" ]; then
      printf '%s\n' "$sha"
    fi
  done
)"
red_count="$(printf '%s\n' "$RED_SHA" | sed '/^$/d' | wc -l | tr -d ' ')"
if [ "$red_count" -ne 1 ]; then
  exit 22
fi
git diff --exit-code "$RED_SHA"..HEAD -- \
  humansearch/tests humansearch/pyproject.toml humansearch/uv.lock
git diff --exit-code -- humansearch
git status --short
```

→ 앞 네 명령은 기능·회귀·형식·타입을 확인한다. 다음 세 명령은 시험이 가짜가 아닌지 확인한다.
그 뒤 이름 규칙에 맞는 G3 화면 경계 검사 전부를 목록으로 출력하고 실행하며, 두 개 미만이면 21로
실패한다. `verify.sh`는 저장소 비밀 검사를 수행한다. 마지막 셋은 공백 결함, RED 불변, 예상 밖
working change를 잡는다.

`CURRENT_ATTEMPT`는 가장 큰 attempt trailer이고, `RED_SHA`는 그 attempt에서 `Phase: RED`인 commit
정확히 한 개다. 0개나 2개 이상이면 22로 실패한다. 첫 diff는 현재 RED 뒤 시험과 dependency가
변하지 않았는지, 둘째 diff는 mutation 전에 제품 경로가 clean인지 증명한다.
`git status --short`에는 append 중인 구현 goal 한 파일만 남을 수 있다. 그 밖의 변경이 있으면
mutation을 시작하지 않는다. 하나라도 실패하면 원인을 다음처럼 분류한다.

- 기존/infra 실패: 이번 diff와 무관함을 명령으로 재현하고 `BLOCKED`.
- 계약을 구현하지 못한 실패: `FIX_RED`.
- 검사 자체가 새 source를 덮지 않는 실패: 이번 AC에서 검사 강화를 추가하지 말고 `BLOCKED` 후 별도
  AC를 제안한다.
- test를 약화해야만 통과하는 실패: `BLOCKED`.

### 12. `MUTATION` — 검사가 실제 결함을 잡는지 한 번 파괴

제품·시험 경로가 clean이고 구현 goal만 evidence append로 변경됐는지 먼저 확인한다.
`classify_auth_surface`의 “유효한 단일 인증 role → AUTHENTICATED” 한 줄만 `UNKNOWN`으로 임시
변경한다. `apply_patch`로 바꾸고 원래 줄을 별도 기록한다.

```bash
(cd humansearch && uv run pytest -q tests/test_auth_surface.py)
```

→ 종료 성적은 0이 아니어야 하고, 실패 test가 인증 단일 role 계약을 직접 가리켜야 한다. 다른 이유로
실패하면 mutation 증거가 아니다.

즉시 `apply_patch`로 원래 한 줄을 복구한다. `git checkout --`, `git reset`, stash로 복구하지 않는다.
그 뒤 같은 targeted test가 통과하고 `git diff --exit-code -- humansearch`가 clean인지 확인한다.
`git status --short`에는 mutation 전부터 append하던 구현 goal 한 파일만 남아야 한다.

mutation 실패 출력, 복구 후 PASS 출력, clean readback을 goal에 기록한다. 임시 잘못된 코드는 commit,
push, stash 어디에도 남기지 않는다.

### 13. `FIX_RED` / `FIX_GREEN` — 결함 수정 규칙

계약 결함을 발견하면 바로 source부터 고치지 않는다.

1. 직전 REVIEW commit이 finding과 재현 증거를 goal에 보존했고 working tree가 clean인지 확인한다.
2. attempt 번호를 하나 올린다.
3. 아직 없는 보장을 재현하는 test만 추가하고 실행해 올바른 이유로 실패시킨다.
4. 그 test 변경만 새 RED commit으로 만든다. `Attempt: N`과 `Fix-for: <finding ID>`를 붙이고 기대값
   삭제·완화는 금지한다.
5. 별도 GREEN commit에서 최소 source만 고친다. 같은 attempt와 finding ID를 붙인다.
6. `LOCAL_VERIFY`부터 다시 전부 실행한다.
7. goal에 발견자, 재현 명령, 실패 출력, RED SHA, GREEN SHA를 append한다.

세 번의 fix loop를 넘으면 `BLOCKED`다. 범위를 확장하거나 설계를 다시 만들지 않는다.

### 14. `CLAUDE_V1` — 다른 엔진의 1차 적대검증

모든 local 검증과 mutation이 끝난 뒤 실행한다. Claude는 target worktree가 아니라 현재 commit을 복제한
일회용 local clone에서만 명령을 실행한다. target의 구현 goal evidence buffer는 그 clone에 복사해
읽게 하되, target 절대 경로는 Claude prompt에 넣지 않는다. API key를 환경에서 제거해야 한다.

아래 `<GOAL_PATH>`는 이번 구현 goal 실제 경로로 바꾼다. 명령 전문을 goal에 먼저 기록하고 실행 후
Claude 출력 본문을 한 글자도 요약하지 않고 같은 파일의 `## 적대 검증 로그`에 넣는다.

```bash
TARGET_ROOT="$(git rev-parse --show-toplevel)"
TARGET_HEAD_BEFORE="$(git rev-parse HEAD)"
TARGET_ORIGIN_MAIN_BEFORE="$(git rev-parse origin/main)"
TARGET_STATUS_BEFORE="$(git status --porcelain=v1 --untracked-files=all)"
TARGET_REFS_BEFORE="$(git show-ref | LC_ALL=C sort | shasum -a 256 | awk '{print $1}')"
AUDIT_BASE="${TMPDIR:-/tmp}"
AUDIT_BASE="${AUDIT_BASE%/}"
AUDIT_PARENT="$(mktemp -d "$AUDIT_BASE/humansearch-l0-v1.XXXXXX")"
AUDIT_REPO="$AUDIT_PARENT/repo"
cleanup_v1_copy() {
  case "$AUDIT_PARENT" in
    "$AUDIT_BASE"/humansearch-l0-v1.*)
      test -d "$AUDIT_PARENT" && rm -rf -- "$AUDIT_PARENT"
      ;;
    *)
      printf 'BLOCKED: unsafe audit temp path: %s\n' "$AUDIT_PARENT" >&2
      return 1
      ;;
  esac
}
trap cleanup_v1_copy EXIT
trap 'cleanup_v1_copy; trap - EXIT; exit 129' HUP
trap 'cleanup_v1_copy; trap - EXIT; exit 130' INT
trap 'cleanup_v1_copy; trap - EXIT; exit 143' TERM
git clone --quiet --no-local --no-hardlinks "$TARGET_ROOT" "$AUDIT_REPO"
git -C "$AUDIT_REPO" checkout --quiet --detach "$TARGET_HEAD_BEFORE"
git -C "$AUDIT_REPO" update-ref refs/remotes/origin/main "$TARGET_ORIGIN_MAIN_BEFORE"
cp "$TARGET_ROOT/<GOAL_PATH>" "$AUDIT_REPO/<GOAL_PATH>"
mkdir -p "$AUDIT_REPO/.uv-cache" "$AUDIT_REPO/.audit-tmp" "$AUDIT_REPO/.audit-home"
EXPECTED_PORTAL_SCRIPTS='scripts/acceptance-hs-portal-constants-hardening.sh
scripts/acceptance-hs-portal-constants-hardening2.sh
scripts/acceptance-hs-portal-constants-hardening3.sh
scripts/acceptance-hs-portal-constants-hardening4.sh
scripts/acceptance-hs-portal-constants-hardening5.sh
scripts/acceptance-hs-portal-constants-hardening6.sh
scripts/acceptance-hs-portal-constants-mutations.sh
scripts/acceptance-hs-portal-constants.sh'
ACTUAL_PORTAL_SCRIPTS="$(
  cd "$AUDIT_REPO" &&
  find scripts -maxdepth 1 -type f -name 'acceptance-hs-portal-constants*.sh' -print |
    LC_ALL=C sort
)"
if [ "$(git -C "$AUDIT_REPO" rev-parse origin/main)" != "$TARGET_ORIGIN_MAIN_BEFORE" ] ||
   [ "$ACTUAL_PORTAL_SCRIPTS" != "$EXPECTED_PORTAL_SCRIPTS" ] ||
   ! (cd "$AUDIT_REPO" && uv sync --project humansearch --frozen); then
  printf '%s\n' 'BLOCKED: Claude V1 격리 검사 준비 실패'
  exit 27
fi

claude_rc=0
CLAUDE_OUTPUT="$(
  (
  cd "$AUDIT_REPO" &&
  env -u ANTHROPIC_API_KEY GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_SYSTEM=/dev/null \
    TMPDIR="$AUDIT_REPO/.audit-tmp" \
    UV_NO_CONFIG=1 UV_OFFLINE=1 UV_CACHE_DIR="$AUDIT_REPO/.uv-cache" \
    claude --safe-mode --no-session-persistence \
    --settings '{"sandbox":{"enabled":true,"failIfUnavailable":true,"autoAllowBashIfSandboxed":false,"allowUnsandboxedCommands":false,"filesystem":{"denyRead":["~/"],"allowRead":["."]},"network":{"allowedDomains":[]}}}' \
    --permission-mode dontAsk --tools Read,Grep,Bash \
    --allowedTools 'Read(./**)' Grep \
      'Bash(git status --short)' \
      'Bash(git rev-parse HEAD)' \
      'Bash(git rev-parse origin/main)' \
      'Bash(git log --format=fuller --decorate origin/main..HEAD)' \
      'Bash(git diff --name-status --no-renames --no-ext-diff origin/main...HEAD -- .)' \
      'Bash(git diff --no-ext-diff --no-textconv origin/main...HEAD -- humansearch/src/humansearch/auth_surface.py humansearch/src/humansearch/__init__.py humansearch/tests/test_auth_surface.py humansearch/pyproject.toml humansearch/uv.lock <GOAL_PATH>)' \
      'Bash(git ls-files -- humansearch/src/humansearch/auth_surface.py humansearch/src/humansearch/__init__.py humansearch/tests/test_auth_surface.py humansearch/pyproject.toml humansearch/uv.lock <GOAL_PATH>)' \
      'Bash(bash scripts/humansearch-l0-claude-audit.sh pytest-auth)' \
      'Bash(bash scripts/humansearch-l0-claude-audit.sh pytest-all)' \
      'Bash(bash scripts/humansearch-l0-claude-audit.sh ruff)' \
      'Bash(bash scripts/humansearch-l0-claude-audit.sh mypy)' \
      'Bash(bash scripts/humansearch-l0-claude-audit.sh gates)' \
      'Bash(bash scripts/humansearch-l0-claude-audit.sh gates-mutations)' \
      'Bash(bash scripts/humansearch-l0-claude-audit.sh gates-antiforge)' \
      'Bash(bash scripts/humansearch-l0-claude-audit.sh portal)' \
      'Bash(bash scripts/humansearch-l0-claude-audit.sh portal-mutations)' \
      'Bash(bash scripts/humansearch-l0-claude-audit.sh portal-hardening)' \
      'Bash(bash scripts/humansearch-l0-claude-audit.sh portal-hardening2)' \
      'Bash(bash scripts/humansearch-l0-claude-audit.sh portal-hardening3)' \
      'Bash(bash scripts/humansearch-l0-claude-audit.sh portal-hardening4)' \
      'Bash(bash scripts/humansearch-l0-claude-audit.sh portal-hardening5)' \
      'Bash(bash scripts/humansearch-l0-claude-audit.sh portal-hardening6)' \
    --disallowedTools Edit Write NotebookEdit \
      'Read(../**)' \
      'Bash(git add *)' 'Bash(git commit *)' 'Bash(git push *)' \
      'Bash(git checkout *)' 'Bash(git switch *)' 'Bash(git reset *)' \
      'Bash(git clean *)' 'Bash(git restore *)' 'Bash(git fetch *)' \
      'Bash(git pull *)' 'Bash(git merge *)' 'Bash(git rebase *)' \
      'Bash(git update-ref *)' 'Bash(gh *)' 'Bash(curl *)' \
      'Bash(rm *)' 'Bash(mv *)' 'Bash(cp *)' 'Bash(tee *)' \
      'Bash(touch *)' 'Bash(mkdir *)' 'Bash(sed -i *)' \
      'Bash(python *)' 'Bash(node *)' 'Bash(perl *)' \
    -p \
    '당신은 구현자가 아닌 독립 적대검증자입니다. 현재 디렉터리는 버릴 수 있는 local clone입니다. Git 조회와 test는 적힌 exact 명령만 쓰십시오. Bash는 Claude native sandbox 안에서 실행되며 network와 clone 밖 쓰기가 금지되고 unsandboxed escape도 닫혀 있습니다. test가 clone 안에 cache와 임시 파일을 만들 수는 있지만 원본 worktree·Git ref·원격·GitHub 상태는 바꾸지 마십시오. 저장소 현재 branch의 docs/sot/humansearch-l0-surface-contract.md, <GOAL_PATH>, humansearch/src/humansearch/auth_surface.py, humansearch/src/humansearch/__init__.py, humansearch/tests/test_auth_surface.py, humansearch/pyproject.toml, humansearch/uv.lock을 읽으십시오. 먼저 고정된 `git diff --name-status --no-renames --no-ext-diff origin/main...HEAD -- .`로 저장소 전체 변경 경로를 확인하고, 그 뒤 고정 파일의 상세 diff를 읽으십시오. 구현자의 요약을 믿지 말고 명령을 직접 실행하십시오. 16개 정상 조합의 완전성, invalid input fail-closed, 정확히 5 states/3 roles, L2/L3 상태 누출 0, RED 뒤 test 불변, Hypothesis가 실제 수집되는지, runtime import, 기존 G2/G3 gate가 새 파일을 덮는지, mutation 증거가 타당한지, 고아 export인지, 금지 I/O/portal literal인지, goal의 명령·출력 과장 여부를 공격하십시오. 모든 finding은 file:line과 재현 명령/전체 출력으로 증명하십시오. 실행하지 못한 것은 NOT_RUN입니다. 마지막 판정은 PASS 또는 FAIL입니다.

[출력 형식 — 반드시 지킬 것]
읽는 사람은 기술 배경이 없는 사업 책임자다. 판정 내용은 절대 축소하지 말고, 표현만 풀어 써라.
1) 문서 맨 앞에 "결론". 결정할 사항 1개당 1~2문장, 전체 분량 상한 없음. 전문용어는 풀어 쓰더라도 결론에서는 쓰지 마라.
2) 그다음 "판단 근거": 왜 그렇게 봤는지, 갈림길에서 왜 이 해석을 골랐는지, 버린 해석은 왜 버렸는지, 이 판정이 틀리면 무엇이 깨지는지.
3) 그다음부터 기술 상세·명령·출력·file:line 전문. 증거는 하나도 생략하지 마라.
- 전문용어는 첫 등장 문장 안에서 괄호로 풀어 써라. 뒤에 몰아 쓴 용어집은 무효다.
- 터미널 출력·코드 블록·표를 붙였으면 바로 아래에 "→ 뭘 시켰나 / 뭐가 나왔나 / 좋은 소식인가 나쁜 소식인가" 1~3줄을 달아라.
- 첫 줄에 VERDICT: PASS|FAIL 한 줄을 두어라. 그 한 줄은 결론의 일부가 아니라 기계가 읽는 표식이므로 결론 제목 앞에 온다.
- file:line 을 인용하면 그 줄이 무슨 일을 하는 줄인지 한 마디 덧붙여라.
- 결함마다 심각도 라벨을 붙이고, 그 옆에 그대로 두면 사업/운영에 무슨 일이 생기는지 한 문장으로 덧붙여라(라벨을 지우지 마라).
- 설계 결정을 지적할 때는 "무엇을 / 왜 / 버린 대안 / 대가 / 되돌리는 법" 5줄로 적어라.
- 이번에 건너뛴 것·확인하지 못한 것·중간에 실패해서 다시 한 것을 판정 앞부분에 명시해라.
- 추정과 확인된 사실을 구분 표시해라(확인 못 한 것은 ※).
- 한국어 존칭체. 초등학생용 비유는 쓰지 마라 — 성인 의사결정자 수준으로 써라.'
  ) 2>&1
)" || claude_rc=$?
printf '%s\n' "$CLAUDE_OUTPUT"

TARGET_HEAD_AFTER="$(git -C "$TARGET_ROOT" rev-parse HEAD)"
TARGET_STATUS_AFTER="$(git -C "$TARGET_ROOT" status --porcelain=v1 --untracked-files=all)"
TARGET_REFS_AFTER="$(git -C "$TARGET_ROOT" show-ref | LC_ALL=C sort | shasum -a 256 | awk '{print $1}')"
if [ "$TARGET_HEAD_BEFORE" != "$TARGET_HEAD_AFTER" ] ||
   [ "$TARGET_STATUS_BEFORE" != "$TARGET_STATUS_AFTER" ] ||
   [ "$TARGET_REFS_BEFORE" != "$TARGET_REFS_AFTER" ]; then
  printf '%s\n' 'BLOCKED: Claude V1 동안 target worktree 또는 refs가 바뀌었다'
  exit 24
fi
if [ "$claude_rc" -ne 0 ]; then
  printf 'BLOCKED: Claude V1 command failed rc=%s\n' "$claude_rc"
  exit 25
fi
```

→ Claude는 버릴 수 있는 복제본에서만 실제 repository와 tests를 공격한다. `--tools`는 사용 가능한
도구를 세 종류로 줄이고, `--allowedTools`는 clone 내부 Read/Grep, option wildcard가 없는 Git 조회,
고정된 검사 명령만 정확히 연다. test는 미리 잠근 의존성을 준비한 뒤 Claude native sandbox와 offline
`uv` 안에서 실행한다. sandbox는 사용할 수 없으면 실패하고, clone 밖 쓰기·network·unsandboxed escape를
닫는다. Claude가 새 Bash를 시작할 때 상위 환경을 덮는 경우까지 막기 위해 각 검사는 추적된 전용
wrapper를 호출한다. wrapper 본문이 시작된 뒤 `HOME`, `TMPDIR`, uv cache를 clone 내부로 다시 export하고
고정된 check ID만 실행한다. `--disallowedTools`는 파일·Git·GitHub 변경 명령을 다시 닫는다. test가
cache나 임시 파일을 써도 복제본 안에만 남는다. 출력 형식 블록도
명령에 포함해야 한다. 실행 전후에는 target HEAD, 전체 status, ref
목록의 지문을 비교한다. 하나라도 달라지면 Claude 판정 내용과 관계없이 24로 중단한다.

Claude 출력이 비었거나 `Done` 한 줄이거나 `VERDICT:`가 없으면 검증 실패다. 형식만 어겼지만 대상
작업은 맞으면 형식 블록을 강조해 같은 attempt에서 최대 한 번 재실행한다. 대상 자체가 불명확하면
질문을 교정한 새 검증을 같은 attempt에서 최대 한 번 실행한다. 두 한도를 모두 썼는데 유효한 판정이
없으면 무한 재호출하지 않고 `BLOCKED`다.

`FAIL`이면 finding을 바로 믿지 말고 다음 Codex V2에서 먼저 재현한다. 실제 결함이면 FIX_RED로 간다.
`PASS`여도 Codex V2를 생략하지 않는다.

### 15. `CODEX_V2` — Claude 판정 자체를 재공격

Claude의 finding을 한 줄씩 번호 붙인다. 각 항목에 대해 Codex가 다음을 직접 수행한다.

1. Claude가 든 file:line을 fresh `nl -ba`로 다시 읽는다.
2. Claude가 든 명령을 같은 worktree에서 다시 실행한다.
3. 전체 출력과 종료값이 같은지 기록한다.
4. finding이 실제 SOT/AC 위반인지, 과장인지, 범위 밖인지 판정한다.
5. Claude가 보지 않은 반대 방향도 공격한다. PASS면 누락을 찾고 FAIL이면 오탐을 찾는다.

goal에 다음 열을 가진 표를 append한다.

| ID | Claude 판정 | Codex 재현 명령 | 재현 결과 | SOT/AC 대조 | 최종 조치 |
|---|---|---|---|---|---|
| V1-1... | 원문 심각도·제목 | 실제 명령 | 일치/불일치 | 실제 근거 | fix/기각/재검증 |

→ Claude의 권위를 옮기는 표가 아니라, 모든 주장을 로컬 증거로 다시 채점하는 표다. 표 아래에는 각
명령의 전체 출력과 `→` 해석을 보존한다.

판정 규칙:

- Claude FAIL + Codex 재현됨: FIX_RED.
- Claude FAIL + 재현 안 됨: 근거를 공개하고 finding 기각. 의심이 남으면 다른 질문으로 Claude 1회 재호출.
- Claude PASS + Codex가 결함 재현: FIX_RED 후 Claude V1부터 다시.
- 둘의 해석이 갈림: 완료 금지. 같은 계약을 직접 판별하는 새 명령을 만들거나 Claude를 한 번 더 호출.
- 둘 다 PASS이고 모든 local evidence가 fresh: SHIP.

Claude finding을 기각한 항목은 숨기지 않는다. PR 본문의 `검증자 지적 중 기각한 항목` 절에 ID,
원문 심각도, 원문 제목, 원문 file:line·명령·출력, Codex 재현 명령·전체 출력, 기각 이유를 모두 싣는다.
요약 한 줄로 줄이지 않는다. 기각 항목이 0개면 `없음`이라고 쓴다.

### 16. `REVIEW_CHECKPOINT` — 검증 회차를 commit하고 다음 분기를 결정

V1/V2 한 회차가 끝나면 source, test, dependency, lockfile이 clean인지 확인한다. goal에는 이번
attempt의 local 검증, mutation, Claude 원문, Codex 재현이 모두 있어야 한다.

goal 파일만 stage해 REVIEW commit을 만든다.

```text
독립 검증의 재현 결과를 다음 수정 전에 고정한다

Constraint: Claude finding은 Codex가 같은 명령으로 재현해야 판정 근거가 된다
Rejected: 검증 로그를 working tree에만 둔 채 다음 수정 | 중단 후 어느 결함을 고쳤는지 복원할 수 없다
Confidence: high
Scope-risk: narrow
Directive: REVIEW의 미해결 finding을 Fix-for trailer 없이 고치지 마라
Tested: Claude V1 findings were reproduced or rejected by Codex V2
Not-tested: CI is NOT_RUN until the final accepted review is pushed
Phase: REVIEW
Attempt: <CURRENT_ATTEMPT>
Fix-for: <INITIAL_CONTRACT_OR_FINDING_ID>
```

→ REVIEW는 검증자의 말과 재현 증거를 source 수정과 분리해 보존한다. 실제 결함이 0이면 EVIDENCE와
SHIP으로 가고, 실제 결함이 있으면 다음 attempt의 FIX_RED로 간다.

### 17. EVIDENCE commit — 검증 장부와 다음 안전한 handoff

V1/V2가 합의하면 구현 goal에 다음을 append한다.

- PLAN/RED/GREEN/fix commit SHA
- 모든 검증 명령, 전체 출력, 종료값, case/file 수와 `→` 해석
- mutation 실패/복구/clean readback
- Claude 명령 전문과 출력 전문
- Codex 재현 명령·출력·판정표
- live, UI, production wiring이 `NOT_RUN`인 이유
- 현재 diff 파일 목록과 `git diff --check` 결과

그리고 다음 파일을 만든다. 같은 경로가 이미 있으면 이전 evidence와 중단선을 보존하면서 현재
attempt의 SHA·검증 결과·재개 조건만 갱신한다. 날짜를 바꾼 중복 파일을 새로 만들거나 기존 근거를
통째로 덮어쓰지 않는다.

`docs/engineering/goal-prompts/humansearch-next-owner-gated-after-L0-<YYYY-MM-DD>.md`

이 다음 prompt는 실행용이 아니라 owner-gated handoff다. 반드시 다음을 적는다.

- L0 PR이 merge되기 전에는 어떤 다음 code도 시작하지 않는다.
- C1은 실제 포털과 개인정보에 닿으므로 오너가 세션에 있고 별도 L3 strict goal을 승인해야 한다.
- 원본 capture는 Git 밖, 마스킹된 구조 fixture만 Git 안이라는 계약을 다시 검증해야 한다.
- 기존 clean-room 계획의 accessible-name/text-free blocker를 먼저 해결한다.
- 자동 로그인, 자동 제출, 후보 등록, 발송, merge, deploy는 권한 밖이다.
- 이 파일을 장기 부재 중 자동 실행하지 말라는 첫 줄 경고.

goal과 next prompt만 stage하여 EVIDENCE commit을 만든다.

```text
검증 증거와 다음 안전 경계를 세션 밖에도 남긴다

Constraint: 다음 단계는 live portal과 개인정보에 닿아 owner presence가 필요하다
Rejected: L0 뒤 C1 자동 연속 실행 | 권한과 위험 등급이 달라진다
Confidence: high
Scope-risk: narrow
Directive: 이 PR을 merge한 뒤에도 owner-gated prompt를 자동 실행하지 마라
Tested: local gates, mutation, Claude V1, Codex V2 passed and are preserved in the goal
Not-tested: live portal, browser, login, PII, merge, deploy are NOT_RUN by design
Phase: EVIDENCE
Attempt: <CURRENT_ATTEMPT>
Fix-for: <INITIAL_CONTRACT_OR_FINDING_ID>
```

→ 이 commit은 code를 바꾸지 않고 검증과 다음 중단선을 영속화한다.

### 18. `SHIP` — 일반 push와 PR만

push 전에 다음이 모두 참이어야 한다.

- `git status --short` 출력 0줄
- `git diff --check origin/main...HEAD` 종료 성적 0
- PLAN 뒤 attempt별 RED→GREEN→REVIEW가 빈틈없이 존재하고 마지막이 가장 큰 attempt의 EVIDENCE임
- RED 이후 GREEN/EVIDENCE에서 기존 RED test 기대값 변경 0
- local verify와 mutation PASS
- Claude V1 본문·VERDICT 존재
- Codex V2 전 finding 재현 표 존재
- V1/V2 미해결 불일치 0

일반 push만 실행한다.

```bash
git push -u origin task/humansearch-l0-surface-classifier
```

→ pre-push가 이름 규칙에 맞는 acceptance 전체를 실행한다. 오래 걸려도 우회하지 않고 최종 종료값과
각 PASS/FAIL을 읽는다. `--no-verify`는 금지다.

이미 open PR이 있는지 먼저 확인한다.

```bash
gh pr list --head task/humansearch-l0-surface-classifier --state open \
  --json number,title,url,headRefOid,baseRefName
```

→ 결과가 한 개면 그 PR을 재사용한다. 0개면 base `main`으로 새 PR을 만든다. 두 개 이상이면
중복 상태이므로 `BLOCKED`다.

새 PR 제목은 `fix: HumanSearch L0 인증 화면 분류 계약을 fail-closed로 구현`으로 한다. PR 본문은
§8 3층 구조로 다음을 포함한다.

- 전문용어 없는 결론과 오너 판단: merge 여부만 판단
- 왜 5-state surface classifier이고 7-state가 아닌지
- 변경 파일과 비범위
- RED와 GREEN SHA
- targeted/all test counts, ruff/mypy, acceptance, verify, mutation
- Claude V1 원문 경로와 Codex V2 표 경로
- 검증자 지적 중 기각한 항목의 원문과 Codex 재현 전문 또는 `없음`
- live/UI/PII `NOT_RUN`
- 자동 merge하지 않는다는 문장

### 19. `CI_WAIT` — 같은 SHA의 서버 검사 확인

push 직후 local, remote branch, PR head를 먼저 비교한다. 그 뒤 서버 run 목록에서 실제 검사 대상 SHA를
읽어 네 번째 비교값으로 쓴다.

```bash
EXPECTED_SHA="$(git rev-parse HEAD)"
REMOTE_SHA="$(git rev-parse origin/task/humansearch-l0-surface-classifier)"
PR_JSON="$(gh pr view <PR_NUMBER> \
  --json headRefOid,baseRefName,url,mergeStateStatus)"
printf '%s\n' "$EXPECTED_SHA"
printf '%s\n' "$REMOTE_SHA"
printf '%s\n' "$PR_JSON"
PR_SHA="$(jq -r '.headRefOid' <<<"$PR_JSON")"
if [ "$EXPECTED_SHA" != "$REMOTE_SHA" ] || [ "$EXPECTED_SHA" != "$PR_SHA" ]; then
  exit 26
fi
```

→ local, remote, PR head가 완전히 같아야 한다. 다르면 서버 결과를 기다리지 말고 원인을 해결하거나
26으로 `BLOCKED`다. 아직 서버 run이 생기기 전이므로 여기서는 세 값만 비교한다.

CI는 한 번에 60초 넘게 잠드는 명령으로 방치하지 않는다. 30초 간격으로 상태를 읽고 최대 45분 동안
기다린다. pending 동안 사용자에게 60초 안에 짧은 진행 상황을 알린다.

각 poll에서 아래 두 조회를 모두 실행한다.

```bash
RUNS_JSON="$(gh run list \
  --branch task/humansearch-l0-surface-classifier \
  --commit "$EXPECTED_SHA" \
  --workflow verify.yml \
  --limit 20 \
  --json databaseId,event,headSha,status,conclusion,url,workflowName)"
CHECKS_JSON="$(gh pr checks <PR_NUMBER> \
  --json name,state,bucket,link,event,workflow)"
printf '%s\n' "$RUNS_JSON"
printf '%s\n' "$CHECKS_JSON"
```

→ 첫 조회는 현재 코드 지문을 대상으로 실행된 서버 작업의 대상 지문·상태·최종 성적을 읽는다. 둘째는
검토 요청 화면에 실제로 붙은 검사 전부를 읽는다. 저장소 보호 설정이 “필수 검사”를 지정했다고
가정하지 않고 관측된 검사를 모두 판정한다.

- pending이 있으면 30초 뒤 다시 확인.
- `RUNS_JSON`의 모든 `headSha`는 `EXPECTED_SHA`와 같아야 한다. 다른 값은 이번 증거로 세지 않는다.
- 현재 SHA의 `push`와 `pull_request` event가 각각 한 건 이상 있어야 한다. 둘 중 하나라도 0건이면
  `NOT_RUN`이며 계속 기다리다가 45분에 `BLOCKED`다.
- 현재 SHA에서 관측된 run은 모두 `status=completed`, `conclusion=success`여야 한다. 실패, 취소,
  건너뜀, 시간 초과, 중립, 오래됨, 조치 필요, 결론 없음은 PASS가 아니다.
- `CHECKS_JSON`은 한 건 이상이어야 하고 모든 `bucket`이 `pass`여야 한다. `pending`은 기다리고,
  `fail`, `skipping`, `cancel`은 실패 원인을 읽는다.
- 관측된 failure가 있으면 해당 run의 실패 log를 읽는다.
- 같은 AC 안에서 재현 가능한 code 결함이면 다음 attempt의
  `FIX_RED→FIX_GREEN→LOCAL_VERIFY→MUTATION→CLAUDE_V1→CODEX_V2→REVIEW_CHECKPOINT→EVIDENCE→SHIP`
  순서를 전부 다시 수행한다.
- infra, secret, permission, unrelated existing failure이면 우회하지 않고 `BLOCKED`.
- run 또는 check 0개는 PASS가 아니라 `NOT_RUN`; `BLOCKED`.
- 45분을 넘으면 timeout `BLOCKED`; 완료로 쓰지 않는다.

현재 SHA의 push·pull_request run과 PR에 관측된 check가 모두 success/pass이면 `gh pr view`로 final
head SHA와 merge state를 다시 읽는다. merge는 하지 않는다.

### 20. `HANDOFF` / `DONE` 출력 계약

최종 보고는 한국어 존칭체로 세 층을 지킨다.

1층 결론:

- merge할 준비가 됐는지 또는 정확히 무엇 때문에 막혔는지
- 오너가 결정할 것은 PR merge 여부 하나인지
- 실제 포털과 후보자 자료를 건드리지 않았다는 사실

2층 판단 근거:

- 5-state surface classifier를 고른 이유
- 버린 7-state 통합안과 우선순위 방식
- 틀리면 무엇이 깨지는지
- 이번에 실패해서 고친 것, 건너뛴 것, 확인 못 한 것
- 결정 카드 다섯 줄: 무엇을/왜/버린 길/대가/되돌리기

3층 증거:

- PR 번호·URL·head SHA
- PLAN, attempt별 RED/GREEN/REVIEW, EVIDENCE와 fix SHA
- test/ruff/mypy/acceptance/verify/mutation의 명령·전체 출력·종료값·건수
- Claude V1 명령·원문 경로·VERDICT·finding 수
- Codex V2 재현 표와 불일치 수
- CI check 이름·상태·대상 SHA
- 변경 파일 목록
- `NOT_RUN` 목록

모든 terminal 출력, code block, 표 바로 아래에는 `→`로 시작하는 1~3줄 해석을 붙인다. 전문용어는
첫 문장에서 뜻을 풀고, 1층에는 전문용어를 쓰지 않는다.

### 21. 완료 판정

아래가 전부 참일 때만 `DONE`이다.

- 선행 PR #13/#14/#15의 merge commit이 fresh `origin/main`에 있음
- tracked SOT가 3 roles/5 states/16 inputs를 정의함
- goal 문서가 code보다 먼저 PLAN commit에 있음
- RED가 정확히 25 target tests를 수집하고 기능 부재로 실패함
- GREEN에서 RED test/dependency/lock 변경 0
- targeted/all pytest, ruff, mypy, 관련 acceptance, verify PASS
- mutation이 실패를 잡고 원복 뒤 PASS+clean
- Claude V1 본문과 Codex V2 전 finding 재현 완료, 미해결 불일치 0
- clean 일반 push, pre-push PASS
- PR head=remote head=local head=관측된 모든 CI run head
- 현재 SHA의 push·pull_request run이 각각 1개 이상이고 전부 success이며, PR에 관측된 check도 모두
  pass이고 fail/skip/cancel/pending이 0개
- goal과 owner-gated next prompt가 Git에 추적됨
- merge/deploy/live/browser/login/PII/registration/send 모두 0회

하나라도 거짓이면 `DONE`이라 쓰지 않는다. 복구 경로가 있으면 상태기계대로 계속하고, 권한·범위·
선행 조건이 막으면 `BLOCKED` 증거와 재개 조건을 남기고 끝낸다.

### 22. 제출 전 셀프 감사

다음 질문의 답이 모두 “아니오”인지 검사한다.

- 결론에 전문용어가 있는가?
- 해석이 없는 출력·code block·표가 있는가?
- 오너가 결정할 사항이 빠졌는가?
- 버린 길과 대가가 빠졌는가?
- file:line이 무슨 일을 하는지 설명하지 않았는가?
- 쉽게 쓰려다 수치·증거·한계를 뺐는가?
- 초등학생용 비유로 내용을 깎았는가?
- 실패·미확인·NOT_RUN을 앞부분에서 숨겼는가?
- 추정을 사실처럼 썼는가?

goal과 next prompt에는 다음 보조 검사도 실행하고 숫자를 기록한다. 이 검사는 경고 도구일 뿐 품질
합격증이 아니다.

```bash
if [ -x "$HOME/.claude/skills/strict/brief-lint.sh" ]; then
  bash "$HOME/.claude/skills/strict/brief-lint.sh" <GOAL_PATH>
  bash "$HOME/.claude/skills/strict/brief-lint.sh" <NEXT_PROMPT_PATH>
else
  printf '%s\n' 'brief-lint: NOT_RUN — helper is not installed'
fi
```

→ 흔한 형식 누락 수를 알려준다. 도구가 없으면 실패를 숨기지 않고 `NOT_RUN`을 기록한 뒤 바로 위
아홉 질문을 사람이 직접 한 번씩 답한다. 경고 0도 내용 검토를 대신하지 않는다.
