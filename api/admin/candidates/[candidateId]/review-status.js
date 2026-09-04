"use strict";

const { loadConfig } = require("../../../../server/admin/config");
const { sendError, sendJson } = require("../../../../server/admin/errors");
const { readBody, requireMethod, requireOrigin } = require("../../../../server/admin/http");
const { requireAdmin } = require("../../../../server/admin/auth");
const { updateReviewStatus } = require("../../../../server/admin/candidates");

const networkBoundary = "delegates fetch(...) to server/admin/auth.requireAdmin and candidates.updateReviewStatus";

function candidateIdFromUrl(req) {
  const pathname = new URL(req.url, "https://valuehire.invalid").pathname;
  const match = pathname.match(/\/api\/admin\/candidates\/([^/]+)\/review-status$/);
  if (!match) return "";
  try {
    return decodeURIComponent(match[1]);
  } catch (error) {
    return "";
  }
}

module.exports = async function handler(req, res) {
  try {
    requireMethod(req, "PATCH");
    const config = loadConfig();
    requireOrigin(req, config);
    const admin = await requireAdmin(req, config);
    const body = await readBody(req);
    const result = await updateReviewStatus(config, admin.emailHash, candidateIdFromUrl(req), body.status, body.expectedVersion);
    sendJson(res, 200, result);
  } catch (error) {
    sendError(res, error);
  }
};
