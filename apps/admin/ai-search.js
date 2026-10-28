(function () {
  "use strict";

  const byId = (id) => document.getElementById(id);
  let candidateLedger = [];
  let candidateLimit = 200;
  let contactCollection = null;
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
    education_evidence_missing: "학력 정보가 메일에 없습니다.",
    experience_evidence_missing: "전체 경력 정보가 메일에 없습니다.",
    key_experience_evidence_missing: "핵심 경력 정보가 메일에 없습니다.",
    no_candidate_scores_verified: "v5 점수 계약으로 확인된 후보 점수가 없습니다.",
    some_candidate_scores_unverified: "일부 후보만 v5 점수 계약으로 확인됐습니다.",
    cross_channel_identity_not_verified: "채널이 다른 프로필의 동일인 여부는 확인하지 않았습니다.",
    better_position_evidence_missing: "더 적합한 포지션을 판단할 근거가 없습니다.",
    candidate_profile_not_in_sent_message: "제안 메일에 후보 프로필 URL이 없어 후보 원장에 연결하지 못했습니다.",
    gmail_sent_pagination_incomplete: "Gmail 보낸편지의 마지막 페이지까지 확인하지 못했습니다.",
    reverse_match_contract_evidence_missing: "역매칭에 필요한 근거가 없습니다.",
    required_sources_not_checked: "필요한 채용사이트를 아직 확인하지 않았습니다.",
    ai_search_load_failed: "AI Search 자료를 불러오지 못했습니다.",
    batch_detail_failed: "검색 상세를 불러오지 못했습니다.",
    candidate_detail_failed: "후보 상세를 불러오지 못했습니다.",
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

  function contactActorLabel(value) {
    if (value === "AI") return "AI 발송";
    if (value === "OWNER") return "직접 발송";
    return "발송 주체 미확인";
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

  function renderSummary(payload) {
    const hasEvidence = payload.batches.length > 0;
    const summary = payload.candidate_summary;
    const candidates = summary.unique_profiles;
    const assignments = summary.known_position_assignments + summary.unknown_position_assignments;
    const contacts = payload.contact_collection;
    byId("cadence").textContent = payload.cadence === "DAILY" ? "매일" : payload.cadence;
    byId("evidence-status").replaceChildren(statusBadge(payload.status));
    byId("batch-count").textContent = hasEvidence
      ? payload.batches.length.toLocaleString("ko-KR")
      : "확인하지 않음";
    byId("candidate-count").textContent = hasEvidence ? valueOrNotRun(candidates) : "확인하지 않음";
    byId("assignment-count").textContent = hasEvidence ? valueOrNotRun(assignments) : "확인하지 않음";
    byId("scored-count").textContent = hasEvidence
      ? `${summary.score_known_profiles.toLocaleString("ko-KR")} / ${candidates.toLocaleString("ko-KR")}명`
      : "확인하지 않음";
    byId("fu-count").textContent = contacts && contacts.status === "PASS"
      ? `${contacts.direct_contact_count.toLocaleString("ko-KR")}건 · 후보 연결 ${contacts.linked_contact_count}건\nAI ${contacts.ai_sent_count} · 직접 ${contacts.owner_sent_count} · 미확인 ${contacts.unknown_sent_count}`
      : "확인하지 않음";
  }

  function renderCoverage(payload) {
    const summary = payload.candidate_summary;
    const total = summary.unique_profiles;
    const coverage = summary.detail_coverage;
    const fields = [
      ["학력", coverage.education_profiles],
      ["전체 경력", coverage.experience_profiles],
      ["핵심 경력", coverage.key_experience_profiles],
      ["필수요건별 근거", coverage.requirements_evidence_profiles],
      ["적합 근거", coverage.why_fit_profiles],
      ["더 적합한 포지션", coverage.better_position_profiles],
      ["컨택 의견 근거", coverage.contact_opinion_profiles],
      ["후보 연결 컨택", coverage.linked_contact_profiles],
    ];
    const root = byId("coverage-grid");
    root.replaceChildren();
    fields.forEach(([label, count]) => {
      const item = element("div", count === 0 ? "coverage-item is-empty" : "coverage-item");
      item.append(
        element("dt", "", label),
        element("dd", "", `${count.toLocaleString("ko-KR")} / ${total.toLocaleString("ko-KR")}명`),
      );
      root.append(item);
    });
  }

  function candidateDisplayName(candidate) {
    if (/^https?:\/\//i.test(candidate.display_name)) {
      return `${candidate.source_channels.join(" · ")} 후보 프로필`;
    }
    return candidate.display_name;
  }

  function scoreHistoryLabel(candidate) {
    const knownScores = candidate.search_history.filter((item) => item.score_status === "PASS");
    if (!knownScores.length) return `미확인 · ${reasonLabel("no_candidate_scores_verified")}`;
    return knownScores
      .map((item) => `${entityLabel(item.company, "고객사")} ${entityLabel(item.position, "포지션")} ${item.score}점`)
      .join(" · ");
  }

  function searchHistoryLabel(history) {
    return history.map((item) => (
      `${entityLabel(item.company, "고객사")} · ${entityLabel(item.position, "포지션")} · ${item.actor_label} · ${shortDate(item.executed_at)}`
    )).join(" / ");
  }

  function contactHistoryLabel(history) {
    const confirmed = history.filter((item) => item.status === "PASS");
    if (!confirmed.length) return "확인된 직접 컨택 없음";
    const counts = { AI: 0, OWNER: 0, UNKNOWN: 0 };
    confirmed.forEach((item) => { counts[item.actor] += 1; });
    return `AI ${counts.AI}건 · 직접 ${counts.OWNER}건 · 주체 미확인 ${counts.UNKNOWN}건`;
  }

  function renderCandidateLedger(payload) {
    candidateLedger = payload.candidate_ledger;
    contactCollection = payload.contact_collection || null;
    candidateLimit = 200;
    renderCandidateLedgerRows();
  }

  function renderCandidateLedgerRows() {
    const root = byId("candidate-ledger-rows");
    const query = byId("candidate-filter").value.trim().toLocaleLowerCase("ko-KR");
    const filtered = query
      ? candidateLedger.filter((candidate) => {
        const text = [
          candidate.display_name,
          ...candidate.profile_urls,
          ...candidate.search_history.flatMap((item) => [item.company, item.position, item.actor_label]),
        ].join(" ").toLocaleLowerCase("ko-KR");
        return text.includes(query);
      })
      : candidateLedger;
    root.replaceChildren();
    filtered.slice(0, candidateLimit).forEach((candidate) => {
      const row = element("tr", "clickable-row");
      row.tabIndex = 0;
      row.setAttribute("role", "button");
      row.setAttribute("aria-label", `${candidateDisplayName(candidate)} 후보 상세 열기`);
      const profile = element("td");
      profile.append(
        element("strong", "", candidateDisplayName(candidate)),
        element("small", "", candidate.source_channels.join(" · ")),
        element("small", "profile-reference", candidate.profile_urls[0]),
      );
      row.append(
        profile,
        element("td", "", scoreHistoryLabel(candidate)),
        element("td", "", searchHistoryLabel(candidate.search_history)),
        element("td", "", contactHistoryLabel(candidate.contact_history)),
      );
      row.addEventListener("click", () => openCandidate(candidate.canonical_key));
      row.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          openCandidate(candidate.canonical_key);
        }
      });
      root.append(row);
    });
    const visible = Math.min(candidateLimit, filtered.length);
    byId("candidate-ledger-limit").textContent = query
      ? `검색 결과 ${filtered.length.toLocaleString("ko-KR")}명 중 ${visible.toLocaleString("ko-KR")}명을 표시합니다.`
      : `전체 ${candidateLedger.length.toLocaleString("ko-KR")}명 중 최근 검색된 ${visible.toLocaleString("ko-KR")}명을 표시합니다.`;
    byId("candidate-more").hidden = visible >= filtered.length;
  }

  function renderContactLedger(payload) {
    const collection = payload.contact_collection;
    const root = byId("contact-ledger-rows");
    root.replaceChildren();
    const events = collection && Array.isArray(collection.events) ? collection.events : [];
    byId("contact-empty-state").hidden = events.length !== 0;
    events.forEach((event) => {
      const row = element("tr");
      const actor = element("td");
      actor.append(
        element("strong", "", contactActorLabel(event.actor)),
        element("small", "", event.source),
      );
      const link = event.link_status === "PASS"
        ? `연결 완료 · ${event.canonical_keys.length}개 프로필`
        : `미연결 · ${reasonLabel(event.link_reason)}`;
      row.append(
        actor,
        element("td", "date-cell", formatDate(event.contacted_at)),
        element("td", "", event.subject),
        element("td", "", link),
      );
      root.append(row);
    });
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
      detailItem("컨택 발송 주체", candidate.contact_actor
        ? contactActorLabel(candidate.contact_actor) : null),
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
    const searches = evidenceList(
      "이 후보의 포지션·검색 묶음 이력",
      candidate.search_history.map((item) => (
        `${entityLabel(item.company, "고객사")} · ${entityLabel(item.position, "포지션")} · ${item.actor_label} · ${item.score_status === "PASS" ? `${item.score}점` : "점수 미확인"} · ${formatDate(item.executed_at)}`
      )),
      "확인된 검색 묶음이 없습니다.",
    );
    const contacts = evidenceList(
      "직접 컨택 이력",
      candidate.contact_history.map((item) => (
        `${contactActorLabel(item.actor)} · ${item.source} · ${valueOrNotRun(item.contacted_at)} · ${statusLabel(item.status)}`
      )),
      "확인된 직접 컨택 이력이 없습니다.",
    );
    article.append(
      heading,
      facts,
      searches,
      contacts,
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

  function profileBetterPositionLabel(profile) {
    if (profile.better_position_exists === null) {
      return `미확인 · ${reasonLabel(profile.better_position_reason)}`;
    }
    if (!profile.better_position_exists) return "없음";
    const reason = known(profile.better_position_reason)
      ? ` · ${profile.better_position_reason}` : "";
    return `있음 · ${valueOrNotRun(profile.better_position)}${reason}`;
  }

  function renderCandidateLedgerDetail(candidate) {
    const profile = candidate.profile_evidence;
    const article = element("article", "candidate-card candidate-ledger-detail");
    const facts = element("dl", "candidate-facts");
    facts.append(
      detailItem("학력", valueOrNotRun(profile.education, "education_evidence_missing")),
      detailItem("전체 경력", valueOrNotRun(profile.experience, "experience_evidence_missing")),
      detailItem("핵심 경력", valueOrNotRun(profile.key_experience, "key_experience_evidence_missing")),
      detailItem("확인된 점수", scoreHistoryLabel(candidate)),
      detailItem("후보 연결 컨택", contactHistoryLabel(candidate.contact_history)),
      detailItem("더 적합한 포지션", profileBetterPositionLabel(profile)),
    );
    const searches = evidenceList(
      "포지션·검색 묶음 전체 이력",
      candidate.search_history.map((item) => (
        `${entityLabel(item.company, "고객사")} · ${entityLabel(item.position, "포지션")} · ${item.actor_label} · ${item.score_status === "PASS" ? `${item.score}점` : "점수 미확인"} · ${formatDate(item.executed_at)} · ${item.batch_id}`
      )),
      "확인된 검색 묶음이 없습니다.",
    );
    const contacts = evidenceList(
      "이 후보와 연결된 직접 컨택",
      candidate.contact_history.map((item) => (
        `${contactActorLabel(item.actor)} · ${item.source} · ${formatDate(item.contacted_at)} · ${statusLabel(item.status)} · ${valueOrNotRun(item.evidence_reference)}`
      )),
      "이 후보의 프로필 정본키와 연결된 직접 컨택은 없습니다.",
    );
    const contactGap = element("div", "candidate-copy contact-gap");
    const unlinked = contactCollection?.unlinked_contact_count || 0;
    contactGap.append(
      element("h4", "", "Gmail 직접 제안과 후보 연결 상태"),
      element(
        "p",
        "",
        unlinked
          ? `Gmail에서 직접 제안 ${contactCollection.direct_contact_count}건을 확인했지만 ${unlinked}건은 후보 프로필 URL이 없어 특정 후보에게 연결하지 않았습니다.`
          : "후보에게 연결하지 못한 Gmail 직접 제안은 없습니다.",
      ),
    );
    article.append(
      facts,
      searches,
      contacts,
      evidenceList(
        "필수요건별 근거",
        profile.requirements_evidence,
        `미확인 · ${reasonLabel("requirements_evidence_missing")}`,
      ),
      evidenceList(
        "적합 근거",
        profile.why_fit,
        `미확인 · ${reasonLabel("why_fit_evidence_missing")}`,
      ),
      evidenceList(
        "컨택 의견 근거",
        profile.contact_opinion_evidence ? [profile.contact_opinion_evidence] : [],
        `미확인 · ${reasonLabel("contact_opinion_evidence_missing")}`,
      ),
      contactGap,
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

  function renderMailEvidence(batch) {
    const evidence = batch.actor_evidence;
    const root = byId("mail-evidence");
    root.replaceChildren();
    const items = evidence ? [
      ["메일 제목", evidence.subject],
      ["발신자", evidence.sender],
      ["Gmail message ID", evidence.message_id],
      ["Gmail thread ID", evidence.thread_id],
      ["수신시각", formatDate(evidence.received_at)],
      ["실행 주체", batch.actor_label],
    ] : [["실행 메일", "미확인"]];
    items.forEach(([label, value]) => root.append(detailItem(label, value)));
  }

  function showError(reason) {
    byId("ai-search").setAttribute("aria-busy", "false");
    byId("evidence-status").replaceChildren(statusBadge("FAIL"));
    byId("batch-count").textContent = "확인하지 않음";
    byId("candidate-count").textContent = "확인하지 않음";
    byId("assignment-count").textContent = "확인하지 않음";
    byId("scored-count").textContent = "확인하지 않음";
    byId("fu-count").textContent = "확인하지 않음";
    byId("empty-state").hidden = true;
    byId("error-state").hidden = false;
    byId("error-reason").textContent = reasonLabel(reason);
    const state = byId("load-state");
    state.dataset.status = "FAIL";
    state.textContent = `AI Search 증빙 미집계 · ${reasonLabel(reason)}`;
  }

  async function openCandidate(canonicalKey) {
    try {
      const response = await fetch(
        `/api/ai-search/candidates/${encodeURIComponent(canonicalKey)}`,
        { cache: "no-store", headers: { Accept: "application/json" } },
      );
      if (!response.ok) throw new Error("candidate_detail_failed");
      const candidate = await response.json();
      byId("candidate-dialog-title").textContent = candidateDisplayName(candidate);
      const scores = candidate.search_history.filter((item) => item.score_status === "PASS");
      const positions = new Set(candidate.search_history.map((item) => `${item.company}\u0000${item.position}`));
      byId("candidate-dialog-summary").replaceChildren(
        detailItem("검색된 포지션", `${positions.size.toLocaleString("ko-KR")}개`),
        detailItem("검색 묶음", `${candidate.search_history.length.toLocaleString("ko-KR")}개`),
        detailItem("확인된 점수", `${scores.length.toLocaleString("ko-KR")}개`),
        detailItem("후보 연결 컨택", `${candidate.contact_history.length.toLocaleString("ko-KR")}건`),
        detailItem("채널", candidate.source_channels.join(" · ")),
        detailItem("프로필", candidate.profile_urls[0]),
      );
      byId("candidate-dialog-body").replaceChildren(renderCandidateLedgerDetail(candidate));
      byId("candidate-dialog").showModal();
    } catch (_error) {
      showError("candidate_detail_failed");
    }
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
        detailItem("Batch ID", batch.batch_id),
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
      renderMailEvidence(batch);
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
    const countedBatches = payload.batches.filter(
      (batch) => batch.candidate_counts_status === "PASS",
    );
    const countTotals = countedBatches.reduce(
      (totals, batch) => {
        Object.keys(totals).forEach((key) => {
          totals[key] += batch.candidate_counts[key];
        });
        return totals;
      },
      { raw: 0, parsed: 0, duplicate: 0, unparsed: 0, excluded: 0 },
    );
    const items = [
      ["자료 출처", "Gmail AI Search"],
      ["확인한 메일", `${gmailMessageCount}건`],
      ["Gmail 상태", statusLabel(gmailStatus)],
      ["전체 페이지 확인", gmail.pagination_exhausted === true ? "완료" : "확인하지 않음"],
      ["보낸편지 확인", payload.contact_collection?.pagination_exhausted === true ? "완료" : "확인하지 않음"],
      ["후보 연결 / 미연결", payload.contact_collection?.status === "PASS"
        ? `${payload.contact_collection.linked_contact_count} / ${payload.contact_collection.unlinked_contact_count}`
        : "확인하지 않음"],
      ["후보 수가 확정된 검색", `${countedBatches.length} / ${payload.batches.length}개`],
      [
        "확정 검색 후보 수식",
        `${countTotals.raw.toLocaleString("ko-KR")} = 확인 ${countTotals.parsed.toLocaleString("ko-KR")} + 중복 ${countTotals.duplicate.toLocaleString("ko-KR")} + 확인 불가 ${countTotals.unparsed.toLocaleString("ko-KR")} + 제외 ${countTotals.excluded.toLocaleString("ko-KR")}`,
      ],
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
      renderCoverage(payload);
      renderCandidateLedger(payload);
      renderContactLedger(payload);
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

  byId("candidate-filter").addEventListener("input", () => {
    candidateLimit = 200;
    renderCandidateLedgerRows();
  });
  byId("candidate-more").addEventListener("click", () => {
    candidateLimit += 200;
    renderCandidateLedgerRows();
  });
  loadAiSearch();
}());
