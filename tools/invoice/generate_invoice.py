#!/usr/bin/env python3
"""Generate one-page ValueConnect recruitment fee invoice PDFs."""
from __future__ import annotations
import argparse
import hashlib
import html
import json
import os
import re
import signal
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Any, NamedTuple
REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_DIR = Path(__file__).resolve().parent
if str(MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(MODULE_DIR))
import storage_remote
DEFAULT_CONTRACT = REPO_ROOT / "contracts" / "invoice" / "invoice-v1.json"
ARTIFACT_ROOT = REPO_ROOT / "artifacts" / "invoices"
ALLOWED_INPUT_FIELDS = frozenset(
    {
        "invoice_number",
        "issue_date",
        "company_name",
        "candidate_name",
        "start_date",
        "position",
        "annual_salary_krw",
        "annual_salary_manwon",
        "fee_percent",
        "fee_agreement_ref",
        "draft",
    }
)
REQUIRED_INPUT_FIELDS = ALLOWED_INPUT_FIELDS - {"annual_salary_krw", "annual_salary_manwon"}
STRING_FIELDS = (
    "invoice_number",
    "company_name",
    "candidate_name",
    "position",
    "fee_agreement_ref",
)
TAX_POLICIES = frozenset({"UNCONFIRMED", "EXCLUSIVE", "INCLUSIVE", "NOT_APPLICABLE"})
class InvoiceError(Exception):
    """Base error for invoice generation."""
class InputError(InvoiceError):
    """Raised when invoice input violates the contract."""
class ContractError(InvoiceError):
    """Raised when the machine-readable contract is invalid."""
class RenderError(InvoiceError):
    """Raised when PDF rendering cannot complete."""
class InvoiceInput(NamedTuple):
    invoice_number: str
    issue_date: date
    company_name: str
    candidate_name: str
    start_date: date
    position: str
    annual_salary_krw: int
    fee_percent: Decimal
    fee_agreement_ref: str
    draft: bool
class InvoiceResult(NamedTuple):
    source: InvoiceInput
    requested_fee_krw: int
    tax_amount_krw: int | None
    total_amount_krw: int
    due_date: date
