// admin-app-runtime.mjs — 관리자 화면 JavaScript 를 **실제로 실행해** 판정한다 (AC10).
//
// 왜 필요한가:
//   humansearch/tests/test_admin_shadow_server.py:70 은 app.js 를 빈 문자열로 써 놓고
//   MIME 타입만 본다. 그래서 app.js 의 API 호출 경로를 바꾸거나 화면을 그리는 코드를
//   통째로 지워도 어떤 시험도 빨개지지 않는다. 파일이 "있다"는 것과 "동작한다"는 것은
//   다르다 (P16: 테스트는 소스 텍스트가 아니라 런타임 동작을 검사한다).
//
// 어떻게:
//   node 만으로 최소 DOM 과 fetch 를 세워 app.js 를 그 위에서 실행하고, 화면에 실제로
//   무엇이 그려졌는지를 읽어 단언한다. 새 런타임 의존성을 들이지 않는다 — node 는
//   개발기와 GitHub ubuntu-latest 러너 양쪽에 이미 있다.
//
// 사용법: node scripts/verify/admin-app-runtime.mjs [--app <app.js>] [--html <index.html>]
// 출력  : PASS:/FAIL: 줄과 마지막 줄 `CHECKED: <단언 수>`
// exit  : 0 = 전부 통과 | 1 = 단언 실패 | 2 = 실행 불가(파일 없음·평가 실패)
//
// 한계(주장하지 않는 것): 여기 쓰는 응답 픽스처는 합성이다. 서버가 실제로 그 모양을
//   돌려주는지는 humansearch 쪽 시험의 몫이며, 이 harness 가 그것까지 증명하지 않는다.
//   또한 최소 DOM 은 브라우저가 아니다 — CSS·레이아웃·실제 이벤트 루프는 재현하지 않는다.

import { readFileSync, existsSync } from "node:fs";
import { argv, exit } from "node:process";

function parseArgs(list) {
  const out = { app: "apps/admin/app.js", html: "apps/admin/index.html" };
  for (let i = 0; i < list.length; i += 1) {
    if (list[i] === "--app" && list[i + 1]) {
      out.app = list[i + 1];
      i += 1;
    } else if (list[i] === "--html" && list[i + 1]) {
      out.html = list[i + 1];
      i += 1;
    }
  }
  return out;
}

function bail(message) {
  console.log(`FAIL: ${message}`);
  console.log("CHECKED: 0");
  exit(2);
}

// ── 최소 DOM ────────────────────────────────────────────────────────────────
class Node {
  constructor(tag) {
    this.tag = tag;
    this.children = [];
    this.attributes = {};
    this.dataset = {};
    this.listeners = {};
    this.ownText = "";
    this.className = "";
    this.id = "";
    this.type = "";
    this.title = "";
  }

  get textContent() {
    if (this.children.length === 0) return this.ownText;
    let acc = this.ownText;
    for (const child of this.children) acc += child.textContent;
    return acc;
  }

  set textContent(value) {
    this.ownText = String(value);
    this.children = [];
  }

  append(...nodes) {
    for (const node of nodes) this.children.push(node);
  }

  // 브라우저에는 있는데 이 최소 DOM 에는 없던 메서드들. 없으면 **정상 코드가 빨개진다**
  // (2026-08-27 V1 F6: append 를 표준 appendChild 로 바꾸자 "버튼 0개" 로 오차단됐다).
  // 최소 DOM 이 브라우저보다 좁으면 그 차이가 그대로 거짓 판정이 된다.
  appendChild(node) {
    this.children.push(node);
    return node;
  }

  insertBefore(node, ref) {
    const at = this.children.indexOf(ref);
    if (at < 0) this.children.push(node);
    else this.children.splice(at, 0, node);
    return node;
  }

  removeChild(node) {
    const at = this.children.indexOf(node);
    if (at >= 0) this.children.splice(at, 1);
    return node;
  }

  get firstChild() {
    if (this.children.length === 0) return null;
    return this.children[0];
  }

  get childNodes() {
    return this.children;
  }

  replaceChildren(...nodes) {
    this.children = [];
    this.ownText = "";
    for (const node of nodes) this.children.push(node);
  }

  setAttribute(name, value) {
    this.attributes[name] = String(value);
  }

  getAttribute(name) {
    if (Object.prototype.hasOwnProperty.call(this.attributes, name)) return this.attributes[name];
    return null;
  }

