# Invoice 저장 정본

최종 갱신: 2026-09-02
업무 정본: `docs/sot/invoice.md`
기계 계약: `contracts/invoice/storage-v1.json` (`schema_version: 1.2`)
DB 마이그레이션: `supabase/migrations/20260901090000_invoice_fee_agreements_and_storage.sql`부터 `supabase/migrations/20260902090000_invoice_runtime_integrity.sql`까지의 Invoice 전진 마이그레이션

## 목적

인보이스, 고객사·포지션별 수수료 계약, 내부 정산 내역을 V4에서 사용하던 Supabase 원장에 보존하고 동일 데이터를 로컬 SQLite에도 기록한다. Supabase가 운영 정본이고 SQLite는 오프라인 미러와 재전송 큐다. SQLite 저장 성공을 Supabase 저장 성공으로 보고하지 않는다.

## 기존 V4 원장 재사용

V4의 다음 테이블을 버리지 않고 확장한다.

- `revenue_invoices`: 매출·청구 금액 원장
- `commission_payouts`: Account Manager, Coworker, 회사 배분 원장
- `client_billing_statements`: 고객 발송 청구 문서 원장

기존 `revenue_invoices.commission_rate default 0.20`은 과거 호환용일 뿐 신규 Invoice의 수수료 정본이 아니다. 신규 저장은 반드시 `recruitment_fee_agreements`의 계약을 참조한다. 포지션 이름과 문서 식별자 등 기존에 없던 필드는 nullable로 추가해 과거 행을 훼손하지 않는다.

## 수수료 계약 정본

`recruitment_fee_agreements`의 유일한 업무 키는 다음 조합이다.

- `tenant_id`
- 정규화된 `client_key`
- 정규화된 `position_key`
- 겹치지 않는 `effective_from`~`effective_to`

수수료율은 0보다 크고 1 이하인 비율로 저장한다. 신규 문서를 만들 때 입사일을 적용일로 하여 Supabase 활성 계약이 정확히 한 건이어야 한다. 온라인 기본 경로는 Supabase를 먼저 조회하고 확인된 행을 SQLite에 미러링한다. 로컬에 값이 있어도 원격 0건, 중복, 고객사·포지션 불일치, 입력 수수료율 불일치이면 실패한다. 기본 20%나 가장 최근 계약으로 대체하지 않는다.

PostgreSQL의 부분 제외 제약은 같은 tenant·고객사·포지션에서 활성 유효기간이 겹치는 두 행을 커밋 시점에 거부한다. 애플리케이션 조회나 트리거만으로 동시 삽입을 막았다고 간주하지 않는다.

계약 참조가 생성된 뒤 고객사·포지션·수수료율·유효기간·근거를 덮어쓰지 않는다. 조건이 바뀌면 기존 계약을 `inactive`로 전환하고 새 `agreement_ref`로 새 행을 만든다. 같은 참조에 다른 값을 재전송하면 `FEE_AGREEMENT_IMMUTABLE` 또는 `IDEMPOTENCY_CONFLICT`로 실패한다.

## 한 성사 건의 원자적 저장

한 성사 건은 다음을 한 트랜잭션으로 저장한다.

1. 수수료 계약 검증
2. `revenue_invoices` 인보이스 원장
3. `client_billing_statements` 고객 발송 문서
4. 내부 정산이 있으면 `commission_payouts` 3행과 `invoice_settlement_details` 1행

인보이스와 정산서가 함께 있으면 인보이스 번호, 고객사, 입사자, 입사일, 포지션, 연봉, 수수료율, 수수료 계약 참조, 청구 금액이 모두 같아야 한다. 회사 배분, 참여자 배분 합계, 원천징수, 납부 기한, 입금 정보는 `invoice_business_contract_versions`의 버전과 SHA-256에 고정된 불변 JSON 계약 스냅샷을 DB 함수가 다시 검증한다. 새 코드는 현재 JSON과 같은 스냅샷만 생성하고, 이미 큐에 들어간 문서·전달 증빙은 이후 활성 버전이 바뀌어도 원래 스냅샷으로 재시도한다. 존재하지 않거나 SHA-256이 다른 스냅샷은 저장하지 않는다.

멱등 키는 두 층이다. **업무키**는 `tenant_id`, 고객사, 입사자, 입사일, 포지션, 수수료 계약, 청구 금액이며 같은 성사 건을 문서 번호만 바꿔 다시 청구하면 `PLACEMENT_DUPLICATE`로 실패한다. 문서 번호는 사람이 정하는 값이므로 그 자체로는 업무키가 될 수 없다. **문서키**인 `document_number`와 `settlement_number`는 재시도 식별자다 — 같은 번호와 같은 `payload_sha256` 재시도는 기존 성공을 반환하고, 같은 번호에 다른 payload는 `IDEMPOTENCY_CONFLICT`로 실패한다. 업무키는 SQLite `revenue_invoices_placement_uniq` 와 PostgreSQL 같은 이름의 부분 unique index 양쪽에서 DB 제약으로 강제하며, 저장 RPC 도 저장 전에 같은 조건을 직접 확인한다.

## SQLite 미러와 동기화

