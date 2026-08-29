import { renderState, setConnection } from "./dashboard.js";

const POLL_INTERVAL_MS = 500;

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
