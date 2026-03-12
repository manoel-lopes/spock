"""Add fund_type column to funds table (no-op if already exists from initial schema).

Revision ID: 001_add_fund_type
Revises: 000_initial_schema
Create Date: 2026-03-11
"""

from alembic import op
import sqlalchemy as sa

revision = "001_add_fund_type"
down_revision = "000_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    result = conn.execute(
        sa.text(
            "SELECT count(*) FROM information_schema.columns "
            "WHERE table_name = 'funds' AND column_name = 'fund_type'"
        )
    )
    if result.scalar() == 0:
        op.add_column(
            "funds",
            sa.Column("fund_type", sa.String(), nullable=False, server_default="equity"),
        )


def downgrade() -> None:
    op.drop_column("funds", "fund_type")
