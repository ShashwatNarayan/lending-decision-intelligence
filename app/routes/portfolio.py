"""Portfolio dashboard routes (threshold slider + ₹ impact, built in Phase 4)."""
from flask import Blueprint

portfolio_bp = Blueprint("portfolio", __name__)


@portfolio_bp.route("/portfolio")
def portfolio():
    return "Portfolio dashboard — coming soon"
