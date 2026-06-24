"""add unique constraint on portfolio_snapshots.threshold

Enables idempotent upserts (INSERT ... ON CONFLICT (threshold) DO UPDATE)
from the Phase 2 backtest pre-compute script.

Revision ID: a1c2e3f40512
Revises: 1be5fbf106ec
Create Date: 2026-06-25 00:00:00.000000

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = 'a1c2e3f40512'
down_revision = '1be5fbf106ec'
branch_labels = None
depends_on = None


def upgrade():
    op.create_unique_constraint(
        'uq_portfolio_snapshots_threshold', 'portfolio_snapshots', ['threshold']
    )


def downgrade():
    op.drop_constraint(
        'uq_portfolio_snapshots_threshold', 'portfolio_snapshots', type_='unique'
    )
