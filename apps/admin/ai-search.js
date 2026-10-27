(function () {
  "use strict";

  const byId = (id) => document.getElementById(id);

  function element(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  }

  function statusBadge(status) {
    return element("span", `status-badge status-${status.toLowerCase()}`, status);
  }

  function formatDate(value) {
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return value;
    return new Intl.DateTimeFormat("ko-KR", {
      month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit", hour12: false,
    }).format(date);
  }

  function renderSummary(payload) {
    const totals = payload.batches.reduce((sum, batch) => ({
      candidates: sum.candidates + batch.unique_candidates,
      strong: sum.strong + batch.score_buckets["90_plus"],
      fu: sum.fu + batch.actual_fu,
    }), { candidates: 0, strong: 0, fu: 0 });
    const hasEvidence = payload.batches.length > 0;
    byId("cadence").textContent = payload.cadence;
    byId("evidence-status").replaceChildren(statusBadge(payload.status));
    byId("batch-count").textContent = hasEvidence ? String(payload.batches.length) : "—";
    byId("candidate-count").textContent = hasEvidence ? String(totals.candidates) : "—";
    byId("strong-count").textContent = hasEvidence ? String(totals.strong) : "—";
    byId("fu-count").textContent = hasEvidence ? String(totals.fu) : "—";
  }

  function accountCell(batch) {
    const cell = element("td");
    cell.append(element("strong", "", batch.company), element("small", "", batch.position));
    return cell;
  }

  function batchCell(batch) {
    const cell = element("td");
    cell.append(element("strong", "", batch.actor_label), element("small", "batch-code", batch.batch_id));
    return cell;
  }

  function numberCell(value, detail) {
    const cell = element("td", "number-cell", String(value));
    if (detail) cell.append(element("small", "", detail));
    return cell;
  }

  function renderRows(payload) {
    const root = byId("batch-rows");
    root.replaceChildren();
    byId("empty-state").hidden = payload.batches.length !== 0;
    payload.batches.forEach((batch) => {
      const row = element("tr", "clickable-row");
      row.tabIndex = 0;
      row.setAttribute("role", "button");
      row.setAttribute("aria-label", `${batch.batch_id} 상세 열기`);
      row.append(
        batchCell(batch),
        accountCell(batch),
        element("td", "", batch.channels.join(" · ")),
        numberCell(batch.unique_candidates, `원시 ${batch.raw_candidates}`),
        numberCell(batch.score_buckets["90_plus"]),
        numberCell(batch.score_buckets["80s"]),
        numberCell(batch.score_buckets["70s"]),
        numberCell(batch.actual_fu),
        element("td", "date-cell", formatDate(batch.executed_at)),
      );
      const status = element("td");
      status.append(statusBadge(batch.verification_status));
      row.append(status);
      row.addEventListener("click", () => openDetail(batch.batch_id));
      row.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          openDetail(batch.batch_id);
        }
      });
      root.append(row);
    });
  }

  function detailItem(label, value) {
    const wrapper = element("div");
    wrapper.append(element("dt", "", label), element("dd", "", value || "미확인"));
    return wrapper;
  }

  function renderCandidate(candidate) {
    const article = element("article", "candidate-card");
    const heading = element("header");
    const title = element("div");
    title.append(element("p", "section-kicker", candidate.source_channel), element("h3", "", candidate.display_name));
    heading.append(title, element("strong", "candidate-score", `${candidate.score}점`));
    const facts = element("dl", "candidate-facts");
    facts.append(
      detailItem("학력", candidate.education),
      detailItem("경력", candidate.experience),
      detailItem("컨택 증빙", candidate.contact_status),
      detailItem("컨택 의견", candidate.contact_recommendation),
    );
    const why = element("div", "candidate-copy");
    why.append(element("h4", "", "왜 잘 맞는가"));
    const list = element("ul");
    candidate.why_fit.forEach((reason) => list.append(element("li", "", reason)));
    why.append(list);
    const reverse = element("div", "candidate-copy reverse-match");
    reverse.append(
      element("h4", "", "역매칭 재검증"),
      element("p", "", candidate.reverse_match_position
        ? `${candidate.reverse_match_position} · ${candidate.reverse_match_score}점 — ${candidate.reverse_match_reason}`
        : candidate.reverse_match_reason || "NOT_RUN"),
    );
    article.append(heading, facts, why, reverse);
    return article;
  }

  function renderChecks(checks) {
    const root = byId("verification-checks");
    root.replaceChildren();
    if (!checks.length) {
      root.append(element("p", "empty-copy", "필수 채널 검증이 아직 실행되지 않았습니다."));
      return;
    }
    checks.forEach((check) => {
      const row = element("div", "verification-row");
      row.append(element("strong", "", check.source), statusBadge(check.status));
      row.append(element("span", "", check.checked_at ? formatDate(check.checked_at) : check.reason));
      root.append(row);
    });
  }

  async function openDetail(batchId) {
    const response = await fetch(`/api/ai-search/${encodeURIComponent(batchId)}`, {
      cache: "no-store", headers: { Accept: "application/json" },
    });
    if (!response.ok) throw new Error("batch_detail_failed");
    const batch = await response.json();
    byId("dialog-batch").textContent = batch.batch_id;
    byId("dialog-title").textContent = `${batch.company} · ${batch.position}`;
    const summary = byId("dialog-summary");
    summary.replaceChildren(
      detailItem("실행 주체", batch.actor_label),
      detailItem("실행 일시", formatDate(batch.executed_at)),
      detailItem("중복 제거", `${batch.raw_candidates} → ${batch.unique_candidates}명`),
      detailItem("실제 FU", `${batch.actual_fu}명`),
    );
    const candidates = byId("candidate-details");
    candidates.replaceChildren(...batch.candidates.map(renderCandidate));
    renderChecks(batch.verification_checks);
    byId("batch-dialog").showModal();
  }

  function renderAudit(payload) {
    const items = [
      ["MODE", payload.mode], ["CONTRACT", payload.contract_version],
      ["STATUS", payload.status], ["WRITES", "DISABLED"],
    ];
    const root = byId("audit-items");
    root.replaceChildren();
    items.forEach(([label, value]) => {
      const wrapper = element("div");
      wrapper.append(element("dt", "", label), element("dd", "", value));
      root.append(wrapper);
    });
  }

  async function loadAiSearch() {
    const state = byId("load-state");
    try {
      const response = await fetch("/api/ai-search", {
        cache: "no-store", headers: { Accept: "application/json" },
      });
      if (!response.ok) throw new Error("ai_search_request_failed");
      const payload = await response.json();
      renderSummary(payload);
      renderRows(payload);
      renderAudit(payload);
      byId("ai-search").setAttribute("aria-busy", "false");
      document.body.dataset.ready = "true";
      state.dataset.status = payload.status;
      state.textContent = payload.status === "PASS"
        ? "일일 검증이 완료되었습니다."
        : `미집계 · ${payload.reason || "evidence_not_ready"}`;
    } catch (_error) {
      byId("ai-search").setAttribute("aria-busy", "false");
      state.dataset.status = "FAIL";
      state.textContent = "AI Search 증빙 미집계 · ai_search_load_failed";
    }
  }

  loadAiSearch();
}());
