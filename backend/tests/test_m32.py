from __future__ import annotations

import asyncio
from collections.abc import Generator
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from pypdf import PdfReader
from sqlalchemy import BigInteger, create_engine, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.application.report_executor import ReportExecutor
from app.application.reports import build_report_context, render_html, render_pdf, report_path
from app.core.config import settings
from app.core.security import create_token
from app.infrastructure import db as db_module
from app.main import app
from app.models.entities import (
    Base,
    Contract,
    ContractElement,
    ContractFile,
    Report,
    ReviewRecord,
    ReviewRevision,
    RiskRecord,
    User,
)


@compiles(BigInteger, "sqlite")
def sqlite_bigint(_: BigInteger, __, **___) -> str:
    return "INTEGER"


def auth(user_id: int) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_token(user_id, 'ignored')}"}


def risk_state(risk: RiskRecord, level: str, status: str, suggestion: str) -> dict[str, object]:
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
        "suggestion": suggestion,
        "confidence": "0.9000",
        "riskStatus": status,
    }


@pytest.fixture()
def m32(tmp_path) -> Generator[tuple[TestClient, sessionmaker[Session]], None, None]:
    engine = create_engine(
        "sqlite+pysqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    old_sessions = db_module.SessionLocal
    old_root = settings.report_root
    db_module.SessionLocal = sessions
    object.__setattr__(settings, "report_root", tmp_path / "reports")
    stamp = datetime(2026, 7, 13, 8, 0, tzinfo=timezone.utc)
    db = sessions()
    db.add_all(
        [
            User(id=1, username="owner", password_hash="x", role="user", status="active"),
            User(id=2, username="other", password_hash="x", role="user", status="active"),
            User(
                id=3, username="法务<script>", password_hash="x", role="legalReviewer", status="active"
            ),
            User(id=4, username="风控", password_hash="x", role="riskReviewer", status="active"),
            User(id=5, username="admin", password_hash="x", role="admin", status="active"),
            Contract(id=1, owner_id=1, name='测试"\r\n/合同', status="reviewed"),
            Contract(id=2, owner_id=2, name="other", status="reviewed"),
            ContractFile(
                id=1,
                contract_id=1,
                file_name="one.pdf",
                storage_path="private/one.pdf",
                file_type="pdf",
                file_size=1,
                sha256="a" * 64,
            ),
        ]
    )
    db.flush()
    review = ReviewRecord(
        id=1,
        contract_id=1,
        contract_file_id=1,
        file_sha256="a" * 64,
        idempotency_user_id=1,
        idempotency_key="m32",
        request_id="req_m32",
        review_mode="full",
        status="completed",
        review_stage="completed",
        ai_result_json={
            "contractType": "purchase",
            "overallRiskLevel": "high",
            "overallScore": "80.00",
            "missingClauses": ["confidentiality"],
        },
        legal_reviewer_id=3,
        risk_reviewer_id=4,
        legal_reviewed_at=stamp,
        risk_reviewed_at=stamp,
        ai_warnings=[],
        missing_clauses=["confidentiality"],
        overall_risk_level="high",
        overall_score=Decimal("80.00"),
    )
    db.add(review)
    db.flush()
    element = ContractElement(
        id=1,
        contract_id=1,
        review_id=1,
        element_type="partyA",
        element_name="甲方",
        value_text="AI甲方",
        source="ai",
    )
    amount = ContractElement(
        id=2,
        contract_id=1,
        review_id=1,
        element_type="contractAmount",
        element_name="合同金额",
        value_text="1000.10",
        source="ai",
    )
    risk1 = RiskRecord(
        id=1,
        review_id=1,
        risk_type="unlimitedLiability",
        risk_name="无限责任",
        risk_level="high",
        clause_text="<script>alert(1)</script>",
        page=1,
        paragraph_index=2,
        basis="依据",
        suggestion="AI建议",
        confidence=Decimal("0.9000"),
        status="active",
    )
    risk2 = RiskRecord(
        id=2,
        review_id=1,
        risk_type="missingConfidentiality",
        risk_name="保密缺失",
        risk_level="medium",
        clause_text="无保密条款",
        basis="依据",
        suggestion="补充条款",
        status="active",
    )
    db.add_all([element, amount, risk1, risk2])
    db.flush()
    db.add_all(
        [
            ReviewRevision(
                id=1,
                review_id=1,
                target_type="contractType",
                before_json={"contractType": "purchase"},
                after_json={"contractType": "nda"},
                actor_id=3,
                actor_role="legalReviewer",
                review_stage="legalReview",
                created_at=stamp,
            ),
            ReviewRevision(
                id=2,
                review_id=1,
                target_type="element",
                target_id=1,
                before_json={"elementId": 1, "elementType": "partyA", "value": "AI甲方"},
                after_json={
                    "elementId": 1,
                    "elementType": "partyA",
                    "elementName": "甲方",
                    "value": "修订甲方",
                    "page": None,
                    "paragraphIndex": None,
                    "confidence": None,
                },
                actor_id=3,
                actor_role="legalReviewer",
                review_stage="legalReview",
                created_at=stamp,
            ),
            ReviewRevision(
                id=3,
                review_id=1,
                target_type="risk",
                target_id=1,
                before_json=risk_state(risk1, "high", "active", "AI建议"),
                after_json=risk_state(risk1, "medium", "active", "第一次建议"),
                actor_id=3,
                actor_role="legalReviewer",
                review_stage="legalReview",
                created_at=stamp,
            ),
            ReviewRevision(
                id=4,
                review_id=1,
                target_type="risk",
                target_id=1,
                before_json=risk_state(risk1, "medium", "active", "第一次建议"),
                after_json=risk_state(risk1, "low", "active", "最终建议"),
                actor_id=4,
                actor_role="riskReviewer",
                review_stage="riskReview",
                created_at=stamp,
            ),
            ReviewRevision(
                id=5,
                review_id=1,
                target_type="risk",
                target_id=2,
                before_json=risk_state(risk2, "medium", "active", "补充条款"),
                after_json=risk_state(risk2, "medium", "dismissed", "补充条款"),
                actor_id=4,
                actor_role="riskReviewer",
                review_stage="riskReview",
                created_at=stamp,
            ),
            ReviewRevision(
                id=6,
                review_id=1,
                target_type="overallRisk",
                before_json={"overallRiskLevel": "high", "overallScore": "80.00"},
                after_json={"overallRiskLevel": "low", "overallScore": "10.25"},
                actor_id=4,
                actor_role="riskReviewer",
                review_stage="riskReview",
                created_at=stamp,
            ),
            Report(id=1, review_id=1, format="html", status="pending"),
        ]
    )
    db.commit()
    db.close()
    try:
        with TestClient(app) as client:
            yield client, sessions
    finally:
        db_module.SessionLocal = old_sessions
        object.__setattr__(settings, "report_root", old_root)
        Base.metadata.drop_all(engine)


def test_report_context_uses_effective_result_and_html_is_safe(m32) -> None:
    _, sessions = m32
    db = sessions()
    context = build_report_context(db, db.get(Report, 1))
    db.close()
    assert context["contract"]["contractType"] == "nda"
    assert context["contract"]["partyA"] == "修订甲方"
    assert context["contract"]["contractAmount"] == "1000.10"
    assert context["contract"]["partyB"] == "未识别"
    assert context["review"]["overallRiskLevel"] == "low"
    assert context["review"]["overallScore"] == "10.25"
    assert context["riskSummary"] == {"total": 1, "high": 0, "medium": 0, "low": 1, "dismissed": 1}
    assert context["risks"][0]["suggestion"] == "最终建议"
    html = render_html(context).decode("utf-8")
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html
    assert "http://" not in html and "https://" not in html
    assert "private/one.pdf" not in html and "Token" not in html


def test_pdf_is_nonempty_multipage_and_has_report_number(m32) -> None:
    _, sessions = m32
    db = sessions()
    context = build_report_context(db, db.get(Report, 1))
    db.close()
    context["risks"] = context["risks"] * 35
    context["riskSummary"]["total"] = 35
    content = render_pdf(context)
    assert content.startswith(b"%PDF") and len(content) > 5000
    reader = PdfReader(__import__("io").BytesIO(content))
    assert len(reader.pages) >= 2
    assert context["reportNumber"] in "".join(page.extract_text() or "" for page in reader.pages)


def test_executor_generates_html_and_pdf_with_relative_paths(m32) -> None:
    _, sessions = m32
    db = sessions()
    db.add(Report(id=2, review_id=1, format="pdf", status="pending"))
    db.commit()
    db.close()
    executor = ReportExecutor(session_factory=sessions)
    assert asyncio.run(executor.run_once())
    assert asyncio.run(executor.run_once())
    db = sessions()
    reports = list(db.scalars(select(Report).order_by(Report.id)))
    assert [item.status for item in reports] == ["completed", "completed"]
    for report in reports:
        assert report.storage_path and not __import__("pathlib").Path(report.storage_path).is_absolute()
        path = report_path(report.storage_path)
        assert path.is_file() and path.stat().st_size == report.file_size
        assert len(report.sha256) == 64 and report.attempt_count == 1
    assert report_path(reports[0].storage_path).read_bytes().startswith(b"<!doctype html>")
    assert report_path(reports[1].storage_path).read_bytes().startswith(b"%PDF")
    db.close()


def test_executor_failure_stale_recovery_limit_and_cleanup(m32, monkeypatch) -> None:
    _, sessions = m32

    def broken(*_):
        raise RuntimeError("secret stack must not persist")

    monkeypatch.setattr("app.application.report_executor.render_report", broken)
    executor = ReportExecutor(session_factory=sessions)
    assert asyncio.run(executor.run_once())
    db = sessions()
    failed = db.get(Report, 1)
    assert failed.status == "failed" and failed.error_code == "REPORT_GENERATION_FAILED"
    assert "secret" not in failed.error_message and failed.storage_path is None
    assert not list(settings.report_root.rglob(".report-*"))
    failed.status = "generating"
    failed.started_at = datetime.now(timezone.utc) - timedelta(hours=1)
    db.commit()
    db.close()
    claimed = executor._claim_one()
    assert claimed == 1
    db = sessions()
    assert db.get(Report, 1).attempt_count == 2
    db.get(Report, 1).status = "generating"
    db.get(Report, 1).started_at = datetime.now(timezone.utc) - timedelta(hours=1)
    db.get(Report, 1).attempt_count = settings.report_max_attempts
    db.commit()
    db.close()
    assert executor._claim_one() is None


def test_database_failure_after_publish_removes_file_and_does_not_complete(m32, monkeypatch) -> None:
    _, sessions = m32
    executor = ReportExecutor(session_factory=sessions)

    def reject_complete(*_):
        raise SQLAlchemyError("database write failed")

    monkeypatch.setattr(executor, "_complete", reject_complete)
    assert asyncio.run(executor.run_once())
    db = sessions()
    report = db.get(Report, 1)
    assert report.status == "failed" and report.generated_at is None
    db.close()
    assert not [path for path in settings.report_root.rglob("*") if path.is_file()]


def test_report_api_permissions_idempotency_retry_and_download(m32) -> None:
    client, sessions = m32
    for user_id in (1, 3, 4, 5):
        assert client.get("/api/v1/reviews/1/reports", headers=auth(user_id)).status_code == 200
        assert client.get("/api/v1/reports/1", headers=auth(user_id)).status_code == 200
    assert client.get("/api/v1/reports/1", headers=auth(2)).status_code == 404
    assert client.get("/api/v1/reports/1").status_code == 401
    assert (
        client.post(
            "/api/v1/reviews/1/reports", headers=auth(3), json={"reportFormat": "pdf"}
        ).json()["code"]
        == "PERMISSION_DENIED"
    )
    html = client.post(
        "/api/v1/reviews/1/reports", headers=auth(1), json={"reportFormat": "html"}
    ).json()["data"]
    assert html["reportId"] == 1
    pdf1 = client.post(
        "/api/v1/reviews/1/reports", headers=auth(5), json={"reportFormat": "pdf"}
    ).json()["data"]
    pdf2 = client.post(
        "/api/v1/reviews/1/reports", headers=auth(1), json={"reportFormat": "pdf"}
    ).json()["data"]
    assert pdf1["reportId"] == pdf2["reportId"]
    assert (
        client.post(
            "/api/v1/reviews/1/reports", headers=auth(1), json={"reportFormat": "docx"}
        ).json()["code"]
        == "REPORT_FORMAT_UNSUPPORTED"
    )
    assert client.get("/api/v1/reports/1/download", headers=auth(1)).json()["code"] == "REPORT_NOT_READY"
    executor = ReportExecutor(session_factory=sessions)
    assert asyncio.run(executor.run_once())
    download = client.get("/api/v1/reports/1/download", headers=auth(1))
    assert download.status_code == 200
    assert download.headers["content-type"].startswith("text/html")
    disposition = download.headers["content-disposition"]
    assert "\r" not in disposition and "\n" not in disposition
    assert "filename*=utf-8''" in disposition.lower()
    assert (
        client.post("/api/v1/reports/1/retry", headers=auth(5)).json()["code"]
        == "REPORT_NOT_READY"
    )
    assert client.get("/api/v1/reports/1/download", headers=auth(2)).status_code == 404

    db = sessions()
    report = db.get(Report, pdf1["reportId"])
    report.status = "failed"
    report.error_code = "REPORT_GENERATION_FAILED"
    db.commit()
    db.close()
    assert (
        client.post(f"/api/v1/reports/{report.id}/retry", headers=auth(1)).json()["code"]
        == "PERMISSION_DENIED"
    )
    retried = client.post(f"/api/v1/reports/{report.id}/retry", headers=auth(5))
    assert retried.status_code == 200 and retried.json()["data"]["reportStatus"] == "pending"


@pytest.mark.parametrize(
    ("status", "path_value", "code"),
    [
        ("pending", None, "REPORT_NOT_READY"),
        ("generating", None, "REPORT_NOT_READY"),
        ("failed", None, "REPORT_GENERATION_FAILED"),
        ("completed", "../escape.html", "REPORT_FILE_NOT_FOUND"),
        ("completed", "C:\\escape.html", "REPORT_FILE_NOT_FOUND"),
        ("completed", "0/missing.html", "REPORT_FILE_NOT_FOUND"),
    ],
)
def test_download_rejects_invalid_states_and_paths(m32, status, path_value, code) -> None:
    client, sessions = m32
    db = sessions()
    report = db.get(Report, 1)
    report.status = status
    report.storage_path = path_value
    db.commit()
    db.close()
    response = client.get("/api/v1/reports/1/download", headers=auth(1))
    assert response.json()["code"] == code


def test_unready_or_deleted_review_cannot_create_report(m32) -> None:
    client, sessions = m32
    db = sessions()
    db.get(ReviewRecord, 1).status = "processing"
    db.commit()
    db.close()
    assert (
        client.post(
            "/api/v1/reviews/1/reports", headers=auth(1), json={"reportFormat": "pdf"}
        ).json()["code"]
        == "REPORT_NOT_READY"
    )
