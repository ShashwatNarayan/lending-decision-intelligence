"""XGBoost model loading and default-probability prediction (Phase 1)."""
import os
import pickle

ARTIFACTS_DIR = os.path.join(
    os.path.dirname(__file__), "..", "..", "model", "artifacts"
)

_ARTIFACTS = ("xgboost_model", "scaler", "feature_columns", "optimal_threshold")


def load_model():
    """Load xgboost_model.pkl, scaler.pkl, feature_columns.pkl, and
    optimal_threshold.pkl from model/artifacts/ and return them as a dict."""
    artifacts = {}
    for name in _ARTIFACTS:
        path = os.path.join(ARTIFACTS_DIR, f"{name}.pkl")
        with open(path, "rb") as f:
            artifacts[name] = pickle.load(f)
    return artifacts


def predict(features_dict):
    """Score a single applicant from a {feature_name: value} dict.

    Returns default_probability, decision, and threshold_used. Real scaling +
    model inference is wired up in Phase 1.
    """
    # TODO (Phase 1): order features per feature_columns, scale, run model,
    # compare against optimal_threshold.
    return {
        "default_probability": None,
        "decision": None,
        "threshold_used": None,
    }
