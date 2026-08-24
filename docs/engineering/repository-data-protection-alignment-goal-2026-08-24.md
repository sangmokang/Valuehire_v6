# 저장소 데이터 보호 보장 일치 Goal — 2026-08-24

## 결론

VERDICT: FAIL

현재 검사는 파일이 하나도 없어도 합격하며, 커밋 후 삭제된 후보자 개인정보도 놓친다. 두 결함을 코드·시험·정본 문서에서 함께 닫고 모든 독립 검증이 합격하기 전에는 완료로 판정하지 않는다.

사용자가 결정할 추가 사항은 없다. 승인 범위는 격리 작업공간의 PLAN → BUILD → AUDIT → CHECKPOINT와 Lore 형식 로컬 커밋까지이며, push·PR 생성·병합·배포는 금지한다.

## 판단 근거

`verify.sh`는 Git이 돌려준 대상 수를 세지 않고 검색 결과가 비면 곧바로 합격한다. `scan-data-exposure.sh history`는 과거 blob의 크기와 경로만 보고 개인정보 내용 판정 함수는 현재 추적 파일에만 적용한다.

이 상태를 두면 보호 장치의 초록불이 실제 검사를 뜻하지 않는다. 빈 저장소와 삭제된 과거 개인정보라는 두 공격 fixture가 현재 모두 종료값 0을 냈으므로 Finding 상태는 `REPRODUCED`다.

> **무엇을** — `verify.sh`는 대상 수와 읽기 성공을 필수 조건으로 만들고, history는 현재 개인정보 판정과 같은 함수로 과거 CSV·TSV·SQL blob 내용까지 검사한다.
> **왜** — 정본은 이미 0건 통과 금지와 도달 가능한 기록의 개인정보 검사를 보장하지만 구현이 그 수준에 못 미친다.
> **버린 길** — 문서를 약한 구현에 맞추는 길과 현재/과거 개인정보 판정기를 두 벌로 복제하는 길은 각각 정본 목적 훼손과 규칙 드리프트 때문에 기각한다.
> **대가** — 과거 blob을 실제로 열므로 history 실행 시간이 늘고, 검사 건수·안전한 지문 메타데이터를 관리해야 한다.
> **되돌리기** — 이 작업의 범위별 로컬 커밋만 역순으로 되돌린다. 탐지된 실제 유출 데이터나 기록은 이 작업에서 삭제·재작성하지 않는다.

## 작업 식별과 고정 기준

- 위험 등급: Strict L3 — 보안·개인정보·공유 검사기·정본 변경.
- 세션: `01a03113-6b08-7841-bb48-a1b6888ea67d`.
- 사용자 지정 시작 SHA: `c59bad7b160c473cda5545e76e6fa6bcc711a7ea`.
- 원본 작업트리 관측 HEAD: `3094eefa646b102074dfb6401777afe450223e6c`.
- 차이: 사용자 지정 SHA는 원본 HEAD의 조상이며, 사이 변경은 finding-runner 범위 6파일 777줄이다. 이 범위는 건드리지 않는다.
- 격리 작업공간: `/tmp/valuehire-rdp-20260824.7e3kk1/worktree`.
- 격리 브랜치: `task/repository-data-protection-20260824`.
- 원본 `docs/sot/verification-commands.md` SHA-256: `d226898f717649c2c0be5790e09e7f716af118dcbb4ccc0eaee9f13632f99911`.
- 원본 `docs/sot/features/engineering/repository-data-protection.yaml` SHA-256: `0c785bfe8981f82efa2059b5e36759c5b36dda08d3d12f119ee8aa044f3dcb3c`.
- 종료 조건: 모든 필수 명령, R2, G/V1/V2가 PASS이고 원본 status와 위 두 SHA-256이 시작값과 같아야 한다.

## 읽은 정본과 과거 증거

