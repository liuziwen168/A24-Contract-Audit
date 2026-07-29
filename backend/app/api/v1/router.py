from __future__ import annotations

import logging
from datetime import datetime
from typing import Annotated, Callable

from fastapi import APIRouter, Depends, File, Header, Path, Query, UploadFile
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.responses import FileResponse
from sqlalchemy import exists, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.errors import AppError, fail
from app.core.request_id import new_request_id, request_id
from app.core.security import create_token, decode_token, hash_password, verify_password
from app.application.manual_review import (
    LEGAL,
    RISK,
    ACTIONS,
    add_log,
    claim,
    effective,
    readable,
    revise,
    revisions,
)
from app.application.admin import (
    ADMIN_ACTIONS,
    add_admin_log,
    dashboard_data,
    public_clause,
    public_rule,
    public_user as admin_public_user,
    redact,
    require_admin,
)
from app.application.reports import report_path, safe_download_name
from app.application.warnings import (
    acknowledge as warning_acknowledge,
    begin_remediation,
    close as warning_close,
    legal_confirm as warning_legal_confirm,
    legal_withdraw as warning_legal_withdraw,
    reopen as warning_reopen,
    risk_activate as warning_risk_activate,
    scoped_warnings,
    visible_warning,
    waive as warning_waive,
    warning_actions,
    warning_payload,
)
from app.domain import CONTRACT_TYPES, RISK_LEVELS, RISK_TYPES, ROLES, USER_STATUSES, WARNING_STATUSES
from app.infrastructure.db import get_db
from app.infrastructure.files import file_type, save_upload, upload_path
from app.models.entities import (
    Contract,
    ContractFile,
    ContractElement,
    Report,
    OperationLog,
    ReviewFeedback,
    ReviewRecord,
    RiskRecord,
    RiskWarning,
    RiskRule,
    StandardClause,
    User,
    utcnow,
)
from app.schemas.api import LoginIn, ReviewIn
from app.schemas.admin import (
    RiskRuleCreateIn,
    RiskRuleUpdateIn,
    StandardClauseCreateIn,
    StandardClauseUpdateIn,
    UserCreateIn,
    UserUpdateIn,
)
from app.schemas.review import (
    ContractTypeIn,
    ElementIn,
    FeedbackIn,
    OpinionIn,
    OverallRiskIn,
    RiskIn,
)
from app.schemas.report import ReportCreateIn
from app.schemas.warning import WarningActivateIn, WarningCommentIn, WarningReopenIn

router = APIRouter(prefix="/api/v1")
Db = Annotated[Session, Depends(get_db)]
bearer = HTTPBearer(auto_error=False)
logger = logging.getLogger(__name__)


def result(data: object) -> dict[str, object]:
    return {"code": "OK", "message": "success", "data": data, "requestId": request_id.get()}


def public_user(user: User) -> dict[str, object]:
    return {"id": user.id, "username": user.username, "role": user.role, "userStatus": user.status}


