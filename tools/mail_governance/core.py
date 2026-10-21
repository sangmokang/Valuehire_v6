"""Pure decisions from explicit reviewer observations; no model or network calls."""
import hashlib
import json
from datetime import datetime
from email.errors import HeaderParseError
from email.headerregistry import Address

LABELS = {"jd": "01JD", "interview": "05인터뷰메일", "daily_weekly": "04dailyweekly", "ontology": "06온톨로지"}
DESTINATION = "dev@valueconnect.kr"
MIRROR_MARKER = "[VC-MIRROR:v1]"
RULE_VERSION = "2026-10-21.v1"
AXES = {"company", "role", "personalization", "layout"}
EVENT_TYPES = ("position_update", "client_rejection", "client_hold", "feedback_clarification",
               "interview_scheduled", "candidate_withdrawal", "candidate_no_response", "feedback")


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest(value):
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def content_hash(authored_text, html=None):
    return digest({"authored_text": authored_text, "html": html})


def require(condition, message):
    if not condition:
        raise ValueError(message)


def string(value, name, nullable=False):
    require((nullable and value is None) or (type(value) is str and bool(value.strip())), name + " must be nonempty text")


def strings(value, name):
    require(type(value) is list and all(type(v) is str and v.strip() for v in value), name + " must be a text list")
    require(len(value) == len(set(value)), name + " contains duplicates")


def timestamp(value, name, nullable=False):
    if nullable and value is None:
        return
    string(value, name)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(name + " must be ISO-8601") from exc
    require(parsed.tzinfo is not None, name + " needs a timezone")


def evidence(message, item):
    require(type(item) is dict and set(item) == {"quote", "representation", "start", "end"}, "invalid evidence fields")
    rep = item["representation"]
    require(rep in ("authored_text", "html"), "evidence representation is not authored content")
    source = message.get(rep)
    require(type(source) is str, "evidence representation is absent")
    start, end = item["start"], item["end"]
    require(type(start) is int and type(end) is int and 0 <= start < end <= len(source), "invalid evidence offsets")
    require(type(item["quote"]) is str and item["quote"].strip() and source[start:end] == item["quote"], "quote does not match source")


def validate(message, review):
    required = {"account", "message_id", "rfc_message_id", "source_hash", "from_address", "to_addresses", "subject",
                "authored_text", "observed_at", "occurred_at", "existing_labels", "source_kind"}
    require(type(message) is dict and required <= set(message) <= required | {"html", "company_id"}, "invalid message fields")
    for key in ("account", "message_id", "source_hash", "from_address", "subject", "authored_text"):
        string(message[key], key)
    for key in ("rfc_message_id", "company_id", "html"):
        string(message.get(key), key, nullable=True)
    for key in ("to_addresses", "existing_labels"):
        strings(message[key], key)
    for address in [message["account"], message["from_address"], *message["to_addresses"]]:
        try:
            parsed = Address(addr_spec=address)
        except (ValueError, HeaderParseError) as exc:
            raise ValueError("mailbox addresses must be normalized addr-specs") from exc
        require(parsed.username and parsed.domain and parsed.addr_spec == address, "mailbox addresses must be normalized addr-specs")
    timestamp(message["observed_at"], "observed_at")
    timestamp(message["occurred_at"], "occurred_at", nullable=True)
    require(message["source_kind"] in ("direct_customer", "internal", "candidate", "unknown"), "invalid source_kind")
    require(message["source_hash"] == content_hash(message["authored_text"], message.get("html")), "source_hash mismatch")
    fields = {"content_hash", "rule_version", "reviewer", "mail_types", "golden_axes", "candidate_ready", "internal_confidential", "ontology_events"}
    require(type(review) is dict and set(review) == fields, "invalid review fields")
    for key in ("content_hash", "rule_version", "reviewer"):
        string(review[key], key)
    require(review["rule_version"] == RULE_VERSION, "unsupported rule_version: use the code-owned version")
    require(review["content_hash"] == message["source_hash"], "review content_hash mismatch")
    strings(review["mail_types"], "mail_types")
    require(set(review["mail_types"]) <= set(LABELS), "unsupported mail type")
    for key in ("candidate_ready", "internal_confidential"):
        require(review[key] is None or type(review[key]) is bool, key + " must be boolean or null")
    axes = review["golden_axes"]
    require(type(axes) is dict and set(axes) == AXES, "exactly four golden axes required")
    for axis in axes.values():
        require(type(axis) is dict and set(axis) == {"status", "evidence"}, "invalid axis fields")
        require(axis["status"] in ("met", "missing", "unknown"), "invalid axis status")
        require(axis["status"] != "met" or axis["evidence"] is not None, "met axis requires evidence")
        if axis["evidence"] is not None:
            evidence(message, axis["evidence"])
    require(type(review["ontology_events"]) is list, "ontology_events must be a list")
    require(not review["ontology_events"] or "ontology" in review["mail_types"], "ontology events require ontology type")
    for event in review["ontology_events"]:
        validate_event(message, event)


def validate_event(message, event):
    fields = {"actor", "event_type", "stage", "reason_quote", "company_id", "position_id", "candidate_id", "application_id", "review_status", "evidence"}
    require(type(event) is dict and set(event) == fields, "invalid event fields")
    require(event["actor"] in ("client", "candidate", "internal", "unknown"), "invalid actor")
    require(event["event_type"] in EVENT_TYPES, "invalid event type")
    require(event["stage"] in ("document", "interview", "offer", "unknown"), "invalid stage")
    require(event["review_status"] in ("proposed", "confirmed", "unresolved"), "invalid event status")
    for key in ("company_id", "position_id", "candidate_id", "application_id", "reason_quote"):
        string(event[key], key, nullable=True)
    evidence(message, event["evidence"])
    require(event["evidence"]["representation"] == "authored_text", "event must cite authored text")
    if event["reason_quote"] is not None:
        require(event["reason_quote"] in event["evidence"]["quote"], "reason must be in cited event evidence")


def classify(message, review):
    validate(message, review)
    axes = review["golden_axes"]
    layout = axes["layout"]["evidence"]
    readable = bool(layout) and (layout["representation"] == "html" or len([line for line in layout["quote"].splitlines() if line.strip()]) >= 3)
    golden = ("jd" in review["mail_types"] and all(a["status"] == "met" for a in axes.values()) and readable
              and review["candidate_ready"] is True and review["internal_confidential"] is False)
    labels = {LABELS[k] for k in review["mail_types"]}
    if golden:
        labels.add("01JD/goldensample")
    events = []
    for source_event in review["ontology_events"]:
        event = dict(source_event)
        needed = ("company_id", "position_id") if event["event_type"] == "position_update" else ("company_id", "position_id", "candidate_id", "application_id")
        verified_client = message["source_kind"] == "direct_customer" and event["actor"] == "client"
        verified_candidate = (event["event_type"] in ("candidate_withdrawal", "candidate_no_response")
                              and message["source_kind"] == "candidate" and event["actor"] == "candidate")
        matching_company = message.get("company_id") is not None and message["company_id"] == event["company_id"]
        if not all(event[k] for k in needed) or (event["review_status"] == "confirmed" and not (matching_company and (verified_client or verified_candidate))):
            event["review_status"] = "unresolved"
        event["reason_status"] = "reason_known" if event["reason_quote"] is not None else "reason_unknown"
        events.append(event)
    return dict(is_golden_sample=golden, labels=sorted(labels), resulting_labels=sorted(labels | set(message["existing_labels"])), events=events)
