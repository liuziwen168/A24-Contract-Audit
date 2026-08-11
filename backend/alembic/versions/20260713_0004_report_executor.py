"""Add report task execution and file metadata.

Revision ID: 20260713_0004
Revises: 20260712_0003
Create Date: 2026-07-13
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

revision = "20260713_0004"
down_revision = "20260712_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("report", sa.Column("started_at", mysql.DATETIME(fsp=3), nullable=True))
    op.add_column(
        "report",
        sa.Column(
            "attempt_count", mysql.INTEGER(unsigned=True), nullable=False, server_default="0"
        ),
    )
    op.add_column("report", sa.Column("error_code", sa.String(32), nullable=True))
    op.add_column("report", sa.Column("error_message", sa.String(500), nullable=True))
    op.add_column("report", sa.Column("file_size", mysql.BIGINT(unsigned=True), nullable=True))
    op.add_column("report", sa.Column("sha256", sa.String(64), nullable=True))
    op.create_index("idx_report_executor", "report", ["status", "started_at"])


def downgrade() -> None:
    op.drop_index("idx_report_executor", table_name="report")
    op.drop_column("report", "sha256")
    op.drop_column("report", "file_size")
    op.drop_column("report", "error_message")
    op.drop_column("report", "error_code")
    op.drop_column("report", "attempt_count")
    op.drop_column("report", "started_at")
