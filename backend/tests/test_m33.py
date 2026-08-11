from __future__ import annotations

from collections.abc import Generator
from datetime import timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import BigInteger, create_engine, func, select
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import create_token
from app.infrastructure import db as db_module
from app.main import app
from app.models.entities import (
    Base,
    Contract,
    ContractFile,
    ReviewRecord,
    RiskRecord,
    RiskWarning,
    User,
    WarningAction,
    utcnow,
)


@compiles(BigInteger, "sqlite")
def sqlite_bigint(_: BigInteger, __, **___) -> str:
    return "INTEGER"


def auth(user_id: int, role: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_token(user_id, role)}"}


@pytest.fixture()
def m33() -> Generator[tuple[TestClient, sessionmaker[Session]], None, None]:
    engine = create_engine(
        "sqlite+pysqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    old = db_module.SessionLocal
    db_module.SessionLocal = sessions
    now = utcnow()
    db = sessions()
    db.add_all(
        [
            User(id=1, username="owner", password_hash="x", role="user", status="active"),
            User(id=2, username="other", password_hash="x", role="user", status="active"),
            User(id=3, username="legal", password_hash="x", role="legalReviewer", status="active"),
            User(id=4, username="risk", password_hash="x", role="riskReviewer", status="active"),
            User(id=5, username="admin", password_hash="x", role="admin", status="active"),
            User(id=6, username="disabled", password_hash="x", role="user", status="disabled"),
            Contract(id=1, owner_id=1, name="one", status="reviewing"),
            Contract(id=2, owner_id=2, name="two", status="reviewing"),
            ContractFile(
                id=1,
                contract_id=1,
                file_name="one.pdf",
                storage_path="one.pdf",
                file_type="pdf",
                file_size=1,
                sha256="a" * 64,
            ),
            ContractFile(
                id=2,
                contract_id=2,
                file_name="two.pdf",
                storage_path="two.pdf",
                file_type="pdf",
                file_size=1,
                sha256="b" * 64,
            ),
            ReviewRecord(
                id=1,
                contract_id=1,
                contract_file_id=1,
                file_sha256="a" * 64,
                idempotency_user_id=1,
                idempotency_key="source-one",
                request_id="source-one",
                review_mode="full",
                status="processing",
                review_stage="legalReview",
                ai_warnings=[],
                missing_clauses=[],
            ),
            ReviewRecord(
                id=2,
                contract_id=2,
                contract_file_id=2,
                file_sha256="b" * 64,
                idempotency_user_id=2,
                idempotency_key="source-two",
                request_id="source-two",
                review_mode="full",
                status="processing",
                review_stage="legalReview",
                ai_warnings=[],
                missing_clauses=[],
            ),
            ReviewRecord(
                id=3,
                contract_id=1,
                contract_file_id=1,
                file_sha256="a" * 64,
                idempotency_user_id=1,
                idempotency_key="remediation-complete",
                request_id="remediation-complete",
                review_mode="full",
                status="completed",
                review_stage="completed",
                ai_warnings=[],
                missing_clauses=[],
            ),
        ]
    )
    db.flush()
    db.add_all(
        [
            RiskRecord(
                id=1,
                review_id=1,
                risk_type="unlimitedLiability",
                risk_name="责任风险",
                risk_level="high",
                clause_text="条款一",
                basis="R1",
                suggestion="修改",
                status="active",
            ),
            RiskRecord(
                id=2,
                review_id=2,
                risk_type="unfairPaymentTerms",
                risk_name="付款风险",
                risk_level="medium",
                clause_text="条款二",
                basis="R2",
                suggestion="修改",
                status="active",
            ),
        ]
    )
    db.flush()
    snapshot = {"rule": {"ruleId": 1, "ruleCode": "R1", "name": "规则一"}}
    for warning_id, key, status, owner_id, contract_id, review_id, risk_id in [
        (1, "pending", "pendingLegal", 1, 1, 1, 1),
        (2, "active", "active", 1, 1, 1, 1),
        (3, "processing", "processing", 1, 1, 1, 1),
        (4, "closed", "closed", 1, 1, 1, 1),
        (5, "waived", "waived", 1, 1, 1, 1),
        (6, "withdrawn", "withdrawn", 1, 1, 1, 1),
        (7, "other", "active", 2, 2, 2, 2),
        (8, "pending-risk", "pendingRisk", 1, 1, 1, 1),
        (9, "withdraw-candidate", "pendingLegal", 1, 1, 1, 1),
    ]:
        db.add(
            RiskWarning(
                id=warning_id,
                warning_key=key,
                source_review_id=review_id,
                source_risk_id=risk_id,
                contract_id=contract_id,
                owner_id=owner_id,
                warning_level="high",
                warning_status=status,
                source_snapshot=snapshot,
                due_at=now + timedelta(days=1),
                acknowledged_at=now if warning_id == 3 else None,
                remediation_review_id=3 if warning_id == 3 else None,
            )
        )
    db.flush()
    db.get(ReviewRecord, 3).source_warning_id = 3
    db.commit()
    db.close()
    try:
        with TestClient(app) as client:
            yield client, sessions
    finally:
        db_module.SessionLocal = old
        Base.metadata.drop_all(engine)


def warning_state(sessions: sessionmaker[Session], warning_id: int) -> tuple[str, int]:
    db = sessions()
    try:
        warning = db.get(RiskWarning, warning_id)
        assert warning is not None
        count = db.scalar(
            select(func.count()).select_from(WarningAction).where(WarningAction.warning_id == warning_id)
        )
        return warning.warning_status, count or 0
    finally:
        db.close()


def test_legal_and_risk_status_machine_with_audit(m33) -> None:
    client, sessions = m33
    legal = auth(3, "legalReviewer")
    risk = auth(4, "riskReviewer")
    assert client.post("/api/v1/warnings/1/legal-confirm", headers=legal, json={}).status_code == 200
    assert warning_state(sessions, 1) == ("pendingRisk", 1)
    db = sessions()
    review = db.get(ReviewRecord, 1)
    assert review is not None
    review.review_stage = "riskReview"
    db.commit()
    db.close()
    activated = client.post(
        "/api/v1/warnings/1/risk-activate",
        headers=risk,
        json={"dueAt": (utcnow() + timedelta(days=2)).isoformat(), "comment": "整改"},
    )
    assert activated.json()["data"]["warningStatus"] == "active"
    assert warning_state(sessions, 1) == ("active", 2)
    assert client.post(
        "/api/v1/warnings/8/waive", headers=risk, json={"comment": "accept candidate"}
    ).json()["data"]["warningStatus"] == "waived"
    assert client.post(
        "/api/v1/warnings/1/waive", headers=risk, json={"comment": "accept"}
    ).json()["data"]["warningStatus"] == "waived"
    withdrawn = client.post(
        "/api/v1/warnings/1/legal-withdraw", headers=legal, json={"comment": "late"}
    )
    assert withdrawn.status_code == 409
    assert withdrawn.json()["code"] in {"WARNING_STAGE_INVALID", "WARNING_STATUS_INVALID"}
    db = sessions()
    review = db.get(ReviewRecord, 1)
    assert review is not None
    review.review_stage = "legalReview"
    db.commit()
    db.close()
    assert client.post(
        "/api/v1/warnings/9/legal-withdraw", headers=legal, json={"comment": "false positive"}
    ).json()["data"]["warningStatus"] == "withdrawn"


def test_user_scope_detail_and_acknowledgement(m33) -> None:
    client, sessions = m33
    owner = auth(1, "user")
    listed = client.get("/api/v1/warnings", headers=owner).json()["data"]
    assert {row["warningId"] for row in listed["items"]} == {2, 3}
    assert client.get("/api/v1/warnings/1", headers=owner).json()["code"] == "WARNING_NOT_FOUND"
    assert client.get("/api/v1/warnings/4", headers=owner).json()["code"] == "WARNING_NOT_FOUND"
    assert client.get("/api/v1/warnings/7", headers=owner).json()["code"] == "WARNING_NOT_FOUND"
    before = warning_state(sessions, 2)
    assert client.post("/api/v1/warnings/2/acknowledge", headers=owner).status_code == 200
    assert warning_state(sessions, 2) == ("active", before[1] + 1)
    assert client.post("/api/v1/warnings/2/acknowledge", headers=owner).status_code == 200
    assert warning_state(sessions, 2) == ("active", before[1] + 1)
    assert client.post("/api/v1/warnings/7/acknowledge", headers=owner).json()["code"] == "WARNING_NOT_FOUND"


def test_rectification_requires_ack_and_is_single_use(m33) -> None:
    client, sessions = m33
    owner = auth(1, "user")
    db = sessions()
    source = db.get(ReviewRecord, 1)
    contract = db.get(Contract, 1)
    assert source is not None and contract is not None
    source.status, source.review_stage, contract.status = "completed", "completed", "reviewed"
    db.commit()
    db.close()
    request = {"contractId": 1, "contractFileId": 1, "reviewMode": "full", "sourceWarningId": 2}
    denied = client.post("/api/v1/reviews", headers={**owner, "Idempotency-Key": "rectify-a"}, json=request)
    assert denied.json()["code"] == "WARNING_ACKNOWLEDGEMENT_REQUIRED"
    assert client.post("/api/v1/warnings/2/acknowledge", headers=owner).status_code == 200
    created = client.post("/api/v1/reviews", headers={**owner, "Idempotency-Key": "rectify-a"}, json=request)
    assert created.status_code == 200
    assert warning_state(sessions, 2)[0] == "processing"
    duplicate = client.post(
        "/api/v1/reviews", headers={**owner, "Idempotency-Key": "rectify-b"}, json=request
    )
    assert duplicate.json()["code"] == "WARNING_STATUS_INVALID"


def test_risk_close_reopen_permissions_and_invalid_transitions(m33) -> None:
    client, sessions = m33
    risk = auth(4, "riskReviewer")
    legal = auth(3, "legalReviewer")
    admin = auth(5, "admin")
    assert client.post("/api/v1/warnings/3/close", headers=risk, json={"comment": "done"}).json()[
        "data"
    ]["warningStatus"] == "closed"
    assert client.post("/api/v1/warnings/3/reopen", headers=risk, json={"comment": "again"}).json()[
        "data"
    ]["warningStatus"] == "active"
    assert client.post("/api/v1/warnings/4/reopen", headers=risk, json={"comment": "again"}).status_code == 200
    for headers, path in [
        (legal, "/api/v1/warnings/2/close"),
        (risk, "/api/v1/warnings/1/legal-confirm"),
        (admin, "/api/v1/warnings/2/close"),
    ]:
        before = warning_state(sessions, 2 if path.endswith("close") else 1)
        response = client.post(path, headers=headers, json={"comment": "no"})
        assert response.status_code == 403
        assert response.json()["code"] == "WARNING_ROLE_NOT_ALLOWED"
        assert warning_state(sessions, 2 if path.endswith("close") else 1) == before


def test_disabled_user_and_admin_detail_are_rejected(m33) -> None:
    client, _ = m33
    assert client.get("/api/v1/warnings", headers=auth(6, "user")).json()["code"] == "AUTH_TOKEN_INVALID"
    assert client.get("/api/v1/warnings/2", headers=auth(5, "admin")).json()["code"] == "WARNING_ROLE_NOT_ALLOWED"
