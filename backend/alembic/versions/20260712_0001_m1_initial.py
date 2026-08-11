"""M1 initial schema.

Revision ID: 20260712_0001
Revises:
Create Date: 2026-07-12
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

revision = "20260712_0001"
down_revision = None
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
    op.create_table(
        "user",
        sa.Column("id", id_type, primary_key=True, autoincrement=True),
        sa.Column("username", sa.String(64), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", sa.String(20), nullable=False, server_default="user"),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("deleted_at", time_type),
        *audit_columns(),
        sa.UniqueConstraint("username", name="uk_user_username"),
    )
    op.create_index("idx_user_role_status", "user", ["role", "status"])
    op.create_table(
        "contract",
        sa.Column("id", id_type, primary_key=True, autoincrement=True),
        sa.Column("owner_id", id_type, sa.ForeignKey("user.id"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("contract_type", sa.String(40)),
        sa.Column("status", sa.String(20), nullable=False, server_default="uploaded"),
        sa.Column("deleted_at", time_type),
        *audit_columns(),
    )
    op.create_index("idx_contract_owner_status", "contract", ["owner_id", "status"])
    op.create_index("idx_contract_type", "contract", ["contract_type"])
    op.create_table(
        "contract_file",
        sa.Column("id", id_type, primary_key=True, autoincrement=True),
        sa.Column("contract_id", id_type, sa.ForeignKey("contract.id"), nullable=False),
        sa.Column("file_name", sa.String(255), nullable=False),
        sa.Column("storage_path", sa.String(500), nullable=False),
        sa.Column("file_type", sa.String(20), nullable=False),
        sa.Column("file_size", id_type, nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        *audit_columns(),
        sa.UniqueConstraint("contract_id", "sha256", name="uk_file_contract_sha"),
    )
    op.create_index("idx_file_contract", "contract_file", ["contract_id"])
    op.create_table(
        "standard_clause",
        sa.Column("id", id_type, primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("contract_type", sa.String(40), nullable=False),
        sa.Column("clause_type", sa.String(40), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("version", sa.String(32), nullable=False, server_default="v0.1"),
        *audit_columns(),
        sa.UniqueConstraint("contract_type", "clause_type", "name", name="uk_clause_type_name"),
    )
    op.create_table(
        "risk_rule",
        sa.Column("id", id_type, primary_key=True, autoincrement=True),
        sa.Column("rule_code", sa.String(40), nullable=False),
        sa.Column("risk_type", sa.String(40), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("risk_level", sa.String(10), nullable=False, server_default="medium"),
        sa.Column("rule_content", sa.Text, nullable=False),
        sa.Column("standard_clause_id", id_type, sa.ForeignKey("standard_clause.id")),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("version", sa.String(32), nullable=False, server_default="v0.1"),
        *audit_columns(),
        sa.UniqueConstraint("rule_code", name="uk_rule_code"),
    )
    op.create_index("idx_rule_type_status", "risk_rule", ["risk_type", "status"])
    op.create_table(
        "review_record",
        sa.Column("id", id_type, primary_key=True, autoincrement=True),
        sa.Column("contract_id", id_type, sa.ForeignKey("contract.id"), nullable=False),
        sa.Column("contract_file_id", id_type, sa.ForeignKey("contract_file.id"), nullable=False),
        sa.Column("file_sha256", sa.String(64), nullable=False),
        sa.Column("request_id", sa.String(64), nullable=False),
        sa.Column("review_mode", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("review_stage", sa.String(20), nullable=False, server_default="aiReview"),
        sa.Column("ai_result_json", mysql.JSON),
        sa.Column("ai_model_name", sa.String(100)),
        sa.Column("ai_model_version", sa.String(100)),
        sa.Column("prompt_version", sa.String(32)),
        sa.Column("ai_warnings", mysql.JSON, nullable=False),
        sa.Column("legal_opinion", sa.Text),
        sa.Column("risk_opinion", sa.Text),
        sa.Column("legal_reviewer_id", id_type, sa.ForeignKey("user.id")),
        sa.Column("risk_reviewer_id", id_type, sa.ForeignKey("user.id")),
        sa.Column("legal_reviewed_at", time_type),
        sa.Column("risk_reviewed_at", time_type),
        sa.Column("missing_clauses", mysql.JSON, nullable=False),
        sa.Column("overall_risk_level", sa.String(10)),
        sa.Column("overall_score", sa.Numeric(5, 2)),
        sa.Column("processing_time_ms", sa.Integer),
        sa.Column("error_code", sa.String(32)),
        sa.Column("error_message", sa.String(500)),
        *audit_columns(),
        sa.UniqueConstraint("request_id", name="uk_review_request"),
    )
    op.create_index("idx_review_contract_created", "review_record", ["contract_id", "created_at"])
    op.create_index("idx_review_file_status", "review_record", ["contract_file_id", "status"])
    op.create_table(
        "contract_element",
        sa.Column("id", id_type, primary_key=True, autoincrement=True),
        sa.Column("contract_id", id_type, sa.ForeignKey("contract.id"), nullable=False),
        sa.Column("review_id", id_type, sa.ForeignKey("review_record.id")),
        sa.Column("element_type", sa.String(40), nullable=False),
        sa.Column("element_name", sa.String(80), nullable=False),
        sa.Column("value_text", sa.Text, nullable=False),
        sa.Column("page", sa.Integer),
        sa.Column("paragraph_index", sa.Integer),
        sa.Column("confidence", sa.Numeric(5, 4)),
        sa.Column("source", sa.String(20), nullable=False, server_default="ai"),
        *audit_columns(),
    )
    op.create_index(
        "idx_element_contract_type", "contract_element", ["contract_id", "element_type"]
    )
    op.create_table(
        "risk_record",
        sa.Column("id", id_type, primary_key=True, autoincrement=True),
        sa.Column("review_id", id_type, sa.ForeignKey("review_record.id"), nullable=False),
        sa.Column("rule_id", id_type, sa.ForeignKey("risk_rule.id")),
        sa.Column("rule_snapshot", mysql.JSON),
        sa.Column("risk_type", sa.String(40), nullable=False),
        sa.Column("risk_name", sa.String(100), nullable=False),
        sa.Column("risk_level", sa.String(10), nullable=False),
        sa.Column("clause_text", sa.Text, nullable=False),
        sa.Column("page", sa.Integer),
        sa.Column("paragraph_index", sa.Integer),
        sa.Column("basis", sa.Text, nullable=False),
        sa.Column("suggestion", sa.Text, nullable=False),
        sa.Column("confidence", sa.Numeric(5, 4)),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        *audit_columns(),
    )
    op.create_index("idx_risk_review_level", "risk_record", ["review_id", "risk_level"])
    op.create_index("idx_risk_type", "risk_record", ["risk_type"])
    op.create_table(
        "review_revision",
        sa.Column("id", id_type, primary_key=True, autoincrement=True),
        sa.Column("review_id", id_type, sa.ForeignKey("review_record.id"), nullable=False),
        sa.Column("target_type", sa.String(20), nullable=False),
        sa.Column("target_id", id_type),
        sa.Column("before_json", mysql.JSON, nullable=False),
        sa.Column("after_json", mysql.JSON, nullable=False),
        sa.Column("comment", sa.Text),
        sa.Column("actor_id", id_type, sa.ForeignKey("user.id"), nullable=False),
        sa.Column("actor_role", sa.String(20), nullable=False),
        sa.Column("review_stage", sa.String(20), nullable=False),
        *audit_columns(),
    )
    op.create_index(
        "idx_revision_review_target", "review_revision", ["review_id", "target_type", "target_id"]
    )
    op.create_table(
        "review_feedback",
        sa.Column("id", id_type, primary_key=True, autoincrement=True),
        sa.Column("review_id", id_type, sa.ForeignKey("review_record.id"), nullable=False),
        sa.Column("target_type", sa.String(20), nullable=False),
        sa.Column("target_id", id_type),
        sa.Column("user_id", id_type, sa.ForeignKey("user.id"), nullable=False),
        sa.Column("judgment", sa.String(20), nullable=False),
        sa.Column("corrected_value", sa.Text),
        sa.Column("comment", sa.Text),
        *audit_columns(),
    )
    op.create_index(
        "idx_feedback_review_target", "review_feedback", ["review_id", "target_type", "target_id"]
    )
    op.create_table(
        "report",
        sa.Column("id", id_type, primary_key=True, autoincrement=True),
        sa.Column("review_id", id_type, sa.ForeignKey("review_record.id"), nullable=False),
        sa.Column("format", sa.String(10), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("storage_path", sa.String(500)),
        sa.Column("generated_at", time_type),
        *audit_columns(),
        sa.UniqueConstraint("review_id", "format", name="uk_report_review_format"),
    )
    op.create_table(
        "operation_log",
        sa.Column("id", id_type, primary_key=True, autoincrement=True),
        sa.Column("user_id", id_type, sa.ForeignKey("user.id")),
        sa.Column("action", sa.String(80), nullable=False),
        sa.Column("resource_type", sa.String(40), nullable=False),
        sa.Column("resource_id", id_type),
        sa.Column("detail_json", mysql.JSON),
        sa.Column("ip", sa.String(45)),
        *audit_columns(),
    )
    op.create_index("idx_log_user_created", "operation_log", ["user_id", "created_at"])
    op.create_index("idx_log_resource", "operation_log", ["resource_type", "resource_id"])


def downgrade() -> None:
    for table in (
        "operation_log",
        "report",
        "review_feedback",
        "review_revision",
        "risk_record",
        "contract_element",
        "review_record",
        "risk_rule",
        "standard_clause",
        "contract_file",
        "contract",
        "user",
    ):
        op.drop_table(table)
