# main 혼합 작업 무손실 복구 및 재발 방지 goal — 2026-08-25

VERDICT: NOT_RUN

## 1층 결론

현재 파일은 사라지지 않았고, 원본 47개는 저장소 밖 독립 복사본과 같은 내용 식별값으로 보존됐다. 잘못 올라간 한 커밋도 서로 다른 보호 이름 두 개로 보존됐다.

아직 `main` 기준점 복구와 B·C 재구축·독립 공격 검증은 시작 전이다. 아래 순서와 중단 조건을 모두 통과하기 전에는 완료로 판정하지 않는다.

## 2층 판단 근거

- 작업 폴더에는 추적 수정 5개와 미추적 파일 42개가 섞였고, 그중 B는 정확히 4개다. 나머지 43개는 소유자를 추측하지 않고 `UNOWNED_PRESERVED`로 rescue에 남긴다.
- `main`의 잘못 올라간 커밋 `3094eefa646b102074dfb6401777afe450223e6c`는 `origin/main`의 `c59bad7b160c473cda5545e76e6fa6bcc711a7ea`보다 정확히 한 커밋 앞선다. `origin/main`은 `main`의 조상이며 반대 방향은 아니다.
- 빠진 동작 때문에 먼저 실패시키고 최소 변경으로 통과시키는 RED→GREEN은 B와 C의 전용 작업 폴더에서만 수행한다. 과거 문서의 숫자나 현재 dirty root 실행은 새 증거가 아니다.
- 저장소 정본은 직접 작성 코드 파일 hard 600줄, 함수 hard 100줄을 요구한다. B 테스트는 원본이 정확히 600줄이므로 RED 뒤 단언을 줄이거나 무심코 한 줄 추가하지 않는다.
- 초록불은 branch 이름이 아니라 정확한 commit SHA와 clean worktree에만 귀속한다. 검증 후 문서를 고치면 SHA가 바뀌므로 전체 검증과 외부 판정을 다시 실행한다.

## 세션과 직접 측정한 현재 상태

- 복구 세션 ID: `VHREC-20260825T200157+0900-01a03893`
- 저장소: `/Users/kangsangmo/Desktop/Valuehire_v6`
- 최초 안정 측정: `2026-08-25T20:05:55+09:00`
- 두 번째 안정 측정: `2026-08-25T20:10:47+09:00`
- 두 측정 공통 HEAD: `3094eefa646b102074dfb6401777afe450223e6c`
- 두 측정 공통 status NUL stream SHA-256: `c67d413d5c48b4edfdec8c75428e756b346077366012f42893212b104441f655`
- dirty 파일 mode·size·SHA-256·NUL path 집계: `7162effdd9e366dc2bfd9e87b468d03b4be6cf583fe3e0cca4c772ba504b8c5a`
- Git index SHA-256: `c7c4ffd025ff84d350a5380286335c58cbbfecf9f7a0c3f681cd9fd8d4787f7f`
- tracked 수정: 5개, staged: 0개, untracked: 42개
- 외부 독립 복사본: `/Users/kangsangmo/Desktop/Valuehire_v6-recovery-20260825T201120.7oELVt`
- 복사본 파일 수: 47개, 복사본 집계 SHA-256: `7162effdd9e366dc2bfd9e87b468d03b4be6cf583fe3e0cca4c772ba504b8c5a`
- C 보호 ref: `refs/heads/task/wu4a-finding-runner-original-20260825T200952`
- 전체 보호 ref: `refs/heads/backup/main-mixed-3094eef-20260825T200952`
- 두 보호 ref readback: 모두 `3094eefa646b102074dfb6401777afe450223e6c`
- control worktree: `/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/main-contamination-recovery-20260825T200952`
- control branch: `task/main-contamination-recovery-20260825T200952`
- control base: `c59bad7b160c473cda5545e76e6fa6bcc711a7ea`

## 읽은 정본과 Gate 0 장부

