"""One-time loader for the loan dataset.

Reads data/stage2_features.csv (133,018 rows x 31 columns: the 30 model features
plus `target`) and inserts each record into the `loan_applications` table in the
Neon PostgreSQL database. Run once during Phase 0 setup, after migrations create
the table. No real DB logic yet — this is a Phase 0 skeleton.
"""
import os
import sys

import pandas as pd

from app import create_app, db

CSV_PATH = os.path.join(os.path.dirname(__file__), "stage2_features.csv")


def main():
    """Load stage2_features.csv into the loan_applications table."""
    # TODO (Phase 0): read CSV with pandas, map columns to the loan_applications
    # model, and bulk-insert within an app context.
    pass


if __name__ == "__main__":
    main()
