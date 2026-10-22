"""Immutable post-delivery findings, separate from the historical send state machine.

Proof JSON is a trusted adapter observation, not provider attestation. The adapter
must read source bytes and the receiver ZIP independently, derive both hashes,
inspect markers, and read labels from the actual recorded receiver message. This
module validates their bindings and stores the observations; it never sends mail
or invents a missing pre-send hash. Old operation/receipt rows stay unchanged.
"""
import json
from datetime import datetime, timezone

from .core import DESTINATION, MIRROR_MARKER, canonical, digest, normalize_address, require, strings
from .journal import normalize_rfc_message_id
from .recovery import sha256

ARCHIVE_CONFIRMED = "ARCHIVE_CONFIRMED_AFTER_DELIVERY"
REPAIRED = "REPAIRED_BY_CONFIRMED_DELIVERY"


def _fields(value, expected, name):
    require(type(value) is dict and set(value) == set(expected), "invalid " + name + " fields")


def _identity(value):
    require(type(value) is list and len(value) == 2 and value[0] == "rfc"
            and type(value[1]) is str and bool(value[1].strip()), "known RFC source identity required")
    return ["rfc", normalize_rfc_message_id(value[1])]


def _reports(value):
    require(type(value) is list and bool(value) and all(sha256(item) for item in value)
            and len(value) == len(set(value)), "private independent readback report hashes required")


def _delivery(journal, operation_id):
    operation = journal.operation(operation_id)
    require(operation["kind"] in ("share", "share_repair"), "only historical deliveries can be resolved")
    require(operation["state"] == "SENT_UNVERIFIED", "historical delivery must have recorded send result")
    payload = operation["payload"]
    require(normalize_address(payload.get("account")) == DESTINATION, "historical destination mismatch")
    require(payload.get("mirror_marker") == MIRROR_MARKER, "historical mirror marker missing")
    require(payload.get("source_review_id") == operation["review_id"], "historical source review mismatch")
    message = journal.review(operation["review_id"])["message"]
    require(payload.get("content_hash") == message["source_hash"], "historical source content mismatch")
    identity = _identity(["rfc", message.get("rfc_message_id")])
    row = journal.db.execute(
        "SELECT payload_json FROM receipts WHERE operation_id=? AND state='SENT_UNVERIFIED' ORDER BY id DESC LIMIT 1",
        (operation_id,)).fetchone()
    require(row is not None, "historical send result missing")
    receipt = json.loads(row[0])
    sender = receipt.get("sender_message_id")
    receivers = [receipt[key] for key in ("receiver_message_id", "dev_message_id") if key in receipt]
    require(type(sender) is str and bool(sender.strip()), "recorded sender message ID required")
    require(bool(receivers) and all(type(value) is str and value.strip() and value == receivers[0] for value in receivers),
            "unambiguous recorded receiver message ID required")
    if "receiver_account" in receipt:
        require(normalize_address(receipt["receiver_account"]) == DESTINATION, "recorded receiver account mismatch")
    return dict(operation=operation, message=message, identity=identity, sender=sender, receiver=receivers[0])


def _repair_parent(journal, repair):
    payload = repair["operation"]["payload"]
    parent = _delivery(journal, payload.get("prior_operation_id"))
    require(parent["operation"]["kind"] == "share", "repair must reference an original share")
    require(parent["operation"]["review_id"] == repair["operation"]["review_id"]
            and parent["identity"] == repair["identity"]
            and parent["message"]["source_hash"] == repair["message"]["source_hash"], "repair source mismatch")
    require(payload.get("prior_sender_message_id") == parent["sender"]
            and payload.get("prior_receiver_message_id") == parent["receiver"], "repair prior delivery IDs mismatch")
    require(payload.get("source_message_id") == parent["message"]["message_id"], "repair source message mismatch")
    require(repair["sender"] != parent["sender"] and repair["receiver"] != parent["receiver"],
            "repair must have distinct sender and receiver")
    return parent


def _receiver(delivery, observation, sender):
    require(sender == delivery["sender"], "observed sender message ID mismatch")
    require(normalize_address(observation["account"]) == DESTINATION
            and observation["message_id"] == delivery["receiver"], "observed receiver identity mismatch")
    require(_identity(observation["source_identity"]) == delivery["identity"]
            and observation["content_hash"] == delivery["message"]["source_hash"], "observed receiver source mismatch")
    require(observation["mirror_marker"] == MIRROR_MARKER
            and observation["operation_id"] == delivery["operation"]["id"], "observed delivery marker mismatch")


def _intent_hashes(journal, delivery, original_sha):
    rows = journal.db.execute("SELECT payload_json FROM receipts WHERE operation_id=? AND state='SENDING'",
                              (delivery["operation"]["id"],)).fetchall()
    require(bool(rows), "historical send intent missing")
    for row in rows:
        intent = json.loads(row[0])
        # Legacy raw_sha256 remains a legacy field; it is not a new send-contract receipt.
        for field in ("original_sha256", "raw_sha256"):
            if field in intent:
                require(sha256(intent[field]) and intent[field] == original_sha, "recorded intent source bytes mismatch")


