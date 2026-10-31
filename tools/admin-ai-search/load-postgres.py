"""Load normalized staging into a specified PostgreSQL database, never deploy code."""

import argparse
import csv
import io
import json
import sqlite3
import subprocess
from pathlib import Path

from humansearch.admin_ai_search.registry import TABLES, Registry
from humansearch.admin_ai_search.storage_encoding import postgres_document

parser = argparse.ArgumentParser()
parser.add_argument("--database", type=Path, required=True)
parser.add_argument("--dsn", required=True)
args = parser.parse_args()
# Opening the registry gives any legacy W..-P.. Batch its shared weekly number before load.
Registry(args.database).db.close()
db = sqlite3.connect(args.database)
root = Path(__file__).parents[2]


def fail_private(error: str) -> None:
    db.execute("CREATE TABLE IF NOT EXISTS load_errors (created_at TEXT, original_error TEXT)")
    db.execute("INSERT INTO load_errors VALUES (datetime('now'),?)", (error,))
    db.commit()
    raise RuntimeError("PostgreSQL load failed; original error saved in private staging DB")


def sql(statement: str) -> str:
    result = subprocess.run(["psql", args.dsn, "-X", "-A", "-t", "-q",
                             "-v", "ON_ERROR_STOP=1"], input=statement, text=True, capture_output=True)
    if result.returncode:
        fail_private(result.stderr)
    return result.stdout


def load(table: str, records: list[dict[str, object]]) -> None:
    allowed = {*TABLES, "collection_runs", "collection_checkpoints", "settings", "source_messages"}
    if table not in allowed:
        raise ValueError("Module table required")
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    for document in records:
        writer.writerow([document["id"], json.dumps(postgres_document(document), ensure_ascii=False)])
    target = "public.admin_ai_search_" + table
    statement = (f"BEGIN; CREATE TEMP TABLE stage (id text,document jsonb); "
                 "COPY stage FROM STDIN WITH(FORMAT csv);\n" + buffer.getvalue() + "\\.\n" +
                 f"INSERT INTO {target}(id,document) SELECT id,document FROM stage ON CONFLICT(id) "
                 "DO UPDATE SET document=excluded.document; COMMIT;")
    sql(statement)
    print(json.dumps({"table": table, "rows": len(records)}))


for table, source in [("source_messages", "normalized_sources"), ("positions", "positions"), ("candidates", "candidates")]:
    load(table, [json.loads(row[0]) for row in db.execute(f"SELECT document FROM {source}")])
# Register every Batch and compare its number with staging in one transaction:
# any mismatch rolls back all Batch writes of this load.
batch_rows = io.StringIO()
batch_writer = csv.writer(batch_rows, lineterminator="\n")
for order, row in enumerate(db.execute("SELECT id,week_year,week_number,grouping_status,document,display_number "
                                       "FROM batches ORDER BY week_year,week_number,sequence")):
    batch = {"id": row[0], "week_year": row[1], "week_number": row[2], "grouping_status": row[3],
             "document": json.loads(row[4])}
    batch_writer.writerow([order, row[5], json.dumps(postgres_document(batch), ensure_ascii=False)])
sql("BEGIN; CREATE TEMP TABLE staged_batches (ord integer, display_number text, batch jsonb); "
    "COPY staged_batches FROM STDIN WITH(FORMAT csv);\n" + batch_rows.getvalue() + "\\.\n" +
    "DO $$ DECLARE r record; registered jsonb; BEGIN\n"
    "  FOR r IN SELECT * FROM staged_batches ORDER BY ord LOOP\n"
    "    registered := public.admin_ai_search_register_batch(r.batch);\n"
    "    IF registered->>'display_number' IS DISTINCT FROM r.display_number THEN\n"
    "      RAISE EXCEPTION 'display_number mismatch between staging and PostgreSQL: % staged % published %',\n"
    "        r.batch->>'id', r.display_number, registered->>'display_number';\n"
    "    END IF;\n"
    "  END LOOP;\n"
    "END $$; COMMIT;")
for table in TABLES:
    if table not in {"positions", "candidates"}:
        load(table, [json.loads(row[0]) for row in db.execute(f"SELECT document FROM {table}")])
runs = [json.loads(row[0]) for row in db.execute("SELECT document FROM collection_runs")]
source_count = db.execute("SELECT count(*) FROM source_messages").fetchone()[0]
normalized_count = db.execute("SELECT count(*) FROM normalized_sources").fetchone()[0]
for run in runs:
    failures = db.execute("SELECT count(*) FROM normalized_sources WHERE "
                          "json_extract(document,'$.processing_status')='FAILED'").fetchone()[0]
    run["normalization_complete"] = source_count == normalized_count and failures == 0 and run["status"] == "SUCCEEDED"
    run["normalization_source_count"] = normalized_count
load("collection_runs", runs)
load("collection_checkpoints", [{"id": run + ":" + scope, **json.loads(document)}
    for run, scope, document in db.execute("SELECT run_id,scope,document FROM collection_checkpoints")])
contract = json.loads((root / "contracts/admin-ai-search/evidence-contract-v1.json").read_text())
load("settings", [{"id": "contract", **contract["weekly_contract"]}])
print(json.dumps({"status": "PASS", "source_rows": source_count, "normalized_rows": normalized_count}))
