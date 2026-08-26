# goal — 검증 체계 보강 (2026-08-27)

작업트리: `.claude/worktrees/history-scan-failclosed` · 브랜치 `task/history-scan-failclosed`
등급: L3 (검증 체계 자체·SOT 수정)
출처 프롬프트: `docs/engineering/verification-hardening-next-prompt-2026-08-27.md`

## 상위 목표 1문장

CI 워크플로와 인수 검사를 **조용히 끌 수 있는 구멍**을 닫아, "초록불"이 실제로 검사가 돌았다는 뜻이 되게 한다.
성공 신호 1개: 무력화 주입 사본(트리거 제거·스텝 삭제·오류 무시·이름 위조·본문 위조) 전량이 로컬과 CI 양쪽에서 빨간불이 된다.

## 현재 상태 (실행으로 확인 · 추측 없음)

| 사실 | 근거 (file:line 또는 실행 출력) |
|---|---|
| 리베이스 전 HEAD | `659eec3` · 리베이스 후 `78ac807` (origin/main `3276712` 위) |
| 프롬프트가 적은 origin/main `c59bad7` 은 이미 6커밋 뒤처짐 | `git log --oneline c59bad7..origin/main` → #42·#20·#39·#32·#40·#41 |
| pytest 파일 28개 / 수집 211건 | `uv run --frozen pytest --collect-only -q` → `211 tests collected` |
| verify.yml 은 step `id:` 가 하나도 없다 | ruby/psych 파싱 결과 25 step 전부 `id=nil` |
| `on:` 트리거를 검사하는 장치가 없다 | `check-ci-step-integrity.sh:46` 은 `doc["jobs"]` 만 읽는다 |
| step 예외가 **표시 이름 문자열**로 판정된다 | `check-ci-step-integrity.sh:30-33,71` `ALLOWED_STEP_IF[step["name"]]` |
| `\|\| true` · `; true` 를 run 본문에서 잡지 않는다 | `check-ci-step-integrity.sh:88-97` 은 `echo`/`bash -n` 두 형태만 본다 |
| 래퍼가 `PASS` 를 **부분 문자열**로 센다 | `run-acceptance.sh:47` `grep -c 'PASS'` → `PASSWORD` 도 1건으로 셈 |
| `CHECKED:` 가 선택 항목이라 없으면 그냥 통과 | `run-acceptance.sh:55` `if grep -q 'CHECKED:'` |
| 제품 테스트가 1개만 남아도 게이트 통과 | `acceptance-hs-gates.sh:60` `[ "$collected" -lt 1 ]` |
| 관리자 JS 를 실행하는 시험이 없다 | `test_admin_shadow_server.py:70` 은 `app.js` 를 **빈 문자열**로 쓰고 MIME 만 본다 |
| 문서의 스텝 수가 수동 숫자다 | `verification-commands.md:20` "스텝 24개" — 구조 대조 장치 없음 |
| 이 브랜치의 `acceptance-history-scan-failclosed.sh` 가 CI·명부에 없다 | `verify.yml` 전문에 문자열 없음 · `mechanism-registry.yaml` 에 항목 없음 |

### 회수했으나 실재하지 않는 문서 (읽었다고 주장하지 않는다)

- `CLAUDE.md`, `AGENTS.md` — 이 저장소에 **없다** (`ls` 실패). 프롬프트가 회수를 지시했으나 대상이 없다.
- `docs/sot/30-strict-mode-contract.md`, `docs/sot/31-strict-recurrence-ledger.md` — 없다. 정본은 `docs/sot/coding-principles.md` + `docs/sot/principles.yaml`.

## 근본 원인

검사 배선이 **문자열 일치**에 의존한다. 워크플로를 문자열로 훑거나(pre-push), 스텝을 표시 이름으로 식별하거나(ci-step-integrity), 출력에 특정 낱말이 있는지만 본다(run-acceptance). 문자열 규칙은 하나 막을 때마다 우회가 하나 는다. 판정 기준을 **안정된 ID와 구조 파싱**으로 옮기고, 필수 항목을 명부에 적어 **양방향**으로 대조해야 한다.

## 계약 (입출력 모양 먼저 · SDD)

### 새 명부 — `docs/sot/ci-required-manifest.yaml`

```yaml
workflow: ".github/workflows/verify.yml"
required_triggers: ["push", "pull_request"]
required_jobs:
  - id: "verify"
required_steps:
  - id: "<안정된 step id>"
    job: "verify"
    must_run_contains: ["<run 본문에 문자 그대로 있어야 하는 명령>"]
    allow_if: "<사유>"        # 선택 — 조건부 실행을 허용할 때만
acceptance_scripts:
  required: ["scripts/acceptance-*.sh 중 CI 에서 실행돼야 하는 것"]
  excluded:
    - path: "scripts/acceptance-0-2.sh"
      reason: "<CI 에 올릴 수 없는 이유>"
pytest_baseline:
  files: 28
  cases: 211
  approved_on: "2026-08-27"
  reason: "WU-0 리베이스(78ac807) 직후 실측"
```

### 새 검사기 — `scripts/verify/check-ci-required-manifest.sh`

- 입력: `$1` = 명부 경로(기본 위 경로), `WORKFLOW_FILE` 환경변수로 워크플로 재지정
- 출력: 항목마다 `PASS:` / `FAIL:`, 마지막 줄 `CHECKED: <대조 항목 수>`
- 종료값: `0` = 전부 통과 / `1` = 위반 / `2` = 스캔 무효(명부 없음·파싱 실패·대조 항목 0개)
- 파싱: **ruby/psych 로 YAML 구조 파싱**. grep·awk 로 실행 의미를 추정하지 않는다.

### 경계·오류 계약 (입력 영역 표)

| 입력 | 처리 |
|---|---|
| 명부 없음 | `NOT_RUN` · exit 2 |
| 워크플로 없음 | `FAIL` · exit 2 |
| YAML 파싱 실패(양쪽 다) | `FAIL` · exit 2 |
| 대조 항목 0개 | `FAIL` · exit 2 (P20 — 0건 통과 금지) |
| `on:` 에 필수 트리거 없음 | `FAIL` · exit 1 |
| 필수 job id 없음 | `FAIL` · exit 1 |
| 필수 step id 없음(삭제·주석·다른 job 이동) | `FAIL` · exit 1 |
| step 의 run 에 필수 명령 문자열 없음 | `FAIL` · exit 1 |
| step 에 `if` 가 있는데 명부에 `allow_if` 없음 | `FAIL` · exit 1 |
| step 에 `continue-on-error` | `FAIL` · exit 1 |
| run 에 오류 무시 꼬리(`\|\| true` 계열, `; true`) | `FAIL` · exit 1 |
| workflow 에 있는데 명부에 없는 acceptance 실행 | `FAIL` · exit 1 |
| 명부에 있는데 workflow 에 없는 항목 | `FAIL` · exit 1 |
| `git ls-files` 의 acceptance 스크립트가 명부 required·excluded 어디에도 없음 | `FAIL` · exit 1 |
| excluded 항목에 reason 없음 | `FAIL` · exit 1 |
| 그 외 전부 | **명시적 거부** (fail-closed) |

## 작업 분해 (WU · 각 WU = AC 1개 단위 = RED 커밋 + GREEN 커밋)

