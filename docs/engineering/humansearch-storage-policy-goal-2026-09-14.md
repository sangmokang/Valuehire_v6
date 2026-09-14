# HS-04.01 HumanSearch 저장 정책 계약 — goal (2026-09-14)

## 1층 — 결론

HS-04.01은 `docs/sot/humansearch-storage-contract.md`를 새 정본으로 추가해 저장·보존·삭제·암호화·권한 정책을
고정한다. 실제 브라우저 접속, 후보 개인정보 저장, SQLite migration, 암호화 구현, Supabase write, OS 계정
분리는 하지 않는다.

제품 배송 상태: `NOT_APPLICABLE`. 이 WU는 문서 계약 작업이며 운영 배포·운영 쓰기·라이브 포털 접속이 없다.

## 2층 — 판단 근거

HS-02.01은 열람 증거 필드를 확정했고, HS-03.03은 암호화 저장 전에 저장 정책 계약을 요구한다. 기존
`docs/sot/humansearch-browser-contract.md` §12는 Git 밖 원본 저장, 암호화, 0700/0600, 보존기간, 삭제,
PII 없는 영수증이 준비돼야 C1 접속이 가능하다고 했지만 구체 정책은 C1 정본에게 넘겼다. 이번 WU는 그 공백을
새 SOT로 채운다.

## 현재 상태

| 항목 | 확인 결과 |
|---|---|
| 기준 SHA | `443631e0e5447062b2f987b179d6a1dffdcad97b` |
| 브랜치 | `hs-0401-storage-policy-contract-20260914` |
| 선행 HS-02.01 | `docs/sot/humansearch-evidence-contract.md` 존재, 열람 증거 필드와 readback 계약 포함 |
| `docs/sot/strict-workflow.md` | 기준 SHA에 없음. strict 스킬의 저장소 SOT 우선 로드는 `NOT_RUN`으로 기록 |
| HumanSearch 암호화 저장 구현 | 없음. `_cdp.py`의 WebSocket key와 admin dashboard의 HMAC/retention 계약은 후보 원문 암호화 저장 구현이 아님 |
| invoice 저장 구현 | `contracts/invoice/storage-v1.json`, `tools/invoice/*` 존재. 도메인이 달라 HumanSearch 후보 원문 암호화 구현으로 재사용하지 않음 |

## 읽은 정본과 근거

- 사용자 AGENTS 지시: 독립 worktree, push/PR 승인, main merge 금지, shared browser SOT 직접 수정 금지.
- `/Users/kangsangmo/Desktop/hs-next-prompt-v5-20260914.md`: 전량 암호화 저장, 독립 readback, 저장 실패 시 순회 중단, SQLite 원본/Supabase 파생, 토큰·쿠키 비수집, 1촌 표시 연락처만.
- `~/.codex/skills/strict/SKILL.md`: strict 직접 로드, AC/counter-AC, 검증 기록 요구.
- `docs/sot/coding-principles.md`, `docs/sot/principles.yaml`, `bash scripts/acceptance-principles-check.sh`.
- `docs/sot/git-workflow.md`, `docs/sot/verification-commands.md`, `docs/sot/humansearch-browser-contract.md` §12/§16, `docs/sot/humansearch-l0-surface-contract.md`.
- `docs/sot/humansearch-evidence-contract.md`, `docs/engineering/humansearch-resume-evidence-contract-goal-2026-09-10.md`.
- `worktrees/hs-0004-recovery-20260910/docs/engineering/humansearch-next-issues-wu-2026-09-10.md` HS-03/04.
- `worktrees/hs-0004-recovery-20260910/docs/engineering/goal-prompts/humansearch-journey-kickoff-2026-09-07.md` 2026-09-08 결정.

## 범위

storage 문서 소유 쓰기 범위는 아래 두 파일이다.

- `docs/sot/humansearch-storage-contract.md`
- `docs/engineering/humansearch-storage-policy-goal-2026-09-14.md`

`docs/sot/humansearch-browser-contract.md`는 root 통합 소유다. 2026-09-14 root가 이 worktree에서 §12 storage
연결만 추가해 같은 HS-04.01 PR에 포함하기로 했다. LinkedIn §4/5 변경은 별도 root 브랜치 소유이며 이 PR 범위가
아니다.

## 인수 기준

### AC-1 저장 원본과 파생, 열람 완전성 분리

When 후보 열람 증거를 저장할 때 시스템은 단일 SQLite 원본에 intent, manifest, readback, purge, Supabase outbox를 연결하고 Supabase를 파생 저장으로만 취급해야 하며, 저장 `confirmed`와 evidence `complete/partial/failed`를 서로 독립 상태로 보존해야 한다.

검증 명령:

```bash
rg -n '단일 원본|SQLite|Supabase|파생|outbox|로컬 저장 완료를 대신하지 않는다|저장 상태와 열람 완전성은 독립|partial.*complete' docs/sot/humansearch-storage-contract.md
```