- 저장소 최상위 `AGENTS.md`, `CLAUDE.md`: 둘 다 현재 작업트리에 없음. 사용자가 이번 요청에 제공한 AGENTS 계약과 Strict 스킬이 적용된다.
- `docs/sot/coding-principles.md`: 전체 74줄 직접 읽음. P3, P11, P13, P15, P20, P21, P22가 직접 관련된다. 직접 작성 코드 hard limit은 파일 600줄, 함수 100줄이다.
- `docs/sot/principles.yaml`: 전체 345줄 직접 읽음.
- `docs/sot/features/engineering/repository-data-protection.yaml`: 원본 dirty 작업트리의 미추적 정본 192줄 전체 직접 읽음.
- `docs/sot/hook-contracts.md`: 전체 76줄 직접 읽음.
- `docs/sot/verification-commands.md`: 원본 dirty 작업트리의 수정 정본 95줄 전체 직접 읽음.
- 관련 기록: `480655c`는 D1/D2/D4 RED를 추가했고 `e312a46`은 현재 공용 판정기를 만들었다. 현재 결함은 당시 history가 크기·경로로만 제한되고 PII는 추적 파일만 본 설계 경계다.
- 관련 기존 goal: `docs/engineering/gate0-unreachable-secret-scan-goal-2026-08-17.md`는 비밀 리터럴의 reachable/unreachable Git 객체 검사를 다루며, 후보자 개인정보 history 내용 판정은 범위 밖이다.
- 무시된 증거 위치 `private-reviews/`, `artifacts/`, `.harness/`, `.omx/`를 경로 검색했으며 이 기능의 별도 활성 goal은 발견하지 못했다.

## 현재 상태와 근본 원인

### Finding RDP-F1 — zero-target 가짜 합격

- 상태: `REPRODUCED`.
- 현재 코드: `verify.sh:57-73`은 목록을 검색하지만 대상을 세지 않는다. `verify.sh:91-93`은 누출 문자열과 도구 오류가 없으면 대상 0개여도 PASS/0이다.
- 근본 원인: 검사 성립 조건인 Git 목록 읽기 성공과 양수 대상 수가 판정 상태에 포함되지 않았다. 출력 계약에도 `CHECKED`가 없다.

### Finding RDP-F2 — 삭제된 과거 PII 미검사

- 상태: `REPRODUCED`.
- 현재 코드: `scripts/scan-data-exposure.sh:79-110`의 history는 blob 크기와 금지 경로만 검사한다. `scripts/scan-data-exposure.sh:130-161`의 `scan_pii`는 `git ls-files`와 인덱스 blob만 읽는다.
- 근본 원인: 개인정보 판정이 내용 스트림에 대한 공용 함수가 아니라 현재 파일 순회 안에 묶여 있어 history 호출 경로가 재사용할 수 없다.

## EARS 합격 조건과 기계 판정

### AC-1 — 빈 검사 차단

When 비어 있는 임시 Git 저장소에서 `verify.sh`를 실행하면, 시스템은 PASS를 출력하지 않고 `NOT_RUN`, `CHECKED: 0`, exit 2를 반환해야 한다.

- 검증: 수정된 secret acceptance 원명령의 zero-target 사례와 독립 임시 저장소 실행.
- 기대: stdout/stderr 합쳐 PASS 0줄, `NOT_RUN` 1줄 이상, `CHECKED: 0`, 종료값 2.

### AC-2 — 정상 대조군

When 안전한 파일 하나가 추적된 저장소에서 `verify.sh`를 실행하면, 시스템은 `PASS`, 양수인 `CHECKED`, exit 0을 반환해야 한다.

- 검증: acceptance의 tracked/index 정상 fixture와 저장소 루트 `bash verify.sh`.
- 기대: `PASS`, `CHECKED: N`에서 N > 0, 종료값 0.

### AC-3 — 과거 PII 탐지

When 후보자 이름·이메일 컬럼과 실제 데이터 행이 있는 CSV 또는 개인정보 적재 SQL을 커밋한 뒤 삭제 커밋을 만들면, `scan-data-exposure.sh history`와 `all`은 과거 blob을 탐지하고 exit 1을 반환해야 한다.

- 검증: 수정된 data acceptance 원명령의 CSV·TSV·SQL 삭제 이력 fixture.
- 기대: 각 history/all 종료값 1, 경로·blob 지문·컬럼 종류 수만 출력.

### AC-4 — 정상 과거 기록 통과

When 정상 지표 CSV와 스키마 정의만 있는 SQL이 과거 기록에 존재하면, 시스템은 이를 개인정보 데이터로 오탐하지 않아야 한다.

- 검증: 정상 지표 CSV, 스키마-only SQL을 커밋 후 삭제한 history fixture.
- 기대: 종료값 0, 양수 `CHECKED`.

### AC-5 — 개인정보 비출력

When 과거 PII 위반을 탐지하면, stdout과 stderr 어디에도 fixture의 실제 이름·이메일·전화번호가 출력되지 않아야 한다.