def _require_dict(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ContractError(f"{label} must be an object")
    return value
def _require_text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ContractError(f"{label} must be a non-empty string")
    return value.strip()
def _require_bool(value: Any, label: str) -> bool:
    if not isinstance(value, bool):
        raise ContractError(f"{label} must be boolean")
    return value
def _parse_decimal(value: Any, label: str, allow_zero: bool = False) -> Decimal:
    if not isinstance(value, str):
        raise ContractError(f"{label} must be a decimal string")
    try:
        parsed = Decimal(value)
    except InvalidOperation as error:
        raise ContractError(f"{label} is not a decimal") from error
    lower_bound = Decimal("0") if allow_zero else Decimal("0.0000001")
    if not parsed.is_finite() or parsed < lower_bound or parsed > Decimal("1"):
        raise ContractError(f"{label} must be between {lower_bound} and 1")
    return parsed
def load_contract(path: str | Path) -> dict[str, Any]:
    contract_path = Path(path).expanduser().resolve()
    if contract_path != DEFAULT_CONTRACT.resolve():
        raise ContractError("only the canonical invoice contract may be loaded")
    try:
        raw = json.loads(contract_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ContractError(f"cannot read contract: {error}") from error
    contract = _require_dict(raw, "contract")
    if contract.get("schema_version") != "1.1":
        raise ContractError("schema_version must be 1.1")
    issuer = _require_dict(contract.get("issuer"), "issuer")
    _require_text(issuer.get("company_name"), "issuer.company_name")
    billing = _require_dict(contract.get("billing"), "billing")
    if billing.get("currency") != "KRW":
        raise ContractError("billing.currency must be KRW")
    fee_policy = _require_dict(billing.get("fee_policy"), "billing.fee_policy")
    if fee_policy.get("source") != "CUSTOMER_POSITION_AGREEMENT":
        raise ContractError("billing.fee_policy.source is unsupported")
    if fee_policy.get("input_unit") != "PERCENT":
        raise ContractError("billing.fee_policy.input_unit must be PERCENT")
    if fee_policy.get("allow_default") is not False:
        raise ContractError("billing.fee_policy.allow_default must be false")
    if fee_policy.get("require_agreement_reference") is not True:
        raise ContractError("billing fee agreement reference must be required")
    if fee_policy.get("minimum_exclusive") != "0" or fee_policy.get("maximum_inclusive") != "100":
        raise ContractError("billing fee percentage bounds are unsupported")
    if billing.get("rounding") != "HALF_UP_TO_WON":
        raise ContractError("billing.rounding must be HALF_UP_TO_WON")
    tax_policy = billing.get("tax_policy")
    if tax_policy not in TAX_POLICIES:
        raise ContractError("billing.tax_policy is unsupported")
    tax_rate = billing.get("tax_rate")
    if tax_policy == "EXCLUSIVE":
        _parse_decimal(tax_rate, "billing.tax_rate", allow_zero=True)
    elif tax_rate is not None:
        raise ContractError("billing.tax_rate must be null unless tax is EXCLUSIVE")
    expected_total_policy = "BLOCK_UNTIL_CONFIRMED" if tax_policy == "UNCONFIRMED" else "FINALIZED"
    if billing.get("final_total_policy") != expected_total_policy:
        raise ContractError("billing.final_total_policy conflicts with billing.tax_policy")
    payment = _require_dict(contract.get("payment"), "payment")
    offset = payment.get("due_offset_days")
    if isinstance(offset, bool) or not isinstance(offset, int) or not 0 <= offset <= 365:
        raise ContractError("payment.due_offset_days must be an integer from 0 to 365")
    if payment.get("due_day_basis") != "CALENDAR_DAYS":
        raise ContractError("payment.due_day_basis must be CALENDAR_DAYS")
    _require_text(payment.get("bank_name"), "payment.bank_name")
    account = _require_text(payment.get("account_number_display"), "payment.account_number_display")
    if not re.fullmatch(r"[0-9 -]{8,32}", account):
        raise ContractError("payment.account_number_display has an invalid format")
    _require_text(payment.get("account_holder"), "payment.account_holder")
    delivery = _require_dict(contract.get("delivery"), "delivery")
    recipient = _require_text(delivery.get("default_recipient"), "delivery.default_recipient")
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", recipient):
        raise ContractError("delivery.default_recipient is invalid")
    for key in (
        "send_enabled",
        "require_final_confirmation",
        "require_attachment_sha256",
        "automatic_retry",
    ):
        _require_bool(delivery.get(key), f"delivery.{key}")
    document = _require_dict(contract.get("document"), "document")
    if document.get("page_size") != "A4" or document.get("max_pages") != 1:
        raise ContractError("document must be one A4 page")
    for key in ("draft_watermark", "draft_total_label", "draft_total_note"):
        _require_text(document.get(key), f"document.{key}")
    return contract
def _input_text(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str):
        raise InputError(f"{key} must be a string")
    cleaned = value.strip()
    if not 1 <= len(cleaned) <= 120:
        raise InputError(f"{key} must contain 1 to 120 characters")
    if any(ord(character) < 32 for character in cleaned):
        raise InputError(f"{key} must not contain control characters")
    return cleaned
def _input_date(payload: dict[str, Any], key: str) -> date:
    value = payload.get(key)
    if not isinstance(value, str):
        raise InputError(f"{key} must be an ISO date string")
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise InputError(f"{key} must be a valid YYYY-MM-DD date") from error
def _input_percent(payload: dict[str, Any], key: str) -> Decimal:
    value = payload.get(key)
    if not isinstance(value, str):
        raise InputError(f"{key} must be a decimal string")
    try:
        parsed = Decimal(value)
    except InvalidOperation as error:
        raise InputError(f"{key} must be a decimal percentage") from error
    if not parsed.is_finite() or parsed <= 0 or parsed > 100:
        raise InputError(f"{key} must be greater than 0 and at most 100")
    return parsed
def validate_input(payload: Any, contract: dict[str, Any]) -> InvoiceInput:
    if not isinstance(payload, dict):
        raise InputError("input must be a JSON object")
    unknown = sorted(set(payload) - ALLOWED_INPUT_FIELDS)
    if unknown:
        raise InputError(f"unknown field(s): {', '.join(unknown)}")
    missing = sorted(REQUIRED_INPUT_FIELDS - set(payload))
    if missing:
        raise InputError(f"missing field(s): {', '.join(missing)}")
    salary_fields = {"annual_salary_krw", "annual_salary_manwon"} & set(payload)
    if len(salary_fields) != 1:
        raise InputError("provide exactly one of annual_salary_krw or annual_salary_manwon")
    strings = {key: _input_text(payload, key) for key in STRING_FIELDS}
    salary_key = salary_fields.pop()
    annual_salary_input = payload.get(salary_key)
    if (
        isinstance(annual_salary_input, bool)
        or not isinstance(annual_salary_input, int)
        or annual_salary_input <= 0
    ):
        raise InputError(f"{salary_key} must be a positive integer")
    annual_salary = (
        annual_salary_input * 10_000
        if salary_key == "annual_salary_manwon"
        else annual_salary_input
    )
    if annual_salary > 10_000_000_000:
        raise InputError("converted annual salary must not exceed 10000000000 KRW")
    draft = payload.get("draft")
    if not isinstance(draft, bool):
        raise InputError("draft must be boolean")
    if not draft and contract["billing"]["tax_policy"] == "UNCONFIRMED":
        raise ContractError("tax policy must be confirmed before a final document")
    return InvoiceInput(
        invoice_number=strings["invoice_number"],
        issue_date=_input_date(payload, "issue_date"),
        company_name=strings["company_name"],
        candidate_name=strings["candidate_name"],
        start_date=_input_date(payload, "start_date"),
        position=strings["position"],
        annual_salary_krw=annual_salary,
        fee_percent=_input_percent(payload, "fee_percent"),
        fee_agreement_ref=strings["fee_agreement_ref"],
        draft=draft,
    )
def _won(value: Decimal) -> int:
    return int(value.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
def calculate_invoice(invoice_input: InvoiceInput, contract: dict[str, Any]) -> InvoiceResult:
    billing = contract["billing"]
    fee_rate = invoice_input.fee_percent / Decimal("100")
    requested_fee = _won(Decimal(invoice_input.annual_salary_krw) * fee_rate)
    tax_policy = billing["tax_policy"]
    tax_amount: int | None = None
    total = requested_fee
    if tax_policy == "EXCLUSIVE":
        tax_amount = _won(Decimal(requested_fee) * Decimal(billing["tax_rate"]))
        total += tax_amount
    due_date = invoice_input.start_date + timedelta(days=contract["payment"]["due_offset_days"])
    return InvoiceResult(invoice_input, requested_fee, tax_amount, total, due_date)
def _format_date(value: date) -> str:
    return value.strftime("%Y.%m.%d")
def _format_krw(value: int) -> str:
    return f"{value:,}원"
def _escape_text(value: str) -> str:
    return html.escape(value).replace("{", "&#123;").replace("}", "&#125;")
def _render_context(invoice: InvoiceResult, contract: dict[str, Any]) -> dict[str, str]:
    source = invoice.source
    issuer = _escape_text(contract["issuer"]["company_name"])
    payment = contract["payment"]
    document = contract["document"]
    watermark = _escape_text(document["draft_watermark"]) if source.draft else ""
    draft_notice = "메일 발송 안 됨 · 금액 및 세금 기준 검수 필요" if source.draft else ""
    total_note = _escape_text(document["draft_total_note"]) if source.draft else ""
    total_label = _escape_text(document["draft_total_label"]) if source.draft else "총 청구 금액"
    safe = {field: _escape_text(getattr(source, field)) for field in STRING_FIELDS}
    tax_row = ""
    if invoice.tax_amount_krw is not None:
        tax_row = f"""
          <div class="amount-row secondary"><span>부가가치세</span><strong>{_format_krw(invoice.tax_amount_krw)}</strong></div>"""
    return {
        "account": _escape_text(payment["account_number_display"]),
        "account_holder": _escape_text(payment["account_holder"]),
        "annual_salary": _format_krw(source.annual_salary_krw),
        "bank": _escape_text(payment["bank_name"]),
        "candidate_name": safe["candidate_name"],
        "company_name": safe["company_name"],
        "draft_badge": f'<div class="draft">{watermark}</div>' if watermark else "",
        "draft_notice": draft_notice,
        "due_date": _format_date(invoice.due_date),
        "due_offset": str(payment["due_offset_days"]),
        "invoice_number": safe["invoice_number"],
        "issue_date": _format_date(source.issue_date),
        "issuer": issuer,
        "position": safe["position"],
        "requested_fee": _format_krw(invoice.requested_fee_krw),
        "start_date": _format_date(source.start_date),
        "tax_note": f'<p class="tax-note">{total_note}</p>' if total_note else "",
        "tax_row": tax_row,
        "total_amount": _format_krw(invoice.total_amount_krw),
        "total_label": total_label,
    }
_HTML_TEMPLATE = """<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{safe['invoice_number']} Invoice</title>
  <style>
    @page {{ size: A4 portrait; margin: 0; }} * {{ box-sizing: border-box; }} html, body {{ margin: 0; padding: 0; background: #eef1f4; color: #17212b; }}
    body {{ font-family: "Apple SD Gothic Neo", "Noto Sans KR", "Malgun Gothic", Arial, sans-serif; }} .page {{ position: relative; width: 210mm; height: 297mm; margin: 0 auto; padding: 18mm 18mm 15mm; background: #fff; overflow: hidden; }}
    .top-rule {{ height: 4px; width: 100%; background: #123b5d; margin-bottom: 12mm; }} .draft {{ position: absolute; top: 13mm; right: 18mm; padding: 2.5mm 4mm; border: 1px solid #a34d47; border-radius: 2mm; color: #8d3732; font-size: 9pt; font-weight: 700; letter-spacing: .08em; }}
    header {{ display: flex; justify-content: space-between; gap: 16mm; align-items: flex-start; }} .eyebrow {{ margin: 0 0 2mm; color: #547083; font-size: 9pt; font-weight: 700; letter-spacing: .18em; }} h1 {{ margin: 0; color: #0f2e46; font-size: 28pt; line-height: 1; letter-spacing: .02em; }} .subtitle {{ margin: 3mm 0 0; color: #667784; font-size: 11pt; }}
    .issuer {{ min-width: 63mm; padding-top: 2mm; text-align: right; }} .issuer strong {{ display: block; color: #0f2e46; font-size: 13pt; }} .issuer span {{ display: block; margin-top: 2mm; color: #6b7983; font-size: 9pt; }}
    .meta {{ display: grid; grid-template-columns: 1fr 1fr 1fr; margin-top: 12mm; border-top: 1px solid #cfd7dd; border-bottom: 1px solid #cfd7dd; }} .meta-item {{ padding: 5mm 5mm 5mm 0; }} .meta-item + .meta-item {{ padding-left: 5mm; border-left: 1px solid #e2e7eb; }}
    .label {{ display: block; margin-bottom: 1.5mm; color: #778792; font-size: 8.5pt; font-weight: 700; letter-spacing: .06em; }} .value {{ color: #1a2c38; font-size: 11pt; font-weight: 700; }} .section-title {{ margin: 11mm 0 4mm; color: #496171; font-size: 9pt; font-weight: 800; letter-spacing: .14em; }}
    .details {{ border-top: 2px solid #183f5e; }} .detail-row {{ display: grid; grid-template-columns: 36mm 1fr; min-height: 14mm; align-items: center; border-bottom: 1px solid #dfe5e9; }} .detail-row span {{ color: #6e7d87; font-size: 9.5pt; font-weight: 700; }} .detail-row strong {{ color: #172b39; font-size: 11pt; font-weight: 650; }}
    .amounts {{ margin-top: 9mm; margin-left: auto; width: 105mm; }} .amount-row {{ display: flex; justify-content: space-between; align-items: center; padding: 4mm 0; color: #50636f; font-size: 10pt; }} .amount-row strong {{ color: #182d3c; font-size: 12pt; }} .amount-row.secondary {{ border-top: 1px solid #e0e5e9; }}
    .amount-row.total {{ margin-top: 1mm; padding: 5mm; background: #123b5d; color: #fff; border-radius: 2mm; }} .amount-row.total strong {{ color: #fff; font-size: 17pt; }} .tax-note {{ margin: 2.5mm 0 0; color: #8a5c34; font-size: 8.5pt; line-height: 1.5; text-align: right; }}
    .payment {{ margin-top: 10mm; padding: 6mm; border: 1px solid #c9d4dc; border-left: 4px solid #2c678d; border-radius: 2mm; background: #f7f9fa; }} .payment-title {{ margin: 0 0 5mm; color: #214b67; font-size: 10pt; font-weight: 800; letter-spacing: .08em; }} .payment-grid {{ display: grid; grid-template-columns: 1.2fr .6fr 1fr 1.2fr; gap: 4mm; }}
    .payment .value {{ font-size: 10.5pt; }} .due-emphasis {{ color: #143f5e !important; font-size: 12pt !important; }} footer {{ position: absolute; left: 18mm; right: 18mm; bottom: 13mm; display: flex; justify-content: space-between; align-items: flex-end; border-top: 1px solid #d8dfe4; padding-top: 4mm; color: #71808a; font-size: 8.5pt; }} .notice {{ color: #8d3732; font-weight: 700; }}
  </style>
</head>
<body>
  <main class="page">
    <div class="top-rule"></div>
    {f'<div class="draft">{watermark}</div>' if watermark else ''}
    <header>
      <div>
        <p class="eyebrow">RECRUITMENT FEE</p>
        <h1>INVOICE</h1>
        <p class="subtitle">채용 수수료 청구서</p>
      </div>
      <div class="issuer">
        <strong>{issuer}</strong>
        <span>Talent Partnership · Executive Search</span>
      </div>
    </header>
    <section class="meta">
      <div class="meta-item"><span class="label">수신</span><span class="value">{safe['company_name']} 귀중</span></div>
      <div class="meta-item"><span class="label">발행일</span><span class="value">{_format_date(source.issue_date)}</span></div>
      <div class="meta-item"><span class="label">INVOICE NO.</span><span class="value">{safe['invoice_number']}</span></div>
    </section>
    <p class="section-title">PLACEMENT DETAILS</p>
    <section class="details">
      <div class="detail-row"><span>입사자명</span><strong>{safe['candidate_name']}</strong></div>
      <div class="detail-row"><span>입사일</span><strong>{_format_date(source.start_date)}</strong></div>
      <div class="detail-row"><span>직책</span><strong>{safe['position']}</strong></div>
      <div class="detail-row"><span>결정 연봉</span><strong>{_format_krw(source.annual_salary_krw)}</strong></div>
    </section>
    <section class="amounts">
      <div class="amount-row"><span>요청 수수료</span><strong>{_format_krw(invoice.requested_fee_krw)}</strong></div>{tax_row}
      <div class="amount-row total"><span>{total_label}</span><strong>{_format_krw(invoice.total_amount_krw)}</strong></div>
      {f'<p class="tax-note">{total_note}</p>' if total_note else ''}
    </section>

    <section class="payment">
      <p class="payment-title">PAYMENT INFORMATION · 입금 안내</p>
      <div class="payment-grid">
        <div><span class="label">계약서에 따른 입금 Due Date</span><span class="value due-emphasis">{_format_date(invoice.due_date)}</span></div>
        <div><span class="label">은행</span><span class="value">{html.escape(payment['bank_name'])}</span></div>
        <div><span class="label">계좌번호</span><span class="value">{html.escape(payment['account_number_display'])}</span></div>
        <div><span class="label">예금주</span><span class="value">{html.escape(payment['account_holder'])}</span></div>
      </div>
    </section>

    <footer>
      <span>입사 후 {payment['due_offset_days']}일 이내 입금 부탁드립니다.</span>
      <span class="notice">{draft_notice}</span>
    </footer>
  </main>
</body>
</html>
"""

def render_html(invoice: InvoiceResult, contract: dict[str, Any]) -> str:
    rendered = _HTML_TEMPLATE.replace("{{", "{").replace("}}", "}")
    context = _render_context(invoice, contract)
    replacements = {
        "{safe['invoice_number']}": context["invoice_number"],
        "{f'<div class=\"draft\">{watermark}</div>' if watermark else ''}": context["draft_badge"],
        "{issuer}": context["issuer"],
        "{safe['company_name']}": context["company_name"],
        "{_format_date(source.issue_date)}": context["issue_date"],
        "{safe['candidate_name']}": context["candidate_name"],
        "{_format_date(source.start_date)}": context["start_date"],
        "{safe['position']}": context["position"],
        "{_format_krw(source.annual_salary_krw)}": context["annual_salary"],
        "{_format_krw(invoice.requested_fee_krw)}": context["requested_fee"],
        "{tax_row}": context["tax_row"],
        "{total_label}": context["total_label"],
        "{_format_krw(invoice.total_amount_krw)}": context["total_amount"],
        "{f'<p class=\"tax-note\">{total_note}</p>' if total_note else ''}": context["tax_note"],
        "{_format_date(invoice.due_date)}": context["due_date"],
        "{html.escape(payment['bank_name'])}": context["bank"],
        "{html.escape(payment['account_number_display'])}": context["account"],
        "{html.escape(payment['account_holder'])}": context["account_holder"],
        "{payment['due_offset_days']}": context["due_offset"],
        "{draft_notice}": context["draft_notice"],
    }
    for token, value in replacements.items():
        if token not in rendered:
            raise ContractError(f"invoice template token missing: {token}")
        rendered = rendered.replace(token, value)
    if re.search(r"\{(?:safe|_format|html\.escape|payment|f'|tax_|total_|draft_)", rendered):
        raise ContractError("invoice template contains unresolved tokens")
    return rendered

def find_chrome(explicit_path: str | None = None) -> str:
    requested = explicit_path or os.environ.get("INVOICE_CHROME_BIN")
    if requested:
        path = Path(requested).expanduser()
        if path.is_file() and os.access(path, os.X_OK):
            return str(path.resolve())
        raise RenderError(f"Chrome executable not found: {requested}")
    candidates = (
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "google-chrome",
        "google-chrome-stable",
        "chromium",
        "chromium-browser",
    )
    for candidate in candidates:
        resolved = shutil.which(candidate) if "/" not in candidate else candidate
        if resolved and Path(resolved).is_file() and os.access(resolved, os.X_OK):
            return str(Path(resolved).resolve())
    raise RenderError("Chrome executable is required for PDF rendering")

def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

def _ensure_artifact_path(path: Path, label: str) -> Path:
    resolved = path.expanduser().resolve()
    root = ARTIFACT_ROOT.resolve()
    if not resolved.is_relative_to(root):
        raise InputError(f"{label} must be inside {ARTIFACT_ROOT}")
    return resolved

def _render_pdf(chrome: str, html_path: Path, pdf_path: Path, profile_path: Path) -> None:
    command = [
        chrome,
        "--headless",
        "--disable-gpu",
        "--disable-extensions",
        "--disable-background-networking",
        "--disable-component-update",
        "--disable-sync",
        "--metrics-recording-only",
        "--no-first-run",
        "--no-default-browser-check",
        "--password-store=basic",
        "--use-mock-keychain",
        "--no-pdf-header-footer",
        "--virtual-time-budget=1000",
        f"--user-data-dir={profile_path}",
        f"--print-to-pdf={pdf_path}",
        html_path.as_uri(),
    ]
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    )
    deadline = time.monotonic() + 30
    pdf_complete = False
    while time.monotonic() < deadline:
        if pdf_path.is_file() and pdf_path.read_bytes().rstrip().endswith(b"%%EOF"):
            pdf_complete = True
            break
        if process.poll() is not None:
            break
        time.sleep(0.25)
    if process.poll() is None:
        os.killpg(process.pid, signal.SIGTERM)
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait(timeout=5)
    stdout, stderr = process.communicate()
    if not pdf_complete:
        detail = (stderr or stdout).strip()
        raise RenderError(f"Chrome PDF rendering did not complete: {detail}")
    if not pdf_path.is_file():
        raise RenderError("Chrome reported success without creating a PDF")
    pdf_bytes = pdf_path.read_bytes()
    if len(pdf_bytes) < 1024 or not pdf_bytes.startswith(b"%PDF-"):
        raise RenderError("rendered file is not a valid non-empty PDF")
    page_count = len(re.findall(rb"/Type\s*/Page\b", pdf_bytes))
    if page_count != 1:
        raise RenderError(f"rendered PDF must contain exactly one page, found {page_count}")

def generate_files(
    input_path: Path, output_path: Path, contract_path: Path,
    chrome_path: str | None, overwrite: bool,
) -> tuple[InvoiceResult, Path, Path, Path, str]:
    input_file = _ensure_artifact_path(input_path, "input")
    output_file = _ensure_artifact_path(output_path, "output")
    if output_file.suffix.lower() != ".pdf":
        raise InputError("output must end in .pdf")
    if not input_file.is_file():
        raise InputError(f"input file does not exist: {input_file}")
    try:
        payload = json.loads(input_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise InputError(f"cannot read input JSON: {error}") from error
    contract = load_contract(contract_path)
    invoice_input = validate_input(payload, contract)
    fee_authority = None
    if not invoice_input.draft:
        try:
            fee_authority = storage_remote.verify_fee_authority(
                invoice_input.company_name, invoice_input.position,
                invoice_input.start_date, invoice_input.fee_percent,
                invoice_input.fee_agreement_ref,
            )
        except storage_remote.RemoteError as error:
            raise ContractError(f"final fee authority was not proven: {error}") from error
    result = calculate_invoice(invoice_input, contract)
    html_text = render_html(result, contract)
    html_output = output_file.with_suffix(".html")
    metadata_output = output_file.with_suffix(".metadata.json")
    targets = (output_file, html_output, metadata_output)
    existing = [str(path) for path in targets if path.exists()]
    if existing and not overwrite:
        raise InputError(f"output already exists; use --overwrite: {', '.join(existing)}")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    chrome = find_chrome(chrome_path)
    with tempfile.TemporaryDirectory(prefix="invoice-", dir=output_file.parent) as temp_dir:
        temp_root = Path(temp_dir)
        temp_html = temp_root / "invoice.html"
        temp_pdf = temp_root / "invoice.pdf"
        temp_metadata = temp_root / "invoice.metadata.json"
        temp_html.write_text(html_text, encoding="utf-8")
        _render_pdf(chrome, temp_html, temp_pdf, temp_root / "chrome-profile")
        pdf_digest = _sha256(temp_pdf)
        metadata = {
            "contract_version": contract["schema_version"],
            "invoice_number": result.source.invoice_number,
            "fee_percent": format(result.source.fee_percent.normalize(), "f"),
            "fee_agreement_ref": result.source.fee_agreement_ref,
            "requested_fee_krw": result.requested_fee_krw,
            "tax_amount_krw": result.tax_amount_krw,
            "total_amount_krw": result.total_amount_krw,
            "due_date": result.due_date.isoformat(),
            "draft": result.source.draft,
            "fee_authority": "SUPABASE" if fee_authority else "UNVERIFIED_DRAFT",
            "fee_agreement_id": fee_authority["id"] if fee_authority else None,
            "input_sha256": _sha256(input_file),
            "pdf_sha256": pdf_digest,
        }
        temp_metadata.write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        os.replace(temp_html, html_output)
        os.replace(temp_metadata, metadata_output)
        os.replace(temp_pdf, output_file)
    if any(not path.is_file() or path.stat().st_size == 0 for path in targets):
        raise RenderError("one or more invoice outputs are missing or empty")
    return result, output_file, html_output, metadata_output, pdf_digest

def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="Input JSON in artifacts/invoices")
    parser.add_argument("--output", required=True, type=Path, help="Output PDF in artifacts/invoices")
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--chrome", help="Explicit Chrome executable")
    parser.add_argument("--overwrite", action="store_true")
    return parser

def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        result, pdf, html_file, metadata, digest = generate_files(
            args.input, args.output, args.contract, args.chrome, args.overwrite
        )
    except (InputError, ContractError) as error:
        prefix = "INPUT_ERROR" if isinstance(error, InputError) else "CONTRACT_ERROR"
        print(f"{prefix}: {error}", file=sys.stderr)
        return 2
    except (RenderError, OSError, subprocess.SubprocessError) as error:
        print(f"RENDER_ERROR: {error}", file=sys.stderr)
        return 3
    checked = sum(path.stat().st_size > 0 for path in (pdf, html_file, metadata))
    print("RENDER_VERDICT: PASS")
    business = "UNVERIFIED_DRAFT" if result.source.draft else "FEE_AUTHORITY_VERIFIED"
    print(f"BUSINESS_STATUS: {business}")
    print(f"PDF: {pdf}")
    print(f"HTML: {html_file}")
    print(f"METADATA: {metadata}")
    print(f"REQUESTED_FEE_KRW: {result.requested_fee_krw}")
    print(f"FEE_PERCENT: {format(result.source.fee_percent.normalize(), 'f')}")
    print(f"FEE_AGREEMENT_REF: {result.source.fee_agreement_ref}")
    print(f"TOTAL_AMOUNT_KRW: {result.total_amount_krw}")
    print(f"DUE_DATE: {result.due_date.isoformat()}")
    print(f"PDF_SHA256: {digest}")
    print(f"CHECKED: {checked}")
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
