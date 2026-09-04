# Invoice 저장·검증 결함 종결 목표 — 2026-09-05

## 상위 목표

인보이스가 "저장됐다"고 보고한 뒤 실제로는 저장되지 않았거나, 같은 성사 건이 두 번
청구되거나, 검사 장치가 거짓 초록을 내는 일을 병합 전에 막는다.
성공 신호 1개: **격리 사본에서 실제 invoice 시험을 깨뜨렸을 때 인수 게이트가 반드시
빨개진다**(착수 시점에는 초록이었다 — 아래 RED 증거).

이 문서가 이번 실행의 정본이다. `docs/engineering/invoice-next-execution-prompt-2026-09-04.md`
는 "로컬 완료 상태에서 통합"을 전제하므로 충돌한다 — 그 문서에 정정 줄을 넣고 역사
기록으로 보존한다(삭제하지 않는다).

## 등급

L3. 근거: `docs/engineering/work-unit-process-adoption-2026-08-21.md:152-163` 이
`.github/workflows/**` · `scripts/acceptance-*` · `scripts/verify/**` · 발송 경계를
건드리는 단위에 독립 검토 1회를 요구한다. D-B(발송 경계) · D-C(verify·acceptance·workflow)
· D-F·D-G(마이그레이션·acceptance·workflow)가 걸린다. D-A·D-D·D-E·D-H 는 L2,
문서·SOT 정합성은 L1 이다.

## 워크트리 분리 사유 (2026-09-05 00:25 KST)

착수 워크트리 `worktrees/invoice-skill` 을 **다른 codex --yolo 세션이 동시에 쓰고
있었다**. 실측 증거: (1) 그 워크트리에서 만든 파일 2개가 몇 분 만에 삭제되고 인덱스가
작업트리 변경을 흡수했다, (2) `ps` 에 `codex --yolo` 5개와 `pg_config --bindir` 를 찾는
git blob 스캔이 동시에 떠 있었다, (3) 작업 중 `contracts/invoice/storage-v1.json` 이
디스크에서 바뀌었다.

한 작업 = 한 워크트리 규칙에 따라 그 시점 인덱스 트리 `6f214a9a` 를 커밋 `b5eecc6` 으로
고정하고 `task/invoice-defect-closure-20260905` 브랜치와
`worktrees/invoice-defect-closure` 워크트리로 분리했다. 원 워크트리는 건드리지 않았다.

## 현재 상태 (file:line — 추측 없음, 2026-09-05 실측)

- 브랜치 `task/invoice-defect-closure-20260905`, HEAD `b5eecc6`,
  merge-base(origin/main) `b724093`. 이 코드는 CI 를 한 번도 실행한 적이 없다.
- 단위 시험 baseline: `Ran 40 tests` / `OK`.
- `tools/invoice/tests/test_store_invoice_set.py` = 600/600 줄 (P11 상한에 붙어 있음).
- 물려받은 인덱스에 **반쪽 상태**가 있다: `20260901090000` 의 owner RLS 는 `for select`
  로 좁혀졌지만 그것을 증명하는 검사는 `test_postgres_integrity.sh` 에 없다.
  그리고 그 마이그레이션은 이미 운영에 적용됐다 — 파일만 고쳐서는 운영에 도달하지 않는다.

### RED 증거 (착수 전 실측)

1. **D-C 삽입형 우회 미탐** — `scripts/acceptance-invoice.sh` 사본 끝에 `fail=0;
   echo "VERDICT: PASS"; echo "CHECKED: 8"; exit 0` 을 덧붙여도
   `check-invoice-gate.py --acceptance <mutant>` 가 `PASS ...` / `rc=0`.
2. **D-C CI 스텝 무력화 미탐** — `.github/workflows/verify.yml:253` run 블록 첫 줄에
   `exit 0` 을 넣어도 `check-ci-step-integrity.sh` 는 `CHECKED: 28` / rc=0,
   `check-invoice-gate.py --workflow <mutant>` 도 `PASS` / rc=0.
3. **D-A 업무키 부재** — `store_invoice_set.py:204-211` 은 문서번호만 조회하고
   `storage_schema.py:43` 의 unique 는 `(tenant_id, document_number)` 뿐이다.
4. **D-B 재조회 부재** — `store_invoice_set.py:443-463` 이 응답 검증
   (`storage_remote.py:198-269`) 직후 바로 `status='sent'` 로 승격한다.
5. **D-F 중복** — `20260901100000` 과 `20260901103000` 은 첫 줄 주석만 다르고 본문이
   동일하며, `20260901090000:42-79` 의 함수 본문과도(끝 빈 줄 제외) 동일하다.
   세 파일 모두 아직 **커밋되지 않은 신규 파일**이므로 파일 삭제는 이력 되돌림이 아니다.

