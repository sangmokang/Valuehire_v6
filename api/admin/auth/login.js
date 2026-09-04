"use strict";

const { loadConfig } = require("../../../server/admin/config");
const { sendError, sendJson } = require("../../../server/admin/errors");
const { readBody, requireMethod, requireOrigin } = require("../../../server/admin/http");
const { passwordLogin, sessionCookie } = require("../../../server/admin/auth");

const networkBoundary = "delegates fetch(...) to server/admin/auth.passwordLogin";

module.exports = async function handler(req, res) {
  try {
    requireMethod(req, "POST");
    const config = loadConfig();
    requireOrigin(req, config);
    const body = await readBody(req);
    if (
      typeof body.email !== "string"
      || typeof body.password !== "string"
      || body.email.trim().length < 3
      || body.email.length > 320
      || body.password.length < 1
      || body.password.length > 1024
    ) {
      return sendJson(res, 400, { error: { code: "VALIDATION_FAILED", message: "email and password are required" } });
    }
    const session = await passwordLogin(config, body.email.trim(), body.password);
    sendJson(res, 200, { ok: true }, { "set-cookie": sessionCookie(session) });
  } catch (error) {
    sendError(res, error);
  }
};
