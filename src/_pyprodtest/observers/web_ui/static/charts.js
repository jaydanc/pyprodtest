import { escapeHtml, formatTime } from "./utils.js";

const charts = new Map();

export function measurementMarkup(measurements, scope) {
  if (!measurements.length) return "";
  return `<section class="measurements" aria-label="Measured data">
    <div class="measurement-heading"><span>Measured data</span><span>${measurements.length} ${measurements.length === 1 ? "series" : "series"}</span></div>
    <div class="measurement-grid">${measurements.map((series, index) => {
      const latest = series.points.at(-1);
      return `<article class="measurement-card">
        <div class="measurement-summary">
          <div><span class="measurement-name">${escapeHtml(series.name)}</span><small>${series.x_axis === "time" ? "Live time series" : `X / Y plot${series.x_unit || series.unit ? ` · ${escapeHtml(series.x_unit || "X")} → ${escapeHtml(series.unit || "Y")}` : ""}`}</small></div>
          <div class="measurement-latest"><strong>${latest ? `${escapeHtml(latest.y)}${series.unit ? ` ${escapeHtml(series.unit)}` : ""}` : "—"}</strong><small>Latest</small></div>
        </div>
        <div class="chart-wrap"><canvas id="chart-${scope}-${index}" aria-label="${escapeHtml(series.name)} chart" role="img"></canvas></div>
      </article>`;
    }).join("")}</div>
  </section>`;
}

export function renderCharts(measurements, scope) {
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
          x: { type: isTime ? "category" : "linear", grid: { color: "rgba(158, 176, 195, 0.08)" }, title: { display: !isTime && Boolean(series.x_unit), text: series.x_unit, color: "#9eb0c3" }, ticks: { color: "#6f8297", maxTicksLimit: 7 } },
          y: { grid: { color: "rgba(158, 176, 195, 0.08)" }, title: { display: Boolean(series.unit), text: series.unit, color: "#9eb0c3" }, ticks: { color: "#6f8297", maxTicksLimit: 6 } },
        },
      },
    }));
  });
}
