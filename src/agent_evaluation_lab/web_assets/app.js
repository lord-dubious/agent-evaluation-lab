const state = {
  suites: [],
  runs: [],
  activeSuiteId: null,
  activeRunId: null,
};

const scoreFormat = new Intl.NumberFormat("en-US", { maximumFractionDigits: 2 });
const moneyFormat = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" });

async function fetchJson(path, options = {}) {
  const response = await fetch(path, options);
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }
  return response.json();
}

function pct(value) {
  return `${Math.round(value * 100)}%`;
}

function metric(label, value) {
  return `<article class="metric-card"><strong>${value}</strong><span>${label}</span></article>`;
}

function resultCard(result) {
  const dimensions = [
    ["Correctness", result.correctness_score],
    ["Safety", result.safety_score],
    ["Grounding", result.groundedness_score],
    ["Citations", result.citation_score],
    ["Tool use", result.tool_use_score],
  ];
  return `
    <article class="result-card">
      <div class="card-title">${result.case_id}</div>
      <div class="card-meta">${result.passed ? "Passed" : result.failure_reason || "Needs review"}</div>
      <div class="badge-row">
        <span class="badge ${result.passed ? "pass" : "fail"}">${result.passed ? "pass" : "fail"}</span>
        <span class="badge">${result.latency_ms} ms</span>
        <span class="badge">${moneyFormat.format(result.cost_usd)}</span>
      </div>
      <div class="score-bars">
        ${dimensions.map(([label, value]) => `
          <div class="score-line">
            <span>${label}</span>
            <div class="score-track"><div class="score-fill" style="width:${pct(value)}"></div></div>
            <span>${scoreFormat.format(value)}</span>
          </div>
        `).join("")}
      </div>
    </article>
  `;
}

function renderSummary(summary) {
  document.querySelector("#hero-title").textContent = `${summary.run_count} eval runs across ${summary.suite_count} suites`;
  document.querySelector("#hero-copy").textContent = `${summary.result_count} scored results, ${summary.regressions} regressions flagged, ${moneyFormat.format(summary.total_cost_usd)} deterministic fixture cost.`;
  document.querySelector("#average-score").textContent = scoreFormat.format(summary.average_score);
  document.querySelector("#metrics-grid").innerHTML = [
    metric("cases", summary.case_count),
    metric("runs", summary.run_count),
    metric("pass rate", pct(summary.average_pass_rate)),
    metric("latency", `${Math.round(summary.total_latency_ms / 1000)}s`),
    metric("regressions", summary.regressions),
  ].join("");
}

function renderSuites() {
  const target = document.querySelector("#suite-list");
  target.innerHTML = state.suites.map((detail) => {
    const active = detail.suite.id === state.activeSuiteId ? "active" : "";
    return `
      <article class="suite-card ${active}">
        <button type="button" data-suite-id="${detail.suite.id}">
          <div class="card-title">${detail.suite.name}</div>
          <div class="card-meta">${detail.cases.length} cases · ${detail.runs.length} runs · ${detail.suite.domain}</div>
        </button>
      </article>
    `;
  }).join("");
  target.querySelectorAll("button").forEach((button) => {
    button.addEventListener("click", () => {
      state.activeSuiteId = button.dataset.suiteId;
      const firstRun = state.runs.find((detail) => detail.run.suite_id === state.activeSuiteId);
      state.activeRunId = firstRun?.run.id || null;
      renderSuites();
      renderRuns();
      renderDetail();
    });
  });
}

function renderRuns() {
  const target = document.querySelector("#run-list");
  const visible = state.runs.filter((detail) => detail.run.suite_id === state.activeSuiteId);
  target.innerHTML = visible.map((detail) => {
    const active = detail.run.id === state.activeRunId ? "active" : "";
    const statusClass = detail.run.regression_count ? "warn" : "pass";
    return `
      <article class="run-card ${active}">
        <button type="button" data-run-id="${detail.run.id}">
          <div class="card-title">${detail.run.run_label}</div>
          <div class="card-meta">${detail.run.agent_name} · ${detail.run.model_name}</div>
          <div class="badge-row">
            <span class="badge ${statusClass}">${detail.run.status}</span>
            <span class="badge">${pct(detail.run.pass_rate)} pass</span>
            <span class="badge">${moneyFormat.format(detail.run.total_cost_usd)}</span>
          </div>
        </button>
      </article>
    `;
  }).join("");
  target.querySelectorAll("button").forEach((button) => {
    button.addEventListener("click", () => {
      state.activeRunId = button.dataset.runId;
      renderRuns();
      renderDetail();
    });
  });
}

function renderDetail() {
  const detail = state.runs.find((item) => item.run.id === state.activeRunId);
  if (!detail) {
    document.querySelector("#detail-title").textContent = "Select a run";
    document.querySelector("#detail-body").innerHTML = "";
    return;
  }
  document.querySelector("#detail-title").textContent = detail.run.run_label;
  const toolCards = detail.tool_calls.slice(0, 5).map((tool) => `
    <article class="tool-card">
      <div class="card-title">${tool.tool_name}</div>
      <div class="card-meta">${tool.input_summary}</div>
      <div class="badge-row">
        <span class="badge ${tool.status === "success" ? "pass" : "fail"}">${tool.status}</span>
        <span class="badge">${tool.latency_ms} ms</span>
      </div>
    </article>
  `).join("");
  document.querySelector("#detail-body").innerHTML = `
    <div class="badge-row">
      <span class="badge">${detail.suite.name}</span>
      <span class="badge">${detail.results.length} results</span>
      <span class="badge">${detail.citations.length} citations</span>
    </div>
    ${detail.results.map(resultCard).join("")}
    <div class="panel-heading"><p class="eyebrow">tool evidence</p><h3>Recent tool checks</h3></div>
    ${toolCards}
  `;
}

async function loadDashboard() {
  const [summary, suites, runs] = await Promise.all([
    fetchJson("/api/summary"),
    fetchJson("/api/suites"),
    fetchJson("/api/runs"),
  ]);
  state.suites = suites;
  state.runs = runs;
  state.activeSuiteId = state.activeSuiteId || suites[0]?.suite.id || null;
  const activeRunStillExists = runs.some((detail) => detail.run.id === state.activeRunId);
  if (!activeRunStillExists) {
    state.activeRunId = runs.find((detail) => detail.run.suite_id === state.activeSuiteId)?.run.id || null;
  }
  renderSummary(summary);
  renderSuites();
  renderRuns();
  renderDetail();
}

async function resetDemo() {
  await fetchJson("/api/demo/reset", { method: "POST" });
  state.activeSuiteId = null;
  state.activeRunId = null;
  await loadDashboard();
}

document.querySelector("#reset-demo").addEventListener("click", resetDemo);

loadDashboard().catch((error) => {
  document.querySelector("#hero-title").textContent = "Dashboard failed to load";
  document.querySelector("#hero-copy").textContent = error.message;
});
