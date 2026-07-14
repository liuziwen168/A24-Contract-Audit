from __future__ import annotations

import os
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, func, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from app.application.admin import ADMIN_ACTIONS, add_admin_log, dashboard_data
from app.core.security import create_token
from app.infrastructure import db as db_module
from app.main import app
from app.models.entities import (
    Contract,
    ContractFile,
    OperationLog,
    ReviewRecord,
    ReviewRevision,
    RiskRecord,
    RiskRule,
    StandardClause,
    User,
)


def _mysql_url() -> str | None:
    raw = os.getenv("MYSQL_TEST_DATABASE_URL")
    if raw is None:
        return None
    database = make_url(raw).database
    if database != "a24_m31_audit_20260713":
        raise RuntimeError(f"unsafe M3.1 MySQL database: {database}")
    return raw


MYSQL_URL = _mysql_url()


def auth(user_id: int) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_token(user_id, 'ignored')}"}


@pytest.fixture()
def mysql_api():
    if MYSQL_URL is None:
        pytest.skip("requires real MySQL")
    engine = create_engine(MYSQL_URL, pool_pre_ping=True)
    sessions = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    old = db_module.SessionLocal
    db_module.SessionLocal = sessions
    token = uuid4().hex[:10]
    db = sessions()
    users = {
        "user": User(username=f"m31_user_{token}", password_hash="x", role="user", status="active"),
        "legal": User(
            username=f"m31_legal_api_{token}",
            password_hash="x",
            role="legalReviewer",
            status="active",
        ),
        "risk": User(
            username=f"m31_risk_api_{token}",
            password_hash="x",
            role="riskReviewer",
            status="active",
        ),
        "admin": User(
            username=f"m31_admin_api_{token}", password_hash="x", role="admin", status="active"
        ),
        "target": User(
            username=f"m31_target_{token}", password_hash="x", role="user", status="active"
        ),
    }
    db.add_all(users.values())
    db.flush()
    clause = StandardClause(
        name=f"M31 API clause {token}",
        contract_type="purchase",
        clause_type="payment",
        content="payment content",
        status="active",
    )
    db.add(clause)
    db.flush()
    rule = RiskRule(
        rule_code=f"API_{token}",
        risk_type="unfairPaymentTerms",
        name=f"M31 API rule {token}",
        risk_level="high",
        rule_content="payment risk",
        standard_clause_id=clause.id,
        status="active",
    )
    db.add(rule)
    db.commit()
    ids = {name: value.id for name, value in users.items()}
    ids.update({"clause": clause.id, "rule": rule.id})
    db.close()
    try:
        with TestClient(app) as client:
            yield client, sessions, ids, token
    finally:
        db_module.SessionLocal = old
        engine.dispose()