counter-AC: Supabase readback 성공을 SQLite 원본 저장 성공으로 대체한다. 부분 열람 원문을 성공 저장했다는 이유로 evidence를 complete로 승격한다.

### AC-2 암호화와 readback

When 후보 원문, 캡처, 추출물, 연락처, 민감 URL 원문을 저장할 때 시스템은 보호 저장소에 암호화하고 독립 readback이 맞지 않으면 완료로 보고하지 않아야 하며, readback은 복호화 payload, manifest, SQLite 관계를 writer 메모리 재사용 없이 다시 검증해야 한다.

검증 명령:

```bash
rg -n '암호화|readback|confirmed|저장 완료가 아니다|복호화 payload|writer의 메모리|현재 HumanSearch 코드에는 재사용 가능한 암호화 저장 구현이 없다' docs/sot/humansearch-storage-contract.md
```

counter-AC: 파일 write만 성공하고 `confirmed`로 처리한다.

### AC-3 실패 시 순회 중단

If 저장, 권한, 암호화, readback, evidence 필수 필드/coverage, 금지 입력 검사 중 하나가 실패하면 시스템은 다음 후보나 다음 채널 순회를 시작하지 않아야 하며, 이미 열람한 후보 원문은 비밀값 제거 뒤 암호화 recovery 격리와 intent 상태로 보존해야 한다.

검증 명령:

```bash
rg -n '순회 중단|다음 후보|forbidden_input|partial|failed|recovery_required|coverage 오류|recovery 격리|비밀값 제거' docs/sot/humansearch-storage-contract.md
```

counter-AC: 저장 실패 뒤 다음 후보 상세를 연다.

### AC-4 보존과 삭제

Where 저장된 후보 증거가 존재할 때 시스템은 무기한 보존하고 명시적 purge 요청으로만 삭제해야 하며, purge 영수증에는 후보자 PII가 없어야 하고 SQLite 원본, 암호화 파일, recovery 격리, Supabase 파생 row, pending outbox 재생성 방지를 tombstone으로 묶어야 한다.

검증 명령:

```bash
rg -n '무기한|명시적 purge|자동 만료 삭제|PII 없는 영수증|recovery_required|멱등|tombstone|outbox|Supabase|재생성|단순 DB 삭제' docs/sot/humansearch-storage-contract.md
```

counter-AC: 보존기간 만료로 자동 삭제하거나 purge 영수증에 이름·연락처·원본 URL 경로를 쓴다.

### AC-5 권한과 Git 유출 금지

When 원본 DB와 암호화 파일을 쓸 때 시스템은 Git 밖 보호 위치, 디렉터리 0700, 파일 0600, 생성 시 restrictive mode/umask, 쓰기 전 owner/mode/symlink/root 검증, SQLite WAL/SHM/journal/temp/백업 권한, OS 독립 쓰기 권한을 요구하고 같은 UID 하위 에이전트 검토를 권한 격리 증거로 부르지 않아야 한다.

검증 명령:

```bash
rg -n 'Git 밖|0700|0600|umask|쓰기 전에|WAL|SHM|journal|temp|백업|EACCES|symlink|같은 UID|Git에 넣지 않는다|운영 프로젝트 입력' docs/sot/humansearch-storage-contract.md
```

counter-AC: 같은 UID에서 작성한 검토 파일을 독립 실행기 영수증으로 인정한다.

### AC-6 토큰·쿠키·연락처 경계

If 저장 입력에 토큰, 쿠키, storageState, 세션 헤더가 포함되면 시스템은 금지 입력으로 중단하고 해당 비밀값 원문은 영구 격리하지 않아야 하며 LinkedIn/RPS 연락처는 표시된 1촌 연락처만 관측 상태로 남겨야 한다.

검증 명령:

```bash
rg -n '토큰|쿠키|storageState|세션|forbidden_input|비밀값 제거|1촌|보이지 않는|추정' docs/sot/humansearch-storage-contract.md
```

counter-AC: 보이지 않는 이메일·전화번호를 추정하거나 CDP cookie dump를 저장 payload에 넣는다.

## 입출력·오류·상태 계약

입력은 `run_id`, `position_ref`, `channel`, `candidate_key`, `evidence_manifest`, `encrypted_payload_refs`,
`observed_contact_fields`, `storage_intent_id`를 갖는다. 토큰·쿠키·storageState·세션 헤더는 입력이 아니다.

출력 상태는 `confirmed`, `partial`, `failed`, `forbidden_input`, `recovery_required`다. `confirmed`만 다음 후보 진행을 허용한다. 저장 `confirmed`는 evidence `complete`를 뜻하지 않는다.

