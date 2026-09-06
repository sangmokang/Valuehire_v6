---
name: invoice
description: "Create and persist ValueConnect recruitment-fee invoice PDFs and internal placement settlement PDFs, resolve customer+position fee agreements without defaults, calculate billing, allocation, withholding and RPS status, visually verify the document, and send only after the final approval gate. Use for 채용 수수료 청구서, 인보이스 PDF, 계산서 발행 정산 내역, 성사 배분, 코웍자 배분, RPS 공제·미공제, DB 저장, or approved email delivery; do not use for statutory tax invoices."
---

# Invoice

Create business-ready, one-page recruitment fee invoices and internal placement settlement statements without letting the model invent amounts, participants, deductions, payment terms, or issuer details.

## Load the contract

Before handling invoice data:

1. Resolve the current repository root.
2. Read `docs/sot/invoice.md` completely.
3. Read `docs/sot/invoice-storage.md` and `contracts/invoice/storage-v1.json` completely.
4. For an external invoice, read `contracts/invoice/invoice-v1.json` and use only `tools/invoice/generate_invoice.py` for calculation and rendering.
5. For an internal settlement, read `contracts/invoice/deduction-v1.json` and use only `tools/invoice/generate_deduction.py` for allocation, withholding, RPS status, and rendering.

Do not supply business constants from the prompt or recompute the fee mentally. The renderers read JSON contracts and persistence verifies the matching business-contract version and SHA-256. If the SOT, JSON contracts, database snapshot, and script behavior disagree, stop with `CONTRACT_ERROR`; do not create a final PDF or email.

## Prepare one input per hire

Required user facts are the client company, candidate, start date, position, and agreed annual salary. Resolve the exact fee agreement from the ledger before creating the input. A review invoice also needs an issue date and a draft invoice number.

- Run `python3 tools/invoice/store_invoice_set.py resolve-fee --company <client> --position <position> --on <start-date>`. This is a Supabase-first lookup; use its `fee_percent`, `fee_agreement_ref`, and `fee_source: SUPABASE` together.
- There is no default fee. Never reuse 20% or another customer's rate when the lookup fails. Stop with `FEE_AGREEMENT_NOT_FOUND` or `FEE_AGREEMENT_CONFLICT`.
- If a new agreement must be registered, run `register-agreement`, then `sync`, and only proceed after the operation-specific Supabase confirmation succeeds. A local pending agreement cannot authorize a final document.
- Convert a salary stated in 만원 into `annual_salary_manwon` without multiplying it yourself.
- Use `annual_salary_krw` only when the user supplied a won amount.
- Never add `fee_amount`, `requested_fee`, `total_amount`, or `due_date`; the renderer owns those values.
- For a review batch without invoice numbers, use `DRAFT-YYYYMMDD-001`, `002`, and so on. Do not present those as final numbering.
- Set `draft: true` until every finalization gate in the SOT is resolved.
- Keep real inputs under `artifacts/invoices/` with non-identifying filenames such as `invoice-review-001.json`. Do not put candidate names in tracked files or filenames.

Input shape:

```json
{
  "invoice_number": "DRAFT-YYYYMMDD-001",
  "issue_date": "YYYY-MM-DD",
  "company_name": "고객사",
  "candidate_name": "입사자",
  "start_date": "YYYY-MM-DD",
  "position": "직책",
  "annual_salary_manwon": 6000,
  "fee_percent": "계약 조회값",
  "fee_agreement_ref": "계약 조회 참조",
  "draft": true
}
```

## Generate and inspect

Run from the repository root:

```bash
python3 tools/invoice/generate_invoice.py \
  --input artifacts/invoices/invoice-review-001.json \
  --output artifacts/invoices/invoice-review-001.pdf
```

A successful render must print `RENDER_VERDICT: PASS`, a nonzero `CHECKED` count derived from the completed outputs, the computed fee, total, due date, and PDF SHA-256. A final (`draft: false`) render must also print `BUSINESS_STATUS: FEE_AUTHORITY_VERIFIED`; the renderer performs its own live Supabase agreement check and fails closed without service-role access. A draft prints `UNVERIFIED_DRAFT`. Render success alone is not database or delivery success. The command creates exactly three non-empty files: PDF, HTML, and metadata. Any missing renderer, invalid input, authority failure, partial output, multi-page PDF, or nonzero exit is a failure.

Render the actual PDF page to an image with an available local PDF renderer, then inspect it before reporting success. Check all required labels and values, Korean glyphs, A4 single-page fit, alignment, clipped text, overlap, bank, account number and account-holder readability, total emphasis, and the review watermark when applicable. HTML-only inspection is insufficient.

Report the calculated fee and due date from stdout or metadata, never from recollection. For multiple hires, generate and inspect each PDF independently.

## Create a calculation issuance settlement

Use this document for internal placement allocation, not customer billing or a statutory tax invoice.

- Supply the same `invoice_number`, `fee_agreement_ref`, salary, and fee percentage used by the paired invoice; never supply a precomputed invoice amount or allocation amount.
- Company share, allocation total, and participant withholding are contract-owned. The participant percentages must fill the contract-defined remainder; a solo placement gives the entire participant remainder to one person and zero to the other.
- The renderer calculates each gross allocation, withholding, and after-tax payment. Do not recompute those values in the prompt.
- Set `rps_status` explicitly: `none` means no RPS, `deferred` means no deduction this Term and a later deduction, `deducted` means deduct now, and `pending` is draft-only. Never infer the status from a zero amount alone.
- `none` and `deferred` require zero amount and no bearer. `deducted` requires both an exact positive won amount and a bearer. A final `deferred` document displays `이번 Term에서 미공제, 추후 공제 예정` and uses `이번 Term 세후 지급액`.
- The visible document title must come from the contract as `계산서 발행 정산 내역`; never render `DEDUCTION` as the PDF title or section heading.
- Never reuse the candidate name as a consultant name. Missing participant names or RPS decisions require `draft: true`, visible `미입력` fields, and no email mutation.
- Generate with `python3 tools/invoice/generate_deduction.py --input <artifact-json> --output <artifact-pdf>` and apply the same actual-PDF visual inspection rules.

