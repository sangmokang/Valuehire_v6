#!/usr/bin/env bash
set -euo pipefail

repo=$(git rev-parse --show-toplevel)
pg_bin=$(pg_config --bindir)
pg_tmp=$(mktemp -d "${TMPDIR:-/tmp}/invoice-pg.XXXXXX")
pg_data="$pg_tmp/data"
pg_socket="$pg_tmp/socket"
pg_port=$((55000 + $$ % 5000))
mkdir -p "$pg_socket"

cleanup() {
  "$pg_bin/pg_ctl" -D "$pg_data" stop -m immediate >/dev/null 2>&1 || true
  rm -rf -- "$pg_tmp"
}
trap cleanup EXIT

"$pg_bin/initdb" -D "$pg_data" --no-locale --encoding=UTF8 >/dev/null
"$pg_bin/pg_ctl" -D "$pg_data" -o "-F -k $pg_socket -p $pg_port" \
  -w start >/dev/null
"$pg_bin/createdb" -h "$pg_socket" -p "$pg_port" invoice_test
psql_cmd=("$pg_bin/psql" -X -v ON_ERROR_STOP=1 -h "$pg_socket" -p "$pg_port" -d invoice_test)

"${psql_cmd[@]}" -f "$repo/tools/invoice/tests/postgres_fixture.sql" >/dev/null
for migration in \
  20260901090000_invoice_fee_agreements_and_storage.sql \
  20260901100000_invoice_fee_agreement_immutability.sql \
  20260901103000_invoice_fee_agreement_idempotent_upsert.sql \
  20260902090000_invoice_runtime_integrity.sql; do
  "${psql_cmd[@]}" -f "$repo/supabase/migrations/$migration" >/dev/null
done

first_sql="begin;
insert into recruitment_fee_agreements (
 agreement_ref,client_key,client_name,position_key,position_name,fee_rate,
 effective_from,effective_to,source_reference,status
) values (
 'RACE-A','race client','Race Client','race position','Race Position',0.2,
 '2026-01-01',null,'race test A','active'
);
select pg_advisory_xact_lock(424242);
select pg_sleep(2);
commit;"
"${psql_cmd[@]}" -c "$first_sql" >"$pg_tmp/first.log" 2>&1 &
first_pid=$!

for _ in {1..50}; do
  lock_count=$("${psql_cmd[@]}" -Atc \
    "select count(*) from pg_locks where locktype='advisory' and objid=424242")
  [ "$lock_count" = "1" ] && break
  sleep 0.05
done
[ "${lock_count:-0}" = "1" ] || {
  echo "FAIL: concurrent transaction did not reach the race barrier"
  exit 1
}

set +e
"${psql_cmd[@]}" -c "insert into recruitment_fee_agreements (
 agreement_ref,client_key,client_name,position_key,position_name,fee_rate,
 effective_from,effective_to,source_reference,status
) values (
 'RACE-B','race client','Race Client','race position','Race Position',0.25,
 '2026-06-01',null,'race test B','active'
);" >"$pg_tmp/second.log" 2>&1
second_rc=$?
set -e
wait "$first_pid"
[ "$second_rc" -ne 0 ] || {
  echo "FAIL: concurrent overlapping fee agreement was accepted"
  exit 1
}
race_count=$("${psql_cmd[@]}" -Atc \
  "select count(*) from recruitment_fee_agreements where client_key='race client'")
[ "$race_count" = "1" ] || {
  echo "FAIL: expected one committed race agreement, got $race_count"
  exit 1
}

"${psql_cmd[@]}" \
  -f "$repo/tools/invoice/tests/postgres_runtime_assertions.sql" >/dev/null
active_contracts=$("${psql_cmd[@]}" -Atc \
  "select count(*) from invoice_business_contract_versions where active")
[ "$active_contracts" = "1" ] || {
  echo "FAIL: expected exactly one active business contract"
  exit 1
}
"${psql_cmd[@]}" -Atc \
  "select jsonb_build_object('version',version,'sha256',sha256,'config',config)
   from invoice_business_contract_versions where active" \
  | python3 "$repo/tools/invoice/tests/assert_contract_snapshot.py"
owner_policy=$("${psql_cmd[@]}" -Atc \
  "select cmd from pg_policies
   where tablename='invoice_delivery_receipts'
     and policyname='invoice_delivery_receipts_owner'")
[ "$owner_policy" = "SELECT" ] || {
  echo "FAIL: owner delivery policy is not read-only: $owner_policy"
  exit 1
}

echo "PASS: PostgreSQL migration, fee race, store RPC, and delivery receipt"
