-- Allow an idempotent upsert to reach the immutable update check for the same ref.
create or replace function reject_overlapping_fee_agreements()
returns trigger
language plpgsql
set search_path = public
as $$
begin
  if tg_op = 'UPDATE' and row(
    new.tenant_id, new.agreement_ref, new.client_key, new.client_name,
    new.position_key, new.position_name, new.fee_rate,
    new.effective_from, new.effective_to, new.source_reference
  ) is distinct from row(
    old.tenant_id, old.agreement_ref, old.client_key, old.client_name,
    old.position_key, old.position_name, old.fee_rate,
    old.effective_from, old.effective_to, old.source_reference
  ) then
    raise exception 'FEE_AGREEMENT_IMMUTABLE';
  end if;
  if new.status = 'active' and exists (
    select 1
    from recruitment_fee_agreements current_agreement
    where current_agreement.tenant_id = new.tenant_id
      and current_agreement.client_key = new.client_key
      and current_agreement.position_key = new.position_key
      and current_agreement.status = 'active'
      and current_agreement.agreement_ref <> new.agreement_ref
      and current_agreement.id <> new.id
      and daterange(
        current_agreement.effective_from,
        current_agreement.effective_to,
        '[]'
      ) && daterange(new.effective_from, new.effective_to, '[]')
  ) then
    raise exception 'FEE_AGREEMENT_CONFLICT';
  end if;
  return new;
end;
$$;
