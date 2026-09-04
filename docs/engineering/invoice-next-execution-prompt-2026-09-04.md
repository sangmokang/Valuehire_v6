# Invoice 다음 실행 프롬프트 — 2026-09-04

아래 내용을 다음 Codex 또는 Claude 세션의 첫 요청으로 사용한다.

```text
ValueHire v6의 Invoice 기능을 로컬 완료 상태에서 안전하게 통합하고, 권한이 확인되는 범위까지만 운영 반영하라. 질문으로 넘길 수 있는 일반적인 로컬 작업은 직접 수행하되 push·PR 생성/병합, 운영 Supabase 변경, Gmail 발송은 현재 요청에 그 외부 효과가 명시적으로 포함된 경우에만 수행하라.

현재 기준
- 저장소: /Users/kangsangmo/Desktop/Valuehire_v6
- 작업트리: /Users/kangsangmo/Desktop/Valuehire_v6/worktrees/invoice-skill
- 브랜치: task/invoice-skill-20260901
- 2026-09-04 확인 당시 origin/main보다 2커밋 앞, 뒤처짐 0이었다. 다시 측정해서 최신 상태만 사용하라.
- Invoice의 추가 보강분은 수정·신규 파일로 작업트리에 남아 있다. main에는 아직 통합되지 않았다.
- main 작업트리의 Invoice와 무관한 미추적 파일을 건드리거나 함께 커밋하지 마라.
- 2026-09-04 재검증은 단위 테스트 40개, 임시 PostgreSQL 마이그레이션·동시성·멱등성 검사, Invoice 인수 게이트가 모두 PASS였다. 과거 결과를 재사용하지 말고 현재 변경에서 다시 실행하라.
- 운영 Supabase 적용과 Gmail 발송은 아직 수행되지 않았다.
- 당시 로컬 환경에는 SUPABASE_URL만 있었고 service-role 키와 supabase/config.toml은 없었다. 실제 값을 출력하거나 저장소에 기록하지 마라.

먼저 읽을 정본
1. docs/sot/invoice.md
2. docs/sot/invoice-storage.md
3. contracts/invoice/invoice-v1.json
4. contracts/invoice/deduction-v1.json
5. contracts/invoice/storage-v1.json
6. .codex/skills/invoice/SKILL.md 또는 .claude/skills/invoice/SKILL.md
7. docs/engineering/invoice-final-implementation-prompt-2026-09-02.md

작업 1 — 로컬 변경 봉합
1. 지정 Invoice 작업트리에서 git status, diff, untracked 파일을 읽고 Invoice 범위와 무관한 변경을 분리하라.
2. 아래 검증을 모두 새로 실행하라.
   - python3 -m unittest discover -s tools/invoice/tests -v
   - bash tools/invoice/tests/test_postgres_integrity.sh
   - python3 scripts/verify/check-invoice-gate.py
   - bash scripts/verify/run-acceptance.sh scripts/acceptance-invoice.sh
   - bash scripts/verify/run-acceptance.sh scripts/acceptance-semantic-mutations.sh
   - bash scripts/verify/run-acceptance.sh scripts/acceptance-ci-step-integrity.sh
   - bash scripts/verify/run-acceptance.sh scripts/acceptance-verify-ac-m.sh
   - git diff --check
3. 하나라도 실패하면 관련 최소 시험으로 원인을 고치고 전체 Invoice 인수 게이트를 다시 실행하라.
4. Codex와 Claude Invoice SKILL.md 및 agents/openai.yaml이 각각 바이트 동일한지 확인하라.
5. Invoice 범위 파일만 명시적으로 stage하라. git add . 또는 무관한 사용자 파일의 포함은 금지한다.
6. diff와 staged diff를 다시 읽은 뒤 Lore Commit Protocol 형식으로 커밋하라. 커밋 후 작업트리 상태와 main 대비 ahead/behind를 보고하라.

작업 2 — 저장소 통합
- 최신 main과 충돌 여부를 확인하고, 충돌이 없으며 현재 요청에 push/PR 권한이 있으면 branch를 push하고 PR 검증을 통과시켜 main에 통합하라.
- 권한이 없으면 READY_TO_PUSH로 중단하고 정확한 브랜치·커밋·검증 결과를 남겨라. push나 PR을 했다고 추정해서 보고하지 마라.

작업 3 — 운영 Supabase 준비와 반영
1. V4/V5에서 사용한 기존 Supabase 프로젝트 연결 정보와 스키마 구조를 읽기 전용으로 찾되 비밀값은 출력하지 마라.
2. 운영 프로젝트, 백업/복구 경로, 적용 대상 migration 목록, 현재 적용 이력을 검증하라.
3. 다음 네 migration을 순서대로 적용할 계획을 만들고 중복 적용·기존 데이터 영향·RLS·SECURITY DEFINER 권한을 점검하라.
   - supabase/migrations/20260901090000_invoice_fee_agreements_and_storage.sql
   - supabase/migrations/20260901100000_invoice_fee_agreement_immutability.sql
   - supabase/migrations/20260901103000_invoice_fee_agreement_idempotent_upsert.sql
   - supabase/migrations/20260902090000_invoice_runtime_integrity.sql
4. 현재 요청에 운영 변경 권한과 자격증명이 모두 있을 때만 적용하라. 없으면 SUPABASE_DEPLOY_BLOCKED로 중단하라.
5. 적용 뒤 활성 business contract version/SHA-256, 테이블·RPC·RLS, 동시 수수료 계약 충돌, 문서·전달 멱등성을 운영 환경에서 비파괴 smoke test로 확인하라.

작업 4 — 고객사·포지션별 수수료 계약
- 기본 수수료율을 만들거나 재사용하지 마라.
- 아래 두 건은 과거 사용자가 제시한 금액상 모두 20%가 계산되지만, 각각 별도의 Supabase 계약 행과 agreement_ref·유효기간·source_reference가 필요하다.
  1. 토트 / AI Engineer / 최다니엘 / 연봉 60,000,000원 / 청구 예상 12,000,000원 / 입사일 2026-09-01
  2. 토트 / 전장 엔지니어 / 김의현 / 연봉 40,000,000원 / 청구 예상 8,000,000원 / 입사일 2026-09-01
- 운영 계약 행이 이미 있으면 정확히 한 건인지와 적용일을 확인하고 사용하라. 없으면 현재 요청에 등록 권한과 계약 근거가 있을 때만 별도 agreement_ref로 등록하라. 예시 금액을 전역 20% 기본값으로 바꾸지 마라.

작업 5 — PDF 세트 생성과 검수
- 인보이스 번호와 발행일을 임의로 만들지 마라. 현재 요청 또는 운영 번호 정책에서 확정된 값을 사용하라.
- 납부기한은 입사일로부터 달력일 14일인 2026-09-15다.
- 부가가치세는 비대상이고 총 청구액은 각각 12,000,000원, 8,000,000원이어야 한다.
- 최다니엘 정산 입력은 Account Manager Tim 강상모 45%, Coworker Dragon 김충수 30%, 회사 25%, RPS 선결제 0원이며 표시 문구는 “이번 Term에서 미공제, 추후 공제 예정”이다.
- 김의현의 내부 정산 참여자·배분율·RPS 정보는 제공된 것으로 추정하지 마라. 값이 없으면 그의 정산서만 BLOCKED_INPUT으로 두고 인보이스 상태와 구분하라.
- 최종 PDF는 live Supabase 수수료 계약 검증 후에만 생성하고 FEE_AUTHORITY_VERIFIED를 확인하라.
- PDF와 HTML·metadata의 SHA-256을 대조하고, A4 1페이지를 실제 이미지로 렌더링하여 잘림·겹침·한글 깨짐·표 정렬·금액·계좌·문구를 육안 검수하라.
- PDF 또는 Base64 원문을 대화창에 출력하지 마라.

작업 6 — Gmail 발송과 전달 영수증
- 기본 수신자는 sangmokang@valueconnect.kr다.
- 실제 발송 직전에 수신자, 제목, 첨부 파일명과 SHA-256, 총액을 한 번에 요약하고 현재 요청의 발송 권한을 확인하라.
- 승인된 파일만 한 번 발송하고 Gmail 메시지 ID로 Sent 메일을 다시 읽어 수신자와 첨부 SHA-256을 검증하라.
- 로컬 record-delivery 성공만으로 SENT라고 하지 마라. 대응 문서 outbox가 Supabase sent이고 record_invoice_delivery 응답까지 일치해야 최종 SENT다.
- Gmail은 성공했지만 Supabase 영수증 sync가 실패하면 재발송하지 말고 GMAIL_SENT / DELIVERY_RECEIPT_PENDING으로 남겨 동일 outbox payload만 재시도하라.

최종 보고
- 변경·커밋·push/PR/main 통합·Supabase 적용·계약 등록·PDF 생성·Gmail 발송·전달 영수증을 각각 별도 상태로 보고하라.
- 실행하지 않은 외부 효과는 NOT_RUN 또는 BLOCKED로 명시하라.
- 성공 주장은 커밋 ID, 테스트 종료값, Supabase 응답 식별자, PDF SHA-256, Gmail 메시지 ID 같은 실제 증거가 있을 때만 하라.
- 로컬 커밋 완료 후 외부 권한이 없으면 READY_TO_PUSH에서 멈춘다. 운영 DB 반영 후 메일 권한이 없으면 REVIEW_READY 또는 SUPABASE_SYNCED에서 멈춘다. Gmail 읽기와 Supabase 전달 영수증이 모두 확인된 경우에만 SENT로 종료한다.
```
