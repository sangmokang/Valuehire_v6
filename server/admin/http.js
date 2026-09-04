"use strict";

const { AdminError } = require("./errors");

function readBody(req, maxBytes = 8192) {
  return new Promise((resolve, reject) => {
    let raw = "";
    req.on("data", (chunk) => {
      raw += chunk;
      if (Buffer.byteLength(raw) > maxBytes) {
        reject(new AdminError("VALIDATION_FAILED", 400, "request body too large"));
        req.destroy();
      }
    });
    req.on("error", () => reject(new AdminError("DEPENDENCY_UNAVAILABLE", 503, "request stream failed")));
    req.on("end", () => {
      if (!raw) return resolve({});
      try {
        return resolve(JSON.parse(raw));
      } catch (error) {
        return reject(new AdminError("VALIDATION_FAILED", 400, "invalid JSON body"));
      }
    });
  });
}

function requireMethod(req, method) {
  if (req.method !== method) {
    throw new AdminError("METHOD_NOT_ALLOWED", 405, "method not allowed");
  }
}

function requireOrigin(req, config) {
  const origin = req.headers.origin;
  if (origin !== config.publicUrl) {
    throw new AdminError("CSRF_REJECTED", 403, "write origin rejected");
  }
}

function parseCookies(req) {
  const out = new Map();
  const header = req.headers.cookie || "";
  for (const part of header.split(";")) {
    const index = part.indexOf("=");
    if (index > 0) out.set(part.slice(0, index).trim(), part.slice(index + 1).trim());
  }
  return out;
}

module.exports = { parseCookies, readBody, requireMethod, requireOrigin };