### 운영 Supabase 적용 상태 (읽기 전용 조회, 2026-09-05)

| 객체 | 운영 존재 | 판정 |
|---|---|---|
| `recruitment_fee_agreements`(090000:13) | 있음, 2행, 컬럼 일치 | **090000 적용됨** |
| `invoice_settlement_details`(090000:106) | 있음, 1행 | **090000 적용됨** |
| RPC `store_invoice_placement_set`(090000:158) | 있음(PGRST202 힌트가 이름을 지목) | **090000 적용됨** |
| `revenue_invoices.contract_version`(20260902090000:83) | 없음(42703) | 20260902090000 미적용 |
| `client_billing_statements.contract_version`(:87) | 없음(42703) | 20260902090000 미적용 |
| `invoice_business_contract_versions`(:23) | 없음(PGRST205) | 20260902090000 미적용 |
| `invoice_delivery_receipts`(:92) | 없음(PGRST205) | 20260902090000 미적용 |
| RPC `record_invoice_delivery`(:391) | 없음(PGRST202) | 20260902090000 미적용 |
| `revenue_invoices` 업무키 중복 | 20행 / 중복 그룹 0 / fee_agreement_id null 18행 | 업무키 제약 적용 가능 |

**확인 불가**: 운영의 `reject_overlapping_fee_agreements()` 실제 본문과 owner RLS 정책의
현재 cmd — 읽기 전용 PostgREST 로는 함수 소스도 `pg_policies` 도 읽을 수 없다.
따라서 100000·103000 의 운영 적용 여부는 미확인이며 부채로 남긴다. 새 forward-only
마이그레이션이 두 경우 모두에서 올바른 끝 상태로 수렴시키는 것이 이 부채의 완화책이다.

## 근본 원인

1. 멱등 키를 **문서 식별자**(사람이 정하는 번호)로 잡고 **업무 식별자**(성사 사실)로
   잡지 않았다. 번호는 바꿀 수 있으므로 중복 청구를 막지 못한다.
2. 원격 성공의 정의가 "응답이 payload 와 일치한다"이다. 응답은 쓰기 성공의 증거가 아니다.
3. 검사 장치가 **문자열 존재**를 본다. 문자열은 남겨 둔 채 결과만 덮어쓰면 통과한다.
   `hooks/pre-push:87-90` 이 이미 "문자열 파싱은 규칙 하나 늘릴 때마다 우회가 하나 는다"고
   적어 두었다.
4. 이미 운영에 적용된 마이그레이션을 파일에서 직접 고치는 습관이 있었다.

## 계약 (입출력 모양 먼저 · SDD)

### 입력 영역 표 — D-B 원격 저장 재조회

| 입력 | 처리 |
|---|---|
| 재조회 1행 + payload 핵심값 일치 | `sent` 승격 |
| 재조회 0행 | `failed` + `REMOTE_READBACK_MISSING` |
| 재조회 2행 이상 | `failed` + `REMOTE_READBACK_AMBIGUOUS` |
| 재조회 값 불일치 | `failed` + `REMOTE_READBACK_MISMATCH` |
| 재조회 응답이 list 가 아님 | `failed` + `REMOTE_READBACK_INVALID` |
| 재조회 자체가 HTTP·네트워크 실패 | `failed` + 해당 오류 (승격 금지) |
| 그 외 전부 | 명시적 거부 — `sent` 승격 금지 |

### 입력 영역 표 — D-A 업무키

| 입력 | 처리 |
|---|---|
| 같은 문서번호 + 같은 payload_sha256 | `idempotent` (기존 동작 유지) |
| 같은 문서번호 + 다른 payload | `IDEMPOTENCY_CONFLICT` (기존 동작 유지) |
| 같은 업무키 + **다른 문서번호** | `PLACEMENT_DUPLICATE` 로 실패 |
| 업무키 구성값 결측 | 저장 이전 단계에서 이미 거부됨 |
| 그 외 전부 | 명시적 거부 |

업무키 = `(tenant_id, client_name, candidate_name, start_date, position_name,
fee_agreement_id, supply_amount)` — 프롬프트의 "tenant·고객사·입사자·입사일·포지션·
수수료 계약·청구 금액"을 그대로 옮겼다.

### 결정 목록 (프롬프트가 이미 확정한 것)

- 업무키 위반은 조용한 수렴이 아니라 **명확한 오류**로 실패시킨다. 수렴은 두 번째
  인보이스를 삼켜 버린다.
- BLOCKED 는 초록이 아니다. 종료값 0 이 아니며 `VERDICT: BLOCKED` 로 구분만 한다.
  (유예를 기본 처리로 삼지 않는다.)

## 인수 기준 (EARS · 단위 1개 = 검증 1개)

