"use strict";

const { createHash } = require("node:crypto");
const { loadConfig } = require("../server/admin/config");
const { sendError, sendJson } = require("../server/admin/errors");
const { requireMethod } = require("../server/admin/http");
const { supabaseFetch } = require("../server/admin/supabase");

function fingerprint(value) {
  return createHash("sha256").update(value).digest("hex").slice(0, 12);
}

module.exports = async function handler(req, res) {
  try {
    requireMethod(req, "GET");
    const config = loadConfig();
    await supabaseFetch(config, "/rest/v1/admin_positions?select=id&limit=1");
    sendJson(res, 200, {
      ok: true,
      environment: config.environment,
      commitSha: config.deploySha,
      systemGitShaPresent: config.systemGitShaPresent,
      schemaDigest: config.schemaDigest,
      supabaseRefFingerprint: fingerprint(new URL(config.supabaseUrl).hostname.split(".")[0]),
      database: "reachable",
      outbound: { email: "DISABLED", sms: "DISABLED", portal: "DISABLED", sentCount: 0 },
    });
  } catch (error) {
    sendError(res, error);
  }
};
