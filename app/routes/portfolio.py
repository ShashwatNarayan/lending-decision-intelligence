"""Portfolio dashboard routes + backtest API (Phase 2).

The dashboard UI itself is built in Phase 4; these JSON endpoints expose the
pre-computed ₹ backtest (portfolio_snapshots) and live threshold evaluation.
"""
from flask import Blueprint, jsonify, render_template

from app.backtest.evaluator import get_evaluator
from app.database import db
from app.models.db_models import PortfolioSnapshot

portfolio_bp = Blueprint("portfolio", __name__)


@portfolio_bp.route("/")
@portfolio_bp.route("/portfolio")
def dashboard():
    """Render the portfolio dashboard pre-filled with the optimal threshold.

    Server-renders the cards (so the page is useful without JS) and passes the
    full 41-threshold series + initial metrics as JSON for the charts/slider.
    """
    evaluator = get_evaluator()
    snaps = (
        PortfolioSnapshot.query.order_by(PortfolioSnapshot.threshold.asc()).all()
    )

    # Full evaluation per stored threshold (net value matches the snapshots;
    # also yields revenue/approval-rate needed by the charts).
    series = [evaluator.evaluate_at_threshold(float(s.threshold)) for s in snaps]
    chart_series = [
        {
            "threshold": r["threshold"],
            "net_portfolio_value": r["net_portfolio_value"],
            "approval_rate": r["approval_rate"],
            "total_revenue": r["total_revenue"],
        }
        for r in series
    ]

    optimal = (
        max(series, key=lambda r: r["net_portfolio_value"])["threshold"]
        if series else 0.44
    )
    initial = evaluator.evaluate_at_threshold(optimal)

    return render_template(
        "portfolio.html",
        initial=initial,
        series=chart_series,
        optimal=optimal,
    )


def _approval_rate(snap):
    total = (snap.approvals or 0) + (snap.rejections or 0)
    return round((snap.approvals or 0) / total * 100.0, 2) if total else 0.0


@portfolio_bp.route("/api/backtest/summary")
def backtest_summary():
    """All stored threshold snapshots (ascending) + the optimal threshold."""
    snaps = (
        PortfolioSnapshot.query.order_by(PortfolioSnapshot.threshold.asc()).all()
    )
    rows = [
        {
            "threshold": float(s.threshold),
            "approvals": s.approvals,
            "rejections": s.rejections,
            "net_portfolio_value": float(s.net_portfolio_value),
            "approval_rate": _approval_rate(s),
        }
        for s in snaps
    ]

    optimal = max(rows, key=lambda r: r["net_portfolio_value"]) if rows else None
    return jsonify(
        optimal_threshold=optimal["threshold"] if optimal else None,
        snapshots=rows,
    )


@portfolio_bp.route("/api/backtest/threshold/<float:threshold>")
def backtest_threshold(threshold):
    """Full evaluation at a threshold (nearest stored grid value, else live)."""
    rounded = round(threshold, 2)

    # Look up the nearest stored snapshot (the grid is 0.10–0.50 by 0.01).
    snap = PortfolioSnapshot.query.filter(
        PortfolioSnapshot.threshold == rounded
    ).first()
    # Whether stored or not, return the full dict from evaluate_at_threshold.
    target = float(snap.threshold) if snap else rounded
    return jsonify(get_evaluator().evaluate_at_threshold(target))


@portfolio_bp.route("/api/backtest/optimal")
def backtest_optimal():
    """The stored threshold with the highest net value, fully evaluated."""
    snap = (
        PortfolioSnapshot.query
        .order_by(PortfolioSnapshot.net_portfolio_value.desc())
        .first()
    )
    if snap is None:
        return jsonify(error="No backtest snapshots found"), 404
    return jsonify(get_evaluator().evaluate_at_threshold(float(snap.threshold)))
