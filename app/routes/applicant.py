"""Single applicant lookup routes (decision + reasons, built in Phase 4)."""
from flask import Blueprint

applicant_bp = Blueprint("applicant", __name__)


@applicant_bp.route("/applicant")
def applicant():
    return "Applicant lookup — coming soon"
