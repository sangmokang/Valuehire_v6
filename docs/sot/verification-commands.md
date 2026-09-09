# Valuehire v6 — 이 저장소의 실제 게이트 명령 (SOT)

최종 갱신: 2026-09-09 (스텝 수 26→29 실측 정정 — PostgreSQL 준비·Invoice 자가시험 스텝 누락 복구, hs-kickoff·hs-kickoff-mutations 추가)
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

**워크플로 스텝 29개 전부**를 적는다(2026-08-12 V1 D6: 이전 판은 `bash ...` 직접 명령만 적어 인라인 본문 스텝이 목록에서 빠졌고, 운영자가 실제로 무엇이 도는지 잘못 판단할 수 있었다). 아래는 `verify.yml` 의 `- name:` 스텝 순서 그대로다.

| # | 스텝 이름 | 실행 내용 |
|---|---|---|
| 1 | 비밀 스캔 (verify.sh) | `bash verify.sh` — 추적 파일 전체 |
| 2 | Strict 원칙 정본·장부·배선 검사 | `bash scripts/acceptance-principles-check.sh` — 34개 정본 문구·장치·명시적 pre-push/CI 배선 |
| 3 | Strict 원칙 적대 fixture·500/501 경계 | `bash scripts/acceptance-principles-mutations.sh` — 정상 fixture와 반례 41건·500/501 경계 |
| 4 | Strict 전역 스킬 잠금 장치 격리 회귀 | `bash scripts/acceptance-guard-global-skill-files.sh` — lock/check/unlock/recover와 동일 UID 한계 |
| 5 | P3 조용한 실패 문법·오탐 회귀 | `scripts/acceptance-silent-failure-lint.sh` + mutation 34건 — 대소문자 확장자 전체 소스와 스테이지 blob 판정 |
| 6 | HumanSearch G1 클린룸 경계 | 인라인 8개 — `scripts/acceptance-hs-cleanroom.sh`, `scripts/acceptance-hs-cleanroom-mutations.sh`, `scripts/acceptance-hs-cleanroom-absolute-paths.sh`, `scripts/acceptance-hs-cleanroom-absolute-contexts.sh`, `scripts/acceptance-hs-cleanroom-colon-paths.sh`, `scripts/acceptance-hs-cleanroom-file-urls.sh`, `scripts/acceptance-hs-cleanroom-hook-env.sh`, `scripts/acceptance-hs-cleanroom-hook-env-mutations.sh` |
| 7 | HumanSearch G2 테스트 게이트 (정적·단위 + runtime import 증명) | 인라인 — `uv` 설치 후 `scripts/acceptance-hs-gates.sh`, `scripts/acceptance-hs-gates-mutations.sh`, `scripts/acceptance-hs-gates-antiforge.sh` (정적 ruff/mypy + pytest 수집·runtime import 증명) |
| 8 | 히스토리 전량 스캔 (도달 가능한 모든 blob) | 인라인 — 도달 가능한 모든 blob 을 열어 자격증명 패턴 대조 |
| 9 | 인수 검사 0-2 상시 내용 검사와 종료상태 분리 (AC-19) | `bash scripts/acceptance-0-2-unreachable-content.sh` — 환경 격리·네 객체형·도구 실패·큰 객체·종료상태·훅 환경 무오염 13개 합성 사례 (AC-19) |
| 10 | 인수 검사 0-6 (가짜 검증 스크립트 0건) | `bash scripts/acceptance-0-6.sh` |
| 11 | 인수 검사 0-7 (훅이 위반 6종을 실제로 차단하는가) | `bash scripts/acceptance-0-7.sh` — 훅 위반 6종 시연 |
| 12 | 인수 검사 0-5 (push · CI 연결) | `bash scripts/acceptance-0-5.sh` — **`main` 브랜치에서만** (`if: github.ref == 'refs/heads/main'`) |
| 13 | 억제 만료 스캔 (suppressions.yaml) | 인라인 — `suppressions.yaml` 의 expiry 형식·경과 |
| 14 | 강제 장치 존재 검사 (hooks/) | 인라인 — `hooks/pre-commit`·`pre-push` 존재·실행권한 |
| 15 | 셸 스크립트 문법 검사 | 인라인 — `git ls-files '*.sh'` 전부 `bash -n` |
| 16 | 패턴 파일 자체에 실제 비밀이 없는지 (자기 오염 방지) | 인라인 — `.secret-patterns.default` 에 값 리터럴 없는지 |
| 17 | 인수 검사 hs-a3 (세션 계열 자격증명 탐지) | `bash scripts/acceptance-hs-a3.sh` — 세션 계열 자격증명 (AC-A3) |
| 18 | 데이터 노출 스캔 (크기 · 금지경로 · 기록 · 개인정보 내용) | `bash scripts/scan-data-exposure.sh all` — 크기·금지경로·기록·개인정보 (AC-A4) |
| 19 | 인수 검사 hs-a4 (대용량·산출물 차단이 실제로 도는가) | `bash scripts/acceptance-hs-a4.sh` — 차단이 실제로 도는가 (AC-A4) |
| 20 | 인수 검사 secret-webhook-vendor (웹훅·벤더 키 탐지 · AC-S1) | `bash scripts/acceptance-secret-webhook-vendor.sh` — 웹훅·벤더 키 (AC-S1) |
| 21 | 인수 검사 verified-sha (초록불이 SHA 에 귀속되는가 · P23) | `bash scripts/acceptance-verified-sha.sh` — 현재 SHA 귀속 진리표(P23) |
| 22 | 인수 검사 ci-step-integrity (스텝을 조용히 끄지 못하는가) | `bash scripts/acceptance-ci-step-integrity.sh` — 조건부·오류무시·echo 대체 차단 |
| 23 | 인수 검사 semantic-mutations (검사를 껐을 때 반드시 빨개지는가) | `bash scripts/acceptance-semantic-mutations.sh` — 인수 검사 무력화 5종 전량 차단 |
| 24 | 인수 검사 verify-ac-m (mechanism 명부 대조 · AC-M) | `bash scripts/acceptance-verify-ac-m.sh` — mechanism 명부 대조 (AC-M) |
| 25 | PostgreSQL 서버 준비 (Invoice 런타임 검사용) | 인라인 — Invoice 실증용 임시 PostgreSQL 설치·기동 |
| 26 | 인수 검사 invoice (채용 수수료 계산·계약·플랫폼 동등성) | `bash scripts/verify/run-acceptance.sh scripts/acceptance-invoice.sh` — 채용 수수료 계산·기한·계약 변조·Codex/Claude 스킬 동등성 + 임시 PostgreSQL 마이그레이션·동시성·저장/전달 RPC |
| 27 | Invoice 게이트 자가시험 (위조 출력·스텝 무력화 차단) | 인라인 — 위조 출력·스텝 무력화가 반드시 빨개지는지 |
| 28 | 인수 검사 hs-kickoff (HumanSearch 착수 정리 · WU-0A) | `bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-kickoff.sh` — 미병합 6건 처분표·CI 스텝 수 일치·설계서 역사 보존·착수 프롬프트·배선·Codex 판정 문서 12건 |
| 29 | 인수 검사 hs-kickoff-mutations (WU-0A 검사를 속일 수 있는가) | `bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-kickoff-mutations.sh` — 양성 1 + 음성 6(실행 줄 주석 위장·오류무시 지시·빈 이름 표 행·처분 대상 중복·근거 자리표시자·판정 문서 첫 줄 위조) 7건 |

*(1번 앞에 `actions/checkout` 이 있고 `fetch-depth: 0` 이다 — 8번이 과거 blob 을 열려면 필요하다.)*

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
- 이 표는 2026-08-22 실행 결과의 스냅샷이다. 스크립트가 추가/삭제되면 다시 확인해야 한다.
