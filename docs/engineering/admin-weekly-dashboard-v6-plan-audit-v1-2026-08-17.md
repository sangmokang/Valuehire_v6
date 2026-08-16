CODEAUDIT SPEC v2

1. verdict

FAIL.

계획 후보는 제품 코드를 건드리지 않은 9개 문서 추가라는 범위는 지켰지만, 계획 PASS 조건은 만족하지 못합니다. 확정 결함은 3개입니다: baseline RED 사실 불일치 1건, 실제 dependency DAG 증명 불가 1건, 독립 분할 가능한 retained micro 1건.

2. requirement/claim matrix

| ID | 판정 | 심각도 | confidence | 근거 |
|---|---|---:|---:|---|
| 40 parent AC 누락 0 | 통과 | P3 | high | 로컬 checker: `PLAN_ORIGINAL_PARENT_COUNT 40 MISSING []`, exit 0 |
| 필수 15개 필드 | 조건부 통과 | P3 | medium | TSV/YAML/anchor merge 해석 후 주요 row 필드 존재 확인. mutation에서 `target_count_method` 제거 시 missing 탐지 |
| baseline 보존 | 실패 | P1 | high | 후보 문서 [controller-goal](docs/engineering/admin-weekly-dashboard-v6-controller-goal-2026-08-17.md:63)는 `RED: 1/19` 기록. 폐기 clone 재실행은 `RED: 2/19`, exit 0 |
| repo fact mismatch 0 | 실패 | P1 | high | 위 baseline 불일치가 repo fact mismatch |
| dependency 실제 존재/DAG | 실패 | P2 | medium | [controller-goal](docs/engineering/admin-weekly-dashboard-v6-controller-goal-2026-08-17.md:158)는 dependency에 PASS audit hash를 요구하지만, row들은 산문/range dependency를 사용 |
| independently splittable micro 0 | 실패 | P2 | medium | [auth-security](docs/engineering/admin-weekly-dashboard-v6-atomic-research-auth-security-2026-08-17.md:283)는 dashboard 비인증 접근과 invalid callback/session cookie를 한 row에 결합 |
| 외부 부작용 0 | 통과 | P3 | high | diff는 문서 9개뿐. push/PR/merge/deploy/live connector/email 실행 0 |
| 고정 다섯 admin acceptance | 조건부 통과 | P3 | medium | [controller-goal](docs/engineering/admin-weekly-dashboard-v6-controller-goal-2026-08-17.md:151)가 security/auth 제안을 무효화하고 고정 5개만 사용한다고 정규화 |
| AC07/AC13/React types/log-root gap 은닉 | 통과 | P3 | high | [controller-goal](docs/engineering/admin-weekly-dashboard-v6-controller-goal-2026-08-17.md:164), :166-167, :177 및 [phase0-plan](docs/engineering/admin-weekly-dashboard-v6-atomic-plan-phase0-2026-08-17.md:328)에 차단 상태 명시 |

3. key-flow

감사 흐름은 base `a02a3da8f36e22997028b0d620de4e7e970f76d8`와 candidate `2d91b8d672aa63ef4f354936f94fa99583d0b696`를 `mktemp -d` 아래 로컬 clone으로 checkout한 뒤 비교했습니다.

`git diff --stat base candidate` 결과는 9개 문서, 2,081 insertions입니다. 제품 코드 변경은 0건입니다.

검증 명령:
- `bash scripts/session-status.sh` → exit 0, `RED: 2/19`
- `bash verify.sh` → exit 0, 비밀 스캔 PASS
- `bash scripts/acceptance-0-2.sh` → exit 2, `.secret-patterns 없음/빈 파일`
- `git diff --check base candidate` → exit 0

4. missed-better-answer

후보 계획이 더 나으려면 다음을 했어야 합니다.

