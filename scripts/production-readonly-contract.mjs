const FIFTEEN_MINUTES_MS = 15 * 60 * 1000;
const ONE_HOUR_MS = 60 * 60 * 1000;

function contractError(code) {
  const error = new Error(code);
  error.code = code;
  return error;
}

export function readonlyTokenExpiresAt(cookie) {
  try {
    const encodedSession = cookie.slice(cookie.indexOf("=") + 1);
    const session = JSON.parse(Buffer.from(encodedSession, "base64url").toString("utf8"));
    const jwtPayload = session.accessToken.split(".")[1];
    const claims = JSON.parse(Buffer.from(jwtPayload, "base64url").toString("utf8"));
    if (!Number.isInteger(claims.exp)) throw new Error("missing exp");
    return claims.exp * 1000;
  } catch (error) {
    throw contractError("invalid_PRODUCTION_READONLY_COOKIE_token_expiry");
  }
}

export function validateReadonlyCredential({ cookie, cookieExpiresAt, now = Date.now() }) {
  if (!cookie) throw contractError("missing_PRODUCTION_READONLY_COOKIE");
  if (!/^vh_admin_session=[A-Za-z0-9_-]+$/.test(cookie)) {
    throw contractError("invalid_PRODUCTION_READONLY_COOKIE");
  }
  const declaredExpiry = Date.parse(cookieExpiresAt || "");
  if (!Number.isFinite(declaredExpiry)) {
    throw contractError("missing_or_invalid_PRODUCTION_READONLY_COOKIE_EXPIRES_AT");
  }
  const cookieTtlMs = declaredExpiry - now;
  if (cookieTtlMs <= 0) throw contractError("production_readonly_cookie_expired");
  if (cookieTtlMs > FIFTEEN_MINUTES_MS) {
    throw contractError("production_readonly_cookie_ttl_exceeds_15_minutes");
  }
  const accessTokenTtlMs = readonlyTokenExpiresAt(cookie) - now;
  if (accessTokenTtlMs <= 0) throw contractError("production_readonly_access_token_expired");
  if (accessTokenTtlMs > ONE_HOUR_MS) {
    throw contractError("production_readonly_access_token_ttl_exceeds_60_minutes");
  }
  return { cookieTtlMs, accessTokenTtlMs };
}
