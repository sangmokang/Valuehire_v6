const REVIEW_STATUSES = ["unreviewed", "reviewed", "rejected"];

function byId(document, id) {
  const node = document.getElementById(id);
  if (!node) throw new Error(`missing_element:${id}`);
  return node;
}

function createElement(document, tagName, className, text) {
  const node = document.createElement(tagName);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function errorText(error) {
  if (error?.code) return `${error.code}: ${error.message || "request failed"}`;
  return "UNEXPECTED_FAILURE: request failed";
}

async function readBody(response) {
  try {
    return await response.json();
  } catch (error) {
    const invalid = new Error("server response was not JSON");
    invalid.code = "NON_JSON_RESPONSE";
    invalid.status = response.status;
    throw invalid;
  }
}

async function requestJson(fetchImpl, path, options = {}) {
  const response = await fetchImpl(path, {
    credentials: "same-origin",
    cache: "no-store",
    ...options,
    headers: {
      accept: "application/json",
      ...(options.body ? { "content-type": "application/json" } : {}),
      ...(options.headers || {}),
    },
  });
  const body = await readBody(response);
  if (!response.ok) {
    const providerError = body?.error || {};
    const error = new Error(providerError.message || `HTTP ${response.status}`);
    error.code = providerError.code || "REQUEST_FAILED";
    error.status = response.status;
    error.localSessionCleared = providerError.localSessionCleared === true;
    throw error;
  }
  return body;
}

function setMessage(nodes, message) {
  nodes.status.textContent = message;
}

function showLogin(nodes, reason) {
  nodes.loginForm.hidden = false;
  nodes.candidateRegion.hidden = true;
  if (reason) setMessage(nodes, reason);
}

function showWorkspace(nodes) {
  nodes.loginForm.hidden = true;
  nodes.loginError.textContent = "";
  nodes.candidateRegion.hidden = false;
}

function renderCandidate(document, candidate, onStatusChange) {
  const card = createElement(document, "article", "candidate-card");
  card.dataset.testid = "candidate-card";

  const copy = createElement(document, "div");
  copy.append(
    createElement(document, "h3", "", candidate.displayName),
    createElement(document, "p", "candidate-meta", `포지션: ${candidate.position.title}`),
    createElement(document, "p", "candidate-meta", `현재 상태: ${candidate.reviewStatus}`),
  );

  const label = createElement(document, "label", "status-control", "검토 상태");
  const selector = createElement(document, "select");
  selector.setAttribute("aria-label", `${candidate.displayName} 검토 상태`);
  for (const status of REVIEW_STATUSES) {
    const option = createElement(document, "option", "", status);
    option.value = status;
    if (status === candidate.reviewStatus) option.selected = true;
    selector.append(option);
  }
  selector.value = candidate.reviewStatus;
  selector.addEventListener("change", () => onStatusChange(candidate, selector));
  label.append(selector);

  card.append(copy, label);
  return card;
}

function getNodes(document) {
  return {
    loginForm: byId(document, "login-form"),
    email: byId(document, "email"),
    password: byId(document, "password"),
    loginError: byId(document, "login-error"),
    candidateRegion: byId(document, "candidate-region"),
    candidateList: byId(document, "candidate-list"),
    status: byId(document, "status-message"),
    logoutButton: byId(document, "logout-button"),
  };
}

function validateCandidate(candidate) {
  return Boolean(
    candidate
      && typeof candidate.id === "string"
      && typeof candidate.displayName === "string"
      && REVIEW_STATUSES.includes(candidate.reviewStatus)
      && Number.isInteger(candidate.version)
      && candidate.position
      && typeof candidate.position.id === "string"
      && typeof candidate.position.title === "string",
  );
}

function createCandidateLoader(fetchImpl, nodes, renderCandidates) {
  return async function loadCandidates() {
    const body = await requestJson(fetchImpl, "/api/admin/candidates");
    if (!Array.isArray(body.candidates)) {
      const error = new Error("candidate response missing candidates array");
      error.code = "CONTRACT_INVALID";
      throw error;
    }
    const candidates = body.candidates;
    if (candidates.length === 0) {
      const error = new Error("candidate list was empty");
      error.code = "EMPTY_RESULT";
      throw error;
    }
    if (!candidates.every(validateCandidate)) {
      const error = new Error("candidate response failed UI validation");
      error.code = "CONTRACT_INVALID";
      throw error;
    }
    showWorkspace(nodes);
    renderCandidates(candidates);
    setMessage(nodes, `조회 ${candidates.length}건`);
  };
}

function createLoginHandler(fetchImpl, nodes, loadCandidates) {
  return async function login(event) {
    event.preventDefault();
    nodes.loginError.textContent = "";
    setMessage(nodes, "로그인 확인 중");
    try {
      await requestJson(fetchImpl, "/api/admin/auth/login", {
        method: "POST",
        body: JSON.stringify({
          email: nodes.email.value,
          password: nodes.password.value,
        }),
      });
      nodes.password.value = "";
      await loadCandidates();
    } catch (error) {
      nodes.password.value = "";
      nodes.loginError.textContent = errorText(error);
      showLogin(nodes, errorText(error));
    }
  };
}

function createStatusUpdater(fetchImpl, nodes, renderSingleCandidate) {
  return async function updateStatus(candidate, selector) {
    const nextStatus = selector.value;
    selector.disabled = true;
    try {
      const body = await requestJson(fetchImpl, `/api/admin/candidates/${candidate.id}/review-status`, {
        method: "PATCH",
        body: JSON.stringify({
          status: nextStatus,
          expectedVersion: candidate.version,
        }),
      });
      candidate.reviewStatus = body.reviewStatus;
      candidate.version = body.version;
      renderSingleCandidate(candidate);
      setMessage(nodes, `저장됨: ${body.reviewStatus}`);
    } catch (error) {
      selector.value = candidate.reviewStatus;
      setMessage(nodes, errorText(error));
    } finally {
      selector.disabled = false;
    }
  };
}

function createLogoutHandler(fetchImpl, nodes) {
  return async function logout() {
    try {
      await requestJson(fetchImpl, "/api/admin/auth/session", { method: "DELETE" });
    } catch (error) {
      if (error.localSessionCleared) {
        nodes.candidateList.replaceChildren();
        showLogin(nodes, `${errorText(error)}; 로컬 세션은 종료되었습니다.`);
        return;
      }
      setMessage(nodes, errorText(error));
      return;
    }
    nodes.candidateList.replaceChildren();
    showLogin(nodes, "로그아웃됨");
  };
}

function createStartHandler(nodes, loadCandidates) {
  return async function start() {
    try {
      await loadCandidates();
    } catch (error) {
      nodes.candidateList.replaceChildren();
      if (error.status === 401 || error.code === "AUTH_REQUIRED") {
        showLogin(nodes, "로그인이 필요합니다.");
        return;
      }
      showLogin(nodes, errorText(error));
    }
  };
}

export function createProductionAdmin(options) {
  const document = options.document;
  const fetchImpl = options.fetch;
  const nodes = getNodes(document);

  let updateStatus = null;
  let currentCandidates = [];
  const renderCandidateList = (candidates) => {
    const cards = candidates.map((candidate) => renderCandidate(document, candidate, updateStatus));
    nodes.candidateList.replaceChildren(...cards);
  };
  const renderCandidates = (candidates) => {
    currentCandidates = candidates;
    renderCandidateList(currentCandidates);
  };
  const renderUpdatedCandidate = (candidate) => {
    currentCandidates = currentCandidates.map((current) => (
      current.id === candidate.id ? candidate : current
    ));
    renderCandidateList(currentCandidates);
  };
  updateStatus = createStatusUpdater(fetchImpl, nodes, renderUpdatedCandidate);
  const loadCandidates = createCandidateLoader(fetchImpl, nodes, renderCandidates);
  const login = createLoginHandler(fetchImpl, nodes, loadCandidates);
  const logout = createLogoutHandler(fetchImpl, nodes);
  const start = createStartHandler(nodes, loadCandidates);

  nodes.loginForm.addEventListener("submit", login);
  nodes.logoutButton.addEventListener("click", logout);

  return { start };
}

if (typeof document !== "undefined" && typeof fetch !== "undefined") {
  createProductionAdmin({ document, fetch }).start();
}
