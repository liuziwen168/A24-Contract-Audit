from __future__ import annotations

from collections import Counter
from collections.abc import Generator
from datetime import datetime, timezone

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
    ContractFile,
    OperationLog,
    ReviewFeedback,
    ReviewRecord,
    ReviewRevision,
    RiskRecord,
    RiskRule,
    StandardClause,
    User,
)


@compiles(BigInteger, "sqlite")
def sqlite_bigint(_: BigInteger, __, **___) -> str:
    return "INTEGER"


def auth(user_id: int) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_token(user_id, 'ignored')}"}


@pytest.fixture()
def m31() -> Generator[tuple[TestClient, sessionmaker[Session]], None, None]:
    engine = create_engine(
        "sqlite+pysqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    old = db_module.SessionLocal
    db_module.SessionLocal = sessions
    same_time = datetime(2026, 7, 13, 8, 0, tzinfo=timezone.utc)
    db = sessions()
    db.add_all(
        [
            User(id=1, username="user", password_hash="secret", role="user", status="active"),
            User(
                id=2,
                username="legal",
                password_hash="secret",
                role="legalReviewer",
                status="active",
            ),
            User(
                id=3,
                username="risk",
                password_hash="secret",
                role="riskReviewer",
                status="active",
            ),
            User(id=4, username="admin", password_hash="secret", role="admin", status="active"),
            User(id=5, username="target", password_hash="secret", role="user", status="active"),
            Contract(id=1, owner_id=1, name="legal stage", status="reviewing"),
            Contract(id=2, owner_id=5, name="risk stage", status="reviewing"),
            Contract(
                id=3,
                owner_id=1,
                name="deleted",
                status="deleted",
                deleted_at=same_time,
            ),
            ContractFile(
                id=1,
                contract_id=1,
                file_name="one.pdf",
                storage_path="private/one.pdf",
                file_type="pdf",
                file_size=1,
                sha256="a" * 64,
            ),
            ContractFile(
                id=2,
                contract_id=2,
                file_name="two.pdf",
                storage_path="private/two.pdf",
                file_type="pdf",
                file_size=1,
                sha256="b" * 64,
            ),
            StandardClause(
                id=1,
                name="付款条款",
                contract_type="purchase",
                clause_type="payment",
                content="三十日内付款",
                status="active",
            ),
        ]
    )
    db.flush()
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
                ai_result_json={"contractType": "purchase"},
                ai_warnings=[],
                missing_clauses=[],
            ),
            ReviewRecord(
                id=2,
                contract_id=2,
                contract_file_id=2,
                file_sha256="b" * 64,
                idempotency_user_id=5,
                idempotency_key="two",
                request_id="req_two",
                review_mode="full",
                status="processing",
                review_stage="riskReview",
                ai_result_json={"contractType": "sales"},
                ai_warnings=[],
                missing_clauses=[],
                legal_reviewer_id=2,
                legal_reviewed_at=same_time,
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
                risk_name="未修订高风险",
                risk_level="high",
                clause_text="a",
                basis="a",
                suggestion="a",
                status="active",
            ),
            RiskRecord(
                id=2,
                review_id=1,
                risk_type="unfairPaymentTerms",
                risk_name="改级风险",
                risk_level="high",
                clause_text="b",
                basis="b",
                suggestion="b",
                status="active",
            ),
            RiskRecord(
                id=3,
                review_id=1,
                risk_type="missingConfidentiality",
                risk_name="忽略风险",
                risk_level="medium",
                clause_text="c",
                basis="c",
                suggestion="c",
                status="active",
            ),
            RiskRecord(
                id=4,
                review_id=2,
                risk_type="forceMajeureMissing",
                risk_name="风控阶段低风险",
                risk_level="low",
                clause_text="d",
                basis="d",
                suggestion="d",
                status="active",
            ),
            ReviewRevision(
                id=1,
                review_id=1,
                target_type="risk",
                target_id=2,
                before_json={"riskId": 2, "riskLevel": "high", "riskStatus": "active"},
                after_json={"riskId": 2, "riskLevel": "medium", "riskStatus": "active"},
                actor_id=2,
                actor_role="legalReviewer",
                review_stage="legalReview",
                created_at=same_time,
            ),
            ReviewRevision(
                id=2,
                review_id=1,
                target_type="risk",
                target_id=2,
                before_json={"riskId": 2, "riskLevel": "medium", "riskStatus": "active"},
                after_json={"riskId": 2, "riskLevel": "low", "riskStatus": "active"},
                actor_id=2,
                actor_role="legalReviewer",
                review_stage="legalReview",
                created_at=same_time,
            ),
            ReviewRevision(
                id=3,
                review_id=1,
                target_type="risk",
                target_id=3,
                before_json={"riskId": 3, "riskLevel": "medium", "riskStatus": "active"},
                after_json={"riskId": 3, "riskLevel": "medium", "riskStatus": "dismissed"},
                actor_id=2,
                actor_role="legalReviewer",
                review_stage="legalReview",
                created_at=same_time,
            ),
            ReviewFeedback(
                id=1,
                review_id=1,
                target_type="risk",
                target_id=1,
                user_id=2,
                judgment="correct",
                created_at=same_time,
            ),
            ReviewFeedback(
                id=2,
                review_id=2,
                target_type="overallRisk",
                user_id=3,
                judgment="modified",
                corrected_value="low",
                created_at=same_time,
            ),
            OperationLog(
                id=1,
                user_id=2,
                action="SAFE_LOG",
                resource_type="review",
                resource_id=1,
                detail_json={"passwordHash": "secret", "storagePath": "C:/private/file"},
                created_at=same_time,
            ),
            OperationLog(
                id=2,
                user_id=3,
                action="SECOND_LOG",
                resource_type="review",
                resource_id=2,
                detail_json={"actorRole": "riskReviewer"},
                created_at=same_time,
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


def test_admin_endpoint_permission_matrix(m31) -> None:
    client, _ = m31
    paths = (
        "/api/v1/users",
        "/api/v1/standard-clauses",
        "/api/v1/risk-rules",
        "/api/v1/feedback",
        "/api/v1/operation-logs",
        "/api/v1/dashboard/summary",
    )
    for path in paths:
        assert client.get(path, headers=auth(4)).status_code == 200
        for user_id in (1, 2, 3):
            denied = client.get(path, headers=auth(user_id))
            assert denied.status_code == 403 and denied.json()["code"] == "PERMISSION_DENIED"
        missing = client.get(path)
        assert missing.status_code == 401 and missing.json()["code"] == "AUTH_TOKEN_MISSING"


def test_user_management_filters_updates_and_audit(m31) -> None:
    client, sessions = m31
    listing = client.get(
        "/api/v1/users?role=user&username=tar&page=1&pageSize=1", headers=auth(4)
    ).json()["data"]
    assert listing["total"] == 1 and listing["items"][0]["username"] == "target"
    assert "password" not in str(listing).lower()
    detail = client.get("/api/v1/users/5", headers=auth(4)).json()["data"]
    assert detail["id"] == 5 and "passwordHash" not in detail
    updated = client.patch(
        "/api/v1/users/5",
        headers=auth(4),
        json={"username": " reviewed ", "role": "legalReviewer", "userStatus": "disabled"},
    )
    assert updated.status_code == 200
    assert updated.json()["data"]["username"] == "reviewed"
    assert client.patch("/api/v1/users/5", headers=auth(4), json={}).json()["code"] == "PARAM_INVALID"
    assert (
        client.patch("/api/v1/users/5", headers=auth(4), json={"role": "owner"}).json()["code"]
        == "PARAM_INVALID"
    )
    assert client.get("/api/v1/users/999", headers=auth(4)).json()["code"] == "USER_NOT_FOUND"
    assert (
        client.patch(
            "/api/v1/users/4", headers=auth(4), json={"userStatus": "disabled"}
        ).json()["code"]
        == "USER_SELF_UPDATE_FORBIDDEN"
    )
    db = sessions()
    log = db.scalar(
        select(OperationLog).where(OperationLog.action == "ADMIN_USER_UPDATED")
    )
    assert log and log.detail_json["beforeValue"]["username"] == "target"
    assert log.detail_json["afterValue"]["username"] == "reviewed"
    db.close()


def test_user_update_and_log_are_atomic(m31) -> None:
    client, sessions = m31

    def reject_log(session, *_):
        if any(isinstance(row, OperationLog) and row.action == "ADMIN_USER_UPDATED" for row in session.new):
            raise RuntimeError("log write failed")

    event.listen(Session, "before_flush", reject_log)
    try:
        with pytest.raises(RuntimeError, match="log write failed"):
            client.patch("/api/v1/users/5", headers=auth(4), json={"username": "changed"})
    finally:
        event.remove(Session, "before_flush", reject_log)
    db = sessions()
    assert db.get(User, 5).username == "target"
    assert (
        db.scalar(
            select(func.count())
            .select_from(OperationLog)
            .where(OperationLog.action == "ADMIN_USER_UPDATED")
        )
        == 0
    )
    db.close()


def test_standard_clause_lifecycle_validation_and_snapshot_safety(m31) -> None:
    client, sessions = m31
    db = sessions()
    snapshot = dict(db.get(ReviewRecord, 1).ai_result_json)
    db.close()
    payload = {
        "name": " 争议解决 ",
        "contractType": "purchase",
        "clauseType": "dispute",
        "content": " 由甲方所在地法院管辖 ",
    }
    created = client.post("/api/v1/standard-clauses", headers=auth(4), json=payload)
    assert created.status_code == 200
    clause_id = created.json()["data"]["clauseId"]
    assert created.json()["data"]["name"] == "争议解决"
    assert (
        client.post("/api/v1/standard-clauses", headers=auth(4), json=payload).json()["code"]
        == "STANDARD_CLAUSE_EXISTS"
    )
    assert (
        client.post(
            "/api/v1/standard-clauses",
            headers=auth(4),
            json={**payload, "name": "   "},
        ).json()["code"]
        == "PARAM_INVALID"
    )
    assert (
        client.post(
            "/api/v1/standard-clauses",
            headers=auth(4),
            json={**payload, "contractType": "unknown"},
        ).json()["code"]
        == "PARAM_INVALID"
    )
    updated = client.patch(
        f"/api/v1/standard-clauses/{clause_id}", headers=auth(4), json={"content": "新文案"}
    )
    assert updated.json()["data"]["content"] == "新文案"
    disabled = client.delete(f"/api/v1/standard-clauses/{clause_id}", headers=auth(4))
    assert disabled.json()["data"]["configStatus"] == "disabled"
    assert (
        client.patch("/api/v1/standard-clauses/999", headers=auth(4), json={"content": "x"}).json()[
            "code"
        ]
        == "STANDARD_CLAUSE_NOT_FOUND"
    )
    db = sessions()
    assert db.get(ReviewRecord, 1).ai_result_json == snapshot
    actions = set(db.scalars(select(OperationLog.action)))
    assert {"STANDARD_CLAUSE_CREATED", "STANDARD_CLAUSE_UPDATED", "STANDARD_CLAUSE_DELETED"} <= actions
    db.close()


def test_risk_rule_lifecycle_reference_and_snapshot_safety(m31) -> None:
    client, sessions = m31
    payload = {
        "ruleCode": " R001 ",
        "riskType": "unlimitedLiability",
        "name": " 无限责任 ",
        "riskLevel": "high",
        "ruleContent": " 识别无限责任约定 ",
        "standardClauseId": 1,
    }
    created = client.post("/api/v1/risk-rules", headers=auth(4), json=payload)
    assert created.status_code == 200
    rule_id = created.json()["data"]["ruleId"]
    assert created.json()["data"]["ruleCode"] == "R001"
    assert (
        client.post("/api/v1/risk-rules", headers=auth(4), json=payload).json()["code"]
        == "RISK_RULE_EXISTS"
    )
    assert (
        client.post(
            "/api/v1/risk-rules", headers=auth(4), json={**payload, "riskLevel": "critical"}
        ).json()["code"]
        == "PARAM_INVALID"
    )
    assert (
        client.post(
            "/api/v1/risk-rules", headers=auth(4), json={**payload, "ruleCode": "R002", "standardClauseId": 999}
        ).json()["code"]
        == "STANDARD_CLAUSE_NOT_FOUND"
    )
    client.patch(
        f"/api/v1/risk-rules/{rule_id}", headers=auth(4), json={"riskLevel": "medium"}
    )
    db = sessions()
    risk = db.get(RiskRecord, 1)
    risk.rule_id = rule_id
    risk.rule_snapshot = {"ruleCode": "R001", "riskLevel": "high"}
    db.commit()
    db.close()
    disabled = client.delete(f"/api/v1/risk-rules/{rule_id}", headers=auth(4))
    assert disabled.json()["data"]["configStatus"] == "disabled"
    db = sessions()
    assert db.get(RiskRecord, 1).rule_snapshot == {"ruleCode": "R001", "riskLevel": "high"}
    assert db.get(RiskRule, rule_id).status == "disabled"
    actions = set(db.scalars(select(OperationLog.action)))
    assert {"RISK_RULE_CREATED", "RISK_RULE_UPDATED", "RISK_RULE_DELETED"} <= actions
    db.close()


def test_feedback_and_operation_log_queries_are_read_only_sorted_and_redacted(m31) -> None:
    client, _ = m31
    feedback = client.get(
        "/api/v1/feedback?submitterRole=legalReviewer&feedbackType=risk&pageSize=1",
        headers=auth(4),
    ).json()["data"]
    assert feedback["total"] == 1 and feedback["items"][0]["feedbackId"] == 1
    all_feedback = client.get("/api/v1/feedback", headers=auth(4)).json()["data"]["items"]
    assert [item["feedbackId"] for item in all_feedback[:2]] == [2, 1]
    logs = client.get("/api/v1/operation-logs", headers=auth(4)).json()["data"]["items"]
    assert [item["logId"] for item in logs[:2]] == [2, 1]
    secret_log = next(item for item in logs if item["logId"] == 1)
    assert secret_log["detail"]["passwordHash"] == "[REDACTED]"
    assert secret_log["detail"]["storagePath"] == "[REDACTED]"
    assert client.patch("/api/v1/feedback", headers=auth(4), json={}).status_code == 405
    assert client.delete("/api/v1/operation-logs", headers=auth(4)).status_code == 405


def test_dashboard_empty_data_returns_all_zero_categories(m31) -> None:
    client, sessions = m31
    db = sessions()
    db.query(ReviewRevision).delete()
    db.query(ReviewFeedback).delete()
    db.query(RiskRecord).delete()
    db.query(ReviewRecord).delete()
    db.query(ContractFile).delete()
    db.query(Contract).delete()
    db.commit()
    db.close()
    data = client.get("/api/v1/dashboard/summary", headers=auth(4)).json()["data"]
    assert data["contractsTotal"] == 0 and data["reviewsTotal"] == 0
    assert set(data["effectiveRisksByLevel"].values()) == {0}
    assert set(data["reviewsByStatus"].values()) == {0}
    assert set(data["reviewsByStage"].values()) == {0}


def test_dashboard_uses_current_effective_risks_and_stable_revision_order(m31) -> None:
    client, _ = m31
    data = client.get("/api/v1/dashboard/summary", headers=auth(4)).json()["data"]
    assert data["contractsTotal"] == 2
    assert data["pendingLegalReview"] == 1 and data["pendingRiskReview"] == 1
    assert data["effectiveRisksByLevel"] == {"high": 1, "low": 2, "medium": 0}
    detail = client.get("/api/v1/reviews/1", headers=auth(4)).json()["data"]
    effective = Counter(
        risk["riskLevel"]
        for risk in detail["effectiveResult"]["risks"]
        if risk["riskStatus"] != "dismissed"
    )
    assert effective == Counter({"high": 1, "low": 1})
    assert detail["effectiveResult"]["risks"][1]["riskLevel"] == "low"


def test_dashboard_rejects_invalid_or_oversized_ranges(m31) -> None:
    client, _ = m31
    invalid = client.get(
        "/api/v1/dashboard/summary?from=2026-07-14T00:00:00Z&to=2026-07-13T00:00:00Z",
        headers=auth(4),
    )
    assert invalid.status_code == 400 and invalid.json()["code"] == "PARAM_INVALID"
    oversized = client.get(
        "/api/v1/dashboard/summary?from=2024-01-01T00:00:00Z&to=2026-07-13T00:00:00Z",
        headers=auth(4),
    )
    assert oversized.status_code == 400 and oversized.json()["code"] == "PARAM_INVALID"
