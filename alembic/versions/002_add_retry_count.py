"""Add retry_count column to reports table.

Revision ID: 002_add_retry_count
Revises: 001_add_fund_type
Create Date: 2026-03-18
"""

from alembic import op
import sqlalchemy as sa

revision = "002_add_retry_count"
down_revision = "001_add_fund_type"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    result = conn.execute(
        sa.text(
            "SELECT count(*) FROM information_schema.columns "
            "WHERE table_name = 'reports' AND column_name = 'retry_count'"
        )
    )
    if result.scalar() == 0:
        op.add_column(
            "reports",
            sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        )


def downgrade() -> None:
    op.drop_column("reports", "retry_count")
