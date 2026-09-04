#!/usr/bin/env bash
set -euo pipefail

repo=$(git rev-parse --show-toplevel)

# 환경 부재(BLOCKED, 종료값 4)와 시험 실패(FAIL)를 구분한다. psql 은 스크립트
# 오류에 종료값 3 을 쓰므로 BLOCKED 에는 3 을 쓰지 않는다.
# CI 러너는 PostgreSQL 서버 바이너리를 PATH 가 아니라 /usr/lib/postgresql/<ver>/bin
# 에 두므로 pg_config 만으로는 initdb 를 찾지 못한다.
resolve_pg_bin() {
  local dir candidate
  if [ -n "${PG_BINDIR:-}" ] && [ -x "$PG_BINDIR/initdb" ]; then
    printf '%s' "$PG_BINDIR"; return 0
  fi
  if command -v pg_config >/dev/null 2>&1; then
    if dir=$(pg_config --bindir 2>/dev/null); then
      if [ -n "$dir" ] && [ -x "$dir/initdb" ]; then printf '%s' "$dir"; return 0; fi
    fi
  fi
  for candidate in $(ls -d /usr/lib/postgresql/*/bin 2>/dev/null | sort -Vr); do
    if [ -x "$candidate/initdb" ]; then printf '%s' "$candidate"; return 0; fi
  done
  return 1
}
pg_bin=$(resolve_pg_bin) || {
  echo "BLOCKED: PostgreSQL 서버 바이너리(initdb)를 찾을 수 없다 — 환경 부재이지 시험 실패가 아니다"
  echo "  PG_BINDIR 로 경로를 주거나 postgresql 서버 패키지를 설치하라"
  exit 4
}
for tool in pg_ctl createdb psql; do
  [ -x "$pg_bin/$tool" ] || {
    echo "BLOCKED: $pg_bin/$tool 이 없다 — PostgreSQL 설치가 불완전하다"
    exit 4
  }
done
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
  20260902090000_invoice_runtime_integrity.sql \
  20260905090000_invoice_owner_policy_and_fee_trigger.sql; do
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
# 로그인 사용자(authenticated)는 원장을 읽기만 할 수 있어야 한다. 쓰기는
# service_role 로만 간다. 20260905090000 이 이 축소를 forward-only 로 가져온다.
owner_policies=$("${psql_cmd[@]}" -Atc \
  "select tablename || ':' || cmd from pg_policies
   where policyname in (
     'recruitment_fee_agreements_owner',
     'invoice_settlement_details_owner',
     'invoice_delivery_receipts_owner'
   ) order by tablename")
expected_owner_policies=$'invoice_delivery_receipts:SELECT\ninvoice_settlement_details:SELECT\nrecruitment_fee_agreements:SELECT'
[ "$owner_policies" = "$expected_owner_policies" ] || {
  echo "FAIL: authenticated owner policies are not read-only: $owner_policies"
  exit 1
}

# 정책 이름만 보고 끝내지 않는다 — 실제로 쓰기를 시도해 막히는지 확인한다.
"${psql_cmd[@]}" -c "grant select, insert, update, delete
  on recruitment_fee_agreements to authenticated;" >/dev/null
set +e
"${psql_cmd[@]}" -c "set role authenticated;
  insert into recruitment_fee_agreements (
    agreement_ref, client_key, client_name, position_key, position_name,
    fee_rate, effective_from, source_reference
  ) values (
    'AUTH-DIRECT', 'auth client', 'Auth Client', 'auth role', 'Auth Role',
    0.99, '2026-01-01', 'must be rejected by RLS'
  );" >"$pg_tmp/owner-write.log" 2>&1
owner_write_rc=$?
set -e
[ "$owner_write_rc" -ne 0 ] || {
  echo "FAIL: an authenticated session wrote a fee agreement directly"
  exit 1
}

echo "PASS: PostgreSQL migration, fee race, store RPC, and delivery receipt"
