import {
  chartsKey,
  chartsLatestMeasurement,
  chartsRefresh,
  chartsRenderVisible,
  chartsSeriesDescription,
} from "./charts.js";

const POLL_INTERVAL_MS = 500;
const OUTCOMES = new Set(["passed", "failed", "running", "skipped", "pending"]);

function statusName(outcome) {
  return OUTCOMES.has(outcome) ? outcome : "pending";
}

function formatDuration(seconds = 0) {
  return seconds < 1 ? `${Math.round(seconds * 1000)} ms` : `${seconds.toFixed(2)} s`;
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

function logMessage(logs, live = false) {
  if (logs.length) return "";
  return live ? "Waiting for log output..." : "No logs captured for this test.";
}

function promptLines(prompt = "") {
  return String(prompt).split(/\r?\n/);
}

function runSummaryText(summary = {}) {
  const complete = summary.complete || 0;
  const total = summary.total || 0;
  const failed = summary.failed || 0;
  const passed = summary.passed || 0;
  return `${complete}/${total} complete | ${passed} passed | ${failed} failed`;
}

function statusIcon(outcome) {
  return { failed: "x", passed: "✓", pending: "·", running: "·", skipped: "-" }[
    statusName(outcome)
  ];
}

window.pyprodtestDashboard = function pyprodtestDashboard() {
  return {
    activeTimer: { nodeid: null, startedAtMs: null, nowMs: Date.now() },
    connectionLabel: "Connecting",
    connectionStatus: "waiting",
    currentRun: null,
    dutId: "Unknown DUT",
    history: [],
    inputRequest: null,
    inputValue: "",
    submittingInput: false,
    tests: [],

    get activeTest() {
      return this.tests.find((test) => test.outcome === "running") || null;
    },

    get completedCount() {
      const outcomes = countOutcomes(this.tests);
      return (outcomes.passed || 0) + (outcomes.failed || 0) + (outcomes.skipped || 0);
    },

    get progress() {
      return this.tests.length ? (this.completedCount / this.tests.length) * 100 : 0;
    },

    get summaryItems() {
      const outcomes = countOutcomes(this.tests);
      return [
        { className: "", label: "Complete", value: this.completedCount },
        { className: "passed", label: "Passed", value: outcomes.passed || 0 },
        { className: "failed", label: "Failed", value: outcomes.failed || 0 },
        { className: "", label: "Total", value: this.tests.length },
      ];
    },

    start() {
      window.setInterval(() => {
        this.activeTimer.nowMs = Date.now();
      }, 250);
      this.refresh();
    },

    async refresh() {
      try {
        const response = await fetch("/api/state", { cache: "no-store" });
        if (!response.ok) throw new Error(response.statusText);
        this.applyState(await response.json());
      } catch (error) {
        console.warn("Unable to refresh PyProdTest state", error);
        this.setConnection("error", "Reconnecting");
      } finally {
        window.setTimeout(() => this.refresh(), POLL_INTERVAL_MS);
      }
    },

    applyState(state) {
      const previousInputId = this.inputRequest?.id || null;
      const nextInputId = state.input_request?.id || null;

      this.tests = state.tests;
      this.currentRun = state.current_run || null;
      this.dutId = state.dut_id || "Unknown DUT";
      this.history = state.history || [];
      this.inputRequest = state.input_request;
      this.updateActiveTimer();
      this.setConnection(state.run_complete ? "complete" : "live", state.run_complete ? "Complete" : "Live");
      this.$nextTick(() => chartsRenderVisible(this.tests));

      if (previousInputId !== nextInputId) {
        this.inputValue = "";
        this.submittingInput = false;
        this.$nextTick(() => this.$refs.operatorInput?.focus());
      }
    },

    async submitInput(value) {
      if (!this.inputRequest || this.submittingInput) return;
      this.submittingInput = true;
      try {
        const response = await fetch(`/api/input/${this.inputRequest.id}`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ value }),
        });
        if (!response.ok) throw new Error("The input request is no longer active.");
      } catch (error) {
        this.submittingInput = false;
        console.warn("Unable to submit PyProdTest input", error);
      }
    },

    setConnection(status, label) {
      this.connectionStatus = status;
      this.connectionLabel = label;
    },

    updateActiveTimer() {
      const test = this.activeTest;
      if (!test) {
        this.activeTimer.nodeid = null;
        this.activeTimer.startedAtMs = null;
        return;
      }
      if (this.activeTimer.nodeid !== test.nodeid) {
        this.activeTimer.nodeid = test.nodeid;
        this.activeTimer.startedAtMs = Date.now();
      }
    },

    // Pytest only reports phase durations after each phase finishes, so a long
    // running test would otherwise look frozen in the live UI.
    liveDuration(test) {
      if (statusName(test.outcome) !== "running" || test.nodeid !== this.activeTimer.nodeid) {
        return test.duration;
      }
      return test.duration + (this.activeTimer.nowMs - this.activeTimer.startedAtMs) / 1000;
    },

    badgeClass(test) {
      return `badge badge-${statusName(test.outcome)}`;
    },

    contextList(items) {
      return Array.isArray(items) ? items : [];
    },

    formatDuration,
    formatTime,
    logMessage,
    promptLines,
    runSummaryText,

    statusIcon,
    statusName,

    chartsKey,
    chartsRefresh,
    chartsSeriesDescription,
    chartsLatestMeasurement,
  };
};