오류는 필수 evidence 누락, coverage/readback 불일치, 암호화 파일 쓰기 실패, 권한 완화, 키 없음, 잘못된 키,
복호화 실패, 금지 입력, Supabase write 실패, purge 일부 실패를 구분한다. 이미 열람한 후보 원문은 비밀값 제거 뒤
암호화 recovery 격리와 intent 상태로 남기고, 세션 비밀값 원문은 영구 격리하지 않는다.

## 비범위

- HS-02 필드 복제 또는 신규 범용 검사기 추가.
- SQLite migration, crypto 구현, 새 crypto 의존성 선택.
- 브라우저 접속, 실제 포털 읽기, 후보 원문 저장.
- Supabase write/readback 실행.
- 독립 실행기 OS 계정 생성 또는 권한 변경.
- main merge.

## Browser SOT §12 통합 상태

root가 `docs/sot/humansearch-browser-contract.md` §12 조건 6/7과 C1 serializer 문단을 storage SOT에 연결했다.
이 변경은 storage 정책 연결만 포함하며, LinkedIn §4/5 정리는 별도 root PR 소유다.

검증 명령:

```bash
rg -n 'humansearch-storage-contract|무기한 보존|명시적 purge|파생 삭제|저장 실패 시 순회 중단|독립 readback|실제 시험을 대신하지 않는다' docs/sot/humansearch-browser-contract.md
```

## 검증 계획

```bash
bash scripts/acceptance-principles-check.sh
rg -n '단일 원본|SQLite|Supabase|파생|outbox|로컬 저장 완료를 대신하지 않는다|저장 상태와 열람 완전성은 독립|partial.*complete' docs/sot/humansearch-storage-contract.md
rg -n '암호화|readback|confirmed|저장 완료가 아니다|복호화 payload|writer의 메모리|현재 HumanSearch 코드에는 재사용 가능한 암호화 저장 구현이 없다' docs/sot/humansearch-storage-contract.md
rg -n '순회 중단|다음 후보|forbidden_input|partial|failed|recovery_required|coverage 오류|recovery 격리|비밀값 제거' docs/sot/humansearch-storage-contract.md
rg -n '무기한|명시적 purge|자동 만료 삭제|PII 없는 영수증|recovery_required|멱등|tombstone|outbox|Supabase|재생성|단순 DB 삭제' docs/sot/humansearch-storage-contract.md
rg -n 'Git 밖|0700|0600|umask|쓰기 전에|WAL|SHM|journal|temp|백업|EACCES|symlink|같은 UID|Git에 넣지 않는다|운영 프로젝트 입력' docs/sot/humansearch-storage-contract.md
rg -n '토큰|쿠키|storageState|세션|forbidden_input|비밀값 제거|1촌|보이지 않는|추정' docs/sot/humansearch-storage-contract.md
rg -n 'humansearch-storage-contract|무기한 보존|명시적 purge|파생 삭제|저장 실패 시 순회 중단|독립 readback|실제 시험을 대신하지 않는다' docs/sot/humansearch-browser-contract.md
git diff --check
bash verify.sh
```

## 현재 검증 제한

로컬 검증, 외부 V1, PR, CI, main 병합, 운영 실증은 서로 다른 상태다. 이 문서 WU는 stable candidate commit,
외부 V1, push/PR까지 수행할 수 있지만 main merge와 browser SOT §12 직접 수정은 이 WU의 소유 범위가 아니다.

## 2026-09-14 외부 V1·codeaudit 상태

외부 V1은 시도했지만 완료하지 못했다. 완료한 검증과 미완료 검증은 아래처럼 구분한다.

| 항목 | 상태 | 증거 |
|---|---|---|
| Claude V1 1차 | `NOT_RUN` | 3분 이상 응답 없음, 중단 뒤 `Error: No messages returned from query`, 종료값 130 |
| Claude V1 2차 | `NOT_RUN` | CLI 옵션 파싱 오류로 prompt가 tool deny rule로 해석됨, 종료값 1 |
| Claude V1 3차 | `NOT_RUN` | 파일 내용을 prompt에 직접 포함했으나 `Credit balance is too low`, 종료값 1 |
| Gemini V1 | `NOT_RUN` | 로컬 `gemini` binary 없음. `omx ask gemini`도 `[ask-gemini] Missing required local CLI binary: gemini`로 종료값 1 |
| root codeaudit | `APPROVE` | root가 commit `235a62d` 범위에서 다섯 storage 계약 결함 해소를 실제 SOT 검토로 승인 |
| 별도 codeaudit runner | `NOT_RUN` | 별도 독립 codeaudit 실행자는 없음. root codeaudit 승인과 로컬 AC 대조까지만 완료 |

따라서 이 WU의 현재 증거는 로컬 문서 AC 대조, strict 원칙 검사, diff 공백 검사, 비밀 스캔, root 수동 감사 지적
반영, root codeaudit 승인이다. Claude/Gemini 외부 V1 통과로 확대해 말하지 않는다.
