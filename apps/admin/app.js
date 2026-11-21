(function () {
  "use strict";

  const byId = (id) => document.getElementById(id);

  function element(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  }

  const REASON_LABELS = {
    retention_policy_missing: "추천·포지션 메일 데이터는 아직 연결하지 않았습니다.",
    identity_link_contract_missing: "채널과 검색을 넘나드는 동일인 확인은 아직 하지 않았습니다.",
    gmail_collection_incomplete: "Gmail 전체 페이지를 끝까지 확인하지 못했습니다.",
  };

  function latestCollectedWeek(dashboard) {
    const collected = dashboard.weeks.filter((week) => week.snapshot);
    const currentWeek = collected[collected.length - 1];
    return currentWeek || dashboard.weeks.at(-1);
  }

  function reasonLabel(reason) {
    return REASON_LABELS[reason] || "아직 확인하지 않았습니다.";
  }

  function statusLabel(status) {
    if (status === "PASS") return "확인 완료";
    if (status === "FAIL") return "오류";
    return "확인하지 않음";
  }

  function renderWindow(currentWeek) {
    byId("window-range").textContent = `${currentWeek.event_start_kst.slice(5, 10)} — ${currentWeek.event_end_inclusive_date_kst.slice(5, 10)}`;
    byId("week-label").textContent = currentWeek.meeting_iso_week;
  }

  function addAuditItem(list, label, value) {
    const wrapper = element("div");
    wrapper.append(element("dt", "", label), element("dd", "", value));
    list.append(wrapper);
  }

  function displayCount(value) {
    return Number.isInteger(value) ? `${value.toLocaleString("ko-KR")}건` : "확인하지 않음";
  }

  function renderAudit(dashboard) {
    const list = byId("audit-items");
    const source = dashboard.source_summary;
    list.replaceChildren();
    addAuditItem(list, "자료 출처", "Gmail AI Search");
    addAuditItem(list, "확인한 메일", displayCount(source.message_count));
    addAuditItem(list, "집계 대상", displayCount(source.included_message_count));
    addAuditItem(list, "제외한 테스트 메일", displayCount(source.excluded_message_count));
    addAuditItem(
      list,
      "전체 페이지 확인",
      source.pagination_exhausted ? "완료" : "확인하지 않음",
    );
  }

  function heatmapLabel(week) {
    if (week.status === "PASS") return `${week.meeting_iso_week}, Gmail 확인 완료`;
    return `${week.meeting_iso_week}, ${reasonLabel(week.reason)}`;
  }

  function selectWeek(dashboard, week, buttons) {
    buttons.forEach((button) => {
      const selected = button.dataset.week === week.meeting_iso_week;
      button.setAttribute("aria-pressed", String(selected));
    });
    renderWindow(week);
    byId("heatmap-detail").textContent = heatmapLabel(week);
    if (!week.snapshot) {
      byId("metric-groups").replaceChildren(
        element("p", "empty-copy", reasonLabel(week.reason)),
      );
      return;
    }
    renderMetrics(dashboard, week.snapshot);
  }

  function renderHeatmap(dashboard, selectedWeek) {
    const list = byId("heatmap");
    list.replaceChildren();
    const buttons = [];
    dashboard.weeks.forEach((week) => {
      const item = element("li");
      const button = element("button", "", week.meeting_iso_week.replace(/^\d{4}-/, ""));
      button.type = "button";
      button.dataset.status = week.status;
      button.dataset.week = week.meeting_iso_week;
      button.setAttribute("aria-label", heatmapLabel(week));
      button.setAttribute("aria-pressed", "false");
      button.title = heatmapLabel(week);
      button.addEventListener("click", () => {
        selectWeek(dashboard, week, buttons);
      });
      item.append(button);
      list.append(item);
      buttons.push(button);
    });
    selectWeek(dashboard, selectedWeek, buttons);
  }

  function renderMetricCard(metadata, result) {
    const card = element("article", "metric-card");
    card.dataset.status = result.status;
    card.dataset.metricId = metadata.id;
    const heading = element("div");
    heading.append(
      element("h4", "", metadata.display_label),
      element("p", "metric-description", metadata.description),
    );
    const value = result.value === null ? "확인하지 않음" : result.value.toLocaleString("ko-KR");
    const valueNode = element("p", "metric-value", value);
    if (result.value !== null) valueNode.append(element("small", "", ` ${metadata.unit}`));
    const footer = element("div");
    footer.append(
      element("p", "metric-status", statusLabel(result.status)),
      element(
        "p",
        "metric-meta",
        result.reason
          ? reasonLabel(result.reason)
          : `Gmail에서 확인한 자료 ${result.source_row_count.toLocaleString("ko-KR")}건`,
      ),
    );
    card.append(heading, valueNode, footer);
    return card;
  }

  function renderMetrics(dashboard, snapshot) {
    const root = byId("metric-groups");
    const metadataByGroup = new Map();
    dashboard.metric_catalog.forEach((metric) => {
      if (metadataByGroup.has(metric.group)) {
        metadataByGroup.get(metric.group).push(metric);
      } else {
        metadataByGroup.set(metric.group, [metric]);
      }
    });
    root.replaceChildren();
    dashboard.metric_groups.forEach((group) => {
      const section = element("section", "metric-group");
      section.setAttribute("aria-labelledby", `group-${group.id}`);
      const heading = element("div", "metric-group-heading");
      const title = element("h2", "", group.display_label);
      title.id = `group-${group.id}`;
      heading.append(title, element("p", "", group.description));
      const grid = element("div", "metric-grid");
      if (metadataByGroup.has(group.id)) {
        metadataByGroup.get(group.id).forEach((metadata) => {
          const result = snapshot.metrics[metadata.id];
          if (!result) throw new Error("metric_result_missing");
          grid.append(renderMetricCard(metadata, result));
        });
      }
      section.append(heading, grid);
      root.append(section);
    });
  }

  async function loadDashboard() {
    const state = byId("load-state");
    try {
      const response = await fetch("/api/dashboard", { cache: "no-store", headers: { Accept: "application/json" } });
      if (!response.ok) throw new Error("dashboard_request_failed");
      const dashboard = await response.json();
      const currentWeek = latestCollectedWeek(dashboard);
      renderAudit(dashboard);
      renderHeatmap(dashboard, currentWeek);
      byId("dashboard").setAttribute("aria-busy", "false");
      document.body.dataset.ready = "true";
      state.dataset.status = dashboard.source_summary.status;
      state.textContent = dashboard.source_summary.status === "PASS"
        ? "Gmail에서 확인한 주간 데이터를 불러왔습니다."
        : "Gmail 자료를 아직 확인하지 못했습니다.";
    } catch (_error) {
      byId("dashboard").setAttribute("aria-busy", "false");
      state.dataset.status = "FAIL";
      state.textContent = "대시보드 자료를 불러오지 못했습니다.";
    }
  }

  loadDashboard();
}());
