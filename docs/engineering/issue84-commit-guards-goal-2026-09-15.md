# 이슈 #84 — 로컬 커밋 위치 차단 목표 (2026-09-15)

## 결론

현재 로컬 훅은 본줄기 `main`의 직접 커밋을 막지 않습니다. 이번 변경은 본줄기 직접 커밋과 기본 작업 공간의 `task/*` 개발 커밋을 서로 다른 이유로 막고, 분리된 `task/*` 작업 공간의 정상 커밋은 허용하는 로컬 장치를 만듭니다. 원격 반영과 병합은 검증 뒤 별도 승인 경계에 남습니다.

## 판단 근거

GitHub 이슈 #84의 원문은 2026-09-10의 `f12ea33` 직접 커밋을 재발 원인으로 들고 A(main 직접 커밋)를 요청합니다. B(기본 작업 공간의 개발 커밋 차단)는 이번 사용자 요청에서 추가됐습니다. 두 판정은 메시지와 임시 저장소의 실제 `git commit` 결과를 분리해 입증합니다. Git 표준 훅은 `--no-verify`로 건너뛸 수 있고 CI는 개발자 로컬의 기본 작업 공간을 볼 수 없습니다. 최종 main 보호는 GitHub 보호 규칙·PR·CI가 맡으며, 현재 보호 설정은 미확인입니다.

**결정 카드**

> **무엇을** — 기존 `hooks/pre-commit`의 첫 단계에 Git 참조와 Git 공통 디렉터리로 판정하는 차단을 둡니다.
> **왜** — staged 파일 검사보다 앞에서 정확한 HEAD를 읽어 main과 기본 작업 공간을 독립적으로 차단할 수 있습니다.
> **버린 길** — 환경변수/설정 우회와 별도 신규 훅은 약화 경로와 설치 누락을 늘려 기각합니다.
> **대가** — 훅은 우회 가능하며 CI는 로컬 작업 공간을 관찰하지 못합니다.
> **되돌리기** — 이 작업 브랜치의 구현 커밋을 revert하고 훅·정본·인수 검사·CI 목록을 함께 되돌립니다.

## 정본, 시작 자격, 원인

- 위험등급 L3: 훅·CI·SOT를 함께 바꾸는 저장소 전역 동작 변경. 배송 상태 `NOT_APPLICABLE`: 내부 Git 검사이며 운영 제품 표면·DB/API 변경이 없습니다.
- 시작 원본: HEAD `f12ea335a0fd323bb3eec3ca0e300ae1ca9b0717`; origin/main `fc6beedc78019862bc2f1b3bf4c4ad3bbd8e845b`; `main...origin/main [ahead 1]` 및 다른 작업의 미커밋 변경 18개. 원본 상태는 마지막에 시작 목록과 바이트 단위로 대조합니다. `f12ea33` 정리와 `task/strict-workflow-sot-20260910`은 비범위입니다.
- 이슈 전용 `worktrees/issue84-commit-guards`의 `task/issue84-commit-guards-20260915`는 `origin/main`에서 분기합니다. `docs/sot/strict-workflow.md`와 `work-unit-policy.yaml`은 현재 원본 main에만 있고 origin/main에는 없어 읽기 전용으로 직접 확인했습니다. 두 파일을 이 작업 브랜치로 복사하지 않습니다.
- 직접 읽은 계약: `docs/sot/strict-workflow.md`, `coding-principles.md`, `principles.yaml`, `git-workflow.md`, `hook-contracts.md`, `verification-commands.md`, `hooks/pre-commit`, `hooks/pre-push`, `scripts/install-hooks.sh`, `scripts/acceptance-0-7.sh`, `scripts/verify/run-acceptance.sh`, `scripts/acceptance-semantic-mutations.sh`, `.github/workflows/verify.yml`. P11 hard 한도는 600 물리 줄입니다.
- 근본 원인: `hooks/pre-commit`은 staged change의 비밀·검사약화 등만 읽고 HEAD 참조와 기본 worktree 여부를 검사하지 않습니다. `hooks/pre-push`의 push/CI 판정은 커밋 전 차단을 대신하지 못합니다.
- `docs/sot/git-workflow.md`: `main` 직접 push 금지(오너 예외 없음), 개발 브랜치 `task/<name>`, 위치 `worktrees/<name>/`, 작업 1개=분리 worktree 1개=브랜치 1개. A는 이슈의 직접 커밋 재발 방지, B는 이 작업 위치 규약을 커밋 시점에 강제합니다.

