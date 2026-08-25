# Repository Data Protection 후속 보강 Goal — 2026-08-25

## 결론

현재 코드는 부분 Git 목록 실패, 여러 줄 SQL, 주석·문자열 오탐, 원문 경로 노출을 막지 못하므로 병합할 수 없습니다. `fdac401…`의 기존 수정은 보존하고 격리 브랜치에서 RED→GREEN과 독립 검증을 다시 수행합니다.

원격 검증이 없는 동안 P23은 `NOT_RUN`이며, `check-docs-sot.sh`의 제한된 PASS는 완료 근거에서 제외합니다. 필수 FAIL/NOT_RUN 또는 fresh humanreview의 `REQUEST_CHANGES`가 하나라도 남으면 완료라고 보고하지 않습니다.

## 판단 근거

부분 목록은 전체 목록이 아니므로 일부 파일을 검사했더라도 검사 자체가 성립하지 않습니다. `all`은 하위 결과를 먼저 모아야 실패와 미실행을 동시에 숨기지 않고 최종 상태를 정확히 만들 수 있습니다. SQL은 판정용 사본에서 주석과 문자열을 지운 뒤 공백을 정규화해야 실제 적재문과 설명용 텍스트를 구분할 수 있습니다.

경로 지문은 비식별화가 아니라 로컬 후보 대조로 복원 가능한 가명입니다. 운영자가 삭제된 과거 경로도 찾을 수 있도록 같은 경로는 항상 같은 12자리 SHA-256 접두어를 사용하고, 여러 후보가 나오면 충돌을 공개합니다.

> **무엇을** — 전용 acceptance와 단일 스캐너 보강, 로컬 역조회 도구, SOT·CI 배선을 한 변경으로 묶습니다.
> **왜** — 기존 `acceptance-hs-a4.sh`가 599줄이라 새 반례를 직접 추가하면 600줄 상한을 넘고 책임도 섞입니다.
> **버린 길** — 기존 검사에 모든 사례를 계속 붙이는 방법은 코드 예산과 검토 가능성을 깨므로 기각했습니다.
> **대가** — CI 스텝과 독립 배선 감시 대상이 하나 늘고, 전체 acceptance 실행 시간이 증가합니다.
> **되돌리기** — 후속 Lore 커밋 하나를 되돌리면 `fdac401…` 상태로 복귀합니다. 개인정보 발견 기록이나 실제 데이터는 생성·저장하지 않습니다.

## 작업 식별과 고정 기준

- 위험등급: L3 — 개인정보, Git 기록, CI/SOT, 3파일 이상 변경.
- 세션: `01a038e5-7e36-7273-9a2b-f186feb314ae`.
- 구현 기준: `fdac401be104bc5d9454401edf0477fb478636dc`.
- 격리 경로: `/private/tmp/valuehire-rdp-20260824.7e3kk1/worktree`.
- 원본 시작 기준: `3094eefa646b102074dfb6401777afe450223e6c`, branch `rescue/main-mixed-20260825T200952`, dirty 41건, status 지문 `804384a21bee0779ffd8c63907bbe559b4d2fe5784835bee2f65119c17541d5d`.
- 공통 조상: `c59bad7b160c473cda5545e76e6fa6bcc711a7ea`.
- 금지: 원본 worktree 수정, 실제 개인정보 사용, push, PR, merge, deploy, 새 의존성, `scan_pii_content` 복제, 기존 판정 기록 수정.
- 중단 조건: 필수 검사 FAIL/NOT_RUN, 원문 개인정보·경로 출력, 원본 dirty 변화, 코드 예산 초과, G/V1/V2 불일치, humanreview 미승인.

## 직접 읽은 정본과 과거 증거