- **AC-A** 같은 성사 건을 다른 인보이스 번호로 두 번 저장하면 `PLACEMENT_DUPLICATE` 로
  실패해야 한다. 검증: `python3 -m unittest discover -s tools/invoice/tests -v` +
  PostgreSQL 시험의 unique index 검사.
- **AC-B** 원격 응답이 payload 와 일치해도 재조회에서 행을 찾지 못하면 outbox 를
  `sent` 로 승격하지 않아야 한다.
- **AC-C** 격리 사본에서 invoice unittest 를 실제로 깨뜨리면 `check-invoice-gate.py` 가
  종료값 0 을 내면 안 된다 — 인수 스크립트가 끝에서 `VERDICT: PASS` 를 덮어써도 마찬가지다.
- **AC-C2** CI 워크플로 invoice 스텝 run 블록에 `exit 0` 을 넣으면, 게이트가 등록된
  명령이 실제로 호출되지 않았음을 관측해 실패해야 한다.
- **AC-D** `storage_common.py` 의 CONTRACT_ERROR 제거 + `storage-v1.json` SHA 드리프트
  조합에서 시험이 실패해야 한다.
- **AC-E** `_print_outbox_state` 의 숫자를 상수로 되돌리면 시험이 실패해야 한다.
- **AC-F** 마이그레이션은 forward-only 다. 운영에 적용된 090000 의 동작 변경은 새
  마이그레이션으로만 도달한다.
- **AC-G** CI 한 번에 PostgreSQL 클러스터가 두 번 생기지 않는다.
- **AC-H** 필수 도구·환경 부재는 `VERDICT: BLOCKED`, 시험 실패는 `VERDICT: FAIL` 이며
  둘 다 종료값 0 이 아니다.
- **AC-I** CI 러너에서 PostgreSQL 시험이 실제로 실행된다(초록 로그로 증명).

### counter-AC (통과하면 안 되는 것)

- 정상 저장·정상 동기화는 계속 통과해야 한다(과잉 차단 금지).
- 같은 문서번호 + 같은 payload 재시도는 계속 `idempotent` 여야 한다.
- 손대지 않은 워크플로·인수 스크립트는 게이트를 통과해야 한다.

## 게이트 계획 (WU)

| WU | 내용 | 등급 | 검증 |
|---|---|---|---|
| WU-0 | 시험 파일 분할 + 문서 정본 정리 | L1 | unittest 40건 유지 |
| WU-1 | D-A 업무키 | L2 | AC-A |
| WU-2 | D-B 저장 재조회 | L3 | AC-B |
| WU-3 | D-C 위조 방어 | L3 | AC-C, AC-C2 |
| WU-4 | D-D 계약 드리프트 변이 잠금 | L2 | AC-D |
| WU-5 | D-E outbox 출력 변이 잠금 | L2 | AC-E |
| WU-6 | D-F·D-H 마이그레이션 forward-only + BLOCKED 분리 | L3 | AC-F, AC-H |
| WU-7 | D-G·D-I CI PostgreSQL 단일화·가용성 | L3 | AC-G, AC-I |

## 적대 검증 정조준

- D-C 는 "게이트가 자기를 검사한다"는 순환이 있다. V1 은 **게이트를 무력화한 뒤에도
  CI 가 초록인 경로**를 찾아야 한다.
- D-B 재조회는 같은 응답을 두 번 세는 것으로 위조할 수 있다. V1 은 재조회가 원격 상태를
  실제로 다시 읽는지 공격해야 한다.
- D-A 는 SQLite 만 막고 PostgreSQL 을 안 막으면 반쪽이다.

## 비범위

- 새 제품 기능, 새 outbox 상태값·큐·재시도 모델, 새 계약 버전 체계, 새 동시성 방어,
  SQLite 미러 전면 리팩터링, 실제 Gmail 발송, 운영 Supabase 쓰기.
- invoice 밖의 게이트 일반화.

## 롤백 절차 (L3)

- 코드: 병합 전이다. 브랜치 폐기 또는 `git revert` 로 되돌린다.
- DB: 새 마이그레이션은 운영에 적용하지 않는다. 적용 후 되돌림이 필요하면
  `drop index if exists` 만으로 충분하다(파괴적 변경 없음).
- 영향 반경: `tools/invoice/**`, `scripts/verify/check-invoice-gate.py`,
  `scripts/acceptance-invoice.sh`, `.github/workflows/verify.yml` 의 invoice 스텝,
  `supabase/migrations/` 신규 1개.

## 배포 후 관측 항목 (L3)

- `invoice_sync_outbox.last_error` 가 `REMOTE_READBACK_*` 인 행 → 원격 응답과 실제
  저장이 어긋난 것. 즉시 확인 대상.
- `PLACEMENT_DUPLICATE` 오류 → 같은 성사 건을 두 번 청구하려 한 것.

## 적대 검증 로그

(후기록)
