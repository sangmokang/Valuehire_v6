"""Extract supported attachments using the host app's existing text parsers."""

import argparse
import json
from pathlib import Path

from collect import ExistingGmailReader
from humansearch.admin_ai_search.normalize import review
from humansearch.admin_ai_search.registry import Registry

parser = argparse.ArgumentParser()
parser.add_argument("--database", type=Path, required=True)
args = parser.parse_args()
registry = Registry(args.database)
reader = ExistingGmailReader()
counts = {"parsed": 0, "review_required": 0}
try:
    for row in registry.db.execute("SELECT a.document FROM source_attachments a JOIN normalized_sources s "
        "ON s.id=json_extract(a.document,'$.source_message_id') WHERE "
        "json_extract(s.document,'$.processing_status') IN ('PROCESSED','REVIEW_REQUIRED')").fetchall():
        attachment = json.loads(row[0])
        if attachment["status"] == "PARSED":
            continue
        if not attachment.get("attachment_id"):
            counts["review_required"] += 1
            continue
        try:
            extracted = reader.request("attachment_text", {
                "message_id": attachment["source_message_id"], "attachment_id": attachment["attachment_id"],
                "filename": attachment["filename"], "mime_type": attachment["mime_type"],
            })
            if extracted.get("status") == "textified":
                attachment.update(status="PARSED", reason=None, extracted_text=extracted["text"],
                                  extraction_parser=extracted["parser"], checksum=extracted.get("content_sha256"),
                                  original_html=extracted.get("original_html"))
                counts["parsed"] += 1
                for review_row in registry.db.execute("SELECT document FROM review_queue").fetchall():
                    pending = json.loads(review_row[0])
                    if pending.get("attachment_id") == attachment["id"]:
                        registry.put("review_queue", {**pending, "status": "RESOLVED"})
                registry.db.execute("UPDATE normalized_sources SET checksum=NULL WHERE id=?", (attachment["source_message_id"],))
            else:
                attachment.update(status="REVIEW_REQUIRED", reason=extracted.get("reason", "attachment_extraction_failed"),
                                  original_error=extracted.get("error"))
                counts["review_required"] += 1
        except Exception as error:
            attachment.update(status="REVIEW_REQUIRED", reason="attachment_read_failed", original_error=str(error))
            counts["review_required"] += 1
        registry.put("source_attachments", attachment)
        if attachment["status"] != "PARSED":
            review(registry, attachment["source_message_id"], attachment["reason"],
                   reference=attachment["id"], attachment_id=attachment["id"])
finally:
    reader.close()
print(json.dumps(counts))
