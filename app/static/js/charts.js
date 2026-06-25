// Chart.js setup for the portfolio ₹-impact charts and the applicant SHAP chart.
// Loaded on both the dashboard and the applicant page (functions are no-ops if
// the relevant canvas is absent).

let netChart = null;
let rateRevChart = null;

// Shared visual tokens (match the CSS design system).
const GRID = "#eef2f7";
const TICK = "#64748b";
const BLUE = "#2563eb";
const GREEN = "#16a34a";
const AMBER = "#f59e0b";
const RED = "#dc2626";

function fmtT(t) { return Number(t).toFixed(2); }

function axisTitle(text) {
  return { display: true, text: text, color: TICK, font: { size: 11, weight: "600" } };
}

// Draws dashed vertical lines (optimal + current threshold) on the net chart.
const verticalMarkers = {
  id: "verticalMarkers",
  afterDraw(chart) {
    const markers = chart.$markers;
    if (!markers || !markers.length) return;
    const x = chart.scales.x;
    const { top, bottom } = chart.chartArea;
    markers.forEach(function (m) {
      const idx = chart.data.labels.indexOf(m.label);
      if (idx < 0) return;
      const px = x.getPixelForValue(idx);
      chart.ctx.save();
      chart.ctx.beginPath();
      chart.ctx.setLineDash([6, 4]);
      chart.ctx.lineWidth = 2;
      chart.ctx.strokeStyle = m.color;
      chart.ctx.moveTo(px, top);
      chart.ctx.lineTo(px, bottom);
      chart.ctx.stroke();
      chart.ctx.restore();
    });
  },
};

function initPortfolioCharts(series, optimal) {
  const labels = series.map(function (s) { return fmtT(s.threshold); });
  const netM = series.map(function (s) { return s.net_portfolio_value / 1e6; });
  const rate = series.map(function (s) { return s.approval_rate; });
  const revM = series.map(function (s) { return s.total_revenue / 1e6; });

  // ---- Chart A: Net Portfolio Value vs Threshold ----
  const netCanvas = document.getElementById("chart-net");
  if (netCanvas) {
    // Soft area gradient under the line.
    const ctx = netCanvas.getContext("2d");
    const grad = ctx.createLinearGradient(0, 0, 0, 300);
    grad.addColorStop(0, "rgba(37, 99, 235, 0.25)");
    grad.addColorStop(1, "rgba(37, 99, 235, 0)");

    netChart = new Chart(netCanvas, {
      type: "line",
      data: {
        labels: labels,
        datasets: [{
          label: "Net ₹ Value (millions)",
          data: netM,
          borderColor: BLUE,
          backgroundColor: grad,
          borderWidth: 2,
          fill: true,
          tension: 0.35,
          pointRadius: 0,
          pointHoverRadius: 4,
          pointHoverBackgroundColor: BLUE,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: "index", intersect: false },
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: function (c) { return "₹" + c.parsed.y.toFixed(1) + "M"; },
            },
          },
        },
        scales: {
          x: {
            title: axisTitle("Threshold"),
            grid: { display: false },
            ticks: { color: TICK, font: { size: 11 }, maxTicksLimit: 9 },
          },
          y: {
            title: axisTitle("Net ₹ (millions)"),
            grid: { color: GRID },
            border: { display: false },
            ticks: { color: TICK, font: { size: 11 } },
          },
        },
      },
      plugins: [verticalMarkers],
    });
    netChart.$optimalLabel = fmtT(optimal);
    netChart.$markers = [{ label: fmtT(optimal), color: AMBER }];
    netChart.update();
  }

  // ---- Chart B: Approval Rate & Revenue vs Threshold (dual axis) ----
  const rrCanvas = document.getElementById("chart-rate-rev");
  if (rrCanvas) {
    rateRevChart = new Chart(rrCanvas, {
      type: "line",
      data: {
        labels: labels,
        datasets: [
          {
            label: "Approval rate (%)",
            data: rate,
            borderColor: GREEN,
            backgroundColor: "rgba(22, 163, 74, 0.08)",
            borderWidth: 2,
            yAxisID: "y",
            tension: 0.35,
            pointRadius: 0,
            pointHoverRadius: 4,
          },
          {
            label: "Revenue (₹M)",
            data: revM,
            borderColor: BLUE,
            backgroundColor: "rgba(37, 99, 235, 0.08)",
            borderWidth: 2,
            yAxisID: "y1",
            tension: 0.35,
            pointRadius: 0,
            pointHoverRadius: 4,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: "index", intersect: false },
        plugins: {
          legend: {
            display: true,
            position: "bottom",
            labels: { color: TICK, usePointStyle: true, boxWidth: 8, font: { size: 12 } },
          },
        },
        scales: {
          x: {
            title: axisTitle("Threshold"),
            grid: { display: false },
            ticks: { color: TICK, font: { size: 11 }, maxTicksLimit: 9 },
          },
          y: {
            position: "left",
            title: axisTitle("Approval rate (%)"),
            grid: { color: GRID },
            border: { display: false },
            ticks: { color: TICK, font: { size: 11 } },
          },
          y1: {
            position: "right",
            title: axisTitle("Revenue (₹M)"),
            grid: { drawOnChartArea: false },
            border: { display: false },
            ticks: { color: TICK, font: { size: 11 } },
          },
        },
      },
    });
  }
}

// Marks the current threshold on Chart A (blue dashed line, kept alongside amber optimal).
function highlightThreshold(t) {
  if (!netChart) return;
  netChart.$markers = [
    { label: netChart.$optimalLabel, color: AMBER },
    { label: fmtT(t), color: BLUE },
  ];
  netChart.update();
}

// Horizontal SHAP bar chart on the applicant page. Positive = red (raises risk),
// negative = green (lowers risk). Shows the top 5 factors.
function initShapChart(shapValues) {
  const canvas = document.getElementById("chart-shap");
  if (!canvas) return;

  const top = shapValues.slice(0, 5);
  const labels = top.map(function (s) { return s.feature; });
  const values = top.map(function (s) { return s.shap_value; });
  const colors = values.map(function (v) { return v >= 0 ? RED : GREEN; });

  // Destroy any prior instance so the canvas/page does not grow on re-render.
  if (window.shapChartInstance) {
    window.shapChartInstance.destroy();
  }
  window.shapChartInstance = new Chart(canvas, {
    type: "bar",
    data: {
      labels: labels,
      datasets: [{ data: values, backgroundColor: colors, borderRadius: 3 }],
    },
    options: {
      indexAxis: "y",
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: function (c) { return "SHAP: " + c.parsed.x.toFixed(3); },
          },
        },
      },
      scales: {
        x: {
          title: axisTitle("SHAP value (→ raises default risk)"),
          grid: { color: GRID },
          border: { display: false },
          ticks: { color: TICK, font: { size: 11 } },
        },
        y: {
          grid: { display: false },
          ticks: { color: TICK, font: { size: 11 } },
        },
      },
    },
  });
}
