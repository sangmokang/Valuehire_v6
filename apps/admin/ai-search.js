(function () {
  "use strict";

  const byId = (id) => document.getElementById(id);
  const REASON_LABELS = {
    daily_verification_incomplete: "일일 재검증은 아직 하지 않았습니다.",
    search_period_not_found: "메일에 검색 기간이 없습니다.",
    fu_portal_verification_not_run: "채용사이트 후속 연락 확인은 아직 하지 않았습니다.",
    fu_portal_verification_out_of_scope: "이번 화면에서는 채용사이트를 확인하지 않습니다.",
    score_contract_evidence_missing: "점수 계산에 필요한 근거가 부족합니다.",
    score_contract_evidence_conflict: "메일 안의 점수 근거가 서로 다릅니다.",
    no_parsed_candidates: "확인 가능한 후보 프로필이 없습니다.",
    candidate_records_not_identifiable: "메일 본문에서 후보 수를 확정할 수 없습니다.",
    requirements_evidence_missing: "필수요건 근거가 메일에 없습니다.",
    why_fit_evidence_missing: "적합 근거가 메일에 없습니다.",
    contact_opinion_evidence_missing: "컨택 의견 근거가 메일에 없습니다.",
    better_position_evidence_missing: "더 적합한 포지션을 판단할 근거가 없습니다.",
    reverse_match_contract_evidence_missing: "역매칭에 필요한 근거가 없습니다.",
    required_sources_not_checked: "필요한 채용사이트를 아직 확인하지 않았습니다.",
    ai_search_load_failed: "AI Search 자료를 불러오지 못했습니다.",
    batch_detail_failed: "검색 상세를 불러오지 못했습니다.",
  };

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
    if (typeof value === "number") return value.toLocaleString("ko-KR");
    if (known(value)) return String(value);
    return reason ? `미확인 · ${reasonLabel(reason)}` : "미확인";
  }

  function reasonLabel(reason) {
    const normalized = typeof reason === "string" ? reason.replace(/^NOT_RUN:/, "") : reason;
    return REASON_LABELS[normalized] || "확인할 근거가 없습니다.";
  }

  function statusLabel(status) {
    if (status === "PASS") return "확인 완료";
    if (status === "FAIL") return "오류";
    return "확인 필요";
  }

  function contactRecommendationLabel(value) {
    if (value === "RECOMMEND") return "연락 추천";
    if (value === "DO_NOT_CONTACT") return "연락 비추천";
    return statusLabel(value);
  }

  function statusBadge(status) {
    const value = status || "NOT_RUN";
    return element("span", `status-badge status-${value.toLowerCase()}`, statusLabel(value));
  }

  function formatDate(value) {
    if (!known(value)) return "미확인";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return String(value);
    return new Intl.DateTimeFormat("ko-KR", {
      year: "numeric", month: "2-digit", day: "2-digit",
      hour: "2-digit", minute: "2-digit", hour12: false,
    }).format(date);
  }

  function shortDate(value) {
    if (!known(value)) return "날짜 미확인";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return "날짜 미확인";
    return new Intl.DateTimeFormat("ko-KR", { month: "long", day: "numeric" }).format(date);
  }

  function entityLabel(value, label) {
    if (known(value) && !value.startsWith("NOT_RUN:")) return value;
    return `${label} 미확인 (메일 제목에서 구분 못함)`;
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
    byId("cadence").textContent = payload.cadence === "DAILY" ? "매일" : payload.cadence;
    byId("evidence-status").replaceChildren(statusBadge(payload.status));
    byId("batch-count").textContent = hasEvidence
      ? payload.batches.length.toLocaleString("ko-KR")
      : "확인하지 않음";
    byId("candidate-count").textContent = hasEvidence ? valueOrNotRun(candidates) : "확인하지 않음";
    byId("strong-count").textContent = hasEvidence ? valueOrNotRun(strong) : "확인하지 않음";
    byId("fu-count").textContent = hasEvidence ? valueOrNotRun(fu) : "확인하지 않음";
  }

  function accountCell(batch) {
    const cell = element("td");
    cell.append(
      element("strong", "", entityLabel(batch.company, "고객사")),
      element("small", "", entityLabel(batch.position, "포지션")),
    );
    return cell;
  }

  function batchCell(batch) {
    const cell = element("td");
    const messageCount = batch.batch_grouping.message_count;
    cell.append(
      element("strong", "", batch.actor_label),
      element("small", "batch-code", `${shortDate(batch.executed_at)} · Gmail ${messageCount}건`),
    );
    return cell;
  }

  function numberCell(value, detail) {
    const cell = element("td", "number-cell", valueOrNotRun(value));
    if (detail) cell.append(element("small", "", reasonLabel(detail)));
    return cell;
  }

  function periodLabel(period) {
    return period.status === "PASS"
      ? `${period.start} ~ ${period.end}`
      : `미확인 · ${reasonLabel(period.reason)}`;
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
      row.setAttribute(
        "aria-label",
        `${batch.actor_label} ${entityLabel(batch.company, "고객사")} ${entityLabel(batch.position, "포지션")} 상세 열기`,
      );
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
      return `미확인 · ${reasonLabel(candidate.better_position_reason)}`;
    }
    if (!candidate.better_position_exists) {
      return `없음 · ${reasonLabel(candidate.better_position_reason)}`;
    }
    return `있음 · ${candidate.better_position} · ${reasonLabel(candidate.better_position_reason)}`;
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
      : `미확인 · ${reasonLabel(candidate.score_reason)}`;
    heading.append(title, element("strong", "candidate-score", score));
    const facts = element("dl", "candidate-facts");
    facts.append(
      detailItem("학력", candidate.education),
      detailItem("전체 경력", candidate.experience),
      detailItem("핵심 경력", candidate.key_experience),
      detailItem(
        "컨택 상태",
        `${statusLabel(candidate.contact_status)} · ${contactRecommendationLabel(candidate.contact_recommendation)}`,
      ),
      detailItem("컨택 출처", candidate.contact_source),
      detailItem("컨택 확인시각", known(candidate.contact_checked_at)
        ? formatDate(candidate.contact_checked_at) : null),
    );
    const contact = element("div", "candidate-copy");
    contact.append(
      element("h4", "", "컨택 의견 근거"),
      element("p", "", valueOrNotRun(candidate.contact_opinion_evidence, "contact_opinion_evidence_missing")),
      element("p", "evidence-meta", `연락 시각 ${valueOrNotRun(candidate.contacted_at)} · 확인 자료 ${valueOrNotRun(candidate.contact_reference)}`),
    );
    const better = element("div", "candidate-copy reverse-match");
    better.append(
      element("h4", "", "더 적합한 포지션 존재 여부"),
      element("p", "", betterPositionLabel(candidate)),
      element("p", "evidence-meta", `기존 역매칭: ${reasonLabel(candidate.reverse_match_reason)}`),
    );
    article.append(
      heading,
      facts,
      evidenceList(
        "필수요건별 근거",
        candidate.requirements_evidence,
        `미확인 · ${reasonLabel("requirements_evidence_missing")}`,
      ),
      evidenceList(
        "적합 근거",
        candidate.why_fit,
        `미확인 · ${reasonLabel("why_fit_evidence_missing")}`,
      ),
      contact,
      better,
    );
    return article;
  }

  function renderChecks(checks) {
    const root = byId("verification-checks");
    root.replaceChildren();
    if (!checks.length) {
      root.append(element("p", "empty-copy", reasonLabel("required_sources_not_checked")));
      return;
    }
    checks.forEach((check) => {
      const row = element("div", "verification-row");
      row.append(element("strong", "", check.source), statusBadge(check.status));
      row.append(
        element("span", "", check.checked_at ? formatDate(check.checked_at) : reasonLabel(check.reason)),
      );
      root.append(row);
    });
  }

  function showError(reason) {
    byId("ai-search").setAttribute("aria-busy", "false");
    byId("evidence-status").replaceChildren(statusBadge("FAIL"));
    byId("batch-count").textContent = "확인하지 않음";
    byId("candidate-count").textContent = "확인하지 않음";
    byId("strong-count").textContent = "확인하지 않음";
    byId("fu-count").textContent = "확인하지 않음";
    byId("empty-state").hidden = true;
    byId("error-state").hidden = false;
    byId("error-reason").textContent = reasonLabel(reason);
    const state = byId("load-state");
    state.dataset.status = "FAIL";
    state.textContent = `AI Search 증빙 미집계 · ${reasonLabel(reason)}`;
  }

  async function openDetail(batchId) {
    try {
      const response = await fetch(`/api/ai-search/${encodeURIComponent(batchId)}`, {
        cache: "no-store", headers: { Accept: "application/json" },
      });
      if (!response.ok) throw new Error("batch_detail_failed");
      const batch = await response.json();
      byId("dialog-batch").textContent = `${batch.actor_label} · Gmail ${batch.batch_grouping.message_count}건`;
      byId("dialog-title").textContent = `${entityLabel(batch.company, "고객사")} · ${entityLabel(batch.position, "포지션")}`;
      const counts = batch.candidate_counts;
      const summary = byId("dialog-summary");
      summary.replaceChildren(
        detailItem("실행 주체", batch.actor_label),
        detailItem("실행 일시", formatDate(batch.executed_at)),
        detailItem("검색 기간", periodLabel(batch.search_period)),
        detailItem(
          "메일 표기 → 확인 가능",
          `${valueOrNotRun(counts.raw, batch.candidate_counts_reason)} → ${counts.parsed}`,
        ),
        detailItem(
          "중복 / 확인 불가 / 제외",
          `${counts.duplicate} / ${valueOrNotRun(counts.unparsed, batch.candidate_counts_reason)} / ${counts.excluded}`,
        ),
        detailItem("실제 후속 연락", valueOrNotRun(batch.actual_fu, batch.actual_fu_reason)),
      );
      const candidates = byId("candidate-details");
      candidates.replaceChildren();
      if (batch.candidates.length) {
        candidates.append(...batch.candidates.map(renderCandidate));
      } else {
        candidates.append(element("p", "empty-copy", "메일에서 확인 가능한 후보 프로필이 없습니다."));
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
      : "확인하지 않음";
    const items = [
      ["자료 출처", "Gmail AI Search"],
      ["확인한 메일", `${gmailMessageCount}건`],
      ["Gmail 상태", statusLabel(gmailStatus)],
      ["전체 페이지 확인", gmail.pagination_exhausted === true ? "완료" : "확인하지 않음"],
      ["원격 DB 저장", payload.external_effects.database_writes === "DISABLED" ? "없음" : "확인 필요"],
      ["외부 발송", payload.external_effects.outreach_sends === "DISABLED" ? "없음" : "확인 필요"],
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
        : `확인 필요 · ${reasonLabel(payload.reason)}`;
    } catch (_error) {
      showError("ai_search_load_failed");
    }
  }

  loadAiSearch();
}());
