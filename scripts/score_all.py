"""One-time batch scorer: score every unscored loan application and write the
results (default_probability, decision, assigned_rate) back to the database.

SHAP is intentionally NOT used here — it is far too slow for 133k rows and is
only needed for per-request explanations. This script computes probability,
decision, and risk-based rate only.

Run: python scripts/score_all.py
"""
import os
import sys
import time

import pandas as pd

# Make the project root importable when run as a script.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()

import psycopg2
from psycopg2.extras import execute_values
from sqlalchemy.exc import OperationalError

from app import create_app
from app.database import db
from app.decision.pricing import assign_rate
from app.models.db_models import LoanApplication
from app.models.scoring import get_model

BATCH_SIZE = 2000
PROGRESS_EVERY = 10000
MAX_RETRIES = 5

# A single UPDATE ... FROM (VALUES ...) writes the whole batch in one round
# trip. psycopg2.executemany (what bulk_update_mappings uses for keyed UPDATEs)
# instead sends one UPDATE per row — ~500 network round trips per batch — which
# crawls and exhausts the Neon connection. This is the fast, robust path.
_UPDATE_SQL = """
UPDATE loan_applications AS t SET
    default_probability = v.dp::numeric,
    decision            = v.decn,
    assigned_rate       = v.ar::numeric
FROM (VALUES %s) AS v(id, dp, decn, ar)
WHERE t.id = v.id::integer
"""


def _commit_batch(values):
    """Write one batch via execute_values, retrying on dropped connections.

    Neon's free tier intermittently closes connections; on OperationalError we
    roll back (invalidating the dead connection) and retry — pool_pre_ping hands
    us a fresh connection on the next attempt.
    """
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            raw = db.session.connection().connection  # psycopg2 connection
            with raw.cursor() as cur:
                execute_values(
                    cur, _UPDATE_SQL, values,
                    template="(%s,%s,%s,%s)", page_size=len(values),
                )
            db.session.commit()
            return
        except (OperationalError, psycopg2.OperationalError):
            db.session.rollback()
            if attempt == MAX_RETRIES:
                raise
            time.sleep(2 * attempt)


def main():
    app = create_app()
    with app.app_context():
        model = get_model()
        feature_columns = model.feature_columns

        # Read id + the 30 feature columns as plain tuples up front. This avoids
        # holding ORM objects in the identity map: after each commit() ORM rows
        # are expired and any later attribute access re-SELECTs per row, which
        # both crawls and exhausts the Neon connection. Plain tuples sidestep
        # that entirely — the scoring loop never touches the session.
        select_cols = [LoanApplication.id] + [
            getattr(LoanApplication, c) for c in feature_columns
        ]
        rows = (
            db.session.query(*select_cols)
            .filter(LoanApplication.default_probability.is_(None))
            .all()
        )
        total = len(rows)
        print(f"Loaded {total} unscored applications.")
        if total == 0:
            print("Nothing to score.")
            return

        start = time.time()
        approved = 0
        rejected = 0
        prob_sum = 0.0
        scored = 0
        threshold = model.threshold

        # Process in batches. Within a batch the model is run on the whole batch
        # in one vectorized predict_proba() call — scoring 133k rows one-at-a-time
        # builds 133k DataFrames and is ~100x slower. The DB write-back is also
        # batched (one UPDATE ... FROM VALUES per batch).
        for offset in range(0, total, BATCH_SIZE):
            chunk = rows[offset:offset + BATCH_SIZE]
            ids = [r[0] for r in chunk]

            # Build a DataFrame of the chunk in exact feature order.
            df = pd.DataFrame(
                [list(r[1:]) for r in chunk], columns=feature_columns
            ).fillna(0.0).astype(float)

            probs = model.model.predict_proba(df)[:, 1]

            values = []
            for row_id, prob in zip(ids, probs):
                prob = round(float(prob), 4)
                decision = "APPROVE" if prob < threshold else "REJECT"
                rate = assign_rate(prob) if decision == "APPROVE" else None

                if decision == "APPROVE":
                    approved += 1
                else:
                    rejected += 1
                prob_sum += prob

                values.append((row_id, prob, decision, rate))

            _commit_batch(values)

            prev = scored
            scored += len(chunk)
            if scored // PROGRESS_EVERY > prev // PROGRESS_EVERY:
                print(f"Scored {scored}/{total}...")

        elapsed = time.time() - start
        mean_prob = prob_sum / scored if scored else 0.0

        print("\n===== Batch scoring complete =====")
        print(f"Approved:        {approved}")
        print(f"Rejected:        {rejected}")
        print(f"Mean probability: {mean_prob:.4f}")
        print(f"Time taken:      {elapsed:.1f}s")


if __name__ == "__main__":
    main()