| 상태 | 시각 | 명령 | 종료값 | 식별 증거 |
|---|---|---|---:|---|
| PASS | 2026-08-25T20:01:57+09:00 | `sed -n '1,1000p' /Users/kangsangmo/.codex/skills/strict/SKILL.md` | 0 | 337줄 전체 읽기 |
| PASS | 2026-08-25T20:02:34+09:00 | `sed -n '1,10000p' docs/sot/coding-principles.md` | 0 | 74줄 전체 읽기; 첫 기록 래퍼 실패 뒤 같은 읽기 재실행 |
| PASS | 2026-08-25T20:02:57+09:00 | `sed -n '1,10000p' docs/sot/principles.yaml` | 0 | 345줄 전체 읽기 |
| PASS | 2026-08-25T20:03:11+09:00 | `bash scripts/acceptance-principles-check.sh` | 0 | `VERDICT: PASS`, `MECHANISMS: PASS 34/34`, `WIRING: PASS pre-push=1 ci=1` |
| PASS | 2026-08-25T20:03:53+09:00 | `sed -n '1,10000p' docs/sot/git-workflow.md` | 0 | 33줄 전체 읽기 |
| PASS | 2026-08-25T20:04:12+09:00 | `sed -n '1,10000p' docs/sot/verification-commands.md` | 0 | 95줄 전체 읽기 |
| PASS | 2026-08-25T20:04:31+09:00 | `sed -n '1,10000p' docs/sot/features/engineering/change-delivery-guardrails.yaml` | 0 | 209줄 전체 읽기 |
| PASS | 2026-08-25T20:04:48+09:00 | `sed -n '1,10000p' scripts/install-hooks.sh` | 0 | 54줄 전체 읽기 |

→ 종료값은 프로그램의 성적이며 0은 이 명령의 합격이다. 전체 출력 원문은 별도 recovery evidence 문서에 보존하고 이 표는 추적 인덱스다.

## T 계약 — 세 검증 주체가 함께 쓰는 채점 기준

### 입력

```text
repository_root: absolute existing Git worktree path
expected_old_main: full 40-hex commit SHA
verified_new_main: full 40-hex origin/main SHA
inventory_status_sha256: 64-hex digest of porcelain-v2 NUL stream
inventory_files: NUL-separated tracked-modified + untracked paths
protection_refs: two absent branch refs created transactionally
lane_scope: exact allowlist for B, C, control, or rescue
```

→ 입력은 자동 추측하지 않는다. HEAD나 상태 지문이 달라지면 이전 inventory를 폐기하고 처음부터 다시 측정한다.

### 출력

```text
main_ref: verified_new_main only after compare-and-swap
rescue_branch: dirty original worktree with unchanged index and 47 file hashes
control_commit: recovery goal, manifest, evidence, and prevention artifact only
c_red_commit / c_green_commit: exact six-file lane only
b_red_commit / b_green_commit: exact four-file lane only
verification: command, timestamp, exit, full output, commit SHA, clean status, session ID
remote_writes: 0
```

→ compare-and-swap은 예상 old SHA와 실제 old SHA가 같을 때만 한 번 바꾸는 조건부 갱신이다.

### 오류와 상태

- `PASS`: 원명령의 종료값·출력·수집 건수·SHA·clean 조건까지 모두 충족했다.
- `FAIL`: 실행됐지만 계약을 위반했다. 원인을 고친 뒤 같은 원명령을 재실행한다.
- `NOT_RUN`: 시작하지 못했거나 원문을 회수하지 못했다. 완료 불가다.
- `BLOCKED`: 안전한 복구 시도 뒤에도 권한·자격증명·외부 서비스처럼 현재 권한 밖 원인이 남았다. 완료 불가다.
- `UNOWNED_PRESERVED`: 소유권을 증거로 정하지 못해 원본 rescue에 byte-for-byte 보존했다. B/C에 포함하지 않는다.
- `RECOVERY_REQUIRED`: 양쪽 원본을 유지했지만 hash 불일치나 부분 적용이 있어 후속 복구가 필요하다.

### 경계

- branch/ref 이름이나 worktree path가 존재하면 덮어쓰지 않는다.
- active writer 또는 B/C 실행 프로세스가 있으면 ref·branch·worktree mutation을 하지 않는다.
- 기존 dirty/rescue worktree에서는 `restore`, `checkout --`, `stash`, `clean`, `reset --hard`를 실행하지 않는다.
- 파일명은 NUL로 구분하고, 파일마다 mode·size·SHA-256을 readback한다.
- secrets 내용은 출력하지 않는다. `.secret-patterns.default`를 실제 비밀 패턴 대체물로 쓰지 않는다.
- push, PR 생성, merge, 배포는 실행하지 않는다.

## 복구 불변조건

