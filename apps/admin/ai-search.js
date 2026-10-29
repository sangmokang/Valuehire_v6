(function () {
  "use strict";

  const PAGE_SIZE = 200;
  const REASONS = {
    gmail_collection_not_run: "Gmail AI Search 수집을 실행하지 않았습니다.",
    gmail_collection_incomplete: "Gmail AI Search 전체 페이지 확인이 끝나지 않았습니다.",
    gmail_sent_collection_not_run: "Gmail 보낸편지 수집을 실행하지 않았습니다.",
    gmail_sent_collection_incomplete: "Gmail 보낸편지 전체 페이지 확인이 끝나지 않았습니다.",
    score_contract_evidence_missing: "점수 계약의 네 항목 근거가 없습니다.",
    no_candidate_scores_verified: "점수 계약으로 확인된 점수가 없습니다.",
    no_candidate_linked_contact_in_week: "이 주차에 후보 프로필로 연결된 제안이 없습니다.",
    candidate_linked_but_batch_attribution_not_verified: "후보 연결은 확인했지만 어느 Batch의 후속 연락인지는 확인하지 못했습니다.",
    candidate_profile_not_in_sent_message: "제안 메일에 후보 프로필 URL이 없어 후보를 특정하지 않았습니다.",
    ai_search_week_not_found: "선택한 주차 자료가 없습니다.",
    weekly_index_load_failed: "주차 목록을 불러오지 못했습니다.",
    weekly_detail_load_failed: "선택한 주차 자료를 불러오지 못했습니다.",
  };

  let currentWeek = null;
  let candidateLimit = PAGE_SIZE;

  function byId(id) {
    return document.getElementById(id);
  }

  function element(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  }

  function reasonLabel(reason) {
    if (!reason) return "확인할 근거가 없습니다.";
    const normalized = String(reason).replace(/^NOT_RUN:/, "");
    return REASONS[normalized] || normalized.replaceAll("_", " ");
  }

  function formatDate(value) {
    const parsed = new Date(value);
    if (Number.isNaN(parsed.getTime())) return "미확인";
    return new Intl.DateTimeFormat("ko-KR", {
      year: "2-digit",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
      timeZone: "Asia/Seoul",
    }).format(parsed);
  }

  function entityLabel(value, kind) {
    if (typeof value === "string" && value && !value.startsWith("NOT_RUN:")) return value;
    return `${kind} 미확인`;
  }

  function batchLabel(batchId) {
    const suffix = String(batchId).split("-").at(-1) || batchId;
    return `배치 ${suffix.slice(-6)}`;
  }

  function actorLabel(actor) {
    if (actor === "AI") return "AI 발송";
    if (actor === "OWNER") return "사람 직접 발송";
    return "발송 주체 미확인";
  }

  function setText(id, text) {
    byId(id).textContent = text;
  }

  function setTab(tab) {
    const candidateSelected = tab === "candidate";
    byId("candidate-tab").setAttribute("aria-selected", String(candidateSelected));
    byId("contact-tab").setAttribute("aria-selected", String(!candidateSelected));
    byId("candidate-sheet").hidden = !candidateSelected;
    byId("contact-sheet").hidden = candidateSelected;
  }

  function showNotice(status, reason) {
    const notice = byId("notice-state");
    if (status === "PASS") {
      notice.hidden = true;
      return;
    }
    notice.hidden = false;
    setText("notice-title", "전체 수집이 끝나지 않아 숫자를 확정하지 않았습니다.");
    setText("notice-copy", reasonLabel(reason));
  }

  function renderWeekOptions(payload) {
    const select = byId("week-select");
    select.replaceChildren();
    [...payload.weeks].reverse().forEach((week) => {
      const option = element(
        "option",
        "",
        `${week.week_id} · ${week.period_label} · Batch ${week.batch_count}개`,
      );
      option.value = week.week_id;
      select.append(option);
    });
    select.disabled = payload.weeks.length === 0;
  }

  function renderSummary(week) {
    setText("selected-week", week.week_id);
    setText("week-period", `${week.period_label} · 일요일 00:00부터 토요일 23:59까지`);
    setText("summary-batches", `${week.batch_count.toLocaleString("ko-KR")}개`);
    setText("summary-candidates", `${week.unique_candidate_count.toLocaleString("ko-KR")}명`);
    setText("summary-rows", `${week.candidate_row_count.toLocaleString("ko-KR")}행`);
    setText("summary-ai-contact", `${week.contact_summary.ai_sent.toLocaleString("ko-KR")}건`);
    setText("summary-owner-contact", `${week.contact_summary.owner_sent.toLocaleString("ko-KR")}건`);
    setText(
      "summary-contact-link",
      `${week.contact_summary.linked.toLocaleString("ko-KR")}건 / ${week.contact_summary.unlinked.toLocaleString("ko-KR")}건`,
    );
  }

  function plainCell(value, className) {
    return element("td", className || "", value);
  }

  function evidenceValue(value, missingReason) {
    if (value !== null && value !== undefined && value !== "") return String(value);
    return `미확인 · ${reasonLabel(missingReason)}`;
  }

  function profileCell(row) {
    const cell = element("td", "profile-url-cell");
    const link = element("a", "profile-link", row.profile_url);
    link.href = row.profile_url;
    link.target = "_blank";
    link.rel = "noopener noreferrer";
    cell.append(link);
    return cell;
  }

  function experienceCell(row) {
    const cell = element("td");
    cell.append(element("strong", "", evidenceValue(row.experience, "experience_evidence_missing")));
    if (row.key_experience) cell.append(element("small", "", `핵심: ${row.key_experience}`));
    return cell;
  }

  function scoreCell(row) {
    if (row.score_status !== "PASS" || typeof row.score !== "number") {
      return plainCell(`미확인 · ${reasonLabel(row.score_reason)}`, "score-cell score-missing");
    }
    return plainCell(`${row.score}점`, "score-cell");
  }

  function scoreEvidenceCell(row) {
    const cell = element("td", "reason-cell");
    if (row.score_evidence.length) {
      const list = element("ul");
      row.score_evidence.forEach((reason) => list.append(element("li", "", reason)));
      cell.append(list);
    } else if (row.score_status === "PASS" && row.score_components) {
      const component = row.score_components;
      cell.textContent = `학력 ${component.education} · 직무 ${component.job_fit} · 고난도 ${component.difficult_work} · 기술 논리 ${component.job_description_logic}`;
    } else {
      cell.textContent = `미확인 · ${reasonLabel(row.score_reason)}`;
    }
    return cell;
  }

  function contactCell(row) {
    const cell = element("td", "weekly-contact-cell");
    const contact = row.weekly_contact;
    if (currentWeek.status !== "PASS") {
      cell.textContent = "미확인 · Gmail 전체 수집 미완료";
      return cell;
    }
    if (contact.status !== "PASS") {
      cell.append(
        element("strong", "", "후보 연결 제안 없음"),
        element("small", "", reasonLabel(contact.reason)),
      );
      return cell;
    }
    cell.append(
      element("strong", "", `AI ${contact.ai_sent_count}건 · 사람 ${contact.owner_sent_count}건`),
      element("small", "", formatDate(contact.latest_contacted_at)),
      element("small", "", reasonLabel(contact.reason)),
    );
    return cell;
  }

  function filteredCandidateRows() {
    if (!currentWeek) return [];
    const query = byId("candidate-filter").value.trim().toLocaleLowerCase("ko-KR");
    if (!query) return currentWeek.candidate_rows;
    return currentWeek.candidate_rows.filter((row) => [
      row.company,
      row.position,
      row.actor_label,
      row.candidate_name,
      row.profile_url,
      row.source_channel,
      row.education,
      row.experience,
      row.key_experience,
    ].filter(Boolean).join(" ").toLocaleLowerCase("ko-KR").includes(query));
  }

  function renderCandidateRows() {
    const rows = filteredCandidateRows();
    const shown = rows.slice(0, candidateLimit);
    const root = byId("candidate-rows");
    root.replaceChildren();
    shown.forEach((row) => {
      const tr = element("tr");
      const executed = element("td", "date-cell");
      executed.append(
        element("strong", "", formatDate(row.executed_at)),
        element("small", "batch-label", batchLabel(row.batch_id)),
      );
      const candidate = element("td", "candidate-name-cell");
      candidate.append(element("strong", "", row.candidate_name));
      tr.append(
        executed,
        plainCell(entityLabel(row.company, "고객사")),
        plainCell(entityLabel(row.position, "포지션")),
        plainCell(row.actor_label, "actor-cell"),
        candidate,
        profileCell(row),
        plainCell(row.source_channel),
        plainCell(evidenceValue(row.education, "education_evidence_missing"), row.education ? "" : "missing-cell"),
        experienceCell(row),
        scoreCell(row),
        scoreEvidenceCell(row),
        contactCell(row),
      );
      root.append(tr);
    });
    byId("candidate-empty").hidden = rows.length !== 0;
    const visible = Math.min(candidateLimit, rows.length);
    const total = currentWeek ? currentWeek.candidate_rows.length : 0;
    const queryActive = Boolean(byId("candidate-filter").value.trim());
    setText(
      "candidate-row-count",
      queryActive
        ? `검색 결과 ${rows.length.toLocaleString("ko-KR")}행 중 ${visible.toLocaleString("ko-KR")}행 표시 · 주차 전체 ${total.toLocaleString("ko-KR")}행`
        : `주차 전체 ${total.toLocaleString("ko-KR")}행 중 ${visible.toLocaleString("ko-KR")}행 표시`,
    );
    byId("candidate-more").hidden = visible >= rows.length;
  }

  function linkedCandidateCell(row) {
    const cell = element("td");
    if (!row.linked_candidates.length) {
      cell.textContent = "후보 미연결";
      return cell;
    }
    row.linked_candidates.forEach((candidate) => {
      if (candidate.profile_url) {
        const link = element("a", "profile-link", candidate.candidate_name);
        link.href = candidate.profile_url;
        link.target = "_blank";
        link.rel = "noopener noreferrer";
        cell.append(link);
      } else {
        cell.append(element("span", "", candidate.candidate_name));
      }
    });
    return cell;
  }

  function renderContactRows() {
    const root = byId("contact-rows");
    root.replaceChildren();
    currentWeek.contact_rows.forEach((row) => {
      const tr = element("tr");
      const state = row.link_status === "PASS"
        ? `연결 완료 · ${row.linked_candidates.length}명`
        : `미연결 · ${reasonLabel(row.link_reason)}`;
      const evidence = element("td", "evidence-id-cell");
      evidence.append(
        element("strong", "", `message ${row.message_id}`),
        element("small", "", `thread ${row.thread_id}`),
      );
      tr.append(
        plainCell(formatDate(row.contacted_at), "date-cell"),
        plainCell(actorLabel(row.actor), `contact-actor contact-${row.actor.toLowerCase()}`),
        plainCell(row.subject),
        linkedCandidateCell(row),
        plainCell(state, row.link_status === "PASS" ? "" : "missing-cell"),
        evidence,
      );
      root.append(tr);
    });
    byId("contact-empty").hidden = currentWeek.contact_rows.length !== 0;
  }

  function renderWeek(week) {
    currentWeek = week;
    candidateLimit = PAGE_SIZE;
    renderSummary(week);
    showNotice(week.status, week.reason);
    renderCandidateRows();
    renderContactRows();
    setText("collection-status", week.status === "PASS" ? "전체 페이지 확인 완료" : "확인 필요");
    setText(
      "load-state",
      week.status === "PASS"
        ? `${week.week_id} Gmail 전체 페이지를 확인했습니다.`
        : `${week.week_id} · ${reasonLabel(week.reason)}`,
    );
    byId("ai-search").setAttribute("aria-busy", "false");
    byId("error-state").hidden = true;
    document.body.dataset.ready = "true";
  }

  function renderExternalEffects(payload) {
    const effects = payload.external_effects || {};
    setText("external-send-state", effects.outreach_sends === "DISABLED" ? "0건 · 기능 비활성" : "확인 필요");
    setText("remote-write-state", effects.database_writes === "DISABLED" ? "0건 · 기능 비활성" : "확인 필요");
  }

  function showError(reason) {
    byId("ai-search").setAttribute("aria-busy", "false");
    byId("error-state").hidden = false;
    setText("error-reason", reasonLabel(reason));
    setText("collection-status", "불러오기 오류");
    setText("load-state", `오류 · ${reasonLabel(reason)}`);
  }

  async function loadWeek(weekId) {
    byId("ai-search").setAttribute("aria-busy", "true");
    try {
      const response = await fetch(`/api/ai-search/weekly/${encodeURIComponent(weekId)}`, {
        cache: "no-store",
        headers: { Accept: "application/json" },
      });
      if (!response.ok) throw new Error("weekly_detail_load_failed");
      renderWeek(await response.json());
    } catch (error) {
      showError(error.message || "weekly_detail_load_failed");
    }
  }

  async function loadIndex() {
    byId("error-state").hidden = true;
    byId("ai-search").setAttribute("aria-busy", "true");
    try {
      const response = await fetch("/api/ai-search/weekly", {
        cache: "no-store",
        headers: { Accept: "application/json" },
      });
      if (!response.ok) throw new Error("weekly_index_load_failed");
      const indexPayload = await response.json();
      renderExternalEffects(indexPayload);
      renderWeekOptions(indexPayload);
      if (!indexPayload.weeks.length) {
        currentWeek = {
          week_id: "자료 없음",
          period_label: "수집된 기간 없음",
          status: indexPayload.status,
          reason: indexPayload.reason,
          batch_count: 0,
          unique_candidate_count: 0,
          candidate_row_count: 0,
          candidate_rows: [],
          contact_rows: [],
          contact_summary: { ai_sent: 0, owner_sent: 0, linked: 0, unlinked: 0 },
        };
        renderWeek(currentWeek);
        return;
      }
      const latest = indexPayload.weeks.at(-1);
      byId("week-select").value = latest.week_id;
      await loadWeek(latest.week_id);
    } catch (error) {
      showError(error.message || "weekly_index_load_failed");
    }
  }

  byId("candidate-tab").addEventListener("click", () => setTab("candidate"));
  byId("contact-tab").addEventListener("click", () => setTab("contact"));
  byId("week-select").addEventListener("change", (event) => loadWeek(event.target.value));
  byId("candidate-filter").addEventListener("input", () => {
    candidateLimit = PAGE_SIZE;
    renderCandidateRows();
  });
  byId("candidate-more").addEventListener("click", () => {
    candidateLimit += PAGE_SIZE;
    renderCandidateRows();
  });
  byId("retry-load").addEventListener("click", loadIndex);

  loadIndex();
}());
