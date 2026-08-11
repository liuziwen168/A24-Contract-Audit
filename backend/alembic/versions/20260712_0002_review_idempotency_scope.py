"""Separate review idempotency from AI request identifiers.

Revision ID: 20260712_0002
Revises: 20260712_0001
Create Date: 2026-07-12
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

revision = "20260712_0002"
down_revision = "20260712_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "review_record",
        sa.Column("idempotency_user_id", mysql.BIGINT(unsigned=True), nullable=True),
    )
    op.add_column("review_record", sa.Column("idempotency_key", sa.String(255), nullable=True))
    op.execute(
        "UPDATE review_record r JOIN contract c ON c.id = r.contract_id SET r.idempotency_user_id = c.owner_id, r.idempotency_key = CONCAT('legacy:', r.request_id)"
    )
    op.alter_column(
        "review_record",
        "idempotency_user_id",
        existing_type=mysql.BIGINT(unsigned=True),
        nullable=False,
    )
    op.alter_column(
        "review_record", "idempotency_key", existing_type=sa.String(255), nullable=False
    )
    op.create_foreign_key(
        "fk_review_idempotency_user", "review_record", "user", ["idempotency_user_id"], ["id"]
    )
    op.create_unique_constraint(
        "uk_review_user_idempotency", "review_record", ["idempotency_user_id", "idempotency_key"]
    )


def downgrade() -> None:
    op.drop_constraint("fk_review_idempotency_user", "review_record", type_="foreignkey")
    op.drop_constraint("uk_review_user_idempotency", "review_record", type_="unique")
    op.drop_column("review_record", "idempotency_key")
    op.drop_column("review_record", "idempotency_user_id")