- `docs/sot/coding-principles.md` — P3/P11/P13/P15/P20/P21과 hard 600줄·함수 100줄.
- `docs/sot/principles.yaml` — 34개 Strict 계약 배선 장부 전체.
- `docs/sot/features/engineering/repository-data-protection.yaml` — 현재 기능 계약; safe path 주장을 가명 지문 계약으로 교정 대상.
- `docs/sot/verification-commands.md` — 실제 CI 명령 표와 현재 `check-docs-sot` 허위 설명.
- `docs/engineering/repository-data-protection-alignment-goal-2026-08-24.md` — 기존 zero-target/history 보강과 48사례 증거.
- `docs/engineering/repository-data-protection-v1-prompt-2026-08-24.md` 및 기존 V1/V2 판정 — 과거 증거이며 fresh 검증을 대체하지 않음.
- `.omx/artifacts/claude-claude-v1-claude-skills-humanreview-skill-md-codex-sha-256-a-2026-08-25T12-15-04-412Z.md` — 교정 프롬프트 공격감사와 HR-1~HR-6 재현 근거.
- 결합 프롬프트: `docs/engineering/repository-data-protection-strict-l3-followup-prompt-2026-08-25.md` — 최초 프롬프트 뒤에만 델타를 추가한 실행 계약.

## 현재 상태와 근본 원인

1. `scripts/scan-data-exposure.sh:63-78,256-270`은 프로세스 치환 안의 `git ls-files -z` 종료값을 회수하지 않아 부분 목록을 완전 목록으로 오인합니다.
2. `scripts/scan-data-exposure.sh:280-301`은 하위 출력을 즉시 내보내 `NOT_RUN` 뒤에도 PASS가 남고, `NOT_RUN` 하위의 부분 `CHECKED`를 합산합니다.
3. `scripts/scan-data-exposure.sh:240-246`은 주석·문자열 제거 없이 줄 단위 정규식으로 SQL을 판정합니다.
4. `scripts/scan-data-exposure.sh:57-60,68,72,76,108-112,163,175,251-252,263`은 원문 또는 shell-escaped 원문 경로를 출력합니다.
5. `scripts/acceptance-hs-a4.sh:61-76`과 `scripts/acceptance-semantic-mutations.sh:53-64`도 Git 대상 수집 종료값과 정확한 실제 대상을 증명하지 못합니다.
6. `docs/sot/verification-commands.md`의 `check-docs-sot` 절은 격리 브랜치의 71줄 검사기가 구현하지 않은 catalog·surface coverage를 주장합니다.

## EARS 합격 조건과 기계 판정

### AC-1 — 부분 Git 목록 실패

When `git ls-files -z`가 한 경로를 출력한 뒤 실패하면, tracked와 pii는 PASS 0줄, `NOT_RUN` 1줄 이상, `CHECKED: 0`, exit 2를 반환해야 합니다. When 같은 실패가 all에서 발생하면 history가 정상이어도 최종 PASS는 0줄이고 exit 2여야 합니다.

검증 명령: `bash scripts/acceptance-repository-data-protection.sh`; 기대: partial tracked/pii/all 사례 모두 PASS 판정, 원명령의 정확한 exit/PASS/FAIL/NOT_RUN/CHECKED 단언.

### AC-2 — all 집계

When 세 하위 검사 중 하나라도 `NOT_RUN`이면, all은 세 출력을 버퍼링하고 다른 하위의 FAIL은 보존하되 모든 PASS를 억제하며, `NOT_RUN` 하위는 0으로 세고 정상 완료 하위의 실제 `CHECKED`만 합산해 exit 2를 반환해야 합니다. When 세 하위가 정상 통과하면 PASS는 정확히 3줄이고 CHECKED는 세 하위 합과 정확히 같아야 합니다.

검증 명령: 전용 acceptance의 세 수치 고정 집계 사례; 기대: 각 사례의 exit와 네 출력 개수 및 CHECKED가 정확히 일치.

### AC-3 — SQL 실제 적재와 정상 설명 구분

When `INSERT`, `INTO`, `VALUES`가 서로 다른 줄에 있거나 주석이 토큰 사이에 있으면, 현재 pii·삭제 history·all은 개인정보 적재 SQL을 exit 1로 차단해야 합니다. When `COPY ... FROM` 적재문이 여러 줄이면 같은 세 모드가 차단해야 합니다. When INSERT/VALUES가 주석 또는 작은따옴표 문자열 안에만 있거나 `copy`가 schema 컬럼 식별자로만 있으면, 같은 판정 함수는 정상 SQL을 exit 0으로 통과시켜야 합니다.

