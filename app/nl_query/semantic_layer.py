"""Semantic layer for the NL->SQL query interface (Phase 4).

This module is the *only* description of the database that the LLM ever sees.
It is deliberately written in plain English so Gemini can map a risk officer's
question onto real columns without ever being shown the live schema or any
internal/audit tables. Keep it accurate: every column named here exists in
``loan_applications`` (see ``app/models/db_models.py``).
"""

# Tables the NL layer is allowed to read. query_log is intentionally absent —
# it is an internal audit table and must never be exposed to a generated query.
ALLOWED_TABLES = ["loan_applications", "portfolio_snapshots"]

# Hard cap on rows returned to the user, enforced by the router when fetching.
MAX_RESULT_ROWS = 500


SCHEMA_DESCRIPTION = """
You are querying a PostgreSQL database for a credit-risk lending platform.
It contains ~133,000 LendingClub-style loan records. Each row in the main
table is ONE loan applicant who has already been scored by an XGBoost
probability-of-default model and put through a cost-sensitive decision engine.

=====================================================================
TABLE: loan_applications  (the main table — query this for almost everything)
Each row is one loan applicant. Columns a risk officer may ask about:

  Loan & income
  - loan_amnt              Requested loan amount (numeric, in the loan currency).
  - int_rate               Original interest rate on the loan (percent, e.g. 13.5).
  - annual_inc             Applicant's self-reported annual income (numeric).
  - loan_to_income         Loan amount divided by annual income (ratio, e.g. 0.32).
  - installment_to_income  Monthly installment divided by income (ratio).

  Credit profile
  - dti                    Debt-to-income ratio as a percentage (e.g. 18.4 = 18.4%).
  - fico_score             Applicant FICO credit score (e.g. 680, 715).
  - credit_history_years   Length of credit history in years (numeric).
  - revol_util             Revolving credit utilization, percent (e.g. 45.2).
  - revol_bal              Revolving balance amount (numeric).
  - emp_length             Employment length in years (numeric, 0-10).
  - mort_acc               Number of mortgage accounts (integer).
  - open_acc_ratio         Ratio of open credit accounts (numeric).
  - has_delinquency        TRUE if the applicant has a past delinquency.
  - has_pub_rec            TRUE if the applicant has a public record (e.g. bankruptcy).
  - high_inq_flag          TRUE if the applicant has many recent credit inquiries.

  Risk grade & loan attributes
  - grade_encoded          Risk grade as an integer: 0=A (best) ... 6=G (worst).
                           So grade A = 0, B = 1, C = 2, D = 3, E = 4, F = 5, G = 6.
  - int_rate_tier          Interest-rate band as an integer 0-4.
  - loan_amnt_tier         Loan-amount band as an integer 0-3.
  - is_short_term          TRUE for short-term (36-month) loans, FALSE for long-term.

  Loan purpose (one-hot booleans — exactly one is typically TRUE per row):
  - purpose_credit_card, purpose_debt_consolidation, purpose_home_improvement,
    purpose_major_purchase, purpose_medical, purpose_other,
    purpose_small_business.

  Home ownership (one-hot booleans):
  - home_OWN, home_RENT, home_OTHER.

  Ground truth
  - target                 1 = the applicant ACTUALLY defaulted, 0 = did NOT default.

  Model & decision outputs
  - default_probability    Model-estimated probability of default, a float 0-1.
  - decision               The engine's decision: text 'APPROVE' or 'REJECT'.
  - assigned_rate          Interest rate assigned to APPROVED applicants (percent).
                           This is NULL for rejected applicants.
  - decision_reasons       A JSON array of plain-English reason strings explaining
                           the decision (stored as text).

=====================================================================
TABLE: portfolio_snapshots  (threshold-level aggregates — use only for
questions about portfolio outcomes at different decision thresholds)
  - threshold              The P(default) cutoff that was simulated (float).
  - approvals              Count of approved loans at that threshold.
  - rejections             Count of rejected loans at that threshold.
  - expected_defaults      Expected defaults among the approved.
  - net_portfolio_value    Net portfolio value (revenue minus loss) at that threshold.

=====================================================================
RULES (non-negotiable):
- The table query_log exists internally but MUST NEVER be queried. It is off-limits.
- Only read from loan_applications and portfolio_snapshots.
- Only SELECT statements are permitted. Never write INSERT, UPDATE, DELETE,
  DROP, ALTER, TRUNCATE, CREATE, GRANT, or any other DDL/DML statement.
- 'approved applicants' means decision = 'APPROVE'; 'rejected' means
  decision = 'REJECT'. 'default rate' means AVG(target) or
  COUNT(target=1)/COUNT(*). A FICO 'above 700' means fico_score > 700.
""".strip()