@pytest.mark.skipif(MYSQL_URL is None, reason="requires real MySQL")
def test_m31_real_mysql_contracts_constraints_audit_and_effective_dashboard() -> None:
    assert MYSQL_URL is not None
    engine = create_engine(MYSQL_URL, pool_pre_ping=True)
    sessions = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    token = uuid4().hex[:10]
    db = sessions()
    assert db.scalar(text("SELECT version_num FROM alembic_version")) == "20260712_0003"

    admin = User(
        username=f"m31_admin_{token}", password_hash="x", role="admin", status="active"
    )
    owner = User(
        username=f"m31_owner_{token}", password_hash="x", role="user", status="active"
    )
    legal = User(
        username=f"m31_legal_{token}",
        password_hash="x",
        role="legalReviewer",
        status="active",
    )
    db.add_all([admin, owner, legal])
    db.flush()
    clause = StandardClause(
        name=f"M31 clause {token}",
        contract_type="purchase",
        clause_type="payment",
        content="pay in 30 days",
        status="active",
    )
    db.add(clause)
    db.flush()
    rule = RiskRule(
        rule_code=f"M31_{token}",
        risk_type="unfairPaymentTerms",
        name=f"M31 rule {token}",
        risk_level="high",
        rule_content="payment risk",
        standard_clause_id=clause.id,
        status="active",
    )
    db.add(rule)
    db.flush()
    contract = Contract(owner_id=owner.id, name=f"M31 {token}", status="reviewing")
    db.add(contract)
    db.flush()
    file = ContractFile(
        contract_id=contract.id,
        file_name="m31.pdf",
        storage_path=f"tests/m31/{token}.pdf",
        file_type="pdf",
        file_size=1,
        sha256=token.ljust(64, "a"),
    )
    db.add(file)
    db.flush()
    review = ReviewRecord(
        contract_id=contract.id,
        contract_file_id=file.id,
        file_sha256=file.sha256,
        idempotency_user_id=owner.id,
        idempotency_key=f"m31-{token}",
        request_id=f"req_m31_{token}",
        review_mode="full",
        status="processing",
        review_stage="legalReview",
        ai_result_json={"overallScore": "90.00"},
        overall_score=Decimal("90.00"),
        ai_warnings=[],
        missing_clauses=[],
    )
    db.add(review)
    db.flush()
    risk = RiskRecord(
        review_id=review.id,
        rule_id=rule.id,
        rule_snapshot={"ruleCode": rule.rule_code, "riskLevel": "high"},
        risk_type=rule.risk_type,
        risk_name=rule.name,
        risk_level="high",
        clause_text="payment after acceptance",
        basis="rule",
        suggestion="set a deadline",
        confidence=Decimal("0.9000"),
        status="active",
    )
    db.add(risk)
    db.flush()
    db.add(
        ReviewRevision(
            review_id=review.id,
            target_type="risk",
            target_id=risk.id,
            before_json={"riskId": risk.id, "riskLevel": "high", "riskStatus": "active"},
            after_json={"riskId": risk.id, "riskLevel": "low", "riskStatus": "active"},
            actor_id=legal.id,
            actor_role="legalReviewer",
            review_stage="legalReview",
            created_at=datetime.now(timezone.utc),
        )
    )
    before = {"id": owner.id, "userStatus": owner.status}
    owner.status = "disabled"
    add_admin_log(
        db,
        admin,
        ADMIN_ACTIONS["userUpdated"],
        "user",
        owner.id,
        before,
        {"id": owner.id, "userStatus": owner.status},
    )
    db.commit()

    duplicate_clause = StandardClause(
        name=clause.name,
        contract_type=clause.contract_type,
        clause_type=clause.clause_type,
        content="duplicate",
        status="active",
    )
    db.add(duplicate_clause)
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()
    duplicate_rule = RiskRule(
        rule_code=rule.rule_code,
        risk_type=rule.risk_type,
        name="duplicate",
        risk_level="low",
        rule_content="duplicate",
        status="active",
    )
    db.add(duplicate_rule)
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()

    assert db.get(RiskRecord, risk.id).rule_snapshot["riskLevel"] == "high"
    assert db.get(ReviewRecord, review.id).overall_score == Decimal("90.00")
    log = db.scalar(
        select(OperationLog).where(
            OperationLog.action == "ADMIN_USER_UPDATED", OperationLog.resource_id == owner.id
        )
    )
    assert log and log.detail_json["afterValue"]["userStatus"] == "disabled"
    summary = dashboard_data(db, None, None)
    assert summary["effectiveRisksByLevel"]["low"] >= 1
    ordered = db.scalars(
        select(StandardClause)
        .where(StandardClause.name.like(f"%{token}%"))
        .order_by(StandardClause.created_at.desc(), StandardClause.id.desc())
    ).all()
    assert [item.id for item in ordered] == sorted((item.id for item in ordered), reverse=True)
    db.close()
    engine.dispose()