- 검증: 이름·이메일·전화 canary 각각에 대해 stdout/stderr 음성 대조.
- 기대: 원문 hit 0건; 위반 메타데이터만 존재.

### AC-6 — SOT 일치

When 구현과 테스트가 완료되면, `repository-data-protection.yaml`의 목적, 오류, 불변조건, 검증 명령은 실제 검사 범위 및 종료값과 정확히 일치해야 한다.

- 검증: `bash scripts/check-docs-sot.sh`, 기능 verification 원명령, diff 수동 대조.
- 기대: 문서가 zero-target, Git read failure, history PII, 안전 출력, 양수 checked를 명시.

### AC-7 — 코드 예산 경계

When 같은 파일 판정기로 600줄 정상 사본과 601줄 고장 사본을 검사하면, 시스템은 600줄을 통과시키고 601줄을 차단해야 한다.

- 검증: 저장소의 기존 파일 크기 판정기 원명령과 합성 600/601 fixture.
- 기대: 600 통과, 601 실패, 검사 대상 양수.

### AC-8 — 데이터 안전

When 모든 RED·GREEN·뮤테이션 fixture를 실행하면, 시스템은 실제 후보자 데이터나 실제 자격증명을 생성·읽기·출력하지 않고 원본 저장소 상태와 미커밋 정본 해시를 바꾸지 않아야 한다.

- 검증: 합성 canary만 사용, 시작/종료 원본 `git status --porcelain=v1 --untracked-files=all` 및 SHA-256 비교.
- 기대: 정확히 동일.

## counter-AC 원장

다음 중 하나라도 재현 가능하면 FAIL이다.

1. 검사 대상 0개인데 `PASS` 또는 exit 0.
2. `CHECKED`가 없거나 0인데 PASS.
3. 현재 추적 파일의 PII만 잡고 삭제된 과거 PII는 통과.
4. history가 크기와 경로만 검사하고 내용은 검사하지 않음.
5. 검사기가 자기 자신이나 특정 과거 blob을 임의 제외.
6. 실제 개인정보 값이 stdout/stderr에 노출.
7. CSV만 잡고 SQL 또는 TSV는 통과.
8. 정상 지표 CSV나 스키마 정의 SQL을 차단.
9. PII 판정 로직이 현재/과거용 두 벌로 갈라짐.
10. 테스트 대상을 0개로 만들거나 검사 호출을 제거해도 테스트가 통과.
11. 코드를 고치지 않고 SOT 문구만 낮춰서 통과.
12. `CHECKED`를 상수 1로 위조해도 acceptance가 통과.
13. Git 목록·blob 읽기 실패가 깨끗한 결과로 접힘.
14. 중복 blob 또는 여러 경로를 거친 같은 blob 때문에 판정이나 건수가 불안정해짐.

## 입출력·오류·경계 계약

### `verify.sh`

```text
Input = {
  scan_source: "worktree" | "index" = "worktree",
  patterns: SECRET_PATTERNS_FILE | [.secret-patterns.default, .secret-patterns],
  repository: readable Git worktree/index
}
Output = ordered safe text lines ending in exactly one CHECKED count
Exit = 0 PASS | 1 FAIL | 2 NOT_RUN
```

- 기본 모드는 현재 추적 파일의 작업트리 내용, `VERIFY_SCAN_SOURCE=index`는 같은 추적 경로의 인덱스 blob을 읽는다.
- 유효 패턴 0개, 패턴 파일 오류, Git 목록/내용 읽기 실패, 대상 0개는 `NOT_RUN`, `CHECKED: 0` 또는 실제 완료 전 건수, exit 2다.
- 대상 1개 이상·도구 오류 없음·위반 없음은 `PASS`, `CHECKED: N`(N > 0), exit 0이다.
- 비밀 또는 `.env` 위반은 `FAIL`, 안전한 경로만 출력, exit 1이다.
- 패턴에 매칭된 실제 값과 파일 본문은 어느 출력에도 내보내지 않는다.
- 알 수 없는 `VERIFY_SCAN_SOURCE`는 `NOT_RUN`, exit 2다.

### `scan-data-exposure.sh history`

```text
Input = reachable Git objects from refs and reflogs
PII decision = classify_pii_content(path, blob_content) -> {kind, pii_column_kinds, has_data}
Output violation = {safe_path, blob_fingerprint, pii_column_kind_count, data_shape}
Exit = 0 PASS | 1 FAIL | 2 NOT_RUN
```

