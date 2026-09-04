# Invoice 다음 실행 목표·검증 기록 — 2026-09-04

## 결론

현재 Invoice 변경은 로컬 작업트리에 남아 있고 최신 원격 기준으로 뒤처진 변경은 없다. 이 실행은 Invoice 범위만 새로 검사해 안전한 로컬 커밋으로 보존하고, 원격 전송·운영 데이터 변경·메일 발송은 실제 권한과 자격증명이 확인되지 않으면 실행하지 않는다.

사용자가 이번 결과에서 판단할 것은 로컬 커밋을 원격으로 전달할지 여부다. 운영 데이터와 메일 단계는 별도 증거가 생기기 전까지 완료로 표시하지 않는다.

## 판단 근거

- 정본(SOT, 업무 규칙의 단일 기준)은 `docs/sot/invoice.md`, `docs/sot/invoice-storage.md`, 세 JSON 계약과 두 플랫폼의 Invoice 스킬이다. 과거 목표 문서는 역사 기록이며 현재 규칙을 공급하지 않는다.
- 현재 브랜치는 `origin/main`보다 2개 커밋 앞이고 0개 뒤다. 따라서 먼저 필요한 일은 새 기능 추가가 아니라 남은 변경의 범위 확인, 현재 검사 재실행, 실패 시 최소 수정, 로컬 안전 커밋이다.
- 원격 저장소 전송, PR 생성·병합, 운영 Supabase 쓰기, Gmail 발송은 외부 상태를 바꾼다. 현재 세션에서 그 권한과 자격증명이 독립 확인되지 않으면 정확한 중단 상태만 남긴다.

> **무엇을** — 기존 Invoice 변경만 검증하고 명시적으로 스테이지해 하나의 로컬 안전 커밋으로 봉합한다.
> **왜** — 사용자 소유의 다른 변경과 외부 운영 상태를 건드리지 않으면서 현재 구현의 재현 가능한 경계를 만들기 위해서다.
> **버린 길** — `git add .`로 전체 작업트리를 묶는 방식은 무관 파일과 조사 산출물을 포함할 수 있어 기각한다.
> **대가** — 원격 전송과 운영 반영은 이 실행만으로 끝나지 않고 별도 권한 확인이 필요하다.
> **되돌리기** — 로컬 커밋은 새 브랜치에서 역커밋하거나, 아직 원격 전달 전이면 해당 커밋의 부모에서 새 브랜치를 만들어 복구한다.

## 현재 상태와 직접 회수

- 위험등급: **L3**. 정본·계약·검사·공유 스킬·데이터베이스 마이그레이션을 포함하고 3개보다 많은 파일과 운영 경계를 다룬다.
- 세션 식별자: `01a06ccb-fd47-7840-8cdc-6336a7b6215e`
- 시작 커밋: `9566b1978b9063388cc735358cdb979a03fd110e`
- 최신 확인 원격 `main`: `b7240936827032d5ee6791fa8cdb7d62ef6584b4`
- 원격 대비: 뒤처짐 `0`, 앞섬 `2` (`git rev-list --left-right --count origin/main...HEAD` 출력 `0 2`).
- 시작 작업트리에는 기존 Invoice 수정·신규 파일이 남아 있다. 시작 스냅샷 뒤 조사 과정에서 `codex-scope-verdict.md`가 새로 나타났으며 Invoice 커밋 범위에서 제외하고 생성 주체를 확인한다.
- 직접 읽은 현재 정본과 지시: `docs/sot/coding-principles.md`, `docs/sot/principles.yaml`, `docs/engineering/invoice-next-execution-prompt-2026-09-04.md`, `docs/sot/invoice.md`, `docs/sot/invoice-storage.md`, `contracts/invoice/invoice-v1.json`, `contracts/invoice/deduction-v1.json`, `contracts/invoice/storage-v1.json`, `.codex/skills/invoice/SKILL.md`, `.claude/skills/invoice/SKILL.md`, `docs/engineering/invoice-final-implementation-prompt-2026-09-02.md`, 역사 기록 `docs/engineering/invoice-skill-goal-2026-09-01.md`, 검증 정본 `docs/sot/verification-commands.md`.
- 코드 한도: 직접 작성 파일 hard 600줄, 함수 hard 100줄. 생성 파일·마이그레이션·fixture는 정본이 명시한 면제 범주이며, 실패 뒤 소급 예외는 만들지 않는다.

## 근본 원인

