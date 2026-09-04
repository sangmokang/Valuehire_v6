"use strict";

const { loadConfig } = require("../../../server/admin/config");
const { sendError, sendJson } = require("../../../server/admin/errors");
const { requireMethod, requireOrigin } = require("../../../server/admin/http");
const { expiredSessionCookie, revokeSession } = require("../../../server/admin/auth");

const networkBoundary = "delegates fetch(...) to server/admin/auth.revokeSession";

module.exports = async function handler(req, res) {
  try {
    requireMethod(req, "DELETE");
    const config = loadConfig();
    requireOrigin(req, config);
    await revokeSession(req, config);
    sendJson(res, 200, { ok: true }, { "set-cookie": expiredSessionCookie() });
  } catch (error) {
    if (error?.code === "DEPENDENCY_UNAVAILABLE") {
      return sendJson(
        res,
        error.status,
        { error: { code: error.code, message: error.message, localSessionCleared: true } },
        { "set-cookie": expiredSessionCookie() },
      );
    }
    sendError(res, error);
  }
};
