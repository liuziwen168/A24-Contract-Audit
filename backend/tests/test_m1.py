from __future__ import annotations

import asyncio
import json
import os
from collections.abc import Generator
from pathlib import Path
from uuid import uuid4

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import BigInteger, create_engine, func, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.application.report_executor import ReportExecutor
from app.application.review_executor import ReviewExecutor
from app.core.config import Settings, settings
from app.core.security import create_token, hash_password
from app.infrastructure import db as db_module
from app.infrastructure.ai_client import AIClient
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


@pytest.fixture()
def client(tmp_path) -> Generator[tuple[TestClient, sessionmaker], None, None]:
    engine = create_engine(
        "sqlite+pysqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    original = db_module.SessionLocal
    old_upload_root = settings.upload_root
    old_report_root = settings.report_root
    db_module.SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    object.__setattr__(settings, "upload_root", tmp_path / "uploads")
    object.__setattr__(settings, "report_root", tmp_path / "reports")
    db = db_module.SessionLocal()
    db.add_all(
        [
            User(
                id=1,
                username="user1",
                password_hash=hash_password("password"),
                role="user",
                status="active",
            ),
            User(
                id=2,
                username="user2",
                password_hash=hash_password("password"),
                role="user",
                status="active",
            ),
            User(
                id=3,
                username="disabled",
                password_hash=hash_password("password"),
                role="user",
                status="disabled",
            ),
            User(
                id=4,
                username="admin",
                password_hash=hash_password("password"),
                role="admin",
                status="active",
            ),
            User(
                id=5,
                username="legal",
                password_hash=hash_password("password"),
                role="legalReviewer",
                status="active",
            ),
            User(
                id=6,
                username="risk",
                password_hash=hash_password("password"),
                role="riskReviewer",
                status="active",
            ),
        ]
    )
    db.commit()
    db.close()
    try:
        with TestClient(app) as test_client:
            yield test_client, db_module.SessionLocal
    finally:
        db_module.SessionLocal = original
        object.__setattr__(settings, "upload_root", old_upload_root)
        object.__setattr__(settings, "report_root", old_report_root)
        Base.metadata.drop_all(engine)


def token(client: TestClient, username: str = "user1") -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/login", json={"username": username, "password": "password"}
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['data']['accessToken']}"}


def upload(
    client: TestClient, headers: dict[str, str], name: str = "contract.pdf"
) -> dict[str, object]:
    response = client.post(
        "/api/v1/contracts",
        headers=headers,
        files={"file": (name, b"%PDF-1.7\n", "application/pdf")},
    )
    assert response.status_code == 200
    return response.json()["data"]


def test_login_success_and_failure(client) -> None:
    http, _ = client
    assert (
        http.post("/api/v1/auth/login", json={"username": "user1", "password": "password"}).json()[
            "code"
        ]
        == "OK"
    )
    assert (
        http.post("/api/v1/auth/login", json={"username": "user1", "password": "wrong"}).json()[
            "code"
        ]
        == "AUTH_LOGIN_FAILED"
    )


def test_invalid_token_and_disabled_login(client) -> None:
    http, _ = client
    assert (
        http.get("/api/v1/users/me", headers={"Authorization": "Bearer invalid"}).json()["code"]
        == "AUTH_TOKEN_INVALID"
    )
    assert (
        http.post(
            "/api/v1/auth/login", json={"username": "disabled", "password": "password"}
        ).json()["code"]
        == "AUTH_LOGIN_FAILED"
    )


def test_expired_token_is_rejected(client) -> None:
    http, _ = client
    original = settings.jwt_expire_seconds
    object.__setattr__(settings, "jwt_expire_seconds", -1)
    expired = create_token(1, "user")
    object.__setattr__(settings, "jwt_expire_seconds", original)
    assert (
        http.get("/api/v1/users/me", headers={"Authorization": f"Bearer {expired}"}).json()["code"]
        == "AUTH_TOKEN_INVALID"
    )


def test_user_cannot_use_admin_scope(client) -> None:
    http, _ = client
    response = http.get("/api/v1/contracts?ownerId=2", headers=token(http))
    assert response.status_code == 403 and response.json()["code"] == "PERMISSION_DENIED"