Invoice의 운영 보강분은 이미 구현됐지만 아직 커밋되지 않았고, 현재 커밋에 귀속된 새 검증 결과도 없다. 과거 초록불은 현재 작업트리의 안전성과 원격·운영 성공을 증명하지 못한다.

## 범위

### 포함

- 작업 지시서의 작업 1: Invoice 변경 범위 분리, 8개 원명령 재실행, 실패 복구, 플랫폼 파일 동등성, 명시적 스테이지, Lore 로컬 커밋.
- 작업 2: 최신 `main`과 충돌 가능성을 읽기 전용으로 확인하고 권한이 없으면 `READY_TO_PUSH`에서 중단.
- 작업 3: 기존 Supabase 연결·스키마·네 Invoice 마이그레이션의 적용 계획과 위험을 읽기 전용으로 검증. 실제 운영 쓰기는 권한·자격증명 없으면 `SUPABASE_DEPLOY_BLOCKED`.
- 작업 4~6: 입력·권한·원격 계약·번호가 실제로 확인되는 범위까지만 순서대로 진행하고, 미충족 경계는 인보이스·정산·메일 상태를 분리해 기록.

### 비범위

- 승인되지 않은 push, PR 생성·병합, 운영 Supabase 쓰기, Gmail 발송.
- Invoice와 무관한 사용자 파일의 수정·스테이지·커밋.
- 실제 후보자 이름·메일·PDF·HTML·metadata·PNG를 추적 문서나 커밋 메시지에 기록.
- V4 전체 마이그레이션 backlog 적용, 기본 수수료율 신설, 미제공 인보이스 번호·정산 참여자 추정.

## T 계약 — 합격 조건

T는 이 문서의 실행 계약과 현재 `docs/sot/invoice.md`, `docs/sot/invoice-storage.md`, `contracts/invoice/*.json`, 두 Invoice `SKILL.md`, `docs/engineering/invoice-final-implementation-prompt-2026-09-02.md`의 합집합이다. 충돌하면 사용자 현재 지시, 저장소 최상위 규칙, 기능 정본 순으로 판정하고 추정으로 메우지 않는다.

### AC-1 — 범위 안전

- EARS 단언: **When** 로컬 커밋을 만들 때, 시스템은 시작 스냅샷에서 확인한 Invoice 범위 파일만 명시적으로 스테이지하고 무관 파일과 조사 산출물을 포함하지 않아야 한다.
- 검증 명령: `git diff --cached --name-status`, `git status --short`, `git diff --cached --check`.
- 기대값: staged 목록이 승인된 Invoice 범위와 이 goal뿐이고, `codex-scope-verdict.md`와 무관 파일은 0건이며 공백 오류가 없다.
- counter-AC: `git add .` 뒤 우연히 검사가 초록이거나, 기존 사용자 파일을 함께 묶거나, 미추적 파일을 읽지 않고 누락하는 것은 가짜 완료다.

### AC-2 — 현재 변경 검증

- EARS 단언: **When** 작업 1을 봉합할 때, 시스템은 지시서의 8개 원명령을 현재 변경에서 모두 실행하고 각 종료값 0과 비어 있지 않은 검사 건수를 확인해야 한다.
- 검증 명령: 지시서의 단위시험, 임시 PostgreSQL 검사, 독립 Invoice 게이트, Invoice·semantic mutation·CI step integrity·AC-M 인수검사, `git diff --check`.
- 기대값: 단위시험은 0건보다 많고, PostgreSQL·게이트·인수검사는 각자의 `VERDICT: PASS`와 `CHECKED` 계약을 만족하며 모든 종료값이 0이다.
- counter-AC: 하위 명령만 통과하고 원명령을 다시 실행하지 않거나, 검사 대상 0건·고정 출력·과거 결과 재사용·필수 검사를 선택 검사로 낮추면 가짜 완료다.

### AC-3 — 수수료·문서·저장 계약

- EARS 단언: **If** 활성 고객사·포지션·적용일 계약이 없거나 중복되거나 입력값과 다르면, 시스템은 기본 비율이나 최근 계약으로 대체하지 않고 명시 오류로 중단해야 한다.
- EARS 단언: **When** 문서 세트를 저장하면, 시스템은 문서 쌍·계약 버전·SHA-256·응답 정체성을 검증하고 SQLite pending과 Supabase 성공을 구분해야 한다.
- 검증 명령: 단위시험, `bash tools/invoice/tests/test_postgres_integrity.sh`, `python3 scripts/verify/check-invoice-gate.py`.
- 기대값: 충돌·불변성·멱등성·거짓 hash·읽기 전용 정책 반례가 차단되고 최초/동일 재시도 상태가 계약대로 구분된다.
- counter-AC: HTTP 2xx, 로컬 outbox, 예시 20% 또는 렌더 성공만으로 원격 계약·저장 성공을 주장하면 가짜 완료다.

