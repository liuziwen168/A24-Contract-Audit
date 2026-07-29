from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Index,
    JSON,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class AuditMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )


class User(AuditMixin, Base):
    __tablename__ = "user"
    __table_args__ = (
        UniqueConstraint("username", name="uk_user_username"),
        Index("idx_user_role_status", "role", "status"),
    )
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[str] = mapped_column(String(64), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), default="user", nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Contract(AuditMixin, Base):
    __tablename__ = "contract"
    __table_args__ = (
        Index("idx_contract_owner_status", "owner_id", "status"),
        Index("idx_contract_type", "contract_type"),
    )
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    contract_type: Mapped[str | None] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(20), default="uploaded", nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ContractFile(AuditMixin, Base):
    __tablename__ = "contract_file"
    __table_args__ = (
        UniqueConstraint("contract_id", "sha256", name="uk_file_contract_sha"),
        Index("idx_file_contract", "contract_id"),
    )
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    contract_id: Mapped[int] = mapped_column(ForeignKey("contract.id"), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_type: Mapped[str] = mapped_column(String(20), nullable=False)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)


class ContractElement(AuditMixin, Base):
    __tablename__ = "contract_element"
    __table_args__ = (Index("idx_element_contract_type", "contract_id", "element_type"),)
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    contract_id: Mapped[int] = mapped_column(ForeignKey("contract.id"), nullable=False)
    review_id: Mapped[int | None] = mapped_column(ForeignKey("review_record.id"))
    element_type: Mapped[str] = mapped_column(String(40), nullable=False)
    element_name: Mapped[str] = mapped_column(String(80), nullable=False)
    value_text: Mapped[str] = mapped_column(Text, nullable=False)
    page: Mapped[int | None] = mapped_column()
    paragraph_index: Mapped[int | None] = mapped_column()
    confidence: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    source: Mapped[str] = mapped_column(String(20), default="ai", nullable=False)


class ReviewRecord(AuditMixin, Base):
    __tablename__ = "review_record"
    __table_args__ = (
        UniqueConstraint("request_id", name="uk_review_request"),
        UniqueConstraint(
            "idempotency_user_id", "idempotency_key", name="uk_review_user_idempotency"
        ),
        Index("idx_review_contract_created", "contract_id", "created_at"),
        Index("idx_review_file_status", "contract_file_id", "status"),
        Index("idx_review_executor", "status", "review_stage", "ai_started_at"),
    )
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    contract_id: Mapped[int] = mapped_column(ForeignKey("contract.id"), nullable=False)
    contract_file_id: Mapped[int] = mapped_column(ForeignKey("contract_file.id"), nullable=False)
    file_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    idempotency_user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False)
    request_id: Mapped[str] = mapped_column(String(64), nullable=False)
    review_mode: Mapped[str] = mapped_column(String(20), nullable=False)
    source_warning_id: Mapped[int | None] = mapped_column(
        ForeignKey("risk_warning.id", name="fk_review_source_warning", use_alter=True)
    )
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    review_stage: Mapped[str] = mapped_column(String(20), default="aiReview", nullable=False)
    ai_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ai_attempt_count: Mapped[int] = mapped_column(default=0, nullable=False)
    ai_result_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    ai_model_name: Mapped[str | None] = mapped_column(String(100))
    ai_model_version: Mapped[str | None] = mapped_column(String(100))
    prompt_version: Mapped[str | None] = mapped_column(String(32))
    ai_warnings: Mapped[list[Any]] = mapped_column(JSON, default=list, nullable=False)
    legal_opinion: Mapped[str | None] = mapped_column(Text)
    risk_opinion: Mapped[str | None] = mapped_column(Text)
    legal_reviewer_id: Mapped[int | None] = mapped_column(ForeignKey("user.id"))
    risk_reviewer_id: Mapped[int | None] = mapped_column(ForeignKey("user.id"))
    legal_reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    risk_reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    missing_clauses: Mapped[list[Any]] = mapped_column(JSON, default=list, nullable=False)
    overall_risk_level: Mapped[str | None] = mapped_column(String(10))
    overall_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    processing_time_ms: Mapped[int | None] = mapped_column()
    error_code: Mapped[str | None] = mapped_column(String(32))
    error_message: Mapped[str | None] = mapped_column(String(500))


class RiskRecord(AuditMixin, Base):
    __tablename__ = "risk_record"
    __table_args__ = (
        Index("idx_risk_review_level", "review_id", "risk_level"),
        Index("idx_risk_type", "risk_type"),
    )
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    review_id: Mapped[int] = mapped_column(ForeignKey("review_record.id"), nullable=False)
    rule_id: Mapped[int | None] = mapped_column(ForeignKey("risk_rule.id"))
    rule_snapshot: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    risk_type: Mapped[str] = mapped_column(String(40), nullable=False)
    risk_name: Mapped[str] = mapped_column(String(100), nullable=False)
    risk_level: Mapped[str] = mapped_column(String(10), nullable=False)
    clause_text: Mapped[str] = mapped_column(Text, nullable=False)
    page: Mapped[int | None] = mapped_column()
    paragraph_index: Mapped[int | None] = mapped_column()
    basis: Mapped[str] = mapped_column(Text, nullable=False)
    suggestion: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)