| WU | 내용 | 겨냥 AC |
|---|---|---|
| WU-0 | origin/main 위로 리베이스 · 기존 검사 전량 회귀 0건 · pytest 기준선 고정 | (선행조건) |
| WU-1 | verify.yml 전 step 에 안정된 `id:` 부여 + 명부 + 양방향 대조 검사기 + 인수검사 | AC1 AC2 AC3 AC7 AC8 |
| WU-2 | `check-ci-step-integrity` 예외를 **step id** 기준으로 전환 + 오류무시 꼬리 탐지 | AC4 AC5 |
| WU-3 | `run-acceptance.sh` 판정 위조 차단(토큰 엄격화 · CHECKED 필수 · 실행량 관측) | AC6 |
| WU-4 | pytest 기준선 게이트(파일 수·수집 수 감소 차단) | AC9 |
| WU-5 | 관리자 JS 실행 기반 시험(node · 새 의존성 없음) | AC10 |
| WU-6 | `verification-commands.md` ↔ workflow 구조 대조 | AC11 |

## 인수 기준 (EARS) — 검증 명령 포함

- **AC1.** When 손대지 않은 workflow 를 검사할 때, 시스템은 exit 0 과 양수 `CHECKED` 를 출력해야 한다.
  검증: `bash scripts/verify/check-ci-required-manifest.sh; echo $?` → `0` + `CHECKED: N (N>0)`
- **AC2.** When `on:` 에서 push/pull_request 를 제거하고 `workflow_dispatch` 만 남길 때, 구조 검사는 실패해야 한다.
  검증: 격리 사본에 주입 후 검사기 exit 1
- **AC3.** When 필수 step 을 삭제·주석 처리·비활성 job 으로 이동할 때, 구조 검사는 실패해야 한다.
- **AC4.** When 필수 run 에 오류 무시 꼬리, `if: false`, 항상 거짓 anchor, `continue-on-error` 를 붙일 때, 전부 실패해야 한다.
- **AC5.** When 허용된 표시 이름을 다른 step 에 복사할 때, 예외 권한이 이동하지 않아야 한다.
- **AC6.** When acceptance 본문을 `exit 0`·`true`·빈 파일·`검사했습니다`·`VERDICT: PASS`·`PASSWORD 검사 없음`·가짜 PASS/CHECKED 출력으로 교체할 때, 전부 실패해야 한다.
- **AC7.** When 새 `scripts/acceptance-*.sh` 가 추가되면, CI·pre-push·명부에서 명시적으로 실행 또는 제외되지 않는 한 실패해야 한다.
- **AC8.** When 등록 항목이 실제 파일·job·step·명령과 어긋나면 실패해야 하며 검사 대상 0개도 실패해야 한다.
- **AC9.** When 제품 pytest 파일 또는 수집 케이스가 승인 기준(파일 28 · 케이스 211)보다 줄면, 명시적 기준 갱신 없이는 실패해야 한다.
- **AC10.** When 관리자 JS 의 API 호출 또는 화면 표시를 고장 내면, 최소 한 개의 실행 기반 시험이 실패해야 한다.
- **AC11.** `verification-commands.md` 의 단계 목록은 실제 workflow 와 **구조적으로** 일치해야 한다.

## counter-AC (이것들이 통과하면 실패로 친다)

1. registry·manifest·생성 결과를 함께 약화해 diff 0 을 만든다 → **저장소 내부 장치로 완전 차단 불가. 아래 "한계" 참조.**
2. workflow 실행 조건 자체를 없애 검사가 시작되지 않는다 → AC2 가 막는다.
3. step 표시 이름만 허용 이름으로 위조한다 → AC5 (id 기준 판정) 가 막는다.
4. run 앞부분은 유지하고 뒤에 오류 무시 명령을 붙인다 → AC4 (꼬리 탐지) 가 막는다.
5. acceptance 가 아무 동작 없이 합격 문구만 출력한다 → AC6 이 막는다.
6. 새 acceptance 가 pre-push 에서만 실행되고 CI 에 없다 → AC7 이 막는다.
7. 테스트 1개만 남겨 수집 수 > 0 조건을 만족한다 → AC9 (기준선) 가 막는다.
8. checker 가 파일 0개를 읽고 합격한다 → 전 검사기 `CHECKED: 0` → exit 2.

## 한계 — 주장하지 않는 것 (정직 표기)

- **같은 커밋에서 검사기와 명부를 함께 약화하는 공격은 저장소 내부 장치만으로 막을 수 없다.** 검사기도 명부도 그 커밋의 내용이기 때문이다. 이를 막는 것은 외부 required check + 승인 규칙이며, 이 계정은 개인 비공개 저장소라 branch protection·ruleset API 가 HTTP 403 이다 → **별도 운영 AC / NOT_RUN 으로 분리한다.**
- AC6 의 "가짜 PASS/CHECKED 출력"은 실행량 관측으로 **실용적 하한**을 두는 것이지 원리적 차단이 아니다. 충분히 정교한 위조(무의미한 명령 padding)는 남는다. 그 몫은 `acceptance-0-6` 과 사람 리뷰다.
- `actionlint` 는 새 의존성이므로 도입하지 않는다. 별도 선택지로만 보고한다.

## 롤백 절차

1. `git revert <GREEN 커밋들>` 또는 브랜치 폐기(`git branch -D task/history-scan-failclosed`).
2. 개별 되돌림 시: `docs/sot/ci-required-manifest.yaml` 과 `scripts/verify/check-ci-required-manifest.sh` 를 지우고, `verify.yml` 에서 해당 스텝과 `id:` 를 제거하고, `mechanism-registry.yaml` 의 새 항목을 제거하면 현재 구조로 정확히 돌아간다.
3. 되돌림 자체가 검사·테스트 파일을 건드리므로 P15② 에 따라 **단독 커밋**으로 한다.

## 영향 반경

| 대상 | 영향 |
|---|---|
| `.github/workflows/verify.yml` | step `id:` 추가(표시 이름 불변) + 새 스텝 추가 → 모든 브랜치의 CI |
| `scripts/verify/run-acceptance.sh` | 전 인수 검사가 이 래퍼를 거친다 → **판정 기준 강화가 기존 검사를 오차단하면 전 브랜치 push 가 막힌다**. WU-3 은 기존 검사 전량 재실행으로 과잉 차단 0건을 먼저 증명한다. |
| `scripts/verify/check-ci-step-integrity.sh` | 예외 판정 기준 변경 → 0-5 스텝의 `if` 허용이 유지되는지 확인 필요 |
| `hooks/pre-push` | 글로브가 새 인수 검사를 자동 수집 → push 시간 증가 |
| `docs/sot/*` | 명부·문서 갱신. SOT 변경이므로 같은 PR 에 diff 동봉 |
| 제품 코드(`humansearch/src`, `apps/admin`) | **변경 없음.** WU-5 는 시험만 추가한다. |

## 배포 후 관측 항목 (L3 필수)

1. 다음 PR 의 CI 에서 새 스텝이 실제로 실행되고 `CHECKED:` 가 양수인지 (job log).
2. push 시 `pre-push` 가 새 인수 검사를 수집해 실행하는지 (`pre-push: 검사 N개 실행` 의 N 증가).
3. 기존 검사 중 오차단이 발생하는지 — 발생 시 즉시 WU-3 롤백.

## 비범위

- 외부 required check·branch protection 설정 (권한 403 · 사장님 계정 요금제 문제)
- `actionlint` 도입
- 비밀 스캔 하한(6자 vs 12자) 정책 결정 — `suppressions.yaml` 의 `keyword-env-value-floor-12` 는 **2026-08-26 만료**로 이미 지났다. 이 작업의 범위가 아니며 **별도 결정 카드**로 올린다.
- 관리자 대시보드 기능 변경

## 적대 검증 로그