검증 명령: 전용 acceptance의 current/history/all 다중행 INSERT·COPY FROM, comment+newline, comment-only, string-only, COPY-identifier schema 사례; 기대: 33개 사례, 위반 exit 1, 정상 exit 0, `scan_pii_content` 정의 1개 및 current/history 직접 호출 유지.

### AC-4 — 원문 경로 비출력과 역조회

When 금지경로, 크기초과, PII 위반, 경로 관련 읽기 실패를 출력하면, scanner의 stdout/stderr에는 원문 경로가 0건이어야 하고 `path [0-9a-f]{12}`만 있어야 합니다. When 운영자가 그 지문을 로컬 역조회 도구에 넣으면, 현재 및 삭제된 history 경로 후보를 찾고 2개 이상이면 충돌과 모든 후보를 표시해야 합니다.

지문 계약: `printf '%s' "$path" | shasum -a 256` 전체값의 앞 12자리 소문자 16진수. 저장소·브랜치·current/history와 무관하게 같은 경로는 같은 값이며 salt·난수·시각을 사용하지 않습니다.

검증 명령: 전용 acceptance의 네 출력 유형 비출력, 결정론, 삭제 history 역조회, 강제 충돌 표현 사례; 기대: canary 경로 원문 grep 0건, 정확한 12자리, 역조회 후보 수 일치.

### AC-5 — acceptance 자신의 대상 수집

When `acceptance-hs-a4.sh` 또는 `acceptance-semantic-mutations.sh`가 Git 대상 목록의 일부만 받은 뒤 Git 실패를 만나면, 각 검사는 PASS를 내지 않고 exit 2 또는 1로 닫혀야 합니다. While 대상 수를 검증하면, Git이 완전히 반환한 실제 대상 수와 acceptance가 처리한 대상 수를 정확히 비교해야 하며 하한 비교를 사용하지 않아야 합니다.

검증 명령: 전용 acceptance의 두 검사기 shim mutation 및 semantic 원명령; 기대: 부분 목록 mutant 둘 다 거부, semantic `CHECKED` 계약값과 실제 대상 수 일치.

### AC-6 — 신규 검사 단일 배선과 독립 삭제 차단

Where 전용 repository-data-protection acceptance가 존재하면, CI는 `run-acceptance.sh`를 통해 정확히 한 번 실행하고, 검증 SOT 표는 같은 스텝을 한 번 등록하며, 기존 hs-a4 acceptance는 실행 줄 삭제 사본을 실패시키고 신규 파일을 코드 예산 대상으로 포함해야 합니다.

검증 명령: `bash scripts/acceptance-hs-a4.sh`, workflow 호출 삭제 mutation, `rg` 정확 건수; 기대: 정상 exit 0, 삭제 사본 exit 1, 각 등록 건수 1.

### AC-7 — 코드 경계와 SOT 진실성

While 직접 작성 shell 파일을 검증하면, 각 파일은 600줄 이하이고 각 함수는 100줄 이하이며 같은 판정기는 합성 600/100줄을 통과시키고 601/101줄을 차단해야 합니다. Where `check-docs-sot.sh`가 catalog·surface 검사를 구현하지 않으면, verification SOT는 그 검사를 주장하지 않고 그 명령의 PASS를 완료 근거로 사용하지 않아야 합니다.

검증 명령: hs-a4 code budget, `wc -l`, `rg 'catalog|surface_coverage' scripts/check-docs-sot.sh docs/sot/verification-commands.md`; 기대: 코드 경계 PASS, 문서는 실제 71줄 검사 범위만 기술.

### AC-8 — 원본 보존과 데이터 안전

While 모든 파괴적 반례를 실행하면, 합성 canary만 `mktemp` 아래에서 사용하고 Git 환경변수를 제거하며, 종료 후 원본 worktree의 HEAD/branch/dirty 수/status 지문과 SOT 지문은 시작 기준과 정확히 같아야 합니다. scanner·goal·판정서·CI 로그에 개인정보 원문과 원문 경로를 저장하지 않아야 합니다.

검증 명령: 시작/종료 원본 read-only 대조와 격리 diff 검사; 기대: 41건 및 지문 동일.

