# 시작 검사 `NOT_RUN`·`RED 2/19` 근본 복구 실행 프롬프트 — 2026-08-18

## 1층 — 결론

문제의 절반은 이미 고쳐져 검토 요청까지 올라가 있습니다. 그 수정안을 다시 만들거나 저장 기록을 강제로 지우지 말고, 남은 문서 변경을 안전하게 따로 보존한 뒤 장시간 아무 말이 없는 시작 검사까지 별도 변경으로 고치십시오.

자동으로 합치지는 마십시오. 검토 요청 생성과 검증까지 끝낸 뒤 사장님이 합칠 두세 건만 명확히 제시하고, 실제로 합쳐진 뒤 원래 시작 검사가 실패 0건을 보고할 때만 완료라고 하십시오.

## 2층 — 판단 근거

현재 첫 번째 실패는 “지운 민감정보가 남았다”가 아니라, 정상 개발 중 생기는 접근 불가능한 저장 조각을 내용과 무관하게 모두 위험으로 취급한 거짓 차단입니다. 이 문제는 기존 작업선과 [PR #23](https://github.com/sangmokang/Valuehire_v6/pull/23)에서 이미 내용 검사 방식으로 고쳤고, 합성 사례 13개와 서버 검사 2개가 통과했습니다.

두 번째 실패는 로컬 기본 작업선에 문서 커밋 6개가 직접 쌓여 서버 기본 작업선보다 앞선 상태입니다. 직접 업로드하거나 강제로 되돌리면 저장소 규칙 또는 사용자 변경 보존을 깨므로, 같은 커밋을 짧은 수명의 작업선으로 보존해 별도 검토 요청으로 보내야 합니다.

`scripts/session-status.sh`는 하위 검사 출력을 전부 숨겨 1분 넘게 어떤 검사가 도는지 알 수 없습니다. 이 때문에 정상 실행을 멈춤으로 오판해 `NOT_RUN`으로 남겼습니다. 최종 세 줄 판정은 유지하되, 현재 검사 이름과 경과를 별도 출력으로 보여주고 진짜 멈춤은 무한 대기하지 않게 만들어야 같은 사고가 반복되지 않습니다.

### 결정 카드

**무엇을** — 기존 PR #23을 정본 수정안으로 재사용하고, 로컬 문서 6개 배송과 시작 검사 진행 표시를 각각 독립 작업선·독립 검토 요청으로 처리합니다.

**왜** — 이미 공격 시험과 서버 검사를 통과한 보안 수정안을 다시 쓰면 중복과 회귀만 늘고, 서로 다른 위험을 한 변경에 섞으면 사장님이 무엇을 승인하는지 불명확해집니다.

**버린 길** — 접근 불가능한 객체를 강제 삭제하는 방법, 기본 작업선 직접 업로드, 검사 제외·성공값 조작, 세 문제를 한 거대 변경으로 합치는 방법을 버립니다. 각각 복구 불가 위험, 규칙 위반, 거짓 합격, 검토 불가능을 만듭니다.

**대가** — 검토 요청이 두세 건으로 나뉘고, 최종 실패 0건은 사장님 병합 뒤에만 증명할 수 있습니다.

**되돌리기** — 기존 로컬 커밋은 보존 작업선이 계속 가리키게 하고, 새 변경은 검토 요청 단위로 닫거나 되돌립니다. 사용자 파일 삭제, 강제 초기화, 객체 강제 정리는 사용하지 않습니다.

## 3층 — 2026-08-18 기준 증거 원문

아래 값은 실행 시작 때 반드시 다시 측정해야 하는 기준선이며, 미래 실행자가 그대로라고 가정하는 고정값이 아닙니다.

```text
$ bash scripts/session-status.sh
HEAD: 74bde5c (ahead 6 / behind 0)
ORIGIN: 4fdef31
RED: 2/19 (acceptance-0-7.sh 제외 — CI 담당)
```

→ 원래 시작 검사는 프로그램 성적 0으로 끝났지만, 내용상 19개 중 2개 실패를 보고했습니다. 종료값만 보고 합격으로 바꾸면 안 됩니다.

```text
$ /usr/bin/time -p bash scripts/acceptance-0-2.sh
PASS: no secret-pattern match in any tracked file, .env not tracked
FAIL: unreachable 객체 244건 잔존 (reflog expire/gc --prune=now 미완)
real 74.12
user 22.63
sys 18.22
```

→ 추적 파일의 민감정보 검사는 통과했고, 내용과 무관한 객체 개수 조건만 실패했습니다. 같은 세션 뒤 측정은 245개였으므로 개수는 공유 저장소의 다른 작업에 따라 변하는 값입니다.

```text
$ git fsck --full --no-reflogs --unreachable | 객체형별 개수만 집계
blob 223
commit 7
total 245
tree 15
```

→ 본문이나 민감값은 출력하지 않고 형식과 개수만 셌습니다. “245개가 안전하다”는 증거가 아니라, 개수 0만으로 상시 개발을 판정하면 흔들린다는 증거입니다.

```text
$ 과거 오염 커밋 6개와 오염 blob 6개에 git cat-file -e 실행
ABSENT 4d53eac48c957e70ece5d04a600b2e53527f384a
ABSENT c32d5fd091748f17259e16236e76098ef325479e
ABSENT e951c59c7dede7762bfcf17aeb9a026c4894609f
ABSENT ce814451f3d83a0f9b6360ec6ab9218a15a03c2c
ABSENT 2f45b7b6dda007976ee493b6cca9b0a4bece25be
ABSENT 965f084fed098db8daeae376ca05f3e21b814d41
ABSENT 2efa8a62dcb79de0836886a96ccebd32f0388446
ABSENT 450f4ace2a410e17c9b3945104dff135fcbb3ddf
ABSENT 5cc108c1159d963e07213add8f6fe0360e4f1bdf
ABSENT bd3eb3eebab7618895b99509e44f26b7347e0420
ABSENT e3a42af9f052964012832e996cc7eec2b9b8509c
ABSENT f9f12ed9a352eb5e4cc881239f39ee5568d80478
```

→ 과거에 이름이 고정된 오염 객체 12개는 실제 객체 저장소에 없습니다. 미래 오염을 놓치지 않으려면 이름 목록뿐 아니라 접근 불가능한 객체의 내용을 검사해야 합니다.

```text
$ /usr/bin/time -p bash scripts/acceptance-0-5.sh
FAIL: origin/main(4fdef31fe75c8519091cebe8a6c4cbf5be1893ae) != main(74bde5cd88dace72c7dada8285478888a89a3f61) — push 미완료
real 5.11
user 2.28
sys 0.48
```

→ 로컬 기본 작업선이 서버보다 6개 앞선 것이 두 번째 실패의 전부입니다. 기본 작업선 직접 업로드는 `docs/sot/git-workflow.md`가 사장님 본인에게도 금지합니다.

```text
$ git log --oneline origin/main..main
74bde5c docs(engineering): codex P0 구현 프롬프트 — 스텝 체인 + push 전 재시험 계약
f3578eb docs(engineering): 잔디밭 스펙 v2 확정 — codex Phase 0 산출 + Claude V1 적대검증 PASS
c60ea5a docs(engineering): codex 투입 Phase 0 프롬프트 — 실측 4종 + 스펙 v2 고정값 지시
22a882a docs(engineering): 모델 라우팅 적대 토론 판정 보존 + 킥오프 §10 반영
26df8cd docs(engineering): 잔디밭 스펙 v1 감사 원문 보존 + v2 개정·구현 킥오프 프롬프트
8e057b7 docs(engineering): 고객사×포지션 맵(잔디밭) 확정 스펙 — v4 구현·SQL 판정·발송 원장 신설
$ git diff --stat origin/main..main
8 files changed, 1989 insertions(+)
$ git rev-list --left-right --count origin/main...main
0	6
```

→ 서버에 없는 변경은 문서 8개에 담긴 커밋 6개입니다. 다만 작업 폴더에는 이 커밋들과 별개인 수정·미추적 파일도 있으므로 통째로 커밋하거나 지우면 안 됩니다.

```text
$ bash scripts/acceptance-0-2-unreachable-content.sh
[1/13] SECRET_PATTERNS_FILE=/dev/null 상속을 격리 -> PASS (exit=0)
[2/13] SECRET_PATTERNS_FILE=.secret-patterns.default 상속을 격리 -> PASS (exit=0)
[3/13] 일반 실행은 무해한 unreachable blob을 허용 -> PASS (exit=0)
[4/13] 일반 실행은 금지값이 든 unreachable blob을 차단 -> BLOCKED (exit=1)
[5/13] unreachable commit message의 금지값을 차단 -> BLOCKED (exit=1)
[6/13] unreachable tree path의 금지값을 차단 -> BLOCKED (exit=1)
[7/13] unreachable annotated tag message의 금지값을 차단 -> BLOCKED (exit=1)
[8/13] git fsck 실패는 검사 대상 없음으로 통과하지 않음 -> BLOCKED (exit=1)
[9/13] unreachable 객체 읽기 실패는 조용히 통과하지 않음 -> BLOCKED (exit=1)
[10/13] 알 수 없는 unreachable 객체형은 읽기 실패로 차단 -> BLOCKED (exit=1)
[11/13] 큰 unreachable blob 앞쪽의 금지값도 차단 -> BLOCKED (exit=1)
[12/13] 종료상태 실행은 무해한 unreachable blob도 차단 -> BLOCKED (exit=1)
[13/13] Git hook 환경에서도 바깥 저장소 무오염 -> PASS (exit=0)
CHECKED: 13
PASS: AC-19 일반 내용 검사와 종료상태 0건 조건 분리
real 38.21
user 9.45
sys 9.13
```

→ 기존 PR #23은 허용해야 할 사례 4개와 차단해야 할 사례 9개를 정확히 구분했습니다. 여기서 `BLOCKED`는 시험 대상이 기대대로 차단됐다는 사례 결과이며 전체 작업의 최종 상태가 아닙니다.

```text
$ bash scripts/acceptance-0-2.sh   # PR #23 작업 공간
PASS: no secret-pattern match in any tracked file, .env not tracked
PASS: 0-2 — 히스토리·객체·reflog·docs 리터럴 0건, 스캐너 뮤테이션 검출 확인
real 74.54
user 24.22
sys 19.47
```

→ 실제 공유 객체 저장소에 접근 불가능한 객체가 245개 있어도, PR #23의 내용 검사는 민감값 0건을 확인하고 통과했습니다.

```json
{"number":23,"state":"OPEN","mergeStateStatus":"CLEAN","headRefOid":"3ec842f7975a0de87fb17f155798e0338d884b09","statusCheckRollup":[{"name":"verify","status":"COMPLETED","conclusion":"SUCCESS"},{"name":"verify","status":"COMPLETED","conclusion":"SUCCESS"}],"url":"https://github.com/sangmokang/Valuehire_v6/pull/23"}
```

→ PR #23은 열려 있고 충돌 없음 상태이며, 현재 업로드된 머리 커밋에 대한 서버 검사 두 개가 모두 성공했습니다. 아직 합쳐지지는 않았습니다.

---

# 실행 프롬프트 시작 — 아래부터 그대로 투입

`$strict`

Valuehire_v6의 시작 검사에서 남은 `RED 2/19`와 장시간 무출력 때문에 생긴 `NOT_RUN` 오판을 근본 복구하라. 새 보안 해법을 발명하는 작업이 아니다. 이미 구현·업로드·검증된 PR #23을 회수하고, 로컬 `main`에 직접 쌓인 문서 커밋 6개를 별도 작업선으로 보존·배송하며, `scripts/session-status.sh`의 무출력·무한대기 가능성을 별도 인수 기준으로 고친 뒤 원래 명령을 다시 실행하는 작업이다.

이 프롬프트는 안전한 로컬 작업, `task/*` 작업선 업로드, 한국어 PR 생성, 이 작업이 만든 PR에 검증 증거 댓글을 쓰고 다시 읽는 것까지 승인한다. `main` 직접 push, PR merge, 운영 배포, 실제 민감값 출력, 사용자 파일 삭제, 복구 어려운 Git 객체 정리는 승인하지 않는다. PR 병합만 사장님 결정으로 남겨라.

## 0. 시작 즉시 읽을 정본과 현재 구현

다음 파일을 먼저 읽고 실제 줄을 goal 문서에 인용하라.

1. `AGENTS.md` 또는 현재 세션에 주입된 최상위 작업 계약
2. `~/.codex/skills/strict/SKILL.md`
3. `~/.claude/skills/harness/SKILL.md`
4. `docs/sot/coding-principles.md`의 P12·P13·P15·P20
5. `docs/sot/git-workflow.md`
6. `docs/sot/hook-contracts.md`
7. `docs/sot/verification-commands.md`
8. `scripts/session-status.sh`
9. `scripts/acceptance-0-2.sh`
10. `scripts/acceptance-0-5.sh`
11. `hooks/pre-push`
12. 기존 `worktrees/gate0-unreachable-secret-scan/` 전체 변경과 `docs/engineering/gate0-unreachable-secret-scan-goal-2026-08-17.md`
13. PR #23의 현재 원격 제목·본문·머리 커밋·서버 검사

이 파일은 세 작업을 나누는 조정용 goal prompt다. 현재 dirty 메인 작업 폴더에 새 goal 파일을 만들지 마라. PR #23은 이미 `docs/engineering/gate0-unreachable-secret-scan-goal-2026-08-17.md`가 있고, 문서 배송은 기존 position-map goal·스펙의 커밋을 그대로 전달하는 작업이라 새 파일을 8개 문서 diff에 섞지 않는다. 새 코드를 만드는 Phase D만 자기 clean worktree에서 가장 먼저 `docs/engineering/session-status-observability-goal-2026-08-18.md`를 만들고 현재 상태·근본 원인·AC·counter-AC·Harness 게이트·SOT·비범위·적대 검증 로그를 기록하라. Phase D 코드는 그 goal 문서보다 먼저 바꾸지 않는다.

## 1. 절대 안전 경계

- `git gc`, `git prune`, `git reflog expire`, `git reset --hard`, `git clean`, 사용자 파일 checkout/삭제, `.git` 직접 삭제를 실행하지 마라.
- `main`을 직접 push하거나 자동 merge하지 마라. `docs/sot/git-workflow.md`의 “오너도 직접 push 금지”를 그대로 지켜라.
- `.secret-patterns`의 내용, `git cat-file -p` 본문, 민감값이 될 수 있는 객체 내용은 화면·문서·PR에 출력하지 마라. 판정기는 내용을 내부 비교하고 SHA·형식·개수·종료값만 보고한다.
- 실제 저장소의 Git 객체 저장소는 모든 worktree가 공유한다. 민감값 뮤테이션은 반드시 `mktemp -d`의 독립 저장소와 합성 카나리에서만 실행하라.
- 현재 dirty worktree의 수정·미추적 파일은 사용자 소유다. stash, add, commit, 삭제, 이름 변경을 임의로 하지 마라. ref나 checkout 상태를 바꾸기 전에 경로·파일형·권한·크기·내용 지문으로 구성한 NUL 안전 manifest를 **파일로 저장하지 말고** 표준 출력 파이프로 즉시 SHA-256 하나로 접어라. 항목 수와 시작 전체 지문만 Phase D의 clean worktree goal 문서에 PR merge 전에 기록하고, 내용이나 민감한 경로는 퍼뜨리지 마라. Phase E 끝에 같은 계산을 다시 실행해 항목 수·전체 지문·`git status --porcelain=v1 -z`가 동일함을 증명하고, 관측성 PR에 시작·끝 항목 수·전체 지문·일치 여부만 한국어 증거 댓글로 남긴 뒤 원격 댓글을 다시 읽어 확인하라. 이 계산 자체가 dirty 작업 폴더에 새 파일을 만들면 실패다.
- 기존 PR #23의 구현을 복제하거나 다른 방식으로 다시 쓰지 마라. fresh evidence가 중간 이상 결함을 보일 때만 그 작업선에서 RED를 먼저 추가하고 최소 수정하라.
- 필수 검사의 `NOT_RUN`은 최종 상태가 아니다. 원인을 고치고 원래 명령을 재실행한다. 외부 병합만 남으면 `BLOCKED — 사장님 병합 대기`라고 하고 완료라고 하지 마라.

## 2. Phase A — 최신 상태 재측정과 문제 소유권 분리

아래를 읽기 전용으로 실행하고 명령·전체 출력을 goal 문서에 보존하라. 기준 SHA·개수와 다르면 최신 값이 우선이다.

```bash
git status --short --branch
git worktree list --porcelain
git rev-parse HEAD main origin/main task/gate0-unreachable-secret-scan origin/task/gate0-unreachable-secret-scan
git rev-list --left-right --count origin/main...main
git log --oneline --decorate origin/main..main
git diff --stat origin/main..main
gh pr view 23 --json number,state,title,body,url,mergeStateStatus,statusCheckRollup,reviewDecision,headRefOid,baseRefOid
/usr/bin/time -p bash scripts/session-status.sh
```

→ 실행자는 현재 상태·작업 공간·원격 검토 요청·원래 시작 검사 전체를 같은 시점에 다시 고정합니다. 하나라도 실패하면 해당 전체 출력을 goal 증거로 남기고 다음 단계의 전제로 숨기지 않습니다.

`session-status.sh`가 오래 조용해도 임의 중단하지 말고 프로세스가 살아 있는지 확인하면서 끝까지 판정하라. 끝난 뒤 실패한 하위 검사만 출력 숨김 없이 각각 재실행한다. 대체 검사는 진단용일 뿐이며 원래 명령의 판정을 대신하지 않는다.

소유권을 다음 세 갈래로 분리하라.

- A: `acceptance-0-2.sh` 거짓 차단 — 기존 PR #23 소유.
- B: `acceptance-0-5.sh`의 로컬 `main` 6커밋 앞섬 — 문서 배송 작업선 소유.
- C: `session-status.sh`의 진행 정보 은폐와 무한대기 가능성 — 별도 시작 검사 관측성 작업선 소유.

한 작업선이나 PR에 셋을 합치지 마라.

## 3. Phase B — 기존 PR #23 재사용·최종 재검증

작업 공간은 기존 `worktrees/gate0-unreachable-secret-scan`, 브랜치는 `task/gate0-unreachable-secret-scan`이다. 없거나 원격과 다르면 원인을 조사하고, 같은 이름으로 덮어쓰지 마라.

다음을 fresh 실행하라.

```bash
git status --short --branch
git rev-parse HEAD origin/task/gate0-unreachable-secret-scan
bash scripts/acceptance-0-2-unreachable-content.sh
bash scripts/acceptance-0-2.sh
bash verify.sh
gh pr view 23 --json number,state,title,body,url,mergeStateStatus,statusCheckRollup,reviewDecision,headRefOid,baseRefOid
```

→ PR #23의 로컬 코드·합성 방어·실제 검사·서버 상태를 한 묶음으로 재확인합니다. 예전 실행 기록이 아니라 현재 머리 커밋의 결과만 합격 근거입니다.

필수 판정:

- 브랜치 HEAD와 원격 PR 머리 커밋이 같고 작업 공간이 깨끗해야 한다.
- 합성 시험은 `CHECKED: 13`과 전체 성공을 내야 한다.
- 실제 0-2는 접근 불가능한 객체가 존재해도 실제 금지값이 없으면 성공해야 한다.
- 무해한 객체, 금지값을 넣은 blob·commit message·tree path·annotated tag, `git fsck` 실패, 객체 읽기 실패, 알 수 없는 형식, 50MiB 큰 객체, 종료상태, Git 훅 환경 외부 오염의 13개 대조가 유지돼야 한다.
- 서버 검사는 현재 PR 머리 커밋에 대해 전부 성공해야 한다. 예전 SHA의 초록은 인정하지 않는다.
- PR #23은 수정이 필요하지 않다면 손대지 않는다. 병합하지 않고 오너 검토 대기로 둔다.

known contaminated SHA 12개 부재만으로 합격시키지 마라. 이름이 알려지지 않은 미래 객체도 내용 검사로 차단해야 한다. 반대로 접근 불가능한 객체 “개수 0”은 `ACCEPTANCE_ENDSTATE=1`인 일회성 청소 종료 판정에서만 요구하고, 평상시 시작 검사에는 요구하지 않는다.

## 4. Phase C — 로컬 `main`의 문서 6커밋을 손실 없이 별도 배송

현재 기준은 `origin/main..main` 6커밋, 문서 8파일, 1,989줄 추가다. 최신 측정이 다르면 무엇이 늘거나 줄었는지 먼저 보고하고 현재 사용자 작업을 임의로 섞지 마라.

1. 현재 `main` SHA를 가리키는 보존 브랜치 `task/position-map-docs-delivery-20260818`를 만든다. 이미 존재하면 덮어쓰지 말고 SHA와 소유자를 확인한다.
2. 메인 작업 폴더의 dirty 파일을 건드리지 않도록 새 clean worktree `worktrees/position-map-docs-delivery-20260818`에서 그 브랜치를 연다.
3. 이 브랜치의 PR diff가 `origin/main..main`의 기존 커밋 내용만 포함하는지 파일 목록·통계·각 diff로 확인한다. 메인 작업 폴더의 수정·미추적 파일이 1개라도 포함되면 실패다.
4. 커밋을 새로 합치거나 메시지를 다시 쓰지 말고 먼저 현 6커밋을 보존한다. PR은 squash merge 정책이 최종 형태를 정한다.
5. 저장소 정본 검증과 pre-push를 통과한 뒤 `task/position-map-docs-delivery-20260818`만 origin에 push하고 한국어 PR을 만든다. 이 프롬프트는 task 브랜치 push와 PR 생성을 승인한다.
6. PR 본문은 `~/.codex/skills/strict/SKILL.md` §8-8 구조를 지키고, “사장님이 반드시 볼 부분”에는 문서 계약의 내용 승인 포인트만 1~5개 둔다. 테스트 숫자나 파일 목록으로 채우지 마라.
7. 생성 뒤 `gh pr view`로 실제 원격 제목·본문·머리 SHA를 다시 읽는다. CI가 현재 머리 SHA에서 성공해야 한다.
8. `main` 직접 push와 자동 merge는 금지한다.

PR #23과 이 문서 PR의 병합 순서는 최신 충돌·CI로 판단하되, 둘 다 사장님 승인 전에는 합치지 마라. 기존 PR #23 변경을 문서 PR에 복사해 한 PR로 만들지 마라.

## 5. Phase D — 장시간 무출력과 진짜 멈춤을 구분하는 별도 변경

브랜치와 worktree는 `task/session-status-observability-20260818`, `worktrees/session-status-observability-20260818`처럼 별도로 만든다. PR #23과 문서 PR을 섞지 않는다. 최신 `origin/main`에 필요한 선행 PR이 아직 병합되지 않았다면 의존 관계를 PR 본문에 명시하고, 병합 뒤 최신 `origin/main`에 다시 맞춘다.

구현 전에 `docs/sot/hook-contracts.md`의 세 줄 표준 출력 계약을 보존하거나, 시간 초과 상태 표현을 바꿔야 한다면 SOT를 먼저 고쳐라.

필수 행위:

1. stdout은 기존 계약의 최종 3줄만 유지한다. 진행 상황은 stderr로 내보내 기존 소비자를 깨지 않는다.
2. 각 하위 검사 시작 전에 순번·전체 수·스크립트 이름을, 종료 뒤 성공/실패·경과 시간을 stderr에 출력한다. 실제 민감값이나 하위 검사 전체 출력은 기본으로 재방출하지 않는다.
3. 한 하위 검사가 영원히 끝나지 않으면 전체 시작 검사가 영원히 멈추지 않도록 제한 시간을 둔다. macOS와 Linux 양쪽에서 동작하고, 환경변수로 짧은 합성 시험을 할 수 있어야 한다. 제한 시간이나 TERM·INT·HUP가 발생하면 부모 셸 하나만 끝내지 말고 그 검사가 만든 자식·손자 프로세스 전체를 종료하고 `wait`로 회수해 좀비·백그라운드 잔존 0건을 증명하라.
4. 기본 제한 시간은 300초로 시작하되 fresh 실측에서 가장 느린 정상 검사가 150초를 넘으면 그 실측의 2배 이상으로 올린다. 이 세션에서 실제 0-2는 74.54초였다. 환경변수로 합성 시험에서만 짧게 덮어쓸 수 있게 하고, 기본값·실측 근거·조정 방법을 SOT에 적는다.
5. 시간 초과는 일반 실패 1건으로 세탁하지 마라. “검사를 끝까지 판정하지 못함”을 stderr와 세 번째 줄에 식별 가능하게 표시하고 프로그램 성적을 0이 아닌 값으로 만든다. `RED: 0/N`으로 보이면 가짜 합격이다.
6. 하위 검사 실행 실패, 목록 생성 실패, 0개 발견, 시간 초과는 모두 조용한 성공을 금지한다.
7. 테스트 fixture는 독립 임시 저장소와 합성 스크립트만 쓴다. 빠른 성공, 일반 실패, 장시간 대기, 검사 0개, 하위 출력 은폐, stdout 정확히 3줄, stderr 진행 표시를 대조한다.
8. `session-status.sh`를 다시 부르는 이름의 `acceptance-*.sh`를 무심코 추가해 재귀 실행을 만들지 마라. 별도 검사 파일을 만들면 session-status 수집 대상과 로컬 push·CI 배선을 설계로 설명하고, 재귀 없음 뮤테이션을 남긴다.
9. 검사 파일·CI·SOT를 바꾸므로 P13과 P15에 따라 RED 커밋과 GREEN 커밋을 분리하고, 로컬 문지기와 CI가 같은 회귀를 실행하게 한다.
10. `scripts/session-status.sh` 자체가 최종 판정 숫자를 코드로 계산해야 한다. LLM이나 문서가 RED 숫자를 받아 쓰지 않는다.

AC-D의 최소 합성 사례:

- 빠른 성공 검사 1개: stderr에 START·PASS·경과, 최종 3줄 유지.
- 일반 실패 검사 1개: stderr에 이름·FAIL, RED 수 1 증가.
- 설정된 짧은 시간을 넘는 검사 1개: 정해진 시간 안에 종료, 이름·TIMEOUT, `UNKNOWN` 의미와 프로그램 성적 비0.
- 장시간 검사에서 자식과 손자 프로세스를 각각 하나씩 띄우는 사례: TIMEOUT·TERM·INT·HUP 뒤 관련 PID·잠금·임시 작업 잔존 0건.
- 검사 0개: `RED: UNKNOWN`, 프로그램 성적 비0.
- 진행 stderr를 제거하거나 하위 출력을 다시 숨기는 mutation: 회귀 시험 실패.
- timeout 처리를 `RED: 0/N`으로 바꾸는 mutation: 회귀 시험 실패.
- 회귀 시험이 session-status를 자기 자신에게서 다시 발견하게 만드는 mutation: 재귀 감지 후 실패.

## 6. Phase E — 병합 대기와 병합 뒤 로컬 기준선 회복

PR 준비·현재 SHA CI 성공까지는 자동 진행한다. merge는 하지 않는다. PR #23, 문서 배송 PR, 관측성 PR 가운데 사장님이 실제로 합칠 항목과 순서를 1층 결론에서 제시하고 `BLOCKED — 사장님 병합 대기`로 멈춘다. 이 상태를 완료라고 부르지 마라.

사장님이 병합한 뒤 재개하면:

1. `git fetch origin` 뒤 각 PR의 merge 상태와 `origin/main` 포함 여부를 원격에서 다시 읽는다.
2. 로컬 `main`의 옛 SHA와 dirty 작업을 먼저 보존한다. 옛 `main` 커밋이 문서 PR에 모두 포함·병합됐음을 파일 내용으로 대조하기 전에는 로컬 `main` ref를 움직이지 마라.
3. 메인 작업 폴더가 dirty면 같은 SHA의 명시적 WIP 보존 브랜치로 작업 폴더를 옮기고, Phase D goal에 기록한 시작값과 끝의 NUL 안전 manifest 항목 수·전체 SHA-256 및 `git status --porcelain=v1 -z`가 완전히 같은지 확인한다. stash·hard reset·파일 삭제는 사용하지 않는다. 관측성 PR에 두 값과 일치 판정만 증거 댓글로 남기고 `gh pr view --comments`로 readback한다.
4. `main`이 어느 worktree에서도 checkout되지 않고, 옛 SHA를 보존 브랜치가 가리키며, 원격 병합으로 내용이 보존됐다는 세 조건 뒤에만 로컬 `main` ref를 `origin/main`과 맞춘다. 실행 전후 SHA와 복구 명령을 기록한다.
5. dirty WIP 브랜치는 자동 삭제하지 않는다. 사용자 파일 정리는 이 작업 비범위다.
6. 최신 `origin/main`에서 새 clean worktree를 만들고 원래 명령과 관련 검증을 실행한다.

```bash
bash scripts/acceptance-0-2-unreachable-content.sh
bash scripts/acceptance-0-2.sh
bash scripts/acceptance-0-5.sh
bash verify.sh
bash scripts/session-status.sh
```

→ 병합 뒤 실제 보안 검사, 배송 상태, 저장소 비밀 스캔, 원래 시작 검사를 순서대로 다시 실행합니다. 마지막 줄이 실패 0건이어도 앞 명령 하나가 실패하거나 미판정이면 전체 완료가 아닙니다.

마지막 명령은 stdout 세 번째 줄이 `RED: 0/M`, `M>0`, `UNKNOWN` 0건이어야 한다. 프로그램 성적 0만으로는 합격이 아니다. 새 관측성 검사의 stderr에는 각 하위 검사 진행이 보여야 한다.

## 7. 기계 인수 기준

- **AC-1 기존 구현 회수:** PR #23의 머리 SHA가 원격 task 브랜치와 같고, 합성 시험 `CHECKED: 13`, 실제 0-2, `bash verify.sh`, 현재 SHA의 서버 검사가 모두 성공한다.
- **AC-2 보안 경계:** 무해한 접근 불가능 객체는 일반 실행에서 허용하고, 합성 금지값이 든 blob·commit·tree·annotated tag와 도구 실패·큰 객체는 차단한다. 일회성 종료상태 실행은 여전히 객체 0개를 요구한다.
- **AC-3 문서 보존:** 기존 로컬 `main`의 6커밋·8파일·1,989줄 또는 최신 재측정된 정확한 집합이 task 브랜치와 PR에 보존되고, dirty 파일은 PR diff 0건이다.
- **AC-4 기본 작업선 규칙:** `main` 직접 push 0건, 자동 merge 0건, 사용자 파일 삭제·stash·hard reset 0건이며 dirty manifest의 전후 항목 수·전체 SHA-256이 같다.
- **AC-5 진행 가시성:** 각 하위 검사 시작·종료·경과·실패/시간초과 이름이 stderr에 보이고 stdout은 SOT가 정한 최종 3줄이다.
- **AC-6 무한대기 차단:** 합성 hang가 정해진 시간 안에 TIMEOUT/UNKNOWN으로 끝나며 프로그램 성적 비0이고, 실제 74.54초 검사는 기본 300초 제한에 의해 잘리지 않으며, timeout·TERM·INT·HUP 뒤 자식·손자·잠금 잔존이 0건이다.
- **AC-7 배선:** 진행·시간초과 회귀 시험이 로컬 push와 CI에서 실제로 실행되고, 검사 0건 또는 재귀가 조용히 통과하지 않는다.
- **AC-8 원명령 회복:** 병합 후 clean 최신 기준에서 `bash scripts/session-status.sh`가 프로그램 성적 0, `RED: 0/M`, `M>0`, `UNKNOWN` 0건을 동시에 만족한다.
- **AC-9 원래 작업 재개:** AC-8 뒤에만 `docs/engineering/goal-prompts/codex-position-map-phase0-spec-v2-2026-08-17.md`의 미완료 항목을 fresh 상태로 재평가한다. 이미 완료된 산출물을 다시 만들지 않는다.
- **AC-10 최종 상태:** 필수 `NOT_RUN`·`FAIL`·`BLOCKED`가 0건이다. 사장님 merge 전에는 AC-10 불충족이다.

## 8. counter-AC — 아래 모습이면 전부 가짜 완료

- `git gc --prune=now`나 reflog 만료로 숫자만 0을 만든다.
- 알려진 SHA 12개만 검사하고 미래 객체 내용 검사를 뺀다.
- 모든 접근 불가능 객체를 무조건 허용해 실제 금지값도 놓친다.
- PR #23을 무시하고 같은 해법을 새 브랜치에 다시 구현한다.
- `acceptance-0-2.sh` 또는 `acceptance-0-5.sh`를 session-status 수집에서 빼 RED 수만 줄인다.
- 하위 검사 실패를 `|| true`, `continue-on-error`, 성공 종료값으로 바꾼다.
- 시간초과를 일반 RED 또는 성공으로 위장하고 `UNKNOWN`을 숨긴다.
- 시간초과 때 부모만 종료하고 자식·손자 프로세스나 잠금을 남긴다.
- stdout 3줄 계약을 진행 로그로 깨거나, 진행 로그를 다시 `/dev/null`로 숨긴다.
- 새 회귀 시험이 자기 자신을 재귀 호출하거나 CI에만/로컬에만 존재한다.
- dirty 메인 작업 폴더를 통째로 add·commit·stash·삭제한다.
- 기본 작업선 직접 push, 자동 merge, 검사 우회 push를 한다.
- 예전 서버 검사 성공을 최신 SHA 성공으로 보고한다.
- `bash verify.sh`나 개별 검사 성공으로 원래 `bash scripts/session-status.sh` 재실행을 대신한다.
- 사장님 merge 대기를 `SKIPPED`, `PASS`, 완료로 바꾼다.

## 9. Claude V1 1차 적대 검증

각 새 변경은 현재 SHA에서 `env -u ANTHROPIC_API_KEY claude -p`로 읽기 전용 검증한다. PR #23의 기존 판정은 보존하되 현재 SHA·현재 CI를 fresh 확인한다. 새 문서 배송 PR과 관측성 PR은 각각 독립 판정을 받는다.

반드시 다음을 공격하게 하라.

1. PR #23이 실제 금지값을 놓치면서 무해한 객체만 허용한 척하는가.
2. 13개 시험의 BLOCKED를 전체 작업 BLOCKED와 혼동했는가.
3. 문서 PR이 dirty·미추적 파일이나 PR #23 변경을 몰래 섞었는가.
4. 로컬 `main` ref 복구가 커밋·dirty 파일을 잃을 수 있는가.
5. 진행 표시가 stdout 3줄 소비자를 깨는가.
6. timeout이 느린 정상 검사를 거짓 실패시키거나 미판정을 RED/PASS로 세탁하는가.
7. 새 시험이 session-status 재귀를 만들거나 CI/로컬 한쪽에만 배선됐는가.
8. 서버 검사 SHA와 로컬 검증 SHA가 다른가.
9. merge 전인데 완료라고 과장했는가.
10. 원래 position-map Phase 0 구현을 중복하거나, Gate 0 복구를 핑계로 범위를 넓혔는가.

Claude 출력은 `~/.codex/skills/strict/SKILL.md` §8-7 형식 블록을 프롬프트 끝에 그대로 붙여 받는다. 빈 답·한 줄 Done·증거 없는 PASS는 무효다. 실행 명령 전문과 판정 본문을 goal 문서 `## 적대 검증 로그`에 그대로 보존한다.

## 10. Codex V2 2차 재공격

Claude 판정을 그대로 믿지 마라.

- Claude가 든 모든 SHA·파일·명령·성공/실패를 직접 재실행한다.
- Claude PASS는 놓친 재귀·시간초과 세탁·dirty 손실·오래된 CI SHA를 다시 공격한다.
- Claude FAIL은 실제 결함인지 과장인지 최소 fixture로 재현한다.
- 양쪽 판정의 일치/불일치를 표로 남긴다.
- 판정이 갈리면 다른 fixture 또는 새 Claude 호출로 해소할 때까지 결론내지 않는다.
- mutation은 독립 임시 저장소와 합성 값에서만 실행하고, 전후 HEAD/status 동일을 증명한다.

## 11. 중단·완료 계약

다음 경우에만 `BLOCKED`로 멈춘다.

- PR들이 현재 SHA에서 검증과 CI를 마쳤고, 남은 유일한 단계가 사장님 merge인 경우.
- 자격증명·GitHub 장애처럼 세 번 다른 복구 시도 뒤에도 외부 권한 없이는 진행 불가한 경우.
- local main ref를 맞추기 전에 사용자 dirty 파일 보존을 기계적으로 증명할 수 없는 경우.

그 전까지는 안전한 진단·작업선 생성·검증·task push·PR 생성·재검증을 계속한다. 최종 완료는 다음을 모두 만족할 때뿐이다.

1. 필요한 PR들이 실제 `origin/main`에 병합됨.
2. 현재 SHA의 CI 성공.
3. `bash scripts/acceptance-0-2-unreachable-content.sh` 성공.
4. `bash scripts/acceptance-0-2.sh` 성공.
5. `bash scripts/acceptance-0-5.sh` 성공.
6. `bash verify.sh` 성공.
7. 원래 `bash scripts/session-status.sh`가 `RED: 0/M`, `M>0`, `UNKNOWN` 0건.
8. 필수 `NOT_RUN`·`FAIL`·`BLOCKED` 0건.
9. dirty 사용자 파일 경로·내용 상태가 작업 전과 동일하고, 시작·끝 항목 수와 전체 SHA-256 일치 증거가 관측성 PR 댓글에 남아 readback됨.
10. Claude V1과 Codex V2 적대 검증 본문·교차표가 각 작업의 기존 goal 또는 Phase D goal 문서에 보존됨.

# 실행 프롬프트 끝

---

## 이 프롬프트의 적대 검증 로그

전체 명령·판정 본문·Codex 재현 출력은 `docs/engineering/gate0-not-run-red-recovery-prompt-verdict-2026-08-18.md`에 보존한다.

- Claude 호출 1: 안전장치가 요청을 거부해 판정 본문 없음. `NOT_RUN`으로 남기지 않고 문구·모델·도구 범위를 바꿔 재실행했다.
- Claude 현재판 최종 V1: `VERDICT: PASS`.
- Codex V2: Claude가 중간에 제기한 `.omx` 오염 주장은 `.git/info/exclude:7` 때문에 현재 저장소에서는 재현되지 않았지만, 다른 환경에 기대지 않도록 raw manifest 파일 자체를 없앴다. 추가로 timeout 때 자식·손자·잠금 회수와 goal 기록 위치를 보강했다.
- 최종 교차 판정: 중간 이상 불일치 0건, `VERDICT: PASS`.
