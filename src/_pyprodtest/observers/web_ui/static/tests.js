import { measurementMarkup, renderCharts } from "./charts.js";
import { chartScope, escapeHtml, formatDuration, formatTime, statusName } from "./utils.js";

let renderedActiveTest = null;
let renderedTestList = null;

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

export function renderActiveTest(container, section, test) {
  const serializedTest = JSON.stringify(test);
  if (serializedTest === renderedActiveTest) return;
  renderedActiveTest = serializedTest;

  if (!test) {
    section.hidden = true;
    container.innerHTML = "";
    return;
  }

  section.hidden = false;
  container.innerHTML = `<article class="active-card">
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

  const logStream = container.querySelector(".log-stream");
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
  const scope = chartScope(test);

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
      ${measurementMarkup(test.measurements, scope)}
      ${renderFailure(test)}
    </div>
  </details>`;
}

export function renderTestList(container, count, tests) {
  const serializedTests = JSON.stringify(tests);
  if (serializedTests === renderedTestList) return;
  renderedTestList = serializedTests;

  count.textContent = `${tests.length} ${tests.length === 1 ? "test" : "tests"}`;
  container.innerHTML = tests.length
    ? tests.map(renderTestRow).join("")
    : '<div class="empty-state">No other tests collected.</div>';
  tests.forEach((test) => renderCharts(test.measurements, chartScope(test)));
}