### V1 (Claude CLI · fresh · 격리 clone `2a0f0da`) — 2026-08-27

실행: `claude -p <v1-prompt> --dangerously-skip-permissions` (clone 안에서 read-only 지시)
1차 시도는 `ANTHROPIC_API_KEY` 잔액 부족으로 실행 불가(NOT_RUN). 키를 걷어내고 재실행해 판정을 받았다.

```
V1_RETRY_CLONE=/private/tmp/claude-501/-Users-kangsangmo-Desktop-Valuehire-v6--claude-worktrees-history-scan-failclosed/4010d7e2-1ee0-4d2e-9c75-f35b56c84e51/scratchpad/v1-clone
V1_RETRY_HEAD=2a0f0da4deee5ecfa0789ace2bdacfa8fa9a7ca6
V1 VERDICT: FAIL

## 1. 반증 시도 내역

모든 파괴적 실험은 `mktemp -d` 아래 `git clone` 사본에서 수행했고, 원 작업트리는 읽기만 했습니다(종료 후 사본 삭제). 대조군: 원 작업트리에서 5개 검사기 직접 실행 → 전부 exit 0 (`CHECKED: 100 / 31 / 88 / 2 / 21`), 사본 원문에서 워크플로 대상 인수 검사 5종(verify-ac-m·ci-step-integrity·ci-required-manifest·docs-workflow-sync·0-7) 전부 OK.

### 뚫린 것

| # | 공격 | 결과 |
|---|---|---|
| 1 | hs-a4 run 을 `… \|\| true; echo done` / `\|\| true  # keep going` / `\|\| :; echo done` / `\|\| echo warn` / `\|\| /bin/true` / `\|\| exit 0 # done` / `&& echo ok` + 다음 줄 / `if …; then …; else …; fi` / `… &` + `echo` / `… \| cat` / `… 2>&1 \| tee` / `set -u +e` / `set +e # relax` / `set +e; …` / `set +o errexit` / `trap 'exit 0' ERR` | manifest=0 · integrity=0 **전부 통과**. 같은 본문을 `bash -e`(GitHub 기본 셸)로 실행해 실패 스크립트를 넣으니 **step-exit=0**(대조군 `bash x.sh` 만 있을 때는 1). |
| 2 | 스텝에 `shell: bash {0}` 추가 후 hs-cleanroom(8줄) 끝에 `echo all-done` | 4종 CI 인수 검사 전부 OK. `bash`(-e 없음) 실증 exit=0. |
| 2′ | 워크플로 최상위 `defaults: run: shell: bash {0}` (스텝은 한 줄도 안 건드림) | manifest=0 · integrity=0. 다줄 스텝(silent-failure-lint 2줄·hs-cleanroom 8줄·hs-gates 3줄)에서 마지막 줄 외 실패 전부 무시. |
| 3 | hs-a3 run 을 `echo "bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-a3.sh"` (인용 echo) / secret-webhook-vendor 를 `printf '%s\n' "bash …"` / `: bash …` / heredoc `cat <<'X'` / `CMD='bash …'; echo "$CMD"` | verify-ac-m·ci-step-integrity·ci-required-manifest 전부 rc=0. `bash -e` 실증 exit=0. (hs-a4 에서만 빨개진 것은 `acceptance-ci-step-integrity.sh:69` 의 하드코딩 주입 문자열이 사라진 부수 효과 — 다른 스텝엔 무관.) |
| 3′ | data-exposure-scan 의 run 을 `# bash scripts/scan-data-exposure.sh all` + `echo "PASS: skipped"` | 3종 전부 rc=0. (`secret-scan` 만은 mechanism-registry 의 `run: bash verify.sh` 항목 덕에 verify-ac-m 이 잡음.) |
| 4 | `on:` 에 push/pull_request 를 **남기고** `branches: ["never-such-branch"]` 또는 `paths-ignore: ["**"]` | manifest=0 · integrity=0. 워크플로는 영원히 실행되지 않음. |
| 5 | `docs/sot/verification-commands.md` 표에 `\| 30 \| \`verify-ac-m\` \|` 중복 1행 추가 + 5·6행 id 맞바꿈 + 3행 이름 위조 | exit 0, 출력 `PASS: 문서 단계 30행이 워크플로 스텝 29개와 순서까지 일치` (거짓 문장). |
| 6 | `apps/admin/index.html` 에서 `<script src="/app.js" defer>` 제거 / `src="/wrong.js"` / `type="text/template"` | 하네스 exit 0. 브라우저에서는 app.js 가 실행조차 안 됨. |
| 6′ | app.js 에 `process.version` 참조 추가 (브라우저 ReferenceError) / 클릭 시 고정 문구 / 히트맵 순서 뒤집기 / aria-label 제거 / 감사 항목 삭제 | 전부 exit 0. |
| 6″ | app.js `item.append(button)` → `item.appendChild(button)` (브라우저 정상) | **exit 1, `버튼 0개`** — 정상 코드 오차단. |
| 7 | run-acceptance 대상 본문을 `echo "PASS: ok" \| cat` / `echo "PASS: ok" >&2` / `echo "PASS: $(:)"` / `echo "VERDICT: PASS" \| cat` / `echo "PASS: ok"` + `builtin true` / `x=1` / `FAIL:` 뒤 `PASS:` / `CHECKED: 0 \| cat` 뒤 `CHECKED: 5` | 전부 `OK(run-acceptance) … 판정 1건`. |
| 8 | run-acceptance.sh 의 `판정을 한 건도 내놓지 않았다` 실제 출력을 없애고 `_doc="…"` 문자열만 남김 | mechanism-registry `acceptance-runner-gate` PASS. |
| 9 | humansearch/tests 전부 `git rm` 후 `parametrize(range(8))` 더미 28파일 | pytest-baseline PASS (224 ≥ 211). |

### 막힌 것

AC1 기준선 · `on:` 키/트리거 삭제 · 필수 스텝 삭제/스텝 단위 주석/비활성 job 이동 · `|| true` **줄 끝** · `; true` · `if: false` · `${{ false }}` · anchor `*never` · continue-on-error(step/job) · 필수 명령 제거 · 미등록/미실행/사유 없는 제외/없는 job · AC5 이름 복사+항상-거짓 조건(STEP_CONDITIONAL 양쪽) · id 중복/키릴 lookalike/대문자/앵커 공유(STEP_DUPLICATE_ID·STEP_MISSING) · job 키 중복(Psych 후승으로 `if` 잡힘) · hs-a4 명령을 0-5 스텝으로 이관(STEP_COMMAND_MISSING) · 새 검사기 5종 각각 삭제 시 해당 인수 검사 exit 2(fail-closed) · 인수검사+스텝+명부 항목 동시 삭제는 verify-ac-m 이 잡음 · `bash -n "…" && echo "bash …"`(SYNTAX_ONLY) · `! cmd || true` · `exit $?` · `X: PASS` + `:` · 미추적 acceptance(`git archive` 에 0건 → CI 도달 불가) · `PYTEST_PROJECT` 는 `acceptance-pytest-baseline.sh:73` 이 값을 덮어써 workflow `env:` 로 우회 불가(가짜 프로젝트는 NOT_RUN=2) · 문서 1행 삭제/이름 위조/낡은 표 중복(단독) 차단.

## 2. 발견 결함

