"""Risk-band to interest-rate mapping for approved applicants (Phase 1)."""
from app.models.scoring import get_model

# Placeholder base rate: RBI repo rate + spread. Risk premiums are added on top.
BASE_RATE = 8.0


def assign_rate(default_probability: float):
    """Map a default probability to a risk-based interest rate.

    Returns None for rejected applicants (probability at/above the model's
    optimal threshold). Otherwise returns BASE_RATE + a risk premium, rounded
    to 2 decimal places.
    """
    threshold = get_model().threshold

    if default_probability >= threshold:
        return None  # Rejected — no rate assigned.

    if default_probability < 0.05:
        premium = 2.0    # Tier 1 — excellent
    elif default_probability < 0.10:
        premium = 4.0    # Tier 2 — good
    elif default_probability < 0.15:
        premium = 6.5    # Tier 3 — fair
    elif default_probability < 0.20:
        premium = 9.0    # Tier 4 — marginal
    else:
        premium = 11.0   # Tier 5 — high risk, borderline (< threshold)

    return round(BASE_RATE + premium, 2)
