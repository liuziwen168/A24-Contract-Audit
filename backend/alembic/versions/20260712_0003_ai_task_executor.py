"""Add AI task execution metadata.

Revision ID: 20260712_0003
Revises: 20260712_0002
Create Date: 2026-07-12
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

revision = "20260712_0003"
down_revision = "20260712_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("review_record", sa.Column("ai_started_at", mysql.DATETIME(fsp=3), nullable=True))
    op.add_column(
        "review_record",
        sa.Column(
            "ai_attempt_count", mysql.INTEGER(unsigned=True), nullable=False, server_default="0"
        ),
    )
    op.create_index(
        "idx_review_executor", "review_record", ["status", "review_stage", "ai_started_at"]
    )


def downgrade() -> None:
    op.drop_index("idx_review_executor", table_name="review_record")
    op.drop_column("review_record", "ai_attempt_count")
    op.drop_column("review_record", "ai_started_at")
