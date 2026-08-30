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
    render_career_summaries,
    render_consultant_focus,
    validate_career_summaries,
    validate_outreach_channel_diagnostics,
    validate_outreach_events,
)
from contract_gate import (
    REQUIRED_PUBLICATION_TARGETS,
    capability_blockers,
    find_sensitive_values,
    publication_state,
    validate_dedupe_decisions,
    validate_source_snapshots,
)


SCHEMA_VERSION = "weekly-ops-input-v1"
SCORE_VERSION = "weekly-priority-v1"
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
FORBIDDEN_KEYS = {
    "raw_body",
    "body_html",
    "body_text",
    "candidate_name",
    "candidate_email",
    "sender_address",
    "recipient_address",
    "access_token",
    "api_key",
    "credential",
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


def find_forbidden_fields(value: Any) -> list[str]:
    found: list[str] = []
    if isinstance(value, dict):
        for key, nested in value.items():
            if key.casefold() in FORBIDDEN_KEYS:
                found.append(key)
            found.extend(find_forbidden_fields(nested))
    elif isinstance(value, list):
        for nested in value:
            found.extend(find_forbidden_fields(nested))
    return found


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
    if not (
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
        if any(ref not in valid_evidence_refs for ref in position["evidence_refs"]):
            errors.append("POSITION_EVIDENCE_UNRESOLVED")
            continue
        if position["origin"] == "SCRAPED_STAGING" and position["intent"] not in {
            "NONE",
            "REFERENCE_ONLY",
        }:
            errors.append("SCRAPED_CUSTOMER_INTENT_CONFLICT")
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
        "outreach_events": bundle.get("outreach_events", []),
        "publication_target_contracts": target_contracts,
        "score_version": SCORE_VERSION,
    }
    if "outreach_channel_diagnostics" in bundle:
        projection["outreach_channel_diagnostics"] = bundle.get("outreach_channel_diagnostics")
    return projection


def render_position(position: dict[str, Any]) -> str:
    score = position["score"]
    return (
        f"- {position['company']} — {position['title']}: {position['action']} "
        f"(우선순위 {score['priority']}, 시급성 {score['urgency']}, 난이도 {score['difficulty']})"
    )


def render_blocker(blocker: str) -> str:
    labels = {
        "clickup_read:STALE": "ClickUp 스키마는 과거 판독값만 있어 쓰기를 중단했다.",
        "notion_read:NOT_RUN": "Notion 대상 DB와 parent를 확인하지 못해 쓰기를 중단했다.",
        "jobkorea_outreach_read:NOT_RUN": "잡코리아 발송함을 재조회하지 못했다.",
        "saramin_outreach_read:NOT_RUN": "사람인 발송함을 재조회하지 못했다.",
        "linkedin_outreach_read:NOT_RUN": "LinkedIn Recruiter 발송함을 재조회하지 못했다.",
        "career:Codeit:PARTIAL": "Codeit은 공고 ID 58개만 확인되어 직무명 대조가 필요하다.",
    }
    if blocker.startswith("source:"):
        return "일부 원천 스냅샷이 완전 검증 상태가 아니다."
    return labels.get(blocker, blocker)


def render_brief(
    bundle: dict[str, Any],
    positions: list[dict[str, Any]],
    career_summaries: list[dict[str, Any]],
    consultant_focus: list[dict[str, Any]],
    snapshot_id: str,
    data_status: str,
    source_blockers: list[str],
) -> str:
    meeting_date = bundle["run"]["meeting_at"][:10]
    status_label = {
        "PASS": "검증 완료(PASS)",
        "PARTIAL": "부분 검증(PARTIAL)",
        "BLOCKED": "차단(BLOCKED)",
    }.get(data_status, data_status)
    customer = [
        item
        for item in positions
        if item["origin"] in {"CLIENT_REQUESTED", "CLIENT_SHARED"}
        and item["lifecycle"] != "CLOSED"
    ]
    operations = sorted(
        (item for item in positions if item["lifecycle"] == "CLOSED"),
        key=lambda item: (item["company"], item["title"]),
    )
    weekly = sorted(
        (item for item in customer if item["period"] == "WEEKLY"),
        key=lambda item: (-item["score"]["priority"], item["company"], item["title"]),
    )
    late = sorted(
        (item for item in customer if item["period"] == "LATE_ALERT"),
        key=lambda item: (-item["score"]["priority"], item["company"], item["title"]),
    )
    scraped = sorted(
        (item for item in positions if item["origin"] == "SCRAPED_STAGING"),
        key=lambda item: (item["company"], item["title"]),
    )
    lines = [
        f"# Weekly CEO Brief | {meeting_date}",
        "",
        "## 결론",
        "",
        f"데이터 판정은 {status_label}이다. 고객 요청과 단순 채용 공고를 분리했으며, "
        "우선순위는 증거 라벨을 버전 고정 수식으로 계산했다.",
        "",
        "## 이번 주 고객 액션",
        "",
    ]
    lines.extend(render_position(item) for item in weekly)
    if not weekly:
        lines.append("- 검증된 고객 액션 없음.")
    if late:
        lines.extend(["", "## 마감 후 경보", ""])
        lines.extend(render_position(item) for item in late)
    if operations:
        lines.extend(["", "## 운영 변경", ""])
        lines.extend(
            f"- {item['company']} — {item['title']}: {item['action']}" for item in operations
        )
    if consultant_focus:
        lines.extend(["", "## 컨설턴트별 몰입 — 검증된 발송", ""])
        lines.extend(render_consultant_focus(consultant_focus))
        lines.append("- 위 발송은 잔디밭 YELLOW 근거가 될 수 있으나 상위 색 판정은 별도다.")
    elif any("_outreach_read:" in blocker for blocker in source_blockers):
        lines.extend(["", "## 컨설턴트별 몰입 — 산출 보류", ""])
        lines.append(
            "- 세 채널 발송함의 provider readback이 없어 집중도를 산출하지 않았다. "
            "활동 0건으로 해석하지 않는다."
        )
    if career_summaries:
        lines.extend(["", "## 채용 페이지 관측 — 고객 의뢰 아님", ""])
        lines.extend(render_career_summaries(career_summaries))
    if scraped:
        if not career_summaries:
            lines.extend(["", "## 채용 페이지 관측 — 고객 의뢰 아님", ""])
        lines.extend(f"- {item['company']} — {item['title']}" for item in scraped)
    if source_blockers:
        lines.extend(["", "## 운영 위험", ""])
        lines.extend(f"- {render_blocker(blocker)}" for blocker in source_blockers)
    lines.extend(["", f"`report_snapshot_id: {snapshot_id}`", ""])
    return "\n".join(lines)


def evaluate(bundle: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    if bundle.get("schema_version") != SCHEMA_VERSION:
        errors.append("SCHEMA_VERSION_INVALID")
    if find_forbidden_fields(bundle):
        errors.append("FORBIDDEN_SENSITIVE_FIELD")
    sensitive_values_found = find_sensitive_values(bundle)
    if sensitive_values_found:
        errors.append("FORBIDDEN_SENSITIVE_VALUE")
    run = validate_run(bundle.get("run"), errors)
    source_blockers = capability_blockers(bundle.get("capabilities"), errors)
    source_snapshot_ids, evidence_refs, snapshot_evidence_refs, snapshot_blockers = validate_source_snapshots(
        bundle.get("source_snapshots"), parse_datetime, errors
    )
    dedupe_decisions = validate_dedupe_decisions(bundle.get("dedupe_decisions"), errors)
    positions = validate_positions(bundle.get("positions"), run, evidence_refs, errors)
    career_summaries, career_blockers = validate_career_summaries(
        bundle.get("career_page_summaries"), source_snapshot_ids, parse_datetime, errors
    )
    position_lookup = {position["canonical_id"]: position for position in positions}
    outreach_diagnostics = validate_outreach_channel_diagnostics(
        bundle.get("outreach_channel_diagnostics"),
        bundle.get("outreach_events"),
        source_snapshot_ids,
        errors,
    )
    consultant_focus = validate_outreach_events(
        bundle.get("outreach_events"),
        outreach_diagnostics,
        position_lookup,
        run,
        source_snapshot_ids,
        snapshot_evidence_refs,
        parse_datetime,
        errors,
    )
    source_blockers.extend(snapshot_blockers + career_blockers)
    projection = stable_projection(bundle, positions, career_summaries, dedupe_decisions)
    input_hash = digest(projection)
    snapshot_id = f"rpt_{input_hash[:24]}"
    data_status = "BLOCKED" if errors else ("PARTIAL" if source_blockers else "PASS")
    brief = (
        render_brief(
            bundle,
            positions,
            career_summaries,
            consultant_focus,
            snapshot_id,
            data_status,
            sorted(set(source_blockers)),
        )
        if run and not sensitive_values_found
        else ""
    )
    content_hash = hashlib.sha256(brief.encode("utf-8")).hexdigest()
    publication_blockers = publication_state(
        bundle.get("publication_targets"), snapshot_id, content_hash, errors
    )
    if errors:
        verdict = "BLOCKED"
    elif source_blockers or publication_blockers:
        verdict = "PARTIAL"
    else:
        verdict = "PASS"
    customer_ids = [
        item["canonical_id"]
        for item in sorted(positions, key=lambda item: -item["score"]["priority"])
        if item["origin"] in {"CLIENT_REQUESTED", "CLIENT_SHARED"}
        and item["lifecycle"] != "CLOSED"
    ]
    return {
        "schema_version": "weekly-ops-publication-v1",
        "verdict": verdict,
        "report_snapshot_id": snapshot_id,
        "input_hash": input_hash,
        "content_hash": content_hash,
        "score_version": SCORE_VERSION,
        "positions": positions,
        "customer_priority_ids": customer_ids,
        "consultant_focus": consultant_focus,
        "career_page_summaries": career_summaries,
        "brief_markdown": brief,
        "errors": sorted(set(errors)),
        "blockers": sorted(set(source_blockers + publication_blockers)),
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--format", choices=("json", "markdown"), default="json")
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
    output = result["brief_markdown"] if args.format == "markdown" else canonical_json(result)
    print(output)
    return 0 if result["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
