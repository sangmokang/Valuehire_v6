# Valuehire v6 — 이 저장소의 실제 게이트 명령 (SOT)

`$strict`의 Codex·Claude 공통 순서와 패리티 계약은 [strict-workflow.md](strict-workflow.md)를 정본으로 읽는다. 원칙 수치는 `coding-principles.md`, Work Unit 값은 `work-unit-policy.yaml`이 소유하며 이 문서에 복제하지 않는다.

최종 갱신: 2026-09-02 (Invoice 독립 단위·PostgreSQL 런타임 게이트 추가)
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

**워크플로 스텝 26개 전부**를 적는다(2026-08-12 V1 D6: 이전 판은 `bash ...` 직접 명령만 적어 인라인 본문 스텝이 목록에서 빠졌고, 운영자가 실제로 무엇이 도는지 잘못 판단할 수 있었다). 아래는 `verify.yml` 의 `- name:` 스텝 순서 그대로다.

| # | 스텝 이름 | 실행 내용 |
|---|---|---|
| 1 | 비밀 스캔 (verify.sh) | `bash verify.sh` — 추적 파일 전체 |
| 2 | Strict 원칙 정본·장부·배선 검사 | `bash scripts/acceptance-principles-check.sh` — 34개 정본 문구·장치·명시적 pre-push/CI 배선 |
| 3 | Strict 원칙 적대 fixture·500/501 경계 | `bash scripts/acceptance-principles-mutations.sh` — 정상 fixture와 반례 41건·500/501 경계 |
| 4 | Strict 전역 스킬 잠금 장치 격리 회귀 | `bash scripts/acceptance-guard-global-skill-files.sh` — lock/check/unlock/recover와 동일 UID 한계 |
| 5 | P3 조용한 실패 문법·오탐 회귀 | `scripts/acceptance-silent-failure-lint.sh` + mutation 34건 — 대소문자 확장자 전체 소스와 스테이지 blob 판정 |
| 6 | HumanSearch G1 클린룸 경계 | 인라인 8개 — `scripts/acceptance-hs-cleanroom.sh`, `scripts/acceptance-hs-cleanroom-mutations.sh`, `scripts/acceptance-hs-cleanroom-absolute-paths.sh`, `scripts/acceptance-hs-cleanroom-absolute-contexts.sh`, `scripts/acceptance-hs-cleanroom-colon-paths.sh`, `scripts/acceptance-hs-cleanroom-file-urls.sh`, `scripts/acceptance-hs-cleanroom-hook-env.sh`, `scripts/acceptance-hs-cleanroom-hook-env-mutations.sh` |
| 7 | HumanSearch G2 테스트 게이트 | 인라인 — `uv` 설치 후 `scripts/acceptance-hs-gates.sh`, `scripts/acceptance-hs-gates-mutations.sh`, `scripts/acceptance-hs-gates-antiforge.sh` (정적 ruff/mypy + pytest 수집·runtime import 증명) |
| 8 | 히스토리 전량 스캔 | 인라인 — 도달 가능한 모든 blob 을 열어 자격증명 패턴 대조 |
| 9 | 인수 검사 0-2 상시/종료상태 분리 | `bash scripts/acceptance-0-2-unreachable-content.sh` — 환경 격리·네 객체형·도구 실패·큰 객체·종료상태·훅 환경 무오염 13개 합성 사례 (AC-19) |
| 10 | 인수 검사 0-6 | `bash scripts/acceptance-0-6.sh` |
| 11 | 인수 검사 0-7 | `bash scripts/acceptance-0-7.sh` — 훅 위반 6종 시연 |
| 12 | 인수 검사 0-5 | `bash scripts/acceptance-0-5.sh` — **`main` 브랜치에서만** (`if: github.ref == 'refs/heads/main'`) |
| 13 | 억제 만료 스캔 | 인라인 — `suppressions.yaml` 의 expiry 형식·경과 |
| 14 | 강제 장치 존재 검사 | 인라인 — `hooks/pre-commit`·`pre-push` 존재·실행권한 |
| 15 | 셸 스크립트 문법 검사 | 인라인 — `git ls-files '*.sh'` 전부 `bash -n` |
| 16 | 패턴 파일 자체 실값 검사 | 인라인 — `.secret-patterns.default` 에 값 리터럴 없는지 |
| 17 | 인수 검사 hs-a3 | `bash scripts/acceptance-hs-a3.sh` — 세션 계열 자격증명 (AC-A3) |
| 18 | 데이터 노출 스캔 | `bash scripts/scan-data-exposure.sh all` — 크기·금지경로·기록·개인정보 (AC-A4) |
| 19 | 인수 검사 hs-a4 | `bash scripts/acceptance-hs-a4.sh` — 차단이 실제로 도는가 (AC-A4) |
| 20 | 인수 검사 secret-webhook-vendor | `bash scripts/acceptance-secret-webhook-vendor.sh` — 웹훅·벤더 키 (AC-S1) |
| 21 | 인수 검사 verified-sha | `bash scripts/acceptance-verified-sha.sh` — 현재 SHA 귀속·모든 verify 실행 집계·조회 오류 및 순서 반례 52건(P23) |
| 22 | 인수 검사 ci-step-integrity | `bash scripts/acceptance-ci-step-integrity.sh` — 조건부·오류무시·echo 대체 차단 및 main 실행별 그룹·이벤트/ref 분리·30분 상한 회귀 24건 |
| 23 | 인수 검사 semantic-mutations | `bash scripts/acceptance-semantic-mutations.sh` — 인수 검사 무력화 5종 전량 차단 |
| 24 | 인수 검사 verify-ac-m | `bash scripts/acceptance-verify-ac-m.sh` — mechanism 명부 대조 (AC-M) |
| 25 | 인수 검사 invoice | `bash scripts/acceptance-invoice.sh` — 채용 수수료 계산·기한·계약 변조·Codex/Claude 스킬 동등성 |
| 26 | Invoice 독립 런타임 게이트 | 게이트 배선 검사 + Python 단위시험 직접 실행 + 임시 PostgreSQL에서 마이그레이션·수수료 동시성·저장/전달 RPC 검증 |

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