- 도달 가능한 고유 blob을 한 개 이상 실제로 열고 크기·금지 경로·PII 내용을 검사한다.
- PII 판정 함수는 tracked `pii`와 history가 공유한다. 파일 경로/내용 획득만 호출자별로 다르다.
- CSV·TSV는 헤더의 개인정보 컬럼 종류 2종 이상과 실제 데이터 행 1개 이상이 함께 있을 때 차단한다.
- SQL은 개인정보 컬럼 종류 2종 이상과 INSERT/VALUES/COPY 적재 형태가 함께 있을 때 차단한다. CREATE TABLE만 있는 스키마는 통과한다.
- Git 열거 실패, 객체형/크기/blob 본문 읽기 실패, 검사 blob 0개는 `NOT_RUN`, exit 2다.
- 출력은 안전한 경로, blob 지문의 축약형 또는 전체 SHA, 컬럼 종류 수, 데이터 형태만 포함한다. 본문·실제 값은 출력하지 않는다.
- 동일 blob은 내용 판정을 한 번만 수행하되, 금지 경로는 도달 가능한 경로별로 놓치지 않는다.

### 공통 경계

- 빈 파일: PII 데이터로 차단하지 않지만 검사 blob 수에는 포함한다.
- 최소: 성공하려면 verify 대상 >= 1, history blob >= 1.
- 최대: 1,048,576바이트 초과 blob은 기존 계약대로 FAIL이며 PII 판정을 생략해도 된다. 읽기 실패는 NOT_RUN이다.
- 파일명: NUL 구분을 유지하고 공백·개행·선행 하이픈을 안전하게 처리한다.
- 동시성/재시도: 읽기 전용 단일 프로세스이며 자동 재시도 없음. Git 상태가 실행 중 바뀌는 동시 수정은 보장하지 않으며 CI의 고정 SHA에서 권위를 갖는다.
- 권한: 저장소와 Git 객체 DB 읽기 권한이 없으면 NOT_RUN. 스캐너는 Git 기록을 수정하지 않는다.

## Harness 게이트 계획

| 게이트 | 계약 | 상태 |
|---|---|---|
| 0 | 규칙·SOT·기록·현재 RED·원본 상태 회수 | 진행 중 |
| 1 | EARS AC, counter-AC, I/O·오류·경계, 롤백·영향·데이터 안전 고정 | PASS |
| 2 | `c59bad7b…` 격리 worktree, 동작 누락 때문에 실패하는 acceptance RED | 대기 |
| 3 | 테스트 기대값 불변 상태의 최소 GREEN 구현 | 대기 |
| 3.5 | 훅/CI → 공용 검사기 → 공용 PII 판정 호출 경로 실행 증명 | 대기 |
| 4 | 필수 원명령·건수·뮤테이션·600/601·라이브 합성 이력 PASS | 대기 |
| 5 | 범위별 Lore 로컬 커밋, 원본 보존 재확인 | 대기 |

## R2 적대검증 계획

1. zero-target 차단 분기 제거 → acceptance FAIL.
2. history의 공용 PII 호출 제거 → CSV·TSV·SQL 삭제 이력 acceptance FAIL.
3. `CHECKED`를 고정 1로 위조 → 실제 대상 수 대조 acceptance FAIL.
4. 스캐너에 PII 본문 출력 주입 → 비출력 acceptance FAIL.
5. 테스트 호출 자체 제거/빈 fixture → 정확한 사례 수와 양수 대상 계약 때문에 FAIL.
6. 600줄 정상/601줄 고장 fixture → 동일 판정기에서 통과/차단.

## 영향 반경

- 직접: `verify.sh`, `scripts/scan-data-exposure.sh`, 기존 secret/data acceptance, 기능 정본 YAML, 검증 명령 정본, 본 goal/판정 기록.
- 배선: `hooks/pre-commit`은 index verify를 호출하고 `.github/workflows/verify.yml`은 verify/all을 호출한다. 기존 호출이 계약을 충족하면 변경하지 않는다.
- 간접: pre-commit, pre-push, CI의 실행 시간과 실패 메시지.
- 비범위: checkpoint/finding 도구·시험·문서, 기존 feature-sot-v1/v2 감사 기록, 제품 기능, 실제 후보자 데이터, Git history rewrite, 원격 작업.

