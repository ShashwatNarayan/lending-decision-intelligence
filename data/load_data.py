"""One-time loader for the loan dataset.

Reads data/stage2_features.csv (133,018 rows x 31 columns: the 30 model features
plus `target`) and inserts each record into the `loan_applications` table in the
Neon PostgreSQL database. Idempotent: skips loading if the table already has rows.

Run once during Phase 0 setup, after migrations have created the schema:
    python data/load_data.py
"""
import os
import sys
import time

import pandas as pd
from dotenv import load_dotenv

# Make the project root importable when run as `python data/load_data.py`.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load .env before importing the app (config reads env vars at import time).
load_dotenv()

from app import create_app
from app.database import db
from app.models.db_models import LoanApplication

CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stage2_features.csv")
BATCH_SIZE = 5000

# Features stored as integers (the CSV encodes these as floats).
INT_COLS = ["mort_acc", "int_rate_tier", "loan_amnt_tier", "grade_encoded"]

# Features stored as booleans (some encoded as 0/1 ints in the CSV).
BOOL_COLS = [
    "has_delinquency", "has_pub_rec", "high_inq_flag", "is_short_term",
    "home_OTHER", "home_OWN", "home_RENT",
    "purpose_credit_card", "purpose_debt_consolidation", "purpose_home_improvement",
    "purpose_major_purchase", "purpose_medical", "purpose_other", "purpose_small_business",
]


def main():
    """Load stage2_features.csv into the loan_applications table."""
    app = create_app()
    with app.app_context():
        # Idempotency guard.
        existing = db.session.query(LoanApplication).count()
        if existing > 0:
            print(f"Data already loaded ({existing} rows). Skipping.")
            return

        df = pd.read_csv(CSV_PATH)
        default_rate = df["target"].mean()
        print(f"CSV loaded: shape={df.shape}, default rate={default_rate:.2%}")

        # Coerce dtypes to match the SQLAlchemy column types.
        for col in INT_COLS:
            df[col] = df[col].astype(int)
        for col in BOOL_COLS:
            df[col] = df[col].astype(bool)
        df["target"] = df["target"].astype(int)

        records = df.to_dict(orient="records")

        # Phase-1 computed columns are NULL at load time.
        for r in records:
            r["default_probability"] = None
            r["decision"] = None
            r["assigned_rate"] = None
            r["decision_reasons"] = None

        total = len(records)
        print(f"Inserting {total} rows in batches of {BATCH_SIZE}...")
        start = time.time()
        inserted = 0
        for i in range(0, total, BATCH_SIZE):
            batch = records[i:i + BATCH_SIZE]
            db.session.bulk_insert_mappings(LoanApplication, batch)
            inserted += len(batch)
            print(f"  batch {i // BATCH_SIZE + 1}: {inserted}/{total} rows staged")

        db.session.commit()
        elapsed = time.time() - start
        print(f"Done. Inserted {inserted} rows in {elapsed:.1f}s.")


if __name__ == "__main__":
    main()
