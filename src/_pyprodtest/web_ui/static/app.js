const POLL_INTERVAL_MS = 500;

const elements = {
  connection: document.querySelector("#connection"),
  inputPanel: document.querySelector("#input-panel"),
  summary: document.querySelector("#summary"),
  tests: document.querySelector("#tests"),
};

let renderedInputId = null;
let renderedTests = null;

function escapeHtml(value) {
  const entities = {
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    "'": "&#39;",
    '"': "&quot;",
  };
  return String(value).replace(/[&<>'"]/g, (character) => entities[character]);
}

function countOutcomes(tests) {
  return tests.reduce((counts, test) => {
    counts[test.outcome] = (counts[test.outcome] || 0) + 1;
    return counts;
  }, {});
}

function renderSummary(tests) {
  const outcomes = countOutcomes(tests);
  const cards = [
    [tests.length, "Total"],
    [outcomes.passed || 0, "Passed"],
    [outcomes.failed || 0, "Failed"],
    [outcomes.running || 0, "Running"],
    [outcomes.pending || 0, "Pending"],
  ];

  elements.summary.innerHTML = cards
    .map(
      ([value, label]) =>
        `<article class="summary-card"><strong>${value}</strong><small>${label}</small></article>`,
    )
    .join("");
}

function renderLogs(test) {
  const entries = test.logs
    .map(
      (log) => `<li>
        <div class="log-meta">${escapeHtml(log.timestamp)} · ${escapeHtml(log.level)} · ${escapeHtml(log.logger)}</div>
        ${escapeHtml(log.message)}
      </li>`,
    )
    .join("");
  return entries || "<li>No logs captured.</li>";
}

function renderTest(test) {
  const description = test.description
    ? `<p>${escapeHtml(test.description)}</p>`
    : "";
  const steps = test.steps.length
    ? `<details><summary>Steps (${test.steps.length})</summary><ol>${test.steps.map((step) => `<li>${escapeHtml(step)}</li>`).join("")}</ol></details>`
    : "";
  const failure = test.failure_reason
    ? `<details open><summary>Failure details</summary><pre><code>${escapeHtml(test.failure_reason)}</code></pre></details>`
    : "";

  return `<article class="test-card">
    <header>
      <div><h2>${escapeHtml(test.name)}</h2>${description}</div>
      <span class="badge badge-${test.outcome}">${test.outcome}</span>
    </header>
    <div class="metadata">${escapeHtml(test.nodeid)} · ${test.duration.toFixed(3)}s</div>
    ${steps}
    <details ${test.outcome === "running" ? "open" : ""}>
      <summary>Logs (${test.logs.length})</summary>
      <ul class="log-list">${renderLogs(test)}</ul>
    </details>
    ${failure}
  </article>`;
}

function renderTests(tests) {
  const serializedTests = JSON.stringify(tests);
  if (serializedTests === renderedTests) return;

  renderedTests = serializedTests;
  renderSummary(tests);
  elements.tests.innerHTML = tests.length
    ? tests.map(renderTest).join("")
    : "<article>No tests collected.</article>";
}

async function submitInput(requestId, value) {
  const response = await fetch(`/api/input/${requestId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ value }),
  });
  if (!response.ok) throw new Error("The input request is no longer active.");
  elements.inputPanel.setAttribute("aria-busy", "true");
}

function bindInputControls(inputRequest) {
  elements.inputPanel.querySelectorAll("button[data-value]").forEach((button) => {
    button.addEventListener("click", () => {
      submitInput(inputRequest.id, button.dataset.value === "true");
    });
  });

  elements.inputPanel.querySelector("form")?.addEventListener("submit", (event) => {
    event.preventDefault();
    const value = new FormData(event.target).get("value");
    submitInput(inputRequest.id, value);
  });
}

function renderInput(inputRequest) {
  const requestId = inputRequest?.id || null;
  if (requestId === renderedInputId) return;
  renderedInputId = requestId;

  if (!inputRequest) {
    elements.inputPanel.hidden = true;
    elements.inputPanel.innerHTML = "";
    elements.inputPanel.removeAttribute("aria-busy");
    return;
  }

  const controls =
    inputRequest.input_type === "bool"
      ? `<div role="group">
          <button data-value="true">Yes</button>
          <button class="secondary" data-value="false">No</button>
        </div>`
      : `<form>
          <input name="value" required autocomplete="off">
          <button type="submit">Submit</button>
        </form>`;

  elements.inputPanel.hidden = false;
  elements.inputPanel.innerHTML = `<article class="input-card">
    <header><strong>Operator input required</strong></header>
    <p>${escapeHtml(inputRequest.prompt)}</p>
    ${controls}
  </article>`;
  bindInputControls(inputRequest);
  elements.inputPanel.querySelector("input")?.focus();
}

async function refresh() {
  try {
    const response = await fetch("/api/state", { cache: "no-store" });
    if (!response.ok) throw new Error(response.statusText);

    const state = await response.json();
    renderTests(state.tests);
    renderInput(state.input_request);
    elements.connection.textContent = state.run_complete ? "Complete" : "Live";
    if (!state.run_complete) scheduleRefresh();
  } catch (error) {
    console.warn("Unable to refresh PyProdTest state", error);
    elements.connection.textContent = "Reconnecting…";
    scheduleRefresh();
  }
}

function scheduleRefresh() {
  window.setTimeout(refresh, POLL_INTERVAL_MS);
}

refresh();