## 롤백과 데이터 안전

- 롤백 단위: 테스트/RED 계약 커밋, 구현/SOT 커밋, 감사 증거 커밋을 역순으로 되돌린다.
- 원본 dirty 작업트리는 읽기·해시 계산 외 수정하지 않는다.
- 원본에서 가져온 두 SOT 파일은 SHA-256을 기록하고 exact copy로 격리한 뒤, 이번 변경분만 커밋한다.
- fixture는 `/tmp` 아래의 독립 Git 저장소에 합성 데이터만 만든다. 실제 개인정보·자격증명·`.secret-patterns` 실제 리터럴은 읽거나 출력하지 않는다.
- history rewrite, `git gc`, reflog 삭제, branch 강제 갱신은 하지 않는다.
- 탐지된 실제 유출이 있으면 본 작업에서 삭제하지 않고 FAIL로 공개한다.

## 검증 장부

### 2026-08-24 09:03:56 KST — 원칙 직접 검사

```text
TIMESTAMP_KST: 2026-08-24 09:03:56 KST
WORKDIR: /Users/kangsangmo/Desktop/valuehire_v6
HEAD: 3094eefa646b102074dfb6401777afe450223e6c
SESSION: 01a03113-6b08-7841-bb48-a1b6888ea67d
VERDICT: PASS
SOT_LOAD: PASS docs/sot/coding-principles.md
LEDGER_LOAD: PASS docs/sot/principles.yaml
MECHANISMS: PASS 34/34 strict-contract-bindings
WIRING: PASS pre-push=1 ci=1
CHECKED: 34
EXIT: 0
```

→ 현재 원칙 정본 2개가 직접 로드됐고 34개 계약 및 pre-push/CI 배선이 모두 확인됐다. 이 합격은 제품 결함 두 건을 면제하지 않는다.

### 2026-08-24 09:06:35 KST — RED 독립 재현

```text
TIMESTAMP_KST: 2026-08-24 09:06:35 KST
WORKDIR: /tmp/rdp-red.e25TN3
SOURCE_HEAD: c59bad7b160c473cda5545e76e6fa6bcc711a7ea
SESSION: 01a03113-6b08-7841-bb48-a1b6888ea67d

CASE: AC-1 baseline empty repository
PASS: no secret-pattern match in any tracked file, .env not tracked
EXIT: 0

CASE: AC-3 baseline deleted historical PII CSV
PASS: 기록 전량 blob 3개 검사, 크기·경로 위반 0건
EXIT: 0

CASE: AC-3 baseline all mode
PASS: 추적 파일 2개 검사, 위반 0건
PASS: 기록 전량 blob 3개 검사, 크기·경로 위반 0건
PASS: csv/tsv/sql 0개 검사(추적 2개 중), 개인정보 적재 0건
EXIT: 0

FIXTURE_DISCLOSURE_CHECK: scanner output omitted synthetic row values=YES
```

→ 빈 대상과 삭제된 과거 개인정보가 모두 잘못 합격했다. 실제 fixture 값은 스캐너 출력에 나타나지 않았지만 탐지 자체가 없으므로 전체 판정은 FAIL이다.

### 2026-08-24 09:11 KST — acceptance RED

