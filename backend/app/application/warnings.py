from __future__ import annotations

from datetime import timedelta, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.application.manual_review import LEGAL, RISK
from app.core.errors import fail
from app.models.entities import (
    ReviewRecord,
    RiskRecord,
    RiskWarning,
    User,
    WarningAction,
    utcnow,
)

USER_VISIBLE = {"active", "processing"}
RISK_VISIBLE = {"pendingRisk", "active", "processing"}


def scoped_warnings(query, user: User):
    if user.role == "admin":
        return query  # admin can see all warnings
    if user.role == "user":
        return query.where(
            RiskWarning.owner_id == user.id, RiskWarning.warning_status.in_(USER_VISIBLE)
        )
    if user.role == LEGAL:
        return query.where(RiskWarning.warning_status == "pendingLegal")
    if user.role == RISK:
        return query.where(RiskWarning.warning_status.in_(RISK_VISIBLE))
    raise fail("WARNING_ROLE_NOT_ALLOWED")


def visible_warning(db: Session, warning_id: int, user: User) -> RiskWarning:
    query = scoped_warnings(select(RiskWarning).where(RiskWarning.id == warning_id), user)
    warning = db.scalar(query)
    if warning is None:
        raise fail("WARNING_NOT_FOUND")
    return warning


def locked_warning(db: Session, warning_id: int, user: User, role: str) -> RiskWarning:
    if user.role != role:
        raise fail("WARNING_ROLE_NOT_ALLOWED")
    warning = db.scalar(select(RiskWarning).where(RiskWarning.id == warning_id).with_for_update())
    if warning is None:
        raise fail("WARNING_NOT_FOUND")
    if role == "user" and warning.owner_id != user.id:
        raise fail("WARNING_NOT_FOUND")
    return warning


def add_action(
    db: Session,
    warning: RiskWarning,
    user: User | None,
    action_type: str,
    from_status: str | None,
    to_status: str | None,
    comment: str | None = None,
    remediation_review_id: int | None = None,
) -> None:
    db.add(
        WarningAction(
            warning_id=warning.id,
            action_type=action_type,
            from_status=from_status,
            to_status=to_status,
            actor_id=user.id if user else None,
            actor_role=user.role if user else None,
            comment=comment,
            remediation_review_id=remediation_review_id,
        )
    )


def _source_review(db: Session, warning: RiskWarning) -> ReviewRecord:
    review = db.get(ReviewRecord, warning.source_review_id)
    if review is None or review.contract_id != warning.contract_id:
        raise fail("WARNING_NOT_FOUND")
    return review


def _require_stage(db: Session, warning: RiskWarning, stage: str) -> None:
    review = _source_review(db, warning)
    if review.status != "processing" or review.review_stage != stage:
        raise fail("WARNING_STAGE_INVALID")


def _transition(
    db: Session,
    warning: RiskWarning,
    user: User,
    expected: set[str],
    target: str,
    action_type: str,
    comment: str | None = None,
    remediation_review_id: int | None = None,
) -> RiskWarning:
    if warning.warning_status not in expected:
        raise fail("WARNING_STATUS_INVALID")
    previous = warning.warning_status
    warning.warning_status = target
    add_action(
        db, warning, user, action_type, previous, target, comment, remediation_review_id
    )
    return warning


def legal_confirm(db: Session, warning_id: int, user: User, comment: str | None) -> RiskWarning:
    warning = locked_warning(db, warning_id, user, LEGAL)
    _require_stage(db, warning, "legalReview")
    return _transition(db, warning, user, {"pendingLegal"}, "pendingRisk", "legalConfirmed", comment)


def legal_withdraw(db: Session, warning_id: int, user: User, comment: str | None) -> RiskWarning:
    warning = locked_warning(db, warning_id, user, LEGAL)
    _require_stage(db, warning, "legalReview")
    if not comment:
        raise fail("PARAM_INVALID")
    return _transition(db, warning, user, {"pendingLegal"}, "withdrawn", "withdrawn", comment)


def risk_activate(
    db: Session, warning_id: int, user: User, due_at, comment: str | None
) -> RiskWarning:
    warning = locked_warning(db, warning_id, user, RISK)
    _require_stage(db, warning, "riskReview")
    if due_at is None:
        due_hours = warning.source_snapshot.get("rule", {}).get("warningDueHours")
        if due_hours:
            due_at = utcnow() + timedelta(hours=int(due_hours))
    if due_at is not None:
        warning.due_at = due_at
    return _transition(db, warning, user, {"pendingRisk"}, "active", "remediationRequired", comment)


