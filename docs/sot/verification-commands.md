# Valuehire v6 — 이 저장소의 실제 게이트 명령 (SOT)

최종 갱신: 2026-08-21 (명령은 실행으로 확인, Work Unit 순서는 계약으로 확정)
근거: `docs/engineering/docs-sot-restructure-goal-2026-08-08.md`,
`docs/engineering/work-unit-methodology-goal-2026-08-21.md`

## 현재 규칙

**이 저장소는 make 레포도 npm 레포도 아니다.** `Makefile`·`package.json`이 없고, `make -n red-ledger`는 `No rule to make target` 로 실패한다(2026-08-08 실행 확인). `~/.claude/skills/harness/SKILL.md`가 기본 전제하는 `make task` / `make verify` / `make ship` 은 이 저장소에 아직 없다 — 아래가 대신 쓰는 실제 명령이다.

| 게이트 | harness 스킬의 기본 명령 | 이 저장소의 실제 명령 |
|---|---|---|
| 0 — 시작 자격(RED 미해결 확인) | `make red-ledger` | `bash scripts/session-status.sh` (stdout 3번째 줄 `RED: N/M`) |
| 2 — 워크트리 파기 | `make task NAME=...` | `git worktree add worktrees/<name> -b task/<name>` |
| 4 — 검증 | `./verify.sh` | `bash verify.sh` (비밀 스캔) — CI(`verify.yml`)가 실제로 도는 검사 전체는 아래 "CI가 실제로 돌리는 것" 표가 정본이다(요약을 여기 두 번 적으면 반드시 갈라진다 — 2026-08-12 REV2-D2 실측). `scripts/acceptance-0-2.sh`는 로컬 전용(`.secret-patterns`에 실제 리터럴이 있어야 해서 CI에 못 올림, 스크립트 주석에 명시) |
| 5 — 배송 | `make ship` | 아직 스크립트 없음 — `git push -u origin task/<name>` 후 `gh pr create` 수동 실행. push 시 `hooks/pre-push`가 verify.sh + acceptance-*.sh 전량(glob)을 재실행 |
| 6 — 종료 | `make task-done NAME=...` | `git worktree remove worktrees/<name>` 수동 실행 |

### Work Unit 정책과 실행 순서

Work Unit의 개수·완료 조건·최종 관문 순서·고위험 검토·비용·롤백 경계는 `docs/sot/work-unit-policy.yaml`이 유일한 기계 정본이다. 사람이 읽는 설명은 YAML에서 생성한 `docs/sot/work-unit-policy.md`를 사용하며, 이 문서에 정책 문장을 복제하지 않는다.

- 정상 정책·생성 문서: `bash scripts/acceptance-work-unit-policy.sh`
- 값·순서·스키마·생성 문서 반례: `bash scripts/acceptance-work-unit-policy-mutations.sh`
- 원칙 P1~P24 장부: `bash scripts/acceptance-principles-check.sh`

로컬 `pre-push`는 `acceptance-*.sh` 글로브로 세 검사를 자동 수집한다. CI는 아래 고정 목록에서 각각 명시적으로 실행한다.

### CI(`​.github/workflows/verify.yml`)가 실제로 돌리는 것

**워크플로 스텝 25개 전부**를 적는다(2026-08-12 V1 D6: 이전 판은 `bash ...` 직접 명령만 적어 인라인 본문 스텝이 목록에서 빠졌고, 운영자가 실제로 무엇이 도는지 잘못 판단할 수 있었다). 아래는 `verify.yml` 의 `- name:` 스텝 순서 그대로다(2026-08-21 Strict 원칙 직접 로드·Work Unit 구조화 정책·SHA 귀속·CI 무력화 저항 스텝 포함).

