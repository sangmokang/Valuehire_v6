(function () {
  "use strict";

  const byId = (id) => document.getElementById(id);

  function element(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  }

  function currentSnapshot(dashboard) {
    const currentWeek = dashboard.weeks[dashboard.weeks.length - 1];
    if (!currentWeek || !currentWeek.snapshot) throw new Error("current_snapshot_missing");
    return { currentWeek, snapshot: currentWeek.snapshot };
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

  function renderAudit(dashboard, snapshot) {
    const list = byId("audit-items");
    list.replaceChildren();
    addAuditItem(list, "자료 상태", dashboard.mode);
    addAuditItem(list, "metric 계약", dashboard.metric_contract_version);
    addAuditItem(list, "snapshot", snapshot.snapshot_sha256.slice(0, 12));
    addAuditItem(list, "외부 효과", "ALL DISABLED");
  }

  function heatmapLabel(week) {
    if (week.status === "PASS") return `${week.meeting_iso_week}, 수집됨`;
    return `${week.meeting_iso_week}, 미집계, ${week.reason}`;
  }

  function renderHeatmap(dashboard) {
    const list = byId("heatmap");
    const detail = byId("heatmap-detail");
    list.replaceChildren();
    dashboard.weeks.forEach((week) => {
      const item = element("li");
      const button = element("button", "", week.meeting_iso_week.replace(/^\d{4}-/, ""));
      button.type = "button";
      button.dataset.status = week.status;
      button.setAttribute("aria-label", heatmapLabel(week));
      button.title = heatmapLabel(week);
      button.addEventListener("click", () => {
        detail.textContent = heatmapLabel(week);
      });
      item.append(button);
      list.append(item);
    });
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
    const value = result.value === null ? "미집계" : String(result.value);
    const valueNode = element("p", "metric-value", value);
    if (result.value !== null) valueNode.append(element("small", "", ` ${metadata.unit}`));
    const footer = element("div");
    footer.append(
      element("p", "metric-status", result.status),
      element(
        "p",
        "metric-meta",
        result.reason || `${result.source_collection} · rows ${result.source_row_count}`,
      ),
    );
    card.append(heading, valueNode, footer);
    return card;
  }

  function renderMetrics(dashboard, snapshot) {
    const root = byId("metric-groups");
    const metadataByGroup = new Map();
    dashboard.metric_catalog.forEach((metric) => {
      const groupMetrics = metadataByGroup.get(metric.group) || [];
      groupMetrics.push(metric);
      metadataByGroup.set(metric.group, groupMetrics);
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
      (metadataByGroup.get(group.id) || []).forEach((metadata) => {
        const result = snapshot.metrics[metadata.id];
        if (!result) throw new Error("metric_result_missing");
        grid.append(renderMetricCard(metadata, result));
      });
      section.append(heading, grid);
      root.append(section);
    });
  }

  function addProvenance(list, label, value) {
    list.append(element("dt", "", label), element("dd", "", value));
  }

  function renderProvenance(dashboard, snapshot) {
    const list = byId("provenance");
    list.replaceChildren();
    addProvenance(list, "input sha256", snapshot.input_sha256);
    addProvenance(list, "snapshot sha256", snapshot.snapshot_sha256);
    addProvenance(list, "contract", dashboard.metric_contract_version);
    addProvenance(
      list,
      "external effects",
      Object.entries(dashboard.external_effects).map(([key, value]) => `${key}=${value}`).join(" · "),
    );
  }

  async function loadDashboard() {
    const state = byId("load-state");
    try {
      const response = await fetch("/api/dashboard", { cache: "no-store", headers: { Accept: "application/json" } });
      if (!response.ok) throw new Error("dashboard_request_failed");
      const dashboard = await response.json();
      const { currentWeek, snapshot } = currentSnapshot(dashboard);
      renderWindow(currentWeek);
      renderAudit(dashboard, snapshot);
      renderHeatmap(dashboard);
      renderMetrics(dashboard, snapshot);
      renderProvenance(dashboard, snapshot);
      byId("dashboard").setAttribute("aria-busy", "false");
      document.body.dataset.ready = "true";
      state.dataset.status = "PASS";
      state.textContent = "로컬 shadow snapshot을 불러왔습니다.";
    } catch (_error) {
      byId("dashboard").setAttribute("aria-busy", "false");
      state.dataset.status = "FAIL";
      state.textContent = "대시보드 미집계 · dashboard_load_failed";
    }
  }

  loadDashboard();
}());