def waive(db: Session, warning_id: int, user: User, comment: str | None) -> RiskWarning:
    warning = locked_warning(db, warning_id, user, RISK)
    if not comment:
        raise fail("PARAM_INVALID")
    if warning.warning_status == "pendingRisk":
        _require_stage(db, warning, "riskReview")
    return _transition(db, warning, user, {"pendingRisk", "active"}, "waived", "waived", comment)


def acknowledge(db: Session, warning_id: int, user: User) -> RiskWarning:
    warning = locked_warning(db, warning_id, user, "user")
    if warning.warning_status != "active":
        raise fail("WARNING_STATUS_INVALID")
    if warning.acknowledged_at is None:
        warning.acknowledged_at = utcnow()
    # 低风险预警：用户确认知悉后自动关闭，从预警中心移除
    if warning.warning_level == "low":
        previous = warning.warning_status
        warning.warning_status = "closed"
        warning.closed_at = utcnow()
        add_action(db, warning, user, "acknowledged", previous, "closed",
                   comment="低风险预警，用户确认知悉后自动关闭")
    else:
        add_action(db, warning, user, "acknowledged", "active", "active")
    return warning


def _require_completed_remediation(db: Session, warning: RiskWarning) -> None:
    review_id = warning.remediation_review_id
    review = db.get(ReviewRecord, review_id) if review_id else None
    if (
        review is None
        or review.contract_id != warning.contract_id
        or review.source_warning_id != warning.id
        or review.status != "completed"
        or review.review_stage != "completed"
    ):
        raise fail("WARNING_REMEDIATION_REVIEW_INVALID")


def close(db: Session, warning_id: int, user: User, comment: str | None) -> RiskWarning:
    warning = locked_warning(db, warning_id, user, RISK)
    if warning.warning_status == "processing":
        _require_completed_remediation(db, warning)
    warning = _transition(db, warning, user, {"active", "processing"}, "closed", "closed", comment)
    warning.closed_at = utcnow()
    return warning


def reopen(
    db: Session, warning_id: int, user: User, due_at, comment: str | None
) -> RiskWarning:
    warning = locked_warning(db, warning_id, user, RISK)
    previous_remediation_review_id = warning.remediation_review_id
    if warning.warning_status == "processing":
        _require_completed_remediation(db, warning)
    if due_at is not None:
        warning.due_at = due_at
    warning.closed_at = None
    warning = _transition(
        db,
        warning,
        user,
        {"processing", "closed"},
        "active",
        "reopened",
        comment,
        previous_remediation_review_id,
    )
    warning.remediation_review_id = None
    return warning


def begin_remediation(
    db: Session, warning_id: int, user: User, contract_id: int, review: ReviewRecord
) -> RiskWarning:
    warning = locked_warning(db, warning_id, user, "user")
    if warning.contract_id != contract_id or warning.warning_status != "active":
        raise fail("WARNING_STATUS_INVALID")
    if warning.acknowledged_at is None:
        raise fail("WARNING_ACKNOWLEDGEMENT_REQUIRED")
    if warning.remediation_review_id is not None:
        raise fail("WARNING_REMEDIATION_REVIEW_INVALID")
    warning.warning_status = "processing"
    warning.remediation_review_id = review.id
    add_action(
        db,
        warning,
        user,
        "remediationStarted",
        "active",
        "processing",
        remediation_review_id=review.id,
    )
    return warning


def complete_remediation(db: Session, review: ReviewRecord) -> RiskWarning | None:
    """整改审核完成后回调：更新源预警状态。

    - 审核整体低风险 → 预警回到 active，用户确认后关闭
    - 仍有风险 → 预警回到 active，用户需继续整改
    """
    if review.source_warning_id is None:
        return None
    warning = db.scalar(
        select(RiskWarning).where(RiskWarning.id == review.source_warning_id).with_for_update()
    )
    if warning is None or warning.remediation_review_id != review.id:
        return None
    # 用新审核结果更新预警信息
    warning.warning_level = review.overall_risk_level or warning.warning_level
    warning.warning_status = "active"
    warning.remediation_review_id = None
    warning.acknowledged_at = None  # 需要重新确认
    add_action(
        db,
        warning,
        None,
        "remediationCompleted",
        "processing",
        "active",
        comment=f"整改审核完成，整体风险等级: {review.overall_risk_level or 'unknown'}",
    )
    return warning