  addEventListener(type, handler) {
    const existing = this.listeners[type];
    if (existing) {
      existing.push(handler);
      return;
    }
    this.listeners[type] = [handler];
  }

  fire(type) {
    const handlers = this.listeners[type];
    if (!handlers) return 0;
    for (const handler of handlers) handler();
    return handlers.length;
  }

  descendants() {
    const acc = [];
    for (const child of this.children) {
      acc.push(child);
      for (const nested of child.descendants()) acc.push(nested);
    }
    return acc;
  }
}

// index.html 의 id 를 그대로 쓴다. app.js 가 없는 id 를 참조하면 여기서 null 이 되어
// 실행이 터진다 — 화면 쪽에서 id 를 지우는 것도 이 harness 가 잡는다.
// 화면이 이 스크립트를 실제로 불러오는가. 여기를 보지 않으면 `<script src>` 를 지우거나
// 경로를 틀리게 하거나 type 을 바꿔도 시험이 초록이다 — 브라우저에서는 app.js 가 한 줄도
// 실행되지 않는데 말이다 (2026-08-27 V1 F6).
function scriptSourcesFromHtml(html) {
  const found = [];
  const re = /<script\b([^>]*)>/gi;
  let m = re.exec(html);
  while (m !== null) {
    const attrs = m[1];
    const src = attrs.match(/\ssrc="([^"]+)"/i);
    const type = attrs.match(/\stype="([^"]+)"/i);
    found.push({ src: src ? src[1] : null, type: type ? type[1].toLowerCase() : null });
    m = re.exec(html);
  }
  return found;
}

function idsFromHtml(html) {
  const found = [];
  const re = /\sid="([^"]+)"/g;
  let m = re.exec(html);
  while (m !== null) {
    found.push(m[1]);
    m = re.exec(html);
  }
  return found;
}

// ── 합성 응답 픽스처 ────────────────────────────────────────────────────────
const SNAPSHOT_SHA = "5f2c8b1ae94d77306cb1aa0f3e5d2c4b8a97613f0d2e4c6a8b0d2f4e6a8c0e2f";
const INPUT_SHA = "a1b2c3d4e5f60718293a4b5c6d7e8f90a1b2c3d4e5f60718293a4b5c6d7e8f90";

function makeWeek(index, collected) {
  const label = `2026-W${String(index + 20).padStart(2, "0")}`;
  const week = {
    meeting_iso_week: label,
    event_start_kst: "2026-08-10T00:00:00+09:00",
    event_end_inclusive_date_kst: "2026-08-16",
    status: collected ? "PASS" : "NOT_RUN",
    reason: collected ? "" : "not_collected",
    snapshot: null,
  };
  if (collected) {
    week.snapshot = {
      snapshot_sha256: SNAPSHOT_SHA,
      input_sha256: INPUT_SHA,
      metrics: {
        runs_started: {
          status: "PASS",
          value: 17,
          reason: "",
          source_collection: "runs",
          source_row_count: 17,
        },
        mails_sent: {
          status: "NOT_RUN",
          value: null,
          reason: "source_missing",
          source_collection: "mails",
          source_row_count: 0,
        },
      },
    };
  }
  return week;
}

function makeDashboard() {
  const weeks = [];
  for (let i = 0; i < 12; i += 1) weeks.push(makeWeek(i, i === 11));
  return {
    mode: "local-shadow",
    metric_contract_version: "weekly-v3",
    external_effects: { mail: "disabled", portal: "disabled" },
    metric_groups: [
      { id: "execution", display_label: "실행", description: "이번 주 실행 수" },
      { id: "outreach", display_label: "접촉", description: "이번 주 접촉 수" },
    ],
    metric_catalog: [
      {
        id: "runs_started",
        group: "execution",
        display_label: "시작된 실행",
        description: "이번 주 시작한 실행",
        unit: "건",
      },
      {
        id: "mails_sent",
        group: "outreach",
        display_label: "발송 메일",
        description: "이번 주 발송한 메일",
        unit: "통",
      },
    ],
    weeks,
  };
}

