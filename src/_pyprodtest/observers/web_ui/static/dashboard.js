import { renderActiveTest, renderTestList } from "./tests.js";
import { countOutcomes, escapeHtml } from "./utils.js";

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

let renderedInputId = null;

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

export function setConnection(status, label) {
  elements.connection.className = `connection connection-${status}`;
  elements.connection.lastElementChild.textContent = label;
}

export function renderState(state) {
  const activeTest = state.tests.find((test) => test.outcome === "running") || null;

  renderSummary(state.tests);
  renderInput(state.input_request);
  renderActiveTest(elements.activeTest, elements.activeSection, activeTest);
  renderTestList(elements.tests, elements.testListCount, state.tests);
  setConnection(state.run_complete ? "complete" : "live", state.run_complete ? "Complete" : "Live");
}
