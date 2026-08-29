const POLL_INTERVAL_MS = 500;
const OUTCOMES = new Set(["passed", "failed", "running", "skipped", "pending"]);

const elements = {
  activeSection: document.querySelector("#active-section"),
  activeTest: document.querySelector("#active-test"),
  connection: document.querySelector("#connection"),
  inputPanel: document.querySelector("#input-panel"),
  progressBar: document.querySelector("#progress-bar"),
  summary: document.querySelector("#summary"),
  testListCount: document.querySelector("#test-list-count"),
  tests: document.querySelector("#tests"),
};

let renderedActiveTest = null;
let renderedInputId = null;
let renderedTestList = null;
const charts = new Map();

function escapeHtml(value) {
  const entities = {
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    "'": "&#39;",
    '"': "&quot;",
  };
  return String(value ?? "").replace(/[&<>'"]/g, (character) => entities[character]);
}

function statusName(outcome) {
  return OUTCOMES.has(outcome) ? outcome : "pending";
}

function formatDuration(seconds) {
  if (seconds < 1) return `${Math.round(seconds * 1000)} ms`;
  return `${seconds.toFixed(2)} s`;
}

function formatTime(timestamp) {
  const date = new Date(timestamp);
  return Number.isNaN(date.valueOf())
    ? timestamp
    : date.toLocaleTimeString([], { hour12: false });
}

function countOutcomes(tests) {
  return tests.reduce((counts, test) => {
    counts[test.outcome] = (counts[test.outcome] || 0) + 1;
    return counts;
  }, {});
}

function renderSummary(tests) {
  const outcomes = countOutcomes(tests);
  const completed =
    (outcomes.passed || 0) + (outcomes.failed || 0) + (outcomes.skipped || 0);
  const progress = tests.length ? (completed / tests.length) * 100 : 0;
  const items = [
    [completed, "Complete", ""],
    [outcomes.passed || 0, "Passed", "passed"],
    [outcomes.failed || 0, "Failed", "failed"],
    [tests.length, "Total", ""],
  ];

  elements.summary.innerHTML = items
    .map(
      ([value, label, className]) => `
        <div class="summary-item ${className}">
          <strong>${value}</strong><span>${label}</span>
        </div>`,
    )
    .join("");
  elements.progressBar.style.width = `${progress}%`;
}

function renderBadge(outcome) {
  const status = statusName(outcome);
  return `<span class="badge badge-${status}">${escapeHtml(status)}</span>`;
}

function renderLogRows(logs, { live = false } = {}) {
  if (!logs.length) {
    const message = live ? "Waiting for log output…" : "No logs captured for this test.";
    return `<li class="empty-log">${message}</li>`;
  }

  return logs
    .map(
      (log) => `<li class="log-row">
        <span class="log-time">${escapeHtml(formatTime(log.timestamp))}</span>
        <span class="log-level">${escapeHtml(log.level)}</span>
        <span class="log-source">${escapeHtml(log.logger)}</span>
        <span class="log-message">${escapeHtml(log.message)}</span>
      </li>`,
    )
    .join("");
}

function renderTestContext(test) {
  const requirements = test.requirements.length
    ? `<div class="requirement-list">${test.requirements
        .map((requirement) => `<span class="requirement">${escapeHtml(requirement)}</span>`)
        .join("")}</div>`
    : '<span class="empty-context">No requirements attached</span>';
  const steps = test.steps.length
    ? `<ol>${test.steps.map((step) => `<li>${escapeHtml(step)}</li>`).join("")}</ol>`
    : '<span class="empty-context">No operator steps defined</span>';

  return `<aside class="test-context">
    <div class="context-block"><h4>Requirements</h4>${requirements}</div>
    <div class="context-block"><h4>Procedure</h4>${steps}</div>
  </aside>`;
}

function measurementMarkup(measurements, scope) {
  if (!measurements.length) return "";
  return `<section class="measurements" aria-label="Measured data">
    <div class="measurement-heading"><span>Measured data</span><span>${measurements.length} ${measurements.length === 1 ? "series" : "series"}</span></div>
    <div class="measurement-grid">${measurements.map((series, index) => {
      const latest = series.points.at(-1);
      return `<article class="measurement-card">
        <div class="measurement-summary">
          <div><span class="measurement-name">${escapeHtml(series.name)}</span><small>${series.x_axis === "time" ? "Live time series" : "X / Y plot"}</small></div>
          <div class="measurement-latest"><strong>${latest ? escapeHtml(latest.y) : "—"}</strong><small>Latest</small></div>
        </div>
        <div class="chart-wrap"><canvas id="chart-${scope}-${index}" aria-label="${escapeHtml(series.name)} chart" role="img"></canvas></div>
      </article>`;
    }).join("")}</div>
  </section>`;
}

function renderCharts(measurements, scope) {
  if (typeof Chart === "undefined") return;
  measurements.forEach((series, index) => {
    const id = `chart-${scope}-${index}`;
    charts.get(id)?.destroy();
    const canvas = document.getElementById(id);
    if (!canvas) return;
    const isTime = series.x_axis === "time";
    const labels = isTime ? series.points.map((point) => formatTime(point.x)) : undefined;
    const data = isTime
      ? series.points.map((point) => point.y)
      : series.points.map((point) => ({ x: point.x, y: point.y }));
    charts.set(id, new Chart(canvas, {
      type: "line",
      data: { labels, datasets: [{ data, borderColor: "#2eb8ff", backgroundColor: "rgba(46, 184, 255, 0.12)", borderWidth: 2, pointRadius: data.length > 40 ? 0 : 2.5, pointHoverRadius: 4, fill: true, tension: 0.22 }] },
      options: {
        animation: false,
        maintainAspectRatio: false,
        parsing: isTime,
        normalized: true,
        plugins: { legend: { display: false }, tooltip: { displayColors: false } },
        scales: {
          x: { type: isTime ? "category" : "linear", grid: { color: "rgba(158, 176, 195, 0.08)" }, ticks: { color: "#6f8297", maxTicksLimit: 7 } },
          y: { grid: { color: "rgba(158, 176, 195, 0.08)" }, ticks: { color: "#6f8297", maxTicksLimit: 6 } },
        },
      },
    }));
  });
}

function renderActiveTest(test) {
  const serializedTest = JSON.stringify(test);
  if (serializedTest === renderedActiveTest) return;
  renderedActiveTest = serializedTest;

  if (!test) {
    elements.activeSection.hidden = true;
    elements.activeTest.innerHTML = "";
    return;
  }

  elements.activeSection.hidden = false;
  elements.activeTest.innerHTML = `<article class="active-card">
    <header class="active-card-header">
      <div>
        <h3>${escapeHtml(test.name)}</h3>
        ${test.description ? `<p class="description">${escapeHtml(test.description)}</p>` : ""}
        <div class="test-meta">
          <code>${escapeHtml(test.nodeid)}</code>
          <span>Elapsed ${formatDuration(test.duration)}</span>
        </div>
      </div>
      ${renderBadge(test.outcome)}
    </header>
    <div class="active-content">
      ${renderTestContext(test)}
      <section class="log-console" aria-label="Live logs">
        <div class="log-header"><span>Live output</span><span class="log-count">${test.logs.length}</span></div>
        <ul class="log-stream">${renderLogRows(test.logs, { live: true })}</ul>
      </section>
    </div>
    ${measurementMarkup(test.measurements, "active")}
  </article>`;

  const logStream = elements.activeTest.querySelector(".log-stream");
  logStream.scrollTop = logStream.scrollHeight;
  renderCharts(test.measurements, "active");
}

function renderFailure(test) {
  if (!test.failure_reason) return "";
  return `<div class="failure">
    <strong>Failure details</strong>
    <pre><code>${escapeHtml(test.failure_reason)}</code></pre>
  </div>`;
}

function renderTestRow(test) {
  const status = statusName(test.outcome);
  const icon = { passed: "✓", failed: "×", skipped: "–", pending: "·" }[status] || "·";
  const subtitle = test.description || test.nodeid;

  return `<details class="test-row test-row-${status}">
    <summary>
      <span class="status-icon ${status}">${icon}</span>
      <span class="test-row-title">
        <strong>${escapeHtml(test.name)}</strong>
        <small>${escapeHtml(subtitle)}</small>
      </span>
      <span class="duration">${formatDuration(test.duration)}</span>
      ${renderBadge(status)}
      <span class="chevron" aria-hidden="true">⌄</span>
    </summary>
    <div class="test-details">
      <div class="test-meta"><code>${escapeHtml(test.nodeid)}</code></div>
      <div class="log-header"><span>Captured logs</span><span class="log-count">${test.logs.length}</span></div>
      <ul class="log-stream">${renderLogRows(test.logs)}</ul>
      ${measurementMarkup(test.measurements, `test-${test.nodeid.replace(/[^a-z0-9]/gi, "-")}`)}
      ${renderFailure(test)}
    </div>
  </details>`;
}

function renderTestList(tests) {
  const serializedTests = JSON.stringify(tests);
  if (serializedTests === renderedTestList) return;
  renderedTestList = serializedTests;

  elements.testListCount.textContent = `${tests.length} ${tests.length === 1 ? "test" : "tests"}`;
  elements.tests.innerHTML = tests.length
    ? tests.map(renderTestRow).join("")
    : '<div class="empty-state">No other tests collected.</div>';
  tests.forEach((test) => renderCharts(test.measurements, `test-${test.nodeid.replace(/[^a-z0-9]/gi, "-")}`));
}

async function submitInput(requestId, value) {
  elements.inputPanel.setAttribute("aria-busy", "true");
  try {
    const response = await fetch(`/api/input/${requestId}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ value }),
    });
    if (!response.ok) throw new Error("The input request is no longer active.");
  } catch (error) {
    elements.inputPanel.removeAttribute("aria-busy");
    throw error;
  }
}

function bindInputControls(inputRequest) {
  elements.inputPanel.querySelectorAll("button[data-value]").forEach((button) => {
    button.addEventListener("click", () => {
      submitInput(inputRequest.id, button.dataset.value === "true");
    });
  });

  elements.inputPanel.querySelector("form")?.addEventListener("submit", (event) => {
    event.preventDefault();
    submitInput(inputRequest.id, new FormData(event.target).get("value"));
  });
}

function renderInput(inputRequest) {
  const requestId = inputRequest?.id || null;
  if (requestId === renderedInputId) return;
  renderedInputId = requestId;
  elements.inputPanel.removeAttribute("aria-busy");

  if (!inputRequest) {
    elements.inputPanel.hidden = true;
    elements.inputPanel.innerHTML = "";
    return;
  }

  const controls =
    inputRequest.input_type === "bool"
      ? `<div role="group">
          <button data-value="true">Yes, continue</button>
          <button class="secondary" data-value="false">No</button>
        </div>`
      : `<form>
          <input name="value" required autocomplete="off" placeholder="Enter response">
          <button type="submit">Submit</button>
        </form>`;

  elements.inputPanel.hidden = false;
  elements.inputPanel.innerHTML = `<div class="operator-card">
    <div class="operator-copy">
      <span class="operator-icon" aria-hidden="true">?</span>
      <div>
        <span class="eyebrow active-eyebrow">Action required</span>
        <h2>Operator input</h2>
        <p>${escapeHtml(inputRequest.prompt)}</p>
      </div>
    </div>
    <div class="operator-controls">${controls}</div>
  </div>`;
  bindInputControls(inputRequest);
  elements.inputPanel.querySelector("input")?.focus();
}

function setConnection(status, label) {
  elements.connection.className = `connection connection-${status}`;
  elements.connection.lastElementChild.textContent = label;
}

function renderState(state) {
  const activeTest = state.tests.find((test) => test.outcome === "running") || null;

  renderSummary(state.tests);
  renderInput(state.input_request);
  renderActiveTest(activeTest);
  renderTestList(state.tests);
  setConnection(state.run_complete ? "complete" : "live", state.run_complete ? "Complete" : "Live");
}

async function refresh() {
  try {
    const response = await fetch("/api/state", { cache: "no-store" });
    if (!response.ok) throw new Error(response.statusText);
    renderState(await response.json());
  } catch (error) {
    console.warn("Unable to refresh PyProdTest state", error);
    setConnection("error", "Reconnecting");
  }
  window.setTimeout(refresh, POLL_INTERVAL_MS);
}

refresh();
