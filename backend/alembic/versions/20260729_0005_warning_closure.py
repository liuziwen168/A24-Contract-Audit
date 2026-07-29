"""Add risk warning closure records.

Revision ID: 20260729_0005
Revises: 20260713_0004
Create Date: 2026-07-29
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

revision = "20260729_0005"
down_revision = "20260713_0004"
branch_labels = None
depends_on = None

id_type = mysql.BIGINT(unsigned=True)
time_type = mysql.DATETIME(fsp=3)


def audit_columns():
    return [
        sa.Column("created_at", time_type, nullable=False),
        sa.Column("updated_at", time_type, nullable=False),
    ]


def upgrade() -> None:
    op.add_column(
        "risk_rule",
        sa.Column("warning_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column("risk_rule", sa.Column("warning_due_hours", mysql.INTEGER(unsigned=True)))
    op.create_table(
        "risk_warning",
        sa.Column("id", id_type, primary_key=True, autoincrement=True),
        sa.Column("warning_key", sa.String(128), nullable=False),
        sa.Column("source_review_id", id_type, sa.ForeignKey("review_record.id"), nullable=False),
        sa.Column("source_risk_id", id_type, sa.ForeignKey("risk_record.id"), nullable=False),
        sa.Column("contract_id", id_type, sa.ForeignKey("contract.id"), nullable=False),
        sa.Column("owner_id", id_type, sa.ForeignKey("user.id"), nullable=False),
        sa.Column("warning_type", sa.String(40), nullable=False, server_default="riskRuleHit"),
        sa.Column("warning_level", sa.String(10), nullable=False),
        sa.Column("warning_status", sa.String(20), nullable=False, server_default="pendingLegal"),
        sa.Column("source_snapshot", mysql.JSON, nullable=False),
        sa.Column("due_at", time_type),
        sa.Column("acknowledged_at", time_type),
        sa.Column("remediation_review_id", id_type, sa.ForeignKey("review_record.id")),
        sa.Column("closed_at", time_type),
        *audit_columns(),
        sa.UniqueConstraint("warning_key", name="uk_warning_key"),
    )
    op.create_index(
        "idx_warning_owner_status_due", "risk_warning", ["owner_id", "warning_status", "due_at"]
    )
    op.create_index("idx_warning_contract_status", "risk_warning", ["contract_id", "warning_status"])
    op.create_index(
        "idx_warning_source_review_status", "risk_warning", ["source_review_id", "warning_status"]
    )
    op.create_index("idx_warning_remediation_review", "risk_warning", ["remediation_review_id"])
    op.create_table(
        "warning_action",
        sa.Column("id", id_type, primary_key=True, autoincrement=True),
        sa.Column("warning_id", id_type, sa.ForeignKey("risk_warning.id"), nullable=False),
        sa.Column("action", sa.String(40), nullable=False),
        sa.Column("from_status", sa.String(20)),
        sa.Column("to_status", sa.String(20)),
        sa.Column("actor_id", id_type, sa.ForeignKey("user.id")),
        sa.Column("actor_role", sa.String(20)),
        sa.Column("comment", sa.Text),
        sa.Column("remediation_review_id", id_type, sa.ForeignKey("review_record.id")),
        sa.Column("detail_json", mysql.JSON),
        *audit_columns(),
    )
    op.create_index(
        "idx_warning_action_warning_created", "warning_action", ["warning_id", "created_at"]
    )
    op.create_index(
        "idx_warning_action_actor_created", "warning_action", ["actor_id", "created_at"]
    )
    op.add_column(
        "review_record",
        sa.Column(
            "source_warning_id",
            id_type,
            sa.ForeignKey("risk_warning.id", name="fk_review_source_warning"),
        ),
    )
    op.create_index("idx_review_source_warning", "review_record", ["source_warning_id"])


def downgrade() -> None:
    op.drop_index("idx_review_source_warning", table_name="review_record")
    op.drop_column("review_record", "source_warning_id")
    op.drop_index("idx_warning_action_actor_created", table_name="warning_action")
    op.drop_index("idx_warning_action_warning_created", table_name="warning_action")
    op.drop_table("warning_action")
    op.drop_index("idx_warning_remediation_review", table_name="risk_warning")
    op.drop_index("idx_warning_source_review_status", table_name="risk_warning")
    op.drop_index("idx_warning_contract_status", table_name="risk_warning")
    op.drop_index("idx_warning_owner_status_due", table_name="risk_warning")
    op.drop_table("risk_warning")
    op.drop_column("risk_rule", "warning_due_hours")
    op.drop_column("risk_rule", "warning_enabled")
