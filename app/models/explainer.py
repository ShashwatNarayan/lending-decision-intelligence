"""SHAP value computation and per-borrower reason inputs (Phase 1)."""
import warnings

import pandas as pd
import shap

from app.models.scoring import ScoringModel, get_model

# Same rationale as scoring.py: silence the pinned-version pickle UserWarning.
warnings.filterwarnings("ignore", category=UserWarning)


class SHAPExplainer:
    """Computes per-feature SHAP contributions for a single applicant."""

    def __init__(self, scoring_model: ScoringModel):
        # TreeExplainer operates directly on the trained tree model and on RAW
        # features — matching how scoring.py runs the model (no scaling).
        self.explainer = shap.TreeExplainer(scoring_model.model)
        self.feature_columns = scoring_model.feature_columns

    def explain(self, features_dict):
        """Return SHAP contributions for an applicant.

        Output keys: shap_values (all 30), top_factors (top 5 by |value|),
        base_value.
        """
        # a. Build a single-row DataFrame in the exact feature order. No scaling.
        df_row = pd.DataFrame([features_dict], columns=self.feature_columns)

        # b. shap_values for a single row → shape (1, 30).
        shap_values = self.explainer.shap_values(df_row)
        row_shap = shap_values[0]
        row_vals = df_row.iloc[0]

        # c. Pair each feature with its SHAP contribution and its raw value.
        factors = [
            {
                "feature": feat,
                "shap_value": float(row_shap[i]),
                "feature_value": float(row_vals[feat]),
            }
            for i, feat in enumerate(self.feature_columns)
        ]

        # d. Sort by magnitude of contribution, most influential first.
        factors.sort(key=lambda f: abs(f["shap_value"]), reverse=True)

        # e. base_value (expected_value) may be a scalar or a 1-element array.
        base = self.explainer.expected_value
        try:
            base_value = float(base[0])
        except (TypeError, IndexError):
            base_value = float(base)

        return {
            "shap_values": factors,
            "top_factors": factors[:5],
            "base_value": base_value,
        }


# Module-level singleton: build the explainer once per process.
_explainer_instance = None


def get_explainer() -> SHAPExplainer:
    """Lazily build (once) and return the shared SHAPExplainer."""
    global _explainer_instance
    if _explainer_instance is None:
        _explainer_instance = SHAPExplainer(get_model())
    return _explainer_instance
