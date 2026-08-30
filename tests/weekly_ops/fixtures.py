import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / ".agents/skills/weekly-ops/scripts/weekly_gate.py"
CAREER_FIXTURES = (
    ("SpoonLabs", "https://www.spoonlabs.com/careers"),
    ("Codeit", "https://careers.codeit.com/recruit"),
    ("GC Company", "https://career.gccompany.co.kr"),
    ("Wrtn Technologies", "https://wrtn.career.greetinghr.com"),
    ("FastView", "https://fastview.career.greetinghr.com"),
)


def load_gate():
    spec = importlib.util.spec_from_file_location("weekly_gate", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def valid_source_snapshots():
    return [
        {
            "snapshot_id": "snap-gmail-fixture",
            "source_system": "gmail",
            "source_uri_ref": "protected:gmail-fixture",
            "fetched_at": "2026-08-29T10:05:00+09:00",
            "status": "PASS",
            "content_hash": "a" * 64,
            "evidence_refs": ["sha256:codeit-request"],
        },
        {
            "snapshot_id": "snap-career-fixture",
            "source_system": "career_page",
            "source_uri_ref": "https://careers.codeit.com/recruit",
            "fetched_at": "2026-08-31T01:29:00+09:00",
            "status": "PASS",
            "content_hash": "b" * 64,
            "evidence_refs": ["sha256:career-codeit"],
        },
        {
            "snapshot_id": "snap-outreach-fixture",
            "source_system": "sourcing_outreach",
            "source_uri_ref": "protected:outreach-fixture",
            "fetched_at": "2026-08-30T00:05:00+09:00",
            "status": "PASS",
            "content_hash": "c" * 64,
            "evidence_refs": [
                "sha256:receipt-1",
                "sha256:receipt-2",
                "sha256:outreach-export",
            ],
        },
    ]


def valid_position():
    return {
        "canonical_id": "pos-codeit-backend",
        "company": "Codeit",
        "title": "Backend Engineer",
        "category": "backend/fullstack/cto",
        "origin": "CLIENT_REQUESTED",
        "intent": "REQUESTED",
        "event_at": "2026-08-29T10:00:00+09:00",
        "deadline_days": None,
        "late_stage": True,
        "difficulty": {
            "scarcity": "HIGH",
            "seniority": "HIGH",
            "constraints": "MEDIUM",
            "funnel_friction": "HIGH",
        },
        "evidence_refs": ["sha256:codeit-request"],
        "action": "후보군 확장과 1차 추천 일정 확정",
    }


def valid_bundle():
    capability_names = (
        "db_read",
        "gmail_read",
        "clickup_read",
        "notion_read",
        "career_pages_read",
        "jobkorea_outreach_read",
        "saramin_outreach_read",
        "linkedin_outreach_read",
    )
    return {
        "schema_version": "weekly-ops-input-v1",
        "run": {
            "meeting_at": "2026-08-31T11:00:00+09:00",
            "window_start": "2026-08-23T00:00:00+09:00",
            "window_end_exclusive": "2026-08-30T00:00:00+09:00",
            "late_alert_end": "2026-08-31T11:00:00+09:00",
        },
        "capabilities": [
            {"name": name, "status": "PASS", "required": True}
            for name in capability_names
        ],
        "source_snapshots": valid_source_snapshots(),
        "dedupe_decisions": [],
        "positions": [valid_position()],
        "career_page_summaries": [
            {
                "company": company,
                "official_url": official_url,
                "status": "PASS",
                "active_requisitions": 1,
                "talent_pools": 0,
                "freshness_at": "2026-08-31T01:29:00+09:00",
                "limitation": "",
                "source_snapshot_id": "snap-career-fixture",
            }
            for company, official_url in CAREER_FIXTURES
        ],
        "consultant_roster": valid_consultant_roster(),
        "outreach_channel_diagnostics": valid_outreach_diagnostics(),
        "outreach_events": [],
        "zero_result_assertions": [
            {
                "collection": "outreach_events",
                "rule_version": "weekly-zero-result-v1",
                "source_snapshot_id": "snap-outreach-fixture",
                "provider_receipt_ref": "sha256:outreach-export",
                "observed_count": 0,
            }
        ],
        "publication_targets": [
            {
                "name": name,
                "target_id": f"{name}-fixture",
                "required": True,
                "status": "NOT_RUN",
            }
            for name in ("database", "clickup", "notion", "admin_web", "email")
        ],
    }


def valid_consultant_roster():
    return [
        {
            "consultant_id": "consultant-a",
            "consultant_display": "Consultant A",
            "provider_accounts": {
                "jobkorea": ["provider-account:consultant-a-jobkorea"],
                "saramin": ["provider-account:consultant-a-saramin"],
                "linkedin_rps": ["provider-seat:consultant-a"],
            },
        }
    ]


def valid_outreach_diagnostics():
    return [
        {
            "channel": "jobkorea",
            "access_state": "AUTHENTICATED",
            "surface_kind": "position_offer_history",
            "surface_ref": "protected:jobkorea-position-offer-history",
            "stable_receipt_available": True,
            "covered_provider_actor_refs": ["provider-account:consultant-a-jobkorea"],
            "source_snapshot_id": "snap-outreach-fixture",
        },
        {
            "channel": "saramin",
            "access_state": "AUTHENTICATED",
            "surface_kind": "detailed_usage_history",
            "surface_ref": "protected:saramin-detailed-usage-history",
            "stable_receipt_available": True,
            "covered_provider_actor_refs": ["provider-account:consultant-a-saramin"],
            "source_snapshot_id": "snap-outreach-fixture",
        },
        {
            "channel": "linkedin_rps",
            "access_state": "AUTHENTICATED",
            "surface_kind": "inmail_audit_report",
            "surface_ref": "protected:linkedin-inmail-audit-report",
            "stable_receipt_available": True,
            "covered_provider_actor_refs": ["provider-seat:consultant-a"],
            "source_snapshot_id": "snap-outreach-fixture",
        },
    ]


def valid_outreach_event(channel="jobkorea"):
    event = {
        "event_id": f"outreach-{channel}",
        "consultant_id": "consultant-a",
        "consultant_display": "Consultant A",
        "position_id": "pos-codeit-backend",
        "channel": channel,
        "status": "SENT",
        "sent_at": "2026-08-24T09:00:00+09:00",
        "candidate_key_hmac": "hmac:candidate-1",
        "provider_actor_ref": f"provider-account:consultant-a-{channel}",
        "provider_receipt_ref": "sha256:receipt-1",
        "source_snapshot_id": "snap-outreach-fixture",
    }
    if channel == "linkedin_rps":
        event.update(
            provider_actor_ref="provider-seat:consultant-a",
            provider_seat_ref="provider-seat:consultant-a",
            provider_project_ref="provider-project:codeit-backend",
        )
    return event


def mark_all_targets_verified(bundle, result):
    for target in bundle["publication_targets"]:
        target.update(
            status="READBACK_VERIFIED",
            write_ahead_intent_id=f"intent-{target['name']}",
            idempotency_key=f"idem-{target['name']}",
            schema_readback_ref=f"sha256:schema-{target['name']}",
            external_object_id=f"object-{target['name']}",
            receipt_id=f"receipt-{target['name']}",
            receipt_persisted_ref=f"db:receipt-{target['name']}",
            report_snapshot_id=result["report_snapshot_id"],
            content_hash=result["content_hash"],
        )