def warning_payload(db: Session, warning: RiskWarning, include_private: bool = False) -> dict[str, Any]:
    risk = db.get(RiskRecord, warning.source_risk_id)
    remediation_review = (
        db.get(ReviewRecord, warning.remediation_review_id)
        if warning.remediation_review_id is not None
        else None
    )
    snapshot = risk.rule_snapshot if risk and risk.rule_snapshot else warning.source_snapshot.get("rule", {})
    due_at = warning.due_at
    if due_at is not None and due_at.tzinfo is None:
        due_at = due_at.replace(tzinfo=timezone.utc)
    payload: dict[str, Any] = {
        "warningId": warning.id,
        "warningKey": warning.warning_key,
        "reviewId": warning.source_review_id,
        "contractId": warning.contract_id,
        "ownerId": warning.owner_id,
        "rule": {
            "ruleId": snapshot.get("ruleId"),
            "ruleCode": snapshot.get("ruleCode"),
            "name": snapshot.get("name"),
        },
        "risk": {
            "riskId": warning.source_risk_id,
            "riskType": risk.risk_type if risk else None,
            "riskName": risk.risk_name if risk else None,
            "riskLevel": warning.warning_level,
            "basis": risk.basis if risk else None,
            "suggestion": risk.suggestion if risk else None,
        },
        "warningStatus": warning.warning_status,
        "warningLevel": warning.warning_level,
        "dueAt": warning.due_at,
        "overdue": bool(
            warning.warning_status in {"active", "processing"}
            and due_at is not None
            and due_at < utcnow()
        ),
        "acknowledgedAt": warning.acknowledged_at,
        "remediationReviewId": warning.remediation_review_id,
        "closedAt": warning.closed_at,
        "createdAt": warning.created_at,
        "updatedAt": warning.updated_at,
    }
    # 风控人员需要在整改复审列表中看到 AI、法务和风控各阶段的实时状态，
    # 因此将关联审核的最小必要信息随预警一并返回，避免前端逐条额外请求。
    if remediation_review is not None:
        payload["remediationReview"] = {
            "reviewId": remediation_review.id,
            "reviewStatus": remediation_review.status,
            "reviewStage": remediation_review.review_stage,
            "overallRiskLevel": remediation_review.overall_risk_level,
            "overallScore": float(remediation_review.overall_score)
            if remediation_review.overall_score is not None
            else None,
            "errorCode": remediation_review.error_code,
            "errorMessage": remediation_review.error_message,
            "updatedAt": remediation_review.updated_at,
        }
    else:
        payload["remediationReview"] = None
    if include_private:
        payload["sourceSnapshot"] = warning.source_snapshot
    return payload


def recent_actions_for_user(db: Session, user_id: int, limit: int = 5) -> list[dict[str, Any]]:
    """获取用户所有预警的最近处置记录"""
    actions = db.scalars(
        select(WarningAction)
        .join(RiskWarning, RiskWarning.id == WarningAction.warning_id)
        .where(RiskWarning.owner_id == user_id)
        .order_by(WarningAction.created_at.desc(), WarningAction.id.desc())
        .limit(limit)
    ).all()
    result: list[dict[str, Any]] = []
    for item in actions:
        warning = db.get(RiskWarning, item.warning_id)
        result.append({
            "warningActionId": item.id,
            "warningId": item.warning_id,
            "actionType": item.action_type,
            "fromStatus": item.from_status,
            "toStatus": item.to_status,
            "actorId": item.actor_id,
            "actorRole": item.actor_role,
            "comment": item.comment,
            "contractId": warning.contract_id if warning else None,
            "riskName": warning.source_snapshot.get("rule", {}).get("name") if warning else None,
            "createdAt": item.created_at,
        })
    return result


def warning_stats_for_user(db: Session, user_id: int) -> dict[str, int]:
    """获取用户预警统计"""
    base = select(RiskWarning).where(RiskWarning.owner_id == user_id)
    return {
        "activeCount": db.scalar(
            select(func.count()).select_from(base.where(RiskWarning.warning_status == "active").subquery())
        ) or 0,
        "processingCount": db.scalar(
            select(func.count()).select_from(base.where(RiskWarning.warning_status == "processing").subquery())
        ) or 0,
        "overdueCount": db.scalar(
            select(func.count()).select_from(
                base.where(
                    RiskWarning.warning_status.in_({"active", "processing"}),
                    RiskWarning.due_at.is_not(None),
                    RiskWarning.due_at < utcnow(),
                ).subquery()
            )
        ) or 0,
        "totalCount": db.scalar(
            select(func.count()).select_from(base.subquery())
        ) or 0,
    }


def warning_actions(db: Session, warning_id: int) -> list[dict[str, Any]]:
    return [
        {
            "warningActionId": item.id,
            "actionType": item.action_type,
            "fromStatus": item.from_status,
            "toStatus": item.to_status,
            "actorId": item.actor_id,
            "actorRole": item.actor_role,
            "comment": item.comment,
            "remediationReviewId": item.remediation_review_id,
            "createdAt": item.created_at,
        }
        for item in db.scalars(
            select(WarningAction)
            .where(WarningAction.warning_id == warning_id)
            .order_by(WarningAction.created_at, WarningAction.id)
        )
    ]