### 검증 핵심 변경의 별도 검토 상태

`bash scripts/verify/check-verification-core.sh <trusted-base-full-sha> <candidate-head-full-sha>`는 검증 핵심 경로의 추가·변경·삭제·이동을 비교한다. 종료값 0은 지정된 두 커밋 사이 핵심 변경 없음, 20은 `VERIFICATION_CORE_CHANGED`(검토 필요), 2는 입력/조회 실패다. 20은 악성 변경 확정이 아니며 정상적인 검사기 수정도 검토 후 진행할 수 있다. 기능 인수 PASS로 20을 덮어쓰지 않는다.

신뢰 조건: 검토된 비교기 사본과 base/head 선택 및 호출 배선은 후보 HEAD 밖에서 관리해야 한다. 후보 HEAD의 비교기를 실행한 결과는 자기 신뢰성을 증명하지 못한다. `--allow-same-ref`는 동일 커밋 정상 대조 시험 전용이며 병합 검증에 쓰지 않는다.

PR #104의 기준 `fc6beedc78019862bc2f1b3bf4c4ad3bbd8e845b`에는 이 비교기가 없다. 따라서 현재 추가는 로컬 구현과 회귀 배선이며, 이미 신뢰된 base 검사기나 외부 필수 검사를 설치했다는 뜻이 아니다. 별도 선행 검토/기준 반영과 HEAD 밖 실행 및 필수 체크 설정이 실제 적용되기 전에는 self-bypass finding을 미해결로 둔다. 새 비교기의 회귀는 기존 `acceptance-rps-inmail.sh` AC-5가 조건 회귀와 함께 실행한다.

### 외부 실행 준비와 설치 경계 (PR #104 후속)

`.github/workflows/verification-integrity.yml`은 `pull_request_target`의 신뢰된 정의에서 실행하도록 준비한 코드다. GitHub 이벤트의 PR base/head SHA와 base 브랜치 `main`을 현재 PR API 응답과 대조하고, 빈 bare Git 저장소에 객체만 fetch한다. 보호되지 않은 다른 base 브랜치의 helper는 실행하지 않는다. base의 `scripts/verify/check-verification-core.sh`를 꺼내 실행하며 HEAD 파일·helper·환경파일·성공 문구는 실행/판정 근거로 사용하지 않는다. base에 검사기가 없으면 실패하며 HEAD 사본으로 대체하지 않는다.

