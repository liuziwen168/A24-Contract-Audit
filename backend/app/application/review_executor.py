from __future__ import annotations

import asyncio
import hashlib
import logging
from collections.abc import Awaitable, Callable
from datetime import timedelta
from pathlib import Path

from sqlalchemy import or_, select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.infrastructure.ai_client import AIClient, AIClientError
from app.infrastructure.db import SessionLocal
from app.models.entities import (
    Contract,
    ContractElement,
    ContractFile,
    ReviewRecord,
    RiskRecord,
    RiskRule,
    RiskWarning,
    StandardClause,
    WarningAction,
    utcnow,
)
from app.schemas.ai import AIReviewResult

logger = logging.getLogger(__name__)
SAFE_MESSAGES = {
    "AI_SERVICE_UNAVAILABLE": "AI服务暂不可用",
    "AI_RESPONSE_INVALID": "AI初审结果无效",
    "LLM_API_FAILED": "大模型调用失败",
    "FILE_PARSE_FAILED": "文件无法用于审核",
    "DATABASE_ERROR": "数据存储失败",
    "REVIEW_FAILED": "当前审核模式暂未实现",
}
AI_ERROR_CODES = {"AI_SERVICE_UNAVAILABLE", "LLM_API_FAILED", "REVIEW_FAILED"}


