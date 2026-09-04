import assert from "node:assert/strict";
import { test } from "node:test";

function makeClassList(node) {
  const tokens = new Set();
  return {
    add(value) {
      tokens.add(value);
      node.className = [...tokens].join(" ");
    },
    remove(value) {
      tokens.delete(value);
      node.className = [...tokens].join(" ");
    },
    contains(value) {
      return tokens.has(value);
    },
  };
}

function makeNode(tagName, ownerDocument) {
  const listeners = new Map();
  const node = {
    tagName: tagName.toUpperCase(),
    ownerDocument,
    children: [],
    attributes: new Map(),
    dataset: {},
    style: {},
    className: "",
    textContent: "",
    value: "",
    disabled: false,
    hidden: false,
    type: "",
    id: "",
    append(...items) {
      for (const item of items) this.appendChild(item);
    },
    appendChild(child) {
      child.parentNode = this;
      this.children.push(child);
      return child;
    },
    replaceChildren(...items) {
      this.children = [];
      this.textContent = "";
      this.append(...items);
    },
    setAttribute(name, value) {
      this.attributes.set(name, String(value));
      if (name === "id") {
        this.id = String(value);
        ownerDocument.nodes.set(this.id, this);
      }
      if (name === "class") this.className = String(value);
    },
    getAttribute(name) {
      if (!this.attributes.has(name)) return null;
      return this.attributes.get(name);
    },
    addEventListener(type, callback) {
      if (!listeners.has(type)) listeners.set(type, []);
      listeners.get(type).push(callback);
    },
    async dispatch(type, event = {}) {
      const callbacks = listeners.has(type) ? listeners.get(type) : [];
      for (const callback of callbacks) {
        await callback({
          preventDefault() {},
          target: this,
          ...event,
        });
      }
    },
    querySelector(selector) {
      if (selector.startsWith("#")) return ownerDocument.getElementById(selector.slice(1));
      return findFirst(this, selector);
    },
    querySelectorAll(selector) {
      return findAll(this, selector);
    },
  };
  node.classList = makeClassList(node);
  return node;
}

function findAll(root, selector) {
  const found = [];
  const matches = (node) => {
    if (selector.startsWith("[data-testid=")) {
      const expected = selector.slice(13, -1).replaceAll('"', "");
      return node.dataset.testid === expected;
    }
    return node.tagName.toLowerCase() === selector.toLowerCase();
  };
  const visit = (node) => {
    if (matches(node)) found.push(node);
    const children = Array.isArray(node.children) ? node.children : [];
    for (const child of children) visit(child);
  };
  visit(root);
  return found;
}

function findFirst(root, selector) {
  const matches = findAll(root, selector);
  return matches.length > 0 ? matches[0] : null;
}

function collectText(node) {
  return [node.textContent, ...node.children.map(collectText)].join(" ");
}

function makeDocument() {
  const document = {
    nodes: new Map(),
    body: null,
    createElement(tagName) {
      return makeNode(tagName, document);
    },
    getElementById(id) {
      return this.nodes.has(id) ? this.nodes.get(id) : null;
    },
    querySelector(selector) {
      return this.body.querySelector(selector);
    },
  };
  document.body = document.createElement("body");
  for (const id of [
    "app",
    "login-form",
    "email",
    "password",
    "login-error",
    "candidate-region",
    "candidate-list",
    "status-message",
    "logout-button",
  ]) {
    const node = document.createElement(id === "login-form" ? "form" : "div");
    node.setAttribute("id", id);
    document.body.appendChild(node);
  }
  document.getElementById("email").value = "owner@example.invalid";
  document.getElementById("password").value = "passphrase";
  return document;
}

function jsonResponse(status, body, headers = {}) {
  return {
    ok: status >= 200 && status < 300,
    status,
    headers: { get: (name) => (name.toLowerCase() in headers ? headers[name.toLowerCase()] : null) },
    async json() {
      return body;
    },
  };
}

function makeFetch(responses) {
  const calls = [];
  const fetchImpl = async (url, options = {}) => {
    calls.push({ url, options });
    const next = responses.shift();
    assert.ok(next, `unexpected fetch call to ${url}`);
    assert.equal(url, next.url);
    return jsonResponse(next.status, next.body);
  };
  fetchImpl.calls = calls;
  return fetchImpl;
}

