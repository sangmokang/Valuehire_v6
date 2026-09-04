"use strict";

const { loadConfig } = require("../../../server/admin/config");
const { sendError, sendJson } = require("../../../server/admin/errors");
const { requireMethod } = require("../../../server/admin/http");
const { requireAdmin } = require("../../../server/admin/auth");
const { listCandidates } = require("../../../server/admin/candidates");

const networkBoundary = "delegates fetch(...) to server/admin/auth.requireAdmin and candidates.listCandidates";

module.exports = async function handler(req, res) {
  try {
    requireMethod(req, "GET");
    const config = loadConfig();
    await requireAdmin(req, config);
    sendJson(res, 200, await listCandidates(config));
  } catch (error) {
    sendError(res, error);
  }
};