def test_upload_type_and_size_validation(client) -> None:
    http, _ = client
    headers = token(http)
    assert (
        http.post(
            "/api/v1/contracts",
            headers=headers,
            files={"file": ("bad.txt", b"hello", "text/plain")},
        ).json()["code"]
        == "FILE_TYPE_UNSUPPORTED"
    )
    object.__setattr__(settings, "max_upload_mb", 0)
    assert (
        http.post(
            "/api/v1/contracts",
            headers=headers,
            files={"file": ("huge.pdf", b"%PDF-", "application/pdf")},
        ).json()["code"]
        == "FILE_TOO_LARGE"
    )
    object.__setattr__(settings, "max_upload_mb", 20)


def test_user_cannot_read_another_contract(client) -> None:
    http, _ = client
    contract = upload(http, token(http, "user1"))
    response = http.get(f"/api/v1/contracts/{contract['contractId']}", headers=token(http, "user2"))
    assert response.status_code == 404 and response.json()["code"] == "CONTRACT_NOT_FOUND"


def test_contract_logical_delete(client) -> None:
    http, _ = client
    headers = token(http)
    contract = upload(http, headers)
    assert (
        http.delete(f"/api/v1/contracts/{contract['contractId']}", headers=headers).json()["data"][
            "contractStatus"
        ]
        == "deleted"
    )
    assert (
        http.get(f"/api/v1/contracts/{contract['contractId']}", headers=headers).json()["code"]
        == "CONTRACT_NOT_FOUND"
    )


def test_contract_file_must_belong_to_contract(client) -> None:
    http, _ = client
    headers = token(http)
    first, second = upload(http, headers), upload(http, headers)
    response = http.post(
        "/api/v1/reviews",
        headers={**headers, "Idempotency-Key": "wrong-file"},
        json={
            "contractId": first["contractId"],
            "contractFileId": second["contractFileId"],
            "reviewMode": "full",
        },
    )
    assert response.status_code == 404 and response.json()["code"] == "CONTRACT_FILE_NOT_FOUND"


def test_review_idempotency_conflict_and_running(client) -> None:
    http, _ = client
    headers = token(http)
    contract = upload(http, headers)
    payload = {
        "contractId": contract["contractId"],
        "contractFileId": contract["contractFileId"],
        "reviewMode": "full",
    }
    one = http.post("/api/v1/reviews", headers={**headers, "Idempotency-Key": "same"}, json=payload)
    two = http.post("/api/v1/reviews", headers={**headers, "Idempotency-Key": "same"}, json=payload)
    assert one.json()["data"]["reviewId"] == two.json()["data"]["reviewId"]
    changed = {**payload, "reviewMode": "rulesOnly"}
    assert (
        http.post(
            "/api/v1/reviews", headers={**headers, "Idempotency-Key": "same"}, json=changed
        ).json()["code"]
        == "IDEMPOTENCY_CONFLICT"
    )
    assert (
        http.post(
            "/api/v1/reviews", headers={**headers, "Idempotency-Key": "new"}, json=payload
        ).json()["code"]
        == "REVIEW_ALREADY_RUNNING"
    )


def test_idempotency_key_conflicts_for_different_contract(client) -> None:
    http, _ = client
    headers = token(http)
    first, second = upload(http, headers), upload(http, headers)
    for contract in (first, second):
        response = http.post(
            "/api/v1/reviews",
            headers={**headers, "Idempotency-Key": "same-contract-key"},
            json={
                "contractId": contract["contractId"],
                "contractFileId": contract["contractFileId"],
                "reviewMode": "full",
            },
        )
    assert response.json()["code"] == "IDEMPOTENCY_CONFLICT"


