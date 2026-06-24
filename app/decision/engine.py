"""Cost-sensitive threshold engine: approve/reject decisions and ₹ portfolio impact (Phase 1)."""
from app.decision.adverse_action import generate_reasons
from app.decision.pricing import assign_rate
from app.models.explainer import get_explainer
from app.models.scoring import get_model


class DecisionEngine:
    """Single entry point for a full lending decision on one applicant."""

    def __init__(self, threshold=None):
        # Default to the model's optimal threshold; allow an override so the
        # Phase 4 dashboard slider can simulate other cut-offs.
        if threshold is None:
            threshold = get_model().threshold
        self.threshold = threshold

    def decide(self, features_dict):
        """Score, explain, price, and justify a single applicant.

        Returns the full decision payload.
        """
        # a. Probability of default + base decision against the model threshold.
        score = get_model().predict(features_dict)
        prob = score["default_probability"]

        # Re-derive the decision against this engine's (possibly custom)
        # threshold rather than the model default.
        decision = "APPROVE" if prob < self.threshold else "REJECT"

        # b. Per-feature SHAP attribution.
        explanation = get_explainer().explain(features_dict)

        # c. Plain-English reasons from the top SHAP factors.
        reasons = generate_reasons(explanation["top_factors"], decision)

        # d. Risk-based interest rate (None when rejected).
        rate = assign_rate(prob) if decision == "APPROVE" else None

        return {
            "default_probability": prob,
            "decision": decision,
            "assigned_rate": rate,
            "reasons": reasons,
            "top_factors": explanation["top_factors"],
            "threshold_used": self.threshold,
        }