- Inv1: 기존 tracked·untracked 대상 파일은 독립 복사본과 SHA-256 readback이 확인되기 전까지 삭제·덮어쓰기하지 않는다.
- Inv2: `3094eef`는 main 이동 전에 충돌 없는 보호 ref 두 개로 보존한다.
- Inv3: main 또는 B/C 파일을 사용하는 프로세스가 살아 있으면 ref·branch·worktree mutation을 하지 않는다.
- Inv4: B, C, 복구 제어 문서, 무관 변경은 서로 다른 소유 경계에 둔다.
- Inv5: main 이동은 old SHA를 조건으로 하는 compare-and-swap 방식으로만 한다.
- Inv6: 복구가 중단돼도 rescue branch와 원본 파일로 같은 작업을 다시 시작할 수 있어야 한다.
- Inv7: commit·test 초록불은 정확한 SHA와 clean worktree에만 귀속한다.

## EARS 인수 기준

- AC1: **When** 복구가 끝나면, 시스템은 사전 inventory의 모든 파일을 동일 hash의 원본·rescue·검증된 task commit 중 적어도 한 곳에서 readback해야 한다.
- AC2: **When** B/C 검증을 실행하면, 시스템은 각각 자기 전용 branch와 worktree에서만 실행해야 한다.
- AC3: **When** main ref를 복구하면, 시스템은 old SHA가 정확히 일치할 때만 `origin/main`의 검증된 SHA로 이동해야 한다.
- AC4: **When** RED commit과 GREEN commit을 각각 checkout해 원명령을 실행하면, 시스템은 RED에서 요구 동작 부재로 실패하고 GREEN에서 같은 테스트를 통과시켜야 한다.
- AC5: **When** B/C scope 밖 파일을 diff하면, 시스템은 변경 0건을 출력해야 한다.
- AC6: **When** V1/V2를 실행하면, 시스템은 정확한 최종 SHA·명령·시각·종료값·전체 출력·session ID를 남겨야 한다.
- AC7: **When** 새 worktree를 검사하면, 시스템은 실제 `.secret-patterns` symlink와 존재하는 target, `core.hooksPath=hooks`를 readback해야 한다.
- AC8: **When** 완료를 보고하면, 시스템은 main·B·C·rescue·control worktree/ref를 모두 다시 읽어야 한다.
- AC9: **When** 이 로컬 CHECKPOINT 작업을 종료하면, 시스템은 push·PR·merge 0건을 증명해야 한다.
- AC10: **When** root dirty worktree를 rescue branch로 전환하면, 시스템은 전환 전후 index hash·tracked diff hash·untracked NUL 목록 hash·47개 파일 집계 hash가 모두 같아야 한다.
- AC11: **When** line/function 경계를 검증하면, 시스템은 600·100 정상 사본을 통과시키고 601·101 고장 사본을 실패시켜야 하며 대상 0건을 합격 처리하지 않아야 한다.
- AC12: **When** B/C 최종 commit을 검증하면, 시스템은 test 수집 1건 이상과 skipped/todo 0건을 기계 출력에서 확인해야 한다.

## counter-AC — 가짜 합격 시나리오

- main ref만 고쳤지만 dirty 파일 하나의 hash가 사라진다.
- C 보호 branch만 남기고 main tracked 수정이 reset으로 사라진다.
- source를 지운 뒤 처음 hash를 계산한다.
- B/C 테스트를 rescue 또는 main에서 실행한다.
- 과거 goal의 7/7·45/45 문구를 신선 실행으로 센다.
- 테스트 0건 수집인데 exit 0을 PASS로 센다.
- `git diff --check`만 실행하고 untracked 파일을 놓친다.
- V1/V2가 요약만 남기고 원문·session ID·SHA를 남기지 않는다.
- `.secret-patterns.default` fallback으로 acceptance를 초록으로 만든다.
- B의 네 번째 파일 `checkpoint-js-scan.mjs`를 누락한다.
- branch 이름 충돌을 force로 덮어쓴다.
- rescue의 무관 변경을 B/C commit에 섞는다.
- B 테스트가 600줄이라는 이유로 기존 단언을 삭제·축약한다.
- 구현 뒤 테스트를 쓰거나 RED 뒤 기존 테스트를 약화한다.
- dirty 또는 다른 SHA에서 얻은 검증 결과를 최종 commit에 재사용한다.
- Claude/Codex가 실행 없이 PASS라고 쓴 문장을 실행 증거로 센다.

## 파일 소유권

### Control lane

- `docs/engineering/main-contamination-recovery-goal-2026-08-25.md`
- `docs/engineering/main-contamination-recovery-manifest-2026-08-25.tsv`
- `docs/engineering/main-contamination-recovery-evidence-2026-08-25.md`
- main 직접 작업 재발 방지용 patch artifact와 후속 prompt

### C lane — 정확히 6파일

