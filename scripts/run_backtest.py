"""Pre-compute the ₹ portfolio backtest across thresholds 0.10–0.50 and store
one snapshot per threshold in portfolio_snapshots.

Idempotent: re-running upserts (INSERT ... ON CONFLICT (threshold) DO UPDATE),
so it can be run repeatedly without duplicating rows.

Run: python scripts/run_backtest.py
"""
import os
import sys

# UTF-8 stdout so the ₹ symbol prints on Windows consoles (cp1252 default).
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Make the project root importable when run as a script.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()

from sqlalchemy import text

from app import create_app
from app.backtest.evaluator import PortfolioEvaluator
from app.database import db

_UPSERT = text(
    """
    INSERT INTO portfolio_snapshots
        (threshold, approvals, rejections, expected_defaults,
         net_portfolio_value, created_at)
    VALUES (:threshold, :approvals, :rejections, :expected_defaults, :net, NOW())
    ON CONFLICT (threshold) DO UPDATE SET
        approvals           = EXCLUDED.approvals,
        rejections          = EXCLUDED.rejections,
        expected_defaults   = EXCLUDED.expected_defaults,
        net_portfolio_value = EXCLUDED.net_portfolio_value,
        created_at          = NOW()
    """
)


def main():
    app = create_app()
    with app.app_context():
        evaluator = PortfolioEvaluator()
        results = evaluator.evaluate_threshold_range(start=0.10, stop=0.50, step=0.01)

        for r in results:
            db.session.execute(
                _UPSERT,
                {
                    "threshold": r["threshold"],
                    "approvals": r["approvals"],
                    "rejections": r["rejections"],
                    "expected_defaults": r["false_positives"],
                    "net": r["net_portfolio_value"],
                },
            )
        db.session.commit()

        optimal = max(results, key=lambda r: r["net_portfolio_value"])

        # Show every 5th threshold, plus the optimal row if it isn't one of them.
        display_thresholds = {round(0.10 + 0.05 * i, 2) for i in range(9)}
        display_thresholds.add(optimal["threshold"])
        shown = [r for r in results if r["threshold"] in display_thresholds]

        print("\n===== Backtest summary (stored 0.10–0.50) =====")
        print(f"{'':2}{'Threshold':>10}{'Approvals':>12}"
              f"{'Net ₹ Value':>20}{'Approval %':>13}")
        print("-" * 57)
        for r in shown:
            marker = "→ " if r["threshold"] == optimal["threshold"] else "  "
            print(
                f"{marker}{r['threshold']:>10.2f}{r['approvals']:>12,}"
                f"{r['net_portfolio_value']:>20,.2f}{r['approval_rate']:>12.2f}%"
            )

        print("-" * 57)
        print(
            f"Optimal threshold: {optimal['threshold']:.2f}  |  "
            f"net ₹{optimal['net_portfolio_value']:,.2f}  |  "
            f"approval {optimal['approval_rate']:.2f}%"
        )


if __name__ == "__main__":
    main()
