# WU0-A2 — 보호 CI 정적 실행 문맥과 파서 모호성 보정

## 결론

기존 WU0-A의 합격 판정은 취소한다. 같은 `run` 글자라도 job·step의 실행 문맥과 중복 key·alias·merge가 선언 의미를 바꿀 수 있는데 d1b1ebe의 검사와 V1/V2는 이를 시험하지 않았다.

이번 작업은 보호 job·step의 정확한 정적 선언, workflow `env`·`defaults` 부재, run 줄 경계, YAML/JSON fail-closed만 보정한다. WU0-B/C/D/E가 남으므로 WU0-A2가 합격해도 저장소 전체 안전성은 `CONDITIONAL`이며 SHIP 또는 merge-ready를 주장하지 않는다.

## 판단 근거

- 위험등급은 L3이다. CI·검사기·기계 정본·인수 시험을 함께 바꾸는 공유 안전장치다.
- RED→GREEN은 빠진 동작 때문에 실패하는 시험을 먼저 독립 commit으로 보존하고 최소 구현으로 통과시키는 절차다.
- 정본은 현재 저장소 파일과 이 문서의 T 계약이다. 구현 Codex(G), 실제 Claude CLI(V1), 새 맥락 Codex(V2)가 같은 계약에 동의해야 한다.
- 기존 digest는 workflow와 계약의 부분 drift를 잡는 tripwire일 뿐, checker까지 바꾸는 작성자에 대한 외부 신뢰 기준은 아니다.

## 기준선과 금지

- 세션 ID: `609BF375-87ED-4ABD-AC85-1B2CF76E1AA1`
- base: `c59bad7b160c473cda5545e76e6fa6bcc711a7ea`
- 기존 WU0-A HEAD: `d1b1ebed926424878161cd7a04c00c3878039e6a`
- 원본 dirty main HEAD: `3094eefa646b102074dfb6401777afe450223e6c`
- 신규 worktree: `worktrees/wu0a2-ci-static-context`
- 신규 branch: `task/wu0a2-ci-static-context`
- fetch: UTC `2026-08-25T17:41:35Z`, KST `2026-08-26T02:41:35+0900`, exit `0`, `origin/main=c59bad7b160c473cda5545e76e6fa6bcc711a7ea`.
- 원본 시작 상태: staged `0`, status SHA-256 `63a8bc253476fbddc5e2e07e8ddd7605b624c1fb8c7bbeeb83328858e3518a46`.
- 기존 WU 시작 상태: staged `0`, clean, status SHA-256 `e987a792deb0d3b476b398931cdaee54238672e0519ae76620dbf12faf3123a6`.
- 원본 main·기존 WU를 수정/reset/checkout/clean하지 않는다. push·PR·merge를 하지 않는다.
- 파괴적·변조 시험은 git 환경변수를 해제한 `mktemp` 사본에서만 한다.
- `3094eef` finding-runner 관련 파일과 WU0-B/C/D/E 구현은 diff에 넣지 않는다.

## 직접 로드 장부

### 코딩 원칙 정본

- 명령: `sed -n '1,$p' docs/sot/coding-principles.md`
- HEAD: `d1b1ebed926424878161cd7a04c00c3878039e6a`
- UTC/KST: `2026-08-25T17:41:59Z` / `2026-08-26T02:41:59+0900`
- 종료값: `0`, 상태: `PASS`
- 전체 출력: 해당 HEAD의 파일 92줄 전체. P11 hard 한도는 파일 600줄, 함수 100줄, diff 3,000줄이다.

### 기계 장부

- 명령: `sed -n '1,$p' docs/sot/principles.yaml`
- HEAD: `d1b1ebed926424878161cd7a04c00c3878039e6a`
- UTC/KST: `2026-08-25T17:42:23Z` / `2026-08-26T02:42:24+0900`
- 종료값: `0`, 상태: `PASS`
- 전체 출력: 해당 HEAD의 파일 356줄 전체. P1~P24, §1-B-1~5, V-1~5 항목을 직접 확인했다.

### 원칙 인수 검사

- 명령: `bash scripts/acceptance-principles-check.sh`
- HEAD: `d1b1ebed926424878161cd7a04c00c3878039e6a`
- UTC/KST: `2026-08-25T17:42:36Z` / `2026-08-26T02:42:48+0900`
- 종료값: `0`, 상태: `PASS`, CHECKED: `34`

```text
VERDICT: PASS
SOT_LOAD: PASS docs/sot/coding-principles.md
LEDGER_LOAD: PASS docs/sot/principles.yaml
MECHANISMS: PASS 34/34 strict-contract-bindings
WIRING: PASS pre-push=1 ci=1
CHECKED: 34
```

