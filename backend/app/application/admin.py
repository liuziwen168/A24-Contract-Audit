from __future__ import annotations

from collections import Counter
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.application.manual_review import apply_risk_revisions
from app.core.errors import fail
from app.core.request_id import client_ip
from app.domain import CONTRACT_STATUSES, REVIEW_STAGES, REVIEW_STATUSES, RISK_LEVELS
from app.models.entities import (
    Contract,
    OperationLog,
    ReviewRecord,
    ReviewRevision,
    RiskRecord,
    RiskRule,
    StandardClause,
    User,
    utcnow,
)

ADMIN_ACTIONS = {
    "userUpdated": "ADMIN_USER_UPDATED",
    "clauseCreated": "STANDARD_CLAUSE_CREATED",
    "clauseUpdated": "STANDARD_CLAUSE_UPDATED",
    "clauseDeleted": "STANDARD_CLAUSE_DELETED",
    "ruleCreated": "RISK_RULE_CREATED",
    "ruleUpdated": "RISK_RULE_UPDATED",
    "ruleDeleted": "RISK_RULE_DELETED",
}


def require_admin(user: User) -> None:
    if user.role != "admin":
        raise fail("PERMISSION_DENIED")


def public_user(user: User) -> dict[str, Any]:
    return {
        "id": user.id,
        "username": user.username,
        "role": user.role,
        "userStatus": user.status,
        "createdAt": user.created_at,
        "updatedAt": user.updated_at,
    }


def public_clause(clause: StandardClause) -> dict[str, Any]:
    return {
        "clauseId": clause.id,
        "name": clause.name,
        "contractType": clause.contract_type,
        "clauseType": clause.clause_type,
        "content": clause.content,
        "configStatus": clause.status,
        "version": clause.version,
        "createdAt": clause.created_at,
        "updatedAt": clause.updated_at,
    }


def public_rule(rule: RiskRule) -> dict[str, Any]:
    return {
        "ruleId": rule.id,
        "ruleCode": rule.rule_code,
        "riskType": rule.risk_type,
        "name": rule.name,
        "riskLevel": rule.risk_level,
        "ruleContent": rule.rule_content,
        "standardClauseId": rule.standard_clause_id,
        "configStatus": rule.status,
        "version": rule.version,
        "createdAt": rule.created_at,
        "updatedAt": rule.updated_at,
    }


def _json_value(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: _json_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_value(item) for item in value]
    return value


def add_admin_log(
    db: Session,
    operator: User,
    action: str,
    target_type: str,
    target_id: int,
    before: dict[str, Any] | None,
    after: dict[str, Any] | None,
) -> None:
    db.add(
        OperationLog(
            user_id=operator.id,
            action=action,
            resource_type=target_type,
            resource_id=target_id,
            detail_json={
                "operatorId": operator.id,
                "operatorRole": operator.role,
                "targetType": target_type,
                "targetId": target_id,
                "beforeValue": _json_value(before),
                "afterValue": _json_value(after),
            },
            ip=client_ip.get(),
        )
    )


_SENSITIVE_PARTS = ("password", "secret", "token", "jwt", "path", "apikey")


def redact(value: Any) -> Any:
    if isinstance(value, dict):
        cleaned: dict[str, Any] = {}
        for key, item in value.items():
            normalized = key.replace("_", "").lower()
            cleaned[key] = "[REDACTED]" if any(x in normalized for x in _SENSITIVE_PARTS) else redact(item)
        return cleaned
    if isinstance(value, list):
        return [redact(item) for item in value]
    return value


def _date_filters(column, start: datetime | None, end: datetime | None) -> list[Any]:
    filters: list[Any] = []
    if start is not None:
        filters.append(column >= start)
    if end is not None:
        filters.append(column <= end)
    return filters


def dashboard_window(
    start: datetime | None, end: datetime | None
) -> tuple[datetime | None, datetime | None]:
    if start and start.tzinfo is None:
        start = start.replace(tzinfo=timezone.utc)
    if end and end.tzinfo is None:
        end = end.replace(tzinfo=timezone.utc)
    if start and end and start > end:
        raise fail("PARAM_INVALID")
    if start and not end:
        end = utcnow()
    if end and not start:
        start = end - timedelta(days=366)
    if start and end and end - start > timedelta(days=366):
        raise fail("PARAM_INVALID")
    return start, end