def test_idempotency_key_conflicts_for_different_file(client) -> None:
    http, sessions = client
    headers = token(http)
    contract = upload(http, headers)
    db = sessions()
    extra_file = ContractFile(
        contract_id=contract["contractId"],
        file_name="other.pdf",
        storage_path="test-only",
        file_type="pdf",
        file_size=8,
        sha256="a" * 64,
    )
    db.add(extra_file)
    db.commit()
    db.refresh(extra_file)
    db.close()
    first = {
        "contractId": contract["contractId"],
        "contractFileId": contract["contractFileId"],
        "reviewMode": "full",
    }
    second = {**first, "contractFileId": extra_file.id}
    assert (
        http.post(
            "/api/v1/reviews", headers={**headers, "Idempotency-Key": "same-file-key"}, json=first
        ).json()["code"]
        == "OK"
    )
    assert (
        http.post(
            "/api/v1/reviews", headers={**headers, "Idempotency-Key": "same-file-key"}, json=second
        ).json()["code"]
        == "IDEMPOTENCY_CONFLICT"
    )


def test_same_idempotency_key_is_scoped_to_user_and_request_id_is_independent(client) -> None:
    http, _ = client
    first_headers, second_headers = token(http, "user1"), token(http, "user2")
    first, second = upload(http, first_headers), upload(http, second_headers)
    created = []
    for headers, contract in ((first_headers, first), (second_headers, second)):
        response = http.post(
            "/api/v1/reviews",
            headers={**headers, "Idempotency-Key": "shared-key"},
            json={
                "contractId": contract["contractId"],
                "contractFileId": contract["contractFileId"],
                "reviewMode": "full",
            },
        )
        assert response.json()["code"] == "OK"
        created.append(response.json()["data"])
    assert created[0]["reviewId"] != created[1]["reviewId"]
    assert all(
        item["requestId"].startswith("req_") and item["requestId"] != "shared-key"
        for item in created
    )


def test_deleted_contract_cannot_start_review(client) -> None:
    http, _ = client
    headers = token(http)
    contract = upload(http, headers)
    http.delete(f"/api/v1/contracts/{contract['contractId']}", headers=headers)
    response = http.post(
        "/api/v1/reviews",
        headers={**headers, "Idempotency-Key": "deleted-contract"},
        json={
            "contractId": contract["contractId"],
            "contractFileId": contract["contractFileId"],
            "reviewMode": "full",
        },
    )
    assert response.status_code == 409 and response.json()["code"] == "CONTRACT_DELETED"


def test_review_persists_file_sha_and_separate_status_stage(client) -> None:
    http, sessions = client
    headers = token(http)
    contract = upload(http, headers)
    created = http.post(
        "/api/v1/reviews",
        headers={**headers, "Idempotency-Key": "snapshot"},
        json={
            "contractId": contract["contractId"],
            "contractFileId": contract["contractFileId"],
            "reviewMode": "full",
        },
    ).json()["data"]
    db = sessions()
    review = db.get(ReviewRecord, created["reviewId"])
    db.close()
    assert (
        review.file_sha256
        == http.get(f"/api/v1/contracts/{contract['contractId']}", headers=headers).json()["data"][
            "files"
        ][0]["sha256"]
    )
    assert (review.status, review.review_stage) == ("pending", "aiReview")


def test_upload_filename_cannot_escape_storage_and_storage_path_is_hidden(client) -> None:
    http, _ = client
    headers = token(http)
    contract = upload(http, headers, "../../escape.pdf")
    payload = http.get(f"/api/v1/contracts/{contract['contractId']}", headers=headers)
    assert "storagePath" not in payload.text and "storage_path" not in payload.text
    root = Path(settings.upload_root).resolve()
    assert all(root in path.resolve().parents or path.resolve() == root for path in root.rglob("*"))
    assert not (root.parent / "escape.pdf").exists()


def test_ai_health_uses_service_root(monkeypatch) -> None:
    urls: list[str] = []

    class Response:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, str]:
            return {"status": "ok"}

    class Client:
        def __init__(self, **_: object) -> None:
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_: object) -> None:
            return None

        async def get(self, url: str, **_: object) -> Response:
            urls.append(url)
            return Response()

    monkeypatch.setattr("app.infrastructure.ai_client.httpx.AsyncClient", Client)
    object.__setattr__(settings, "ai_service_base_url", "http://ai-service:8001/internal/v1")
    assert asyncio.run(AIClient().health()) == {"status": "ok"}
    assert urls == ["http://ai-service:8001/health"]