→ 현재 정본 두 파일과 pre-push/CI 배선 34건을 원명령이 모두 확인했다. 이 숫자는 WU0-A2 구현의 합격이 아니라 Strict 시작 자격만 증명한다.

### 추가 직접 회수

다음 파일을 d1b1ebe에서 `sed -n '1,$p'`로 직접 읽었다: `mechanism-registry.yaml`, `verification-commands.md`, `ci-required-steps.json`, `verify.yml`, CI checker·acceptance 5개, 기존 WU0-A goal. `git show --format=fuller`로 `0190be9`, `c9206ec`, `d1b1ebe`의 commit 메시지와 diff를 읽었다.

기존 WU 전용 artifact 4개를 전수 검색하고 SHA-256과 전문을 읽었다. 기존 V1 artifact `82c263b2…e2f`, V2 artifact `7ddc3374…aa4`는 d1b1ebe를 PASS했지만 A2의 신규 위협면을 실행하지 않았다.

### Psych 환경 차이

- 첫 AST 진단은 leaf의 `children=nil`을 처리하지 않아 exit `1`; 순회 코드를 바꿔 재실행했다.
- 재실행: Ruby `2.6.10`, Psych `3.1.0`, exit `0`.
- 따옴표 없는 최상위 `on`은 `String "on"`이 아니라 `TrueClass true` key로 읽혔고 `workflow["on"]`은 `nil`이었다.
- 현재 workflow AST는 alias `0`, anchor `0`, merge key `0`이었다.
- WU0-A2는 trigger 내용을 비교하지 않는다. WU0-C는 `workflow["on"]`만 사용하지 말고 AST 또는 YAML 1.1 boolean 차이를 명시적으로 처리해야 한다.

## T 계약 — 입출력·오류·경계

### CLI 입력

```text
bash scripts/verify/check-ci-step-integrity.sh [WORKFLOW] [CONTRACT]
```

- `WORKFLOW` 기본값: `.github/workflows/verify.yml`
- `CONTRACT` 기본값: `docs/sot/ci-required-steps.json`
- 새 dependency 없이 Ruby Psych·JSON·Digest만 사용한다.

### 출력과 종료값

- 정상: `PASS:`와 `CHECKED: N`, exit `0`, `N >= 1`.
- 정책 불일치: `FAIL:`과 `CHECKED: N`, exit `1`.
- 파일 없음·파싱 실패·중복 mapping/object key·anchor/alias/merge·schema 오류·보호 대상 0개: `NOT_RUN:` 또는 fail-closed 오류와 `CHECKED: 0`, exit `2`.
- 검사기의 `PASS:`/`CHECKED:` 진실성은 WU0-B 범위다.

### 기계 계약 schema

- root는 schema version, workflow 경로, workflow context, protected jobs, protected steps의 폐쇄 schema다.
- workflow context는 root `env`와 `defaults`의 부재만 exact로 선언한다.
- 보호 job `verify`는 `runs-on`, `steps`만 허용하고 `runs-on`은 exact `ubuntu-latest`다.
- 각 보호 step은 지정 job·exact name으로 정확히 1개이며 계약의 `allowed_keys`와 실제 key 집합이 같아야 한다.
- 일반 보호 step은 `name`, `run`; `인수 검사 0-5`만 `name`, `run`, `if`이며 if는 exact `github.ref == 'refs/heads/main'`다.
- 미승인 `${{ ... }}`는 exact scalar 비교에서 불일치한다. 평가·공백 정규화·의미 비교를 하지 않는다.

### run 줄 경계

- CRLF만 LF로 바꾸고 각 줄 끝 space/tab만 제거한다.
- YAML block scalar의 표준 terminal newline은 최대 1개만 제거한다.
- 두 번째 이후 terminal blank line, 시작·중간 빈 줄, 순서, 주석, wrapper, shell 문법은 보존한다.

## EARS 인수 기준과 counter-AC

1. When 정상 workflow를 검사할 때 시스템은 exit 0과 보호 대상 CHECKED 수를 내야 한다.
2. When workflow 또는 계약 파일이 없거나 파싱할 수 없을 때 시스템은 exit 2를 내야 한다.
3. When YAML mapping 또는 JSON object에 중복 key가 있을 때 시스템은 의미 Hash 생성 전에 exit 2를 내야 한다.
4. When YAML 어디에든 anchor, alias, `<<` merge key가 있을 때 시스템은 exit 2를 내야 한다.
5. When workflow root에 `env` 또는 `defaults`가 있을 때 시스템은 exit 1을 내야 한다.
6. When 보호 job key 집합 또는 `runs-on`이 계약과 다를 때 시스템은 exit 1을 내야 한다.
7. When 보호 step key 집합·name·run·if가 계약과 다를 때 시스템은 exit 1을 내야 한다.
8. When run 차이가 CRLF 또는 줄 끝 공백뿐일 때 시스템은 통과해야 한다.
9. When run 끝의 표준 newline 뒤에 blank line이 더 있을 때 시스템은 `RUN_MISMATCH` exit 1을 내야 한다.
10. When 비보호 setup, workflow metadata, checkout step의 현재 key 집합만 바뀌지 않았을 때 A2는 통과해야 한다.
11. If 보호 대상이 0개면 시스템은 exit 2를 내야 한다.
12. While 파괴적 반례를 실행할 때 시스템은 원본 세 worktree의 HEAD/status/staged/hash를 바꾸지 않아야 한다.

