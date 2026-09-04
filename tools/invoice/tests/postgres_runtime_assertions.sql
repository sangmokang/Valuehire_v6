insert into recruitment_fee_agreements (
  agreement_ref, client_key, client_name, position_key, position_name,
  fee_rate, effective_from, effective_to, source_reference, status
) values (
  'RPC-TEST-2026', normalize_invoice_key('가상회사'), '가상회사',
  normalize_invoice_key('AI Engineer'), 'AI Engineer', 0.20,
  '2026-01-01', null, 'PostgreSQL runtime test', 'active'
);

do $$
declare
  payload_base jsonb := jsonb_build_object(
    'tenant_id', 'valueconnect',
    'contract_version', 'invoice-business-2026-09-02.1',
    'contract_sha256',
      '1728e9ae0dca3d619f0b6e65f0b8a3842b95b99752770176d27dccc0fe34094e',
    'fee_source', 'SUPABASE',
    'invoice', jsonb_build_object(
      'invoice_number', 'VC-PG-TEST-001',
      'issue_date', '2026-09-02',
      'company_name', '가상회사',
      'candidate_name', '홍길동',
      'start_date', '2026-09-01',
      'position', 'AI Engineer',
      'annual_salary_krw', 60000000,
      'fee_percent', 20,
      'fee_agreement_ref', 'RPC-TEST-2026',
      'invoice_amount_krw', 12000000,
      'due_date', '2026-09-15',
      'pdf_sha256', repeat('b', 64),
      'draft', false
    ),
    'settlement', null
  );
  payload jsonb;
  stored jsonb;
  retried jsonb;
begin
  payload := payload_base || jsonb_build_object(
    'payload_canonical', payload_base::text,
    'payload_sha256', encode(digest(convert_to(payload_base::text, 'UTF8'), 'sha256'), 'hex')
  );
  stored := store_invoice_placement_set(payload);
  retried := store_invoice_placement_set(payload);
  if stored ->> 'status' <> 'stored'
    or retried ->> 'status' <> 'idempotent'
    or stored ->> 'fee_agreement_id' is null
    or retried ->> 'fee_agreement_id' is null
    or stored ->> 'document_number' <> 'VC-PG-TEST-001'
    or stored ->> 'fee_agreement_ref' <> 'RPC-TEST-2026'
    or stored ->> 'payload_sha256' <> payload ->> 'payload_sha256' then
    raise exception 'runtime store RPC assertion failed';
  end if;

  begin
    perform store_invoice_placement_set(
      jsonb_set(payload, '{payload_sha256}', to_jsonb(repeat('0', 64)))
    );
    raise exception 'false payload hash was accepted';
  exception when others then
    if sqlerrm = 'false payload hash was accepted'
      or sqlerrm not like 'CONTRACT_ERROR:%' then
      raise;
    end if;
  end;
end;
$$;

do $$
declare
  result jsonb;
  delivery_base jsonb := jsonb_build_object(
    'tenant_id', 'valueconnect',
    'contract_version', 'invoice-business-2026-09-02.1',
    'contract_sha256',
      '1728e9ae0dca3d619f0b6e65f0b8a3842b95b99752770176d27dccc0fe34094e',
    'document_number', 'VC-PG-TEST-001',
    'recipient', 'sangmokang@valueconnect.kr',
    'subject', '[밸류커넥트] PostgreSQL delivery test',
    'gmail_message_id', 'gmail-pg-test-001',
    'sent_at', '2026-09-02T10:00:00+09:00',
    'attachment_sha256', repeat('b', 64),
    'readback_confirmed', true
  );
  delivery jsonb;
begin
  delivery := delivery_base || jsonb_build_object(
    'payload_canonical', delivery_base::text,
    'payload_sha256',
      encode(digest(convert_to(delivery_base::text, 'UTF8'), 'sha256'), 'hex')
  );
  result := record_invoice_delivery(delivery);
  if result ->> 'status' <> 'stored'
    or record_invoice_delivery(delivery) ->> 'status' <> 'idempotent'
    or result ->> 'document_number' <> 'VC-PG-TEST-001'
    or result ->> 'payload_sha256' <> delivery ->> 'payload_sha256' then
    raise exception 'runtime delivery RPC assertion failed';
  end if;
  if (select status from client_billing_statements
      where statement_no = 'VC-PG-TEST-001') <> 'sent' then
    raise exception 'billing statement was not marked sent';
  end if;
  update invoice_business_contract_versions set active = false where active;
  insert into invoice_business_contract_versions(version, sha256, config, active)
  select 'invoice-business-test-rotated', repeat('c', 64), config, true
  from invoice_business_contract_versions
  where version = delivery ->> 'contract_version';
  if record_invoice_delivery(delivery) ->> 'status' <> 'idempotent' then
    raise exception 'delivery retry failed after active contract rotation';
  end if;
  update invoice_business_contract_versions set active = false where active;
  update invoice_business_contract_versions set active = true
  where version = delivery ->> 'contract_version';
end;
$$;

do $$
begin
  perform record_invoice_delivery(jsonb_build_object(
    'tenant_id', 'valueconnect',
    'contract_version', 'wrong-version',
    'contract_sha256', repeat('0', 64),
    'document_number', 'VC-PG-TEST-001',
    'recipient', 'sangmokang@valueconnect.kr',
    'subject', 'must fail',
    'gmail_message_id', 'wrong-contract-message',
    'sent_at', '2026-09-02T10:00:00+09:00',
    'attachment_sha256', repeat('b', 64),
    'readback_confirmed', true
  ));
  raise exception 'wrong contract was accepted';
exception
  when others then
    if sqlerrm = 'wrong contract was accepted'
      or sqlerrm not like 'CONTRACT_ERROR:%' then
      raise;
    end if;
end;
$$;
