// Chart.js setup for the portfolio ₹-impact charts and the applicant SHAP chart.
// Loaded on both the dashboard and the applicant page (functions are no-ops if
// the relevant canvas is absent).

let netChart = null;
let rateRevChart = null;
let shapChart = null;

function fmtT(t) { return Number(t).toFixed(2); }

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
    netChart = new Chart(netCanvas, {
      type: "line",
      data: {
        labels: labels,
        datasets: [{
          label: "Net ₹ Value (millions)",
          data: netM,
          borderColor: "#2563eb",
          backgroundColor: "rgba(37,99,235,0.10)",
          fill: true,
          tension: 0.25,
          pointRadius: 2,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: function (c) { return "₹" + c.parsed.y.toFixed(1) + "M"; },
            },
          },
        },
        scales: {
          x: { title: { display: true, text: "Threshold" } },
          y: { title: { display: true, text: "Net ₹ (millions)" } },
        },
      },
      plugins: [verticalMarkers],
    });
    netChart.$optimalLabel = fmtT(optimal);
    netChart.$markers = [{ label: fmtT(optimal), color: "#f59e0b" }];
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
            borderColor: "#16a34a",
            backgroundColor: "rgba(22,163,74,0.08)",
            yAxisID: "y",
            tension: 0.25,
            pointRadius: 2,
          },
          {
            label: "Revenue (₹M)",
            data: revM,
            borderColor: "#2563eb",
            backgroundColor: "rgba(37,99,235,0.08)",
            yAxisID: "y1",
            tension: 0.25,
            pointRadius: 2,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: true, position: "bottom" } },
        scales: {
          x: { title: { display: true, text: "Threshold" } },
          y: {
            position: "left",
            title: { display: true, text: "Approval rate (%)" },
          },
          y1: {
            position: "right",
            title: { display: true, text: "Revenue (₹M)" },
            grid: { drawOnChartArea: false },
          },
        },
      },
    });
  }
}

// Marks the current threshold on Chart A (blue dashed line, kept alongside gold optimal).
function highlightThreshold(t) {
  if (!netChart) return;
  netChart.$markers = [
    { label: netChart.$optimalLabel, color: "#f59e0b" },
    { label: fmtT(t), color: "#2563eb" },
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
  const colors = values.map(function (v) {
    return v >= 0 ? "#dc2626" : "#16a34a";
  });

  if (shapChart) shapChart.destroy();
  shapChart = new Chart(canvas, {
    type: "bar",
    data: {
      labels: labels,
      datasets: [{ data: values, backgroundColor: colors }],
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
        x: { title: { display: true, text: "SHAP value (→ raises default risk)" } },
      },
    },
  });
}