기본 로컬 경로는 `data/invoice-ledger.sqlite3`이며 git에 포함하지 않는다. 온라인 로컬 저장은 한 SQLite 트랜잭션으로 원장과 `invoice_sync_outbox`를 함께 기록한다. `--offline`은 SQLite 계약으로 검수용 draft를 만드는 명시적 비상 경로일 뿐 최종 문서를 만들거나 원격 문서 outbox를 생성하지 않는다. 오프라인 draft 번호를 최종 번호로 재사용하지 않는다.

- `pending`: Supabase에 아직 확인되지 않음
- `sent`: 작업별 응답 검증이 요구하는 UUID와 참조값을 Supabase가 반환함
- `failed`: 마지막 동기화가 실패했으며 오류 요약과 시도 횟수를 보관함

빈 body, `{}`, 잘못된 ID뿐 아니라 다른 tenant·문서 번호·계약 참조·계약 버전·PDF SHA-256·수신자·제목·Gmail 메시지 ID를 돌려준 2xx도 실패다. outbox는 수수료 계약(10), 문서 세트(20), 전달 영수증(30) 순서로 처리한다. 수수료 계약을 이번 로컬 큐에서 생성한 경우 그 작업이 `sent`여야 문서 RPC를 호출한다. 이미 Supabase에 있던 계약은 직전 권위 조회와 SQLite mirror receipt로 증명되므로 별도 upsert 행이 없어도 문서 RPC를 호출할 수 있다. 전달 영수증은 대응하는 문서 outbox의 `sent` 증거가 반드시 있어야 하며, 행 자체가 없거나 `pending`·`failed`이면 RPC를 호출하지 않는다. 네트워크 실패 후 자동으로 메일을 보내거나 원격 성공으로 승격하지 않는다.

문서와 전달 payload는 `payload_canonical`과 그 UTF-8 SHA-256인 `payload_sha256`을 함께 보낸다. PostgreSQL은 canonical 문자열을 다시 JSON으로 읽어 실제 payload와 같은지 확인하고 SHA-256을 직접 재계산한 뒤에만 저장한다. SQLite 영수증, outbox, Supabase 행과 RPC 응답은 이 같은 hash를 사용한다. 비밀키는 DB·JSON·로그·메타데이터에 저장하지 않고 실행 환경에서만 읽으며, 이름이 모호한 `SUPABASE_KEY`는 service-role 자격으로 받아들이지 않는다.

## Gmail 전달 영수증

메일 발송 성공 응답만으로 원장 상태를 `sent`로 바꾸지 않는다. Gmail 메시지를 ID로 다시 읽어 수신자와 PDF 첨부를 확인한 뒤 `record-delivery`에 전달 증빙을 넣는다. 로컬 영수증 기록 시 청구서는 `delivery_confirmed_local`이고, Supabase `record_invoice_delivery`가 같은 문서·PDF·문서 생성 당시 계약 스냅샷·수신자·메시지 ID를 확인한 뒤에만 로컬과 원격 청구서를 `sent`로 바꾼다.

Gmail 읽기가 성공하고 Supabase 기록이 실패하면 메일은 이미 발송된 사실로 남는다. 이때 메일을 다시 보내지 않고 전달 outbox만 재시도한다.

## 상태와 오류

- `SQLITE_STORED`: 로컬 트랜잭션만 성공
- `SUPABASE_SYNCED`: 원격 RPC 성공을 확인하고 outbox를 `sent`로 갱신
- `SUPABASE_PENDING`: 원격 호출을 하지 않았거나 확인하지 못함
- `delivery_confirmed_local`: Gmail 읽기와 로컬 영수증만 확인됐고 Supabase 전달 영수증은 미확인
- `REMOTE_CONFIRMATION_ERROR`: 2xx 응답이 작업별 성공 증거를 충족하지 못함
- `OFFLINE_FINAL_FORBIDDEN`: SQLite 전용 값으로 최종 문서를 만들려 함
- `DELIVERY_NOT_CONFIRMED`: Gmail 읽기 증빙이 없음
- `DELIVERY_ATTACHMENT_MISMATCH`: Gmail 첨부 SHA-256과 저장 문서가 다름
- `FEE_AGREEMENT_NOT_FOUND`: 활성 계약 없음
- `FEE_AGREEMENT_CONFLICT`: 활성 계약 중복
- `DOCUMENT_PAIR_MISMATCH`: 인보이스와 정산서 불일치
- `IDEMPOTENCY_CONFLICT`: 같은 문서 번호의 payload가 달라짐

로그와 사용자 보고는 SQLite와 Supabase 상태를 각각 표시한다. 둘 중 하나만 성공했는데 “DB 저장 완료”라고 뭉뚱그리지 않는다.

## 변경 절차

테이블·RPC·키·동기화 상태를 바꾸면 이 문서, `storage-v1.json`, Supabase 마이그레이션, SQLite 스키마, 저장 회귀시험을 같은 변경에서 갱신한다. V4의 전체 마이그레이션 상태가 불일치하므로 이 기능과 무관한 과거 로컬 마이그레이션을 함께 push하지 않는다.
