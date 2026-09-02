// Finds measurement chart canvases in the rendered Alpine DOM and updates them
// with the latest test measurement series from each polled state snapshot.
function chartsFormatTime(timestamp) {
  const date = new Date(timestamp);
  return Number.isNaN(date.valueOf())
    ? timestamp
    : date.toLocaleTimeString([], { hour12: false });
}

function chartsData(series) {
  const isTime = series.x_axis === "time";
  return {
    data: isTime
      ? series.points.map((point) => point.y)
      : series.points.map((point) => ({ x: point.x, y: point.y })),
    isTime,
    labels: isTime ? series.points.map((point) => chartsFormatTime(point.x)) : undefined,
  };
}

function chartsFormatValue(value, unit) {
  if (!unit) return `${value}`;
  return `${value} ${unit}`;
}

function chartsTooltipCallbacks(series, isTime) {
  return {
    title: () => [],
    label: (context) => {
      const x = isTime ? context.label : context.parsed.x;
      return [
        `X: ${chartsFormatValue(x, series.x_unit)}`,
        `Y: ${chartsFormatValue(context.parsed.y, series.unit)}`,
      ];
    },
  };
}

function chartsOptions(series, isTime) {
  return {
    animation: false,
    maintainAspectRatio: false,
    normalized: true,
    parsing: isTime,
    plugins: {
      legend: { display: false },
      tooltip: {
        callbacks: chartsTooltipCallbacks(series, isTime),
        displayColors: false,
      },
    },
    scales: {
      x: {
        grid: { color: "rgba(158, 176, 195, 0.08)" },
        ticks: { color: "#6f8297", maxTicksLimit: 7 },
        title: {
          color: "#9eb0c3",
          display: !isTime && Boolean(series.x_unit),
          text: series.x_unit,
        },
        type: isTime ? "category" : "linear",
      },
      y: {
        grid: { color: "rgba(158, 176, 195, 0.08)" },
        ticks: { color: "#6f8297", maxTicksLimit: 6 },
        title: {
          color: "#9eb0c3",
          display: Boolean(series.unit),
          text: series.unit,
        },
      },
    },
  };
}

function chartsRenderMeasurement(canvas, series) {
  if (typeof Chart === "undefined" || !canvas || !series) return;

  const { data, isTime, labels } = chartsData(series);
  const dataset = {
    backgroundColor: "rgba(46, 184, 255, 0.12)",
    borderColor: "#2eb8ff",
    borderWidth: 2,
    data,
    fill: true,
    pointHoverRadius: 4,
    pointRadius: data.length > 40 ? 0 : 2.5,
    tension: 0.22,
  };

  if (canvas.pyprodtestChart) {
    canvas.pyprodtestChart.data.labels = labels;
    canvas.pyprodtestChart.data.datasets = [dataset];
    canvas.pyprodtestChart.options = chartsOptions(series, isTime);
    canvas.pyprodtestChart.update("none");
    return;
  }

  canvas.pyprodtestChart = new Chart(canvas, {
    type: "line",
    data: { labels, datasets: [dataset] },
    options: chartsOptions(series, isTime),
  });
}

export function chartsRefresh(container) {
  container.querySelectorAll("canvas").forEach((canvas) => {
    canvas.pyprodtestChart?.resize();
    canvas.pyprodtestChart?.update("none");
  });
}

export function chartsKey(test, series) {
  return `${test.nodeid || test.name}:${series.name}`;
}

function chartsSeriesByKey(tests) {
  const seriesByKey = new Map();
  tests.forEach((test) => {
    test.measurements.forEach((series) => {
      seriesByKey.set(chartsKey(test, series), series);
    });
  });
  return seriesByKey;
}

export function chartsRenderVisible(tests) {
  const seriesByKey = chartsSeriesByKey(tests);
  document.querySelectorAll("canvas[data-chart-key]").forEach((canvas) => {
    chartsRenderMeasurement(canvas, seriesByKey.get(canvas.dataset.chartKey));
  });
}

export function chartsSeriesDescription(series) {
  if (series.x_axis === "time") return "Live time series";
  if (!series.x_unit && !series.unit) return "X / Y plot";
  return `X / Y plot · ${series.x_unit || "X"} -> ${series.unit || "Y"}`;
}

export function chartsLatestMeasurement(series) {
  const latest = series.points.at(-1);
  if (!latest) return "-";
  return `${latest.y}${series.unit ? ` ${series.unit}` : ""}`;
}
