"""XGBoost model loading and default-probability prediction (Phase 1)."""
import os
import pickle
import warnings

import pandas as pd

# The pickled scaler/model were serialized with sklearn 1.3.2 / xgboost 2.0.3
# (pinned in requirements.txt). Loading them can emit an InconsistentVersion
# UserWarning depending on the runtime; the versions are pinned and verified
# compatible in CLAUDE.md, so this is safe to silence.
warnings.filterwarnings("ignore", category=UserWarning)

ARTIFACTS_DIR = os.path.join(
    os.path.dirname(__file__), "..", "..", "model", "artifacts"
)


class ScoringModel:
    """Loads the XGBoost artifacts and scores single applicants."""

    def __init__(self):
        self.model = self._load("xgboost_model")
        self.scaler = self._load("scaler")
        self.feature_columns = self._load("feature_columns")  # list of 30
        self.threshold = self._load("optimal_threshold")  # 0.2282...

    @staticmethod
    def _load(name):
        path = os.path.join(ARTIFACTS_DIR, f"{name}.pkl")
        with open(path, "rb") as f:
            return pickle.load(f)

    def predict(self, features_dict):
        """Score a single applicant from a {feature_name: value} dict.

        Returns default_probability, decision, and threshold_used.
        """
        # a. Build a single-row DataFrame in the exact feature order.
        df_row = pd.DataFrame([features_dict], columns=self.feature_columns)

        # b. The XGBoost model was trained on RAW (unscaled) features — verified
        #    empirically: raw scoring reproduces the dataset's ~20% default rate
        #    and the documented median-applicant probability (~0.19), while
        #    scaler.transform() inputs produce nonsensical ~0.60 probabilities
        #    and break correlation with the ground-truth target. Tree models do
        #    not require feature scaling, and SHAP's TreeExplainer is run on raw
        #    features too (see explainer.py) — so the scorer and explainer must
        #    agree on raw inputs. The scaler artifact is still loaded per spec
        #    but is intentionally not applied here.
        # c. P(default) is the probability of the positive class (index 1).
        prob = float(self.model.predict_proba(df_row)[0][1])

        # d. Decision: approve only if risk is below the optimal threshold.
        decision = "APPROVE" if prob < self.threshold else "REJECT"

        # e. Return the structured result.
        return {
            "default_probability": round(prob, 4),
            "decision": decision,
            "threshold_used": self.threshold,
        }


# Module-level singleton: load the artifacts once per process.
_model_instance = None


def get_model() -> ScoringModel:
    """Lazily build (once) and return the shared ScoringModel."""
    global _model_instance
    if _model_instance is None:
        _model_instance = ScoringModel()
    return _model_instance


if __name__ == "__main__":
    model = get_model()

    sample_applicant = {
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

    result = model.predict(sample_applicant)
    print(result)
