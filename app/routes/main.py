"""Landing and base page routes."""
from flask import Blueprint

main_bp = Blueprint("main", __name__)


@main_bp.route("/health")
def health():
    # "/" now renders the portfolio dashboard (portfolio_bp); this stays a
    # lightweight liveness check.
    return "LDIP running"
