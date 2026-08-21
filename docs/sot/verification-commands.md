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

### 개발·검증 순서 — 작은 증명 뒤 전체 통합 검사

기존 `strict → codeaudit → 전체 적대검증`을 없애지 않는다. Work Unit마다 작은 검증 경계를 먼저 닫고, 기존 세 검사를 PR 전체의 최종 관문으로 사용한다.

```text
1. ISSUE / 요구사항
2. Work Unit 분해: WU-01, WU-02, ...
3. 필요한 RED 계약을 먼저 커밋
4. WU-01: IMPLEMENT → LOCAL VALIDATE → 작은 적대검증 → 완료 커밋
5. WU-02: IMPLEMENT → LOCAL VALIDATE → 작은 적대검증 → 완료 커밋
6. WU-N까지 같은 순서로 반복
7. 전체 strict
8. 전체 codeaudit
9. 전체 적대검증
10. PR
11. GitHub verify CI
12. CI GREEN 확인 뒤 MERGE
```

10번 PR 단계는 `git push`로 브랜치를 원격에 올린 뒤 PR을 만드는 순서다. `git push` 때 pre-push가 결정적 스크립트를 전량 다시 실행하지만, 이는 7번 전체 strict의 실행 장부, 8번 codeaudit의 코드·설계 검토, 9번 전체 적대검증의 Work Unit 결합 공격을 대신하지 않는다. Work Unit 완료 커밋을 중간 백업 목적으로 push할 수는 있어도 PR 전체 PASS를 뜻하지 않는다.

`LOCAL VALIDATE`는 “이번 Work Unit에서 약속한 기능 하나가 실제로 되는가?”만 묻는다. goal에 고정한 해당 AC의 원명령과 기대 종료값·출력을 실제로 실행하며, 다른 Work Unit의 성공으로 대신하지 않는다.

`작은 적대검증`은 “이 약속을 어떻게 속여서 통과시킬 수 있는가?”를 묻는다. 일반 Work Unit은 counter-AC에 정조준한 반증 1~3개를 실제로 실행한다. 예를 들어 검사 실행 배선이면 `echo`, `true`, `|| true`, `if: false`, 조기 `exit 0` 중 해당 주장과 관련된 최소 조합을 시험한다.

`전체 strict`는 저장소가 기계 원칙과 계약을 지키는지 광범위한 결정적 명령으로 확인한다. `전체 codeaudit`은 구현의 논리·구조·중복·복잡도와 설계 부채를 검토한다. `전체 적대검증`은 각 Work Unit이 따로는 PASS여도 결합·순서·공유 상태·동시 실행에서 뚫리는지 공격한다. 셋은 질문이 다르므로 서로의 PASS를 대신하지 않는다.

최종 관문을 생략·선택·권장으로 낮추거나 다른 검사로 대체하는 예외 문장은 둘 수 없다.

### 위험도에 따른 Work Unit 검사 강도

일반 Work Unit은 `IMPLEMENT → 해당 AC 실행 → 반증 1~3개 → 완료 커밋`으로 닫는다. 모든 작은 UI·문서 변경에 full codeaudit나 외부 Agent를 강제하지 않는다.

다음 검증·보안·운영 경계를 건드리는 Work Unit은 `IMPLEMENT → LOCAL VALIDATE → 작은 적대검증 → 독립 REVIEW → 완료 커밋`으로 강화한다.

- `.github/workflows/**`
- `hooks/**`
- `scripts/acceptance-*`, `verify*`, `mechanism-registry`
- 비밀·후보자 데이터 노출 검사
- 배포·인증·로그인

독립 REVIEW는 다음 두 등급을 구분한다.

- **실행 REVIEW**: 구현 결론을 그대로 받아쓰지 않고 같은 AC와 counter-AC를 새 맥락에서 재실행한다. 고위험 Work Unit을 닫으려면 실행 REVIEW가 필요하다.
- **문서 REVIEW**: diff·문서·전달받은 로그만 읽고 공격한다. 결함을 찾으면 `FAIL`을 만들 수 있지만 실행 증명이 아니므로 `PASS`를 만들 수 없다. 문서 REVIEW의 PASS만으로 고위험 Work Unit을 닫을 수 없다.

다른 Agent나 모델을 쓸 수 있지만 필수 외부 서비스로 고정하지 않는다. 도구 연결 실패 등으로 재실행할 수 없으면 실행 REVIEW는 `NOT_RUN`이며 고위험 Work Unit을 PASS로 닫지 않는다.

독립 REVIEW의 기본 경로는 저장소 명령을 실행할 수 있는 비용 없는 새 로컬 맥락이다. 비용이 발생하는 외부 모델은 사용자가 명시적으로 승인했을 때만 선택한다.

원칙 게이트는 검토 등급 정의와 예외 문구의 무결성만 검사한다. 같은 쓰기 권한 안에서는 독립 검토자 신원을 기계로 보증하지 못하므로, goal 장부에 새 맥락·실행 명령·출력을 기록하고 최종 codeaudit가 수행 여부를 판정한다. 구현자가 스스로 발급한 영수증은 독립성의 신뢰점이 아니다.

### Work Unit 완료와 PR 완료는 다르다

Work Unit 완료 커밋은 그 주장 하나의 표적 증거가 닫혔다는 뜻이다. PR 완료는 모든 Work Unit의 결합, 전체 저장소 원칙, 코드 품질, 원격 CI까지 닫혔다는 뜻이다. Work Unit PASS만으로 PR을 만들거나 병합 완료를 주장하지 않는다.

