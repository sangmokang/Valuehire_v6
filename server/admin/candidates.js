"use strict";

const { AdminError } = require("./errors");
const { encodeQuery, supabaseFetch } = require("./supabase");

const REVIEW_STATUSES = new Set(["unreviewed", "reviewed", "rejected"]);
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const EMAIL_SHA256 = /^[0-9a-f]{64}$/;

function mapCandidate(row, position) {
  return {
    id: row.id,
    externalKey: row.external_key,
    displayName: row.display_name,
    reviewStatus: row.review_status,
    version: row.version,
    updatedAt: row.updated_at,
    position: {
      id: position.id,
      externalKey: position.external_key,
      title: position.title,
    },
  };
}

async function listCandidates(config) {
  const tenant = encodeQuery(config.tenantId);
  const { body: rows } = await supabaseFetch(
    config,
    `/rest/v1/admin_candidates?tenant_id=eq.${tenant}&select=id,position_id,external_key,display_name,review_status,version,updated_at&order=created_at.asc`,
  );
  if (!Array.isArray(rows)) throw new AdminError("DEPENDENCY_UNAVAILABLE", 503, "candidate query failed");
  if (rows.length === 0) return { candidates: [] };
  const positionIds = [...new Set(rows.map((row) => row.position_id))];
  const quoted = positionIds.map((id) => `"${id}"`).join(",");
  const { body: positions } = await supabaseFetch(
    config,
    `/rest/v1/admin_positions?tenant_id=eq.${tenant}&id=in.(${quoted})&select=id,external_key,title`,
  );
  if (!Array.isArray(positions)) throw new AdminError("DEPENDENCY_UNAVAILABLE", 503, "position query failed");
  const byId = new Map(positions.map((position) => [position.id, position]));
  return {
    candidates: rows.map((row) => {
      const position = byId.get(row.position_id);
      if (!position) throw new AdminError("DEPENDENCY_UNAVAILABLE", 503, "candidate position missing");
      return mapCandidate(row, position);
    }),
  };
}

async function updateReviewStatus(config, actorEmailHash, candidateId, status, expectedVersion) {
  if (!EMAIL_SHA256.test(actorEmailHash)) throw new AdminError("AUTH_REQUIRED", 401, "admin identity is invalid");
  if (!UUID.test(candidateId)) throw new AdminError("VALIDATION_FAILED", 400, "candidateId must be a UUID");
  if (!REVIEW_STATUSES.has(status)) throw new AdminError("VALIDATION_FAILED", 400, "invalid review status");
  if (!Number.isInteger(expectedVersion) || expectedVersion < 1) {
    throw new AdminError("VALIDATION_FAILED", 400, "expectedVersion must be a positive integer");
  }
  const id = encodeQuery(candidateId);
  const tenant = encodeQuery(config.tenantId);
  const nextStatus = encodeQuery(status);
  const { body: updated } = await supabaseFetch(
    config,
    `/rest/v1/admin_candidates?id=eq.${id}&tenant_id=eq.${tenant}&version=eq.${expectedVersion}&review_status=neq.${nextStatus}&select=id,review_status,version,updated_at`,
    {
      method: "PATCH",
      headers: { prefer: "return=representation" },
      body: JSON.stringify({
        review_status: status,
        version: expectedVersion + 1,
        pending_review_actor_email_sha256: actorEmailHash,
      }),
    },
  );
  if (Array.isArray(updated) && updated.length === 1) {
    const row = updated[0];
    return { candidateId: row.id, reviewStatus: row.review_status, version: row.version, updatedAt: row.updated_at };
  }
  const { body: existing } = await supabaseFetch(
    config,
    `/rest/v1/admin_candidates?id=eq.${id}&tenant_id=eq.${tenant}&select=id,review_status,version`,
  );
  if (!Array.isArray(existing) || existing.length === 0) throw new AdminError("NOT_FOUND", 404, "candidate not found");
  if (existing[0].version === expectedVersion && existing[0].review_status === status) {
    throw new AdminError("VALIDATION_FAILED", 400, "review status is unchanged");
  }
  throw new AdminError("VERSION_CONFLICT", 409, "candidate version changed");
}

module.exports = { REVIEW_STATUSES, listCandidates, updateReviewStatus };