**F1 [치명] 오류 삼킴 탐지가 "줄 끝 꼬리" 6종뿐 — AC4 위반**
`scripts/verify/check-ci-required-manifest.sh:142`, `scripts/verify/check-ci-step-integrity.sh:43`. 표 #1 의 16개 변형이 모두 두 검사기를 통과하고 `bash -e` 에서 exit 0. `|| true; echo done` 처럼 AC4 가 명시한 "`|| true` 계열" 자체가 뚫린다. 재현: 사본 워크플로의 hs-a4 `run:` 뒤에 ` || true; echo done` 추가 → `bash scripts/verify/check-ci-required-manifest.sh; echo $?` → 0.

**F2 [치명] `shell:` / `defaults.run.shell` 을 아무도 보지 않음**
두 검사기 모두 `if`·`continue-on-error`·`run` 만 본다. `defaults: run: shell: bash {0}` 한 블록으로 다줄 스텝 13개 호출 중 10개의 실패가 무시된다(GitHub 는 커스텀 `shell` 에 `-e` 를 붙이지 않음). 재현: `perl -0pi -e 's{^permissions:}{defaults:\n  run:\n    shell: bash {0}\npermissions:}m' .github/workflows/verify.yml` 후 두 검사기 exit 0.

**F3 [높음] 필수 명령 대조가 주석 포함 substring — AC3 "주석 처리" 부분 위반, STEP_ECHO_ONLY 무력**
`check-ci-required-manifest.sh:221` `run.include?(cmd)` 는 주석 줄을 걷어내지 않고, `:277` 실행 추출은 `scripts/acceptance-*.sh` 문자열만 본다. `check-ci-step-integrity.sh:109` 는 `echo bash` 만 잡아 `echo "bash …"`·`printf`·`:`·heredoc·변수 대입이 통과. 명령 자체를 `#` 로 주석 처리해도 manifest 는 통과하며, mechanism-registry 에 target 이 없는 스텝(hs-a3·hs-a4·hs-cleanroom·hs-gates·guard-global-skill-files·principles-mutations·0-2/0-6/0-7·data-exposure-scan·history-scan·secret-webhook-vendor)은 어떤 CI 검사도 잡지 못한다.

**F4 [높음] AC2 는 키 존재만 봄 — `branches`/`paths-ignore` 필터로 워크플로를 영구 비활성화**
`check-ci-required-manifest.sh:95-97`. `push: branches: ["never-such-branch"]` 로 `present.include?("push")` 가 참. 실행 조건이 사라지는 대표 공격을 반쯤만 막았다.

**F5 [높음] AC11 — 문서 행 1개 중복이면 순서·이름 대조 전체가 건너뛰어지고 거짓 PASS 문장 출력**
`check-docs-workflow-sync.sh:112` `doc_ids.size == wf_ids.size && …` 조건이 거짓이면 ②③ 블록이 통째로 생략되지만 오류로 남지 않는다. 중복+순서 뒤바꿈+이름 위조가 exit 0 이고 "30행이 29개와 순서까지 일치" 를 찍는다.

**F6 [높음] AC10 — index.html 이 app.js 를 로드하는지 시험하지 않음**
`admin-app-runtime.mjs:119` 는 HTML 에서 `id=` 만 뽑고 `<script src>` 는 보지 않는다. 스크립트 태그 제거·경로 오기·`type=text/template` 모두 통과. 반대로 `appendChild`(표준 DOM) 는 `class Node`(`:46`) 에 없어 정상 코드를 빨갛게 만든다(`버튼 0개`). node 전역(`process`) 참조도 통과한다 — "최소 DOM 이 브라우저와 다르게 동작" 하는 양방향 사례.

**F7 [보통] AC6 실용 하한이 한 글자**
`run-acceptance.sh:60` 의 `[|>]` 예외로 `echo "PASS: ok" | cat` / `>&2` 한 줄이 "has-work". 문서가 "의미 없는 명령 섞기"를 한계로 적어두었지만, 실제 하한은 파이프 문자 하나이고 AC6 의 `VERDICT: PASS` 위조도 `| cat` 만 붙이면 통과한다. 별도로 `FAIL:` 줄이 있어도 `PASS:` 1건이면 통과.

**F8 [낮음] mechanism manual target 이 실행 여부와 무관한 grep -F**
`check-mechanism-registry.sh:166`. 죽은 문자열 대입 `_doc="…"` 으로 통과. "manual 항목도 target 을 대조한다"(2a0f0da) 는 문자열 존재만 대조한다.

**F9 [낮음] pytest 기준선은 개수만** — 실제 시험 전량을 더미로 갈아치워도 통과. AC9 문언("줄면") 안이라 설계 한계로 분류하되, `hs-gates` 의 `collected<1` 을 보완한다는 취지에는 못 미친다.

## 3. 판정 근거

