from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker

from app.application.manual_review import LEGAL, RISK, claim
from app.core.errors import AppError
from app.models.entities import Contract, ContractFile, ReviewRecord, User


def _mysql_url() -> str | None:
    raw = os.getenv("M22_MYSQL_DATABASE_URL")
    if raw is None:
        return None
    database = make_url(raw).database
    if database != "a24_m22_regression_20260713":
        raise RuntimeError(f"unsafe M22 MySQL database: {database}")
    return raw


MYSQL_URL = _mysql_url()


@pytest.mark.skipif(MYSQL_URL is None, reason="requires real MySQL")
@pytest.mark.parametrize(
    ("role", "stage", "suffix"),
    [(LEGAL, "legalReview", "legal"), (RISK, "riskReview", "risk")],
)
def test_real_mysql_row_lock_allows_only_one_reviewer(role: str, stage: str, suffix: str) -> None:
    assert MYSQL_URL is not None
    engine = create_engine(MYSQL_URL, pool_pre_ping=True)
    sessions = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    db = sessions()
    token = uuid4().hex[:8]
    users = [
        User(
            username=f"m22_owner_{suffix}_{token}",
            password_hash="x",
            role="user",
            status="active",
        ),
        User(username=f"m22_{suffix}_1_{token}", password_hash="x", role=role, status="active"),
        User(username=f"m22_{suffix}_2_{token}", password_hash="x", role=role, status="active"),
    ]
    db.add_all(users)
    db.flush()
    contract = Contract(owner_id=users[0].id, name=f"m22-lock-{suffix}", status="reviewing")
    db.add(contract)
    db.flush()
    file = ContractFile(
        contract_id=contract.id,
        file_name=f"lock-{suffix}.pdf",
        storage_path=f"test/lock-{suffix}.pdf",
        file_type="pdf",
        file_size=1,
        sha256="c" * 64,
    )
    db.add(file)
    db.flush()
    review = ReviewRecord(
        contract_id=contract.id,
        contract_file_id=file.id,
        file_sha256=file.sha256,
        idempotency_user_id=users[0].id,
        idempotency_key=f"m22-lock-{suffix}-{token}",
        request_id=f"req_m22_lock_{suffix}_{token}",
        review_mode="full",
        status="processing",
        review_stage=stage,
        ai_result_json={},
        ai_warnings=[],
        missing_clauses=[],
    )
    db.add(review)
    db.commit()
    review_id = review.id
    reviewer_ids = [users[1].id, users[2].id]
    db.close()

    def attempt(user_id: int) -> str:
        worker: Session = sessions()
        try:
            claim(worker, review_id, user_id, role)
            worker.commit()
            return "claimed"
        except AppError as error:
            worker.rollback()
            return error.code
        finally:
            worker.close()

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(attempt, reviewer_ids))
    assert sorted(outcomes) == ["REVIEW_ALREADY_CLAIMED", "claimed"]
    engine.dispose()
