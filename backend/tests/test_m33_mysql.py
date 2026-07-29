from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, delete, func, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from app.core.security import create_token
from app.infrastructure import db as db_module
from app.main import app
from app.models.entities import (
    Contract,
    ContractFile,
    ReviewRecord,
    RiskRecord,
    RiskWarning,
    User,
    WarningAction,
    utcnow,
)


def _mysql_url() -> str | None:
    raw = os.getenv("M33_MYSQL_DATABASE_URL")
    if raw is None:
        return None
    if make_url(raw).database != "a24_m33_regression_20260729":
        raise RuntimeError("unsafe M3.3 MySQL database")
    return raw


MYSQL_URL = _mysql_url()


def auth(user_id: int, role: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_token(user_id, role)}"}


@pytest.fixture()
def mysql_m33():
    if MYSQL_URL is None:
        pytest.skip("requires isolated M3.3 MySQL")
    engine = create_engine(MYSQL_URL, pool_pre_ping=True)
    sessions = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    old = db_module.SessionLocal
    db_module.SessionLocal = sessions
    suffix = uuid4().hex[:12]
    db = sessions()
    assert db.scalar(text("SELECT version_num FROM alembic_version")) == "20260729_0005"
    users = {
        "owner": User(username=f"m33_owner_{suffix}", password_hash="x", role="user", status="active"),
        "other": User(username=f"m33_other_{suffix}", password_hash="x", role="user", status="active"),
        "legal": User(username=f"m33_legal_{suffix}", password_hash="x", role="legalReviewer", status="active"),
        "risk": User(username=f"m33_risk_{suffix}", password_hash="x", role="riskReviewer", status="active"),
        "admin": User(username=f"m33_admin_{suffix}", password_hash="x", role="admin", status="active"),
        "disabled": User(username=f"m33_disabled_{suffix}", password_hash="x", role="user", status="disabled"),
    }
    db.add_all(users.values())
    db.flush()
    contract = Contract(owner_id=users["owner"].id, name=f"m33-{suffix}", status="reviewed")
    db.add(contract)
    db.flush()
    file = ContractFile(
        contract_id=contract.id, file_name="m33.pdf", storage_path="m33.pdf", file_type="pdf",
        file_size=1, sha256="a" * 64,
    )
    db.add(file)
    db.flush()
    review = ReviewRecord(
        contract_id=contract.id, contract_file_id=file.id, file_sha256=file.sha256,
        idempotency_user_id=users["owner"].id, idempotency_key=f"source-{suffix}",
        request_id=f"source-{suffix}", review_mode="full", status="processing", review_stage="legalReview",
        ai_warnings=[], missing_clauses=[],
    )
    db.add(review)
    db.flush()
    risk = RiskRecord(
        review_id=review.id, risk_type="unlimitedLiability", risk_name="risk", risk_level="high",
        clause_text="clause", basis="basis", suggestion="fix", status="active",
    )
    db.add(risk)
    db.flush()
    snapshot = {"rule": {"ruleId": 1, "ruleCode": "M33", "name": "M33", "warningDueHours": 24}}
    def warning(key: str, status: str) -> RiskWarning:
        return RiskWarning(
            warning_key=f"{key}-{suffix}", source_review_id=review.id, source_risk_id=risk.id,
            contract_id=contract.id, owner_id=users["owner"].id, warning_level="high",
            warning_status=status, source_snapshot=snapshot,
        )
    pending = warning("pending", "pendingLegal")
    withdrawn = warning("withdraw", "pendingLegal")
    waived = warning("waive", "pendingRisk")
    active = warning("active", "active")
    db.add_all((pending, withdrawn, waived, active))
    db.commit()
    ids = {name: item.id for name, item in users.items()}
    ids.update({"contract": contract.id, "file": file.id, "review": review.id, "riskRecord": risk.id,
                "pending": pending.id, "withdraw": withdrawn.id, "waive": waived.id, "active": active.id})
    db.close()
    try:
        with TestClient(app) as client:
            yield client, sessions, ids
    finally:
        db = sessions()
        warning_ids = list(db.scalars(select(RiskWarning.id).where(RiskWarning.contract_id == ids["contract"])))
        db.execute(delete(WarningAction).where(WarningAction.warning_id.in_(warning_ids)))
        db.execute(
            ReviewRecord.__table__.update()
            .where(ReviewRecord.source_warning_id.in_(warning_ids))
            .values(source_warning_id=None)
        )
        db.execute(delete(RiskWarning).where(RiskWarning.id.in_(warning_ids)))
        db.execute(delete(RiskRecord).where(RiskRecord.review_id == ids["review"]))
        db.execute(delete(ReviewRecord).where(ReviewRecord.contract_id == ids["contract"]))
        db.execute(delete(ContractFile).where(ContractFile.contract_id == ids["contract"]))
        db.execute(delete(Contract).where(Contract.id == ids["contract"]))
        db.execute(delete(User).where(User.id.in_(ids[name] for name in ("owner", "other", "legal", "risk", "admin", "disabled"))))
        db.commit()
        db.close()
        db_module.SessionLocal = old
        engine.dispose()