def test_mysql_all_m31_endpoints_require_admin_and_users_me_is_not_shadowed(mysql_api) -> None:
    client, _, ids, token = mysql_api
    valid_clause = {
        "name": f"permission clause {token}",
        "contractType": "purchase",
        "clauseType": "payment",
        "content": "content",
    }
    valid_rule = {
        "ruleCode": f"PERM_{token}",
        "riskType": "unfairPaymentTerms",
        "name": f"permission rule {token}",
        "riskLevel": "high",
        "ruleContent": "content",
    }
    endpoints = [
        ("GET", "/api/v1/users", None),
        ("GET", f"/api/v1/users/{ids['target']}", None),
        ("PATCH", f"/api/v1/users/{ids['target']}", {"role": "user"}),
        ("GET", "/api/v1/standard-clauses", None),
        ("GET", f"/api/v1/standard-clauses/{ids['clause']}", None),
        ("POST", "/api/v1/standard-clauses", valid_clause),
        ("PATCH", f"/api/v1/standard-clauses/{ids['clause']}", {"content": "x"}),
        ("DELETE", f"/api/v1/standard-clauses/{ids['clause']}", None),
        ("GET", "/api/v1/risk-rules", None),
        ("GET", f"/api/v1/risk-rules/{ids['rule']}", None),
        ("POST", "/api/v1/risk-rules", valid_rule),
        ("PATCH", f"/api/v1/risk-rules/{ids['rule']}", {"riskLevel": "medium"}),
        ("DELETE", f"/api/v1/risk-rules/{ids['rule']}", None),
        ("GET", "/api/v1/feedback", None),
        ("GET", "/api/v1/operation-logs", None),
        ("GET", "/api/v1/dashboard/summary", None),
    ]
    for method, path, body in endpoints:
        missing = client.request(method, path, json=body)
        assert missing.status_code == 401 and missing.json()["code"] == "AUTH_TOKEN_MISSING"
        for role in ("user", "legal", "risk"):
            denied = client.request(method, path, headers=auth(ids[role]), json=body)
            assert denied.status_code == 403 and denied.json()["code"] == "PERMISSION_DENIED"

    for path in (
        "/api/v1/users",
        "/api/v1/standard-clauses",
        "/api/v1/risk-rules",
        "/api/v1/feedback",
        "/api/v1/operation-logs",
        "/api/v1/dashboard/summary",
    ):
        assert client.get(path, headers=auth(ids["admin"])).status_code == 200
    me = client.get("/api/v1/users/me", headers=auth(ids["admin"]))
    assert me.status_code == 200 and me.json()["data"]["id"] == ids["admin"]

    for method, path, body in (
        ("PATCH", "/api/v1/reviews/999/contract-type", {"contractType": "nda"}),
        ("PATCH", "/api/v1/reviews/999/overall-risk", {"overallRiskLevel": "low", "overallScore": "1.00"}),
        ("POST", "/api/v1/reviews/999/feedback", {"targetType": "risk", "targetId": 1, "judgment": "correct"}),
        ("POST", "/api/v1/reviews/999/legal-confirm", {}),
        ("POST", "/api/v1/reviews/999/risk-confirm", {}),
    ):
        denied = client.request(method, path, headers=auth(ids["admin"]), json=body)
        assert denied.status_code == 403 and denied.json()["code"] == "REVIEW_ROLE_NOT_ALLOWED"


def test_mysql_user_update_audit_self_protection_json_enum_and_utc_filter(mysql_api) -> None:
    client, sessions, ids, token = mysql_api
    response = client.patch(
        f"/api/v1/users/{ids['target']}",
        headers=auth(ids["admin"]),
        json={"username": f"m31_updated_{token}", "role": "riskReviewer", "userStatus": "disabled"},
    )
    assert response.status_code == 200
    assert "password" not in str(response.json()).lower()
    assert response.json()["data"]["role"] == "riskReviewer"
    for payload in ({"role": "user"}, {"userStatus": "disabled"}):
        denied = client.patch(
            f"/api/v1/users/{ids['admin']}", headers=auth(ids["admin"]), json=payload
        )
        assert denied.status_code == 409
        assert denied.json()["code"] == "USER_SELF_UPDATE_FORBIDDEN"
    invalid = client.patch(
        f"/api/v1/users/{ids['target']}",
        headers=auth(ids["admin"]),
        json={"role": "superAdmin"},
    )
    assert invalid.status_code == 400 and invalid.json()["code"] == "PARAM_INVALID"

    db = sessions()
    log = db.scalar(
        select(OperationLog).where(
            OperationLog.action == "ADMIN_USER_UPDATED",
            OperationLog.resource_id == ids["target"],
        )
    )
    assert log is not None
    assert log.detail_json["beforeValue"]["userStatus"] == "active"
    assert log.detail_json["afterValue"]["userStatus"] == "disabled"
    created = log.created_at.replace(tzinfo=timezone.utc)
    db.close()
    logs = client.get(
        "/api/v1/operation-logs",
        headers=auth(ids["admin"]),
        params={
            "action": "ADMIN_USER_UPDATED",
            "targetId": ids["target"],
            "from": (created - timedelta(seconds=1)).isoformat(),
            "to": (created + timedelta(seconds=1)).isoformat(),
        },
    )
    assert logs.status_code == 200 and logs.json()["data"]["total"] == 1
    item = logs.json()["data"]["items"][0]
    assert item["beforeValue"]["userStatus"] == "active"
    assert item["afterValue"]["userStatus"] == "disabled"


