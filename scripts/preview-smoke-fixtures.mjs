#!/usr/bin/env node

async function createUser(config, fixture, request, assert, denied = false) {
  const prefix = denied ? "denied" : "admin";
  const user = await request(
    config,
    "/auth/v1/admin/users",
    {
      method: "POST",
      body: JSON.stringify({
        email: fixture[`${prefix}Email`],
        password: fixture[`${prefix}Password`],
        email_confirm: true,
        app_metadata: { valuehire_admin: true, test_run_id: fixture.runId },
      }),
    },
    [200, 201],
  );
  assert(typeof user?.id === "string", "FIXTURE_AUTH_INVALID", `${prefix} Auth fixture did not return a user ID`);
  fixture[`${prefix}UserId`] = user.id;
}

async function createPosition(config, fixture, request, foreign = false) {
  const prefix = foreign ? "foreign" : "admin";
  await request(
    config,
    "/rest/v1/admin_positions",
    {
      method: "POST",
      headers: { prefer: "return=minimal" },
      body: JSON.stringify({
        tenant_id: foreign ? fixture.foreignTenantId : config.tenantId,
        id: fixture[`${prefix}PositionId`],
        title: foreign ? "E2E-TEST-FOREIGN-POSITION" : "E2E-TEST-POSITION",
        external_key: `E2E-TEST-${foreign ? "FOREIGN-" : ""}POSITION-${fixture.runId}`,
        status: "open",
      }),
    },
    [201],
  );
}

async function createCandidate(config, fixture, request, foreign = false) {
  const prefix = foreign ? "foreign" : "admin";
  await request(
    config,
    "/rest/v1/admin_candidates",
    {
      method: "POST",
      headers: { prefer: "return=minimal" },
      body: JSON.stringify({
        tenant_id: foreign ? fixture.foreignTenantId : config.tenantId,
        id: fixture[`${prefix}CandidateId`],
        position_id: fixture[`${prefix}PositionId`],
        external_key: `E2E-TEST-${foreign ? "FOREIGN-" : ""}CANDIDATE-${fixture.runId}`,
        display_name: foreign ? "E2E-TEST-FOREIGN-CANDIDATE" : "E2E-TEST-CANDIDATE",
        review_status: "unreviewed",
        version: 1,
      }),
    },
    [201],
  );
}

async function listAuthUsers(config, request) {
  const page = await request(config, "/auth/v1/admin/users?page=1&per_page=1000", {}, [200]);
  return Array.isArray(page?.users) ? page.users : [];
}

export async function createPreviewFixtures(config, fixture, request, assert) {
  const users = await listAuthUsers(config, request);
  const fixtureEmails = new Set([fixture.adminEmail, fixture.deniedEmail]);
  assert(!users.some((user) => fixtureEmails.has(user?.email)), "FIXTURE_IDENTITY_COLLISION", "a synthetic Auth identity already exists");
  await createUser(config, fixture, request, assert);
  await createUser(config, fixture, request, assert, true);
  await createPosition(config, fixture, request);
  await createCandidate(config, fixture, request);
  await createPosition(config, fixture, request, true);
  await createCandidate(config, fixture, request, true);
}

async function attempt(failures, label, action) {
  try {
    await action();
  } catch (error) {
    failures.push(`${label}:${error.code || error.name}`);
  }
}

async function deleteRow(config, request, table, id, tenantId) {
  await request(
    config,
    `/rest/v1/${table}?id=eq.${id}&tenant_id=eq.${encodeURIComponent(tenantId)}`,
    { method: "DELETE", headers: { prefer: "return=minimal" } },
    [204],
  );
}

async function proveRowAbsent(config, request, assert, table, id, label) {
  const rows = await request(config, `/rest/v1/${table}?id=eq.${id}&select=id`, {}, [200]);
  assert(Array.isArray(rows) && rows.length === 0, "CLEANUP_INCOMPLETE", `${label} remains after cleanup`);
}

async function deleteReviewEvents(config, request, candidateId, tenantId) {
  await request(
    config,
    `/rest/v1/admin_candidate_review_events?candidate_id=eq.${candidateId}&tenant_id=eq.${encodeURIComponent(tenantId)}`,
    { method: "DELETE", headers: { prefer: "return=minimal" } },
    [204],
  );
}

async function proveReviewEventsAbsent(config, request, assert, candidateId, label) {
  const rows = await request(
    config,
    `/rest/v1/admin_candidate_review_events?candidate_id=eq.${candidateId}&select=id`,
    {},
    [200],
  );
  assert(Array.isArray(rows) && rows.length === 0, "CLEANUP_INCOMPLETE", `${label} review events remain after cleanup`);
}

function resolveUserIds(users, fixture, assert) {
  for (const prefix of ["admin", "denied"]) {
    if (fixture[`${prefix}UserId`]) continue;
    const matches = users.filter((user) => (
      user?.email === fixture[`${prefix}Email`]
      && user?.app_metadata?.test_run_id === fixture.runId
    ));
    assert(matches.length <= 1, "CLEANUP_AMBIGUOUS", "multiple synthetic Auth users matched one cleanup identity");
    fixture[`${prefix}UserId`] = matches[0]?.id || "";
  }
}

export async function cleanupPreviewFixtures(config, fixture, request, assert) {
  const failures = [];
  const eventTargets = [
    ["review-event", fixture.adminCandidateId, config.tenantId],
    ["foreign-review-event", fixture.foreignCandidateId, fixture.foreignTenantId],
  ];
  const rows = [
    ["candidate", "admin_candidates", fixture.adminCandidateId, config.tenantId],
    ["foreign-candidate", "admin_candidates", fixture.foreignCandidateId, fixture.foreignTenantId],
    ["position", "admin_positions", fixture.adminPositionId, config.tenantId],
    ["foreign-position", "admin_positions", fixture.foreignPositionId, fixture.foreignTenantId],
  ];
  for (const [label, candidateId, tenantId] of eventTargets) {
    await attempt(failures, `${label}-delete`, () => deleteReviewEvents(config, request, candidateId, tenantId));
  }
  for (const [label, table, id, tenantId] of rows) {
    await attempt(failures, `${label}-delete`, () => deleteRow(config, request, table, id, tenantId));
  }

  await attempt(failures, "auth-user-resolve", async () => resolveUserIds(await listAuthUsers(config, request), fixture, assert));
  for (const prefix of ["admin", "denied"]) {
    const userId = fixture[`${prefix}UserId`];
    if (!userId) continue;
    await attempt(failures, `${prefix}-auth-delete`, () => request(config, `/auth/v1/admin/users/${userId}`, { method: "DELETE" }, [200]));
  }

  for (const [label, table, id] of rows) {
    await attempt(failures, `${label}-absence`, () => proveRowAbsent(config, request, assert, table, id, label));
  }
  for (const [label, candidateId] of eventTargets) {
    await attempt(failures, `${label}-absence`, () => proveReviewEventsAbsent(config, request, assert, candidateId, label));
  }
  for (const prefix of ["admin", "denied"]) {
    const userId = fixture[`${prefix}UserId`];
    if (!userId) continue;
    await attempt(failures, `${prefix}-auth-absence`, () => request(config, `/auth/v1/admin/users/${userId}`, {}, [404]));
  }

  const targetIds = [
    fixture.adminCandidateId,
    fixture.adminPositionId,
    fixture.foreignCandidateId,
    fixture.foreignPositionId,
    fixture.adminUserId,
    fixture.deniedUserId,
  ].filter(Boolean).join(",");
  assert(failures.length === 0, "CLEANUP_FAILED", `${failures.join(",")}; cleanup_target_ids=${targetIds}`);
}
