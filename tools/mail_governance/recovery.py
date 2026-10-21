"""Add label-only successors after an adapter establishes zero-effect preflight failure.

Imported evidence and private report hashes are trusted adapter assertions, not
authenticated Gmail attestations. The adapter must independently inspect archives,
bind the observed receiver ID/bytes before any mutation, and collect label readback.
This module does not send mail, call a provider, or authorize replay of old intents.
"""
import json

from .core import canonical, require


def sha256(value):
    return type(value) is str and len(value) == 64 and all(c in "0123456789abcdef" for c in value)


def validate_proof(evidence):
    fields = {"reason", "provider_mutation_attempts", "report_sha256s"}
    require(type(evidence) is dict and fields <= set(evidence) <= fields | {"legacy_original_observation"},
            "explicit preflight failure evidence required")
    require(evidence["reason"] == "preflight_failed", "only preflight failure can be recovered")
    attempts = evidence["provider_mutation_attempts"]
    require(type(attempts) is int and attempts == 0, "zero provider mutation attempts must be established")
    reports = evidence["report_sha256s"]
    require(type(reports) is list and bool(reports) and all(sha256(item) for item in reports),
            "private preflight report SHA-256 hashes required")
    require(len(reports) == len(set(reports)), "duplicate report hashes")
    return json.loads(canonical(evidence))


def source_identity(journal, original, evidence):
    """Accept a missing legacy identity only from explicit source-bound observation."""
    payload = original["payload"]
    identity = payload.get("source_identity")
    observation = evidence.get("legacy_original_observation")
    if observation is None:
        require(identity is not None, "legacy source identity requires independent original observation")
        return identity
    fields = {"source_identity", "content_hash", "original_sha256", "receiver_message_id"}
    require(type(observation) is dict and set(observation) == fields, "invalid legacy original observation")
    require(payload.get("source_review_id") == original["review_id"], "legacy source review mismatch")
    message = journal.review(original["review_id"])["message"]
    rfc = message["rfc_message_id"]
    require(type(rfc) is str and bool(rfc.strip()), "legacy migration requires known RFC source identity")
    expected = ["rfc", rfc]
    require(observation["source_identity"] == expected, "legacy observed original identity mismatch")
    require(observation["content_hash"] == payload["content_hash"] == message["source_hash"],
            "legacy observed source content mismatch")
    require(sha256(observation["original_sha256"]), "legacy original RFC SHA-256 required")
    receiver_id = observation["receiver_message_id"]
    require(type(receiver_id) is str and bool(receiver_id.strip()) and receiver_id == receiver_id.strip(),
            "legacy receiver message ID required")
    require(identity is None or identity == expected, "existing source identity cannot be overridden")
    return expected


def recover_label_preflight(journal, old_operation_id, evidence):
    """Append FAILED plus one receiver-label successor; identical evidence is resumable.

    No attempt is made to infer zero effects from SENDING. An ambiguous/provider
    failure is ineligible. Legacy identity migration retains its explicit archive
    observation in the old operation's new FAILED receipt, without rewriting rows.
    """
    proof = validate_proof(evidence)
    original = journal.operation(old_operation_id)
    require(original["kind"] == "receiver_labels", "only receiver-label operations can be recovered")
    require(original["state"] in ("SENDING", "FAILED"), "operation is not an eligible preflight failure")
    identity = source_identity(journal, original, proof)
    if original["state"] == "SENDING":
        journal.receipt(old_operation_id, "FAILED", proof)
    else:
        row = journal.db.execute(
            "SELECT payload_json FROM receipts WHERE operation_id=? ORDER BY id DESC LIMIT 1",
            (old_operation_id,)).fetchone()
        require(json.loads(row[0]) == proof, "conflicting preflight failure evidence")
    payload = dict(original["payload"], source_identity=identity, supersedes_operation_id=old_operation_id)
    if "legacy_original_observation" in proof:
        payload["bound_receiver_message_id"] = proof["legacy_original_observation"]["receiver_message_id"]
    return journal._plan_operation(original["review_id"], "receiver_labels",
                                   "receiver-label-recovery:" + old_operation_id, payload)
