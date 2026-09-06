#!/usr/bin/env python3
"""Deterministic gate and CEO brief renderer for weekly-ops evidence bundles."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import unicodedata
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

SCRIPT_DIRECTORY = Path(__file__).resolve().parent
if str(SCRIPT_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIRECTORY))

from activity_gate import (
    apply_coverage_comparability,
    build_channel_coverage,
    validate_career_summaries,
    validate_consultant_roster,
    validate_outreach_channel_diagnostics,
    validate_outreach_events,
)
from brief_renderer import render_brief, render_html, render_publication_report
from contract_gate import (
    ALLOWED_EMAIL_TARGETS,
    REQUIRED_PUBLICATION_TARGETS,
    capability_blockers,
    find_sensitive_text,
    find_sensitive_values,
    publication_receipts,
    publication_state,
    validate_dedupe_decisions,
    validate_source_snapshots,
    validate_zero_result_assertions,
)
from operating_gate import validate_operating_snapshot
from schema_gate import (
    final_output_violations,
    find_forbidden_fields,
    find_unknown_fields,
    sanitized_blocked_result,
)


SCHEMA_VERSION = "weekly-ops-input-v1"
SCORE_VERSION = "weekly-priority-v1"
CONSULTANT_FOCUS_VERSION = "consultant-focus-v2"
ORIGINS = {
    "SCRAPED_STAGING",
    "CLIENT_REQUESTED",
    "CLIENT_SHARED",
    "INTERNAL_CREATED",
}
INTENT_SCORES = {
    "REQUESTED": 40,
    "POSITION_SHARED": 30,
    "REQUIREMENT_CHANGED": 20,
    "PIPELINE_FEEDBACK": 15,
    "REFERENCE_ONLY": 0,
    "NONE": 0,
}
ORIGIN_INTENTS = {
    "SCRAPED_STAGING": frozenset({"REFERENCE_ONLY", "NONE"}),
    "CLIENT_REQUESTED": frozenset({"REQUESTED", "REQUIREMENT_CHANGED", "PIPELINE_FEEDBACK"}),
    "CLIENT_SHARED": frozenset({"POSITION_SHARED", "REQUIREMENT_CHANGED", "PIPELINE_FEEDBACK"}),
    "INTERNAL_CREATED": frozenset({"REFERENCE_ONLY", "NONE"}),
}
CLIENT_PRIORITY_POINTS = {
    "TOP": 50,
    "HIGH": 25,
    "NORMAL": 0,
    "NONE": 0,
}
LIFECYCLES = {"ACTIVE", "PIPELINE", "CLOSING", "CLOSED"}
CATEGORIES = {
    "backend/fullstack/cto",
    "ai/ml/data",
    "po/pm/기획",
    "frontend",
    "designer",
    "sales/bd",
    "marketing",
    "devops/sre/security/qa",
    "hr/finance/strategy/etc",
    "c-level",
    "app",
    "etc",
    "UNCLASSIFIED",
}
DIFFICULTY_POINTS = {
    "scarcity": {"LOW": 0, "MEDIUM": 20, "HIGH": 35},
    "seniority": {"LOW": 0, "MEDIUM": 15, "HIGH": 25},
    "constraints": {"LOW": 0, "MEDIUM": 15, "HIGH": 25},
    "funnel_friction": {"LOW": 0, "MEDIUM": 8, "HIGH": 15},
}
def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def parse_datetime(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("timezone_required")
    return parsed


def normalized_key(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).casefold()
    return re.sub(r"\s+", " ", normalized).strip()


def recency_points(event_at: datetime, meeting_at: datetime) -> int:
    age = meeting_at - event_at
    if age < timedelta(0):
        return 0
    if age <= timedelta(days=3):
        return 25
    if age <= timedelta(days=7):
        return 15
    if age <= timedelta(days=14):
        return 5
    return 0


def deadline_points(deadline_days: Any) -> int:
    if deadline_days is None:
        return 0
    if not isinstance(deadline_days, int) or deadline_days < 0:
        raise ValueError("deadline_days_invalid")
    if deadline_days <= 7:
        return 25
    if deadline_days <= 14:
        return 15
    return 0


def score_position(position: dict[str, Any], meeting_at: datetime) -> dict[str, Any]:
    event_at = parse_datetime(position["event_at"])
    urgency = INTENT_SCORES[position["intent"]]
    urgency += recency_points(event_at, meeting_at)
    urgency += deadline_points(position.get("deadline_days"))
    urgency += 10 if position.get("late_stage") is True else 0
    urgency += CLIENT_PRIORITY_POINTS[position.get("client_priority", "NONE")]
    urgency = min(100, urgency)

    difficulty = 0
    evidence = position["difficulty"]
    for dimension, point_map in DIFFICULTY_POINTS.items():
        difficulty += point_map[evidence[dimension]]
    difficulty = min(100, difficulty)

    priority = round(0.7 * urgency + 0.3 * difficulty)
    if position["origin"] == "SCRAPED_STAGING":
        priority = min(20, priority)
    return {
        "urgency": urgency,
        "difficulty": difficulty,
        "priority": priority,
        "version": SCORE_VERSION,
    }


def validate_run(run: Any, errors: list[str]) -> dict[str, datetime] | None:
    required = ("meeting_at", "window_start", "window_end_exclusive", "late_alert_end")
    if not isinstance(run, dict) or any(not run.get(key) for key in required):
        errors.append("RUN_CONTRACT_INVALID")
        return None
    try:
        parsed = {key: parse_datetime(run[key]) for key in required}
    except (TypeError, ValueError):
        errors.append("RUN_DATETIME_INVALID")
        return None
    window_is_week = (
        parsed["window_start"].weekday() == 0
        and parsed["window_end_exclusive"].weekday() == 0
        and parsed["window_start"].time() == datetime.min.time()
        and parsed["window_end_exclusive"].time() == datetime.min.time()
        and parsed["window_end_exclusive"] - parsed["window_start"] == timedelta(days=7)
        and parsed["window_end_exclusive"].date() == parsed["meeting_at"].date()
        and all(value.utcoffset() == timedelta(hours=9) for value in parsed.values())
    )
    if not window_is_week or not (
        parsed["window_start"] < parsed["window_end_exclusive"]
        <= parsed["meeting_at"]
        <= parsed["late_alert_end"]
    ):
        errors.append("RUN_WINDOW_INVALID")
    return parsed


def validate_difficulty(value: Any) -> bool:
    if not isinstance(value, dict) or set(value) != set(DIFFICULTY_POINTS):
        return False
    return all(value[key] in DIFFICULTY_POINTS[key] for key in DIFFICULTY_POINTS)


def validate_positions(
    positions: Any,
    run: dict[str, datetime] | None,
    valid_evidence_refs: set[str],
    errors: list[str],
) -> list[dict[str, Any]]:
    if not isinstance(positions, list):
        errors.append("POSITIONS_INVALID")
        return []
    validated: list[dict[str, Any]] = []
    canonical_keys: dict[tuple[str, str], str] = {}
    canonical_ids: set[str] = set()
    required = {
        "canonical_id",
        "company",
        "title",
        "category",
        "origin",
        "intent",
        "event_at",
        "difficulty",
        "evidence_refs",
        "action",
    }
    for position in positions:
        if not isinstance(position, dict) or not required.issubset(position):
            errors.append("POSITION_CONTRACT_INVALID")
            continue
        canonical_id = position["canonical_id"]
        if not isinstance(canonical_id, str) or not canonical_id or canonical_id in canonical_ids:
            errors.append("DUPLICATE_CANONICAL_ID")
            continue
        canonical_ids.add(canonical_id)
        if position["origin"] not in ORIGINS or position["intent"] not in INTENT_SCORES:
            errors.append("POSITION_ENUM_INVALID")
            continue
        if position["intent"] not in ORIGIN_INTENTS[position["origin"]]:
            errors.append(
                "SCRAPED_CUSTOMER_INTENT_CONFLICT"
                if position["origin"] == "SCRAPED_STAGING"
                else "POSITION_ORIGIN_INTENT_MISMATCH"
            )
            continue
        if position.get("client_priority", "NONE") not in CLIENT_PRIORITY_POINTS:
            errors.append("POSITION_ENUM_INVALID")
            continue
        if position.get("lifecycle", "ACTIVE") not in LIFECYCLES:
            errors.append("POSITION_ENUM_INVALID")
            continue
        if position["category"] not in CATEGORIES or not validate_difficulty(position["difficulty"]):
            errors.append("POSITION_ENUM_INVALID")
            continue
        if not isinstance(position["evidence_refs"], list) or not position["evidence_refs"]:
            errors.append("POSITION_EVIDENCE_MISSING")
            continue
        if any(not isinstance(ref, str) or ref not in valid_evidence_refs for ref in position["evidence_refs"]):
            errors.append("POSITION_EVIDENCE_UNRESOLVED")
            continue
        key = (normalized_key(position["company"]), normalized_key(position["title"]))
        prior_id = canonical_keys.get(key)
        if prior_id is not None and prior_id != position["canonical_id"]:
            errors.append("DUPLICATE_CANONICAL_KEY")
        canonical_keys[key] = position["canonical_id"]
        try:
            scored = dict(position)
            scored["client_priority"] = position.get("client_priority", "NONE")
            scored["lifecycle"] = position.get("lifecycle", "ACTIVE")
            scored["score"] = score_position(position, run["meeting_at"] if run else datetime.now().astimezone())
            event_at = parse_datetime(position["event_at"])
            if run and event_at >= run["late_alert_end"]:
                errors.append("EVENT_AFTER_CUTOFF")
            scored["period"] = (
                "LATE_ALERT" if run and event_at >= run["window_end_exclusive"] else "WEEKLY"
            )
            validated.append(scored)
        except (KeyError, TypeError, ValueError):
            errors.append("POSITION_SCORE_INPUT_INVALID")
    return validated


def stable_projection(
    bundle: dict[str, Any],
    positions: list[dict[str, Any]],
    career_summaries: list[dict[str, Any]],
    dedupe_decisions: list[dict[str, Any]],
    operating_snapshot: dict[str, Any],
) -> dict[str, Any]:
    target_contracts = [
        {
            "name": target.get("name"),
            "target_id": target.get("target_id"),
            "required": target.get("name") in REQUIRED_PUBLICATION_TARGETS,
        }
        for target in bundle.get("publication_targets", [])
        if isinstance(target, dict)
    ]
    projection = {
        "schema_version": bundle.get("schema_version"),
        "run": bundle.get("run"),
        "capabilities": bundle.get("capabilities"),
        "source_snapshots": bundle.get("source_snapshots"),
        "dedupe_decisions": dedupe_decisions,
        "positions": positions,
        "career_page_summaries": career_summaries,
        "operating_snapshot": operating_snapshot,
        "outreach_events": bundle.get("outreach_events", []),
        "zero_result_assertions": bundle.get("zero_result_assertions", []),
        "publication_target_contracts": target_contracts,
        "score_version": SCORE_VERSION,
        "consultant_focus_version": CONSULTANT_FOCUS_VERSION,
    }
    if "outreach_channel_diagnostics" in bundle:
        projection["outreach_channel_diagnostics"] = bundle.get("outreach_channel_diagnostics")
    if "consultant_roster" in bundle:
        projection["consultant_roster"] = bundle.get("consultant_roster")
    return projection


def capability_requirements(capabilities: Any) -> tuple[bool, bool, bool]:
    statuses = {
        item.get("name"): item.get("status")
        for item in capabilities
        if isinstance(item, dict)
    } if isinstance(capabilities, list) else {}
    career_complete = statuses.get("career_pages_read") == "PASS"
    outreach_complete = all(
        statuses.get(name) == "PASS"
        for name in (
            "jobkorea_outreach_read",
            "saramin_outreach_read",
            "linkedin_outreach_read",
        )
    )
    core_position_complete = all(
        statuses.get(name) == "PASS"
        for name in ("db_read", "gmail_read", "clickup_read", "notion_read")
    )
    return career_complete, outreach_complete, core_position_complete


def capability_passed(capabilities: Any, name: str) -> bool:
    return any(
        isinstance(item, dict)
        and item.get("name") == name
        and item.get("status") == "PASS"
        for item in capabilities
    ) if isinstance(capabilities, list) else False


def required_zero_collections(
    positions: list[dict[str, Any]],
    consultant_focus: list[dict[str, Any]],
    outreach_complete: bool,
    core_position_complete: bool,
) -> set[str]:
    required: set[str] = set()
    if core_position_complete and not positions:
        required.add("positions")
    if outreach_complete and not consultant_focus:
        required.add("outreach_events")
    return required


def customer_priority_ids(positions: list[dict[str, Any]]) -> list[str]:
    return [
        item["canonical_id"]
        for item in sorted(positions, key=lambda item: -item["score"]["priority"])
        if item["origin"] in {"CLIENT_REQUESTED", "CLIENT_SHARED"}
        and item["lifecycle"] != "CLOSED"
    ]


def assemble_result(
    bundle: dict[str, Any],
    positions: list[dict[str, Any]],
    consultant_focus: list[dict[str, Any]],
    channel_coverage: list[dict[str, Any]],
    excluded_rows: list[dict[str, str]],
    career_summaries: list[dict[str, Any]],
    operating_snapshot: dict[str, Any],
    errors: list[str],
    source_blockers: list[str],
    data_status: str,
    snapshot_id: str,
    input_hash: str,
    brief: str,
) -> dict[str, Any]:
    content_hash = hashlib.sha256(brief.encode("utf-8")).hexdigest()
    error_count_before_publication = len(errors)
    publication_blockers = publication_state(
        bundle.get("publication_targets"), snapshot_id, content_hash, errors
    )
    publication_errors = sorted(set(errors[error_count_before_publication:]))
    publication_verdict = (
        "BLOCKED" if len(errors) > error_count_before_publication
        else "PARTIAL" if publication_blockers
        else "PASS"
    )
    verdict = (
        "BLOCKED" if errors
        else "PARTIAL" if source_blockers or publication_blockers
        else "PASS"
    )
    publication_report = render_publication_report(
        publication_verdict,
        sorted(set(publication_blockers)),
        publication_errors,
        snapshot_id,
        content_hash,
    )
    return {
        "schema_version": "weekly-ops-publication-v1",
        "verdict": verdict,
        "data_verdict": data_status,
        "publication_verdict": publication_verdict,
        "publication_errors": publication_errors,
        "report_snapshot_id": snapshot_id,
        "input_hash": input_hash,
        "content_hash": content_hash,
        "score_version": SCORE_VERSION,
        "consultant_focus_version": CONSULTANT_FOCUS_VERSION,
        "positions": positions,
        "customer_priority_ids": customer_priority_ids(positions),
        "consultant_focus": consultant_focus,
        "channel_coverage": channel_coverage,
        "excluded_rows": excluded_rows,
        "career_page_summaries": career_summaries,
        "operating_snapshot": operating_snapshot,
        "brief_markdown": brief,
        "publication_report_markdown": publication_report,
        "receipts": publication_receipts(bundle.get("publication_targets")),
        "errors": sorted(set(errors)),
        "blockers": sorted(set(source_blockers + publication_blockers)),
    }


def input_boundary_errors(bundle: dict[str, Any]) -> list[str]:
    """WU-1 허용목록·금지 키·민감 값의 입력 경계 검사(fail-closed)."""
    errors: list[str] = []
    if bundle.get("schema_version") != SCHEMA_VERSION:
        errors.append("SCHEMA_VERSION_INVALID")
    if find_forbidden_fields(bundle):
        errors.append("FORBIDDEN_SENSITIVE_FIELD")
    if find_unknown_fields(bundle):
        errors.append("FORBIDDEN_UNKNOWN_FIELD")
    if find_sensitive_values(bundle):
        errors.append("FORBIDDEN_SENSITIVE_VALUE")
    return errors


def evaluate(bundle: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = input_boundary_errors(bundle)
    sensitive_values_found = "FORBIDDEN_SENSITIVE_VALUE" in errors
    run = validate_run(bundle.get("run"), errors)
    source_blockers = capability_blockers(bundle.get("capabilities"), errors)
    cutoff = run["meeting_at"] if run else None
    source_snapshot_ids, evidence_refs, snapshot_evidence_refs, snapshot_blockers = (
        validate_source_snapshots(bundle.get("source_snapshots"), parse_datetime, errors, cutoff)
    )
    positions = validate_positions(bundle.get("positions"), run, evidence_refs, errors)
    canonical_ids = {position["canonical_id"] for position in positions}
    dedupe_decisions = validate_dedupe_decisions(
        bundle.get("dedupe_decisions"), canonical_ids, evidence_refs, errors
    )
    career_complete, outreach_complete, core_position_complete = capability_requirements(bundle.get("capabilities"))
    career_summaries, career_blockers = validate_career_summaries(
        bundle.get("career_page_summaries"),
        source_snapshot_ids,
        parse_datetime,
        errors,
        require_complete=career_complete,
    )
    operating_snapshot = validate_operating_snapshot(
        bundle.get("operating_snapshot"),
        run,
        bundle.get("source_snapshots"),
        parse_datetime,
        errors,
        require_snapshot=capability_passed(bundle.get("capabilities"), "db_read"),
    )
    position_lookup = {position["canonical_id"]: position for position in positions}
    consultant_roster = validate_consultant_roster(
        bundle.get("consultant_roster"),
        bundle.get("outreach_events"),
        errors,
        require_roster=outreach_complete,
    )
    outreach_diagnostics = validate_outreach_channel_diagnostics(
        bundle.get("outreach_channel_diagnostics"),
        bundle.get("outreach_events"),
        consultant_roster,
        source_snapshot_ids,
        errors,
        require_all_channels=True,
    )
    channel_coverage, coverage_blockers = build_channel_coverage(
        outreach_diagnostics, consultant_roster
    )
    consultant_focus, excluded_rows = validate_outreach_events(
        bundle.get("outreach_events"),
        outreach_diagnostics,
        consultant_roster,
        position_lookup,
        run,
        source_snapshot_ids,
        snapshot_evidence_refs,
        parse_datetime,
        errors,
    )
    consultant_focus = apply_coverage_comparability(consultant_focus, coverage_blockers)
    zero_result_assertions = validate_zero_result_assertions(
        bundle.get("zero_result_assertions"),
        required_zero_collections(
            positions, consultant_focus, outreach_complete, core_position_complete
        ),
        snapshot_evidence_refs,
        errors,
    )
    source_blockers.extend(snapshot_blockers + career_blockers + coverage_blockers)
    projection = stable_projection(bundle, positions, career_summaries, dedupe_decisions, operating_snapshot)
    projection["zero_result_assertions"] = zero_result_assertions
    input_hash = digest(projection)
    snapshot_id = f"rpt_{input_hash[:24]}"
    data_status = "BLOCKED" if errors else ("PARTIAL" if source_blockers else "PASS")
    brief = (
        render_brief(
            bundle,
            positions,
            career_summaries,
            consultant_focus,
            operating_snapshot,
            snapshot_id,
            data_status,
            sorted(set(source_blockers)),
        )
        if run and not sensitive_values_found
        else ""
    )
    result = assemble_result(
        bundle, positions, consultant_focus, channel_coverage, excluded_rows,
        career_summaries, operating_snapshot, errors,
        source_blockers, data_status, snapshot_id, input_hash, brief,
    )
    if final_output_violations(result):
        return sanitized_blocked_result(result)
    return result


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--format", choices=("json", "markdown", "html"), default="json")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    try:
        bundle = json.loads(args.input.read_text(encoding="utf-8"))
        if not isinstance(bundle, dict):
            raise ValueError("input_object_required")
        result = evaluate(bundle)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(json.dumps({"verdict": "NOT_RUN", "reason": type(error).__name__}))
        return 2
    if args.format == "markdown":
        output = result["brief_markdown"]
    elif args.format == "html":
        output = render_html(
            result["brief_markdown"], result["report_snapshot_id"], result["content_hash"],
            result["publication_report_markdown"],
        )
    else:
        output = canonical_json(result)
    scan_text = output
    if args.format == "json":
        for allowed in sorted(ALLOWED_EMAIL_TARGETS):
            scan_text = re.sub(
                rf"(?<![\w.+-]){re.escape(allowed)}(?![\w.-])", "", scan_text
            )
    if find_sensitive_text(scan_text):
        print(json.dumps({"verdict": "BLOCKED", "reason": "FORBIDDEN_SENSITIVE_OUTPUT"}))
        return 1
    sys.stdout.write(output)
    if not output.endswith("\n"):
        sys.stdout.write("\n")
    return 0 if result["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