def test_progress_data_scope(client) -> None:
    http, _ = client
    headers = token(http)
    contract = upload(http, headers)
    review = http.post(
        "/api/v1/reviews",
        headers={**headers, "Idempotency-Key": "progress"},
        json={
            "contractId": contract["contractId"],
            "contractFileId": contract["contractFileId"],
            "reviewMode": "full",
        },
    ).json()["data"]
    assert (
        http.get(f"/api/v1/reviews/{review['reviewId']}/progress", headers=headers).json()["code"]
        == "OK"
    )
    assert (
        http.get(
            f"/api/v1/reviews/{review['reviewId']}/progress", headers=token(http, "user2")
        ).json()["code"]
        == "REVIEW_NOT_FOUND"
    )


def test_error_response_has_request_id(client) -> None:
    http, _ = client
    body = http.get("/api/v1/users/me").json()
    assert body["code"] == "AUTH_TOKEN_MISSING" and body["requestId"].startswith("req_")


def test_health_response_has_request_id(client) -> None:
    http, _ = client
    body = http.get("/health").json()
    assert body["status"] == "ok" and body["requestId"].startswith("req_")


def test_review_result_readiness_snapshot_and_data_scope(client) -> None:
    http, sessions = client
    db = sessions()
    db.add_all(
        [
            Contract(id=1, owner_id=1, name="reviewed", status="reviewing"),
            ContractFile(
                id=1,
                contract_id=1,
                file_name="safe.pdf",
                storage_path="internal",
                file_type="pdf",
                file_size=1,
                sha256="a" * 64,
            ),
            ReviewRecord(
                id=1,
                contract_id=1,
                contract_file_id=1,
                file_sha256="a" * 64,
                idempotency_user_id=1,
                idempotency_key="result",
                request_id="req_result",
                review_mode="full",
                status="processing",
                review_stage="aiReview",
                ai_warnings=[],
                missing_clauses=[],
            ),
        ]
    )
    db.commit()
    headers = token(http)
    assert (
        http.get("/api/v1/reviews/1", headers=headers).json()["code"] == "REVIEW_RESULT_NOT_READY"
    )
    review = db.get(ReviewRecord, 1)
    assert review
    review.status, review.review_stage = "processing", "legalReview"
    review.ai_result_json = {"requestId": "req_result", "contractId": 1}
    db.commit()
    db.close()
    response = http.get("/api/v1/reviews/1", headers=headers)
    assert response.json()["data"]["effectiveResult"] == {
        "requestId": "req_result",
        "contractId": 1,
    }
    assert "storagePath" not in response.text and "filePath" not in response.text
    assert (
        http.get("/api/v1/reviews/1/progress", headers=headers).json()["data"]["aiResultAvailable"]
        is True
    )
    assert (
        http.get("/api/v1/reviews/1", headers=token(http, "user2")).json()["code"]
        == "REVIEW_NOT_FOUND"
    )


