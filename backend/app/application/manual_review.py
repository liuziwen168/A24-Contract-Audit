from __future__ import annotations

import copy
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import fail
from app.core.request_id import client_ip
from app.models.entities import (
    Contract,
    ContractElement,
    OperationLog,
    ReviewRecord,
    ReviewRevision,
    RiskRecord,
)

LEGAL = "legalReviewer"
RISK = "riskReviewer"
ACTIONS = {
    "contractType": "REVIEW_CONTRACT_TYPE_REVISED",
    "element": "REVIEW_ELEMENT_REVISED",
    "risk": "REVIEW_RISK_REVISED",
    "overallRisk": "REVIEW_OVERALL_RISK_REVISED",
    "feedback": "REVIEW_FEEDBACK_SUBMITTED",
    "legalConfirm": "REVIEW_LEGAL_CONFIRMED",
    "riskConfirm": "REVIEW_RISK_CONFIRMED",
}


def _json_value(value):
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: _json_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_value(item) for item in value]
    return value


def claim(db: Session, review_id: int, user_id: int, role: str) -> ReviewRecord:
    review = db.scalar(select(ReviewRecord).where(ReviewRecord.id == review_id).with_for_update())
    if not review:
        raise fail("REVIEW_NOT_FOUND")
    expected_stage = "legalReview" if role == LEGAL else "riskReview"
    if review.status != "processing" or review.review_stage != expected_stage:
        raise fail("REVIEW_STAGE_INVALID")
    field = "legal_reviewer_id" if role == LEGAL else "risk_reviewer_id"
    reviewer_id = getattr(review, field)
    if reviewer_id not in (None, user_id):
        raise fail("REVIEW_ALREADY_CLAIMED")
    if reviewer_id is None:
        setattr(review, field, user_id)
    return review


def add_log(
    db: Session,
    user_id: int,
    role: str,
    action: str,
    review: ReviewRecord,
    target_type: str | None = None,
    target_id: int | None = None,
) -> None:
    detail = {
        "reviewId": review.id,
        "actorRole": role,
        "reviewStage": review.review_stage,
    }
    if target_type:
        detail.update({"targetType": target_type, "targetId": target_id})
    db.add(
        OperationLog(
            user_id=user_id,
            action=action,
            resource_type="review",
            resource_id=review.id,
            detail_json=detail,
            ip=client_ip.get(),
        )
    )


def revisions(db: Session, review_id: int) -> list[ReviewRevision]:
    return list(
        db.scalars(
            select(ReviewRevision)
            .where(ReviewRevision.review_id == review_id)
            .order_by(ReviewRevision.created_at, ReviewRevision.id)
        )
    )


def apply_risk_revisions(
    risks: dict[int, dict], revision_rows: list[ReviewRevision]
) -> dict[int, dict]:
    for revision in revision_rows:
        if revision.target_type == "risk" and revision.target_id in risks:
            risks[revision.target_id] = copy.deepcopy(revision.after_json)
    return risks


def effective(db: Session, review: ReviewRecord) -> dict:
    data = copy.deepcopy(review.ai_result_json or {})
    elements = {
        row.id: {
            "elementId": row.id,
            "elementType": row.element_type,
            "elementName": row.element_name,
            "value": row.value_text,
            "page": row.page,
            "paragraphIndex": row.paragraph_index,
            "confidence": row.confidence,
        }
        for row in db.scalars(
            select(ContractElement)
            .where(ContractElement.review_id == review.id)
            .order_by(ContractElement.id)
        )
    }
    risks = {
        row.id: {
            "riskId": row.id,
            "ruleId": row.rule_id,
            "riskType": row.risk_type,
            "riskName": row.risk_name,
            "riskLevel": row.risk_level,
            "clauseText": row.clause_text,
            "page": row.page,
            "paragraphIndex": row.paragraph_index,
            "basis": row.basis,
            "suggestion": row.suggestion,
            "confidence": row.confidence,
            "riskStatus": row.status,
        }
        for row in db.scalars(
            select(RiskRecord).where(RiskRecord.review_id == review.id).order_by(RiskRecord.id)
        )
    }
    revision_rows = revisions(db, review.id)
    for revision in revision_rows:
        if revision.target_type == "contractType":
            data["contractType"] = revision.after_json["contractType"]
        elif revision.target_type == "overallRisk":
            data.update(revision.after_json)
        elif revision.target_type == "element" and revision.target_id in elements:
            elements[revision.target_id] = copy.deepcopy(revision.after_json)
    apply_risk_revisions(risks, revision_rows)
    if elements or "elements" in data:
        data["elements"] = list(elements.values())
    if risks or "risks" in data:
        data["risks"] = list(risks.values())
    return data


def revise(
    db: Session,
    review_id: int,
    user_id: int,
    role: str,
    target_type: str,
    target_id: int | None,
    after: dict,
    comment: str | None,
    action: str,
) -> ReviewRevision:
    review = claim(db, review_id, user_id, role)
    current = effective(db, review)
    if target_type == "contractType":
        before = {"contractType": current.get("contractType")}
    elif target_type == "overallRisk":
        before = {
            "overallRiskLevel": current.get("overallRiskLevel"),
            "overallScore": current.get("overallScore"),
        }
    elif target_type == "element":
        before = next((x for x in current["elements"] if x["elementId"] == target_id), None)
    else:
        before = next((x for x in current["risks"] if x["riskId"] == target_id), None)
    if before is None:
        code = "CONTRACT_ELEMENT_NOT_FOUND" if target_type == "element" else "RISK_NOT_FOUND"
        raise fail(code)
    revision = ReviewRevision(
        review_id=review.id,
        target_type=target_type,
        target_id=target_id,
        before_json=_json_value(before),
        after_json=_json_value(after),
        comment=comment,
        actor_id=user_id,
        actor_role=role,
        review_stage=review.review_stage,
    )
    db.add(revision)
    db.flush()
    add_log(db, user_id, role, action, review, target_type, target_id)
    return revision


def readable(review: ReviewRecord, contract: Contract | None, user_id: int, role: str) -> bool:
    if role == "admin" or (contract and contract.owner_id == user_id):
        return True
    if role == LEGAL:
        return (
            review.review_stage == "legalReview" and review.legal_reviewer_id in (None, user_id)
        ) or review.legal_reviewer_id == user_id
    if role == RISK:
        return (
            review.review_stage == "riskReview" and review.risk_reviewer_id in (None, user_id)
        ) or review.risk_reviewer_id == user_id
    return False
