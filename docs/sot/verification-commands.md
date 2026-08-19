# Valuehire v6 — 이 저장소의 실제 게이트 명령 (SOT)

최종 갱신: 2026-08-19 (PR #31 P3 문법 판정·독립 작업 배선 기준)
근거: `docs/engineering/docs-sot-restructure-goal-2026-08-08.md`

## 현재 규칙

**이 저장소는 make 레포도 npm 레포도 아니다.** `Makefile`·`package.json`이 없고, `make -n red-ledger`는 `No rule to make target` 로 실패한다(2026-08-08 실행 확인). `~/.claude/skills/harness/SKILL.md`가 기본 전제하는 `make task` / `make verify` / `make ship` 은 이 저장소에 아직 없다 — 아래가 대신 쓰는 실제 명령이다.

| 게이트 | harness 스킬의 기본 명령 | 이 저장소의 실제 명령 |
|---|---|---|
| 0 — 시작 자격(RED 미해결 확인) | `make red-ledger` | `bash scripts/session-status.sh` (stdout 3번째 줄 `RED: N/M`) |
| 2 — 워크트리 파기 | `make task NAME=...` | `git worktree add worktrees/<name> -b task/<name>` |
| 4 — 검증 | `./verify.sh` | `bash verify.sh` (비밀 스캔) — CI(`verify.yml`)가 실제로 도는 검사 전체는 아래 "CI가 실제로 돌리는 것" 표가 정본이다(요약을 여기 두 번 적으면 반드시 갈라진다 — 2026-08-12 REV2-D2 실측). `scripts/acceptance-0-2.sh`는 로컬 전용(`.secret-patterns`에 실제 리터럴이 있어야 해서 CI에 못 올림, 스크립트 주석에 명시) |
| 5 — 배송 | `make ship` | 아직 스크립트 없음 — `git push -u origin task/<name>` 후 `gh pr create` 수동 실행. push 시 `hooks/pre-push`가 verify.sh + acceptance-*.sh 전량(glob)을 재실행 |
| 6 — 종료 | `make task-done NAME=...` | `git worktree remove worktrees/<name>` 수동 실행 |

### CI(`​.github/workflows/verify.yml`)가 실제로 돌리는 것

**워크플로는 독립 작업 4개, checkout 4개와 이름 있는 검증 23개, 총 27개 단계다.** `principles-structure`, `p3`, `verify`는 이 저장소 정책상 필수 검사이며 서로 `needs`(다른 작업의 성공을 기다리는 설정)가 없다. `p1-completion-diagnostic`는 32개 전체 완료 여부를 알리는 진단이다. 여기서 “필수”는 저장소 문서의 병합 판단 기준이지, GitHub branch protection의 required check가 실제 활성이라는 뜻이 아니다. 보호 설정은 아래 한계 절의 원격 실측만 근거로 판단한다.

전체 완료 진단은 기존 명령 `bash scripts/acceptance-principles-check.sh`를 인자 없이 그대로 실행한다. 종료값 1이면 `P1_UNMET` 원문과 `P1_COMPLETION_RAW_EXIT: 1`, `P1_COMPLETION_RESULT: UNMET`을 로그에 남기고 다른 세 작업을 막지 않는다. 종료값 2 이상은 검사 자체를 수행하지 못한 것이므로 진단 작업도 실패한다. 따라서 필수 검사 세 작업이 초록이어도 32개 원칙 전체 완료를 뜻하지 않는다.

| # | 작업 | 스텝 이름 | 실행 내용 |
|---|---|---|---|
| 1 | `principles-structure` | P1 원칙 장부 필수 파일 존재 검사 | `principles.yaml`·검사기 존재·실행권한 확인 |
| 2 | `principles-structure` | P1 원칙 장부 mutation 검사 | `bash scripts/acceptance-principles-mutations.sh` — 격리 반례·대조군과 작업 이름·모드 고정 |
| 3 | `principles-structure` | 전역 strict guard 격리 복구·한계 검사 | `bash scripts/acceptance-guard-global-skill-files.sh` — rollback/recover와 동일 UID 우회 재현 |
| 4 | `principles-structure` | P1 원칙 장부 스키마·정적 배선 검사 | `bash scripts/acceptance-principles-check.sh --schema-only` — 필수 구조 검사 |
| 5 | `p1-completion-diagnostic` | P1 원칙 32개 전체 완료 판정 | 인자 없는 기존 전체 명령 — 31/32 미충족은 경고와 원문으로 남고, 검사 불가는 실패 |
| 6 | `p3` | P3 조용한 실패 문법 판정 | `bash scripts/acceptance-silent-failure-lint.sh` + `bash scripts/acceptance-silent-failure-lint-mutations.sh` — P1 진단과 독립 실행 |
| 7 | `verify` | 비밀 스캔 (verify.sh) | `bash verify.sh` — 추적 파일 전체 |
| 8 | `verify` | HumanSearch G1 클린룸 경계 | 인라인 8개 — `scripts/acceptance-hs-cleanroom.sh`, `scripts/acceptance-hs-cleanroom-mutations.sh`, `scripts/acceptance-hs-cleanroom-absolute-paths.sh`, `scripts/acceptance-hs-cleanroom-absolute-contexts.sh`, `scripts/acceptance-hs-cleanroom-colon-paths.sh`, `scripts/acceptance-hs-cleanroom-file-urls.sh`, `scripts/acceptance-hs-cleanroom-hook-env.sh`, `scripts/acceptance-hs-cleanroom-hook-env-mutations.sh` |
| 9 | `verify` | HumanSearch G2 테스트 게이트 | 인라인 — `uv` 설치 후 `scripts/acceptance-hs-gates.sh`, `scripts/acceptance-hs-gates-mutations.sh`, `scripts/acceptance-hs-gates-antiforge.sh` |
| 10 | `verify` | 히스토리 전량 스캔 | 인라인 — 도달 가능한 모든 blob을 열어 자격증명 패턴 대조 |
| 11 | `verify` | 인수 검사 0-2 상시/종료상태 분리 | `bash scripts/acceptance-0-2-unreachable-content.sh` |
| 12 | `verify` | 인수 검사 0-6 | `bash scripts/acceptance-0-6.sh` |
| 13 | `verify` | 인수 검사 0-7 | `bash scripts/acceptance-0-7.sh` — 훅 위반 6종 시연 |
| 14 | `verify` | 인수 검사 0-5 | `bash scripts/acceptance-0-5.sh` — **`main` 브랜치에서만** |
| 15 | `verify` | 억제 만료 스캔 | 인라인 — `suppressions.yaml`의 expiry 형식·경과 |
| 16 | `verify` | 강제 장치 존재 검사 | 인라인 — `hooks/pre-commit`·`pre-push` 존재·실행권한 |
| 17 | `verify` | 셸 스크립트 문법 검사 | 인라인 — `git ls-files '*.sh'` 전부 `bash -n` |
| 18 | `verify` | 패턴 파일 자체 실값 검사 | 인라인 — `.secret-patterns.default`에 값 리터럴 없는지 |
| 19 | `verify` | 인수 검사 hs-a3 | `bash scripts/acceptance-hs-a3.sh` |
| 20 | `verify` | 데이터 노출 스캔 | `bash scripts/scan-data-exposure.sh all` |
| 21 | `verify` | 인수 검사 hs-a4 | `bash scripts/acceptance-hs-a4.sh` |
| 22 | `verify` | 인수 검사 secret-webhook-vendor | `bash scripts/acceptance-secret-webhook-vendor.sh` |
| 23 | `verify` | 인수 검사 verify-ac-m | `bash scripts/acceptance-verify-ac-m.sh` |

→ 무엇을 적었나: 서버가 실행하는 23개 이름 있는 검사를 작업별로 나눴다. / 무엇이 달라졌나: P1 구조 검사는 필수, 32개 전체 완료는 비차단 진단, P3와 기존 회귀는 독립 실행이다. / 판단: 좋은 변화지만, 실제 서버 로그가 네 작업의 실행을 확인하기 전에는 배선 완료로 단정하지 않는다.

*(네 작업 각각 앞에 `actions/checkout`이 있다. `principles-structure`와 `verify`는 `fetch-depth: 0`이며, `verify`의 기록 전량 검사가 과거 blob을 열려면 이 설정이 필요하다.)*

**CI는 고정 목록이고 로컬 `pre-push`는 글로브(이름 규칙 자동 수집)다.** 그래서 새 인수 스크립트를 만들면 로컬에서는 저절로 돌지만 CI에서는 한 줄도 안 돈다 — P15③("로컬에만 있는 검사는 없는 것으로 친다")에 걸린다. **새 `scripts/acceptance-*.sh`를 추가하는 PR은 `verify.yml`과 이 표 양쪽에 자기 줄을 함께 넣어야 한다.**

### 데이터 노출 판정기 — `scripts/scan-data-exposure.sh`

후보자 데이터가 git으로 새는 세 경로를 **한 판정기**로 막는다. CI도 인수 검사도 **같은 파일을 실행**한다 — 규칙을 두 벌로 적으면 반드시 갈라진다(2026-08-12 실측: 인라인 본문 시절엔 CI 스텝에 `if: ${{ false }}`를 넣어 영구히 꺼도 로컬 방어 셋이 전부 초록이었다).

| 모드 | 무엇을 보나 |
|---|---|
| `tracked` | 지금 추적 중인 파일의 크기(1MB)·금지 경로 |
| `history` | **도달 가능한 모든 blob**의 크기·금지 경로 — 커밋 후 지운 파일의 과거 본문까지 |
| `pii` | `*.csv`·`*.tsv`·`*.sql`의 **개인정보 컬럼 조합** — 크기·확장자로는 안 잡히는 것 |
| `all` | 셋 다 (CI가 쓰는 모드) |

종료값 `0=PASS / 1=FAIL / 2=NOT_RUN`. **검사 대상 0건은 통과가 아니라 `NOT_RUN`이다**(P20).

`pii`는 오탐을 막기 위해 **두 조건을 모두** 만족해야 차단한다 — ① 개인정보 컬럼 낱말 2종 이상 ② 실제 데이터를 담은 형태(CSV는 데이터 행 1줄 이상, SQL은 `INSERT`/`VALUES`/`COPY`). 그래서 **`CREATE TABLE candidates(name, email)` 같은 스키마 정의는 통과한다** — 정상 마이그레이션까지 막으면 개발이 멈춘다.

**금지 경로 목록은 `hooks/pre-commit`과 이 판정기 두 곳에 있다**(훅은 '스테이지된 것'만 보므로 별도 코드다). 한쪽만 넓히면 조용히 갈라지므로 `scripts/acceptance-hs-a4.sh`가 두 목록의 동치를 검사한다.

## 시행 지점

이 문서 자체가 "가정 대신 실행 확인"의 산출물이다. 명령이 바뀌면(예: `Makefile`이 나중에 생기면) 이 표를 그 시점에 다시 실행해서 갱신한다 — 표를 먼저 고치고 나중에 확인하지 않는다.

## 비범위 / 한계

- `main` 브랜치 GitHub 보호 규칙의 실제 활성화 여부는 확인하지 않았다(`docs/sot/git-workflow.md` 한계와 동일).
- 이 표는 2026-08-08 실행 결과의 스냅샷이다. 스크립트가 추가/삭제되면 다시 확인해야 한다.
