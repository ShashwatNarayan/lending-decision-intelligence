"""SQLAlchemy ORM models for the Lending Decision Intelligence Platform.

Three tables: loan_applications (the 133k records + computed decision columns),
portfolio_snapshots (threshold simulation results), and query_log (Phase 5 NL audit).
"""
from datetime import datetime

from app.database import db


class LoanApplication(db.Model):
    __tablename__ = "loan_applications"

    id = db.Column(db.Integer, primary_key=True)

    # Raw numeric features
    loan_amnt = db.Column(db.Numeric)
    int_rate = db.Column(db.Numeric)
    annual_inc = db.Column(db.Numeric)
    dti = db.Column(db.Numeric)
    emp_length = db.Column(db.Numeric)
    revol_bal = db.Column(db.Numeric)
    revol_util = db.Column(db.Numeric)

    # Integer-coded features
    mort_acc = db.Column(db.Integer)
    int_rate_tier = db.Column(db.Integer)
    loan_amnt_tier = db.Column(db.Integer)
    grade_encoded = db.Column(db.Integer)

    # Engineered numeric features
    credit_history_years = db.Column(db.Numeric)
    loan_to_income = db.Column(db.Numeric)
    fico_score = db.Column(db.Numeric)
    installment_to_income = db.Column(db.Numeric)
    open_acc_ratio = db.Column(db.Numeric)

    # Boolean flags
    has_delinquency = db.Column(db.Boolean)
    has_pub_rec = db.Column(db.Boolean)
    high_inq_flag = db.Column(db.Boolean)
    is_short_term = db.Column(db.Boolean)

    # One-hot: home ownership
    home_OTHER = db.Column(db.Boolean)
    home_OWN = db.Column(db.Boolean)
    home_RENT = db.Column(db.Boolean)

    # One-hot: loan purpose
    purpose_credit_card = db.Column(db.Boolean)
    purpose_debt_consolidation = db.Column(db.Boolean)
    purpose_home_improvement = db.Column(db.Boolean)
    purpose_major_purchase = db.Column(db.Boolean)
    purpose_medical = db.Column(db.Boolean)
    purpose_other = db.Column(db.Boolean)
    purpose_small_business = db.Column(db.Boolean)

    # Ground truth: 1 = default, 0 = no default
    target = db.Column(db.SmallInteger)

    # Computed in Phase 1+ (nullable until then)
    default_probability = db.Column(db.Numeric(6, 4), nullable=True)
    decision = db.Column(db.String(10), nullable=True)  # 'APPROVE' or 'REJECT'
    assigned_rate = db.Column(db.Numeric(6, 3), nullable=True)
    decision_reasons = db.Column(db.Text, nullable=True)  # JSON string

    loaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.Index("ix_loan_applications_decision", "decision"),
        db.Index("ix_loan_applications_target", "target"),
    )


class PortfolioSnapshot(db.Model):
    __tablename__ = "portfolio_snapshots"

    id = db.Column(db.Integer, primary_key=True)
    threshold = db.Column(db.Numeric(6, 4))
    approvals = db.Column(db.Integer)
    rejections = db.Column(db.Integer)
    expected_defaults = db.Column(db.Integer)
    net_portfolio_value = db.Column(db.Numeric(16, 2))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class QueryLog(db.Model):
    __tablename__ = "query_log"

    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.Text)
    generated_sql = db.Column(db.Text, nullable=True)
    was_blocked = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
