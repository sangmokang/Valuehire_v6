"""Portal registration packet builder for candidate-facing JD fields.

This layer is intentionally separate from render.py. Channel drafts may compact or
drop non-core units to fit message limits; registration packets must preserve each
source unit exactly once and expose field-by-field fit/readback status.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .measure import PORTAL_SAFE_SUBSTITUTE, measure, scan_portal_risk
from .units import JDSource, SECTION_LABEL, Unit, UnitError, load


DIRECT_APPLY = re.compile(
    r"(?:https?://|www\.|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}|"
    r"지원\s*(?:하기|버튼|링크|URL|메일|이메일|페이지|해\s*주세요)|"
    r"apply\s*(?:now|here)|career\.|recruit\.)",
    re.IGNORECASE,
)
DIRECT_ROUTE = re.compile(
    r"(?:[A-Za-z0-9-]+\.)+(?:com|co\.kr|kr|io|net|org)(?:/|\b)|"
    r"(?:당사|회사|자사|채용)\s*(?:홈페이지|페이지|사이트).*?(?:지원|접수)", re.IGNORECASE)


@dataclass(frozen=True)
class FieldSpec:
    name: str
    limit: int
    persistent: bool = True


def _contract() -> dict[str, Any]:
    path = Path(__file__).resolve().parents[2] / "contracts" / "jd-registration.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _specs(channel: str) -> dict[str, FieldSpec]:
    raw = _contract()["channels"][channel]
    specs = {raw["title"]["field"]: FieldSpec(raw["title"]["field"], raw["title"]["limit"])}
    for name, item in raw["fields"].items():
        specs[name] = FieldSpec(name, item["limit"], item.get("persistent", True))
    return specs

SARAMIN_OFFER = {"company", "team", "domain", "role", "growth", "conditions", "process", "documents"}
JOBKOREA_PROPOSAL = {"company", "team", "domain", "role", "growth", "conditions", "process", "documents"}
JOBKOREA_WORK = {"duties", "requirements"}
JOBKOREA_ST_CORE_SPARE = {"process", "conditions"}


def nfc_lf(text: str) -> str:
    return unicodedata.normalize("NFC", text.replace("\r\n", "\n").replace("\r", "\n"))


def counts(text: str) -> dict[str, int | dict[str, int]]:
    m = measure(text)
    return {
        "codepoints": m.codepoints,
        "utf16_units": m.utf16_units,
        "utf8_bytes": m.utf8_bytes,
        "without_whitespace": len("".join(text.split())),
        "lines": m.lines,
        "invisible": m.invisible,
        "suspicious_space": m.suspicious_space,
    }


def _title(src: JDSource, limit: int) -> str:
    raw = f"{src.company} {src.position}"
    title = nfc_lf(raw).strip()
    if max(counts(title)["codepoints"], counts(title)["utf16_units"]) > limit:  # type: ignore[arg-type]
        raise UnitError(f"title exceeds {limit}: {title}")
    return title


def _unit_line(unit: Unit) -> str:
    return nfc_lf(unit.full.strip())


def _unit_heading(unit: Unit) -> str:
    label = SECTION_LABEL.get(unit.section, unit.section)
    heading = nfc_lf(unit.heading.strip()) if unit.heading else ""
    return f"[{label}]" if not heading else f"[{label} | {heading}]"


def _join(units: list[Unit], *, intro: str = "") -> str:
    blocks: list[str] = []
    current = None
    bucket: list[str] = []
    for unit in units:
        heading = _unit_heading(unit)
        if current is not None and heading != current:
            blocks.append(current + "\n" + "\n".join(bucket))
            bucket = []
        current = heading
        bucket.append(_unit_line(unit))
    if current is not None:
        blocks.append(current + "\n" + "\n".join(bucket))
    if intro:
        blocks.insert(0, nfc_lf(intro.strip()))
    return nfc_lf("\n\n".join(b for b in blocks if b.strip()))


def _sanitize_portal(text: str, portal: str) -> tuple[str, list[dict[str, str | int]]]:
    changes = []
    for bad, (count, why) in scan_portal_risk(text, portal).items():
        if bad not in PORTAL_SAFE_SUBSTITUTE:
            raise UnitError(f"unmapped portal-risk character: {bad!r}")
        good = PORTAL_SAFE_SUBSTITUTE[bad]
        text = text.replace(bad, good)
        changes.append({"from": bad, "to": good, "count": count, "why": why})
    return text, changes


def _field(value: str, spec: FieldSpec, portal: str) -> dict[str, Any]:
    value, changes = _sanitize_portal(nfc_lf(value), portal)
    c = counts(value)
    errors: list[str] = []
    if max(c["codepoints"], c["utf16_units"]) > spec.limit:  # type: ignore[arg-type]
        errors.append(f"OVER_LIMIT:{spec.name}:{spec.limit}")
    if c["invisible"]:
        errors.append(f"INVISIBLE:{spec.name}")
    if portal == "saramin" and "'" in value:
        errors.append(f"UNSUPPORTED_APOSTROPHE:{spec.name}")
    tech_names = {"asp.net", "vb.net", "ado.net", "socket.io"}
    direct_routes = [m.group() for m in DIRECT_ROUTE.finditer(value)
                     if m.group().casefold() not in tech_names]
    if DIRECT_APPLY.search(value) or direct_routes:
        errors.append(f"FORBIDDEN_TEXT:{spec.name}")
    return {"value": value, "limit": spec.limit, "persistent": spec.persistent,
            "counts": c, "errors": errors, "portal_changes": changes}


def _ordered(src: JDSource, predicate) -> list[Unit]:
    return [u for u in src.units if predicate(u)]


def _source_order(src: JDSource, units: list[Unit]) -> list[Unit]:
    ids = {u.id for u in units}
    return [u for u in src.units if u.id in ids]


def _append_if_fits(src: JDSource, units: list[Unit], unit: Unit, spec: FieldSpec) -> tuple[list[Unit], bool]:
    candidate = _source_order(src, units + [unit])
    if _fits(candidate, spec, "jobkorea"):
        return candidate, True
    return units, False


def _assert_source(src: JDSource) -> None:
    ready = {"OK", "READY", "READY_SOURCE", "VERIFIED", "FETCHED_VERBATIM", "VERIFIED_USER_INPUT"}
    if src.source_status not in ready:
        raise UnitError(f"source_status not ready: {src.source_status}")


def _finish(src: JDSource, channel: str, fields: dict[str, dict[str, Any]],
            assignments: dict[str, list[str]], overflow: list[str] | None = None) -> dict[str, Any]:
    assigned = [uid for ids in assignments.values() for uid in ids]
    expected = [u.id for u in src.units]
    errors: list[str] = []
    if sorted(assigned) != sorted(expected) or len(assigned) != len(set(assigned)):
        errors.append(f"UNIT_ASSIGNMENT_MISMATCH:expected_once={expected}:actual={assigned}")
    for name, field in fields.items():
        errors.extend(field["errors"])
    status = "READY_FOR_UI" if not errors else "BLOCKED"
    packet = {
        "schema": "jd-registration/2026-09-22",
        "channel": channel,
        "source": {"company": src.company, "position": src.position, "jd_id": src.jd_id,
                   "source_url": src.source_url, "source_status": src.source_status},
        "source_hash": _source_hash(src),
        "source_hash_version": 2,
        "units": [{"id": u.id, "section": u.section, "kind": u.kind,
                   "full": u.full, "source": u.source} for u in src.units],
        "status": status,
        "fields": fields,
        "assignments": assignments,
        "unit_order": expected,
        "errors": errors,
        "permanent_overflow_units": overflow or [],
        "readback_status": "NOT_VERIFIED",
    }
    if channel == "jobkorea":
        packet["proposal_status"] = "NOT_VERIFIED"
        packet["position_status"] = "NOT_VERIFIED"
    return packet


def _fits(units: list[Unit], spec: FieldSpec, portal: str, intro: str = "") -> bool:
    field = _field(_join(units, intro=intro), spec, portal)
    return not field["errors"]


def build_packet(src: JDSource, channel: str) -> dict[str, Any]:
    _assert_source(src)
    if channel == "saramin":
        return _build_saramin(src)
    if channel == "jobkorea":
        return _build_jobkorea(src)
    raise UnitError(f"unsupported registration channel: {channel}")


def _build_saramin(src: JDSource) -> dict[str, Any]:
    specs = _specs("saramin")
    title = _title(src, specs["hiringTitle"].limit)
    offer_units = _ordered(src, lambda u: u.section in SARAMIN_OFFER)
    work_units = _ordered(src, lambda u: u.section not in SARAMIN_OFFER)
    intro = "후속 절차는 밸류커넥트를 통해 안내드립니다."
    offer_units, work_units = _balance_saramin(offer_units, work_units, specs, intro)
    fields = {
        "hiringTitle": _field(title, specs["hiringTitle"], "saramin"),
        "offerComment": _field(_join(offer_units, intro=intro), specs["offerComment"], "saramin"),
        "chargeWork": _field(_join(work_units), specs["chargeWork"], "saramin"),
    }
    return _finish(src, "saramin", fields, {
        "offerComment": [u.id for u in offer_units],
        "chargeWork": [u.id for u in work_units],
    })


def _build_jobkorea(src: JDSource) -> dict[str, Any]:
    specs = _specs("jobkorea")
    title = _title(src, specs["GI_PSTN"].limit)
    proposal = _ordered(src, lambda u: u.section in JOBKOREA_PROPOSAL)
    work = _ordered(src, lambda u: u.section in JOBKOREA_WORK)
    preferred = _ordered(src, lambda u: u.section == "preferred")
    st_units = list(preferred)
    work_overflow: list[Unit] = []
    proposal_overflow: list[Unit] = []
    while work and not _fits(work, specs["EXEC_WORK"], "jobkorea"):
        work_overflow.append(work.pop(0))
    while st_units and not _fits(st_units, specs["ST"], "jobkorea"):
        proposal_overflow.append(st_units.pop(0))
    for moved in work_overflow:
        st_units, placed = _append_if_fits(src, st_units, moved, specs["ST"])
        if not placed:
            proposal_overflow.append(moved)
    if work_overflow:
        for moved in _ordered(src, lambda u: u.section in JOBKOREA_ST_CORE_SPARE and u.kind == "core"):
            st_units, placed = _append_if_fits(src, st_units, moved, specs["ST"])
            if placed:
                proposal = [u for u in proposal if u.id != moved.id]
        for moved in _ordered(src, lambda u: u.section == "documents" and u.kind == "core"):
            st_units, placed = _append_if_fits(src, st_units, moved, specs["ST"])
            if placed:
                proposal = [u for u in proposal if u.id != moved.id]
    proposal = _source_order(src, [u for u in proposal + proposal_overflow if u.id not in {s.id for s in st_units}])
    intro = "후속 절차는 밸류커넥트를 통해 안내드립니다."
    fields = {
        "GI_PSTN": _field(title, specs["GI_PSTN"], "jobkorea"),
        "proposalMessage": _field(_join(proposal, intro=intro), specs["proposalMessage"], "jobkorea"),
        "EXEC_WORK": _field(_join(work), specs["EXEC_WORK"], "jobkorea"),
        "ST": _field(_join(st_units), specs["ST"], "jobkorea"),
    }
    return _finish(src, "jobkorea", fields, {
        "proposalMessage": [u.id for u in proposal],
        "EXEC_WORK": [u.id for u in work],
        "ST": [u.id for u in st_units],
    }, [u.id for u in proposal_overflow])


def _balance_saramin(offer: list[Unit], work: list[Unit], specs: dict[str, FieldSpec],
                     intro: str) -> tuple[list[Unit], list[Unit]]:
    offer, work = list(offer), list(work)
    while offer and not _fits(offer, specs["offerComment"], "saramin", intro=intro):
        work.insert(0, offer.pop())
    while work and not _fits(work, specs["chargeWork"], "saramin"):
        offer.append(work.pop(0))
    return offer, work


def _source_hash(src: JDSource) -> str:
    payload = json.dumps({"jd_id": src.jd_id, "company": src.company, "position": src.position,
                         "source_url": src.source_url, "source_status": src.source_status,
                         "units": [(u.id, u.section, u.full) for u in src.units]},
                         ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _field_names(channel: str) -> set[str]:
    return set(_specs(channel))


def _assignment_errors(packet: dict[str, Any]) -> list[str]:
    assignments = packet.get("assignments", {})
    assigned = [uid for ids in assignments.values() for uid in ids]
    units = packet.get("units", [])
    expected = [unit["id"] for unit in units]
    field_names = _field_names(packet["channel"])
    assignment_fields = field_names - {_contract()["channels"][packet["channel"]]["title"]["field"]}
    errors: list[str] = []
    if not units:
        errors.append("PACKET_ZERO_UNITS")
    if set(assignments) != assignment_fields:
        errors.append(f"PACKET_ASSIGNMENT_FIELDS_MISMATCH:expected={sorted(assignment_fields)}:actual={sorted(assignments)}")
    if sorted(assigned) != sorted(expected) or len(assigned) != len(set(assigned)):
        errors.append(f"PACKET_UNIT_ASSIGNMENT_MISMATCH:expected_once={expected}:actual={assigned}")
    unit_by_id = {unit["id"]: unit for unit in units}
    fields = packet.get("fields", {})
    for field_name, ids in assignments.items():
        field_value = fields.get(field_name, {}).get("value", "")
        for uid in ids:
            unit = unit_by_id.get(uid)
            if not unit:
                continue
            expected_text = _sanitize_portal(nfc_lf(unit["full"].strip()), packet["channel"])[0]
            if expected_text and expected_text not in field_value:
                errors.append(f"PACKET_UNIT_TEXT_MISSING:{field_name}:{uid}")
    return errors


def _packet_integrity_errors(channel: str, packet: dict[str, Any]) -> list[str]:
    specs = _specs(channel)
    fields = packet.get("fields", {})
    errors: list[str] = []
    if packet.get("errors"):
        errors.append("PACKET_UNRESOLVED_ERRORS")
    source_payload = json.dumps({
        "jd_id": packet.get("source", {}).get("jd_id"),
        **{k: packet.get("source", {}).get(k) for k in
           ("company", "position", "source_url", "source_status")},
        "units": [(u["id"], u["section"], u["full"]) for u in packet.get("units", [])],
    }, ensure_ascii=False, sort_keys=True)
    if hashlib.sha256(source_payload.encode("utf-8")).hexdigest() != packet.get("source_hash"):
        errors.append("PACKET_SOURCE_HASH_MISMATCH")
    if packet.get("status") != "READY_FOR_UI":
        errors.append(f"PACKET_NOT_READY:{packet.get('status')}")
    if set(fields) != set(specs):
        errors.append(f"PACKET_FIELD_SET_MISMATCH:expected={sorted(specs)}:actual={sorted(fields)}")
    for name, spec in specs.items():
        field = fields.get(name)
        if not isinstance(field, dict):
            continue
        if field.get("limit") != spec.limit:
            errors.append(f"PACKET_LIMIT_TAMPER:{name}")
        if field.get("persistent", True) != spec.persistent:
            errors.append(f"PACKET_PERSISTENT_TAMPER:{name}")
        if field.get("errors"):
            errors.append(f"PACKET_FIELD_ERRORS:{name}:{field.get('errors')}")
        value = field.get("value")
        if not isinstance(value, str):
            errors.append(f"PACKET_VALUE_NOT_TEXT:{name}")
            continue
        canonical = _sanitize_portal(nfc_lf(value), channel)[0]
        if value != canonical:
            errors.append(f"PACKET_VALUE_NOT_CANONICAL:{name}")
        recomputed = _field(value, spec, channel)
        if recomputed["errors"]:
            errors.extend(f"PACKET_{err}" for err in recomputed["errors"])
        if max(recomputed["counts"]["codepoints"], recomputed["counts"]["utf16_units"]) > spec.limit:
            errors.append(f"PACKET_VALUE_OVER_LIMIT:{name}")
        if counts(value) != field.get("counts"):
            errors.append(f"PACKET_COUNTS_TAMPER:{name}")
    errors.extend(_assignment_errors(packet))
    return errors


def _approved_disabled_title_values(packet: dict[str, Any], name: str) -> set[str]:
    # Alternate metadata keys cannot authorize a different title after generation.
    value = packet.get("fields", {}).get(name, {}).get("value", "")
    return {value} if value else set()


def _disabled_title_bound(packet: dict[str, Any], observed: dict[str, Any], name: str) -> bool:
    if packet.get("channel") != "jobkorea" or name != "GI_PSTN":
        return False
    binding = observed.get("field_bindings", {}).get(name)
    if not isinstance(binding, dict):
        return False
    if binding.get("kind") not in {"existing_disabled_title", "disabled_title"}:
        return False
    if binding.get("disabled") is not True:
        return False
    value = nfc_lf(str(binding.get("value", "")).strip())
    identity = binding.get("canonical_identity")
    source = packet.get("source", {})
    canonical = (
        isinstance(identity, dict)
        and identity.get("company") == source.get("company")
        and identity.get("position") == source.get("position")
    )
    raw_value = str(binding.get("value", "")).strip()
    return (
        bool(value)
        and raw_value == value
        and value in _approved_disabled_title_values(packet, name)
        and max(counts(raw_value)["codepoints"], counts(raw_value)["utf16_units"]) <= _specs("jobkorea")[name].limit
        and canonical
    )  # type: ignore[arg-type]


def readback_compare(packet: dict[str, Any], observed: dict[str, Any]) -> dict[str, Any]:
    try:
        if packet.get("channel") not in {"saramin", "jobkorea"}:
            raise UnitError("UNSUPPORTED_CHANNEL")
        return _readback_compare(packet, observed)
    except (KeyError, TypeError, ValueError, AttributeError, OSError) as exc:
        return {"status": "FAIL", "channel": packet.get("channel") if isinstance(packet, dict) else None,
                "position_status": "FAIL", "proposal_status": "NOT_VERIFIED",
                "errors": [f"INVALID_INPUT_OR_DEPENDENCY:{type(exc).__name__}:{exc}"],
                "bound_fields": [], "mismatches": [], "compared_fields": []}


def _readback_compare(packet: dict[str, Any], observed: dict[str, Any]) -> dict[str, Any]:
    channel = packet["channel"]
    if observed.get("channel") != channel:
        return {"status": "FAIL", "errors": ["CHANNEL_MISMATCH"], "bound_fields": []}
    if not observed.get("position_id"):
        return {"status": "FAIL", "errors": ["MISSING_POSITION_ID"], "bound_fields": []}
    specs = _specs(channel)
    expected_fields = packet["fields"]
    observed_fields = observed.get("fields", {})
    errors = _packet_integrity_errors(channel, packet)
    extra = sorted(set(observed_fields) - set(expected_fields))
    if extra:
        errors.append(f"OBSERVED_EXTRA_FIELDS:{extra}")
    if observed.get("readback_kind") != "persisted_reopen":
        errors.append("POSITION_NOT_PERSISTED_REOPEN")
    if observed.get("fresh_saved_position") is not True:
        errors.append("FRESH_SAVED_POSITION_REQUIRED")
    mismatches: list[str] = []
    position_mismatches: list[str] = []
    proposal_mismatches: list[str] = []
    position_fields = []
    proposal_fields = []
    bound_fields: list[str] = []
    for name, expected in expected_fields.items():
        if name not in observed_fields:
            if _disabled_title_bound(packet, observed, name):
                position_fields.append((name, True))
                bound_fields.append(name)
            continue
        raw_observed = observed_fields[name]
        ok = False
        if not isinstance(raw_observed, str):
            errors.append(f"OBSERVED_VALUE_NOT_TEXT:{name}")
        else:
            if raw_observed != nfc_lf(raw_observed):
                errors.append(f"OBSERVED_VALUE_NOT_CANONICAL:{name}")
            if max(counts(raw_observed)["codepoints"], counts(raw_observed)["utf16_units"]) > expected["limit"]:
                errors.append(f"OBSERVED_VALUE_OVER_LIMIT:{name}")
            ok = raw_observed == expected["value"]
        target = proposal_fields if not expected.get("persistent", True) else position_fields
        target.append((name, ok))
        if not ok:
            mismatches.append(name)
            if expected.get("persistent", True):
                position_mismatches.append(name)
            else:
                proposal_mismatches.append(name)
    persistent_names = [n for n, f in expected_fields.items() if f.get("persistent", True)]
    transient_names = [n for n, f in expected_fields.items() if not f.get("persistent", True)]
    missing_persistent = [n for n in persistent_names if not any(n == seen for seen, _ in position_fields)]
    if missing_persistent:
        errors.append(f"OBSERVED_MISSING_FIELDS:{missing_persistent}")
    position_complete = (
        not missing_persistent
        and not position_mismatches
        and observed.get("readback_kind") == "persisted_reopen"
        and observed.get("fresh_saved_position") is True
        and not any(e.startswith("PACKET_") or e.startswith("OBSERVED_EXTRA_FIELDS") for e in errors)
        and not any(e.startswith("OBSERVED_VALUE_") for e in errors)
    )
    proposal_exact = bool(transient_names) and all(
        any(n == seen and ok for seen, ok in proposal_fields) for n in transient_names)
    if channel != "jobkorea":
        proposal_status = "NOT_APPLICABLE"
        status = "COMPLETE" if position_complete and not errors else "FAIL"
    else:
        if (proposal_exact and observed.get("readback_kind") == "persisted_reopen"
                and observed.get("fresh_saved_proposal") is True and observed.get("proposal_id")):
            proposal_status = "COMPLETE"
        elif proposal_exact:
            proposal_status = "EDITOR_VERIFIED"
        elif proposal_mismatches:
            proposal_status = "NOT_SAVED"
        else:
            proposal_status = "NOT_VERIFIED"
        status = "COMPLETE" if position_complete and proposal_status == "COMPLETE" else "PARTIAL"
        if not position_complete:
            status = "FAIL"
    if errors and channel != "jobkorea":
        status = "FAIL"
    return {
        "status": status,
        "channel": channel,
        "position_id": observed.get("position_id"),
        "proposal_id": observed.get("proposal_id"),
        "position_status": "COMPLETE" if position_complete and not position_mismatches else "FAIL",
        "proposal_status": proposal_status,
        "mismatches": mismatches,
        "errors": errors,
        "bound_fields": bound_fields,
        "compared_fields": sorted(observed_fields),
    }


def _cmd_packet(args: argparse.Namespace) -> int:
    src = load(args.source)
    packet = build_packet(src, args.channel)
    text = json.dumps(packet, ensure_ascii=False, indent=2)
    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0 if packet["status"] == "READY_FOR_UI" else 2


def _cmd_readback(args: argparse.Namespace) -> int:
    packet = json.loads(Path(args.packet).read_text(encoding="utf-8"))
    observed = json.loads(Path(args.observed).read_text(encoding="utf-8"))
    result = readback_compare(packet, observed)
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    if result["status"] == "COMPLETE":
        return 0
    if result["status"] == "PARTIAL":
        return 3
    return 2


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m jd_channels")
    sub = parser.add_subparsers(dest="command", required=True)
    packet = sub.add_parser("packet")
    packet.add_argument("--source", required=True)
    packet.add_argument("--channel", choices=("saramin", "jobkorea"), required=True)
    packet.add_argument("--output")
    packet.set_defaults(func=_cmd_packet)
    readback = sub.add_parser("readback")
    readback.add_argument("--packet", required=True)
    readback.add_argument("--observed", required=True)
    readback.add_argument("--output")
    readback.set_defaults(func=_cmd_readback)
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
