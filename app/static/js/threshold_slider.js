// Threshold slider: render initial state from server data, then fetch updated
// ₹ portfolio metrics from /api/backtest/threshold/<T> as the slider moves.

(function () {
  const TOTAL = window.LDI_TOTAL || 133018;

  function fmtInt(n) { return Number(n).toLocaleString("en-IN"); }
  function fmtRupeesM(v) { return "₹" + (v / 1e6).toFixed(1) + "M"; }

  // Updates the four metric cards from an evaluate_at_threshold() response.
  function renderCards(d) {
    const approvalRate = d.approval_rate;
    const rejectionRate = (d.rejections / TOTAL) * 100;

    document.getElementById("card-approvals").textContent = fmtInt(d.approvals);
    document.getElementById("card-approvals-sub").textContent =
      approvalRate.toFixed(2) + "% of " + fmtInt(TOTAL);

    document.getElementById("card-rejections").textContent = fmtInt(d.rejections);
    document.getElementById("card-rejections-sub").textContent =
      rejectionRate.toFixed(2) + "% of " + fmtInt(TOTAL);

    document.getElementById("card-net").textContent =
      fmtRupeesM(d.net_portfolio_value);

    document.getElementById("card-defaults").textContent =
      fmtInt(d.false_positives);
  }

  function setThresholdLabels(t) {
    document.getElementById("slider-value").textContent = Number(t).toFixed(2);
    const topbar = document.getElementById("topbar-threshold");
    if (topbar) topbar.textContent = Math.round(t * 100) + "%";
  }

  document.addEventListener("DOMContentLoaded", function () {
    const slider = document.getElementById("threshold-slider");
    if (!slider) return;

    // 1. Initial render from server-provided data (works without any fetch).
    renderCards(window.LDI_INITIAL);
    initPortfolioCharts(window.LDI_SERIES, window.LDI_OPTIMAL);
    slider.value = window.LDI_OPTIMAL;
    setThresholdLabels(window.LDI_OPTIMAL);
    highlightThreshold(window.LDI_OPTIMAL);

    // 2. On slide: fetch the evaluation at the new threshold and update.
    slider.addEventListener("input", function () {
      const t = parseFloat(slider.value);
      setThresholdLabels(t);
      highlightThreshold(t);

      fetch("/api/backtest/threshold/" + t.toFixed(2))
        .then(function (r) { return r.json(); })
        .then(function (d) { renderCards(d); })
        .catch(function () { /* keep last good values on failure */ });
    });
  });
})();
