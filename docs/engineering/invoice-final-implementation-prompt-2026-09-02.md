# Invoice 최종 구현·검증 프롬프트 — 2026-09-02

## 목표

ValueConnect의 외부 채용 수수료 인보이스와 내부 `계산서 발행 정산 내역`을 한 성사 건으로 묶어 생성·검수·저장하고, 승인된 Gmail 발송 뒤 전달 영수증까지 남긴다. Codex와 Claude는 같은 Invoice 스킬, SOT, JSON 계약, Python 실행기를 사용한다.

완료 조건은 PDF가 만들어지는 것만이 아니다. 고객사·포지션·입사일에 해당하는 Supabase 수수료 계약을 사용하고, DB 저장 응답과 Gmail 읽기 증빙을 각각 확인하며, SQLite pending을 원격 성공이라고 보고하지 않아야 한다.

## 먼저 읽을 정본

1. `docs/sot/invoice.md`
2. `docs/sot/invoice-storage.md`
3. `contracts/invoice/invoice-v1.json`
4. `contracts/invoice/deduction-v1.json`
5. `contracts/invoice/storage-v1.json`
6. `.codex/skills/invoice/SKILL.md` 또는 `.claude/skills/invoice/SKILL.md`

거래 입력, 업무 규칙, 수수료 계약, DB 스냅샷, 로컬 복구 상태, Gmail 전달 사실의 정본을 서로 바꾸어 사용하지 않는다. 불일치는 추정으로 복구하지 말고 명시된 오류로 중단한다.

## 구현 불변조건

- 수수료 기본값은 없다. Supabase에서 tenant·정규화 고객사·정규화 포지션·입사일로 활성 계약을 조회해 정확히 한 건이어야 한다.
- 활성 수수료 계약의 유효기간 중복은 PostgreSQL 부분 제외 제약이 동시 트랜잭션에서도 거부해야 한다.
- 최종 문서 payload는 `fee_source: SUPABASE`여야 한다. SQLite 오프라인 값은 검수용 draft만 허용하고 문서 RPC outbox를 만들지 않는다.
- 최종 렌더러도 Supabase 활성 계약을 직접 재조회한다. `RENDER_VERDICT: PASS`만으로 업무 합격을 뜻하지 않으며 최종본에는 `FEE_AUTHORITY_VERIFIED`가 필요하다.
- 인보이스와 정산서는 번호, 고객사, 입사자, 입사일, 포지션, 연봉, 수수료율, 계약 참조, 청구 금액이 일치해야 한다.
- 계산·계좌·수신자·배분 규칙은 JSON 묶음의 버전·SHA-256과 같은 `invoice_business_contract_versions` 불변 스냅샷으로 DB에서 재검증한다. 이미 큐에 들어간 payload는 활성 버전이 바뀌어도 원래 스냅샷으로 재시도한다.
- payload의 canonical 문자열과 SHA-256을 함께 보내고 PostgreSQL이 JSON 동등성과 hash를 독립 재계산한다.
- 원격 sync는 HTTP 2xx만으로 성공하지 않는다. 작업별 UUID뿐 아니라 tenant, 계약, 문서 번호, PDF SHA-256, 수신자, 제목, Gmail 메시지 ID 등 aggregate 정체성이 payload와 모두 일치해야 outbox를 `sent`로 바꾼다.
- outbox 처리 순서는 수수료 계약, 문서 세트, 전달 영수증이며 선행 작업이 확인되지 않으면 후행 RPC를 호출하지 않는다.
- Gmail은 구체적인 최종 발송 요약 승인 뒤 한 번만 호출한다. 발송 결과를 메시지 ID로 다시 읽어 수신자와 PDF 첨부를 확인한다.
- Gmail 읽기 확인 뒤에만 `record-delivery`를 기록한다. 전달 영수증 sync 실패는 재발송 사유가 아니며 `GMAIL_SENT / DELIVERY_RECEIPT_PENDING`으로 남긴다.
- 로컬 전달 기록은 청구서를 `delivery_confirmed_local`로만 바꾸고, Supabase 전달 영수증까지 확인된 뒤에만 `sent`로 승격한다.
- Base64 또는 PDF 원문을 사용자 메시지에 출력하지 않는다.
- 운영 Supabase migration 적용, Gmail 발송, push·PR·배포는 각각 명시적 권한이 있는 경우에만 수행한다.