- `docs/engineering/finding-runner-goal-2026-08-24.md`
- `tests/finding-runner.test.mjs`
- `tests/fixtures/finding-runner/blocked.json`
- `tests/fixtures/finding-runner/not-reproducible.json`
- `tests/fixtures/finding-runner/reproduced.json`
- `tools/strict/finding-runner.mjs`

### B lane — 정확히 4파일

- `docs/engineering/checkpoint-gate-goal-2026-08-24.md`
- `tests/checkpoint-gate.test.mjs`
- `tools/strict/checkpoint-gate.mjs`
- `tools/strict/checkpoint-js-scan.mjs`

### Rescue lane

- B 4파일은 원본 hash readback이 끝날 때까지 보존한다.
- 나머지 dirty 43파일은 `UNOWNED_PRESERVED`이며 owner를 추측하거나 자동 commit하지 않는다.
- C 6파일의 원본 commit은 두 보호 ref로 보존한다.

## 실행 순서와 중단 조건

1. Gate 0 정본·inventory·process·refs·reflog·ancestry를 읽기 전용으로 회수한다.
2. `3094eef` 보호 ref 두 개를 원자적으로 만들고 readback한다.
3. 외부 독립 복사본과 index를 만들고 47개 집계 hash를 readback한다.
4. control branch/worktree를 검증된 base에 만들고 이 goal을 먼저 고정한다.
5. active writer 0과 상태 불변을 재확인한 뒤 root를 `rescue/main-mixed-*` branch로 전환한다.
6. 전환 전후 index·diff·untracked·파일 hash를 대조한다.
7. main checkout 0과 보호 ref 두 개를 확인한 뒤 `git update-ref refs/heads/main <new> <old>`로만 main을 이동한다.
8. C와 B를 각각 검증된 base의 전용 branch/worktree에서 RED→GREEN으로 재구축한다.
9. `.secret-patterns`와 hooksPath를 각 lane에서 readback한다.
10. main writer preflight의 version-controlled canonical source를 찾고, 없으면 control lane에 적용 가능한 patch와 정확한 후속 prompt를 남긴다.
11. R2~R5, 저장소 전체 검사, Claude V1, 새 맥락 Codex V2를 정확한 final SHA에서 실행한다.
12. 모든 ref/worktree/hash와 remote write 0건을 최종 readback한다.

중단 조건은 ref/path 충돌, 예상 HEAD/status 변화, active writer, hash 불일치, 파일 소유권 충돌, 필수 검사 `FAIL|NOT_RUN|BLOCKED`, V1/V2 불일치다. 복구 가능한 실패는 원인·원명령·전체 출력을 남기고 접근을 바꿔 계속한다.

## RED→GREEN 계획

### C

1. `origin/main` base의 전용 branch/worktree를 만든다.
2. 원본 commit에서 goal·test·fixture 3개만 복원한다.
3. 구현 파일 부재로 같은 테스트가 요구 동작 부재 RED인지 확인하고 Lore RED commit을 만든다.
4. 구현을 복원하되 trailing whitespace와 과장·실행 신원 누락 문구를 현재 증거로 고친다.
5. 문서 계약 변경이 필요하면 별도 Work Unit으로 분리한다.
6. R2 고장 사본, GREEN, clean SHA, V1/V2를 실행하고 Lore GREEN commit을 만든다.

### B

1. `origin/main` base의 전용 branch/worktree를 만든다.
2. rescue 4파일의 SHA-256을 기록하고 매 복사 전후 비교한다.
3. goal·test만 복사해 구현 2파일 부재 RED를 실행하고 Lore RED commit을 만든다.
4. 구현 2파일을 같은 hash로 복사해 GREEN을 만든다.
5. 테스트가 600줄을 넘으면 동작 단위로 분리하되 단언을 삭제·축약하지 않는다.
6. 과거 V1/V2·hash·test 수를 새 SHA의 원문 증거로 교체한다.
7. R2 고장 사본, 경계, clean SHA, V1/V2를 실행하고 Lore GREEN commit을 만든다.

## 검증 명령

```bash
node --test tests/finding-runner.test.mjs
node --test tests/checkpoint-gate.test.mjs
node --check tools/strict/finding-runner.mjs
node --check tools/strict/checkpoint-gate.mjs
node --check tools/strict/checkpoint-js-scan.mjs
bash scripts/acceptance-principles-check.sh
bash verify.sh
bash scripts/check-docs-sot.sh
git diff --check
git show --check <commit>
git status --porcelain=v2 --branch --untracked-files=all
```

