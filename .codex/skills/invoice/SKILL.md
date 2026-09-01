---
name: invoice
description: "Create ValueConnect recruitment-fee invoice PDFs from hire details, calculate the fee and due date from the repository contract, visually verify the document, and send it through connected Gmail only after the final approval gate. Use for 채용 수수료 청구서, 인보이스 PDF, 입사 수수료 계산, or approved invoice email delivery; do not use for tax invoices or unrelated billing."
---

# Invoice

Create a business-ready, one-page recruitment fee invoice without letting the model invent amounts, payment terms, or issuer details.

## Load the contract

Before handling invoice data:

1. Resolve the current repository root.
2. Read `docs/sot/invoice.md` completely.
3. Read `contracts/invoice/invoice-v1.json` completely.
4. Use only `tools/invoice/generate_invoice.py` for salary normalization, fee calculation, due-date calculation, HTML rendering, and PDF generation.

Do not copy contract constants into a prompt or recompute the fee mentally. If your direct read or validation detects disagreement between the SOT, JSON contract, and script behavior, stop with `CONTRACT_ERROR`; do not create a final PDF or email.

## Prepare one input per hire

Required user facts are the client company, candidate, start date, position, and agreed annual salary. A review invoice also needs an issue date and a draft invoice number.

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

A successful run must print `VERDICT: PASS`, a nonzero `CHECKED` count derived from the completed outputs, the computed fee, total, due date, and PDF SHA-256. It creates exactly three non-empty files: the PDF, an HTML source, and metadata. Any missing renderer, invalid input, partial output, multi-page PDF, or nonzero exit is a failure.

Render the actual PDF page to an image with an available local PDF renderer, then inspect it before reporting success. Check all required labels and values, Korean glyphs, A4 single-page fit, alignment, clipped text, overlap, account readability, total emphasis, and the review watermark. HTML-only inspection is insufficient.

Report the calculated fee and due date from stdout or metadata, never from recollection. For multiple hires, generate and inspect each PDF independently.

## Finalize and send

PDF generation and Gmail delivery are separate states. A review request never authorizes sending.

The Python renderer has no mail transport. The following delivery gates are workflow obligations that you must enforce with the connected Gmail tool; do not describe them as Python-enforced guarantees.

Do not call any Gmail mutation when any of these is true:

- `draft` is true;
- the tax policy is `UNCONFIRMED`;
- `delivery.send_enabled` is false;
- visual verification did not pass;
- the connected Gmail tool is unavailable;
- the user has not approved the exact final delivery summary.

Immediately before sending, show one concise approval summary containing the recipient read from the contract, subject, company, candidate, requested fee, total amount, due date, PDF path, and full PDF SHA-256. Approval must refer to that concrete summary.

Before the send call, search Sent mail for the full SHA-256 included in prior invoice bodies. If found, stop as a possible duplicate and require a new explicit resend approval. Do not retry a failed send automatically.

After approval, use the connected Gmail tool to send the PDF as a binary attachment. Include the full PDF SHA-256 in the message body for duplicate detection. Do not substitute a local path, cloud link, HTML file, or metadata file for the PDF attachment. If no Gmail connector is available, return `BLOCKED`; do not request SMTP credentials or create a new mail transport.

After sending, read back the Gmail result by its returned message identifier and verify recipient plus attachment presence. Report `SENT` only with that evidence. Otherwise report `FAIL` or `BLOCKED` and preserve the PDF for review.

## Report states

Keep these outcomes distinct:

- `PASS / REVIEW_READY`: PDF generation and visual inspection passed; no email was sent.
- `BLOCKED`: a required owner decision, approval, Gmail connection, or readback is unavailable.
- `FAIL`: input, contract, calculation, rendering, visual inspection, or delivery violated the contract.
- `SENT`: Gmail returned a message identifier and readback confirmed the intended recipient and PDF attachment.

Always link the review PDF and PNG preview when the platform supports local file links. State unresolved business decisions before inviting final delivery approval.
