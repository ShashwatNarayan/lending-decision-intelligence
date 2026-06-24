"""Applicant routes — split into two blueprints.

- ``applicant_bp``      → HTML pages, mounted at ``/applicant`` (Part E).
- ``applicant_api_bp``  → JSON API, mounted at root so the existing
  ``/api/score`` and ``/api/applicant/*`` paths stay exactly as they were.

Keeping the API in its own root-mounted blueprint is the only way to honour both
"register the applicant blueprint at url_prefix=/applicant" and "keep existing
API routes unchanged".
"""
import json
from decimal import Decimal

from flask import (
    Blueprint, jsonify, redirect, render_template, request, url_for,
)
from sqlalchemy import func

from app.database import db
from app.decision.engine import DecisionEngine
from app.models.db_models import LoanApplication
from app.models.explainer import get_explainer

applicant_bp = Blueprint("applicant", __name__)          # HTML, prefix /applicant
applicant_api_bp = Blueprint("applicant_api", __name__)  # JSON, no prefix

# Dataset median values for all 30 features. Any feature omitted from a request
# defaults to its median, so callers can submit just the fields they care about.
FEATURE_DEFAULTS = {
    "loan_amnt": 10000,
    "int_rate": 13.99,
    "annual_inc": 65000,
    "dti": 17.0,
    "emp_length": 5.0,
    "revol_bal": 8000,
    "revol_util": 45.0,
    "mort_acc": 1,
    "credit_history_years": 12.0,
    "loan_to_income": 0.154,
    "fico_score": 692.0,
    "installment_to_income": 0.035,
    "int_rate_tier": 2,
    "open_acc_ratio": 0.5,
    "has_delinquency": 0,
    "has_pub_rec": 0,
    "high_inq_flag": 0,
    "loan_amnt_tier": 1,
    "is_short_term": 1,
    "grade_encoded": 2,
    "home_OTHER": 0,
    "home_OWN": 0,
    "home_RENT": 1,
    "purpose_credit_card": 0,
    "purpose_debt_consolidation": 1,
    "purpose_home_improvement": 0,
    "purpose_major_purchase": 0,
    "purpose_medical": 0,
    "purpose_other": 0,
    "purpose_small_business": 0,
}


def _num(value):
    """Convert DB Numeric/bool to a plain JSON-friendly number."""
    if value is None:
        return None
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, Decimal):
        return float(value)
    return value


def _serialize_applicant(row):
    """Build the response dict for a stored loan application."""
    reasons = row.decision_reasons
    if reasons:
        try:
            reasons = json.loads(reasons)
        except (ValueError, TypeError):
            pass  # leave as the raw stored text if it isn't valid JSON

    data = {
        "id": row.id,
        "default_probability": _num(row.default_probability),
        "decision": row.decision,
        "assigned_rate": _num(row.assigned_rate),
        "decision_reasons": reasons,
        "target": row.target,
    }
    for feature in FEATURE_DEFAULTS:
        data[feature] = _num(getattr(row, feature))
    return data


def _feature_vector(row):
    """Numeric {feature: value} dict for the 30 model features of one row."""
    return {f: float(_num(getattr(row, f)) or 0) for f in FEATURE_DEFAULTS}


# ----------------------------------------------------------------------------
# JSON API (root-mounted, paths unchanged from Phase 1/2)
# ----------------------------------------------------------------------------
@applicant_api_bp.route("/api/score", methods=["POST"])
def score():
    """Score an applicant. Body: JSON with any subset of the 30 features."""
    payload = request.get_json(silent=True) or {}

    features = dict(FEATURE_DEFAULTS)
    for name, value in payload.items():
        if name not in FEATURE_DEFAULTS:
            continue  # Ignore unknown keys rather than failing the request.
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return jsonify(error=f"Invalid feature value: {name}"), 400
        features[name] = value

    try:
        result = DecisionEngine().decide(features)
    except Exception:
        return jsonify(error="Scoring failed"), 500

    return jsonify(
        decision=result["decision"],
        default_probability=result["default_probability"],
        assigned_rate=result["assigned_rate"],
        reasons=result["reasons"],
        top_factors=result["top_factors"],
        threshold_used=result["threshold_used"],
    )


@applicant_api_bp.route("/api/applicant/random")
def applicant_random_api():
    """A random scored applicant, optionally filtered by decision."""
    query = LoanApplication.query
    decision = request.args.get("decision")
    if decision:
        query = query.filter(LoanApplication.decision == decision)

    row = query.order_by(func.random()).first()
    if row is None:
        return jsonify(error="Applicant not found"), 404
    return jsonify(_serialize_applicant(row))


@applicant_api_bp.route("/api/applicant/<int:applicant_id>")
def applicant_detail_api(applicant_id):
    """Full stored decision + features for one application by id."""
    row = db.session.get(LoanApplication, applicant_id)
    if row is None:
        return jsonify(error="Applicant not found"), 404
    return jsonify(_serialize_applicant(row))


@applicant_api_bp.route("/api/applicant/<int:applicant_id>/shap")
def applicant_shap_api(applicant_id):
    """Fresh top-10 SHAP attribution for one applicant (powers the bar chart)."""
    row = db.session.get(LoanApplication, applicant_id)
    if row is None:
        return jsonify(error="Applicant not found"), 404

    shap_values = get_explainer().get_shap_values(_feature_vector(row), top_n=10)
    return jsonify(applicant_id=applicant_id, shap_values=shap_values)


# ----------------------------------------------------------------------------
# HTML pages (mounted at /applicant)
# ----------------------------------------------------------------------------
@applicant_bp.route("/<int:applicant_id>")
def applicant_page(applicant_id):
    """Render the single-applicant detail page."""
    row = db.session.get(LoanApplication, applicant_id)
    if row is None:
        return render_template("404.html", message="Applicant not found."), 404
    return render_template("applicant.html", applicant=_serialize_applicant(row))


@applicant_bp.route("/random")
def random_applicant():
    """Pick a random applicant (optionally by decision) and redirect to it."""
    query = LoanApplication.query
    decision = request.args.get("decision")
    if decision:
        query = query.filter(LoanApplication.decision == decision)

    row = query.order_by(func.random()).first()
    if row is None:
        return render_template("404.html", message="No matching applicant."), 404
    return redirect(url_for("applicant.applicant_page", applicant_id=row.id))
