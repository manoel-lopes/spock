"""Add fund_type column to funds table.

Revision ID: 001_add_fund_type
Revises:
Create Date: 2026-03-11
"""

from alembic import op
import sqlalchemy as sa

revision = "001_add_fund_type"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "funds",
        sa.Column("fund_type", sa.String(), nullable=False, server_default="equity"),
    )


def downgrade() -> None:
    op.drop_column("funds", "fund_type")