def test_openapi_uses_external_names_and_secures_all_business_routes() -> None:
    specification = app.openapi()
    expected_paths = {
        "/health",
        "/api/v1/auth/login",
        "/api/v1/users/me",
        "/api/v1/users",
        "/api/v1/users/{userId}",
        "/api/v1/contracts",
        "/api/v1/contracts/{contractId}",
        "/api/v1/reviews",
        "/api/v1/reviews/{reviewId}",
        "/api/v1/reviews/{reviewId}/progress",
        "/api/v1/reviews/{reviewId}/contract-type",
        "/api/v1/reviews/{reviewId}/elements/{elementId}",
        "/api/v1/reviews/{reviewId}/overall-risk",
        "/api/v1/reviews/{reviewId}/feedback",
        "/api/v1/reviews/{reviewId}/legal-confirm",
        "/api/v1/reviews/{reviewId}/risk-confirm",
        "/api/v1/reviews/{reviewId}/reports",
        "/api/v1/risks/{riskId}",
        "/api/v1/standard-clauses",
        "/api/v1/standard-clauses/{clauseId}",
        "/api/v1/risk-rules",
        "/api/v1/risk-rules/{ruleId}",
        "/api/v1/feedback",
        "/api/v1/operation-logs",
        "/api/v1/dashboard/summary",
        "/api/v1/reports/{reportId}",
        "/api/v1/reports/{reportId}/retry",
        "/api/v1/reports/{reportId}/download",
    }
    assert set(specification["paths"]) == expected_paths
    for path, operations in specification["paths"].items():
        for method, operation in operations.items():
            if method not in {"get", "post", "patch", "delete"}:
                continue
            for parameter in operation.get("parameters", []):
                assert "_" not in parameter["name"], (method, path, parameter["name"])
            if path not in {"/health", "/api/v1/auth/login"}:
                assert operation.get("security") == [{"HTTPBearer": []}], (method, path)
    schemas = specification["components"]["schemas"]
    assert schemas["ReportCreateIn"]["properties"]["reportFormat"]["enum"] == ["html", "pdf"]
    assert schemas["ReviewIn"]["properties"]["reviewMode"]["enum"] == ["full", "rulesOnly"]
    role_schema = schemas["UserUpdateIn"]["properties"]["role"]["anyOf"][0]
    assert role_schema["enum"] == ["user", "legalReviewer", "riskReviewer", "admin"]


def test_production_configuration_rejects_development_defaults() -> None:
    with pytest.raises(RuntimeError, match="production secrets"):
        Settings(app_env="production")


def test_lifespan_starts_and_stops_both_background_executors(monkeypatch) -> None:
    instances = []

    class Executor:
        def __init__(self) -> None:
            self.stopped = False
            instances.append(self)

        async def run_forever(self) -> None:
            await asyncio.Event().wait()

        def stop(self) -> None:
            self.stopped = True

    old_review_enabled = settings.task_executor_enabled
    old_report_enabled = settings.report_executor_enabled
    object.__setattr__(settings, "task_executor_enabled", True)
    object.__setattr__(settings, "report_executor_enabled", True)
    monkeypatch.setattr("app.main.ReviewExecutor", Executor)
    monkeypatch.setattr("app.main.ReportExecutor", Executor)
    try:
        with TestClient(app):
            tasks = [app.state.review_executor_task, app.state.report_executor_task]
            assert len(instances) == 2 and all(not task.done() for task in tasks)
        assert all(instance.stopped for instance in instances)
        assert all(task.cancelled() for task in tasks)
    finally:
        object.__setattr__(settings, "task_executor_enabled", old_review_enabled)
        object.__setattr__(settings, "report_executor_enabled", old_report_enabled)


