from __future__ import annotations

import asyncio
import hashlib
from collections.abc import Generator
from datetime import timedelta

import httpx
import pytest
from pydantic import ValidationError
from sqlalchemy import BigInteger, create_engine, select
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.application.review_executor import ReviewExecutor
from app.core.config import settings
from app.infrastructure.ai_client import AIClient
from app.models.entities import (
    Base,
    Contract,
    ContractElement,
    ContractFile,
    ReviewRecord,
    RiskRecord,
    RiskRule,
    RiskWarning,
    User,
    WarningAction,
    utcnow,
)
from app.schemas.ai import AIReviewResult


@compiles(BigInteger, "sqlite")
def sqlite_bigint(_: BigInteger, __, **___) -> str:
    return "INTEGER"


def response(
    request_id: str = "req_ai", contract_id: int = 1, rule_id: int | None = 1, **overrides
) -> AIReviewResult:
    data = {
        "requestId": request_id,
        "contractId": contract_id,
        "contractType": "purchase",
        "typeConfidence": "0.90",
        "elements": [
            {
                "elementType": "partyA",
                "elementName": "甲方",
                "value": "A公司",
                "page": 1,
                "paragraphIndex": 0,
                "confidence": "0.90",
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
                "basis": "R001",
                "suggestion": "设置上限",
                "confidence": "0.80",
                "ruleId": rule_id,
            }
        ],
        "missingClauses": [],
        "overallRiskLevel": "high",
        "overallScore": "72.50",
        "modelName": "mock",
        "modelVersion": "v1",
        "promptVersion": "v0.1",
        "processingTimeMs": 12,
        "warnings": [],
        "error": None,
    }
    data.update(overrides)
    return AIReviewResult.model_validate(data)


class FakeAIClient:
    def __init__(self, result: AIReviewResult | Exception):
        self.result = result
        self.calls: list[dict[str, object]] = []

    async def review_full(self, payload: dict[str, object]) -> AIReviewResult:
        self.calls.append(payload)
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