핵심 변경 없음은 0, 핵심 변경은 20이다. 정상적인 core 수정은 **GitHub의 현재 base/head에 대한 `reviewDecision=APPROVED`**를 사용한다. 리뷰 작성자 목록이나 Git 커밋 작성자 정보로 자체 승인 규칙을 만들지 않는다. GraphQL로 기존 branch protection의 승인 1건 이상·stale 승인 철회·마지막 push한 사람 외 승인·관리자 적용이 모두 유지되는지도 확인한다. 정책 누락/완화, 옛 SHA, `REVIEW_REQUIRED`/`CHANGES_REQUESTED`/null은 통과하지 않는다. 새 승인 시스템이나 라벨을 만들지 않는다. 리뷰 이후 기존 target 실행을 재실행하며 다른 branch protection 조건은 별도로 계속 적용한다.

로컬 회귀는 `python3 -m unittest tests.test_verification_core`이며 기존 RPS 인수 AC-5 → pre-push/verify 경로에서 실행한다. 이는 준비한 workflow 본문을 실제 실행하는 fixture 시험이지, GitHub required workflow가 설치됐다는 증거가 아니다.

**현재 상태: 코드 측 준비 / 외부 강제 미적용.** `main` base `fc6beedc...`에는 workflow와 검사기가 없다. 현재 저장소의 필수 status check는 `verify`/GitHub Actions 앱(15368)이며 workflow identity를 고정하지 않는다. [GitHub 공식 문서](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/troubleshooting-rules)는 required status checks가 workflow·matrix·event 종류를 구별하지 않는다고 명시한다. 따라서 이름 `verification-integrity`를 required check에 추가하는 것만으로 동명 가짜 job 공격을 닫았다고 할 수 없다.

실제 강제의 선행 조건:

1. 검토된 workflow와 검사기를 신뢰된 default/base에 먼저 반영한다. 이번 작업의 main 병합 금지 범위에서는 실행하지 않는다.
2. 이름이 아니라 **source repository + workflow path + trusted ref를 지정하는 required workflow 규칙**을 활성화하고 우회 주체를 허용하지 않는다. 공식 설정은 [조직 ruleset](https://docs.github.com/en/organizations/managing-organization-settings/creating-rulesets-for-repositories-in-your-organization)에 있다. 현재 저장소에는 이 required workflow 규칙을 적용하지 않았으며, 필요한 소유자/플랜/권한 확인은 이번 범위 밖이다. 같은 Actions 앱 이름 제한 또는 CODEOWNERS만으로 이 강제와 동등하다고 주장하지 않는다. 별도 서비스/App를 새로 만들지 않는다.
3. 보호된 소스 정의로 실행한 실제 PR에서 정상 기능 변경 성공, core 변경의 검토 대기, 동명 가짜 성공 job으로 필수 workflow 실패를 덮지 못함을 확인한다. 이 원격 실증 전에는 integrity/merge-ready 완료 판정을 하지 않는다.

`pull_request_target`는 base 저장소의 신뢰된 workflow 정의를 사용한다. [공식 보안 문서](https://docs.github.com/en/actions/reference/security/securely-using-pull_request_target)는 이 이벤트가 높은 신뢰 권한에서 동작하므로 PR code checkout/실행을 피하라고 설명한다. 현재 workflow는 읽기 권한만 요청하고 checkout·cache·artifact·HEAD 실행을 하지 않는다. 원격 보호 규칙·환경·이벤트 정책을 이번 작업에서 변경하지 않는다.

### 2026-09-22 후속 감사 정정

직접 CI 단계가 호출하는 `scripts/scan-data-exposure.sh`가 핵심 경로에서 빠져 있었다.
이 파일을 exit 0 / true / 빈 본문 / PASS 출력으로 바꾼 격리 반례 4종에서 기존 workflow 본문은 0을 반환했다.
핵심 경로에 해당 파일 한 개를 추가하고 같은 반례가 20(검토 필요)을 반환하도록 수정했다.
이는 경로 누락의 로컬 수정이며 외부 required workflow 설치를 의미하지 않는다.

소유 형태/권한은 후속 조회에서 개인(User)·public·관리자 권한으로 확인했다. 구독 상품은 API null로 미확인이다.
[공식 required workflows 규칙](https://docs.github.com/en/enterprise-cloud%40latest/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets)은 organization/enterprise 수준이다.
현재 개인 저장소의 필수 check 이름+Actions 앱 지정으로 workflow 정체성을 고정하지 못한다.
기존의 “소유자/플랜/권한 확인은 범위 밖”은 앞선 단계 기록이며 현재 확인 범위는 위와 같다.
코드 준비는 검증된 경로 범위에 한정하며, 모든 검증 의존성의 무결성을 증명한 것이 아니다.
외부 강제 미완료와 merge-ready 아님을 유지한다. suppression #71/#72는 별도 작업으로 남긴다.