## 입출력·오류·경계 계약

```text
entry: Git의 표준 pre-commit 호출 → hooks/pre-commit (stdin 없음)
input: 현재 HEAD의 `git symbolic-ref -q HEAD` 참조(unborn branch 포함),
       --git-dir, --git-common-dir, staged ACMR 목록
output: 허용 exit 0; 차단 exit 1 + stderr `BLOCKED: direct commit to main` 또는
        `BLOCKED: development commit in primary worktree` (사유는 분리)
error: Git 조회/디렉터리 정규화 실패 시 exit 1 + BLOCKED (fail-closed)
boundary: main은 모든 worktree에서 차단. 기본 worktree의 task/*는 차단.
          별도 worktree의 task/*는 기존 비밀·약화 검사를 통과해야 허용.
          task/* 이외 개발 브랜치는 git-workflow의 허용 범위 밖이며 이 AC의 허용 사례가 아니다.
          detached HEAD는 유효한 커밋 확인 뒤 두 정책의 범위 밖;
          unborn main도 `refs/heads/main`이므로 차단.
side effect: 훅 차단 시 HEAD 불변. Git의 기존 staged change는 그대로 남음.
```

Git 디렉터리 비교는 실제 경로로 정규화합니다. 기본 worktree는 Git이 반환한 git-dir과 git-common-dir이 같은 경우입니다. 별도 worktree의 git-dir은 공통 디렉터리 아래 `worktrees/<id>`여서 다릅니다. 저장소 파일 경로의 `worktrees/<name>/`과 Git 내부 관리 디렉터리의 `worktrees/<id>`는 서로 다른 의미입니다. 빈 staged 목록도 main/기본 위치 차단보다 뒤에서 처리합니다. 프로젝트 전용 허용 우회 변수·설정은 만들지 않습니다.

## EARS 인수 기준, 검증 명령, 반례

검증 본문은 `bash scripts/verify/run-acceptance.sh scripts/acceptance-commit-worktree-guards.sh`입니다. 모든 시나리오 커밋은 `mktemp -d`의 임시 저장소에서 Git 환경변수를 제거하고 `scripts/install-hooks.sh`를 실제로 실행해 재현합니다. 종료값은 0이 성공, 0이 아니면 실패라는 프로그램 성적입니다.

1. **A — 이슈 원문 중심.** When HEAD가 `refs/heads/main`이고 staged change를 `git commit`하면 시스템은 종료값 비0, stderr `BLOCKED: direct commit to main`, 전후 HEAD 동일로 거부해야 합니다. counter-AC: 소스 문자열만 존재하거나 `nothing to commit` 때문에 비0인 가짜 차단. 훅을 끈 대조군은 같은 입력으로 성공해야 합니다.
2. **허용 — A/B 공통 대조군.** When `task/example`을 별도 worktree에서 checkout하고 staged change를 `git commit`하면 시스템은 종료값 0과 새 HEAD로 허용해야 합니다. counter-AC: `core.hooksPath`가 미설치라 우연히 성공한 사례. 설치 readback과 훅 실행 trace를 확인합니다.
3. **B — 이번 요청 추가.** When 기본 worktree에서 `task/*`를 checkout하고 staged change를 `git commit`하면 시스템은 종료값 비0, stderr `BLOCKED: development commit in primary worktree`, 전후 HEAD 동일로 거부해야 합니다. counter-AC: main 차단 메시지로 B를 합격시킨 사례. 훅을 끈 대조군은 같은 입력으로 성공해야 합니다.
4. If fixture·검사 대상·실행 사례 중 하나가 0개이면 시스템은 PASS를 출력해서는 안 됩니다. 반례: `exit 0`, 빈 파일, 무출력 또는 `CHECKED: 0`으로 바꾼 인수 검사. 래퍼와 검사 본문의 0건 주입을 확인합니다.
5. When 기존 비밀 스캔과 workflow 약화의 정상·차단 사례를 다시 실행하면 종전 판정이 유지돼야 합니다. 검증: `bash verify.sh`, `bash scripts/acceptance-0-7.sh`, 기존 secret/workflow acceptance, 셸 문법 및 원칙 검사. counter-AC: B가 기존 인수 fixture의 기본 `task/*` clone을 막아 원래 검사 목적을 가린 위양성.