def test_mysql_log_failure_rolls_back_user_update(mysql_api) -> None:
    client, sessions, ids, _ = mysql_api
    db = sessions()
    before = db.get(User, ids["target"]).username
    db.close()

    def reject_log(session, *_):
        if any(
            isinstance(row, OperationLog) and row.action == "ADMIN_USER_UPDATED"
            for row in session.new
        ):
            raise RuntimeError("log write failed")

    event.listen(Session, "before_flush", reject_log)
    try:
        with pytest.raises(RuntimeError, match="log write failed"):
            client.patch(
                f"/api/v1/users/{ids['target']}",
                headers=auth(ids["admin"]),
                json={"username": f"should_rollback_{uuid4().hex[:8]}"},
            )
    finally:
        event.remove(Session, "before_flush", reject_log)
    db = sessions()
    assert db.get(User, ids["target"]).username == before
    assert (
        db.scalar(
            select(func.count())
            .select_from(OperationLog)
            .where(
                OperationLog.action == "ADMIN_USER_UPDATED",
                OperationLog.resource_id == ids["target"],
            )
        )
        == 0
    )
    db.close()


def test_mysql_concurrent_unique_clause_and_rule_return_stable_errors(mysql_api) -> None:
    client, _, ids, token = mysql_api
    clause_payload = {
        "name": f"concurrent clause {token}",
        "contractType": "purchase",
        "clauseType": "payment",
        "content": "content",
    }
    rule_payload = {
        "ruleCode": f"CONCURRENT_{token}",
        "riskType": "unfairPaymentTerms",
        "name": f"concurrent rule {token}",
        "riskLevel": "high",
        "ruleContent": "content",
    }

    def create(path: str, payload: dict) -> tuple[int, str, str]:
        response = client.post(path, headers=auth(ids["admin"]), json=payload)
        return response.status_code, response.json()["code"], response.text

    with ThreadPoolExecutor(max_workers=2) as pool:
        clause_results = list(
            pool.map(lambda _: create("/api/v1/standard-clauses", clause_payload), range(2))
        )
        rule_results = list(
            pool.map(lambda _: create("/api/v1/risk-rules", rule_payload), range(2))
        )
    assert sorted((status, code) for status, code, _ in clause_results) == [
        (200, "OK"),
        (409, "STANDARD_CLAUSE_EXISTS"),
    ]
    assert sorted((status, code) for status, code, _ in rule_results) == [
        (200, "OK"),
        (409, "RISK_RULE_EXISTS"),
    ]
    assert all("IntegrityError" not in body for _, _, body in clause_results + rule_results)


def test_mysql_config_delete_is_idempotent_and_preserves_rows(mysql_api) -> None:
    client, sessions, ids, _ = mysql_api
    for path in (
        f"/api/v1/standard-clauses/{ids['clause']}",
        f"/api/v1/risk-rules/{ids['rule']}",
    ):
        first = client.delete(path, headers=auth(ids["admin"]))
        second = client.delete(path, headers=auth(ids["admin"]))
        assert first.status_code == second.status_code == 200
        assert first.json()["data"]["configStatus"] == "disabled"
        assert second.json()["data"]["configStatus"] == "disabled"
    db = sessions()
    assert db.get(StandardClause, ids["clause"]).status == "disabled"
    assert db.get(RiskRule, ids["rule"]).status == "disabled"
    db.close()


def _risk_state(risk: RiskRecord, level: str, status: str) -> dict[str, object]:
    return {
        "riskId": risk.id,
        "ruleId": risk.rule_id,
        "riskType": risk.risk_type,
        "riskName": risk.risk_name,
        "riskLevel": level,
        "clauseText": risk.clause_text,
        "page": risk.page,
        "paragraphIndex": risk.paragraph_index,
        "basis": risk.basis,
        "suggestion": risk.suggestion,
        "confidence": None,
        "riskStatus": status,
    }


