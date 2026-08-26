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

(후기록 — V1/V2 판정 본문을 여기에 append 한다)

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

## 대조군 / 실험군 분리 기록

| 구분 | ref | 방법 | 결과 |
|---|---|---|---|
| 대조군 | `origin/main` = `3276712` | 격리 clone, 인수 검사 전량 | **27/27 rc=0**, `STATUS_BEFORE=[] STATUS_AFTER=[]` — 실험 성립 |
| 오염된 1차 | 작업 브랜치(작업 중) | 워크트리에서 직접 | 6건 rc=1 — **작업 중 실행이라 무효**. 단독 재실행 시 전부 통과 |
| 실험군 | 작업 브랜치 최종 | 격리 clone, 전량 + 구조 검사기 + pre-push | (아래 증거 원문) |

---

## 코드 예산 (P11) — 실측과 권고

| 구간 | 변경량 | 판정 |
|---|---|---|
| 전체 브랜치 `origin/main..HEAD` | **3,481 추가 / 52 삭제** | P11③ **3,000줄 초과** — 한 PR 로 올리면 원칙 위반 |
| 선행 작업분 `origin/main..78ac807` (히스토리 스캐너) | 835 추가 | 단독으로는 문제 없음 |
| 이번 세션분 `78ac807..HEAD` (검증 체계 보강) | 2,646 추가 / 52 삭제 | 단독으로는 문제 없음 |

**권고**: 이 브랜치에는 성격이 다른 두 작업이 겹쳐 있다. **PR 을 둘로 나눈다.**
① `b0f4f2e..78ac807` — 히스토리 스캐너 fail-closed (835줄)
② `b030c08..HEAD` — 검증 체계 보강 (2,646줄)
둘 다 3,000줄 이하가 되고, 되돌릴 때도 서로 독립적이다. 나누는 실행은 push 권한이 있는
쪽의 몫이므로 여기서는 권고만 남긴다.

### 파일 크기 (P11① soft 300 / hard 600)

soft 를 넘긴 파일 3개. 전부 hard 이내다.

| 파일 | 줄 | 왜 이 크기인가 |
|---|---|---|
| `scripts/acceptance-ci-required-manifest.sh` | 383 | 공격 사례 25개를 한 파일에 모았다. 쪼개면 "어느 파일이 무엇을 막는가"가 흩어진다 |
| `scripts/verify/admin-app-runtime.mjs` | 364 | 최소 DOM 구현(약 100줄)과 단언 23건이 한 파일에 있다. DOM 을 별 파일로 빼면 그 파일만 지워도 시험이 조용히 죽는다 |
| `scripts/verify/check-ci-required-manifest.sh` | 333 | 양방향 대조 4방향이 한 판정기에 있다. 나누면 판정기가 2벌이 되어 P16 에 걸린다 |