counter-AC는 사용자가 지정한 신규 23종, 기존 10종, checker no-op, 삭제·중복·rename·if·continue-on-error, missing/parse/zero-target 전부다. 신규 23종은 구현 전 실제 checker 또는 중첩 acceptance를 호출하고 변조 원문, AST key 수·alias/merge, Psych 의미 결과, 시각, exit, 전체 출력을 기록한다.

## 위협 모델과 책임 경계

- WU0-A2: 현재 파일의 보호 job·step exact 정적 문맥과 parser ambiguity만 증명한다.
- WU0-B: 호출 script의 no-op, 가짜 PASS/CHECKED, 출력 위조.
- WU0-C: `on` 자동 실행, checkout exact uses/with, ref/path/sparse/persist-credentials, 선행 step 순서·cardinality, environment/output, workspace provenance.
- WU0-D: checker·contract·workflow·acceptance를 함께 바꾸는 행위자에 대한 외부 trust root.
- WU0-E: workflow/job permissions, 토큰 쓰기, environment approval.

## Harness, R2~R5, 검증

- Gate 0~1: 기준선·SOT·T 계약·RED 원장을 이 문서로 고정한다.
- Gate 2: 새 worktree에서 신규 acceptance만 commit하고 d1b1ebe checker가 빠진 동작 때문에 실패하는지 확인한다.
- Gate 3: contract/checker/docs 최소 변경으로 RED 전부 GREEN. 기존 26개 record를 삭제하거나 기대값을 약화하지 않는다.
- Gate 3.5/R4: `verify.yml` 보호 step → JSON contract → checker → acceptance → mechanism registry/CI step 호출을 정적·실행으로 잇는다.
- Gate 4/R2: 원검증, 독립 mutation, checker 한 줄 고장 사본, 600/601·100/101 경계, diff·상태 불변을 실행한다.
- Gate 5: 로컬 Lore commit까지만 보존한다. 원격 check·보호 규칙을 읽지 않았으므로 SHIP하지 않는다.
- R5: 같은 실패 방식을 세 번 반복하지 않고 실패 원인과 변경한 접근을 기록한다.

## known-gap 재현과 완료 제한

mktemp에서 trigger 제거(WU0-C), checkout ref 과거 SHA(WU0-C), 선행 script 덮어쓰기(WU0-C), 가짜 PASS/CHECKED(WU0-B), workflow·contract·checker pin 동시 약화(WU0-D), `permissions: write-all`(WU0-E)을 다시 실행한다. 모두 남아 있어도 WU0-A2 자체는 PASS 가능하지만 전체 안전성은 `CONDITIONAL`이다.

## 롤백·영향 반경·데이터 안전

- 영향 반경: 로컬 CI 선언 검사, 그 contract, acceptance, SOT 설명만이다. workflow 자체 실행 내용은 바꾸지 않는다.
- 데이터 안전 AC: 모든 mutation은 `mktemp` 복제본에서만 수행하고 시작·종료 원본 상태를 해시로 대조한다.
- 롤백: 신규 RED/GREEN/document commit을 폐기하면 d1b1ebe로 복귀한다. 원본 main과 기존 WU에는 적용할 commit이 없다.

## 결정 카드

> **무엇을** — 보호 job·step의 정확한 실행 문맥과 파서 모호성만 보정한다.
> **왜** — run 글자가 같아도 shell/env/defaults와 중복 key·별칭으로 선언 의미가 달라진다.
> **버린 길** — 모든 workflow 위험과 script hash를 A2 하나에 묶는 방식은 정상 변경 비용과 책임 경계가 과도해 기각한다.
> **대가** — A2 통과 후에도 WU0-B/C/D/E가 끝날 때까지 전체 안전성은 조건부다.
> **되돌리기** — 신규 RED/GREEN commit을 폐기하면 d1b1ebe로 복귀한다.

## 적대 검증 로그

구현·G 완료 뒤 실제 `env -u ANTHROPIC_API_KEY claude -p` V1의 명령·모델·session·시각·exit·전문·artifact SHA-256을 추가한다. 그 뒤 구현 맥락을 상속하지 않은 Codex V2가 V1의 file:line과 명령을 다시 실행하고 양방향 반박을 추가한다.
