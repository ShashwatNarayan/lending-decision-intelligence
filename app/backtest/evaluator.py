"""₹-based portfolio backtesting over all scored applications (Phase 2).

Replays every loan application against a candidate approval threshold and
computes the net ₹ portfolio value, so the cost of a threshold choice can be
read in money rather than in classifier metrics.

Business model encoded here:
  - APPROVE + no default  → earn interest revenue
        revenue = loan_amnt × (assigned_rate / 100) × term_years × 0.5
        term_years = 3.0 (is_short_term=1) or 5.0 (is_short_term=0)
        the 0.5 factor approximates principal amortising over the term
  - APPROVE + default     → lose 60% of principal (Loss Given Default)
        loss = loan_amnt × 0.60
  - REJECT (either way)   → net 0
"""
import numpy as np
from sqlalchemy import text

from app.database import db
from app.decision.pricing import BASE_RATE, assign_rate

LGD = 0.60                     # Loss Given Default
SHORT_TERM_YEARS = 3.0
LONG_TERM_YEARS = 5.0
REVENUE_FACTOR = 0.5           # crude amortisation adjustment
# assign_rate() returns None at/above the model threshold (those are normally
# rejected). When the slider approves them anyway, price them at the top band.
TOP_TIER_RATE = BASE_RATE + 11.0


class PortfolioEvaluator:
    """Evaluates net ₹ portfolio value at arbitrary approval thresholds."""

    def __init__(self):
        self._loaded = False

    def _load(self):
        """Fetch all scored rows once and pre-compute per-row economics.

        Rates and per-row revenue/loss do not depend on the threshold — only
        the approve/reject split does — so they are computed a single time and
        reused across every threshold evaluation.
        """
        if self._loaded:
            return

        rows = db.session.execute(
            text(
                "SELECT id, loan_amnt, is_short_term, default_probability, "
                "target, assigned_rate FROM loan_applications"
            )
        ).fetchall()

        self.loan_amnt = np.array([float(r.loan_amnt) for r in rows])
        is_short = np.array([1 if r.is_short_term else 0 for r in rows])
        self.prob = np.array([float(r.default_probability) for r in rows])
        self.target = np.array([int(r.target) for r in rows])

        term_years = np.where(is_short == 1, SHORT_TERM_YEARS, LONG_TERM_YEARS)

        # Reuse the Phase 1 pricing bands. assign_rate() returns None for
        # probabilities at/above the model threshold; those rows are priced at
        # the top tier so they still earn revenue when a high slider threshold
        # approves them.
        rates = np.array(
            [
                (assign_rate(p) if assign_rate(p) is not None else TOP_TIER_RATE)
                for p in self.prob
            ]
        )
        self.rate = rates

        self.revenue_if_repaid = (
            self.loan_amnt * (rates / 100.0) * term_years * REVENUE_FACTOR
        )
        self.loss_if_default = self.loan_amnt * LGD

        self._loaded = True

    def evaluate_at_threshold(self, threshold: float) -> dict:
        """Replay all applications at one threshold and return ₹ + confusion metrics."""
        self._load()

        # Decision is recomputed from probability — never read from the stored
        # decision column — so the threshold can be varied freely.
        approved = self.prob < threshold
        rejected = ~approved
        defaulted = self.target == 1
        repaid = self.target == 0

        tp = approved & repaid       # approved, did not default — correct approval
        fp = approved & defaulted    # approved, defaulted — costly mistake
        tn = rejected & defaulted    # rejected, would have defaulted — correct reject
        fn = rejected & repaid       # rejected, would have repaid — lost revenue

        approvals = int(approved.sum())
        rejections = int(rejected.sum())
        total = approvals + rejections

        total_revenue = float(self.revenue_if_repaid[tp].sum())
        total_losses = float(self.loss_if_default[fp].sum())
        net = total_revenue - total_losses

        approval_rate = (approvals / total * 100.0) if total else 0.0
        default_rate_among_approved = (
            int(fp.sum()) / approvals * 100.0 if approvals else 0.0
        )
        mean_assigned_rate = (
            float(self.rate[approved].mean()) if approvals else 0.0
        )

        return {
            "threshold": round(float(threshold), 4),
            "approvals": approvals,
            "rejections": rejections,
            "true_positives": int(tp.sum()),
            "false_positives": int(fp.sum()),
            "true_negatives": int(tn.sum()),
            "false_negatives": int(fn.sum()),
            "total_revenue": round(total_revenue, 2),
            "total_losses": round(total_losses, 2),
            "net_portfolio_value": round(net, 2),
            "approval_rate": round(approval_rate, 2),
            "default_rate_among_approved": round(default_rate_among_approved, 2),
            "mean_assigned_rate": round(mean_assigned_rate, 2),
        }

    def evaluate_threshold_range(self, start=0.10, stop=0.50, step=0.01) -> list:
        """Evaluate every threshold in [start, stop] and return results ascending."""
        results = []
        t = start
        while t <= stop + 1e-9:
            th = round(t, 2)
            results.append(self.evaluate_at_threshold(th))
            print(f"Evaluated threshold {th:.2f}...")
            t += step
        results.sort(key=lambda r: r["threshold"])
        return results

    def find_optimal_threshold(self) -> dict:
        """Return the threshold result with the highest net portfolio value."""
        results = self.evaluate_threshold_range()
        return max(results, key=lambda r: r["net_portfolio_value"])


# Module-level singleton so the 133k-row load happens once per process.
_evaluator_instance = None


def get_evaluator() -> PortfolioEvaluator:
    """Lazily build (once) and return the shared PortfolioEvaluator."""
    global _evaluator_instance
    if _evaluator_instance is None:
        _evaluator_instance = PortfolioEvaluator()
    return _evaluator_instance