### CI(`​.github/workflows/verify.yml`)가 실제로 돌리는 것

**워크플로 스텝 23개 전부**를 적는다(2026-08-12 V1 D6: 이전 판은 `bash ...` 직접 명령만 적어 인라인 본문 스텝이 목록에서 빠졌고, 운영자가 실제로 무엇이 도는지 잘못 판단할 수 있었다). 아래는 `verify.yml` 의 `- name:` 스텝 순서 그대로다(2026-08-21 Strict 원칙 직접 로드·SHA 귀속·CI 무력화 저항 스텝 포함).

| # | 스텝 이름 | 실행 내용 |
|---|---|---|
| 1 | 비밀 스캔 (verify.sh) | `bash verify.sh` — 추적 파일 전체 |
| 2 | Strict 원칙·Work Unit 정본·장부·배선 검사 | `bash scripts/acceptance-principles-check.sh` — 원칙 계약 34개와 Work Unit 계약 28개, 장치, 명시적 pre-push/CI 배선 |
| 3 | Strict 원칙·Work Unit 적대 fixture·500/501 경계 | `bash scripts/acceptance-principles-mutations.sh` — 정상 fixture, 원칙 반례, Work Unit 반례 13개, 500/501 경계 |
| 4 | Strict 전역 스킬 잠금 장치 격리 회귀 | `bash scripts/acceptance-guard-global-skill-files.sh` — lock/check/unlock/recover와 동일 UID 한계 |
| 5 | HumanSearch G1 클린룸 경계 | 인라인 8개 — `scripts/acceptance-hs-cleanroom.sh`, `scripts/acceptance-hs-cleanroom-mutations.sh`, `scripts/acceptance-hs-cleanroom-absolute-paths.sh`, `scripts/acceptance-hs-cleanroom-absolute-contexts.sh`, `scripts/acceptance-hs-cleanroom-colon-paths.sh`, `scripts/acceptance-hs-cleanroom-file-urls.sh`, `scripts/acceptance-hs-cleanroom-hook-env.sh`, `scripts/acceptance-hs-cleanroom-hook-env-mutations.sh` |
| 6 | HumanSearch G2 테스트 게이트 | 인라인 — `uv` 설치 후 `scripts/acceptance-hs-gates.sh`, `scripts/acceptance-hs-gates-mutations.sh`, `scripts/acceptance-hs-gates-antiforge.sh` (정적 ruff/mypy + pytest 수집·runtime import 증명) |
| 7 | 히스토리 전량 스캔 | 인라인 — 도달 가능한 모든 blob 을 열어 자격증명 패턴 대조 |
| 8 | 인수 검사 0-2 상시/종료상태 분리 | `bash scripts/acceptance-0-2-unreachable-content.sh` — 환경 격리·네 객체형·도구 실패·큰 객체·종료상태·훅 환경 무오염 13개 합성 사례 (AC-19) |
| 9 | 인수 검사 0-6 | `bash scripts/acceptance-0-6.sh` |
| 10 | 인수 검사 0-7 | `bash scripts/acceptance-0-7.sh` — 훅 위반 6종 시연 |
| 11 | 인수 검사 0-5 | `bash scripts/acceptance-0-5.sh` — **`main` 브랜치에서만** (`if: github.ref == 'refs/heads/main'`) |
| 12 | 억제 만료 스캔 | 인라인 — `suppressions.yaml` 의 expiry 형식·경과 |
| 13 | 강제 장치 존재 검사 | 인라인 — `hooks/pre-commit`·`pre-push` 존재·실행권한 |
| 14 | 셸 스크립트 문법 검사 | 인라인 — `git ls-files '*.sh'` 전부 `bash -n` |
| 15 | 패턴 파일 자체 실값 검사 | 인라인 — `.secret-patterns.default` 에 값 리터럴 없는지 |
| 16 | 인수 검사 hs-a3 | `bash scripts/acceptance-hs-a3.sh` — 세션 계열 자격증명 (AC-A3) |
| 17 | 데이터 노출 스캔 | `bash scripts/scan-data-exposure.sh all` — 크기·금지경로·기록·개인정보 (AC-A4) |
| 18 | 인수 검사 hs-a4 | `bash scripts/acceptance-hs-a4.sh` — 차단이 실제로 도는가 (AC-A4) |
| 19 | 인수 검사 secret-webhook-vendor | `bash scripts/acceptance-secret-webhook-vendor.sh` — 웹훅·벤더 키 (AC-S1) |
| 20 | 인수 검사 verified-sha | `bash scripts/acceptance-verified-sha.sh` — 로컬·원격·CI 검사 SHA 귀속 진리표와 fail-closed (P23) |
| 21 | 인수 검사 ci-step-integrity | `bash scripts/acceptance-ci-step-integrity.sh` — 조건부·오류무시로 CI 스텝을 끄는 구조 차단 |
| 22 | 인수 검사 semantic-mutations | `bash scripts/acceptance-semantic-mutations.sh` — 인수 검사 무력화 5종을 전량 격리 사본에서 차단 |
| 23 | 인수 검사 verify-ac-m | `bash scripts/acceptance-verify-ac-m.sh` — mechanism 명부 대조 (AC-M) |

*(1번 앞에 `actions/checkout` 이 있고 `fetch-depth: 0` 이다 — 7번이 과거 blob 을 열려면 필요하다.)*

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