## counter-AC 원장

1. 부분 `git ls-files`가 안전 파일 하나만 내고 실패했는데 그 부분 목록으로 PASS.
2. tracked가 NOT_RUN인데 history PASS가 all 최종 출력에 남음.
3. history FAIL 뒤 pii NOT_RUN이 exit 2가 되지만 FAIL 줄을 버림.
4. NOT_RUN 하위가 처리한 일부 수를 all CHECKED에 더함.
5. 세 정상 하위의 CHECKED를 상수로 위조함.
6. 다중행 INSERT는 잡지만 주석 속 INSERT를 오탐함.
7. 주석을 지우면서 토큰을 붙여 다른 식별자를 INSERT INTO로 오인함.
8. 문자열 내용을 지우지 않아 예제 SQL을 실제 적재로 오인함.
9. current와 history가 SQL 판정 함수를 복제해 한쪽만 고쳐짐.
10. PII 본문은 가렸지만 경로에 든 이름·이메일을 출력함.
11. PII FAIL만 지문화하고 금지경로·크기·NOT_RUN은 원문 경로를 출력함.
12. 지문이 실행마다 달라 삭제 history 경로를 역조회하지 못함.
13. 12자리 충돌 후보 중 첫 경로만 조용히 선택함.
14. 신규 acceptance 파일은 있으나 CI 호출 또는 SOT 표 등록이 없음.
15. 신규 acceptance 자신의 CI 호출 삭제를 자기 자신만 검사해 삭제와 함께 침묵함.
16. semantic target 수를 `>=5`로만 검사해 부분 목록 누락을 놓침.
17. 원본 dirty worktree의 미커밋 475줄 검사기를 격리 증거로 사용함.
18. `check-docs-sot.sh` exit 0을 catalog/surface 검증 PASS로 과장함.
19. 새 파일이 hs-a4 코드 예산 목록에서 빠져 601줄이 통과함.
20. acceptance 호출 또는 SQL/ls-files/path 방어를 제거해도 검사가 초록임.

## 입출력·오류·경계 계약

```text
scan-data-exposure <tracked|history|pii|all>
stdout := zero or more FAIL/NOT_RUN/PASS metadata lines + exactly one CHECKED line
stderr := empty
exit := 0 PASS | 1 FAIL | 2 NOT_RUN
single NOT_RUN := PASS lines 0, CHECKED 0, exit 2
all NOT_RUN := PASS lines 0, preserve FAIL lines, CHECKED=sum(completed child counts), exit 2
all complete := child output concatenation, CHECKED=sum(all child counts), exit=max semantic state
path fingerprint := lowercase hex SHA-256 prefix length 12
PII decision := full-file PII word count >=2 AND sanitized SQL/row data shape
```

```text
resolve-data-path-fingerprint <12hex>
input error := exit 2, no repository mutation
no match := exit 1, MATCHES: 0
one match := exit 0, one reversible shell-escaped local path, MATCHES: 1
collision := exit 1, all matching reversible shell-escaped paths, COLLISION: N
enumeration failure := exit 2, partial candidates discarded
```

경계: 빈 저장소, 한 대상, NUL 경로, 탭·따옴표·줄바꿈 경로, 1MiB/1MiB+1, PII 1종/2종, 600/601 파일, 100/101 함수, 0/1/2+ fingerprint 후보, 부분 Git 출력 후 실패를 포함합니다. 동시성 상태는 없고 재시도는 호출자가 원인을 고친 뒤 같은 원명령을 다시 실행합니다.

## Harness 게이트와 검증 장부

| 게이트 | 계약 | 현재 상태 |
|---|---|---|
| 0 | 기준 SHA, 원본 dirty 지문, 과거 증거, RED 원장 | PASS |
| 1 | EARS AC, counter-AC, I/O·오류·경계, 영향·롤백·데이터 안전 | PASS |
| 2 | 격리 worktree에서 새 acceptance RED | PASS |
| 3 | 최소 구현으로 RED→GREEN, 테스트 약화 없음 | PASS |
| 3.5 | workflow→runner→acceptance→scanner 및 역조회 배선 | PASS |
| 4 | 원명령·수치·mutation·전체 all fresh 검증 | 진행 — COPY 보강 뒤 재실행 필요 |
| 5 | Lore 로컬 커밋, clean SHA, V1/V2/humanreview, P23 공개 | REQUEST_CHANGES — V1·P23·humanreview 미충족 |
| 6 | push/PR/merge/배포 | 금지 |