- baseline을 문서 주장 `RED: 1/19`가 아니라 재실행값 `RED: 2/19`로 갱신하거나, 왜 실행 환경 차이로 RED 수가 달라졌는지 별도 blocker로 분리해야 합니다.
- 모든 `dependencies`를 산문이 아니라 exact micro_id와 required PASS audit hash field로 정규화해야 합니다.
- retained row `AC36-M04`는 `unauth-dashboard-runtime`과 `invalid-callback-no-session`으로 나눠야 합니다.

5. adversarial rebuttal

가장 강한 반론: controller 문서는 “시작 당시에는 RED 1/19였고, 지금 감사자가 candidate에서 다시 돌려 2/19가 나온 것은 시간이 지난 baseline drift일 수 있다”는 주장입니다.

반박: 원 요구는 “현재 baseline을 직접 재실행하고 비교”하라고 했고, 계획 PASS 조건에 repo fact mismatch 0이 있습니다. 현재 재실행값이 다르면 계획은 최소한 `BASELINE_DRIFT`로 중지해야지 `RED: 1/19`를 계속 계획 사실로 사용할 수 없습니다.

6. evidence ledger

| 주장 | 판정 | 1차 근거 | 실행 증거 |
|---|---|---|---|
| 원 요구 파일 무결성 | 확인 | sha256 요청값 일치 | `sha256sum ...original-user-request.md`, exit 0 |
| candidate branch/head 일치 | 확인 | HEAD와 branch 일치 | `git rev-parse HEAD`, `branch --show-current`, exit 0 |
| diff 범위는 문서 9개 | 확인 | added docs only | `git diff --name-status base head`, exit 0 |
| 목표 문서 1,331줄 읽음 | 확인 | [replacement-goal](docs/engineering/admin-weekly-dashboard-v6-replacement-goal-2026-08-16.md:1)~:1331 | `wc -l`, exit 0 |
| baseline RED 1/19 | 반증 | [controller-goal](docs/engineering/admin-weekly-dashboard-v6-controller-goal-2026-08-17.md:63) | 재실행 `RED: 2/19`, exit 0 |
| parent AC 누락 0 | 확인 | [controller-goal](docs/engineering/admin-weekly-dashboard-v6-controller-goal-2026-08-17.md:182)~:195 | checker `MISSING []`, exit 0 |
| AC36-M04 원자성 | 반증 | [auth-security](docs/engineering/admin-weekly-dashboard-v6-atomic-research-auth-security-2026-08-17.md:283)~:294 | 직접 line read, exit 0 |
| 제품 worktree 무변경 | 확인 | source HEAD 유지 | `git status --short`, 출력 없음, exit 0 |

7. repetition result

반복 질문/과거 대화 횟수 조사는 이번 감사 범위에 포함된 명시 요구가 아니었습니다. 현재 감사는 제공된 원 요구 파일, base/candidate, SOT, 목표 문서, 계획 문서 9개만 대상으로 했습니다.

8. validation limits

외부 네트워크와 connector는 사용하지 않았습니다. 실제 Gmail/Calendar/ClickUp, PR, push, merge, 배포, 이메일 발송은 모두 미실행입니다. lsp/type diagnostics는 문서-only diff라 실행하지 않았습니다. 폐기용 clone과 mutation 사본은 `/tmp` 계열 아래에서만 사용했습니다.

9. prioritized next action

1. 계획 후보를 FAIL로 처리하고 제품 코드 작성 금지를 유지합니다.
2. baseline을 현재 재실행값 기준으로 다시 고정하거나 drift 사유를 blocker로 남깁니다.
3. dependency field를 exact micro_id + PASS audit hash로 정규화합니다.
4. `AC36-M04`를 두 개 이상의 원자 row로 분리합니다.
5. 수정 후 같은 codeaudit를 다시 돌립니다.

민감 원문 실제값은 인용하지 않았고 `[REDACTED]` 원칙을 지켰습니다. 외부 부작용 실제 발생 건수: 0.
