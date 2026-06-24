"""Translate top SHAP features into plain-English adverse-action reasons (Phase 1)."""

# Minimum absolute SHAP contribution for a factor to be worth mentioning.
_MIN_ABS_SHAP = 0.05

# Static feature -> reason text for REJECT explanations. Features whose reason
# only applies when a flag is set are handled separately in _reject_reason().
_REJECT_REASONS = {
    "int_rate": "The assigned interest rate indicates elevated risk.",
    "int_rate_tier": "The assigned interest rate indicates elevated risk.",
    "dti": "Debt-to-income ratio exceeds acceptable thresholds.",
    "loan_to_income": "Loan amount is high relative to annual income.",
    "installment_to_income": "Monthly payment burden is high relative to income.",
    "fico_score": "Credit score is below the threshold for approval.",
    "grade_encoded": "Loan grade reflects elevated borrower risk.",
}

# Positive framing for APPROVE explanations (factor reduces risk).
_APPROVE_REASONS = {
    "fico_score": "Strong credit score.",
    "dti": "Low debt-to-income ratio.",
    "loan_to_income": "Loan amount is modest relative to income.",
    "installment_to_income": "Affordable monthly payment relative to income.",
    "int_rate": "Favorable assigned interest rate.",
    "int_rate_tier": "Favorable assigned interest rate.",
    "grade_encoded": "Strong loan grade.",
    "has_delinquency": "No recent delinquencies on record.",
    "has_pub_rec": "No public derogatory records.",
    "high_inq_flag": "Few recent credit inquiries.",
    "is_short_term": "Shorter loan term reduces default risk.",
    "revol_util": "Low revolving credit utilization.",
    "annual_inc": "Healthy annual income.",
}


def _reject_reason(factor):
    """Return the REJECT reason string for one top_factor dict, or None."""
    feat = factor["feature"]
    val = factor["feature_value"]

    # Flag-conditional reasons: only meaningful when the flag is on.
    if feat == "has_delinquency" and val == 1:
        return "Recent delinquency on credit record."
    if feat == "has_pub_rec" and val == 1:
        return "Public derogatory record present (bankruptcy or judgement)."
    if feat == "high_inq_flag" and val == 1:
        return "Multiple recent credit inquiries indicate financial stress."
    if feat == "is_short_term" and val == 0:
        return "60-month term loans carry higher default risk."
    if feat == "purpose_debt_consolidation" and val == 1:
        return "Debt consolidation purpose carries elevated risk."

    if feat in _REJECT_REASONS:
        return _REJECT_REASONS[feat]

    # Skip flag features that didn't meet their on-condition above.
    if feat in ("has_delinquency", "has_pub_rec", "high_inq_flag",
                "is_short_term", "purpose_debt_consolidation"):
        return None

    return f"Risk factor: {feat}."


def generate_reasons(top_factors: list, decision: str) -> list:
    """Build plain-English adverse-action / approval reasons from SHAP factors.

    Only factors with |shap_value| > 0.05 are considered. Output is capped at
    4 reasons. Returns a plain list of strings.
    """
    reasons = []
    seen = set()

    if decision == "REJECT":
        # Risk-increasing factors have positive SHAP values; consider those
        # that meaningfully push toward default.
        for factor in top_factors:
            if factor["shap_value"] <= 0:
                continue
            if abs(factor["shap_value"]) <= _MIN_ABS_SHAP:
                continue
            text = _reject_reason(factor)
            if text and text not in seen:
                seen.add(text)
                reasons.append(text)
            if len(reasons) >= 4:
                break
    else:  # APPROVE
        # Risk-reducing factors have negative SHAP values.
        for factor in top_factors:
            if factor["shap_value"] >= 0:
                continue
            if abs(factor["shap_value"]) <= _MIN_ABS_SHAP:
                continue
            text = _APPROVE_REASONS.get(factor["feature"])
            if text is None:
                text = f"Favorable factor: {factor['feature']}."
            if text not in seen:
                seen.add(text)
                reasons.append(text)
            if len(reasons) >= 2:
                break

    return reasons[:4]