class ReviewExecutor:
    def __init__(
        self,
        client: AIClient | None = None,
        session_factory: sessionmaker[Session] = SessionLocal,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    ) -> None:
        self.client = client or AIClient(sleep=sleep)
        self.session_factory = session_factory
        self.sleep = sleep
        self._stopped = False

    async def run_forever(self) -> None:
        while not self._stopped:
            handled = await self.run_once()
            if not handled:
                await self.sleep(settings.task_poll_seconds)

    def stop(self) -> None:
        self._stopped = True

    def _claim_one(self) -> int | None:
        db = self.session_factory()
        try:
            now = utcnow()
            candidate = db.scalar(
                select(ReviewRecord.id)
                .where(ReviewRecord.status == "pending", ReviewRecord.review_stage == "aiReview")
                .order_by(ReviewRecord.created_at)
                .limit(1)
            )
            recovering = False
            if candidate is None:
                stale_before = now - timedelta(seconds=settings.task_stale_seconds)
                candidate = db.scalar(
                    select(ReviewRecord.id)
                    .where(
                        ReviewRecord.status == "processing",
                        ReviewRecord.review_stage == "aiReview",
                        ReviewRecord.ai_result_json.is_(None),
                        or_(
                            ReviewRecord.ai_started_at.is_(None),
                            ReviewRecord.ai_started_at < stale_before,
                        ),
                    )
                    .order_by(ReviewRecord.ai_started_at)
                    .limit(1)
                )
                recovering = candidate is not None
            if candidate is None:
                return None
            conditions = [
                ReviewRecord.id == candidate,
                ReviewRecord.status == ("processing" if recovering else "pending"),
                ReviewRecord.review_stage == "aiReview",
                ReviewRecord.ai_result_json.is_(None),
            ]
            if recovering:
                conditions.append(
                    or_(
                        ReviewRecord.ai_started_at.is_(None),
                        ReviewRecord.ai_started_at
                        < now - timedelta(seconds=settings.task_stale_seconds),
                    )
                )
            claimed = db.execute(
                update(ReviewRecord)
                .where(*conditions)
                .values(
                    status="processing",
                    review_stage="aiReview",
                    ai_started_at=now,
                    ai_attempt_count=ReviewRecord.ai_attempt_count + 1,
                )
            )
            db.commit()
            return candidate if claimed.rowcount == 1 else None
        except SQLAlchemyError:
            db.rollback()
            return None
        finally:
            db.close()

    async def run_once(self) -> bool:
        review_id = self._claim_one()
        if review_id is None:
            return False
        await self._process(review_id)
        return True

    @staticmethod
    def _safe_file(path_value: str, expected_sha: str) -> Path:
        root = settings.upload_root.resolve()
        path = Path(path_value).resolve()
        if root not in path.parents or not path.is_file():
            raise AIClientError("FILE_PARSE_FAILED")
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        if digest.hexdigest() != expected_sha:
            raise AIClientError("FILE_PARSE_FAILED")
        return path

    def _load_payload(
        self, review_id: int
    ) -> tuple[dict[str, object], dict[int, dict[str, object]]]:
        db = self.session_factory()
        try:
            review = db.get(ReviewRecord, review_id)
            if (
                not review
                or review.status != "processing"
                or review.review_stage != "aiReview"
                or review.ai_result_json is not None
            ):
                raise AIClientError("REVIEW_FAILED")
            if review.review_mode != "full":
                raise AIClientError("REVIEW_FAILED")
            contract = db.get(Contract, review.contract_id)
            contract_file = db.get(ContractFile, review.contract_file_id)
            if not contract or not contract_file or contract_file.contract_id != contract.id:
                raise AIClientError("FILE_PARSE_FAILED")
            path = self._safe_file(contract_file.storage_path, review.file_sha256)
            clauses = db.scalars(
                select(StandardClause).where(StandardClause.status == "active")
            ).all()
            rules = db.scalars(select(RiskRule).where(RiskRule.status == "active")).all()
            standard_clauses = [
                {
                    "clauseId": item.id,
                    "name": item.name,
                    "contractType": item.contract_type,
                    "clauseType": item.clause_type,
                    "content": item.content,
                    "version": item.version,
                    "warningEnabled": item.warning_enabled,
                    "warningDueHours": item.warning_due_hours,
                }
                for item in clauses
            ]
            rule_snapshots = {
                item.id: {
                    "ruleId": item.id,
                    "ruleCode": item.rule_code,
                    "riskType": item.risk_type,
                    "name": item.name,
                    "riskLevel": item.risk_level,
                    "ruleContent": item.rule_content,
                    "version": item.version,
                    "warningEnabled": item.warning_enabled,
                    "warningDueHours": item.warning_due_hours,
                }
                for item in rules
            }
            return (
                {
                    "requestId": review.request_id,
                    "contractId": review.contract_id,
                    "contractFileId": review.contract_file_id,
                    "fileSha256": review.file_sha256,
                    "filePath": str(path),
                    "fileType": contract_file.file_type,
                    "standardClauses": standard_clauses,
                    "riskRules": list(rule_snapshots.values()),
                },
                rule_snapshots,
            )
        finally:
            db.close()

    async def _process(self, review_id: int) -> None:
        try:
            payload, snapshots = self._load_payload(review_id)
            logger.info(
                "ai_review_attempt review_id=%s request_id=%s", review_id, payload["requestId"]
            )
            result = await self.client.review_full(payload)
            if (
                result.request_id != payload["requestId"]
                or result.contract_id != payload["contractId"]
            ):
                raise AIClientError("AI_RESPONSE_INVALID")
            if result.error is not None:
                raise AIClientError(
                    result.error.code if result.error.code in AI_ERROR_CODES else "REVIEW_FAILED"
                )
            if any(
                risk.rule_id is not None and risk.rule_id not in snapshots for risk in result.risks
            ):
                raise AIClientError("AI_RESPONSE_INVALID")
            self._persist(review_id, result, snapshots)
        except AIClientError as error:
            self._mark_failed(review_id, error.code)
        except SQLAlchemyError:
            self._mark_failed(review_id, "DATABASE_ERROR")
        except Exception:
            self._mark_failed(review_id, "REVIEW_FAILED")

    def _persist(
        self, review_id: int, result: AIReviewResult, snapshots: dict[int, dict[str, object]]
    ) -> None:
        db = self.session_factory()
        try:
            review = db.scalar(
                select(ReviewRecord).where(ReviewRecord.id == review_id).with_for_update()
            )
            if (
                not review
                or review.ai_result_json is not None
                or review.status != "processing"
                or review.review_stage != "aiReview"
            ):
                db.rollback()
                return
            contract = db.get(Contract, review.contract_id)
            if contract is None:
                db.rollback()
                return
            for element in result.elements:
                db.add(
                    ContractElement(
                        contract_id=review.contract_id,
                        review_id=review.id,
                        element_type=element.element_type,
                        element_name=element.element_name,
                        value_text=element.value,
                        page=element.page,
                        paragraph_index=element.paragraph_index,
                        confidence=element.confidence,
                        source="ai",
                    )
                )
            persisted_risks: list[RiskRecord] = []
            for risk in result.risks:
                persisted = RiskRecord(
                        review_id=review.id,
                        rule_id=risk.rule_id,
                        rule_snapshot=snapshots.get(risk.rule_id) if risk.rule_id else None,
                        risk_type=risk.risk_type,
                        risk_name=risk.risk_name,
                        risk_level=risk.risk_level,
                        clause_text=risk.clause_text,
                        page=risk.page,
                        paragraph_index=risk.paragraph_index,
                        basis=risk.basis,
                        suggestion=risk.suggestion,
                        confidence=risk.confidence,
                        status="active",
                )
                db.add(persisted)
                persisted_risks.append(persisted)
            db.flush()
            for risk in persisted_risks:
                snapshot = snapshots.get(risk.rule_id) if risk.rule_id else None
                if not snapshot or not snapshot.get("warningEnabled"):
                    continue
                key_source = f"{review.id}:{risk.id}:{snapshot['ruleId']}:{snapshot['version']}"
                warning_key = hashlib.sha256(key_source.encode()).hexdigest()
                source_snapshot = {
                    "rule": snapshot,
                    "risk": {
                        "riskId": risk.id,
                        "riskType": risk.risk_type,
                        "riskName": risk.risk_name,
                        "riskLevel": risk.risk_level,
                        "clauseText": risk.clause_text,
                        "page": risk.page,
                        "paragraphIndex": risk.paragraph_index,
                        "basis": risk.basis,
                        "suggestion": risk.suggestion,
                        "confidence": str(risk.confidence) if risk.confidence is not None else None,
                    },
                }
                warning = RiskWarning(
                    warning_key=warning_key,
                    source_review_id=review.id,
                    source_risk_id=risk.id,
                    contract_id=review.contract_id,
                    owner_id=contract.owner_id,
                    warning_level=risk.risk_level,
                    source_snapshot=source_snapshot,
                )
                db.add(warning)
                db.flush()
                db.add(
                    WarningAction(
                        warning_id=warning.id,
                        action_type="candidateCreated",
                        from_status=None,
                        to_status="pendingLegal",
                    )
                )
            review.ai_result_json = result.model_dump(by_alias=True, mode="json")
            review.ai_model_name = result.model_name
            review.ai_model_version = result.model_version
            review.prompt_version = result.prompt_version
            review.ai_warnings = result.warnings
            review.processing_time_ms = result.processing_time_ms
            review.missing_clauses = result.missing_clauses
            review.overall_risk_level = result.overall_risk_level
            review.overall_score = result.overall_score
            review.status = "processing"
            review.review_stage = "legalReview"
            db.commit()
        except SQLAlchemyError:
            db.rollback()
            raise
        finally:
            db.close()

    def _mark_failed(self, review_id: int, code: str) -> None:
        db = self.session_factory()
        try:
            review = db.get(ReviewRecord, review_id)
            if review and review.ai_result_json is None:
                review.status = "failed"
                review.review_stage = "aiReview"
                review.error_code = code if code in SAFE_MESSAGES else "REVIEW_FAILED"
                review.error_message = SAFE_MESSAGES.get(
                    review.error_code, SAFE_MESSAGES["REVIEW_FAILED"]
                )
                contract = db.get(Contract, review.contract_id)
                if contract:
                    contract.status = "failed"
                db.commit()
        except SQLAlchemyError:
            db.rollback()
        finally:
            db.close()