def _archive_proof(journal, delivery, proof):
    _fields(proof, {"sender_message_id", "source_observation", "receiver_observation", "label_observation", "report_sha256s"}, "archive proof")
    _reports(proof["report_sha256s"])
    source, receiver, labels = (proof[key] for key in ("source_observation", "receiver_observation", "label_observation"))
    _fields(source, {"account", "message_id", "source_identity", "content_hash", "original_sha256"}, "source observation")
    _fields(receiver, {"account", "message_id", "source_identity", "content_hash", "original_sha256", "mirror_marker", "operation_id"}, "receiver observation")
    _fields(labels, {"account", "message_id", "labels"}, "label observation")
    message = delivery["message"]
    require(normalize_address(source["account"]) == normalize_address(message["account"])
            and source["message_id"] == message["message_id"], "observed original account/message mismatch")
    require(_identity(source["source_identity"]) == delivery["identity"]
            and source["content_hash"] == message["source_hash"], "observed original source mismatch")
    require(sha256(source["original_sha256"]) and receiver["original_sha256"] == source["original_sha256"],
            "received original RFC bytes mismatch")
    _receiver(delivery, receiver, proof["sender_message_id"])
    require(normalize_address(labels["account"]) == DESTINATION
            and labels["message_id"] == delivery["receiver"], "observed label identity mismatch")
    strings(labels["labels"], "readback labels")
    require(set(delivery["operation"]["payload"]["labels"]) <= set(labels["labels"]), "required historical labels missing")
    _intent_hashes(journal, delivery, source["original_sha256"])
    if delivery["operation"]["kind"] == "share_repair":
        _intent_hashes(journal, _repair_parent(journal, delivery), source["original_sha256"])


def _append(journal, operation_id, outcome, payload):
    encoded = canonical(payload)
    row = journal.db.execute("SELECT outcome,payload_json FROM delivery_resolutions WHERE operation_id=?", (operation_id,)).fetchone()
    if row:
        require(row["outcome"] == outcome and row["payload_json"] == encoded, "immutable delivery resolution conflict")
    else:
        journal.db.execute("INSERT INTO delivery_resolutions VALUES(?,?,?,?)",
                           (operation_id, outcome, encoded, datetime.now(timezone.utc).isoformat()))
    return delivery_status(journal, operation_id)


def resolve_delivery_archive(journal, operation_id, proof):
    """Resolve an existing copy from independent archive/label observations only."""
    with journal.db:
        journal.db.execute("BEGIN IMMEDIATE")
        delivery = _delivery(journal, operation_id)
        _archive_proof(journal, delivery, proof)
        return _append(journal, operation_id, ARCHIVE_CONFIRMED, dict(proof=proof))


def resolve_delivery_repair(journal, original_operation_id, repair_operation_id, failure_proof):
    """Keep the original archive failure visible and link its confirmed repair."""
    with journal.db:
        journal.db.execute("BEGIN IMMEDIATE")
        original = _delivery(journal, original_operation_id)
        repair = _delivery(journal, repair_operation_id)
        require(original["operation"]["kind"] == "share" and repair["operation"]["kind"] == "share_repair",
                "original share and distinct repair required")
        require(_repair_parent(journal, repair)["operation"]["id"] == original_operation_id, "repair references a different original")
        row = journal.db.execute("SELECT outcome,payload_json FROM delivery_resolutions WHERE operation_id=?", (repair_operation_id,)).fetchone()
        require(row is not None and row["outcome"] == ARCHIVE_CONFIRMED, "repair archive must be confirmed first")
        repair_proof = json.loads(row["payload_json"])["proof"]
        _archive_proof(journal, repair, repair_proof)
        require(set(original["operation"]["payload"]["labels"]) <= set(repair_proof["label_observation"]["labels"]),
                "repair does not satisfy original labels")
        _fields(failure_proof, {"sender_message_id", "receiver_observation", "report_sha256s"}, "original failure proof")
        _reports(failure_proof["report_sha256s"])
        observation = failure_proof["receiver_observation"]
        _fields(observation, {"account", "message_id", "source_identity", "content_hash", "mirror_marker", "operation_id", "original_archive_preserved"}, "original failure observation")
        require(observation["original_archive_preserved"] is False, "explicit original archive failure required")
        _receiver(original, observation, failure_proof["sender_message_id"])
        return _append(journal, original_operation_id, REPAIRED,
                       dict(proof=failure_proof, repair_operation_id=repair_operation_id))


def delivery_status(journal, operation_id):
    """Expose the historical state and separate effective resolution honestly."""
    operation = journal.operation(operation_id)
    row = journal.db.execute("SELECT * FROM delivery_resolutions WHERE operation_id=?", (operation_id,)).fetchone()
    result = dict(operation_id=operation_id, historical_state=operation["state"], resolved=row is not None,
                  outcome=row["outcome"] if row else "UNRESOLVED", original_archive_preserved=None,
                  repair_operation_id=None)
    if row:
        payload = json.loads(row["payload_json"])
        result.update(original_archive_preserved=row["outcome"] == ARCHIVE_CONFIRMED,
                      repair_operation_id=payload.get("repair_operation_id"),
                      evidence_sha256=digest(payload), recorded_at=row["recorded_at"])
    return result
