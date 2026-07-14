from __future__ import annotations

from collections.abc import Generator
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import BigInteger, create_engine, event, func, select
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import create_token
from app.infrastructure import db as db_module
from app.main import app
from app.models.entities import (
    Base,
    Contract,
    ContractElement,
    ContractFile,
    OperationLog,
    Report,
    ReviewFeedback,
    ReviewRecord,
    ReviewRevision,
    RiskRecord,
    User,
)


@compiles(BigInteger, "sqlite")
def sqlite_bigint(_: BigInteger, __, **___) -> str:
    return "INTEGER"


def auth(user_id: int, role: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_token(user_id, role)}"}


@pytest.fixture()
def m22() -> Generator[tuple[TestClient, sessionmaker[Session]], None, None]:
    engine = create_engine(
        "sqlite+pysqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    old = db_module.SessionLocal
    db_module.SessionLocal = sessions
    db = sessions()
    db.add_all(
        [
            User(id=1, username="owner", password_hash="x", role="user", status="active"),
            User(id=2, username="other", password_hash="x", role="user", status="active"),
            User(id=3, username="legal1", password_hash="x", role="legalReviewer", status="active"),
            User(id=4, username="legal2", password_hash="x", role="legalReviewer", status="active"),
            User(id=5, username="risk1", password_hash="x", role="riskReviewer", status="active"),
            User(id=6, username="risk2", password_hash="x", role="riskReviewer", status="active"),
            User(id=7, username="admin", password_hash="x", role="admin", status="active"),
            Contract(id=1, owner_id=1, name="one", status="reviewing"),
            Contract(id=2, owner_id=2, name="two", status="reviewing"),
            ContractFile(
                id=1,
                contract_id=1,
                file_name="one.pdf",
                storage_path="private/one.pdf",
                file_type="pdf",
                file_size=10,
                sha256="a" * 64,
            ),
            ContractFile(
                id=2,
                contract_id=2,
                file_name="two.pdf",
                storage_path="private/two.pdf",
                file_type="pdf",
                file_size=10,
                sha256="b" * 64,
            ),
        ]
    )
    db.add_all(
        [
            ReviewRecord(
                id=1,
                contract_id=1,
                contract_file_id=1,
                file_sha256="a" * 64,
                idempotency_user_id=1,
                idempotency_key="one",
                request_id="req_one",
                review_mode="full",
                status="processing",
                review_stage="legalReview",
                ai_result_json={
                    "contractType": "purchase",
                    "overallRiskLevel": "high",
                    "overallScore": "80.00",
                },
                ai_warnings=[],
                missing_clauses=[],
            ),
            ReviewRecord(
                id=2,
                contract_id=2,
                contract_file_id=2,
                file_sha256="b" * 64,
                idempotency_user_id=2,
                idempotency_key="two",
                request_id="req_two",
                review_mode="full",
                status="processing",
                review_stage="legalReview",
                ai_result_json={"contractType": "sales"},
                ai_warnings=[],
                missing_clauses=[],
            ),
        ]
    )
    db.flush()
    db.add_all(
        [
            ContractElement(
                id=1,
                contract_id=1,
                review_id=1,
                element_type="partyA",
                element_name="甲方",
                value_text="AI甲方",
                confidence=Decimal("0.9"),
            ),
            ContractElement(
                id=2,
                contract_id=2,
                review_id=2,
                element_type="partyA",
                element_name="甲方",
                value_text="其他合同",
            ),
            RiskRecord(
                id=1,
                review_id=1,
                risk_type="liability",
                risk_name="责任风险",
                risk_level="high",
                clause_text="AI条款",
                basis="R1",
                suggestion="AI建议",
                confidence=Decimal("0.8"),
                status="active",
            ),
            RiskRecord(
                id=2,
                review_id=2,
                risk_type="payment",
                risk_name="付款风险",
                risk_level="medium",
                clause_text="其他条款",
                basis="R2",
                suggestion="其他建议",
                status="active",
            ),
        ]
    )
    db.commit()
    db.close()
    try:
        with TestClient(app) as client:
            yield client, sessions
    finally:
        db_module.SessionLocal = old
        Base.metadata.drop_all(engine)


def test_permissions_claim_and_append_only_effective_result(m22) -> None:
    client, sessions = m22
    assert (
        client.patch(
            "/api/v1/reviews/1/contract-type",
            headers=auth(1, "user"),
            json={"contractType": "nda"},
        ).json()["code"]
        == "REVIEW_ROLE_NOT_ALLOWED"
    )
    assert (
        client.patch(
            "/api/v1/reviews/1/contract-type",
            headers=auth(7, "admin"),
            json={"contractType": "nda"},
        ).json()["code"]
        == "REVIEW_ROLE_NOT_ALLOWED"
    )
    assert (
        client.patch(
            "/api/v1/reviews/1/contract-type",
            headers=auth(3, "legalReviewer"),
            json={"contractType": "nda"},
        ).status_code
        == 200
    )
    denied = client.patch(
        "/api/v1/reviews/1/elements/1",
        headers=auth(4, "legalReviewer"),
        json={"value": "changed"},
    )
    assert denied.json()["code"] == "REVIEW_ALREADY_CLAIMED"
    changed = client.patch(
        "/api/v1/reviews/1/elements/1",
        headers=auth(3, "legalReviewer"),
        json={"value": "人工甲方"},
    )
    assert changed.status_code == 200
    detail = client.get("/api/v1/reviews/1", headers=auth(1, "user")).json()["data"]
    assert detail["aiResult"]["contractType"] == "purchase"
    assert detail["effectiveResult"]["contractType"] == "nda"
    assert detail["effectiveResult"]["elements"][0]["value"] == "人工甲方"
    db = sessions()
    assert db.get(ContractElement, 1).value_text == "AI甲方"
    assert db.scalar(select(func.count()).select_from(ReviewRevision)) == 2
    db.close()


def test_feedback_validation_rolls_back_claim(m22) -> None:
    client, sessions = m22
    invalid = client.post(
        "/api/v1/reviews/2/feedback",
        headers=auth(3, "legalReviewer"),
        json={"targetType": "element", "targetId": 999, "judgment": "correct"},
    )
    assert invalid.json()["code"] == "FEEDBACK_INVALID"
    db = sessions()
    assert db.get(ReviewRecord, 2).legal_reviewer_id is None
    assert db.scalar(select(func.count()).select_from(ReviewFeedback)) == 0
    db.close()


def test_full_legal_and_risk_close_loop(m22) -> None:
    client, sessions = m22
    legal = auth(3, "legalReviewer")
    risk = auth(5, "riskReviewer")
    assert (
        client.post(
            "/api/v1/reviews/1/feedback",
            headers=legal,
            json={"targetType": "risk", "targetId": 1, "judgment": "correct"},
        ).status_code
        == 200
    )
    confirmed = client.post(
        "/api/v1/reviews/1/legal-confirm", headers=legal, json={"opinion": "法务通过"}
    )
    assert confirmed.json()["data"]["reviewStage"] == "riskReview"
    assert (
        client.patch(
            "/api/v1/risks/1",
            headers=risk,
            json={"riskStatus": "dismissed", "comment": "风控判断"},
        ).status_code
        == 200
    )
    assert (
        client.patch(
            "/api/v1/reviews/1/overall-risk",
            headers=risk,
            json={"overallRiskLevel": "low", "overallScore": "10.25"},
        ).status_code
        == 200
    )
    completed = client.post(
        "/api/v1/reviews/1/risk-confirm", headers=risk, json={"opinion": "风控通过"}
    )
    assert completed.json()["data"]["reviewStatus"] == "completed"
    duplicate = client.post(
        "/api/v1/reviews/1/risk-confirm", headers=risk, json={"opinion": "again"}
    )
    assert duplicate.json()["code"] == "REVIEW_STAGE_INVALID"
    detail = client.get("/api/v1/reviews/1", headers=auth(7, "admin")).json()["data"]
    assert detail["effectiveResult"]["risks"][0]["riskStatus"] == "dismissed"
    assert detail["effectiveResult"]["overallScore"] == "10.25"
    assert detail["legalReview"]["opinion"] == "法务通过"
    assert detail["riskReview"]["opinion"] == "风控通过"
    db = sessions()
    assert db.get(ReviewRecord, 1).ai_result_json["overallScore"] == "80.00"
    assert db.get(Contract, 1).status == "reviewed"
    assert db.scalar(select(func.count()).select_from(Report)) == 1
    assert (
        db.scalar(
            select(func.count())
            .select_from(OperationLog)
            .where(OperationLog.action == "REVIEW_RISK_CONFIRMED")
        )
        == 1
    )
    db.close()


def test_data_scopes_risk_detail_and_no_storage_path(m22) -> None:
    client, sessions = m22
    client.patch(
        "/api/v1/reviews/1/contract-type",
        headers=auth(3, "legalReviewer"),
        json={"contractType": "nda"},
    )
    assert client.get("/api/v1/reviews/1", headers=auth(4, "legalReviewer")).status_code == 404
    assert client.get("/api/v1/risks/1", headers=auth(2, "user")).status_code == 404
    assert client.get("/api/v1/risks/1", headers=auth(1, "user")).status_code == 200
    contracts = client.get("/api/v1/contracts", headers=auth(3, "legalReviewer")).json()["data"]
    assert [item["contractId"] for item in contracts["items"]] == [1, 2]
    contracts2 = client.get("/api/v1/contracts", headers=auth(4, "legalReviewer")).json()["data"]
    assert [item["contractId"] for item in contracts2["items"]] == [2]
    detail = client.get("/api/v1/contracts/1", headers=auth(1, "user")).json()
    assert "storagePath" not in str(detail)
    db = sessions()
    assert db.get(ReviewRecord, 1).legal_reviewer_id == 3
    db.close()


def test_revision_order_cross_review_targets_and_stable_reads(m22) -> None:
    client, sessions = m22
    legal = auth(3, "legalReviewer")
    for contract_type in ("nda", "labor"):
        assert (
            client.patch(
                "/api/v1/reviews/1/contract-type",
                headers=legal,
                json={"contractType": contract_type},
            ).status_code
            == 200
        )
    assert (
        client.patch("/api/v1/reviews/1/elements/2", headers=legal, json={"value": "越权"}).json()[
            "code"
        ]
        == "CONTRACT_ELEMENT_NOT_FOUND"
    )
    first = client.get("/api/v1/reviews/1", headers=auth(1, "user")).json()["data"]
    second = client.get("/api/v1/reviews/1", headers=auth(1, "user")).json()["data"]
    assert first["effectiveResult"] == second["effectiveResult"]
    assert first["effectiveResult"]["contractType"] == "labor"
    db = sessions()
    rows = list(
        db.scalars(
            select(ReviewRevision)
            .where(ReviewRevision.review_id == 1)
            .order_by(ReviewRevision.created_at, ReviewRevision.id)
        )
    )
    assert rows[1].before_json == rows[0].after_json
    db.close()


def test_confirm_can_be_first_write_and_role_matrix(m22) -> None:
    client, sessions = m22
    assert (
        client.post(
            "/api/v1/reviews/1/legal-confirm",
            headers=auth(3, "legalReviewer"),
            json={},
        ).status_code
        == 200
    )
    db = sessions()
    review = db.get(ReviewRecord, 1)
    assert review and review.legal_reviewer_id == 3 and review.risk_reviewer_id is None
    db.close()
    assert (
        client.post(
            "/api/v1/reviews/1/risk-confirm", headers=auth(5, "riskReviewer"), json={}
        ).status_code
        == 200
    )
    for path, role, user_id, payload in [
        (
            "/api/v1/reviews/2/overall-risk",
            "legalReviewer",
            3,
            {"overallRiskLevel": "low", "overallScore": 1},
        ),
        ("/api/v1/reviews/2/contract-type", "riskReviewer", 5, {"contractType": "nda"}),
        ("/api/v1/reviews/2/elements/2", "riskReviewer", 5, {"value": "x"}),
    ]:
        assert (
            client.patch(path, headers=auth(user_id, role), json=payload).json()["code"]
            == "REVIEW_ROLE_NOT_ALLOWED"
        )
    assert (
        client.post(
            "/api/v1/reviews/2/risk-confirm", headers=auth(3, "legalReviewer"), json={}
        ).json()["code"]
        == "REVIEW_ROLE_NOT_ALLOWED"
    )
    assert (
        client.post(
            "/api/v1/reviews/2/legal-confirm", headers=auth(5, "riskReviewer"), json={}
        ).json()["code"]
        == "REVIEW_ROLE_NOT_ALLOWED"
    )


def test_log_failure_rolls_back_claim_and_business_write(m22) -> None:
    client, sessions = m22

    def reject_log(session, *_):
        if any(isinstance(row, OperationLog) for row in session.new):
            raise RuntimeError("log write failed")

    event.listen(Session, "before_flush", reject_log)
    try:
        with pytest.raises(RuntimeError, match="log write failed"):
            client.patch(
                "/api/v1/reviews/1/contract-type",
                headers=auth(3, "legalReviewer"),
                json={"contractType": "nda"},
            )
    finally:
        event.remove(Session, "before_flush", reject_log)
    db = sessions()
    assert db.get(ReviewRecord, 1).legal_reviewer_id is None
    assert db.scalar(select(func.count()).select_from(ReviewRevision)) == 0
    db.close()


def test_feedback_does_not_change_effective_result(m22) -> None:
    client, _ = m22
    legal = auth(3, "legalReviewer")
    before = client.get("/api/v1/reviews/1", headers=legal).json()["data"]["effectiveResult"]
    assert (
        client.post(
            "/api/v1/reviews/1/feedback",
            headers=legal,
            json={
                "targetType": "contractType",
                "judgment": "modified",
                "correctedValue": "nda",
            },
        ).status_code
        == 200
    )
    after = client.get("/api/v1/reviews/1", headers=legal).json()["data"]["effectiveResult"]
    assert before == after
    assert (
        client.post(
            "/api/v1/reviews/2/feedback",
            headers=legal,
            json={"targetType": "contractType", "targetId": 2, "judgment": "correct"},
        ).json()["code"]
        == "PARAM_INVALID"
    )
    assert (
        client.post(
            "/api/v1/reviews/2/feedback",
            headers=legal,
            json={"targetType": "contractType", "judgment": "modified"},
        ).json()["code"]
        == "PARAM_INVALID"
    )