### AC-4 — 플랫폼 동등성과 검사 무력화 저항

- EARS 단언: **Where** Codex와 Claude가 Invoice 스킬을 로드하면, 두 `SKILL.md`와 두 `agents/openai.yaml`은 각각 바이트 동일하고 같은 정본·실행기를 사용해야 한다.
- EARS 단언: **If** Invoice 인수검사나 CI 배선을 빈 본문·항상 성공·조건부 미실행·출력 위조로 약화하면, 독립 게이트는 실패해야 한다.
- 검증 명령: `cmp -s` 두 쌍, 각 SHA-256, semantic mutation·CI step integrity·AC-M 원명령.
- 기대값: 두 `cmp` 종료값 0, 쌍별 hash 동일, 모든 무력화 반례 차단, 검사 대상 0건 차단.
- counter-AC: 내용이 비슷하지만 바이트가 다르거나, 검사기 자기 선언만 믿거나, 신규 검사만 pre-push 또는 CI 한쪽에 연결하면 가짜 완료다.

### AC-5 — 외부 효과 경계

- EARS 단언: **While** push·PR·운영 Supabase 쓰기·Gmail 발송에 필요한 명시 권한과 자격증명이 독립 확인되지 않는 경우, 시스템은 해당 외부 효과를 실행하지 않고 각각 `READY_TO_PUSH`, `SUPABASE_DEPLOY_BLOCKED`, `BLOCKED`로 기록해야 한다.
- EARS 단언: **When** 읽기 전용 확인을 수행하면, 시스템은 비밀값을 출력·복사·저장하지 않아야 한다.
- 검증 명령: 실행 명령 감사, 환경변수 이름의 존재 여부만 확인하는 비밀값 비출력 검사, 최종 `git status`, 원격/메일/DB 쓰기 식별자 부재 확인.
- 기대값: 로컬 커밋 외 외부 쓰기 0건이며 실행하지 않은 단계를 성공으로 표현하지 않는다.
- counter-AC: 원격 URL 존재를 권한으로 간주하거나, `SUPABASE_URL`만으로 service-role 권한을 추정하거나, Gmail 도구 연결만으로 발송 승인을 추정하면 가짜 완료다.

### AC-6 — 데이터 안전과 롤백

- EARS 단언: **When** 검증·커밋·보고를 수행할 때, 시스템은 실제 후보자 자료를 `artifacts/invoices/` 밖 추적 파일이나 커밋 메시지에 넣지 않아야 한다.
- EARS 단언: **If** 로컬 변경을 되돌려야 하면, 시스템은 외부 상태 변경 없이 Invoice 체크포인트만 식별 가능한 방법으로 복구할 수 있어야 한다.
- 검증 명령: `bash scripts/scan-data-exposure.sh tracked`, staged 파일·커밋 메시지 감사, `git show --stat --oneline HEAD`.
- 기대값: 추적 개인정보 노출 0건, 커밋 범위 식별 가능, 외부 쓰기 식별자 0건.
- counter-AC: 실제 이름을 검증 로그·goal·커밋 제목에 복사하거나, 롤백이 테스트·계약 변경을 조용히 잃게 만들면 가짜 완료다.

## 입출력·오류·경계 계약

### 입력

```json
{
  "repository_root": "/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/invoice-skill",
  "branch": "task/invoice-skill-20260901",
  "sot": [
    "docs/sot/invoice.md",
    "docs/sot/invoice-storage.md",
    "contracts/invoice/invoice-v1.json",
    "contracts/invoice/deduction-v1.json",
    "contracts/invoice/storage-v1.json"
  ],
  "external_writes": false
}
```

- 빈 저장소 경로, 다른 worktree, 다른 브랜치, 정본 누락·빈 파일·파싱 실패는 구현·커밋 전에 실패다.
- 실제 Invoice 거래 입력은 현재 추적 문서에 복사하지 않는다. 발행 번호·원격 계약·정산 입력이 없으면 해당 후속 산출물을 만들지 않는다.

### 출력