def test_mysql_state_permissions_audit_and_unique_warning_key(mysql_m33) -> None:
    client, sessions, ids = mysql_m33
    legal, risk, owner = auth(ids["legal"], "legalReviewer"), auth(ids["risk"], "riskReviewer"), auth(ids["owner"], "user")
    assert client.post(
        f"/api/v1/warnings/{ids['withdraw']}/legal-withdraw", headers=legal, json={"comment": "false"}
    ).status_code == 200
    assert client.post(f"/api/v1/warnings/{ids['pending']}/legal-confirm", headers=legal, json={}).status_code == 200
    db = sessions()
    db.get(ReviewRecord, ids["review"]).review_stage = "riskReview"
    db.commit()
    db.close()
    activated = client.post(f"/api/v1/warnings/{ids['pending']}/risk-activate", headers=risk, json={})
    assert activated.status_code == 200 and activated.json()["data"]["dueAt"] is not None
    assert client.post(f"/api/v1/warnings/{ids['waive']}/waive", headers=risk, json={"comment": "accepted"}).status_code == 200
    listed = client.get("/api/v1/warnings", headers=owner).json()["data"]["items"]
    assert {item["warningId"] for item in listed} == {ids["pending"], ids["active"]}
    assert client.get(f"/api/v1/warnings/{ids['withdraw']}", headers=owner).json()["code"] == "WARNING_NOT_FOUND"
    assert client.get(f"/api/v1/warnings/{ids['active']}", headers=auth(ids["admin"], "admin")).json()["code"] == "WARNING_ROLE_NOT_ALLOWED"
    assert client.get("/api/v1/warnings", headers=auth(ids["disabled"], "user")).json()["code"] == "AUTH_TOKEN_INVALID"
    db = sessions()
    original = db.get(RiskWarning, ids["pending"])
    assert original is not None
    duplicate = RiskWarning(
        warning_key=original.warning_key, source_review_id=original.source_review_id,
        source_risk_id=original.source_risk_id, contract_id=original.contract_id,
        owner_id=original.owner_id, warning_level="high", source_snapshot=original.source_snapshot,
    )
    db.add(duplicate)
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()
    actions = db.scalar(select(func.count()).select_from(WarningAction).where(WarningAction.warning_id == ids["pending"]))
    assert actions == 2
    db.close()


def test_mysql_concurrent_legal_confirm_and_remediation(mysql_m33) -> None:
    client, sessions, ids = mysql_m33
    legal = auth(ids["legal"], "legalReviewer")
    path = f"/api/v1/warnings/{ids['pending']}/legal-confirm"
    def confirm() -> int:
        with TestClient(app) as concurrent_client:
            return concurrent_client.post(path, headers=legal, json={}).status_code
    with ThreadPoolExecutor(max_workers=2) as pool:
        statuses = list(pool.map(lambda _: confirm(), range(2)))
    assert statuses.count(200) == 1
    db = sessions()
    warning = db.get(RiskWarning, ids["pending"])
    assert warning is not None and warning.warning_status == "pendingRisk"
    assert db.scalar(select(func.count()).select_from(WarningAction).where(WarningAction.warning_id == warning.id)) == 1
    db.get(ReviewRecord, ids["review"]).status = "completed"
    db.get(ReviewRecord, ids["review"]).review_stage = "completed"
    active = db.get(RiskWarning, ids["active"])
    assert active is not None
    active.acknowledged_at = utcnow()
    db.commit()
    db.close()
    owner = auth(ids["owner"], "user")
    body = {"contractId": ids["contract"], "contractFileId": ids["file"], "reviewMode": "full", "sourceWarningId": ids["active"]}
    def remediate(key: str) -> int:
        with TestClient(app) as concurrent_client:
            return concurrent_client.post("/api/v1/reviews", headers={**owner, "Idempotency-Key": key}, json=body).status_code
    with ThreadPoolExecutor(max_workers=2) as pool:
        statuses = list(pool.map(remediate, ("m33-a", "m33-b")))
    assert statuses.count(200) == 1
    db = sessions()
    active = db.get(RiskWarning, ids["active"])
    assert active is not None and active.warning_status == "processing"
    assert db.scalar(select(func.count()).select_from(ReviewRecord).where(ReviewRecord.source_warning_id == active.id)) == 1
    assert db.scalar(select(func.count()).select_from(WarningAction).where(WarningAction.warning_id == active.id, WarningAction.action_type == "remediationStarted")) == 1
    db.close()