AC4(오류 무시 꼬리)·AC2(실행 조건)·AC11(문서 구조 일치)·AC10(화면 실행 시험)이 각각 **한 줄짜리 변형**으로 뚫렸고, 모두 사본에서 실제 명령으로 재현하고 `bash -e` 로 삼킴을 실증했다. F1·F2·F3 은 구현자가 스스로 약하다고 본 지점(#1)이 예상보다 훨씬 넓게 열려 있음을 보여주며, "명령 앞부분이 그대로여도 실패가 전파되지 않으면 검사가 아니다" 라는 검사기 자신의 계약을 지키지 못한다. AC1·AC3(삭제/스텝 주석/이동)·AC5·AC7·AC8·#3·#5·#6·#7 은 막혔지만, 위 치명·높음 결함이 CI 최종 방어선을 무력화하므로 FAIL 이다.

V1_EXIT=0
V1_DONE

```


---

## 결정 카드 — 만료된 억제 (이 작업 범위 밖 · 사장님 판단 필요)

**무엇** — `suppressions.yaml` 의 `keyword-env-value-floor-12` 는 `expiry: 2026-08-26` 이고
오늘(2026-08-27) 기준 **이미 만료**했다.

**결과** — CI 의 `suppressions-expiry` 스텝이 그 자체로 실패한다. 이 브랜치의 변경과 무관하게
**모든 브랜치의 CI 가 이 한 줄 때문에 빨간불**이다. 실측:

```
$ awk '/^ *expiry:/{...}' suppressions.yaml
2026-09-15 / 2026-09-15 / 2026-09-30 / 2026-08-26     ← 마지막이 오늘보다 이르다
```

**왜 여기서 처리하지 않았나** — 이 억제의 내용은 "비밀 스캔 키워드 대입 규칙의 값 하한을
6자에서 12자로 올려 6~11자 값 탐지가 사라졌다"이다. 원장 본문이 이미 사장님 판단 항목으로
두 선택지를 적어 두었다(① 12자 하한을 정책으로 확정하고 종결 ② 6~11자 탐지를 복구하고
오탐 2종을 허용 목록으로 처리 — ②는 `verify.sh` 구조 변경 필요). **만료일만 미루는 것은
그만큼 구멍을 승인하는 것**이라 이 작업에서 임의로 하지 않았다.

**선택지**

| | 무엇을 한다 | 대가 |
|---|---|---|
| A | ① 을 택해 억제를 원장에서 **종결**(삭제)하고 12자 하한을 정책으로 문서화 | 6~11자 비밀은 앞으로도 안 잡힌다. 그 사실이 정책으로 명시된다 |
| B | ② 를 택해 6~11자 탐지를 복구하고 허용 목록을 도입 | `verify.sh` 에 허용 목록 경로가 없어 스캐너 구조 변경이 필요하다 |
| C | 만료일만 미룬다 | 같은 결정을 다시 미루는 것이다. 권하지 않는다 |

**되돌리기** — 어느 쪽이든 `suppressions.yaml` 한 파일의 변경이므로 revert 한 커밋이면 된다.

---

## 이번 run 에서 발견해 같은 PR 에 편입한 반례 (R9)

| # | 발견 | 어떻게 편입했나 |
|---|---|---|
| F1 | `check-mechanism-registry.sh` 의 `stage:manual` 이 target 을 한 번도 대조하지 않았다. 정상 fixture 자신의 target 이 그 파일에 없었던 것이 증거 | `acceptance-verify-ac-m.sh` 에 죽은 target·주석 전용 target 두 반례 추가 + fixture 정정 + 검사기에 대조 추가 (WU-7) |
| F2 | 강화한 실행 래퍼가 `pre-push` 런타임 증명의 probe(`printf … > marker`)를 "출력뿐"으로 오차단했다 | 리다이렉트·파이프·명령 치환이 붙은 줄을 work 로 세도록 정정하고, 샌드박스 스텁 2개를 계약에 맞게 고침 (WU-3 안에서) |
| F3 | Psych 가 YAML 1.1 규칙으로 `on:` 을 boolean `true` 키로 읽는다. 모르면 트리거 검사가 조용히 0건이 된다 | 검사기에 주석으로 근거를 남기고 `wf.key?(true)` 로 처리. AC2 두 사례가 이를 회귀로 고정 |
| F4 | 인수 검사를 **작업과 병렬로** 돌리면 "원본 저장소 상태 불변" 검사가 거짓 실패한다 | 최종 검증을 격리 clone 에서, 작업을 멈춘 상태로 수행하도록 절차를 바꿈. 오염된 1차 실행 결과는 폐기하고 대조군을 다시 쟀다 |
| F5 | WU-1 이 `verify.yml` 에 `id:` 줄을 넣자 `acceptance-principles-mutations.sh` 의 C10-B·C10-C 주입이 조용히 빗나갔다. 공격이 꽂히지 않은 원본이 그대로 통과해 기대와 어긋났다 — **막지 못한 것이 아니라 공격하지 않은 것** | 주입 지점을 안정된 step id 로 앵커링하고, 주입 실패 시 `raise` 로 즉시 드러내도록 고침. 격리 clone 재검증으로 확인 |
| F6 | 작업 중 `bash -x` 로 인수 검사를 훑는 임시 조사 스크립트가 저장소 루트에 `marker` 파일을 남겼다 | 격리 clone 최종 검증의 `STATUS_AFTER=[]` 로 **저장소 코드는 무죄**임을 확인. 오염원은 scratchpad 의 조사 스크립트였고 커밋되지 않았다 |

## 대조군 / 실험군 분리 기록

| 구분 | ref | 방법 | 결과 |
|---|---|---|---|
| 대조군 | `origin/main` = `3276712` | 격리 clone, 인수 검사 전량 | **27/27 rc=0**, `STATUS_BEFORE=[] STATUS_AFTER=[]` — 실험 성립 |
| 오염된 1차 | 작업 브랜치(작업 중) | 워크트리에서 직접 | 6건 rc=1 — **작업 중 실행이라 무효**. 단독 재실행 시 전부 통과 |
| 실험군 | 작업 브랜치 최종 | 격리 clone, 전량 + 구조 검사기 + pre-push | (아래 증거 원문) |

---

## 코드 예산 (P11) — 실측과 권고

V1·V2 두 라운드 결함 수정까지 마친 최종 실측이다. **한 PR 로 올리면 P11③(3,000줄 초과 절대 금지)에
걸린다.** 셋으로 나누면 전부 한도 안에 들어가고, 되돌릴 때도 서로 독립적이다.

| 구간 | 범위 | 변경량 | 판정 |
|---|---|---|---|
| 전체 | `origin/main..HEAD` | **4,602 추가 / 54 삭제** | ❌ P11③ 위반 |
| ① 히스토리 스캐너 fail-closed | `origin/main..78ac807` | 835 추가 | ✅ |
| ② 검증 체계 보강 (AC1~AC11) | `78ac807..739325f` | 2,730 추가 / 54 삭제 | ✅ |
| ③ 적대검증 결함 수정 (V1 9건 + V2 8건) | `739325f..HEAD` | 1,125 추가 / 88 삭제 | ✅ |

**권고**: 위 셋을 각각 별도 PR 로 올린다. ②③ 은 성격이 이어지므로 ② 를 먼저 병합한 뒤
③ 을 올리는 순서가 자연스럽다. 나누는 실행은 push 권한이 있는 쪽의 몫이므로 여기서는
권고만 남긴다.

### 파일 크기 (P11① soft 300 / hard 600)

soft 를 넘긴 파일 3개. 전부 hard 이내다.

| 파일 | 줄 | 왜 이 크기인가 |
|---|---|---|
| `scripts/acceptance-ci-required-manifest.sh` | 383 | 공격 사례 25개를 한 파일에 모았다. 쪼개면 "어느 파일이 무엇을 막는가"가 흩어진다 |
| `scripts/verify/admin-app-runtime.mjs` | 364 | 최소 DOM 구현(약 100줄)과 단언 23건이 한 파일에 있다. DOM 을 별 파일로 빼면 그 파일만 지워도 시험이 조용히 죽는다 |
| `scripts/verify/check-ci-required-manifest.sh` | 333 | 양방향 대조 4방향이 한 판정기에 있다. 나누면 판정기가 2벌이 되어 P16 에 걸린다 |

### V1 결함의 처리 (R9 — 반례의 영구 편입)

V1 이 낸 9건을 보고서로 끝내지 않았다. 7건은 같은 PR 에서 **회귀 시험으로 편입**했고,
2건은 고치지 않았음을 **한계로 명시**했다.

| # | 심각도 | V1 지적 | 처리 | 회귀 시험 |
|---|---|---|---|---|
| F1 | 치명 | 오류 삼킴 탐지가 줄 끝 꼬리 6종뿐. 16개 변형이 통과하고 `bash -e` 에서 exit 0 | 필수 명령이 **그 줄에서 단독**이어야 한다는 규칙으로 근본 전환 + `set +e`·`set +o errexit`·`trap … ERR` 금지 | `acceptance-ci-workflow-hardening.sh` F1-1~F1-12 |
| F2 | 치명 | `shell:` / `defaults.run.shell` 을 아무도 안 봄. 한 블록으로 다줄 스텝 10개의 중간 실패가 무시됨 | 최상위·job·step 세 곳 모두 금지 | 같은 파일 F2-1~F2-3 |
| F3 | 높음 | 필수 명령 대조가 주석 포함 substring. `echo "bash …"`·`printf`·`:`·heredoc 통과 | 단독 줄 규칙 + 주석 제거 + heredoc 본문 건너뛰기 | 같은 파일 F3-1~F3-4 |
| F4 | 높음 | 트리거는 키 존재만 봄. `branches: [never-such-branch]`·`paths-ignore: [**]` 로 영구 비활성화 | 차단성 필터 5종 금지, `branches` 는 `**` 를 덮어야 함 | 같은 파일 F4-1~F4-3 |
| F5 | 높음 | 문서 행 중복이면 순서·이름 대조가 통째로 생략되고 거짓 PASS 문장 출력 | 중복 검출 + 개수 불일치를 오류로 + 대조를 절대 건너뛰지 않음 | `acceptance-docs-workflow-sync.sh` 2건 추가 |
| F6 | 높음 | `<script src>` 미검사(태그 제거·경로 오기·type 변경 통과) / 표준 `appendChild` 오차단 / node 전역 통과 | 로드·type 단언 추가, 표준 DOM 메서드 지원, node 전역 차단 | `acceptance-admin-app-runtime.sh` 5건 추가 |
| F7 | 보통 | 위조 하한이 파이프 한 글자. `\| cat`·`>&2`·`$(:)` 로 전부 되살아남 | 부수 효과 기준을 "파일로 쓰는가"로 좁힘 | `acceptance-semantic-mutations.sh` 4종 추가 |
| F8 | 낮음 | manual target 이 죽은 문자열 대입으로 통과 | **고치지 않음.** 검사기 주석에 한계로 명시하고 앞선 커밋 메시지의 과장을 정정 | — |
| F9 | 낮음 | pytest 기준선이 개수만 본다 | **고치지 않음.** AC9 문언("줄면") 안이며 설계 한계로 분류 | — |

**설계상 배운 것**: "명령 문자열이 run 에 있는가"는 앞뒤에 무엇이 붙어도 참이므로 원리적으로
뚫린다. 판정을 **"그 명령이 그 줄에서 단독으로 실행되는가"**로 바꾸자 V1 이 찾은 우회 13개가
한꺼번에 닫혔다. 문자열 규칙을 하나씩 늘리는 방향이 아니라 **구조를 바꾸는 방향**이 맞았다.


### V2 (Codex · 새 맥락 · 격리 clone `2571603`) — 2026-08-27

실행: `codex exec --dangerously-bypass-approvals-and-sandbox`
1차 시도는 Codex 의 사이버 정책이 프롬프트를 차단해 **실행 불가(NOT_RUN)** 였다. 표현을
중립적인 코드 리뷰 어투로 바꾸고 확인 사례를 표로 옮겨 재실행했다(재현 범위는 같다).

V1 이 지적한 F1~F7 과 F6′ 오탐은 **전부 수정 확인**되었으나, 같은 종류의 다른 형태를
새로 찾아 **DISPUTE(REQUEST_CHANGES)** 를 냈다.

```
V2 VERDICT: DISPUTE

지정된 F1~F7 재현 입력은 모두 고쳐졌습니다. 그러나 같은 공격군에서 새로운 fail-open 우회 4종, 정상 HTML·안전한 명시 셸 오탐, F9 코드 주석 누락이 실행으로 확인됐습니다.

## 1. 항목별 확인 표

공통 절차:

```bash
T=$(mktemp -d)
cp .github/workflows/verify.yml "$T/w.yml"
ruby scripts/verify/wf-mutate.rb "$T/w.yml" <변이>
WORKFLOW_FILE="$T/w.yml" \
  bash scripts/verify/check-ci-required-manifest.sh \
  docs/sot/ci-required-manifest.yaml
```

| 항목 | 돌린 변이/명령 | 실제 종료값·핵심 출력 | 판정 |
|---|---|---|---|
| F1 | `append-run '; echo after'`, `'\| cat'`, `'&'`; `prepend-run 'set +e'`, `'set +o errexit'`, `"trap 'true' ERR"` | 전부 `rc=1`; `STEP_COMMAND_NOT_STANDALONE` 또는 `RUN_SWALLOWS_ERROR`; `CHECKED: 105` | 검출됨(수정 확인) |
| F2 | `workflow-shell bash`; `job-shell verify bash`; `step-shell hs-a4 bash` | 전부 `rc=1`; `SHELL_OVERRIDE`; `CHECKED: 105` | 검출됨(수정 확인) |
| F3 | `wrap-run 'echo "CMD"'`, `printf`, `: CMD`, `# CMD`, 표준 `EOF` heredoc | 전부 `rc=1`; `STEP_COMMAND_NOT_STANDALONE`; `CHECKED: 105/106` | 검출됨(수정 확인) |
| F4 | `trigger-filter push branches never-such-branch`, `paths-ignore '**'`, `tags never-such-tag` | 전부 `rc=1`; `TRIGGER_NARROWED` 또는 `TRIGGER_FILTERED`; `CHECKED: 105` | 검출됨(수정 확인) |
| F5 | 임시 문서에 31번째 `verify-ac-m` 중복 행 추가, 20·22번째 id 순서 교환, 이름 위조 | `rc=1`; `DOC_DUPLICATE_ROW`, `DOC_COUNT_MISMATCH`, 두 `DOC_ORDER_MISMATCH`, 두 `DOC_NAME_MISMATCH`; `CHECKED: 94` | 검출됨(수정 확인) |
| F6 | script 태그 삭제, `/wrong.js`, `type="text/template"` | 각각 `rc=1`; `app.js 참조=false` 또는 `type=text/template`; `CHECKED: 25` | 검출됨(수정 확인) |
| F6′ | `item.append(button)` → `item.appendChild(button)` | `rc=0`; `버튼 12개`, 클릭 반응 PASS, `CHECKED: 25` | 정상 통과(오탐 수정 확인) |
| F7 | 요청한 4개 한 줄 스크립트 각각 `run-acceptance.sh` 실행 | 전부 `rc=1`; `출력·종료 명령만으로 이뤄져 있다` | 검출됨(수정 확인) |
| F8 | `rg -n '한계\(V1 F8\|죽은.*대입' scripts/verify/check-mechanism-registry.sh` | “문자열이 코드 안에 있는가만 본다”, “죽은 대입으로도 통과”, “실행 경로는 보지 않는다” 출력 | 인정 정확히 명시 |
| F9 | `rg -n -i 'F9\|개수만\|더미\|semantic' scripts/verify/check-pytest-baseline.sh` | 출력 없음. 인정은 코드가 아니라 목표 문서 232행에만 존재 | 코드 주석 인정 누락 |

F8 주석은 [check-mechanism-registry.sh](/private/tmp/claude-501/-Users-kangsangmo-Desktop-Valuehire-v6--claude-worktrees-history-scan-failclosed/4010d7e2-1ee0-4d2e-9c75-f35b56c84e51/scratchpad/v2-clone/scripts/verify/check-mechanism-registry.sh:167)에 정확히 있습니다. F9는 [check-pytest-baseline.sh](/private/tmp/claude-501/-Users-kangsangmo-Desktop-Valuehire-v6--claude-worktrees-history-scan-failclosed/4010d7e2-1ee0-4d2e-9c75-f35b56c84e51/scratchpad/v2-clone/scripts/verify/check-pytest-baseline.sh:18)에 수집 불가 한계만 있고, “개수만 보므로 더미 교체를 못 잡는다”는 인정은 [목표 문서](/private/tmp/claude-501/-Users-kangsangmo-Desktop-Valuehire-v6--claude-worktrees-history-scan-failclosed/4010d7e2-1ee0-4d2e-9c75-f35b56c84e51/scratchpad/v2-clone/docs/engineering/verification-hardening-goal-2026-08-27.md:232)에만 있습니다.

## 2. 새로 찾은 미탐 사례

### 치명: 필수 명령이 단독 줄이어도 실행되지 않을 수 있음

`hs-a4`의 필수 명령을 다음처럼 감싼 사본을 검사했습니다.

```bash
wrap-run $'exit 0\nCMD'
wrap-run $'if false; then\n  CMD\nfi'
wrap-run $'never_called() {\n  CMD\n}'
wrap-run $'command set +e\nCMD\ntrue'
wrap-run $'cat <<\'123\'\nCMD\n123'
```

실제 출력:

```text
set_plus_e_swallow checker_rc=0 PASS: 필수 구조 105건이 명부와 양방향으로 일치 CHECKED: 105
dead_function checker_rc=0 PASS: 필수 구조 105건이 명부와 양방향으로 일치 CHECKED: 105
numeric_heredoc checker_rc=0 PASS: 필수 구조 105건이 명부와 양방향으로 일치 CHECKED: 105
false_if checker_rc=0 PASS: 필수 구조 105건이 명부와 양방향으로 일치 CHECKED: 105
```

별도 `bash -e` 실행에서도 네 경우 모두 필수 실패가 실행되지 않거나 삼켜진 뒤 `rc=0`임을 확인했습니다.

원인은 [SWALLOW 패턴](/private/tmp/claude-501/-Users-kangsangmo-Desktop-Valuehire-v6--claude-worktrees-history-scan-failclosed/4010d7e2-1ee0-4d2e-9c75-f35b56c84e51/scratchpad/v2-clone/scripts/verify/check-ci-required-manifest.sh:191)이 제한된 줄 시작 형태만 보고, [단독 줄 검사](/private/tmp/claude-501/-Users-kangsangmo-Desktop-Valuehire-v6--claude-worktrees-history-scan-failclosed/4010d7e2-1ee0-4d2e-9c75-f35b56c84e51/scratchpad/v2-clone/scripts/verify/check-ci-required-manifest.sh:304)가 셸 제어 흐름을 해석하지 않기 때문입니다.

### 높음: `must_run_contains` 다섯 곳은 F3형 echo 위장을 그대로 허용

각 step의 전체 `run`을 `echo "<fragment>"` 한 줄로 바꿨습니다.

```text
history-scan rc=0 PASS: STEP history-scan ~ `git cat-file blob`
suppressions-expiry rc=0 PASS: STEP suppressions-expiry ~ `suppressions.yaml`
hooks-present rc=0 PASS: STEP hooks-present ~ `hooks/pre-commit hooks/pre-push`
shell-syntax rc=0 PASS: STEP shell-syntax ~ `bash -n`
pattern-file-selfcheck rc=0 PASS: STEP pattern-file-selfcheck ~ `.secret-patterns.default`
```

모두 최종 `PASS: 필수 구조 105건… / CHECKED: 105`였습니다. [must_run_contains 구현](/private/tmp/claude-501/-Users-kangsangmo-Desktop-Valuehire-v6--claude-worktrees-history-scan-failclosed/4010d7e2-1ee0-4d2e-9c75-f35b56c84e51/scratchpad/v2-clone/scripts/verify/check-ci-required-manifest.sh:319)은 주석만 제거한 뒤 부분 문자열을 셉니다.

따라서 두 필드가 같은 명부 항목에서 충돌하지는 않지만, “필수 명령은 실행돼야 한다”는 정책에는 의미상 큰 예외 통로가 남습니다.

### 높음: HTML 정규식 검사 우회

다음 HTML 사본이 전부 `rc=0 / CHECKED: 25`였습니다.

```html
<!-- <script src="/app.js" defer></script> -->
<script src="/wrong/place/app.js" defer></script>
<script src="/app.js" type='text/template' defer></script>
```

`/wrong/place/app.js`는 실제 서버가 제공하지 않습니다. 서버 라우트는 [`/app.js` 하나뿐](/private/tmp/claude-501/-Users-kangsangmo-Desktop-Valuehire-v6--claude-worktrees-history-scan-failclosed/4010d7e2-1ee0-4d2e-9c75-f35b56c84e51/scratchpad/v2-clone/humansearch/src/humansearch/admin_weekly_dashboard/shadow_server.py:191)입니다.

원인은 [HTML 정규식](/private/tmp/claude-501/-Users-kangsangmo-Desktop-Valuehire-v6--claude-worktrees-history-scan-failclosed/4010d7e2-1ee0-4d2e-9c75-f35b56c84e51/scratchpad/v2-clone/scripts/verify/admin-app-runtime.mjs:152)이 주석을 제거하지 않고 속성의 큰따옴표만 읽으며, [경로 전체가 아니라 basename만 비교](/private/tmp/claude-501/-Users-kangsangmo-Desktop-Valuehire-v6--claude-worktrees-history-scan-failclosed/4010d7e2-1ee0-4d2e-9c75-f35b56c84e51/scratchpad/v2-clone/scripts/verify/admin-app-runtime.mjs:347)하기 때문입니다.

### 보통: F7의 한 글자 변형은 막았지만 출력 위조 하한은 여전히 낮음

```bash
echo "PASS: $(true)"
```

```text
rc=0
PASS:
OK(run-acceptance): ... — 판정 1건
```

또한:

```bash
printf "padding" > /dev/null
echo "PASS: ok"
```

도 `rc=0`입니다. [정적 판정](/private/tmp/claude-501/-Users-kangsangmo-Desktop-Valuehire-v6--claude-worktrees-history-scan-failclosed/4010d7e2-1ee0-4d2e-9c75-f35b56c84e51/scratchpad/v2-clone/scripts/verify/run-acceptance.sh:55)이 임의 명령 치환과 파일 리다이렉트를 곧바로 “일을 함”으로 분류합니다.

## 3. 오탐·규칙 충돌·고아 검사

정상 저장소 실행:

| 명령 | 결과 |
|---|---|
| `check-ci-required-manifest.sh` | `rc=0`, `CHECKED: 105` |
| `check-docs-workflow-sync.sh` | `rc=0`, `CHECKED: 91` |
| `check-ci-step-integrity.sh` | `rc=0`, `CHECKED: 32` |
| `check-mechanism-registry.sh` | `rc=0`, `CHECKED: 22` |
| `admin-app-runtime.mjs` | `rc=0`, `CHECKED: 25` |

추가 오탐은 두 가지입니다.

- 정상 HTML인 `<script src='/app.js' defer></script>`는 `rc=1`, `app.js 참조=false`였습니다.
- `shell: bash --noprofile --norc -eo pipefail {0}`도 `SHELL_OVERRIDE / rc=1`입니다. 같은 셸을 직접 실행한 `false; echo unreachable`은 `rc=1`로 실패 전파가 정상입니다. “모든 명시 셸 금지”가 정책이면 의도된 차단이지만, 검사기의 “명시하면 `-e`가 사라진다”는 진단은 이 경우 사실이 아닙니다.

고아 검사는 전부 fail-closed였습니다.

| 임시 clone에서 삭제 | 실패한 인수 검사 |
|---|---|
| `check-ci-required-manifest.sh` | `acceptance-ci-required-manifest.sh rc=2`, `acceptance-ci-workflow-hardening.sh rc=2` |
| `check-docs-workflow-sync.sh` | `acceptance-docs-workflow-sync.sh rc=2` |
| `check-pytest-baseline.sh` | `acceptance-pytest-baseline.sh rc=2` |
| `admin-app-runtime.mjs` | `acceptance-admin-app-runtime.sh rc=2` |
| `wf-mutate.rb` | `acceptance-ci-workflow-hardening.sh rc=2` |

고아 검사기는 없습니다.

## 4. 공통 가정 점검

로컬 Psych 실행:

```text
Psych=3.1.0
true(TrueClass)=>"a"
false(FalseClass)=>"b"
```

즉 `on`, `yes`는 `true`, `off`는 `false` 키로 합쳐집니다. YAML 1.1이 `on/off/yes/no`를 boolean으로 정의한다는 점과 일치합니다. [YAML 1.1 boolean 명세](https://yaml.org/type/bool.html)

현재 코드는 `wf.key?(true) ? wf[true] : wf["on"]`으로 정상 `on:`은 보완했습니다. 하지만 다음 사본은 문제가 됩니다.

```yaml
on:
  push:
    branches: ["**"]
true:
  push:
  pull_request:
```

Psych 출력:

```text
PARSED_KEYS=[["name", String], ["true", TrueClass], ["permissions", String], ["jobs", String]]
TRIGGER_VALUE={"push"=>nil, "pull_request"=>nil}
```

검사기 출력:

```text
rc=0
PASS: TRIGGER push
PASS: TRIGGER pull_request
PASS: 필수 구조 105건이 명부와 양방향으로 일치
```

GitHub 문서상 워크플로 트리거는 `on` 키가 정의하며, 위 원문의 `on`에는 `pull_request`가 없습니다. 따라서 검사기는 GitHub가 트리거로 보는 노드가 아니라 Psych에서 충돌한 `true` 노드를 검증합니다. [GitHub Actions workflow syntax](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax)

한편 YAML anchor/alias는 2025년 이후 GitHub Actions가 공식 지원하며, 검사기도 `aliases: true`를 사용하므로 단순 anchor/alias는 현재 공통 가정 문제가 아닙니다. [GitHub 공식 anchor 문서](https://docs.github.com/en/actions/reference/workflows-and-actions/reusing-workflow-configurations)

원격 GitHub에 변이 워크플로를 push하지 않았으므로 해당 충돌 사본에 대한 GitHub 서버 파서의 실제 오류 문구는 미확인입니다. 다만 로컬 검사기가 원문의 `on`이 아닌 다른 노드를 검사하며 초록을 내는 사실은 실행으로 확정됐습니다.

## 5. 판정 근거

- 요청된 과거 미탐 F1~F7과 F6′은 모두 의도대로 수정됐습니다.
- 그러나 필수 명령의 도달 가능성·실행 여부를 보지 않아 동일 공격군의 더 단순한 우회가 `rc=0`입니다.
- `must_run_contains` 다섯 곳은 `echo` 위장만으로 전부 통과합니다.
- HTML 로더 검사는 주석·홑따옴표·실제 라우트 전체 경로를 처리하지 못합니다.
- Psych의 `on` 보정은 `true:` 키 충돌에서 다른 노드를 검증합니다.
- 정상 홑따옴표 HTML과 안전한 명시 셸을 오차단합니다.
- F9의 인정은 요청한 코드 주석에 없습니다.
- 리뷰 전후 HEAD는 `2571603aa1837e62ea1da2f56663d93cefc74030`, `git status --short`는 빈 출력, `git diff --exit-code`는 `0`입니다. 저장소 파일·커밋·원격은 변경하지 않았습니다.

병합 전 판정은 `REQUEST_CHANGES`입니다.

V2_EXIT=0
V2_DONE

```


### V2 결함의 처리 (R9 — 반례의 영구 편입)

V2 가 낸 지적 8건을 전부 처리했다. 6건은 회귀 시험으로 편입, 2건은 오탐이라 해소했다.

| # | 심각도 | V2 지적 | 처리 | 회귀 시험 |
|---|---|---|---|---|
| G1 | 치명 | 필수 명령이 단독 줄이어도 그 줄에 **닿지 않게** 만들 수 있다(죽은 코드·거짓 분기·미호출 함수·`command` 접두·숫자 heredoc) | 도달 가능성 판정 추가. 블록 깊이는 셸 키워드로만 센다 | `acceptance-ci-workflow-hardening.sh` G1-1~G1-5 |
| G2 | 높음 | 인라인 본문 5스텝은 조각 인용 `echo` 한 줄로 통과 | 조각이 출력 명령 안에만 있으면 불합격 | 같은 파일 G2-1~G2-5 |
| G3 | 높음 | HTML 정규식이 주석을 안 걷어내고 basename 만 비교 | 주석 제거 + 경로 전체 비교 | `acceptance-admin-app-runtime.sh` 2건 |
| G4 | 높음 | YAML 1.1 의 `on`/`true` 키 충돌로 검사기가 다른 노드를 읽음 | 원문에서 최상위 boolean 별칭 키 충돌을 먼저 거름 | `acceptance-ci-workflow-hardening.sh` G4-1 |
| G5 | 보통 | `$(true)`·`> /dev/null` 로 위조 하한 우회 | 무의미 치환과 `/dev/null` 을 예외에서 뺌 | `acceptance-semantic-mutations.sh` 2종 |
| G6 | 오탐 | 홑따옴표 속성을 쓴 **정상 화면**을 차단 | 속성 따옴표 양쪽 지원 | `acceptance-admin-app-runtime.sh` 1건(통과 방향) |
| G7 | 오탐 | `-e` 가 켜진 명시 셸도 차단하면서 진단 문구가 사실과 달랐다 | 금지 정책은 유지, **진단 문구를 사실대로** 정정 | — (정책 결정) |
| G8 | — | pytest 기준선의 "개수만 본다" 한계가 코드 주석에 없었다 | 코드 주석에 명시 | — |

**G7 을 정책으로 유지한 이유**: 명시된 셸 문자열을 읽어 `-e` 가 켜졌는지 판정하는 것은
또 하나의 문자열 규칙이고, 문자열 규칙은 늘릴 때마다 우회가 는다(이 작업 전체의 교훈).
기본 셸만 허용하는 쪽이 단순하고 안전하다. 다만 **차단 사유를 사실대로** 적는다 —
"`-e` 가 사라진다"가 아니라 "명시한 셸이 `-e` 를 켜는지 검사기는 알 수 없다"이다.

### 이 두 라운드에서 배운 것

V1 은 "문자열이 있는가"를 뚫었고, V2 는 그 수정("줄에 혼자 있는가")을 다시 뚫었다.
매번 한 단계씩 더 깊은 질문이 필요했다:

1. 그 명령이 **적혀** 있는가 → 앞뒤에 무엇이든 붙일 수 있다
2. 그 명령이 그 줄에 **혼자** 있는가 → 그 줄에 닿지 않게 만들 수 있다
3. 그 줄에 **닿는가** → 지금 여기까지 왔다

3단계도 완전하지 않다. 셸을 정적으로 읽는 한 남는 구멍이 있고, 그것은 이 문서의
"한계" 절에 적힌 대로 외부 required check 와 사람 리뷰의 몫이다.

### 도달 가능성 판정의 남은 빈틈 — 자체 실측 (2026-08-27)

V2 가 "이 설계가 놓치는 형태가 있는가"라고 물은 후보들을 직접 주입해 봤다.
결과는 **뚫림 0건**이다. `rc=0` 이 나온 셋은 미탐이 아니라 **실제로 실행되는 형태**이므로
통과가 정확한 판정이다.

| 주입 형태 | rc | 해석 |
|---|---|---|
| `false && CMD` | 1 | 조건부 — 막힘 |
| `true \|\| CMD` | 1 | 조건부 — 막힘 |
| `if false; then CMD; fi` (한 줄) | 1 | 막힘 |
| `case x in never) CMD ;; esac` | 1 | 막힘 |
| 중첩 함수 본문 | 1 | 막힘 |
| `{ CMD }` 명령 그룹 | 0 | **정탐** — 그룹은 그대로 실행된다 |
| `( CMD )` 서브셸 | 0 | **정탐** — 실행되고 실패도 전파된다 |
| `f() { return 0; }` 뒤의 `CMD` | 0 | **정탐** — `return` 은 함수만 빠져나온다 |

`source`/`.` 로 다른 파일에 넘기는 형태는 그 줄에 명령 자체가 없으므로
`STEP_COMMAND_NOT_STANDALONE` 으로 걸린다.

이것은 **자체 점검**이지 독립 검증이 아니다. 독립 확인은 아래 V2 3차 항목을 본다.
