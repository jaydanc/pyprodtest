const OUTCOMES = new Set(["passed", "failed", "running", "skipped", "pending"]);

export function escapeHtml(value) {
  const entities = {
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    "'": "&#39;",
    '"': "&quot;",
  };
  return String(value ?? "").replace(/[&<>'"]/g, (character) => entities[character]);
}

export function statusName(outcome) {
  return OUTCOMES.has(outcome) ? outcome : "pending";
}

export function formatDuration(seconds) {
  if (seconds < 1) return `${Math.round(seconds * 1000)} ms`;
  return `${seconds.toFixed(2)} s`;
}

export function formatTime(timestamp) {
  const date = new Date(timestamp);
  return Number.isNaN(date.valueOf())
    ? timestamp
    : date.toLocaleTimeString([], { hour12: false });
}

export function countOutcomes(tests) {
  return tests.reduce((counts, test) => {
    counts[test.outcome] = (counts[test.outcome] || 0) + 1;
    return counts;
  }, {});
}

export function chartScope(test) {
  return `test-${test.nodeid.replace(/[^a-z0-9]/gi, "-")}`;
}