### 2026-08-25 21:31:23 KST — Strict 원칙 직접 로드

```text
COMMAND: bash scripts/acceptance-principles-check.sh
PWD: /private/tmp/valuehire-rdp-20260824.7e3kk1/worktree
HEAD: fdac401be104bc5d9454401edf0477fb478636dc
SESSION: 01a038e5-7e36-7273-9a2b-f186feb314ae
VERDICT: PASS
SOT_LOAD: PASS docs/sot/coding-principles.md
LEDGER_LOAD: PASS docs/sot/principles.yaml
MECHANISMS: PASS 34/34 strict-contract-bindings
WIRING: PASS pre-push=1 ci=1
CHECKED: 34
EXIT: 0
```

→ 정본 두 파일을 직접 읽고 검사했으며 Strict 계약 배선 34개가 성립했습니다. 이는 repository-data-protection 구현 완료 증거가 아닙니다.

## R2~R5와 독립 검증 계획

- R2: SQL sanitizer, Git 목록 실패 처리, 경로 지문, 신규 CI 호출을 각각 제거한 고장 사본이 acceptance exit 1인지 실행합니다. 600/601·100/101 경계도 같은 판정기로 확인합니다.
- R3: 이 문서의 주장은 격리 worktree 코드와 원명령 출력에만 귀속하고, 원본 dirty 파일은 비교 지문 외 근거로 쓰지 않습니다.
- R4: `.github/workflows/verify.yml` → `scripts/verify/run-acceptance.sh` → 전용 acceptance → `scripts/scan-data-exposure.sh`/역조회 도구의 호출을 정적·실행으로 증명합니다.
- R5: 기존 `all` 30분 정체와 Claude credit 실패를 반복하지 않습니다. 하위 명령으로 원인을 좁힌 뒤 같은 원명령을 충분한 제한으로 fresh 재실행하고, V1 실패 시 한 번 복구 후 재시도합니다.
- V1: `env -u ANTHROPIC_API_KEY claude -p`로 clean 최종 SHA를 읽기 전용 공격하고 §8-7 원문을 보존합니다.
- V2: 새 Codex verifier가 V1의 모든 근거를 재현하고 PASS 누락·FAIL 과장을 양방향 공격합니다.
- humanreview: 요구·diff·실행 증거·mutation을 fresh 공격해 `APPROVE`인지 확인합니다.

## 영향 반경, 롤백, 데이터 안전

- 직접 영향: scanner 네 모드, 현재/과거 SQL 판정, 로그 메타데이터, local remediation, data acceptance, semantic target collection, CI/SOT 인벤토리.
- 간접 영향: pre-push acceptance glob, CI 실행 시간, 운영자의 위반 경로 찾기 절차.
- 롤백: 후속 Lore 커밋 하나를 revert해 `fdac401…`로 복귀. 실제 유출이 발견된 경우에는 기록 삭제·자격증명 회전 전 증거를 지우지 않습니다.
- 데이터 안전: 합성 canary만 임시 저장소에서 사용하고 실제 후보자 파일을 열지 않습니다. 출력 검사에는 canary 원문과 경로가 없는지만 grep으로 확인하며, goal에는 원문을 복사하지 않습니다.
- 잔여 `REQUEST_CHANGES`: `check-docs-sot.sh`는 여전히 CI에 연결되지 않은 제한된 수동 검사입니다. 이번 범위에서는 전역 catalog/surface 검증기를 구현하지 않고 허위 SOT만 제거하므로, 그 명령의 PASS는 완료 근거에서 제외합니다.
- P23: 원격 브랜치/CI가 없으면 `NOT_RUN`. 로컬 검증으로 대체하지 않습니다.

## 적대 검증 로그

