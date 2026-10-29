"""Grok reports bind contacts only through verifiable channel identities."""

from pathlib import Path

from humansearch.admin_ai_search.contact_reports import ingest_report
from humansearch.admin_ai_search.normalize import key
from humansearch.admin_ai_search.registry import Registry


def registry(tmp_path: Path) -> Registry:
    store = Registry(tmp_path / "private.sqlite")
    import hashlib
    candidate = hashlib.sha256(b"https://linkedin.com/in/candidate").hexdigest()
    store.put("candidates", {"id": candidate})
    position = key("Client", "Engineer")
    store.put("positions", {"id": position, "company": "Client", "title": "Engineer"})
    store.put("candidate_position_evaluations", {"id": "evaluation", "candidate_id": candidate, "position_id": position})
    return store


def event() -> dict[str, object]:
    return {"candidate_profile_url": "https://linkedin.com/in/candidate", "company": "Client",
            "position": "Engineer", "channel": "LINKEDIN", "actor": "OWNER",
            "status": "CONTACTED", "sent_at": "2026-10-23T12:00:00+09:00",
            "checked_at": "2026-10-24T12:00:00+09:00", "evidence_reference": "inmail:message-1"}


def test_explicit_candidate_position_contact_is_idempotent(tmp_path: Path) -> None:
    store = registry(tmp_path)
    report = {"version": "ai-search-contact-report/v1", "events": [event()]}
    ingest_report(store, "report-mail", report)
    ingest_report(store, "report-mail", report)
    contacts = store.documents("contact_events")
    assert len(contacts) == 1
    assert contacts[0]["actor"] == "OWNER"
    assert contacts[0]["position_id"] == key("Client", "Engineer")
    assert contacts[0]["status"] == "CONTACTED"


def test_incomplete_negative_is_not_confirmed_uncontacted(tmp_path: Path) -> None:
    store = registry(tmp_path)
    negative = {**event(), "status": "CONFIRMED_NOT_CONTACTED", "pagination_exhausted": False}
    ingest_report(store, "report-mail", {"version": "ai-search-contact-report/v1", "events": [negative]})
    assert store.documents("contact_events")[0]["status"] == "NOT_RUN"
    assert store.documents("review_queue")[0]["reason"] == "contact_scope_incomplete"


def test_aggregate_counts_never_become_candidate_contacts(tmp_path: Path) -> None:
    store = registry(tmp_path)
    ingest_report(store, "report-mail", {"totals": {"SARAMIN": 15, "LINKEDIN": 9}})
    assert store.documents("contact_events") == []
    assert store.documents("contact_evidence")[0]["reported_totals"] == {"SARAMIN": 15, "LINKEDIN": 9}
    assert store.documents("review_queue")[0]["reason"] == "contact_report_binding_pending"