def dashboard_data(
    db: Session, start: datetime | None, end: datetime | None
) -> dict[str, Any]:
    start, end = dashboard_window(start, end)
    contract_filters = [Contract.deleted_at.is_(None), *_date_filters(Contract.created_at, start, end)]
    review_filters = [
        Contract.deleted_at.is_(None),
        *_date_filters(ReviewRecord.created_at, start, end),
    ]

    contract_counts = dict(
        db.execute(
            select(Contract.status, func.count()).where(*contract_filters).group_by(Contract.status)
        ).all()
    )
    review_counts = dict(
        db.execute(
            select(ReviewRecord.status, func.count())
            .join(Contract, Contract.id == ReviewRecord.contract_id)
            .where(*review_filters)
            .group_by(ReviewRecord.status)
        ).all()
    )
    stage_counts = dict(
        db.execute(
            select(ReviewRecord.review_stage, func.count())
            .join(Contract, Contract.id == ReviewRecord.contract_id)
            .where(*review_filters)
            .group_by(ReviewRecord.review_stage)
        ).all()
    )

    risk_rows = db.execute(
        select(RiskRecord)
        .join(ReviewRecord, ReviewRecord.id == RiskRecord.review_id)
        .join(Contract, Contract.id == ReviewRecord.contract_id)
        .where(*review_filters, ReviewRecord.ai_result_json.is_not(None))
        .order_by(RiskRecord.id)
    ).scalars().all()
    risk_map = {
        row.id: {"riskId": row.id, "riskLevel": row.risk_level, "riskStatus": row.status}
        for row in risk_rows
    }
    if risk_map:
        revision_rows = list(
            db.scalars(
                select(ReviewRevision)
                .where(
                    ReviewRevision.target_type == "risk",
                    ReviewRevision.target_id.in_(risk_map),
                )
                .order_by(ReviewRevision.created_at, ReviewRevision.id)
            )
        )
        apply_risk_revisions(risk_map, revision_rows)
    risk_counts = Counter(
        item.get("riskLevel")
        for item in risk_map.values()
        if item.get("riskStatus") != "dismissed"
    )

    trend_end = end or utcnow()
    trend_start = start or datetime.combine(
        trend_end.date() - timedelta(days=6), time.min, tzinfo=timezone.utc
    )
    trend_dates = list(
        db.scalars(
            select(Contract.created_at).where(
                Contract.deleted_at.is_(None),
                Contract.created_at >= trend_start,
                Contract.created_at <= trend_end,
            )
        )
    )
    uploads = Counter(value.date().isoformat() for value in trend_dates)
    days = (trend_end.date() - trend_start.date()).days
    trend = [
        {
            "date": (trend_start.date() + timedelta(days=offset)).isoformat(),
            "contractCount": uploads[(trend_start.date() + timedelta(days=offset)).isoformat()],
        }
        for offset in range(days + 1)
    ]

    return {
        "contractsTotal": sum(contract_counts.values()),
        "contractsByStatus": {
            value: contract_counts.get(value, 0) for value in sorted(CONTRACT_STATUSES)
        },
        "reviewsTotal": sum(review_counts.values()),
        "reviewsByStatus": {
            value: review_counts.get(value, 0) for value in sorted(REVIEW_STATUSES)
        },
        "reviewsByStage": {
            value: stage_counts.get(value, 0) for value in sorted(REVIEW_STAGES)
        },
        "effectiveRisksByLevel": {
            value: risk_counts.get(value, 0) for value in sorted(RISK_LEVELS)
        },
        "pendingLegalReview": stage_counts.get("legalReview", 0),
        "pendingRiskReview": stage_counts.get("riskReview", 0),
        "completedReviews": review_counts.get("completed", 0),
        "contractUploadTrend": trend,
        "from": start,
        "to": end,
        "timezone": "UTC",
        "scope": "nonDeletedContractsWithCurrentEffectiveRisks",
    }