```text
TIMESTAMP_KST: 2026-08-24 09:11:28 KST
WORKDIR: /private/tmp/valuehire-rdp-20260824.7e3kk1/worktree
HEAD: c59bad7b160c473cda5545e76e6fa6bcc711a7ea
COMMAND: bash scripts/acceptance-secret-webhook-vendor.sh
PASS: 탐지됨 — discord 웹훅 URL
PASS: 탐지됨 — discordapp.com 변종(구 도메인)
PASS: 탐지됨 — Slack 웹훅 URL
PASS: 탐지됨 — Anthropic 벤더 키(하이픈 접두 · 중립 변수명)
PASS: 탐지됨 — WEBHOOK 계열 .env 대입(불투명 토큰)
PASS: 탐지됨 — CREDENTIAL 계열 .env 대입
PASS: 탐지됨 — PRIVATE_KEY 한 줄 형태
PASS: 탐지됨 — BOT_TOKEN (기존 TOKEN 규칙 회귀 앵커 · 신규 규칙에는 없음)
PASS: 탐지됨 — discord 버전 경로 /api/v10/ (공식 권장 형식)
PASS: 탐지됨 — discord 하위 도메인(canary)
PASS: 탐지됨 — Slack 공공기관용 GovSlack 도메인
PASS: 탐지됨 — Slack services 없는 형태(OAuth 응답 예시)
PASS: 탐지됨 — 벤더 키 39자 본문(길이 경계)
PASS: 탐지됨 — 인라인 주석이 붙은 .env 값
PASS: 오탐 없음 — 일반 discord 채널 URL(비밀 아님)
PASS: 오탐 없음 — 코드 대입(값이 아니라 호출)
PASS: 오탐 없음 — 환경변수 참조(값이 없다)
PASS: 오탐 없음 — 산문 속 키 형식 언급
PASS: 오탐 없음 — 일반 Slack 워크스페이스 URL
PASS: 오탐 없음 — .env.example 의 예시 주소
PASS: 오탐 없음 — 숫자만 있는 설정값(재시도 간격)
PASS: 오탐 없음 — 접미사 위장 도메인(notdiscord.com)
PASS: 오탐 없음 — 접미사 위장 도메인(not-hooks.slack.com)
PASS: 오탐 없음 — CREDENTIAL 저장 방식 이름(글자 설정값)
PASS: 오탐 없음 — PRIVATE_KEY 형식 이름(짧은 글자+숫자 설정값)
PASS: 오탐 없음 — sk-ant 조각을 품은 평범한 식별자(왼쪽 경계)
PASS: 오탐 없음 — 밑줄 접두 위장 discord 도메인
PASS: 오탐 없음 — 밑줄 접두 위장 slack 도메인
PASS: 스캐너 종단 — 벤더 키 파일을 verify.sh 가 차단 (verify.sh exit=1)
PASS: 스캐너 종단 — 대문자 표기 웹훅도 차단(-i 손실 감지) (verify.sh exit=1)
PASS: 스캐너 종단 — 정상 파일은 verify.sh 가 통과 (verify.sh exit=0)
FAIL: verify 계약 — 빈 Git 인덱스는 합격이 아니다 (기대 NOT_RUN/CHECKED:0/exit:2, 실제 CHECKED:없음/exit:0)
FAIL: verify 계약 — 안전한 Git 인덱스 blob 한 개 (기대 PASS/CHECKED:1/exit:0, 실제 CHECKED:없음/exit:0)
FAIL: verify 계약 — CHECKED 상수 위조 방지용 안전 blob 두 개 (기대 PASS/CHECKED:2/exit:0, 실제 CHECKED:없음/exit:0)
PASS: 3축 종료 상태 동일 (파일 상태[무시 포함] · HEAD · 객체 수 — 중간에 바꿨다 되돌린 변경·같은 개수 객체 교체는 못 본다, REV2-D1)
CHECKED: 35
EXIT: 1
```

→ 기존 32개 사례는 그대로 통과했고 새 계약 3개만 실패했다. 문법이나 fixture 준비 오류가 아니라 zero-target와 실제 CHECKED 누락 때문에 RED다.

