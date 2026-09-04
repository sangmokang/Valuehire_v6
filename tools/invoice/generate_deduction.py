#!/usr/bin/env python3
"""Generate a deterministic ValueConnect placement settlement PDF."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import tempfile
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONTRACT = REPO_ROOT / "contracts" / "invoice" / "deduction-v1.json"
CORE_PATH = Path(__file__).with_name("generate_invoice.py")
CORE_SPEC = importlib.util.spec_from_file_location("invoice_core", CORE_PATH)
if not CORE_SPEC or not CORE_SPEC.loader:
    raise RuntimeError("cannot load invoice rendering core")
invoice_core = importlib.util.module_from_spec(CORE_SPEC)
CORE_SPEC.loader.exec_module(invoice_core)

InputError = invoice_core.InputError
ContractError = invoice_core.ContractError
RenderError = invoice_core.RenderError

REQUIRED_FIELDS = frozenset(
    {
        "settlement_number",
        "invoice_number",
        "fee_agreement_ref",
        "issue_date",
        "company_name",
        "candidate_name",
        "start_date",
        "position",
        "annual_salary_manwon",
        "guarantee_months",
        "fee_percent",
        "account_manager_name",
        "account_manager_percent",
        "coworker_name",
        "coworker_percent",
        "rps_status",
        "rps_advance_krw",
        "rps_bearer",
        "draft",
    }
)
RPS_BEARER_LABELS = {
    "account_manager": "Account Manager",
    "coworker": "Coworker",
    "company": "회사",
    "pro_rata": "참여자 비례",
}


@dataclass(frozen=True)
class DeductionInput:
    settlement_number: str
    invoice_number: str
    fee_agreement_ref: str
    issue_date: date
    company_name: str
    candidate_name: str
    start_date: date
    position: str
    annual_salary_krw: int
    guarantee_months: int
    fee_percent: Decimal
    account_manager_name: str | None
    account_manager_percent: Decimal
    coworker_name: str | None
    coworker_percent: Decimal
    rps_status: str
    rps_advance_krw: int | None
    rps_bearer: str | None
    draft: bool


@dataclass(frozen=True)
class DeductionResult:
    source: DeductionInput
    invoice_amount_krw: int
    company_share_krw: int
    account_manager_gross_krw: int
    coworker_gross_krw: int
    account_manager_withholding_krw: int
    coworker_withholding_krw: int
    account_manager_rps_krw: int | None
    coworker_rps_krw: int | None
    company_rps_krw: int | None
    account_manager_net_krw: int
    coworker_net_krw: int
    company_net_krw: int


def _text(value: Any, label: str) -> str:
    if not isinstance(value, str):
        raise InputError(f"{label} must be a string")
    cleaned = value.strip()
    if not 1 <= len(cleaned) <= 120 or any(ord(char) < 32 for char in cleaned):
        raise InputError(f"{label} must contain 1 to 120 printable characters")
    return cleaned


def _optional_text(value: Any, label: str) -> str | None:
    return None if value is None else _text(value, label)


def _date(value: Any, label: str) -> date:
    if not isinstance(value, str):
        raise InputError(f"{label} must be an ISO date string")
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise InputError(f"{label} must be a valid YYYY-MM-DD date") from error


def _percent(value: Any, label: str, allow_zero: bool = False) -> Decimal:
    if not isinstance(value, str):
        raise InputError(f"{label} must be a decimal string")
    try:
        parsed = Decimal(value)
    except InvalidOperation as error:
        raise InputError(f"{label} is not a decimal percentage") from error
    lower = Decimal("0") if allow_zero else Decimal("0.000001")
    if not parsed.is_finite() or parsed < lower or parsed > Decimal("100"):
        raise InputError(f"{label} must be between {lower} and 100")
    return parsed


def _won(value: Decimal) -> int:
    return int(value.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def load_contract(path: str | Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    contract_path = Path(path).expanduser().resolve()
    if contract_path != DEFAULT_CONTRACT.resolve():
        raise ContractError("only the canonical deduction contract may be loaded")
    try:
        raw = json.loads(contract_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ContractError(f"cannot read deduction contract: {error}") from error
    if not isinstance(raw, dict) or raw.get("schema_version") != "1.1":
        raise ContractError("deduction contract schema_version must be 1.1")
    if raw.get("currency") != "KRW":
        raise ContractError("deduction contract currency must be KRW")
    _text(raw.get("issuer_name"), "issuer_name")
    company = _percent(raw.get("company_share_percent"), "company_share_percent")
    withholding = _percent(raw.get("withholding_percent"), "withholding_percent", True)
    total = _percent(raw.get("allocation_total_percent"), "allocation_total_percent")
    if company != Decimal("25") or withholding != Decimal("3.3") or total != Decimal("100"):
        raise ContractError("deduction contract business constants are unsupported")
    bearers = raw.get("rps_bearers")
    if not isinstance(bearers, list) or set(bearers) != set(RPS_BEARER_LABELS):
        raise ContractError("deduction contract rps_bearers are invalid")
    statuses = raw.get("rps_statuses")
    expected_statuses = {"pending", "none", "deferred", "deducted"}
    if not isinstance(statuses, list) or set(statuses) != expected_statuses:
        raise ContractError("deduction contract rps_statuses are invalid")
    document = raw.get("document")
    if not isinstance(document, dict) or document.get("page_size") != "A4":
        raise ContractError("deduction document must use A4")
    if document.get("max_pages") != 1:
        raise ContractError("deduction document must contain one page")
    _text(document.get("draft_watermark"), "document.draft_watermark")
    _text(document.get("title_ko"), "document.title_ko")
    status_labels = document.get("status_en")
    if not isinstance(status_labels, dict) or set(status_labels) != expected_statuses:
        raise ContractError("deduction document status_en is invalid")
    for status, label in status_labels.items():
        _text(label, f"document.status_en.{status}")
    _text(document.get("zero_rps_status"), "document.zero_rps_status")
    return raw


def validate_input(payload: Any, contract: dict[str, Any]) -> DeductionInput:
    if not isinstance(payload, dict):
        raise InputError("input must be a JSON object")
    unknown = sorted(set(payload) - REQUIRED_FIELDS)
    missing = sorted(REQUIRED_FIELDS - set(payload))
    if unknown:
        raise InputError(f"unknown field(s): {', '.join(unknown)}")
    if missing:
        raise InputError(f"missing field(s): {', '.join(missing)}")
    salary = payload.get("annual_salary_manwon")
    if isinstance(salary, bool) or not isinstance(salary, int) or salary <= 0:
        raise InputError("annual_salary_manwon must be a positive integer")
    annual_salary = salary * 10_000
    if annual_salary > 10_000_000_000:
        raise InputError("converted annual salary must not exceed 10000000000 KRW")
    guarantee = payload.get("guarantee_months")
    if isinstance(guarantee, bool) or not isinstance(guarantee, int) or not 0 <= guarantee <= 60:
        raise InputError("guarantee_months must be an integer from 0 to 60")
    fee_percent = _percent(payload.get("fee_percent"), "fee_percent")
    am_percent = _percent(payload.get("account_manager_percent"), "account_manager_percent", True)
    coworker_percent = _percent(payload.get("coworker_percent"), "coworker_percent", True)
    company_percent = Decimal(contract["company_share_percent"])
    if company_percent + am_percent + coworker_percent != Decimal("100"):
        raise InputError("company, Account Manager, and Coworker percentages must total 100")
    am_name = _optional_text(payload.get("account_manager_name"), "account_manager_name")
    coworker_name = _optional_text(payload.get("coworker_name"), "coworker_name")
    rps_status = payload.get("rps_status")
    if rps_status not in contract["rps_statuses"]:
        raise InputError("rps_status is unsupported")
    rps_amount = payload.get("rps_advance_krw")
    if rps_amount is not None and (
        isinstance(rps_amount, bool) or not isinstance(rps_amount, int) or rps_amount < 0
    ):
        raise InputError("rps_advance_krw must be null or a non-negative integer")
    bearer = payload.get("rps_bearer")
    if bearer is not None and bearer not in contract["rps_bearers"]:
        raise InputError("rps_bearer is unsupported")
    if rps_status == "pending" and (rps_amount is not None or bearer is not None):
        raise InputError("pending RPS requires null amount and bearer")
    if rps_status in {"none", "deferred"} and (rps_amount != 0 or bearer is not None):
        raise InputError(f"{rps_status} RPS requires zero amount and null bearer")
    if rps_status == "deducted" and (not rps_amount or bearer is None):
        if bearer is None:
            raise InputError("positive rps_advance_krw requires rps_bearer")
        raise InputError("rps_bearer requires a positive rps_advance_krw")
    draft = payload.get("draft")
    if not isinstance(draft, bool):
        raise InputError("draft must be boolean")
    if not draft:
        if rps_status == "pending":
            raise InputError("final settlement requires an explicit RPS status")
        if am_percent > 0 and am_name is None:
            raise InputError("final settlement requires account_manager_name")
        if coworker_percent > 0 and coworker_name is None:
            raise InputError("final settlement requires coworker_name")
    return DeductionInput(
        settlement_number=_text(payload["settlement_number"], "settlement_number"),
        invoice_number=_text(payload["invoice_number"], "invoice_number"),
        fee_agreement_ref=_text(payload["fee_agreement_ref"], "fee_agreement_ref"),
        issue_date=_date(payload["issue_date"], "issue_date"),
        company_name=_text(payload["company_name"], "company_name"),
        candidate_name=_text(payload["candidate_name"], "candidate_name"),
        start_date=_date(payload["start_date"], "start_date"),
        position=_text(payload["position"], "position"),
        annual_salary_krw=annual_salary,
        guarantee_months=guarantee,
        fee_percent=fee_percent,
        account_manager_name=am_name,
        account_manager_percent=am_percent,
        coworker_name=coworker_name,
        coworker_percent=coworker_percent,
        rps_status=rps_status,
        rps_advance_krw=rps_amount,
        rps_bearer=bearer,
        draft=draft,
    )


def calculate_settlement(source: DeductionInput, contract: dict[str, Any]) -> DeductionResult:
    gross = _won(Decimal(source.annual_salary_krw) * source.fee_percent / 100)
    company = _won(Decimal(gross) * Decimal(contract["company_share_percent"]) / 100)
    am_gross = _won(Decimal(gross) * source.account_manager_percent / 100)
    coworker_gross = gross - company - am_gross
    withholding = Decimal(contract["withholding_percent"]) / 100
    am_tax = _won(Decimal(am_gross) * withholding)
    coworker_tax = _won(Decimal(coworker_gross) * withholding)
    am_rps = coworker_rps = company_rps = None if source.rps_advance_krw is None else 0
    rps = source.rps_advance_krw
    if rps:
        if source.rps_bearer == "account_manager":
            am_rps = rps
        elif source.rps_bearer == "coworker":
            coworker_rps = rps
        elif source.rps_bearer == "company":
            company_rps = rps
        else:
            participant_percent = source.account_manager_percent + source.coworker_percent
            am_rps = _won(Decimal(rps) * source.account_manager_percent / participant_percent)
            coworker_rps = rps - am_rps
    am_net = am_gross - am_tax - (am_rps or 0)
    coworker_net = coworker_gross - coworker_tax - (coworker_rps or 0)
    company_net = company - (company_rps or 0)
    if min(am_net, coworker_net, company_net) < 0:
        raise InputError("RPS deduction exceeds the selected allocation")
    return DeductionResult(
        source, gross, company, am_gross, coworker_gross, am_tax, coworker_tax,
        am_rps, coworker_rps, company_rps, am_net, coworker_net, company_net,
    )


def _money(value: int) -> str:
    return f"{value:,}원"


def _percent_text(value: Decimal) -> str:
    return f"{format(value.normalize(), 'f')}%"


def render_html(result: DeductionResult, contract: dict[str, Any]) -> str:
    source = result.source
    esc = invoice_core._escape_text
    am_name = esc(source.account_manager_name or "미입력")
    coworker_name = esc(source.coworker_name or "미입력")
    if source.rps_status == "pending":
        rps_value = "미입력 · 금액/부담 주체 확정 필요"
    elif source.rps_status == "none":
        rps_value = "없음"
    elif source.rps_status == "deferred":
        rps_value = contract["document"]["zero_rps_status"]
    else:
        rps_value = f"{_money(source.rps_advance_krw)} · {RPS_BEARER_LABELS[source.rps_bearer or 'company']} 부담"
    watermark = (
        f'<div class="draft">{esc(contract["document"]["draft_watermark"])}</div>'
        if source.draft else ""
    )
    net_label = {
        "pending": "RPS 반영 전 세후 지급액",
        "none": "이번 Term 세후 지급액",
        "deferred": "이번 Term 세후 지급액",
        "deducted": "RPS 공제 후 세후 지급액",
    }[source.rps_status]
    footer_left = "내부 정산 검수용 · 세금계산서가 아닙니다." if source.draft else "내부 계산서 발행 정산 내역 · 세금계산서가 아닙니다."
    if source.draft:
        footer_status = "미입력 항목 확정 전 지급·발송 금지"
    elif source.rps_status == "deferred":
        footer_status = "배분·원천징수 확인 완료 · RPS 이번 Term 미공제"
    else:
        footer_status = "배분·원천징수·RPS 확인 완료"
    context = {
        "watermark": watermark,
        "number": esc(source.settlement_number),
        "invoice_number": esc(source.invoice_number),
        "issue_date": source.issue_date.strftime("%Y.%m.%d"),
        "company": esc(source.company_name),
        "candidate": esc(source.candidate_name),
        "start_date": source.start_date.strftime("%Y.%m.%d"),
        "position": esc(source.position),
        "salary": _money(source.annual_salary_krw),
        "guarantee": f"{source.guarantee_months}개월",
        "fee_percent": _percent_text(source.fee_percent),
        "invoice_amount": _money(result.invoice_amount_krw),
        "company_percent": contract["company_share_percent"] + "%",
        "company_share": _money(result.company_share_krw),
        "rps_value": esc(rps_value),
        "title_ko": esc(contract["document"]["title_ko"]),
        "issuer": esc(contract["issuer_name"]),
        "status_en": esc(contract["document"]["status_en"][source.rps_status]),
        "am_name": am_name,
        "am_percent": _percent_text(source.account_manager_percent),
        "am_gross": _money(result.account_manager_gross_krw),
        "am_tax": _money(result.account_manager_withholding_krw),
        "am_net": _money(result.account_manager_net_krw),
        "coworker_name": coworker_name,
        "coworker_percent": _percent_text(source.coworker_percent),
        "coworker_gross": _money(result.coworker_gross_krw),
        "coworker_tax": _money(result.coworker_withholding_krw),
        "coworker_net": _money(result.coworker_net_krw),
        "withholding": contract["withholding_percent"] + "%",
        "net_label": net_label,
        "footer_left": footer_left,
        "footer_status": footer_status,
        "footer_class": "warning" if source.draft else "complete",
    }
    return _HTML_TEMPLATE.format_map(context)


_HTML_TEMPLATE = """<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{number} Settlement</title><style>
@page {{ size:A4 portrait;margin:0; }} * {{ box-sizing:border-box; }} html,body {{ margin:0;background:#eef1f4;color:#17212b; }} body {{ font-family:"Apple SD Gothic Neo","Noto Sans KR","Malgun Gothic",Arial,sans-serif; }}
.page {{ position:relative;width:210mm;height:297mm;margin:0 auto;padding:17mm 18mm 14mm;background:#fff;overflow:hidden; }} .rule {{ height:4px;background:#123b5d;margin-bottom:10mm; }}
.draft {{ position:absolute;right:18mm;top:12mm;padding:2.5mm 4mm;border:1px solid #a34d47;border-radius:2mm;color:#8d3732;font-size:9pt;font-weight:800;letter-spacing:.08em; }} header {{ display:flex;justify-content:space-between;align-items:flex-start; }}
.eyebrow {{ margin:0 0 2mm;color:#547083;font-size:8.5pt;font-weight:800;letter-spacing:.13em; }} h1 {{ margin:0;color:#0f2e46;font-size:22pt;line-height:1.12; }} .subtitle {{ margin:2.5mm 0 0;color:#667784;font-size:10.5pt; }} .issuer {{ text-align:right;color:#0f2e46;font-weight:800;font-size:12pt; }} .issuer small {{ display:block;margin-top:2mm;color:#72808a;font-size:8pt;font-weight:500; }}
.meta {{ display:grid;grid-template-columns:1fr 1fr 1fr;margin-top:9mm;border-top:1px solid #cfd7dd;border-bottom:1px solid #cfd7dd; }} .meta div {{ padding:4mm 4mm 4mm 0; }} .meta div+div {{ padding-left:4mm;border-left:1px solid #e2e7eb; }} .label {{ display:block;margin-bottom:1.3mm;color:#778792;font-size:8pt;font-weight:800;letter-spacing:.05em; }} .value {{ color:#1a2c38;font-size:10pt;font-weight:750; }} .invoice-ref {{ display:block;margin-top:1mm;color:#778792;font-size:7pt;font-weight:650; }}
.section-title {{ margin:7mm 0 3mm;color:#496171;font-size:8.5pt;font-weight:850;letter-spacing:.13em; }} .basis {{ display:grid;grid-template-columns:1fr 1fr;border-top:2px solid #183f5e; }} .basis div {{ display:grid;grid-template-columns:34mm 1fr;align-items:center;min-height:10.5mm;border-bottom:1px solid #dfe5e9; }} .basis div:nth-child(odd) {{ padding-right:5mm; }} .basis div:nth-child(even) {{ padding-left:5mm;border-left:1px solid #e2e7eb; }} .basis span {{ color:#6e7d87;font-size:8.5pt;font-weight:750; }} .basis strong {{ color:#172b39;font-size:10pt; }}
.gross {{ display:flex;justify-content:space-between;align-items:center;margin-top:5mm;padding:4mm 5mm;background:#123b5d;border-radius:2mm;color:#fff; }} .gross span {{ font-size:10pt;font-weight:750; }} .gross strong {{ font-size:16pt; }}
.deductions {{ display:grid;grid-template-columns:1fr 1.5fr;gap:4mm; }} .deduction {{ padding:4mm 5mm;border:1px solid #cbd6dd;border-left:4px solid #2c678d;border-radius:2mm;background:#f7f9fa; }} .deduction strong {{ display:block;margin-top:2mm;color:#163e5a;font-size:11pt; }} .deduction.warn strong {{ color:#8a5c34;font-size:9.2pt; }}
table {{ width:100%;border-collapse:collapse;border-top:2px solid #183f5e;table-layout:fixed; }} th {{ padding:3mm 2mm;background:#f4f6f8;color:#60727e;font-size:7.5pt;text-align:right;border-bottom:1px solid #cfd7dd; }} th:first-child,td:first-child {{ text-align:left;width:25%; }} td {{ padding:3.5mm 2mm;color:#263b49;font-size:8.8pt;text-align:right;border-bottom:1px solid #dfe5e9; }} td strong {{ color:#143f5e;font-size:10pt; }} .person small {{ display:block;margin-top:1mm;color:#778792;font-size:7.5pt; }}
.note {{ margin-top:4mm;color:#72808a;font-size:7.8pt;line-height:1.55; }} footer {{ position:absolute;left:18mm;right:18mm;bottom:12mm;display:flex;justify-content:space-between;border-top:1px solid #d8dfe4;padding-top:3mm;color:#71808a;font-size:7.8pt; }} footer strong.warning {{ color:#8d3732; }} footer strong.complete {{ color:#214b67; }}
</style></head><body><main class="page"><div class="rule"></div>{watermark}
<header><div><p class="eyebrow">{status_en}</p><h1>{title_ko}</h1><p class="subtitle">성사 배분 내역</p></div><div class="issuer">{issuer}<small>Internal Settlement Statement</small></div></header>
<section class="meta"><div><span class="label">고객사</span><span class="value">{company}</span></div><div><span class="label">발행일</span><span class="value">{issue_date}</span></div><div><span class="label">SETTLEMENT NO.</span><span class="value">{number}<small class="invoice-ref">INVOICE {invoice_number}</small></span></div></section>
<p class="section-title">PLACEMENT & BILLING BASIS</p><section class="basis">
<div><span>입사자명</span><strong>{candidate}</strong></div><div><span>입사일</span><strong>{start_date}</strong></div>
<div><span>직책</span><strong>{position}</strong></div><div><span>보증기간</span><strong>{guarantee}</strong></div>
<div><span>기준 연봉</span><strong>{salary}</strong></div><div><span>수수료율</span><strong>{fee_percent}</strong></div></section>
<div class="gross"><span>청구서 발행 금액</span><strong>{invoice_amount}</strong></div>
<p class="section-title">COMPANY SHARE &amp; RPS STATUS</p><section class="deductions">
<div class="deduction"><span class="label">회사 배분 · {company_percent}</span><strong>{company_share}</strong></div>
<div class="deduction warn"><span class="label">RPS 회사 선결제 상태</span><strong>{rps_value}</strong></div></section>
<p class="section-title">ALLOCATION & NET PAYOUT</p><table><thead><tr><th>구분 / 이름</th><th>배분률</th><th>배분액</th><th>원천징수 {withholding}</th><th>{net_label}</th></tr></thead><tbody>
<tr><td class="person">Account Manager<small>{am_name}</small></td><td>{am_percent}</td><td>{am_gross}</td><td>{am_tax}</td><td><strong>{am_net}</strong></td></tr>
<tr><td class="person">Coworker<small>{coworker_name}</small></td><td>{coworker_percent}</td><td>{coworker_gross}</td><td>{coworker_tax}</td><td><strong>{coworker_net}</strong></td></tr>
</tbody></table><p class="note">배분률은 청구서 발행 금액 기준입니다. 회사 25%와 참여자 배분률의 합계는 반드시 100%여야 합니다. 세후 지급액은 각 참여자 배분액에서 3.3% 원천징수를 차감해 계산하며, RPS 상태가 미공제이면 이번 Term 지급액에서 차감하지 않고 추후 별도 공제합니다.</p>
<footer><span>{footer_left}</span><strong class="{footer_class}">{footer_status}</strong></footer>
</main></body></html>"""


def generate_files(
    input_path: Path, output_path: Path, contract_path: Path,
    chrome_path: str | None, overwrite: bool,
) -> tuple[DeductionResult, Path, Path, Path, str]:
    input_file = invoice_core._ensure_artifact_path(input_path, "input")
    output_file = invoice_core._ensure_artifact_path(output_path, "output")
    if output_file.suffix.lower() != ".pdf":
        raise InputError("output must end in .pdf")
    if not input_file.is_file():
        raise InputError(f"input file does not exist: {input_file}")
    try:
        payload = json.loads(input_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise InputError(f"cannot read input JSON: {error}") from error
    contract = load_contract(contract_path)
    result = calculate_settlement(validate_input(payload, contract), contract)
    fee_authority = None
    if not result.source.draft:
        try:
            fee_authority = invoice_core.storage_remote.verify_fee_authority(
                result.source.company_name,
                result.source.position,
                result.source.start_date,
                result.source.fee_percent,
                result.source.fee_agreement_ref,
            )
        except invoice_core.storage_remote.RemoteError as error:
            raise ContractError(f"final fee authority was not proven: {error}") from error
    html_text = render_html(result, contract)
    html_output = output_file.with_suffix(".html")
    metadata_output = output_file.with_suffix(".metadata.json")
    targets = (output_file, html_output, metadata_output)
    existing = [str(path) for path in targets if path.exists()]
    if existing and not overwrite:
        raise InputError(f"output already exists; use --overwrite: {', '.join(existing)}")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    chrome = invoice_core.find_chrome(chrome_path)
    with tempfile.TemporaryDirectory(prefix="deduction-", dir=output_file.parent) as temp_dir:
        root = Path(temp_dir)
        temp_html, temp_pdf = root / "deduction.html", root / "deduction.pdf"
        temp_metadata = root / "deduction.metadata.json"
        temp_html.write_text(html_text, encoding="utf-8")
        invoice_core._render_pdf(chrome, temp_html, temp_pdf, root / "chrome-profile")
        digest = invoice_core._sha256(temp_pdf)
        metadata = {
            "contract_version": contract["schema_version"],
            "settlement_number": result.source.settlement_number,
            "invoice_number": result.source.invoice_number,
            "fee_percent": format(result.source.fee_percent.normalize(), "f"),
            "fee_agreement_ref": result.source.fee_agreement_ref,
            "invoice_amount_krw": result.invoice_amount_krw,
            "company_share_krw": result.company_share_krw,
            "account_manager_gross_krw": result.account_manager_gross_krw,
            "account_manager_withholding_krw": result.account_manager_withholding_krw,
            "account_manager_net_krw": result.account_manager_net_krw,
            "coworker_gross_krw": result.coworker_gross_krw,
            "coworker_withholding_krw": result.coworker_withholding_krw,
            "coworker_net_krw": result.coworker_net_krw,
            "rps_advance_krw": result.source.rps_advance_krw,
            "rps_bearer": result.source.rps_bearer,
            "rps_status": result.source.rps_status,
            "company_net_krw": result.company_net_krw,
            "draft": result.source.draft,
            "fee_authority": "SUPABASE" if fee_authority else "UNVERIFIED_DRAFT",
            "fee_agreement_id": fee_authority["id"] if fee_authority else None,
            "input_sha256": hashlib.sha256(input_file.read_bytes()).hexdigest(),
            "pdf_sha256": digest,
        }
        temp_metadata.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        os.replace(temp_html, html_output)
        os.replace(temp_metadata, metadata_output)
        os.replace(temp_pdf, output_file)
    if any(not path.is_file() or path.stat().st_size == 0 for path in targets):
        raise RenderError("one or more deduction outputs are missing or empty")
    return result, output_file, html_output, metadata_output, digest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--chrome")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args(argv)
    try:
        result, pdf, html_file, metadata, digest = generate_files(
            args.input, args.output, args.contract, args.chrome, args.overwrite,
        )
    except (InputError, ContractError) as error:
        print(f"INPUT_ERROR: {error}", file=__import__("sys").stderr)
        return 2
    except (RenderError, OSError) as error:
        print(f"RENDER_ERROR: {error}", file=__import__("sys").stderr)
        return 3
    print("RENDER_VERDICT: PASS")
    print(
        "BUSINESS_STATUS: "
        + ("UNVERIFIED_DRAFT" if result.source.draft else "FEE_AUTHORITY_VERIFIED")
    )
    print(f"PDF: {pdf}")
    print(f"HTML: {html_file}")
    print(f"METADATA: {metadata}")
    print(f"INVOICE_AMOUNT_KRW: {result.invoice_amount_krw}")
    print(f"ACCOUNT_MANAGER_NET_KRW: {result.account_manager_net_krw}")
    print(f"COWORKER_NET_KRW: {result.coworker_net_krw}")
    print(f"PDF_SHA256: {digest}")
    print(f"CHECKED: {sum(path.stat().st_size > 0 for path in (pdf, html_file, metadata))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