def _run_complete_contract_lifecycle(client, monkeypatch, usernames=None) -> None:
    http, sessions = client
    usernames = usernames or {
        "owner": "user1",
        "other": "user2",
        "admin": "admin",
        "legal": "legal",
        "risk": "risk",
    }
    owner = token(http, usernames["owner"])
    other = token(http, usernames["other"])
    admin = token(http, usernames["admin"])
    legal = token(http, usernames["legal"])
    risk_reviewer = token(http, usernames["risk"])
    dashboard_before = http.get("/api/v1/dashboard/summary", headers=admin).json()["data"]
    contract = upload(http, owner, "full-lifecycle.pdf")
    payload = {
        "contractId": contract["contractId"],
        "contractFileId": contract["contractFileId"],
        "reviewMode": "full",
    }
    review_response = http.post(
        "/api/v1/reviews",
        headers={**owner, "Idempotency-Key": "final-e2e"},
        json=payload,
    )
    repeated = http.post(
        "/api/v1/reviews",
        headers={**owner, "Idempotency-Key": "final-e2e"},
        json=payload,
    )
    review = review_response.json()["data"]
    review_id = review["reviewId"]
    assert repeated.json()["data"] == review
    assert (review["reviewStatus"], review["reviewStage"]) == ("pending", "aiReview")
    assert (
        http.patch(
            f"/api/v1/reviews/{review_id}/contract-type",
            headers=legal,
            json={"contractType": "nda"},
        ).json()["code"]
        == "REVIEW_STAGE_INVALID"
    )

    seen_requests: list[dict[str, object]] = []

    def ai_service(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        seen_requests.append(body)
        assert request.url.path.endswith("/internal/v1/reviews/full")
        assert request.headers["X-Request-Id"] == body["requestId"]
        assert request.headers["X-Internal-Token"] == settings.ai_internal_token
        return httpx.Response(
            200,
            json={
                "requestId": body["requestId"],
                "contractId": body["contractId"],
                "contractType": "purchase",
                "typeConfidence": "0.9500",
                "elements": [
                    {
                        "elementType": "partyA",
                        "elementName": "甲方",
                        "value": "AI甲方",
                        "page": 1,
                        "paragraphIndex": 0,
                        "confidence": "0.9000",
                    }
                ],
                "risks": [
                    {
                        "riskType": "unlimitedLiability",
                        "riskName": "无限责任",
                        "riskLevel": "high",
                        "clauseText": "承担全部责任",
                        "page": 1,
                        "paragraphIndex": 1,
                        "basis": "模型识别",
                        "suggestion": "设置责任上限",
                        "confidence": "0.8800",
                        "ruleId": None,
                    },
                    {
                        "riskType": "missingConfidentiality",
                        "riskName": "缺失保密条款",
                        "riskLevel": "medium",
                        "clauseText": "未约定保密义务",
                        "page": 2,
                        "paragraphIndex": 2,
                        "basis": "模型识别",
                        "suggestion": "补充保密条款",
                        "confidence": "0.8000",
                        "ruleId": None,
                    },
                ],
                "missingClauses": ["confidentiality"],
                "overallRiskLevel": "high",
                "overallScore": "75.00",
                "modelName": "controlled-http-mock",
                "modelVersion": "test-v1",
                "promptVersion": "test-v1",
                "processingTimeMs": 10,
                "warnings": [],
                "error": None,
            },
        )

    real_async_client = httpx.AsyncClient
    transport = httpx.MockTransport(ai_service)

    def controlled_client(**kwargs):
        return real_async_client(transport=transport, **kwargs)

    monkeypatch.setattr("app.infrastructure.ai_client.httpx.AsyncClient", controlled_client)

    async def no_wait(_: float) -> None:
        return None

    assert asyncio.run(
        ReviewExecutor(
            client=AIClient(sleep=no_wait), session_factory=sessions, sleep=no_wait
        ).run_once()
    )
    assert len(seen_requests) == 1
    db = sessions()
    stored_review = db.get(ReviewRecord, review_id)
    elements = list(
        db.scalars(select(ContractElement).where(ContractElement.review_id == review_id))
    )
    risks = list(db.scalars(select(RiskRecord).where(RiskRecord.review_id == review_id)))
    assert stored_review and stored_review.ai_attempt_count == 1
    assert (stored_review.status, stored_review.review_stage) == ("processing", "legalReview")
    assert stored_review.ai_result_json["contractType"] == "purchase"
    element_id = elements[0].id
    first_risk_id, second_risk_id = risks[0].id, risks[1].id
    db.close()

    assert (
        http.patch(
            f"/api/v1/risks/{first_risk_id}",
            headers=risk_reviewer,
            json={"riskLevel": "low"},
        ).json()["code"]
        == "REVIEW_STAGE_INVALID"
    )
    for path, body in [
        (f"/api/v1/reviews/{review_id}/contract-type", {"contractType": "nda"}),
        (f"/api/v1/reviews/{review_id}/elements/{element_id}", {"value": "人工甲方"}),
        (
            f"/api/v1/risks/{first_risk_id}",
            {"suggestion": "法务修订建议", "comment": "法务复核"},
        ),
    ]:
        assert http.patch(path, headers=legal, json=body).status_code == 200
    assert (
        http.post(
            f"/api/v1/reviews/{review_id}/feedback",
            headers=legal,
            json={
                "targetType": "element",
                "targetId": element_id,
                "judgment": "modified",
                "correctedValue": "人工甲方",
            },
        ).status_code
        == 200
    )
    legal_confirmed = http.post(
        f"/api/v1/reviews/{review_id}/legal-confirm",
        headers=legal,
        json={"opinion": "法务通过"},
    )
    assert legal_confirmed.json()["data"]["reviewStage"] == "riskReview"
    assert (
        http.post(
            f"/api/v1/reviews/{review_id}/risk-confirm", headers=admin, json={}
        ).json()["code"]
        == "REVIEW_ROLE_NOT_ALLOWED"
    )
    assert (
        http.post(
            f"/api/v1/reviews/{review_id}/reports",
            headers=owner,
            json={"reportFormat": "pdf"},
        ).json()["code"]
        == "REPORT_NOT_READY"
    )

    assert (
        http.patch(
            f"/api/v1/risks/{first_risk_id}",
            headers=risk_reviewer,
            json={"riskLevel": "low", "comment": "降低等级"},
        ).status_code
        == 200
    )
    assert (
        http.patch(
            f"/api/v1/risks/{second_risk_id}",
            headers=risk_reviewer,
            json={"riskStatus": "dismissed", "comment": "风险不适用"},
        ).status_code
        == 200
    )
    assert (
        http.patch(
            f"/api/v1/reviews/{review_id}/overall-risk",
            headers=risk_reviewer,
            json={"overallRiskLevel": "low", "overallScore": "12.50"},
        ).status_code
        == 200
    )
    assert (
        http.post(
            f"/api/v1/reviews/{review_id}/feedback",
            headers=risk_reviewer,
            json={"targetType": "risk", "targetId": second_risk_id, "judgment": "incorrect"},
        ).status_code
        == 200
    )
    completed = http.post(
        f"/api/v1/reviews/{review_id}/risk-confirm",
        headers=risk_reviewer,
        json={"opinion": "风控通过"},
    )
    assert (completed.json()["data"]["reviewStatus"], completed.json()["data"]["reviewStage"]) == (
        "completed",
        "completed",
    )
    assert (
        http.patch(
            f"/api/v1/risks/{first_risk_id}",
            headers=risk_reviewer,
            json={"riskLevel": "high"},
        ).json()["code"]
        == "REVIEW_STAGE_INVALID"
    )

    detail = http.get(f"/api/v1/reviews/{review_id}", headers=owner).json()["data"]
    assert detail["aiResult"]["contractType"] == "purchase"
    assert detail["effectiveResult"]["contractType"] == "nda"
    assert detail["effectiveResult"]["elements"][0]["value"] == "人工甲方"
    effective_risks = {item["riskId"]: item for item in detail["effectiveResult"]["risks"]}
    assert effective_risks[first_risk_id]["riskLevel"] == "low"
    assert effective_risks[second_risk_id]["riskStatus"] == "dismissed"
    assert detail["effectiveResult"]["overallScore"] == "12.50"

    html_report = http.get(f"/api/v1/reviews/{review_id}/reports", headers=owner).json()["data"][
        "items"
    ][0]
    assert html_report["reportFormat"] == "html" and html_report["reportStatus"] == "pending"
    pdf_report = http.post(
        f"/api/v1/reviews/{review_id}/reports",
        headers=owner,
        json={"reportFormat": "pdf"},
    ).json()["data"]
    report_executor = ReportExecutor(session_factory=sessions)
    assert asyncio.run(report_executor.run_once())
    assert asyncio.run(report_executor.run_once())
    assert not asyncio.run(report_executor.run_once())
    for report_id, content_type, prefix in [
        (html_report["reportId"], "text/html", b"<!doctype html>"),
        (pdf_report["reportId"], "application/pdf", b"%PDF"),
    ]:
        downloaded = http.get(f"/api/v1/reports/{report_id}/download", headers=owner)
        assert downloaded.status_code == 200
        assert downloaded.headers["content-type"].startswith(content_type)
        assert downloaded.content.startswith(prefix)
        assert http.get(f"/api/v1/reports/{report_id}/download", headers=other).status_code == 404

    dashboard = http.get("/api/v1/dashboard/summary", headers=admin).json()["data"]
    assert dashboard["completedReviews"] == dashboard_before["completedReviews"] + 1
    assert (
        dashboard["effectiveRisksByLevel"]["low"]
        == dashboard_before["effectiveRisksByLevel"]["low"] + 1
    )
    for level in ("high", "medium"):
        assert (
            dashboard["effectiveRisksByLevel"][level]
            == dashboard_before["effectiveRisksByLevel"][level]
        )
    feedback = http.get(
        f"/api/v1/feedback?reviewId={review_id}", headers=admin
    ).json()["data"]
    logs = http.get(
        f"/api/v1/operation-logs?reviewId={review_id}", headers=admin
    ).json()["data"]
    assert feedback["total"] == 2
    expected_actions = {
        "REVIEW_CONTRACT_TYPE_REVISED",
        "REVIEW_ELEMENT_REVISED",
        "REVIEW_RISK_REVISED",
        "REVIEW_OVERALL_RISK_REVISED",
        "REVIEW_FEEDBACK_SUBMITTED",
        "REVIEW_LEGAL_CONFIRMED",
        "REVIEW_RISK_CONFIRMED",
    }
    assert expected_actions <= {item["action"] for item in logs["items"]}
    db = sessions()
    assert db.get(Contract, contract["contractId"]).status == "reviewed"
    assert (
        db.scalar(select(func.count()).select_from(Report).where(Report.review_id == review_id)) == 2
    )
    assert (
        db.scalar(
            select(func.count())
            .select_from(ReviewFeedback)
            .where(ReviewFeedback.review_id == review_id)
        )
        == 2
    )
    assert (
        db.scalar(
            select(func.count())
            .select_from(ReviewRevision)
            .where(ReviewRevision.review_id == review_id)
        )
        == 6
    )
    assert (
        db.scalar(
            select(func.count())
            .select_from(OperationLog)
            .where(OperationLog.resource_type == "review", OperationLog.resource_id == review_id)
        )
        == 10
    )
    assert db.get(ReviewRecord, review_id).ai_result_json["overallScore"] == "75.00"
    db.close()


def test_complete_contract_lifecycle_through_http_ai_and_reports(client, monkeypatch) -> None:
    _run_complete_contract_lifecycle(client, monkeypatch)


def _final_mysql_url() -> str | None:
    raw = os.getenv("BACKEND_FINAL_MYSQL_DATABASE_URL")
    if raw is not None and make_url(raw).database != "a24_backend_final_audit_20260713":
        raise RuntimeError("unsafe backend final MySQL database")
    return raw


@pytest.fixture()
def final_mysql_client(tmp_path):
    mysql_url = _final_mysql_url()
    if mysql_url is None:
        pytest.skip("requires backend final real MySQL")
    engine = create_engine(mysql_url, pool_pre_ping=True)
    sessions = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    old_sessions = db_module.SessionLocal
    old_upload_root = settings.upload_root
    old_report_root = settings.report_root
    db_module.SessionLocal = sessions
    object.__setattr__(settings, "upload_root", tmp_path / "uploads")
    object.__setattr__(settings, "report_root", tmp_path / "reports")
    suffix = uuid4().hex[:10]
    usernames = {
        role: f"final_{role}_{suffix}" for role in ("owner", "other", "admin", "legal", "risk")
    }
    role_names = {
        "owner": "user",
        "other": "user",
        "admin": "admin",
        "legal": "legalReviewer",
        "risk": "riskReviewer",
    }
    db = sessions()
    assert db.scalar(text("SELECT version_num FROM alembic_version")) == "20260713_0004"
    db.add_all(
        User(
            username=username,
            password_hash=hash_password("password"),
            role=role_names[role],
            status="active",
        )
        for role, username in usernames.items()
    )
    db.commit()
    db.close()
    try:
        with TestClient(app) as test_client:
            yield (test_client, sessions), usernames
    finally:
        db_module.SessionLocal = old_sessions
        object.__setattr__(settings, "upload_root", old_upload_root)
        object.__setattr__(settings, "report_root", old_report_root)
        engine.dispose()


def test_final_mysql_complete_contract_lifecycle(final_mysql_client, monkeypatch) -> None:
    mysql_client, usernames = final_mysql_client
    _run_complete_contract_lifecycle(mysql_client, monkeypatch, usernames)