```text
TIMESTAMP_KST: 2026-08-24 09:11:30 KST
WORKDIR: /private/tmp/valuehire-rdp-20260824.7e3kk1/worktree
HEAD: c59bad7b160c473cda5545e76e6fa6bcc711a7ea
COMMAND: bash scripts/acceptance-hs-a4.sh
PASS: gitignore 적용 — artifacts/x.png
PASS: gitignore 적용 — data/humansearch.sqlite3
PASS: gitignore 적용 — humansearch.db
PASS: gitignore 적용 — run.sqlite
PASS: gitignore 적용 — private-reviews/x.md
PASS: 추적 파일 186개 중 1048576 바이트 초과 0건
PASS: pre-commit 차단 확인 — 1MB 초과 파일 (exit=1 · 사유 일치)
PASS: pre-commit 차단 확인 — SQLite 파일 (exit=1 · 사유 일치)
PASS: pre-commit 차단 확인 — 아티팩트 스크린샷 (exit=1 · 사유 일치)
PASS: pre-commit 차단 확인 — 하위 경로 아티팩트 (exit=1 · 사유 일치)
PASS: pre-commit 차단 확인 — 하위 경로 데이터 (exit=1 · 사유 일치)
PASS: pre-commit 차단 확인 — SQLite WAL 사이드카 (exit=1 · 사유 일치)
PASS: pre-commit 차단 확인 — JSONL 덤프 (exit=1 · 사유 일치)
PASS: pre-commit 차단 확인 — 대문자 확장자 (exit=1 · 사유 일치)
PASS: pre-commit 차단 확인 — 디렉터리 규칙(확장자 무해) (exit=1 · 사유 일치)
PASS: pre-commit 차단 확인 — 비공개 리뷰 경로 (exit=1 · 사유 일치)
PASS: 인덱스 blob 기준 측정 확인 (작업트리 덮어쓰기로 우회 불가)
PASS: rename 도 검사 대상 (git mv 로 우회 불가)
PASS: 하위 경로 정상 소스는 조용히 사라지지 않는다 (앵커 확인)
PASS: 정상 파일은 통과 (차단과 통과가 한 쌍)
PASS: 훅과 공용 판정기의 금지 경로 패턴이 동치 (하위경로·사이드카·덤프·비공개리뷰 포함)
PASS: 판정기 실행 — 기록에만 남은 1MB 초과 파일을 잡는다 (D1) (exit=1)
PASS: 판정기 실행 — 깨끗한 기록은 통과시킨다 (차단과 통과가 한 쌍) (exit=0)
PASS: 판정기 실행 — 후보자 컬럼 CSV 를 잡는다 (D2) (exit=1)
PASS: 판정기 실행 — 후보자 컬럼 SQL 을 잡는다 (D2) (exit=1)
PASS: 판정기 실행 — 정상 지표 CSV 는 통과시킨다 (오탐 대조군) (exit=0)
PASS: 판정기 실행 — 정상 마이그레이션 SQL 은 통과시킨다 (오탐 대조군) (exit=0)
FAIL: 판정기 실행 — 삭제된 CSV blob (기대 exit=1, 실제 0)
FAIL: 판정기 실행 — 삭제된 TSV blob (기대 exit=1, 실제 0)
FAIL: 판정기 실행 — 삭제된 SQL blob을 all에서도 탐지 (기대 exit=1, 실제 0)
PASS: 판정기 실행 — 삭제된 정상 지표 CSV history 통과 (exit=0)
PASS: 판정기 실행 — 삭제된 schema-only SQL history 통과 (exit=0)
PASS: CI 가 공용 판정기를 실행 줄에서 호출한다
PASS: 판정기 스텝에 비활성화 조건 없음
PASS: 작업트리 무오염 (git status 기준 — git 설정·내부 객체·참조는 범위 밖)
CHECKED: 35
EXIT: 1
```

→ 기존 크기·경로·현재 PII·정상 대조군은 통과했고 삭제된 과거 CSV·TSV·SQL 세 사례만 실패했다. history 내용 호출 누락 때문에 RED임이 분리됐다.

## 필수 명령 대기표

| 명령 | 필수 | 최종 상태 |
|---|---|---|
| `bash scripts/acceptance-principles-check.sh` | 예 | 시작 PASS, 최종 재실행 대기 |
| `bash scripts/check-docs-sot.sh` | 예 | 대기 |
| 수정한 secret/data acceptance 원명령 전부 | 예 | RED/GREEN 대기 |
| `bash verify.sh` | 예 | 대기 |
| `bash scripts/scan-data-exposure.sh tracked` | 예 | 대기 |
| `bash scripts/scan-data-exposure.sh history` | 예 | 대기 |
| `bash scripts/scan-data-exposure.sh pii` | 예 | 대기 |
| `bash scripts/scan-data-exposure.sh all` | 예 | 대기 |
| workflow 무결성 및 semantic mutation 원명령 | 예 | 대기 |
| `git diff --check` | 예 | 대기 |
| 비밀 패턴 검사 | 예 | 대기 |
| 원본 dirty 상태·두 SOT SHA-256 재대조 | 예 | 대기 |
| Claude V1 | 예 | NOT_RUN — 구현 후 실행 |
| 새 맥락 Codex V2 | 예 | NOT_RUN — V1 후 실행 |

## 적대 검증 로그

G 구현, Claude V1, 새 맥락 Codex V2의 명령·전체 출력·SHA·판정 대조를 이 절에 추가한다. G/V1/V2가 위 T 계약과 일치하지 않으면 PASS로 끝내지 않는다.

## 제출 직전 §8-6b 셀프 감사

최종 제출 직전에 아홉 문항을 다시 판정한다. 현재는 진행 중이므로 완료 체크로 사용하지 않는다.