// ── 실행 ────────────────────────────────────────────────────────────────────
async function runApp(source, ids, responder) {
  const registry = new Map();
  for (const id of ids) registry.set(id, new Node("div"));
  const body = new Node("body");
  const calls = [];

  const documentStub = {
    body,
    createElement(tag) {
      return new Node(tag);
    },
    getElementById(id) {
      const node = registry.get(id);
      if (node) return node;
      return null;
    },
  };

  const fetchStub = (url, options) => {
    calls.push({ url, options });
    return responder(url, options);
  };

  // 브라우저에 없는 node 전역을 가린다. 가리지 않으면 `process.version` 같은 참조가
  // 여기서는 통과하고 브라우저에서만 ReferenceError 로 죽는다 (2026-08-27 V1 F6).
  const factory = new Function(
    "document",
    "fetch",
    "console",
    "process",
    "require",
    "module",
    "global",
    "Buffer",
    "__dirname",
    "__filename",
    `"use strict";\n${source}\n`,
  );
  factory(documentStub, fetchStub, console,
    undefined, undefined, undefined, undefined, undefined, undefined, undefined);

  // app.js 는 loadDashboard() 의 Promise 를 밖으로 넘기지 않는다. 화면이 결론을 낼
  // 때까지(load-state 에 판정이 찍힐 때까지) 마이크로태스크를 흘려보내며 기다린다.
  const state = registry.get("load-state");
  for (let i = 0; i < 200; i += 1) {
    if (state && state.dataset.status) break;
    await new Promise((resolve) => setTimeout(resolve, 1));
  }
  return { registry, body, calls };
}

