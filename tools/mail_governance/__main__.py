"""JSON-in/JSON-out offline CLI. No credentials and no external mutations."""
import argparse
import json
import sys

from .core import canonical, content_hash
from .journal import Journal
from .historical_delivery import delivery_status, resolve_delivery_archive, resolve_delivery_repair


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", required=True)
    parser.add_argument("command", choices=("hash", "import-review", "plan", "receipt", "operation", "coverage", "coverage-status",
                                            "delivery-status", "resolve-delivery-archive", "resolve-delivery-repair"))
    parser.add_argument("--input", default="-", help="JSON file, or - for stdin")
    args = parser.parse_args()
    source = sys.stdin if args.input == "-" else open(args.input, encoding="utf-8")
    try:
        data = json.load(source)
    finally:
        if source is not sys.stdin:
            source.close()
    if args.command == "hash":
        print(canonical({"source_hash": content_hash(data["authored_text"], data.get("html"))}))
        return
    journal = Journal(args.db)
    try:
        if args.command == "import-review":
            result = {"review_id": journal.import_review(data["message"], data["review"])}
        elif args.command == "plan":
            result = journal.plan(data["review_id"])
        elif args.command == "receipt":
            result = journal.receipt(data["operation_id"], data["state"], data["receipt"])
        elif args.command == "operation":
            result = journal.operation(data["operation_id"])
        elif args.command == "coverage":
            result = journal.coverage(**data)
        elif args.command == "delivery-status":
            result = delivery_status(journal, data["operation_id"])
        elif args.command == "resolve-delivery-archive":
            result = resolve_delivery_archive(journal, data["operation_id"], data["proof"])
        elif args.command == "resolve-delivery-repair":
            result = resolve_delivery_repair(journal, data["operation_id"], data["repair_operation_id"], data["proof"])
        else:
            result = journal.coverage_status(data["account"], data["query"])
        print(canonical(result))
    finally:
        journal.close()


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, TypeError, OSError) as exc:
        print(canonical({"status": "FAIL", "reason": str(exc)}), file=sys.stderr)
        sys.exit(1)