## Harness·Work Unit·적대검증·롤백

- WU1: goal과 독립 실제 commit 인수 검사 작성; 빠진 정책 때문에 RED 확인 후 로컬 RED 커밋으로 보존. 원격으로 RED를 보내지 않습니다.
- WU2: 기존 pre-commit에 최소 판정 추가, hook-contracts와 git-workflow를 함께 갱신; 첫 GREEN.
- WU3: 기존 인수 fixture가 새 위치 정책을 피하지 않고 정상 분리 worktree에서 원래 비밀·약화 차단을 검증하도록 연결. CI 고정 목록·verification 명령·인수 무결성 배선을 확인하고 회귀·고장 주입·독립 V1/V2 검증.
- 영향 반경: `git commit` 표준 훅 설치가 된 로컬 저장소의 main checkout과 기본 worktree의 task/* checkout. 데이터/DB/원격 ref 변화 없음. 모든 파괴적 시나리오는 임시 저장소에서만 실행합니다.
- 롤백 불변조건: revert가 훅만 제거하고 계약·인수·CI를 남겨 서로 다른 정책이 되면 실패입니다. revert 뒤 기존 secret/workflow 정상·차단 사례를 다시 확인해야 합니다.
- V1은 다른 독립 엔진에 산출물과 이 계약 및 실행 원문만 전달합니다. V2는 V1 명령을 재현하고 누락·오탐을 역공격합니다. 판정 한 곳의 일부러 고장 낸 사본이 인수 검사를 떨어뜨려야 하며, 검사 사례 0개도 실패해야 합니다.

## 검증 장부

세션 식별: `issue84-20260915-kt23`; 기준 시각 2026-09-15 23:41 KST. 증거 원문은 진행 중 이 문서에 보존합니다.

| 단계 | 명령 | 시각(KST) | 종료값 | 전체 출력 | 현재 SHA | 판정 |
|---|---|---|---:|---|---|---|
| 원칙 정본 직접 로드 | `cat docs/sot/coding-principles.md` | 23:40 | 0 | 전체 파일을 직접 읽음(P1~P24, P11 hard 600) | fc6beed | PASS |
| 원칙 장부 직접 로드 | `cat docs/sot/principles.yaml` | 23:40 | 0 | 전체 파일을 직접 읽음(34 IDs) | fc6beed | PASS |
| 원칙 검사 | `bash scripts/acceptance-principles-check.sh` | 23:40 | 0 | `VERDICT: PASS` / `SOT_LOAD: PASS docs/sot/coding-principles.md` / `LEDGER_LOAD: PASS docs/sot/principles.yaml` / `MECHANISMS: PASS 34/34 strict-contract-bindings` / `WIRING: PASS pre-push=1 ci=1` / `CHECKED: 34` | fc6beed | PASS |
| RED 실제 커밋 시험 | `bash scripts/verify/run-acceptance.sh scripts/acceptance-commit-worktree-guards.sh` | 23:44:55~23:45:06 | 1 | 전체 출력: `docs/engineering/issue84-commit-guards-red-output-2026-09-15.txt`; A/B는 exit 0·HEAD 전진, 허용은 exit 0·HEAD 전진, 5사례·4 fixture | fc6beed | FAIL(의도한 RED) |
| 첫 GREEN 임시 구현 사본 | `git clone . <mktemp>/repo; git apply <변경 diff>; git commit <임시>; bash scripts/install-hooks.sh; bash scripts/verify/run-acceptance.sh scripts/acceptance-commit-worktree-guards.sh` | 23:48:34~23:48:42 | 0 | 전체 출력: `docs/engineering/issue84-commit-guards-green-output-2026-09-15.txt`; A/B exit 1·각각 다른 stderr·HEAD 불변, 허용 exit 0·HEAD 전진, 5사례·4 fixture | 임시 7fd6eb1 | PASS |
| 기존 훅 6종 GREEN 회귀 | 위와 같은 임시 구현 사본에서 `bash scripts/verify/run-acceptance.sh scripts/acceptance-0-7.sh` | 23:49 | 0 | 전체 출력: `docs/engineering/issue84-existing-hook-regression-output-2026-09-15.txt`; 6/6 훅 ON 차단·OFF 허용 | 임시 구현 사본 | PASS |
| 최종 AC(첫 구현 커밋) | `bash scripts/verify/run-acceptance.sh scripts/acceptance-commit-worktree-guards.sh` | 23:51:23~23:51:30 | 0 | 전체 출력: `docs/engineering/issue84-final-ac-output-2026-09-15.txt`; A/B exit 1·stderr 분리·HEAD 불변, 허용 exit 0·HEAD 전진, 5사례·4 fixture | 352b72f | PASS |
| 0건 공격 | `bash scripts/verify/run-acceptance.sh scripts/acceptance-commit-worktree-guards.sh --self-test-empty` | 23:51 | 1 | 전체 출력: `docs/engineering/issue84-zero-cases-output-2026-09-15.txt`; CHECKED: 0, VERDICT: FAIL | 352b72f | PASS(거부 판정) |
| A 판정 한 줄 고장 | `refs/heads/main` 비교를 `refs/heads/nonmain`으로 바꾼 mktemp 커밋 사본에서 원 인수 명령 | 23:51:59~23:52:07 | 1 | 전체 출력: `docs/engineering/issue84-main-predicate-mutation-output-2026-09-15.txt`; AC1 FAIL·AC3 PASS | 임시 cbca01c | PASS(시험 감도) |
| B 판정 한 줄 고장 | 기본/공통 git-dir 비교를 `/nonexistent`로 바꾼 mktemp 커밋 사본에서 원 인수 명령 | 23:56:02~23:56:14 | 1 | 전체 출력: `docs/engineering/issue84-primary-predicate-mutation-output-2026-09-15.txt`; AC3 FAIL·AC1 PASS | 임시 99f4c5a | PASS(시험 감도) |
| 실제 pre-push 첫 실행 | mktemp clone·bare에서 `git push --dry-run <bare> HEAD:refs/heads/task/issue84-commit-guards-20260915` | 23:57:03~00:00 | 1 | 전체 출력: `docs/engineering/issue84-prepush-output-2026-09-15.txt`; 신규 인수는 ok, hs-a4·silent-failure-lint-mutations는 BLOCKED. 전체 원명령 FAIL | 352b72f | FAIL(복구 필요) |
| 하위 실패 원인 재현 | 352b72f의 임시 clone에서 두 원 인수 명령 | 00:03 | 각 1 | 전체 출력: `issue84-hs-a4-prefixed-fail-output-2026-09-16.txt`, `issue84-silent-lint-prefixed-fail-output-2026-09-16.txt` | 352b72f | REPRODUCED |
| 하위 원명령 수정 후 재실행 | `bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-a4.sh`; `... scripts/acceptance-silent-failure-lint-mutations.sh` | 00:02~00:04 | 각 0 | 전체 출력: `issue84-hs-a4-diagnosis-output-2026-09-16.txt`(33건), `issue84-silent-lint-diagnosis-output-2026-09-16.txt`(34건) | 352b72f+미커밋 수정 | PASS(하위만) |

첫 병렬 검증에서 기존 훅 0-7, semantic mutations, mechanism registry의 원본 상태
비교가 새 증거 파일 생성과 충돌해 각각 FAIL했습니다. 출력은 각 기존 로그의 첫
실행에 있었고, 파일 이름을 고정한 뒤 **같은 원명령**을 순차 재실행해 6/6,
30개 대상×5 무력화, 명부 31건 모두 PASS를 받았습니다. 병렬 실패를 대체
검사의 PASS로 쓰지 않습니다.

pre-push 하위 실패의 원인은 두 가지입니다. 새 훅이 초기 커밋 전(unborn) HEAD에
`git rev-parse --symbolic-full-name HEAD`를 써 P21 fixture가 검사 전 fatal로
끝났습니다. P3의 기본 clone은 HEAD가 task/*라 위치 정책이 먼저 차단했습니다.
훅은 `git symbolic-ref -q HEAD`로 unborn 참조를 읽게 수정했고, 기존 fixture는
P21용 비개발 참조와 P3용 실제 분리 task worktree로 옮겼습니다. 두 검사 모두
원래 크기/경로·index blob 판정을 다시 확인했습니다. **전체 pre-push는 아직
재실행 전이므로 PASS가 아닙니다.**

## 적대 검증 로그

V1/V2 실행 신원·명령·전체 출력·판정 비교를 여기에 덧붙입니다. 미실행을 PASS로 적지 않습니다.