async function main() {
  const args = parseArgs(argv.slice(2));
  if (!existsSync(args.app)) bail(`관리자 스크립트가 없다 — ${args.app} (fail-closed)`);
  if (!existsSync(args.html)) bail(`관리자 화면이 없다 — ${args.html} (fail-closed)`);

  const source = readFileSync(args.app, "utf8");
  const html = readFileSync(args.html, "utf8");
  const ids = idsFromHtml(html);
  if (ids.length === 0) bail(`화면에서 id 를 하나도 찾지 못했다 — ${args.html} (대상 0개는 합격이 아니다)`);

  let checked = 0;
  let failed = 0;
  const say = (ok, label, detail) => {
    checked += 1;
    if (ok) {
      console.log(`PASS: ${label} — ${detail}`);
      return;
    }
    console.log(`FAIL: ${label} — ${detail}`);
    failed = 1;
  };

  const dashboard = makeDashboard();
  let ok;
  try {
    ok = await runApp(source, ids, () =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve(dashboard),
      }),
    );
  } catch (error) {
    console.log(`FAIL: 관리자 스크립트를 실행하지 못했다 — ${error && error.message}`);
    console.log("CHECKED: 0");
    exit(2);
  }

  const { registry, body, calls } = ok;
  const get = (id) => registry.get(id);
  const text = (id) => {
    const node = get(id);
    if (!node) return "";
    return node.textContent;
  };

  // ⓪ 화면이 이 스크립트를 실제로 불러오는가
  const scripts = scriptSourcesFromHtml(html);
  const appName = args.app.split("/").pop();
  const loader = scripts.find((t) => t.src !== null && t.src.split("/").pop() === appName);
  say(loader !== undefined, "화면이 관리자 스크립트를 불러온다", `<script src> ${scripts.length}개 중 ${appName} 참조=${loader !== undefined}`);
  const loaderType = loader ? loader.type : null;
  const executableType = loaderType === null || loaderType === "module" || loaderType === "text/javascript";
  say(executableType, "그 스크립트가 실행되는 type 이다", `type=${String(loaderType)}`);

  // ① API 호출
  say(calls.length === 1, "API 를 정확히 한 번 부른다", `호출 ${calls.length}회`);
  const firstUrl = calls.length > 0 ? calls[0].url : "(호출 없음)";
  say(firstUrl === "/api/dashboard", "API 경로가 /api/dashboard 다", `실제: ${firstUrl}`);
  const firstOptions = calls.length > 0 ? calls[0].options : null;
  const cacheMode = firstOptions && firstOptions.cache;
  say(cacheMode === "no-store", "캐시를 쓰지 않고 부른다", `cache=${String(cacheMode)}`);

  // ② 집계 기간
  const current = dashboard.weeks[dashboard.weeks.length - 1];
  say(text("week-label") === current.meeting_iso_week, "회의 주차를 화면에 쓴다", `"${text("week-label")}"`);
  say(text("window-range").includes("—"), "실적 창을 기간 형태로 쓴다", `"${text("window-range")}"`);

  // ③ 감사 스트립
  const auditText = text("audit-items");
  say(auditText.includes(dashboard.mode), "자료 상태를 화면에 쓴다", `"${dashboard.mode}" 포함=${auditText.includes(dashboard.mode)}`);
  say(
    auditText.includes(SNAPSHOT_SHA.slice(0, 12)),
    "snapshot 지문을 화면에 쓴다",
    `앞 12자 포함=${auditText.includes(SNAPSHOT_SHA.slice(0, 12))}`,
  );

  // ④ 히트맵 — 주차 수와 클릭 반응
  const heatmap = get("heatmap");
  const buttons = heatmap ? heatmap.descendants().filter((n) => n.tag === "button") : [];
  say(buttons.length === dashboard.weeks.length, "12주 전부를 히트맵에 그린다", `버튼 ${buttons.length}개`);
  const detailBefore = text("heatmap-detail");
  if (buttons.length > 0) buttons[0].fire("click");
  const detailAfter = text("heatmap-detail");
  say(detailAfter !== detailBefore, "주차를 누르면 설명이 바뀐다", `"${detailBefore}" → "${detailAfter}"`);

  // ⑤ 지표 카드
  const groups = get("metric-groups");
  const sections = groups ? groups.descendants().filter((n) => n.tag === "section") : [];
  say(sections.length === dashboard.metric_groups.length, "지표 묶음을 전부 그린다", `section ${sections.length}개`);
  const cards = groups ? groups.descendants().filter((n) => n.dataset.metricId) : [];
  say(cards.length === dashboard.metric_catalog.length, "지표 카드를 전부 그린다", `카드 ${cards.length}개`);
  const groupsText = groups ? groups.textContent : "";
  say(groupsText.includes("17"), "집계된 값을 숫자로 보여준다", `"17" 포함=${groupsText.includes("17")}`);
  say(groupsText.includes("미집계"), "미집계는 숫자를 지어내지 않는다", `"미집계" 포함=${groupsText.includes("미집계")}`);
  say(groupsText.includes("source_missing"), "미집계 사유를 함께 보여준다", `사유 포함=${groupsText.includes("source_missing")}`);

  // ⑥ 판정 근거
  const provenanceText = text("provenance");
  say(provenanceText.includes(INPUT_SHA), "입력 지문을 화면에 쓴다", `포함=${provenanceText.includes(INPUT_SHA)}`);
  say(provenanceText.includes(SNAPSHOT_SHA), "snapshot 지문을 판정 근거에 쓴다", `포함=${provenanceText.includes(SNAPSHOT_SHA)}`);
  say(provenanceText.includes("mail=disabled"), "외부 효과 차단 상태를 쓴다", `포함=${provenanceText.includes("mail=disabled")}`);

  // ⑦ 완료 표시
  const dash = get("dashboard");
  say(dash !== null && dash.getAttribute("aria-busy") === "false", "다 그린 뒤 busy 를 내린다", `aria-busy=${dash && dash.getAttribute("aria-busy")}`);
  say(body.dataset.ready === "true", "완료 표식을 남긴다", `ready=${String(body.dataset.ready)}`);
  const loadState = get("load-state");
  say(loadState !== null && loadState.dataset.status === "PASS", "불러오기 판정을 PASS 로 남긴다", `status=${loadState && loadState.dataset.status}`);

  // ⑧ 실패 경로 — 조용히 성공으로 넘어가지 않는가 (P3)
  let failPath;
  try {
    failPath = await runApp(source, ids, () => Promise.resolve({ ok: false, json: () => Promise.resolve({}) }));
  } catch (error) {
    failPath = null;
  }
  if (failPath === null) {
    say(false, "응답이 실패하면 화면이 실패를 말한다", "실패 경로 실행 중 예외");
  } else {
    const failState = failPath.registry.get("load-state");
    const status = failState ? failState.dataset.status : "(없음)";
    say(status === "FAIL", "응답이 실패하면 화면이 실패를 말한다", `status=${status}`);
    const failText = failState ? failState.textContent : "";
    say(failText.includes("dashboard_load_failed"), "실패 사유를 화면에 남긴다", `"${failText}"`);
    say(failPath.body.dataset.ready !== "true", "실패했는데 완료 표식을 남기지 않는다", `ready=${String(failPath.body.dataset.ready)}`);
  }

  console.log(`CHECKED: ${checked}`);
  exit(failed);
}

main();