test("production admin UI authenticates, updates review status, and reloads persisted state", async () => {
  const { createProductionAdmin } = await import("../../apps/production-admin/ui.js");
  const document = makeDocument();
  const fetchImpl = makeFetch([
    { url: "/api/admin/candidates", status: 401, body: { error: { code: "AUTH_REQUIRED", message: "login required" } } },
    { url: "/api/admin/auth/login", status: 401, body: { error: { code: "AUTH_INVALID", message: "invalid credentials" } } },
    { url: "/api/admin/auth/login", status: 200, body: { ok: true } },
    { url: "/api/admin/candidates", status: 200, body: { candidates: [candidate("unreviewed", 1)] } },
    { url: "/api/admin/candidates/candidate-1/review-status", status: 200, body: { candidateId: "candidate-1", reviewStatus: "reviewed", version: 2, updatedAt: "2026-09-04T00:00:00Z" } },
    { url: "/api/admin/candidates", status: 200, body: { candidates: [candidate("reviewed", 2)] } },
  ]);
  const storageTrap = new Proxy({}, {
    get() {
      throw new Error("browser storage must not be used");
    },
  });

  const app = createProductionAdmin({
    document,
    fetch: fetchImpl,
    localStorage: storageTrap,
    sessionStorage: storageTrap,
  });
  await app.start();

  assert.equal(document.getElementById("login-form").hidden, false);
  await document.getElementById("login-form").dispatch("submit");
  assert.match(document.getElementById("login-error").textContent, /AUTH_INVALID/);

  document.getElementById("password").value = "correct";
  await document.getElementById("login-form").dispatch("submit");
  assert.equal(document.getElementById("candidate-region").hidden, false);
  assert.equal(document.getElementById("candidate-list").querySelectorAll("[data-testid=candidate-card]").length, 1);

  const selector = document.getElementById("candidate-list").querySelector("select");
  selector.value = "reviewed";
  await selector.dispatch("change", { target: selector });
  assert.match(document.getElementById("status-message").textContent, /reviewed/);

  await app.start();
  assert.match(collectText(document.getElementById("candidate-list")), /reviewed/);
  const mutatingCalls = fetchImpl.calls.filter((call) => call.options.method === "POST" || call.options.method === "PATCH");
  assert.equal(mutatingCalls.every((call) => call.options.headers.accept === "application/json"), true);
  assert.equal(mutatingCalls.every((call) => call.options.headers["content-type"] === "application/json"), true);
  assert.equal(fetchImpl.calls.some((call) => /localStorage|sessionStorage/.test(JSON.stringify(call))), false);
});

test("production admin UI preserves the full candidate list after one status update", async () => {
  const { createProductionAdmin } = await import("../../apps/production-admin/ui.js");
  const document = makeDocument();
  const fetchImpl = makeFetch([
    { url: "/api/admin/candidates", status: 200, body: { candidates: [candidate("unreviewed", 1), candidate("reviewed", 7, "candidate-2", "E2E-TEST-CANDIDATE-2")] } },
    { url: "/api/admin/candidates/candidate-1/review-status", status: 200, body: { candidateId: "candidate-1", reviewStatus: "rejected", version: 2, updatedAt: "2026-09-04T00:00:00Z" } },
  ]);

  const app = createProductionAdmin({ document, fetch: fetchImpl });
  await app.start();

  const firstSelector = document.getElementById("candidate-list").querySelector("select");
  firstSelector.value = "rejected";
  await firstSelector.dispatch("change", { target: firstSelector });

  const cards = document.getElementById("candidate-list").querySelectorAll("[data-testid=candidate-card]");
  assert.equal(cards.length, 2);
  assert.match(collectText(document.getElementById("candidate-list")), /E2E-TEST-CANDIDATE/);
  assert.match(collectText(document.getElementById("candidate-list")), /E2E-TEST-CANDIDATE-2/);
  assert.equal(cards[0].querySelector("select").value, "rejected");
  assert.equal(cards[1].querySelector("select").value, "reviewed");
});

test("production admin UI exposes typed API errors instead of showing empty success", async () => {
  const { createProductionAdmin } = await import("../../apps/production-admin/ui.js");
  const document = makeDocument();
  const fetchImpl = makeFetch([
    { url: "/api/admin/candidates", status: 502, body: { error: { code: "DEPENDENCY_UNAVAILABLE", message: "database unavailable" } } },
  ]);

  const app = createProductionAdmin({ document, fetch: fetchImpl });
  await app.start();

  assert.equal(document.getElementById("candidate-region").hidden, true);
  assert.match(document.getElementById("status-message").textContent, /DEPENDENCY_UNAVAILABLE/);
  assert.equal(document.getElementById("candidate-list").children.length, 0);
});

test("production admin UI clears local state when remote logout fails after cookie expiry", async () => {
  const { createProductionAdmin } = await import("../../apps/production-admin/ui.js");
  const document = makeDocument();
  const fetchImpl = makeFetch([
    { url: "/api/admin/candidates", status: 200, body: { candidates: [candidate("reviewed", 2)] } },
    { url: "/api/admin/auth/session", status: 503, body: { error: { code: "DEPENDENCY_UNAVAILABLE", message: "logout failed", localSessionCleared: true } } },
  ]);

  const app = createProductionAdmin({ document, fetch: fetchImpl });
  await app.start();
  await document.getElementById("logout-button").dispatch("click");

  assert.equal(document.getElementById("candidate-region").hidden, true);
  assert.equal(document.getElementById("candidate-list").children.length, 0);
  assert.match(document.getElementById("status-message").textContent, /DEPENDENCY_UNAVAILABLE/);
  assert.match(document.getElementById("status-message").textContent, /로컬 세션은 종료/);
});

test("production admin UI rejects non-JSON success responses", async () => {
  const { createProductionAdmin } = await import("../../apps/production-admin/ui.js");
  const document = makeDocument();
  const fetchImpl = async () => ({
    ok: true,
    status: 200,
    async json() { throw new SyntaxError("not JSON"); },
  });

  const app = createProductionAdmin({ document, fetch: fetchImpl });
  await app.start();

  assert.equal(document.getElementById("candidate-region").hidden, true);
  assert.match(document.getElementById("status-message").textContent, /NON_JSON_RESPONSE/);
});

function candidate(reviewStatus, version, id = "candidate-1", displayName = "E2E-TEST-CANDIDATE") {
  return {
    id,
    displayName,
    reviewStatus,
    version,
    position: { id: "position-1", title: "E2E-TEST-POSITION" },
  };
}
