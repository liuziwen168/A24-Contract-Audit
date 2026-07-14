from __future__ import annotations

import asyncio
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

from app.application.report_executor import ReportExecutor
from app.core.config import settings
from app.core.security import create_token
from app.infrastructure import db as db_module
from app.main import app
from app.models.entities import (
    Contract,
    ContractFile,
    Report,
    ReviewRecord,
    ReviewRevision,
    RiskRecord,
    User,
)


def _mysql_url() -> str | None:
    raw = os.getenv("M32_MYSQL_DATABASE_URL")
    if raw is None:
        return None
    database = make_url(raw).database
    if database != "a24_m32_audit_20260713":
        raise RuntimeError(f"unsafe M3.2 MySQL database: {database}")
    return raw


MYSQL_URL = _mysql_url()


def auth(user_id: int) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_token(user_id, 'ignored')}"}


@pytest.fixture()
def mysql_m32(tmp_path):
    if MYSQL_URL is None:
        pytest.skip("requires M3.2 real MySQL")
    engine = create_engine(MYSQL_URL, pool_pre_ping=True)
    sessions = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    old_sessions = db_module.SessionLocal
    old_root = settings.report_root
    db_module.SessionLocal = sessions
    object.__setattr__(settings, "report_root", tmp_path / "reports")
    token = uuid4().hex[:10]
    stamp = datetime.now(timezone.utc)
    db = sessions()
    assert db.scalar(text("SELECT version_num FROM alembic_version")) == "20260713_0004"
    users = {
        "owner": User(
            username=f"m32_owner_{token}", password_hash="x", role="user", status="active"
        ),
        "other": User(
            username=f"m32_other_{token}", password_hash="x", role="user", status="active"
        ),
        "legal": User(
            username=f"m32_legal_{token}",
            password_hash="x",
            role="legalReviewer",
            status="active",
        ),
        "risk": User(
            username=f"m32_risk_{token}",
            password_hash="x",
            role="riskReviewer",
            status="active",
        ),
        "admin": User(
            username=f"m32_admin_{token}", password_hash="x", role="admin", status="active"
        ),
    }
    db.add_all(users.values())
    db.flush()
    contract = Contract(owner_id=users["owner"].id, name=f"M32合同{token}", status="reviewed")
    db.add(contract)
    db.flush()
    file = ContractFile(
        contract_id=contract.id,
        file_name="m32.pdf",
        storage_path=f"tests/m32/{token}.pdf",
        file_type="pdf",
        file_size=1,
        sha256=token.ljust(64, "e"),
    )
    db.add(file)
    db.flush()
    review = ReviewRecord(
        contract_id=contract.id,
        contract_file_id=file.id,
        file_sha256=file.sha256,
        idempotency_user_id=users["owner"].id,
        idempotency_key=f"m32-{token}",
        request_id=f"req_m32_{token}",
        review_mode="full",
        status="completed",
        review_stage="completed",
        ai_result_json={
            "contractType": "purchase",
            "overallRiskLevel": "high",
            "overallScore": "75.00",
        },
        legal_reviewer_id=users["legal"].id,
        risk_reviewer_id=users["risk"].id,
        legal_reviewed_at=stamp,
        risk_reviewed_at=stamp,
        ai_warnings=[],
        missing_clauses=[],
        overall_risk_level="high",
        overall_score=Decimal("75.00"),
    )
    db.add(review)
    db.flush()
    active = RiskRecord(
        review_id=review.id,
        risk_type="unlimitedLiability",
        risk_name="有效风险",
        risk_level="high",
        clause_text="风险原文",
        basis="依据",
        suggestion="建议",
        status="active",
    )
    dismissed = RiskRecord(
        review_id=review.id,
        risk_type="missingConfidentiality",
        risk_name="忽略风险",
        risk_level="medium",
        clause_text="忽略原文",
        basis="依据",
        suggestion="建议",
        status="active",
    )
    db.add_all([active, dismissed])
    db.flush()
    db.add_all(
        [
            ReviewRevision(
                review_id=review.id,
                target_type="risk",
                target_id=active.id,
                before_json={"riskId": active.id, "riskLevel": "high", "riskStatus": "active"},
                after_json={
                    "riskId": active.id,
                    "riskType": active.risk_type,
                    "riskName": active.risk_name,
                    "riskLevel": "low",
                    "clauseText": active.clause_text,
                    "page": None,
                    "paragraphIndex": None,
                    "basis": active.basis,
                    "suggestion": "最终建议",
                    "confidence": None,
                    "ruleId": None,
                    "riskStatus": "active",
                },
                actor_id=users["risk"].id,
                actor_role="riskReviewer",
                review_stage="riskReview",
            ),
            ReviewRevision(
                review_id=review.id,
                target_type="risk",
                target_id=dismissed.id,
                before_json={
                    "riskId": dismissed.id,
                    "riskLevel": "medium",
                    "riskStatus": "active",
                },
                after_json={
                    "riskId": dismissed.id,
                    "riskType": dismissed.risk_type,
                    "riskName": dismissed.risk_name,
                    "riskLevel": "medium",
                    "clauseText": dismissed.clause_text,
                    "page": None,
                    "paragraphIndex": None,
                    "basis": dismissed.basis,
                    "suggestion": dismissed.suggestion,
                    "confidence": None,
                    "ruleId": None,
                    "riskStatus": "dismissed",
                },
                actor_id=users["risk"].id,
                actor_role="riskReviewer",
                review_stage="riskReview",
            ),
            Report(review_id=review.id, format="html", status="pending"),
        ]
    )
    db.commit()
    ids = {name: value.id for name, value in users.items()}
    ids.update({"review": review.id, "contract": contract.id})
    db.close()
    try:
        with TestClient(app) as client:
            yield client, sessions, ids, token
    finally:
        db_module.SessionLocal = old_sessions
        object.__setattr__(settings, "report_root", old_root)
        engine.dispose()