→ 각 lane의 목표 테스트는 전용 worktree에서 실행한다. `verify.sh`는 실제 `.secret-patterns` 연결을 readback한 뒤 실행한다.

경계와 적대 공격은 600/601 파일, 100/101 함수, 구현 호출 제거, test 수집 0건, test 삭제/skip/only/todo, B 네 번째 파일 누락, C의 `BLOCKED|NOT_TESTED` 병합 정책을 포함한다.

## R2~R5와 G/V1/V2/T

- R2: RED가 import 문법 오류가 아니라 구현 부재로 실패하는지, 구현 핵심 한 줄을 고장 내 같은 테스트가 실패하는지 확인한다.
- R3: 보고의 각 주장을 local command·file hash·ref readback에 연결하고, 반례와 미확인 범위를 적는다.
- R4: C는 CLI 진입점부터 실제 repro 실행까지, B는 CLI부터 Git index·secret scanner·JS scanner까지 호출 경로를 실행으로 증명한다.
- R5: 같은 원인으로 두 번 막히면 세 번째 반복 대신 더 작은 명령이나 별도 임시 복제 방식으로 바꾼다.
- G: 구현 Codex가 산출물을 만든다. 자기 테스트만으로 합격하지 않는다.
- V1: `ANTHROPIC_API_KEY`를 제거한 Claude CLI가 구현 결론 없이 T·산출물·실행 증거를 공격한다.
- V2: 새 맥락 Codex가 V1의 모든 재현 가능한 finding을 원명령으로 다시 실행하고 V1의 과장·누락을 양방향 공격한다.
- T: 이 문서의 EARS AC, counter-AC, 입출력·오류·경계, 저장소 SOT다.

## 롤백과 실패 주입

- main 이동 전: 보호 ref와 외부 snapshot을 유지한 채 mutation을 멈춘다.
- rescue branch 전환 뒤: root 파일을 건드리지 않고 해당 branch에서 같은 inventory를 다시 읽는다.
- main CAS 뒤 되돌려야 하면, 현재 main이 새 SHA와 정확히 같고 보호 ref·rescue hash가 유지될 때만 반대 방향 `git update-ref refs/heads/main <old> <new>`를 사용한다.
- B/C RED 또는 GREEN 실패: 해당 lane branch/worktree를 보존하고 rescue 원본을 유지한다. force 삭제하지 않는다.
- hash 불일치: 양쪽 파일을 모두 남기고 `RECOVERY_REQUIRED`로 기록한다.
- ref 충돌 실패 주입: 이미 존재하는 임시 ref에 다른 expected-old를 준 update-ref가 실패하고 기존 object가 유지되는지 `mktemp` 복제 저장소에서 확인한다.
- 부분 복구 중단: control goal, 외부 snapshot, 보호 ref, rescue branch만으로 같은 절차를 재개할 수 있어야 한다.

## 결정 카드

> **무엇을** — dirty root를 그대로 rescue branch로 전환하고 main ref만 조건부 갱신한다.
> **왜** — 파일과 index를 이동·재작성하지 않아 손실 가능성이 가장 작다.
> **버린 길** — stash, restore, reset, clean은 dirty 상태를 재작성하거나 제거하므로 기각한다.
> **대가** — rescue branch는 의도적으로 dirty하며 verified라고 부를 수 없다.
> **되돌리기** — rescue branch와 외부 snapshot의 hash를 읽어 같은 상태에서 재개한다.

> **무엇을** — B·C·control을 서로 다른 branch/worktree/commit으로 분리한다.
> **왜** — 각 초록불과 소유권을 정확한 SHA에 귀속할 수 있다.
> **버린 길** — 한 branch에서 순차 commit은 dirty root와 검증 장부가 섞일 위험이 있어 기각한다.
> **대가** — worktree와 검증 횟수가 늘어난다.
> **되돌리기** — 각 branch를 보존한 채 필요한 lane만 다시 실행한다.

## 완료 금지 조건

다음 중 하나라도 남으면 `VERDICT: PASS` 또는 완료를 쓰지 않는다: main SHA 불일치, 보호 ref 2개 미만, inventory hash 누락, B/C RED·GREEN 미재현, scope 밖 diff, dirty final lane, `.secret-patterns` 보정 미확인, 필수 `FAIL|NOT_RUN|BLOCKED`, G/V1/V2/T 불일치, remote write 1건 이상.

## 현재 판정

- PLAN: 진행 중
- BUILD: NOT_RUN
- AUDIT: NOT_RUN
- CHECKPOINT: NOT_RUN
- SHIP: 금지된 비범위