## 구현 표면

- 렌더: `tools/invoice/generate_invoice.py`, `tools/invoice/generate_deduction.py`
- 로컬 원장·outbox: `tools/invoice/store_invoice_set.py`, `storage_*.py`
- Supabase 전진 마이그레이션: `supabase/migrations/20260901*.sql`, `20260902090000_invoice_runtime_integrity.sql`
- 전달 영수증: SQLite와 Supabase `invoice_delivery_receipts`, `record_invoice_delivery(jsonb)`
- 플랫폼 스킬: `.codex/skills/invoice`, `.claude/skills/invoice`
- CI: `scripts/acceptance-invoice.sh`, `scripts/verify/check-invoice-gate.py`, `.github/workflows/verify.yml`

## 필수 검증

다음 명령을 현재 변경에서 직접 실행하고 종료값과 출력을 읽는다.

```bash
python3 -m unittest discover -s tools/invoice/tests -v
bash tools/invoice/tests/test_postgres_integrity.sh
python3 scripts/verify/check-invoice-gate.py
bash scripts/verify/run-acceptance.sh scripts/acceptance-invoice.sh
bash scripts/verify/run-acceptance.sh scripts/acceptance-semantic-mutations.sh
bash scripts/verify/run-acceptance.sh scripts/acceptance-ci-step-integrity.sh
bash scripts/verify/run-acceptance.sh scripts/acceptance-verify-ac-m.sh
git diff --check
```

PostgreSQL 검증은 새 임시 클러스터에서 기존 Invoice 마이그레이션과 신규 전진 마이그레이션을 순서대로 적용하고 다음을 증명해야 한다.

1. 겹치는 두 활성 수수료 계약의 동시 삽입 중 하나가 실패한다.
2. DB 활성 업무 스냅샷이 JSON 계약에서 계산한 버전·SHA-256·구성과 같다.
3. 문서 저장 RPC의 최초 호출은 `stored`, 동일 재시도는 `idempotent`이며 수수료 계약 ID를 반환한다.
4. 전달 RPC는 PDF SHA-256과 계약 정체성을 확인하고 최초 `stored`, 동일 재시도 `idempotent`를 반환한다.
5. 계약 활성 버전을 회전해도 이미 보낸 메일의 동일 전달 payload 재시도가 `idempotent`로 성공한다.
6. 거짓 payload SHA-256은 PostgreSQL에서 거부된다.
7. 전달 영수증의 authenticated owner 정책은 읽기 전용이다.

## 판정

- `REVIEW_READY`: PDF 생성·실제 페이지 시각 검수·로컬 저장까지 통과했지만 메일은 보내지 않음
- `SUPABASE_SYNCED`: 작업별 원격 성공 응답을 확인함
- `GMAIL_SENT / DELIVERY_RECEIPT_PENDING`: Gmail 읽기 확인은 됐으나 원격 전달 영수증 미확인
- `SENT`: Gmail 읽기와 Supabase 전달 영수증이 모두 같은 수신자·첨부 SHA-256·메시지 ID를 확인함
- `FAIL`: 계약, 계산, 문서 쌍, 렌더, DB, 응답 증거 중 하나가 위반됨
- `BLOCKED`: 필요한 승인·연결·권한이 없어 외부 효과를 실행할 수 없음

검증 하나라도 실패하면 완료라고 보고하지 않는다. 실패한 경계를 수정한 뒤 관련 최소 시험과 전체 Invoice 인수 검사를 다시 실행한다.