```json
{
  "local_commit": "40-char git sha or null",
  "local_validation": "PASS|FAIL|NOT_RUN",
  "push_pr": "READY_TO_PUSH|PASS|BLOCKED|NOT_RUN",
  "supabase_deploy": "PASS|SUPABASE_DEPLOY_BLOCKED|FAIL|NOT_RUN",
  "agreement_registration": "PASS|BLOCKED_INPUT|BLOCKED|NOT_RUN",
  "pdf": "REVIEW_READY|BLOCKED_INPUT|BLOCKED|FAIL|NOT_RUN",
  "gmail": "SENT|GMAIL_SENT / DELIVERY_RECEIPT_PENDING|BLOCKED|FAIL|NOT_RUN",
  "delivery_status": "LOCAL_ONLY|PREVIEW_VERIFIED|PRODUCTION_REACHABLE|PRODUCTION_VERIFIED|BUSINESS_USED"
}
```

### 오류·권한·동시성·재시도 경계

- 필수 로컬 검증 실패는 `FAIL`; 명령을 시작하지 못했거나 출력을 읽지 못하면 `NOT_RUN`; 권한 밖 조건이 복구 뒤에도 없으면 해당 외부 단계만 `BLOCKED`다.
- 한 필수 원명령이 실패하면 원명령·폴더·시각·종료값·전체 출력을 기록하고 하위 원인을 고친 뒤 같은 원명령을 다시 실행한다.
- 수수료 계약과 문서 번호는 멱등 키를 사용하며 같은 키의 다른 payload는 실패한다. Gmail 실패는 자동 재발송하지 않는다.
- 직접 작성 코드 파일은 600줄 이하, 함수는 100줄 이하이다. 같은 판정기로 600줄 정상 사본과 601줄 고장 사본을 임시 디렉터리에서 시험하고 원본을 바꾸지 않는다.

## Harness 게이트 계획

| 게이트 | 이번 실행의 증거 |
|---|---|
| 0 | 현재 원칙 직접 로드·34/34 검사, 시작 HEAD·원격 대비·오염·과거 goal 회수 |
| 1 | 이 문서의 EARS 단언, counter-AC, 입출력·오류·경계 계약 |
| 2 | 기존 전용 worktree를 사용하고, 현재 작업은 신규 구현이 아니라 미커밋 보강분 봉합이므로 역사적 RED를 합격증으로 재사용하지 않는다. 현재 뮤테이션과 실패 주입을 새로 실행한다 |
| 3 | 필수 검증이 실패할 때만 관련 최소 변경으로 복구하고 같은 원명령을 재실행한다 |
| 3.5 | Invoice 스킬 → 정본·JSON → 렌더·저장 CLI → SQLite/Supabase RPC 경로를 정적·런타임 검사로 재확인한다 |
| 4 | 작업 지시서 8개 명령, 플랫폼 동등성, 파일·함수 경계, 데이터 노출 검사, V1/V2 |
| 5 | Invoice 범위만 로컬 Lore 커밋하고 `READY_TO_PUSH` 증거를 남긴다 |
| 6 | push·PR·병합·운영 쓰기·메일은 현재 자동 실행하지 않는다 |

## SKELETON·배송 상태

- 이 실행은 이미 존재하는 Invoice 제품 표면의 봉합 작업이므로 새 운영 표면을 만들지 않는다. 새 운영 주소나 인증 계층을 추가하지 않는다.
- 로컬/임시 PostgreSQL에서 스키마·RPC·동시성·멱등성·롤백 가능성을 검증하되 fixture와 임시 DB를 운영 증거로 부르지 않는다.
- 목표 배송 상태는 `LOCAL_ONLY`다. 실제 운영 프로젝트 쓰기와 독립 readback이 없으므로 `PRODUCTION_VERIFIED` 이상을 주장하지 않는다.
- 네 전진 마이그레이션의 한 명령 롤백은 운영 적용 전 백업·복구 경로와 현재 적용 이력이 확인될 때만 계획에 확정한다. 권한 없이는 실행하지 않는다.

## G/V1/V2/T 적대검증

- G: 현재 Codex 세션이 범위 분리, 필요 최소 복구, 검증, 로컬 커밋을 수행한다. 자기 검사는 최종 합격증이 아니다.
- V1: `ANTHROPIC_API_KEY`를 제거한 실제 Claude CLI가 staged 산출물과 T, 실행 증거만 받아 가짜 완료, 부분 배선, 동시성, 권한, 회귀, 600/601 경계, 검사 대상 0건을 공격한다.
- V2: 새 맥락 Codex 검증자가 V1의 `file:line`과 명령을 재현하고 V1의 과장·누락, staged 범위와 제품 호출 경로의 상관된 맹점을 재공격한다.
- T: 이 goal의 AC와 counter-AC, 기능 정본, JSON 계약, 검증 정본이다. G·V1·V2가 갈리면 완료로 판정하지 않는다.

