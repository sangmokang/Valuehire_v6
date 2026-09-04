"use strict";

class AdminError extends Error {
  constructor(code, status, message) {
    super(message);
    this.name = "AdminError";
    this.code = code;
    this.status = status;
  }
}

function sendJson(res, status, body, headers = {}) {
  res.statusCode = status;
  for (const [key, value] of Object.entries({
    "content-type": "application/json; charset=utf-8",
    "cache-control": "no-store",
    ...headers,
  })) {
    res.setHeader(key, value);
  }
  res.end(JSON.stringify(body));
}

function sendError(res, error) {
  const known = error instanceof AdminError;
  const status = known ? error.status : 500;
  const code = known ? error.code : "INTERNAL_ERROR";
  const message = known ? error.message : "request failed";
  sendJson(res, status, { error: { code, message } });
}

module.exports = { AdminError, sendError, sendJson };