RED, GREEN, 원명령, mutation, V1, V2, humanreview의 시각·PWD·HEAD·exit·CHECKED·전체 출력을 아래에 실행 순서대로 추가합니다.

### 2026-08-25 21:39:27 KST — fresh 수동 RED

```text
RED multiline-current: exit=0 PASS=1 FAIL=0 NOT_RUN=0 CHECKED=1
RED multiline-history: exit=0 PASS=1 FAIL=0 NOT_RUN=0 CHECKED=2
RED comment-only-control: exit=1 PASS=0 FAIL=1 NOT_RUN=0 CHECKED=2
RED partial-ls-files-tracked: exit=0 PASS=1 FAIL=0 NOT_RUN=0 CHECKED=1
PWD: /var/folders/.../repo
BASE HEAD: fdac401be104bc5d9454401edf0477fb478636dc
HARNESS EXIT: 0 (재현 결과 네 건이 계약과 반대임을 수치로 확인)
```

→ 다중행 현재·삭제 history SQL과 부분 Git 목록 실패가 거짓 PASS였고, 주석에만 적재문이 있는 정상 SQL은 거짓 FAIL이었습니다. fixture 원문과 원문 경로는 장부에 복사하지 않았고 임시 저장소는 종료 시 제거했습니다.

### 2026-08-25 23:24:18 KST — COPY 식별자 오탐 RED

```text
COMMAND: bash scripts/acceptance-repository-data-protection.sh
PWD: /private/tmp/valuehire-rdp-20260824.7e3kk1/worktree
HEAD: 3136354d174290f87a88489bcb4ea323af815c47
PASS: multiline COPY FROM SQL load
FAIL: COPY identifier schema control — got exit=1 PASS=0 FAIL=1 NOT_RUN=0 CHECKED=1
CHECKED: 31
VERDICT: FAIL
EXIT: 1
```

→ `copy`가 컬럼 이름으로만 있는 정상 schema SQL을 적재문으로 오인하는 새 반례가 RED로 재현됐습니다. 실제 `COPY ... FROM` 여러 줄 적재문은 기존 코드에서도 차단됐으므로, 누락이 아니라 bare `copy` 오탐이 원인이었습니다.

### 2026-08-25 23:24:49 KST — COPY FROM 계약 GREEN

```text
COMMAND: bash scripts/acceptance-repository-data-protection.sh
PWD: /private/tmp/valuehire-rdp-20260824.7e3kk1/worktree
HEAD: 3136354d174290f87a88489bcb4ea323af815c47 + uncommitted RED/GREEN patch
PASS: multiline COPY FROM SQL load
PASS: COPY identifier schema control
CHECKED: 31
VERDICT: PASS
EXIT: 0
COMMAND: shellcheck scripts/scan-data-exposure.sh scripts/acceptance-repository-data-protection.sh
EXIT: 0
COMMAND: bash -n scripts/scan-data-exposure.sh scripts/acceptance-repository-data-protection.sh
EXIT: 0
```

→ SQL 판정은 이제 `COPY` 뒤에 실제 `FROM` 절이 있는 경우만 적재문으로 인정합니다. 이어서 current·삭제 history·all의 여러 줄 COPY 사례를 추가해 전용 acceptance 계약값을 33으로 올렸으며, 최종 커밋 SHA에서 전체 게이트를 다시 실행합니다.

### 2026-08-25 23:25:05 KST — canonical Claude V1 복구 시도

```text
COMMAND: omx ask claude '<final SHA 3136354... read-only adversarial prompt>'
PWD: /private/tmp/valuehire-rdp-20260824.7e3kk1/worktree
PROVIDER: claude
EXIT: 1
OUTPUT: Credit balance is too low
ARTIFACT: .omx/artifacts/claude-you-are-claude-v1-an-independent-adversarial-reviewer-work-r-2026-08-25T14-25-05-039Z.md
STATUS: NOT_RUN
```

→ 정식 OMX Claude 경로도 검토 본문을 만들기 전에 외부 크레딧에서 종료했습니다. Codex 검증으로 대체하지 않으며, 최종 구현 SHA에서 `ANTHROPIC_API_KEY`를 제거한 인증 경로로 한 번 더 복구 시도합니다.