def current_user(
    db: Db, credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise fail("AUTH_TOKEN_MISSING")
    data = decode_token(credentials.credentials)
    user = db.get(User, int(data["sub"]))
    if not user or user.deleted_at or user.status != "active":
        raise fail("AUTH_TOKEN_INVALID")
    return user


CurrentUser = Annotated[User, Depends(current_user)]


@router.post("/auth/login")
def login(body: LoginIn, db: Db) -> dict[str, object]:
    user = db.scalar(select(User).where(User.username == body.username, User.deleted_at.is_(None)))
    if (
        not user
        or user.status != "active"
        or not verify_password(body.password, user.password_hash)
    ):
        raise fail("AUTH_LOGIN_FAILED")
    return result(
        {
            "accessToken": create_token(user.id, user.role),
            "tokenType": "Bearer",
            "expiresIn": settings.jwt_expire_seconds,
            "user": public_user(user),
        }
    )


@router.get("/users/me")
def me(user: CurrentUser) -> dict[str, object]:
    return result(public_user(user))


@router.post("/contracts")
async def create_contract(
    user: CurrentUser, db: Db, file: UploadFile = File(...), name: str | None = None
) -> dict[str, object]:
    if user.role != "user":
        raise fail("PERMISSION_DENIED")
    content = await file.read(settings.max_upload_mb * 1024 * 1024 + 1)
    if len(content) > settings.max_upload_mb * 1024 * 1024:
        raise fail("FILE_TOO_LARGE")
    kind = file_type(file.filename or "", content)
    contract = Contract(
        owner_id=user.id, name=name or (file.filename or "contract"), status="uploaded"
    )
    db.add(contract)
    db.flush()
    path, digest = save_upload(contract.id, file.filename or "upload", content)
    contract_file = ContractFile(
        contract_id=contract.id,
        file_name=file.filename or "upload",
        storage_path=path,
        file_type=kind,
        file_size=len(content),
        sha256=digest,
    )
    db.add(contract_file)
    db.commit()
    return result(
        {
            "contractId": contract.id,
            "contractFileId": contract_file.id,
            "contractStatus": contract.status,
        }
    )


def contracts_scope(query, user: User):
    if user.role == "user":
        return query.where(Contract.owner_id == user.id)
    if user.role == "admin":
        return query
    stage = "legalReview" if user.role == "legalReviewer" else "riskReview"
    reviewer_id = (
        ReviewRecord.legal_reviewer_id
        if user.role == "legalReviewer"
        else ReviewRecord.risk_reviewer_id
    )
    visible = exists(
        select(1).where(
            ReviewRecord.contract_id == Contract.id,
            (
                (ReviewRecord.review_stage == stage)
                & ((reviewer_id.is_(None)) | (reviewer_id == user.id))
            )
            | (reviewer_id == user.id),
        )
    )
    return query.where(visible)


@router.get("/contracts")
def list_contracts(
    user: CurrentUser,
    db: Db,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, alias="pageSize", ge=1, le=100),
    owner_id: int | None = Query(None, alias="ownerId"),
    contract_status: str | None = Query(None, alias="contractStatus"),
    contract_type: str | None = Query(None, alias="contractType"),
) -> dict[str, object]:
    if owner_id is not None and user.role != "admin":
        raise fail("PERMISSION_DENIED")
    query = select(Contract).where(Contract.deleted_at.is_(None))
    query = contracts_scope(query, user)
    if owner_id is not None:
        query = query.where(Contract.owner_id == owner_id)
    if contract_status:
        query = query.where(Contract.status == contract_status)
    if contract_type:
        query = query.where(Contract.contract_type == contract_type)
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    rows = db.scalars(
        query.order_by(Contract.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    ).all()
    return result(
        {
            "items": [
                {
                    "contractId": x.id,
                    "name": x.name,
                    "contractType": x.contract_type,
                    "contractStatus": x.status,
                    "ownerId": x.owner_id,
                    "createdAt": x.created_at,
                }
                for x in rows
            ],
            "total": total,
        }
    )


def accessible_contract(db: Session, contract_id: int, user: User) -> Contract:
    contract = db.scalar(
        select(Contract).where(Contract.id == contract_id, Contract.deleted_at.is_(None))
    )
    if not contract:
        raise fail("CONTRACT_NOT_FOUND")
    if user.role == "admin" or contract.owner_id == user.id:
        return contract
    scoped = contracts_scope(select(Contract).where(Contract.id == contract.id), user)
    if not db.scalar(scoped):
        raise fail("CONTRACT_NOT_FOUND")
    return contract


@router.get("/contracts/{contractId}")
def get_contract(
    contract_id: Annotated[int, Path(alias="contractId")], user: CurrentUser, db: Db
) -> dict[str, object]:
    contract = accessible_contract(db, contract_id, user)
    files = db.scalars(select(ContractFile).where(ContractFile.contract_id == contract.id)).all()
    latest_review = db.scalar(
        select(ReviewRecord)
        .where(ReviewRecord.contract_id == contract.id)
        .order_by(ReviewRecord.created_at.desc(), ReviewRecord.id.desc())
        .limit(1)
    )
    return result(
        {
            "contractId": contract.id,
            "name": contract.name,
            "contractType": contract.contract_type,
            "contractStatus": contract.status,
            "files": [
                {
                    "contractFileId": item.id,
                    "fileName": item.file_name,
                    "fileType": item.file_type,
                    "fileSize": item.file_size,
                    "sha256": item.sha256,
                }
                for item in files
            ],
            "latestReview": (
                {
                    "reviewId": latest_review.id,
                    "reviewStatus": latest_review.status,
                    "reviewStage": latest_review.review_stage,
                    "legalReviewerId": latest_review.legal_reviewer_id,
                    "riskReviewerId": latest_review.risk_reviewer_id,
                }
                if latest_review
                else None
            ),
        }
    )


@router.get("/contracts/{contractId}/files/{contractFileId}/download")
def download_contract_file(
    contract_id: Annotated[int, Path(alias="contractId")],
    contract_file_id: Annotated[int, Path(alias="contractFileId")],
    user: CurrentUser,
    db: Db,
):
    contract = accessible_contract(db, contract_id, user)
    contract_file = db.scalar(
        select(ContractFile).where(
            ContractFile.id == contract_file_id,
            ContractFile.contract_id == contract.id,
        )
    )
    if contract_file is None:
        raise fail("CONTRACT_FILE_NOT_FOUND")
    path = upload_path(contract_file.storage_path)
    if not path.is_file():
        raise fail("CONTRACT_FILE_NOT_FOUND")
    media_types = {
        "pdf": "application/pdf",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "image": "application/octet-stream",
    }
    return FileResponse(
        path,
        media_type=media_types.get(contract_file.file_type, "application/octet-stream"),
        filename=contract_file.file_name,
        content_disposition_type="attachment",
    )


@router.delete("/contracts/{contractId}")
def delete_contract(
    contract_id: Annotated[int, Path(alias="contractId")], user: CurrentUser, db: Db
) -> dict[str, object]:
    contract = accessible_contract(db, contract_id, user)
    if user.role not in {"admin", "user"} or (user.role == "user" and contract.owner_id != user.id):
        raise fail("PERMISSION_DENIED")
    contract.deleted_at, contract.status = utcnow(), "deleted"
    db.commit()
    return result({"contractId": contract.id, "contractStatus": contract.status})


@router.post("/reviews")
def create_review(
    body: ReviewIn,
    user: CurrentUser,
    db: Db,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> dict[str, object]:
    if user.role != "user":
        raise fail("PERMISSION_DENIED")
    if not idempotency_key or len(idempotency_key) > 255:
        raise fail("PARAM_INVALID")
    previous = db.scalar(
        select(ReviewRecord).where(
            ReviewRecord.idempotency_user_id == user.id,
            ReviewRecord.idempotency_key == idempotency_key,
        )
    )
    if previous:
        if (
            previous.contract_id,
            previous.contract_file_id,
            previous.review_mode,
            previous.source_warning_id,
        ) != (
            body.contract_id,
            body.contract_file_id,
            body.review_mode,
            body.source_warning_id,
        ):
            raise fail("IDEMPOTENCY_CONFLICT")
        return result(
            {
                "reviewId": previous.id,
                "reviewStatus": previous.status,
                "reviewStage": previous.review_stage,
                "requestId": previous.request_id,
            }
        )
    contract = db.get(Contract, body.contract_id)
    if not contract:
        raise fail("CONTRACT_NOT_FOUND")
    if contract.owner_id != user.id:
        raise fail("PERMISSION_DENIED")
    if contract.deleted_at or contract.status == "deleted":
        raise fail("CONTRACT_DELETED")
    contract_file = db.scalar(
        select(ContractFile).where(
            ContractFile.id == body.contract_file_id, ContractFile.contract_id == contract.id
        )
    )
    if not contract_file:
        raise fail("CONTRACT_FILE_NOT_FOUND")
    warning = None
    if body.source_warning_id is not None:
        warning = db.scalar(
            select(RiskWarning)
            .where(RiskWarning.id == body.source_warning_id)
            .with_for_update()
        )
        if warning is None or warning.owner_id != user.id:
            raise fail("WARNING_NOT_FOUND")
        if warning.contract_id != contract.id or warning.warning_status != "active":
            raise fail("WARNING_STATUS_INVALID")
        if warning.acknowledged_at is None:
            raise fail("WARNING_ACKNOWLEDGEMENT_REQUIRED")
        if warning.remediation_review_id is not None:
            raise fail("WARNING_REMEDIATION_REVIEW_INVALID")
    running = db.scalar(
        select(ReviewRecord.id).where(
            ReviewRecord.contract_id == contract.id,
            ReviewRecord.status.in_(("pending", "processing")),
        )
    )
    if running:
        raise fail("REVIEW_ALREADY_RUNNING")
    review = ReviewRecord(
        contract_id=contract.id,
        contract_file_id=contract_file.id,
        file_sha256=contract_file.sha256,
        idempotency_user_id=user.id,
        idempotency_key=idempotency_key,
        request_id=new_request_id(),
        review_mode=body.review_mode,
        source_warning_id=body.source_warning_id,
        status="pending",
        review_stage="aiReview",
        ai_warnings=[],
        missing_clauses=[],
    )
    contract.status = "reviewing"
    db.add(review)
    try:
        db.flush()
        if warning is not None:
            begin_remediation(db, warning.id, user, contract.id, review)
        db.commit()
    except Exception:
        db.rollback()
        raise
    return result(
        {
            "reviewId": review.id,
            "reviewStatus": review.status,
            "reviewStage": review.review_stage,
            "requestId": review.request_id,
        }
    )


def accessible_review(db: Session, review_id: int, user: User) -> ReviewRecord:
    review = db.get(ReviewRecord, review_id)
    if not review:
        raise fail("REVIEW_NOT_FOUND")
    contract = db.get(Contract, review.contract_id)
    if readable(review, contract, user.id, user.role):
        return review
    raise fail("REVIEW_NOT_FOUND")


@router.get("/reviews")
def list_reviews(
    user: CurrentUser,
    db: Db,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, alias="pageSize", ge=1, le=100),
    contract_id: int | None = Query(None, alias="contractId"),
    review_status: str | None = Query(None, alias="reviewStatus"),
    review_stage: str | None = Query(None, alias="reviewStage"),
    owner_id: int | None = Query(None, alias="ownerId"),
) -> dict[str, object]:
    if owner_id is not None and user.role != "admin":
        raise fail("PERMISSION_DENIED")
    query = select(ReviewRecord).join(Contract, Contract.id == ReviewRecord.contract_id)
    if user.role == "user":
        query = query.where(Contract.owner_id == user.id)
    elif user.role == LEGAL:
        query = query.where(
            (
                (ReviewRecord.review_stage == "legalReview")
                & (ReviewRecord.legal_reviewer_id.is_(None))
            )
            | (ReviewRecord.legal_reviewer_id == user.id)
        )
    elif user.role == RISK:
        query = query.where(
            (
                (ReviewRecord.review_stage == "riskReview")
                & (ReviewRecord.risk_reviewer_id.is_(None))
            )
            | (ReviewRecord.risk_reviewer_id == user.id)
        )
    if contract_id is not None:
        query = query.where(ReviewRecord.contract_id == contract_id)
    if review_status:
        query = query.where(ReviewRecord.status == review_status)
    if review_stage:
        query = query.where(ReviewRecord.review_stage == review_stage)
    if owner_id is not None:
        query = query.where(Contract.owner_id == owner_id)
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    rows = db.scalars(
        query.order_by(ReviewRecord.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return result(
        {
            "items": [
                {
                    "reviewId": row.id,
                    "contractId": row.contract_id,
                    "reviewStatus": row.status,
                    "reviewStage": row.review_stage,
                    "reviewMode": row.review_mode,
                    "legalReviewerId": row.legal_reviewer_id,
                    "riskReviewerId": row.risk_reviewer_id,
                    "createdAt": row.created_at,
                }
                for row in rows
            ],
            "total": total,
        }
    )


@router.get("/reviews/{reviewId}/progress")
def review_progress(
    review_id: Annotated[int, Path(alias="reviewId")], user: CurrentUser, db: Db
) -> dict[str, object]:
    review = accessible_review(db, review_id, user)
    progress = {
        ("pending", "aiReview"): 0,
        ("processing", "aiReview"): 25,
        ("processing", "legalReview"): 60,
        ("processing", "riskReview"): 80,
        ("completed", "completed"): 100,
    }.get((review.status, review.review_stage), 0)
    return result(
        {
            "reviewId": review.id,
            "reviewStatus": review.status,
            "reviewStage": review.review_stage,
            "progress": progress,
            "aiResultAvailable": review.ai_result_json is not None,
            "errorCode": review.error_code,
        }
    )


@router.get("/reviews/{reviewId}")
def get_review(
    review_id: Annotated[int, Path(alias="reviewId")], user: CurrentUser, db: Db
) -> dict[str, object]:
    review = accessible_review(db, review_id, user)
    if review.ai_result_json is None:
        raise fail("REVIEW_RESULT_NOT_READY")
    contract = db.get(Contract, review.contract_id)
    if not readable(review, contract, user.id, user.role):
        raise fail("REVIEW_NOT_FOUND")
    revision_rows = revisions(db, review.id)
    revision_data = [
        {
            "revisionId": x.id,
            "targetType": x.target_type,
            "targetId": x.target_id,
            "before": x.before_json,
            "after": x.after_json,
            "comment": x.comment,
            "createdAt": x.created_at,
        }
        for x in revision_rows
    ]
    current = effective(db, review)
    return result(
        {
            "reviewId": review.id,
            "reviewStatus": review.status,
            "reviewStage": review.review_stage,
            "aiResult": review.ai_result_json,
            "legalReview": {
                "reviewerId": review.legal_reviewer_id,
                "reviewedAt": review.legal_reviewed_at,
                "opinion": review.legal_opinion,
                "revisions": [
                    value
                    for value, row in zip(revision_data, revision_rows, strict=True)
                    if row.review_stage == "legalReview"
                ],
            },
            "riskReview": {
                "reviewerId": review.risk_reviewer_id,
                "reviewedAt": review.risk_reviewed_at,
                "opinion": review.risk_opinion,
                "revisions": [
                    value
                    for value, row in zip(revision_data, revision_rows, strict=True)
                    if row.review_stage == "riskReview"
                ],
                "overallRiskLevel": current.get("overallRiskLevel"),
                "overallScore": current.get("overallScore"),
            },
            "effectiveResult": current,
        }
    )


def _write(db: Session, fn):
    try:
        value = fn()
        db.commit()
        return result(value)
    except Exception:
        db.rollback()
        raise


@router.get("/warnings")
def list_warnings(
    user: CurrentUser,
    db: Db,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, alias="pageSize", ge=1, le=100),
    warning_status: str | None = Query(None, alias="warningStatus"),
) -> dict[str, object]:
    if warning_status is not None and warning_status not in WARNING_STATUSES:
        raise fail("PARAM_INVALID")
    query = scoped_warnings(select(RiskWarning), user)
    if warning_status is not None:
        query = query.where(RiskWarning.warning_status == warning_status)
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    rows = db.scalars(
        query.order_by(RiskWarning.created_at.desc(), RiskWarning.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    private = user.role in {LEGAL, RISK}
    return result(
        {"items": [warning_payload(db, row, private) for row in rows], "total": total}
    )


@router.get("/warnings/{warningId}")
def get_warning(
    warning_id: Annotated[int, Path(alias="warningId")], user: CurrentUser, db: Db
) -> dict[str, object]:
    warning = visible_warning(db, warning_id, user)
    private = user.role in {LEGAL, RISK}
    data = warning_payload(db, warning, private)
    if private:
        data["actions"] = warning_actions(db, warning.id)
    return result(data)


@router.post("/warnings/{warningId}/legal-confirm")
def confirm_warning_legal(
    warning_id: Annotated[int, Path(alias="warningId")],
    body: WarningCommentIn,
    user: CurrentUser,
    db: Db,
):
    return _write(
        db,
        lambda: warning_payload(
            db, warning_legal_confirm(db, warning_id, user, body.comment), True
        ),
    )


@router.post("/warnings/{warningId}/legal-withdraw")
def withdraw_warning_legal(
    warning_id: Annotated[int, Path(alias="warningId")],
    body: WarningCommentIn,
    user: CurrentUser,
    db: Db,
):
    return _write(
        db,
        lambda: warning_payload(
            db, warning_legal_withdraw(db, warning_id, user, body.comment), True
        ),
    )


@router.post("/warnings/{warningId}/risk-activate")
def activate_warning_risk(
    warning_id: Annotated[int, Path(alias="warningId")],
    body: WarningActivateIn,
    user: CurrentUser,
    db: Db,
):
    return _write(
        db,
        lambda: warning_payload(
            db, warning_risk_activate(db, warning_id, user, body.due_at, body.comment), True
        ),
    )


@router.post("/warnings/{warningId}/waive")
def waive_warning(
    warning_id: Annotated[int, Path(alias="warningId")],
    body: WarningCommentIn,
    user: CurrentUser,
    db: Db,
):
    return _write(db, lambda: warning_payload(db, warning_waive(db, warning_id, user, body.comment), True))


@router.post("/warnings/{warningId}/acknowledge")
def acknowledge_warning(
    warning_id: Annotated[int, Path(alias="warningId")], user: CurrentUser, db: Db
):
    return _write(db, lambda: warning_payload(db, warning_acknowledge(db, warning_id, user)))


@router.post("/warnings/{warningId}/close")
def close_warning(
    warning_id: Annotated[int, Path(alias="warningId")],
    body: WarningCommentIn,
    user: CurrentUser,
    db: Db,
):
    return _write(db, lambda: warning_payload(db, warning_close(db, warning_id, user, body.comment), True))


@router.post("/warnings/{warningId}/reopen")
def reopen_warning(
    warning_id: Annotated[int, Path(alias="warningId")],
    body: WarningReopenIn,
    user: CurrentUser,
    db: Db,
):
    return _write(
        db,
        lambda: warning_payload(
            db, warning_reopen(db, warning_id, user, body.due_at, body.comment), True
        ),
    )


def _review(db: Session, review_id: int) -> ReviewRecord:
    review = db.scalar(select(ReviewRecord).where(ReviewRecord.id == review_id).with_for_update())
    if not review:
        raise fail("REVIEW_NOT_FOUND")
    return review


@router.patch("/reviews/{reviewId}/contract-type")
def patch_contract_type(
    review_id: Annotated[int, Path(alias="reviewId")],
    body: ContractTypeIn,
    user: CurrentUser,
    db: Db,
):
    if user.role != LEGAL:
        raise fail("REVIEW_ROLE_NOT_ALLOWED")

    def go():
        revision = revise(
            db,
            review_id,
            user.id,
            LEGAL,
            "contractType",
            None,
            {"contractType": body.contract_type},
            body.comment,
            ACTIONS["contractType"],
        )
        return {
            "reviewId": review_id,
            "contractType": body.contract_type,
            "revisionId": revision.id,
        }

    return _write(db, go)


@router.patch("/reviews/{reviewId}/elements/{elementId}")
def patch_element(
    review_id: Annotated[int, Path(alias="reviewId")],
    element_id: Annotated[int, Path(alias="elementId")],
    body: ElementIn,
    user: CurrentUser,
    db: Db,
):
    if user.role != LEGAL:
        raise fail("REVIEW_ROLE_NOT_ALLOWED")

    def go():
        item = db.scalar(
            select(ContractElement).where(
                ContractElement.id == element_id, ContractElement.review_id == review_id
            )
        )
        if not item:
            raise fail("CONTRACT_ELEMENT_NOT_FOUND")
        after = {
            "elementId": item.id,
            "elementType": item.element_type,
            "elementName": item.element_name,
            "value": body.value,
            "page": item.page,
            "paragraphIndex": item.paragraph_index,
            "confidence": item.confidence,
        }
        revision = revise(
            db,
            review_id,
            user.id,
            LEGAL,
            "element",
            item.id,
            after,
            body.comment,
            ACTIONS["element"],
        )
        return {**after, "revisionId": revision.id}

    return _write(db, go)


@router.patch("/risks/{riskId}")
def patch_risk(
    risk_id: Annotated[int, Path(alias="riskId")], body: RiskIn, user: CurrentUser, db: Db
):
    if user.role not in {LEGAL, RISK}:
        raise fail("REVIEW_ROLE_NOT_ALLOWED")
    if user.role == LEGAL and "risk_status" in body.model_fields_set:
        raise fail("REVIEW_ROLE_NOT_ALLOWED")

    def go():
        item = db.get(RiskRecord, risk_id)
        if not item:
            raise fail("RISK_NOT_FOUND")
        review = db.get(ReviewRecord, item.review_id)
        if not review:
            raise fail("REVIEW_NOT_FOUND")
        current = next(x for x in effective(db, review)["risks"] if x["riskId"] == item.id)
        after = {
            **current,
            **{
                k: v
                for k, v in {
                    "riskLevel": body.risk_level,
                    "suggestion": body.suggestion,
                    "riskStatus": body.risk_status,
                }.items()
                if v is not None
            },
        }
        revision = revise(
            db,
            review.id,
            user.id,
            user.role,
            "risk",
            item.id,
            after,
            body.comment,
            ACTIONS["risk"],
        )
        return {**after, "revisionId": revision.id}

    return _write(db, go)


@router.get("/risks/{riskId}")
def get_risk(risk_id: Annotated[int, Path(alias="riskId")], user: CurrentUser, db: Db):
    item = db.get(RiskRecord, risk_id)
    if not item:
        raise fail("RISK_NOT_FOUND")
    review = accessible_review(db, item.review_id, user)
    risk = next(
        (value for value in effective(db, review)["risks"] if value["riskId"] == item.id),
        None,
    )
    if risk is None:
        raise fail("RISK_NOT_FOUND")
    return result({"reviewId": review.id, **risk})


@router.patch("/reviews/{reviewId}/overall-risk")
def patch_overall(
    review_id: Annotated[int, Path(alias="reviewId")],
    body: OverallRiskIn,
    user: CurrentUser,
    db: Db,
):
    if user.role != RISK:
        raise fail("REVIEW_ROLE_NOT_ALLOWED")

    def go():
        after = {"overallRiskLevel": body.overall_risk_level, "overallScore": body.overall_score}
        revision = revise(
            db,
            review_id,
            user.id,
            RISK,
            "overallRisk",
            None,
            after,
            body.comment,
            ACTIONS["overallRisk"],
        )
        return {"reviewId": review_id, **after, "revisionId": revision.id}

    return _write(db, go)


@router.post("/reviews/{reviewId}/feedback")
def create_feedback(
    review_id: Annotated[int, Path(alias="reviewId")],
    body: FeedbackIn,
    user: CurrentUser,
    db: Db,
):
    if user.role not in {LEGAL, RISK}:
        raise fail("REVIEW_ROLE_NOT_ALLOWED")

    def go():
        review = claim(db, review_id, user.id, user.role)
        allowed = (
            {"contractType", "element", "risk"} if user.role == LEGAL else {"risk", "overallRisk"}
        )
        if body.target_type not in allowed:
            raise fail("FEEDBACK_INVALID")
        if body.target_type == "element" and not db.scalar(
            select(ContractElement.id).where(
                ContractElement.id == body.target_id,
                ContractElement.review_id == review.id,
            )
        ):
            raise fail("FEEDBACK_INVALID")
        if body.target_type == "risk" and not db.scalar(
            select(RiskRecord.id).where(
                RiskRecord.id == body.target_id,
                RiskRecord.review_id == review.id,
            )
        ):
            raise fail("FEEDBACK_INVALID")
        feedback = ReviewFeedback(
            review_id=review.id,
            target_type=body.target_type,
            target_id=body.target_id,
            user_id=user.id,
            judgment=body.judgment,
            corrected_value=body.corrected_value,
            comment=body.comment,
        )
        db.add(feedback)
        db.flush()
        add_log(
            db,
            user.id,
            user.role,
            ACTIONS["feedback"],
            review,
            body.target_type,
            body.target_id,
        )
        return {"feedbackId": feedback.id}

    return _write(db, go)


@router.post("/reviews/{reviewId}/legal-confirm")
def legal_confirm(
    review_id: Annotated[int, Path(alias="reviewId")],
    body: OpinionIn,
    user: CurrentUser,
    db: Db,
):
    if user.role != LEGAL:
        raise fail("REVIEW_ROLE_NOT_ALLOWED")

    def go():
        review = claim(db, review_id, user.id, LEGAL)
        review.legal_opinion = body.opinion
        review.legal_reviewed_at = utcnow()
        add_log(db, user.id, LEGAL, ACTIONS["legalConfirm"], review)
        review.review_stage = "riskReview"
        return {
            "reviewId": review.id,
            "reviewStatus": review.status,
            "reviewStage": review.review_stage,
            "legalReview": {
                "reviewerId": review.legal_reviewer_id,
                "reviewedAt": review.legal_reviewed_at,
                "opinion": review.legal_opinion,
            },
        }

    return _write(db, go)


@router.post("/reviews/{reviewId}/risk-confirm")
def risk_confirm(
    review_id: Annotated[int, Path(alias="reviewId")],
    body: OpinionIn,
    user: CurrentUser,
    db: Db,
):
    if user.role != RISK:
        raise fail("REVIEW_ROLE_NOT_ALLOWED")

    def go():
        review = claim(db, review_id, user.id, RISK)
        if review.legal_reviewer_id is None or review.legal_reviewed_at is None:
            raise fail("REVIEW_LEGAL_NOT_COMPLETED")
        review.risk_opinion = body.opinion
        review.risk_reviewed_at = utcnow()
        add_log(db, user.id, RISK, ACTIONS["riskConfirm"], review)
        review.status = "completed"
        review.review_stage = "completed"
        contract = db.get(Contract, review.contract_id)
        if contract:
            contract.status = "reviewed"
        report = db.scalar(
            select(Report).where(Report.review_id == review.id, Report.format == "html")
        )
        if report is None:
            report = Report(review_id=review.id, format="html", status="pending")
            db.add(report)
            db.flush()
        return {
            "reviewId": review.id,
            "reviewStatus": review.status,
            "reviewStage": review.review_stage,
            "riskReview": {
                "reviewerId": review.risk_reviewer_id,
                "reviewedAt": review.risk_reviewed_at,
                "opinion": review.risk_opinion,
            },
        }

    return _write(db, go)


def _admin_write(
    db: Session, operation: Callable[[], dict[str, object]], conflict_code: str | None = None
):
    try:
        value = operation()
        db.commit()
        return result(value)
    except IntegrityError:
        db.rollback()
        raise fail(conflict_code or "DATABASE_ERROR")
    except Exception:
        db.rollback()
        raise


def _validate_admin_filters(
    *,
    role: str | None = None,
    status: str | None = None,
    contract_type: str | None = None,
    risk_type: str | None = None,
    risk_level: str | None = None,
) -> None:
    if role is not None and role not in ROLES:
        raise fail("PARAM_INVALID")
    if status is not None and status not in USER_STATUSES:
        raise fail("PARAM_INVALID")
    if contract_type is not None and contract_type not in CONTRACT_TYPES:
        raise fail("PARAM_INVALID")
    if risk_type is not None and risk_type not in RISK_TYPES:
        raise fail("PARAM_INVALID")
    if risk_level is not None and risk_level not in RISK_LEVELS:
        raise fail("PARAM_INVALID")


def _validate_range(start: datetime | None, end: datetime | None) -> None:
    if start is not None and end is not None and start > end:
        raise fail("PARAM_INVALID")


@router.get("/users")
def admin_list_users(
    user: CurrentUser,
    db: Db,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, alias="pageSize", ge=1, le=100),
    username: str | None = None,
    role: str | None = None,
    user_status: str | None = Query(None, alias="userStatus"),
) -> dict[str, object]:
    require_admin(user)
    _validate_admin_filters(role=role, status=user_status)
    query = select(User).where(User.deleted_at.is_(None))
    if username is not None:
        username = username.strip()
        if not username:
            raise fail("PARAM_INVALID")
        query = query.where(User.username.contains(username, autoescape=True))
    if role is not None:
        query = query.where(User.role == role)
    if user_status is not None:
        query = query.where(User.status == user_status)
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    rows = db.scalars(
        query.order_by(User.created_at.desc(), User.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return result({"items": [admin_public_user(row) for row in rows], "total": total})


@router.post("/users")
def admin_create_user(body: UserCreateIn, user: CurrentUser, db: Db) -> dict[str, object]:
    require_admin(user)

    def go() -> dict[str, object]:
        if db.scalar(select(User).where(User.username == body.username)) is not None:
            raise fail("USER_USERNAME_EXISTS")
        target = User(
            username=body.username,
            password_hash=hash_password(body.password),
            role=body.role,
            status="active",
        )
        db.add(target)
        db.flush()
        after = admin_public_user(target)
        add_admin_log(
            db, user, ADMIN_ACTIONS["userCreated"], "user", target.id, None, after
        )
        return after

    return _admin_write(db, go, "USER_USERNAME_EXISTS")


@router.get("/users/{userId}")
def admin_get_user(
    user_id: Annotated[int, Path(alias="userId")], user: CurrentUser, db: Db
) -> dict[str, object]:
    require_admin(user)
    target = db.scalar(select(User).where(User.id == user_id, User.deleted_at.is_(None)))
    if target is None:
        raise fail("USER_NOT_FOUND")
    return result(admin_public_user(target))


@router.patch("/users/{userId}")
def admin_update_user(
    user_id: Annotated[int, Path(alias="userId")],
    body: UserUpdateIn,
    user: CurrentUser,
    db: Db,
) -> dict[str, object]:
    require_admin(user)

    def go() -> dict[str, object]:
        target = db.scalar(
            select(User).where(User.id == user_id, User.deleted_at.is_(None)).with_for_update()
        )
        if target is None:
            raise fail("USER_NOT_FOUND")
        values = body.model_dump(exclude_unset=True)
        if target.id == user.id and (
            values.get("role", target.role) != "admin"
            or values.get("user_status", target.status) != "active"
        ):
            raise fail("USER_SELF_UPDATE_FORBIDDEN")
        before = admin_public_user(target)
        if "username" in values:
            target.username = values["username"]
        if "role" in values:
            target.role = values["role"]
        if "user_status" in values:
            target.status = values["user_status"]
        db.flush()
        after = admin_public_user(target)
        add_admin_log(
            db, user, ADMIN_ACTIONS["userUpdated"], "user", target.id, before, after
        )
        return after

    return _admin_write(db, go, "USER_USERNAME_EXISTS")


@router.get("/standard-clauses")
def admin_list_clauses(
    user: CurrentUser,
    db: Db,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, alias="pageSize", ge=1, le=100),
    name: str | None = None,
    contract_type: str | None = Query(None, alias="contractType"),
    clause_type: str | None = Query(None, alias="clauseType"),
    config_status: str | None = Query(None, alias="configStatus"),
) -> dict[str, object]:
    require_admin(user)
    _validate_admin_filters(status=config_status, contract_type=contract_type)
    query = select(StandardClause)
    if name is not None:
        name = name.strip()
        if not name:
            raise fail("PARAM_INVALID")
        query = query.where(StandardClause.name.contains(name, autoescape=True))
    if contract_type is not None:
        query = query.where(StandardClause.contract_type == contract_type)
    if clause_type is not None:
        query = query.where(StandardClause.clause_type == clause_type)
    if config_status is not None:
        query = query.where(StandardClause.status == config_status)
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    rows = db.scalars(
        query.order_by(StandardClause.created_at.desc(), StandardClause.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return result({"items": [public_clause(row) for row in rows], "total": total})


@router.get("/standard-clauses/{clauseId}")
def admin_get_clause(
    clause_id: Annotated[int, Path(alias="clauseId")], user: CurrentUser, db: Db
) -> dict[str, object]:
    require_admin(user)
    clause = db.get(StandardClause, clause_id)
    if clause is None:
        raise fail("STANDARD_CLAUSE_NOT_FOUND")
    return result(public_clause(clause))


@router.post("/standard-clauses")
def admin_create_clause(
    body: StandardClauseCreateIn, user: CurrentUser, db: Db
) -> dict[str, object]:
    require_admin(user)

    def go() -> dict[str, object]:
        clause = StandardClause(
            name=body.name,
            contract_type=body.contract_type,
            clause_type=body.clause_type,
            content=body.content,
            status=body.config_status,
        )
        db.add(clause)
        db.flush()
        after = public_clause(clause)
        add_admin_log(
            db, user, ADMIN_ACTIONS["clauseCreated"], "standardClause", clause.id, None, after
        )
        return after

    return _admin_write(db, go, "STANDARD_CLAUSE_EXISTS")


@router.patch("/standard-clauses/{clauseId}")
def admin_update_clause(
    clause_id: Annotated[int, Path(alias="clauseId")],
    body: StandardClauseUpdateIn,
    user: CurrentUser,
    db: Db,
) -> dict[str, object]:
    require_admin(user)

    def go() -> dict[str, object]:
        clause = db.scalar(
            select(StandardClause).where(StandardClause.id == clause_id).with_for_update()
        )
        if clause is None:
            raise fail("STANDARD_CLAUSE_NOT_FOUND")
        before = public_clause(clause)
        values = body.model_dump(exclude_unset=True)
        for field, value in values.items():
            setattr(clause, "status" if field == "config_status" else field, value)
        db.flush()
        after = public_clause(clause)
        add_admin_log(
            db, user, ADMIN_ACTIONS["clauseUpdated"], "standardClause", clause.id, before, after
        )
        return after

    return _admin_write(db, go, "STANDARD_CLAUSE_EXISTS")


@router.delete("/standard-clauses/{clauseId}")
def admin_delete_clause(
    clause_id: Annotated[int, Path(alias="clauseId")], user: CurrentUser, db: Db
) -> dict[str, object]:
    require_admin(user)

    def go() -> dict[str, object]:
        clause = db.scalar(
            select(StandardClause).where(StandardClause.id == clause_id).with_for_update()
        )
        if clause is None:
            raise fail("STANDARD_CLAUSE_NOT_FOUND")
        before = public_clause(clause)
        clause.status = "disabled"
        db.flush()
        after = public_clause(clause)
        add_admin_log(
            db, user, ADMIN_ACTIONS["clauseDeleted"], "standardClause", clause.id, before, after
        )
        return after

    return _admin_write(db, go)


@router.get("/risk-rules")
def admin_list_rules(
    user: CurrentUser,
    db: Db,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, alias="pageSize", ge=1, le=100),
    rule_code: str | None = Query(None, alias="ruleCode"),
    name: str | None = None,
    risk_type: str | None = Query(None, alias="riskType"),
    risk_level: str | None = Query(None, alias="riskLevel"),
    config_status: str | None = Query(None, alias="configStatus"),
) -> dict[str, object]:
    require_admin(user)
    _validate_admin_filters(status=config_status, risk_type=risk_type, risk_level=risk_level)
    query = select(RiskRule)
    if rule_code is not None:
        query = query.where(RiskRule.rule_code == rule_code.strip())
    if name is not None:
        name = name.strip()
        if not name:
            raise fail("PARAM_INVALID")
        query = query.where(RiskRule.name.contains(name, autoescape=True))
    if risk_type is not None:
        query = query.where(RiskRule.risk_type == risk_type)
    if risk_level is not None:
        query = query.where(RiskRule.risk_level == risk_level)
    if config_status is not None:
        query = query.where(RiskRule.status == config_status)
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    rows = db.scalars(
        query.order_by(RiskRule.created_at.desc(), RiskRule.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return result({"items": [public_rule(row) for row in rows], "total": total})


@router.get("/risk-rules/{ruleId}")
def admin_get_rule(
    rule_id: Annotated[int, Path(alias="ruleId")], user: CurrentUser, db: Db
) -> dict[str, object]:
    require_admin(user)
    rule = db.get(RiskRule, rule_id)
    if rule is None:
        raise fail("RISK_RULE_NOT_FOUND")
    return result(public_rule(rule))


def _check_standard_clause(db: Session, clause_id: int | None) -> None:
    if clause_id is not None and db.get(StandardClause, clause_id) is None:
        raise fail("STANDARD_CLAUSE_NOT_FOUND")


@router.post("/risk-rules")
def admin_create_rule(
    body: RiskRuleCreateIn, user: CurrentUser, db: Db
) -> dict[str, object]:
    require_admin(user)

    def go() -> dict[str, object]:
        _check_standard_clause(db, body.standard_clause_id)
        rule = RiskRule(
            rule_code=body.rule_code,
            risk_type=body.risk_type,
            name=body.name,
            risk_level=body.risk_level,
            rule_content=body.rule_content,
            standard_clause_id=body.standard_clause_id,
            status=body.config_status,
            warning_enabled=body.warning_enabled,
            warning_due_hours=body.warning_due_hours,
        )
        db.add(rule)
        db.flush()
        after = public_rule(rule)
        add_admin_log(db, user, ADMIN_ACTIONS["ruleCreated"], "riskRule", rule.id, None, after)
        return after

    return _admin_write(db, go, "RISK_RULE_EXISTS")


@router.patch("/risk-rules/{ruleId}")
def admin_update_rule(
    rule_id: Annotated[int, Path(alias="ruleId")],
    body: RiskRuleUpdateIn,
    user: CurrentUser,
    db: Db,
) -> dict[str, object]:
    require_admin(user)

    def go() -> dict[str, object]:
        rule = db.scalar(select(RiskRule).where(RiskRule.id == rule_id).with_for_update())
        if rule is None:
            raise fail("RISK_RULE_NOT_FOUND")
        values = body.model_dump(exclude_unset=True)
        if "standard_clause_id" in values:
            _check_standard_clause(db, values["standard_clause_id"])
        before = public_rule(rule)
        for field, value in values.items():
            setattr(rule, "status" if field == "config_status" else field, value)
        db.flush()
        after = public_rule(rule)
        add_admin_log(db, user, ADMIN_ACTIONS["ruleUpdated"], "riskRule", rule.id, before, after)
        return after

    return _admin_write(db, go, "RISK_RULE_EXISTS")


@router.delete("/risk-rules/{ruleId}")
def admin_delete_rule(
    rule_id: Annotated[int, Path(alias="ruleId")], user: CurrentUser, db: Db
) -> dict[str, object]:
    require_admin(user)

    def go() -> dict[str, object]:
        rule = db.scalar(select(RiskRule).where(RiskRule.id == rule_id).with_for_update())
        if rule is None:
            raise fail("RISK_RULE_NOT_FOUND")
        before = public_rule(rule)
        rule.status = "disabled"
        db.flush()
        after = public_rule(rule)
        add_admin_log(db, user, ADMIN_ACTIONS["ruleDeleted"], "riskRule", rule.id, before, after)
        return after

    return _admin_write(db, go)


@router.get("/feedback")
def admin_list_feedback(
    user: CurrentUser,
    db: Db,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, alias="pageSize", ge=1, le=100),
    review_id: int | None = Query(None, alias="reviewId"),
    contract_id: int | None = Query(None, alias="contractId"),
    submitter_id: int | None = Query(None, alias="submitterId"),
    submitter_role: str | None = Query(None, alias="submitterRole"),
    feedback_type: str | None = Query(None, alias="feedbackType"),
    judgment: str | None = None,
    start: datetime | None = Query(None, alias="from"),
    end: datetime | None = Query(None, alias="to"),
) -> dict[str, object]:
    require_admin(user)
    _validate_admin_filters(role=submitter_role)
    _validate_range(start, end)
    query = (
        select(ReviewFeedback, ReviewRecord.contract_id, User.role)
        .join(ReviewRecord, ReviewRecord.id == ReviewFeedback.review_id)
        .join(User, User.id == ReviewFeedback.user_id)
    )
    if review_id is not None:
        query = query.where(ReviewFeedback.review_id == review_id)
    if contract_id is not None:
        query = query.where(ReviewRecord.contract_id == contract_id)
    if submitter_id is not None:
        query = query.where(ReviewFeedback.user_id == submitter_id)
    if submitter_role is not None:
        query = query.where(User.role == submitter_role)
    if feedback_type is not None:
        query = query.where(ReviewFeedback.target_type == feedback_type)
    if judgment is not None:
        query = query.where(ReviewFeedback.judgment == judgment)
    if start is not None:
        query = query.where(ReviewFeedback.created_at >= start)
    if end is not None:
        query = query.where(ReviewFeedback.created_at <= end)
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    rows = db.execute(
        query.order_by(ReviewFeedback.created_at.desc(), ReviewFeedback.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return result(
        {
            "items": [
                {
                    "feedbackId": item.id,
                    "reviewId": item.review_id,
                    "contractId": row_contract_id,
                    "targetType": item.target_type,
                    "targetId": item.target_id,
                    "submitterId": item.user_id,
                    "submitterRole": row_role,
                    "judgment": item.judgment,
                    "correctedValue": item.corrected_value,
                    "comment": item.comment,
                    "createdAt": item.created_at,
                }
                for item, row_contract_id, row_role in rows
            ],
            "total": total,
        }
    )


@router.get("/operation-logs")
def admin_list_logs(
    user: CurrentUser,
    db: Db,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, alias="pageSize", ge=1, le=100),
    operator_id: int | None = Query(None, alias="operatorId"),
    operator_role: str | None = Query(None, alias="operatorRole"),
    action: str | None = None,
    target_type: str | None = Query(None, alias="targetType"),
    target_id: int | None = Query(None, alias="targetId"),
    review_id: int | None = Query(None, alias="reviewId"),
    start: datetime | None = Query(None, alias="from"),
    end: datetime | None = Query(None, alias="to"),
) -> dict[str, object]:
    require_admin(user)
    _validate_admin_filters(role=operator_role)
    _validate_range(start, end)
    query = select(OperationLog, User.role).outerjoin(User, User.id == OperationLog.user_id)
    if operator_id is not None:
        query = query.where(OperationLog.user_id == operator_id)
    if operator_role is not None:
        query = query.where(User.role == operator_role)
    if action is not None:
        query = query.where(OperationLog.action == action)
    if target_type is not None:
        query = query.where(OperationLog.resource_type == target_type)
    if target_id is not None:
        query = query.where(OperationLog.resource_id == target_id)
    if review_id is not None:
        query = query.where(
            OperationLog.resource_type == "review", OperationLog.resource_id == review_id
        )
    if start is not None:
        query = query.where(OperationLog.created_at >= start)
    if end is not None:
        query = query.where(OperationLog.created_at <= end)
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    rows = db.execute(
        query.order_by(OperationLog.created_at.desc(), OperationLog.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    items = []
    for log, stored_role in rows:
        detail = redact(log.detail_json or {})
        items.append(
            {
                "logId": log.id,
                "operatorId": log.user_id,
                "operatorRole": detail.get("operatorRole", detail.get("actorRole", stored_role)),
                "action": log.action,
                "targetType": log.resource_type,
                "targetId": log.resource_id,
                "beforeValue": detail.get("beforeValue"),
                "afterValue": detail.get("afterValue"),
                "detail": detail,
                "ip": log.ip,
                "createdAt": log.created_at,
            }
        )
    return result({"items": items, "total": total})


@router.get("/dashboard/summary")
def admin_dashboard(
    user: CurrentUser,
    db: Db,
    start: datetime | None = Query(None, alias="from"),
    end: datetime | None = Query(None, alias="to"),
) -> dict[str, object]:
    require_admin(user)
    return result(dashboard_data(db, start, end))


def _public_report(report: Report) -> dict[str, object]:
    return {
        "reportId": report.id,
        "reviewId": report.review_id,
        "reportFormat": report.format,
        "reportStatus": report.status,
        "attemptCount": report.attempt_count,
        "errorCode": report.error_code,
        "fileSize": report.file_size,
        "sha256": report.sha256,
        "generatedAt": report.generated_at,
        "createdAt": report.created_at,
        "updatedAt": report.updated_at,
    }


def _report_access(db: Session, report_id: int, user: User) -> tuple[Report, ReviewRecord, Contract]:
    report = db.get(Report, report_id)
    if report is None:
        raise fail("REPORT_NOT_FOUND")
    review = db.get(ReviewRecord, report.review_id)
    contract = db.get(Contract, review.contract_id) if review else None
    if review is None or contract is None or not readable(review, contract, user.id, user.role):
        raise fail("REPORT_NOT_FOUND")
    return report, review, contract


def _report_ready(review: ReviewRecord, contract: Contract) -> bool:
    return (
        review.status == "completed"
        and review.review_stage == "completed"
        and review.ai_result_json is not None
        and review.legal_reviewer_id is not None
        and review.risk_reviewer_id is not None
        and review.legal_reviewed_at is not None
        and review.risk_reviewed_at is not None
        and contract.deleted_at is None
    )


@router.get("/reviews/{reviewId}/reports")
def list_reports(
    review_id: Annotated[int, Path(alias="reviewId")],
    user: CurrentUser,
    db: Db,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, alias="pageSize", ge=1, le=100),
) -> dict[str, object]:
    accessible_review(db, review_id, user)
    query = select(Report).where(Report.review_id == review_id)
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    rows = db.scalars(
        query.order_by(Report.created_at.desc(), Report.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return result({"items": [_public_report(row) for row in rows], "total": total})


@router.post("/reviews/{reviewId}/reports")
def create_report(
    review_id: Annotated[int, Path(alias="reviewId")],
    body: ReportCreateIn,
    user: CurrentUser,
    db: Db,
) -> dict[str, object]:
    if body.report_format not in {"html", "pdf"}:
        raise fail("REPORT_FORMAT_UNSUPPORTED")
    review = db.get(ReviewRecord, review_id)
    contract = db.get(Contract, review.contract_id) if review else None
    if review is None or contract is None:
        raise fail("REVIEW_NOT_FOUND")
    if user.role == "user":
        if contract.owner_id != user.id:
            raise fail("REVIEW_NOT_FOUND")
    elif user.role != "admin":
        raise fail("PERMISSION_DENIED")
    if not _report_ready(review, contract):
        raise fail("REPORT_NOT_READY")
    existing = db.scalar(
        select(Report).where(Report.review_id == review.id, Report.format == body.report_format)
    )
    if existing is not None:
        return result(_public_report(existing))
    report = Report(review_id=review.id, format=body.report_format, status="pending")
    db.add(report)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        existing = db.scalar(
            select(Report).where(Report.review_id == review.id, Report.format == body.report_format)
        )
        if existing is None:
            raise fail("DATABASE_ERROR")
        report = existing
    return result(_public_report(report))


@router.get("/reports/{reportId}")
def get_report(
    report_id: Annotated[int, Path(alias="reportId")], user: CurrentUser, db: Db
) -> dict[str, object]:
    report, _, _ = _report_access(db, report_id, user)
    return result(_public_report(report))


@router.post("/reports/{reportId}/retry")
def retry_report(
    report_id: Annotated[int, Path(alias="reportId")], user: CurrentUser, db: Db
) -> dict[str, object]:
    if user.role != "admin":
        raise fail("PERMISSION_DENIED")

    def go() -> dict[str, object]:
        report = db.scalar(select(Report).where(Report.id == report_id).with_for_update())
        if report is None:
            raise fail("REPORT_NOT_FOUND")
        if report.status != "failed":
            raise fail("REPORT_NOT_READY")
        if report.attempt_count >= settings.report_max_attempts:
            raise fail("REPORT_GENERATION_FAILED")
        report.status = "pending"
        report.started_at = None
        report.error_code = None
        report.error_message = None
        report.storage_path = None
        report.file_size = None
        report.sha256 = None
        report.generated_at = None
        return _public_report(report)

    return _write(db, go)


@router.get("/reports/{reportId}/download")
def download_report(
    report_id: Annotated[int, Path(alias="reportId")], user: CurrentUser, db: Db
):
    report, _, contract = _report_access(db, report_id, user)
    if report.status in {"pending", "generating"}:
        raise fail("REPORT_NOT_READY")
    if report.status == "failed":
        raise fail("REPORT_GENERATION_FAILED")
    if report.status != "completed" or report.storage_path is None:
        raise fail("REPORT_FILE_NOT_FOUND")
    try:
        path = report_path(report.storage_path)
    except AppError:
        logger.warning("report_file_invalid report_id=%s", report.id)
        raise
    if not path.is_file() or (report.file_size is not None and path.stat().st_size != report.file_size):
        logger.warning("report_file_missing report_id=%s", report.id)
        raise fail("REPORT_FILE_NOT_FOUND")
    media_type = "text/html; charset=utf-8" if report.format == "html" else "application/pdf"
    return FileResponse(
        path,
        media_type=media_type,
        filename=safe_download_name(contract.name, report.format),
        content_disposition_type="attachment",
    )