class StandardClause(AuditMixin, Base):
    __tablename__ = "standard_clause"
    __table_args__ = (
        UniqueConstraint("contract_type", "clause_type", "name", name="uk_clause_type_name"),
    )
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    contract_type: Mapped[str] = mapped_column(String(40), nullable=False)
    clause_type: Mapped[str] = mapped_column(String(40), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    version: Mapped[str] = mapped_column(String(32), default="v0.1", nullable=False)


class RiskRule(AuditMixin, Base):
    __tablename__ = "risk_rule"
    __table_args__ = (
        UniqueConstraint("rule_code", name="uk_rule_code"),
        Index("idx_rule_type_status", "risk_type", "status"),
    )
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    rule_code: Mapped[str] = mapped_column(String(40), nullable=False)
    risk_type: Mapped[str] = mapped_column(String(40), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    risk_level: Mapped[str] = mapped_column(String(10), default="medium", nullable=False)
    rule_content: Mapped[str] = mapped_column(Text, nullable=False)
    standard_clause_id: Mapped[int | None] = mapped_column(ForeignKey("standard_clause.id"))
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    warning_enabled: Mapped[bool] = mapped_column(default=False, nullable=False)
    warning_due_hours: Mapped[int | None] = mapped_column()
    version: Mapped[str] = mapped_column(String(32), default="v0.1", nullable=False)


class RiskWarning(AuditMixin, Base):
    __tablename__ = "risk_warning"
    __table_args__ = (
        UniqueConstraint("warning_key", name="uk_warning_key"),
        Index("idx_warning_owner_status_due", "owner_id", "warning_status", "due_at"),
        Index("idx_warning_contract_status", "contract_id", "warning_status"),
        Index("idx_warning_source_review_status", "source_review_id", "warning_status"),
        Index("idx_warning_remediation_review", "remediation_review_id"),
    )
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    warning_key: Mapped[str] = mapped_column(String(128), nullable=False)
    source_review_id: Mapped[int] = mapped_column(ForeignKey("review_record.id"), nullable=False)
    source_risk_id: Mapped[int] = mapped_column(ForeignKey("risk_record.id"), nullable=False)
    contract_id: Mapped[int] = mapped_column(ForeignKey("contract.id"), nullable=False)
    owner_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    warning_type: Mapped[str] = mapped_column(String(40), default="riskRuleHit", nullable=False)
    warning_level: Mapped[str] = mapped_column(String(10), nullable=False)
    warning_status: Mapped[str] = mapped_column(String(20), default="pendingLegal", nullable=False)
    source_snapshot: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    remediation_review_id: Mapped[int | None] = mapped_column(ForeignKey("review_record.id"))
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class WarningAction(AuditMixin, Base):
    __tablename__ = "warning_action"
    __table_args__ = (
        Index("idx_warning_action_warning_created", "warning_id", "created_at"),
        Index("idx_warning_action_actor_created", "actor_id", "created_at"),
    )
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    warning_id: Mapped[int] = mapped_column(ForeignKey("risk_warning.id"), nullable=False)
    action_type: Mapped[str] = mapped_column("action", String(40), nullable=False)
    from_status: Mapped[str | None] = mapped_column(String(20))
    to_status: Mapped[str | None] = mapped_column(String(20))
    actor_id: Mapped[int | None] = mapped_column(ForeignKey("user.id"))
    actor_role: Mapped[str | None] = mapped_column(String(20))
    comment: Mapped[str | None] = mapped_column(Text)
    remediation_review_id: Mapped[int | None] = mapped_column(ForeignKey("review_record.id"))
    detail_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)


class ReviewRevision(AuditMixin, Base):
    __tablename__ = "review_revision"
    __table_args__ = (Index("idx_revision_review_target", "review_id", "target_type", "target_id"),)
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    review_id: Mapped[int] = mapped_column(ForeignKey("review_record.id"), nullable=False)
    target_type: Mapped[str] = mapped_column(String(20), nullable=False)
    target_id: Mapped[int | None] = mapped_column()
    before_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    after_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    comment: Mapped[str | None] = mapped_column(Text)
    actor_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    actor_role: Mapped[str] = mapped_column(String(20), nullable=False)
    review_stage: Mapped[str] = mapped_column(String(20), nullable=False)


class ReviewFeedback(AuditMixin, Base):
    __tablename__ = "review_feedback"
    __table_args__ = (Index("idx_feedback_review_target", "review_id", "target_type", "target_id"),)
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    review_id: Mapped[int] = mapped_column(ForeignKey("review_record.id"), nullable=False)
    target_type: Mapped[str] = mapped_column(String(20), nullable=False)
    target_id: Mapped[int | None] = mapped_column()
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    judgment: Mapped[str] = mapped_column(String(20), nullable=False)
    corrected_value: Mapped[str | None] = mapped_column(Text)
    comment: Mapped[str | None] = mapped_column(Text)


class Report(AuditMixin, Base):
    __tablename__ = "report"
    __table_args__ = (
        UniqueConstraint("review_id", "format", name="uk_report_review_format"),
        Index("idx_report_executor", "status", "started_at"),
    )
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    review_id: Mapped[int] = mapped_column(ForeignKey("review_record.id"), nullable=False)
    format: Mapped[str] = mapped_column(String(10), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    storage_path: Mapped[str | None] = mapped_column(String(500))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    attempt_count: Mapped[int] = mapped_column(default=0, nullable=False)
    error_code: Mapped[str | None] = mapped_column(String(32))
    error_message: Mapped[str | None] = mapped_column(String(500))
    file_size: Mapped[int | None] = mapped_column(BigInteger)
    sha256: Mapped[str | None] = mapped_column(String(64))
    generated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class OperationLog(AuditMixin, Base):
    __tablename__ = "operation_log"
    __table_args__ = (
        Index("idx_log_user_created", "user_id", "created_at"),
        Index("idx_log_resource", "resource_type", "resource_id"),
    )
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("user.id"))
    action: Mapped[str] = mapped_column(String(80), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(40), nullable=False)
    resource_id: Mapped[int | None] = mapped_column()
    detail_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    ip: Mapped[str | None] = mapped_column(String(45))
