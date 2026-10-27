(function () {
  "use strict";

  const byId = (id) => document.getElementById(id);

  function element(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  }

  function known(value) {
    return value !== null && value !== undefined && value !== "";
  }

  function valueOrNotRun(value, reason) {
    if (known(value)) return String(value);
    return reason ? `NOT_RUN · ${reason}` : "NOT_RUN";
  }

  function statusBadge(status) {
    const value = status || "NOT_RUN";
    return element("span", `status-badge status-${value.toLowerCase()}`, value);
  }

  function formatDate(value) {
    if (!known(value)) return "NOT_RUN";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return String(value);
    return new Intl.DateTimeFormat("ko-KR", {
      year: "numeric", month: "2-digit", day: "2-digit",
      hour: "2-digit", minute: "2-digit", hour12: false,
    }).format(date);
  }

  function sumKnown(batches, select) {
    const values = batches.map(select);
    return values.every(known) ? values.reduce((sum, value) => sum + value, 0) : null;
  }

  function renderSummary(payload) {
    const hasEvidence = payload.batches.length > 0;
    const candidates = sumKnown(payload.batches, (batch) => batch.unique_candidates);
    const strong = sumKnown(payload.batches, (batch) => batch.score_buckets["90_plus"]);
    const fu = sumKnown(payload.batches, (batch) => batch.actual_fu);
    byId("cadence").textContent = payload.cadence;
    byId("evidence-status").replaceChildren(statusBadge(payload.status));
    byId("batch-count").textContent = hasEvidence ? String(payload.batches.length) : "NOT_RUN";
    byId("candidate-count").textContent = hasEvidence ? valueOrNotRun(candidates) : "NOT_RUN";
    byId("strong-count").textContent = hasEvidence ? valueOrNotRun(strong) : "NOT_RUN";
    byId("fu-count").textContent = hasEvidence ? valueOrNotRun(fu) : "NOT_RUN";
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
    const cell = element("td", "number-cell", valueOrNotRun(value));
    if (detail) cell.append(element("small", "", detail));
    return cell;
  }

  function periodLabel(period) {
    return period.status === "PASS"
      ? `${period.start} ~ ${period.end}`
      : `NOT_RUN · ${period.reason}`;
  }

  function renderRows(payload) {
    const root = byId("batch-rows");
    root.replaceChildren();
    byId("empty-state").hidden = payload.batches.length !== 0;
    byId("error-state").hidden = true;
    payload.batches.forEach((batch) => {
      const row = element("tr", "clickable-row");
      row.tabIndex = 0;
      row.setAttribute("role", "button");
      row.setAttribute("aria-label", `${batch.batch_id} 상세 열기`);
      row.append(
        batchCell(batch),
        accountCell(batch),
        element("td", "", batch.channels.join(" · ")),
        numberCell(batch.raw_candidates),
        numberCell(batch.unique_candidates),
        numberCell(batch.score_buckets["90_plus"], batch.score_reason),
        numberCell(batch.score_buckets["80s"], batch.score_reason),
        numberCell(batch.score_buckets["70s"], batch.score_reason),
        numberCell(batch.actual_fu, batch.actual_fu_reason),
        element("td", "date-cell", periodLabel(batch.search_period)),
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
    wrapper.append(element("dt", "", label), element("dd", "", valueOrNotRun(value)));
    return wrapper;
  }

  function evidenceList(title, values, fallback) {
    const wrapper = element("div", "candidate-copy");
    wrapper.append(element("h4", "", title));
    if (!values.length) {
      wrapper.append(element("p", "", fallback));
      return wrapper;
    }
    const list = element("ul");
    values.forEach((value) => list.append(element("li", "", value)));
    wrapper.append(list);
    return wrapper;
  }

  function betterPositionLabel(candidate) {
    if (candidate.better_position_exists === null) {
      return `NOT_RUN · ${candidate.better_position_reason}`;
    }
    if (!candidate.better_position_exists) return `없음 · ${candidate.better_position_reason}`;
    return `있음 · ${candidate.better_position} · ${candidate.better_position_reason}`;
  }

  function renderCandidate(candidate) {
    const article = element("article", "candidate-card");
    const heading = element("header");
    const title = element("div");
    title.append(
      element("p", "section-kicker", candidate.source_channel),
      element("h3", "", candidate.display_name),
      element("p", "profile-reference", candidate.profile_url),
    );
    const score = candidate.score_status === "PASS"
      ? `${candidate.score}점`
      : `NOT_RUN · ${candidate.score_reason}`;
    heading.append(title, element("strong", "candidate-score", score));
    const facts = element("dl", "candidate-facts");
    facts.append(
      detailItem("학력", candidate.education),
      detailItem("전체 경력", candidate.experience),
      detailItem("핵심 경력", candidate.key_experience),
      detailItem("컨택 상태", `${candidate.contact_status} · ${candidate.contact_recommendation}`),
      detailItem("컨택 출처", candidate.contact_source),
      detailItem("컨택 확인시각", known(candidate.contact_checked_at)
        ? formatDate(candidate.contact_checked_at) : null),
    );
    const contact = element("div", "candidate-copy");
    contact.append(
      element("h4", "", "컨택 의견 근거"),
      element("p", "", valueOrNotRun(candidate.contact_opinion_evidence, "contact_opinion_evidence_missing")),
      element("p", "evidence-meta", `contacted_at=${valueOrNotRun(candidate.contacted_at)} · reference=${valueOrNotRun(candidate.contact_reference)}`),
    );
    const better = element("div", "candidate-copy reverse-match");
    better.append(
      element("h4", "", "더 적합한 포지션 존재 여부"),
      element("p", "", betterPositionLabel(candidate)),
      element("p", "evidence-meta", `기존 역매칭: ${candidate.reverse_match_reason || "NOT_RUN"}`),
    );
    article.append(
      heading,
      facts,
      evidenceList(
        "필수요건별 근거",
        candidate.requirements_evidence,
        "NOT_RUN · requirements_evidence_missing",
      ),
      evidenceList("적합 근거", candidate.why_fit, "NOT_RUN · why_fit_evidence_missing"),
      contact,
      better,
    );
    return article;
  }

  function renderChecks(checks) {
    const root = byId("verification-checks");
    root.replaceChildren();
    if (!checks.length) {
      root.append(element("p", "empty-copy", "NOT_RUN · required_sources_not_checked"));
      return;
    }
    checks.forEach((check) => {
      const row = element("div", "verification-row");
      row.append(element("strong", "", check.source), statusBadge(check.status));
      row.append(element("span", "", check.checked_at ? formatDate(check.checked_at) : check.reason));
      root.append(row);
    });
  }

  function renderActorEvidence(evidence) {
    const root = byId("actor-evidence");
    root.replaceChildren();
    if (!evidence) {
      root.append(detailItem("판정 근거", "NOT_RUN · actor_evidence_missing"));
      return;
    }
    root.append(
      detailItem("제목", evidence.subject),
      detailItem("발신자", evidence.sender),
      detailItem("Thread ID", evidence.thread_id),
      detailItem("Message ID", evidence.message_id),
      detailItem("수신 시각", formatDate(evidence.received_at)),
      detailItem("판정", evidence.reason),
    );
  }

  function showError(reason) {
    byId("ai-search").setAttribute("aria-busy", "false");
    byId("evidence-status").replaceChildren(statusBadge("FAIL"));
    byId("batch-count").textContent = "NOT_RUN";
    byId("candidate-count").textContent = "NOT_RUN";
    byId("strong-count").textContent = "NOT_RUN";
    byId("fu-count").textContent = "NOT_RUN";
    byId("empty-state").hidden = true;
    byId("error-state").hidden = false;
    byId("error-reason").textContent = reason;
    const state = byId("load-state");
    state.dataset.status = "FAIL";
    state.textContent = `AI Search 증빙 미집계 · ${reason}`;
  }

  async function openDetail(batchId) {
    try {
      const response = await fetch(`/api/ai-search/${encodeURIComponent(batchId)}`, {
        cache: "no-store", headers: { Accept: "application/json" },
      });
      if (!response.ok) throw new Error("batch_detail_failed");
      const batch = await response.json();
      byId("dialog-batch").textContent = batch.batch_id;
      byId("dialog-title").textContent = `${batch.company} · ${batch.position}`;
      const counts = batch.candidate_counts;
      const summary = byId("dialog-summary");
      summary.replaceChildren(
        detailItem("실행 주체", batch.actor_label),
        detailItem("실행 일시", formatDate(batch.executed_at)),
        detailItem("검색 기간", periodLabel(batch.search_period)),
        detailItem(
          "원시 → 파싱",
          `${valueOrNotRun(counts.raw, batch.candidate_counts_reason)} → ${counts.parsed}`,
        ),
        detailItem(
          "중복 / 미파싱 / 제외",
          `${counts.duplicate} / ${valueOrNotRun(counts.unparsed, batch.candidate_counts_reason)} / ${counts.excluded}`,
        ),
        detailItem("실제 FU", valueOrNotRun(batch.actual_fu, batch.actual_fu_reason)),
      );
      renderActorEvidence(batch.actor_evidence);
      const candidates = byId("candidate-details");
      candidates.replaceChildren();
      if (batch.candidates.length) {
        candidates.append(...batch.candidates.map(renderCandidate));
      } else {
        candidates.append(element("p", "empty-copy", "파싱된 후보가 없습니다. count ledger를 확인하세요."));
      }
      renderChecks(batch.verification_checks);
      byId("batch-dialog").showModal();
    } catch (_error) {
      showError("batch_detail_failed");
    }
  }

  function renderAudit(payload) {
    const gmail = payload.gmail_collection || {};
    const gmailStatus = known(gmail.status) ? gmail.status : "NOT_RUN";
    const gmailMessageCount = known(gmail.message_count)
      ? gmail.message_count
      : "NOT_RUN";
    const items = [
      ["MODE", payload.mode],
      ["CONTRACT", payload.contract_version],
      ["GMAIL", `${gmailStatus} · ${gmailMessageCount} messages`],
      ["PAGINATION", gmail.pagination_exhausted === true ? "EXHAUSTED" : "NOT_RUN"],
      ["REMOTE DB WRITES", payload.external_effects.database_writes],
      ["OUTREACH SENDS", payload.external_effects.outreach_sends],
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
      showError("ai_search_load_failed");
    }
  }

  loadAiSearch();
}());
