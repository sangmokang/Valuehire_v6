import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const config = JSON.parse(readFileSync(new URL("../../vercel.json", import.meta.url), "utf8"));
const previewSmoke = readFileSync(new URL("../../scripts/smoke-preview-admin.mjs", import.meta.url), "utf8");

test("CSP protects every public static route, not only the admin alias", () => {
  const globalHeaders = config.headers.find((entry) => entry.source === "/(.*)");
  assert.ok(globalHeaders, "global headers contract is missing");
  const csp = globalHeaders.headers.find((entry) => entry.key === "Content-Security-Policy");
  assert.ok(csp, "global Content-Security-Policy is missing");
  for (const directive of [
    "default-src 'self'",
    "connect-src 'self'",
    "script-src 'self'",
    "style-src 'self'",
    "img-src 'self'",
    "object-src 'none'",
    "base-uri 'none'",
    "frame-ancestors 'none'",
    "form-action 'self'",
  ]) {
    assert.match(csp.value, new RegExp(directive.replaceAll("'", "\\'")));
  }
  assert.doesNotMatch(csp.value, /unsafe-inline|unsafe-eval/i);
  const hsts = globalHeaders.headers.find((entry) => entry.key === "Strict-Transport-Security");
  assert.equal(hsts?.value, "max-age=31536000; includeSubDomains");
});

test("Preview smoke proves the deployed CSP on static and API response surfaces", () => {
  assert.match(previewSmoke, /proveSecurityHeaders\(config\)/);
  for (const path of ["/admin", "/admin/ui.js", "/admin/styles.css", "/api/health"]) {
    assert.ok(previewSmoke.includes(JSON.stringify(path)), `Preview smoke does not probe ${path}`);
  }
  assert.match(previewSmoke, /response\.headers\.get\("content-security-policy"\)/);
  assert.match(previewSmoke, /DEPLOYED_CSP_MISSING/);
  assert.match(previewSmoke, /DEPLOYED_CSP_UNSAFE/);
});

test("Preview smoke proves deployment protection without a bypass credential", () => {
  assert.match(previewSmoke, /provePreviewAccessRestricted\(config\)/);
  assert.match(previewSmoke, /PREVIEW_PROTECTION_PATHS = \["\/admin", "\/api\/health"\]/);
  assert.match(previewSmoke, /fetch\(`\$\{config\.baseUrl\}\$\{path\}`, \{ redirect: "manual" \}\)/);
  assert.match(previewSmoke, /assert\(redirectedToVercel/);
  assert.match(previewSmoke, /PREVIEW_ACCESS_PUBLIC/);
  assert.match(previewSmoke, /VERCEL_DEPLOYMENT_PROTECTED: PASS/);
  assert.match(previewSmoke, /PREVIEW_ACCESS_RESTRICTED: PASS/);
});
