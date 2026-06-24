"""Single applicant lookup routes (decision + reasons).

Exposes POST /api/score: a JSON applicant profile in, a full lending decision
out. Missing features fall back to dataset medians (FEATURE_DEFAULTS).
"""
from flask import Blueprint, jsonify, request

from app.decision.engine import DecisionEngine

applicant_bp = Blueprint("applicant", __name__)

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


@applicant_bp.route("/applicant")
def applicant():
    return "Applicant lookup — coming soon"


@applicant_bp.route("/api/score", methods=["POST"])
def score():
    """Score an applicant. Body: JSON with any subset of the 30 features."""
    payload = request.get_json(silent=True) or {}

    # Start from medians, overlay any provided values, validating numerics.
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