## R2~R5 실행 계획

- R2: 현재 semantic mutation 원명령과 Invoice 게이트를 실행하고, 필요한 직접 뮤테이션은 `mktemp` 아래 복사본에서만 수행한다. 원본 테스트를 약화하지 않는다.
- R3: 외부 상태·도구 버전·권한 주장은 현재 명령 출력에만 근거하고, 확인하지 못한 운영 사실은 추정이 아니라 한계로 기록한다.
- R4: 두 플랫폼 스킬에서 렌더·저장 CLI, 계약, SQLite, PostgreSQL RPC까지 제품 진입 경로를 추적하고 테스트에서만 불리는 고아 구현이 없는지 확인한다.
- R5: 과거 goal에서 `omx explore`가 `cargo` 부재로 실패한 경로는 반복하지 않는다. 필수 원명령 실패는 하위 원인을 바꿔 복구하고 같은 원명령으로 승격한다.

## 영향 반경·데이터 안전·롤백

- 영향 반경: Invoice 스킬, 문서·JSON 계약, 렌더·저장 Python, Invoice 시험·인수 게이트, 네 전진 마이그레이션, 관련 CI·정본 배선.
- 데이터 안전 AC: 운영 DB 쓰기 0건, Gmail 발송 0건, 추적 파일의 실제 후보자 데이터 0건, 비밀값 출력·저장 0건.
- 로컬 롤백: 새 체크포인트 커밋 SHA를 기준으로 전체 역커밋하거나 필요한 파일만 별도 검토 후 역커밋한다. 테스트·계약을 조용히 제외하지 않는다.
- 운영 롤백: 실제 적용 전 현재 migration 이력·백업·복구 명령·N-1 읽기 호환을 확인하지 못하면 배포 자체를 하지 않는다.

## 검증 장부

### Strict 원칙 직접 로드

| 시각 | 커밋/세션 | 명령 | 상태 | 전체 출력 또는 해석 |
|---|---|---|---|---|
| 2026-09-04T23:22:37+09:00 | `9566b197` / `01a06ccb-fd47-7840-8cdc-6336a7b6215e` | `sed -n '1,1200p' docs/sot/coding-principles.md` | PASS | 74줄 전체를 직접 읽었고 P11의 파일 hard 600·함수 hard 100을 확인했다. 파일 자체가 전체 원문이다. |
| 2026-09-04T23:22:41+09:00 | 동일 | `sed -n '1,1600p' docs/sot/principles.yaml` | PASS | 345줄 전체를 직접 읽었고 34개 원칙 장부와 strict/pre-push/CI 연결 선언을 확인했다. 파일 자체가 전체 원문이다. |
| 2026-09-04T23:22:45+09:00 | 동일 | `bash scripts/acceptance-principles-check.sh` | PASS | 아래 원문, 종료값 0. |

```text
VERDICT: PASS
SOT_LOAD: PASS docs/sot/coding-principles.md
LEDGER_LOAD: PASS docs/sot/principles.yaml
MECHANISMS: PASS 34/34 strict-contract-bindings
WIRING: PASS pre-push=1 ci=1
CHECKED: 34
EXIT_CODE=0
```

→ 현재 저장소의 코딩 원칙 34개와 두 로컬·원격 검사 연결을 실제 검사기가 모두 찾았다. 이는 Invoice 기능 자체의 합격이 아니라 Strict 시작 자격의 합격이다.

### 작업 실행 로그

후속 필수 명령의 시각·종료값·전체 출력과 V1/V2 원문을 이 절에 계속 기록한다.

## 제출 직전 셀프 감사

- 결론에 전문용어가 있나? `아니오`
- `→` 해석 없는 출력·코드·표가 있나? `아니오`
- 결론에 결정할 사항이 빠졌나? `아니오`
- 결정에 버린 길·대가가 빠졌나? `아니오`
- `file:line`의 역할 설명이 빠졌나? `아니오`
- 쉽게 쓰며 증거·수치·한계를 뺐나? `아니오`
- 초등학생 비유로 내용을 깎았나? `아니오`
- 건너뜀·미확인·실패 후 재시도가 앞부분에서 빠졌나? `아니오`
- 추정을 확인된 사실처럼 썼나? `아니오`