@pytest.fixture()
def review_db(tmp_path) -> Generator[tuple[sessionmaker[Session], ReviewRecord], None, None]:
    engine = create_engine(
        "sqlite+pysqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    object.__setattr__(settings, "upload_root", tmp_path / "uploads")
    file_path = settings.upload_root / "1" / "contract.pdf"
    file_path.parent.mkdir(parents=True)
    content = b"%PDF-1.7\n"
    file_path.write_bytes(content)
    digest = hashlib.sha256(content).hexdigest()
    db = sessions()
    db.add_all(
        [
            User(id=1, username="owner", password_hash="x", role="user", status="active"),
            Contract(id=1, owner_id=1, name="contract", status="reviewing"),
            ContractFile(
                id=1,
                contract_id=1,
                file_name="contract.pdf",
                storage_path=str(file_path),
                file_type="pdf",
                file_size=len(content),
                sha256=digest,
            ),
            RiskRule(
                id=1,
                rule_code="R001",
                risk_type="unlimitedLiability",
                name="无限责任",
                risk_level="high",
                rule_content="rule",
                status="active",
                version="v1",
            ),
        ]
    )
    review = ReviewRecord(
        id=1,
        contract_id=1,
        contract_file_id=1,
        file_sha256=digest,
        idempotency_user_id=1,
        idempotency_key="key",
        request_id="req_ai",
        review_mode="full",
        status="pending",
        review_stage="aiReview",
        ai_warnings=[],
        missing_clauses=[],
    )
    db.add(review)
    db.commit()
    db.close()
    try:
        yield sessions, review
    finally:
        Base.metadata.drop_all(engine)


async def no_wait(_: float) -> None:
    return None


def state(sessions: sessionmaker[Session]) -> ReviewRecord:
    db = sessions()
    review = db.get(ReviewRecord, 1)
    db.close()
    assert review
    return review


def test_pending_task_is_claimed_and_persisted_atomically(review_db) -> None:
    sessions, _ = review_db
    client = FakeAIClient(response())
    assert asyncio.run(ReviewExecutor(client, sessions, no_wait).run_once())
    review = state(sessions)
    db = sessions()
    assert (review.status, review.review_stage, review.ai_result_json["requestId"]) == (
        "processing",
        "legalReview",
        "req_ai",
    )
    assert db.scalar(select(ContractElement).where(ContractElement.review_id == 1)) is not None
    assert db.scalar(select(RiskRecord).where(RiskRecord.review_id == 1)) is not None
    db.close()
    assert client.calls[0]["requestId"] == client.calls[0]["requestId"]


def test_warning_enabled_rule_creates_one_candidate_warning(review_db) -> None:
    sessions, _ = review_db
    db = sessions()
    rule = db.get(RiskRule, 1)
    assert rule is not None
    rule.warning_enabled = True
    db.commit()
    db.close()
    executor = ReviewExecutor(FakeAIClient(response()), sessions, no_wait)
    assert asyncio.run(executor.run_once())
    db = sessions()
    warning = db.scalar(select(RiskWarning).where(RiskWarning.source_review_id == 1))
    assert warning is not None
    assert warning.warning_status == "pendingLegal"
    assert warning.warning_key
    assert db.scalar(
        select(WarningAction).where(
            WarningAction.warning_id == warning.id,
            WarningAction.action_type == "candidateCreated",
        )
    ) is not None
    db.close()
    assert not asyncio.run(executor.run_once())


def test_database_conditional_claim_prevents_double_claim(review_db) -> None:
    sessions, _ = review_db
    executor = ReviewExecutor(FakeAIClient(response()), sessions, no_wait)
    assert executor._claim_one() == 1
    assert executor._claim_one() is None
    assert state(sessions).ai_attempt_count == 1


@pytest.mark.parametrize("field,value", [("request_id", "wrong"), ("contract_id", 99)])
def test_identity_mismatch_fails_without_results(review_db, field: str, value: object) -> None:
    sessions, _ = review_db
    result = response()
    result = result.model_copy(update={field: value})
    asyncio.run(ReviewExecutor(FakeAIClient(result), sessions, no_wait).run_once())
    review = state(sessions)
    assert (review.status, review.review_stage, review.error_code, review.ai_result_json) == (
        "failed",
        "aiReview",
        "AI_RESPONSE_INVALID",
        None,
    )


def test_ai_error_and_unknown_rule_fail_safely(review_db) -> None:
    sessions, _ = review_db
    failed = response(error={"code": "LLM_API_FAILED", "message": "secret"}, elements=[], risks=[])
    asyncio.run(ReviewExecutor(FakeAIClient(failed), sessions, no_wait).run_once())
    assert state(sessions).error_code == "LLM_API_FAILED"
    db = sessions()
    review = db.get(ReviewRecord, 1)
    assert review
    review.status = "pending"
    review.error_code = None
    review.error_message = None
    db.commit()
    db.close()
    asyncio.run(ReviewExecutor(FakeAIClient(response(rule_id=999)), sessions, no_wait).run_once())
    assert state(sessions).error_code == "AI_RESPONSE_INVALID"


def test_path_escape_and_sha_mismatch_do_not_call_ai(review_db) -> None:
    sessions, _ = review_db
    client = FakeAIClient(response())
    db = sessions()
    file = db.get(ContractFile, 1)
    assert file
    file.storage_path = str(settings.upload_root.parent / "outside.pdf")
    db.commit()
    db.close()
    asyncio.run(ReviewExecutor(client, sessions, no_wait).run_once())
    assert not client.calls and state(sessions).error_code == "FILE_PARSE_FAILED"
    db = sessions()
    review = db.get(ReviewRecord, 1)
    file = db.get(ContractFile, 1)
    assert review and file
    review.status = "pending"
    review.error_code = None
    file.storage_path = str(settings.upload_root / "1" / "contract.pdf")
    review.file_sha256 = "0" * 64
    db.commit()
    db.close()
    asyncio.run(ReviewExecutor(client, sessions, no_wait).run_once())
    assert not client.calls and state(sessions).error_code == "FILE_PARSE_FAILED"


def test_rules_only_is_not_sent_to_full_ai_endpoint(review_db) -> None:
    sessions, _ = review_db
    db = sessions()
    review = db.get(ReviewRecord, 1)
    assert review
    review.review_mode = "rulesOnly"
    db.commit()
    db.close()
    client = FakeAIClient(response())
    asyncio.run(ReviewExecutor(client, sessions, no_wait).run_once())
    assert not client.calls and state(sessions).error_code == "REVIEW_FAILED"


def test_stale_processing_is_recovered_but_fresh_task_is_not(review_db) -> None:
    sessions, _ = review_db
    db = sessions()
    review = db.get(ReviewRecord, 1)
    assert review
    review.status = "processing"
    review.ai_started_at = utcnow() - timedelta(seconds=settings.task_stale_seconds + 1)
    db.commit()
    db.close()
    assert asyncio.run(ReviewExecutor(FakeAIClient(response()), sessions, no_wait).run_once())
    db = sessions()
    review = db.get(ReviewRecord, 1)
    assert review
    review.status = "processing"
    review.review_stage = "aiReview"
    review.ai_result_json = None
    review.ai_started_at = utcnow()
    db.commit()
    db.close()
    assert not asyncio.run(ReviewExecutor(FakeAIClient(response()), sessions, no_wait).run_once())


def test_completed_snapshot_is_not_overwritten(review_db) -> None:
    sessions, _ = review_db
    executor = ReviewExecutor(FakeAIClient(response()), sessions, no_wait)
    asyncio.run(executor.run_once())
    first = state(sessions).ai_result_json
    executor._persist(1, response(modelName="other"), {1: {"ruleId": 1}})
    assert state(sessions).ai_result_json == first


def test_persistence_error_rolls_back_results_and_marks_database_failure(review_db) -> None:
    sessions, _ = review_db
    invalid_risk = response().risks[0].model_copy(update={"risk_name": None})
    result = response().model_copy(update={"risks": [invalid_risk]})
    asyncio.run(ReviewExecutor(FakeAIClient(result), sessions, no_wait).run_once())
    db = sessions()
    assert db.scalar(select(ContractElement).where(ContractElement.review_id == 1)) is None
    assert db.scalar(select(RiskRecord).where(RiskRecord.review_id == 1)) is None
    db.close()
    review = state(sessions)
    assert (review.status, review.review_stage, review.error_code, review.ai_result_json) == (
        "failed",
        "aiReview",
        "DATABASE_ERROR",
        None,
    )


class MockResponse:
    def __init__(self, status: int, data: dict[str, object]):
        self.status_code, self.data = status, data

    def json(self) -> dict[str, object]:
        return self.data


@pytest.mark.parametrize("retry_status", [429, 500])
def test_ai_client_uses_matching_header_and_retries_recoverable_status(
    monkeypatch, retry_status: int
) -> None:
    calls: list[tuple[dict[str, object], dict[str, str]]] = []
    responses = [
        MockResponse(retry_status, {}),
        MockResponse(retry_status, {}),
        MockResponse(200, response().model_dump(by_alias=True, mode="json")),
    ]

    class Client:
        def __init__(self, **_: object) -> None:
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_: object) -> None:
            return None

        async def post(
            self, _url: str, json: dict[str, object], headers: dict[str, str]
        ) -> MockResponse:
            calls.append((json, headers))
            return responses.pop(0)

    monkeypatch.setattr("app.infrastructure.ai_client.httpx.AsyncClient", Client)
    delays: list[float] = []

    async def sleep(value: float) -> None:
        delays.append(value)

    payload = {"requestId": "req_ai"}
    assert asyncio.run(AIClient(sleep=sleep).review_full(payload)).request_id == "req_ai"
    assert len(calls) == 3 and all(
        headers["X-Request-Id"] == body["requestId"] for body, headers in calls
    )
    assert len(delays) == 2