def test_mysql_dashboard_matches_effective_result_after_ordered_revisions(mysql_api) -> None:
    client, sessions, ids, token = mysql_api
    offset = int(token[:8], 16) % (300 * 24 * 60 * 60)
    stamp = datetime(2035, 1, 1, tzinfo=timezone.utc) + timedelta(seconds=offset)
    db = sessions()
    contract = Contract(
        owner_id=ids["user"], name=f"dashboard {token}", status="reviewing", created_at=stamp
    )
    deleted = Contract(
        owner_id=ids["user"],
        name=f"deleted dashboard {token}",
        status="deleted",
        deleted_at=stamp,
        created_at=stamp,
    )
    db.add_all([contract, deleted])
    db.flush()
    file = ContractFile(
        contract_id=contract.id,
        file_name="dashboard.pdf",
        storage_path=f"tests/m31/{token}.pdf",
        file_type="pdf",
        file_size=1,
        sha256=token.ljust(64, "d"),
        created_at=stamp,
    )
    db.add(file)
    db.flush()
    review = ReviewRecord(
        contract_id=contract.id,
        contract_file_id=file.id,
        file_sha256=file.sha256,
        idempotency_user_id=ids["user"],
        idempotency_key=f"dashboard-{token}",
        request_id=f"req_dashboard_{token}",
        review_mode="full",
        status="processing",
        review_stage="legalReview",
        ai_result_json={"contractType": "purchase", "overallScore": "72.50"},
        overall_score=Decimal("72.50"),
        ai_warnings=[],
        missing_clauses=[],
        created_at=stamp,
    )
    db.add(review)
    db.flush()
    risks = [
        RiskRecord(
            review_id=review.id,
            risk_type="unlimitedLiability",
            risk_name="multi revision",
            risk_level="high",
            clause_text="a",
            basis="a",
            suggestion="a",
            status="active",
            created_at=stamp,
        ),
        RiskRecord(
            review_id=review.id,
            risk_type="missingConfidentiality",
            risk_name="dismissed",
            risk_level="medium",
            clause_text="b",
            basis="b",
            suggestion="b",
            status="active",
            created_at=stamp,
        ),
        RiskRecord(
            review_id=review.id,
            risk_type="unilateralTermination",
            risk_name="unchanged",
            risk_level="high",
            clause_text="c",
            basis="c",
            suggestion="c",
            status="active",
            created_at=stamp,
        ),
    ]
    db.add_all(risks)
    db.flush()
    same_time = stamp + timedelta(milliseconds=1)
    medium = _risk_state(risks[0], "medium", "active")
    low = _risk_state(risks[0], "low", "active")
    dismissed = _risk_state(risks[1], "medium", "dismissed")
    db.add_all(
        [
            ReviewRevision(
                review_id=review.id,
                target_type="risk",
                target_id=risks[0].id,
                before_json=_risk_state(risks[0], "high", "active"),
                after_json=medium,
                actor_id=ids["legal"],
                actor_role="legalReviewer",
                review_stage="legalReview",
                created_at=same_time,
            ),
            ReviewRevision(
                review_id=review.id,
                target_type="risk",
                target_id=risks[0].id,
                before_json=medium,
                after_json=low,
                actor_id=ids["legal"],
                actor_role="legalReviewer",
                review_stage="legalReview",
                created_at=same_time,
            ),
            ReviewRevision(
                review_id=review.id,
                target_type="risk",
                target_id=risks[1].id,
                before_json=_risk_state(risks[1], "medium", "active"),
                after_json=dismissed,
                actor_id=ids["legal"],
                actor_role="legalReviewer",
                review_stage="legalReview",
                created_at=same_time,
            ),
        ]
    )
    db.commit()
    review_id = review.id
    assert db.get(ReviewRecord, review_id).overall_score == Decimal("72.50")
    db.close()

    params = {
        "from": (stamp - timedelta(milliseconds=1)).isoformat(),
        "to": (stamp + timedelta(milliseconds=1)).isoformat(),
    }
    dashboard = client.get(
        "/api/v1/dashboard/summary", headers=auth(ids["admin"]), params=params
    )
    assert dashboard.status_code == 200
    data = dashboard.json()["data"]
    assert data["contractsTotal"] == 1
    assert data["effectiveRisksByLevel"] == {"high": 1, "low": 1, "medium": 0}
    assert data["timezone"] == "UTC"
    detail = client.get(f"/api/v1/reviews/{review_id}", headers=auth(ids["admin"]))
    assert detail.status_code == 200
    effective = detail.json()["data"]["effectiveResult"]["risks"]
    effective_counts = Counter(
        item["riskLevel"] for item in effective if item["riskStatus"] != "dismissed"
    )
    assert effective_counts == Counter(data["effectiveRisksByLevel"])
    revised = next(item for item in effective if item["riskId"] == risks[0].id)
    assert revised["riskLevel"] == "low"