| # | 스텝 이름 | 실행 내용 |
|---|---|---|
| 1 | 비밀 스캔 (verify.sh) | `bash verify.sh` — 추적 파일 전체 |
| 2 | Strict 원칙 정본·장부·배선 검사 | `bash scripts/verify/run-acceptance.sh scripts/acceptance-principles-check.sh` — 원칙 계약 34개, 장치, 명시적 pre-push/CI 배선 |
| 3 | Strict 원칙 적대 fixture·500/501 경계 | `bash scripts/verify/run-acceptance.sh scripts/acceptance-principles-mutations.sh` — 정상 fixture, 원칙 반례, 500/501 경계 |
| 4 | Work Unit 구조화 정책·생성 문서 검사 | `bash scripts/verify/run-acceptance.sh scripts/acceptance-work-unit-policy.sh` — YAML 정책 19개 계약과 생성 문서 byte-exact 일치 |
| 5 | Work Unit 정책 변조·동의어 우회 검사 | `bash scripts/verify/run-acceptance.sh scripts/acceptance-work-unit-policy-mutations.sh` — 값·순서·스키마·문서 변조와 감사 동의어 우회 3종 |
| 6 | Strict 전역 스킬 잠금 장치 격리 회귀 | `bash scripts/verify/run-acceptance.sh scripts/acceptance-guard-global-skill-files.sh` — lock/check/unlock/recover와 동일 UID 한계 |
| 7 | HumanSearch G1 클린룸 경계 | 인라인 — `scripts/acceptance-hs-cleanroom.sh`, `scripts/acceptance-hs-cleanroom-mutations.sh`, `scripts/acceptance-hs-cleanroom-absolute-paths.sh`, `scripts/acceptance-hs-cleanroom-absolute-contexts.sh`, `scripts/acceptance-hs-cleanroom-colon-paths.sh`, `scripts/acceptance-hs-cleanroom-file-urls.sh`, `scripts/acceptance-hs-cleanroom-hook-env.sh`, `scripts/acceptance-hs-cleanroom-hook-env-mutations.sh`를 각각 `bash scripts/verify/run-acceptance.sh <검사>`로 실행 |
| 8 | HumanSearch G2 테스트 게이트 (정적·단위 + runtime import 증명) | 인라인 — `uv` 0.11.3 고정 후 `scripts/acceptance-hs-gates.sh`, `scripts/acceptance-hs-gates-mutations.sh`, `scripts/acceptance-hs-gates-antiforge.sh`를 각각 `bash scripts/verify/run-acceptance.sh <검사>`로 실행 |
| 9 | 히스토리 전량 스캔 (도달 가능한 모든 blob) | 인라인 — 도달 가능한 모든 blob을 열어 자격증명 패턴 대조 |
| 10 | 인수 검사 0-2 상시 내용 검사와 종료상태 분리 (AC-19) | `bash scripts/verify/run-acceptance.sh scripts/acceptance-0-2-unreachable-content.sh` — 환경 격리·네 객체형·도구 실패·큰 객체·종료상태·훅 환경 무오염 13개 합성 사례 |
| 11 | 인수 검사 0-6 (가짜 검증 스크립트 0건) | `bash scripts/verify/run-acceptance.sh scripts/acceptance-0-6.sh` |
| 12 | 인수 검사 0-7 (훅이 위반 6종을 실제로 차단하는가) | `bash scripts/verify/run-acceptance.sh scripts/acceptance-0-7.sh` — 훅 위반 6종 시연 |
| 13 | 인수 검사 0-5 (push · CI 연결) | `bash scripts/verify/run-acceptance.sh scripts/acceptance-0-5.sh` — **`main` 브랜치에서만** (`if: github.ref == 'refs/heads/main'`) |
| 14 | 억제 만료 스캔 (suppressions.yaml) | 인라인 — `suppressions.yaml`의 expiry 형식·경과 |
| 15 | 강제 장치 존재 검사 (hooks/) | 인라인 — `hooks/pre-commit`·`pre-push` 존재·실행권한 |
| 16 | 셸 스크립트 문법 검사 | 인라인 — `git ls-files '*.sh'` 전부 `bash -n` |
| 17 | 패턴 파일 자체에 실제 비밀이 없는지 (자기 오염 방지) | 인라인 — `.secret-patterns.default`에 값 리터럴 없는지 |
| 18 | 인수 검사 hs-a3 (세션 계열 자격증명 탐지) | `bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-a3.sh` — 세션 계열 자격증명 탐지 (AC-A3) |
| 19 | 데이터 노출 스캔 (크기 · 금지경로 · 기록 · 개인정보 내용) | `bash scripts/scan-data-exposure.sh all` — 크기·금지경로·기록·개인정보 (AC-A4) |
| 20 | 인수 검사 hs-a4 (대용량·산출물 차단이 실제로 도는가) | `bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-a4.sh` — 차단이 실제로 도는가 (AC-A4) |
| 21 | 인수 검사 secret-webhook-vendor (웹훅·벤더 키 탐지 · AC-S1) | `bash scripts/verify/run-acceptance.sh scripts/acceptance-secret-webhook-vendor.sh` |
| 22 | 인수 검사 verified-sha (초록불이 SHA 에 귀속되는가 · P23) | `bash scripts/verify/run-acceptance.sh scripts/acceptance-verified-sha.sh` — 로컬·원격·CI 검사 SHA 귀속 진리표와 fail-closed |
| 23 | 인수 검사 ci-step-integrity (스텝을 조용히 끄지 못하는가) | `bash scripts/verify/run-acceptance.sh scripts/acceptance-ci-step-integrity.sh` — 조건부·오류무시로 CI 스텝을 끄는 구조 차단 |
| 24 | 인수 검사 semantic-mutations (검사를 껐을 때 반드시 빨개지는가) | `bash scripts/verify/run-acceptance.sh scripts/acceptance-semantic-mutations.sh` — 인수 검사 무력화 5종을 전량 격리 사본에서 차단 |
| 25 | 인수 검사 verify-ac-m (mechanism 명부 대조 · AC-M) | `bash scripts/verify/run-acceptance.sh scripts/acceptance-verify-ac-m.sh` |

*(1번 앞에 `actions/checkout` 이 있고 `fetch-depth: 0` 이다 — 9번이 과거 blob 을 열려면 필요하다.)*

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
- 이 표는 2026-08-20 실행 결과의 스냅샷이다. 스크립트가 추가/삭제되면 다시 확인해야 한다.