def test_ai_client_does_not_retry_4xx_or_invalid_schema(monkeypatch) -> None:
    calls: list[int] = []

    class Client:
        def __init__(self, **_: object) -> None:
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_: object) -> None:
            return None

        async def post(self, *_: object, **__: object) -> MockResponse:
            calls.append(1)
            return MockResponse(400 if len(calls) == 1 else 200, {})

    monkeypatch.setattr("app.infrastructure.ai_client.httpx.AsyncClient", Client)
    with pytest.raises(Exception):
        asyncio.run(AIClient(sleep=no_wait).review_full({"requestId": "req_ai"}))
    assert len(calls) == 1


def test_ai_client_does_not_retry_invalid_schema(monkeypatch) -> None:
    calls: list[int] = []

    class Client:
        def __init__(self, **_: object) -> None:
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_: object) -> None:
            return None

        async def post(self, *_: object, **__: object) -> MockResponse:
            calls.append(1)
            return MockResponse(200, {})

    monkeypatch.setattr("app.infrastructure.ai_client.httpx.AsyncClient", Client)
    with pytest.raises(Exception):
        asyncio.run(AIClient(sleep=no_wait).review_full({"requestId": "req_ai"}))
    assert len(calls) == 1


@pytest.mark.parametrize(
    "payload",
    [
        {"overallScore": "100.01"},
        {
            "elements": [
                {"elementType": "partyA", "elementName": "甲方", "value": "A", "confidence": "1.01"}
            ]
        },
    ],
)
def test_ai_schema_rejects_out_of_range_scores_and_confidence(payload: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        response(**payload)


def test_ai_client_retries_read_timeout(monkeypatch) -> None:
    calls: list[int] = []

    class Client:
        def __init__(self, **_: object) -> None:
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_: object) -> None:
            return None

        async def post(self, *_: object, **__: object) -> MockResponse:
            calls.append(1)
            if len(calls) < 3:
                raise httpx.ReadTimeout("timeout")
            return MockResponse(200, response().model_dump(by_alias=True, mode="json"))

    monkeypatch.setattr("app.infrastructure.ai_client.httpx.AsyncClient", Client)
    assert (
        asyncio.run(AIClient(sleep=no_wait).review_full({"requestId": "req_ai"})).request_id
        == "req_ai"
    )
    assert len(calls) == 3