## Persist the document set

After generation and visual inspection, resolve the Supabase agreement and store the agreement-backed invoice and optional settlement in the local transaction before any email mutation:

```bash
python3 tools/invoice/store_invoice_set.py store \
  --invoice-input <invoice-json> --invoice-pdf <invoice-pdf> \
  --invoice-metadata <invoice-metadata-json> \
  --settlement-input <settlement-json> --settlement-pdf <settlement-pdf> \
  --settlement-metadata <settlement-metadata-json>
```

Omit all three settlement arguments for an invoice-only record. The command must validate the PDF hashes, resolve exactly one active Supabase customer+position agreement, mirror it, and compare every paired document field before writing. `SQLITE_STORED` means only the local transaction succeeded; report `SUPABASE_PENDING` until `python3 tools/invoice/store_invoice_set.py sync` returns `SUPABASE_SYNCED` with no failures. Empty responses, malformed IDs, or mismatched references remain failures even after HTTP 2xx. Never call SQLite pending data a completed remote save.

Use `--offline` only for a review draft when Supabase is unavailable. It must return `fee_source: SQLITE_OFFLINE`, cannot create a final document, does not enqueue the document RPC, and its draft document number must not be reused as the final number.

The sync command uses a Supabase service-role credential from the execution environment. Never print, copy, or save that credential. Do not run the V4 repository's full migration backlog as part of this workflow; only the Invoice migrations named in the storage SOT are in scope.

## Finalize and send

PDF generation and Gmail delivery are separate states. A review request never authorizes sending.

The Python renderer has no mail transport. The following delivery gates are workflow obligations that you must enforce with the connected Gmail tool; do not describe them as Python-enforced guarantees.

Do not call any Gmail mutation when any of these is true:

- `draft` is true;
- the tax policy is not the contract-confirmed value;
- `delivery.send_enabled` is false;
- visual verification did not pass;
- the connected Gmail tool is unavailable;
- the user has not approved the exact final delivery summary.

Immediately before sending, show one concise approval summary containing the recipient read from the contract, subject, document number, company, candidate, calculated monetary result, relevant due date or payout values, PDF path, and full PDF SHA-256. Approval must refer to that concrete summary.

Before the send call, search Sent mail for the full SHA-256 included in prior invoice bodies. If found, stop as a possible duplicate and require a new explicit resend approval. Do not retry a failed send automatically.

After approval, use the connected Gmail tool to send the PDF as a binary attachment. Include the full PDF SHA-256 in the message body for duplicate detection. Do not substitute a local path, cloud link, HTML file, or metadata file for the PDF attachment. If no Gmail connector is available, return `BLOCKED`; do not request SMTP credentials or create a new mail transport.

Never print, quote, or return the PDF's Base64/Base64URL attachment payload in a user-visible update or final response. After a send call, report only delivery metadata such as message identifier, recipient, subject, attachment filename, and verification result.

After sending, read back the Gmail result by its returned message identifier and verify recipient plus the intended PDF attachment. Build a delivery JSON containing the document number, recipient, subject, Gmail message ID, timezone-aware sent timestamp, PDF SHA-256, and `readback_confirmed: true`, then run:

```bash
python3 tools/invoice/store_invoice_set.py record-delivery --input <delivery-json>
python3 tools/invoice/store_invoice_set.py sync
```

The first command atomically stores the local receipt and marks the local statement `delivery_confirmed_local`, not `sent`. Report plain `SENT` only after the delivery RPC returns the statement ID, delivery receipt ID, and all matching aggregate identity fields, at which point sync promotes the local statement to `sent`. If Gmail readback succeeded but receipt sync failed, report `GMAIL_SENT / DELIVERY_RECEIPT_PENDING` and retry only the unchanged outbox payload; never resend the email. Contract rotation must not rewrite or block that historical proof. If Gmail readback itself fails, report `FAIL` or `BLOCKED` and preserve the PDF for review.

## Report states

Keep these outcomes distinct:

- `PASS / REVIEW_READY`: PDF generation and visual inspection passed; no email was sent.
- `BLOCKED`: a required owner decision, approval, Gmail connection, or readback is unavailable.
- `FAIL`: input, contract, calculation, rendering, visual inspection, or delivery violated the contract.
- `GMAIL_SENT / DELIVERY_RECEIPT_PENDING`: Gmail readback passed but the Supabase delivery receipt is not confirmed; do not resend.
- `SENT`: Gmail readback and the Supabase delivery receipt both confirmed the intended recipient, PDF SHA-256, and message ID.
- `SQLITE_STORED / SUPABASE_PENDING`: local ledger and outbox succeeded; remote storage is not yet confirmed.
- `SUPABASE_SYNCED`: the Supabase RPC confirmed the fee agreement and document set were stored.

Always link the review PDF and PNG preview when the platform supports local file links. State unresolved business decisions before inviting final delivery approval.