def test_mysql_concurrent_report_create_is_idempotent(mysql_m32) -> None:
    client, sessions, ids, _ = mysql_m32
    payload = {"reportFormat": "pdf"}

    def create() -> tuple[int, str, int]:
        response = client.post(
            f"/api/v1/reviews/{ids['review']}/reports",
            headers=auth(ids["owner"]),
            json=payload,
        )
        return response.status_code, response.json()["code"], response.json()["data"]["reportId"]

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(lambda _: create(), range(2)))
    assert [(status, code) for status, code, _ in outcomes] == [(200, "OK"), (200, "OK")]
    assert len({report_id for _, _, report_id in outcomes}) == 1
    db = sessions()
    reports = list(
        db.scalars(
            select(Report).where(Report.review_id == ids["review"], Report.format == "pdf")
        )
    )
    assert len(reports) == 1
    for report in db.scalars(select(Report).where(Report.review_id == ids["review"])):
        report.status = "failed"
        report.error_code = "REPORT_GENERATION_FAILED"
        report.error_message = "test cleanup state"
    db.commit()
    db.close()


def test_mysql_atomic_claim_stale_recovery_generation_and_download(mysql_m32) -> None:
    client, sessions, ids, _ = mysql_m32
    db = sessions()
    report = db.scalar(
        select(Report).where(Report.review_id == ids["review"], Report.format == "html")
    )
    report_id = report.id
    db.close()
    workers = [ReportExecutor(session_factory=sessions), ReportExecutor(session_factory=sessions)]
    with ThreadPoolExecutor(max_workers=2) as pool:
        claims = list(pool.map(lambda worker: worker._claim_one(), workers))
    assert claims.count(report_id) == 1 and claims.count(None) == 1
    db = sessions()
    report = db.get(Report, report_id)
    report.started_at = datetime.now(timezone.utc) - timedelta(hours=1)
    db.commit()
    db.close()
    assert asyncio.run(workers[0].run_once())
    db = sessions()
    report = db.get(Report, report_id)
    assert report.status == "completed" and report.attempt_count == 2
    assert report.storage_path and report.file_size and len(report.sha256) == 64
    assert not os.path.isabs(report.storage_path)
    db.close()
    for user_id in (ids["owner"], ids["legal"], ids["risk"], ids["admin"]):
        response = client.get(f"/api/v1/reports/{report_id}/download", headers=auth(user_id))
        assert response.status_code == 200 and response.content.startswith(b"<!doctype html>")
    assert client.get(f"/api/v1/reports/{report_id}/download", headers=auth(ids["other"])).status_code == 404
    db = sessions()
    db.get(Report, report_id).storage_path = "0/missing.html"
    db.commit()
    db.close()
    missing = client.get(f"/api/v1/reports/{report_id}/download", headers=auth(ids["owner"]))
    assert missing.status_code == 404 and missing.json()["code"] == "REPORT_FILE_NOT_FOUND"


def test_mysql_html_pdf_generation_uses_effective_risks(mysql_m32) -> None:
    client, sessions, ids, _ = mysql_m32
    html = client.post(
        f"/api/v1/reviews/{ids['review']}/reports",
        headers=auth(ids["owner"]),
        json={"reportFormat": "html"},
    ).json()["data"]
    pdf = client.post(
        f"/api/v1/reviews/{ids['review']}/reports",
        headers=auth(ids["admin"]),
        json={"reportFormat": "pdf"},
    ).json()["data"]
    executor = ReportExecutor(session_factory=sessions)
    while asyncio.run(executor.run_once()):
        pass
    html_response = client.get(
        f"/api/v1/reports/{html['reportId']}/download", headers=auth(ids["owner"])
    )
    pdf_response = client.get(
        f"/api/v1/reports/{pdf['reportId']}/download", headers=auth(ids["owner"])
    )
    assert html_response.status_code == pdf_response.status_code == 200
    assert html_response.content.startswith(b"<!doctype html>")
    assert pdf_response.content.startswith(b"%PDF")
    html_text = html_response.content.decode("utf-8")
    assert "最终建议" in html_text and "忽略原文" not in html_text
    assert "高 0、中 0、低 1" in html_text
